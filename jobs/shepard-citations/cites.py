"""Pure parsing helpers for Shepard: no file, network or repository access.

Everything here turns a piece of text into citation candidates. Nothing is a legal finding:
a relation word found near a citation says only that the word is printed there.
"""
from __future__ import annotations

import datetime as dt
import re

# --- dates --------------------------------------------------------------------------------------

MONTHS = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3, "april": 4, "apr": 4,
    "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7, "august": 8, "aug": 8, "september": 9,
    "sept": 9, "sep": 9, "october": 10, "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12,
}
MONTH_RE = (r"(?:January|February|March|April|May|June|July|August|September|October|November|December|"
            r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept|Sep|Oct|Nov|Dec)\.?")
_UNITS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
          "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
          "seventeen": 17, "eighteen": 18, "nineteen": 19,
          "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8,
          "ninth": 9, "tenth": 10, "eleventh": 11, "twelfth": 12, "thirteenth": 13, "fourteenth": 14,
          "fifteenth": 15, "sixteenth": 16, "seventeenth": 17, "eighteenth": 18, "nineteenth": 19}
_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80,
         "ninety": 90, "twentieth": 20, "thirtieth": 30}
_WORD = r"(?:" + "|".join(sorted(list(_UNITS) + list(_TENS), key=len, reverse=True)) + r")"
SPELLED_NUMBER = _WORD + r"(?:[\s-]+" + _WORD + r")?"
SPELLED_YEAR = r"(?:eighteen|nineteen)\s+hundred(?:\s+and)?(?:\s+" + SPELLED_NUMBER + r")?"
DAY = r"(?:\d{1,2}(?:st|nd|rd|th|d)?|" + SPELLED_NUMBER + r")"
YEAR = r"(?:\d{4}|" + SPELLED_YEAR + r")"
# 'June 6, 1906', 'Nov. 9 1907', 'November nine, nineteen hundred and seven', '6th day of June, 1906'
DATE_ANY = (r"(?:" + MONTH_RE + r"\s+" + DAY + r",?\s+" + YEAR +
            r"|" + DAY + r"\s+(?:day\s+)?of\s+" + MONTH_RE + r",?\s+(?:A\.\s?D\.\s+)?" + YEAR + r")")


def _spelled(value):
    total = 0
    for word in re.split(r"[\s-]+", value.strip().lower()):
        if not word or word == "and":
            continue
        if word in _UNITS:
            total += _UNITS[word]
        elif word in _TENS:
            total += _TENS[word]
        else:
            return None
    return total or None


def _year(value):
    value = value.strip().lower()
    if value.isdigit():
        return int(value)
    m = re.fullmatch(r"(eighteen|nineteen)\s+hundred(?:\s+and)?(?:\s+(.+))?", re.sub(r"\s+", " ", value))
    if not m:
        return None
    base = 1800 if m.group(1) == "eighteen" else 1900
    rest = _spelled(m.group(2)) if m.group(2) else 0
    return None if rest is None else base + rest


def _day(value):
    m = re.fullmatch(r"(\d{1,2})(?:st|nd|rd|th|d)?", value.strip(), re.I)
    return int(m.group(1)) if m else _spelled(value)


def parse_date(text):
    """Any DATE_ANY form -> datetime.date, or None."""
    if not text:
        return None
    t = re.sub(r"\s+", " ", text.strip())
    m = re.fullmatch(r"(" + MONTH_RE + r")\s+(" + DAY + r"),?\s+(" + YEAR + r")", t, re.I)
    if m:
        month, day, year = m.group(1), m.group(2), m.group(3)
    else:
        m = re.fullmatch(r"(" + DAY + r")\s+(?:day\s+)?of\s+(" + MONTH_RE + r"),?\s+(?:A\.\s?D\.\s+)?(" + YEAR + r")",
                         t, re.I)
        if not m:
            return None
        day, month, year = m.group(1), m.group(2), m.group(3)
    mo = MONTHS.get(month.lower().rstrip("."))
    d, y = _day(day), _year(year)
    if not (mo and d and y):
        return None
    try:
        return dt.date(y, mo, d)
    except ValueError:
        return None


# --- relation words -------------------------------------------------------------------------------

# (regex, mechanism). Order matters only for the alternation; the nearest match to a citation wins.
RELATIONS = [
    (r"partial(?:ly)?\s+revo(?:k\w*|cation\w*)", "revocation"),
    (r"revo(?:k\w*|cation\w*)|revoc\w*", "revocation"),
    (r"rescind\w*|rescission\w*", "rescission"),
    (r"supersed\w*|supercede\w*", "supersession"),
    (r"in\s+lieu\s+of", "replacement"),
    (r"modif\w*", "modification"),
    (r"amend\w*", "amendment"),
    (r"restor\w*", "restoration"),
    (r"extend\w*|extension\w*", "extension"),
    (r"correct\w*", "correction"),
    (r"vacat\w*", "vacation"),
    (r"terminat\w*", "termination"),
    (r"abolish\w*", "abolition"),
    (r"suspend\w*|suspension\w*", "suspension"),
    (r"see", "cross_reference"),
]
RELATION_RE = re.compile(r"\b(?:" + "|".join(f"(?P<r{i}>{p})" for i, (p, _) in enumerate(RELATIONS)) + r")\b", re.I)
PARTIAL_RE = re.compile(r"\bin\s+part\b|\bpartial(?:ly)?\b|\binsofar\s+as\b|\bso\s+far\s+as\b", re.I)
# 'as amended by Executive Order No. 5414', 'Amended by PLO No. 956': the cited instrument is the actor.
PASSIVE_BEFORE = re.compile(
    r"\b(?:amended|modified|revoked|superseded|extended|corrected|rescinded|restored|supplemented|continued)"
    r"(?:\s+in\s+part)?\s+by\s*(?:the\s+)?$", re.I)
NEGATION_RE = re.compile(
    r"\bnothing\s+(?:in|herein|contained)\b|\bshall\s+not\s+(?:be\s+)?(?:construed|deemed|affect|revoke|modify|amend)"
    r"|\b(?:is|are)\s+not\s+(?:hereby\s+)?(?:revoked|amended|modified|superseded|rescinded)", re.I)


def relation_matches(segment):
    """[(start, end, mechanism, word)] for every relation word in the segment."""
    out = []
    for m in RELATION_RE.finditer(segment):
        idx = next(i for i in range(len(RELATIONS)) if m.group(f"r{i}") is not None)
        out.append((m.start(), m.end(), RELATIONS[idx][1], re.sub(r"\s+", " ", m.group(0)).lower()))
    return out


def classify(segment, start, end, prefer="before", passive_window=40):
    """Mechanism for a citation at segment[start:end].

    Returns dict: mechanism, words (all relation words in the segment), partial (bool),
    actor_named (the citation follows 'amended by' etc.: the cited instrument acts), negated (bool).
    prefer='before' (tables: 'revoking EO No. 5214') takes the nearest preceding word, then the nearest
    following one; prefer='text' (order texts) first takes a following word introduced by 'hereby'
    ('... is hereby revoked'), then the nearest preceding, then the nearest following one.
    """
    rel = relation_matches(segment)
    words = sorted({w for _, _, _, w in rel})
    before_text = segment[max(0, start - passive_window):start]
    actor_named = bool(PASSIVE_BEFORE.search(before_text))
    chosen = None
    # A word printed right before the citation ('in lieu of Executive Order No. 1304', 'revoking EO No. 5214',
    # 'Revocation of Executive Order No. 4810') governs it, whatever else the sentence says.
    adjacent = [r for r in rel if r[1] <= start and re.fullmatch(r"[\s,;:()]*(?:(?:of|the|in\s+part|partially|to)[\s,;:()]*)*",
                                                                   segment[r[1]:start], re.I)]
    if adjacent:
        chosen = adjacent[-1]
    if chosen is None and prefer == "text":
        after = [r for r in rel if r[0] >= end]
        hereby = [r for r in after if re.search(r"\bhereby\s+(?:\w+\s+){0,2}$", segment[max(end, r[0] - 40):r[0]], re.I)]
        if hereby:
            chosen = hereby[0]
    if chosen is None:
        before = [r for r in rel if r[1] <= start]
        if before:
            chosen = before[-1]
    if chosen is None:
        after = [r for r in rel if r[0] >= end]
        if after:
            chosen = after[0]
    mechanism = chosen[2] if chosen else "cross_reference"
    partial = False
    if chosen:
        lo, hi = (chosen[0], start) if chosen[1] <= start else (end, chosen[1])
        between = segment[min(lo, chosen[0]):max(hi, chosen[1]) + 20]
        partial = bool(PARTIAL_RE.search(between)) or chosen[3].startswith("partial")
    return {"mechanism": mechanism, "word": chosen[3] if chosen else "", "words": words,
            "partial": partial, "actor_named": actor_named, "negated": bool(NEGATION_RE.search(segment))}


# --- citations -----------------------------------------------------------------------------------

_SEP = r"(?:\s*,\s*(?:(?:and|or|&)\s+)?|\s+(?:and|or|&)\s+)"
NUMBER_LIST = r"\d{1,5}(?:[-–]?[A-Z](?![A-Za-z0-9]))?(?:" + _SEP + r"\d{1,5}(?:[-–]?[A-Z](?![A-Za-z0-9]))?)*"
_LEAD = r"(?:\bExecutive\s+Orders?|\bE\.\s?O\.|\bEOs?\b)"
EO_NUMBER_RE = re.compile(_LEAD + r"\s*\(?\s*(?:Nos?\.?|Numbers?|Numbered)?\s*(?P<nums>" + NUMBER_LIST + r")\s*\)?"
                          r"(?:\s*,?\s*(?:of|dated)\s+(?P<date>" + DATE_ANY + r"))?", re.I)
DATE_CHAIN = r"(?P<dates>" + DATE_ANY + r"(?:\s*,?\s*(?:and|or|&)?\s*" + DATE_ANY + r")*)"
EO_DATE_RE = re.compile(
    r"(?:" + _LEAD + r"|\bPresident'?s?\s+[Oo]rders?|\b[Oo]rders?\s+of\s+the\s+President)\s*(?:,\s*)?"
    r"(?:of|dated|signed|issued|made)\s+(?:on\s+)?(?:the\s+)?" + DATE_CHAIN, re.I)
_SINGLE_DATE = re.compile(DATE_ANY, re.I)
PLO_RE = re.compile(r"(?:\bPLOs?|\bP\.\s?L\.\s?O\.|\bPublic\s+Land\s+Orders?)\s*(?:Nos?\.?)?\s*(?P<nums>" + NUMBER_LIST + r")",
                    re.I)
PROC_RE = re.compile(r"\bProc(?:lamation)?s?\.?\s*(?:Nos?\.?)?\s*(?P<nums>" + NUMBER_LIST + r")", re.I)
RESERVES = [
    (r"Power[\s-]*Site\s+Reserve|Powersite\s+Reserve", "PSR", "Power Site Reserve"),
    (r"Public\s+Water\s+Reserve", "PWR", "Public Water Reserve"),
    (r"Reservoir\s+Site\s+Reserve", "RSR", "Reservoir Site Reserve"),
    (r"Stock\s+Driveway\s+Withdrawal", "SDW", "Stock Driveway Withdrawal"),
    (r"Air\s+Navigation\s+Site\s+Withdrawal", "ANSW", "Air Navigation Site Withdrawal"),
    (r"Naval\s+Petroleum\s+Reserve", "NPR", "Naval Petroleum Reserve"),
    (r"Naval\s+Oil\s+Shale\s+Reserve", "NOSR", "Naval Oil Shale Reserve"),
    (r"Phosphate\s+Reserve", "PHR", "Phosphate Reserve"),
    (r"Petroleum\s+Reserve", "PR", "Petroleum Reserve"),
]
RESERVE_RE = re.compile(r"\b(?:" + "|".join(f"(?P<k{i}>{p})" for i, (p, _, _) in enumerate(RESERVES)) +
                        r")\s*(?:No\.?|Number)\s*(?P<num>\d{1,4})\b", re.I)


def numbers_in(run):
    """'7185, 7212, 7452 and 8331' -> [('7185',''), ...]; '325-A' -> ('325','A')."""
    out = []
    for m in re.finditer(r"(\d{1,5})(?:[-–]?([A-Z])(?![A-Za-z0-9]))?", run):
        if m.group(1).startswith("0"):
            continue
        out.append((m.group(1), (m.group(2) or "").upper()))
    return out


def eo_number_mentions(text):
    """[(start, end, number, suffix, stated_date or None)] for 'Executive Order No. 6910', 'EO Nos. 1, 2 and 3'."""
    out = []
    for m in EO_NUMBER_RE.finditer(text):
        d = parse_date(m.group("date")) if m.group("date") else None
        nums = numbers_in(m.group("nums"))
        for i, (n, s) in enumerate(nums):
            out.append((m.start(), m.end(), n, s, d if i == len(nums) - 1 else None))
    return out


def eo_date_mentions(text):
    """[(start, end, date, phrase)] for 'Executive order of June 6, 1906' (and date lists after it)."""
    out = []
    for m in EO_DATE_RE.finditer(text):
        for dm in _SINGLE_DATE.finditer(m.group("dates")):
            d = parse_date(dm.group(0))
            if d:
                out.append((m.start(), m.end(), d, re.sub(r"\s+", " ", m.group(0))))
    return out


def reserve_mentions(text):
    """[(start, end, kind_code, number, phrase)] for 'Power Site Reserve No. 325'."""
    out = []
    for m in RESERVE_RE.finditer(text):
        idx = next(i for i in range(len(RESERVES)) if m.group(f"k{i}") is not None)
        out.append((m.start(), m.end(), RESERVES[idx][1], int(m.group("num")), re.sub(r"\s+", " ", m.group(0))))
    return out


def plo_mentions(text):
    out = []
    for m in PLO_RE.finditer(text):
        for n, _ in numbers_in(m.group("nums")):
            out.append((m.start(), m.end(), int(n)))
    return out


_SENT_END = re.compile(r"(?<!\bNo)(?<!\bNos)(?<!\bSec)(?<![A-Z])(?<!\b[A-Z][a-z])(?<!\b[A-Z][a-z][a-z])(?<!\bSept)"
                       r"\.\s+(?=[A-Z\[(])|\n\s*\n")


def sentence_bounds(text, start, end, limit=600):
    """(lo, hi) of the sentence holding text[start:end]; '. ' followed by a capital, or a blank line, ends one.

    Abbreviation periods ('No. 6910', 'Feb. 4', 'Sec. 2', 'U.S.') do not end a sentence."""
    lo = max(0, start - limit)
    hi = min(len(text), end + limit)
    s = lo
    for m in _SENT_END.finditer(text, lo, min(len(text), start + 1)):
        if m.end() <= start:
            s = m.end()
    m = _SENT_END.search(text, end, hi)
    e = m.start() + 1 if m else hi
    return s, e


def squeeze(text):
    return re.sub(r"\s+", " ", text).strip()


# --- BLM Public Land Order tables ---------------------------------------------------------------

FR_RE = re.compile(r"(?P<vol>\d{1,3})\s*F\.?\s?R\.?\s*(?P<page>\d{1,6})(?:\s*[–-]\s*(?P<end>\d{1,6}))?")
PLO_START = re.compile(r"^\s*(?P<num>\d{1,4})\s+(?:[.\s]{0,8})?(?P<date>" + MONTH_RE + r"\s+\d{1,2},?\s*\d{4})\b(?P<rest>.*)$")
TABLE_NOISE = re.compile(
    r"^\s*(?:Table\s+of\s+Public\s+Land\s+Orders.*|PLO\s*(?:No\.?)?\s*$|(?:PLO\s+)?No\.\s+Signature\s+Date.*|"
    r"EDITORIAL\s+NOTE.*|Signature\s+Date\s+Subject.*)$", re.I)


def _paren_depths(text):
    depth, out = 0, []
    for ch in text:
        if ch == "(":
            depth += 1
        out.append(depth)
        if ch == ")":
            depth = max(0, depth - 1)
    return out


def _longest_increasing(values):
    """Indices of one longest strictly increasing subsequence of values (patience sorting)."""
    import bisect
    tails, tails_idx, prev = [], [], [-1] * len(values)
    for i, v in enumerate(values):
        k = bisect.bisect_left(tails, v)
        if k == len(tails):
            tails.append(v)
            tails_idx.append(i)
        else:
            tails[k] = v
            tails_idx[k] = i
        prev[i] = tails_idx[k - 1] if k else -1
    out, i = [], tails_idx[-1] if tails_idx else -1
    while i >= 0:
        out.append(i)
        i = prev[i]
    return out[::-1]


def parse_plo_table(pages, lo=None, hi=None):
    """Rows of one BLM 'Table of Public Land Orders' from its per-page text.

    pages: list of page texts (index = PDF page - 1). lo/hi: the PLO number range the file covers.
    Each row: number, date (ISO), date_raw, subject, fr_citation, fr_volume, fr_page, pdf_page, flags, raw.
    Candidate row starts are lines opening with a number and a signature date; the longest run of candidates whose
    numbers rise is kept, so a wrapped subject line that happens to start with a number and a date cannot cut the
    table, and a gap in the numbering does not stop the parse.
    """
    lines = []
    for pi, page in enumerate(pages):
        plines = [ln for ln in page.splitlines() if ln.strip()]
        for li, line in enumerate(plines):
            if TABLE_NOISE.match(line):
                continue
            nxt = plines[li + 1] if li + 1 < len(plines) else ""
            if ((li == 0 or li == len(plines) - 1) and re.fullmatch(r"\s*\d{1,3}\s*", line)
                    and not re.match(r"\s*" + MONTH_RE + r"\s+\d", nxt)):
                continue  # printed page number
            lines.append((pi + 1, line))
    # A text layer may put the number and the date on separate lines ('936' / 'Feb. 4, 1954 ...'): join them.
    joined = []
    for i, (pdf_page, line) in enumerate(lines):
        if (joined and re.fullmatch(r"\s*\d{1,4}\s*", joined[-1][1]) and re.match(r"\s*" + MONTH_RE + r"\s+\d{1,2},?\s*\d{4}", line)):
            joined[-1] = (joined[-1][0], joined[-1][1].strip() + " " + line)
        else:
            joined.append((pdf_page, line))
    lines = joined
    cands = []
    for idx, (pdf_page, line) in enumerate(lines):
        m = PLO_START.match(line)
        if not m:
            continue
        n = int(m.group("num"))
        if (lo is not None and n < lo) or (hi is not None and n > hi) or not parse_date(m.group("date")):
            continue
        cands.append((idx, n, m))
    chosen = [cands[i] for i in _longest_increasing([n for _, n, _ in cands])]
    records = []
    for k, (idx, n, m) in enumerate(chosen):
        stop = chosen[k + 1][0] if k + 1 < len(chosen) else len(lines)
        records.append({"number": n, "date_raw": squeeze(m.group("date")), "pdf_page": lines[idx][0],
                        "lines": [m.group("rest")] + [ln for _, ln in lines[idx + 1:stop]]})
    rows = []
    for r in records:
        rest = squeeze(" ".join(r["lines"]))
        rest = re.sub(r"^[.\s]+", "", rest)
        depths = _paren_depths(rest)
        cites = [m for m in FR_RE.finditer(rest) if depths[m.start()] == 0]
        flags = []
        fr = cites[-1] if cites else None
        if fr is None:
            flags.append("fr_citation_not_found")
            subject = rest
        else:
            subject = squeeze(rest[:fr.start()] + " " + rest[fr.end():])
            if len(cites) > 1:
                flags.append("several_unbracketed_fr_citations_last_taken")
        subject = re.sub(r"(?:\s*\.){2,}\s*", " ", subject).strip(" .")
        d = parse_date(r["date_raw"])
        rows.append({"number": r["number"], "date": d.isoformat() if d else "", "date_raw": r["date_raw"],
                     "subject": subject, "fr_citation": squeeze(fr.group(0)) if fr else "",
                     "fr_volume": int(fr.group("vol")) if fr else "", "fr_page": int(fr.group("page")) if fr else "",
                     "pdf_page": r["pdf_page"], "flags": flags, "raw": squeeze(r["date_raw"] + " " + rest)})
    return rows


def plo_subject_refs(subject):
    """Citations inside one PLO subject heading.

    Returns a list of dicts: kind ('eo_number' | 'eo_date' | 'plo' | 'reserve' | 'proc'), value, stated_date,
    start, end, and the classify() result for the ';'-clause holding it ('revoking EO No. 5214 of Oct. 30, 1929').
    """
    refs = []
    clauses, pos = [], 0
    for part in re.split(r"(;)", subject):
        if part != ";":
            clauses.append((pos, part))
        pos += len(part)

    def clause_of(start):
        for cpos, ctext in clauses:
            if cpos <= start < cpos + len(ctext) + 1:
                return cpos, ctext
        return 0, subject

    def add(kind, value, start, end, stated=None, extra=None):
        cpos, ctext = clause_of(start)
        c = classify(ctext, start - cpos, end - cpos, prefer="before")
        row = {"kind": kind, "value": value, "stated_date": stated.isoformat() if stated else "",
               "start": start, "end": end, "clause": ctext.strip(), **c}
        if extra:
            row.update(extra)
        refs.append(row)

    for s, e, n, suf, d in eo_number_mentions(subject):
        add("eo_number", n + suf, s, e, d)
    for s, e, d, phrase in eo_date_mentions(subject):
        add("eo_date", d.isoformat(), s, e, d, {"phrase": phrase})
    for s, e, n in plo_mentions(subject):
        add("plo", n, s, e)
    for s, e, code, n, phrase in reserve_mentions(subject):
        add("reserve", f"{code}:{n}", s, e, None, {"phrase": phrase})
    for m in PROC_RE.finditer(subject):
        for n, _ in numbers_in(m.group("nums")):
            add("proc", n, m.start(), m.end())
    refs.sort(key=lambda r: (r["start"], r["kind"], str(r["value"])))
    return refs


# --- Federal Register daily contents ('Codification guide') ---------------------------------------

SECTION_RE = re.compile(
    r"\(\s*(?P<eo>Executive\s+orders?)\s*\)|\(\s*(?P<plo>Public\s+land\s+orders?)\s*\)|\(\s*(?P<proc>Proclamations?)\s*\)"
    r"|(?P<eo2>Executive\s+orders?)\s*:|(?P<plo2>Public\s+land\s+orders?)\s*:|(?P<proc2>Proclamations?)\s*:"
    r"|(?P<reset>\bTitle\s+\d{1,2}\b|\b\d{1,2}\s+CFR\b)", re.I)
CONTENTS_REL = re.compile(r"see|revok|revoc|amend|modif|correct|supersed|supplement|extend|restor|vacat|terminat", re.I)
ENTRY_RE = re.compile(
    r"(?<![\w.,/])(?P<num>\d{1,5}[A-Z]?)\s*\(\s*(?P<rel>[A-Za-z][A-Za-z ,;.]{0,40}?)\s*"
    r"(?P<kind>P\.?\s?L\.?\s?O\.?|E\.?\s?O\.?|Proc\.?|Public\s+Land\s+Order)\s*"
    r"(?P<nums>\d{1,5}(?:\s*[;,]\s*(?:and\s+)?\d{1,5})*)\s*[-]?\s*\)")
PAGE_AFTER = re.compile(r"[\s_.\-—–~*>|^:;,'`\"]*?(?P<page>\d(?: \d){2,4}(?!\d)|\d{1,5}(?!\d))")
PLAIN_ENTRY_RE = re.compile(r"(?<![\w.(/])(?P<num>\d{1,5}[A-Z]?)\s*[_.\-—–~*]{2,}[\s_.\-—–~*>|^]*(?P<page>\d(?: \d){2,4}(?!\d)|\d{1,5}(?!\d))")
PDF_PAGE_RE = re.compile(r"^=== PDF page (\d+) of (\d+)", re.M)


def _kind_of(raw):
    k = raw.lower().replace(" ", "").replace(".", "")
    if k.startswith("plo") or k.startswith("publicland"):
        return "PLO"
    if k.startswith("eo"):
        return "EO"
    return "PROC"


def contents_entries(text):
    """Entries such as '4872 (revoked by PLO 4620) ..... 6689' in a Federal Register codification guide.

    Returns (entries, page_index). entries: dicts section ('EO'|'PLO'|'PROC'), number, rel, acting_kind,
    acting_numbers, page (int or None), pdf_page, raw, pos. page_index: {(kind, number): printed page} from
    plain entries such as '949 ______ 1807'. Only text after a recognised section heading is read.
    """
    pages = []
    marks = list(PDF_PAGE_RE.finditer(text))
    if marks:
        for i, m in enumerate(marks):
            end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
            pages.append((int(m.group(1)), text[m.end():end]))
    else:
        pages.append((None, text))
    section, entries, page_index = None, [], {}
    for pdf_page, ptext in pages:
        flat = re.sub(r"\s+", " ", ptext)
        events = [(m.start(), "section", m) for m in SECTION_RE.finditer(flat)]
        events += [(m.start(), "entry", m) for m in ENTRY_RE.finditer(flat)]
        events += [(m.start(), "plain", m) for m in PLAIN_ENTRY_RE.finditer(flat)]
        events.sort(key=lambda e: (e[0], e[1] != "section"))
        consumed_until = -1
        for pos, what, m in events:
            if what == "section":
                if m.group("reset"):
                    section = None
                else:
                    section = "EO" if (m.group("eo") or m.group("eo2")) else "PLO" if (m.group("plo") or m.group("plo2")) else "PROC"
                continue
            if section is None or pos < consumed_until:
                continue
            if what == "entry":
                if not CONTENTS_REL.search(m.group("rel")):
                    continue
                page, tail = None, flat[m.end():m.end() + 60]
                pm = PAGE_AFTER.match(tail)
                if pm:
                    after = tail[pm.end():pm.end() + 3].lstrip()
                    # A number followed by a leader or '(' is the next entry's number, not this entry's page.
                    if not (after[:1] in ("_", ".", "(", "—", "-", "–") and not after.startswith(". ")):
                        page = int(pm.group("page").replace(" ", ""))
                entries.append({"section": section, "number": m.group("num").upper(), "rel": squeeze(m.group("rel")),
                                "acting_kind": _kind_of(m.group("kind")),
                                "acting_numbers": [int(x) for x in re.findall(r"\d{1,5}", m.group("nums"))],
                                "page": page, "pdf_page": pdf_page, "raw": squeeze(m.group(0) + flat[m.end():m.end() + 30]),
                                "pos": pos})
                consumed_until = m.end()
            elif what == "plain":
                page_index.setdefault((section, m.group("num").upper()), int(m.group("page").replace(" ", "")))
    return entries, page_index


# --- Wikisource 'Notes' sections (editorial cross-references printed under each order) -------------------

WS_HEADINGS = [
    (r"revoked\s*\(?in\s+part\)?\s*by", "revocation", True, True), (r"revoked\s+by", "revocation", False, True),
    (r"revokes\s*\(?in\s+part\)?", "revocation", True, False), (r"revokes", "revocation", False, False),
    (r"amended\s+by", "amendment", False, True), (r"amends\s*\(?in\s+part\)?", "amendment", True, False),
    (r"amends", "amendment", False, False), (r"superseded\s+by", "supersession", False, True),
    (r"supersedes", "supersession", False, False), (r"modified\s+by", "modification", False, True),
    (r"modifies", "modification", False, False), (r"supplemented\s+by", "supplementation", False, True),
    (r"supplements", "supplementation", False, False), (r"see\s+related|see\s+also|related", "cross_reference", False, False),
]
WS_HEADING_RE = re.compile(r"^\s*(?:" + "|".join(f"(?P<h{i}>{p})" for i, (p, _, _, _) in enumerate(WS_HEADINGS)) + r")\s*:?\s*$", re.I)
WS_ITEM_RE = re.compile(r"^\s*(?P<kind>Executive\s+Order|Public\s+Land\s+Order|Proclamation)\s+(?:No\.\s*)?(?P<num>\d{1,5})(?P<suf>-?[A-Z])?\b"
                        r"(?:\s*,\s*(?P<date>" + MONTH_RE + r"\s+\d{1,2},?\s+\d{4}))?", re.I)


def wikisource_parts(text):
    """(body, body_offset, notes) of a saved Wikisource page: the order's own text without the navigation header
    and footer, and its 'Notes' items as (mechanism, partial, item_is_actor, kind, number, suffix, date, line, offset)."""
    start = 0
    m = re.search(r"\n\s*\u2192\s*\n", text[:3000])
    if m:
        start = m.end()
    end = len(text)
    for marker in ("\nNotes\n", "This work is in the public domain", "Retrieved from \""):
        i = text.find(marker, start)
        if i >= 0:
            end = min(end, i)
    notes = []
    n = text.find("\nNotes\n", start)
    if n >= 0:
        stop = text.find("This work is in the public domain", n)
        block = text[n:stop if stop > 0 else n + 6000]
        heading = None
        pos = n
        for line in block.splitlines(True):
            hm = WS_HEADING_RE.match(line)
            if hm:
                idx = next(i for i in range(len(WS_HEADINGS)) if hm.group(f"h{i}") is not None)
                heading = WS_HEADINGS[idx]
            else:
                im = WS_ITEM_RE.match(line)
                if im and heading:
                    kind = {"e": "EO", "p": "PLO" if im.group("kind").lower().startswith("public") else "PROC"}[im.group("kind")[0].lower()]
                    d = parse_date(im.group("date")) if im.group("date") else None
                    notes.append((heading[1], heading[2], heading[3], kind, im.group("num"),
                                  (im.group("suf") or "").replace("-", "").upper(), d, line.strip(), pos))
            pos += len(line)
    return text[start:end], start, notes
