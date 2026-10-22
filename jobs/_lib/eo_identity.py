"""Shared identity helpers for the Lewis and Clark jobs (the project's "Corps of Discovery").

Lewis (jobs/lewis-originals) finds official originals for orders the project holds only as
transcriptions. Clark (jobs/clark-discovery) finds orders the project cannot yet identify. Both
need the same things: the 14,972-order universe, every date or title any index gives an order,
the saved texts, the ProQuest supplied-link list, and one way of reading an order number.

Everything here is read-only and standard library. Nothing it returns is a legal finding or an
identity authentication; these are the project's existing machine leads, loaded once.
"""
from __future__ import annotations

import csv
import datetime as _dt
import json
import os
import re

csv.field_size_limit(min(2**31 - 1, 10**9))

UNIVERSE = "research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv"
READINESS = "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv"
OFR_CATALOG = "jobs/later-events/output/CATALOG_INDEX.csv"
APP_INDEX = "jobs/app-executive-orders/output/INDEX.csv"
WPA_PRE1900 = "jobs/census-completeness/data/WPA_NUMBERED_pre1900.csv"
PROQUEST_DIR = "research/pre-1937-sources/ProQuest Pre-1937 Orders"
PROQUEST_LINKS = PROQUEST_DIR + "/_resume/proquest_download_links.html"
FIRST_FEDERAL_REGISTER = _dt.date(1936, 3, 14)

# Fragment files the readiness tracker reads, by the class it gives them. The texts behind them
# are the project's saved order texts. Order matters only for reporting.
FRAGMENT_FILES = {
    "official": [
        "jobs/fr-originals/data/full_run/FRAGMENTS.jsonl",
        "jobs/fr-originals/output/FRAGMENTS.jsonl",
        "jobs/ofr-compilations/output/FRAGMENTS.jsonl",
        "jobs/isthmian-canal-1911/output/FRAGMENTS.jsonl",
        "jobs/indian-reservations-1912/output/FRAGMENTS.jsonl",
    ],
    "transcription": [
        "jobs/richardson-volumes/output/FRAGMENTS.jsonl",
        "jobs/app-executive-orders/output/FRAGMENTS.jsonl",
        "jobs/app-executive-orders/output/MIRROR_FRAGMENTS.jsonl",
        "jobs/hathi-gpo-orders/output/FRAGMENTS.jsonl",
        "jobs/numbered-early-orders/output/FRAGMENTS.jsonl",
        "jobs/wikisource-texts/output/FRAGMENTS.jsonl",
        "jobs/csc-annual-reports/output/FRAGMENTS.jsonl",
    ],
    # Lewis's own ProQuest text layers, read by Clark on the next run.
    "archival_replica": ["jobs/pinakes-proquest-ingest/output/FRAGMENTS.jsonl", "jobs/lewis-originals/output/FRAGMENTS.jsonl"],
}

_ID_RE = re.compile(r"^EO:(\d{1,5})(?:-?([A-Z])|(½|\s?1/2)|-(\d{1,2}))?$")
_HALF = "½"


def parse_eo_id(value):
    """'EO:1234', 'EO:1234A', 'EO:1234-A', 'EO:1182½', 'EO:23-1' -> (1234, 'A') / (23, '-1'); else None.

    'EO:23-1' is the census's second document under one number (a duplicate-number case), kept as
    the suffix '-1' so the id round-trips through canon_id. Unnumbered ids ('EO:UN:...') do not parse.
    """
    if not isinstance(value, str):
        return None
    m = _ID_RE.match(value.strip().upper().replace("1/2", _HALF))
    if not m:
        return None
    suffix = m.group(2) or (_HALF if m.group(3) else "") or (f"-{m.group(4)}" if m.group(4) else "")
    return int(m.group(1)), suffix


def canon_id(number, suffix=""):
    suffix = (suffix or "").upper().replace("1/2", _HALF)
    if not suffix.startswith("-"):
        suffix = suffix.replace("-", "")
    return f"EO:{int(number)}{suffix}"


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def read_jsonl(path):
    out = []
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                out.append({"_bad_line": n, "_file": path})
    return out


def parse_date(value):
    """ISO date, 'March 3, 1932', 'Mar 3, 1932' or a bare year -> date (year -> Jan 1) or None."""
    if not value:
        return None
    value = str(value).strip()
    for fmt in ("%Y-%m-%d", "%B %d, %Y", "%b %d, %Y", "%b. %d, %Y", "%Y"):
        try:
            return _dt.datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    m = re.match(r"^(\d{4})", value)
    return _dt.date(int(m.group(1)), 1, 1) if m else None


def load_universe(root):
    """id -> census row, for the orders counted in the 14,972 denominator."""
    return {r["id"]: r for r in read_csv(os.path.join(root, UNIVERSE))
            if r.get("included_in_bibliography") == "1"}


def load_readiness(root):
    return {r["instrument_id"]: r for r in read_csv(os.path.join(root, READINESS))}


def load_fragments(root, classes=("official", "transcription", "archival_replica")):
    """id -> list of fragment summaries: who produced it, grade, text path, date, title, url."""
    out = {}
    for cls in classes:
        for rel in FRAGMENT_FILES.get(cls, []):
            path = os.path.join(root, rel)
            base = os.path.dirname(path)
            for r in read_jsonl(path):
                iid = r.get("instrument_id")
                if not iid or r.get("_bad_line"):
                    continue
                d = r.get("data") or {}
                src = (r.get("sources") or [{}])[0]
                tp = d.get("text_path")
                out.setdefault(iid, []).append({
                    "class": cls,
                    "produced_by": r.get("produced_by") or os.path.basename(os.path.dirname(base)),
                    "grade": r.get("grade") or d.get("grade") or ("official" if cls == "official" else ""),
                    "needs_page_check": d.get("needs_page_check"),
                    "acceptable_as_original": r.get("acceptable_as_original", d.get("acceptable_as_original")),
                    "text_path": os.path.join(base, tp) if tp else None,
                    "sha256": d.get("sha256") or src.get("sha256") or "",
                    "url": d.get("url") or src.get("url") or "",
                    "page_or_item": d.get("page_or_item") or src.get("page_or_item") or "",
                    "date": d.get("signing_date") or d.get("app_date") or d.get("match_date") or "",
                    "title": d.get("title") or "",
                })
    return out


def load_proquest_rows(root):
    """The owner's supplied ProQuest link list (the `const ROWS=` JSON inside the saved HTML)."""
    path = os.path.join(root, PROQUEST_LINKS)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8", errors="replace") as fh:
        html = fh.read()
    m = re.search(r"const ROWS\s*=\s*(\[.*?\]);", html, re.S)
    if not m:
        return []
    try:
        rows = json.loads(m.group(1))
    except json.JSONDecodeError:
        return []
    return [r for r in rows if isinstance(r, dict) and parse_eo_id(str(r.get("id", "")))]


_PQ_NAME = re.compile(r"^(?:PT1-)?(\d{4})-EO-(\d{1,5})(?:-?([A-Z]))?(?:_From_(\d+)_to_(\d+))?(?:\s\((\d+)\))?\.pdf$", re.I)
PROQUEST_DIRS = (PROQUEST_DIR, "ProQuest Pre-1937 Orders")  # the research folder, and the owner's upload at the repo root


def proquest_filename(name):
    """'PT1-1865-EO-4 (1).pdf' -> {'year': 1865, 'number': 4, 'suffix': '', 'copy': 1, 'page_range': ''}.

    Also '1900-EO-125-A.pdf' (hyphenated suffix) and '1918-EO-3016-E_From_1_to_2.pdf' (a page range
    the viewer put in the name). Anything else -> None.
    """
    m = _PQ_NAME.match(name)
    if not m:
        return None
    return {"year": int(m.group(1)), "number": int(m.group(2)), "suffix": (m.group(3) or "").upper(),
            "copy": int(m.group(6) or 0), "page_range": f"{m.group(4)}-{m.group(5)}" if m.group(4) else ""}


def load_dates(root, fragments=None):
    """id -> {'date': 'YYYY-MM-DD' or 'YYYY', 'title': str, 'date_source': str}.

    Best source first: the OFR catalog (1937 on), fr-originals, the American Presidency Project index,
    any other fragment, the WPA pre-1900 list, then the ProQuest list (year only) and the census year.
    Every one of these is a machine index; none authenticates an identity.
    """
    out = {}

    def put(iid, date, title, source, president=""):
        if not iid:
            return
        cur = out.get(iid)
        if cur is None:
            out[iid] = {"date": date or "", "title": title or "", "date_source": source if date else "",
                        "president": president or ""}
            return
        if not cur["date"] and date:
            cur["date"], cur["date_source"] = date, source
        if not cur["title"] and title:
            cur["title"] = title
        if not cur["president"] and president:
            cur["president"] = president

    for r in read_csv(os.path.join(root, OFR_CATALOG)):
        put(r.get("id"), r.get("signing_date"), r.get("title"), "ofr_catalog", r.get("president", ""))
    frags = fragments if fragments is not None else load_fragments(root)
    for iid, fs in frags.items():
        for f in fs:
            if f["produced_by"] == "fr-originals":
                put(iid, f["date"], f["title"], "fr-originals")
    for r in read_csv(os.path.join(root, APP_INDEX)):
        put(r.get("instrument_id"), r.get("date"), r.get("title"), "app_index", re.sub(r"\s*\(.*?\)", "", r.get("president", "")))
    for iid, fs in frags.items():
        for f in fs:
            put(iid, f["date"], f["title"], f["produced_by"])
    for r in read_csv(os.path.join(root, WPA_PRE1900)):
        iid = r.get("id") or (canon_id(r["number"], r.get("suffix", "")) if r.get("number") else None)
        md = (r.get("month_day") or "").strip()
        date = None
        if r.get("year"):
            date = parse_date(f"{md}, {r['year']}") if md else None
            date = date.isoformat() if date else r["year"]
        put(iid, date, (r.get("text") or "")[:160], "wpa_pre1900_list")
    for r in load_proquest_rows(root):
        put(canon_id(*parse_eo_id(str(r["id"]))), str(r["y"]) if r.get("y") else None, None, "proquest_list_year")
    for iid, r in load_universe(root).items():
        put(iid, r.get("date_effective") or None, None, "census_year")
    return out


def numbered_timeline(dates):
    """Sorted (date, number) pairs for numbered orders with a full date; for plausibility checks."""
    pairs = []
    for iid, d in dates.items():
        p = parse_eo_id(iid)
        if not p or p[1]:
            continue
        dd = parse_date(d["date"]) if len(d["date"]) >= 10 else None
        if dd:
            pairs.append((dd, p[0]))
    pairs.sort()
    return pairs


def max_number_by(timeline, when, slack_days=60):
    """Largest order number signed by `when` (+ slack), from a numbered_timeline; None if unknown."""
    if not when or not timeline:
        return None
    limit = when + _dt.timedelta(days=slack_days)
    best = None
    for d, n in timeline:
        if d > limit:
            break
        best = n if best is None else max(best, n)
    return best


def iter_texts(fragments, classes=None, max_chars=2_000_000):
    """Yield (instrument_id, fragment, text) for every saved text that exists on this machine."""
    seen = set()
    for iid, fs in fragments.items():
        for f in fs:
            if classes and f["class"] not in classes:
                continue
            p = f["text_path"]
            if not p or p in seen or not os.path.isfile(p):
                continue
            seen.add(p)
            try:
                with open(p, encoding="utf-8", errors="replace") as fh:
                    yield iid, f, fh.read(max_chars)
            except OSError:
                continue


# --- references to executive orders inside prose -------------------------------------------------

_LEAD = r"(?:Executive\s+Orders?|E\.\s?O\.|EO)\s*(?:Nos?\.?|Numbers?|№)?\s*"
# A letter suffix counts only when attached or hyphenated ('325A', '325-A'): OCR of small-caps titles
# spaces out the first letter ('EXECUTIVE ORDER 10728 E stablishing'), which must not read as 10728E.
_NUM = r"(\d{1,2},\d{3}|\d{1,5})(?:[-–]?([A-Z])(?![A-Za-z0-9]))?(?:\s?(½|1/2))?(?![A-Za-z0-9])"
# A later number in a list must not be the volume of a Federal Register, Stat. or CFR cite ('E.O. 9322, 8 F.R. 1').
_NUM_MORE = r"(?!\d{1,5}\s*(?:F\.?\s?R\b|Stat\b|U\.?\s?S\.?\s?C\b|C\.?F\.?R\b|Fed\b|Comp\b))" + _NUM
_SEP = r"(?:\s*,\s*(?:(?:and|or)\s+)?|\s+(?:and|or)\s+)"
_MONTH = (r"(?:January|February|March|April|May|June|July|August|September|October|November|December|"
          r"Jan\.?|Feb\.?|Mar\.?|Apr\.?|Jun\.?|Jul\.?|Aug\.?|Sept?\.?|Oct\.?|Nov\.?|Dec\.?)")
_DATE = r"(?:\s*,?\s*(?:of|dated|signed)?\s*\(?\s*(?P<date>" + _MONTH + r"\s+\d{1,2},?\s+\d{4}))?"
MENTION_RE = re.compile(_LEAD + "(?P<run>" + _NUM + "(?:" + _SEP + _NUM_MORE + ")*)" + _DATE, re.I)
_NUM_RE = re.compile(_NUM)


def parse_prose_date(value):
    """'Sept. 5 1932', 'Mar 3, 1932', 'March 3, 1932' -> date or None."""
    if not value:
        return None
    txt = re.sub(r"\s+", " ", value.strip())
    txt = re.sub(r"^(Sept)\.?", "Sep", txt, flags=re.I).replace(".", "")
    txt = re.sub(r"(\d{1,2}),?\s+(\d{4})$", r"\1, \2", txt)
    return parse_date(txt)
UNNUMBERED_RE = re.compile(
    r"Executive\s+order\s+(?:of|dated)\s+((?:January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+\d{1,2},?\s+\d{4})", re.I)


def find_mentions(text):
    """Every executive-order number named in `text`, with its sentence and any date stated beside it.

    Returns dicts: number, suffix, span (of the whole mention), date (ISO or ''), after (the four
    characters following the number, for OCR checks), quote (the sentence, whitespace squeezed).
    Lists ('Nos. 9001, 9002 and 9005') give one dict per number; '10,000' is one number. A range
    ('9001-9010') is NOT expanded: the second number is read as its own mention.
    """
    out = []
    for m in MENTION_RE.finditer(text):
        d = parse_prose_date(m.group("date"))
        date = d.isoformat() if d else ""
        run_start = m.start("run")
        for n in _NUM_RE.finditer(m.group("run")):
            raw = n.group(1).replace(",", "")
            if raw.startswith("0"):  # '00', '0041': a leading zero is a typesetting or OCR slip, not a number
                continue
            num = int(raw)
            suffix = (n.group(2) or "").upper() or (_HALF if n.group(3) else "")
            after = text[run_start + n.end(): run_start + n.end() + 4]
            out.append({"number": num, "suffix": suffix, "span": m.span(), "date": date,
                        "after": after, "quote": sentence_around(text, m.start(), m.end())})
    return out


def sentence_around(text, start, end, limit=400):
    """The sentence containing [start, end), whitespace squeezed and clipped to `limit` characters."""
    lo = max(0, start - limit)
    hi = min(len(text), end + limit)
    before = text[lo:start]
    after = text[end:hi]
    cut = max(before.rfind(". "), before.rfind("\n\n"))
    before = before[cut + 2:] if cut >= 0 else before
    cut = min([i for i in (after.find(". "), after.find("\n\n")) if i >= 0] or [len(after)])
    after = after[:cut + 1]
    return re.sub(r"\s+", " ", before + text[start:end] + after).strip()[:limit * 2]
