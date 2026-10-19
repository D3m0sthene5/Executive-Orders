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
import hashlib
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
    # Official government printings of the orders' texts (GPO / Office of the Federal Register compilations).
    # They count under the same rule as fr-originals: only a find the job did not flag needs_page_check.
    "official_compilation_fragments": ["jobs/ofr-compilations/output/FRAGMENTS.jsonl",
                                       "jobs/isthmian-canal-1911/output/FRAGMENTS.jsonl",
                                       "jobs/indian-reservations-1912/output/FRAGMENTS.jsonl"],
    # Richardson's Messages and Papers: a printed compilation transcribed from records and newspapers, not the
    # signed or officially printed original. A lead only; it never counts as the original text.
    "compiled_transcription_fragments": ["jobs/richardson-volumes/output/FRAGMENTS.jsonl"],
    "opus_status": "jobs/opus-media-match/output/OPUS_CASE_MEDIA_STATUS.csv",
    "opus_refetch": "jobs/opus-media-match/output/REFETCH_LIST.jsonl",
    "ladder_sources": ["jobs/source-ladder/output/SOURCES.jsonl"],
    "checker": "jobs/claim-checker/output/PER_CLAIM.json",
    # The bounded later-source searches the machines run over every order.
    "le_summary": "jobs/later-events/output/SUMMARY.json",
    "le_catalog": "jobs/later-events/output/CATALOG_INDEX.csv",
    "le_conflicts": "jobs/later-events/output/COUNTEREVIDENCE_LEADS.csv",
    "le_status": "jobs/later-events/output/STATUS.json",
    "cl_summary": "jobs/current-law/output/SUMMARY.json",
    "cl_conflicts": "jobs/current-law/output/POSSIBLE_CONFLICTS.csv",
    "cl_status": "jobs/current-law/output/STATUS.json",
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

    # Official compilations: {id: [data, ...]} (an order may be printed more than once).
    official = collections.defaultdict(list)
    for rel in J["official_compilation_fragments"]:
        job = rel.split("/")[1]
        paths = existing([rel])
        rows, more = read_jsonl(paths)
        problems += more
        ids = set()
        for r in rows:
            if r.get("kind") == "original_representation" and isinstance(r.get("instrument_id"), str):
                official[r["instrument_id"]].append(r.get("data") if isinstance(r.get("data"), dict) else {})
                ids.add(r["instrument_id"])
        used[job] = len(ids) if paths else None
    transcription = set()
    for rel in J["compiled_transcription_fragments"]:
        job = rel.split("/")[1]
        paths = existing([rel])
        rows, more = read_jsonl(paths)
        problems += more
        ids = {r["instrument_id"] for r in rows
               if r.get("kind") == "original_representation" and isinstance(r.get("instrument_id"), str)}
        transcription |= ids
        used[f"{job} (lead only, never counted as the original)"] = len(ids) if paths else None

    status_path = os.path.join(root, J["opus_status"])
    opus_status = None
    if os.path.exists(status_path):
        with open(status_path, encoding="utf-8", newline="") as fh:
            opus_status = {r["instrument_id"]: r for r in csv.DictReader(fh)}
    used["opus-media-match status"] = len(opus_status) if opus_status is not None else None

    paths = existing(J["ladder_sources"])
    rows, more = read_jsonl(paths)
    problems += more
    # A re-fetch counts only when its bytes match the hash Opus recorded (if it recorded one).
    ladder_found = {r["wanted_id"] for r in rows if r.get("wanted_id") and r.get("sha256")
                    and r.get("matches_expected_sha256") is not False}
    used["source-ladder"] = len(ladder_found) if paths else None

    # Opus originals still missing per order, from opus-media-match's re-fetch list.
    refetch_path = os.path.join(root, J["opus_refetch"])
    opus_missing = collections.defaultdict(set)
    if os.path.exists(refetch_path):
        rows, more = read_jsonl([refetch_path])
        problems += more
        for r in rows:
            for i in r.get("instrument_ids") or []:
                # same key as source-ladder's work item: the expected sha256, else the URL
                opus_missing[i].add("opus-refetch:" + (r.get("expected_sha256") or r.get("url") or ""))

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
    search = load_machine_search(root, problems)
    used["machine later-source search"] = len(search["catalog"]) if search["complete"] else None
    return {"fr": fr, "opus_text": opus_text, "official": official, "transcription": transcription,
            "opus_status": opus_status, "ladder_found": ladder_found,
            "opus_missing": opus_missing, "search": search,
            "checker": checker, "used": used}, problems


def load_machine_search(root, problems):
    """Which orders the machines' later-source searches fully covered, and which they flagged.

    complete only when later-events read the whole OFR catalog and scanned the saved texts,
    and current-law scanned the whole U.S. Code and eCFR (not a sample)."""
    def js(key):
        try:
            with open(os.path.join(root, J[key]), encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return {}

    def ids(key):
        path = os.path.join(root, J[key])
        if not os.path.exists(path):
            return set()
        with open(path, encoding="utf-8", newline="") as fh:
            return {r["instrument_id"] for r in csv.DictReader(fh) if r.get("instrument_id")}

    le, cl = js("le_summary"), js("cl_summary")
    catalog = set()
    path = os.path.join(root, J["le_catalog"])
    if os.path.exists(path):
        with open(path, encoding="utf-8", newline="") as fh:
            catalog = {r["id"] for r in csv.DictReader(fh) if r.get("id") and r.get("post_cutoff") != "yes"}
    complete = (le.get("catalog_complete") is True and le.get("job_limit") is None
                and (le.get("text_documents_scanned") or 0) > 0
                and cl.get("sample_mode") is False and cl.get("job_limit") is None and bool(catalog))
    if catalog and not complete:
        problems.append("machine later-source search incomplete (later-events or current-law ran a sample); "
                        "the counterevidence step is not counted from it")
    dates = {k: (js(k).get("finished_utc") or "")[:10] for k in ("le_status", "cl_status")}
    return {"complete": complete, "catalog": catalog, "conflicts_le": ids("le_conflicts"),
            "conflicts_cl": ids("cl_conflicts"), "dates": dates,
            "texts": le.get("text_documents_scanned") or 0}


def machine_search_record(i, search):
    """Claim-shaped later_source_search entries for what the machines searched for this order."""
    n = i.split(":", 1)[1]
    d_le, d_cl = search["dates"].get("le_status") or "", search["dates"].get("cl_status") or ""
    return [
        {"repository": "Office of the Federal Register executive-order catalog (federalregister.gov API v1, 1937-2026)",
         "query_or_scope": f"editorial disposition notes on EO {n} and on every other catalogued order naming it "
                           "(jobs/later-events)", "checked_on": d_le},
        {"repository": f"project saved order texts ({search['texts']:,} documents, incl. every fr-originals official text)",
         "query_or_scope": f"revocation, amendment, supersession and reinstatement sentences naming EO {n} "
                           "(jobs/later-events)", "checked_on": d_le},
        {"repository": "U.S. Code release point 119-121 and eCFR as of 2026-10-14",
         "query_or_scope": f"every mention of EO {n} in current law (jobs/current-law)", "checked_on": d_cl},
    ]


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
    # A negative source audit is an unresolved research conflict, never a human
    # review or a status change. It applies only to the exact audited claim.
    holds = load_source_audit_holds(root, claims, claim_gate, problems)
    exhausted, more = load_exhausted(root)
    problems += more + job_problems

    orders = []
    machine_searched = set()
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
        official = jobs["official"].get(i, [])
        saved = (cq.get("locally_preserved_primary_representation") == "1"
                 or cu.get("custody_state", "").startswith("PDF_BYTES_CAPTURED")
                 or (fr is not None and fr.get("needs_page_check") is False)
                 # same rule as fr-originals: a find the job itself did not flag for a page check
                 or any(o.get("needs_page_check") is False for o in official)
                 or i in jobs["opus_text"])
        steps["original_text"] = saved or from_claim("original_text")
        if not steps["original_text"]:
            if fr is not None or official:
                blockers["original_text"].append("ORIGINAL_FOUND_NEEDS_PAGE_CHECK")
            elif cx.get("selected_literal_URL"):
                blockers["original_text"].append("OFFICIAL_URL_KNOWN_NOT_DOWNLOADED")
            else:
                blockers["original_text"].append("NO_OFFICIAL_SOURCE_LOCATED")
            if i in jobs["transcription"]:
                # Only Richardson's printed transcription was found: a lead to the original, not the original.
                blockers["original_text"].append("ONLY_COMPILED_TRANSCRIPTION_FOUND")

        # 3-6. need a claim (partial claims light up the steps they satisfy)
        for step, code in (
            ("clause_inventory", "NO_CLAUSE_INVENTORY"),
            ("ending_or_current_basis", "CURRENT_BASIS_UNPROVED" if status == "yes" else "FIRST_END_UNPROVED"),
            ("savings_residuals", "SAVINGS_RESIDUALS_NOT_CLOSED"),
            ("counterevidence", "LATER_SOURCE_SEARCH_NOT_RECORDED"),
        ):
            steps[step] = from_claim(step)
            if step == "counterevidence" and not steps[step] and status:
                # The machines' bounded searches count when they covered the order and found nothing contrary.
                srch = jobs["search"]
                flagged = [name for name, ids_ in (("later-events", srch["conflicts_le"]),
                                                   ("current-law", srch["conflicts_cl"])) if i in ids_]
                if srch["complete"] and i in srch["catalog"] and not flagged:
                    steps[step] = True
                    machine_searched.add(i)
                    continue
                if flagged:
                    code = "MACHINE_SEARCH_FOUND_CONTRARY_LEAD:" + "+".join(flagged)
                elif srch["complete"]:
                    code = "NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE"
            if not steps[step] and status:  # unresearched orders are blocked by status alone
                blockers[step].append(claim_blocker(step, code))
        if int(cq.get("quarantined_relationship_count") or 0):
            steps["counterevidence"] = False
            machine_searched.discard(i)  # its search record must not claim "no open conflicts"
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
                missing = jobs["opus_missing"].get(i, set())
                refetched_all = bool(missing) and missing <= jobs["ladder_found"]
                steps["opus_media"] = ms.get("all_cited_media_resolved") == "yes" or (
                    refetched_all and str(ms.get("ambiguous_members") or "0") == "0"
                    and ms.get("media_gap") in ("cited_files_not_packaged", "originals_not_in_companion"))
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
        if i in holds:
            ready = False
            blockers['counterevidence'].append('OPEN_SOURCE_AUDIT:'+holds[i]['claim_sha256'][:12])
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
    build.machine_search = {i: machine_search_record(i, jobs["search"]) for i in sorted(machine_searched)}
    return orders, problems


def load_source_audit_holds(root, claims, gate, problems):
    """Fail closed on damaged audit evidence; a corrected claim needs a fresh audit.

    The old hold remains visible as stale when the exact claim changes. This
    function cannot approve a claim, alter any step or certify a legal finding.
    """
    from pathlib import Path
    base=Path(root).resolve()
    path=base/'research/readiness/SOURCE_AUDIT_HOLDS.jsonl'
    if not path.exists():return {}
    result={}
    for number, line in enumerate(path.read_text('utf-8').splitlines(),1):
        if not line.strip():continue
        row=json.loads(line)
        if row.get('schema')!='eo-source-audit-hold/v1' or row.get('state')!='unresolved' or not row.get('reason'):
            raise ValueError(f'invalid source-audit hold at line {number}')
        review=(base/row['review_path']).resolve()
        if not review.is_relative_to(base) or hashlib.sha256(review.read_bytes()).hexdigest()!=row['review_sha256']:
            raise ValueError(f'missing, unsafe or changed source-audit evidence at line {number}')
        iid=row['instrument_id']
        if iid not in claims or gate.claim_sha(claims[iid])!=row['claim_sha256']:
            problems.append(f'STALE_SOURCE_AUDIT_HOLD:{iid}: reconcile changed claim with {row["review_path"]}')
            continue
        result[iid]=row
    return result


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
        {"action": "Check the page location of fr-originals and official-compilation finds marked medium/low confidence",
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
    # Claim-shaped later_source_search for each order the machines' searches completed;
    # agents copy it into the order's claim (claim-drafts and case-bundles can merge it).
    with open(os.path.join(out, "MACHINE_LATER_SEARCH.jsonl"), "w", encoding="utf-8", newline="\n") as fh:
        for i, rec in getattr(build, "machine_search", {}).items():
            fh.write(json.dumps({"instrument_id": i, "later_source_search": rec, "open_conflicts": [],
                                 "produced_by": "readiness-tracker"}, sort_keys=True) + "\n")
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
    candidate = s.get("historical_census_candidates_OUTSIDE_DENOMINATOR")
    if candidate:
        lines += ["", "## Historical census candidates — separate from the 14,972 working identities", "",
          f"- Distinct LOC catalog item candidates: {candidate['distinct_LOC_item_ID_candidates']:,} (not yet admitted).",
          f"- LOC item transcripts obtained: {candidate['LOC_transcribed_items']:,}.",
          f"- LOC items with retained original-page images: {candidate['LOC_items_with_original_page_images']:,}.",
          f"- Lord indexed date-row appearances awaiting identity authentication: {candidate['Lord_index_appearances_UNAUTHENTICATED']:,}, including {candidate['Lord_19c_gap_appearances']:,} nineteenth-century gap leads.",
          "**Newly admitted EOs: 0.** Catalog data and manuscripts need independent signer, authority, duplicate and legal inclusion review.",
          "See jobs/census-candidates/output/CENSUS_READINESS.md and ITEM_CANDIDATES.csv."]
    if s["input_problems"]:
        lines += ["", "## Input problems", ""] + [f"- {p}" for p in s["input_problems"]]
    with open(os.path.join(out, "TRACKER.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    root, out = os.environ.get("REPO_ROOT", "."), os.environ.get("OUTPUT_DIR", "readiness-output")
    orders, problems = build(root)
    summary = summarise(orders, problems)
    # The early rangers survey potential *new* identities outside the existing
    # 14,972 working bibliography. They must NEVER be added to order metrics.
    census_file = os.path.join(root, "jobs/census-candidates/output/SUMMARY.json")
    if os.path.isfile(census_file):
        with open(census_file, encoding="utf-8") as f:
            candidate_metrics = json.load(f)
        summary["historical_census_candidates_OUTSIDE_DENOMINATOR"] = {
            "distinct_LOC_item_ID_candidates": candidate_metrics["distinct_LOC_item_ID_candidates"],
            "LOC_transcribed_items": candidate_metrics["items_with_LOC_XML_transcript"],
            "LOC_items_with_original_page_images": candidate_metrics["items_with_saved_original_pages"],
            "Lord_index_appearances_UNAUTHENTICATED": candidate_metrics["Lord_index_appearances_UNAUTHENTICATED"],
            "Lord_19c_gap_appearances": candidate_metrics["Lord_19c_gap_rows"],
            "newly_admitted_EOs": candidate_metrics["newly_admitted_EOs"],
            "separate_from_14972_census": True
        }

    inputs = {k: v for k, v in P.items() if k != "claim_gate_dir"}
    inputs["job_outputs"] = {k: (v if isinstance(v, str) else " + ".join(v)) for k, v in J.items()}
    # How many orders (or authorities) each job's output supplied; null = that job has not run yet.
    inputs["job_outputs_used"] = getattr(build, "job_outputs_used", {})
    write_outputs(out, orders, summary, inputs)
    print(open(os.path.join(out, "TRACKER.md"), encoding="utf-8").read())


if __name__ == "__main__":
    main()
