"""Download and read BLM's 'Table of Public Land Orders' PDFs (PLOs 1-7898, 24 files).

The listing page https://www.blm.gov/programs/lands-and-realty/land-tenure/withdrawals/public-land-orders is read
fresh on every run, so a new table file is picked up; data/blm_plo_tables.json holds the 24 links seen on
2026-10-28 as a fallback. Each PDF goes through the shared fetch pool (robots.txt, pacing, sha256, bounded size,
cache under JOB_CACHE_DIR), its text layer is read with pypdf, and the text is written to texts/blm/<range>.txt.
A PDF no larger than BLM_COMMIT_MAX_BYTES is also committed (blm/<range>.pdf) so its sha256 can be re-checked
from held bytes. If a download fails, the text and source record of the previous committed run are carried
forward (JOB_PRIOR_OUTPUT_DIR) and flagged.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import os
import re
import shutil
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "_lib"))
import fetch_pool  # noqa: E402

USER_AGENT = "EO-afterlife-research/1.0 (shepard-citations; bounded research job)"
LISTING_URL = "https://www.blm.gov/programs/lands-and-realty/land-tenure/withdrawals/public-land-orders"
MAX_PDF_BYTES = 80_000_000
TEXT_HEADER = ("Table: {name}\nSource: {url}\nSHA-256 of the downloaded file: {sha}\nRetrieved: {when}\n"
               "Text layer read with pypdf. BLM editorial table: every row is a finding aid, not the order itself.\n")


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def table_range(url):
    """(lo, hi) PLO numbers from a table file name such as '..._public-land-orders_695-2250.pdf'."""
    name = urllib.parse.unquote(urllib.parse.urlsplit(url).path.rsplit("/", 1)[-1])
    m = re.search(r"(\d{1,4})\s*[-_]\s*(\d{1,4})\.pdf$", name, re.I)
    return (int(m.group(1)), int(m.group(2))) if m else (None, None)


def parse_listing(page, base=LISTING_URL):
    """Table links on the BLM listing page: [{'url', 'lo', 'hi'}], ordered by lo."""
    out, seen = [], set()
    for href in re.findall(r"href\s*=\s*[\"']([^\"']+\.pdf)[\"']", page, re.I):
        url = urllib.parse.urljoin(base, html.unescape(href))
        low = urllib.parse.unquote(url).lower()
        if "land" not in low or "order" not in low:
            continue
        lo, hi = table_range(url)
        if lo is None or url in seen:
            continue
        seen.add(url)
        out.append({"url": url, "lo": lo, "hi": hi})
    return sorted(out, key=lambda t: t["lo"])


def extract_pages(raw):
    """Per-page text of a PDF with pypdf (imported here so the offline tests need no PDF library)."""
    import io
    import pypdf
    reader = pypdf.PdfReader(io.BytesIO(raw))
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception as exc:  # a damaged page must not lose the whole table
            pages.append(f"[page text unreadable: {type(exc).__name__}]")
    return pages


def text_file(name, url, sha, pages, when):
    parts = [TEXT_HEADER.format(name=name, url=url, sha=sha, when=when)]
    for i, p in enumerate(pages, 1):
        parts.append(f"\n=== PDF page {i} of {len(pages)} ===\n{p.rstrip()}\n")
    return "".join(parts)


def pages_from_text(text):
    marks = list(re.finditer(r"^=== PDF page (\d+) of (\d+) ===\n", text, re.M))
    return [text[m.end():(marks[i + 1].start() if i + 1 < len(marks) else len(text))] for i, m in enumerate(marks)]


def _prior_sources(prior_dir):
    out = {}
    path = os.path.join(prior_dir or "", "SOURCES.jsonl")
    if prior_dir and os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if rec.get("url"):
                    out[rec["url"]] = rec
    return out


def fetch_tables(out_dir, cache_dir, prior_dir, seed_path, *, max_requests=60, commit_max_bytes=2_000_000,
                 offline=False, transport=None, extract=extract_pages, log=print):
    """Return (tables, source_records). Each table: name, url, lo, hi, sha256, bytes, pages, status, error,
    carried_forward, committed, text_path."""
    with open(seed_path, encoding="utf-8") as fh:
        seed = json.load(fh)
    pool = fetch_pool.FetchPool(cache_dir, workers=1, per_host=1, transport=transport, max_bytes=MAX_PDF_BYTES,
                                user_agent=USER_AGENT, min_interval=1.5, offline=offline)
    listed, listing_status = [], "not_attempted"
    if not offline:
        try:
            for p in pool._paths(seed.get("listing_url", LISTING_URL)):  # always read the listing fresh
                p.unlink(missing_ok=True)
            got = pool.fetch(seed.get("listing_url", LISTING_URL))
            listed = parse_listing(got["body"].decode("utf-8", "replace"), seed.get("listing_url", LISTING_URL))
            listing_status = f"read: {len(listed)} table links"
        except Exception as exc:
            listing_status = f"failed: {type(exc).__name__}: {exc}"
    log("BLM listing: " + listing_status)
    tables = listed if len(listed) >= 10 else [dict(t) for t in seed["tables"]]
    for t in tables:
        if t.get("lo") is None:
            t["lo"], t["hi"] = table_range(t["url"])
    prior = _prior_sources(prior_dir)
    when = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    records = []
    os.makedirs(os.path.join(out_dir, "texts", "blm"), exist_ok=True)
    for t in tables:
        t["name"] = f"{t['lo']}-{t['hi']}"
        t.update(status="", error="", carried_forward=False, committed=False, pages=None, sha256="", bytes=0)
        text_rel = f"texts/blm/plo_{t['name']}.txt"
        raw = None
        if offline:
            t["error"] = "offline"
        elif pool.requests >= max_requests:
            t["error"] = "request_budget_exhausted"
        else:
            try:
                got = pool.fetch(t["url"])
                raw = got["body"]
                if not raw.startswith(b"%PDF"):
                    raise fetch_pool.FetchError("not a PDF")
            except Exception as exc:
                raw, t["error"] = None, f"{type(exc).__name__}: {exc}"
        if raw is not None:
            t["sha256"], t["bytes"] = sha256(raw), len(raw)
            t["pages"] = extract(raw)
            text = text_file(t["name"], t["url"], t["sha256"], t["pages"], when)
            t["status"] = "downloaded"
            rec = {"url": t["url"], "sha256": t["sha256"], "bytes": t["bytes"], "content_type": "application/pdf",
                   "retrieved_utc": when, "route": "official/blm_plo_table"}
            if t["bytes"] <= commit_max_bytes:
                rel = f"blm/plo_{t['name']}.pdf"
                os.makedirs(os.path.join(out_dir, "blm"), exist_ok=True)
                with open(os.path.join(out_dir, rel), "wb") as fh:
                    fh.write(raw)
                rec["cache_path"] = rel
                t["committed"] = True
        else:
            old = prior.get(t["url"])
            old_text = os.path.join(prior_dir or "", old.get("text_path", "")) if old else ""
            if old and os.path.isfile(old_text):
                with open(old_text, encoding="utf-8") as fh:
                    text = fh.read()
                t["pages"] = pages_from_text(text)
                t["sha256"], t["bytes"] = old.get("sha256", ""), old.get("bytes", 0)
                t["status"], t["carried_forward"] = "carried_forward_from_previous_run", True
                rec = {k: v for k, v in old.items() if k not in ("cache_path", "text_path", "text_sha256")}
                rec["carried_forward"] = True
                old_pdf = os.path.join(prior_dir, old["cache_path"]) if old.get("cache_path") else ""
                if old_pdf and os.path.isfile(old_pdf):
                    with open(old_pdf, "rb") as fh:
                        if sha256(fh.read()) == old.get("sha256"):
                            os.makedirs(os.path.join(out_dir, "blm"), exist_ok=True)
                            shutil.copyfile(old_pdf, os.path.join(out_dir, old["cache_path"]))
                            rec["cache_path"] = old["cache_path"]
                            t["committed"] = True
            else:
                t["status"] = "failed"
                log(f"BLM table {t['name']}: {t['error']} (no previous copy)")
                continue
        with open(os.path.join(out_dir, text_rel), "w", encoding="utf-8") as fh:
            fh.write(text)
        with open(os.path.join(out_dir, text_rel), "rb") as fh:
            rec["text_sha256"] = sha256(fh.read())
        rec.update(text_path=text_rel, instrument_ids=[],
                   page_or_item=f"BLM Table of Public Land Orders {t['name']} (whole table)",
                   note="BLM finding aid listing many PLOs; not the text of any order. instrument_ids is empty on purpose.")
        t["text_path"] = text_rel
        records.append(rec)
        log(f"BLM table {t['name']}: {t['status']} {t['bytes']} bytes, {len(t['pages'] or [])} pages"
            + (" (committed)" if t["committed"] else ""))
    stats = {"listing": listing_status, "requests": pool.requests, "bytes_downloaded": pool.bytes_downloaded,
             "cache_hits": pool.cache_hits}
    return tables, records, stats
