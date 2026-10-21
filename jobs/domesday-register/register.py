"""Domesday: one table of every executive order the project knows to have been signed, and what it holds for each.

One row per order in the 14,972-order census (research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv):
its number, date, title and president from the best index the project has; every source held, by
class (official original, archival replica scan, compiled or volunteer transcription); the readiness
tracker's status and blockers; the ProQuest acquisition state; and what Lewis and Clark last found
for it, offline and on the web. A second table lists order numbers that are NOT in the census but
that some index, citation, web page or list names: candidates for census intake, never entries.

Like the Domesday survey, this records what is held, not what is true: a row's `best_held` is the
strongest class of document on file, and nothing here authenticates an identity, assigns a custody
grade or changes a count. The census file remains the only universe; the tracker remains the only
readiness count.
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "_lib"))
import eo_identity as ident  # noqa: E402

JOB = "domesday-register"
LEWIS = "jobs/lewis-originals/output"
CLARK = "jobs/clark-discovery/output"
PINAKES = "jobs/pinakes-proquest-ingest/output"
FIELDS = ["instrument_id", "number", "suffix", "era", "census_class", "date", "date_source", "title", "president",
          "best_held", "official_sources", "archival_replica", "transcription_sources", "text_files",
          "provisional_status", "original_text_step", "ready_for_human_review", "blockers",
          "proquest_link_supplied", "proquest_pdf_file", "proquest_pdf_sha256", "proquest_text_source", "proquest_text_usable",
          "lewis_route", "lewis_status", "lewis_next_action", "lewis_web_best_score", "lewis_web_best_url",
          "clark_class", "clark_web_best_score", "clark_web_best_url", "web_pages_naming_it"]
CANDIDATE_FIELDS = ["instrument_id", "number", "suffix", "named_by", "dates_seen", "titles_seen", "strength", "example_source", "note"]


def web_best(root, job):
    """id -> (best_score, best_url) from a job's committed WEB_STATE.json."""
    path = os.path.join(root, job, "WEB_STATE.json")
    out = {}
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as fh:
                for iid, st in (json.load(fh).get("targets") or {}).items():
                    out[iid] = (st.get("best_score", 0), st.get("best_url", ""))
        except (OSError, ValueError):
            pass
    return out


def run(root, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    universe = ident.load_universe(root)
    readiness = ident.load_readiness(root)
    frags = ident.load_fragments(root)
    dates = ident.load_dates(root, frags)
    pq_rows = {ident.canon_id(*ident.parse_eo_id(str(r["id"]))): r for r in ident.load_proquest_rows(root)}
    routes = {r["instrument_id"]: r for r in ident.read_csv(os.path.join(root, LEWIS, "ROUTES.csv"))}
    pq_inv = {r["instrument_id"]: r for r in ident.read_csv(os.path.join(root, PINAKES, "ORDERS.csv")) if r.get("instrument_id")}
    if not pq_inv:  # before the ingest has run, Lewis's own inventory
        pq_inv = {r["instrument_id"]: r for r in ident.read_csv(os.path.join(root, LEWIS, "PROQUEST_INVENTORY.csv"))
                  if r.get("instrument_id") and r.get("pdf_signature") == "yes" and not r.get("duplicate_of")}
    clark_class = {}
    for name, cls in (("NUMBER_GAPS.csv", "number_gap"), ("IDENTITY_UNKNOWN.csv", "identity_unknown")):
        for r in ident.read_csv(os.path.join(root, CLARK, name)):
            clark_class.setdefault(r["instrument_id"], cls)
    lewis_web, clark_web = web_best(root, LEWIS), web_best(root, CLARK)
    named = collections.Counter()
    for job in (LEWIS, CLARK):
        for r in ident.read_csv(os.path.join(root, job, "WEB_NUMBERS_NAMED.csv")):
            named[r["instrument_id"]] += int(r.get("pages_naming_it") or 0)
    listed = {r["instrument_id"]: r for r in ident.read_csv(os.path.join(root, CLARK, "WEB_LISTED_ORDERS.csv"))}
    problems = []
    if not universe:
        problems.append("universe file missing")

    rows = []
    for iid in sorted(universe, key=lambda i: (ident.parse_eo_id(i) or (10**9, ""), i)):
        u, rd, d = universe[iid], readiness.get(iid, {}), dates.get(iid, {})
        p = ident.parse_eo_id(iid) or ("", "")
        fs = frags.get(iid, [])
        official = sorted({f["produced_by"] for f in fs if f["class"] == "official"})
        replica = sorted({f["produced_by"] for f in fs if f["class"] == "archival_replica"})
        transcription = sorted({f["produced_by"] for f in fs if f["class"] == "transcription"})
        texts = sum(1 for f in fs if f["text_path"] and os.path.isfile(f["text_path"]))
        if rd.get("step_original_text") == "done":
            best = "official_original_counted"
        elif official:
            best = "official_found_page_check_pending"
        elif replica or iid in pq_inv:
            best = "archival_replica_scan"
        elif transcription:
            best = "transcription_only"
        else:
            best = "nothing"
        r = routes.get(iid, {})
        lw, cw = lewis_web.get(iid, (0, "")), clark_web.get(iid, (0, ""))
        rows.append({
            "instrument_id": iid, "number": p[0], "suffix": p[1], "era": u.get("year_group", ""), "census_class": u.get("bibliographic_class", ""),
            "date": d.get("date", ""), "date_source": d.get("date_source", ""), "title": (d.get("title") or "")[:200], "president": d.get("president", ""),
            "best_held": best, "official_sources": "|".join(official), "archival_replica": "|".join(replica), "transcription_sources": "|".join(transcription),
            "text_files": texts, "provisional_status": rd.get("provisional_status", ""), "original_text_step": rd.get("step_original_text", ""),
            "ready_for_human_review": rd.get("ready_for_human_review", ""), "blockers": rd.get("blockers", ""),
            "proquest_link_supplied": "yes" if iid in pq_rows else "no",
            "proquest_pdf_file": pq_inv.get(iid, {}).get("file", ""), "proquest_pdf_sha256": pq_inv.get(iid, {}).get("sha256", ""),
            "proquest_text_source": pq_inv.get(iid, {}).get("text_source", ""), "proquest_text_usable": pq_inv.get(iid, {}).get("text_usable", ""),
            "lewis_route": r.get("best_route", ""), "lewis_status": r.get("route_status", ""), "lewis_next_action": r.get("next_action", ""),
            "lewis_web_best_score": lw[0] or "", "lewis_web_best_url": lw[1], "clark_class": clark_class.get(iid, ""),
            "clark_web_best_score": cw[0] or "", "clark_web_best_url": cw[1], "web_pages_naming_it": named.get(iid, 0),
        })
    with open(os.path.join(out_dir, "REGISTER.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    # candidates: numbers named somewhere that the census lacks
    cand = {}

    def add(iid, by, date="", title="", strength="", src="", note=""):
        p = ident.parse_eo_id(iid)
        if not p or iid in universe:
            return
        c = cand.setdefault(iid, {"instrument_id": iid, "number": p[0], "suffix": p[1], "named_by": set(), "dates_seen": set(),
                                  "titles_seen": set(), "strength": "", "example_source": src, "note": note})
        c["named_by"].add(by)
        if date:
            c["dates_seen"].add(date)
        if title:
            c["titles_seen"].add(title[:120])
        rank = {"strong": 3, "cited": 2, "weak": 1, "": 0}
        if rank.get(strength, 0) > rank.get(c["strength"], 0):
            c["strength"] = strength
        c["example_source"] = c["example_source"] or src

    for r in ident.read_csv(os.path.join(root, CLARK, "NUMBER_GAPS.csv")):
        ev = r.get("identity_evidence", "")
        add(r["instrument_id"], "number_gap:" + r.get("known_to_index", ""), "", "", r.get("strength", ""), ev[:160],
            f"window {r.get('window_from', '')} -> {r.get('window_to', '')}")
    for r in ident.read_csv(os.path.join(root, CLARK, "CITED_BUT_UNKNOWN.csv")):
        if r.get("plausibility") == "plausible":
            add(r["cited_id"], "cited_by:" + r.get("citing_id", ""), r.get("date_stated", ""), "", "cited", r.get("source_ref", ""), r.get("quote", "")[:160])
    for iid, r in listed.items():
        if r.get("in_census") == "no":
            add(iid, "web_list_page", (r.get("dates_seen") or "").split("|")[0], r.get("context", "")[:120], "cited", r.get("example_page", ""))
    for job in (LEWIS, CLARK):
        for r in ident.read_csv(os.path.join(root, job, "WEB_NUMBERS_NAMED.csv")):
            if r.get("in_census") == "no":
                add(r["instrument_id"], "web_page_read", "", "", "weak", r.get("example_url", ""))
    for job in (LEWIS, CLARK):
        for iid, (score, url) in web_best(root, job).items():
            if iid not in universe and score >= 60:
                add(iid, "web_search_confirmed_page", "", "", "strong", url)
    crow = []
    for iid, c in sorted(cand.items(), key=lambda kv: (ident.parse_eo_id(kv[0]) or (0, ""), kv[0])):
        crow.append({**c, "named_by": "|".join(sorted(c["named_by"])), "dates_seen": "|".join(sorted(c["dates_seen"])),
                     "titles_seen": " ; ".join(sorted(c["titles_seen"]))})
    with open(os.path.join(out_dir, "CANDIDATES_NOT_IN_REGISTER.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CANDIDATE_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(crow)

    held = collections.Counter(r["best_held"] for r in rows)
    summary = {
        "job": JOB, "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "orders": len(rows), "by_best_held": dict(held), "by_era": dict(collections.Counter(r["era"] for r in rows)),
        "with_date": sum(1 for r in rows if r["date"]), "with_title": sum(1 for r in rows if r["title"]),
        "with_any_text_file": sum(1 for r in rows if r["text_files"]),
        "proquest": {"link_supplied": sum(1 for r in rows if r["proquest_link_supplied"] == "yes"),
                     "pdf_in_repository": sum(1 for r in rows if r["proquest_pdf_file"])},
        "lewis": {"routed": sum(1 for r in rows if r["lewis_route"]), "web_confirmed_page": sum(1 for r in rows if (r["lewis_web_best_score"] or 0) and int(r["lewis_web_best_score"]) >= 60)},
        "clark": {"classed": sum(1 for r in rows if r["clark_class"]), "web_confirmed_page": sum(1 for r in rows if (r["clark_web_best_score"] or 0) and int(r["clark_web_best_score"]) >= 60)},
        "candidates_not_in_register": {"total": len(crow), "by_strength": dict(collections.Counter(c["strength"] for c in crow))},
        "problems": problems,
        "what_this_is_not": "A survey of what is held. No identity, custody grade, readiness count or legal status changes here.",
    }
    with open(os.path.join(out_dir, "SUMMARY.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
    with open(os.path.join(out_dir, "REPORT.md"), "w", encoding="utf-8") as fh:
        s = summary
        lines = ["# Domesday register", "", f"Generated {s['generated_utc']}. {s['orders']} orders; one row each in `REGISTER.csv`.", "",
                 "| Best document held | Orders |", "|---|---:|"]
        lines += [f"| {k} | {v} |" for k, v in sorted(held.items(), key=lambda kv: -kv[1])]
        lines += ["", f"Dated: {s['with_date']}. Titled: {s['with_title']}. With a text file on disk: {s['with_any_text_file']}. "
                      f"ProQuest links supplied: {s['proquest']['link_supplied']}; PDFs in the repository: {s['proquest']['pdf_in_repository']}. "
                      f"Lewis routed {s['lewis']['routed']} orders and has a web page naming the order for {s['lewis']['web_confirmed_page']}; "
                      f"Clark classed {s['clark']['classed']} and has one for {s['clark']['web_confirmed_page']}.", "",
                  f"**Candidates not in the register: {s['candidates_not_in_register']['total']}** (`CANDIDATES_NOT_IN_REGISTER.csv`), by strength "
                  + ", ".join(f"{k or 'unrated'} {v}" for k, v in sorted(s["candidates_not_in_register"]["by_strength"].items())) + ". "
                  "These are leads for census intake, never entries.", ""]
        fh.write("\n".join(lines) + "\n")
    return summary


def main():
    root = os.environ.get("REPO_ROOT") or os.path.abspath(os.path.join(HERE, "..", ".."))
    out_dir = os.environ.get("OUTPUT_DIR") or os.path.join(HERE, "output")
    s = run(root, out_dir)
    print(json.dumps({k: s[k] for k in ("orders", "by_best_held", "candidates_not_in_register", "problems")}, indent=2))


if __name__ == "__main__":
    main()
