"""Official fixity: compare the project's sha256 for each govinfo file with GPO's own.

govinfo publishes a PREMIS preservation record for every package
(https://www.govinfo.gov/metadata/pkg/<package>/premis.xml) that lists the SHA-256
GPO computed for the package's files. For scanned Federal Register issues
(1936-1994) the issue PDF is the first object, a few KB into a record that can
be 17 MB, so each record is streamed and closed as soon as the file's digest is
read. Single-document PDFs (1995 on) are not listed in these records; they keep
the project's own sha256 only. The server ignores Range requests, so the job
never re-requests a record: one streamed GET per package, stopped early.

Outputs are custody evidence, never legal findings.
"""

import csv
import json
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

UA = "EO-afterlife-research/1.0 (owner-run research; github.com/D3m0sthene5)"
PREMIS = "https://www.govinfo.gov/metadata/pkg/{package}/premis.xml"
GOVINFO_FILE = re.compile(r"^https://www\.govinfo\.gov/content/pkg/([A-Za-z0-9._-]+)/pdf/([A-Za-z0-9._-]+\.pdf)$")
OBJECT = re.compile(r"<(?:premis:)?object\b.*?</(?:premis:)?object>", re.S)
NAME = re.compile(r"<(?:premis:)?originalName>\s*([^<]+?)\s*<")
ALG = re.compile(r"<(?:premis:)?messageDigestAlgorithm>\s*([^<]+?)\s*<")
DIGEST = re.compile(r"<(?:premis:)?messageDigest>\s*([0-9A-Fa-f]{32,128})\s*<")
COLUMNS = ["url", "package", "filename", "recorded_sha256", "gpo_sha256", "algorithm", "result",
           "detail", "premis_url", "premis_bytes_read", "checked_utc", "instrument_ids", "found_in"]


def now_utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def split_url(url):
    """(package, filename) for a govinfo package file URL, else None (fragments ignored)."""
    m = GOVINFO_FILE.match((url or "").split("#", 1)[0].split("?", 1)[0])
    return (m.group(1), m.group(2)) if m else None


def scan_premis(chunks, filename, max_bytes=262_144):
    """Read PREMIS text from an iterator of byte chunks until `filename`'s object is found.

    Returns (algorithm, digest_lowercase_or_None, bytes_read). Stops at the first
    object whose originalName equals filename; gives up after max_bytes (the issue
    PDF is the first object, about 2 KB in, so 256 KB is ample)."""
    buf, read = "", 0
    for data in chunks:
        read += len(data)
        buf += data.decode("utf-8", "replace")
        last = 0
        for m in OBJECT.finditer(buf):
            block = m.group(0)
            name = NAME.search(block)
            if name and name.group(1) == filename:
                alg, dig = ALG.search(block), DIGEST.search(block)
                return (alg.group(1) if alg else None), (dig.group(1).lower() if dig else None), read
            last = m.end()
        buf = buf[last:]
        if read >= max_bytes:
            break
    return None, None, read


def urllib_chunks(url, timeout=60, size=65536):
    """Stream a URL; the caller stops early simply by not consuming more chunks."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    resp = urllib.request.urlopen(req, timeout=timeout)

    def gen():
        try:
            while True:
                data = resp.read(size)
                if not data:
                    return
                yield data
        finally:
            resp.close()
    return gen()


def check_one(item, open_chunks=urllib_chunks, retries=2, sleep=time.sleep):
    pkg, name = item["package"], item["filename"]
    row = {k: "" for k in COLUMNS}
    row.update(url=item["url"], package=pkg, filename=name, recorded_sha256=" | ".join(sorted(item["shas"])),
               premis_url=PREMIS.format(package=pkg), checked_utc=now_utc(),
               instrument_ids=" | ".join(sorted(item["ids"])), found_in=" | ".join(sorted(item["found_in"])))
    if name != pkg + ".pdf":
        # Measured 2026-10-17: PREMIS records list only the package's own PDF, never
        # single-document granules, so there is nothing to fetch.
        row.update(result="not_listed", detail="single-document PDF: PREMIS lists only the package PDF",
                   premis_bytes_read=0)
        return row
    for attempt in range(retries + 1):
        try:
            alg, dig, read = scan_premis(open_chunks(row["premis_url"]), name)
            row["premis_bytes_read"] = read
            if not dig:
                row.update(result="not_listed",
                           detail="file not listed in the package's PREMIS record (single-document PDFs are not)")
            elif (alg or "").upper().replace("-", "") != "SHA256":
                row.update(result="other_algorithm", gpo_sha256=dig, algorithm=alg or "")
            else:
                row.update(gpo_sha256=dig, algorithm=alg)
                row["result"] = "match" if item["shas"] == {dig} else (
                    "mismatch" if dig not in item["shas"] else "partial_match")
                if row["result"] != "match":
                    row["detail"] = "project hashes: " + row["recorded_sha256"]
            return row
        except urllib.error.HTTPError as exc:
            if exc.code in (404, 410):
                row.update(result="no_premis_record", detail=f"HTTP {exc.code}")
                return row
            row.update(result="unavailable", detail=f"HTTP {exc.code}")
        except Exception as exc:  # timeouts, resets: retry, then report
            row.update(result="unavailable", detail=f"{type(exc).__name__}: {exc}"[:200])
        sleep(2 * (attempt + 1))
    return row


def collect_sources(repo):
    """Distinct govinfo files across every job's SOURCES.jsonl, fr-originals' full run and rule files."""
    repo = Path(repo)
    items = {}

    def add(url, sha, ids, where):
        parts = split_url(url)
        if not parts or not re.fullmatch(r"[0-9a-f]{64}", sha or ""):
            return
        key = url.split("#", 1)[0]
        it = items.setdefault(key, {"url": key, "package": parts[0], "filename": parts[1],
                                    "shas": set(), "ids": set(), "found_in": set()})
        it["shas"].add(sha)
        it["ids"].update(i for i in ids if isinstance(i, str))
        it["found_in"].add(where)

    paths = sorted(repo.glob("jobs/*/output/SOURCES.jsonl")) + sorted(repo.glob("jobs/*/data/full_run/SOURCES.jsonl"))
    for p in paths:
        where = p.relative_to(repo).as_posix()
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            # A record's sha256 is of the bytes its url served; skip excerpts and text-only records.
            if r.get("sha256_is_of_url_bytes") is False or r.get("usable_as_document") is False:
                continue
            add(r.get("url") or "", r.get("sha256"), r.get("instrument_ids") or [], where)
    for p in sorted(repo.glob("research/readiness/rules/*.json")):
        try:
            rule = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            continue
        src = rule.get("source") or {}
        add(src.get("url") or "", src.get("sha256"), [rule.get("acting_id")], p.relative_to(repo).as_posix())
    return sorted(items.values(), key=lambda x: x["url"])


def run(repo, out, prior_rows=None, workers=6, limit=None, open_chunks=urllib_chunks, log=print):
    """Check every file not already checked with the same recorded hash. Returns summary dict."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    items = collect_sources(repo)
    prior = {(r["url"], r["recorded_sha256"]): r for r in (prior_rows or [])
             if r.get("result") in ("match", "mismatch", "partial_match", "not_listed", "other_algorithm", "no_premis_record")}
    rows, todo = [], []
    for it in items:
        old = prior.get((it["url"], " | ".join(sorted(it["shas"]))))
        if old:
            old = dict(old, instrument_ids=" | ".join(sorted(it["ids"])), found_in=" | ".join(sorted(it["found_in"])))
            rows.append(old)
        else:
            todo.append(it)
    if limit is not None:
        todo = todo[:limit]
    log(f"{len(items)} govinfo files; {len(rows)} carried forward from earlier checks; checking {len(todo)} "
        f"with {workers} workers")
    t0, read_now = time.time(), 0
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for n, row in enumerate(pool.map(lambda it: check_one(it, open_chunks), todo), 1):
            rows.append(row)
            read_now += int(row.get("premis_bytes_read") or 0)
            if n % 250 == 0:
                log(f"  {n}/{len(todo)} checked ({time.time() - t0:.0f} s)")
    rows.sort(key=lambda r: r["url"])
    with open(out / "FIXITY.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    by_sha = {}
    for r in rows:
        if r["result"] == "match":
            by_sha[r["gpo_sha256"]] = {"url": r["url"], "gpo_sha256": r["gpo_sha256"], "premis_url": r["premis_url"],
                                      "checked_utc": r["checked_utc"], "result": "match"}
    with open(out / "MATCHED_BY_SHA256.json", "w", encoding="utf-8", newline="\n") as fh:
        json.dump(dict(sorted(by_sha.items())), fh, indent=1, sort_keys=True)
        fh.write("\n")
    counts = {}
    for r in rows:
        counts[r["result"]] = counts.get(r["result"], 0) + 1
    ids_matched = {i for r in rows if r["result"] == "match" for i in r["instrument_ids"].split(" | ") if i}
    summary = {
        "job": "official-fixity", "files": len(rows), "checked_this_run": len(todo),
        "carried_forward": len(rows) - len(todo), "results": dict(sorted(counts.items())),
        "orders_with_a_gpo_matched_file": len(ids_matched),
        "premis_bytes_read_this_run": read_now,
        "seconds": round(time.time() - t0, 1),
        "establishes": "byte-identity of the project's copy with GPO's published SHA-256; custody evidence only",
    }
    with open(out / "SUMMARY.json", "w", encoding="utf-8", newline="\n") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return summary
