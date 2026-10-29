"""Parse the two WPA Historical Records Survey lists of presidential executive orders.

numbered:   "Presidential Executive Orders", vol. 1 (List), numbered series 1-8030, 1862-1938
            (Historical Records Survey, New York, 1944). Entries look like
            "337-A :July 3 Administration of ... 1905 CSR 89." under year headers.
unnumbered: Clifford L. Lord, ed., "List and Index of Presidential Executive Orders,
            Unnumbered Series (1789-1941)" (New Jersey Historical Records Survey, 1943).
            Each year block lists a column of dates, then the entries in the same
            order; each entry ends with its printed-source citation line.

Both come from OCR text layers (Google Books; HathiTrust), committed as page text
in data/. Everything here is a lead for census reconciliation and research, never
an admission to the census or a legal finding.
"""

import collections
import csv
import json
import re
from pathlib import Path

MONTHS = r"(Jan|Feb|Mar|Apr|May|June?|July?|Aug|Sept?|Oct|Nov|Dec)\.?"
YEAR = re.compile(r"^\s*(1[789]\d\d)\s*$")
N_ENTRY = re.compile(r"^\s*(\d{1,4})(?:\s*[-–]\s*([A-Z]))?\s*:\s*(.*)$")
DATE_AT_START = re.compile(rf"^{MONTHS}\s*(\d{{1,2}})\b\*?\s*(.*)$")
DATE_ONLY = re.compile(rf"^\s*{MONTHS}\s*(\d{{1,2}})\s*[.,*]?\s*$")
PAGE_NUMBER = re.compile(r"^\s*\d{1,3}\s*$")
# Printed-source abbreviations used by both lists (see their prefaces).
CITE_TOKEN = re.compile(
    r"\b(?:[IVXL]+\s+Richardson\s+\d+|[IVXL]+\s+R\s+\d+|[IVXL]+\s+Kappler\s+\d+|\d{4}\s+(?:CSR|CSA|GLO|MR|CIA|IR)\s+\d+|"
    r"\d+\s+Stat\.\s*L\.\s*\d+|\d+\s+FR\s+\d+|EO\s+\d{1,4}|[IVXL]+\s+CFR\s+\d+)")
SOURCE_NAMES = {
    "CSR": "Civil Service Commission annual report", "CSA": "Civil Service Commission act/rules compilation",
    "GLO": "General Land Office annual report", "MR": "Military reservations list (War Dept.)",
    "CIA": "Commissioner of Indian Affairs annual report", "IR": "Indian reservations compilation",
    "Richardson": "Richardson, Messages and Papers of the Presidents", "R": "Richardson, Messages and Papers",
    "Kappler": "Kappler, Indian Affairs: Laws and Treaties", "Stat. L.": "Statutes at Large",
    "FR": "Federal Register", "CFR": "Code of Federal Regulations", "EO": "cross-reference to a numbered order",
}
# Keyword families (first match wins), used only to group orders for later family rules.
FAMILIES = [
    ("civil_service_individual", r"made eligible|eligible for (appointment|reinstatement|transfer)|reinstate|appointed .* without examination"),
    ("civil_service_rules", r"civil service rule|schedule [a-z]\b|classified service|competitive (service|classified)"),
    ("military_reservation", r"military reserv|fort .* reservation|reserved for military"),
    ("indian_reservation", r"indian reservation|reservation .* indian|allotment"),
    ("national_forest", r"national forest|forest reserve"),
    ("land_withdrawal", r"withdrawn|public water reserve|petroleum reserve|coal land|power site|lands? .* reserved|restored to (the )?public domain"),
    ("lighthouse_navigation", r"light-?house|lighthouse|navigation aid"),
    ("bird_wildlife_refuge", r"bird refuge|wildlife|game (preserve|refuge)"),
    ("office_closing_mourning", r"ordered closed|closed .* (memory|respect)|mourning|flag .* half"),
    ("canal_zone", r"canal zone|panama canal"),
    ("tariff_customs", r"customs|tariff|duty|port of entry"),
    ("emergency_war", r"war|defense|emergency|alien property"),
    ("nra_codes", r"\bnra\b|code of fair competition"),
]


def clean(s):
    return re.sub(r"\s+", " ", s).strip()


def family_of(summary):
    low = summary.lower()
    for name, pat in FAMILIES:
        if re.search(pat, low):
            return name
    return "other"


def citations(text):
    return sorted({clean(c) for c in CITE_TOKEN.findall(text)})


def source_kinds(cites):
    out = set()
    for c in cites:
        for k in ("Richardson", "Kappler", "CSR", "CSA", "GLO", "MR", "CIA", "IR", "Stat. L", "FR", "CFR", "EO"):
            if re.search(rf"\b{re.escape(k)}\b", c):
                out.add("Stat. L." if k == "Stat. L" else k)
                break
        else:
            if re.search(r"\b[IVXL]+\s+R\s+\d", c):
                out.add("R")
    return sorted(out)


# ------------------------------------------------------------------ numbered list
def parse_numbered(pages):
    """Entries of the numbered list, in order. Out-of-sequence numbers are treated as text."""
    entries, year, cur = [], None, None
    for pg in pages:
        for line in pg["text"].splitlines():
            m = YEAR.match(line)
            if m:
                year = int(m.group(1))
                continue
            m = N_ENTRY.match(line)
            if m and year:
                num, suf, rest = int(m.group(1)), m.group(2) or "", m.group(3)
                if not cur or cur["number"] - 5 <= num <= cur["number"] + 60:
                    d = DATE_AT_START.match(rest.strip())
                    cur = {"number": num, "suffix": suf, "id": f"EO:{num}{suf}", "year": year,
                           "month_day": f"{d.group(1)} {d.group(2)}" if d else "",
                           "text": d.group(3) if d else rest, "page": pg["page"]}
                    entries.append(cur)
                    continue
            if cur:
                cur["text"] += " " + line.strip()
    for e in entries:
        e["text"] = clean(e["text"])
        e["citations"] = citations(e["text"])
        e["source_kinds"] = source_kinds(e["citations"])
        e["family_hint"] = family_of(e["text"])
        e["has_form_of_proclamation"] = "form of a proclamation" in e["text"].lower()
    return entries


# ------------------------------------------------------------------ unnumbered list
def _is_citation_line(line):
    """An entry's closing source line starts with "(" or with a source citation; a
    citation inside a sentence ("under the act of ... (23 Stat.L. 103)") does not count."""
    s = line.strip()
    return bool(s) and (s.startswith("(") or bool(CITE_TOKEN.match(s)))


def parse_unnumbered(pages, first_page=20):
    """Pair each year-block's date column with its entries (each ending in a citation line).

    Returns (entries, blocks); a block whose date count differs from its entry count is
    kept with pairing 'uncertain' so nothing is silently mis-dated."""
    entries, blocks = [], []
    year = None
    dates, texts, cur, in_cite = [], [], [], False

    def flush(page):
        nonlocal dates, texts, cur
        if cur:
            texts.append(cur)
            cur = []
        if not texts and not dates:
            return
        ok = len(dates) == len(texts)
        blocks.append({"page": page, "year": year, "dates": len(dates), "entries": len(texts), "paired": ok})
        for k, t in enumerate(texts):
            body = [l for l in t if not _is_citation_line(l)]
            cite = " ".join(l for l in t if _is_citation_line(l))
            summary = clean(" ".join(body))
            entries.append({
                "year": year, "date": dates[k] if ok else "", "page": page, "pairing": "paired" if ok else "uncertain",
                "summary": summary, "citation_text": clean(cite), "citations": citations(cite),
            })
        dates, texts = [], []

    started = False
    for pg in pages:
        if pg["page"] < first_page:
            continue
        if not started:  # skip the preface: the list begins at its first year header
            if not any(YEAR.match(l) for l in pg["text"].splitlines()):
                continue
            started = True
        lines = [l for l in pg["text"].splitlines()]
        for n, line in enumerate(lines):
            if n == 0 and PAGE_NUMBER.match(line):
                continue  # printed page number at the top
            m = YEAR.match(line)
            if m:
                flush(pg["page"])
                year = int(m.group(1))
                in_cite = False
                continue
            if DATE_ONLY.match(line):
                if texts or cur:          # a new date column starts a new block
                    flush(pg["page"])
                d = DATE_ONLY.match(line)
                dates.append(f"{d.group(1)} {d.group(2)}")
                continue
            d = DATE_AT_START.match(line.strip())
            if d and not cur and not in_cite:   # "Mar. 31 All persons ..." (date and text on one line)
                dates.append(f"{d.group(1)} {d.group(2)}")
                cur = [d.group(3)]
                continue
            if not line.strip():
                continue
            if _is_citation_line(line) or in_cite:
                cur.append(line)
                opened = line.count("(") - line.count(")")
                in_cite = (in_cite or line.strip().startswith("(")) and ")" not in line if opened >= 0 else False
                if not in_cite:
                    texts.append(cur)
                    cur = []
                continue
            cur.append(line)
    flush(pages[-1]["page"] if pages else 0)
    for k, e in enumerate(entries, 1):
        e["seq"] = k
        e["family_hint"] = family_of(e["summary"])
        e["source_kinds"] = source_kinds(e["citations"])
    return entries, blocks


# ------------------------------------------------------------------ cross-check
def numbered_crosscheck(entries, census_rows):
    wpa = {}
    for e in entries:
        wpa.setdefault(e["id"], e)
    uni = {r["id"]: r for r in census_rows}

    def is_numbered(i):
        m = re.fullmatch(r"EO:(\d+)[A-Z]?", i)
        return bool(m) and int(m.group(1)) <= 8030

    rows = []
    for i in sorted((x for x in uni if is_numbered(x)), key=lambda x: (int(re.match(r"EO:(\d+)", x).group(1)), x)):
        e = wpa.get(i)
        cy = (uni[i].get("date_effective") or "")[:4]
        rows.append({"instrument_id": i, "in_wpa_list": "yes" if e else "no", "wpa_year": e["year"] if e else "",
                     "wpa_month_day": e["month_day"] if e else "", "census_year": cy,
                     "year_agrees": "" if not e else ("yes" if str(e["year"]) == cy else "no"),
                     "wpa_page": e["page"] if e else "", "family_hint": e["family_hint"] if e else "",
                     "printed_sources": " | ".join(e["citations"]) if e else "",
                     "wpa_summary": e["text"][:400] if e else ""})
    not_in_census = [e for i, e in wpa.items() if i not in uni]
    return rows, not_in_census


def write_csv(path, rows, fields):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def run(repo, here, out):
    repo, here, out = Path(repo), Path(here), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    load = lambda p: [json.loads(l) for l in (here / "data" / p).read_text(encoding="utf-8").splitlines() if l.strip()]
    num = parse_numbered(load("numbered_pages.jsonl"))
    unn, blocks = parse_unnumbered(load("unnumbered_pages.jsonl"))
    with open(repo / "research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv", encoding="utf-8") as fh:
        census = list(csv.DictReader(fh))
    cross, extra = numbered_crosscheck(num, census)

    for e in num:
        e["citations_joined"] = " | ".join(e["citations"])
        e["source_kinds_joined"] = " | ".join(e["source_kinds"])
    write_csv(out / "NUMBERED_ENTRIES.csv", num,
              ["id", "number", "suffix", "year", "month_day", "page", "family_hint", "has_form_of_proclamation",
               "source_kinds_joined", "citations_joined", "text"])
    write_csv(out / "NUMBERED_CENSUS_CROSSCHECK.csv", cross, list(cross[0].keys()) if cross else ["instrument_id"])
    write_csv(out / "WPA_ORDERS_NOT_IN_CENSUS.csv", extra, ["id", "year", "month_day", "page", "text"])
    for e in unn:
        e["citations_joined"] = " | ".join(e["citations"])
        e["source_kinds_joined"] = " | ".join(e["source_kinds"])
    write_csv(out / "UNNUMBERED_ENTRIES.csv", unn,
              ["seq", "year", "date", "pairing", "page", "family_hint", "source_kinds_joined", "citations_joined",
               "summary", "citation_text"])
    write_csv(out / "UNNUMBERED_BLOCKS.csv", blocks, ["page", "year", "dates", "entries", "paired"])

    kinds = collections.Counter(k for e in num + unn for k in e["source_kinds"])
    matched = [r for r in cross if r["in_wpa_list"] == "yes"]
    summary = {
        "job": "wpa-lists",
        "sources": json.loads((here / "data" / "PROVENANCE.json").read_text(encoding="utf-8")),
        "numbered": {
            "entries": len(num), "census_numbered_1_8030": len(cross), "census_found_in_list": len(matched),
            "coverage_pct": round(100 * len(matched) / max(len(cross), 1), 2),
            "year_disagreements": sum(1 for r in matched if r["year_agrees"] == "no"),
            "list_orders_not_in_census": len(extra),
            "entries_with_printed_source": sum(1 for e in num if e["citations"]),
            "families": dict(collections.Counter(e["family_hint"] for e in num).most_common()),
        },
        "unnumbered": {
            "entries": len(unn), "paired_with_date": sum(1 for e in unn if e["pairing"] == "paired"),
            "blocks": len(blocks), "blocks_paired": sum(1 for b in blocks if b["paired"]),
            "years": f"{min((e['year'] for e in unn if e['year']), default='')}-{max((e['year'] for e in unn if e['year']), default='')}",
            "entries_with_printed_source": sum(1 for e in unn if e["citations"]),
            "families": dict(collections.Counter(e["family_hint"] for e in unn).most_common()),
            "census_identities_unnumbered_today": sum(1 for r in census if not re.fullmatch(r"EO:\d+[A-Z½]?(-\d+)?", r["id"])),
        },
        "printed_source_kinds": {k: {"count": v, "name": SOURCE_NAMES.get(k, k)} for k, v in kinds.most_common()},
        "establishes": "census leads only: no identity is admitted, merged or changed; no legal finding",
    }
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary
