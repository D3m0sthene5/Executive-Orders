"""Clark, online stage: hunt the open web for orders the project cannot identify, and for orders it
has never recorded.

Two campaigns, after the offline stage (clark.py):

1. Targets. Number gaps and plausible cited-but-unknown ids first, then census orders known by
   number only, searched by number, date window and every query strategy across every engine that
   answers; pages that name the order are read and quoted. State carries forward run to run.
2. List pages. Every page in `list_pages.txt` (and the pages it links to about executive orders)
   is read and harvested for every executive-order number it names, with the date and title
   printed beside it. Numbers the census lacks go to WEB_LISTED_ORDERS.csv. Any page read in the
   target campaign is harvested the same way (WEB_NUMBERS_NAMED.csv).

Environment: JOB_MAX_REQUESTS (default 400), JOB_MAX_TARGETS (default 30), JOB_CACHE_DIR. The defaults keep a run
short, so a push to the branch while it runs rarely collides with it; state carries forward anyway.
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "_lib"))
import eo_identity as ident  # noqa: E402
import eo_websearch as web  # noqa: E402

JOB = "clark-discovery"
LIST_PAGES = os.path.join(HERE, "list_pages.txt")
LIST_LINK = re.compile(r"(?i)executive\s+orders?")


def targets_from_outputs(out_dir, dates):
    out = {}

    def add(iid, kind, priority, date="", title=""):
        p = ident.parse_eo_id(iid)
        if not p or iid in out:
            return
        d = dates.get(iid) or {}
        out[iid] = {"id": iid, "number": p[0], "suffix": p[1], "date": date or d.get("date", ""),
                    "title": title or d.get("title", ""), "president": d.get("president", ""), "kind": kind, "priority": priority}

    for r in ident.read_csv(os.path.join(out_dir, "NUMBER_GAPS.csv")):
        date = ""
        m = re.search(r"app_index:(\d{4}-\d{2}-\d{2}):([^;]*)", r.get("identity_evidence", ""))
        title = m.group(2).strip() if m else ""
        if m:
            date = m.group(1)
        else:
            m2 = re.search(r"cited_with_date:(\d{4}-\d{2}-\d{2})", r.get("identity_evidence", ""))
            date = m2.group(1) if m2 else (r.get("window_from", "").split(" ")[-1][:4] if r.get("window_from") else "")
        add(r["instrument_id"], "number_gap", 0 if r.get("strength") in ("strong", "cited") else 1, date, title)
    for r in ident.read_csv(os.path.join(out_dir, "CITED_BUT_UNKNOWN.csv")):
        if r.get("plausibility") == "plausible":
            add(r["cited_id"], "cited_but_unknown", 1, r.get("date_stated", "") or r.get("citing_date", "")[:4])
    for r in ident.read_csv(os.path.join(out_dir, "IDENTITY_UNKNOWN.csv")):
        pr = 2 if r.get("proquest_link_supplied") != "yes" else 4
        add(r["instrument_id"], "identity_unknown", pr, r.get("census_year", ""))
    return list(out.values())


def harvest_list_page(text, url):
    """Every order number a page names, with a date and a few title words printed beside it."""
    rows = []
    for m in ident.find_mentions(text):
        iid = ident.canon_id(m["number"], m["suffix"])
        around = m["quote"]
        date = m["date"]
        if not date:
            dm = re.search(r"((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}|\d{4}-\d{2}-\d{2})", around)
            if dm:
                d = ident.parse_prose_date(dm.group(1)) or ident.parse_date(dm.group(1))
                date = d.isoformat() if d else ""
        rows.append({"instrument_id": iid, "date_seen": date, "context": around[:240], "page": url})
    return rows


def run_list_pages(searcher, seeds, universe, out_dir, max_pages=60):
    seen, queue, rows, pages_read = set(), list(seeds), [], []
    while queue and max_pages > 0 and searcher.budget_left():
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        text, links, rec = searcher.read_page(url)
        pages_read.append({"url": url, "status": rec["status"], "error": rec.get("error", ""), "sha256": rec["sha256"]})
        max_pages -= 1
        if not text:
            continue
        rows.extend(harvest_list_page(text, url))
        host = urllib.parse.urlsplit(url).hostname
        for link in links:
            if LIST_LINK.search(link["text"]) and urllib.parse.urlsplit(link["url"]).hostname == host and link["url"] not in seen:
                queue.append(link["url"])
    by_id = {}
    for r in rows:
        cur = by_id.setdefault(r["instrument_id"], {"instrument_id": r["instrument_id"], "in_census": "yes" if r["instrument_id"] in universe else "no",
                                                    "pages": set(), "dates_seen": set(), "context": r["context"]})
        cur["pages"].add(r["page"])
        if r["date_seen"]:
            cur["dates_seen"].add(r["date_seen"])
    out = []
    for iid, r in sorted(by_id.items(), key=lambda kv: ident.parse_eo_id(kv[0]) or (0, "")):
        out.append({"instrument_id": iid, "in_census": r["in_census"], "pages_naming_it": len(r["pages"]),
                    "dates_seen": "|".join(sorted(r["dates_seen"])), "example_page": sorted(r["pages"])[0], "context": r["context"]})
    with open(os.path.join(out_dir, "WEB_LISTED_ORDERS.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["instrument_id", "in_census", "pages_naming_it", "dates_seen", "example_page", "context"])
        w.writeheader()
        w.writerows(out)
    return {"pages_read": pages_read, "orders_named": len(out), "not_in_census": sum(1 for r in out if r["in_census"] == "no")}


def run(root, out_dir, transport=None, env=None, engines=None):
    env = os.environ if env is None else env
    dates = ident.load_dates(root)
    universe = set(ident.load_universe(root))
    targets = targets_from_outputs(out_dir, dates)
    cache = env.get("JOB_CACHE_DIR") or os.path.join(out_dir, "..", ".web-cache")
    max_requests = int(env.get("JOB_MAX_REQUESTS", "400"))
    list_budget = max(10, min(100, max_requests // 4))  # a share of the budget for the list pages
    summary = web.run_campaign(JOB, root, out_dir, targets, cache_dir=os.path.join(cache, "web"),
                               max_requests=max(1, max_requests - list_budget), max_targets=int(env.get("JOB_MAX_TARGETS", "30")),
                               transport=transport, env=env, engines=engines, universe_ids=universe)
    seeds = []
    if os.path.exists(LIST_PAGES):
        with open(LIST_PAGES, encoding="utf-8") as fh:
            seeds = [l.split("#", 1)[0].strip() for l in fh if l.split("#", 1)[0].strip()]
    searcher = web.Searcher(os.path.join(cache, "web"), max_requests=list_budget, transport=transport, env=env, engines=engines)
    lists = run_list_pages(searcher, seeds, universe, out_dir)
    summary["list_pages"] = lists
    with open(os.path.join(out_dir, "SOURCES.jsonl"), "a", encoding="utf-8") as fh:
        for s in searcher.sources:
            fh.write(json.dumps(s, sort_keys=True) + "\n")
    with open(os.path.join(out_dir, "WEB_SUMMARY.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
    append_report(os.path.join(out_dir, "REPORT.md"), summary)
    return summary


def append_report(path, s):
    lp = s["list_pages"]
    lines = ["", "## Web search (online stage)", "",
             f"{s['advanced_this_run']} of {s['targets_total']} unknowns advanced this run ({s['never_searched']} never searched yet); "
             f"{s['requests_used']} of {s['max_requests']} requests used. {s['hits_total']} hits on file, {s['leads_page_confirmed']} pages "
             f"confirmed to name the order ({s['targets_with_page_confirmed_lead']} unknowns): `WEB_LEADS.csv`. "
             f"{s['numbers_named_not_in_census']} order numbers named on pages read are absent from the census: `WEB_NUMBERS_NAMED.csv`.", "",
             f"List pages: {len(lp['pages_read'])} read, {lp['orders_named']} order numbers named, **{lp['not_in_census']} absent from the census**: "
             "`WEB_LISTED_ORDERS.csv`.", "", "| Engine | Status |", "|---|---|"]
    for k, v in sorted(s["engines"].items()):
        lines.append(f"| {k} | {v} |")
    with open(path, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    root = os.environ.get("REPO_ROOT") or os.path.abspath(os.path.join(HERE, "..", ".."))
    out = os.environ.get("OUTPUT_DIR") or os.path.join(HERE, "output")
    print(json.dumps(run(root, out), indent=2))
