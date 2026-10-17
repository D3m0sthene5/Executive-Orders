"""Current-law scan: where do the U.S. Code and the eCFR (as of 2026-10-14)
mention executive orders? Runs its unit tests first. See README.md.

Environment (all optional except OUTPUT_DIR / REPO_ROOT):
  JOB_LIMIT          sample size: at most N U.S. Code titles, N eCFR titles,
                     and N search-result pages per eCFR search query
  JOB_USC_TITLES     comma list of U.S. Code title codes, e.g. 03,05,50
  JOB_ECFR_TITLES    comma list of CFR title numbers, e.g. 3,5,32
  JOB_CACHE_DIR      download cache (default <OUTPUT_DIR>/../current-law-cache)
  USC_RELEASE_POINT  release point to read (default: pinned 119-121, current
                     through 2026-10-09); "auto" = latest listed one on or
                     before the cutoff; "119-123@2026-10-13" gives the date of
                     a point that is not on the listing pages
  JOB_SKIP_USC / JOB_SKIP_ECFR   set to 1 to skip a part
  JOB_OFFLINE        set to 1 to use only cached downloads
"""

import json
import os
import pathlib
import subprocess
import sys
import time
import zipfile
from collections import Counter

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

USC_PRIORITY = ["03", "05", "50", "42", "10", "22", "12", "15", "31", "08", "19", "16", "26", "20", "21", "07",
                "49", "40", "41", "43", "33", "46", "47", "18", "28", "25", "38", "05a"]
# Release point read by default: current through Pub. L. 119-121 (2026-10-09),
# the last one dated on or before the cutoff when this job was written. Its
# ZIP URLs follow a stable pattern, so it keeps working after the OLRC
# listing pages drop it. The listing is still read to report newer points.
PINNED_USC_RELEASE_POINT = "119-121"
ECFR_PRIORITY = [3, 5, 32, 2, 31, 29, 41, 28, 22, 24, 48, 7, 15, 40, 10, 49, 50]


class HashingReader:
    def __init__(self, raw):
        import hashlib
        self.raw, self.h, self.n = raw, hashlib.sha256(), 0

    def read(self, size=-1):
        b = self.raw.read(size)
        self.h.update(b)
        self.n += len(b)
        return b

    def drain(self):
        while self.read(1 << 20):
            pass


def env_list(name):
    v = os.environ.get(name, "").strip()
    return [x.strip() for x in v.split(",") if x.strip()] if v else None


def run_tests():
    r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", ".", "-v"], cwd=HERE)
    if r.returncode:
        sys.exit("Unit tests failed; the scan was not run.")


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    run_tests()
    import build
    import ecfr_scan
    import eo_refs
    import net
    import usc_scan

    started = time.time()
    out = pathlib.Path(os.environ["OUTPUT_DIR"]).resolve()
    repo = pathlib.Path(os.environ.get("REPO_ROOT", ".")).resolve()
    out.mkdir(parents=True, exist_ok=True)
    cache = pathlib.Path(os.environ.get("JOB_CACHE_DIR") or (out.parent / "current-law-cache")).resolve()
    limit = int(os.environ["JOB_LIMIT"]) if os.environ.get("JOB_LIMIT", "").strip() else None
    log_path = out / "FETCH_LOG.jsonl"
    if log_path.exists():
        log_path.unlink()
    fetcher = net.Fetcher(cache, log_path=log_path, offline=os.environ.get("JOB_OFFLINE") == "1")
    book = build.Book(build.load_universe(repo))
    book.ecfr_amddate = {}
    summary = {"job": "current-law", "legal_cutoff": eo_refs.LEGAL_CUTOFF, "sample_mode": limit is not None,
               "job_limit": limit, "problems": []}

    # ------------------------------------------------------------ USC --
    if os.environ.get("JOB_SKIP_USC") != "1":
        summary["usc"] = scan_usc(fetcher, book, limit, summary, usc_scan, net)
    # ----------------------------------------------------------- eCFR --
    if os.environ.get("JOB_SKIP_ECFR") != "1":
        summary["ecfr"] = scan_ecfr(fetcher, book, limit, summary, ecfr_scan, net, eo_refs)

    # ---------------------------------------------------------- write --
    book.dedupe()
    search_complete = bool(summary.get("ecfr", {}).get("search_complete"))
    book.mark_search_confirmation(search_complete)
    frags = book.fragments()
    if book.eo_notes:
        for sid in {n["source_id"] for n in book.eo_notes}:
            if sid in book.sources:
                book.sources[sid]["text_path"] = "USC_EO_NOTES.jsonl"
                book.sources[sid]["notes"] += (" Extracted text of each printed executive-order note is in "
                                               "USC_EO_NOTES.jsonl, one JSON line per note, keyed by note_id.")
    # instrument ids per source
    per_source = {}
    for m in book.mentions:
        if m["instrument_id"]:
            per_source.setdefault(m["source_id"], set()).add(m["instrument_id"])
    for sid, rec in book.sources.items():
        rec["instrument_ids"] = sorted(per_source.get(sid, set()))
    build.write_csv(out / "MENTIONS.csv", book.mentions, build.MENTION_FIELDS)
    build.write_csv(out / "EVENT_CANDIDATES.csv", book.events, build.EVENT_FIELDS)
    build.write_jsonl(out / "FRAGMENTS.jsonl", frags)
    build.write_jsonl(out / "SOURCES.jsonl", list(book.sources.values()))
    if book.eo_notes:
        build.write_jsonl(out / "USC_EO_NOTES.jsonl", book.eo_notes)
    if book.search_hits:
        build.write_csv(out / "ECFR_SEARCH_HITS.csv", book.search_hits,
                        ["query", "page", "title", "part", "section", "appendix", "type", "starts_on", "ends_on",
                         "removed", "eo_numbers_in_excerpt", "source_id"])
    orders, conflicts = build.order_table(book)
    build.write_csv(out / "ORDERS_CURRENT_LAW.csv", orders, build.ORDER_FIELDS)
    build.write_csv(out / "POSSIBLE_CONFLICTS.csv", conflicts, build.CONFLICT_FIELDS)

    summary.update(make_counts(book, frags, orders, conflicts))
    summary["fragment_codes"] = book.fragment_codes()
    summary["requests_made"] = fetcher.requests_made
    summary["cache_hits"] = fetcher.cache_hits
    summary["elapsed_seconds"] = round(time.time() - started, 1)
    summary["outputs"] = sorted(p.name for p in out.iterdir() if p.is_file())
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print_summary(summary)


# ----------------------------------------------------------------- USC --
def member_code(member):
    """'uscode/usc05A.xml' -> '05a' (zip member name -> normalized title code)."""
    import usc_scan
    base = member.rsplit("/", 1)[-1]
    return usc_scan.norm_title_code(base[3:-4]) if base.lower().startswith("usc") else base.lower()


def scan_usc(fetcher, book, limit, summary, usc_scan, net):
    pages = []
    for url, rel in (("https://uscode.house.gov/download.html", "usc/pages/download.html"),
                     ("https://uscode.house.gov/priorreleasepoints.html", "usc/pages/priorreleasepoints.html")):
        try:
            meta = fetcher.get(url, rel, route="usc_release_point_listing", expect="html")
            text = pathlib.Path(meta["path"]).read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            summary["problems"].append(f"USC listing page failed: {url}: {exc}")
            continue
        sid = "usc:page:" + rel.rsplit("/", 1)[-1]
        book.add_source(sid, meta, page_or_item="release point listing",
                        notes="OLRC download page; used to check whether a newer release point on or before the cutoff exists.")
        pages.append((text, url))
    points = {}
    for text, url in pages:
        for p in usc_scan.parse_release_points(text, url):
            points.setdefault(p["id"], p)
    rp, why, rp_problems = usc_scan.choose_release(list(points.values()), override=os.environ.get("USC_RELEASE_POINT"),
                                                   pinned=PINNED_USC_RELEASE_POINT)
    summary["problems"].extend(rp_problems)
    checked_through = usc_scan.usc_checked_through(rp)
    info = {"release_point": rp["id"], "current_through_public_law_date": rp["date"], "label": rp["label"],
            "why_chosen": why, "release_points_listed": sorted(points), "checked_through_for_entries": checked_through,
            "titles": []}
    edition = f"U.S. Code release point {rp['id']}"
    book.usc_currency = usc_scan.usc_currency_note(rp)
    info["currency_note"] = book.usc_currency
    avail = {usc_scan.norm_title_code(c): u for c, u in rp["title_zip_urls"].items()}
    wanted = env_list("JOB_USC_TITLES")
    if wanted is not None:
        wanted = [usc_scan.norm_title_code(t) for t in wanted]
    elif limit is not None:
        wanted = [t for t in USC_PRIORITY if t in avail][:limit]
    if wanted is not None:
        zips = []
        for t in wanted:
            url = avail.get(t)
            if not url:
                summary["problems"].append(f"USC title {t} not in release point {rp['id']}")
                continue
            zips.append(url)
    else:
        zips = [rp["all_zip_url"]] if rp["all_zip_url"] else list(rp["title_zip_urls"].values())
    for url in zips:
        name = url.rsplit("/", 1)[-1]
        try:
            meta = fetcher.get(url, f"usc/{rp['id']}/{name}", route="usc_release_point_xml_zip", expect="zip")
            z = zipfile.ZipFile(meta["path"])
        except Exception as exc:
            summary["problems"].append(f"USC download failed: {url}: {exc}")
            continue
        sid = f"usc:{rp['id']}:{name}"
        n_ok = tried = 0
        with z:
            members = sorted(n for n in z.namelist() if n.lower().endswith(".xml"))
            for member in members:
                code = member_code(member)
                if wanted is not None and code not in wanted:
                    continue
                tried += 1
                t0 = time.time()
                try:
                    with z.open(member) as raw:
                        hr = HashingReader(raw)
                        recs = list(usc_scan.scan_uslm(hr, member))
                        hr.drain()
                except Exception as exc:  # one bad title file must not end the run
                    summary["problems"].append(f"USC member {member} in {name} could not be parsed: {type(exc).__name__}: {exc}")
                    continue
                if n_ok == 0:
                    book.add_source(sid, meta, page_or_item=f"{name} (all USLM XML title files in it)",
                                    notes=f"Official OLRC USLM XML, {rp['label']}; Last-Modified {meta.get('last_modified', '')}. "
                                          "Per-title member sha256 values are in MENTIONS.csv page_or_item and SUMMARY.json.")
                    info["release_last_modified"] = meta.get("last_modified", "")
                n_ok += 1
                member_sha = hr.h.hexdigest()
                counts = Counter(k for k, _ in recs)
                kept = Counter()
                for kind, rec in recs:
                    poi = (f"{rec['citation']}" + (f"; note '{rec.get('note_heading', rec.get('heading', ''))[:90]}' [USLM note id {rec['note_id']}]" if rec.get("note_id") else "")
                           + f"; {member} (sha256 {member_sha}) in {name}")
                    if kind == "mention":
                        book.add_mention(rec, "usc", "usc_release_point_xml_zip", edition, sid, poi, checked_through)
                    elif kind == "event":
                        if book.add_event(rec, "usc", edition, sid, poi) is not None:
                            kept["event"] += 1
                    elif kind == "eo_note":
                        ids = [book.u.map(*split_norm(s))[0] for s in rec["subjects"]]
                        book.eo_notes.append(dict(rec, instrument_ids=[i for i in ids if i], edition=edition,
                                                  source_id=sid, page_or_item=poi))
                info["titles"].append({"member": member, "sha256": member_sha, "bytes": hr.n, "zip": name,
                                       "mentions": counts["mention"], "events": kept["event"],
                                       "printed_eo_notes": counts["eo_note"], "seconds": round(time.time() - t0, 1)})
                print(f"  USC {member}: {counts['mention']} mentions, {kept['event']} editorial events, "
                      f"{counts['eo_note']} printed orders ({time.time() - t0:.0f}s)")
        if n_ok == 0:
            summary["problems"].append(f"USC {name}: no title file parsed ({tried} tried); not recorded as a source")
    return info


def split_norm(s):
    import re
    m = re.match(r"(\d+)([A-Za-z]?)$", s)
    return (int(m.group(1)), m.group(2)) if m else (0, "")


def build_cutoff():
    import eo_refs
    return eo_refs.LEGAL_CUTOFF


# ---------------------------------------------------------------- eCFR --
def scan_ecfr(fetcher, book, limit, summary, ecfr_scan, net, eo_refs):
    info = {"date": eo_refs.LEGAL_CUTOFF, "queries": {}, "titles": [], "search_complete": True}
    # 1. point-in-time search
    for q in ecfr_scan.SEARCH_QUERIES:
        slug = "".join(c if c.isalnum() else "_" for c in q).strip("_")
        page, total_pages, n_hits = 1, 1, 0
        while page <= total_pages:
            if limit is not None and page > limit:
                info["search_complete"] = False
                break
            url = ecfr_scan.search_url(q, page)
            try:
                meta = fetcher.get(url, f"ecfr/search/{eo_refs.LEGAL_CUTOFF}/{slug}_p{page}.json",
                                   route="ecfr_search_api_point_in_time", expect="json")
                m, hits = ecfr_scan.parse_search_page(pathlib.Path(meta["path"]).read_bytes())
            except Exception as exc:
                summary["problems"].append(f"eCFR search failed: {url}: {type(exc).__name__}: {exc}")
                info["search_complete"] = False
                break
            sid = f"ecfr:search:{slug}:p{page}"
            book.add_source(sid, meta, page_or_item=f"eCFR search results, query {q}, date={eo_refs.LEGAL_CUTOFF}, page {page}",
                            notes="Point-in-time search API; each result is a section in force on the date; excerpts are partial.")
            total_pages = int(m.get("total_pages") or 1)
            info["queries"][q] = {"total_count": m.get("total_count"), "total_pages": total_pages}
            for h in hits:
                n_hits += 1
                ms = ecfr_scan.search_hit_mentions(h)
                book.search_hits.append(dict(h, query=q, page=page, source_id=sid,
                                             eo_numbers_in_excerpt=" ".join(sorted({eo_refs.normalized(x['eo_number'], x['eo_suffix']) for x in ms}))))
                for rec in ms:
                    poi = f"{rec['citation']} (eCFR search API result, query {q}, date={eo_refs.LEGAL_CUTOFF}, page {page})"
                    book.add_mention(rec, "ecfr", "ecfr_search_api_point_in_time", f"eCFR as of {eo_refs.LEGAL_CUTOFF}",
                                     sid, poi, eo_refs.LEGAL_CUTOFF, changed_after_cutoff="n/a (point-in-time)")
            page += 1
        info["queries"].setdefault(q, {})["hits_read"] = n_hits
    # 2. full titles
    try:
        # Fixed cache name (retrieved_utc is in its .meta.json), so JOB_OFFLINE=1 works on a later day.
        tmeta = fetcher.get(ecfr_scan.TITLES_URL, "ecfr/titles.json", route="ecfr_titles_api", expect="json")
        tlist = json.loads(pathlib.Path(tmeta["path"]).read_text(encoding="utf-8"))["titles"]
        title_meta = {t["number"]: t for t in tlist}
        titles = [t["number"] for t in tlist if not t.get("reserved")]
        book.add_source("ecfr:titles", tmeta, page_or_item="eCFR title list", notes="Used to list non-reserved titles.")
    except Exception as exc:
        summary["problems"].append(f"eCFR titles list failed: {type(exc).__name__}: {exc}; using titles 1-50 (reserved ones will fail)")
        title_meta = {}
        titles = list(range(1, 51))
    wanted = env_list("JOB_ECFR_TITLES")
    if wanted is not None:
        titles = [int(t) for t in wanted]
    elif limit is not None:
        titles = [t for t in ECFR_PRIORITY if t in titles][:limit]
    window_start = ecfr_scan.versions_url(1).rsplit("=", 1)[-1]
    for t in titles:
        t0 = time.time()
        try:
            vmeta = fetcher.get(ecfr_scan.versions_url(t), f"ecfr/versions/title-{t}_since_{window_start}.json",
                                route="ecfr_versioner_versions", expect="json")
            vrows = ecfr_scan.version_rows(pathlib.Path(vmeta["path"]).read_bytes())
            nchg = sum(1 for r in vrows if r[0] > eo_refs.LEGAL_CUTOFF)
            book.add_source(f"ecfr:versions:title-{t}", vmeta, page_or_item=f"title {t} content versions issued since {window_start}",
                            notes=f"Used to flag sections whose text changed after {eo_refs.LEGAL_CUTOFF} (or between the bulk file date and the cutoff).")
        except Exception as exc:
            summary["problems"].append(f"eCFR versions failed for title {t}: {type(exc).__name__}: {exc}")
            vrows, nchg = None, None
        url = ecfr_scan.GOVINFO_URL.format(title=t)
        amddates, recs = [], []
        try:
            meta = fetcher.get(url, f"ecfr/govinfo/ECFR-title{t}.xml", route="govinfo_ecfr_bulk_xml", expect="xml")
            with open(meta["path"], "rb") as f:
                for kind, rec in ecfr_scan.scan_ecfr_xml(f, t):
                    if kind == "amddate":
                        if rec:
                            amddates.append(rec)
                    else:
                        recs.append((kind, rec))
        except Exception as exc:  # one bad title must not end the run
            summary["problems"].append(f"GovInfo eCFR title {t} failed: {url}: {type(exc).__name__}: {str(exc)[:200]}")
            continue
        sid = f"ecfr:govinfo:title-{t}"
        book.add_source(sid, meta, page_or_item=f"ECFR-title{t}.xml (whole title)",
                        notes=f"GovInfo eCFR bulk XML (current text); Last-Modified {meta.get('last_modified', '')}.")
        amddate = max(amddates) if amddates else None  # each volume carries its own date; the title is current to the latest
        latest = title_meta.get(t, {}).get("latest_amended_on")
        stale = bool(amddate and latest and amddate < min(latest, eo_refs.LEGAL_CUTOFF))
        flags = Counter()
        edition = f"eCFR (GovInfo bulk, amended through {amddate})"
        n_mentions = n_events = 0
        for kind, rec in recs:
            poi = f"{rec['citation']} ({rec['location_kind']}; GovInfo eCFR XML title {t}, amended through {amddate}; NODE {rec['container_id']})"
            if kind == "event":
                if book.add_event(rec, "ecfr", edition, sid, poi) is not None:
                    n_events += 1
                continue
            n_mentions += 1
            chg = ecfr_scan.currency_flag(rec, vrows, amddate, window_start=window_start)
            flags[chg] += 1
            ct = eo_refs.LEGAL_CUTOFF if chg == "no" else None
            book.add_mention(rec, "ecfr", "govinfo_ecfr_bulk_xml", edition, sid, poi, ct, changed_after_cutoff=chg)
        book.ecfr_amddate[str(t)] = amddate
        info["titles"].append({"title": t, "sha256": meta["sha256"], "bytes": meta["bytes"], "amddate": amddate,
                               "ecfr_latest_amended_on": latest, "bulk_file_behind_ecfr": stale,
                               "mentions": n_mentions, "text_events": n_events, "currency_flags": dict(flags),
                               "versions_after_cutoff": nchg, "seconds": round(time.time() - t0, 1)})
        if stale:
            summary["problems"].append(f"eCFR title {t}: GovInfo bulk file amended through {amddate} but eCFR says {latest}; "
                                       "sections changed in between are flagged only if inside the versions window")
        print(f"  eCFR title {t}: {n_mentions} mentions, {n_events} text events (amended through {amddate}, "
              f"{nchg} versions after cutoff, {time.time() - t0:.0f}s)")
    return info


# -------------------------------------------------------------- counts --
def make_counts(book, frags, orders, conflicts):
    import build
    u = book.u
    yes = {i for i, s in u.statuses.items() if s == "yes"}
    no = {i for i, s in u.statuses.items() if s == "no"}
    by_sys = {}
    for system in ("usc", "ecfr"):
        ms = [m for m in book.mentions if m["system"] == system]
        ids = {m["instrument_id"] for m in ms if m["instrument_id"]}
        pred = {m["instrument_id"] for m in ms if m["instrument_id"] and m["is_predicate_lead"] == "yes"}
        by_sys[system] = {"mention_rows": len(ms), "orders_mentioned": len(ids), "orders_with_predicate_leads": len(pred),
                          "unmapped_mention_rows": sum(1 for m in ms if not m["instrument_id"]),
                          "caution_rows": sum(1 for m in ms if m.get("caution")),
                          "by_role": dict(Counter(m["role"] for m in ms).most_common()),
                          "provisional_yes_mentioned": len(ids & yes), "provisional_yes_with_predicate_leads": len(pred & yes),
                          "provisional_no_mentioned": len(ids & no), "provisional_no_with_predicate_leads": len(pred & no)}
    all_ids = {m["instrument_id"] for m in book.mentions if m["instrument_id"]}
    all_pred = {m["instrument_id"] for m in book.mentions if m["instrument_id"] and m["is_predicate_lead"] == "yes"}
    printed = {m["instrument_id"] for m in book.mentions if m["instrument_id"] and m["role"] == "printed_eo_text"}
    ended = {e["subject_instrument_id"] for e in book.events if e["subject_instrument_id"] and e["event_type_candidate"] != "amendment"
             and e["in_scope"] == "yes" and not any(c in e["caution"] for c in build.EXCLUDED_CAUTIONS)}
    return {
        "counts": {
            "orders_mentioned_any_source": len(all_ids),
            "orders_with_predicate_leads_any_source": len(all_pred),
            "by_source": by_sys,
            "provisional_yes_total": len(yes),
            "provisional_yes_with_any_current_mention": len(all_ids & yes),
            "provisional_yes_with_predicate_lead": len(all_pred & yes),
            "provisional_no_total": len(no),
            "provisional_no_printed_or_cited_in_current_law (POSSIBLE_CONFLICTS.csv)": len(conflicts),
            "provisional_no_printed_as_text_in_usc": len(printed & no),
            "provisional_no_with_ending_statement_found": len(ended & no),
            "orders_with_ending_or_amendment_statements": len({e["subject_instrument_id"] for e in book.events if e["subject_instrument_id"]}),
            "event_candidates": len(book.events),
            "event_candidates_after_cutoff_excluded": sum(1 for e in book.events if e["in_scope"] != "yes"),
            "event_candidates_by_caution": dict(Counter(e["caution"] or "none" for e in book.events).most_common()),
            "event_candidates_by_scope": dict(Counter(e["scope_candidate"] or "n/a (amendment)" for e in book.events).most_common()),
            "event_candidates_by_system": dict(Counter(e["system"] for e in book.events)),
            "events_dropped": dict(book.dropped_events),
            "fragments": dict(Counter(f["kind"] for f in frags)),
            "possible_conflicts_by_signal": dict(sorted(Counter(c["signal"] for c in conflicts).items())),
            "usc_printed_eo_notes": len(book.eo_notes),
            "ecfr_search_hits": len(book.search_hits),
            "sources": len(book.sources),
        }
    }


def print_summary(s):
    c = s["counts"]
    print()
    print("Current-law scan finished" + (" (SAMPLE run, JOB_LIMIT=%s)" % s["job_limit"] if s["sample_mode"] else ""))
    if "usc" in s:
        print(f"  U.S. Code release point {s['usc']['release_point']} (current through a law of {s['usc']['current_through_public_law_date']}), "
              f"{len(s['usc']['titles'])} title file(s) read")
    if "ecfr" in s:
        print(f"  eCFR: {len(s['ecfr']['titles'])} title file(s) read; point-in-time search {'complete' if s['ecfr']['search_complete'] else 'PARTIAL'}")
    for k, v in c["by_source"].items():
        print(f"  {k.upper()}: {v['mention_rows']} mention rows, {v['orders_mentioned']} orders named, "
              f"{v['orders_with_predicate_leads']} with 'still operating' leads")
    print(f"  Provisional YES orders with at least one current-law mention: {c['provisional_yes_with_any_current_mention']} of {c['provisional_yes_total']}")
    print(f"  Provisional NO orders still printed or cited in current law (possible conflicts, leads only): "
          f"{c['provisional_no_printed_or_cited_in_current_law (POSSIBLE_CONFLICTS.csv)']}")
    print(f"  Editorial revocation/amendment statements found: {c['event_candidates']}")
    print(f"  Requests made: {s['requests_made']}, cache hits: {s['cache_hits']}, time {s['elapsed_seconds']}s")
    for p in s["problems"]:
        print("  PROBLEM:", p)
    print("Nothing here changes any provisional status; every row is a lead for human review.")


if __name__ == "__main__":
    main()
