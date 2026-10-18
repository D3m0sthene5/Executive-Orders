"""Split *Executive Orders Relating to Indian Reservations, from May 14, 1855 to July 1, 1912* (GPO 1912)
into one text per presidential act, and compare the acts with the census and the two WPA lists.

The job reads the committed text layer of the scan (data/ir1912_pages.jsonl), never the network.
The book is arranged by state, then by reservation. Under each reservation heading it prints the
departmental letters that led to an order, then the order itself ("Executive Mansion, April 28,
1875." ... "U. S. Grant."), or a President's indorsement on a letter ("Let the lands be withdrawn
as recommended. Andrew Johnson."), or a proclamation. Orders carry no numbers in this book.

An act ends at a President's signature. It starts after the previous act (or at the reservation
heading). Notes, countersignatures and referrals printed after a signature belong to that act.
Its date comes, in order, from a proclamation's "Done at ... this ... day of" clause, the last
"Executive Mansion, <date>" / "White House, <date>" header, a date printed right after the
signature, or (indorsements only) the last standalone dateline before the signature. OCR-damaged
digits are repaired only when exactly one reading falls inside the signer's term.

Machine leads only: nothing here admits, merges, dates or changes a census identity or a status.
"""

import collections
import csv
import difflib
import hashlib
import itertools
import json
import os
import pathlib
import re

BODY = (16, 237)   # PDF pages holding the documents (the index starts at PDF 238)
OFFSET = 13        # printed page = PDF page - 13 in the body

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]
ABBR = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9,
        "oct": 10, "nov": 11, "dec": 12}

PRES = {
    "PIERCE": ["FRANKLIN PIERCE"], "BUCHANAN": ["JAMES BUCHANAN"],
    "LINCOLN": ["A LINCOLN", "ABRAHAM LINCOLN"], "JOHNSON": ["ANDREW JOHNSON"],
    "GRANT": ["U S GRANT"], "HAYES": ["R B HAYES", "RUTHERFORD B HAYES"],
    "GARFIELD": ["JAMES A GARFIELD", "J A GARFIELD"], "ARTHUR": ["CHESTER A ARTHUR", "C A ARTHUR"],
    "CLEVELAND": ["GROVER CLEVELAND"], "HARRISON": ["BENJ HARRISON", "BENJAMIN HARRISON"],
    "MCKINLEY": ["WILLIAM MCKINLEY", "WM MCKINLEY"], "ROOSEVELT": ["THEODORE ROOSEVELT", "T ROOSEVELT"],
    "TAFT": ["WM H TAFT", "WILLIAM H TAFT"],
}
# First and last day each President could sign (Cleveland's two terms are treated as one span).
TERMS = {
    "PIERCE": ("1853-03-04", "1857-03-04"), "BUCHANAN": ("1857-03-04", "1861-03-04"),
    "LINCOLN": ("1861-03-04", "1865-04-15"), "JOHNSON": ("1865-04-15", "1869-03-04"),
    "GRANT": ("1869-03-04", "1877-03-04"), "HAYES": ("1877-03-04", "1881-03-04"),
    "GARFIELD": ("1881-03-04", "1881-09-19"), "ARTHUR": ("1881-09-19", "1885-03-04"),
    "CLEVELAND": ("1885-03-04", "1897-03-04"), "HARRISON": ("1889-03-04", "1893-03-04"),
    "MCKINLEY": ("1897-03-04", "1901-09-14"), "ROOSEVELT": ("1901-09-14", "1909-03-04"),
    "TAFT": ("1909-03-04", "1913-03-04")}
NOT_PRESIDENT = {"ROBERT T LINCOLN", "SMITH AND JOHNSON"}   # Secretary of War (pp. 141-142); "Messrs. Smith and Johnson."
CONF = str.maketrans({"E": "R", "B": "R", "K": "R", "0": "O", "1": "I", "L": "I"})   # OCR confuses R/E/B/K
# What a misread digit glyph may stand for.
DIG = {"0": "0", "1": "1", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7", "8": "8", "9": "9",
       "O": "0", "o": "0", "D": "0", "Q": "0", "I": "1", "l": "1", "i": "1", "J": "1", "]": "1", "t": "1", "|": "1",
       "S": "538", "s": "5", "B": "82", "&": "8", "£": "2", "%": "2", "Z": "2", "z": "2", "k": "4", "h": "4",
       "A": "4", "^": "0123456789", "?": "0123456789", "fl": "8", "g": "9", "q": "9", "G": "6", "b": "6",
       "T": "7", "H": "4", "W": "0123456789", "M": "0123456789", "}": "0123456789", "Ii": "4", "IB": "18",
       "j": "1", "U": "0", "u": "0", "e": "6", "n": "1", "x": "0123456789", "f": "1", "r": "1"}

STATES = ["ARIZONA", "CALIFORNIA", "COLORADO", "FLORIDA", "IDAHO", "MICHIGAN", "MINNESOTA", "MONTANA",
          "NEBRASKA", "NEVADA", "NEW MEXICO", "NORTH DAKOTA", "OKLAHOMA", "OREGON", "SOUTH DAKOTA", "UTAH",
          "WASHINGTON", "WISCONSIN", "WYOMING"]
STATE_PAT = {
    "ARIZONA": r"Ariz|Arizona", "CALIFORNIA": r"Calif|California|\bCal\.", "COLORADO": r"Colo\b|Colorado",
    "FLORIDA": r"Fla\b|Florida", "IDAHO": r"Idaho", "MICHIGAN": r"Mich\b|Michigan", "MINNESOTA": r"Minn\b|Minnesota",
    "MONTANA": r"Mont\b|Montana", "NEBRASKA": r"Nebr\b|Nebraska", "NEVADA": r"Nev\b|Nevada",
    "NEW MEXICO": r"N\.\s*Mex|New Mexico", "NORTH DAKOTA": r"N\.\s*Dak|North Dakota", "OKLAHOMA": r"Okla|Oklahoma",
    "OREGON": r"Oreg|Oregon", "SOUTH DAKOTA": r"S\.\s*Dak|South Dakota", "UTAH": r"Utah",
    "WASHINGTON": r"Wash\b|Washington(?!,\s*D)", "WISCONSIN": r"Wis\b|Wisconsin", "WYOMING": r"Wyo\b|Wyoming"}
NAVAJO_STATES = {"ARIZONA", "NEW MEXICO", "UTAH"}   # may be named together without penalty

GPO_MARK = re.compile(r"^\s*5\S{1,3}43\s*°")            # "57643°—12 2", "5T643°", "57fi43°— 12"
IR_NUM = re.compile(r"(?<![A-Za-z0-9])[I1l]R\s*(\d{1,3})")   # WPA numbered list: "IR 22", OCR "1R 127"
FOREST = re.compile(r"([A-Z][a-z]{3,})\s*National\s+Forest")
IR_LORD = re.compile(r"\b([IV]{1,3}|1|l)\s*IR\s*\.?\s*((?:\d{1,3}\s*,\s*)*\d{1,3})")   # Lord: "I IR 24, 25"


# ---------------------------------------------------------------- reading dates

def glyph_readings(tok):
    """Every digit string a short OCR token could stand for ("1&55" -> ["1855"])."""
    tok = tok.strip(" .,;:'`-~*")
    if not tok or len(tok) > 5:
        return []
    parts, i = [], 0
    while i < len(tok):
        if len(tok[i:i + 2]) == 2 and tok[i:i + 2] in DIG:
            parts.append(DIG[tok[i:i + 2]])
            i += 2
            continue
        if tok[i] not in DIG:
            return []
        parts.append(DIG[tok[i]])
        i += 1
    return ["".join(p) for p in itertools.product(*parts)][:5000]


def month_of(word):
    """Month number of an OCR-damaged month word ("Decemher", "Felruary", "AtJGTTST"), else None."""
    w = re.sub(r"[^A-Za-z]", "", word)
    if w.isupper() and len(w) > 4:
        w = re.sub(r"TJ|IJ|TT(?=S)", "U", w)    # all-caps OCR: "AtJGTTST" -> "AUGUST"
    w = re.sub(r"(?i)tj", "u", w).lower()
    if len(w) < 3:
        return None
    if w[:3] in ABBR and (len(w) <= 4 or difflib.SequenceMatcher(None, w, MONTHS[ABBR[w[:3]] - 1].lower()).ratio() > 0.6):
        return ABBR[w[:3]]
    best = difflib.get_close_matches(w, [m.lower() for m in MONTHS], 1, 0.62)
    return MONTHS.index(best[0].capitalize()) + 1 if best else None


def read_date(text, term=None):
    """First date in text as (year, month, day, raw, repaired); day may be "". With a signer's term,
    damaged digits are kept only when exactly one reading lies inside the term."""
    text = re.sub(r"\b([A-Z]),(?=[a-z]{2})", r"\1", text)   # "D,ec. 13" -> "Dec. 13"
    toks = [t for t in re.split(r"[\s,;]+", text) if t and re.search(r"[A-Za-z0-9^&£%?}\]|]", t)]
    for k, tok in enumerate(toks):
        mo = month_of(tok)
        if not mo or k + 1 >= len(toks):
            continue
        day_tok = toks[k + 1].strip(".")
        if re.fullmatch(r"\d{1,2}(st|d|nd|rd|th)", day_tok):
            day_tok = re.sub(r"\D", "", day_tok)
        year_tok = toks[k + 2].strip(".-'\"") if k + 2 < len(toks) else ""
        if re.fullmatch(r"\S{1,3}\.\S{4}", day_tok):          # "1.1911"
            day_tok, year_tok = day_tok.split(".")
        years = [y for y in glyph_readings(year_tok) if len(y) == 4 and y[:2] in ("18", "19")]
        if not years and re.fullmatch(r"13\d\d", year_tok):   # "1375" for 187x
            years = ["18" + year_tok[2:]]
        if not years:
            continue
        days = [d for d in glyph_readings(day_tok) if len(d) <= 2 and 1 <= int(d) <= 31]
        cands = [(y, d) for y in years for d in (days or [""])]
        if term:
            lo, hi = term
            keep = [(y, d) for y, d in cands
                    if lo[:4] <= y <= hi[:4] and (not d or lo <= f"{y}-{mo:02d}-{int(d):02d}" <= hi)]
            cands = keep or cands
        ys = sorted({y for y, _ in cands})
        ds = sorted({d for _, d in cands})
        if len(ys) != 1:
            continue
        d = str(int(ds[0])) if len(ds) == 1 and ds[0] else ""
        literal = bool(re.fullmatch(r"1[89]\d\d", year_tok)) and bool(re.fullmatch(r"\d{1,2}", day_tok))
        return ys[0], mo, d, " ".join(toks[k:k + 3]), not literal
    return None


def header_date(line, next_line, term=None):
    """The date of an 'Executive Mansion, <date>' header. The next line is used only to finish a
    date that wraps ('Executive Mansion, August' / '9,1879.'), never to borrow a date from the text."""
    d = read_date(line, term)
    if d:
        return d
    if re.match(r"(?i)\W*washin", next_line):   # 'Executive Mansion,' / 'Washington, D. C., May 17, 1884.'
        return read_date(next_line, term)
    d = read_date(line + " " + " ".join(next_line.split()[:3]), term)
    tail = line.split()[-3:] + next_line.split()[:1]   # the month ends the header line or starts the next
    if d and d[3].split()[0] in tail + [w.strip(",.") for w in tail]:
        return d
    return None


WORDNUM = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8,
           "ninth": 9, "tenth": 10, "eleventh": 11, "twelfth": 12, "thirteenth": 13, "fourteenth": 14,
           "fifteenth": 15, "sixteenth": 16, "seventeenth": 17, "eighteenth": 18, "nineteenth": 19,
           "twentieth": 20, "thirtieth": 30}
UNITS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
         "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
         "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
         "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}


def proclamation_date(text):
    """'Done at the city of Washington this 29th day of May, in the year of our Lord one thousand
    nine hundred and two' -> ("1902", 5, "29", raw, False)."""
    t = re.sub(r"-\s*\n\s*", "", text)
    t = re.sub(r"\s+", " ", t)
    m = re.search(r"(?i)this\s+(?P<day>[\w-]+(?:[ -][\w]+)?)\s+day\s+of\s+(?P<mon>\w+)\s*,?\s*in\s+the\s+year\s+of\s+"
                  r"our\s+Lord\s+(?P<yr>[a-z -]+?)(?:,|\s+and\s+of\s+the)", t)
    if not m:
        return None
    mo = month_of(m.group("mon"))
    dtxt = m.group("day").lower().replace("-", " ")
    dd = re.match(r"(\d{1,2})", dtxt)
    day = int(dd.group(1)) if dd else (sum(WORDNUM.get(w, UNITS.get(w, 0)) for w in dtxt.split()) or None)
    total, cur = 0, 0
    for w in m.group("yr").lower().replace("-", " ").split():
        if w == "thousand":
            total, cur = total + (cur or 1) * 1000, 0
        elif w == "hundred":
            cur = (cur or 1) * 100
        elif w in UNITS:
            cur += UNITS[w]
    year = total + cur
    if not mo or not 1850 < year < 1913:
        return None
    return str(year), mo, str(day) if day else "", m.group(0)[:80], False


def iso(y, mo, d):
    if y and mo and d:
        return f"{y}-{mo:02d}-{int(d):02d}"
    return f"{y}-{mo:02d}" if y and mo else (y or "")


# ---------------------------------------------------------------- recognising lines

def is_running_head(line):
    """'EXECUTIVE OEDEES EELATING TO INDIAN EESEEVATIONS. 5' and other OCR forms of the running head."""
    s = re.sub(r"^\W*\S{0,4}\d\S{0,2}\s+|\s+\S{0,2}\d\S{0,3}\W*$", "", line.strip())
    if len(s) > 85 or len(s) < 20:
        return False
    return difflib.SequenceMatcher(None, s.upper(), "EXECUTIVE ORDERS RELATING TO INDIAN RESERVATIONS.").ratio() > 0.6


def is_header(line):
    """'Executive Mansion, <date>' or '(The) White House, <date>' at the start of a line, OCR-tolerant.
    The first two words are checked letter by letter, so 'Chief Moses' and 'Executive action' fail."""
    raw = line.split()
    while raw and not re.search(r"[A-Za-z0-9]", raw[0]):   # ", The White House" / ". The White House"
        raw = raw[1:]
    if not raw or re.match(r"\W*\d", raw[0]):                  # running text: "28, 1856, which he refers to"
        return False
    w = [re.sub(r"[^A-Za-z]", "", t).upper() for t in re.split(r"[\s,.]+", " ".join(raw))[:4]]
    w = [t for t in w if t]
    if w and w[0] in ("G", "I", "J"):     # a stray glyph before the header: "g . Executive MAijfsiON"
        w = w[1:]
    if w and w[0] in ("THE", "THU"):
        w = w[1:]
    if len(w) >= 2:
        if (w[0][:1] in "EF" and w[1][:1] == "M" and difflib.SequenceMatcher(None, w[0], "EXECUTIVE").ratio() >= 0.55
                and difflib.SequenceMatcher(None, w[1], "MANSION").ratio() >= 0.7):
            return True
        if w[0][:2] == "WH" and w[1][:1] == "H" and len(w[1]) >= 4 and difflib.SequenceMatcher(None, w[1], "HOUSE").ratio() >= 0.5:
            return True
    joined = re.sub(r"[^A-Za-z]", "", line)[:18].upper()
    return joined[9:10] == "M" and difflib.SequenceMatcher(None, joined[:16], "EXECUTIVEMANSION").ratio() >= 0.8


def _words(s):
    s = re.sub(r"\[[^\]]*\]", " ", s)
    return re.sub(r"[^A-Z ]", "", re.sub(r"[.,\-]", " ", s.upper())).split()


def is_signature(line):
    """(president, glued_date_text, score) when the line is, or ends with, a President's signature."""
    s = line.strip()
    if not s or len(s) > 140:
        return None
    tail = ""
    m = re.search(r"\.\s*((?:Jan|Feb|Mar|Apr|May|June|July|Aug|Sep|Oct|Nov|Dec)\w*\.?\s+\S{1,3},?\s+\S{4}\.?)\s*$", s)
    if m:   # a date glued after the name: "A. Lincoln.April 16, 1864."
        tail, s = m.group(1), s[:m.start() + 1]
    s = re.sub(r",\s*President\.?\s*$", ".", s)
    s = re.sub(r"\[\s*seal\s*\.?\s*\]", " ", s, flags=re.I).strip()
    compact = re.sub(r"[^A-Z]", "", s.upper().replace("1", "L").replace("0", "O"))
    compact = re.sub(r"^(IT|TJ|IJ|LJ|II)S", "US", compact)   # "IT. S. Grant." -> US GRANT
    if 6 <= len(compact) <= 22 and compact not in {x.replace(" ", "") for x in NOT_PRESIDENT}:
        for p, variants in PRES.items():
            for v in variants:
                r = difflib.SequenceMatcher(None, compact.translate(CONF), v.replace(" ", "").translate(CONF)).ratio()
                if r >= 0.78:
                    return p, tail, round(r, 2)
    w = _words(s)
    if not w or " ".join(w[-3:]) in NOT_PRESIDENT or " ".join(w[-3:]).endswith("SMITH AND JOHNSON"):
        return None
    best = None
    for p, variants in PRES.items():
        for v in variants:
            vw = v.split()
            for k in (len(vw), len(vw) + 1, len(vw) - 1):
                if k <= 0 or k > len(w):
                    continue
                r = difflib.SequenceMatcher(None, " ".join(w[-k:]).translate(CONF), v.translate(CONF)).ratio()
                if r >= 0.80 and (best is None or r > best[1]):
                    best = (p, r, len(w) - k)
    if not best:
        return None
    if best[2] > 0:   # a longer line: the name must follow a sentence end
        if best[2] < 3 or not re.search(r"[.:;]\W*\S+\W*\S*\W*\S*\W*\S*\.?\W*$", s):
            return None
    return best[0], tail, round(best[1], 2)


def state_heading(lines, i):
    s = lines[i].strip()
    up = re.sub(r"[^A-Z ]", "", s.upper()).strip()
    if len(s) >= 18 or not re.fullmatch(r"[A-Za-z .]+[.:]?", s) or i + 1 >= len(lines) or not lines[i + 1].strip().isupper():
        return None
    hit = difflib.get_close_matches(up, STATES, 1, 0.8)
    return hit[0] if hit else None


def reservation_heading(line):
    """'CAMP VERDE RESERVATION.' and OCR forms: 'CAMP McDOWEIL RESERVATION.', 'rORT HAH RESERVATION".'
    (one or two lowercase OCR glyphs are allowed), but not bracketed subheads like '[Partly in California.]'."""
    s = line.strip()
    if len(s) >= 80 or s[:1] == "[":
        return None
    core = re.sub(r"Mc(?=[A-Z])", "MC", re.sub(r"^[^A-Za-z(]{0,6}", "", s))
    letters = re.sub(r"[^A-Za-z]", "", core)
    if len(letters) < 6 or sum(c.islower() for c in letters) > (2 if len(letters) >= 12 else 0):
        return None
    if re.search(r"R\S{0,2}S\S{0,2}RV|RES\S{0,3}V|ESE\S{0,2}V|SER\S{0,2}AT|FISHERY|BAND|MILITARY", core) or core.rstrip(".").endswith("PAIUTE"):
        return re.sub(r"\s+", " ", core.rstrip("., \"'"))
    return None


DATELINE = re.compile(r"\S{3,}\.?\s+\S{1,4}\s*[,.]\s*\S{4}\.?\W{0,3}$")
REFERRAL = re.compile(r"(?i)^\W*(respectfully\s+)?(referred|returned)\b")
OFFICIAL_SIGNOFF = re.compile(r"(?i)(secretary(\s+of\s+the\s+interior|\s+of\s+war|\s+of\s+state)?|commissioner|general)\W*$")
ADDRESSEE = re.compile(r"^\W*(Gen|Hon|Lieut|Maj|Col|Capt|Mr|Commanding|Commander|Superintendent)\b\.?")


def trailer_end(st, i):
    """Index of the last line, after the signature at i, that still belongs to the act: the
    signature's second line, a countersignature, a parenthetical or bracketed note, a referral by a
    Secretary, an indorsement by a General, or a date printed after the signature."""
    n, j, last = len(st), i + 1, i
    kinds = []
    while j < n:
        s = st[j][2].strip()
        if is_header(s) or reservation_heading(s) or state_heading([x[2] for x in st], j):
            break
        if re.match(r"(?i)^\W{0,3}president\s+of\s+the\s+united\s+states", s):
            last, j = j, j + 1
            kinds.append("signature_second_line")
            continue
        if re.match(r"(?i)^by\s+the\s+president", s):
            k = next((k for k in range(j, min(j + 4, n)) if re.search(r"(?i)secretar", st[k][2])), None)
            last = k if k is not None else j
            j = last + 1
            kinds.append("countersignature")
            continue
        if s[:1] in "([":
            close = ")" if s[:1] == "(" else "]"
            k = next((k for k in range(j, min(j + 12, n)) if close in st[k][2]), None)
            if k is None:
                break
            last, j = k, k + 1
            kinds.append("note")
            continue
        if re.match(r"(?i)^and\s+indorsed\s+by", s):
            k = next((k for k in range(j + 1, min(j + 80, n)) if OFFICIAL_SIGNOFF.search(st[k][2].strip())
                      and len(st[k][2].strip()) < 60), None)
            if k is None:
                break
            last, j = k, k + 1
            while j < n and ADDRESSEE.match(st[j][2]) and j <= k + 3:
                last, j = j, j + 1
            kinds.append("indorsed_by")
            continue
        if len(s) < 30 and DATELINE.search(s) and read_date(s):
            if j + 1 < n and REFERRAL.match(st[j + 1][2]):
                k = next((k for k in range(j + 1, min(j + 10, n)) if OFFICIAL_SIGNOFF.search(st[k][2].strip())), None)
                if k is None:
                    break
                last, j = k, k + 1
                kinds.append("referral")
                continue
            if not kinds:   # a date printed under the signature ("Franklin Pierce," / "January 20, 1857.")
                last, j = j, j + 1
                kinds.append("date_after_signature")
                continue
        break
    return last, kinds


# ---------------------------------------------------------------- the volume

def load_pages(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh]


def stream(pages, body=BODY, offset=OFFSET):
    """Body lines as (pdf_page, printed_page, line), without running heads, page numbers and GPO marks."""
    out, heads = [], 0
    for d in pages:
        p = int(d["page"])
        if not body[0] <= p <= body[1]:
            continue
        lines = [l.rstrip() for l in d["text"].split("\n")]
        while lines and not lines[-1].strip():
            lines.pop()
        idx = [k for k, l in enumerate(lines) if l.strip()]
        if idx and is_running_head(lines[idx[0]]):
            lines[idx[0]] = ""
            heads += 1
        if lines and re.fullmatch(r"\s*\S?\d{1,3}\s*\W?\s*", lines[-1]):
            lines.pop()
        for l in lines:
            if l.strip() and not GPO_MARK.match(l):
                out.append((p, p - offset, l))
    return out, heads


def parse(st):
    """Return (acts, headings) from the body stream."""
    state, reservation = "", ""
    acts, heads = [], []
    boundary, skip = 0, -1
    texts = [x[2] for x in st]
    for i, (pdf, printed, l) in enumerate(st):
        if i <= skip:
            continue
        s = l.strip()
        stt = state_heading(texts, i)
        if stt:
            state = stt
            heads.append({"kind": "state", "name": state, "pdf_page": pdf, "printed_page": printed})
            boundary = i + 1
            continue
        res = reservation_heading(s)
        if res:
            reservation = res
            heads.append({"kind": "reservation", "name": reservation, "state": state, "pdf_page": pdf, "printed_page": printed})
            boundary = i + 1
            continue
        sig = is_signature(s)
        if not sig:
            continue
        pres, tail, score = sig
        term = TERMS[pres]
        span = st[boundary:i + 1]
        text = "\n".join(x[2] for x in span)
        t_end, t_kinds = trailer_end(st, i)
        trailer = st[i + 1:t_end + 1]
        hdr = [k for k, x in enumerate(span) if is_header(x[2].strip())]
        if re.search(r"(?i)in\s+witness\s+whereof|hereunto\s+set\s+my\s+hand", text):
            kind = "proclamation"
        elif hdr:
            kind = "order"
        else:
            kind = "indorsement_or_approval"
        start = hdr[-1] if hdr and kind == "order" else 0   # departmental papers printed before the order
        date, src = None, ""
        if kind == "proclamation":
            date, src = proclamation_date(text), "proclamation_done_clause"
        if not date and hdr:
            k = hdr[-1]
            date = header_date(span[k][2], span[k + 1][2] if k + 1 < len(span) else "", term)
            src = "header" if date else ""
        decade = ""
        if not date and hdr:     # a header that cannot be read: never fall back to other dates in the span
            t = span[hdr[-1]][2].strip()
            ym = re.search(r"\b(1[89]\d\d)\.?\W*$", t)
            if ym and term[0][:4] <= ym.group(1) <= term[1][:4]:   # the year is printed clearly, the month is not
                date, src = (ym.group(1), "", "", t[-12:], False), "header_year_only"
            else:
                pm = re.search(r"(1[89]\d)\S\W*$", t) or re.search(r"(1[89]\d)\S", t)
                decade = pm.group(1) + "x" if pm else ""
        if not date and not hdr and tail:
            date, src = read_date(tail, term), "date_glued_after_signature"
        if not date and not hdr and "date_after_signature" in t_kinds:
            date, src = read_date(trailer[t_kinds.index("date_after_signature")][2], term), "date_after_signature"
        if not date and not hdr:
            for x in reversed(span[:-1]):   # indorsements: the last standalone dateline before the signature
                t = x[2].strip()
                if len(t) < 70 and DATELINE.search(t) and (re.match(r"\W*Approved", t) or not re.search(
                        r"(?i)approved|dated|of\s+\S+\s+\S+,\s*\S+\.?$|act\s+of", t)):
                    date = read_date(t, term)
                    if date:
                        src = "standalone_dateline"
                        break
        if not date:
            src = ""
        y, mo, d, raw, repaired = date if date else ("", "", "", "", False)
        referral = ""
        if "referral" in t_kinds:
            r = read_date(trailer[0][2], term)
            referral = iso(r[0], r[1], r[2]) if r else ""
        acts.append({
            "seq": len(acts) + 1, "state": state, "reservation": reservation, "signer": pres, "kind": kind,
            "date": iso(y, mo, d), "date_raw": raw.replace("\n", " "), "date_source": src,
            "date_repaired": bool(repaired), "decade": decade or (y[:3] + "x" if y else ""),
            "year_in_term": ("yes" if term[0][:4] <= y <= term[1][:4] else "NO") if y else "",
            "signature_line": s, "signature_score": score, "referral_date": referral,
            "trailer": "|".join(t_kinds),
            "span": (boundary, t_end), "act_lines": (boundary + start, i), "papers": (boundary, boundary + start - 1) if start else None,
            "pdf_start": span[0][0], "pdf_end": st[t_end][0], "printed_start": span[0][1], "printed_end": st[t_end][1],
            "act_pdf_start": span[start][0], "act_printed_start": span[start][1],
        })
        boundary, skip = t_end + 1, t_end
    return acts, heads


def lead_ids(acts):
    per_page = collections.Counter()
    for a in acts:
        per_page[a["act_printed_start"]] += 1
        a["lead_id"] = f"IR1912:p{a['act_printed_start']}:{per_page[a['act_printed_start']]}"


# ---------------------------------------------------------------- matching with the WPA lists

def month_day(s):
    m = re.match(r"\s*([A-Za-z]+)\.?\s*(\d{1,2})?", s or "")
    if not m:
        return None, None
    return month_of(m.group(1)), int(m.group(2)) if m.group(2) else None


def wpa_date(r):
    mo, dd = month_day(r.get("month_day", ""))
    return f"{r['year']}-{mo:02d}-{dd:02d}" if mo and dd and r.get("year", "").isdigit() else ""


def act_pages(a):
    return range(a["printed_start"], a["printed_end"] + 1)


def names_in(name, text):
    """True when an OCR-tolerant form of a proper name ('Sitgreaves') occurs in text."""
    n = name.lower()
    for w in re.findall(r"[A-Za-z]{4,}", text):
        w = w.lower()
        if w[:5] == n[:5] or difflib.SequenceMatcher(None, w, n).ratio() >= 0.7:
            return True
    return False


def match_numbered(acts, numbered, act_text=None):
    """Pair acts with WPA numbered entries. Candidates share the exact date; or the month, with an IR
    page citation; or, for undated acts, an IR page citation inside the signer's term. A WPA entry that
    names a National Forest is a candidate only for an act whose text names that forest. Pairs are
    assigned globally, best score first, so a same-day cluster resolves as a whole. A pairing that
    could have gone another way at the same score is not made: it is returned as a tie.
    Returns ({seq: (entry, score, level)}, {seq: [(score, entry_id), ...]} for ties)."""
    act_text = act_text or {}
    by_date, by_month, by_page = collections.defaultdict(list), collections.defaultdict(list), collections.defaultdict(list)
    for r in numbered:
        d = wpa_date(r)
        if d:
            by_date[d].append(r)
            by_month[d[:7]].append(r)
        for p in IR_NUM.findall(r.get("text", "")):
            by_page[int(p)].append(r)
    rank = {"exact_date": 0, "same_month_and_IR_page": 1, "year_and_IR_page": 2, "undated_IR_page_in_term": 3}
    pairs = []
    for a in acts:
        if len(a["date"]) == 10:
            cands, level = by_date.get(a["date"], []), "exact_date"
        elif len(a["date"]) == 7:
            cands, level = by_month.get(a["date"], []), "same_month_and_IR_page"
        elif len(a["date"]) == 4:
            cands = [r for p in act_pages(a) for r in by_page.get(p, []) if r["year"] == a["date"]]
            level = "year_and_IR_page"
        elif not a["date"]:
            lo, hi = TERMS[a["signer"]]
            cands = [r for p in act_pages(a) for r in by_page.get(p, [])]
            cands = [r for r in cands if lo[:4] <= r["year"] <= hi[:4]
                     and (not a["decade"] or r["year"].startswith(a["decade"][:3]))]
            level = "undated_IR_page_in_term"
        else:
            continue
        key = [k for k in re.sub(r"[^A-Za-z ]", "", a["reservation"]).split()
               if len(k) > 3 and k not in ("RESERVATION", "INDIAN", "PUEBLO", "MILITARY", "VALLEY", "RIVER")]
        seen = set()
        for r in cands:
            if r["id"] in seen:
                continue
            seen.add(r["id"])
            text = r.get("text", "")
            page_hit = any(a["printed_start"] - 1 <= int(p) <= a["printed_end"] + 1 for p in IR_NUM.findall(text))
            if level != "exact_date" and not page_hit:
                continue
            forests = FOREST.findall(text)
            if forests and a["seq"] in act_text and not all(names_in(f, act_text[a["seq"]]) for f in forests):
                continue
            sc = 1 + (4 if page_hit else 0)
            if re.search(r"(?i)indian|reservation|pueblo|tribe", text):
                sc += 2
            if key and any(k.lower()[:5] in text.lower() for k in key):
                sc += 2
            named = {s for s, pat in STATE_PAT.items() if re.search(pat, text)}
            if a["state"] in named:
                sc += 2
            elif named and not (a["state"] in NAVAJO_STATES and named & NAVAJO_STATES):
                sc -= 3
            if sc >= (3 if level == "exact_date" else 5):
                pairs.append((-sc, rank[level], a["seq"], r["id"], level, r))
    pairs.sort(key=lambda t: t[:4])
    assigned, taken = {}, {}
    for negsc, _, seq, rid, level, r in pairs:
        if seq in assigned or rid in taken:
            continue
        assigned[seq] = (r, -negsc, level)
        taken[rid] = (seq, -negsc)
    # a tie: the act had another candidate at the same score that was free, or that went to an act
    # which could equally have taken this one
    score_of = {(seq, rid): -negsc for negsc, _, seq, rid, _, _ in pairs}
    ties = {}
    for seq, (r, sc, _) in assigned.items():
        rivals = []
        for (s2, rid2), sc2 in score_of.items():
            if s2 != seq or rid2 == r["id"] or sc2 != sc:
                continue
            owner = taken.get(rid2)
            if owner is None or (owner[1] == sc and score_of.get((owner[0], r["id"])) == sc):
                rivals.append(rid2)
        if rivals:
            ties[seq] = sorted([r["id"]] + rivals)
    for seq in ties:
        rid = assigned.pop(seq)[0]["id"]
        taken.pop(rid, None)
    return assigned, ties


def lord_crosswalk(acts, lord):
    """Each Lord citation of 'I IR <page>' resolved to the acts on that page of the same year:
    match (exactly one), ambiguous (several, and the date does not single one out) or unmatched."""
    on_page = collections.defaultdict(list)
    for a in acts:
        for p in act_pages(a):
            on_page[p].append(a)

    def same_year(a, yr):
        return a["date"][:4] == yr or (not a["date"] and a["decade"] and yr.startswith(a["decade"][:3]))

    rows = []
    for r in lord:
        txt = (r.get("summary") or "") + " ;; " + (r.get("citation_text") or "")
        yr = r.get("year", "")
        mo, dd = month_day(r["date"]) if r.get("date") else (None, None)
        ldate = f"{yr}-{mo:02d}-{dd:02d}" if mo and dd else ""
        for vol, pages in IR_LORD.findall(txt):
            for p in [int(x) for x in re.findall(r"\d{1,3}", pages)]:
                here = on_page.get(p, [])
                cands, how = [a for a in here if same_year(a, yr)], "same_year_on_page"
                if not cands:
                    cands, how = [a for a in on_page.get(p - 1, []) + on_page.get(p + 1, []) if same_year(a, yr)], "same_year_adjacent_page"
                exact = [a for a in cands if ldate and a["date"] == ldate]
                if len(cands) == 1:
                    res, pick = "match", cands
                elif exact and len(exact) == 1:
                    res, pick, how = "match", exact, "exact_date_on_page"
                elif cands:
                    res, pick = "ambiguous", cands
                else:
                    res, pick, how = "unmatched", [], "acts_on_page_other_year" if here else "no_act_on_page"
                rows.append({"lord_seq": r["seq"], "lord_year": yr, "lord_date": r.get("date", ""),
                             "lord_pairing": r.get("pairing", ""), "volume": vol, "ir_page": p, "resolution": res,
                             "how": how, "acts": "|".join(a["lead_id"] for a in pick),
                             "act_dates": "|".join(a["date"] or a["decade"] or "?" for a in pick),
                             "acts_on_page": "|".join(f"{a['lead_id']}={a['date'] or a['decade'] or '?'}" for a in here)})
    return rows


# ---------------------------------------------------------------- ending leads

ENDING_SIGNALS = [
    ("revokes_or_cancels", r"\brevok|\brescind|\bcancel|\bannul|\bvacated\b"),
    ("restores_to_public_domain", r"restored\s+to\s+the\s+public\s+domain"),
    ("supersedes", r"\bin\s+lieu\s+of\b|\bsupersed"),
    ("amends_modifies_enlarges", r"\bamend|\bmodif|\benlarg|\badded\s+to"),
]
CITED_ORDER = re.compile(r"(?i)(?:executive\s+orders?|orders?\s+of\s+the\s+president)\s*(?:,\s*)?(?:dated|of)\s+"
                         r"((?:[A-Za-z]{3,}\.?)\s+\S{1,4},?\s+\S{4})")


def ending_leads(acts, lines_of):
    rows = []
    for a in acts:
        lo, hi = a["act_lines"]
        t = re.sub(r"-\s+", "", " ".join(lines_of[lo:hi + 1]))
        kinds = [k for k, pat in ENDING_SIGNALS if re.search("(?i)" + pat, t)]
        if not kinds:
            continue
        cited = []
        for m in CITED_ORDER.finditer(t):
            d = read_date(m.group(1))
            if d:
                cited.append(iso(*d[:3]))
        for c in sorted(set(cited)) or [""]:
            target, how = [], "no_date_cited"
            if c:
                target = [b for b in acts if b["seq"] < a["seq"] and b["date"] == c and b["reservation"] == a["reservation"]]
                how = "same_section"
                if not target:
                    target = [b for b in acts if b["seq"] != a["seq"] and b["date"] == c and b["state"] == a["state"]]
                    how = "same_state"
                how = (how if len(target) == 1 else "ambiguous_" + how) if target else "not_in_volume_or_unread"
            rows.append({"lead_id": a["lead_id"], "date": a["date"], "signer": a["signer"], "state": a["state"],
                         "reservation": a["reservation"], "signals": "|".join(kinds), "cited_order_date": c,
                         "target_resolution": how, "target_lead_ids": "|".join(b["lead_id"] for b in target)})
    return rows


# ---------------------------------------------------------------- inputs and outputs

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path, rows, fields):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def slug(s, n=40):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:n].strip("-") or "x"


def check_hashes(vol, repo, job_dir):
    text_path = job_dir / vol["text"]
    text_sha = sha256_bytes(text_path.read_bytes())
    if text_sha != vol["text_sha256"]:
        raise SystemExit(f"{vol['text']}: sha256 {text_sha} does not match PROVENANCE.json")
    pdf = repo / vol["pdf"]
    if not pdf.exists():
        return text_path, "pdf_not_checked_out"
    with open(pdf, "rb") as fh:
        if fh.read(40).startswith(b"version https://git-lfs"):
            return text_path, "pdf_is_lfs_pointer_text_layer_hash_verified"
    if sha256_bytes(pdf.read_bytes()) != vol["pdf_sha256"]:
        raise SystemExit(f"{vol['pdf']}: sha256 does not match PROVENANCE.json")
    return text_path, "match"


def run(repo_root, job_dir, out_dir, wpa_dir=None):
    repo, job_dir, out = pathlib.Path(repo_root), pathlib.Path(job_dir), pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    prov = json.loads((job_dir / "data" / "PROVENANCE.json").read_text(encoding="utf-8"))
    vol = prov["volumes"][0]
    key = vol["key"]
    text_path, pdf_check = check_hashes(vol, repo, job_dir)

    census = {r["id"].upper(): r for r in read_csv(repo / prov["census"])}
    rp = repo / prov["readiness"]
    readiness = {r["instrument_id"].upper(): r for r in read_csv(rp)} if rp.exists() else {}
    wpa = pathlib.Path(wpa_dir) if wpa_dir else repo / prov["wpa_lists"]
    num_p, un_p = wpa / "NUMBERED_ENTRIES.csv", wpa / "UNNUMBERED_ENTRIES.csv"
    numbered = read_csv(num_p) if num_p.exists() else []
    lord = read_csv(un_p) if un_p.exists() else []

    st, heads_removed = stream(load_pages(text_path), tuple(vol["body_pdf_pages"]), vol["printed_page_offset"])
    acts, heads = parse(st)
    lead_ids(acts)
    lines_of = [x[2] for x in st]
    by_seq = {a["seq"]: a for a in acts}

    act_text = {a["seq"]: " ".join(lines_of[a["act_lines"][0]:a["span"][1] + 1]) for a in acts}
    assigned, ties = match_numbered(acts, numbered, act_text)
    lord_rows = lord_crosswalk(acts, lord)
    lord_by_act = collections.defaultdict(lambda: {"match": set(), "ambiguous": set()})
    for r in lord_rows:
        if r["resolution"] in ("match", "ambiguous"):
            for lid in r["acts"].split("|"):
                lord_by_act[lid][r["resolution"]].add(r["lord_seq"])
    lord_by_seq = {r["seq"]: r for r in lord}
    lord_unmatched = collections.defaultdict(list)   # page -> Lord rows citing it that no act of their year explains
    for r in lord_rows:
        if r["resolution"] == "unmatched":
            mo, dd = month_day(r["lord_date"]) if r["lord_date"] else (None, None)
            if mo:
                lord_unmatched[r["ir_page"]].append((r["lord_seq"], r["lord_year"], mo, dd))

    texts = out / "texts"
    texts.mkdir(parents=True, exist_ok=True)
    act_rows, fragments, leads = [], [], []
    matched_ids = set()
    for a in acts:
        hit = assigned.get(a["seq"])
        eo, score, level, wdate = "", "", "", ""
        if hit:
            r, score, level = hit
            eo, wdate = r["id"].upper(), wpa_date(r) or r["year"]
            matched_ids.add(eo)
        c = census.get(eo) if eo else None
        de = (c or {}).get("date_effective", "").strip()
        tied = ties.get(a["seq"], [])
        if not numbered:
            cstate = "not_compared_wpa_lists_missing"
        elif tied:
            cstate = "AMBIGUOUS_NUMBERED_MATCH"
        elif not eo:
            cstate = "UNNUMBERED_NOT_IN_CENSUS"
        elif not c:
            cstate = "NUMBERED_NOT_IN_CENSUS"
        elif not de:
            cstate = "census_date_blank"
        elif len(de) == 4:
            book_year = a["date"][:4] or wdate[:4]
            cstate = "census_year_only" if de == book_year else "YEAR_CONFLICT"
        else:
            cstate = "census_exact_date" if de == a["date"] else "DATE_CONFLICT"
        rd = readiness.get(eo, {}) if eo else {}
        lm = lord_by_act[a["lead_id"]]
        lord_years = {lord_by_seq[s]["year"] for s in lm["match"] if s in lord_by_seq}
        lord_dates = set()
        for s in lm["match"]:
            lr = lord_by_seq.get(s, {})
            mo, dd = month_day(lr.get("date", "")) if lr.get("date") else (None, None)
            if mo and dd:
                lord_dates.add(f"{lr['year']}-{mo:02d}-{dd:02d}")
        conflict = sorted({f"Lord {q}: {y}-{m:02d}" + (f"-{d:02d}" if d else "")
                           for p in act_pages(a) for q, y, m, d in lord_unmatched.get(p, [])
                           if a["date"][5:7] and m == int(a["date"][5:7]) and y != a["date"][:4]}
                          ) if a["date_repaired"] or a["year_in_term"] == "NO" else []   # only where the digits were in doubt
        if not a["date"]:
            check = ""
        elif conflict:
            check = "LORD_SAME_MONTH_OTHER_YEAR"
        elif wdate and len(wdate) == 10 and a["date"] == wdate:
            check = "wpa_date_agrees"
        elif wdate and len(a["date"]) == 7 and wdate.startswith(a["date"]):
            check = "wpa_month_agrees"
        elif a["date"] in lord_dates:
            check = "lord_date_agrees"
        elif a["date"][:4] in lord_years:
            check = "lord_year_agrees"
        elif lord_years or wdate:
            check = "OTHER_LIST_DATE_DIFFERS"
        else:
            check = "no_list_date"
        lo, hi = a["act_lines"]
        span_lo, span_hi = a["span"]
        body_lines = lines_of[lo:span_hi + 1]
        body = "\n".join(body_lines).strip() + "\n"
        body_sha = sha256_bytes(body.encode("utf-8"))
        stem = f"{a['date'] or 'undated-' + (a['decade'] or 'x')}_{a['lead_id'].replace(':', '-')}_{slug(a['reservation'])}"
        fname = f"texts/{stem}.txt"
        confidence = ("high" if a["date_source"] and not a["date_repaired"] and len(a["date"]) == 10 and a["year_in_term"] == "yes"
                      else "medium" if a["date"] else "low")
        act_pdf = f"PDF pages {st[lo][0]}-{st[span_hi][0]}"
        act_printed = f"printed pages {st[lo][1]}-{st[span_hi][1]}"
        header = (f"# {a['lead_id']}: {a['kind']} signed by {a['signer'].title()}, {a['date'] or 'date unread'}"
                  f" ({a['reservation'] or 'no reservation heading'}, {a['state'].title() or 'no state heading'})"
                  + (f"; matched to {eo} in the WPA numbered list ({level})" if eo else "; no WPA numbered entry matched") + "\n"
                  f"# Source: {vol['title']} ({vol['published']}); {vol['digitized_by']}\n"
                  f"# PDF: {vol['pdf']} sha256 {vol['pdf_sha256']}\n"
                  f"# {act_pdf}; {act_printed}; date from {a['date_source'] or 'nowhere (unread)'}"
                  f"{' after digit repair' if a['date_repaired'] else ''}; confidence {confidence}\n"
                  f"# Text: OCR text layer of the scan ({vol['extractor']}), running heads and page numbers removed. "
                  f"Not human-verified. Body sha256 {body_sha}\n\n")
        (out / fname).write_text(header + body, encoding="utf-8", newline="\n")
        papers_path, papers_pages = "", ""
        if a["papers"]:
            plo, phi = a["papers"]
            ptext = "\n".join(lines_of[plo:phi + 1]).strip() + "\n"
            papers_path = f"texts/{stem}.papers.txt"
            papers_pages = f"{st[plo][0]}-{st[phi][0]}"
            (out / papers_path).write_text(
                f"# Related papers printed before {a['lead_id']} (departmental letters; not the President's act)\n"
                f"# PDF pages {papers_pages}; printed pages {st[plo][1]}-{st[phi][1]}; body sha256 "
                f"{sha256_bytes(ptext.encode('utf-8'))}\n\n" + ptext, encoding="utf-8", newline="\n")
        row = {
            "lead_id": a["lead_id"], "seq": a["seq"], "kind": a["kind"], "signer": a["signer"], "date": a["date"],
            "date_source": a["date_source"], "date_raw": a["date_raw"], "date_repaired": a["date_repaired"],
            "decade": a["decade"], "year_in_term": a["year_in_term"], "date_check_against_lists": check,
            "referral_date_after_signature": a["referral_date"], "trailer": a["trailer"],
            "state": a["state"], "reservation": a["reservation"],
            "act_pdf_pages": f"{st[lo][0]}-{st[span_hi][0]}", "act_printed_pages": f"{st[lo][1]}-{st[span_hi][1]}",
            "span_pdf_pages": f"{a['pdf_start']}-{a['pdf_end']}", "span_printed_pages": f"{a['printed_start']}-{a['printed_end']}",
            "related_papers_pdf_pages": papers_pages, "related_papers_lines": (a["papers"][1] - a["papers"][0] + 1) if a["papers"] else 0,
            "numbered_eo": eo, "match_level": level, "match_score": score, "wpa_date": wdate,
            "numbered_candidates_tied": "|".join(tied),
            "lord_seqs": "|".join(sorted(lm["match"], key=int)), "lord_seqs_ambiguous": "|".join(sorted(lm["ambiguous"], key=int)),
            "census": cstate, "census_date_effective": de, "provisional_status": rd.get("provisional_status", ""),
            "original_text_step_before": rd.get("step_original_text", ""), "blockers": rd.get("blockers", ""),
            "confidence": confidence, "signature_line": a["signature_line"], "text_path": fname, "text_sha256": body_sha,
            "papers_path": papers_path, "chars": len(body)}
        act_rows.append(row)
        evidence = f"{vol['short']}, {act_printed}, {act_pdf}"
        if c:
            exact = level == "exact_date"
            fragments.append({
                "instrument_id": eo, "kind": "original_representation", "produced_by": "indian-reservations-1912",
                "confidence_note": ("Machine location lead, confidence " + ("high" if exact else "medium") + ". "
                                    "The book prints no order numbers: this act was paired with the WPA numbered list "
                                    + ("on the exact date" if exact else "by month or IR page citation only") +
                                    f" (score {score}). Official compilation (GPO 1912), Cornell copy scanned by the Internet "
                                    "Archive, PDF via HathiTrust; text is the scan's OCR layer. Identity, boundaries and wording "
                                    "are NOT human-verified; this is not a legal conclusion."),
                "data": {"url": vol["handle_url"], "sha256": vol["pdf_sha256"], "page_or_item": evidence,
                         "route": "official/gpo_compilation_1912", "location_confidence": "high" if exact else "medium",
                         "location_verified": False, "needs_page_check": not exact,
                         "signing_date": a["date"], "title": f"{a['reservation'].title()}, {a['state'].title()}",
                         "text_path": fname, "text_sha256": body_sha, "match_level": level,
                         "source_id": f"indian-reservations-1912:{a['lead_id']}:{vol['pdf_sha256'][:12]}"},
                "sources": [{"url": vol["handle_url"], "sha256": vol["pdf_sha256"], "page_or_item": evidence}]})

        def lead(kind, note=""):
            leads.append({"lead": kind, "lead_id": a["lead_id"], "instrument_id": eo, "date_in_book": a["date"],
                          "decade": a["decade"], "signer": a["signer"], "census_date_effective": de, "wpa_date": wdate,
                          "lord_seqs": row["lord_seqs"], "evidence": evidence, "text_path": fname, "note": note})
        if not numbered:
            pass   # without the WPA lists nothing can be said about numbering or census presence
        elif tied:
            lead("AMBIGUOUS_NUMBERED_MATCH", "equal-score WPA candidates, not paired: " + ", ".join(tied))
        elif not eo:
            lord_note = (f"; Lord's unnumbered list cites this page and year (seq {row['lord_seqs']})" if row["lord_seqs"]
                         else f"; Lord's citation of this page is ambiguous (seq {row['lord_seqs_ambiguous']})" if row["lord_seqs_ambiguous"]
                         else "; Lord does not cite this page for this year")
            lead("UNNUMBERED_NOT_IN_CENSUS", "no WPA numbered entry matched" + lord_note
                 + ("; from 1900 on this may be a numbered order whose WPA date differs (not checked)"
                    if (a["date"][:4] or "0") >= "1900" and not row["lord_seqs"] else ""))
        elif cstate == "census_year_only" and len(a["date"]) == 10 and a["date"][:4] == de:
            lead("BOOK_EXACT_DATE_FOR_YEAR_ONLY", f"match {level}, score {score}")
        elif cstate in ("YEAR_CONFLICT", "DATE_CONFLICT", "census_date_blank", "NUMBERED_NOT_IN_CENSUS"):
            lead(cstate, f"match {level}, score {score}")
        if conflict:
            lead("DATE_CONFLICT_WITH_LORD", f"book reads '{a['date_raw']}'"
                 + (" after digit repair" if a["date_repaired"] else "") + "; Lord cites this page for " + "; ".join(conflict))
        if a["year_in_term"] == "NO":
            lead("DATE_OUT_OF_TERM", f"read '{a['date_raw']}' outside {a['signer'].title()}'s term; OCR misread suspected")
        if not a["date"]:
            lead("UNDATED_ACT", (f"header unread; decade {a['decade']}" if a["decade"] else "no date line found")
                 + (f"; a referral after the signature is dated {a['referral_date']}" if a["referral_date"] else ""))

    # WPA entries that cite an IR page but were not paired with an act on that page
    wpa_rows = []
    act_by_eo = {r["numbered_eo"]: r for r in act_rows if r["numbered_eo"]}
    for r in numbered:
        pages = [int(p) for p in IR_NUM.findall(r.get("text", ""))]
        if not pages:
            continue
        eo = r["id"].upper()
        m = act_by_eo.get(eo)
        for p in pages:
            if m:
                a = by_seq[m["seq"]]
                res = "matched_act_on_page" if a["printed_start"] - 1 <= p <= a["printed_end"] + 1 else "MATCHED_ACT_ELSEWHERE"
            else:
                res = "NO_ACT_MATCHED"
            here = [b for b in acts if b["printed_start"] <= p <= b["printed_end"]]
            wpa_rows.append({"instrument_id": eo, "wpa_date": wpa_date(r), "ir_page": p, "resolution": res,
                             "matched_lead_id": m["lead_id"] if m else "", "matched_act_date": m["date"] if m else "",
                             "acts_on_page": "|".join(f"{b['lead_id']}={b['date'] or b['decade'] or '?'}" for b in here),
                             "in_census": "yes" if eo in census else "no"})
            if res != "matched_act_on_page":
                leads.append({"lead": "WPA_CITATION_MISMATCH", "lead_id": "", "instrument_id": eo, "date_in_book": "",
                              "decade": "", "signer": "", "census_date_effective": census.get(eo, {}).get("date_effective", ""),
                              "wpa_date": wpa_date(r), "lord_seqs": "", "evidence": f"WPA numbered list cites IR {p}",
                              "text_path": "", "note": f"{res}; acts on that page: "
                              + ("; ".join(f"{b['lead_id']}={b['date'] or b['decade'] or '?'}" for b in here) or "none")})

    endings = ending_leads(acts, lines_of)

    write_csv(out / f"{key}_ACTS.csv", act_rows, list(act_rows[0].keys()))
    write_csv(out / "CENSUS_LEADS.csv", leads, ["lead", "lead_id", "instrument_id", "date_in_book", "decade", "signer",
                                                "census_date_effective", "wpa_date", "lord_seqs", "evidence", "text_path", "note"])
    write_csv(out / "LORD_IR_CROSSWALK.csv", lord_rows, ["lord_seq", "lord_year", "lord_date", "lord_pairing", "volume",
                                                         "ir_page", "resolution", "how", "acts", "act_dates", "acts_on_page"])
    write_csv(out / "WPA_IR_CITATIONS.csv", wpa_rows, ["instrument_id", "wpa_date", "ir_page", "resolution", "matched_lead_id",
                                                       "matched_act_date", "acts_on_page", "in_census"])
    write_csv(out / "ENDING_LEADS.csv", endings, ["lead_id", "date", "signer", "state", "reservation", "signals",
                                                  "cited_order_date", "target_resolution", "target_lead_ids"])
    write_csv(out / f"{key}_HEADINGS.csv", heads, ["kind", "name", "state", "pdf_page", "printed_page"])
    with open(out / "FRAGMENTS.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for f in fragments:
            fh.write(json.dumps(f, ensure_ascii=False, sort_keys=True) + "\n")

    C = collections.Counter
    decided = [r for r in act_rows if r["provisional_status"]]
    lord_cited = {r["lord_seq"] for r in lord_rows}
    summary = {
        "leads_only": "Nothing is admitted, merged, dated or changed in the census or in any status.",
        "volume": key, "title": vol["title"], "pdf_check": pdf_check, "text_sha256": vol["text_sha256"],
        "census": prov["census"], "readiness_read": bool(readiness),
        "wpa_lists_read": bool(numbered), "wpa_dir": str(wpa),
        "body_lines": len(st), "running_heads_removed": heads_removed,
        "states": sum(1 for h in heads if h["kind"] == "state"),
        "reservation_headings": sum(1 for h in heads if h["kind"] == "reservation"),
        "acts": len(acts), "acts_by_kind": dict(C(a["kind"] for a in acts)),
        "acts_by_signer": dict(C(a["signer"] for a in acts)),
        "date_source": dict(C(a["date_source"] or "unread" for a in acts)),
        "dates": {"full": sum(1 for a in acts if len(a["date"]) == 10), "year_month": sum(1 for a in acts if len(a["date"]) == 7),
                  "year_only": sum(1 for a in acts if len(a["date"]) == 4),
                  "undated": sum(1 for a in acts if not a["date"]), "repaired": sum(1 for a in acts if a["date_repaired"]),
                  "out_of_term": sum(1 for a in acts if a["year_in_term"] == "NO")},
        "acts_before_1900": sum(1 for a in acts if a["date"] and a["date"] < "1900"),
        "acts_with_trailer": dict(C(k for a in acts for k in a["trailer"].split("|") if k)),
        "numbered_matches": len(assigned), "numbered_ties_not_paired": {str(k): v for k, v in ties.items()},
        "numbered_match_level": dict(C(level for _, _, level in assigned.values())),
        "numbered_matches_in_census": sum(1 for r in act_rows if r["numbered_eo"] and r["census"] != "NUMBERED_NOT_IN_CENSUS"),
        "acts_by_census_state": dict(C(r["census"] for r in act_rows)),
        "decided_orders_matched": len(decided),
        "matched_orders_original_text_step_open": sum(1 for r in act_rows if r["numbered_eo"] and r["original_text_step_before"] == "open"),
        "fragments": len(fragments),
        "census_leads": dict(C(l["lead"] for l in leads)),
        "wpa_entries_citing_ir": len({r["instrument_id"] for r in wpa_rows}),
        "wpa_ir_citations": len(wpa_rows), "wpa_ir_citation_resolution": dict(C(r["resolution"] for r in wpa_rows)),
        "lord_rows_citing_ir": len(lord_cited), "lord_ir_citations": len(lord_rows),
        "lord_resolution": dict(C(r["resolution"] for r in lord_rows)),
        "lord_how": dict(C(r["how"] for r in lord_rows)),
        "acts_with_a_lord_match": sum(1 for r in act_rows if r["lord_seqs"]),
        "unnumbered_acts_by_lord_support": dict(C(("lord_match" if r["lord_seqs"] else "lord_ambiguous" if r["lord_seqs_ambiguous"]
                                                   else "no_lord_cite") + ("_before_1900" if r["date"] and r["date"] < "1900" else "_1900_on" if r["date"] else "_undated")
                                                  for r in act_rows if r["census"] == "UNNUMBERED_NOT_IN_CENSUS")),
        "unnumbered_acts_before_1900_with_a_lord_match": sum(1 for r in act_rows if not r["numbered_eo"] and r["lord_seqs"]
                                                             and r["date"] and r["date"] < "1900"),
        "ending_lead_rows": len(endings), "ending_signals": dict(C(s for r in endings for s in r["signals"].split("|"))),
        "ending_targets": dict(C(r["target_resolution"] for r in endings)),
    }
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary


def wpa_dir_from_env():
    return os.environ.get("WPA_DIR") or None
