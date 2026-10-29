"""Cotton: commit the exact bytes of web sources that lifecycle claims cite, so every checker can re-hash them.

Named for Sir Robert Cotton (1571-1631), whose library preserved manuscripts that would otherwise have been lost.

The American Presidency Project (APP) mirror saved each page's text and the page's SHA-256, but not the page
bytes, so the claim checker could only record custody ("custody_record_only"). Cotton fetches each cited page
again from the same fixed source, keeps it only if its SHA-256 equals the recorded one, and publishes it with a
SOURCES.jsonl record whose cache_path points at the committed copy. The claim checker then re-hashes those bytes.

Routes, tried in this order for each wanted hash:
- archive capture: the exact Common Crawl WARC byte range, or the Wayback raw capture, recorded in
  jobs/app-executive-orders/output/MIRROR_DOCUMENTS.jsonl, decoded exactly as app_mirror.split_warc did;
- live page: the cited https URL, for pages harvested live (DOCUMENTS.jsonl); kept only if unchanged;
- Commons file: a https://commons.wikimedia.org/wiki/File: URL via Special:FilePath, up to MAX_BYTES.
A hash that no route reproduces is listed in FAILURES.jsonl and nothing is published for it.

Wanted hashes: every source sha256 cited in research/readiness/claims/*.jsonl, plus data/WANTED.jsonl
(hash and URL pairs for claims awaiting completion). No legal finding; no status or count changes.

Archive successors: a wanted hash that is a live APP page (DOCUMENTS.jsonl) cannot be re-proven once the page
changes. When the archive lane holds a capture of the same page (MIRROR_DOCUMENTS.jsonl, including rows the
poggio-archive-backfill job has not yet merged), Cotton also preserves that capture and marks it successor_of
the live hash, so a claim can be re-cited to bytes that stay provable. The live hash itself is unchanged.
"""
import gzip
import hashlib
import json
import os
import time
import urllib.request
from pathlib import Path

CC_DATA = "https://data.commoncrawl.org/"
COMMONS_FILE = "https://commons.wikimedia.org/wiki/File:"
MAX_BYTES = 60_000_000
AGENT = "EO-afterlife-research/1.0 (cotton-capture-custody)"
# Archive-lane captures: the APP job's own file, then rows the Poggio backfill job has not yet merged into it.
CAPTURE_FILES = ("jobs/app-executive-orders/output/MIRROR_DOCUMENTS.jsonl",
                 "jobs/poggio-archive-backfill/output/MIRROR_DOCUMENTS.jsonl")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def warc_response_body(raw):
    """(target URI, HTTP body) of one gzip WARC response record, decoded the way app_mirror.split_warc does."""
    data = gzip.decompress(raw)
    warc_block, rest = data.split(b"\r\n\r\n", 1)
    http_block, body = rest.split(b"\r\n\r\n", 1)
    warc = {k.strip().lower(): v.strip() for k, _, v in
            (line.partition(":") for line in warc_block.decode("utf-8", "replace").splitlines()[1:])}
    http = {k.strip().lower(): v.strip() for k, _, v in
            (line.partition(":") for line in http_block.decode("latin-1").splitlines()[1:])}
    if warc.get("warc-type") != "response" or "warc-truncated" in warc:
        raise ValueError("not a complete WARC response record")
    if http.get("transfer-encoding", "").lower() == "chunked":
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
        body = b"".join(out)
    if http.get("content-encoding", "").lower() in ("gzip", "x-gzip"):
        body = gzip.decompress(body)
    return (warc.get("warc-target-uri") or "").strip("<>"), body


def http_get(url, headers=None, tries=3):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": AGENT, **(headers or {})})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read(MAX_BYTES + 1)
        except Exception:  # noqa: BLE001  (offline, blocked, timeout: retried, then a recorded failure)
            if attempt + 1 == tries:
                raise
            time.sleep(2 * (attempt + 1))


def wanted(repo, job_dir):
    """sha256 -> {"url", "instrument_ids"} from published claims and data/WANTED.jsonl."""
    out = {}

    def add(sha, url, iid):
        if isinstance(sha, str) and len(sha) == 64:
            rec = out.setdefault(sha.lower(), {"url": None, "instrument_ids": set()})
            if url and not rec["url"]:
                rec["url"] = url
            if iid:
                rec["instrument_ids"].add(iid)

    def walk(node, iid):
        if isinstance(node, dict):
            if "sha256" in node:
                add(node.get("sha256"), node.get("url"), node.get("instrument_id") or iid)
            for v in node.values():
                walk(v, iid)
        elif isinstance(node, list):
            for v in node:
                walk(v, iid)

    for path in sorted((Path(repo) / "research/readiness/claims").glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                claim = json.loads(line)
            except ValueError:
                continue
            if isinstance(claim, dict):
                walk(claim, claim.get("instrument_id"))
    extra = Path(job_dir) / "data" / "WANTED.jsonl"
    if extra.is_file():
        for line in extra.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                add(r.get("sha256"), r.get("url"), r.get("instrument_id"))
    return out


def captures(repo):
    """sha256 -> archive capture pointer (APP mirror, including unmerged Poggio backfill rows)."""
    out = {}
    for rel in CAPTURE_FILES:
        path = Path(repo) / rel
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if isinstance(r.get("capture"), dict) and r.get("sha256") and r["sha256"] not in out:
                out[r["sha256"]] = dict(r["capture"], url=r.get("url"), page_or_item=r.get("heading"))
    return out


def add_archive_successors(want, caps, live):
    """Add the archive capture of each wanted live APP page (same URL) to want; returns how many were added."""
    by_url = {}
    for sha, cap in sorted(caps.items()):
        by_url.setdefault(cap.get("url"), []).append(sha)
    added = 0
    for sha, w in sorted(want.items()):
        url = live.get(sha)
        if not url or sha in caps:
            continue
        for succ in by_url.get(url, []):
            if succ not in want:
                want[succ] = {"url": url, "instrument_ids": set(w["instrument_ids"]), "successor_of": sha}
                added += 1
    return added


def live_pages(repo):
    """sha256 -> URL for APP pages harvested live (DOCUMENTS.jsonl)."""
    out = {}
    path = Path(repo) / "jobs/app-executive-orders/output/DOCUMENTS.jsonl"
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r.get("sha256") and r.get("url"):
                out[r["sha256"]] = r["url"]
    return out


def fetch_capture(cap, get=http_get):
    if cap.get("archive") == "common-crawl":
        name, offset, length = cap["warc_filename"], int(cap["warc_offset"]), int(cap["warc_length"])
        if not name.startswith("crawl-data/") or ".." in name or length <= 0:
            raise ValueError("unusable WARC pointer")
        raw = get(CC_DATA + name, {"Range": f"bytes={offset}-{offset + length - 1}"})
        if len(raw) != length:
            raise ValueError(f"range read returned {len(raw)} of {length} bytes")
        uri, body = warc_response_body(raw)
        if cap.get("url") and uri != cap["url"]:
            raise ValueError("capture URI mismatch: " + uri)
        return body, "archive/common-crawl " + cap.get("captured_utc", "")
    if cap.get("archive") == "wayback":
        url = cap.get("wayback_url") or ""
        if not url.startswith("https://web.archive.org/web/") or "id_/" not in url:
            raise ValueError("unusable Wayback URL")
        return get(url), "archive/wayback " + cap.get("captured_utc", "")
    raise ValueError("unknown archive")


def candidates(sha, want, caps, live):
    """[(route label, zero-argument fetcher)] in preference order."""
    out = []
    if sha in caps:
        out.append(("capture", lambda get: fetch_capture(caps[sha], get)))
    url = live.get(sha) or want.get("url") or ""
    host = url.split("/")[2] if url.startswith("https://") else ""
    # No live route: APP asks crawlers for a 10-second delay and a live page that has changed can never be
    # re-proven, so Cotton reads only fixed archive captures and Commons files.
    if url.startswith(COMMONS_FILE):
        file_url = "https://commons.wikimedia.org/wiki/Special:FilePath/" + url[len(COMMONS_FILE):]
        out.append(("commons", lambda get: (get(file_url), "commons " + file_url)))
    return out


def run(repo, job_dir, out_dir, get=http_get, limit=None):
    repo, out_dir = Path(repo), Path(out_dir)
    (out_dir / "captures").mkdir(parents=True, exist_ok=True)
    want = wanted(repo, job_dir)
    caps, live = captures(repo), live_pages(repo)
    cited = len(want)
    successors = add_archive_successors(want, caps, live)
    # Bytes already committed by an earlier run are re-hashed and kept without a new download.
    prior = Path(job_dir) / "output" / "captures"
    sources, failures = [], []
    for n, (sha, w) in enumerate(sorted(want.items())):
        if limit is not None and n >= limit:
            break
        routes = candidates(sha, w, caps, live)
        if not routes:
            continue  # not a web source Cotton can reproduce (held PDFs, scans, books)
        dest = out_dir / "captures" / (sha + ".bin")
        kept = prior / (sha + ".bin")
        how = None
        if kept.is_file() and sha256(kept.read_bytes()) == sha:
            dest.write_bytes(kept.read_bytes())
            how = "kept from an earlier Cotton run"
        else:
            errors = []
            for label, fetch in routes:
                try:
                    body, how = fetch(get)
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{label}: {type(exc).__name__}: {str(exc)[:160]}")
                    continue
                if len(body) > MAX_BYTES:
                    errors.append(f"{label}: larger than {MAX_BYTES} bytes")
                    continue
                if sha256(body) != sha:
                    errors.append(f"{label}: bytes differ from the recorded hash")
                    how = None
                    continue
                dest.write_bytes(body)
                break
            else:
                how = None
            if how is None:
                failures.append({"sha256": sha, "url": w["url"], "instrument_ids": sorted(w["instrument_ids"]),
                                 "errors": errors, **({"successor_of": w["successor_of"]} if "successor_of" in w else {})})
                continue
        cap = caps.get(sha, {})
        sources.append({"sha256": sha, "url": w["url"] or cap.get("url") or live.get(sha), "bytes": dest.stat().st_size,
                        "cache_path": "captures/" + dest.name, "route": "cotton: " + how,
                        "page_or_item": cap.get("page_or_item") or "web page bytes re-fetched and re-hashed",
                        "instrument_ids": sorted(w["instrument_ids"]),
                        "note": "Exact bytes whose SHA-256 equals the recorded source hash. Custody copy only; no "
                                "legal finding.",
                        **({"successor_of": w["successor_of"]} if "successor_of" in w else {})})
    write_jsonl(out_dir / "SOURCES.jsonl", sources)
    write_jsonl(out_dir / "FAILURES.jsonl", failures)
    summary = {"wanted_hashes": cited, "archive_successors": successors,
               "published": len(sources), "failed": len(failures),
               "not_web_sources": len(want) - len(sources) - len(failures) if limit is None else None}
    (out_dir / "SUMMARY.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    print(json.dumps(run(os.environ.get("REPO_ROOT", "."), os.environ.get("JOB_DIR", here),
                         os.environ.get("OUTPUT_DIR", here / "output"))))
