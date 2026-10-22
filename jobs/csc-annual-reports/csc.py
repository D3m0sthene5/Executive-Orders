"""Civil Service Commission annual reports (GovInfo Serial Set) -> WPA-cited executive-order texts.

For each gap order whose WPA/Lord entry cites "<year> CSR <page>", fetch that fiscal year's annual
report from the Serial Set on GovInfo, map the printed page to a PDF page from the running heads,
find the order's date line on or next to that page, and cut the paragraph that follows it up to the
next date line or heading. Results are location leads from an agency report's printing (often an
abstract of the order), never authenticated originals.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import pathlib
import re
import sys
import time
from collections import Counter, defaultdict

MONTHS = {"jan": "January", "feb": "February", "mar": "March", "apr": "April", "may": "May",
          "jun": "June", "june": "June", "jul": "July", "july": "July", "aug": "August",
          "sep": "September", "sept": "September", "oct": "October", "nov": "November", "dec": "December"}
MONTH_ALT = "|".join(sorted(set(MONTHS.values()), key=len, reverse=True))
CITE_RE = re.compile(r"\b(1[89]\d\d)\s*C[S8]R\s*(\d{1,4})\b")
# A date standing alone on its line opens an order in these reports ("October 10, 1916.").
DATE_LINE_RE = re.compile(rf"^\s*(?:{MONTH_ALT})\s+\d{{1,2}}\s*[,;.:]?\s*1[89]\d[\d%]\s*[.:;,]?\s*[:.;,]?\s*$", re.I)
HEADER_RE = re.compile(r"^\s*(?:(\d{1,4})\s+[A-Z][A-Z .,'\-]{6,}|[A-Z][A-Z .,'\-]{6,}?\s(\d{1,4}))\s*$")
FY_RE = re.compile(r"(?:FISCAL\s+YEAR\s+ENDED\s+JUNE\s+30|YEAR\s+ENDED\s+JUNE\s+30|TO\s+JUNE\s+30)[\s,.]*(1[89]\d\d)", re.I)


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def wpa_date(month_day: str, year: str):
    """WPA 'Oct 10' + '1916' -> ('October', 10, 1916), or None."""
    parts = month_day.replace(".", " ").split()
    if len(parts) != 2 or not parts[1].isdigit():
        return None
    month = MONTHS.get(parts[0].lower())
    return (month, int(parts[1]), int(year)) if month else None


def date_regex(month: str, day: int, year: int, fuzzy_year: bool = False) -> re.Pattern:
    yr = rf"{str(year)[:3]}[\d%]" if fuzzy_year else str(year)
    return re.compile(rf"\b{month}\s+{day}\s*[,;.:]?\s*{yr}(?!\d)", re.I)


def citations(rows) -> list[dict]:
    """One item per (order, cited report year, page). An order with several WPA rows keeps each row's text."""
    out, seen = [], set()
    for r in rows:
        for fy, page in CITE_RE.findall(r["citations_joined"]):
            key = (r["id"], int(fy), int(page))
            if key in seen:
                continue
            seen.add(key)
            out.append({"id": r["id"], "fy": int(fy), "page": int(page), "wpa": r})
    return out


UNITS = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8,
         "ninth": 9, "tenth": 10, "eleventh": 11, "twelfth": 12, "thirteenth": 13, "fourteenth": 14,
         "fifteenth": 15, "sixteenth": 16, "seventeenth": 17, "eighteenth": 18, "nineteenth": 19}
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60}
TENTHS = {"twentieth": 20, "thirtieth": 30, "fortieth": 40, "fiftieth": 50, "sixtieth": 60}
ORDINAL_RE = re.compile(r"\b(?:(twenty|thirty|forty|fifty|sixty)[\s-]*)?(" + "|".join(list(UNITS) + list(TENTHS))
                        + r")\s+(?:annual\s+)?report", re.I)


def report_number(text: str):
    """'THIRTY-FOURTH ANNUAL REPORT' -> 34; '57th Annual Report' -> 57."""
    m = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)\s+(?:annual\s+)?report", text, re.I)
    if m:
        return int(m.group(1))
    m = ORDINAL_RE.search(text)
    if not m:
        return None
    word = m.group(2).lower()
    return TENS.get((m.group(1) or "").lower(), 0) + UNITS.get(word, 0) + TENTHS.get(word, 0)


def report_fy(first_pages_text: str):
    """Fiscal year from the title page. Report n covers FY 1883 + n (the 34th covers FY 1917); the ordinal
    wins when OCR garbles the year (the 40th report's title page reads 1925 for 1923)."""
    text = norm_space(first_pages_text)
    m = FY_RE.search(text)
    fy = int(m.group(1)) if m else None
    n = report_number(text)
    if n and n >= 4 and (fy is None or fy != 1883 + n):
        return 1883 + n
    return fy


def printed_number(page_text: str):
    """Arabic running-head page number from the first two non-empty lines, or None."""
    lines = [l for l in page_text.splitlines() if l.strip()][:2]
    for line in lines:
        m = HEADER_RE.match(line.strip())
        if m:
            return int(m.group(1) or m.group(2))
    return None


def page_map(texts: list[str]) -> dict[int, int]:
    """printed page -> 0-based PDF page. Detected heads first; gaps filled from the nearest head's offset."""
    detected = {}
    for i, t in enumerate(texts):
        p = printed_number(t)
        if p is not None and p not in detected:
            detected[p] = i
    # Keep only heads consistent with their neighbours (OCR can misread a number).
    offsets = sorted((p, i - p) for p, i in detected.items())
    good = {}
    for k, (p, off) in enumerate(offsets):
        near = [o for _, o in offsets[max(0, k - 3):k + 4]]
        if Counter(near).most_common(1)[0][0] == off or near.count(off) >= 2:
            good[p] = p + off
    out = dict(good)
    known = sorted(good)
    if known:
        for p in range(1, known[-1] + 30):
            if p in out:
                continue
            nearest = min(known, key=lambda q: abs(q - p))
            if abs(nearest - p) <= 12:
                idx = p + (good[nearest] - nearest)
                if 0 <= idx < len(texts):
                    out[p] = idx
    return out


def is_heading(line: str) -> bool:
    s = line.strip()
    letters = [c for c in s if c.isalpha()]
    return len(letters) >= 8 and sum(c.isupper() for c in letters) / len(letters) > 0.9 and len(s.split()) >= 2


def body_lines(text: str) -> list[str]:
    lines = text.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and printed_number(lines[0]) is not None:
        lines = lines[1:]
    return lines


def segments_on(texts: list[str], idx: int, rx: re.Pattern) -> list[tuple[int, str]]:
    """Each date-line match on page idx, with the order text up to the next date line or heading (may run one page on)."""
    found = []
    lines = body_lines(texts[idx])
    for n, line in enumerate(lines):
        if not (DATE_LINE_RE.match(line) and rx.search(line)):
            continue
        seg, stop = [line.strip()], False
        tail = lines[n + 1:] + (body_lines(texts[idx + 1]) if idx + 1 < len(texts) else [])
        for nxt in tail:
            if DATE_LINE_RE.match(nxt) or is_heading(nxt):
                stop = True
                break
            seg.append(nxt.rstrip())
        found.append((n, "\n".join(seg).strip() + "\n", stop))
    return [(n, s) for n, s, _ in found]


def overlap(a: str, b: str) -> float:
    wa = {w for w in re.findall(r"[a-z]{4,}", a.lower())}
    wb = {w for w in re.findall(r"[a-z]{4,}", b.lower())}
    return len(wa & wb) / max(1, len(wa))


def locate(texts: list[str], pmap: dict[int, int], cite: dict):
    """Return (pdf_index, segment_text, confidence, how) or (None, None, None, reason)."""
    d = wpa_date(cite["wpa"]["month_day"], cite["wpa"]["year"])
    if not d:
        return None, None, None, "wpa_date_unparsed"
    target = pmap.get(cite["page"])
    if target is None:
        return None, None, None, "printed_page_not_mapped"
    for fuzzy in (False, True):
        rx = date_regex(*d, fuzzy_year=fuzzy)
        for delta in (0, -1, 1, -2, 2):
            idx = target + delta
            if not 0 <= idx < len(texts):
                continue
            segs = segments_on(texts, idx, rx)
            if not segs:
                continue
            if len(segs) == 1:
                conf = "high" if delta == 0 and not fuzzy else "medium"
                return idx, segs[0][1], conf, f"date line on pdf page {idx + 1} (cited page offset {delta:+d})"
            best = max(segs, key=lambda s: overlap(cite["wpa"]["text"], s[1]))
            cite["_same_date_segments"] = [s for _, s in segs]
            return idx, best[1], "low", f"{len(segs)} orders share this date on the page; picked by WPA summary overlap"
    # Older reports often cite an order inline ("By Executive order of November 2, 1894, ...").
    rx = date_regex(*d)
    for delta in (0, -1, 1):
        idx = target + delta
        if not 0 <= idx < len(texts):
            continue
        lines = body_lines(texts[idx])
        hits = [n for n, l in enumerate(lines) if rx.search(l)]
        if hits:
            n = hits[0]
            start = n
            while start > 0 and lines[start - 1].strip() and not is_heading(lines[start - 1]) and n - start < 3:
                start -= 1
            seg = []
            for line in lines[start:]:
                if seg and (DATE_LINE_RE.match(line) or is_heading(line)):
                    break
                seg.append(line.rstrip())
            return idx, "\n".join(seg).strip() + "\n", "low", f"date found inline on pdf page {idx + 1}, no date-line heading"
    return None, None, None, "date_not_found_near_cited_page"


def load_reports(job_dir: pathlib.Path) -> list[dict]:
    return json.loads((job_dir / "data" / "REPORTS.json").read_text(encoding="utf-8"))["reports"]


def pdf_texts(raw: bytes) -> list[str]:
    import pypdf
    reader = pypdf.PdfReader(io.BytesIO(raw))
    return [(p.extract_text() or "") for p in reader.pages]


def run(repo: pathlib.Path, job_dir: pathlib.Path, out: pathlib.Path, pool, max_reports: int | None = None):
    rows = list(csv.DictReader(open(job_dir / "data" / "CITATIONS.csv", encoding="utf-8")))
    cites = citations(rows)
    ids_all = sorted({r["id"] for r in rows})
    need_fy = sorted({c["fy"] for c in cites})
    reports = load_reports(job_dir)
    # Fetch every package whose title year is a needed year or next to one; the title page decides its real year.
    want = [r for r in reports if r["title_fy"] and any(abs(r["title_fy"] - fy) <= 1 for fy in need_fy)]
    if max_reports:
        want = want[:max_reports]
    print(f"{len(ids_all)} orders, {len(cites)} citations, {len(need_fy)} report years needed; fetching {len(want)} packages", flush=True)

    by_fy = defaultdict(list)
    fetched = []
    tmpl = "https://www.govinfo.gov/content/pkg/{p}/pdf/{p}.pdf"

    def one(rep):
        # Parse inside the worker so only page texts, never PDF bodies, outlive the call.
        url = tmpl.format(p=rep["package_id"])
        row = {"package_id": rep["package_id"], "title_fy": rep["title_fy"], "url": url, "error": ""}
        t0 = time.time()
        try:
            got = pool.fetch(url)
        except Exception as e:  # recorded, never an absence finding
            row.update(error=f"{type(e).__name__}: {e}", seconds=round(time.time() - t0, 1))
            return row, None
        raw = got["body"]
        row.update(bytes=len(raw), sha256=got["sha256"], seconds=round(time.time() - t0, 1))
        if raw[:5] != b"%PDF-":
            row["error"] = "not_a_pdf"
            return row, None
        texts = pdf_texts(raw)
        del raw, got
        fy = report_fy("\n".join(texts[:4]))
        pmap = page_map(texts)
        row.update(pdf_pages=len(texts), fy_on_title_page=fy or "", printed_pages_mapped=len(pmap))
        return row, ({"rep": rep, "url": url, "sha256": row["sha256"], "texts": texts, "pmap": pmap} if fy else None)

    for row, vol in pool.map(one, want):
        if vol:
            by_fy[row["fy_on_title_page"]].append(vol)
        fetched.append(row)
        print(f"  {row['package_id']} title_fy={row['title_fy']} -> fy={row.get('fy_on_title_page')} "
              f"pages={row.get('pdf_pages')} mapped={row.get('printed_pages_mapped')} {row['error']}", flush=True)

    (out / "texts").mkdir(parents=True, exist_ok=True)
    results, frags = [], []
    best_by_id = {}
    rank = {"high": 3, "medium": 2, "low": 1}
    for c in cites:
        res = {"id": c["id"], "cited": f"{c['fy']} CSR {c['page']}", "wpa_date": f"{c['wpa']['month_day']} {c['wpa']['year']}",
               "family_hint": c["wpa"]["family_hint"], "package_id": "", "pdf_page": "", "confidence": "", "how": ""}
        vols = by_fy.get(c["fy"], [])
        if not vols:
            res["how"] = "report_for_cited_year_not_held"
        for v in vols:
            idx, seg, conf, how = locate(v["texts"], v["pmap"], c)
            res.update(package_id=v["rep"]["package_id"], how=how)
            if idx is not None:
                res.update(pdf_page=idx + 1, confidence=conf)
                prev = best_by_id.get(c["id"])
                if not prev or rank[conf] > rank[prev[0]]:
                    best_by_id[c["id"]] = (conf, c, v, idx, seg, how)
                break
        results.append(res)

    # Orders sharing a date on one page are printed in number order: when every such paragraph is
    # claimed by exactly that many gap orders, pair them in order instead of by word overlap.
    groups = defaultdict(list)
    for iid, (conf, c, v, idx, seg, how) in best_by_id.items():
        if c.get("_same_date_segments"):
            groups[(v["rep"]["package_id"], idx, c["wpa"]["month_day"], c["wpa"]["year"])].append(iid)
    for key, iids in groups.items():
        segs = best_by_id[iids[0]][1]["_same_date_segments"]
        if len(iids) == len(segs):
            for iid, seg in zip(sorted(iids, key=lambda i: int(re.match(r"EO:(\d+)", i).group(1))), segs):
                conf, c, v, idx, _, _ = best_by_id[iid]
                best_by_id[iid] = ("medium", c, v, idx, seg,
                                   f"{len(segs)} gap orders share this date on pdf page {idx + 1}; paired in number order")
    for iid, (conf, c, v, idx, seg, how) in sorted(best_by_id.items()):
        name = "EO_" + iid.split(":", 1)[1] + ".txt"
        data = seg.encode("utf-8")
        (out / "texts" / name).write_bytes(data)
        page_url = f"{v['url']}#page={idx + 1}"
        place = f"{v['rep']['title']}, printed page {c['page']} as cited by WPA, PDF page {idx + 1}"
        frags.append({
            "acceptable_as_original": False,
            "confidence_note": (f"Machine location lead, confidence {conf}: {how}. Text is the GovInfo scan's OCR layer of a "
                                "Civil Service Commission annual report, which may print the order in full or only as an "
                                "abstract. Located from the WPA/Lord citation and the WPA date; identity, boundaries and "
                                "wording are NOT human-verified; this is not a legal conclusion."),
            "data": {"acceptable_as_original": False, "grade": "compiled_transcription_lead",
                     "representation_type": "agency_annual_report_printing_or_abstract",
                     "location_confidence": conf, "location_verified": False, "needs_page_check": True,
                     "page_or_item": place, "route": "official_publication/csc_annual_report_serial_set",
                     "sha256": v["sha256"], "source_id": f"csc-annual-reports:{iid}:{v['sha256'][:12]}",
                     "text_path": "texts/" + name, "text_sha256": sha256(data), "url": page_url,
                     "wpa_citation": f"{c['fy']} CSR {c['page']}", "wpa_date_lead": f"{c['wpa']['month_day']} {c['wpa']['year']}"},
            "instrument_id": iid, "kind": "original_representation", "produced_by": "csc-annual-reports",
            "sources": [{"page_or_item": place, "sha256": v["sha256"], "url": page_url}]})

    for r in results:
        b = best_by_id.get(r["id"])
        if b and r["package_id"] == b[2]["rep"]["package_id"] and r["pdf_page"] == b[3] + 1:
            r["confidence"], r["how"] = b[0], b[5]
    with open(out / "FRAGMENTS.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for f in frags:
            fh.write(json.dumps(f, sort_keys=True, ensure_ascii=False) + "\n")
    for name, rows_, fields in (("CITATION_RESULTS.csv", results, list(results[0]) if results else ["id"]),
                                ("REPORTS_FETCHED.csv", fetched, sorted({k for r in fetched for k in r}))):
        with open(out / name, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
            w.writeheader()
            w.writerows(rows_)
    held = set(best_by_id)
    missing_reasons = Counter(r["how"] for r in results if r["id"] not in held)
    summary = {
        "orders_targeted": len(ids_all), "citations": len(cites), "report_years_needed": need_fy,
        "packages_fetched_ok": sum(1 for r in fetched if not r["error"]), "packages_failed": sum(1 for r in fetched if r["error"]),
        "report_years_held": sorted(by_fy), "report_years_needed_not_held": [fy for fy in need_fy if fy not in by_fy],
        "orders_located": len(held), "orders_by_confidence": dict(Counter(v[0] for v in best_by_id.values())),
        "orders_not_located": len(ids_all) - len(held),
        "unlocated_citation_reasons": dict(missing_reasons),
        "bytes_downloaded": pool.bytes_downloaded, "requests": pool.requests, "cache_hits": pool.cache_hits,
        "note": "Location leads only. Nothing here authenticates an order, changes the census or decides a status.",
    }
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(summary, indent=1))
    return summary


if __name__ == "__main__":
    sys.exit("run job.py")
