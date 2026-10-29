"""Join Lewis routes to the existing Panizzi queue/results; never enqueue or fetch.

Only exact target/step/citation requests without conflicting edition constraints
are joined. Published retrieval records remain leads awaiting page and custody
review. Missing result rows never mean unattempted or exhausted.
"""
from __future__ import annotations
import collections
import csv
import hashlib
import io
import json
import re
from pathlib import Path

QUEUE = "research/readiness/FETCH_QUEUE.jsonl"
RESULTS = "jobs/source-ladder/output/RESULTS.csv"
SOURCES = "jobs/source-ladder/output/SOURCES.jsonl"
MAX_INPUT = 32_000_000


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def key(row, iid=None):
    identity = iid or row.get("instrument_id")
    step = {"original_page_check": "original_text"}.get(row.get("step"), row.get("step") or "original_text")
    cite = row.get("citation")
    if not isinstance(identity, str) or not re.fullmatch(r"EO:\d+[A-Z]?", identity) or not isinstance(cite, str) or not cite.strip():
        return None
    # Lewis's original-source requests have no edition/date qualification.
    # A qualified queue item must not suppress an undated request.
    if any(row.get(k) not in (None, "") for k in ("as_of", "required_date", "edition_year")):
        return None
    return identity, step, " ".join(cite.upper().split())


def annotate(proposals, queue, results, sources, queue_lines=None, source_lines=None):
    queued = collections.defaultdict(list)
    found = collections.defaultdict(list)
    for n, row in enumerate(queue, 1):
        k = key(row)
        if k:
            queued[k].append(queue_lines[n - 1] if queue_lines is not None else n)
    for n, row in enumerate(results, 2):
        for iid in re.split(r"\s*\|\s*", row.get("instrument_ids") or ""):
            k = key(row, iid)
            if k:
                found[k].append((n, row))
    decisions, remaining = [], []
    for proposal in proposals:
        k = key(proposal)
        if k is None:
            raise ValueError("unjoinable Lewis original-source proposal")
        matches = found.get(k, []) if k in queued else []
        refs = []
        for n, result in matches:
            receipts = []
            for line, source in enumerate(sources, 1):
                if (source.get("sha256") and source.get("sha256") == result.get("sha256")
                        and source.get("url") == result.get("url")
                        and (not source.get("wanted_id") or source["wanted_id"] == result.get("wanted_id"))):
                    receipts.append({"record": SOURCES + ":" + str(source_lines[line - 1] if source_lines is not None else line), "sha256": source["sha256"],
                                     "url": source.get("url"), "text_path": source.get("text_path"),
                                     "cache_path": source.get("cache_path"), "page_or_item": source.get("page_or_item"),
                                     "custody": "record_only_not_rehashed_by_Lewis"})
            refs.append({"record": RESULTS + "#data-record=" + str(n - 1), "result": result.get("result"),
                         "why": result.get("why"), "sources": receipts})
        states = {r.get("result") for _, r in matches}
        if k not in queued:
            state, action, owner = "not_queued", "Enqueue the filtered PROPOSED_FETCH_REQUESTS.jsonl through request_contract.py", "machine_job"
            remaining.append(proposal)
        elif not matches:
            state, action, owner = "queued_result_not_published", "Already queued; inspect Panizzi's next bounded plan. No matching published result establishes what was attempted.", "machine_job"
        elif len(states) > 1:
            state, action, owner = "published_results_conflict", "Inspect all matching result versions and source receipts; do not infer a current success or requeue automatically.", "agent_check"
        elif states == {"found"}:
            state = "retrieval_recorded_needs_review" if any(r["sources"] for r in refs) else "found_record_needs_revalidation"
            action, owner = "Open the linked source receipt/text; verify target pages, identity and current byte custody before using it.", "agent_check"
        else:
            state = "queued_" + str(next(iter(states)))
            action, owner = "Preserve the published failure/deferment reason; inspect the existing acquisition task without duplicate enqueueing.", "machine_job"
        decisions.append({"instrument_id": proposal["instrument_id"], "citation": proposal["citation"],
                          "route_status": state, "next_action": action, "action_owner": owner,
                          "queue_records": [QUEUE + ":" + str(n) for n in queued.get(k, [])], "result_records": refs})
    return decisions, remaining


def read(path):
    if not path.is_file():
        return b""
    if path.stat().st_size > MAX_INPUT:
        raise ValueError("input byte bound exceeded: " + str(path))
    return path.read_bytes()


def jsonlines(raw):
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    if not all(isinstance(r, dict) for r in rows):
        raise ValueError("non-object JSONL input")
    return rows


def refresh(repo, out, write_report):
    repo, out = Path(repo), Path(out)
    proposal_path = out / "PROPOSED_FETCH_REQUESTS.jsonl"
    raw = read(proposal_path)
    all_path = out / "ALL_FETCH_PROPOSALS.jsonl"
    prior = out / "HANDOFF_AUDIT.json"
    if prior.is_file():
        previous = json.loads(read(prior))
        if digest(raw) == previous.get("remaining_sha256") and digest(read(all_path)) == previous.get("all_sha256"):
            raw = read(all_path)  # idempotent refresh of the same generated routes
    inputs = {p: read(repo / p) for p in (QUEUE, RESULTS, SOURCES)}
    # A missing queue cannot prove that requests have not been queued.
    if not inputs[QUEUE]:
        raise ValueError("queue unavailable/empty; refusing to invent unqueued requests")
    results = list(csv.DictReader(io.StringIO(inputs[RESULTS].decode("utf-8"))))
    decisions, remaining = annotate(jsonlines(raw), jsonlines(inputs[QUEUE]), results, jsonlines(inputs[SOURCES]),
        queue_lines=[n for n, line in enumerate(inputs[QUEUE].splitlines(), 1) if line.strip()],
        source_lines=[n for n, line in enumerate(inputs[SOURCES].splitlines(), 1) if line.strip()])
    all_path.write_bytes(raw)
    kept = "".join(json.dumps(r, sort_keys=True) + "\n" for r in remaining).encode()
    proposal_path.write_bytes(kept)
    routes = list(csv.DictReader(io.StringIO(read(out / "ROUTES.csv").decode("utf-8"))))
    by_id = {r["instrument_id"]: r for r in decisions}
    for row in routes:
        item = by_id.get(row["instrument_id"])
        row["handoff_records"] = ""
        if item and row.get("best_route") == "federal_register":
            row.update({k: item[k] for k in ("route_status", "next_action", "action_owner")})
            row["handoff_records"] = json.dumps({"queue": item["queue_records"], "results": item["result_records"]}, sort_keys=True)
    if routes:
        with (out / "ROUTES.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(routes[0]))
            writer.writeheader(); writer.writerows(routes)
    summary = json.loads(read(out / "SUMMARY.json"))
    counts = dict(collections.Counter(r["route_status"] for r in decisions))
    summary["handoff"] = {"all_proposals": len(decisions), "unqueued_proposals": len(remaining), "states": counts}
    summary["proposed_fetch_requests"].update(count=len(remaining), contract_valid=len(remaining))
    summary["routes"] = dict(collections.Counter(r["best_route"] + ":" + r["route_status"] for r in routes))
    summary["by_owner"] = dict(collections.Counter(r["action_owner"] for r in routes))
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(out / "REPORT.md", summary, routes)
    audit = {"schema": "eo-lewis-handoff/1", "input_sha256": {p: digest(b) for p, b in inputs.items()},
             "all_sha256": digest(raw), "remaining_sha256": digest(kept), "decisions": decisions,
             "states": counts, "legal_effect": "none; retrieval records are not authenticated originals"}
    (out / "HANDOFF_AUDIT.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    return counts
