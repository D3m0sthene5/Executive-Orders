"""Who does which step: the remaining work by step and by lane.

For every open readiness step the tracker records, puts the order into one lane:

  machine_queued     a wired job can do it; it only has to run (fetch queue, re-fetch list)
  machine_unwired    a machine copy or draft exists, or the owner has ruled, but the tracker
                     does not count it until the rule or output is wired in
  ai_judgment        a machine draft or lead exists; an agent claim line can finish it
  owner_ruling       blocked on a ruling the owner has not made
  owner_action       the owner is doing it by hand (ProQuest scans, phrase searches)
  prerequisite       cannot start until an earlier step is done (status or text first)
  no_route           no copy, lead or job reaches it today

Owner rulings of 2026-10-21 (research/readiness/owner_rulings/) are applied: report
deadlines and strike-and-insert no longer block; transcriptions may satisfy the text
step once the tracker rule is wired (until then they sit in machine_unwired).

Lane membership is decided from the tracker's own blockers plus committed job
outputs (X1 types, claim-drafts, Lambertini, claim-kit families). Counts are
orders. Writes TOOLMAP_WORKLOAD.csv next to this file; TOOLS.csv is hand-kept.
"""
import collections, csv, json, re
from pathlib import Path

import build_remaining_work as brw

ROOT, HERE, JOBS = brw.ROOT, brw.HERE, brw.ROOT / "jobs"
MODERN_FROM = 7532

LANES = ["machine_queued", "machine_unwired", "ai_judgment", "owner_ruling", "owner_action", "prerequisite", "no_route"]
STEPS = [("provisional_status", "First yes/no"), ("original_text", "Official text"),
         ("clause_inventory", "Clause inventory"), ("ending_or_current_basis", "Ending or current basis"),
         ("savings_residuals", "Savings and residuals"), ("counterevidence", "Counter-evidence search"),
         ("shared_sources", "Cited sources"), ("opus_media", "Evidence images")]


def ids(path, col="instrument_id"):
    p = ROOT / path
    if not p.exists():
        return set()
    with open(p) as f:
        return {r[col] for r in csv.DictReader(f) if r.get(col)}


def main():
    tracker = list(csv.DictReader(open(brw.TRACKER)))
    year = {}
    for r in csv.DictReader(open(brw.PROJ)):
        if r["date_effective"].isdigit():
            year[r["id"]] = int(r["date_effective"])
    drafts = {r["instrument_id"]: r for r in csv.DictReader(open(JOBS / "claim-drafts/output/TODO_BY_ORDER.csv"))}
    clause_draft = ids("jobs/clause-drafts/output/CLAUSES.csv")
    hist = set()
    p = JOBS / "status-history/output/INDEX.json"
    if p.exists():
        hist = {x["instrument_id"] for x in json.load(open(p)) if x["history"] or x["events"]}
    edge_targets = ids("jobs/later-events/output/EDGES.csv", "target_id")
    lamb_prefill = ids("jobs/lambertini/output/SAVINGS_PREFILL.csv")
    lamb_ce = set()
    p = JOBS / "lambertini/output/COUNTEREVIDENCE_RECORDS.jsonl"
    if p.exists():
        for line in open(p):
            try:
                lamb_ce.add(json.loads(line).get("instrument_id"))
            except json.JSONDecodeError:
                pass
    lewis = {}
    p = JOBS / "lewis-originals/output/ROUTES.csv"
    if p.exists():
        for r in csv.DictReader(open(p)):
            lewis[r["instrument_id"]] = (r["best_route"], r["route_status"], r["action_owner"])
    report_deadline = set()
    p = JOBS / "claim-kit/output/FAMILIES.json"
    if p.exists():
        for f in json.load(open(p)):
            if f["family_id"] == "own_term:report_deadline":
                report_deadline |= set(f["instrument_ids"])

    def modern(i):
        n = brw.num(i)
        return n >= MODERN_FROM if n is not None else year.get(i, 0) >= 1937

    out = collections.Counter()
    tools = collections.defaultdict(set)
    for r in tracker:
        i = r["instrument_id"]
        bl = {b.split(":")[0] for b in r["blockers"].split("|") if b}
        st = r["provisional_status"] in ("yes", "no")
        text = r["step_original_text"] == "done"
        lead_text = "ONLY_COMPILED_TRANSCRIPTION_FOUND" in bl
        m = modern(i)
        judged = drafts.get(i, {}).get("only_judgment_left") == "yes"
        has_hist = i in hist or i in edge_targets

        def put(step, lane, tool=""):
            out[step, lane] += 1
            if tool:
                tools[step, lane].add(tool)

        if r["step_provisional_status"] == "open":
            if m:
                put("provisional_status", "ai_judgment", "Bowditch Y1 · Sinclair (lean review)")
            elif text or lead_text:
                put("provisional_status", "ai_judgment", "X1 type rules on held or transcribed text")
            else:
                put("provisional_status", "prerequisite")
        if r["step_original_text"] == "open":
            route, status, owner = lewis.get(i, ("", "", ""))
            if "ORIGINAL_FOUND_NEEDS_PAGE_CHECK" in bl:
                put("original_text", "ai_judgment", "page check")
            elif lead_text:
                put("original_text", "machine_unwired", "transcription ruled usable; tracker rule pending (Lewis routes the original)")
            elif owner == "machine_job":
                put("original_text", "machine_queued", "Lewis → source-ladder fetch request")
            elif owner == "agent_check":
                put("original_text", "ai_judgment", "Lewis: check a volume index or page")
            elif owner == "owner":
                put("original_text", "owner_action", "Lewis: ProQuest scan or phrase search by the owner")
            elif m:
                put("original_text", "machine_queued", "fr-originals · source-ladder")
            else:
                put("original_text", "no_route", "Clark: identity unknown")
        if r["step_clause_inventory"] == "open":
            if not st:
                put("clause_inventory", "prerequisite")
            elif i in clause_draft:
                put("clause_inventory", "ai_judgment", "clause-drafts → claim-kit")
            elif text or lead_text:
                put("clause_inventory", "machine_unwired", "clause-drafts (not yet segmented)")
            else:
                put("clause_inventory", "prerequisite")
        if r["step_ending_or_current_basis"] == "open":
            if not st:
                put("ending_or_current_basis", "prerequisite")
            elif i in report_deadline:
                put("ending_or_current_basis", "ai_judgment", "Pullman packets (report-deadline ruling made)")
            elif judged:
                put("ending_or_current_basis", "ai_judgment", "claim-drafts judgment-only")
            elif has_hist:
                put("ending_or_current_basis", "ai_judgment", "Lambertini · Rastell · Lamm")
            elif text:
                put("ending_or_current_basis", "no_route", "no ending instrument held")
            else:
                put("ending_or_current_basis", "prerequisite")
        if r["step_savings_residuals"] == "open":
            if not st:
                put("savings_residuals", "prerequisite")
            elif i in lamb_prefill:
                put("savings_residuals", "ai_judgment", "Lambertini prefill")
            elif text:
                put("savings_residuals", "ai_judgment", "claim-kit")
            else:
                put("savings_residuals", "prerequisite")
        if r["step_counterevidence"] == "open":
            if not st:
                put("counterevidence", "prerequisite")
            elif "MACHINE_SEARCH_FOUND_CONTRARY_LEAD" in bl:
                put("counterevidence", "ai_judgment", "resolve contrary lead")
            elif i in lamb_ce:
                put("counterevidence", "machine_unwired", "Lambertini draft record")
            else:
                put("counterevidence", "ai_judgment", "later-events · current-law")
        if r["step_shared_sources"] == "open":
            put("shared_sources", "machine_queued", "source-ladder queue")
        if r["step_opus_media"] == "open":
            if bl & {"OPUS_MEDIA_REFETCH_NEEDED", "OPUS_MEDIA_ORIGINAL_NOT_KEPT"}:
                put("opus_media", "machine_queued", "opus-media-match re-fetch")
            else:
                put("opus_media", "ai_judgment", "match or settle images")

    with open(HERE / "TOOLMAP_WORKLOAD.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["step_order", "step", "step_label", "lane_order", "lane", "orders", "tools"])
        for si, (s, label) in enumerate(STEPS, 1):
            for li, lane in enumerate(LANES, 1):
                if out[s, lane]:
                    w.writerow([si, s, label, li, lane, out[s, lane], " / ".join(sorted(tools[s, lane]))])
    summary = {lane: sum(v for (s, l), v in out.items() if l == lane) for lane in LANES}
    summary["open_steps"] = sum(out.values())
    summary["tracker_rows"] = len(tracker)
    summary["ready"] = sum(r["ready_for_human_review"] == "yes" for r in tracker)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
