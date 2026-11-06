"""Mabillon scan inventory: which bound or digitized sets of numbered executive orders exist, by number range?

The State Department began the numbered series in 1907 and the Government Printing Office printed orders as slips,
which libraries bound as "Executive Orders" volumes with number ranges in their titles. The project already reads
eight such volumes (orders 6071-8027) from Wikimedia Commons. This job asks two keyless public catalogues which other
volumes exist, so a later job can read them: the Commons category of executive-order scans (HTML category pages,
recursively, bounded) and the Internet Archive's advanced search (texts titled "executive orders", 1862-1945).

It downloads no scans: only catalogue pages. Each volume's number range is read from its title, and the frame's
orders inside each range are counted as a ceiling (a range in a title is not proof that each order is printed).
"""
from __future__ import annotations

import csv
import html
import json
import os
import re
import sys
import time
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("REPO_ROOT", HERE.parent.parent)).resolve()
sys.path.insert(0, str(REPO / "jobs/_lib"))
FRAME = REPO / "research/mabillon/frame/FRAME.csv"
COMMONS = "https://commons.wikimedia.org"
ROOT_CATEGORIES = ["Category:Executive_orders_of_the_United_States"]
IA_SEARCH = ("https://archive.org/advancedsearch.php?q={q}&fl%5B%5D=identifier&fl%5B%5D=title&fl%5B%5D=date"
             "&fl%5B%5D=publisher&fl%5B%5D=collection&fl%5B%5D=volume&rows=500&page={page}&output=json")
IA_QUERIES = ['title:("executive orders") AND mediatype:texts AND date:[1862-01-01 TO 1945-12-31]',
              'title:("executive order") AND mediatype:texts AND date:[1862-01-01 TO 1945-12-31]',
              'title:("proclamations and executive orders") AND mediatype:texts']
RANGE = re.compile(r"(?:executive[_\s]+orders?|nos?\.?|numbers?)[_\s,]*(\d{1,5})\s*[A-Z]?\s*(?:-|–|_to_|\sto\s|through|thru)\s*"
                   r"(\d{1,5})", re.I)
# Only United States presidential order categories of the period the frame needs, and the National Archives' own
# upload series. The first run (60 pages) spent its pages on state and photograph categories.
PRESIDENTS = ("Abraham_Lincoln", "Andrew_Johnson", "Ulysses_S._Grant", "Rutherford_B._Hayes", "James_A._Garfield",
              "Chester_A._Arthur", "Grover_Cleveland", "Benjamin_Harrison", "William_McKinley", "Theodore_Roosevelt",
              "William_Howard_Taft", "Woodrow_Wilson", "Warren_G._Harding", "Calvin_Coolidge", "Herbert_Hoover",
              "Franklin_D._Roosevelt")
WANTED_CATEGORY = re.compile(r"Category:(?:Executive_orders_of_(?:the_United_States(?:_by_president)?|"
                             + "|".join(re.escape(p) for p in PRESIDENTS) + r")$|US_National_Archives_series:_Executive)")
UNWANTED_CATEGORY = re.compile(r"signing|_by_state", re.I)
LINK = re.compile(r'<a[^>]+href="(/wiki/(?:Category|File):[^"#?]+)"[^>]*>', re.I)


def ranges_in(title):
    out = []
    for a, b in RANGE.findall(html.unescape(urllib.parse.unquote(title or "")).replace("_", " ")):
        a, b = int(a), int(b)
        if a < b <= 15000 and b - a <= 3000:
            out.append((a, b))
    return out


def commons(pool, max_pages):
    seen, queue, files, pages = set(), list(ROOT_CATEGORIES), {}, 0
    while queue and pages < max_pages:
        cat = queue.pop(0)
        if cat in seen:
            continue
        seen.add(cat)
        url = f"{COMMONS}/wiki/{cat}"
        nxt = url
        while nxt and pages < max_pages:
            got = pool.fetch(nxt)
            pages += 1
            body = got["body"].decode("utf-8", "replace")
            for href in LINK.findall(body):
                name = urllib.parse.unquote(href.split("/wiki/", 1)[1])
                if name.startswith("Category:"):
                    if WANTED_CATEGORY.search(name) and not UNWANTED_CATEGORY.search(name):
                        queue.append(name)
                elif re.search(r"\.(djvu|pdf)$", name, re.I):
                    files.setdefault(name, {"host": "commons", "id": name, "title": name, "source_page": url})
            m = re.search(r'<a href="([^"]+pagefrom=[^"]+)"[^>]*>next page', body)
            nxt = COMMONS + html.unescape(m.group(1)) if m else None
    return list(files.values()), pages, sorted(seen)


def internet_archive(pool):
    out = {}
    for q in IA_QUERIES:
        for page in (1, 2, 3):
            got = pool.fetch(IA_SEARCH.format(q=urllib.parse.quote(q), page=page))
            docs = (json.loads(got["body"].decode("utf-8", "replace")).get("response") or {}).get("docs") or []
            for d in docs:
                coll = d.get("collection") or []
                coll = coll if isinstance(coll, list) else [coll]
                # The Philippine government's annual "Executive Orders" (collection govph) restart at 1 each year;
                # they are not the United States numbered series and would give false range ceilings.
                if any(re.match(r"govph|philippine", str(c), re.I) for c in coll):
                    continue
                flat = lambda v: " ; ".join(v) if isinstance(v, list) else str(v or "")  # noqa: E731
                out[d["identifier"]] = {"host": "internet_archive", "id": d["identifier"],
                                        "title": flat(d.get("title")) + (" " + flat(d.get("volume")) if d.get("volume") else ""),
                                        "date": flat(d.get("date")), "publisher": flat(d.get("publisher")),
                                        "collection": flat(d.get("collection")),
                                        "source_page": f"https://archive.org/details/{d['identifier']}"}
            if len(docs) < 500:
                break
    return list(out.values())


def main(out=None, pool=None):
    out = Path(out or os.environ.get("OUTPUT_DIR", HERE / "output"))
    out.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    if pool is None:
        from fetch_pool import FetchPool
        pool = FetchPool(Path(os.environ.get("JOB_CACHE_DIR", REPO / ".job-cache/mabillon-scan-inventory")),
                         workers=2, per_host=1, min_interval=1.0, max_bytes=20_000_000,
                         user_agent="EO-Road-System/1.0 (mabillon-scan-inventory; "
                                    "https://github.com/D3m0sthene5/Executive-Orders)")
    errors = []
    try:
        cfiles, cpages, cats = commons(pool, int(os.environ.get("JOB_MAX_PAGES", "150")))
    except Exception as exc:  # noqa: BLE001 - a refusal is recorded, never worked around
        cfiles, cpages, cats = [], 0, []
        errors.append({"host": "commons", "error": f"{type(exc).__name__}: {exc}"[:300]})
    try:
        ia = internet_archive(pool)
    except Exception as exc:  # noqa: BLE001
        ia = []
        errors.append({"host": "internet_archive", "error": f"{type(exc).__name__}: {exc}"[:300]})
    frame = []
    if FRAME.is_file():
        with open(FRAME, newline="", encoding="utf-8") as f:
            frame = [int(r["number"]) for r in csv.DictReader(f) if r["number"]]
    rows, covered = [], set()
    for v in cfiles + ia:
        if v["host"] == "commons" and not re.search(r"Executive[_ ]Orders?|EOCompilation|Title_3_CFR", v["id"], re.I):
            continue  # Commons category pages also list unrelated files (CFR titles, state orders)
        for a, b in ranges_in(v["title"]) or [(None, None)]:
            inside = [n for n in frame if a is not None and a <= n <= b]
            if a is not None and a < 5076:
                covered.update(inside)
            rows.append({**{k: v.get(k, "") for k in ("host", "id", "title", "date", "publisher", "collection",
                                                     "source_page")},
                         "range_low": a or "", "range_high": b or "", "frame_orders_in_range": len(inside)})
    rows.sort(key=lambda r: (r["range_low"] == "", r["range_low"] or 0, r["host"], r["id"]))
    with open(out / "SCANS.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["host", "id", "title", "date", "publisher", "collection", "source_page",
                                          "range_low", "range_high", "frame_orders_in_range"])
        w.writeheader()
        w.writerows(rows)
    ranged = [r for r in rows if r["range_low"] != ""]
    summary = {"job": "mabillon-scan-inventory", "commons_category_pages": cpages, "commons_categories": cats,
               "commons_files": len(cfiles), "ia_items": len(ia), "volumes_with_number_range": len(ranged),
               "ranges": [[r["host"], r["id"], r["range_low"], r["range_high"]] for r in ranged],
               "frame_orders_below_5076_inside_a_listed_range": len(covered),
               "errors": errors, "requests": pool.requests, "seconds": round(time.monotonic() - started),
               "what_this_is_not": "Catalogue entries only; a range in a title is a ceiling, not a verified printing."}
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=1)[:6000])
    return summary


if __name__ == "__main__":
    main()
