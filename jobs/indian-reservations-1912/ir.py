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
year digits are repaired only when exactly one reading falls inside the signer's term. A day printed
as anything but plain digits is never guessed: the date keeps only its month unless another printing,
Lord's list, the WPA numbered list or a citation elsewhere in the book gives a day the glyph can stand
for (on the italic headers 'H' is 14, not 4).

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
# What a misread DAY glyph may stand for, as whole readings. These are candidates only: a day read
# this way is kept only when another source gives one of them (see corroborate_days). On the italic
# headers 'H' is "14" ("December H, 1872" is the order the book itself cites as of December 14, 1872;
# the page images of p. 15, 18, 70, 73, 89 and 148 read 14), and 'i' is 1 (p. 13) or 4 (p. 206).
DAY_GLYPH = {k: list(v) for k, v in DIG.items() if len(v) < 10}
DAY_GLYPH.update({"H": ["4", "11", "14"], "Ii": ["4", "11", "14"], "i": ["1", "4"], "IB": ["13", "18"]})
DAY_NOISE = set("^?W}Mx")      # stands for any digit; a day made only of these has no candidates
MAX_DAY_READINGS = 10

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


def day_readings(tok):
    """The days (1-31) a damaged day token could stand for ("H" -> [4, 11, 14], "1^" -> [10..19]);
    [] when the token is only noise, cannot be read, or allows more than MAX_DAY_READINGS days."""
    tok = tok.strip(" .,;:'`-~*")
    if not tok or len(tok) > 4:
        return []
    parts, i, noise = [], 0, 0
    while i < len(tok):
        two = tok[i:i + 2]
        if len(two) == 2 and two in DAY_GLYPH:
            parts.append(DAY_GLYPH[two])
            i += 2
            continue
        c = tok[i]
        if c in DAY_NOISE:
            parts.append(list("0123456789"))
            noise += 1
        elif c in DAY_GLYPH:
            parts.append(DAY_GLYPH[c])
        else:
            return []
        i += 1
    if noise == len(parts):
        return []
    vals = sorted({int(x) for x in ("".join(p) for p in itertools.product(*parts)) if len(x) <= 2 and 1 <= int(x) <= 31})
    return vals if len(vals) <= MAX_DAY_READINGS else []


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
    """First date in text as (year, month, day, raw, repaired, day_candidates); day may be "". With a
    signer's term, damaged year digits are kept only when exactly one reading lies inside the term. A
    day is kept only when printed as plain digits; a damaged day is left blank and its possible readings
    are returned as day_candidates (never chosen here: see corroborate_days)."""
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
        if not years and re.fullmatch(r"13\d\d", year_tok):   # "1375" for "1873": an italic 8 read as 3; the
            years = [f"18{year_tok[2]}{k}" for k in range(10)]   # last digit is no safer, so only the decade is trusted
        if not years:
            continue
        literal_day = bool(re.fullmatch(r"\d{1,2}", day_tok)) and 1 <= int(day_tok) <= 31
        days = [str(int(day_tok))] if literal_day else [str(x) for x in day_readings(day_tok)]
        cands = [(y, d) for y in years for d in (days or [""])]
        if term:
            lo, hi = term
            keep = [(y, d) for y, d in cands
                    if lo[:4] <= y <= hi[:4] and (not d or lo <= f"{y}-{mo:02d}-{int(d):02d}" <= hi)]
            cands = keep or cands
        ys = sorted({y for y, _ in cands})
        if len(ys) != 1:
            continue
        ds = sorted({int(d) for y, d in cands if d and y == ys[0]})
        d = str(ds[0]) if literal_day and ds else ""
        day_cands = () if literal_day else tuple(ds)
        literal = bool(re.fullmatch(r"1[89]\d\d", year_tok)) and literal_day
        return ys[0], mo, d, " ".join(toks[k:k + 3]), not literal, day_cands
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
    return str(year), mo, str(day) if day else "", m.group(0)[:80], False, ()


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
    if re.search(r"R\S{0,2}S\S{0,2}RV|RES\S{0,3}V|ESE\S{0,2}V|SER\S{0,2}AT|FISHERY|BAND|MILITARY|SCHOOL", core) or core.rstrip(".").endswith("PAIUTE"):
        return re.sub(r"\s+", " ", core.rstrip("., \"'"))
    return None


SUBHEAD = r"\s*[\[Il|({]\s*[A-Z][^\]\[]{0,60}\]\W*"   # a bracketed subhead, its '[' possibly misread
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
            state, reservation = stt, ""   # a new state never inherits the last state's reservation
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
        decade, header_unread = "", ""
        if not date and hdr:     # a header that cannot be read: never fall back to other dates in the span
            k = hdr[-1]
            t = span[k][2].strip()
            nxt = span[k + 1][2].strip() if k + 1 < len(span) else ""
            if not re.search(r"1[389]\d", t) and len(nxt) < 30 and DATELINE.search(nxt):
                t = t + " " + nxt     # 'The White House,' / 'J^dy 7, 1910.': the date is on the next line
            header_unread = t[:80]
            ym = re.search(r"\b(1[89]\d\d)\.?\W*$", t)
            if ym and term[0][:4] <= ym.group(1) <= term[1][:4]:   # the year is printed clearly, the month is not
                date, src = (ym.group(1), "", "", t[-12:], False, ()), "header_year_only"
            else:   # only the decade: "1375" is 187x (an italic 8 read as 3)
                pm = re.search(r"(1[389]\d)\S\W*$", t) or re.search(r"(1[389]\d)\S", t)
                decade = ("18" + pm.group(1)[2] if pm.group(1)[:2] == "13" else pm.group(1)) + "x" if pm else ""
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
        y, mo, d, raw, repaired, day_cands = date if date else ("", "", "", "", False, ())
        referral = ""
        if "referral" in t_kinds:
            r = read_date(trailer[0][2], term)
            referral = iso(r[0], r[1], r[2]) if r else ""
        acts.append({
            "seq": len(acts) + 1, "state": state, "reservation": reservation, "signer": pres, "kind": kind,
            "date": iso(y, mo, d), "date_raw": raw.replace("\n", " "), "date_source": src,
            "header_unread": "" if date else header_unread,
            "date_repaired": bool(repaired), "decade": decade or (y[:3] + "x" if y else ""),
            "day_candidates": list(day_cands) if mo else [], "day_basis": "printed" if d else "",
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


def same_name(a, b):
    """OCR-tolerant equality of two proper names ('Crooir' = 'Crook')."""
    a, b = a.lower(), b.lower()
    return a[:5] == b[:5] or difflib.SequenceMatcher(None, a, b).ratio() >= 0.7


ACT_FOREST = re.compile(r"\b([A-Z][A-Za-z]{2,})\W{0,2}\s*Nat\w{3,6}\s+For\w{2,4}")


def act_forests(text):
    """The National Forests an act names, in order. The first is the forest the order acts on ('the
    boundaries of the Apache National Forest ... be modified'); later ones are cross-references
    ('not transferred to the Crook National Forest')."""
    return ACT_FOREST.findall(re.sub(r"(?<=[A-Za-z])-\s+(?=[a-z])", "", text or ""))


def reservation_keys(a):
    return [k for k in re.sub(r"[^A-Za-z ]", "", a["reservation"]).split()
            if len(k) > 3 and k not in ("RESERVATION", "INDIAN", "PUEBLO", "MILITARY", "VALLEY", "RIVER")]


def subject_score(a, r, act_text):
    """(score, page_hit) of pairing act a with WPA numbered entry r on subject, or None when the entry
    names a National Forest the act does not act on. Points: the entry cites this page of the book (4),
    names Indians, a reservation, pueblo or tribe (2), the reservation (2), the act's state (2); another
    state named costs 3."""
    text = r.get("text", "")
    page_hit = any(a["printed_start"] - 1 <= int(p) <= a["printed_end"] + 1 for p in IR_NUM.findall(text))
    forests = FOREST.findall(text)
    if forests and a["seq"] in act_text:
        named = act_forests(act_text[a["seq"]])
        if not named or not same_name(forests[0], named[0]):
            return None
    sc = 1 + (4 if page_hit else 0)
    if re.search(r"(?i)indian|reservation|pueblo|tribe", text):
        sc += 2
    key = reservation_keys(a)
    if key and any(k.lower()[:5] in text.lower() for k in key):
        sc += 2
    named = {s for s, pat in STATE_PAT.items() if re.search(pat, text)}
    if a["state"] in named:
        sc += 2
    elif named and not (a["state"] in NAVAJO_STATES and named & NAVAJO_STATES):
        sc -= 3
    return sc, page_hit


RANK = {"exact_date": 0, "same_month_and_IR_page": 1, "same_month_day_candidate": 2, "year_and_IR_page": 3,
        "undated_IR_page_in_term": 4, "late_same_month_subject": 5, "late_same_year_subject": 6}


def assign_pairs(pairs, group):
    """Assign (-score, rank, seq, entry id, level, entry) candidates globally, best score first. The
    printings of one order (group: {seq: first printing's seq}) compete as one, scored by their best
    printing. A pairing that could have gone another way at the same score is not made, whichever side
    the tie is on: an order with two equally good entries, or an entry with two equally good orders.
    Returns ({seq: (entry, score, level)} keyed by the printing that scored, {first printing's seq:
    {"entries": [...], "acts": [first printings' seqs]}} for ties)."""
    best = {}   # (order, entry) -> its best printing's (-score, rank, seq, level, entry)
    for negsc, rk, seq, rid, level, r in sorted(pairs, key=lambda t: t[:4]):
        best.setdefault((group.get(seq, seq), rid), (negsc, rk, seq, level, r))
    score = {k: -v[0] for k, v in best.items()}
    assigned_g, taken = {}, {}
    for (g, rid), (negsc, rk, seq, level, r) in sorted(best.items(), key=lambda kv: (kv[1][0], kv[1][1], kv[0][0], kv[0][1])):
        if g in assigned_g or rid in taken:
            continue
        assigned_g[g] = (rid, -negsc, seq, level, r)
        taken[rid] = (g, -negsc)
    ties = collections.defaultdict(lambda: {"entries": set(), "acts": set()})
    for g, (rid, sc, _, _, _) in assigned_g.items():
        # this order could equally have taken another entry: one that is free, or one that went to an
        # order which could equally have taken this order's entry
        for (g2, rid2), sc2 in score.items():
            if g2 != g or rid2 == rid or sc2 != sc:
                continue
            owner = taken.get(rid2)
            if owner is None or (owner[1] == sc and score.get((owner[0], rid)) == sc):
                ties[g]["entries"] |= {rid, rid2}
        # another order could equally have taken this entry: an order left unpaired, or one paired at
        # the same score with an entry this order could equally have taken
        for (g2, rid2), sc2 in score.items():
            if rid2 != rid or g2 == g or sc2 != sc:
                continue
            other = assigned_g.get(g2)
            if other is None or (other[1] == sc and score.get((g, other[0])) == sc):
                ties[g]["entries"].add(rid)
                ties[g]["acts"] |= {g, g2}
                ties[g2]["entries"].add(rid)
                ties[g2]["acts"] |= {g, g2}
    for g in ties:
        if g in assigned_g:
            taken.pop(assigned_g.pop(g)[0], None)
    assigned = {seq: (r, sc, level) for rid, sc, seq, level, r in assigned_g.values()}
    return assigned, {g: {"entries": sorted(v["entries"]), "acts": sorted(v["acts"])} for g, v in ties.items()}


def match_numbered(acts, numbered, act_text=None, group=None):
    """Pair acts with WPA numbered entries. Candidates share the exact date; or the month, with an IR
    page citation; or the month and a day the act's damaged day glyph can stand for (no page needed,
    but score 5); or, for undated acts, an IR page citation inside the signer's term. A WPA entry that
    names a National Forest is a candidate only for an act whose text names that same forest first:
    the forest it acts on, not one it mentions in passing, and not a word of the reservation's name
    ('White Mountain Apache'). Pairs are assigned by assign_pairs. Proclamations are not passed in."""
    act_text = act_text or {}
    group = group or {}
    by_date, by_month, by_page = collections.defaultdict(list), collections.defaultdict(list), collections.defaultdict(list)
    for r in numbered:
        d = wpa_date(r)
        if d:
            by_date[d].append(r)
            by_month[d[:7]].append(r)
        for p in IR_NUM.findall(r.get("text", "")):
            by_page[int(p)].append(r)
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
        seen = set()
        for r in cands:
            if r["id"] in seen:
                continue
            seen.add(r["id"])
            hit = subject_score(a, r, act_text)
            if hit is None:
                continue
            sc, page_hit = hit
            lv = level
            if level == "same_month_and_IR_page" and not page_hit:
                wd = wpa_date(r)
                if not (wd and int(wd[8:]) in a.get("day_candidates", [])):
                    continue
                lv = "same_month_day_candidate"
            elif level != "exact_date" and not page_hit:
                continue
            if sc >= (3 if lv == "exact_date" else 5):
                pairs.append((-sc, RANK[lv], a["seq"], r["id"], lv, r))
    return assign_pairs(pairs, group)


WPA_TEXT_DATE = re.compile(r"\b([A-Z][a-z]{2,8})\.?\s*(\d{1,2})\s*,\s*(1[789]\d\d)\b")
ACT_TEXT_DATE = re.compile(r"\b([A-Z][a-z]{2,8})\.?\s+(\d{1,2})\s*,?\s*(1[789]\d\d)\b")
LATE_MIN = {"late_same_month_subject": 5, "late_same_year_subject": 7}
LAND = re.compile(r"(?i)lands?\b|reserv|withdr[ae]w|set\s*apart|set\s*aside|restor|boundar|allot|tract")


def text_dates(pattern, text):
    out = set()
    for mon, d, y in pattern.findall(re.sub(r"\s+", " ", text or "")):
        mo = month_of(mon)
        if mo and 1 <= int(d) <= 31:
            out.add(f"{y}-{mo:02d}-{int(d):02d}")
    return out


def match_late(acts, numbered, act_text, group, odate, taken):
    """The numbered series reaches back past 1900, so an order of 1900 or later that the date rules did
    not pair may still be a numbered order whose date the OCR (or the WPA list) prints otherwise
    ('April 18' on p. 53 for EO 1517 of April 13, 1912). Each such order (odate: {first printing's seq:
    order date}, from 1900) is compared with the numbered entries of its year not already taken: of
    its month when the book prints one, else of the year. Only entries about land count (LAND: lands,
    reserved, withdrawn, set apart, restored, boundaries, allotment, tract), so a civil-service
    appointment at an Indian agency of the same month does not. The subject is scored as in
    subject_score, plus 2 when the state is named only with an OCR space inside it ('Cali fornia'),
    plus 3 when the entry cites a date the act's text also cites ('E. O. of Aug. 25, 1877'). The bar is
    LATE_MIN (higher when only the year is shared), and pairs are assigned by assign_pairs.
    Returns (assigned, ties, best candidate per order {first printing's seq: (entry id, score, level)})."""
    by_year = collections.defaultdict(list)
    for r in numbered:
        if r["id"].upper() not in taken:
            by_year[r.get("year", "")].append(r)
    pairs, best = [], {}
    for a in acts:
        g = group.get(a["seq"], a["seq"])
        od = odate.get(g, "")
        if not od or od[:4] < "1900":
            continue
        cited = text_dates(ACT_TEXT_DATE, act_text.get(a["seq"], ""))
        for r in by_year.get(od[:4], []):
            wd = wpa_date(r)
            if len(od) >= 7:
                if not wd or wd[:7] != od[:7]:
                    continue
                level = "late_same_month_subject"
            else:
                level = "late_same_year_subject"
            text = r.get("text", "")
            hit = subject_score(a, r, act_text) if LAND.search(text) else None
            if hit is None:
                continue
            sc = hit[0] + (3 if cited & text_dates(WPA_TEXT_DATE, text) else 0)
            if (a["state"] and not re.search(STATE_PAT[a["state"]], text)
                    and a["state"].replace(" ", "").lower() in re.sub(r"\s+", "", text).lower()):
                sc += 2
            if g not in best or sc > best[g][1]:
                best[g] = (r["id"].upper(), sc, level)
            if sc >= LATE_MIN[level]:
                pairs.append((-sc, RANK[level], a["seq"], r["id"], level, r))
    assigned, ties = assign_pairs(pairs, group)
    return assigned, ties, best


def agreed_date(book, wpa):
    """The part of the book's date that the WPA date does not contradict ('1912-04-18' and '1912-04-13'
    agree on '1912-04')."""
    if not wpa or not book:
        return book
    out = ""
    for k in (4, 7, 10):
        if len(book) >= k and len(wpa) >= k and book[:k] != wpa[:k]:
            break
        if len(book) >= k:
            out = book[:k]
    return out


# ---------------------------------------------------------------- printings of one order

REPRINT_MIN = 0.97   # measured: reprints 0.976-1.0; distinct orders at most 0.961 (same-day forest orders 0.957)


def norm_text(s):
    return re.sub(r"[^a-z0-9]+", " ", re.sub(r"-\s*\n\s*", "", s).lower()).strip()


def dates_compatible(a, b):
    """Could two printings carry one order's date? Equal; one a prefix of the other ('1882-08' and
    '1882-08-04'); one undated in the same decade; or full dates differing only in the day or only in
    the year within a decade (an OCR misread: 'January 11, 1876' printed as 1875)."""
    d1, d2 = a["date"], b["date"]
    if not d1 or not d2:
        x, y = (d1[:3] + "x" if d1 else a["decade"]), (d2[:3] + "x" if d2 else b["decade"])
        return not x or not y or x == y
    if d1 == d2:
        return True
    if len(d1) != len(d2):
        short, long_ = sorted((d1, d2), key=len)
        return long_.startswith(short)
    if len(d1) == 10:
        return d1[:7] == d2[:7] or (d1[4:] == d2[4:] and d1[:3] == d2[:3])
    return False


def reprint_groups(acts, act_body):
    """The book prints an order under every reservation it touches. Two acts are printings of one
    order when the same President signed both, their dates are compatible, they act on the same
    National Forest (if either names one), and their texts (header to signature, letters and digits
    only) agree to REPRINT_MIN. Returns ({seq: seq of the order's first printing}, [(seq, seq, ratio)])."""
    norm = {a["seq"]: norm_text(act_body[a["seq"]]) for a in acts}
    forests = {a["seq"]: act_forests(act_body[a["seq"]]) for a in acts}
    parent = {a["seq"]: a["seq"] for a in acts}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    links = []
    for i, a in enumerate(acts):
        for b in acts[i + 1:]:
            if a["signer"] != b["signer"] or not dates_compatible(a, b):
                continue
            x, y = norm[a["seq"]], norm[b["seq"]]
            if not x or not y or min(len(x), len(y)) / max(len(x), len(y)) < 0.9:
                continue
            fa, fb = forests[a["seq"]], forests[b["seq"]]
            if (fa or fb) and not (fa and fb and same_name(fa[0], fb[0])):
                continue
            sm = difflib.SequenceMatcher(None, x, y, autojunk=False)
            if sm.real_quick_ratio() < REPRINT_MIN or sm.quick_ratio() < REPRINT_MIN:
                continue
            r = sm.ratio()
            if r >= REPRINT_MIN:
                links.append((a["seq"], b["seq"], round(r, 3)))
                ra, rb = find(a["seq"]), find(b["seq"])
                parent[max(ra, rb)] = min(ra, rb)
    return {s: find(s) for s in parent}, links


def order_date(printings, wpa_full=""):
    """One date for an order printed several times, and how it was chosen. Full dates win over
    partial ones; among full dates the most printings win; a tie is broken by the WPA numbered
    list's date when it agrees with one of them, else by the first printing."""
    full = collections.Counter(a["date"] for a in printings if len(a["date"]) == 10)
    if not full:
        dated = sorted((a for a in printings if a["date"]), key=lambda a: (-len(a["date"]), a["seq"]))
        return (dated[0]["date"], "only_partial_dates" if len(printings) > 1 else "") if dated else ("", "")
    if len(full) == 1:
        return next(iter(full)), ("printings_agree" if len(printings) > 1 else "")
    top = max(full.values())
    cands = [d for d in full if full[d] == top]
    if len(cands) == 1:
        return cands[0], "most_printings"
    if wpa_full in cands:
        return wpa_full, "printings_tie_wpa_date_agrees"
    first = min((a for a in printings if a["date"] in cands), key=lambda a: a["seq"])
    return first["date"], "printings_tie_first_printing"


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


# ---------------------------------------------------------------- days the glyph alone cannot give

CITED_DATE = re.compile(r"(?i)\b(?:executive\s+)?orders?\s+(?:of\s+the\s+president\s*)?,?\s*(?:dated|of)\s+"
                        r"((?:[A-Za-z]{3,}\.?)\s+\S{1,4},?\s+\S{4})")


def in_book_references(acts, lines_of):
    """Dates the book cites for orders ('the order of December 14, 1872'), day and year printed as
    plain digits, with the act whose span (related papers, act and trailer) prints the citation:
    [(iso date, citing act's seq, snippet)]."""
    out = []
    for a in acts:
        lo, hi = a["span"]
        t = re.sub(r"\s+", " ", re.sub(r"-\s*\n\s*", "", "\n".join(lines_of[lo:hi + 1])))
        for m in CITED_DATE.finditer(t):
            if not month_of(m.group(1).split()[0]):
                continue
            d = read_date(m.group(1))
            if d and d[2] and not d[4]:
                out.append((iso(*d[:3]), a["seq"], m.group(0)[:70]))
    return out


def corroborate_days(acts, group, refs=(), lord_rows=(), lord_by_seq=None, wpa_dates=None):
    """Give a day to a printing whose day glyph is damaged (its date is month-only and it has
    day_candidates) only when an independent source gives a day the glyph can stand for and no source
    gives another one: a printing of the same order with the day in plain digits; a citation of that
    date elsewhere in the book (not in the order's own printings, not explained by another order printed
    with that date, and supporting no other order); Lord's list (a row resolved to a printing of this
    order alone); or the WPA numbered entry paired with the order (wpa_dates: {first printing's seq:
    (WPA date, entry id)}). The sources are recorded in day_basis. Returns the number of days given."""
    import calendar
    lord_by_seq = lord_by_seq or {}
    wpa_dates = wpa_dates or {}
    by_seq = {a["seq"]: a for a in acts}
    members = collections.defaultdict(list)
    for a in acts:
        members[group.get(a["seq"], a["seq"])].append(a)
    lord_for = collections.defaultdict(set)
    for r in lord_rows:
        if r["resolution"] == "match":
            for lid in r["acts"].split("|"):
                lord_for[lid].add(r["lord_seq"])
    printed = collections.defaultdict(set)   # full date printed in plain digits -> orders
    for a in acts:
        if len(a["date"]) == 10 and a["day_basis"] == "printed":
            printed[a["date"]].add(group.get(a["seq"], a["seq"]))
    support, ref_orders = {}, collections.defaultdict(set)
    for a in acts:
        if len(a["date"]) != 7 or not a["day_candidates"]:
            continue
        g, ym, cands = group.get(a["seq"], a["seq"]), a["date"], set(a["day_candidates"])
        sup = []   # (day, kind, source, citation key)
        for b in members[g]:
            if b is not a and b["day_basis"] == "printed" and b["date"][:7] == ym and int(b["date"][8:]) in cands:
                sup.append((int(b["date"][8:]), "other_printing", b["lead_id"], None))
        for d, seq, snip in refs:
            if (d[:7] == ym and int(d[8:]) in cands and group.get(seq, seq) != g
                    and not (printed.get(d, set()) - {g})):
                sup.append((int(d[8:]), "in_book_reference", f"{by_seq[seq]['lead_id']} '{snip}'", (d, seq)))
                ref_orders[(d, seq)].add(g)
        for b in members[g]:
            for q in sorted(lord_for.get(b["lead_id"], ()), key=int):
                lr = lord_by_seq.get(q, {})
                mo, dd = month_day(lr.get("date", "")) if lr.get("date") else (None, None)
                if mo and dd and f"{lr.get('year', '')}-{mo:02d}" == ym and dd in cands:
                    sup.append((dd, "lord", f"seq {q}", None))
        w, eo = wpa_dates.get(g, ("", ""))
        if len(w) == 10 and w[:7] == ym and int(w[8:]) in cands:
            sup.append((int(w[8:]), "wpa", eo, None))
        support[a["seq"]] = sup
    given = 0
    for seq, sup in support.items():
        a = by_seq[seq]
        # a citation that would give a day to two different orders identifies neither
        sup = [x for x in sup if x[3] is None or len(ref_orders[x[3]]) == 1]
        days = sorted({x[0] for x in sup})
        y, mo = int(a["date"][:4]), int(a["date"][5:7])
        if len(days) == 1 and days[0] <= calendar.monthrange(y, mo)[1]:
            a["date"] = f"{a['date']}-{days[0]:02d}"
            a["day_basis"] = "; ".join(f"{k} {src}" for _, k, src, _ in sup)
            a["date_repaired"] = True
            given += 1
        elif len(days) > 1:
            a["day_basis"] = "sources_disagree: " + "; ".join(f"{d} ({k} {src})" for d, k, src, _ in sup)
    return given


# ---------------------------------------------------------------- ending leads

ENDING_SIGNALS = [
    ("revokes_or_cancels", r"\brevok|\brescind|\bcancel|\bannul|\bvacated\b"),
    ("restores_to_public_domain", r"restored\s+to\s+the\s+public\s+domain"),
    ("supersedes", r"\bin\s+lieu\s+of\b|\bsupersed"),
    ("amends_modifies_enlarges", r"\bamend|\bmodif|\benlarg|\badded\s+to"),
]
CITED_ORDER = re.compile(r"(?i)(?:executive\s+orders?|orders?\s+of\s+the\s+president)\s*(?:,\s*)?(?:dated|of)\s+"
                         r"((?:[A-Za-z]{3,}\.?)\s+\S{1,4},?\s+\S{4})")


def ending_leads(acts, lines_of, group=None):
    """One row per order (its first printing) that revokes, restores, supersedes or amends, and per
    earlier order it cites by date. Several printings of the cited order count as one target."""
    group = group or {}
    by_seq = {a["seq"]: a for a in acts}
    rows = []
    for a in acts:
        if group.get(a["seq"], a["seq"]) != a["seq"]:
            continue   # a reprint: its first printing carries the lead
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
                mine = {s for s, g in group.items() if g == group.get(a["seq"], a["seq"])} | {a["seq"]}
                target = [b for b in acts if b["seq"] < a["seq"] and b["date"] == c and b["reservation"] == a["reservation"]]
                how = "same_section"
                if not target:
                    target = [b for b in acts if b["seq"] not in mine and b["date"] == c and b["state"] == a["state"]]
                    how = "same_state"
                printings = target
                target = [by_seq[s] for s in sorted({group.get(b["seq"], b["seq"]) for b in target})]
                how = (how if len(target) == 1 else "ambiguous_" + how) if target else "not_in_volume_or_unread"
            else:
                printings = []
            rows.append({"lead_id": a["lead_id"], "date": a["date"], "signer": a["signer"], "state": a["state"],
                         "reservation": a["reservation"], "signals": "|".join(kinds), "cited_order_date": c,
                         "target_resolution": how, "target_lead_ids": "|".join(b["lead_id"] for b in target),
                         "target_printings": "|".join(b["lead_id"] for b in printings)})
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
    wl = prov["wpa_lists"]
    if wpa_dir:
        wpa, wpa_source = pathlib.Path(wpa_dir), "WPA_DIR override"
    else:   # the committed subset of the wpa-lists job's output, checked against its recorded sha256
        wpa, wpa_source = job_dir / wl["dir"], f"vendored subset ({wl['dir']})"
        for name, h in wl.get("sha256", {}).items():
            got = sha256_bytes((wpa / name).read_bytes()) if (wpa / name).exists() else "missing"
            if got != h:
                raise SystemExit(f"{wl['dir']}/{name}: sha256 {got} does not match PROVENANCE.json")
    num_p, un_p = wpa / "NUMBERED_ENTRIES.csv", wpa / "UNNUMBERED_ENTRIES.csv"
    numbered = read_csv(num_p) if num_p.exists() else []
    lord = read_csv(un_p) if un_p.exists() else []

    st, heads_removed = stream(load_pages(text_path), tuple(vol["body_pdf_pages"]), vol["printed_page_offset"])
    acts, heads = parse(st)
    lead_ids(acts)
    lines_of = [x[2] for x in st]
    by_seq = {a["seq"]: a for a in acts}

    # printings of one order: the book reprints an order under every reservation it touches
    act_body = {a["seq"]: "\n".join(lines_of[a["act_lines"][0]:a["act_lines"][1] + 1]) for a in acts}
    group, reprint_links = reprint_groups(acts, act_body)
    printings = collections.defaultdict(list)
    for a in acts:
        printings[group[a["seq"]]].append(a)

    # a damaged day is never guessed: it is taken only from another printing, a citation in the book,
    # Lord's list or (below) the paired WPA entry
    refs = in_book_references(acts, lines_of)
    lord_by_seq = {r["seq"]: r for r in lord}
    days_given = corroborate_days(acts, group, refs, lord_crosswalk(acts, lord), lord_by_seq)

    act_text = {a["seq"]: " ".join(lines_of[a["act_lines"][0]:a["span"][1] + 1]) for a in acts}
    pairable = [a for a in acts if a["kind"] != "proclamation"]   # proclamations are not executive orders
    assigned, ties = match_numbered(pairable, numbered, act_text, group)
    # orders of 1900 or later still unpaired: compared with the numbered entries of their year by subject
    done = {group[seq] for seq in assigned} | set(ties)
    taken = {hit[0]["id"].upper() for hit in assigned.values()} | {e.upper() for t in ties.values() for e in t["entries"]}
    late_odate = {g: order_date(ms)[0] for g, ms in printings.items() if g not in done}
    late_assigned, late_ties, late_best = match_late([a for a in pairable if group[a["seq"]] not in done], numbered,
                                                     act_text, group, late_odate, taken)
    assigned.update(late_assigned)
    ties.update(late_ties)
    paired = {group[seq]: (seq, hit) for seq, hit in assigned.items()}   # order -> (printing paired, (entry, score, level))
    days_given += corroborate_days(acts, group, refs, lord_crosswalk(acts, lord), lord_by_seq,
                                   {g: (wpa_date(hit[0]), hit[0]["id"].upper()) for g, (_, hit) in paired.items()})
    odate = {g: order_date(ms, wpa_date(paired[g][1][0]) if g in paired else "") for g, ms in printings.items()}

    lord_rows = lord_crosswalk(acts, lord)
    lord_by_act = collections.defaultdict(lambda: {"match": set(), "ambiguous": set()})
    for r in lord_rows:
        if r["resolution"] in ("match", "ambiguous"):
            for lid in r["acts"].split("|"):
                lord_by_act[lid][r["resolution"]].add(r["lord_seq"])
    lord_unmatched = collections.defaultdict(list)   # page -> Lord rows citing it that no act of their year explains
    for r in lord_rows:
        if r["resolution"] == "unmatched":
            mo, dd = month_day(r["lord_date"]) if r["lord_date"] else (None, None)
            if mo:
                lord_unmatched[r["ir_page"]].append((r["lord_seq"], r["lord_year"], mo, dd))

    def joined(seqs):
        return "|".join(sorted(seqs, key=int))

    def label(b):
        return f"{b['lead_id']}={b['date'] or b['decade'] or '?'}"

    texts = out / "texts"
    texts.mkdir(parents=True, exist_ok=True)
    act_rows, fragments, leads = [], [], []
    for a in acts:
        g = group[a["seq"]]
        others = [b for b in printings[g] if b["seq"] != a["seq"]]
        od, od_how = odate[g]
        pseq, hit = paired.get(g, (None, None))
        rep = pseq or g   # the printing that carries the order's leads (and fragment): the paired one, else the first
        eo, score, level, wdate = "", "", "", ""
        if hit:
            r, score, level = hit
            eo, wdate = r["id"].upper(), wpa_date(r) or r["year"]
        c = census.get(eo) if eo else None
        de = (c or {}).get("date_effective", "").strip()
        tie = ties.get(g)
        if a["kind"] == "proclamation":
            cstate = "PROCLAMATION_NOT_AN_EXECUTIVE_ORDER"
        elif not numbered:
            cstate = "not_compared_wpa_lists_missing"
        elif tie:
            cstate = "AMBIGUOUS_NUMBERED_MATCH"
        elif not eo:
            cstate = "UNNUMBERED_NOT_IN_CENSUS"
        elif not c:
            cstate = "NUMBERED_NOT_IN_CENSUS"
        elif not de:
            cstate = "census_date_blank"
        elif len(de) == 4:
            book_year = od[:4] or wdate[:4]
            cstate = "census_year_only" if de == book_year else "YEAR_CONFLICT"
        else:
            cstate = "census_exact_date" if de == od else "DATE_CONFLICT"
        rd = readiness.get(eo, {}) if eo else {}
        lm = lord_by_act[a["lead_id"]]
        g_lord = set().union(*(lord_by_act[b["lead_id"]]["match"] for b in printings[g]))
        g_lord_amb = set().union(*(lord_by_act[b["lead_id"]]["ambiguous"] for b in printings[g])) - g_lord
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
        elif len(a["date"]) == 10 and any(x[:7] == a["date"][:7] for x in lord_dates):
            check = "LORD_DAY_DIFFERS"   # a row resolved to this act gives the same month, another day
        elif a["date"][:4] in lord_years:
            check = "lord_year_agrees"
        elif lord_years or wdate:
            check = "OTHER_LIST_DATE_DIFFERS"
        else:
            check = "no_list_date"
        # other printings of the same order: do they print the same date?
        differs = [b for b in others if a["date"] and b["date"]
                   and not (a["date"].startswith(b["date"]) or b["date"].startswith(a["date"]))]
        reprint_check = ("" if not others else "DIFFERS: " + "; ".join(label(b) for b in differs) if differs
                         else "agrees" if a["date"] and any(b["date"] for b in others) else "not_comparable")
        # this printing's date disagrees with the date taken for the order (the other printings, or the WPA list)
        off = bool(differs and od and not (od.startswith(a["date"]) or a["date"].startswith(od)))
        # 'high' needs a full date read literally, inside the term, that another source or printing repeats
        # and nothing contradicts: a literal OCR reading is not by itself a guarantee ('February 11' for 17)
        corroborated = check in ("wpa_date_agrees", "lord_date_agrees") or any(b["date"] == a["date"] for b in others)
        contradicted = check in ("LORD_SAME_MONTH_OTHER_YEAR", "LORD_DAY_DIFFERS", "OTHER_LIST_DATE_DIFFERS") or off
        literal = bool(a["date_source"]) and not a["date_repaired"] and len(a["date"]) == 10 and a["year_in_term"] == "yes"
        confidence = "high" if literal and corroborated and not contradicted else "medium" if a["date"] else "low"
        lo, hi = a["act_lines"]
        span_lo, span_hi = a["span"]
        body_lines = lines_of[lo:span_hi + 1]
        body = "\n".join(body_lines).strip() + "\n"
        body_sha = sha256_bytes(body.encode("utf-8"))
        stem = f"{a['date'] or 'undated-' + (a['decade'] or 'x')}_{a['lead_id'].replace(':', '-')}_{slug(a['reservation'])}"
        fname = f"texts/{stem}.txt"
        act_pdf = f"PDF pages {st[lo][0]}-{st[span_hi][0]}"
        act_printed = f"printed pages {st[lo][1]}-{st[span_hi][1]}"
        via = "" if not eo or pseq == a["seq"] else f" via its printing {by_seq[pseq]['lead_id']}"
        header = (f"# {a['lead_id']}: {a['kind']} signed by {a['signer'].title()}, {a['date'] or 'date unread'}"
                  f" ({a['reservation'] or 'no reservation heading'}, {a['state'].title() or 'no state heading'})"
                  + (f"; matched to {eo} in the WPA numbered list ({level}{via})" if eo else "; no WPA numbered entry matched") + "\n"
                  + (f"# One of {len(others) + 1} printings of this order (first: {by_seq[g]['lead_id']}); others: "
                     f"{', '.join(label(b) for b in others)}; order date {od or 'unread'}"
                     f"{' (' + od_how + ')' if od_how else ''}\n" if others else "")
                  + f"# Source: {vol['title']} ({vol['published']}); {vol['digitized_by']}\n"
                  f"# PDF: {vol['pdf']} sha256 {vol['pdf_sha256']}\n"
                  f"# {act_pdf}; {act_printed}; date from {a['date_source'] or 'nowhere (unread)'}"
                  f"{' after digit repair' if a['date_repaired'] else ''}"
                  f"{'; day from ' + a['day_basis'] if a['day_basis'] and a['day_basis'] != 'printed' else ''}"
                  f"{'; day glyph could be ' + '/'.join(map(str, a['day_candidates'])) if a['day_candidates'] and len(a['date']) == 7 else ''}"
                  f"; confidence {confidence}\n"
                  f"# Text: OCR text layer of the scan ({vol['extractor']}), running heads and page numbers removed. "
                  f"Not human-verified. Body sha256 {body_sha}\n\n")
        (out / fname).write_text(header + body, encoding="utf-8", newline="\n")
        papers_path, papers_pages = "", ""
        if a["papers"] and all(re.fullmatch(SUBHEAD, lines_of[k]) or not lines_of[k].strip()
                               for k in range(a["papers"][0], a["papers"][1] + 1)):
            a["papers"] = None   # only '[Partly in California.]' (OCR 'IPartly In California.]') before the order
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
            "day_candidates": "|".join(map(str, a["day_candidates"])), "day_basis": a["day_basis"],
            "header_unread": a["header_unread"],
            "decade": a["decade"], "year_in_term": a["year_in_term"], "date_check_against_lists": check,
            "order_lead_id": by_seq[g]["lead_id"], "printings": len(others) + 1,
            "other_printings": "|".join(b["lead_id"] for b in others), "order_date": od, "order_date_basis": od_how,
            "reprint_date_check": reprint_check,
            "referral_date_after_signature": a["referral_date"], "trailer": a["trailer"],
            "state": a["state"], "reservation": a["reservation"],
            "act_pdf_pages": f"{st[lo][0]}-{st[span_hi][0]}", "act_printed_pages": f"{st[lo][1]}-{st[span_hi][1]}",
            "span_pdf_pages": f"{a['pdf_start']}-{a['pdf_end']}", "span_printed_pages": f"{a['printed_start']}-{a['printed_end']}",
            "related_papers_pdf_pages": papers_pages, "related_papers_lines": (a["papers"][1] - a["papers"][0] + 1) if a["papers"] else 0,
            "numbered_eo": eo, "paired_printing": by_seq[pseq]["lead_id"] if pseq else "",
            "match_level": level, "match_score": score, "wpa_date": wdate,
            "numbered_candidates_tied": "|".join(tie["entries"]) if tie else "",
            "orders_tied_for_entry": "|".join(by_seq[s]["lead_id"] for s in tie["acts"] if s != g) if tie else "",
            "lord_seqs": joined(lm["match"]), "lord_seqs_ambiguous": joined(lm["ambiguous"]),
            "census": cstate, "census_date_effective": de, "provisional_status": rd.get("provisional_status", ""),
            "original_text_step_before": rd.get("step_original_text", ""), "blockers": rd.get("blockers", ""),
            "confidence": confidence, "signature_line": a["signature_line"], "text_path": fname, "text_sha256": body_sha,
            "papers_path": papers_path, "chars": len(body)}
        act_rows.append(row)
        evidence = f"{vol['short']}, {act_printed}, {act_pdf}"
        if c and pseq == a["seq"]:
            exact = level == "exact_date"
            how = {"exact_date": "on the exact date",
                   "same_month_and_IR_page": "by month and the WPA list's citation of this page",
                   "same_month_day_candidate": "by month and a day the damaged day glyph can stand for",
                   "year_and_IR_page": "by year and the WPA list's citation of this page",
                   "undated_IR_page_in_term": "by the WPA list's citation of this page within the signer's term",
                   "late_same_month_subject": "by month and subject only (the days differ or one is unread)",
                   "late_same_year_subject": "by year and subject only (the book's month is unread)"}[level]
            fragments.append({
                "instrument_id": eo, "kind": "original_representation", "produced_by": "indian-reservations-1912",
                "confidence_note": ("Machine location lead, confidence " + ("high" if exact else "medium") + ". "
                                    "The book prints no order numbers: this act was paired with the WPA numbered list "
                                    + how +
                                    f" (score {score}). "
                                    + (f"The book prints the same order again at {', '.join(label(b) for b in others)}. " if others else "")
                                    + "Official compilation (GPO 1912), Cornell copy scanned by the Internet "
                                    "Archive, PDF via HathiTrust; text is the scan's OCR layer. Identity, boundaries and wording "
                                    "are NOT human-verified; this is not a legal conclusion."),
                "data": {"url": vol["handle_url"], "sha256": vol["pdf_sha256"], "page_or_item": evidence,
                         "route": "official/gpo_compilation_1912", "location_confidence": "high" if exact else "medium",
                         "location_verified": False, "needs_page_check": not exact,
                         "signing_date": agreed_date(od, wdate), "title": f"{a['reservation'].title()}, {a['state'].title()}",
                         "text_path": fname, "text_sha256": body_sha, "match_level": level,
                         "source_id": f"indian-reservations-1912:{a['lead_id']}:{vol['pdf_sha256'][:12]}"},
                "sources": [{"url": vol["handle_url"], "sha256": vol["pdf_sha256"], "page_or_item": evidence}]})

        def lead(kind, note="", lord_seqs=None):
            leads.append({"lead": kind, "kind": a["kind"], "lead_id": a["lead_id"], "instrument_id": eo, "date_in_book": a["date"],
                          "decade": a["decade"], "signer": a["signer"], "census_date_effective": de, "wpa_date": wdate,
                          "lord_seqs": row["lord_seqs"] if lord_seqs is None else lord_seqs,
                          "other_printings": row["other_printings"], "evidence": evidence, "text_path": fname, "note": note})
        also = (f"; the book prints this order {len(others) + 1} times (also {', '.join(label(b) for b in others)}); "
                f"one order, not {len(others) + 1}" if others else "")
        if a["kind"] == "proclamation" and a["seq"] == rep:
            lead("PROCLAMATION_NOT_AN_EXECUTIVE_ORDER", "a proclamation ('In witness whereof', 'Done at ...', seal, "
                 "countersigned by the Secretary of State), not an executive order: not an unnumbered-order lead and "
                 "not paired with the numbered list" + also)
        elif numbered and a["seq"] == rep:   # one lead per order, never one per printing
            if tie:
                lead("AMBIGUOUS_NUMBERED_MATCH", "equal-score pairings, none made: WPA entries " + ", ".join(tie["entries"])
                     + ("; orders competing for the same entry: " + ", ".join(by_seq[s]["lead_id"] for s in tie["acts"])
                        if tie["acts"] else "") + also)
            elif not eo:
                lord_note = (f"; Lord's unnumbered list cites a printing's page and year (seq {joined(g_lord)})" if g_lord
                             else f"; Lord's citation of the page is ambiguous (seq {joined(g_lord_amb)})" if g_lord_amb
                             else "; Lord does not cite the page for this year")
                if od and od[:4] >= "1900":
                    lb = late_best.get(g)
                    late_note = ("; from 1900 on: compared with the WPA numbered entries of "
                                 + (od[:7] if len(od) >= 7 else od[:4]) + " by subject, none paired"
                                 + (f" (best {lb[0]}, score {lb[1]}, needs {LATE_MIN[lb[2]]})" if lb else " (no entry about land of that date)"))
                elif not od and (a["decade"][:2] == "19" or a["signer"] in ("ROOSEVELT", "TAFT")):
                    late_note = "; undated, from 1900 on: may be a numbered order (not compared, no date)"
                else:
                    late_note = ""
                lead("UNNUMBERED_NOT_IN_CENSUS", "no WPA numbered entry matched" + lord_note + late_note + also, joined(g_lord))
            elif cstate == "census_year_only" and len(od) == 10 and len(wdate) == 10 and od != wdate:
                lead("BOOK_DATE_DIFFERS_FROM_WPA", f"match {level}, score {score}; the book reads {od}, the WPA list "
                     f"{wdate}; check the page image" + also)
            elif cstate == "census_year_only" and len(od) == 10 and od[:4] == de:
                with_od = [b for b in printings[g] if b["date"] == od]
                day_note = ("" if any(b["day_basis"] == "printed" for b in with_od) else
                            f"; the day glyph is damaged, the day is from {with_od[0]['day_basis']}" if with_od else "")
                lead("BOOK_EXACT_DATE_FOR_YEAR_ONLY", f"match {level}, score {score}; book date {od}" + day_note + also)
            elif cstate in ("YEAR_CONFLICT", "DATE_CONFLICT", "census_date_blank", "NUMBERED_NOT_IN_CENSUS"):
                lead(cstate, f"match {level}, score {score}" + also)
        if conflict:
            lead("DATE_CONFLICT_WITH_LORD", f"book reads '{a['date_raw']}'"
                 + (" after digit repair" if a["date_repaired"] else "") + "; Lord cites this page for " + "; ".join(conflict))
        elif check == "LORD_DAY_DIFFERS":
            lead("DATE_CONFLICT_WITH_LORD", f"book reads '{a['date_raw']}' ({a['date']}"
                 + (f", day from {a['day_basis']}" if a["day_basis"] != "printed" else "") + "); Lord's list, resolved to "
                 "this act, gives " + ", ".join(sorted(x for x in lord_dates if x[:7] == a["date"][:7]))
                 + ("; another printing repeats the book's date" if any(b["date"] == a["date"] for b in others) else ""))
        if a["year_in_term"] == "NO":
            lead("DATE_OUT_OF_TERM", f"read '{a['date_raw']}' outside {a['signer'].title()}'s term; OCR misread suspected")
        if off:
            lead("REPRINT_DATE_CONFLICT", f"this printing reads '{a['date_raw']}' ({a['date']}); other printings of the same "
                 f"order: {', '.join(label(b) for b in differs)}; order date taken as {od} ({od_how}); check the page image")
        if a["seq"] == rep and not od:
            lead("UNDATED_ACT", (f"header unread ('{a['header_unread']}')" if a["header_unread"] else "no date line found")
                 + (f"; decade {a['decade']}" if a["decade"] else "")
                 + (f"; a referral after the signature is dated {a['referral_date']}" if a["referral_date"] else ""))

    # WPA entries that cite an IR page but were not paired with an order printed on that page
    wpa_rows = []
    act_by_eo = {r["numbered_eo"]: r for r in act_rows if r["numbered_eo"] and r["paired_printing"] == r["lead_id"]}
    for r in numbered:
        pages = [int(p) for p in IR_NUM.findall(r.get("text", ""))]
        if not pages:
            continue
        eo = r["id"].upper()
        m = act_by_eo.get(eo)
        mine = printings[group[m["seq"]]] if m else []
        for p in pages:
            if m:
                on = any(b["printed_start"] - 1 <= p <= b["printed_end"] + 1 for b in mine)
                res = "matched_act_on_page" if on else "MATCHED_ACT_ELSEWHERE"
            else:
                res = "NO_ACT_MATCHED"
            here = [b for b in acts if b["printed_start"] <= p <= b["printed_end"]]
            wpa_rows.append({"instrument_id": eo, "wpa_date": wpa_date(r), "ir_page": p, "resolution": res,
                             "matched_lead_id": m["lead_id"] if m else "", "matched_act_date": m["order_date"] if m else "",
                             "matched_printings": "|".join(b["lead_id"] for b in mine),
                             "acts_on_page": "|".join(label(b) for b in here),
                             "in_census": "yes" if eo in census else "no"})
            if res != "matched_act_on_page":
                leads.append({"lead": "WPA_CITATION_MISMATCH", "kind": m["kind"] if m else "",
                              "lead_id": m["lead_id"] if m else "", "instrument_id": eo,
                              "date_in_book": m["order_date"] if m else "", "decade": "", "signer": "",
                              "census_date_effective": census.get(eo, {}).get("date_effective", ""),
                              "wpa_date": wpa_date(r), "lord_seqs": "", "other_printings": "",
                              "evidence": f"WPA numbered list cites IR {p}", "text_path": m["text_path"] if m else "",
                              "note": f"{res}; acts on that page: " + ("; ".join(label(b) for b in here) or "none")
                              + (f"; the order is paired with {', '.join(b['lead_id'] for b in mine)}, printed at "
                                 f"{', '.join('p. ' + str(b['printed_start']) for b in mine)}" if m else "")})

    endings = ending_leads(acts, lines_of, group)

    write_csv(out / f"{key}_ACTS.csv", act_rows, list(act_rows[0].keys()))
    write_csv(out / "CENSUS_LEADS.csv", leads, ["lead", "kind", "lead_id", "instrument_id", "date_in_book", "decade", "signer",
                                                "census_date_effective", "wpa_date", "lord_seqs", "other_printings",
                                                "evidence", "text_path", "note"])
    write_csv(out / "LORD_IR_CROSSWALK.csv", lord_rows, ["lord_seq", "lord_year", "lord_date", "lord_pairing", "volume",
                                                         "ir_page", "resolution", "how", "acts", "act_dates", "acts_on_page"])
    write_csv(out / "WPA_IR_CITATIONS.csv", wpa_rows, ["instrument_id", "wpa_date", "ir_page", "resolution", "matched_lead_id",
                                                       "matched_act_date", "matched_printings", "acts_on_page", "in_census"])
    write_csv(out / "ENDING_LEADS.csv", endings, ["lead_id", "date", "signer", "state", "reservation", "signals",
                                                  "cited_order_date", "target_resolution", "target_lead_ids", "target_printings"])
    write_csv(out / "REPRINTS.csv", [{"lead_id": by_seq[x]["lead_id"], "other_lead_id": by_seq[y]["lead_id"],
                                      "date": by_seq[x]["date"], "other_date": by_seq[y]["date"], "text_ratio": r,
                                      "order_lead_id": by_seq[group[x]]["lead_id"]} for x, y, r in reprint_links],
              ["order_lead_id", "lead_id", "other_lead_id", "date", "other_date", "text_ratio"])
    write_csv(out / f"{key}_HEADINGS.csv", heads, ["kind", "name", "state", "pdf_page", "printed_page"])
    with open(out / "FRAGMENTS.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for f in fragments:
            fh.write(json.dumps(f, ensure_ascii=False, sort_keys=True) + "\n")

    C = collections.Counter
    first = [r for r in act_rows if r["order_lead_id"] == r["lead_id"]]                 # one row per order
    rep_rows = [r for r in act_rows if r["lead_id"] == (r["paired_printing"] or r["order_lead_id"])]
    decided = [r for r in rep_rows if r["provisional_status"]]
    lord_cited = {r["lord_seq"] for r in lord_rows}
    ods = [r["order_date"] for r in first]
    unnumbered = [r for r in rep_rows if r["census"] == "UNNUMBERED_NOT_IN_CENSUS"]
    un_leads = {l["lead_id"]: l for l in leads if l["lead"] == "UNNUMBERED_NOT_IN_CENSUS"}
    summary = {
        "leads_only": "Nothing is admitted, merged, dated or changed in the census or in any status.",
        "volume": key, "title": vol["title"], "pdf_check": pdf_check, "text_sha256": vol["text_sha256"],
        "census": prov["census"], "readiness_read": bool(readiness),
        "wpa_lists_read": bool(numbered), "wpa_lists_source": wpa_source,
        "wpa_dir": wl["dir"] if wpa_source.startswith("vendored") else str(wpa),
        "body_lines": len(st), "running_heads_removed": heads_removed,
        "states": sum(1 for h in heads if h["kind"] == "state"),
        "reservation_headings": sum(1 for h in heads if h["kind"] == "reservation"),
        "acts": len(acts), "acts_by_kind": dict(C(a["kind"] for a in acts)),
        "orders": len(printings), "reprints": len(acts) - len(printings),
        "orders_printed_more_than_once": sum(1 for ms in printings.values() if len(ms) > 1),
        "orders_by_printings": {str(k): v for k, v in sorted(C(len(ms) for ms in printings.values()).items())},
        "orders_whose_printings_disagree_on_the_date": len({r["order_lead_id"] for r in act_rows
                                                             if r["reprint_date_check"].startswith("DIFFERS")}),
        "printings_off_their_order_date": sum(1 for l in leads if l["lead"] == "REPRINT_DATE_CONFLICT"),
        "acts_by_signer": dict(C(a["signer"] for a in acts)),
        "date_source": dict(C(a["date_source"] or "unread" for a in acts)),
        "dates": {"full": sum(1 for a in acts if len(a["date"]) == 10), "year_month": sum(1 for a in acts if len(a["date"]) == 7),
                  "year_only": sum(1 for a in acts if len(a["date"]) == 4),
                  "undated": sum(1 for a in acts if not a["date"]), "repaired": sum(1 for a in acts if a["date_repaired"]),
                  "out_of_term": sum(1 for a in acts if a["year_in_term"] == "NO"),
                  "day_damaged": sum(1 for a in acts if a["day_candidates"]),
                  "day_from_other_sources": days_given,
                  "day_damaged_left_month_only": sum(1 for a in acts if a["day_candidates"] and len(a["date"]) == 7)},
        "day_sources": dict(C(k.split(" ")[0] for a in acts if a["day_candidates"] and len(a["date"]) == 10
                              for k in a["day_basis"].split("; "))),
        "order_dates": {"full": sum(1 for d in ods if len(d) == 10), "year_month": sum(1 for d in ods if len(d) == 7),
                        "year_only": sum(1 for d in ods if len(d) == 4), "undated": sum(1 for d in ods if not d)},
        "acts_before_1900": sum(1 for a in acts if a["date"] and a["date"] < "1900"),
        "orders_before_1900": sum(1 for d in ods if d and d < "1900"),
        "orders_from_1900": sum(1 for d in ods if d >= "1900"),
        "orders_by_decade": {k: v for k, v in sorted(C(d[:3] + "0s" for d in ods if d).items())},
        "confidence": dict(C(r["confidence"] for r in act_rows)),
        "acts_with_trailer": dict(C(k for a in acts for k in a["trailer"].split("|") if k)),
        "numbered_matches": len(assigned),
        "numbered_ties_not_paired": {by_seq[g]["lead_id"]: v["entries"] for g, v in ties.items()},
        "numbered_match_level": dict(C(level for _, _, level in assigned.values())),
        "numbered_late_subject_pairs": {by_seq[group[seq]]["lead_id"]: hit[0]["id"].upper() for seq, hit in late_assigned.items()},
        "numbered_matches_in_census": sum(1 for r in rep_rows if r["numbered_eo"] and r["census"] != "NUMBERED_NOT_IN_CENSUS"),
        "numbered_reprints_inheriting_pairing": sum(1 for r in act_rows if r["numbered_eo"] and r["paired_printing"] != r["lead_id"]),
        "acts_by_census_state": dict(C(r["census"] for r in act_rows)),
        "orders_by_census_state": dict(C(r["census"] for r in rep_rows)),
        "decided_orders_matched": len(decided),
        "matched_orders_original_text_step_open": sum(1 for r in rep_rows if r["numbered_eo"] and r["original_text_step_before"] == "open"),
        "fragments": len(fragments),
        "census_leads": dict(C(l["lead"] for l in leads)),
        "wpa_entries_citing_ir": len({r["instrument_id"] for r in wpa_rows}),
        "wpa_ir_citations": len(wpa_rows), "wpa_ir_citation_resolution": dict(C(r["resolution"] for r in wpa_rows)),
        "lord_rows_citing_ir": len(lord_cited), "lord_ir_citations": len(lord_rows),
        "lord_resolution": dict(C(r["resolution"] for r in lord_rows)),
        "lord_how": dict(C(r["how"] for r in lord_rows)),
        "acts_with_a_lord_match": sum(1 for r in act_rows if r["lord_seqs"]),
        "unnumbered_orders_by_lord_support": dict(C(
            ("lord_match" if un_leads[r["lead_id"]]["lord_seqs"] else "lord_ambiguous" if "ambiguous" in un_leads[r["lead_id"]]["note"]
             else "no_lord_cite") + ("_before_1900" if r["order_date"] and r["order_date"] < "1900"
                                     else "_1900_on" if r["order_date"] else "_undated") for r in unnumbered)),
        "unnumbered_orders_before_1900": sum(1 for r in unnumbered if r["order_date"] and r["order_date"] < "1900"),
        "unnumbered_orders_printed_more_than_once": sum(1 for r in unnumbered if r["printings"] > 1),
        "ending_lead_rows": len(endings), "ending_signals": dict(C(s for r in endings for s in r["signals"].split("|"))),
        "ending_targets": dict(C(r["target_resolution"] for r in endings)),
    }
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary


def wpa_dir_from_env():
    return os.environ.get("WPA_DIR") or None
