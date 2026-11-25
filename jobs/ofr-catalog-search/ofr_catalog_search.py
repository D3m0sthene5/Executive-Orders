"""Panizzi: record, for each order the tracker lists as lacking an OFR catalog entry, what the OFR catalog holds.

The tracker (jobs/readiness-tracker/tracker.py, load_machine_search) counts the counterevidence step from the
OFR catalog only when the order's id is in jobs/later-events/output/CATALOG_INDEX.csv. An order outside that file gets
NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE. This module reads the same catalog source (federalregister.gov API v1) and
the National Archives disposition-table coverage statement, and writes one search record per order. Leads only.
"""
import csv
import hashlib
import html
import json
import re
import time
import urllib.parse
import urllib.request

BLOCKER = "NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE"
API_BASE = "https://www.federalregister.gov/api/v1/documents.json"
INDEX_URL = "https://www.archives.gov/federal-register/executive-orders/disposition"
USER_AGENT = "EO-afterlife-research/1.0 (owner-run research; contact via repo)"
FIELDS = ("citation", "disposition_notes", "document_number", "executive_order_number", "html_url",
          "publication_date", "signing_date", "title")
PER_PAGE = 1000
MAX_PAGES = 12          # the catalog had 7 pages of 1,000 in Oct 2026
GAP_SECONDS = 1.1
OUTCOMES = ("entry_found", "searched_complete_no_entry", "search_incomplete")
COVERAGE_RE = re.compile(r"[^.<>]*January\s+8,\s*1937[^.<>]*\.", re.I)


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def api_url(page):
    pairs = [("conditions[correction]", "0"), ("conditions[presidential_document_type]", "executive_order"),
             ("conditions[type][]", "PRESDOCU"), ("include_pre_1994_docs", "true"),
             ("order", "executive_order_number"), ("per_page", str(PER_PAGE)), ("page", str(page))]
    return API_BASE + "?" + urllib.parse.urlencode(pairs + [("fields[]", f) for f in FIELDS])


def http_get(url):
    last = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read(), r.geturl()
        except Exception as exc:  # noqa: BLE001 - retried, then reported
            last = exc
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"fetch failed for {url}: {last}")


def target_ids(csv_text, blocker=BLOCKER):
    """Instrument ids whose blockers column names the blocker, in file order."""
    return [r["instrument_id"] for r in csv.DictReader(csv_text.splitlines())
            if blocker in (r.get("blockers") or "").split("|")]


def number_of(instrument_id):
    return instrument_id.split(":", 1)[1].strip().upper()


def parse_index(page_html):
    """The disposition index page's coverage sentence (quoted), or None."""
    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", page_html)))
    m = COVERAGE_RE.search(text)
    return m.group(0).strip() if m else None


def parse_api_page(body):
    """(total_pages, records) from one API page; raises ValueError on a non-catalog answer."""
    data = json.loads(body)
    if not isinstance(data, dict) or "results" not in data:
        raise ValueError("not an API result page")
    return int(data.get("total_pages") or 0), data["results"]


def quote_entry(rec):
    parts = [f"EO {rec.get('executive_order_number')}", rec.get("signing_date") or "", rec.get("title") or "",
             rec.get("citation") or "", "Notes: " + (rec.get("disposition_notes") or "(none)")]
    return " | ".join(p for p in parts if p)


def build_records(ids, catalog, pages, coverage_quote, index_info, complete):
    """catalog: {NUMBER: (record, page_no)}; pages: [{page, url, sha256, first, last}]."""
    nums = sorted(int(re.match(r"\d+", n).group()) for n in catalog if re.match(r"\d+", n))
    lo, hi = (nums[0], nums[-1]) if nums else (None, None)
    out = []
    for i in ids:
        n = number_of(i)
        rec_pg = catalog.get(n)
        base = {"instrument_id": i, "searched_number": n, "catalog_lowest_number": lo, "catalog_highest_number": hi,
                "index_url": INDEX_URL, "index_sha256": index_info.get("sha256", ""),
                "coverage_quote": coverage_quote or ""}
        if rec_pg:
            rec, pg = rec_pg
            p = pages[pg]
            base.update(outcome="entry_found", url=rec.get("html_url") or p["url"], page_url=p["url"],
                        page_sha256=p["sha256"], entry_text=quote_entry(rec))
        elif complete and coverage_quote:
            base.update(outcome="searched_complete_no_entry", url="", page_url=";".join(p["url"] for p in pages),
                        page_sha256=";".join(p["sha256"] for p in pages),
                        entry_text="No record with executive_order_number %s in the %d fetched catalog pages "
                                   "(lowest number %s, highest %s)." % (n, len(pages), lo, hi))
        else:
            base.update(outcome="search_incomplete", url="", page_url="", page_sha256="",
                        entry_text="Catalog or coverage statement not fully read; no conclusion.")
        out.append(base)
    return out


def run_search(ids, fetch=http_get, past_stop=lambda: False, sleep=time.sleep, state_cb=lambda s: None):
    """Fetch the coverage page and every catalog page, then build records for ids."""
    index_body, _ = fetch(INDEX_URL)
    index_info = {"sha256": sha256(index_body), "bytes": len(index_body)}
    coverage = parse_index(index_body.decode("utf-8", "replace"))
    catalog, pages, complete, total = {}, [], False, None
    for page in range(1, MAX_PAGES + 1):
        if past_stop():
            break
        url = api_url(page)
        body, _ = fetch(url)
        total, recs = parse_api_page(body)
        nums = [r.get("executive_order_number") for r in recs]
        pages.append({"page": page, "url": url, "sha256": sha256(body), "records": len(recs),
                      "first": nums[0] if nums else None, "last": nums[-1] if nums else None})
        for r in recs:
            n = str(r.get("executive_order_number") or "").strip().upper()
            if n:
                catalog[n] = (r, len(pages) - 1)
        state_cb({"pages_fetched": page, "total_pages": total, "catalog_records": len(catalog)})
        if page >= total:
            complete = True
            break
        sleep(GAP_SECONDS)
    return build_records(ids, catalog, pages, coverage, index_info, complete), {
        "complete": complete, "pages": pages, "total_pages": total, "catalog_records": len(catalog),
        "coverage_quote": coverage, "index_sha256": index_info["sha256"]}
