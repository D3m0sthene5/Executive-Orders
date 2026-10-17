"""Readiness tracker: how many orders the machines have finished.

An order is READY FOR HUMAN REVIEW when every research step it needs is either
done (backed by a saved source or a claim that passes the Stage 19 claim gate)
or recorded as exhausted (the source ladder was searched and logged, and
nothing more can be found by machine). Human verification is a separate,
later count and is never implied here.

The tracker also counts what blocks each step and groups blockers that one
shared action would clear for many orders at once (one statute retrieved, one
bulk download run), so Opus and Astra can work on whatever unblocks the most.

Inputs are committed files only. Nothing here changes a status or a count in
the research ledger.
"""

import collections
import csv
import glob
import json
import os
import sys

STEPS = [
    ("provisional_status", "Has a provisional YES/NO status"),
    ("original_text", "Original text saved in the project"),
    ("clause_inventory", "Complete inventory of the order's operative clauses"),
    ("ending_or_current_basis", "When and how it ended (NO), or what keeps it operating now (YES)"),
    ("savings_residuals", "Savings clauses and surviving effects closed"),
    ("counterevidence", "Search for later contrary sources recorded, no open conflicts"),
    ("shared_sources", "Every shared legal source it cites has been retrieved"),
    ("opus_media", "Opus evidence images matched to this order (Opus cases only)"),
]
STEP_NAMES = [s for s, _ in STEPS]

# Which step each claim_gate error belongs to.
GATE_ERROR_STEP = [
    ("original_representation", "original_text"),
    ("operative_clauses_empty", "clause_inventory"),
    ("_scope_id", "clause_inventory"),
    ("_original_text_or_source", "clause_inventory"),
    ("_state", "clause_inventory"),
    ("_later_event", "clause_inventory"),
    ("_not_object", "clause_inventory"),
    ("_current_predicate", "ending_or_current_basis"),
    ("_first_end", "ending_or_current_basis"),
    ("whole_order", "ending_or_current_basis"),
    ("continuing_clause", "ending_or_current_basis"),
    ("savings_residuals", "savings_residuals"),
    ("bounded_later_search", "counterevidence"),
]

P = {
    "universe": "research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv",
    "decided": "research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv",
    "causal": "research/stage19/output/CAUSAL_QUEUE.csv",
    "crosswalk": "research/stage21/sources_index/OFFICIAL_SOURCE_CASE_CROSSWALK.csv",
    "custody": "research/stage21/original_sources/CASE_ORIGINAL_SOURCE_CUSTODY.csv",
    "shared": "research/stage20/output/SHARED_SOURCE_CASE_REVIEW_QUEUE.csv",
    "statute": "research/stage20/output/STATUTE_CASE_REVIEW_QUEUE.csv",
    "media": "research/stage20/output/MEDIA_BATCH_ASSOCIATION_AUDIT.csv",
    "claims": "research/readiness/claims/*.jsonl",
    "exhausted": "research/readiness/EXHAUSTED.jsonl",
    "claim_gate_dir": "research/stage19/code",
}

# Outputs of the other jobs. Each is optional: when a job has not run yet, the
# tracker falls back to the older evidence above and says so in SUMMARY.json.
J = {
    "fr_fragments": ["jobs/fr-originals/data/full_run/FRAGMENTS.jsonl", "jobs/fr-originals/output/FRAGMENTS.jsonl"],
    "opus_fragments": ["jobs/opus-media-match/output/FRAGMENTS.jsonl"],
    "opus_status": "jobs/opus-media-match/output/OPUS_CASE_MEDIA_STATUS.csv",
    "ladder_sources": ["jobs/source-ladder/output/SOURCES.jsonl"],
    "checker": "jobs/claim-checker/output/PER_CLAIM.json",
}

# Opus media blockers, from opus-media-match's media_gap / media_status.
OPUS_GAP_BLOCKER = {
    "cited_files_not_packaged": "OPUS_MEDIA_REFETCH_NEEDED",
    "originals_not_in_companion": "OPUS_MEDIA_ORIGINAL_NOT_KEPT",
    "none_cited": "OPUS_MEDIA_NONE_CITED",
}


def read_csv(root, key):
    path = os.path.join(root, P[key])
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def read_jsonl(paths):
    rows, problems = [], []
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            for n, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    problems.append(f"{os.path.basename(path)} line {n}: {exc.msg}")
    return rows, problems


def step_for_gate_error(error):
    for fragment, step in GATE_ERROR_STEP:
        if fragment in error:
            return step
    return None


def load_exhausted(root):
    """Steps recorded as searched to the end, per order: {id: {step: record}}."""
    path = os.path.join(root, P["exhausted"])
    rows, problems = read_jsonl([path]) if os.path.exists(path) else ([], [])
    out = collections.defaultdict(dict)
    for r in rows:
        i, step = r.get("instrument_id"), r.get("step")
        searched = r.get("searched")
        if step not in STEP_NAMES or not isinstance(i, str):
            problems.append(f"EXHAUSTED.jsonl: bad instrument_id/step in {json.dumps(r)[:120]}")
        elif not isinstance(searched, list) or not searched or not r.get("recorded_by") or not r.get("recorded_on"):
            problems.append(f"EXHAUSTED.jsonl: {i} {step} needs a non-empty 'searched' list, 'recorded_by' and 'recorded_on'")
        else:
            out[i][step] = r
    return out, problems


def load_job_outputs(root):
    """Read the other jobs' committed outputs; missing ones are reported, not fatal."""
    used, problems = {}, []

    def existing(paths):
        return [os.path.join(root, p) for p in paths if os.path.exists(os.path.join(root, p))]

    fr = {}
    paths = existing(J["fr_fragments"])
    rows, more = read_jsonl(paths)
    problems += more
    for r in rows:  # later files win: output/ is the newest cumulative copy
        if r.get("kind") == "original_representation" and isinstance(r.get("instrument_id"), str):
            fr[r["instrument_id"]] = r.get("data") or {}
    used["fr-originals"] = len(fr) if paths else None

    paths = existing(J["opus_fragments"])
    rows, more = read_jsonl(paths)
    problems += more
    opus_text = {r["instrument_id"] for r in rows
                 if r.get("kind") == "original_representation" and isinstance(r.get("instrument_id"), str)}
    used["opus-media-match fragments"] = len(opus_text) if paths else None

    status_path = os.path.join(root, J["opus_status"])
    opus_status = None
    if os.path.exists(status_path):
        with open(status_path, encoding="utf-8", newline="") as fh:
            opus_status = {r["instrument_id"]: r for r in csv.DictReader(fh)}
    used["opus-media-match status"] = len(opus_status) if opus_status is not None else None

    paths = existing(J["ladder_sources"])
    rows, more = read_jsonl(paths)
    problems += more
    ladder_found = {r["wanted_id"] for r in rows if r.get("wanted_id") and r.get("sha256")}
    used["source-ladder"] = len(ladder_found) if paths else None

    checker_path = os.path.join(root, J["checker"])
    checker = None
    if os.path.exists(checker_path):
        try:
            with open(checker_path, encoding="utf-8") as fh:
                checker = json.load(fh).get("by_instrument") or {}
        except (json.JSONDecodeError, AttributeError) as exc:
            problems.append(f"claim-checker PER_CLAIM.json unreadable: {exc}")
            checker = {}
    used["claim-checker"] = len(checker) if checker is not None else None
    return {"fr": fr, "opus_text": opus_text, "opus_status": opus_status, "ladder_found": ladder_found,
            "checker": checker, "used": used}, problems


def build(root):
    sys.path.insert(0, os.path.join(root, P["claim_gate_dir"]))
    import claim_gate  # the project's own structural gate

    jobs, job_problems = load_job_outputs(root)

    universe = [r["id"] for r in read_csv(root, "universe") if r["included_in_bibliography"] == "1"]
    decided = {r["instrument_id"]: r for r in read_csv(root, "decided")}
    causal = {r["instrument_id"]: r for r in read_csv(root, "causal")}
    crosswalk = {r["instrument_id"]: r for r in read_csv(root, "crosswalk")}
    custody = {r["instrument_id"]: r for r in read_csv(root, "custody")}

    statute_ok = {(r["source_key"], r["instrument_id"]) for r in read_csv(root, "statute") if r["acquired_pdf_bytes"] == "yes"}
    shared_missing = collections.defaultdict(list)  # order -> authorities not yet retrieved
    for r in read_csv(root, "shared"):
        retrieved = (r["source_already_retrieved"] == "yes" or (r["authority"], r["cited_in"]) in statute_ok
                     or r["authority"] in jobs["ladder_found"])
        if not retrieved:
            shared_missing[r["cited_in"]].append(r["authority"])
    shared_cited = {r["cited_in"] for r in read_csv(root, "shared")}

    media_linked = set()
    for r in read_csv(root, "media"):
        if r["association_grade"] not in ("no_case_specific_evidence", ""):
            media_linked.update(x.strip() for x in r["example_case_ids"].split("|") if x.strip())

    claim_rows, problems = read_jsonl(sorted(glob.glob(os.path.join(root, P["claims"]))))
    claims = {}
    for c in claim_rows:
        i = c.get("instrument_id")
        if isinstance(i, str):
            claims[i] = c  # later files and lines win
    exhausted, more = load_exhausted(root)
    problems += more + job_problems

    orders = []
    for i in universe:
        d = decided.get(i)
        status = d["provisional_substantive_status"] if d else None
        steps, blockers = {}, collections.defaultdict(list)
        claim = claims.get(i)
        gate_errors = claim_gate.validate_claim(claim, expected_status=status) if claim else None
        claim_steps_failing = {step_for_gate_error(e) for e in gate_errors or []}
        if "operative_clauses_empty" in (gate_errors or []):
            # The gate stops at an empty clause list without checking the ending,
            # savings or later search, so none of those can count.
            claim_steps_failing |= {"clause_inventory", "ending_or_current_basis", "savings_residuals", "counterevidence"}

        # A claim step counts only when the gate passes it AND claim-checker has
        # passed that step for this exact version of the claim.
        check = (jobs["checker"] or {}).get(i) if claim else None
        checked_current = bool(check) and check.get("claim_sha256") == claim_gate.claim_sha(claim)

        def from_claim(step):
            if claim is None or step in claim_steps_failing:
                return False
            return checked_current and bool((check.get("steps_checker_passed") or {}).get(step))

        def claim_blocker(step, default_code):
            if claim is None:
                return default_code
            if step in claim_steps_failing:
                return f"CLAIM_INCOMPLETE:{step}"
            return f"CLAIM_CHECK_FAILED:{step}" if checked_current else "CLAIM_NOT_YET_CHECKED"

        # 1. provisional status
        steps["provisional_status"] = status in ("yes", "no")
        if not steps["provisional_status"]:
            blockers["provisional_status"].append("NO_PROVISIONAL_STATUS")

        # 2. original text
        cq, cx, cu = causal.get(i, {}), crosswalk.get(i, {}), custody.get(i, {})
        fr = jobs["fr"].get(i)
        saved = (cq.get("locally_preserved_primary_representation") == "1"
                 or cu.get("custody_state", "").startswith("PDF_BYTES_CAPTURED")
                 or (fr is not None and fr.get("needs_page_check") is False)
                 or i in jobs["opus_text"])
        steps["original_text"] = saved or from_claim("original_text")
        if not steps["original_text"]:
            if fr is not None:
                blockers["original_text"].append("ORIGINAL_FOUND_NEEDS_PAGE_CHECK")
            elif cx.get("selected_literal_URL"):
                blockers["original_text"].append("OFFICIAL_URL_KNOWN_NOT_DOWNLOADED")
            else:
                blockers["original_text"].append("NO_OFFICIAL_SOURCE_LOCATED")

        # 3-6. need a claim (partial claims light up the steps they satisfy)
        for step, code in (
            ("clause_inventory", "NO_CLAUSE_INVENTORY"),
            ("ending_or_current_basis", "CURRENT_BASIS_UNPROVED" if status == "yes" else "FIRST_END_UNPROVED"),
            ("savings_residuals", "SAVINGS_RESIDUALS_NOT_CLOSED"),
            ("counterevidence", "LATER_SOURCE_SEARCH_NOT_RECORDED"),
        ):
            steps[step] = from_claim(step)
            if not steps[step] and status:  # unresearched orders are blocked by status alone
                blockers[step].append(claim_blocker(step, code))
        if int(cq.get("quarantined_relationship_count") or 0):
            steps["counterevidence"] = False
            blockers["counterevidence"].append("QUARANTINED_RELATIONSHIP_CONFLICT")

        # 7. shared sources (only orders that cite one)
        if i in shared_cited:
            steps["shared_sources"] = not shared_missing.get(i)
            for a in shared_missing.get(i, []):
                blockers["shared_sources"].append(f"SHARED_SOURCE_NOT_RETRIEVED:{a}")

        # 8. Opus media (Opus cases only)
        if d and d["decision_origin"].startswith("opus"):
            if jobs["opus_status"] is None:  # opus-media-match has not run: older audit
                steps["opus_media"] = i in media_linked
                if not steps["opus_media"]:
                    blockers["opus_media"].append("OPUS_MEDIA_NOT_MATCHED_TO_ORDER")
            else:
                # Done only when every medium the Opus records cite is resolved.
                ms = jobs["opus_status"].get(i) or {}
                steps["opus_media"] = ms.get("all_cited_media_resolved") == "yes"
                if not steps["opus_media"]:
                    gap = ms.get("media_gap", "")
                    if gap in OPUS_GAP_BLOCKER:
                        blockers["opus_media"].append(OPUS_GAP_BLOCKER[gap])
                    elif ms.get("media_status") == "ambiguous_only":
                        blockers["opus_media"].append("OPUS_MEDIA_MATCH_AMBIGUOUS")
                    elif ms.get("media_status") == "unique_supported":
                        blockers["opus_media"].append("OPUS_MEDIA_PARTLY_RESOLVED")
                    else:
                        blockers["opus_media"].append("OPUS_MEDIA_NOT_MATCHED_TO_ORDER")

        # Exhausted steps count as machine-finished.
        exhausted_steps = []
        for step, rec in exhausted.get(i, {}).items():
            if step in steps and not steps[step]:
                steps[step] = True
                blockers.pop(step, None)
                exhausted_steps.append(step)

        claim_level = [e for e in gate_errors or [] if step_for_gate_error(e) is None]
        complete_claim = claim is not None and not gate_errors
        # An exhausted step may leave its gap listed in the claim; nothing else may fail.
        exhausted_ok = bool(exhausted_steps) and set(claim_level) <= {"unresolved_material_gaps"}
        ready = all(steps.values()) and (complete_claim or exhausted_ok)
        orders.append({
            "instrument_id": i,
            "provisional_status": status or "",
            "decision_origin": d["decision_origin"] if d else "",
            "steps_applicable": len(steps),
            "steps_done": sum(steps.values()),
            "ready_for_human_review": "yes" if ready else "no",
            "ready_tier": ("complete_claim" if complete_claim else "machine_exhausted") if ready else "",
            "exhausted_steps": "|".join(exhausted_steps),
            "claim_present": "yes" if claim else "no",
            "claim_record_errors": "|".join(claim_level),
            "blockers": "|".join(b for s in STEP_NAMES for b in blockers.get(s, [])),
            **{f"step_{s}": ("done" if steps[s] else "open") if s in steps else "n/a" for s in STEP_NAMES},
        })
    build.job_outputs_used = jobs["used"]
    return orders, problems


def summarise(orders, problems):
    total = len(orders)
    decided = [o for o in orders if o["provisional_status"]]
    ready = [o for o in orders if o["ready_for_human_review"] == "yes"]

    blocker_orders = collections.Counter()  # all orders
    blocker_decided = collections.Counter()  # orders with a provisional status
    shared = collections.Counter()
    for o in orders:
        seen = set()
        for b in o["blockers"].split("|") if o["blockers"] else []:
            code = b.split(":", 1)[0]
            if code not in seen:
                blocker_orders[code] += 1
                blocker_decided[code] += bool(o["provisional_status"])
                seen.add(code)
            if code == "SHARED_SOURCE_NOT_RETRIEVED":
                shared[b.split(":", 1)[1]] += 1

    step_done = {s: sum(o[f"step_{s}"] == "done" for o in decided) for s in STEP_NAMES}
    step_applicable = {s: sum(o[f"step_{s}"] != "n/a" for o in decided) for s in STEP_NAMES}
    ladder = collections.Counter((o["steps_done"], o["steps_applicable"]) for o in decided)

    # Actions that clear one blocker for many orders at once.
    unlocks = [
        {"action": "Run one bulk download of the official links already found (Stage 21 crosswalk)",
         "kind": "machine_job", "orders_unblocked": blocker_orders["OFFICIAL_URL_KNOWN_NOT_DOWNLOADED"], "blocker": "OFFICIAL_URL_KNOWN_NOT_DOWNLOADED"},
        {"action": "Match the 496 Opus evidence images to orders by their contents (opus-media-match)",
         "kind": "machine_job", "orders_unblocked": blocker_orders["OPUS_MEDIA_NOT_MATCHED_TO_ORDER"], "blocker": "OPUS_MEDIA_NOT_MATCHED_TO_ORDER"},
        {"action": "Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl",
         "kind": "machine_job", "orders_unblocked": blocker_orders["OPUS_MEDIA_REFETCH_NEEDED"], "blocker": "OPUS_MEDIA_REFETCH_NEEDED"},
        {"action": "Check the page location of fr-originals finds marked medium/low confidence",
         "kind": "agent_check", "orders_unblocked": blocker_orders["ORIGINAL_FOUND_NEEDS_PAGE_CHECK"], "blocker": "ORIGINAL_FOUND_NEEDS_PAGE_CHECK"},
        {"action": "Settle ambiguous Opus media matches (MATCHES.csv rows graded ambiguous)",
         "kind": "agent_check", "orders_unblocked": blocker_orders["OPUS_MEDIA_MATCH_AMBIGUOUS"], "blocker": "OPUS_MEDIA_MATCH_AMBIGUOUS"},
        {"action": "Run claim-checker on the newest claims (it reruns on every claims change and daily)",
         "kind": "machine_job", "orders_unblocked": blocker_orders["CLAIM_NOT_YET_CHECKED"], "blocker": "CLAIM_NOT_YET_CHECKED"},
    ] + [
        {"action": f"Retrieve shared source {a}", "kind": "one_source", "orders_unblocked": n, "blocker": f"SHARED_SOURCE_NOT_RETRIEVED:{a}"}
        for a, n in shared.most_common()
    ]
    unlocks = sorted((u for u in unlocks if u["orders_unblocked"]), key=lambda u: -u["orders_unblocked"])

    return {
        "orders_total": total,
        "orders_with_provisional_status": len(decided),
        "ready_for_human_review": len(ready),
        "ready_by_tier": dict(collections.Counter(o["ready_tier"] for o in ready)),
        "human_verified": "not counted here; see the Stage 19 tracker",
        "step_done_among_decided": {s: {"done": step_done[s], "applicable": step_applicable[s]} for s in STEP_NAMES},
        "decided_by_steps_done": {f"{k[0]}/{k[1]}": v for k, v in sorted(ladder.items())},
        "orders_blocked_by": dict(blocker_orders.most_common()),
        "decided_orders_blocked_by": dict(blocker_decided.most_common()),
        "shared_unlocks": unlocks,
        "input_problems": problems,
    }


def pct(n, d):
    return f"{100 * n / d:.1f}%" if d else "n/a"


def write_outputs(out, orders, summary, inputs):
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "READINESS_BY_ORDER.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(orders[0]))
        w.writeheader()
        w.writerows(orders)
    with open(os.path.join(out, "SHARED_UNLOCKS.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["orders_unblocked", "kind", "action", "blocker"])
        w.writeheader()
        w.writerows(summary["shared_unlocks"])
    summary = {**summary, "inputs": inputs}
    with open(os.path.join(out, "SUMMARY.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
        fh.write("\n")

    s, total, dec = summary, summary["orders_total"], summary["orders_with_provisional_status"]
    lines = [
        "# Readiness tracker",
        "",
        f"**Ready for human review: {s['ready_for_human_review']:,} of {total:,} orders ({pct(s['ready_for_human_review'], total)})**",
        "",
        "An order is ready when the machines have finished every step it needs: each step is backed by a saved",
        "source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in",
        "`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.",
        "",
        f"Orders with a provisional YES/NO status: {dec:,}. The other {total - dec:,} have not been researched yet.",
        "",
        "## Steps finished (orders with a provisional status)",
        "",
        "| Step | Done | Of | Share |",
        "|---|---:|---:|---:|",
    ]
    for name, label in STEPS:
        st = s["step_done_among_decided"][name]
        lines.append(f"| {label} | {st['done']:,} | {st['applicable']:,} | {pct(st['done'], st['applicable'])} |")
    lines += ["", "## Do these first: one action, many orders", "",
              "| Orders unblocked | Kind | Action |", "|---:|---|---|"]
    for u in s["shared_unlocks"][:25]:
        lines.append(f"| {u['orders_unblocked']:,} | {u['kind'].replace('_', ' ')} | {u['action']} |")
    if len(s["shared_unlocks"]) > 25:
        lines.append(f"| | | ...and {len(s['shared_unlocks']) - 25} more in `SHARED_UNLOCKS.csv` |")
    lines += ["", "## What blocks orders", "", "| Blocker | Orders with a status | All orders |", "|---|---:|---:|"]
    for code, n in s["orders_blocked_by"].items():
        lines.append(f"| `{code}` | {s['decided_orders_blocked_by'].get(code, 0):,} | {n:,} |")
    lines += ["", "## How to move an order forward", "",
              "- Add or extend its claim in `research/readiness/claims/*.jsonl` (format: `research/stage19/CLAIM_SCHEMA.md`).",
              "  Partial claims count: each step lights up once its part passes the gate and claim-checker.",
              "- Start from the order's draft in `jobs/claim-drafts/output/` (see `jobs/claim-drafts/AGENT_GUIDE.md`).",
              "- Need a source? Add it to `research/readiness/FETCH_QUEUE.jsonl`; source-ladder fetches it.",
              "- If a step cannot be finished by machine, add a line to `research/readiness/EXHAUSTED.jsonl` with",
              "  `instrument_id`, `step`, `searched` (list of repositories and queries), `recorded_by`, `recorded_on`.",
              f"- Step names: {', '.join(f'`{n}`' for n in STEP_NAMES)}.",
              "- Per-order detail is in `READINESS_BY_ORDER.csv`."]
    used = inputs.get("job_outputs_used", {})
    if used:
        lines += ["", "## Job outputs read", ""] + [
            f"- {job}: {'not run yet' if n is None else f'{n:,}'}" for job, n in used.items()]
    if s["input_problems"]:
        lines += ["", "## Input problems", ""] + [f"- {p}" for p in s["input_problems"]]
    with open(os.path.join(out, "TRACKER.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    root, out = os.environ.get("REPO_ROOT", "."), os.environ.get("OUTPUT_DIR", "readiness-output")
    orders, problems = build(root)
    summary = summarise(orders, problems)
    inputs = {k: v for k, v in P.items() if k != "claim_gate_dir"}
    inputs["job_outputs"] = {k: (v if isinstance(v, str) else " + ".join(v)) for k, v in J.items()}
    # How many orders (or authorities) each job's output supplied; null = that job has not run yet.
    inputs["job_outputs_used"] = getattr(build, "job_outputs_used", {})
    write_outputs(out, orders, summary, inputs)
    print(open(os.path.join(out, "TRACKER.md"), encoding="utf-8").read())


if __name__ == "__main__":
    main()
