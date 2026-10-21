"""Clark: find the orders the project cannot yet identify.

Lewis (jobs/lewis-originals) starts from an order whose wording is known and looks for its official
original. Clark starts one step earlier, from orders the project knows only as a number, or does not
know at all, and tries to establish what they are: a date, a title, a citing document, a place to
look. Four kinds of unknown are reported, each in its own file:

  NUMBER_GAPS.csv         integers between 1 and the highest numbered order that have no row in the
                          14,972-order census: with the dates of the nearest known numbers on either
                          side (the window the missing order must fall in), whether any index knows
                          the number anyway (the American Presidency Project index, the OFR catalog,
                          the ProQuest list) and whether any saved text or OFR note cites it.
  CITED_BUT_UNKNOWN.csv   executive-order numbers named in saved order texts and OFR disposition
                          notes that are not in the census, with the citing document, the exact
                          sentence, any date stated beside the number, and a plausibility check
                          (a number larger than any order signed by the citing document's date is
                          almost always an OCR footnote digit glued to a real number: 86402 = 8640).
  IDENTITY_UNKNOWN.csv    census orders whose original_text step is open with no transcription lead
                          and no date or title in any index: a number and nothing else. For each,
                          what little is known (census year group, a ProQuest link if the owner's
                          list has one, a WPA-list line) and where to look next.
  DATED_UNNUMBERED.csv    "Executive order of <date>" references in texts and notes whose date
                          matches no numbered order and no unnumbered census cluster: leads for the
                          unnumbered series that the census-completeness job measures.

HANDOFF_TO_LEWIS.jsonl lists every unknown for which Clark found identity evidence (a date or title
from an index, a dated citation, a ProQuest link), so Lewis can route it to an original on the next
run. Nothing here enters the census, changes a readiness count, or authenticates an identity: every
row is a lead for a person to check.
"""
from __future__ import annotations

import bisect
import collections
import csv
import datetime as dt
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "_lib"))
import eo_identity as ident  # noqa: E402

JOB = "clark-discovery"
UNPARSED_NOTES = "jobs/later-events/output/UNPARSED_NOTE_SEGMENTS.csv"
CENSUS_CLUSTERS = "jobs/census-completeness/output/CLUSTERS.csv"
LEWIS_FRAGMENTS = "jobs/lewis-originals/output/FRAGMENTS.jsonl"
PLAUSIBILITY_RANK = {"plausible": 0, "citing_date_unknown": 1, "rare_suffix_letter": 2,
                     "exceeds_numbers_issued_by_citing_date": 3, "likely_ocr_letter_for_digit": 4,
                     "likely_ocr_footnote_digit": 5}
# Letters OCR produces for digits in scanned Federal Register headings ('Executive Order 1T 060').
OCR_LETTER_DIGITS = {"T": "1", "I": "1", "L": "1", "J": "1", "S": "5", "O": "0", "Q": "0", "D": "0", "B": "8",
                     "Z": "2", "G": "6"}
GLUE_MIN_DIGITS = 5          # 86402: five digits, and 8640 is a real order -> footnote digit glued on
NUMBER_SLACK = 20            # a cited number may run a little ahead of the dated timeline


# --- mentions harvest ------------------------------------------------------------------------------

def canon_set(ids):
    """Census ids in canonical form ('EO:7933a' -> 'EO:7933A'), for membership tests."""
    out = set()
    for i in ids:
        p = ident.parse_eo_id(i)
        if p:
            out.add(ident.canon_id(*p))
    return out


def harvest_mentions(root, frags, dates, universe):
    """Every executive-order number named in a saved text or an OFR note. Returns a list of mention rows."""
    timeline = ident.numbered_timeline(dates)
    known = canon_set(universe)
    # Suffix letters the census has actually seen; a mention with any other letter is usually an OCR misread
    # ('Executive Order 1T 060' for 11060, '1284S' for 12845), so it is ranked below the plausible rows.
    suffix_counts = collections.Counter(ident.parse_eo_id(i)[1] for i in universe if ident.parse_eo_id(i))
    mentions = []

    def ocr_digit_reading(m):
        """'1T 060' -> EO:11060, '1284S' -> EO:12845: the letter was a digit; returns the census id or ''."""
        digit = OCR_LETTER_DIGITS.get(m["suffix"])
        if not digit:
            return ""
        tail = re.match(r"\s?(\d+)", m.get("after", ""))
        cand = ident.canon_id(int(str(m["number"]) + digit + (tail.group(1) if tail else "")))
        return cand if cand in known else ""

    def add(citing_id, source_kind, source_ref, m):
        iid = ident.canon_id(m["number"], m["suffix"])
        citing_canon = ident.canon_id(*ident.parse_eo_id(citing_id)) if citing_id and ident.parse_eo_id(citing_id) else citing_id
        if iid in known or iid == citing_canon:
            return
        citing_date = ident.parse_date((dates.get(citing_id) or {}).get("date", "")) if citing_id else None
        cap = ident.max_number_by(timeline, citing_date)
        glued = ""
        if len(str(m["number"])) >= GLUE_MIN_DIGITS and not m["suffix"]:
            shorter = ident.canon_id(m["number"] // 10)
            if shorter in known:
                glued = shorter
        after = m.get("after", "")
        misread = ocr_digit_reading(m) if m["suffix"] else ""
        if glued:
            plaus = "likely_ocr_footnote_digit"
        elif misread:
            plaus, glued = "likely_ocr_letter_for_digit", misread
        elif m["suffix"] and suffix_counts.get(m["suffix"], 0) <= 3:
            plaus = "rare_suffix_letter"
        elif cap is not None and m["number"] > cap + NUMBER_SLACK:
            plaus = "exceeds_numbers_issued_by_citing_date"
        elif citing_date is None:
            plaus = "citing_date_unknown"
        else:
            plaus = "plausible"
        mentions.append({"cited_id": iid, "number": m["number"], "suffix": m["suffix"], "date_stated": m["date"],
                         "citing_id": citing_id or "", "citing_date": citing_date.isoformat() if citing_date else "",
                         "source_kind": source_kind, "source_ref": source_ref, "plausibility": plaus,
                         "glued_candidate": glued, "max_number_by_citing_date": cap if cap is not None else "",
                     "after": after,
                         "quote": m["quote"][:500]})

    classes = ("official", "transcription", "archival_replica")
    scanned = 0
    for citing_id, f, text in ident.iter_texts(frags, classes):
        scanned += 1
        for m in ident.find_mentions(text):
            add(citing_id, "order_text:" + f["produced_by"], f["url"] or f["text_path"] or "", m)
    notes = 0
    for r in ident.read_csv(os.path.join(root, ident.OFR_CATALOG)):
        note = r.get("disposition_notes") or ""
        if not note:
            continue
        notes += 1
        for m in ident.find_mentions(note):
            add(r.get("id"), "ofr_disposition_note", r.get("html_url") or r.get("api_page_source_id") or "", m)
    for r in ident.read_csv(os.path.join(root, UNPARSED_NOTES)):
        for m in ident.find_mentions(r.get("segment") or ""):
            add(r.get("instrument_id"), "ofr_unparsed_note_segment", r.get("reason") or "", m)
    return mentions, {"texts_scanned": scanned, "ofr_notes_scanned": notes}


def harvest_unnumbered(root, frags, dates, universe):
    """'Executive order of <date>' references whose date matches no known numbered or unnumbered order."""
    dated = collections.defaultdict(set)
    for iid, d in dates.items():
        if len(d.get("date", "")) >= 10:
            dated[d["date"]].add(iid)
    clusters = collections.defaultdict(set)
    for r in ident.read_csv(os.path.join(root, CENSUS_CLUSTERS)):
        if len(r.get("date", "")) >= 10:
            clusters[r["date"]].add(r.get("cluster_id", ""))
    out = {}
    sources = [(iid, "order_text:" + f["produced_by"], f["url"] or "", text)
               for iid, f, text in ident.iter_texts(frags, ("official", "transcription", "archival_replica"))]
    sources += [(r.get("id"), "ofr_disposition_note", r.get("html_url") or "", r.get("disposition_notes") or "")
                for r in ident.read_csv(os.path.join(root, ident.OFR_CATALOG))]
    for citing_id, kind, ref, text in sources:
        for m in ident.UNNUMBERED_RE.finditer(text):
            d = ident.parse_prose_date(m.group(1))
            if d is None:
                continue
            iso = d.isoformat()
            key = (iso, citing_id)
            if key in out:
                continue
            out[key] = {"date": iso, "numbered_orders_that_day": "|".join(sorted(dated.get(iso, ()))),
                        "census_clusters_that_day": "|".join(sorted(clusters.get(iso, ()))),
                        "matches_known_order": "yes" if dated.get(iso) or clusters.get(iso) else "no",
                        "citing_id": citing_id or "", "source_kind": kind, "source_ref": ref,
                        "quote": ident.sentence_around(text, m.start(), m.end())[:500]}
    rows = [r for r in out.values() if r["matches_known_order"] == "no"]
    rows.sort(key=lambda r: (r["date"], r["citing_id"]))
    return rows


# --- the four unknowns ----------------------------------------------------------------------------

def number_gaps(universe, dates, pq_rows, app_index, catalog, mentions):
    nums = sorted(n for n in (ident.parse_eo_id(i) for i in universe) if n and not n[1])
    numbers = [n for n, _ in nums]
    known = set(numbers)
    top = max(numbers) if numbers else 0
    dated = {}
    for n in numbers:
        d = (dates.get(ident.canon_id(n)) or {}).get("date", "")
        if d:
            dated[n] = d
    cited = collections.defaultdict(list)
    for m in mentions:
        if not m["suffix"]:
            cited[m["number"]].append(m)
    dated_numbers = sorted(dated)
    rows = []
    for n in range(1, top + 1):
        if n in known:
            continue
        iid = ident.canon_id(n)
        at = bisect.bisect_left(dated_numbers, n)
        prev = dated_numbers[at - 1] if at > 0 else None
        nxt = dated_numbers[at] if at < len(dated_numbers) else None
        ms = cited.get(n, [])
        plaus = [m for m in ms if m["plausibility"] in ("plausible", "citing_date_unknown")]
        app = app_index.get(iid) or {}
        cat = catalog.get(iid) or {}
        pq = pq_rows.get(iid) or {}
        evidence = []
        if app:
            evidence.append(f"app_index:{app.get('date', '')}:{(app.get('title') or '')[:80]}")
        if cat:
            evidence.append(f"ofr_catalog:{cat.get('signing_date', '')}:{(cat.get('title') or '')[:80]}")
        if pq:
            evidence.append(f"proquest_list:{pq.get('y', '')}")
        stated = sorted({m["date_stated"] for m in plaus if m["date_stated"]})
        if stated:
            evidence.append("cited_with_date:" + "|".join(stated))
        rows.append({"instrument_id": iid, "number": n,
                     "window_from": f"{iid and ident.canon_id(prev)} {dated.get(prev, '')}".strip() if prev else "",
                     "window_to": f"{ident.canon_id(nxt)} {dated.get(nxt, '')}".strip() if nxt else "",
                     "known_to_index": "|".join(e.split(":")[0] for e in evidence) or "none",
                     "identity_evidence": " ; ".join(evidence),
                     "cited_plausibly_by": "|".join(sorted({m["citing_id"] for m in plaus if m["citing_id"]})),
                     "citations_total": len(ms),
                     "strength": "strong" if (app or cat or stated) else ("cited" if plaus else "number_only"),
                     "where_to_look": where_to_look(n, "", dated.get(prev) or dated.get(nxt) or "", bool(pq))})
    return rows


def where_to_look(number, suffix, date_hint, proquest_link):
    year = (date_hint or "")[:4]
    if proquest_link:
        return "ProQuest supplied link (owner's list) -> upload PDF; Lewis routes it"
    if year and year < "1937":
        return f'ProQuest Congressional phrase search "Executive Order No. {number}{suffix}" (1789-1936 set); NARA RG 11 (catalog NAID 299999)'
    if year:
        return f"govinfo Federal Register {year} by date; OFR executive-order tables"
    return 'ProQuest Congressional phrase search; Lord\'s list and WPA numbered list for pre-1900'


def identity_unknown(universe, readiness, frags, dates, pq_rows, pq_local, wpa):
    rows = []
    for iid, r in readiness.items():
        if r.get("step_original_text") != "open" or "ONLY_COMPILED_TRANSCRIPTION_FOUND" in (r.get("blockers") or ""):
            continue
        if any(f["class"] == "transcription" for f in frags.get(iid, [])):
            continue
        d = dates.get(iid) or {}
        has_identity = bool(d.get("title")) or (d.get("date_source") not in ("", "census_year", "proquest_list_year"))
        if has_identity:
            continue
        p = ident.parse_eo_id(iid)
        num, suffix = p if p else ("", "")
        u = universe.get(iid) or {}
        w = wpa.get(iid) or {}
        pq = pq_rows.get(iid) or {}
        known = []
        if pq:
            known.append(f"proquest_link_year_{pq.get('y', '')}")
        if iid in pq_local:
            known.append("proquest_pdf_in_repository")
        if w:
            known.append("wpa_pre1900_line")
        if u.get("date_effective"):
            known.append(f"census_year_{u['date_effective']}")
        rows.append({"instrument_id": iid, "year_group": u.get("year_group", ""), "census_year": u.get("date_effective", ""),
                     "bibliographic_class": u.get("bibliographic_class", ""), "what_is_known": "|".join(known) or "number_only",
                     "proquest_link_supplied": "yes" if pq else "no", "proquest_pdf_in_repository": "yes" if iid in pq_local else "no",
                     "wpa_line": (w.get("text") or "")[:160], "blockers": r.get("blockers", ""),
                     "where_to_look": where_to_look(num, suffix, u.get("date_effective", ""), bool(pq))})
    rows.sort(key=lambda r: (ident.parse_eo_id(r["instrument_id"]) or (0, ""), r["instrument_id"]))
    return rows


def handoff_rows(gaps, cited_rows, unknown_rows, pq_rows, dates):
    """Unknowns with identity evidence, in the shape Lewis reads (instrument_id + evidence + reason)."""
    out = {}
    for g in gaps:
        if g["strength"] in ("strong", "cited"):
            out[g["instrument_id"]] = {"instrument_id": g["instrument_id"], "in_census": False, "clark_class": "number_gap",
                                       "identity_evidence": g["identity_evidence"], "strength": g["strength"],
                                       "cited_by": g["cited_plausibly_by"], "window": f"{g['window_from']} -> {g['window_to']}"}
    for c in cited_rows:
        if c["plausibility"] in ("plausible",) and c["cited_id"] not in out and c["suffix"]:
            out[c["cited_id"]] = {"instrument_id": c["cited_id"], "in_census": False, "clark_class": "cited_but_unknown",
                                  "identity_evidence": f"cited by {c['citing_id']} ({c['source_kind']})" + (f" with date {c['date_stated']}" if c["date_stated"] else ""),
                                  "strength": "cited", "cited_by": c["citing_id"], "window": ""}
    for u in unknown_rows:
        if u["proquest_link_supplied"] == "yes" or u["proquest_pdf_in_repository"] == "yes" or u["wpa_line"]:
            d = dates.get(u["instrument_id"]) or {}
            out[u["instrument_id"]] = {"instrument_id": u["instrument_id"], "in_census": True, "clark_class": "identity_unknown",
                                       "identity_evidence": u["what_is_known"], "strength": "weak",
                                       "cited_by": "", "window": d.get("date", "")}
    rows = list(out.values())
    for r in rows:
        r["produced_by"] = JOB
        r["note"] = "Lead only: no census entry, readiness step or identity authentication follows from this line."
    rows.sort(key=lambda r: (ident.parse_eo_id(r["instrument_id"]) or (0, ""), r["instrument_id"]))
    return rows


# --- main ----------------------------------------------------------------------------------------

def write_csv(path, rows, fields):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def run(root, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    universe = ident.load_universe(root)
    readiness = ident.load_readiness(root)
    frags = ident.load_fragments(root)
    dates = ident.load_dates(root, frags)
    pq_rows = {ident.canon_id(*ident.parse_eo_id(str(r["id"]))): r for r in ident.load_proquest_rows(root)}
    app_index = {r["instrument_id"]: r for r in ident.read_csv(os.path.join(root, ident.APP_INDEX)) if r.get("instrument_id")}
    catalog = {r["id"]: r for r in ident.read_csv(os.path.join(root, ident.OFR_CATALOG))}
    wpa = {}
    for r in ident.read_csv(os.path.join(root, ident.WPA_PRE1900)):
        iid = r.get("id") or (ident.canon_id(r["number"], r.get("suffix", "")) if r.get("number") else None)
        if iid:
            wpa[iid] = r
    pq_local = set()
    for r in ident.read_jsonl(os.path.join(root, LEWIS_FRAGMENTS)):
        if r.get("instrument_id"):
            pq_local.add(r["instrument_id"])
    problems = []
    if not universe:
        problems.append("universe file missing: " + ident.UNIVERSE)
    if not readiness:
        problems.append("readiness output missing: " + ident.READINESS)

    mentions, scan = harvest_mentions(root, frags, dates, universe)
    gaps = number_gaps(universe, dates, pq_rows, app_index, catalog, mentions)
    unknown = identity_unknown(universe, readiness, frags, dates, pq_rows, pq_local, wpa)
    unnumbered = harvest_unnumbered(root, frags, dates, universe)

    # one row per (cited id, citing document): keep the first quote, count the rest
    cited = {}
    for m in mentions:
        key = (m["cited_id"], m["citing_id"], m["source_kind"])
        if key in cited:
            cited[key]["mentions_in_source"] += 1
            if m["date_stated"] and not cited[key]["date_stated"]:
                cited[key]["date_stated"] = m["date_stated"]
        else:
            cited[key] = {**m, "mentions_in_source": 1}
    cited_rows = sorted(cited.values(), key=lambda r: (PLAUSIBILITY_RANK[r["plausibility"]],
                                                       r["number"], r["suffix"], r["citing_id"]))
    handoff = handoff_rows(gaps, cited_rows, unknown, pq_rows, dates)

    write_csv(os.path.join(out_dir, "NUMBER_GAPS.csv"), gaps,
              ["instrument_id", "number", "window_from", "window_to", "strength", "known_to_index", "identity_evidence",
               "cited_plausibly_by", "citations_total", "where_to_look"])
    write_csv(os.path.join(out_dir, "CITED_BUT_UNKNOWN.csv"), cited_rows,
              ["cited_id", "number", "suffix", "plausibility", "glued_candidate", "date_stated", "citing_id", "citing_date",
               "max_number_by_citing_date", "source_kind", "source_ref", "mentions_in_source", "quote"])
    write_csv(os.path.join(out_dir, "IDENTITY_UNKNOWN.csv"), unknown,
              ["instrument_id", "year_group", "census_year", "bibliographic_class", "what_is_known", "proquest_link_supplied",
               "proquest_pdf_in_repository", "wpa_line", "blockers", "where_to_look"])
    write_csv(os.path.join(out_dir, "DATED_UNNUMBERED.csv"), unnumbered,
              ["date", "citing_id", "source_kind", "source_ref", "numbered_orders_that_day", "census_clusters_that_day", "quote"])
    with open(os.path.join(out_dir, "HANDOFF_TO_LEWIS.jsonl"), "w", encoding="utf-8") as fh:
        for r in handoff:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")

    summary = {
        "job": JOB, "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "number_gaps": {"total": len(gaps), "by_strength": dict(collections.Counter(g["strength"] for g in gaps)),
                        "highest_numbered_order": max((ident.parse_eo_id(i)[0] for i in universe if ident.parse_eo_id(i)), default=0)},
        "cited_but_unknown": {"distinct_ids": len({r["cited_id"] for r in cited_rows}), "rows": len(cited_rows),
                              "by_plausibility": dict(collections.Counter(r["plausibility"] for r in cited_rows)),
                              "mentions_raw": len(mentions), **scan},
        "identity_unknown": {"orders": len(unknown), "by_year_group": dict(collections.Counter(u["year_group"] for u in unknown)),
                             "with_proquest_link": sum(1 for u in unknown if u["proquest_link_supplied"] == "yes"),
                             "with_proquest_pdf": sum(1 for u in unknown if u["proquest_pdf_in_repository"] == "yes"),
                             "number_only": sum(1 for u in unknown if u["proquest_link_supplied"] == "no"
                                                and u["proquest_pdf_in_repository"] == "no" and not u["wpa_line"])},
        "dated_unnumbered": {"rows": len(unnumbered), "distinct_dates": len({r["date"] for r in unnumbered})},
        "handoff_to_lewis": {"rows": len(handoff), "by_class": dict(collections.Counter(r["clark_class"] for r in handoff))},
        "inputs": {"universe": len(universe), "readiness_rows": len(readiness), "dated_orders": len(dates),
                   "proquest_list_rows": len(pq_rows), "app_index_rows": len(app_index), "ofr_catalog_rows": len(catalog),
                   "lewis_proquest_fragments": len(pq_local), "wpa_rows": len(wpa)},
        "problems": problems,
        "what_this_is_not": "Leads only. Nothing here enters the census, changes a readiness count or authenticates an identity.",
    }
    with open(os.path.join(out_dir, "SUMMARY.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
    write_report(os.path.join(out_dir, "REPORT.md"), summary, gaps, cited_rows, unknown)
    return summary


def write_report(path, s, gaps, cited_rows, unknown):
    g, c, u = s["number_gaps"], s["cited_but_unknown"], s["identity_unknown"]
    lines = ["# Clark: orders the project cannot yet identify", "",
             f"Generated {s['generated_utc']}. Leads only; no census, count or identity changes.", "",
             "| Unknown | Count | File |", "|---|---:|---|",
             f"| Numbers with no census row (1 to {g['highest_numbered_order']}) | {g['total']} | NUMBER_GAPS.csv |",
             f"| Numbers cited in texts or OFR notes but absent from the census | {c['distinct_ids']} ids ({c['by_plausibility'].get('plausible', 0)} plausible) | CITED_BUT_UNKNOWN.csv |",
             f"| Census orders known by number only | {u['orders']} | IDENTITY_UNKNOWN.csv |",
             f"| Dated unnumbered references matching nothing known | {s['dated_unnumbered']['rows']} | DATED_UNNUMBERED.csv |",
             f"| Handed to Lewis with identity evidence | {s['handoff_to_lewis']['rows']} | HANDOFF_TO_LEWIS.jsonl |", "",
             "## Number gaps", "", "| Number | Window | Strength | Evidence |", "|---|---|---|---|"]
    for r in gaps:
        lines.append(f"| {r['instrument_id']} | {r['window_from']} -> {r['window_to']} | {r['strength']} | {r['identity_evidence'][:120]} |")
    lines += ["", "## Cited but unknown (plausible rows first)", "",
              f"{c['rows']} (cited id, citing document) pairs from {c['texts_scanned']} saved texts and {c['ofr_notes_scanned']} OFR notes. "
              f"By plausibility: {', '.join(f'{k} {v}' for k, v in sorted(c['by_plausibility'].items()))}. "
              "A number larger than any order signed by the citing document's date is read as an OCR artifact (a footnote digit "
              "glued to a real number) and listed last; it still names a real citing sentence to check.", "",
              "| Cited | Stated date | Cited by | Plausibility | Quote |", "|---|---|---|---|---|"]
    for r in [x for x in cited_rows if x["plausibility"] == "plausible"][:40]:
        lines.append(f"| {r['cited_id']} | {r['date_stated']} | {r['citing_id']} | {r['plausibility']} | {r['quote'][:140].replace('|', '/')} |")
    lines += ["", "## Identity unknown", "",
              f"{u['orders']} census orders have an open original_text step, no transcription lead and no date or title in any index. "
              f"{u['with_proquest_link']} are on the owner's ProQuest link list (year known from the accession) and {u['with_proquest_pdf']} "
              f"already have a ProQuest PDF in the repository; {u['number_only']} are a number and nothing else. By census era: "
              + ", ".join(f"{k} {v}" for k, v in sorted(u["by_year_group"].items())) + ".", ""]
    if s["problems"]:
        lines += ["## Problems", ""] + [f"- {x}" for x in s["problems"]]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    root = os.environ.get("REPO_ROOT") or os.path.abspath(os.path.join(HERE, "..", ".."))
    out_dir = os.environ.get("OUTPUT_DIR") or os.path.join(HERE, "output")
    s = run(root, out_dir)
    print(json.dumps({k: s[k] for k in ("number_gaps", "cited_but_unknown", "identity_unknown", "dated_unnumbered",
                                        "handoff_to_lewis", "problems")}, indent=2))


if __name__ == "__main__":
    main()
