"""Acquire official PDF candidates with hashes, bounded batches and no EO verdicts.

Only URLs already recorded in the frozen Stage 14 OFR metadata are requested.
All outcomes are recorded. An acquired PDF remains an unreviewed original
representation CANDIDATE; printed pages, scope and first cessation are unknown.
"""
import argparse
import csv
import hashlib
import io
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
INDEX = ROOT / "research/stage21/sources_index/ORIGINAL_SOURCE_RETRIEVAL_QUEUE.csv"
OUT = ROOT / "research/stage21/original_sources"
LOG = OUT / "ACQUISITION_LOG.jsonl"
SUMMARY = OUT / "SOURCE_ACQUISITION_METRICS.json"
CASES = OUT / "CASE_ORIGINAL_SOURCE_CUSTODY.csv"
MAX_FILE = 12_000_000
MAX_RUN = 90_000_000
PDF_HOSTS = {"www.govinfo.gov", "govinfo.gov"}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def selected(rows):
    seen = set()
    output = []
    for r in rows:
        if r["format"] != "pdf_url":
            continue
        id_ = r["instrument_id"]
        url = r["literal_url"]
        parsed = urllib.parse.urlsplit(url)
        if not re.fullmatch(r"EO:\d+[A-Z]?", id_) or id_ in seen:
            raise ValueError("Missing or repeated candidate original identity")
        if not (parsed.scheme == "https" and parsed.hostname in PDF_HOSTS and
                "/content/pkg/" in parsed.path and parsed.path.endswith(".pdf")):
            raise ValueError("Non-whitelisted candidate PDF URL " + id_)
        seen.add(id_)
        output.append(r)
    return output

def filename_for(identifier):
    if not re.fullmatch(r"EO:\d+[A-Z]?", identifier):
        raise ValueError("Unsafe instrument identifier")
    return "EO_" + identifier[3:] + ".pdf"

def validate_pdf(payload):
    if len(payload) < 400 or len(payload) > MAX_FILE:
        raise ValueError("PDF outside approved bounds")
    if not payload.startswith(b"%PDF-") or b"%%EOF" not in payload[-4096:]:
        raise ValueError("PDF signature or EOF missing")
    return sha(payload)

def load_log():
    if not LOG.exists():
        return {}
    out = {}
    for line in LOG.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        row = json.loads(line)
        id_ = row["instrument_id"]
        if id_ in out:
            raise ValueError("Acquisition log reused an identity; preserve audit trail")
        out[id_] = row
    return out

def acquire(row):
    id_, url = row["instrument_id"], row["literal_url"]
    entry = {
        "instrument_id": id_, "requested_url": url,
        "attempted_at_utc": datetime.now(timezone.utc).isoformat(),
        "custody_state": "attempted_unresolved", "bytes": 0,
        "sha256": "", "repository_path": "", "error": ""
    }
    try:
        request = urllib.request.Request(url, headers={
            "User-Agent": "EO-Lifecycle-Research/Stage21 (official document acquisition)",
            "Accept": "application/pdf"})
        with urllib.request.urlopen(request, timeout=28) as response:
            final = urllib.parse.urlsplit(response.geturl())
            if final.scheme != "https" or final.hostname not in PDF_HOSTS or (
                    "/error" in final.path):
                raise ValueError("Unexpected GovInfo endpoint or error redirect")
            body = response.read(MAX_FILE + 1)
            if len(body) > MAX_FILE:
                raise ValueError("Source larger than per-document cap")
            if "pdf" not in (response.headers.get("Content-Type") or "").lower():
                raise ValueError("Response MIME type is not PDF")
        digest = validate_pdf(body)
        rel = "research/stage21/original_sources/" + filename_for(id_)
        path = ROOT / rel
        if path.exists():
            if sha(path.read_bytes()) != digest:
                raise ValueError("Existing immutable PDF differs in bytes")
        else:
            path.write_bytes(body)
        entry.update({
            "custody_state": "PDF_BYTES_CAPTURED_NOT_AUTHENTICATED",
            "bytes": len(body), "sha256": digest,
            "repository_path": rel,
        })
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as error:
        entry["custody_state"] = "fetch_failed_REVIEW_MANUALLY"
        entry["error"] = (type(error).__name__ + ": " + str(error))[:240]
    return entry

def reports(rows, log):
    table = []
    for r in rows:
        record = log.get(r["instrument_id"], {})
        table.append({
            "instrument_id": r["instrument_id"],
            "official_PDF_candidate_URL": r["literal_url"],
            "custody_state": record.get("custody_state", "not_attempted"),
            "sha256_source_bytes_if_present": record.get("sha256", ""),
            "source_repository_path": record.get("repository_path", ""),
            "bytes": record.get("bytes", ""),
            "attempted_utc": record.get("attempted_at_utc", ""),
            "retrieval_error": record.get("error", ""),
            "original_EO_identity_and_pages_human_verified": "no",
            "operative_clause_scope_verified": "no",
            "causal_effects_verified": "no",
            "independent_human_certified": "no",
        })
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=list(table[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(table)
    metrics = {
        "schema": "eo-stage21-official-PDF-bounded-acquisition/v1",
        "PDF_source_candidates_from_frozen_OFR_urls": len(rows),
        "actual_network_attempts_recorded": len(log),
        "successfully_archived_PDF_source_candidates": sum(
            r.get("custody_state") == "PDF_BYTES_CAPTURED_NOT_AUTHENTICATED"
            for r in log.values()),
        "failures_recorded": sum(
            r.get("custody_state") == "fetch_failed_REVIEW_MANUALLY"
            for r in log.values()),
        "archive_bytes_total": sum(
            r.get("bytes", 0) for r in log.values()),
        "source_input_sha256": sha(INDEX.read_bytes()),
        "original_clause_inventory_human_verified": 0,
        "legal_effects_adjudicated": 0,
        "independently_human_certified_lifecycles": 0,
    }
    return buf.getvalue(), metrics

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--fetch",action="store_true")
    p.add_argument("--check",action="store_true")
    p.add_argument("--limit",type=int,default=40)
    a=p.parse_args()
    if a.limit<1 or a.limit>75:
        p.error("limit must be 1–75")
    if a.fetch and a.check:
        p.error("--fetch and --check are exclusive")
    with INDEX.open(newline="", encoding="utf-8") as f:
        rows=selected(list(csv.DictReader(f)))
    if len(rows)!=386:
        raise SystemExit("Stage 21 original PDF candidate inventory changed")
    OUT.mkdir(parents=True,exist_ok=True)
    log=load_log()
    if a.fetch:
        attempts=0
        bytes_this_run=0
        for row in rows:
            if row["instrument_id"] in log or attempts>=a.limit or bytes_this_run>=MAX_RUN:
                continue
            outcome=acquire(row)
            with LOG.open("a", encoding="utf-8") as f:
                f.write(json.dumps(outcome,sort_keys=True)+"\n")
            log[outcome["instrument_id"]]=outcome
            attempts+=1
            bytes_this_run+=outcome["bytes"]
            time.sleep(0.3)
    for id_,r in log.items():
        if r.get("custody_state")!="PDF_BYTES_CAPTURED_NOT_AUTHENTICATED":
            continue
        path=ROOT / r["repository_path"]
        if not path.exists() or path.stat().st_size!=r["bytes"] or sha(path.read_bytes())!=r["sha256"]:
            raise SystemExit("Archived PDF custody mismatch: "+id_)
    table,metrics=reports(rows,log)
    outputs={
        CASES:table.encode("utf-8"),
        SUMMARY:(json.dumps(metrics,indent=2,sort_keys=True)+"\n").encode("utf-8")
    }
    for path,body in outputs.items():
        if a.check:
            if not path.is_file() or path.read_bytes()!=body:
                raise SystemExit("Stale acquisition output "+str(path))
        else:
            path.write_bytes(body)
    print(json.dumps(metrics,indent=2))

if __name__=="__main__":
    main()
