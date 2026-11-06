"""Photius Lane 1: map the twelve GPO bound slip-order volumes to order numbers and register each printing.

Reads the page cache written by ocr_pages.py (one JSONL row per page: the PDF's own text layer, a local Tesseract
read of the 300-dpi render, and the render's SHA-256), finds every closing tag "[No. NNNN.]" and "EXECUTIVE ORDER"
heading, keeps the longest increasing chain of tags (OCR misreads fall out), assigns page ranges, runs the identity
test (the dateline against the identity layer and the volume's years, and the signature block), and writes:

  output/ORDERS.csv            one row per order located, with pages, hashes, tests and verdict
  output/texts/EO_<n>.txt      the printing's text (layer where present, else OCR) with a provenance header
  output/FRAGMENTS.jsonl       producer schema the tracker reads; needs_page_check false only on verdict pass
  output/PAGE_CHECK_QUEUE.csv  every check/fail verdict plus a seeded 5% sample of passes, for the Opus page check
  output/pages/<htid>.jsonl.gz the page texts and render hashes (public; the PDFs stay private)
  output/SUMMARY.json, REPORT.md

A located printing is a machine location of an official GPO printing (R37), not an authentication of the signed
original. Nothing here changes a status, the census, the codebook or the certified count.

    python -I jobs/photius-gpo-volumes/segment.py [--cache research/owner-inbox/hathi-gpo/pages] [--out jobs/photius-gpo-volumes/output]
"""
from __future__ import annotations

import argparse
import bisect
import collections
import csv
import gzip
import hashlib
import json
import os
import random
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "jobs" / "_lib"))
import eo_identity as ei  # noqa: E402

JOB = "photius-gpo-volumes"
TAG = re.compile(r"\[\s*No\.?\s*(\d{3,4})\s*(?:-\s*|\s)?([A-Za-z])?\s*\.?\s*[\]\}]")
HEAD = re.compile(r"\bEXECUTIVE\s+ORDER\b", re.I)
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
MON = {m: i + 1 for i, m in enumerate(MONTHS.split("|"))}
DATELINE = re.compile(rf"(THE\s+WHITE\s+HOUSE|EXECUTIVE\s+MANSION)[\s,.]*\n?\s*({MONTHS})\s+(\d{{1,2}})\s*,?\s*(1[89]\d\d)", re.I)
ANYDATE = re.compile(rf"\b({MONTHS})\s+(\d{{1,2}})\s*,?\s*(1[89]\d\d)\b", re.I)
PRESIDENTS = ["COOLIDGE", "HOOVER", "ROOSEVELT", "HARDING", "WILSON", "TAFT"]
SIGN = re.compile(r"(THE\s+WHITE\s+HOUSE|W[hH]?[iuy]i?te\s+H[o0]use|" + "|".join(PRESIDENTS) + r")", re.I)
# OCR of the small-caps dateline ("Tue Waite House, Mareh 30, 1926"): any capitalised word, day, 18xx/19xx; month by letters
FUZZYDATE = re.compile(r"\b([A-Z][a-z]{2,9})\.?\s+(\d{1,2})\s*[,.]?\s*(1[89]\d\d)\b")
HOUSE = re.compile(r"(W[hH]?[iuy]i?te\s+H[o0]use|WHITE\s+HOUSE|Executive\s+Mansion)", re.I)
MONTH_FIX = {"jan": 1, "feb": 2, "fcb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jnn": 6, "jul": 7, "ju1": 7, "aug": 8, "ang": 8,
             "sep": 9, "oct": 10, "oet": 10, "nov": 11, "dec": 12, "deo": 12}


def month_of(word):
    return MONTH_FIX.get(word[:3].lower())


def read_dateline(text):
    """The signing date printed before the closing tag: the last date after the last 'White House' in the final
    900 characters, else the last date in the final 500 characters. Returns ISO or ''."""
    tail = text[-900:]
    hm = None
    for hm in HOUSE.finditer(tail):
        pass
    region = tail[hm.start():] if hm else text[-500:]
    best = ""
    for m in FUZZYDATE.finditer(region):
        mo = month_of(m.group(1))
        if mo and 1 <= int(m.group(2)) <= 31:
            best = f"{int(m.group(3)):04d}-{mo:02d}-{int(m.group(2)):02d}"
    return best
SUFFIX_ORDER = {"": 0, "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6}
CHECK_SAMPLE = 0.05
SEED = 20261106


def page_text(row):
    layer, ocr = row.get("layer") or "", row.get("ocr") or ""
    if len(layer.strip()) >= 0.6 * len(ocr.strip()) and len(layer.strip()) > 80:
        return layer, "layer"
    return ocr, "ocr"


def load_volume(cache, htid):
    rows = []
    for ch in sorted((cache / htid).glob("chunk_*.jsonl")):
        with open(ch, encoding="utf-8") as f:
            rows += [json.loads(l) for l in f]
    rows.sort(key=lambda r: r["page_index"])
    return rows


def find_tags(rows, lo, hi):
    """Every closing tag with its position, from the OCR and the layer, in reading order."""
    found = []
    for r in rows:
        seen = set()
        for src in ("ocr", "layer"):
            text = r.get(src) or ""
            for m in TAG.finditer(text):
                n = int(m.group(1))
                suf = (m.group(2) or "").upper()
                if not (lo - 5 <= n <= hi + 5) or suf not in SUFFIX_ORDER:
                    continue
                key = (n, suf)
                if key in seen:
                    continue
                seen.add(key)
                frac = m.end() / max(1, len(text))
                found.append({"page": r["page_index"], "n": n, "suf": suf, "frac": frac, "src": src})
    found.sort(key=lambda t: (t["page"], t["frac"]))
    return found


def lis(tags):
    """Longest strictly increasing chain of (number, suffix) in reading order; OCR misreads drop out."""
    keys = [(t["n"], SUFFIX_ORDER[t["suf"]]) for t in tags]
    tails, prev, idx = [], [-1] * len(tags), []
    for i, k in enumerate(keys):
        pos = bisect.bisect_left(tails, k)
        if pos == len(tails):
            tails.append(k)
            idx.append(i)
        else:
            tails[pos] = k
            idx[pos] = i
        prev[i] = idx[pos - 1] if pos > 0 else -1
    out, i = [], idx[-1] if idx else -1
    while i >= 0:
        out.append(tags[i])
        i = prev[i]
    return out[::-1]


def text_between(rows, start_page, start_frac, end_page, end_frac):
    parts, sources = [], set()
    for p in range(start_page, end_page + 1):
        t, src = page_text(rows[p])
        sources.add(src)
        a = int(len(t) * start_frac) if p == start_page else 0
        b = int(len(t) * end_frac) if p == end_page else len(t)
        parts.append(t[a:b])
    return "\n\f\n".join(parts), sources


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=str(Path(r"C:\Users\danie\Projects\Executive-Orders\research\owner-inbox\hathi-gpo\pages")))
    ap.add_argument("--out", default=str(REPO / "jobs" / JOB / "output"))
    a = ap.parse_args(argv)
    cache, out = Path(a.cache), Path(a.out)
    (out / "texts").mkdir(parents=True, exist_ok=True)
    (out / "pages").mkdir(exist_ok=True)
    vols = json.load(open(REPO / "jobs" / JOB / "data" / "VOLUMES.json"))["volumes"]
    ident = {r["instrument_id"]: r for r in csv.DictReader(open(REPO / "research/photius/IDENTITY_DATES.csv", encoding="utf-8"))}

    orders, page_rows_public, summary = [], {}, {"volumes": {}}
    for v in vols:
        htid, lo, hi = v["htid"], v["range_min"], v["range_max"]
        rows = load_volume(cache, htid)
        if not rows:
            summary["volumes"][htid] = {"error": "no page cache"}
            continue
        years = set()
        tags = find_tags(rows, lo, hi)
        kept = lis(tags)
        kept_keys = {(t["n"], t["suf"]) for t in kept}
        # year range of the volume from its datelines
        for r in rows:
            t, _ = page_text(r)
            for m in DATELINE.finditer(t):
                years.add(int(m.group(4)))
        vol_years = (min(years), max(years)) if years else (None, None)
        prev = None
        vol_orders = []
        for k_i, t in enumerate(kept):
            if prev is None:
                # first order of the volume: start at the first page with a heading, or the tag's page
                start_page, start_frac = t["page"], 0.0
                for p in range(0, t["page"] + 1):
                    pt, _ = page_text(rows[p])
                    if HEAD.search(pt[:600]):
                        start_page = p
                        break
            else:
                pt, _ = page_text(rows[prev["page"]])
                rest = pt[int(len(pt) * prev["frac"]):]
                if len(rest.strip()) >= 120 or HEAD.search(rest):
                    start_page, start_frac = prev["page"], prev["frac"]
                else:
                    start_page, start_frac = min(prev["page"] + 1, t["page"]), 0.0
            text, sources = text_between(rows, start_page, start_frac, t["page"], t["frac"])
            # numbers skipped between the previous kept tag and this one
            gap = []
            if prev is not None and t["suf"] == "" and prev["n"] + 1 < t["n"]:
                gap = list(range(prev["n"] + 1, t["n"]))
            headings = len(HEAD.findall(text))
            iid = ei.canon_id(t["n"], t["suf"])
            idd = ident.get(iid, {})
            exp_date = idd.get("date", "")
            seen_date = read_dateline(text)
            if exp_date and len(exp_date) >= 10 and exp_date in {f"{int(x.group(3)):04d}-{month_of(x.group(1)) or 0:02d}-{int(x.group(2)):02d}" for x in FUZZYDATE.finditer(text[-900:])}:
                seen_date = exp_date  # the identity date is printed in the dateline region
            if seen_date and exp_date and len(exp_date) >= 10:
                date_test = "match" if seen_date == exp_date else ("year_match" if seen_date[:4] == exp_date[:4] else "conflict")
            elif seen_date and exp_date:
                date_test = "year_match" if seen_date[:4] == exp_date[:4] else "conflict"
            elif seen_date:
                date_test = "no_identity_date"
            else:
                date_test = "dateline_not_found"
            year_ok = (not seen_date) or (vol_years[0] is None) or (vol_years[0] - 1 <= int(seen_date[:4]) <= vol_years[1] + 1)
            sig = bool(SIGN.search(text[-1200:]))
            reasons = []
            if date_test in ("conflict",):
                reasons.append("date_conflict")
            if not year_ok:
                reasons.append("year_outside_volume")
            if date_test == "dateline_not_found":
                reasons.append("dateline_not_found")
            if not sig:
                reasons.append("signature_not_found")
            if gap and headings != 1:
                reasons.append(f"tag_gap_before:{gap[0]}-{gap[-1]}:headings={headings}")
            if len(text.strip()) < 200:
                reasons.append("text_short")
            if iid not in ident:
                reasons.append("not_in_identity_layer")
            if "not_in_identity_layer" in reasons or ("date_conflict" in reasons and "year_outside_volume" in reasons):
                verdict = "fail"
            elif reasons:
                verdict = "check"
            else:
                verdict = "pass"
            pages = list(range(start_page, t["page"] + 1))
            hashes = [rows[p]["render_png_sha256"] for p in pages]
            text_path = f"texts/EO_{t['n']}{t['suf']}.txt"
            header = (f"# {iid} | GPO bound slip-order volume HathiTrust {htid} | PDF pages {pages[0] + 1}-{pages[-1] + 1} (1-based)\n"
                      f"# text: {'/'.join(sorted(sources))} | closing tag [No. {t['n']}{('-' + t['suf']) if t['suf'] else ''}.] on PDF page {t['page'] + 1} read from {t['src']}\n"
                      f"# page render sha256 (300 dpi grayscale PNG, pypdfium2): {';'.join(hashes)}\n"
                      f"# machine location of an official printing (R37); not an authentication of the signed original\n\n")
            (out / text_path).write_text(header + text, encoding="utf-8", newline="\n")
            rec = {
                "instrument_id": iid, "number": t["n"], "suffix": t["suf"], "htid": htid, "volume_title_range": v["title_range"],
                "pdf_page_first": pages[0] + 1, "pdf_page_last": pages[-1] + 1, "page_count": len(pages),
                "tag_page": t["page"] + 1, "tag_source": t["src"], "text_source": "/".join(sorted(sources)),
                "dateline_seen": seen_date, "identity_date": exp_date, "date_test": date_test, "signature_seen": "yes" if sig else "no",
                "headings_in_span": headings, "gap_before": f"{gap[0]}-{gap[-1]}" if gap else "",
                "verdict": verdict, "reasons": "|".join(reasons), "text_chars": len(text),
                "text_sha256": hashlib.sha256((header + text).encode("utf-8")).hexdigest(), "text_path": text_path,
                "page_render_sha256": ";".join(hashes), "pdf_sha256": v["sha256"],
                "hathitrust_page_url": f"https://babel.hathitrust.org/cgi/pt?id={htid}&seq={pages[0] + 1}",
            }
            vol_orders.append(rec)
            prev = t
        # Orders whose tag the OCR missed but a page checker saw inside another order's span (apply_checks.py):
        # registered on the page the checker named, verdict check, counted only through PAGE_CHECKS.
        rec_path = out / "RECOVERED.csv"
        if rec_path.exists():
            located = {(o["number"], o["suffix"]) for o in vol_orders}
            for rr in csv.DictReader(open(rec_path, encoding="utf-8")):
                if rr["htid"] != htid or not str(rr["pdf_page"]).strip().isdigit():
                    continue
                num_s = rr["number"].upper()
                n = int("".join(ch for ch in num_s if ch.isdigit()))
                suf = "".join(ch for ch in num_s if ch.isalpha())
                if (n, suf) in located or suf not in SUFFIX_ORDER:
                    continue
                pg = int(rr["pdf_page"]) - 1
                if not 0 <= pg < len(rows):
                    continue
                text, sources = page_text(rows[pg])[0], {page_text(rows[pg])[1]}
                iid = ei.canon_id(n, suf)
                idd = ident.get(iid, {})
                exp_date = idd.get("date", "")
                seen_date = rr["dateline"] or read_dateline(text)
                date_test = ("match" if seen_date == exp_date else "year_match" if seen_date[:4] == exp_date[:4] else "conflict") if (seen_date and exp_date) else ("no_identity_date" if seen_date else "dateline_not_found")
                hashes = [rows[pg]["render_png_sha256"]]
                text_path = f"texts/EO_{n}{suf}.txt"
                nl = chr(10)
                header = (f"# {iid} | GPO bound slip-order volume HathiTrust {htid} | PDF page {pg + 1} (1-based)" + nl
                          + f"# text: {'/'.join(sorted(sources))} | tag not read by OCR; the order's heading or tag was seen on this page by {rr['by']} inside the span of {rr['seen_in_span_of']}" + nl
                          + f"# page render sha256 (300 dpi grayscale PNG, pypdfium2): {';'.join(hashes)}" + nl
                          + "# machine location of an official printing (R37); not an authentication of the signed original" + nl + nl)
                (out / text_path).write_text(header + text, encoding="utf-8", newline=nl)
                vol_orders.append({
                    "instrument_id": iid, "number": n, "suffix": suf, "htid": htid, "volume_title_range": v["title_range"],
                    "pdf_page_first": pg + 1, "pdf_page_last": pg + 1, "page_count": 1, "tag_page": pg + 1, "tag_source": "page_check",
                    "text_source": "/".join(sorted(sources)), "dateline_seen": seen_date, "identity_date": exp_date, "date_test": date_test,
                    "signature_seen": "yes" if SIGN.search(text) else "no", "headings_in_span": len(HEAD.findall(text)), "gap_before": "",
                    "verdict": "check", "reasons": f"recovered_by_page_check:{rr['seen_in_span_of']}", "text_chars": len(text),
                    "text_sha256": hashlib.sha256((header + text).encode("utf-8")).hexdigest(), "text_path": text_path,
                    "page_render_sha256": ";".join(hashes), "pdf_sha256": v["sha256"],
                    "hathitrust_page_url": f"https://babel.hathitrust.org/cgi/pt?id={htid}&seq={pg + 1}",
                })
        orders += vol_orders
        nums_found = {o["number"] for o in vol_orders if o["suffix"] == ""}
        expected = set(range(lo, hi + 1))
        summary["volumes"][htid] = {
            "pages": len(rows), "tags_seen": len(tags), "tags_kept": len(kept), "orders": len(vol_orders),
            "expected_numbers": len(expected), "found_in_title_range": len(nums_found & expected),
            "missing_in_title_range": sorted(expected - nums_found)[:400], "dateline_years": vol_years,
            "verdicts": dict(collections.Counter(o["verdict"] for o in vol_orders)),
        }
        with gzip.open(out / "pages" / f"{htid}.jsonl.gz", "wt", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # one row per instrument: when a number appears in two volumes (mdp overlaps hvd), keep the best verdict, list both
    by_id = collections.defaultdict(list)
    for o in orders:
        by_id[o["instrument_id"]].append(o)
    rank = {"pass": 0, "check": 1, "fail": 2}
    final = []
    for iid, lst in by_id.items():
        lst.sort(key=lambda o: (rank[o["verdict"]], o["htid"]))
        best = dict(lst[0])
        best["also_in"] = ";".join(f"{o['htid']}:p{o['pdf_page_first']}-{o['pdf_page_last']}:{o['verdict']}" for o in lst[1:])
        final.append(best)
    final.sort(key=lambda o: (o["number"], SUFFIX_ORDER.get(o["suffix"], 9)))
    with open(out / "ORDERS.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(final[0].keys()))
        w.writeheader()
        w.writerows(final)

    rnd = random.Random(SEED)
    queue = [o for o in final if o["verdict"] != "pass"] + [o for o in final if o["verdict"] == "pass" and rnd.random() < CHECK_SAMPLE]
    with open(out / "PAGE_CHECK_QUEUE.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["instrument_id", "htid", "pdf_page_first", "pdf_page_last", "verdict", "reasons", "why_queued"])
        for o in queue:
            w.writerow([o["instrument_id"], o["htid"], o["pdf_page_first"], o["pdf_page_last"], o["verdict"], o["reasons"],
                        "alignment_failed" if o["verdict"] != "pass" else "random_5pct_sample"])

    checks = {}
    pc = out / "PAGE_CHECKS.csv"
    if pc.exists():
        for r in csv.DictReader(open(pc, encoding="utf-8")):
            checks[r["instrument_id"]] = r
    with open(out / "FRAGMENTS.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for o in final:
            chk = checks.get(o["instrument_id"])
            checked_pass = chk is not None and chk.get("result") == "pass"
            checked_fail = chk is not None and chk.get("result") == "fail"
            counts = (o["verdict"] == "pass" and not checked_fail) or checked_pass
            page_ref = f"HathiTrust {o['htid']} (GPO bound Executive orders, title range {o['volume_title_range']}), PDF pages {o['pdf_page_first']}-{o['pdf_page_last']}"
            note = (f"Official GPO printing located by its closing tag [No. {o['number']}{o['suffix']}.] in the bound slip-order volume; "
                    f"dateline {o['dateline_seen'] or 'not read'} against identity date {o['identity_date'] or 'none'} ({o['date_test']}); "
                    f"signature block {'read' if o['signature_seen'] == 'yes' else 'not read'}. "
                    + (f"Opus page check {chk['result']} ({chk.get('note', '')[:160]}). " if chk else "")
                    + ("Counts as an official printing witness under ruling R37 (2026-11-06); " if counts else
                       f"Alignment needs a page check ({o['reasons']}); ")
                    + "a machine location of a government printing, not an authentication of the signed original; not a legal conclusion.")
            frag = {
                "acceptable_as_original": False,
                "confidence_note": note,
                "data": {
                    "acceptable_as_original": False, "grade": "official_printing",
                    "location_confidence": "high" if counts else ("medium" if o["verdict"] == "check" else "low"),
                    "location_verified": bool(chk), "needs_page_check": not counts,
                    "page_or_item": page_ref, "representation_type": "gpo_bound_slip_order_volume_page",
                    "route": "owner_download/hathitrust_gpo_bound_volume", "sha256": o["pdf_sha256"],
                    "page_render_sha256": o["page_render_sha256"].split(";"), "signing_date": o["dateline_seen"] or o["identity_date"],
                    "source_id": f"{JOB}:{o['instrument_id']}:{o['pdf_sha256'][:12]}", "text_path": o["text_path"],
                    "text_sha256": o["text_sha256"], "title": ident.get(o["instrument_id"], {}).get("title", ""),
                    "url": o["hathitrust_page_url"], "tag_page": o["tag_page"], "date_test": o["date_test"],
                    "alignment_verdict": o["verdict"], "alignment_reasons": o["reasons"],
                    "page_check": ({"result": chk["result"], "by": chk.get("by", ""), "note": chk.get("note", "")} if chk else None),
                },
                "grade": "official_printing", "instrument_id": o["instrument_id"], "kind": "original_representation",
                "produced_by": JOB,
                "sources": [{"page_or_item": page_ref, "sha256": o["pdf_sha256"], "url": o["hathitrust_page_url"]}],
            }
            f.write(json.dumps(frag, ensure_ascii=False) + "\n")

    counted = sum(1 for o in final if (o["verdict"] == "pass" and checks.get(o["instrument_id"], {}).get("result") != "fail")
                  or checks.get(o["instrument_id"], {}).get("result") == "pass")
    summary.update({
        "orders_located": len(final), "verdicts": dict(collections.Counter(o["verdict"] for o in final)),
        "page_checks_recorded": len(checks), "counting_as_official_printing": counted,
        "in_4306_7315": sum(1 for o in final if 4306 <= o["number"] <= 7315),
        "counting_in_4306_7315": sum(1 for o in final if 4306 <= o["number"] <= 7315 and (
            (o["verdict"] == "pass" and checks.get(o["instrument_id"], {}).get("result") != "fail") or checks.get(o["instrument_id"], {}).get("result") == "pass")),
        "page_check_queue": len(queue),
        "note": "Machine locations of official GPO printings (R37). No status, census, codebook or certified count changes.",
    })
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1) + "\n")
    import datetime as dt
    (out / "STATUS.json").write_text(json.dumps({
        "job": JOB, "status": "succeeded", "exit_code": 0, "runner": "owner's PC (Photius session; Opus page checks through the Agent tool)",
        "branch": "main", "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "note": "PC run; the GitHub runner does not run this job (no job.py; the PDFs are private). Outputs are for main."}, indent=1) + "\n")
    lines = ["# Photius GPO volumes: report", "",
             f"Orders located: {len(final)}; verdicts {summary['verdicts']}; counting as official printing: {counted}; "
             f"in 4306-7315: {summary['in_4306_7315']} (counting {summary['counting_in_4306_7315']}); page-check queue {len(queue)}.", "",
             "| Volume | Pages | Tags seen | Kept | Orders | Expected | Found in range | Verdicts |", "|---|---:|---:|---:|---:|---:|---:|---|"]
    for htid, s in summary["volumes"].items():
        if "error" in s:
            continue
        lines.append(f"| {htid} | {s['pages']} | {s['tags_seen']} | {s['tags_kept']} | {s['orders']} | {s['expected_numbers']} | {s['found_in_title_range']} | {s['verdicts']} |")
    (out / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "volumes"}, indent=1))
    for htid, s in summary["volumes"].items():
        print(htid, {k: v for k, v in s.items() if k != "missing_in_title_range"}, "missing:", s.get("missing_in_title_range", [])[:12])


if __name__ == "__main__":
    main()
