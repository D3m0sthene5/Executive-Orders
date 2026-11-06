"""Mabillon NARA census: which executive orders does the National Archives Catalog describe and image?

Reads the National Archives' own public bulk export of Catalog descriptions on the AWS Registry of Open Data
(bucket `nara-national-archives-catalog`, anonymous access, documented at
https://www.archives.gov/developer/national-archives-catalog-dataset). It lists the Record Group 11 description chunks
(`descriptions/record-groups/rg_11/rg_11-N.jsonl`), streams each one, and keeps every description whose own title or
an ancestor's title names executive orders, with its digital-object URLs. It then reads order numbers from the
titles and measures coverage of Mabillon's frame (orders with no official printing or page image held).

This is the key-free route. The Catalog API (catalog.archives.gov/api/v2) needs a key and its terms ask users not to
cache or store returned content; this job does not call it. Nothing here downloads an image: the census is metadata.

Standard library only. No status, identity, census, codebook or count changes.
"""
from __future__ import annotations

import collections
import csv
import gzip
import io
import json
import os
import re
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("REPO_ROOT", HERE.parent.parent)).resolve()
sys.path.insert(0, str(REPO / "jobs/_lib"))

BUCKET = "https://nara-national-archives-catalog.s3.us-east-2.amazonaws.com"
S3NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"
EO_WORDS = re.compile(r"executive\s+orders?|\bE\.\s?O\.\s?\d", re.I)
URL_RE = re.compile(r"^https?://", re.I)
FRAME = REPO / "research/mabillon/frame/FRAME.csv"

# Order numbers in a title: "Executive Order No. 1234", "Executive Order 1234-A", "E.O. 1234", "No. 1234".
NUM_PATTERNS = [
    re.compile(r"executive\s+order\s+(?:no\.?|number|#)?\s*(\d{1,5})(?:\s*[-–]?\s*([A-Z])\b)?", re.I),
    re.compile(r"\bE\.\s?O\.\s*(?:no\.?\s*)?(\d{1,5})(?:\s*[-–]?\s*([A-Z])\b)?", re.I),
    re.compile(r"^\s*(?:no\.?|number)\s*(\d{1,5})(?:\s*[-–]?\s*([A-Z])\b)?", re.I),
    re.compile(r"^\s*(\d{1,5})(?:\s*[-–]?\s*([A-Z]))?\s*$"),
]
RANGE_RE = re.compile(r"(?:executive\s+orders?|nos?\.?)\s*(\d{1,5})\s*(?:-|–|through|to|thru)\s*(\d{1,5})", re.I)


# --------------------------------------------------------------------------------------------- S3 listing

def list_keys(pool, prefix):
    """All objects under a prefix (ListObjectsV2, paged)."""
    out, token = [], None
    while True:
        q = {"list-type": "2", "prefix": prefix, "max-keys": "1000"}
        if token:
            q["continuation-token"] = token
        got = pool.fetch(BUCKET + "/?" + urllib.parse.urlencode(q))
        root = ET.fromstring(got["body"])
        for c in root.findall(S3NS + "Contents"):
            out.append({"key": c.findtext(S3NS + "Key"), "size": int(c.findtext(S3NS + "Size") or 0),
                        "last_modified": c.findtext(S3NS + "LastModified"), "etag": (c.findtext(S3NS + "ETag") or "").strip('"')})
        if (root.findtext(S3NS + "IsTruncated") or "").lower() != "true":
            return out
        token = root.findtext(S3NS + "NextContinuationToken")
        if not token:
            return out


# --------------------------------------------------------------------------------------------- schema-agnostic reading

def key_paths(obj, prefix="", out=None, depth=0):
    """Every key path in a record (lists collapsed to []), for learning the export's schema."""
    out = out if out is not None else set()
    if depth > 8:
        return out
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else k
            out.add(p)
            key_paths(v, p, out, depth + 1)
    elif isinstance(obj, list):
        for v in obj[:3]:
            key_paths(v, prefix + "[]", out, depth + 1)
    return out


def unwrap(rec):
    """The export may wrap a description (e.g. {"record": {...}}); return the dict that carries naId/title."""
    for _ in range(3):
        if isinstance(rec, dict) and not ("naId" in rec or "title" in rec):
            inner = [v for v in rec.values() if isinstance(v, dict) and ("naId" in v or "title" in v)]
            if len(inner) == 1:
                rec = inner[0]
                continue
        break
    return rec


def digital_objects(obj, depth=0):
    """Dicts that carry a URL to a file (objectUrl, url, ...), with their sibling descriptors."""
    found = []
    if depth > 8:
        return found
    if isinstance(obj, dict):
        urls = {k: v for k, v in obj.items() if isinstance(v, str) and URL_RE.match(v) and "url" in k.lower()}
        if urls:
            k, v = sorted(urls.items(), key=lambda kv: (kv[0].lower() != "objecturl", kv[0]))[0]
            found.append({"url": v, "url_key": k,
                          **{kk: vv for kk, vv in obj.items() if isinstance(vv, (str, int, float)) and kk != k
                             and len(str(vv)) < 300}})
        for v in obj.values():
            if isinstance(v, (dict, list)):
                found += digital_objects(v, depth + 1)
    elif isinstance(obj, list):
        for v in obj:
            found += digital_objects(v, depth + 1)
    return found


def ancestors_of(rec):
    """Ancestor descriptions: the export's 'ancestors' list if present, else any nested dict with naId and title."""
    anc = rec.get("ancestors")
    if isinstance(anc, list):
        return [{"naId": a.get("naId"), "title": a.get("title"), "level": a.get("levelOfDescription")}
                for a in anc if isinstance(a, dict)]
    out = []

    def walk(o, depth):
        if depth > 6:
            return
        if isinstance(o, dict):
            if depth and "naId" in o and isinstance(o.get("title"), str):
                out.append({"naId": o.get("naId"), "title": o.get("title"), "level": o.get("levelOfDescription")})
            for v in o.values():
                walk(v, depth + 1)
        elif isinstance(o, list):
            for v in o:
                walk(v, depth + 1)
    walk(rec, 0)
    return out


def flat_text(v):
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return " ; ".join(flat_text(x) for x in v)
    if isinstance(v, dict):
        return " ; ".join(flat_text(x) for x in v.values())
    return str(v or "")


def numbers_in(title):
    """Order numbers named by a title: [(number, suffix)], plus any explicit range."""
    title = title or ""
    found = []
    for pat in NUM_PATTERNS:
        for m in pat.finditer(title):
            found.append((int(m.group(1)), (m.group(2) or "").upper()))
        if found:
            break
    rng = [(int(a), int(b)) for a, b in RANGE_RE.findall(title) if int(a) < int(b)]
    return found, rng


def lean(rec, chunk):
    rec = unwrap(rec)
    title = flat_text(rec.get("title"))
    anc = ancestors_of(rec)
    objs = digital_objects({k: v for k, v in rec.items() if k != "ancestors"})
    dates = {k: flat_text(v)[:80] for k, v in rec.items() if "date" in k.lower() and not isinstance(v, (dict, list))}
    for k in ("inclusiveDates", "coverageDates", "productionDates"):
        if k in rec:
            dates[k] = flat_text(rec[k])[:120]
    return {"naId": rec.get("naId"), "level": rec.get("levelOfDescription"), "title": title[:300],
            "record_group": rec.get("recordGroupNumber"), "dates": dates,
            "ancestors": [{"naId": a["naId"], "title": (a["title"] or "")[:200], "level": a["level"]} for a in anc],
            "objects": [{k: v for k, v in o.items() if k in ("url", "url_key", "objectType", "objectFilename",
                                                             "objectFileSize", "objectId", "objectDescription")}
                        for o in objs],
            "chunk": chunk}


def is_eo(rec):
    rec = unwrap(rec)
    titles = [flat_text(rec.get("title"))] + [a["title"] or "" for a in ancestors_of(rec)]
    return any(EO_WORDS.search(t) for t in titles)


# --------------------------------------------------------------------------------------------- coverage

def eo_number_index(records):
    """instrument_id -> description records that name it, by number in the item title, or for a series/file unit by
    an explicit number range (range coverage is weaker and kept apart)."""
    by_id, by_range = collections.defaultdict(list), []
    for r in records:
        nums, rng = numbers_in(r["title"])
        # A bare number or "No. N" title counts only under an executive-order ancestor.
        anc_eo = any(EO_WORDS.search(a["title"] or "") for a in r["ancestors"])
        own_eo = bool(EO_WORDS.search(r["title"]))
        for n, s in nums:
            if own_eo or anc_eo:
                by_id[f"EO:{n}{s}"].append(r)
        for a, b in rng:
            if b - a <= 2000:
                by_range.append((a, b, r))
    return by_id, by_range


def read_frame():
    if not FRAME.is_file():
        return []
    with open(FRAME, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def coverage(frame, by_id, by_range):
    rows = []
    for o in frame:
        iid = o["instrument_id"]
        n = int(o["number"]) if o["number"] else None
        item = by_id.get(iid, [])
        with_obj = [r for r in item if r["objects"]]
        ranged = [r for a, b, r in by_range if n is not None and a <= n <= b]
        rows.append({"instrument_id": iid, "number": o["number"], "band": o["band"], "era": o["era"],
                     "best_held": o["best_held"], "item_descriptions": len(item),
                     "item_with_objects": len(with_obj),
                     "objects": sum(len(r["objects"]) for r in with_obj),
                     "item_naIds": "|".join(str(r["naId"]) for r in item[:5]),
                     "range_descriptions": len(ranged),
                     "range_with_objects": sum(1 for r in ranged if r["objects"]),
                     "range_naIds": "|".join(str(r["naId"]) for r in ranged[:5])})
    return rows


# --------------------------------------------------------------------------------------------- main

def main(out=None, pool=None):
    out = Path(out or os.environ.get("OUTPUT_DIR", HERE / "output"))
    out.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    prefix = os.environ.get("NARA_PREFIX", "descriptions/record-groups/rg_11/")
    max_bytes = int(os.environ.get("JOB_MAX_BYTES", str(3_000_000_000)))
    max_chunks = int(os.environ.get("JOB_MAX_CHUNKS", "5000"))
    if pool is None:
        from fetch_pool import FetchPool
        pool = FetchPool(Path(os.environ.get("JOB_CACHE_DIR", REPO / ".job-cache/mabillon-nara")),
                         workers=int(os.environ.get("JOB_WORKERS", "4")), per_host=4,
                         user_agent="EO-Road-System/1.0 (mabillon-nara; executive-order research)",
                         min_interval=0.1, max_bytes=100_000_000)
    keys = [k for k in list_keys(pool, prefix) if k["key"].endswith((".jsonl", ".json", ".jsonl.gz", ".json.gz"))]
    total = sum(k["size"] for k in keys)
    plan = {"prefix": prefix, "chunks": len(keys), "bytes": total, "cap_bytes": max_bytes,
            "estimate_minutes_at_20MBps": round(total / 20e6 / 60, 1)}
    print("plan:", json.dumps(plan), flush=True)
    if total > max_bytes:
        keys_run = []
        acc = 0
        for k in keys:
            if acc + k["size"] > max_bytes:
                break
            keys_run.append(k)
            acc += k["size"]
    else:
        keys_run = keys
    keys_run = keys_run[:max_chunks]

    stats = collections.Counter()
    levels = collections.Counter()
    schema = collections.Counter()
    sample_any, sample_eo = [], []
    kept = []
    errors = []
    chunk_receipts = []

    def read_chunk(k):
        url = BUCKET + "/" + urllib.parse.quote(k["key"])
        try:
            got = pool.fetch(url)
        except Exception as exc:  # noqa: BLE001
            return k, None, f"{type(exc).__name__}: {exc}"[:300]
        return k, got, None

    for k, got, err in pool.map(read_chunk, keys_run):
        if err:
            errors.append({"key": k["key"], "error": err})
            continue
        raw = got["body"]
        if k["key"].endswith(".gz"):
            raw = gzip.decompress(raw)
        chunk_receipts.append({"key": k["key"], "bytes": got["bytes"], "sha256": got["sha256"], "etag": k["etag"],
                               "last_modified": k["last_modified"]})
        name = k["key"].rsplit("/", 1)[-1]
        text = raw.decode("utf-8", "replace")
        lines = text.splitlines()
        if len(lines) == 1 and lines[0].lstrip().startswith("["):  # a JSON array instead of JSON lines
            try:
                recs = json.loads(lines[0])
            except ValueError:
                recs = []
        else:
            recs = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    recs.append(json.loads(line))
                except ValueError:
                    stats["bad_lines"] += 1
        for rec in recs:
            stats["records"] += 1
            u = unwrap(rec)
            if isinstance(u, dict):
                levels[str(u.get("levelOfDescription"))] += 1
            if len(sample_any) < 3:
                sample_any.append(json.dumps(rec)[:6000])
            if stats["records"] <= 200:
                schema.update(key_paths(rec))
            if is_eo(rec):
                stats["eo_records"] += 1
                if len(sample_eo) < 5:
                    sample_eo.append(json.dumps(rec)[:12000])
                kept.append(lean(rec, name))

    by_id, by_range = eo_number_index(kept)
    frame = read_frame()
    cov = coverage(frame, by_id, by_range)

    # Series and file units that name executive orders, with their object counts.
    groups = collections.defaultdict(lambda: {"descriptions": 0, "with_objects": 0, "objects": 0, "numbers": set()})
    for r in kept:
        top = next((a for a in r["ancestors"] if (a.get("level") or "").lower() == "series"), None)
        key = (top or {}).get("naId") or r["naId"]
        g = groups[key]
        g["title"] = (top or {}).get("title") or r["title"]
        g["descriptions"] += 1
        g["with_objects"] += bool(r["objects"])
        g["objects"] += len(r["objects"])
        g["numbers"].update(n for n, _ in numbers_in(r["title"])[0])
    series_rows = []
    for k, g in groups.items():
        nums = sorted(g["numbers"])
        series_rows.append({"series_naId": k, "title": g["title"][:200], "descriptions": g["descriptions"],
                            "with_objects": g["with_objects"], "objects": g["objects"],
                            "numbered_items": len(nums), "min_number": nums[0] if nums else "",
                            "max_number": nums[-1] if nums else ""})
    series_rows.sort(key=lambda x: -x["descriptions"])

    with gzip.open(out / "EO_DESCRIPTIONS.jsonl.gz", "wt", encoding="utf-8") as f:
        for r in kept:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    with open(out / "SERIES.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["series_naId", "title", "descriptions", "with_objects", "objects",
                                          "numbered_items", "min_number", "max_number"])
        w.writeheader()
        w.writerows(series_rows)
    if cov:
        with open(out / "FRAME_COVERAGE.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(cov[0]))
            w.writeheader()
            w.writerows(cov)
    # Every order number the census found an imaged item description for (all orders, not only the frame).
    with open(out / "BY_ORDER.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["instrument_id", "descriptions", "with_objects", "objects", "naIds", "first_object_url"])
        for iid in sorted(by_id, key=lambda x: (int(re.match(r"EO:(\d+)", x).group(1)), x)):
            rs = by_id[iid]
            objs = [o for r in rs for o in r["objects"]]
            w.writerow([iid, len(rs), sum(1 for r in rs if r["objects"]), len(objs),
                        "|".join(str(r["naId"]) for r in rs[:5]), objs[0]["url"] if objs else ""])
    (out / "SCHEMA_SAMPLE.json").write_text(json.dumps(
        {"key_paths_first_200_records": dict(schema.most_common()), "sample_records": sample_any,
         "sample_eo_records": sample_eo}, indent=1) + "\n")
    with open(out / "CHUNKS.jsonl", "w", encoding="utf-8") as f:
        for c in chunk_receipts:
            f.write(json.dumps(c) + "\n")
    with open(out / "ERRORS.jsonl", "w", encoding="utf-8") as f:
        for e in errors:
            f.write(json.dumps(e) + "\n")

    frame_ids = {o["instrument_id"] for o in frame}
    summary = {
        "job": "mabillon-nara", "stage": "census", "plan": plan, "chunks_read": len(chunk_receipts),
        "chunk_errors": len(errors), "records": stats["records"], "eo_records": stats["eo_records"],
        "bad_lines": stats["bad_lines"], "levels": dict(levels.most_common()),
        "eo_with_objects": sum(1 for r in kept if r["objects"]),
        "eo_objects": sum(len(r["objects"]) for r in kept),
        "orders_named_by_item_title": len(by_id),
        "orders_named_with_objects": sum(1 for v in by_id.values() if any(r["objects"] for r in v)),
        "frame_orders": len(frame),
        "frame_item_described": sum(1 for r in cov if r["item_descriptions"]),
        "frame_item_with_objects": sum(1 for r in cov if r["item_with_objects"]),
        "frame_range_described": sum(1 for r in cov if r["range_descriptions"]),
        "frame_range_with_objects": sum(1 for r in cov if r["range_with_objects"]),
        "frame_in_index": len(frame_ids & set(by_id)),
        "series_top": series_rows[:25],
        "requests": pool.requests, "bytes_downloaded": getattr(pool, "bytes_downloaded", None),
        "seconds": round(time.monotonic() - started),
        "access": "AWS Registry of Open Data public bucket, anonymous HTTPS; no Catalog API calls, no key",
        "what_this_is_not": "Metadata only. A description or object URL is a location lead, not a verified match; "
                            "no status, identity, census, codebook or count changes.",
    }
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=2, default=list) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "series_top"}, indent=1, default=list))
    for s in series_rows[:15]:
        print(s)
    return summary


if __name__ == "__main__":
    main()
