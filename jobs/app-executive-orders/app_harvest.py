"""American Presidency Project (APP) executive-order harvest, polite and resumable.

Explicit local invocation only; this is not an automatically scheduled job.py.

  index      read every listing page of the APP "Executive Orders" category
             (100 rows per page) into output/INDEX.jsonl and INDEX.csv
  documents  read each listed order page: full text, Federal Register note,
             APP citation/node, president, categories, attributes

Every request goes through the shared FetchPool: one worker, robots.txt
rules, and at least CRAWL_DELAY seconds between requests (the site's
robots.txt asks for Crawl-delay: 10). HTTP 403/429/5xx, Retry-After, a
challenge page or a response slower than 60 seconds stops the run; rerunning
resumes from what is already saved. APP pages are an editorial secondary
compilation, never an original: every record carries
acceptable_as_original=false and no legal or status finding.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlsplit

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "jobs/_lib"))
import fetch_pool
sys.path.insert(0, str(ROOT / "jobs/source-ladder"))
import fetch_ladder

HOST = "www.presidency.ucsb.edu"
BASE = "https://" + HOST
LISTING = BASE + "/documents/app-categories/written-presidential-orders/presidential/executive-orders"
PER_PAGE = 100
CRAWL_DELAY = 10
USER_AGENT = "EO-Historical-Research/1.0 (https://github.com/D3m0sthene5/Executive-Orders)"
INDEX_FIELDS = ["instrument_id", "eo_number_raw", "date", "title", "president", "president_path", "path", "url", "listing_page"]


class SiteStopped(RuntimeError):
    pass


class PageFailure(RuntimeError):
    pass


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def stamp():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())
    temp.replace(path)


def lines(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()] if path.exists() else []


def append(path, value):
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")


def clean(fragment):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def instrument_id(title):
    """EO:<number><suffix> from an APP title such as 'Executive Order 14356—...'; None if unnumbered."""
    m = re.match(r"\s*Executive Order\s+(?:No\.\s*)?(\d+)(?:-?([A-Z]{1,2}))?(?![\w])", title)
    return ("EO:" + str(int(m[1])) + (m[2] or ""), m[0].strip()) if m else (None, "")


def check_page(raw):
    text = raw.decode("utf-8", "replace")
    low = text[:20000].lower()
    if any(x in low for x in ("<title>just a moment", "cf-chl-", 'id="challenge-form"', "<title>access denied")):
        raise SiteStopped("HTML access challenge; acquisition stopped")
    return text


def parse_listing(text, page):
    rows = []
    for block in re.split(r'<div class="views-row\b', text)[1:]:
        about = re.search(r'about="(/documents/[^"]+)"', block)
        title = re.search(r'<div class="field-title">\s*<p><a href="[^"]+">(.*?)</a>', block, re.S)
        if not about or not title:
            continue
        date = re.search(r'property="dc:date"[^>]*content="(\d{4}-\d{2}-\d{2})', block)
        prez = re.search(r'<a href="(/people/president/[^"]+)">(.*?)</a>', block, re.S)
        t = clean(title[1])
        iid, raw_no = instrument_id(t)
        rows.append({"instrument_id": iid, "eo_number_raw": raw_no, "date": date[1] if date else "",
                     "title": t, "president": clean(prez[2]) if prez else "",
                     "president_path": prez[1] if prez else "", "path": about[1],
                     "url": BASE + about[1], "listing_page": page})
    last = re.search(r'pager-last"><a[^>]*href="[^"]*[?&;]page=(\d+)', text)
    return rows, int(last[1]) if last else None


def between(text, start_marker, end_markers):
    i = text.find(start_marker)
    if i < 0:
        return ""
    i += len(start_marker)
    ends = [j for j in (text.find(m, i) for m in end_markers) if j >= 0]
    return text[i:min(ends)] if ends else text[i:]


def parse_document(text):
    main = text[text.find('id="block-system-main"'):] if 'id="block-system-main"' in text else text
    h1 = re.search(r"<h1\b[^>]*>(.*?)</h1>", main, re.S)
    date = re.search(r'field-docs-start-date-time">\s*<span[^>]*content="([^"]+)"[^>]*>(.*?)</span>', main, re.S)
    prez = re.search(r'<h3 class="diet-title"><a href="([^"]+)">(.*?)</a>', main, re.S)
    byline = re.search(r'<div class="diet-by-line[^"]*">(.*?)</div>', main, re.S)
    body = between(main, '<div class="field-docs-content">',
                   ['<div class="field-docs-footnote">', '<div class="field-prez-document-citation">', '<div class="col-sm-4'])
    note = between(main, '<div class="field-docs-footnote">', ['<div class="field-prez-document-citation">', '<div class="col-sm-4'])
    location = re.search(r'<div class="field-spot-state">(.*?)</div>', main, re.S)
    citation = re.search(r'<p class="ucsbapp_citation">(.*?)</p>', main, re.S)
    node = re.search(r"/node/(\d+)", citation[1]) if citation else None
    meta = between(main, '<div class="group-meta">', ['<div class="rrssb"', '<div class="field-ds-big-search-block">'])
    cats = between(meta, ">Categories</h3>", [">Attributes</h3>", '<div class="jump">'])
    attrs = between(meta, ">Attributes</h3>", ['<div class="jump">'])
    links = lambda s: [clean(x) for x in re.findall(r'<a href="/documents/app-(?:categories|attributes)/[^"]*"[^>]*>(.*?)</a>', s, re.S)]
    return {"heading": clean(h1[1]) if h1 else "",
            "date": date[1][:10] if date else "", "date_display": clean(date[2]) if date else "",
            "president": clean(prez[2]) if prez else "", "president_path": prez[1] if prez else "",
            "president_byline": clean(byline[1]) if byline else "",
            "location": clean(location[1]) if location else "",
            "text": fetch_ladder.html_to_text(body.rsplit("</div>", 1)[0]) if body else "",
            "footnote": fetch_ladder.html_to_text(note.rsplit("</div>", 1)[0]) if note else "",
            "citation": clean(citation[1]) if citation else "",
            "app_node": node[1] if node else "",
            "categories": links(cats), "attributes": links(attrs)}


STATISTICS = BASE + "/statistics/data/executive-orders"
STAT_FIELDS = ["president", "term", "total_orders", "avg_per_year", "years_in_office", "eo_number_range", "search_url"]


def parse_statistics(text):
    main = text[text.find('id="block-system-main"'):] if 'id="block-system-main"' in text else text
    table = re.search(r"<table\b.*?</table>", main, re.S)
    rows, president = [], ""
    for tr in re.findall(r"<tr\b.*?</tr>", table[0] if table else "", re.S):
        cells = re.findall(r"<td\b[^>]*>(.*?)</td>", tr, re.S)
        if len(cells) != 6 or clean(cells[0]) == "President":
            continue
        values = [clean(c) for c in cells]
        president = values[0] or president
        link = re.search(r'href="([^"]+)"', cells[2])
        rows.append(dict(zip(STAT_FIELDS, [president] + values[1:] + [html.unescape(link[1]) if link else ""])))
    field = lambda name: fetch_ladder.html_to_text(between(main, f'<div class="{name}">', ["<h3", '<div class="field-'])
                                                 .rsplit("</div>", 1)[0])
    intro = between(main, '<div class="field-body">', ["<table"]) if '<div class="field-body">' in main else ""
    footer = re.search(r"<table\b.*?</tbody>\s*</table>", main, re.S)
    note = re.findall(r'<td colspan="6">(.*?)</td>', footer[0] if footer else "", re.S)
    return {"title": clean((re.search(r"<h1\b[^>]*>(.*?)</h1>", main, re.S) or ["", ""])[1]),
            "methodology_text": fetch_ladder.html_to_text(intro),
            "table_notes": fetch_ladder.html_to_text(note[-1]) if note else "",
            "last_updated": field("field-prez-election-updated-at"),
            "notes": field("field-prez-election-notes"),
            "sources": field("field-prez-election-data-sources"),
            "rows": rows}


def run_statistics(pool, out):
    result = pool.fetch(STATISTICS)
    text = check_page(result["body"])
    stats = parse_statistics(text)
    if len(stats["rows"]) < 40:
        raise PageFailure(f"statistics table parsed only {len(stats['rows'])} rows")
    stats.update(url=STATISTICS, sha256=result["sha256"], bytes=result["bytes"], retrieved_utc=stamp(),
                 acceptable_as_original=False,
                 caution="APP editorial counts (pre-1945 include unnumbered orders). A comparison source, not a census finding.")
    write_json(out / "STATISTICS.json", stats)
    with (out / "STATISTICS.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=STAT_FIELDS)
        w.writeheader()
        w.writerows(stats["rows"])
    fetch_ladder.write_text_lf(out / "STATISTICS_PAGE.txt", fetch_ladder.html_to_text(
        text[text.find('id="block-system-main"'):text.find('<footer')]) + "\n")
    print(f"statistics: {len(stats['rows'])} rows, last updated {stats['last_updated']}", flush=True)


def make_pool(cache_dir):
    def guarded_transport(url, headers, timeout):
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname != HOST:
            raise SiteStopped("Unexpected host; request refused: " + url)
        started = time.monotonic()
        status, hs, response = fetch_pool.http_transport(url, headers, timeout)
        if status in (401, 403, 408, 425, 429) or status >= 500 or hs.get("retry-after"):
            response.close()
            raise SiteStopped("Site blocking/throttling/server response HTTP " + str(status) +
                              ("; Retry-After=" + hs["retry-after"] if hs.get("retry-after") else ""))
        if time.monotonic() - started > 60:
            response.close()
            raise SiteStopped("Site response exceeded 60 seconds; stopped without retry")
        return status, hs, response

    return fetch_pool.FetchPool(cache_dir, workers=1, per_host=1, min_interval=CRAWL_DELAY,
                                max_bytes=4_000_000, timeout=60, transport=guarded_transport,
                                user_agent=USER_AGENT, max_cache_bytes=4096 * 1024 * 1024)


def run_index(pool, out):
    rows, page, last, pages = [], 0, None, []
    while last is None or page <= last:
        url = f"{LISTING}?items_per_page={PER_PAGE}&page={page}"
        result = pool.fetch(url)
        found, pager_last = parse_listing(check_page(result["body"]), page)
        if pager_last is not None:
            last = max(pager_last, last or 0)
        elif last is None or last < page:
            last = page + 1  # no pager seen: keep reading until an empty page
        pages.append({"page": page, "url": url, "sha256": result["sha256"], "rows": len(found), "retrieved_utc": stamp()})
        rows.extend(found)
        print(f"index page {page}/{last}: {len(found)} rows, total {len(rows)}", flush=True)
        if not found:
            break
        page += 1
    seen, unique = set(), []
    for r in rows:
        if r["path"] not in seen:
            seen.add(r["path"])
            unique.append(r)
    with (out / "INDEX.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for r in unique:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    with (out / "INDEX.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=INDEX_FIELDS)
        w.writeheader()
        w.writerows(unique)
    numbers = [r["instrument_id"] for r in unique if r["instrument_id"]]
    summary = {"retrieved_utc": stamp(), "listing": LISTING, "pages": len(pages), "rows": len(rows),
               "unique_documents": len(unique), "numbered": len(numbers),
               "distinct_instrument_ids": len(set(numbers)), "unnumbered": len(unique) - len(numbers),
               "listing_pages": pages}
    write_json(out / "INDEX_SUMMARY.json", {k: v for k, v in summary.items()})
    print(json.dumps({k: v for k, v in summary.items() if k != "listing_pages"}), flush=True)


def text_name(path):
    slug = path.rsplit("/", 1)[-1]
    return slug if len(slug) <= 110 else slug[:100] + "-" + sha(slug.encode())[:8]


def sort_key(row):
    m = re.match(r"EO:(\d+)(.*)", row.get("instrument_id") or "")
    return (0, int(m[1]), m[2], row["path"]) if m else (1, 0, row.get("date", ""), row["path"])


def mirror_covered(out, audit_every):
    """Paths the archive lane (app_mirror.py) already saved, minus an audit sample fetched live anyway.

    Returns (skip, audit): the live lane skips `skip`; it fetches `audit` and records whether the live
    text agrees with the capture in MIRROR_AUDIT.jsonl. The sample is every audit_every-th covered path
    in path order (0 = no sample), minus paths already audited.
    """
    covered = {d["path"]: d for d in lines(out / "MIRROR_DOCUMENTS.jsonl")}
    audited = {a["path"] for a in lines(out / "MIRROR_AUDIT.jsonl")}
    audit = {}
    if audit_every:
        # Backfill rows (app_mirror.py backfill-documents) back pages already fetched live and carry their own
        # live comparison; leaving them out keeps the sample, and so the live requests it costs, unchanged.
        sampled = sorted(p for p, d in covered.items() if not d.get("live_backfill"))
        for i, path in enumerate(sampled):
            if i % audit_every == 0 and path not in audited:
                audit[path] = covered[path]
    # A capture whose page parsed but holds no text (APP's "[Not Published.]") is a finding, not a fetch problem.
    empty = {f["path"] for f in lines(out / "MIRROR_FAILURES.jsonl") if f.get("reason") == "no_usable_text"}
    return {p for p in covered if p not in audit} | empty, audit


def run_documents(pool, out, max_new, ids_file, audit_every=0):
    index = lines(out / "INDEX.jsonl")
    if not index:
        raise SystemExit("Run the index phase first: output/INDEX.jsonl is missing")
    for name in ("DOCUMENTS.jsonl", "SOURCES.jsonl", "FRAGMENTS.jsonl", "FAILURES.jsonl", "ATTEMPTS.jsonl"):
        (out / name).touch(exist_ok=True)
    done = {d["path"] for d in lines(out / "DOCUMENTS.jsonl")}
    failed = {f["path"] for f in lines(out / "FAILURES.jsonl")}
    mirrored, audit = mirror_covered(out, audit_every)
    priority = set()
    if ids_file:
        priority = {s.strip() for s in Path(ids_file).read_text(encoding="utf-8").split() if s.strip()}
    queue = sorted((r for r in index if r["path"] not in done and r["path"] not in failed and r["path"] not in mirrored),
                   key=lambda r: (r.get("instrument_id") not in priority, sort_key(r)))
    stopped, started_new = "", 0

    def checkpoint():
        left = len(index) - len(done) - len(failed) - len(mirrored - done)
        state = {"updated_utc": stamp(), "indexed": len(index), "saved": len(done), "failed": len(failed),
                 "mirror_saved": len(mirrored) + len(audit), "audit_sample": len(audit),
                 "remaining": left, "site_stopped": bool(stopped),
                 "stop_reason": stopped, "complete": left <= 0,
                 "seconds_per_request": CRAWL_DELAY,
                 "estimated_hours_left": round(max(0, left) * CRAWL_DELAY / 3600, 1)}
        write_json(out / "STATE.json", state)
        print(json.dumps(state), flush=True)

    checkpoint()
    for row in queue:
        if started_new >= max_new:
            break
        started_new += 1
        entry = {"kind": "document", "path": row["path"], "instrument_id": row["instrument_id"], "attempted_utc": stamp()}
        try:
            result = pool.fetch(row["url"])
            raw = result["body"]
            doc = parse_document(check_page(raw))
            if len(doc["text"]) < 40:
                raise PageFailure("no_usable_text")
            iid, _ = instrument_id(doc["heading"])
            if row["instrument_id"] and iid != row["instrument_id"]:
                raise PageFailure(f"identity_mismatch: listing {row['instrument_id']} page {iid}; heading={doc['heading']}")
            mirror = audit.get(row["path"])
            text_rel = "texts/" + text_name(row["path"]) + (".live.txt" if mirror else ".txt")
            fetch_ladder.write_text_lf(out / text_rel, doc["text"] + "\n")
            retrieved = stamp()
            record = {"instrument_id": iid, "path": row["path"], "url": row["url"], "final_url": result["final_url"],
                      "sha256": result["sha256"], "bytes": result["bytes"], "retrieved_utc": retrieved,
                      "text_path": text_rel, "text_sha256": sha((out / text_rel).read_bytes()),
                      "text_chars": len(doc["text"]), "listing_title": row["title"], "listing_date": row["date"],
                      **{k: v for k, v in doc.items() if k != "text"}}
            if mirror:
                record["audit_of_mirror"] = mirror["route"]
                append(out / "MIRROR_AUDIT.jsonl", {
                    "path": row["path"], "instrument_id": iid, "archive": mirror["route"],
                    "captured_utc": mirror.get("capture", {}).get("captured_utc", ""), "live_retrieved_utc": retrieved,
                    "mirror_text_sha256": mirror["text_sha256"], "live_text_sha256": record["text_sha256"],
                    "text_agrees": mirror["text_sha256"] == record["text_sha256"],
                    "mirror_page_sha256": mirror["sha256"], "live_page_sha256": result["sha256"],
                    "page_agrees": mirror["sha256"] == result["sha256"]})
            append(out / "DOCUMENTS.jsonl", record)
            source = {"source_id": "app-executive-orders:" + (iid or "node/" + doc["app_node"]) + ":" + result["sha256"][:12],
                      "instrument_ids": [iid] if iid else [], "url": row["url"],
                      "archival_id": "app:node/" + doc["app_node"] if doc["app_node"] else "",
                      "sha256": result["sha256"], "bytes": result["bytes"], "retrieved_utc": retrieved,
                      "content_type": "text/html", "route": "mirror/american-presidency-project",
                      "page_or_item": doc["heading"] + "; " + doc["date_display"] + "; APP node " + doc["app_node"],
                      "text_path": text_rel, "text_sha256": record["text_sha256"],
                      "grade": "mirror_transcription", "representation_type": "secondary_compilation_transcription",
                      "acceptable_as_original": False,
                      "notes": "American Presidency Project editorial transcription, not an original. Raw page bytes are hashed but not committed; APP footnotes kept separately in DOCUMENTS.jsonl. No legal finding."}
            append(out / "SOURCES.jsonl", source)
            if iid:
                data = {k: source[k] for k in ("source_id", "url", "sha256", "text_path", "text_sha256",
                                               "page_or_item", "archival_id", "grade", "representation_type",
                                               "acceptable_as_original")}
                data.update(needs_page_check=True, location_verified=False, location_confidence="medium",
                            app_date=doc["date"], app_footnote=doc["footnote"])
                append(out / "FRAGMENTS.jsonl", {
                    "kind": "original_representation", "instrument_id": iid, "produced_by": "app-executive-orders",
                    "grade": "mirror_transcription", "representation_type": "secondary_compilation_transcription",
                    "acceptable_as_original": False, "data": data,
                    "sources": [{k: source[k] for k in ("url", "sha256", "page_or_item", "archival_id")}],
                    "confidence_note": "Listing and page headings agree on the EO number. APP editorial transcription only; not an authenticated original, identity authentication or legal conclusion."})
            done.add(row["path"])
            entry["result"] = "saved"
        except Exception as exc:
            reason = str(exc)
            entry.update(result="failed", reason=reason, error_type=type(exc).__name__)
            if isinstance(exc, SiteStopped) or isinstance(exc, (TimeoutError, OSError)):
                stopped = reason
                entry["result"] = "stopped"
            else:
                failed.add(row["path"])
                append(out / "FAILURES.jsonl", entry)
        append(out / "ATTEMPTS.jsonl", entry)
        if stopped:
            break
        if started_new % 25 == 0:
            checkpoint()
    checkpoint()
    if stopped:
        raise SystemExit("Stopped: " + stopped)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("phase", choices=["statistics", "index", "documents", "parse-test"])
    ap.add_argument("--download", action="store_true", help="Required to authorize network acquisition")
    ap.add_argument("--cache-dir", type=Path, help="Raw page cache (not committed); reruns reuse it without new requests")
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "output")
    ap.add_argument("--max-new", type=int, default=100000, help="Stop after this many document pages")
    ap.add_argument("--ids-file", help="Whitespace-separated instrument IDs (EO:123) to fetch first")
    ap.add_argument("--audit-every", type=int, default=0,
                    help="documents: skip pages the archive lane (app_mirror.py) saved, except every Nth, "
                         "which is fetched live and compared in MIRROR_AUDIT.jsonl (0 = skip all)")
    ap.add_argument("files", nargs="*", help="parse-test: saved HTML pages to parse offline")
    args = ap.parse_args()
    if args.phase == "parse-test":
        for f in args.files:
            text = Path(f).read_text(encoding="utf-8")
            if "statistics/data/executive-orders" in text and "<table" in text and 'class="views-row' not in text:
                st = parse_statistics(text)
                print(json.dumps({**{k: v for k, v in st.items() if k != "rows"}, "rows": len(st["rows"]),
                                  "first": st["rows"][:3], "last": st["rows"][-2:]}, ensure_ascii=False, indent=1)[:4000])
            elif 'class="field-docs-content"' not in text and 'class="views-row' in text:
                rows, last = parse_listing(text, 0)
                print(json.dumps({"rows": len(rows), "pager_last": last, "first": rows[:2]}, ensure_ascii=False, indent=1))
            else:
                doc = parse_document(text)
                doc["text"] = doc["text"][:300] + " ..."
                print(json.dumps(doc, ensure_ascii=False, indent=1))
        return
    if not args.download or not args.cache_dir:
        ap.error("Use --download and --cache-dir explicitly; there is no automatic acquisition")
    args.out.mkdir(parents=True, exist_ok=True)
    pool = make_pool(args.cache_dir)
    if args.phase == "statistics":
        run_statistics(pool, args.out)
    elif args.phase == "index":
        run_index(pool, args.out)
    else:
        run_documents(pool, args.out, args.max_new, args.ids_file, args.audit_every)
    print(f"requests={pool.requests} cache_hits={pool.cache_hits} bytes={pool.bytes_downloaded}", flush=True)


if __name__ == "__main__":
    main()
