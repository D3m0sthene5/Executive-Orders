"""Nalimov one-question tiers: reach, question-packet tokens and projected cost per adopted status. Zero tokens.

The script drafts everything it can for an order and narrows what is left to single legal questions, each with a
small packet: the decisive held sentence(s) with hashes and the field the answer fills. A model answers each
question; the drafter fills the field; the claim then goes through the conveyor's ordinary stages.

Tiers measured, in the coordinator's order (largest that needs no new source first):
  one_time_commands   "Was this one-time command performed, and when, per this held text?"      (clause_needs_judgment)
  recorded_amendments "Does this held amending provision leave the order whole, and which clause does it change?"
  read_current_law    "Does this held U.S. Code / eCFR text state the order is in force or ended?" (needs F3 for text)
  read_unlocated_actor "Does this held text of another order act on this order, and how?"         (needs F4 for text)
Other blockers are listed with their count; a tier that needs a source (second witness, page checks) or a doctrine
the rulings do not give is not a one-question tier.

Inputs: research/nalimov/census/CENSUS.csv, the blocked candidates' frozen evidence (census.py --evidence-cache
DIR, written to DIR/blocked/), and jobs/current-law/output/MENTIONS.csv and jobs/pothier/output/LEADS.jsonl from a
checkout with outputs.

    python -I research/nalimov/tiers.py --evidence DIR/blocked --data CHECKOUT > research/nalimov/TIERS.json
"""
import argparse
import collections
import csv
import json
import re
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "jobs/nalimov-tablebase"))
import drafter as D  # noqa: E402
import tally as T  # noqa: E402

csv.field_size_limit(1 << 30)
TIERS = ("one_time_commands", "recorded_amendments", "read_current_law", "read_unlocated_actor",
         "own_terms_before_end", "delayed_effect")
NEEDS_FIX = {"read_current_law": "F3", "read_unlocated_actor": "F4"}
QUESTION_OVERHEAD = 700        # tokens: the fixed question prompt, field definition and answer format
ANSWER_TOKENS = 250
PRICE = {"input": 2.0, "output": 10.0}   # Sonnet 5.5 list, USD per MTok (jobs/necker-costs/PRICES.json, 2026-11-06)
VERIFY_USD_PER_CLAIM = 0.109             # research/nalimov/PROJECTION.json, mid case (three readers)
COORD_USD_PER_CLAIM = 0.03
UPHELD = 0.80
FULL_ROUTE_USD = 7.71


def tok(text):
    return round(len(str(text or "")) / 4)


def windows(text, iid, width=1200):
    pat = D.P._id_pattern(iid)
    flat = D.flat(text)
    spans = [(max(0, m.start() - width), m.end() + width) for m in re.finditer(pat, flat)] if pat else []
    return sum(b - a for a, b in spans[:4])


def questions(ev, dr, mentions):
    """{tier: [question packet token counts]} for one blocked order."""
    d = ev["base_dossier"]
    recs = d.get("evidence") or {}
    iid = ev["instrument_id"]
    f = dr.get("facts") or {}
    out = collections.defaultdict(list)
    names = {b.split(":")[0] for b in dr["blockers"]}
    end_sentence = tok(f.get("provision_text"))
    if "clause_needs_judgment" in names:
        texts = {c["scope_id"]: str(c.get("text") or "") for c in d.get("clauses") or []}
        for scope, state in (f.get("clause_states") or {}).items():
            if state == "needs_judgment":
                out["one_time_commands"].append(tok(texts.get(scope)) + end_sentence + QUESTION_OVERHEAD)
    if names & {"another_instrument_acts", "chain_event_by_another_actor", "same_actor_other_act", "catalog_entry_acts_on_order"}:
        actors = collections.defaultdict(int)
        for k, r in recs.items():
            if k.startswith("ACT:") and r.get("actor_id") != f.get("actor_id"):
                actors[r.get("actor_id")] = max(actors[r.get("actor_id")], tok(r.get("provision_text") or r.get("text")))
        for ev_ in ((d.get("chain") or {}).get("events") or []):
            if ev_.get("actor_id") not in (f.get("actor_id"), None):
                actors[ev_.get("actor_id")] = max(actors[ev_.get("actor_id")], tok(ev_.get("provision_text")))
        labels = sum(tok(c.get("label")) + 4 for c in d.get("clauses") or [])
        for a, t in actors.items():
            out["recorded_amendments"].append(t + labels + QUESTION_OVERHEAD)
        if not actors:
            out["recorded_amendments"].append(labels + 200 + QUESTION_OVERHEAD)   # a catalog entry only
    if names & {"current_law_mention_needs_reading", "current_law_lead_needs_reading"}:
        for m in mentions or []:
            out["read_current_law"].append(tok(m.get("snippet")) + 150 + QUESTION_OVERHEAD)
        if not mentions:
            out["read_current_law"].append(400 + QUESTION_OVERHEAD)
    if "own_term_needs_reading" in names:
        seen = set()   # one question per term, not per held representation of it (TERM:...@<representation>)
        for k, r in recs.items():
            base = k.split("@")[0]
            if k.startswith("TERM:") and r.get("kind") not in D.HARMLESS_TERM_KINDS and base not in seen:
                seen.add(base)
                out["own_terms_before_end"].append(tok(r.get("text")) + end_sentence + QUESTION_OVERHEAD)
    if names & {"effective_wording_unparsed", "actor_effective_sentence_needs_reading", "effective_class_needs_reading",
                "end_date_not_derivable", "dates_out_of_order"}:
        atext = (recs.get(f"ACTOR_TEXT:{f.get('actor_id')}") or {}).get("text") or ""
        hits = [s for s in D._sentences(atext) if D.DELAYED.search(s)][:3]
        out["delayed_effect"].append(sum(tok(s) for s in hits) + end_sentence + QUESTION_OVERHEAD)
    unlocated = [str(m).split(":", 1)[1].strip() for m in d.get("missing") or []
                 if str(m).startswith(("target provision not located", "cited by number, no change provision located"))]
    for a in unlocated:
        text = (recs.get(f"ACTOR_TEXT:{a}") or {}).get("text")
        size = windows(text, iid) if text else 2400 * 4    # not held yet: F4 routes it; estimate two windows
        out["read_unlocated_actor"].append(round(size / 4) + QUESTION_OVERHEAD)
    return out


def cost(tokens_in):
    return (tokens_in * PRICE["input"] + ANSWER_TOKENS * PRICE["output"]) / 1e6


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--data", required=True)
    a = ap.parse_args(argv)
    data = Path(a.data)
    rows = {r["instrument_id"]: r for r in csv.DictReader(open(HERE / "census/CENSUS.csv", encoding="utf-8"))
            if r["kind"] == "express_named_revocation" and r["complete"] != "True"}
    mindex = D.mentions_index(csv.DictReader(open(data / "jobs/current-law/output/MENTIONS.csv", encoding="utf-8")))
    pothier = {}
    for line in open(data / "jobs/pothier/output/LEADS.jsonl", encoding="utf-8"):
        r = json.loads(line)
        pothier[r["instrument_id"]] = r
    per_order = {}
    for p in sorted(Path(a.evidence).glob("EO_*.json")):
        ev = json.loads(p.read_text(encoding="utf-8"))
        iid = ev["instrument_id"]
        if iid not in rows:
            continue
        dr = D.draft(ev, mentions=D.mentions_for(mindex, iid))
        q = questions(ev, dr, D.mentions_for(mindex, iid))
        remedies = {x for _, need in T.remedies(rows[iid]) for x in need}
        per_order[iid] = {"questions": {k: v for k, v in q.items()}, "remedies": sorted(remedies)}
    tiers_tag = {"tier:" + t for t in TIERS}
    fix_ok = {"F3", "F4", "F5", "F6", "F7"}
    result = {"schema": "nalimov-tiers/v1", "orders_measured": len(per_order),
              "basis": "express-revocation candidates blocked on main (854514831e outputs); upper bounds",
              "assumptions": {"question_overhead_tokens": QUESTION_OVERHEAD, "answer_tokens": ANSWER_TOKENS,
                              "answer_model_price_usd_per_mtok": PRICE, "verify_usd_per_claim": VERIFY_USD_PER_CLAIM,
                              "coordinator_usd_per_claim": COORD_USD_PER_CLAIM, "upheld_rate": UPHELD,
                              "answers": "one answer per question; the claim then gets the full conveyor review"},
              "tiers": {}, "cumulative": []}
    for t in TIERS:
        have = [i for i, o in per_order.items() if "tier:" + t in o["remedies"]]
        qs = [x for i in have for x in per_order[i]["questions"].get(t, [])]
        sole = [i for i in have if all(r == "tier:" + t or r in fix_ok for r in per_order[i]["remedies"])]
        sole_now = [i for i in have if set(per_order[i]["remedies"]) <= {"tier:" + t} | (
            {NEEDS_FIX[t]} if t in NEEDS_FIX else set())]
        pothier_cov = collections.Counter((pothier.get(i) or {}).get("lead_kind") or "no Pothier lead" for i in have)
        q_per_order = [len(per_order[i]["questions"].get(t, [])) for i in have]
        med_q = statistics.median(qs) if qs else 0
        per_status = (sum(cost(x) for x in qs) / max(1, len(have)) + VERIFY_USD_PER_CLAIM + COORD_USD_PER_CLAIM) / UPHELD
        result["tiers"][t] = {
            "orders_with_this_blocker": len(have), "questions": len(qs),
            "questions_per_order_median": statistics.median(q_per_order) if q_per_order else 0,
            "question_packet_tokens_median": med_q, "question_packet_tokens_p90": sorted(qs)[int(0.9 * (len(qs) - 1))] if qs else 0,
            "unlocked_by_this_tier_alone": len(sole_now),
            "unlocked_by_this_tier_with_F3_F7": len(sole),
            "needs_fix_first": NEEDS_FIX.get(t),
            "projected_usd_per_adopted_status": round(per_status, 3),
            "vs_full_route": round(FULL_ROUTE_USD / per_status, 1),
            "pothier_lead_kinds": dict(pothier_cov.most_common(6))}
    done = set()
    allowed = set(fix_ok)
    for t in TIERS:
        allowed.add("tier:" + t)
        now = {i for i, o in per_order.items() if set(o["remedies"]) <= allowed}
        result["cumulative"].append({"tiers_through": t, "with_F3_F7": True, "orders_unlocked": len(now),
                                     "new_at_this_step": len(now - done)})
        done |= now
    other = collections.Counter(r for o in per_order.values() for r in o["remedies"]
                                if r not in tiers_tag and r not in fix_ok)
    result["remaining_remedies_after_four_tiers"] = dict(other.most_common())
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
