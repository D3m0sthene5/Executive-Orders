#!/usr/bin/env python3
"""Portable, offline ProQuest queue and append-only download audit.

The original attachment is the only source of EO identities and URLs. This
program never opens a website or controls a browser. `saved_requested` means
the viewer's Save command completed; separate evidence is required for a file.
Inventory checks a single explicitly named local folder without writing state.
Reconcile explicitly records files found there, using filename identity, size,
SHA256, and a %PDF- signature. It does not validate the PDF's full structure or
the legal identity of its contents. Historical paths and browser authentication
do not transfer files or sign-in sessions to another computer.

Usage:
    python scripts/proquest_progress.py next --limit 10
    python scripts/proquest_progress.py record < one_event.json
    python scripts/proquest_progress.py status
    python scripts/proquest_progress.py inventory --folder PATH
    python scripts/proquest_progress.py reconcile --folder PATH

An event requires `id`, `status`, and nonempty `evidence`. For linked rows,
`source_url` must be one of that row's exact supplied PDF or record URLs.
`verified_screenshot` may omit source_url when its evidence is a file listing.
`verified_local_pdf` is reserved for reconcile, which performs the local checks.
`verified_repository` records a confirmed GitHub file with repository_path,
repository_url, evidence, and observed commit/blob hashes when available; it
does not claim that the file exists in this computer's Downloads folder.
Optional metadata is retained. `terminal` defaults to true except
for error_unresolved; it means exclude this order from the action queue, not
that a file is verified. Explicit terminal errors can be reopened by recording
another error_unresolved event with terminal=false. Unattempted entries precede
retryable errors in `next`, preserving attachment order within each group.

Defaults resolve from this script's package, independent of working directory:
_resume/proquest_download_links.html, _resume/checkpoint.json, and
_resume/progress.jsonl. The checkpoint provides existing screenshot evidence
without modification. Missing-link rows count as link_unavailable automatically.
Writes use an advisory lock, fsync, and atomic replacement of old log bytes plus
one JSON line; readers therefore see a complete old or complete new log.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT / "_resume" / "proquest_download_links.html"
DEFAULT_CHECKPOINT = ROOT / "_resume" / "checkpoint.json"
DEFAULT_LOG = ROOT / "_resume" / "progress.jsonl"
STATUSES = frozenset({
    "saved_requested", "link_unavailable", "error_unresolved",
    "verified_screenshot", "verified_local_pdf", "verified_repository",
})
PDF_FILENAME = re.compile(
    r"^(?:PT1-)?(?P<year>\d{4})-EO-(?P<number>\d+[A-Za-z]*)"
    r"(?: \((?P<copy>\d+)\))?\.pdf$", re.IGNORECASE
)


class AuditError(ValueError):
    pass


def read_source(path: Path):
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    marker = "const ROWS="
    start = text.find(marker)
    if start < 0:
        raise AuditError("Source does not contain the original ROWS declaration")
    rows, _ = json.JSONDecoder().raw_decode(text[start + len(marker):])
    if not isinstance(rows, list) or not rows:
        raise AuditError("Source ROWS must be a nonempty JSON array")
    by_id = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str):
            raise AuditError("Source contains an invalid EO row")
        if row["id"] in by_id:
            raise AuditError("Duplicate EO ID in original source: " + row["id"])
        by_id[row["id"]] = row
    return rows, by_id, hashlib.sha256(raw).hexdigest()


def normalize_event(event, by_id, source_sha256, *, allow_local=False):
    if not isinstance(event, dict):
        raise AuditError("record requires exactly one JSON object")
    event = dict(event)
    eo_id = event.get("id")
    if not isinstance(eo_id, str) or eo_id not in by_id:
        raise AuditError("Unknown or missing exact source EO ID: " + repr(eo_id))
    row = by_id[eo_id]
    status = event.get("status")
    if not isinstance(status, str) or status not in STATUSES:
        raise AuditError("status must be one of: " + ", ".join(sorted(STATUSES)))
    if status == "verified_local_pdf":
        if not allow_local:
            raise AuditError("Use reconcile --folder PATH to record verified_local_pdf")
        if not row.get("pdf") or row.get("y") is None:
            raise AuditError("Local verification requires a supplied, dated source row")
        if event.get("pdf_signature_valid") is not True:
            raise AuditError("Local verification requires a valid %PDF- signature")
        if not isinstance(event.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", event["sha256"]):
            raise AuditError("Local verification requires a SHA256 hash")
        if not isinstance(event.get("size_bytes"), int) or event["size_bytes"] < 5:
            raise AuditError("Local verification requires a PDF file size")
        if not isinstance(event.get("local_path"), str) or not event["local_path"]:
            raise AuditError("Local verification requires its observed local path")
    elif status == "verified_repository":
        if not row.get("pdf") or row.get("y") is None:
            raise AuditError("Repository verification requires a supplied, dated source row")
        for key in ("repository_path", "repository_url"):
            if not isinstance(event.get(key), str) or not event[key].strip():
                raise AuditError("Repository verification requires " + key)
        for key in ("git_blob_sha", "blob_sha", "repository_blob_sha",
                    "commit_sha", "repository_commit_sha"):
            if key in event and (not isinstance(event[key], str)
                    or not re.fullmatch(r"[0-9a-fA-F]{40}(?:[0-9a-fA-F]{24})?", event[key])):
                raise AuditError(key + " must be an observed 40- or 64-character Git hash")
    if not isinstance(event.get("evidence"), str) or not event["evidence"].strip():
        raise AuditError("Nonempty evidence is required; report what was observed")
    allowed_urls = {row[k] for k in ("pdf", "rec") if row.get(k)}
    if status != "verified_screenshot" and allowed_urls and not event.get("source_url"):
        raise AuditError("source_url is required and must be an exact supplied link")
    for key in ("source_url", "pdf", "rec", "pdf_url", "record_url",
                "source_pdf", "source_record"):
        if key in event and event[key] is not None:
            value = event[key]
            if not isinstance(value, str) or value not in allowed_urls:
                raise AuditError(key + " is not an exact supplied URL for " + eo_id)
            if key in {"pdf", "pdf_url", "source_pdf"} and value != row.get("pdf"):
                raise AuditError(key + " does not match the supplied PDF URL")
            if key in {"rec", "record_url", "source_record"} and value != row.get("rec"):
                raise AuditError(key + " does not match the supplied record URL")
    if "source_urls" in event:
        urls = event["source_urls"]
        if not isinstance(urls, list) or any(
            not isinstance(url, str) or url not in allowed_urls for url in urls
        ):
            raise AuditError("source_urls contains an unsupplied URL")
    for key in ("n", "y"):
        if key in event and event[key] != row.get(key):
            raise AuditError(key + " does not match the original EO row")
    if status == "saved_requested" and not row.get("pdf"):
        raise AuditError("Cannot record Save requested for a row without a supplied PDF link")
    if "source_sha256" in event and event["source_sha256"] != source_sha256:
        raise AuditError("Audit event belongs to a different source attachment")
    terminal = event.get("terminal", status != "error_unresolved")
    if not isinstance(terminal, bool):
        raise AuditError("terminal must be a JSON boolean")
    if status in {"saved_requested", "verified_screenshot", "verified_local_pdf", "verified_repository"} and not terminal:
        raise AuditError(status + " must be terminal for the action queue")
    event["terminal"] = terminal
    event["source_sha256"] = source_sha256
    event.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    if not isinstance(event["timestamp"], str):
        raise AuditError("timestamp must be a string")
    event["filesystem_verified"] = status in {"verified_screenshot", "verified_local_pdf"}
    event["repository_verified"] = status == "verified_repository"
    return event


def parse_log(raw: bytes, by_id, source_sha256):
    events = []
    for number, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = normalize_event(json.loads(line), by_id, source_sha256, allow_local=True)
        except (ValueError, TypeError) as exc:
            raise AuditError(f"Invalid audit line {number}: {exc}") from exc
        events.append(event)
    return events


def read_log(path: Path, by_id, source_sha256):
    return parse_log(path.read_bytes() if path.exists() else b"", by_id, source_sha256)


def screenshot_ids(path: Path, by_id):
    if not path.exists():
        return set()
    checkpoint = json.loads(path.read_text(encoding="utf-8"))
    verified = set()
    for entry in checkpoint.get("downloaded_files_verified", []):
        eo_id = entry.get("eo", entry.get("id"))
        if eo_id not in by_id:
            raise AuditError("Checkpoint contains an unknown EO ID: " + repr(eo_id))
        if "screenshot" in str(entry.get("evidence", "")).lower():
            verified.add(eo_id)
    return verified


def summarize(rows, events, verified):
    latest = {}
    verified = set(verified)
    local_verified = set()
    repository_verified = set()
    for event in events:
        latest[event["id"]] = event
        if event["status"] == "verified_screenshot":
            verified.add(event["id"])
        elif event["status"] == "verified_local_pdf":
            local_verified.add(event["id"])
        elif event["status"] == "verified_repository":
            repository_verified.add(event["id"])
    counts = {status: 0 for status in sorted(STATUSES)}
    fresh_queue = []
    retry_queue = []
    for row in rows:
        eo_id = row["id"]
        if eo_id in repository_verified:
            counts["verified_repository"] += 1
            continue
        if eo_id in local_verified:
            counts["verified_local_pdf"] += 1
            continue
        if eo_id in verified:
            counts["verified_screenshot"] += 1
            continue
        event = latest.get(eo_id)
        if event is not None:
            counts[event["status"]] += 1
            if row.get("pdf") and not event["terminal"]:
                retry_queue.append(row)
        elif not row.get("pdf"):
            counts["link_unavailable"] += 1
        else:
            fresh_queue.append(row)
    queue = fresh_queue + retry_queue
    counts.update({
        "total_rows": len(rows),
        "supplied_pdf_urls": sum(bool(row.get("pdf")) for row in rows),
        "source_rows_without_links": sum(not row.get("pdf") for row in rows),
        "linked_unavailable": sum(
            bool(row.get("pdf")) and row["id"] not in verified | local_verified | repository_verified
            and latest.get(row["id"], {}).get("status") == "link_unavailable"
            for row in rows
        ),
        "verified_files_any_evidence": len(verified | local_verified | repository_verified),
        "orders_with_screenshot_evidence": len(verified),
        "orders_with_local_file_evidence": len(local_verified),
        "orders_with_repository_evidence": len(repository_verified),
        "remaining": len(queue),
        "remaining_unattempted": len(fresh_queue),
        "remaining_retryable": len(retry_queue),
        "audit_events": len(events),
        "save_commands_logged": sum(e["status"] == "saved_requested" for e in events),
        "saved_requested_means": "Viewer Save command completed; file existence unverified",
        "remaining_means": "Linked action queue, including nonterminal unresolved attempts",
        "local_verification_means": "Historical local file observation: matching filename, size, SHA256, and %PDF- signature; run inventory on this computer to establish present files",
        "repository_verification_means": "A confirmed repository file, with recorded path and upload evidence; it may need restoring to this computer",
    })
    return counts, queue


@contextmanager
def audit_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_name(path.name + ".lock").open("a+b") as lock:
        if os.name == "nt":
            import msvcrt

            lock.seek(0, os.SEEK_END)
            if lock.tell() == 0:
                lock.write(b"\0")
                lock.flush()
            deadline = time.monotonic() + 30
            while True:
                lock.seek(0)
                try:
                    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise AuditError("Timed out waiting for the audit file lock")
                    time.sleep(0.1)
            try:
                yield
            finally:
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def append_events(path: Path, new_events, by_id, source_sha256, *, deduplicate_local=False):
    with audit_lock(path):
        old = path.read_bytes() if path.exists() else b""
        existing = parse_log(old, by_id, source_sha256)
        if deduplicate_local:
            known = {
                (e["id"], e.get("local_path"), e.get("sha256"), e.get("size_bytes"))
                for e in existing if e["status"] == "verified_local_pdf"
            }
            filtered = []
            for event in new_events:
                key = (event["id"], event["local_path"], event["sha256"], event["size_bytes"])
                if key not in known:
                    filtered.append(event)
                    known.add(key)
            new_events = filtered
        if not new_events:
            return 0
        if old and not old.endswith(b"\n"):
            old += b"\n"
        lines = b"".join(
            (json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
            for event in new_events
        )
        temp_name = None
        try:
            with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent,
                                             prefix="." + path.name + ".", delete=False) as temp:
                temp_name = temp.name
                temp.write(old)
                temp.write(lines)
                temp.flush()
                os.fsync(temp.fileno())
            os.replace(temp_name, path)
            temp_name = None
            if os.name != "nt":
                directory_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
        finally:
            if temp_name is not None:
                Path(temp_name).unlink(missing_ok=True)
        return len(new_events)


def identify_pdf_filename(filename, by_id):
    match = PDF_FILENAME.fullmatch(filename)
    if match is None:
        return {"eo_id": None, "filename_match": False,
                "identity_error": "Filename does not match a supplied EO year/number pattern"}
    year = int(match["year"])
    eo_id = "EO:" + match["number"].upper()
    row = by_id.get(eo_id)
    result = {
        "eo_id": None,
        "candidate_eo_id": eo_id,
        "filename_year": year,
        "filename_eo_number": match["number"].upper(),
        "chrome_copy_number": None if match["copy"] is None else int(match["copy"]),
        "filename_match": False,
    }
    if row is None:
        result["identity_error"] = "EO number is absent from the original attachment"
    elif row.get("y") != year:
        result["identity_error"] = "Filename year does not match the original row's known year"
    elif not row.get("pdf"):
        result["identity_error"] = "Original row has no supplied PDF link"
    else:
        result["eo_id"] = eo_id
        result["filename_match"] = True
        result["identity_method"] = "Filename year and number match the original attachment"
    return result


def inventory_folder(folder: Path, by_id, source_sha256):
    folder = folder.expanduser().resolve(strict=True)
    if not folder.is_dir():
        raise AuditError("--folder must name an existing directory")
    files = []
    for path in sorted(folder.iterdir(), key=lambda p: p.name.casefold()):
        if path.suffix.lower() != ".pdf":
            continue
        if not path.is_file() and not path.is_symlink():
            continue
        entry = {
            "filename": path.name,
            "local_path": str(path),
            "size_bytes": None,
            "sha256": None,
            "pdf_signature_valid": False,
            "eligible_for_reconcile": False,
            "content_identity_verified": False,
            **identify_pdf_filename(path.name, by_id),
        }
        if path.is_symlink():
            entry["read_error"] = "Symbolic links are not scanned outside the specified folder"
            files.append(entry)
            continue
        try:
            digest = hashlib.sha256()
            size = 0
            with path.open("rb") as file:
                before = os.fstat(file.fileno())
                signature = file.read(5)
                digest.update(signature)
                size += len(signature)
                while True:
                    chunk = file.read(1024 * 1024)
                    if not chunk:
                        break
                    digest.update(chunk)
                    size += len(chunk)
                after = os.fstat(file.fileno())
            entry.update(size_bytes=size, sha256=digest.hexdigest(),
                         pdf_signature_valid=signature == b"%PDF-")
            if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns or size != after.st_size:
                entry["read_error"] = "File changed while being scanned; rerun inventory after saving finishes"
            else:
                entry["eligible_for_reconcile"] = entry["filename_match"] and entry["pdf_signature_valid"]
        except OSError as exc:
            entry["read_error"] = str(exc)
        files.append(entry)
    groups = {}
    for entry in files:
        if entry["eligible_for_reconcile"]:
            groups.setdefault(entry["eo_id"], []).append(entry)
    duplicates = [
        {"id": eo_id, "filenames": [e["filename"] for e in group],
         "extra_files": len(group) - 1,
         "distinct_sha256": len({e["sha256"] for e in group})}
        for eo_id, group in groups.items() if len(group) > 1
    ]
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "folder": str(folder),
        "recursive": False,
        "source_sha256": source_sha256,
        "summary": {
            "pdf_files": len(files),
            "valid_pdf_signatures": sum(e["pdf_signature_valid"] for e in files),
            "recognized_pdf_files": sum(e["eligible_for_reconcile"] for e in files),
            "unique_orders": len(groups),
            "duplicate_files": sum(d["extra_files"] for d in duplicates),
            "unmatched_filenames": sum(not e["filename_match"] for e in files),
            "invalid_pdf_signatures": sum(not e["pdf_signature_valid"] and "read_error" not in e for e in files),
            "read_errors": sum("read_error" in e for e in files),
        },
        "duplicate_groups": duplicates,
        "files": files,
        "verification_scope": "Filename match and %PDF- signature with SHA256 and byte size; full PDF structure and contents are not validated",
    }


def reconcile_folder(folder, rows, by_id, source_sha256, checkpoint, log):
    inventory = inventory_folder(folder, by_id, source_sha256)
    groups = {}
    for entry in inventory["files"]:
        if entry["eligible_for_reconcile"]:
            groups.setdefault(entry["eo_id"], []).append(entry)
    candidates = []
    for eo_id, group in groups.items():
        group.sort(key=lambda e: (e["chrome_copy_number"] is not None,
                                  e["chrome_copy_number"] or 0, e["filename"].casefold()))
        chosen = group[0]
        candidates.append(normalize_event({
            "id": eo_id,
            "status": "verified_local_pdf",
            "source_url": by_id[eo_id]["pdf"],
            "timestamp": inventory["timestamp"],
            "evidence": "Explicit local reconciliation found a file whose year/number match the original row and whose first five bytes are %PDF-; size and SHA256 recorded",
            "local_path": chosen["local_path"],
            "filename": chosen["filename"],
            "size_bytes": chosen["size_bytes"],
            "sha256": chosen["sha256"],
            "pdf_signature_valid": True,
            "content_identity_verified": False,
            "inventory_folder": inventory["folder"],
            "matching_files": [{k: e[k] for k in ("filename", "local_path", "size_bytes", "sha256")} for e in group],
        }, by_id, source_sha256, allow_local=True))
    added = append_events(log, candidates, by_id, source_sha256, deduplicate_local=True) if candidates else 0
    events = read_log(log, by_id, source_sha256)
    screenshots = screenshot_ids(checkpoint, by_id)
    status, _ = summarize(rows, events, screenshots)
    latest = {e["id"]: e for e in events}
    local_history = {e["id"] for e in events if e["status"] == "verified_local_pdf"}
    repository_history = {e["id"] for e in events if e["status"] == "verified_repository"}
    recognized = set(groups)
    return {
        "folder": inventory["folder"],
        "inventory_summary": inventory["summary"],
        "duplicate_groups": inventory["duplicate_groups"],
        "audit_events_added": added,
        "matching_orders_already_recorded": len(candidates) - added,
        "saved_requested_without_matching_file_here": [
            row["id"] for row in rows
            if latest.get(row["id"], {}).get("status") == "saved_requested"
            and row["id"] not in recognized
        ],
        "historically_verified_without_matching_file_here": [
            row["id"] for row in rows
            if row["id"] in screenshots | local_history and row["id"] not in recognized
        ],
        "repository_verified_without_matching_file_here": [
            row["id"] for row in rows
            if row["id"] in repository_history and row["id"] not in recognized
        ],
        "absence_note": "Files absent from this folder are reported without erasing historical evidence or retrying any website",
        "status": status,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    commands = parser.add_subparsers(dest="command", required=True)
    next_parser = commands.add_parser("next", help="Return exact source rows awaiting action")
    next_parser.add_argument("--limit", type=int, default=10)
    commands.add_parser("record", help="Append one JSON event read from stdin")
    commands.add_parser("status", help="Return progress counts as JSON")
    inventory_parser = commands.add_parser("inventory", help="Read only: inspect PDFs in one explicitly named local folder")
    inventory_parser.add_argument("--folder", type=Path, required=True)
    reconcile_parser = commands.add_parser("reconcile", help="Explicitly append local PDF verification from the selected folder")
    reconcile_parser.add_argument("--folder", type=Path, required=True)
    args = parser.parse_args()
    try:
        rows, by_id, source_sha256 = read_source(args.source)
        if args.command == "record":
            event = normalize_event(json.load(sys.stdin), by_id, source_sha256)
            append_events(args.log, [event], by_id, source_sha256)
            result = {"recorded": event, "log": str(args.log.resolve())}
        elif args.command == "inventory":
            result = inventory_folder(args.folder, by_id, source_sha256)
        elif args.command == "reconcile":
            result = reconcile_folder(args.folder, rows, by_id, source_sha256,
                                      args.checkpoint, args.log)
        else:
            events = read_log(args.log, by_id, source_sha256)
            verified = screenshot_ids(args.checkpoint, by_id)
            counts, queue = summarize(rows, events, verified)
            if args.command == "next":
                if args.limit < 0:
                    raise AuditError("--limit must be nonnegative")
                result = queue[:args.limit]
            else:
                result = counts
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
