"""Ptolemy: keep the bytes of every cited source the project holds only as a hash.

Named for the Ptolemies' rule at Alexandria that every book arriving on a ship was copied for the Library
before the ship sailed. The project has read about 11,000 cited sources once, recorded their SHA-256 and
text, and kept no bytes. On GitHub's runner the claim checker can re-download some of them, but agents work
where those hosts are unreachable, so their checks report `custody_record_only` and the claim kit refuses to
file. The Herschel survey (2026-11-05) found this blocks work on about 2,900 orders. Ptolemy fetches each
wanted source once, keeps it only if it hashes exactly as recorded, and publishes a SOURCES.jsonl record that
the checker's existing index resolves (custody `job_cache`, re-hashed on every check).

Routes (from REQUESTS.jsonl, built by build_requests.py):
  archive  American Presidency Project pages re-read from their recorded Common Crawl or Wayback capture with
           Cassiodorus's own reader. The live APP site is never requested.
  live     files re-downloaded from their own URL through the shared fetch pool, which obeys robots.txt and
           paces each host.

Each run works through a bounded share (fetch counts, bytes and wall time), carries every earlier kept file
and attempt forward, and retries a failed fetch at most three times. A source whose bytes no longer hash as
recorded is reported and never kept under the recorded hash. Nothing here grades a source, authenticates an
original, or changes a claim, status or count.
"""
from __future__ import annotations

import concurrent.futures
import datetime as _dt
import hashlib
import json
import os
import shutil
import sys
import threading
import time
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "jobs/_lib"))
sys.path.insert(0, str(REPO / "jobs/cassiodorus"))
sys.path.insert(0, str(REPO / "jobs/app-executive-orders"))

ARCHIVE_FETCHES_PER_RUN = 6000      # Common Crawl ranges at one a second: under two hours
LIVE_FETCHES_PER_RUN = 3000
BYTES_PER_RUN = 900_000_000          # keeps each committed generation under a gigabyte
MAX_FILE_BYTES = 25_000_000
WALL_SECONDS = 150 * 60              # stop starting new fetches after this, well inside the runner's limit
MAX_ATTEMPTS = 3
FINAL = {"kept", "hash_mismatch", "blocked_by_robots_txt", "http_404", "http_410", "too_large"}
USER_AGENT = "EO-Historical-Research/1.0 (https://github.com/D3m0sthene5/Executive-Orders; source custody)"
EXT = {".pdf", ".html", ".htm", ".txt", ".xml", ".json"}


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def now():
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_jsonl(path):
    out = []
    p = Path(path)
    if p.is_file():
        with p.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except ValueError:
                        pass
    return out


def write_jsonl(path, rows):
    tmp = Path(str(path) + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def file_name(req, body=b""):
    ext = Path(urllib.parse.urlparse(req.get("url") or "").path).suffix.lower()
    if req.get("route") == "archive":
        ext = ".html"
    elif body[:5] == b"%PDF-":
        ext = ".pdf"
    elif ext not in EXT:
        ext = ".bin"
    return req["sha256"] + ext


def content_type(name):
    return {".pdf": "application/pdf", ".html": "text/html", ".htm": "text/html", ".txt": "text/plain",
            ".xml": "application/xml", ".json": "application/json"}.get(Path(name).suffix, "application/octet-stream")


def carry_forward(prior, out):
    """Copy the previous generation's kept files (re-hashed) and records into this run's output."""
    prior, out = Path(prior), Path(out)
    (out / "raw").mkdir(parents=True, exist_ok=True)
    kept = {}
    if prior.resolve() != out.resolve() and (prior / "raw").is_dir():
        for p in (prior / "raw").iterdir():
            if p.is_file() and sha256(p.read_bytes()) == p.name.split(".")[0]:
                dst = out / "raw" / p.name
                try:
                    os.link(p, dst)
                except OSError:
                    shutil.copyfile(p, dst)
    for p in (out / "raw").iterdir():
        if p.is_file():
            kept[p.name.split(".")[0]] = p.name
    sources = {r["sha256"]: r for r in read_jsonl(prior / "SOURCES.jsonl") if r.get("sha256") in kept}
    ledger = {r["sha256"]: r for r in read_jsonl(prior / "LEDGER.jsonl") if r.get("sha256")}
    return kept, sources, ledger


class Budget:
    def __init__(self, started, wall=WALL_SECONDS, max_bytes=BYTES_PER_RUN):
        self.started, self.wall, self.max_bytes = started, wall, max_bytes
        self.bytes, self.lock = 0, threading.Lock()

    def open(self):
        with self.lock:
            return self.bytes < self.max_bytes and time.monotonic() - self.started < self.wall

    def add(self, n):
        with self.lock:
            self.bytes += n


def run(job_dir, out, cache, prior=None, fetch_archive=None, pool=None, budget=None,
        archive_limit=ARCHIVE_FETCHES_PER_RUN, live_limit=LIVE_FETCHES_PER_RUN):
    job_dir, out, cache = Path(job_dir), Path(out), Path(cache)
    out.mkdir(parents=True, exist_ok=True)
    started = now()
    kept, sources, ledger = carry_forward(prior or out, out)
    requests = read_jsonl(job_dir / "REQUESTS.jsonl")
    budget = budget or Budget(time.monotonic())
    lock = threading.Lock()

    def due(req):
        sha = req["sha256"]
        if sha in kept:
            return False
        prev = ledger.get(sha, {})
        if prev.get("result") == "kept":
            return True  # recorded as kept, but the carried file is missing or no longer hashes: fetch again
        return prev.get("result") not in FINAL and int(prev.get("attempts", 0)) < MAX_ATTEMPTS

    def record(req, result, note="", body=None, how=""):
        sha = req["sha256"]
        with lock:
            prev = ledger.get(sha, {})
            ledger[sha] = {"sha256": sha, "url": req.get("url", ""), "route": req["route"], "result": result,
                           "attempts": int(prev.get("attempts", 0)) + 1, "last_utc": now(), "note": note[:300]}
            if body is not None:
                name = file_name(req, body)
                tmp = out / "raw" / (name + ".tmp")
                tmp.write_bytes(body)
                os.replace(tmp, out / "raw" / name)
                kept[sha] = name
                sources[sha] = {
                    "source_id": "ptolemy-" + sha[:12], "instrument_ids": req.get("instrument_ids", []),
                    "url": req.get("url", ""), "sha256": sha, "bytes": len(body), "content_type": content_type(name),
                    "retrieved_utc": started, "route": "job:ptolemy-custody:" + req["route"],
                    "page_or_item": how, "cache_path": "raw/" + name,
                    "notes": "Bytes kept so the checker can re-hash them; they hash exactly as first recorded. "
                             "Custody only: no grade, identity or finding."}

    def keep_if_exact(req, body, how):
        got = sha256(body)
        if got != req["sha256"]:
            record(req, "hash_mismatch", f"re-read bytes hash to {got}; not kept under the recorded hash")
            return
        budget.add(len(body))
        record(req, "kept", body=body, how=how)

    archive = [r for r in requests if r.get("route") == "archive" and due(r)]
    live = [r for r in requests if r.get("route") == "live" and due(r)]
    counts = {"archive_due": len(archive), "live_due": len(live)}

    def do_archive():
        import cassiodorus
        import app_mirror as M
        fetch = fetch_archive or cassiodorus.fetch_bytes
        throttles = {"cc": M.Throttle(1.0), "wayback": M.Throttle(2.0)}
        failures = 0
        for req in archive[:archive_limit]:
            if not budget.open() or failures >= 25:
                break
            cap = req.get("capture") or {}
            row = {"url": cap.get("url") or req.get("url"), "capture": {
                "archive": cap.get("archive"), "crawl": cap.get("crawl", ""), "cc_digest": cap.get("cc_digest", ""),
                "warc_filename": cap.get("warc_filename"), "warc_offset": cap.get("warc_offset"),
                "warc_length": cap.get("warc_length"), "wayback_url": cap.get("wayback_url")}}
            try:
                body, how = fetch({"kind": "mirror", "row": row}, cache, throttles)
                failures = 0
            except Exception as exc:  # noqa: BLE001 (every failure is recorded)
                failures += 1
                record(req, "fetch_failed", f"{type(exc).__name__}: {exc}")
                continue
            keep_if_exact(req, body, f"American Presidency Project page; {how}; captured {cap.get('captured_utc', '')}")

    def do_live():
        import fetch_pool as F
        p = pool or F.FetchPool(cache / "live", workers=8, per_host=2, max_bytes=MAX_FILE_BYTES,
                                user_agent=USER_AGENT, min_interval=0.5,
                                max_cache_bytes=int(os.environ.get("JOB_CACHE_MB", "1024")) * 1024 * 1024)

        def one(req):
            if not budget.open():
                return
            try:
                got = p.fetch(req["url"])
            except Exception as exc:  # noqa: BLE001
                msg = str(exc)
                result = ("blocked_by_robots_txt" if "robots_txt" in msg else "http_404" if "HTTP 404" in msg
                          else "http_410" if "HTTP 410" in msg else "too_large" if "exceeds bound" in msg
                          else "fetch_failed")
                record(req, result, f"{type(exc).__name__}: {msg}")
                return
            keep_if_exact(req, got["body"], f"downloaded from {got['final_url']}")
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
            list(ex.map(one, live[:live_limit]))

    threads = [threading.Thread(target=do_archive), threading.Thread(target=do_live)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    write_jsonl(out / "SOURCES.jsonl", [sources[s] for s in sorted(sources) if s in kept])
    write_jsonl(out / "LEDGER.jsonl", [ledger[s] for s in sorted(ledger)])
    results = {}
    for r in ledger.values():
        results[r["result"]] = results.get(r["result"], 0) + 1
    wanted = {r["sha256"] for r in requests}
    remaining = sum(1 for r in requests if due(r))
    summary = {
        "job": "ptolemy-custody", "generated_utc": started, "requests": len(requests),
        "kept_total": sum(1 for s in kept if s in wanted), "kept_this_run_bytes": budget.bytes,
        "outcomes_all_runs": dict(sorted(results.items())), "still_due": remaining, "this_run": counts,
        "orders_with_a_kept_source": len({i for s, r in sources.items() if s in kept for i in r.get("instrument_ids", [])}),
        "limits": {"archive_fetches_per_run": archive_limit, "live_fetches_per_run": live_limit,
                   "bytes_per_run": budget.max_bytes, "max_file_bytes": MAX_FILE_BYTES, "wall_seconds": budget.wall,
                   "max_attempts": MAX_ATTEMPTS},
        "statuses_changed": 0, "legal_conclusions": 0,
        "notice": "Custody only: kept bytes hash exactly as first recorded; nothing here grades or authenticates a source."}
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("kept_total", "still_due", "outcomes_all_runs")}), flush=True)
    return summary
