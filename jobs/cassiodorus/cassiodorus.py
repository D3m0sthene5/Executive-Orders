"""Cassiodorus: keep the bytes of the web pages that claims cite, so the checker can verify them.

Named for Cassiodorus, whose monastery at Vivarium copied and kept the texts later ages could
check against. The project holds thousands of orders only as American Presidency Project (APP)
transcriptions. Each transcription's page bytes were read once (live, or from a Common Crawl or
Wayback capture) and hashed, but the bytes stayed in a download cache that is not committed, so
the claim checker reports every reference to such a page as ``custody_record_only`` and
``kit.py complete`` refuses to file the claim. Under the owner's 2026-10-21 ruling a labelled
transcription may serve as a provisional working text; this job supplies the missing custody.

For every requested page it re-reads the recorded capture (Common Crawl WARC byte range, or the
Wayback original-bytes URL), checks that the bytes hash to
the recorded sha256, and keeps them under ``output/raw/<sha256>.html`` with a ``SOURCES.jsonl``
record whose ``cache_path`` the existing checker index resolves (custody ``job_cache``, bytes
re-hashed on every check). A page whose bytes no longer hash as recorded is reported, not kept.

Requests come from two places, both bounded: ``REQUESTS.json`` in this folder (explicit sha256s
or instrument ids) and the APP pages cited by claims in ``research/readiness/claims`` and by the
``CLAIMS.proposed.jsonl`` files of claim-kit packets under ``research/excavator``. Nothing here
grades a source, authenticates an original, or changes a claim; it keeps bytes and reports.
Standard library only; the archive readers are app-executive-orders' own.
"""
from __future__ import annotations

import datetime as _dt
import glob
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "app-executive-orders"))

APP_OUT = "jobs/app-executive-orders/output"
APP_HOST = "presidency.ucsb.edu"
MAX_PAGES_PER_RUN = 300
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class ArchiveUnavailable(RuntimeError):
    """The wanted page has no supported fixed archive capture; never request live APP."""


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def now():
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_jsonl(path):
    out = []
    p = Path(path)
    if not p.is_file():
        return out
    with p.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue
    return out


def cited_app_pages(root):
    """{sha256: url} for every APP page a claim cites (filed claims and packet proposals)."""
    found = {}

    def walk(o):
        if isinstance(o, dict):
            url, sha = o.get("url"), str(o.get("sha256", "")).lower()
            if isinstance(url, str) and APP_HOST in url and HEX64.match(sha):
                found.setdefault(sha, url)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    files = sorted(glob.glob(os.path.join(root, "research/readiness/claims/*.jsonl")))
    files += sorted(glob.glob(os.path.join(root, "research/excavator/*/packet*/applied-*/CLAIMS.proposed.jsonl")))
    files += sorted(glob.glob(os.path.join(root, "research/excavator/*/*/applied-*/CLAIMS.proposed.jsonl")))
    for f in files:
        for rec in read_jsonl(f):
            walk(rec)
    return found


def explicit_requests(root, job_dir):
    """REQUESTS.json: {"sha256": [...], "instrument_ids": [...]} -> set of sha256 plus instrument ids."""
    p = Path(job_dir) / "REQUESTS.json"
    if not p.is_file():
        return set(), set()
    data = json.loads(p.read_text(encoding="utf-8"))
    shas = {str(s).lower() for s in data.get("sha256", []) if HEX64.match(str(s).lower())}
    ids = {str(i) for i in data.get("instrument_ids", [])}
    return shas, ids


def page_records(root):
    """sha256 -> {'kind': 'mirror'|'live', 'row': record} from the APP job's document lists."""
    recs = {}
    for name, kind in (("MIRROR_DOCUMENTS.jsonl", "mirror"), ("DOCUMENTS.jsonl", "live")):
        for row in read_jsonl(os.path.join(root, APP_OUT, name)):
            sha = str(row.get("sha256", "")).lower()
            if HEX64.match(sha):
                recs.setdefault(sha, {"kind": kind, "row": row})
    return recs


def fetch_bytes(record, cache, throttles):
    """(bytes, how) for one page record; raises on failure."""
    import app_mirror as M  # noqa: E402  (app-executive-orders' archive readers)
    row = record["row"]
    cap = row.get("capture") if isinstance(row.get("capture"), dict) else None
    if record["kind"] == "mirror" and cap and cap.get("archive") == "common-crawl" and cap.get("warc_filename"):
        c = {"url": row["url"], "crawl": cap.get("crawl", ""), "digest": cap.get("cc_digest", ""),
             "warc_filename": cap["warc_filename"], "warc_offset": int(cap["warc_offset"]),
             "warc_length": int(cap["warc_length"])}
        original = M.http_get
        M.http_get = lambda url, headers=None, timeout=90, tries=6, throttle=None: original(url, headers, timeout, 2, throttle)
        try:
            body, prov = M.read_cc(c, cache, throttles["cc"])
        finally:
            M.http_get = original
        return body, "common-crawl WARC range " + cap["warc_filename"] + f"@{cap['warc_offset']}"
    if record["kind"] == "mirror" and cap and cap.get("archive") == "wayback" and cap.get("wayback_url"):
        status, _, body = M.http_get(cap["wayback_url"], throttle=throttles["wayback"], tries=2)
        if status != 200:
            raise M.ArchiveError(f"wayback returned {status}")
        return body, "wayback " + cap["wayback_url"]
    raise ArchiveUnavailable("no supported archive capture recorded; live APP acquisition is disabled")


def run(root, job_dir, out, cache, limit=MAX_PAGES_PER_RUN):
    import app_mirror as M  # noqa: E402
    root, out, cache = Path(root), Path(out), Path(cache)
    out.mkdir(parents=True, exist_ok=True)
    (out / "raw").mkdir(exist_ok=True)
    started = now()
    cited = cited_app_pages(str(root))
    shas, ids = explicit_requests(str(root), job_dir)
    records = page_records(str(root))
    by_id = {}
    for sha, rec in records.items():
        iid = rec["row"].get("instrument_id")
        if iid:
            by_id.setdefault(iid, []).append(sha)
    wanted = dict(cited)
    for s in shas:
        wanted.setdefault(s, records.get(s, {}).get("row", {}).get("url", ""))
    for iid in ids:
        for s in by_id.get(iid, []):
            wanted.setdefault(s, records[s]["row"].get("url", ""))
    prior = {r["sha256"] for r in read_jsonl(out / "SOURCES.jsonl")} if (out / "SOURCES.jsonl").is_file() else set()
    throttles = {"cc": M.Throttle(1.0), "wayback": M.Throttle(2.0)}
    results, sources, counts = [], [], {"requested": len(wanted), "kept": 0, "already_kept": 0, "hash_mismatch": 0,
                                        "no_record": 0, "no_archive_capture": 0, "fetch_failed": 0, "skipped_over_limit": 0, "skipped_after_failures": 0}
    consecutive_failures = 0
    for n, (sha, url) in enumerate(sorted(wanted.items())):
        if n >= limit:
            counts["skipped_over_limit"] += 1
            continue
        path = out / "raw" / (sha + ".html")
        if path.is_file() and sha256(path.read_bytes()) == sha:
            counts["already_kept"] += 1
            kept = True
        else:
            kept = False
        rec = records.get(sha)
        if not rec and not kept:
            counts["no_record"] += 1
            results.append({"sha256": sha, "url": url, "result": "no_capture_record",
                            "note": "no DOCUMENTS or MIRROR_DOCUMENTS row carries this sha256; nothing to re-read"})
            continue
        if not kept:
            if consecutive_failures >= 5:
                counts["skipped_after_failures"] += 1
                results.append({"sha256": sha, "url": url, "result": "skipped", "note": "five consecutive fetch failures; the archives are unreachable from this machine"})
                continue
            try:
                body, how = fetch_bytes(rec, cache, throttles)
                consecutive_failures = 0
            except ArchiveUnavailable as exc:
                counts["no_archive_capture"] += 1
                results.append({"sha256": sha, "url": url, "result": "no_archive_capture", "note": str(exc)})
                continue
            except Exception as exc:  # noqa: BLE001  (every failure is reported, none hidden)
                consecutive_failures += 1
                counts["fetch_failed"] += 1
                results.append({"sha256": sha, "url": url, "result": "fetch_failed", "note": f"{type(exc).__name__}: {str(exc)[:200]}"})
                continue
            got = sha256(body)
            if got != sha:
                counts["hash_mismatch"] += 1
                results.append({"sha256": sha, "url": url, "result": "hash_mismatch", "fetched_sha256": got, "how": how,
                                "note": "re-read bytes do not hash as recorded; not kept under the recorded hash"})
                continue
            path.write_bytes(body)
            counts["kept"] += 1
            results.append({"sha256": sha, "url": url, "result": "kept", "how": how, "bytes": len(body)})
        row = rec["row"] if rec else {}
        sources.append({"source_id": "cassiodorus-" + sha[:12], "instrument_ids": [row.get("instrument_id")] if row.get("instrument_id") else [],
                        "url": url or row.get("url", ""), "sha256": sha, "bytes": path.stat().st_size, "content_type": "text/html",
                        "retrieved_utc": started, "route": "job:cassiodorus:" + (rec["kind"] if rec else "kept"),
                        "page_or_item": (row.get("heading") or row.get("listing_title") or "APP page") +
                        ("; " + (row.get("capture") or {}).get("archive", "live") + " capture " + str((row.get("capture") or {}).get("captured_utc") or row.get("retrieved_utc", "")) if row else ""),
                        "cache_path": "raw/" + sha + ".html",
                        "notes": "Page bytes kept so the checker can re-hash them; a transcription page, acceptable_as_original=false; no grade or finding."})
    with (out / "SOURCES.jsonl").open("w", encoding="utf-8") as fh:
        for s in sources:
            fh.write(json.dumps(s, ensure_ascii=False, sort_keys=True) + "\n")
    (out / "RESULTS.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    summary = {"job": "cassiodorus", "generated_utc": started, "counts": counts, "pages_kept_total": len(sources),
               "requests": {"cited_by_claims": len(cited), "explicit_sha256": len(shas), "explicit_instrument_ids": sorted(ids)},
               "limits": {"pages_per_run": limit, "live_fetches_per_run": 0},
               "legal_conclusions": 0, "statuses_changed": 0,
               "notice": "Kept bytes of transcription pages for custody checks only; nothing here authenticates an original."}
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps(counts), flush=True)
    return summary
