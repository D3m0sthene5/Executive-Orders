"""Selden census: the later instruments that act on census orders, and whether the project holds their official text.

Zero tokens. Reads committed job outputs only and writes research/selden/census/:

  ACTING_INSTRUMENTS.csv  one row per acting instrument: type, era, holding, orders it acts on (ending / modifying)
  ORDER_NEEDS.csv         one row per census order: open steps, acting leads, the unheld instruments it needs
  BY_TYPE.csv             instruments and orders by instrument type, era and holding
  SUMMARY.json            the counts quoted in research/selden/REPORT.md

Every pair is a lead from an editorial finding aid or a machine scan (later-events, shepard-citations, current-law).
A pair says that a later instrument is printed as acting on an order; it is not a finding that it did.
"""
import collections
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "census"

ENDING = {"revocation", "supersession", "termination", "abolition", "rescission", "nullification", "repeal",
          "vacation", "expiration", "authority_repeal", "supersession_or_revocation", "replacement", "voiding",
          "ceased_to_function", "restoration", "cancellation"}
MODIFYING = {"amendment", "modification", "extension", "continuation", "correction", "supplementation",
             "clarification", "reinstatement", "ratification", "suspension"}
TYPE_OF_PREFIX = {
    "EO": "executive_order", "PLO": "public_land_order", "PROC": "proclamation", "NOTICE": "presidential_notice",
    "PL": "statute", "STAT": "statute", "ACT": "statute_or_agency_act", "PUBRES": "statute",
    "REORG_PLAN": "reorganization_plan", "TRANSFER_ORDER": "agency_document", "MEMORANDUM": "presidential_memorandum",
    "PRES_DETERMINATION": "presidential_determination", "CANAL_ZONE_ORDER": "agency_document",
    "FS_REG": "agency_document", "TREATY": "treaty", "UNNUMBERED_EO": "executive_order_unnumbered",
}


def read_csv(p):
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def era(date):
    y = int(date[:4]) if date and date[:4].isdigit() else None
    if y is None:
        return "undated"
    if y < 1936:
        return "pre-1936 (before the Federal Register)"
    if y < 1994:
        return "1936-1993 (scanned Federal Register issues)"
    return "1994 on (Federal Register documents)"


def label_actor(acting_id, label):
    """Normalise an acting instrument with no id from its printed label (later-events leaves agency documents blank)."""
    if acting_id:
        return acting_id
    lab = label or ""
    m = re.search(r"\((\d+) FR (\d+)\)", lab)
    if m:
        return f"FRDOC:{m.group(1)}FR{m.group(2)}"
    return ""


def main():
    rt = {r["instrument_id"]: r for r in read_csv(ROOT / "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv")}
    universe = set(rt)
    status_hist = set()
    with open(ROOT / "jobs/status-history/output/FRAGMENTS.jsonl", encoding="utf-8") as fh:
        for line in fh:
            try:
                status_hist.add(json.loads(line).get("instrument_id"))
            except ValueError:
                pass
    # Held non-EO instruments: fr-pages PLO pages; theophilus FR continuation notices (by publication date).
    held_plo = {}
    for line in open(ROOT / "jobs/fr-pages/output/SOURCES.jsonl", encoding="utf-8"):
        d = json.loads(line)
        p = d.get("printed_instrument_id") or (d.get("instrument_ids") or [""])[0]
        if str(p).startswith("PLO:"):
            held_plo[p] = d.get("location_confidence")
    notice_dates = set()
    for line in open(ROOT / "jobs/theophilus-sources/output/SOURCES.jsonl", encoding="utf-8"):
        d = json.loads(line)
        m = re.search(r"/(\d{4})/(\d{2})/(\d{2})/", d.get("url", ""))
        if d.get("source_id", "").startswith("fr:notice") and m:
            notice_dates.add("-".join(m.groups()))

    def notice_held(date):
        if not date or date not in {d for d in notice_dates}:
            # publication follows signing by a few days
            import datetime as dt
            try:
                d0 = dt.date.fromisoformat(date[:10])
            except ValueError:
                return False
            return any((d0 + dt.timedelta(days=k)).isoformat() in notice_dates for k in range(0, 8))
        return True

    def holding(actor, itype, date):
        if itype == "executive_order":
            if actor not in universe:
                return "not_in_census"
            tier = rt[actor]["text_evidence_tier"]
            return {"original_supported": "held_official", "transcription_dependent": "held_transcription_only"}.get(
                tier, "not_held")
        if itype == "public_land_order":
            return "held_official_page" if actor in held_plo else "not_held"
        if itype == "presidential_notice":
            return "held_official" if notice_held(date) else "not_held"
        return "not_held"

    pairs = {}   # (target, actor) -> record
    sources_used = collections.Counter()

    def add(target, actor, label, mech, date, evidence, origin, fr_cite=""):
        if target not in universe or not actor or actor == target:
            return
        prefix = actor.split(":", 1)[0]
        itype = TYPE_OF_PREFIX.get(prefix, "agency_document" if prefix == "FRDOC" else "other")
        mech = (mech or "").strip()
        kind = "ending" if mech in ENDING else "modifying" if mech in MODIFYING else "mention"
        key = (target, actor)
        rec = pairs.setdefault(key, {"target": target, "actor": actor, "type": itype, "label": label, "date": "",
                                     "kinds": set(), "mechanisms": set(), "evidence": set(), "origins": set(),
                                     "fr": ""})
        rec["kinds"].add(kind)
        rec["mechanisms"].add(mech)
        rec["evidence"].add(evidence)
        rec["origins"].add(origin)
        if date and not rec["date"]:
            rec["date"] = date
        if label and len(label) > len(rec["label"] or ""):
            rec["label"] = label
        if fr_cite and not rec["fr"]:
            rec["fr"] = fr_cite
        sources_used[origin] += 1

    for r in read_csv(ROOT / "jobs/later-events/output/EDGES.csv"):
        actor = label_actor(r["acting_id"], r["acting_label"])
        m = re.search(r"\b(\d+) FR (\d+)", r["acting_label"] or "")
        add(r["target_id"], actor, r["acting_label"], r["mechanism"], r["date_candidate"], r["evidence_type"],
            "later-events", f"{m.group(1)} FR {m.group(2)}" if m else "")
    plo_fr = {r["plo_id"]: (r["fr_citation"], r["signature_date"]) for r in
              read_csv(ROOT / "jobs/shepard-citations/output/PLO_TABLE.csv")}
    for r in read_csv(ROOT / "jobs/shepard-citations/output/EDGES.csv"):
        fr = plo_fr.get(r["acting_id"], ("", ""))[0]
        if not fr:
            m = re.search(r"\b(\d+) FR (\d+)", r["acting_label"] or "")
            fr = f"{m.group(1)} FR {m.group(2)}" if m else ""
        add(r["target_id"], r["acting_id"], r["acting_label"], r["mechanism"], r["date_candidate"],
            r["evidence_type"], "shepard-citations", fr)
    for r in read_csv(ROOT / "jobs/current-law/output/EVENT_CANDIDATES.csv"):
        add(r["subject_instrument_id"], r["acting_instrument_id"], r["acting_raw"], r["event_type_candidate"],
            r["date_candidate"], "current_law_note:" + r["system"], "current-law", r["acting_fr_citation"])

    # Kit dossiers (decided orders): actors the kit could not use.
    kit_absent = collections.defaultdict(set)
    for p in sorted((ROOT / "jobs/claim-kit/output/dossiers").glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            continue
        for m in d.get("missing") or []:
            if isinstance(m, str) and m.startswith(("Acting identity absent from census: ", "acting text absent: ")):
                kit_absent[d.get("instrument_id")].add(m.split(": ", 1)[1])

    # Per instrument
    inst = {}
    for (t, a), rec in pairs.items():
        e = inst.setdefault(a, {"actor": a, "type": rec["type"], "label": "", "date": "", "fr": "",
                                "targets_ending": set(), "targets_modifying": set(), "targets_mention": set(),
                                "evidence": set()})
        for k in rec["kinds"]:
            e["targets_" + k].add(t)
        e["evidence"] |= rec["evidence"]
        if rec["date"] and not e["date"]:
            e["date"] = rec["date"]
        if rec["fr"] and not e["fr"]:
            e["fr"] = rec["fr"]
        if len(rec["label"] or "") > len(e["label"]):
            e["label"] = rec["label"]
    for a, e in inst.items():
        if a.startswith("PLO:") and a in plo_fr:
            e["fr"] = e["fr"] or plo_fr[a][0]
            e["date"] = e["date"] or plo_fr[a][1]
        e["holding"] = holding(a, e["type"], e["date"])
        e["era"] = era(e["date"])

    # Per order
    orders = []
    for iid, r in rt.items():
        acts = [(a, rec) for (t, a), rec in pairs.items() if t == iid] if False else None
        orders.append(iid)
    by_target = collections.defaultdict(list)
    for (t, a), rec in pairs.items():
        by_target[t].append(rec)
    order_rows = []
    for iid in sorted(universe, key=lambda s: (len(s), s)):
        r = rt[iid]
        recs = by_target.get(iid, [])
        acting = [x for x in recs if x["kinds"] & {"ending", "modifying"}]
        ending = [x for x in recs if "ending" in x["kinds"]]
        unheld = sorted({x["actor"] for x in acting if inst[x["actor"]]["holding"] not in ("held_official",
                                                                                            "held_official_page")})
        unheld_end = sorted({x["actor"] for x in ending if inst[x["actor"]]["holding"] not in ("held_official",
                                                                                               "held_official_page")})
        status = r["provisional_status"] or ""
        status_ok = bool(status) or iid in status_hist
        original_ok = r["text_evidence_tier"] == "original_supported"
        end_open = r["step_ending_or_current_basis"] == "open"
        order_rows.append({
            "instrument_id": iid, "provisional_status": status, "status_history": "yes" if iid in status_hist else "no",
            "text_evidence_tier": r["text_evidence_tier"], "ending_step": r["step_ending_or_current_basis"],
            "counterevidence_step": r["step_counterevidence"],
            "acting_leads": len(acting), "ending_leads": len(ending), "unheld_acting": len(unheld),
            "unheld_ending": len(unheld_end),
            "unheld_types": "|".join(sorted({inst[a]["type"] + ":" + inst[a]["holding"] for a in unheld})),
            "unheld_instruments": "|".join(unheld[:40]),
            "kit_absent_actors": "|".join(sorted(kit_absent.get(iid, ()))),
            # Operational populations (see REPORT.md): A = ending step open and an acting instrument is printed as
            # acting on the order but not held as official text; S = A, with the order's own official text held and
            # a status or dated status history, so the missing acting text is the remaining source gap the census
            # can see.
            "pop_A": "yes" if end_open and unheld else "no",
            "pop_S": "yes" if end_open and unheld and original_ok and status_ok else "no",
            "pop_S_ending": "yes" if end_open and unheld_end and original_ok and status_ok else "no",
            "no_named_instrument": "yes" if end_open and not acting else "no",
        })

    OUT.mkdir(parents=True, exist_ok=True)
    cols = ["actor", "type", "era", "holding", "date", "fr", "orders_ending", "orders_modifying", "orders_acted_on",
            "orders_pop_S", "label", "evidence", "targets_ending_sample"]
    popS = {o["instrument_id"] for o in order_rows if o["pop_S"] == "yes"}
    rows = []
    for a, e in inst.items():
        acted = e["targets_ending"] | e["targets_modifying"]
        if not acted:
            continue
        rows.append({"actor": a, "type": e["type"], "era": e["era"], "holding": e["holding"], "date": e["date"],
                     "fr": e["fr"], "orders_ending": len(e["targets_ending"]),
                     "orders_modifying": len(e["targets_modifying"] - e["targets_ending"]),
                     "orders_acted_on": len(acted), "orders_pop_S": len(acted & popS),
                     "label": (e["label"] or "")[:160], "evidence": "|".join(sorted(e["evidence"])),
                     "targets_ending_sample": "|".join(sorted(e["targets_ending"])[:12])})
    rows.sort(key=lambda x: (-x["orders_pop_S"], -x["orders_acted_on"], x["actor"]))
    with open(OUT / "ACTING_INSTRUMENTS.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, cols)
        w.writeheader()
        w.writerows(rows)
    with open(OUT / "ORDER_NEEDS.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, list(order_rows[0]))
        w.writeheader()
        w.writerows(order_rows)

    # By type x era x holding
    agg = collections.defaultdict(lambda: {"instruments": 0, "orders": set(), "orders_ending": set(),
                                           "orders_pop_S": set()})
    for a, e in inst.items():
        acted = e["targets_ending"] | e["targets_modifying"]
        if not acted:
            continue
        g = agg[(e["type"], e["era"], e["holding"])]
        g["instruments"] += 1
        g["orders"] |= acted
        g["orders_ending"] |= e["targets_ending"]
        g["orders_pop_S"] |= acted & popS
    bt = [{"type": k[0], "era": k[1], "holding": k[2], "instruments": v["instruments"], "orders_acted_on": len(v["orders"]),
           "orders_ended": len(v["orders_ending"]), "orders_pop_S": len(v["orders_pop_S"])}
          for k, v in agg.items()]
    bt.sort(key=lambda x: (-x["orders_pop_S"], -x["orders_acted_on"]))
    with open(OUT / "BY_TYPE.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, list(bt[0]))
        w.writeheader()
        w.writerows(bt)

    def cnt(f):
        return sum(1 for o in order_rows if o[f] == "yes")
    unheld_inst = [x for x in rows if x["holding"] not in ("held_official", "held_official_page")]
    summary = {
        "inputs": {k: v for k, v in sources_used.items()},
        "pairs": len(pairs), "acting_instruments": len(rows),
        "acting_instruments_unheld": len(unheld_inst),
        "unheld_by_type": dict(collections.Counter(x["type"] for x in unheld_inst).most_common()),
        "orders_ending_step_open": sum(1 for o in order_rows if o["ending_step"] == "open"),
        "pop_A_orders": cnt("pop_A"), "pop_S_orders": cnt("pop_S"), "pop_S_ending_orders": cnt("pop_S_ending"),
        "orders_ending_open_with_no_named_acting_instrument": cnt("no_named_instrument"),
        "decided_orders_with_kit_absent_actor": sum(1 for o in order_rows if o["kit_absent_actors"]),
        "note": "Leads only. Holding: held_official = the project holds an official text (EO original_supported, "
                "fr-pages PLO page, theophilus FR notice); everything else is not held as official text.",
    }
    (OUT / "SUMMARY.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    sys.exit(main())
