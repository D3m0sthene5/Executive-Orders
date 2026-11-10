"""Nalimov whole-pool tier tally: does the one-question tier reach thousands of orders, or stay near 200? Zero tokens.

A coarse model, applied to every order in the pool from main's compiled leads (no evidence is frozen):
- **Basis kind**: the evidence an ending or current claim could rest on:
  - express: a whole named ACT passing Respondendi's sentence predicate;
  - own_terms: a whole-scope own term with a stated date;
  - amendment_only: a Pothier P2 'merged into parent' lead, after F5;
  - yes_current: a printed or current U.S. Code / eCFR text with no ending signal, after F3;
  - partial_only: only partial acts;
  - none: no basis held.
- **Text gate**: an acceptable original passes; a held working text needs F6; neither needs a source; a page check
  owed needs a source.
- **Questions**, one per item the script cannot settle:
  - one-time clauses (drafter.classify_clause says needs_judgment);
  - acts by other instruments (recorded amendments);
  - U.S. Code / eCFR mentions (current-law notes, after F3);
  - unlocated acting texts (after F4);
  - own terms of an ending kind (express and YES kinds only).
- **Sources and rules**: a missing second witness before EO 7532 (undecided express only) and partial_only / none
  bases need a source or a new rule, not a question.

An order is reachable when its basis kind is one of the four, its text gate is passable, and everything else is a
question. Cumulative reach adds tiers in the order of the whole-pool count. These are upper bounds. Larrey's gate file
(PR #280) is not on main, so it is not applied.

    python -I research/nalimov/pool_tally.py --data CHECKOUT > research/nalimov/POOL_TALLY.json
"""
import argparse
import collections
import csv
import glob
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "jobs/nalimov-tablebase"))
import drafter as D  # noqa: E402
import predicate as P  # noqa: E402

csv.field_size_limit(1 << 30)
QUESTION_TIERS = ("one_time_commands", "recorded_amendments", "read_current_law", "read_unlocated_actor",
                  "own_terms_before_end")
TIER_TOKENS = {"one_time_commands": 786, "recorded_amendments": 945, "read_current_law": 919,
               "read_unlocated_actor": 1301, "own_terms_before_end": 816, "basis": 900}   # medians, TIERS.json
VERIFY_USD, COORD_USD, UPHELD, FULL = 0.109, 0.03, 0.80, 7.71
ENDING_SIGNALS = ("revoked", "superseded", "terminated", "rescinded", "repealed", "expired", "abolished", "no longer")


def jsonl(paths):
    for p in paths:
        with open(p, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)


def num(iid):
    m = re.match(r"\D*(\d+)", iid or "")
    return int(m.group(1)) if m else 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--yes-slice", type=int, default=405)
    a = ap.parse_args(argv)
    data = Path(a.data)
    kit = data / "jobs/claim-kit/output"
    tracker = {r["instrument_id"]: r for r in csv.DictReader(
        open(data / "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv", encoding="utf-8"))}
    pools = {
        "undecided": sorted(i for i, r in tracker.items() if not r["provisional_status"]),
        "decided_no_lifecycle": sorted(i for i, r in tracker.items()
                                       if r["provisional_status"] == "no" and r["ready_for_human_review"] != "yes"),
        "decided_yes_lifecycle": sorted((i for i, r in tracker.items()
                                         if r["provisional_status"] == "yes" and r["ready_for_human_review"] != "yes"),
                                        key=num)[:a.yes_slice],
    }
    want = set().union(*pools.values())
    kind = P.EXPRESS
    acts, terms, clauses, leads, selected = (collections.defaultdict(list), collections.defaultdict(list), {}, {}, {})
    for r in jsonl(sorted(glob.glob(str(kit / "ACTING_PROVISIONS*.jsonl")))):
        if r.get("target_id") in want:
            acts[r["target_id"]].append(r)
    for r in jsonl(sorted(glob.glob(str(kit / "OWN_TERMS*.jsonl")))):
        if r.get("instrument_id") in want:
            terms[r["instrument_id"]].append(r)
    for r in jsonl([kit / "CLAUSES.jsonl"]):
        iid = r.get("instrument_id") or ((r.get("clauses") or [{}])[0].get("scope_id", "").split("#")[0])
        if iid in want:
            clauses[iid] = r.get("clauses") or []
    for r in jsonl([kit / "STATUS_LEADS.jsonl"]):
        if r.get("instrument_id") in want:
            leads[r["instrument_id"]] = r
    for r in jsonl(sorted(glob.glob(str(kit / "OVERLAY_INPUTS*.jsonl")))):
        if r.get("instrument_id") in want:
            selected[r["instrument_id"]] = r.get("selected") or {}
    mentions = collections.Counter()
    for r in csv.DictReader(open(data / "jobs/current-law/output/MENTIONS.csv", encoding="utf-8")):
        if r.get("instrument_id") in want and r.get("role") != "ending_order_in_status_line":
            mentions[r["instrument_id"]] += 1
    p2 = set()
    for r in jsonl([data / "jobs/pothier/output/LEADS.jsonl"]):
        if r.get("lead_kind") == "merged_into_parent_on_issue":
            p2.add(r["instrument_id"])
    decided_original = {}
    for pool in ("decided_no_lifecycle", "decided_yes_lifecycle"):
        for iid in pools[pool]:
            path = kit / "dossiers" / (iid.replace(":", "_") + ".json")
            if path.exists():
                dz = json.loads(path.read_text(encoding="utf-8"))
                o = (dz.get("evidence") or {}).get(dz.get("original_source_id")) or {}
                decided_original[iid] = o
                clauses.setdefault(iid, dz.get("clauses") or [])
                leads.setdefault(iid, {"missing": dz.get("missing") or [], "current_law_leads": dz.get("current_law_leads") or []})

    def model(iid, pool):
        sel = decided_original.get(iid) if pool != "undecided" else selected.get(iid)
        sel = sel or {}
        if sel.get("acceptable_as_original") is True:
            gate = "sources" if sel.get("requires_page_check") else "ok"
        elif (tracker.get(iid) or {}).get("text_evidence_tier") in ("original_supported", "transcription_dependent"):
            gate = "F6"
        else:
            gate = "sources"
        a_ = acts.get(iid, [])
        express = [r for r in a_ if r.get("scope") == "whole" and r.get("names_target") and not r.get("reaches_target_via")
                   and r.get("verb") in kind["act_verbs"] and P.named_end_in(str(r.get("provision_text") or ""), iid, kind)]
        dated_terms = [t for t in terms.get(iid, []) if t.get("kind") in ("fixed_term", "sunset_date")
                       and P._date(t.get("stated_end_date")) and t.get("scope_id") in (iid, iid + "#whole")]
        cl_leads = (leads.get(iid) or {}).get("current_law_leads") or []
        printed = [c for c in cl_leads if (c.get("meta") or c).get("basis_code") in ("printed_eo_text", "printed_eo_note")]
        if pool == "decided_yes_lifecycle":
            basis = "yes_current" if (printed or mentions[iid]) else "none"
        elif express:
            basis = "express"
        elif iid in p2:
            basis = "amendment_only"
        elif dated_terms:
            basis = "own_terms"
        elif pool == "undecided" and printed and not any(w in json.dumps(cl_leads).lower() for w in ENDING_SIGNALS):
            basis = "yes_current"
        elif any(r.get("scope") == "partial" for r in a_):
            basis = "partial_only"
        else:
            basis = "none"
        q = collections.Counter()
        for c in clauses.get(iid, []):
            if D.classify_clause(str(c.get("text") or ""), re.sub(r"\D", "", iid)) == "needs_judgment":
                q["one_time_commands"] += 1
        enders = {r.get("actor_id") for r in express}
        q["recorded_amendments"] += len({r.get("actor_id") for r in a_ if r.get("actor_id") not in enders})
        q["read_current_law"] += mentions[iid] if basis != "yes_current" else 0
        q["read_unlocated_actor"] += sum(1 for m in (leads.get(iid) or {}).get("missing") or []
                                         if str(m).startswith(("target provision not located", "cited by number")))
        if basis in ("express", "yes_current"):
            q["own_terms_before_end"] += len({t["id"].split("@")[0] for t in terms.get(iid, [])
                                              if t.get("kind") not in D.HARMLESS_TERM_KINDS})
        fixes = set()
        if gate == "F6":
            fixes.add("F6")
        if basis == "amendment_only":
            fixes.add("F5")
        if basis == "yes_current" or q["read_current_law"]:
            fixes.add("F3")
        if q["read_unlocated_actor"]:
            fixes.add("F4")
        needs_source = gate == "sources" or basis in ("partial_only", "none") or (
            pool == "undecided" and basis == "express" and num(iid) < 7532)       # second witness (catalog from 7532)
        return {"basis": basis, "gate": gate, "questions": {k: v for k, v in q.items() if v}, "fixes": sorted(fixes),
                "needs_source_or_rule": needs_source}

    out = {"schema": "nalimov-pool-tally/v1", "basis": "origin/main 854514831e outputs; coarse model, upper bounds",
           "larrey_gate_applied": False, "pools": {}}
    everything = {}
    for pool, ids in pools.items():
        rows = {i: model(i, pool) for i in ids}
        everything.update({(pool, i): v for i, v in rows.items()})
        basis = collections.Counter(v["basis"] for v in rows.values())
        gate = collections.Counter(v["gate"] for v in rows.values())
        qorders = collections.Counter(t for v in rows.values() for t in v["questions"])
        reach = [i for i, v in rows.items() if not v["needs_source_or_rule"]]
        out["pools"][pool] = {"orders": len(ids), "basis_kind": dict(basis.most_common()), "text_gate": dict(gate.most_common()),
                              "orders_needing_tier": dict(qorders.most_common()),
                              "reachable_with_F3_F7_and_all_question_tiers": len(reach),
                              "reachable_by_basis": dict(collections.Counter(rows[i]["basis"] for i in reach).most_common()),
                              "needs_source_or_rule": sum(1 for v in rows.values() if v["needs_source_or_rule"])}
    # Cumulative over the whole pool, tiers in the order of the whole-pool count.
    reach_all = {k: v for k, v in everything.items() if not v["needs_source_or_rule"]}
    count = collections.Counter(t for v in reach_all.values() for t in v["questions"])
    order = [t for t, _ in count.most_common()]
    cum, allowed, prev = [], set(), 0
    none_needed = sum(1 for v in reach_all.values() if not v["questions"])
    cum.append({"tiers": "none (basis questions only)", "orders": none_needed})
    for t in order:
        allowed.add(t)
        n = sum(1 for v in reach_all.values() if set(v["questions"]) <= allowed)
        cum.append({"tiers_through": t, "orders": n, "new": n - (cum[-1]["orders"])})
    qs = [sum(v["questions"].values()) for v in reach_all.values()]
    tokens = [sum(TIER_TOKENS[t] * n for t, n in v["questions"].items()) + TIER_TOKENS["basis"] for v in reach_all.values()]
    usd_q = [(tk * 2.0 + (sum(v["questions"].values()) + 1) * 250 * 10.0) / 1e6 for tk, v in zip(tokens, reach_all.values())]
    per_status = (sum(usd_q) / max(1, len(usd_q)) + VERIFY_USD + COORD_USD) / UPHELD
    out["whole_pool"] = {"orders": len(everything), "reachable": len(reach_all), "tier_order": order, "cumulative": cum,
                         "questions_per_reachable_order_median": sorted(qs)[len(qs) // 2] if qs else 0,
                         "question_tokens_per_order_median": sorted(tokens)[len(tokens) // 2] if tokens else 0,
                         "projected_usd_per_adopted_status": round(per_status, 3),
                         "vs_full_route": round(FULL / per_status, 1),
                         "needs_source_or_rule": len(everything) - len(reach_all),
                         "fixes_needed_by_reachable": dict(collections.Counter(f for v in reach_all.values() for f in v["fixes"]).most_common())}
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
