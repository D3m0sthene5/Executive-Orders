"""APP archive lane: read public web-archive captures of APP order pages instead of asking APP.

Explicit local invocation only; this is not an automatically scheduled job.py.

The live harvester (app_harvest.py documents) honours APP's robots.txt
Crawl-delay: 10, so 10,000 pages cost 30 hours. Common Crawl and the Wayback
Machine already hold captures of most APP /documents/executive-order-* pages.
Reading those captures loads the archives, not APP, so this lane runs several
workers and finishes in minutes. Nothing here sends a request to APP.

  cc-index       ask index.commoncrawl.org which crawls captured each APP order
                 page (newest crawl wins) -> output/MIRROR_INDEX.jsonl
  wayback-index  same for paths Common Crawl lacks, from the Wayback CDX API
  documents      read each capture (WARC byte range from data.commoncrawl.org,
                 or web.archive.org/web/<ts>id_/<url> original bytes), parse it
                 with app_harvest.parse_document, and write MIRROR_DOCUMENTS,
                 MIRROR_SOURCES, MIRROR_FRAGMENTS, MIRROR_ATTEMPTS,
                 MIRROR_FAILURES and texts/<slug>.txt

Handoff with the live lane: this lane walks the queue in the opposite order
(highest EO number first) and re-reads DOCUMENTS.jsonl every minute, so the two
never fetch the same page. Once this lane is done, app_harvest.py's documents
phase skips every path in MIRROR_DOCUMENTS.jsonl (except an audit sample) and
only the residue costs 10 s a page.

Live-only backfill (see CHANGE_NOTES.md): pages the live lane saved first have a
page hash that can never be re-proven, because the live page changes. These
phases find and read archive captures of exactly those pages and only append:

  seed                print the numbered orders in DOCUMENTS.jsonl whose instrument
                      id has no MIRROR_DOCUMENTS.jsonl row (offline)
  backfill-index      for seed pages with no capture pointer at all, ask older Common
                      Crawl crawls, then the Wayback CDX one URL at a time
  backfill-documents  read the capture of each seed page and append MIRROR_* rows; the
                      capture text goes to texts/<slug>.capture.txt so the live text
                      is never overwritten
  merge               append a backfill output folder (--from) to --out (offline)

Every request goes through http_get, which refuses any host but the three archive
hosts (also on redirects); lock_to_archives() additionally refuses DNS lookups of
any other host for the whole process. Nothing here can request APP.

A capture is the APP editorial page as it was on the capture date, not an
original: every record carries acceptable_as_original=false, the archive, crawl
and capture date, and no legal or status finding.
"""
import argparse
import concurrent.futures
from datetime import datetime, timezone
import gzip
import hashlib
import http.client
import json
from pathlib import Path
import os
import random
import re
import socket
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import app_harvest as live  # parse_document, instrument_id, text_name, sort_key, lines, append, write_json, stamp, sha
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "jobs/source-ladder"))
import fetch_ladder

USER_AGENT = "EO-Historical-Research/1.0 (https://github.com/D3m0sthene5/Executive-Orders; archive reader)"
CC_INDEX = "https://index.commoncrawl.org/"
CC_DATA = "https://data.commoncrawl.org/"
WAYBACK_CDX = "https://web.archive.org/cdx/search/cdx"
WAYBACK_RAW = "https://web.archive.org/web/{ts}id_/{url}"
PATTERN = "www.presidency.ucsb.edu/documents/executive-order-*"
MIRROR_FILES = ("MIRROR_DOCUMENTS.jsonl", "MIRROR_SOURCES.jsonl", "MIRROR_FRAGMENTS.jsonl",
                "MIRROR_ATTEMPTS.jsonl", "MIRROR_FAILURES.jsonl")
# The only hosts this lane may contact. APP (live.HOST) is deliberately absent.
ARCHIVE_HOSTS = frozenset({"index.commoncrawl.org", "data.commoncrawl.org", "web.archive.org"})
assert live.HOST not in ARCHIVE_HOSTS
CAPTURE_TEXT_SUFFIX = ".capture.txt"  # backfill: capture text beside the live text, never over it


class ArchiveError(RuntimeError):
    pass


class ArchiveRefused(RuntimeError):
    """A request to a host outside ARCHIVE_HOSTS. Never retried, never caught as a network error."""


def require_archive_host(url):
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or (parts.hostname or "").lower() not in ARCHIVE_HOSTS:
        raise ArchiveRefused("request refused, not an archive host: " + url[:200])
    return url


class _ArchiveOnlyRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        require_archive_host(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_OPENER = urllib.request.build_opener(_ArchiveOnlyRedirects)


def lock_to_archives():
    """Refuse DNS lookups of every host but the archives (and a configured proxy) for this process.

    Returns the original socket.getaddrinfo so a test can restore it. With this in place even code that
    bypasses http_get cannot reach APP directly.
    """
    allowed = set(ARCHIVE_HOSTS)
    for var in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
        value = os.environ.get(var) or ""
        if value:
            host = urllib.parse.urlsplit(value if "://" in value else "http://" + value).hostname
            if host and host.lower() != live.HOST:
                allowed.add(host.lower())
    original = socket.getaddrinfo

    def guarded(host, *args, **kwargs):
        name = (host.decode() if isinstance(host, bytes) else str(host or "")).lower().rstrip(".")
        if name not in allowed:
            raise ArchiveRefused("DNS lookup refused, not an archive host: " + name)
        return original(host, *args, **kwargs)

    socket.getaddrinfo = guarded
    return original


class Throttle:
    """At most one request start per `interval` seconds per host, shared by all workers."""

    def __init__(self, interval):
        self.interval, self.lock, self.next_at = interval, threading.Lock(), 0.0

    def wait(self):
        with self.lock:
            at = max(time.monotonic(), self.next_at)
            self.next_at = at + self.interval
        delay = at - time.monotonic()
        if delay > 0:
            time.sleep(delay)


def http_get(url, headers=None, timeout=90, tries=6, throttle=None):
    """GET with backoff on 429/5xx and network errors. Returns (status, headers, bytes).

    Only https URLs on ARCHIVE_HOSTS are requested; anything else (and any redirect elsewhere) raises
    ArchiveRefused before a connection is made.
    """
    require_archive_host(url)
    last = None
    for attempt in range(tries):
        if throttle:
            throttle.wait()
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
        try:
            with _OPENER.open(req, timeout=timeout) as r:
                return r.status, {k.lower(): v for k, v in r.headers.items()}, r.read()
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return e.code, {k.lower(): v for k, v in e.headers.items()}, b""
            last = f"HTTP {e.code}"
            if e.code not in (429, 500, 502, 503, 504):
                raise ArchiveError(last)
        except (urllib.error.URLError, TimeoutError, OSError, ConnectionError, http.client.HTTPException) as e:
            # IncompleteRead (a response cut short by the archive server) is an HTTPException, not an OSError.
            last = type(e).__name__ + ": " + str(e)[:120]
        time.sleep(min(60, 3 * 2 ** attempt) + random.random())
    raise ArchiveError("gave up after retries: " + str(last))


# --------------------------------------------------------------------------
# Index phases
# --------------------------------------------------------------------------

def cc_collections(limit):
    status, _, raw = http_get(CC_INDEX + "collinfo.json")
    cols = [c["id"] for c in json.loads(raw.decode("utf-8"))]
    return cols[:limit]


def cc_query(crawl, throttle):
    """All status-200 HTML captures of PATTERN in one crawl; [] when the crawl has none or no index."""
    base = f"{CC_INDEX}{crawl}-index?url={urllib.parse.quote(PATTERN, safe='*')}&output=json&filter==status:200"
    status, _, raw = http_get(base + "&showNumPages=true", throttle=throttle)
    if status != 200:
        return []
    try:
        pages = int(json.loads(raw.decode("utf-8"))["pages"])
    except (ValueError, KeyError):
        return []
    records = []
    for page in range(pages):
        for attempt in range(4):
            status, _, raw = http_get(f"{base}&page={page}", throttle=throttle)
            text = raw.decode("utf-8", "replace")
            rows, bad = [], 0
            for line in text.splitlines():
                if not line.startswith("{"):
                    continue
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    bad += 1
            if status == 200 and not bad:
                break
            time.sleep(5 * (attempt + 1))
        else:
            raise ArchiveError(f"{crawl} page {page}: index response stayed corrupt")
        records.extend(rows)
    return records


def normalise_path(url):
    p = urllib.parse.urlsplit(url)
    return p.path if p.hostname in ("www.presidency.ucsb.edu", "presidency.ucsb.edu") else ""


def run_cc_index(out, crawls, throttle):
    index = {r["path"] for r in live.lines(out / "INDEX.jsonl")}
    best = {}
    for crawl in crawls:
        try:
            records = cc_query(crawl, throttle)
        except ArchiveError as exc:
            print(f"{crawl}: skipped ({exc})", flush=True)
            continue
        new = 0
        for r in records:
            path = normalise_path(r.get("url", ""))
            if path not in index or r.get("mime", "text/html") != "text/html" or r.get("status") != "200":
                continue
            cap = {"path": path, "archive": "common-crawl", "crawl": crawl, "timestamp": r["timestamp"],
                   "url": r["url"], "digest": r.get("digest", ""), "warc_filename": r["filename"],
                   "warc_offset": int(r["offset"]), "warc_length": int(r["length"])}
            if path not in best or cap["timestamp"] > best[path]["timestamp"]:
                best[path] = cap
                new += 1
        print(f"{crawl}: {len(records)} captures, {new} new or newer; covered {len(best)}/{len(index)}", flush=True)
    write_captures(out, best, "common-crawl")


def wayback_cdx_url():
    return (f"{WAYBACK_CDX}?url={urllib.parse.quote(PATTERN, safe='*')}&output=json&filter=statuscode:200"
            "&filter=mimetype:text/html&collapse=urlkey&fl=original,timestamp,digest")


def run_wayback_index(out, cache, throttle):
    index = {r["path"] for r in live.lines(out / "INDEX.jsonl")}
    have = {c["path"] for c in live.lines(out / "MIRROR_INDEX.jsonl")}
    cached = cache / "wayback" / "cdx.json"  # a same-day CDX answer is reused; delete it to ask again
    if cached.is_file() and time.time() - cached.stat().st_mtime < 86400 and cached.read_bytes().lstrip().startswith(b"["):
        raw = cached.read_bytes()
    else:
        status, _, raw = http_get(wayback_cdx_url(), timeout=600, throttle=throttle)
        if status != 200 or not raw.lstrip().startswith(b"["):
            raise ArchiveError("Wayback CDX unavailable (status %s)" % status)
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_bytes(raw)
    rows = json.loads(raw.decode("utf-8"))[1:]
    best = {}
    for original, ts, digest in rows:
        path = normalise_path(original)
        if path in index and path not in have:
            cap = {"path": path, "archive": "wayback", "crawl": "", "timestamp": ts, "url": original,
                   "digest": digest, "warc_filename": "", "warc_offset": 0, "warc_length": 0}
            if path not in best or ts > best[path]["timestamp"]:
                best[path] = cap
    print(f"wayback: {len(rows)} captures, {len(best)} cover paths Common Crawl lacks", flush=True)
    write_captures(out, best, "wayback")


def write_captures(out, best, archive):
    """Merge new captures into MIRROR_INDEX.jsonl: one row per path and archive, the newest capture wins."""
    merged = {}
    for c in live.lines(out / "MIRROR_INDEX.jsonl") + list(best.values()):
        key = (c["path"], c["archive"])
        if key not in merged or c["timestamp"] > merged[key]["timestamp"]:
            merged[key] = c
    rows = sorted(merged.values(), key=lambda c: (c["path"], c["archive"]))
    with (out / "MIRROR_INDEX.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for c in rows:
            fh.write(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n")
    counts = {}
    for c in rows:
        counts[c["archive"]] = counts.get(c["archive"], 0) + 1
    live.write_json(out / "MIRROR_INDEX_SUMMARY.json", {"written_utc": live.stamp(), "captures": len(rows), "by_archive": counts,
                                                       "pattern": PATTERN})
    print(json.dumps({"captures": len(rows), "by_archive": counts}), flush=True)


# --------------------------------------------------------------------------
# Capture readers
# --------------------------------------------------------------------------

def split_warc(raw):
    """(warc_headers, http_headers, body) of one gzip WARC response record."""
    data = gzip.decompress(raw)
    try:
        warc_block, rest = data.split(b"\r\n\r\n", 1)
        http_block, body = rest.split(b"\r\n\r\n", 1)
    except ValueError:
        raise ArchiveError("malformed WARC record")
    warc = {}
    for line in warc_block.decode("utf-8", "replace").splitlines()[1:]:
        k, _, v = line.partition(":")
        warc[k.strip().lower()] = v.strip()
    http = {}
    for line in http_block.decode("latin-1").splitlines()[1:]:
        k, _, v = line.partition(":")
        http[k.strip().lower()] = v.strip()
    if warc.get("warc-type") != "response":
        raise ArchiveError("not a WARC response record: " + warc.get("warc-type", "?"))
    if "warc-truncated" in warc:
        raise ArchiveError("capture truncated: " + warc["warc-truncated"])
    if http.get("transfer-encoding", "").lower() == "chunked":
        body = dechunk(body)
    if http.get("content-encoding", "").lower() in ("gzip", "x-gzip"):
        body = gzip.decompress(body)
    length = int(warc.get("content-length", "0") or 0)
    return warc, http, body, length


def dechunk(body):
    out, i = [], 0
    while True:
        j = body.find(b"\r\n", i)
        if j < 0:
            break
        size = int(body[i:j].split(b";")[0].strip() or b"0", 16)
        if size == 0:
            break
        out.append(body[j + 2:j + 2 + size])
        i = j + 2 + size + 2
    return b"".join(out)


def read_cc(cap, cache, throttle):
    key = live.sha(f"{cap['warc_filename']}:{cap['warc_offset']}".encode())
    path = cache / "cc" / key[:2] / (key + ".warc.gz")
    if path.is_file():
        raw = path.read_bytes()
    else:
        end = cap["warc_offset"] + cap["warc_length"] - 1
        status, headers, raw = http_get(CC_DATA + cap["warc_filename"],
                                        {"Range": f"bytes={cap['warc_offset']}-{end}"}, throttle=throttle)
        if status not in (200, 206) or len(raw) != cap["warc_length"]:
            raise ArchiveError(f"range read returned {status}, {len(raw)} of {cap['warc_length']} bytes")
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(raw)
        tmp.replace(path)
    warc, http, body, _ = split_warc(raw)
    if (warc.get("warc-target-uri") or "").strip("<>") != cap["url"]:
        raise ArchiveError("capture URI mismatch: " + warc.get("warc-target-uri", ""))
    return body, {"archive": "common-crawl", "crawl": cap["crawl"], "captured_utc": warc.get("warc-date", ""),
                  "warc_record_id": warc.get("warc-record-id", ""), "warc_filename": cap["warc_filename"],
                  "warc_offset": cap["warc_offset"], "warc_length": cap["warc_length"], "cc_digest": cap["digest"],
                  "server_date": http.get("date", "")}


def read_wayback(cap, cache, throttle):
    key = live.sha(f"{cap['timestamp']}:{cap['url']}".encode())
    path = cache / "wayback" / key[:2] / (key + ".html")
    if path.is_file():
        body = path.read_bytes()
    else:
        status, headers, body = http_get(WAYBACK_RAW.format(ts=cap["timestamp"], url=cap["url"]), throttle=throttle)
        if status != 200:
            raise ArchiveError(f"wayback returned {status}")
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(body)
        tmp.replace(path)
    ts = cap["timestamp"]
    captured = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}T{ts[8:10]}:{ts[10:12]}:{ts[12:14]}Z"
    return body, {"archive": "wayback", "crawl": "", "captured_utc": captured, "cc_digest": cap["digest"],
                  "wayback_url": WAYBACK_RAW.format(ts=ts, url=cap["url"])}


# --------------------------------------------------------------------------
# Shared by the documents and backfill-documents phases
# --------------------------------------------------------------------------

def read_capture(cap, cache, throttle):
    reader = read_cc if cap["archive"] == "common-crawl" else read_wayback
    return reader(cap, cache, throttle)


def parse_capture(body, row):
    """(parsed page, instrument id) of a capture; PageFailure when it has no text or names another order."""
    doc = live.parse_document(live.check_page(body))
    if len(doc["text"]) < 40:
        raise live.PageFailure("no_usable_text")
    iid, _ = live.instrument_id(doc["heading"])
    if row["instrument_id"] and iid != row["instrument_id"]:
        raise live.PageFailure(f"identity_mismatch: listing {row['instrument_id']} page {iid}; heading={doc['heading']}")
    return doc, iid


def append_capture(out, cap, row, body, prov, doc, iid, text_rel, extra=None):
    """Write the capture text and append its MIRROR_DOCUMENTS, MIRROR_SOURCES and MIRROR_FRAGMENTS rows.

    `extra` adds fields to the MIRROR_DOCUMENTS row only (the backfill marks its rows there).
    """
    page_sha = live.sha(body)
    fetch_ladder.write_text_lf(out / text_rel, doc["text"] + "\n")
    text_sha = live.sha((out / text_rel).read_bytes())
    retrieved = live.stamp()
    record = {"instrument_id": iid, "path": cap["path"], "url": cap["url"], "final_url": cap["url"],
              "sha256": page_sha, "bytes": len(body), "retrieved_utc": retrieved,
              "route": "archive/" + cap["archive"], "capture": prov,
              "text_path": text_rel, "text_sha256": text_sha, "text_chars": len(doc["text"]),
              "listing_title": row["title"], "listing_date": row["date"],
              **{k: v for k, v in doc.items() if k != "text"}, **(extra or {})}
    live.append(out / "MIRROR_DOCUMENTS.jsonl", record)
    item = (doc["heading"] + "; " + doc["date_display"] + "; APP node " + doc["app_node"] +
            "; " + cap["archive"] + " capture " + prov["captured_utc"])
    source = {"source_id": "app-executive-orders:" + (iid or "node/" + doc["app_node"]) + ":" +
              cap["archive"] + ":" + page_sha[:12],
              "instrument_ids": [iid] if iid else [], "url": cap["url"],
              "archival_id": "app:node/" + doc["app_node"] if doc["app_node"] else "",
              "sha256": page_sha, "bytes": len(body), "retrieved_utc": retrieved,
              "captured_utc": prov["captured_utc"], "content_type": "text/html",
              "route": "archive/" + cap["archive"] + "/american-presidency-project",
              "page_or_item": item, "text_path": text_rel, "text_sha256": text_sha,
              "grade": "mirror_transcription", "representation_type": "secondary_compilation_transcription",
              "acceptable_as_original": False, "capture": prov,
              "notes": "American Presidency Project editorial transcription as captured by " + cap["archive"] +
                       " on " + prov["captured_utc"][:10] + "; not an original and possibly older than the live "
                       "APP page. Raw capture bytes are hashed but not committed; APP footnotes kept separately "
                       "in MIRROR_DOCUMENTS.jsonl. No legal finding."}
    live.append(out / "MIRROR_SOURCES.jsonl", source)
    if iid:
        data = {k: source[k] for k in ("source_id", "url", "sha256", "text_path", "text_sha256", "page_or_item",
                                       "archival_id", "grade", "representation_type", "acceptable_as_original",
                                       "captured_utc", "route")}
        data.update(needs_page_check=True, location_verified=False, location_confidence="medium",
                    app_date=doc["date"], app_footnote=doc["footnote"])
        live.append(out / "MIRROR_FRAGMENTS.jsonl", {
            "kind": "original_representation", "instrument_id": iid, "produced_by": "app-executive-orders",
            "grade": "mirror_transcription", "representation_type": "secondary_compilation_transcription",
            "acceptable_as_original": False, "data": data,
            "sources": [{k: source[k] for k in ("url", "sha256", "page_or_item", "archival_id")}],
            "confidence_note": "Listing and page headings agree on the EO number. Web-archive capture of an "
                               "APP editorial transcription; not an authenticated original, identity "
                               "authentication or legal conclusion."})
    return record


# --------------------------------------------------------------------------
# Documents phase
# --------------------------------------------------------------------------

def run_documents(out, cache, max_new, ids_file, workers, interval, archives):
    index = {r["path"]: r for r in live.lines(out / "INDEX.jsonl")}
    captures = [c for c in live.lines(out / "MIRROR_INDEX.jsonl") if c["archive"] in archives]
    if not index or not captures:
        raise SystemExit("Need output/INDEX.jsonl and output/MIRROR_INDEX.jsonl (run cc-index first)")
    for name in MIRROR_FILES:
        (out / name).touch(exist_ok=True)
    done = {d["path"] for d in live.lines(out / "MIRROR_DOCUMENTS.jsonl")}
    failed = {f["path"] for f in live.lines(out / "MIRROR_FAILURES.jsonl")}
    live_done = {d["path"] for d in live.lines(out / "DOCUMENTS.jsonl")}
    priority = set()
    if ids_file:
        priority = {s.strip() for s in Path(ids_file).read_text(encoding="utf-8").split() if s.strip()}
    queue = [c for c in captures if c["path"] not in done and c["path"] not in failed and c["path"] not in live_done]
    # Opposite order to the live lane (which ascends): priority first, highest EO number first.
    queue.sort(key=lambda c: (index[c["path"]].get("instrument_id") not in priority, live.sort_key(index[c["path"]])))
    queue = [c for c in queue if index[c["path"]].get("instrument_id") in priority][::-1] + \
            [c for c in queue if index[c["path"]].get("instrument_id") not in priority][::-1]
    queue = queue[:max_new]
    throttles = {"common-crawl": Throttle(interval), "wayback": Throttle(max(interval, 1.5))}
    write_lock, state_lock = threading.Lock(), threading.Lock()
    counts = {"saved": 0, "failed": 0, "skipped_live": 0}
    refreshed = [time.monotonic()]

    def checkpoint():
        state = {"updated_utc": live.stamp(), "indexed": len(index), "captures": len(captures),
                 "mirror_saved": len(done), "mirror_failed": len(failed), "live_saved": len(live_done),
                 "queue_left": max(0, len(queue) - counts["saved"] - counts["failed"] - counts["skipped_live"]),
                 "uncovered_by_any_lane": len(set(index) - done - live_done - {c["path"] for c in captures}),
                 "this_run": dict(counts)}
        live.write_json(out / "MIRROR_STATE.json", state)
        print(json.dumps(state), flush=True)

    def one(cap):
        row = index[cap["path"]]
        with state_lock:
            if time.monotonic() - refreshed[0] > 60:
                live_done.update(d["path"] for d in live.lines(out / "DOCUMENTS.jsonl"))
                refreshed[0] = time.monotonic()
            if cap["path"] in live_done:
                counts["skipped_live"] += 1
                return
        entry = {"kind": "document", "path": cap["path"], "instrument_id": row["instrument_id"],
                 "archive": cap["archive"], "capture_timestamp": cap["timestamp"], "attempted_utc": live.stamp()}
        try:
            body, prov = read_capture(cap, cache, throttles[cap["archive"]])
            doc, iid = parse_capture(body, row)
            text_rel = "texts/" + live.text_name(cap["path"]) + ".txt"
            with write_lock:
                if cap["path"] in live_done:
                    counts["skipped_live"] += 1
                    return
                append_capture(out, cap, row, body, prov, doc, iid, text_rel)
                done.add(cap["path"])
                counts["saved"] += 1
                entry["result"] = "saved"
        except Exception as exc:
            entry.update(result="failed", reason=str(exc)[:500], error_type=type(exc).__name__)
            with write_lock:
                counts["failed"] += 1
                # Archive outages and short reads are retried by the next run; only the capture's own
                # content (no text, identity mismatch, truncated record) is a permanent failure.
                if isinstance(exc, live.PageFailure) or "truncated" in str(exc):
                    failed.add(cap["path"])
                    live.append(out / "MIRROR_FAILURES.jsonl", entry)
        with write_lock:
            live.append(out / "MIRROR_ATTEMPTS.jsonl", entry)
            n = counts["saved"] + counts["failed"] + counts["skipped_live"]
        if n % 50 == 0:
            with state_lock:
                checkpoint()

    checkpoint()
    started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(one, queue))
    checkpoint()
    print(f"done in {time.monotonic() - started:.0f}s: {counts}", flush=True)


# --------------------------------------------------------------------------
# Live-only backfill: archive captures of pages the live lane saved first
# --------------------------------------------------------------------------
# `base` is the app-executive-orders output folder, only read. `out` receives appended rows; it may be
# `base` itself (local run) or a separate folder (the runner job), later appended to base by `merge`.

def live_only_ids(base):
    """Numbered orders in DOCUMENTS.jsonl whose instrument id has no MIRROR_DOCUMENTS.jsonl row, sorted."""
    mirrored = {d.get("instrument_id") for d in live.lines(base / "MIRROR_DOCUMENTS.jsonl")}
    ids = {d["instrument_id"] for d in live.lines(base / "DOCUMENTS.jsonl")
           if d.get("instrument_id") and d["instrument_id"] not in mirrored}
    return sorted(ids, key=lambda i: live.sort_key({"instrument_id": i, "path": ""}))


def read_ids(ids_file):
    return {s.strip() for s in Path(ids_file).read_text(encoding="utf-8").split() if s.strip()}


def _both(base, out, name):
    rows = live.lines(base / name)
    if out.resolve() != base.resolve():
        rows += live.lines(out / name)
    return rows


def backfill_targets(base, out, ids):
    """INDEX rows of seed orders whose page was saved live, has no capture saved yet and no permanent failure."""
    live_done = {d["path"] for d in live.lines(base / "DOCUMENTS.jsonl")}
    mirrored = {d["path"] for d in _both(base, out, "MIRROR_DOCUMENTS.jsonl")}
    failed = {f["path"] for f in _both(base, out, "MIRROR_FAILURES.jsonl")}
    return [r for r in live.lines(base / "INDEX.jsonl")
            if r.get("instrument_id") in ids and r["path"] in live_done
            and r["path"] not in mirrored and r["path"] not in failed]


def wayback_cdx_one_url(url):
    bare = re.sub(r"^https?://", "", url)
    return (f"{WAYBACK_CDX}?url={urllib.parse.quote(bare, safe='/')}&output=json&filter=statuscode:200"
            "&filter=mimetype:text/html&fl=original,timestamp,digest")


def run_backfill_index(base, out, ids, crawls, cc_throttle, wb_throttle, archives=("common-crawl", "wayback")):
    """Find a capture pointer for seed pages that have none. Appends to out/MIRROR_INDEX.jsonl only.

    Common Crawl first (newest crawl first, crawls already present in MIRROR_INDEX are skipped because the
    original cc-index run read them in full), stopping as soon as every target is covered; then one Wayback
    CDX request per page still uncovered. No request at all when every target already has a pointer.
    """
    targets = {r["path"]: r for r in backfill_targets(base, out, ids)}
    known = _both(base, out, "MIRROR_INDEX.jsonl")
    missing = set(targets) - {c["path"] for c in known}
    found, asked = {}, {"common-crawl": 0, "wayback": 0}
    print(f"backfill-index: {len(targets)} seed pages without a saved capture, {len(missing)} without any pointer",
          flush=True)
    if missing and "common-crawl" in archives:
        queried = {c["crawl"] for c in known if c["archive"] == "common-crawl"}
        for crawl in crawls() if callable(crawls) else crawls:
            if not missing:
                break
            if crawl in queried:
                continue
            asked["common-crawl"] += 1
            try:
                records = cc_query(crawl, cc_throttle)
            except ArchiveError as exc:
                print(f"{crawl}: skipped ({exc})", flush=True)
                continue
            hit = {}
            for r in records:
                path = normalise_path(r.get("url", ""))
                if path not in missing or r.get("mime", "text/html") != "text/html" or r.get("status") != "200":
                    continue
                cap = {"path": path, "archive": "common-crawl", "crawl": crawl, "timestamp": r["timestamp"],
                       "url": r["url"], "digest": r.get("digest", ""), "warc_filename": r["filename"],
                       "warc_offset": int(r["offset"]), "warc_length": int(r["length"])}
                if path not in hit or cap["timestamp"] > hit[path]["timestamp"]:
                    hit[path] = cap
            found.update(hit)
            missing -= set(hit)
            print(f"{crawl}: {len(records)} captures, {len(hit)} seed pages found; {len(missing)} still missing", flush=True)
    if missing and "wayback" in archives:
        for path in sorted(missing):
            asked["wayback"] += 1
            try:
                status, _, raw = http_get(wayback_cdx_one_url(targets[path]["url"]), throttle=wb_throttle)
                rows = json.loads(raw.decode("utf-8"))[1:] if status == 200 and raw.lstrip().startswith(b"[") else []
            except (ArchiveError, ValueError) as exc:
                print(f"wayback {path}: skipped ({exc})", flush=True)
                continue
            best = None
            for original, ts, digest in rows:
                if normalise_path(original) == path and (best is None or ts > best["timestamp"]):
                    best = {"path": path, "archive": "wayback", "crawl": "", "timestamp": ts, "url": original,
                            "digest": digest, "warc_filename": "", "warc_offset": 0, "warc_length": 0}
            if best:
                found[path] = best
        missing -= set(found)
    (out / "MIRROR_INDEX.jsonl").touch(exist_ok=True)
    have = {(c["path"], c["archive"]) for c in known}
    added = [c for p, c in sorted(found.items()) if (p, c["archive"]) not in have]
    for c in added:
        live.append(out / "MIRROR_INDEX.jsonl", c)
    result = {"targets": len(targets), "pointers_added": len(added), "requests_by_archive": asked,
              "no_capture_found": sorted(targets[p]["instrument_id"] for p in missing)}
    print(json.dumps(result), flush=True)
    return result


def run_backfill_documents(base, out, cache, ids, workers, interval, archives, max_new=100000):
    """Read the capture of every seed page and append MIRROR_* rows to `out`. Never touches the live rows.

    The identity check is the archive lane's own (listing number must equal the capture's heading number).
    The capture text goes to texts/<slug>.capture.txt; the live text at texts/<slug>.txt stays as it is.
    Each row also records whether the capture's text and page bytes agree with the live harvest.
    """
    for name in MIRROR_FILES:
        (out / name).touch(exist_ok=True)
    live_docs = {d["path"]: d for d in live.lines(base / "DOCUMENTS.jsonl")}
    targets = {r["path"]: r for r in backfill_targets(base, out, ids)}
    pointers = {}
    for c in _both(base, out, "MIRROR_INDEX.jsonl"):
        if c["path"] in targets and c["archive"] in archives:
            old = pointers.get(c["path"])
            # One capture per page: Common Crawl (exact WARC range) before Wayback, then the newest.
            rank = (c["archive"] == "common-crawl", c["timestamp"])
            if old is None or rank > (old["archive"] == "common-crawl", old["timestamp"]):
                pointers[c["path"]] = c
    queue = sorted(pointers.values(), key=lambda c: live.sort_key(targets[c["path"]]))[:max_new]
    throttles = {"common-crawl": Throttle(interval), "wayback": Throttle(max(interval, 1.5))}
    lock = threading.Lock()
    counts = {"saved": 0, "failed": 0, "retry_next_run": 0}

    def one(cap):
        row = targets[cap["path"]]
        entry = {"kind": "document", "path": cap["path"], "instrument_id": row["instrument_id"],
                 "archive": cap["archive"], "capture_timestamp": cap["timestamp"], "attempted_utc": live.stamp(),
                 "live_backfill": True}
        try:
            body, prov = read_capture(cap, cache, throttles[cap["archive"]])
            doc, iid = parse_capture(body, row)
            prior = live_docs[cap["path"]]
            if prior.get("instrument_id") != iid:
                raise live.PageFailure(f"identity_mismatch: live page {prior.get('instrument_id')} capture {iid}")
            text_rel = "texts/" + live.text_name(cap["path"]) + CAPTURE_TEXT_SUFFIX
            # write_text_lf writes these exact UTF-8 bytes, so this is the capture text's file hash.
            text_sha = live.sha((doc["text"] + "\n").encode("utf-8"))
            compare = {"live_retrieved_utc": prior.get("retrieved_utc", ""), "live_page_sha256": prior.get("sha256", ""),
                       "live_text_sha256": prior.get("text_sha256", ""), "page_agrees": prior.get("sha256") == live.sha(body),
                       "text_agrees": prior.get("text_sha256") == text_sha}
            with lock:
                record = append_capture(out, cap, row, body, prov, doc, iid, text_rel,
                                        extra={"live_backfill": True, "live_comparison": compare})
                if record["text_sha256"] != text_sha:
                    raise RuntimeError("capture text hash changed on write")
                counts["saved"] += 1
                entry.update(result="saved", text_agrees=compare["text_agrees"])
        except ArchiveRefused:
            raise
        except Exception as exc:
            entry.update(result="failed", reason=str(exc)[:500], error_type=type(exc).__name__)
            with lock:
                if isinstance(exc, live.PageFailure) or "truncated" in str(exc):
                    counts["failed"] += 1
                    live.append(out / "MIRROR_FAILURES.jsonl", entry)
                else:
                    counts["retry_next_run"] += 1
        with lock:
            live.append(out / "MIRROR_ATTEMPTS.jsonl", entry)

    started = time.monotonic()
    print(f"backfill-documents: {len(targets)} seed pages to back, {len(queue)} with a capture pointer", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(one, queue))
    remaining = backfill_targets(base, out, ids)
    state = {"updated_utc": live.stamp(), "seed_ids": len(ids), "targets_at_start": len(targets),
             "with_pointer": len(queue), "this_run": counts, "seconds": round(time.monotonic() - started),
             "still_without_capture": sorted(r["instrument_id"] for r in remaining)}
    live.write_json(out / "BACKFILL_STATE.json", state)
    print(json.dumps({k: v for k, v in state.items() if k != "still_without_capture"}), flush=True)
    return state


def _hash_file(path, size=None):
    h = hashlib.sha256()
    with path.open("rb") as fh:
        h.update(fh.read() if size is None else fh.read(size))
    return h.hexdigest()


def run_merge(src, base):
    """Append a backfill folder's rows and capture texts to base. Offline, idempotent, append-only.

    Every row is checked first (listing number = record number = heading number, capture route, text hash,
    no text overwritten); a single problem aborts before anything is written. Afterwards each base file is
    verified to begin with exactly its previous bytes.
    """
    index = {r["path"]: r for r in live.lines(base / "INDEX.jsonl")}
    have_docs = {d["path"] for d in live.lines(base / "MIRROR_DOCUMENTS.jsonl")}
    docs, seen = [], set()
    for d in live.lines(src / "MIRROR_DOCUMENTS.jsonl"):
        if d["path"] in have_docs or d["path"] in seen:
            continue
        seen.add(d["path"])
        listed = (index.get(d["path"]) or {}).get("instrument_id")
        heading = live.instrument_id(d.get("heading", ""))[0]
        problems = []
        if not d.get("route", "").startswith("archive/") or not isinstance(d.get("capture"), dict):
            problems.append("not an archive capture")
        if not (listed and listed == d.get("instrument_id") == heading):
            problems.append(f"identity: listing {listed} record {d.get('instrument_id')} heading {heading}")
        text = src / d.get("text_path", "")
        if not (d.get("text_path", "").endswith(CAPTURE_TEXT_SUFFIX) and text.is_file()
                and live.sha(text.read_bytes()) == d.get("text_sha256")):
            problems.append("capture text missing, misnamed or not matching its hash")
        elif (base / d["text_path"]).exists() and (base / d["text_path"]).read_bytes() != text.read_bytes():
            problems.append("would overwrite a different text")
        if problems:
            raise SystemExit(f"merge refused, nothing written: {d['path']}: {'; '.join(problems)}")
        docs.append(d)
    texts = {d["text_path"] for d in docs}
    have_index = {(c["path"], c["archive"]) for c in live.lines(base / "MIRROR_INDEX.jsonl")}
    seen_keys = lambda name: {(r.get("path"), r.get("attempted_utc")) for r in live.lines(base / name)}
    plan = {
        "MIRROR_INDEX.jsonl": [c for c in live.lines(src / "MIRROR_INDEX.jsonl") if (c["path"], c["archive"]) not in have_index],
        "MIRROR_DOCUMENTS.jsonl": docs,
        "MIRROR_SOURCES.jsonl": [s for s in live.lines(src / "MIRROR_SOURCES.jsonl") if s.get("text_path") in texts],
        "MIRROR_FRAGMENTS.jsonl": [f for f in live.lines(src / "MIRROR_FRAGMENTS.jsonl")
                                   if (f.get("data") or {}).get("text_path") in texts],
    }
    for name in ("MIRROR_ATTEMPTS.jsonl", "MIRROR_FAILURES.jsonl"):
        keys = seen_keys(name)
        plan[name] = [r for r in live.lines(src / name) if (r.get("path"), r.get("attempted_utc")) not in keys]
    before = {name: ((base / name).stat().st_size, _hash_file(base / name)) for name in plan if (base / name).is_file()}
    for rel in sorted(texts):
        (base / rel).parent.mkdir(parents=True, exist_ok=True)
        (base / rel).write_bytes((src / rel).read_bytes())
    for name, rows in plan.items():
        for r in rows:
            live.append(base / name, r)
    for name, (size, digest) in before.items():
        if _hash_file(base / name, size) != digest:
            raise SystemExit(f"merge broke append-only on {name}")
    counts = {name: len(rows) for name, rows in plan.items()}
    print(json.dumps({"merged_from": str(src), "texts": len(texts), "rows_appended": counts}), flush=True)
    return counts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("phase", choices=["cc-index", "wayback-index", "documents", "seed", "backfill-index",
                                      "backfill-documents", "merge"])
    ap.add_argument("--base", type=Path, default=HERE / "output",
                    help="backfill/merge: the app-executive-orders output folder (only read by backfill phases)")
    ap.add_argument("--from", dest="src", type=Path, help="merge: backfill output folder to append to --out")
    ap.add_argument("--download", action="store_true", help="Required to authorize network acquisition from the archives")
    ap.add_argument("--cache-dir", type=Path, help="Raw capture cache (not committed); reruns reuse it without new requests")
    ap.add_argument("--out", type=Path, default=HERE / "output")
    ap.add_argument("--crawls", type=int, default=12, help="cc-index: how many of the newest Common Crawl crawls to ask")
    ap.add_argument("--crawl-ids", help="cc-index: comma-separated crawl ids (CC-MAIN-2025-38,...) instead of --crawls")
    ap.add_argument("--max-new", type=int, default=100000)
    ap.add_argument("--ids-file", help="Whitespace-separated instrument IDs (EO:123) to fetch first")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--interval", type=float, default=0.25, help="Minimum seconds between request starts per archive")
    ap.add_argument("--archives", default="common-crawl,wayback")
    args = ap.parse_args()
    if args.phase == "seed":
        print("\n".join(live_only_ids(args.base)))
        return
    if args.phase == "merge":
        if not args.src:
            ap.error("merge needs --from <backfill output folder>")
        run_merge(args.src, args.out)
        return
    if not args.download or not args.cache_dir:
        ap.error("Use --download and --cache-dir explicitly; there is no automatic acquisition")
    args.out.mkdir(parents=True, exist_ok=True)
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    if args.phase == "cc-index":
        crawls = args.crawl_ids.split(",") if args.crawl_ids else cc_collections(args.crawls)
        run_cc_index(args.out, crawls, Throttle(1.0))
    elif args.phase == "wayback-index":
        run_wayback_index(args.out, args.cache_dir, Throttle(1.5))
    elif args.phase in ("backfill-index", "backfill-documents"):
        if not args.ids_file:
            ap.error(args.phase + " needs --ids-file (python app_mirror.py seed > ids.txt)")
        ids, archives = read_ids(args.ids_file), set(args.archives.split(","))
        if args.phase == "backfill-index":
            crawls = args.crawl_ids.split(",") if args.crawl_ids else (lambda: cc_collections(args.crawls))
            run_backfill_index(args.base, args.out, ids, crawls, Throttle(1.0), Throttle(1.5), archives)
        else:
            run_backfill_documents(args.base, args.out, args.cache_dir, ids, max(1, min(args.workers, 8)),
                                   args.interval, archives, args.max_new)
    else:
        run_documents(args.out, args.cache_dir, args.max_new, args.ids_file, max(1, min(args.workers, 8)),
                      args.interval, set(args.archives.split(",")))


if __name__ == "__main__":
    main()
