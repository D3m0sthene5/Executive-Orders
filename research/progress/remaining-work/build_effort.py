"""Remaining work weighted by estimated AI effort.

Same open steps as build_remaining_work.py (readiness tracker, plus the
orders APP counts that the project does not hold yet), but each step gets
the agent-minutes of its tier in EFFORT_MODEL.csv. The tier depends on what
the project's jobs already hold for that order. See EFFORT_NOTES.md.

Writes EFFORT_LONG.csv (president x kind of work), EFFORT_BY_TIER.csv
(kind x tier, with the weight and its basis) and EFFORT.json next to this file.
"""
import collections, csv, json, re
from pathlib import Path

import build_remaining_work as brw

ROOT, HERE = brw.ROOT, brw.HERE
JOBS = ROOT / "jobs"
LEGAL = {"clause_inventory", "ending_or_current_basis", "savings_residuals", "counterevidence"}
SIZE = {"small": 0.7, "medium": 1.0, "large": 1.4}
MODERN_FROM = 7532  # first order in the OFR catalog (January 1937)


def ids(path, col="instrument_id"):
    with open(path) as f:
        return {r[col] for r in csv.DictReader(f)}


def load_model():
    return {r["tier"]: r for r in csv.DictReader(open(HERE / "EFFORT_MODEL.csv"))}


def assign():
    """One record per open step: order, president, step, tier, legal-step multiplier.

    Orders APP counts but the project does not hold come as records with
    instrument_id None and a count, at the hardest tier of each step."""
    model = load_model()
    tracker = list(csv.DictReader(open(brw.TRACKER)))
    pres, _ = brw.attribute(tracker)

    year = {}
    for r in csv.DictReader(open(brw.PROJ)):
        if r["date_effective"].isdigit():
            year[r["id"]] = int(r["date_effective"])
    clause_draft = ids(JOBS / "clause-drafts/output/CLAUSES.csv")
    not_segmented = ids(JOBS / "clause-drafts/output/NOT_SEGMENTED.csv")
    printed = ids(JOBS / "numbered-early-orders/output/FOUND.csv")
    catalog = ids(JOBS / "later-events/output/CATALOG_INDEX.csv", "id")
    edge_targets = ids(JOBS / "later-events/output/EDGES.csv", "target_id")
    app_listed = {i for i in ids(brw.INDEX) if i}
    family = {"EO:" + p.stem[3:] for p in (JOBS / "family-rules/output/certificates").glob("*/EO_*.json")}
    history, status_lead = set(), set()
    for x in json.load(open(JOBS / "status-history/output/INDEX.json")):
        if x["history"] or x["events"]:
            history.add(x["instrument_id"])
        if x["observations"]:
            status_lead.add(x["instrument_id"])
    drafts = {r["instrument_id"]: r for r in
              csv.DictReader(open(JOBS / "claim-drafts/output/TODO_BY_ORDER.csv"))}

    def modern(iid):
        n = brw.num(iid)
        return n >= MODERN_FROM if n is not None else year.get(iid, 0) >= 1937

    def tier(step, iid, blockers, text_done):
        m = modern(iid)
        d = drafts.get(iid, {})
        judged = d.get("only_judgment_left") == "yes"
        hist = iid in history or iid in edge_targets or iid in family
        if step == "provisional_status":
            return "PS1" if iid in status_lead or iid in catalog else "PS2"
        if step == "original_text":
            if "ORIGINAL_FOUND_NEEDS_PAGE_CHECK" in blockers:
                return "OT1"
            if iid in printed or "ONLY_COMPILED_TRANSCRIPTION_FOUND" in blockers:
                return "OT2"
            if m:
                return "OT3"
            if iid in app_listed or iid in clause_draft or iid in not_segmented:
                return "OT4"
            return "OT5"
        if step == "clause_inventory":
            if iid in clause_draft:
                return "CI1"
            return "CI2" if text_done or iid in not_segmented else "CI3"
        if step == "ending_or_current_basis":
            return "EB1" if judged else "EB2" if hist else "EB3" if m else "EB4"
        if step == "savings_residuals":
            return "SR1" if judged else "SR2" if hist else "SR3"
        if step == "counterevidence":
            if "MACHINE_SEARCH_FOUND_CONTRARY_LEAD" in blockers:
                return "CE1"
            return "CE2" if iid in catalog else "CE3" if m else "CE4"
        if step == "shared_sources":
            return "SS1"
        if step == "opus_media":
            return "OM1" if blockers & {"OPUS_MEDIA_REFETCH_NEEDED", "OPUS_MEDIA_ORIGINAL_NOT_KEPT"} else "OM2"
        raise ValueError(step)

    records = []
    for r in tracker:
        iid, p = r["instrument_id"], pres[r["instrument_id"]]
        blockers = {b.split(":")[0] for b in r["blockers"].split("|") if b}
        text_done = r["step_original_text"] == "done"
        mult = SIZE.get(drafts.get(iid, {}).get("estimated_effort"), 1.0)
        for s in brw.STEPS[1:]:
            if r["step_" + s] == "open":
                records.append({"instrument_id": iid, "president": p, "step": s, "count": 1,
                                "tier": tier(s, iid, blockers, text_done), "modern": modern(iid),
                                "mult": mult if s in LEGAL else 1.0})
    gap_tiers = {"admit": "AD", "provisional_status": "PS2", "original_text": "OT5",
                 "clause_inventory": "CI3", "ending_or_current_basis": "EB4",
                 "savings_residuals": "SR3", "counterevidence": "CE4"}
    for r in json.load(open(HERE / "REMAINING_WORK.json"))["presidents"]:
        if r["not_yet_in_project"]:
            for s, t in gap_tiers.items():
                records.append({"instrument_id": None, "president": r["president"], "step": s,
                                "count": r["not_yet_in_project"], "tier": t, "modern": False, "mult": 1.0})
    return records, model


def main():
    records, model = assign()
    rows = json.load(open(HERE / "REMAINING_WORK.json"))["presidents"]
    minutes = collections.defaultdict(float)   # (president, step) -> minutes
    steps = collections.Counter()              # (president, step) -> open steps
    by_tier = collections.Counter(); tier_min = collections.defaultdict(float)
    for x in records:
        w = float(model[x["tier"]]["minutes"]) * x["mult"] * x["count"]
        minutes[x["president"], x["step"]] += w; steps[x["president"], x["step"]] += x["count"]
        by_tier[x["step"], x["tier"]] += x["count"]; tier_min[x["step"], x["tier"]] += w

    kinds = {"admit": (1, "Find and admit to the census"),
             "provisional_status": (2, "First yes/no on whether in effect"),
             "original_text": (3, "Save an official copy of the text"),
             "clause_inventory": (4, "List every operative clause"),
             "ending_or_current_basis": (5, "Prove how it ended or what keeps it in force"),
             "savings_residuals": (6, "Close parts that outlive it"),
             "counterevidence": (7, "Search later law for contrary sources"),
             "shared_sources": (8, "Retrieve cited sources and evidence images"),
             "opus_media": (8, "Retrieve cited sources and evidence images")}
    order = [r["president"] for r in rows]
    with open(HERE / "EFFORT_LONG.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["president_order", "president", "step_order", "kind", "open_steps",
                    "agent_minutes", "agent_hours"])
        for i, p in enumerate(order, 1):
            merged = collections.defaultdict(lambda: [0, 0.0])
            for s in brw.STEPS:
                if steps[p, s]:
                    k = kinds[s]
                    merged[k][0] += steps[p, s]; merged[k][1] += minutes[p, s]
            for (j, k), (n, mins) in sorted(merged.items()):
                w.writerow([i, p, j, k, n, round(mins, 1), round(mins / 60, 2)])
    with open(HERE / "EFFORT_BY_TIER.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["step_order", "kind", "tier", "when", "minutes_per_step", "basis",
                    "open_steps", "agent_hours"])
        for (s, t), n in sorted(by_tier.items(), key=lambda kv: (kinds[kv[0][0]][0], kv[0][1])):
            m = model[t]
            w.writerow([kinds[s][0], kinds[s][1], t, m["when"], m["minutes"], m["basis"], n,
                        round(tier_min[s, t] / 60, 1)])
    total_min = sum(minutes.values())
    by_kind = collections.defaultdict(float)
    for (p, s), v in minutes.items():
        by_kind[kinds[s][1]] += v / 60
    out = {"open_steps": sum(steps.values()), "agent_hours": round(total_min / 60),
           "hours_by_kind": {k: round(v) for k, v in sorted(by_kind.items(), key=lambda kv: -kv[1])},
           "model": "EFFORT_MODEL.csv", "notes": "EFFORT_NOTES.md"}
    (HERE / "EFFORT.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
