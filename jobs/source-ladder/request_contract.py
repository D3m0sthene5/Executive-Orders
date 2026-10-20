"""Append-only source-request validation shared by enqueueing and execution.

Normalizations are recorded, never written back over a historical queue line.
An unidentified ending instrument remains an unresolved task, not another fetch
of the original order. The returned task ID is independent of queue position.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

STEPS = ("original_text", "clause_inventory", "ending_or_current_basis", "savings_residuals",
         "counterevidence", "shared_sources", "opus_media")
ALIASES = {"current_basis": "ending_or_current_basis", "original_page_check": "original_text"}
VERSION = "eo-source-request/v1"
EO_ID = re.compile(r"^EO:\d{1,5}(?:-?[A-Za-z])?$")


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def _eo_number(value):
    return str(value).split(":", 1)[-1].replace("-", "").upper()


def http_url(value):
    try:
        return isinstance(value, str) and urlsplit(value).scheme in ("http", "https") and bool(urlsplit(value).hostname)
    except ValueError:
        return False


def normalize_request(raw, *, line_number=None, source="FETCH_QUEUE.jsonl"):
    """Return an audit record with original input, corrections, tasks and errors.

    Accepted legacy names have one meaning. Compound original/ending requests
    are split; a second EO is mapped only when the request identifies exactly
    one other EO. More complicated mappings remain visible and unresolved.
    """
    original = copy.deepcopy(raw)
    raw_hash = digest(raw)
    rid = (raw.get("request_id") if isinstance(raw, dict) else None) or "request:" + raw_hash
    audit = {"schema": VERSION, "request_id": rid, "source": source,
             "line_number": line_number, "original_sha256": raw_hash,
             "original_request": original, "corrections": [], "errors": [], "tasks": []}
    errors, corrections = audit["errors"], audit["corrections"]
    if not isinstance(raw, dict):
        errors.append("request must be a JSON object")
        audit["status"] = "invalid"
        return audit
    r = copy.deepcopy(raw)
    if not isinstance(rid, str) or not rid.strip():
        errors.append("request_id must be a nonempty string")
    iid = r.get("instrument_id")
    if not isinstance(iid, str) or not EO_ID.fullmatch(iid):
        errors.append("instrument_id must look like EO:1234 or EO:9132A")
    urls = r.get("urls", [])
    if urls is None:
        urls = []
    if not isinstance(urls, list) or not all(http_url(u) for u in urls):
        errors.append("urls must be a list of absolute http(s) URLs")
        urls = []
    clean_urls = list(dict.fromkeys("https://" + u[7:] if u.startswith("http://") else u for u in urls))
    if clean_urls != urls:
        corrections.append({"field": "urls", "from": urls, "to": clean_urls,
                            "reason": "HTTPS normalization and exact URL deduplication"})
    citation = r.get("citation", "") or ""
    if not isinstance(citation, str):
        errors.append("citation must be a string")
        citation = ""
    note = r.get("note", "") or ""
    if not isinstance(note, str):
        errors.append("note must be a string")
        note = ""
    if not citation and not clean_urls and isinstance(iid, str):
        # Two audited rows put an exact request for their own original in note.
        m = re.match(r"\s*Original text of EO\s*(\d{1,5}(?:-?[A-Za-z])?)\b", note, re.I)
        if m and _eo_number(m.group(1)) == _eo_number(iid):
            citation = "EO " + m.group(1).replace("-", "")
            corrections.append({"field": "citation", "from": "", "to": citation,
                                "reason": "note explicitly requests this EO's original text; step unchanged"})
    if not clean_urls and not citation.strip():
        errors.append("needs urls or a citation; source identity cannot be inferred")
    step = r.get("step") or "original_text"
    legacy_step = step
    if isinstance(step, str) and step in ALIASES:
        step = ALIASES[step]
        corrections.append({"field": "step", "from": legacy_step, "to": step,
                            "reason": "unambiguous legacy step alias; no evidence or review promoted"})
    if step not in STEPS and step != "original_and_ending_basis":
        errors.append(f"unknown step {step!r}")
    for key in ("as_of", "required_date", "edition_year"):
        value = r.get(key)
        if value in (None, ""):
            continue
        if key == "as_of" and value == "current":
            continue
        try:
            if re.fullmatch(r"\d{4}", str(value)):
                date(int(value), 1, 1)
            else:
                date.fromisoformat(str(value))
        except (ValueError, TypeError):
            errors.append(f"{key} must be a year or ISO date" + (" or current" if key == "as_of" else ""))
    if r.get("as_of") and r.get("required_date") and str(r["as_of"]) != str(r["required_date"]):
        errors.append("as_of and required_date conflict")
    if errors:
        audit["status"] = "invalid"
        return audit
    extra = {"request_id": rid, "request_sha256": raw_hash, "request_schema": VERSION,
             "original_request": original, "request_corrections": corrections, "queue_note": note}
    for key in ("as_of", "required_date", "edition_year"):
        if r.get(key) is not None:
            extra[key] = r[key]
    if legacy_step == "original_page_check":
        extra["review_requirement"] = "original_page_check remains required; fetching does not complete it"
    task = {"instrument_id": iid, "citation": citation, "urls": clean_urls, "step": step,
            "requested_by": str(r.get("requested_by") or ""), "extra": extra, "status": "valid"}
    if step == "original_and_ending_basis":
        numbers = list(dict.fromkeys(_eo_number(n) for n in re.findall(
            r"\bEO\s*(\d{1,5}(?:-?[A-Za-z])?)\b", citation + " " + note, re.I)))
        other = [n for n in numbers if n != _eo_number(iid)]
        original_task = copy.deepcopy(task)
        original_task["step"] = "original_text"
        ending_task = copy.deepcopy(task)
        ending_task["step"] = "ending_or_current_basis"
        # One precisely named later actor, without a URL referring to the original.
        if len(other) == 1 and not clean_urls:
            original_task["citation"] = "EO " + _eo_number(iid)
            ending_task["citation"] = "EO " + other[0]
            original_task["extra"]["parent_citation"] = citation
            ending_task["extra"]["parent_citation"] = citation
        else:
            ending_task.update(status="unresolved", urls=[], citation="")
            ending_task["reason"] = "ending instrument not unambiguously identified; do not refetch the original as ending evidence"
        audit["tasks"] = [original_task, ending_task]
        corrections.append({"field": "step", "from": step,
                            "to": [t["step"] for t in audit["tasks"]],
                            "reason": "separate original-source acquisition from investigation of the ending instrument"})
    else:
        audit["tasks"] = [task]
    for t in audit["tasks"]:
        t["task_id"] = rid + ":" + t["step"]
        t["extra"]["task_id"] = t["task_id"]
        t["extra"]["request_corrections"] = copy.deepcopy(corrections)
    audit["status"] = ("unresolved" if any(t["status"] == "unresolved" for t in audit["tasks"])
                       else "corrected" if corrections else "valid")
    return audit


def execution_errors(wanted):
    """Fail closed for malformed in-memory requests, including non-queue callers."""
    errors = []
    if not isinstance(wanted.wanted_id, str) or not wanted.wanted_id.strip():
        errors.append("wanted_id is required")
    if wanted.step not in STEPS:
        errors.append("unknown step " + repr(wanted.step))
    if not isinstance(wanted.instrument_ids, list) or not wanted.instrument_ids or not all(
            isinstance(i, str) and EO_ID.fullmatch(i) for i in wanted.instrument_ids):
        errors.append("instrument_ids must contain EO identities")
    if not isinstance(wanted.citation, str):
        errors.append("citation must be a string")
    if not isinstance(wanted.urls, list) or not all(http_url(u) for u in wanted.urls):
        errors.append("urls must be absolute http(s) URLs")
    if not wanted.citation and not wanted.urls:
        errors.append("needs urls or a citation")
    if (wanted.extra or {}).get("validation_status") == "unresolved":
        errors.append("source mapping remains unresolved")
    for key in ("as_of", "required_date", "edition_year"):
        value = (wanted.extra or {}).get(key)
        if value in (None, "", "current"):
            continue
        try:
            if re.fullmatch(r"\d{4}", str(value)):
                date(int(value), 1, 1)
            else:
                date.fromisoformat(str(value))
        except (ValueError, TypeError):
            errors.append(f"invalid {key}")
    return errors


def enqueue_requests(queue_path, requests):
    """Validate the entire batch before an append. Existing bytes remain intact.

    Returns all audit records. Invalid or unresolved tasks raise ValueError and
    write nothing. A task-free search request must still name its wanted source.
    """
    audits = [normalize_request(r) for r in requests]
    bad = [a for a in audits if a["status"] in ("invalid", "unresolved")]
    if bad:
        raise ValueError(json.dumps(bad, ensure_ascii=False, sort_keys=True))
    path = Path(queue_path)
    old = path.read_bytes() if path.exists() else b""
    if old and not old.endswith(b"\n"):
        raise ValueError("queue lacks a final newline; append would corrupt the last record")
    existing = set()
    for line in old.decode("utf-8").splitlines():
        try:
            existing.add(digest(json.loads(line)))
        except ValueError:
            pass  # Existing defects remain visible during execution; never rewritten here.
    additions = []
    for r in requests:
        key = digest(r)
        if key not in existing:
            additions.append(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
            existing.add(key)
    if additions:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("ab") as fh:
            fh.write("".join(additions).encode())
    return audits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "enqueue"))
    parser.add_argument("--input", required=True, help="JSONL requests")
    parser.add_argument("--queue", help="append-only destination, required for enqueue")
    args = parser.parse_args()
    rows = [json.loads(line) for line in Path(args.input).read_text().splitlines() if line.strip()]
    if args.command == "enqueue":
        if not args.queue:
            parser.error("enqueue requires --queue")
        try:
            audits = enqueue_requests(args.queue, rows)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
    else:
        audits = [normalize_request(r, line_number=i, source=args.input) for i, r in enumerate(rows, 1)]
    for a in audits:
        print(json.dumps(a, ensure_ascii=False, sort_keys=True))
    return 2 if any(a["status"] in ("invalid", "unresolved") for a in audits) else 0


if __name__ == "__main__":
    raise SystemExit(main())
