"""Split the saved text of one executive order into a DRAFT clause inventory.

Pure functions only (no files, no network), so the unit tests can feed in
short realistic excerpts.  Everything here produces LEADS: boundaries, kinds
and targets are machine guesses that a human must check.

Main entry points
-----------------
locate_order(text, number)   -> Located or None
    Finds one order inside a longer text (an FR issue, a web page, a PDF
    text layer) and returns where its heading, body, signature block and
    end are.
segment(text, loc, instrument_id) -> dict
    Splits the located body into recitals (non-operative) and clauses
    (operative units), each with exact character offsets into ``text`` so
    every clause text is a verbatim substring of the saved text.
find_headings(text)          -> list of (number_string, offset)
    Cheap scan used to discover which orders a text contains.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Small regex helpers
# ---------------------------------------------------------------------------


def fuzzy(word: str) -> str:
    """Regex for ``word`` that tolerates OCR letter spacing ("E x e c u t iv e")."""
    return "[ ]?".join(re.escape(c) for c in word)


EXEC_ORDER = fuzzy("executive") + r"[ \t]+" + fuzzy("order")

# Generic heading: "Executive Order 12944 of December 28, 1994",
# "EXECUTIVE ORDER 9066", "Executive Order No. 4359-A—Citizenship ...".
GENERIC_HEADING = re.compile(
    r"(?im)^[ \t]*" + EXEC_ORDER + r"[ \t]*(?:N[ ]?o\.?[ \t]*)?\n?[ \t]*"
    r"(\d(?:[ ]?\d){0,4})(?:[ \t]*[-‐–][ \t]*([A-Z])\b|([A-Z])\b)?"
)

UNNUMBERED_HEADING = re.compile(r"(?im)^[ \t]*" + EXEC_ORDER + r"[ \t]*(?:[—–\-:][^\n]*)?$")

MONTHS = (
    "January|February|March|April|May|June|July|August|September|October|November|December|"
    "Jan\\.|Feb\\.|Mar\\.|Apr\\.|Aug\\.|Sept?\\.|Oct\\.|Nov\\.|Dec\\."
)
DATE_LINE = re.compile(r"^\s*(?:" + MONTHS + r")\s*\d{1,2}\s*,\s*\d{4}\s*\.?\s*$")
# What may follow the number on a real heading line. A "." straight after the
# number ("Executive Order No. 10033.") or after its date ("Executive Order No.
# 11290 of July 21, 1966." in a list of revoked orders) is a sentence in a
# body, never a heading.
HEADING_TAIL_OK = re.compile(
    r"^\s*(?:$|[—–\-:]|of\s+(?:" + MONTHS + r")\s*\d{1,2}\s*,\s*\d{4}\s*$|[A-Z])"
)

WHITE_HOUSE = re.compile(
    r"(?im)^[ \t]*" + fuzzy("the") + r"[ \t]+" + fuzzy("white") + r"[ \t]+" + fuzzy("house")
    + r"[ \t]*[,.]?[ \t]*(?:[A-Z][^\n]{0,30}\d{4}[ \t]*\.?)?[ \t]*$"
)
FR_DOC = re.compile(r"(?im)^[ \t]*\[[ \t]*F[ ]?\.?[ ]?R[ ]?\.?[ \t]*D[ ]?o[ ]?c")
NO_LINE = re.compile(r"(?im)^[ \t]*\[[ \t]*No\.[ \t]*\d")
FILED_WITH = re.compile(r"(?im)^[ \t]*\[?Filed with the Office of the Federal Register")
APP_CITATION = re.compile(r"(?m)^[^\n]*Online by Gerhard Peters and John T\. Woolley|^[ \t]*Related Images[ \t]*$")

# Lines that are page furniture, never part of the order's words.
FURNITURE = [
    re.compile(r"^\s*\d*\s*Federal Register\s*/\s*Vol\.", re.I),
    re.compile(r"Federal Register\s*/\s*Vol\.\s*\d+.*Presidential Documents\s*\d*\s*$", re.I),
    re.compile(r"^\s*F\s?E\s?D\s?E\s?R\s?A\s?L\s+R\s?E\s?G\s?I\s?S\s?T\s?E\s?R\b.*\d{4}\s*$"),
    re.compile(r"^\s*\d{1,6}\s*$"),
    re.compile(r"^\s*Billing code\b", re.I),
    re.compile(r"^\s*\[\[Page \d+\]\]\s*$"),
    re.compile(r"^\s*T\s?H\s?E\s+P\s?R\s?E\s?S\s?I\s?D\s?E\s?N\s?T\s*$"),  # old FR running head
    re.compile(r"^\s*VerDate\b"),
    re.compile(r"\bJkt \d+ PO \d+ Frm \d+\b"),
    re.compile(r"\bon DSK\w+ with PRESDOC"),
    re.compile(r"^\s*[A-Z]+\.EPS</GPH>\s*$"),
    re.compile(r"^\s*[œŒ][–\-]?\s*$"),  # signature image placeholder glyphs
]

PRESIDENT_SIGNATURES = {
    "abrahamlincoln", "andrewjohnson", "usgrant", "ulyssessgrant", "rbhayes", "rutherfordbhayes",
    "jamesagarfield", "chesteraarthur", "grovercleveland", "benjharrison", "benjaminharrison",
    "williammckinley", "theodoreroosevelt", "williamhtaft", "wmhtaft", "woodrowwilson",
    "warrengharding", "calvincoolidge", "herberthoover", "franklindroosevelt", "harrystruman",
    "dwightdeisenhower", "johnfkennedy", "lyndonbjohnson", "richardnixon", "richardmnixon",
    "geraldrford", "jimmycarter", "ronaldreagan", "georgebush", "georgewbush", "williamjclinton",
    "barackobama", "donaldjtrump", "josephrbidenjr", "josephrbiden",
}
SURNAMES = (
    "lincoln johnson grant hayes garfield arthur cleveland harrison mckinley roosevelt taft "
    "wilson harding coolidge hoover truman eisenhower kennedy nixon ford carter reagan bush "
    "clinton obama trump biden"
).split()


def is_furniture(line: str) -> bool:
    return any(p.search(line) for p in FURNITURE)


def is_signature_line(line: str) -> bool:
    s = line.strip()
    if not s or len(s) > 50:
        return False
    if re.fullmatch(r"\(Presidential Sig\.?\)", s):
        return True
    collapsed = re.sub(r"[^a-z]", "", s.lower())
    if collapsed in PRESIDENT_SIGNATURES:
        return True
    letters = re.sub(r"[^A-Za-z]", "", s)
    if letters and letters.isupper() and len(s.split()) <= 5:
        return any(collapsed.endswith(n) or collapsed.endswith(n + "jr") for n in SURNAMES)
    return False


def lines_with_offsets(text: str, start: int = 0, end: int | None = None):
    """Yield (line_start, line_end_without_newline, line_text) for text[start:end]."""
    end = len(text) if end is None else end
    pos = start
    while pos < end:
        nl = text.find("\n", pos, end)
        stop = end if nl == -1 else nl
        yield pos, stop, text[pos:stop]
        pos = stop + 1


def number_pattern(number: str) -> str:
    """Regex for an order number such as '12944', '4359-A' or '10026A'."""
    m = re.fullmatch(r"(\d+)(?:[-\s]?([A-Za-z]+|\d+))?", number.strip())
    if not m:
        return re.escape(number)
    digits, suffix = m.group(1), m.group(2)
    pat = "[ ]?".join(digits)
    if suffix:
        pat += r"[ \t]*[-‐–]?[ \t]*" + re.escape(suffix)
        return pat + r"(?![A-Za-z0-9])"
    return pat + r"(?![\d])(?![ \t]*[-‐–][ \t]*[A-Z]\b)"


# ---------------------------------------------------------------------------
# Locating one order inside a text
# ---------------------------------------------------------------------------


@dataclass
class Located:
    doc_start: int          # start of the "Executive Order ..." heading line
    body_start: int         # first word after heading/title lines
    body_end: int           # start of the signature block
    doc_end: int            # end of the whole document (filing line etc.)
    heading_style: str      # "numbered" | "trailing_number" | "unnumbered_hint"
    signature_found: bool
    warnings: list = field(default_factory=list)


RECITAL_START = re.compile(
    r"^\s*(?:By virtue|By the authority|By authority|Under the authority|Under and by virtue|Under authority|"
    r"Pursuant to|In accordance with|In order to|Whereas|WHEREAS|W[ ]?HEREAS|Now,? therefore|NOW,? THEREFORE|"
    r"B[ ]?y[ ]?v[ ]?irtue|B[ ]?y the authority|Upon the recommendation|On the recommendation|"
    r"In the exercise of|As President|And it is|It is hereby|It is ordered|I hereby|I,? )",
    re.I,
)


def _is_title_line(line: str) -> bool:
    s = line.strip()
    if not s:
        return True
    if is_furniture(s) or DATE_LINE.match(s):
        return True
    if s.startswith("TITLE:"):
        return True
    if s in ("Washington", "Presidential Documents", "Title 3—", "Title 3—", "The President"):
        return True
    if RECITAL_START.match(s) or MARKER_L1.match(line) or SUB_MARKER.match(line):
        return False
    if not re.search(r"[a-z]", s):  # ALL CAPS title line
        return True
    if len(s) > 160 or s.endswith((".", ";", ":")) and not s.endswith("Jr."):
        return False
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z'’]*", s) if len(w) > 3]
    if not words:
        return True
    caps = sum(1 for w in words if w[0].isupper())
    return caps / len(words) >= 0.75


def _skip_title(text: str, after_heading: int, limit: int) -> int:
    """Return the offset of the first body line after heading/title lines."""
    n = 0
    for ls, le, line in lines_with_offsets(text, after_heading, limit):
        if n >= 14:
            return ls
        if not _is_title_line(line):
            return ls + (len(line) - len(line.lstrip()))
        n += 1
    return limit


def _find_heading(text: str, number: str):
    """Yield heading matches (start, end_of_line) for ``number`` that look like real headings."""
    pat = re.compile(r"(?im)^[ \t]*" + EXEC_ORDER + r"[ \t]*(?:N[ ]?o\.?[ \t]*)?\n?[ \t]*" + number_pattern(number))
    for m in pat.finditer(text):
        eol = text.find("\n", m.end())
        eol = len(text) if eol == -1 else eol
        line_start = text.rfind("\n", 0, m.start() + 1)
        line = text[line_start + 1:eol]
        tail = text[m.end():eol]
        if "|" in line or "Online by" in line or "American Presidency Project" in line:
            continue
        if not HEADING_TAIL_OK.match(tail):
            continue
        yield m.start(), eol


def _valid_generic(text: str, m) -> bool:
    eol = text.find("\n", m.end())
    eol = len(text) if eol == -1 else eol
    line_start = text.rfind("\n", 0, m.start() + 1)
    line = text[line_start + 1:eol]
    if "|" in line or "Online by" in line or "American Presidency Project" in line:
        return False
    return bool(HEADING_TAIL_OK.match(text[m.end():eol]))


def _next_doc_heading(text: str, after: int) -> int:
    """Offset of the next order heading after ``after`` (to cap a document), or len(text)."""
    best = len(text)
    for m in GENERIC_HEADING.finditer(text, after):
        if _valid_generic(text, m):
            best = m.start()
            break
    m = UNNUMBERED_HEADING.search(text, after)
    if m and m.start() < best:
        best = m.start()
    m = re.compile(r"(?m)^[ \t]*(?:A[ ]?P[ ]?R[ ]?O[ ]?C[ ]?L[ ]?A[ ]?M[ ]?A[ ]?T[ ]?I[ ]?O[ ]?N|Proclamation \d+ of)\b").search(text, after)
    if m and m.start() < best:
        best = m.start()
    return best


def _end_anchors(text: str, start: int, limit: int):
    """Return (body_end, doc_end, signature_found)."""
    cands = []
    for rx in (WHITE_HOUSE, FR_DOC, NO_LINE, FILED_WITH, APP_CITATION):
        m = rx.search(text, start, limit)
        if m:
            cands.append(m.start())
    for ls, le, line in lines_with_offsets(text, start, limit):
        if is_signature_line(line):
            cands.append(ls)
            break
    if not cands:
        return limit, limit, False
    body_end = min(cands)
    # doc end: through the FR Doc / [No.] filing lines, or up to the APP citation
    doc_end = None
    m = FR_DOC.search(text, body_end, limit)
    if m and m.start() - body_end < 1500:
        close = text.find("]", m.start(), min(limit, m.start() + 250))
        eol = text.find("\n", close if close != -1 else m.end())
        doc_end = (limit if eol == -1 else min(eol, limit))
    if doc_end is None:
        m = NO_LINE.search(text, body_end, limit)
        if m and m.start() - body_end < 600:
            eol = text.find("\n", m.end())
            doc_end = limit if eol == -1 else min(eol, limit)
    if doc_end is None:
        m = APP_CITATION.search(text, body_end, limit)
        if m and m.start() - body_end < 20000:
            doc_end = m.start()
    if doc_end is None:
        m = WHITE_HOUSE.search(text, body_end, limit)
        if m:
            pos = text.find("\n", m.end())
            # include one following date line
            for ls, le, line in lines_with_offsets(text, (pos + 1) if pos != -1 else limit, limit):
                if line.strip():
                    doc_end = le if DATE_LINE.match(line) else m.end()
                    break
            if doc_end is None:
                doc_end = m.end()
        else:
            doc_end = min(limit, body_end + 300)
    while doc_end > body_end and text[doc_end - 1] in " \t\n":
        doc_end -= 1
    return body_end, doc_end, True


# Lines that start a different document in an FR issue.
DOC_BREAK = re.compile(
    r"(?im)^[ \t]*(?:\[[ \t]*F[ ]?\.?[ ]?R[ ]?\.?[ \t]*D[ ]?o[ ]?c|\[[ \t]*No\.|"
    r"A[ ]?P[ ]?R[ ]?O[ ]?C[ ]?L[ ]?A[ ]?M[ ]?A[ ]?T[ ]?I[ ]?O[ ]?N\b|"
    r"B[ ]?Y[ ]+T[ ]?H[ ]?E[ ]+P[ ]?R[ ]?E[ ]?S[ ]?I[ ]?D[ ]?E[ ]?N[ ]?T\b)"
)


def _trailing_heading(text: str, no_pos: int, window: int = 20000):
    """The unnumbered "EXECUTIVE ORDER" heading that owns a "[No. NNNN]" line at
    ``no_pos`` (old FR style), or None if another document starts in between
    (proclamations use the same "[No. ...]" lines)."""
    heads = list(UNNUMBERED_HEADING.finditer(text, max(0, no_pos - window), no_pos))
    if not heads:
        return None
    h = heads[-1]
    if DOC_BREAK.search(text, h.end(), no_pos):
        return None
    return h


def locate_order(text: str, number: str, hint_unnumbered: bool = False) -> Located | None:
    """Find the order ``number`` in ``text``.

    Tries, in order: a numbered heading ("Executive Order 12944 ..."); an old
    Federal Register heading without number followed by a "[No. 7594]" line
    after the signature; and (only when ``hint_unnumbered`` is True, e.g. a
    page that is known to be this order) a heading line with no number.
    """
    first = None
    for hs, eol in _find_heading(text, number):
        limit = _next_doc_heading(text, eol + 1)
        body_start = _skip_title(text, eol + 1, limit)
        if body_start >= limit:
            continue
        body_end, doc_end, sig = _end_anchors(text, body_start, limit)
        if body_end <= body_start:
            continue
        loc = Located(hs, body_start, body_end, max(doc_end, body_end), "numbered", sig)
        if sig:
            return loc  # first heading whose document has a signature block
        if first is None:
            loc.warnings.append("no_signature_block_found")
            first = loc
    if first is not None:
        return first
    # Old FR style: number printed after the signature as "[No. 7594]".
    no_rx = re.compile(r"(?im)^[ \t]*\[[ \t]*No\.[ \t]*" + number_pattern(number).replace("(?![\\d])", "(?:\\]|1?[ \\t]*$)", 1))
    for m in no_rx.finditer(text):
        h = _trailing_heading(text, m.start())
        if h is None:
            continue
        eol = text.find("\n", h.end())
        body_start = _skip_title(text, eol + 1, m.start())
        # the document ends with the "[No. ...]" line, or the "[F. R. Doc ...]" line just after it
        stop = text.find("\n", m.end())
        stop = len(text) if stop == -1 else stop
        fr = FR_DOC.search(text, stop, min(len(text), stop + 200))
        if fr:
            close = text.find("]", fr.start(), min(len(text), fr.start() + 250))
            nl = text.find("\n", close if close != -1 else fr.end())
            stop = len(text) if nl == -1 else nl
        body_end, doc_end, sig = _end_anchors(text, body_start, stop)
        if body_end > m.start() or body_end <= body_start:
            continue
        loc = Located(h.start(), body_start, body_end, max(doc_end, body_end), "trailing_number", sig)
        loc.warnings.append("heading_has_no_number_matched_by_trailing_No_line")
        return loc
    if hint_unnumbered:
        for h in UNNUMBERED_HEADING.finditer(text):
            line_start = text.rfind("\n", 0, h.start() + 1)
            if "|" in text[line_start + 1:h.end()]:
                continue
            limit = _next_doc_heading(text, h.end() + 1)
            body_start = _skip_title(text, h.end() + 1, limit)
            body_end, doc_end, sig = _end_anchors(text, body_start, limit)
            if body_end <= body_start:
                continue
            loc = Located(h.start(), body_start, body_end, max(doc_end, body_end), "unnumbered_hint", sig)
            loc.warnings.append("heading_has_no_number_identity_from_file_name_only")
            return loc
    return None


def locate_body_only(text: str) -> Located | None:
    """For a text that is known (from its URL) to be one order but has no heading:
    the body starts at the first non-title line."""
    body_start = _skip_title(text, 0, len(text))
    if body_start >= len(text):
        return None
    limit = _next_doc_heading(text, body_start + 1)
    body_end, doc_end, sig = _end_anchors(text, body_start, limit)
    if body_end <= body_start:
        return None
    loc = Located(0, body_start, body_end, max(doc_end, body_end), "body_only", sig)
    loc.warnings.append("no_heading_in_text_identity_from_source_url_only")
    if not sig:
        loc.warnings.append("no_signature_block_found")
    return loc


def find_headings(text: str):
    """All order numbers that appear as headings in ``text`` (number, offset)."""
    found = []
    for m in GENERIC_HEADING.finditer(text):
        digits = m.group(1).replace(" ", "")
        suffix = m.group(2) or m.group(3) or ""
        if not _valid_generic(text, m):
            continue
        found.append((digits + (("-" + suffix) if suffix else ""), m.start()))
    for m in re.finditer(r"(?im)^[ \t]*\[[ \t]*No\.[ \t]*(\d{3,5})(?:\]|1?[ \t]*$)", text):
        if _trailing_heading(text, m.start()) is not None:
            found.append((m.group(1), m.start()))
    return found


# ---------------------------------------------------------------------------
# Structure markers
# ---------------------------------------------------------------------------

SEC_WORD = r"(?:S[ ]?e[ ]?c[ ]?t[ ]?i[ ]?o[ ]?n|S[ ]?E[ ]?C[ ]?T[ ]?I[ ]?O[ ]?N|S[ ]?e[ ]?c[ ]?\.|S[ ]?E[ ]?C[ ]?\.)"
# A section marker that OCR/pdftotext has run onto the end of the previous sentence.
INLINE_SEC = re.compile(r"(?<=[.;:][ \t])(?=" + SEC_WORD + r"[ \t]*\d+(?:[-.]\d+)*[A-Za-z]?[ \t]*\.[ \t]+[A-Z])")
# Level-1 markers. Matched against the whole text at a line's start (not just the
# line), so that the web-page form "Section 1\n. \nPurpose\n. ..." (number and
# period on separate lines) is recognised. The period after a section number is
# optional ("SEC. 2 (a) ...", "SEC. 2 The ..."); without it, the next word must
# start with a capital, "(" or a quote on the same line.
MARKER_L1 = re.compile(
    r"[ \t]*(?:"
    r"(?P<sec>" + SEC_WORD + r"[ \t]*(?P<secnum>\d+(?:[-.]\d+)*[A-Za-z]?|[IVX]{1,5}(?=[ \t]*\n?[ \t]*\.))"
    r"(?:(?P<secdot>[ \t]*\n?[ \t]*\.)|(?=[ \t]+[A-Z(\"“‘])))"
    r"|(?P<dash>(?P<dashnum>\d+-\d+)[ \t]*\.)(?=[ \t])"
    r"|(?P<num>(?P<numnum>\d{1,3})[ \t]?\.)(?=[ \t]+[\"“‘(A-Z]|[ \t]*\n[ \t]*[A-Z])"
    r"|(?P<part>(?:PART|Part)[ \t]+(?P<partnum>[IVXLC]+|\d+)\b)"
    r")"
)
ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10,
         "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15, "XVI": 16, "XVII": 17, "XVIII": 18, "XIX": 19, "XX": 20}
SUB_MARKER = re.compile(r"^[ \t]*\([ ]?(?P<key>[a-z]{1,2}|\d{1,3}|[ivx]+)[ ]?\)")
INLINE_FIRST_SUB = re.compile(r"[.,:—–-][ \t]*\n?[ \t]*\([ ]?(?P<key>a|1)[ ]?\)[ \t]")

LETTERS = "abcdefghijklmnopqrstuvwxyz"


def _next_key(kind: str, key: str) -> str:
    if kind == "digit":
        return str(int(key) + 1)
    i = LETTERS.find(key[-1])
    if len(key) == 1 and i < 25:
        return LETTERS[i + 1]
    if len(key) == 1:
        return "aa"
    return key[0] + LETTERS[LETTERS.find(key[1]) + 1] if key[1] != "z" else key + "a"


# A line that ends a sentence or list item (so the next line may start a new
# unit). Closing quotes may be typographic (” ’’) or typed ('' ` ").
TERMINAL = re.compile(r"(?:[.:;—][\"”’)'`\s]*(?:[ \t]-)?|[;,]\s*(?:and|or)|\bfollows|:\s*[\"“‘`]+)\s*$")


def _quote_state(text: str, start: int, end: int):
    """Return a function giving True if position p (start<=p<end) is inside a quotation."""
    marks = []
    inside = False
    i = start
    while i < end:
        c = text[i]
        two = text[i:i + 2]
        if two == "‘‘" or c == "“" or two == "``":
            inside = True
            i += 2 if two in ("‘‘", "``") else 1
            marks.append((i, inside))
            continue
        if two == "’’" or c == "”" or two == "''":
            inside = False
            i += 2 if two in ("’’", "''") else 1
            marks.append((i, inside))
            continue
        if c == '"':
            prev = text[i - 1] if i > start else "\n"
            inside = prev in " \t\n(—-" if not inside else False
            marks.append((i + 1, inside))
        i += 1

    def at(p):
        state = False
        lo, hi = 0, len(marks)
        while lo < hi:
            mid = (lo + hi) // 2
            if marks[mid][0] <= p:
                lo = mid + 1
            else:
                hi = mid
        if lo:
            state = marks[lo - 1][1]
        return state

    return at, inside


def _content_lines(text, start, end):
    """(line_start, content_start, line_text) for non-furniture lines in [start,end)."""
    out = []
    for ls, le, line in lines_with_offsets(text, start, end):
        if is_furniture(line):
            continue
        cuts = [m.start() for m in INLINE_SEC.finditer(line)]
        pieces = [0] + cuts
        for k, a in enumerate(pieces):
            b = pieces[k + 1] if k + 1 < len(pieces) else len(line)
            piece = line[a:b]
            if k and not piece.strip():
                continue
            out.append((ls + a, ls + a + len(piece) - len(piece.lstrip()), piece))
    return out


def _prev_ok(lines, idx, body_start):
    """Previous non-empty content line ends a sentence/list item, or there is a blank line."""
    j = idx - 1
    blank = False
    while j >= 0 and not lines[j][2].strip():
        blank = True
        j -= 1
    if j < 0:
        return True
    if blank:
        return True
    return bool(TERMINAL.search(lines[j][2].rstrip()))


def _major(key: str) -> int:
    m = re.match(r"\d+", key)
    return int(m.group()) if m else 0


def _keytuple(key: str):
    """Sortable key. Carter-style "1-101" means part 1, section 1, item 01."""
    nums = [int(x) for x in re.findall(r"\d+", key)]
    if not nums:
        return (0,)
    if "-" in key and len(nums) == 2:
        a, b = nums
        return (a, b // 100, b % 100) if b >= 100 else (a, b, 0)
    return tuple(nums)


def _marker_at(text, cs, end):
    """MARKER_L1 match at content start ``cs`` (may span a line break), or None."""
    m = MARKER_L1.match(text, cs, end)
    if m and m.end() == cs:
        return None
    return m


def _level1(text, start, end, inq, lines, warnings=None):
    """Validated level-1 markers: list of dicts(kind, key, start, marker_end).

    Section numbers must rise. A gap ("Sec. 3." then "Sec. 5.") is accepted for
    markers printed with a period and noted in ``warnings``; a marker without a
    period after the number must be exactly the next number."""
    found = {"sec": [], "num": [], "dash": []}
    parts = []
    for idx, (ls, cs, line) in enumerate(lines):
        m = _marker_at(text, cs, end)
        if not m or inq(cs):
            continue
        if not (idx == 0 or _prev_ok(lines, idx, start)):
            continue
        if m.group("part"):
            parts.append({"kind": "part", "key": m.group("partnum"), "start": cs, "marker_end": m.end()})
            continue
        for kind, g in (("sec", "secnum"), ("dash", "dashnum"), ("num", "numnum")):
            if m.group(kind):
                key = m.group(g)
                printed = key
                if key in ROMAN:
                    key = str(ROMAN[key])
                found[kind].append({"kind": kind, "key": key, "printed": printed, "start": cs, "marker_end": m.end(),
                                    "dotted": kind != "sec" or bool(m.group("secdot"))})
                break
    best = []
    gaps = []
    for kind in ("sec", "dash", "num"):
        seq = []
        last = None
        kind_gaps = []
        for c in found[kind]:
            k = _keytuple(c["key"])
            if last is None:
                ok = k[0] <= 2 or k[0] % 100 == 1
            elif kind == "num":
                ok = k[0] == last[0] + 1
            elif kind == "sec":
                ok = k > last and k[0] <= last[0] + 10
                if ok and not c["dotted"]:
                    ok = k[0] == last[0] + 1 or (k[0] == last[0] and len(k) > 1)
                if ok and k[0] > last[0] + 1:
                    kind_gaps.append(f"{last[0]}->{k[0]}")
            else:
                ok = k > last and (k[0] <= last[0] + 1 or k[0] % 100 in (0, 1))
            if ok:
                seq.append(c)
                last = k
        if kind == "sec" and seq:
            best, gaps = seq, kind_gaps
            break
        if len(seq) > len(best) and (kind != "num" or len(seq) >= 2 or (seq and seq[0]["key"] == "1")):
            best, gaps = seq, kind_gaps
    if warnings is not None and gaps:
        warnings.append("section_number_gap_" + ",".join(gaps))
    return best, parts


def _level2(text, start, end, inq, lines, marker_end):
    """Validated sub-markers ((a)/(1)) inside one unit. Returns list of dicts."""
    subs = []
    expected = None
    kind = None
    # inline first sub-marker right after the section heading, e.g. "Sec. 5. Title. (a) ..."
    head_zone = text[marker_end:min(end, marker_end + 220)]
    m = INLINE_FIRST_SUB.search(head_zone)
    lead = re.match(r"[ \t]*\([ ]?(?P<key>a|1)[ ]?\)[ \t]", head_zone)
    if lead and (not m or m.start() > lead.start()):
        m = lead
    first_inline = None
    if m:
        pre = head_zone[:m.start()]
        if "\n\n" not in pre and len(pre) < 200 and not inq(marker_end + m.start()):
            pos = marker_end + m.start() + head_zone[m.start():].find("(")
            first_inline = pos
            kind = "digit" if m.group("key") == "1" else "letter"
            subs.append({"key": m.group("key"), "start": pos, "inline": True})
            expected = _next_key(kind, m.group("key"))
    for idx, (ls, cs, line) in enumerate(lines):
        if cs < marker_end or cs >= end:
            continue
        if first_inline is not None and cs <= first_inline:
            continue
        m = SUB_MARKER.match(line)
        if not m or inq(cs):
            continue
        key = m.group("key")
        if expected is None:
            if key not in ("a", "1"):
                continue
            kind = "digit" if key == "1" else "letter"
        elif key != expected:
            continue
        if not _prev_ok(lines, idx, start) and cs != marker_end:
            continue
        subs.append({"key": key, "start": cs, "inline": False})
        expected = _next_key(kind, key)
    if kind == "letter":
        pass
    # old style lower-case "a." items when nothing else was found
    if not subs:
        expected = "a"
        for idx, (ls, cs, line) in enumerate(lines):
            if cs < marker_end or cs >= end:
                continue
            mm = re.match(r"^[ \t]*([a-z])\.[ \t]+[A-Z\"“]", line)
            if mm and mm.group(1) == expected and not inq(cs) and _prev_ok(lines, idx, start):
                subs.append({"key": mm.group(1), "start": cs, "inline": False})
                expected = _next_key("letter", expected)
        if len(subs) < 2:
            subs = []
    return subs


# ---------------------------------------------------------------------------
# Paragraphs, recitals, kinds, targets
# ---------------------------------------------------------------------------

OPERATIVE_PHRASE = re.compile(
    r"(?:(?i:\bit\s+is\s+(?:hereby\s+)?ordered\b)|\bI\s+(?:do\s+)?(?i:hereby)\b|(?i:\bdo\s+hereby\b)|"
    r"\bI,?\s+[A-Z][A-Za-z. \n]{2,40},[^.;]{0,160}?\bdo\b|"
    r"(?i:\bhereby\s+(?:order|direct|prescribe|establish|designate|authorize|declare|extend|revoke|amend|exempt|withdraw|reserve)\b)|"
    r"(?i:\bare\s+hereby\b)|(?i:\bis\s+hereby\b))"
)
RECITAL_LEAD = re.compile(
    r"^\s*(?:B[ ]?y[ ]+v[ ]?i[ ]?r[ ]?t[ ]?u[ ]?e|By the authority|By authority|Under the authority|Under and by virtue|"
    r"Under authority|Pursuant to|In accordance with|In order to|Upon the recommendation|On the recommendation|"
    r"In the exercise of|As President|By direction|Under and pursuant|Under the provisions|In pursuance of|"
    r"Now,? therefore|NOW,? THEREFORE|And,? (?:it is|whereas)|AND,? (?:IT IS|WHEREAS))",
    re.I,
)
ENACTING_ONLY = re.compile(
    r"(?i)(?:it\s+is\s+(?:hereby\s+)?(?:ordered|directed)|I\s+(?:do\s+)?hereby\s+(?:order|prescribe|direct)|"
    r"(?:do\s+)?hereby\s+(?:order|prescribe|direct))(?:,?\s+as[ ]?f[ ]?o[ ]?l[ ]?l[ ]?o[ ]?w[ ]?s|\s+that|\s+the\s+following)?\s*[:\u2014\u2013.,-]*\s*$"
)


def split_recital(text: str, s: int, e: int):
    """Split one preamble paragraph into (recital_span or None, operative_span or None).

    "Whereas ..." and "By the authority ..., it is hereby ordered as follows:" are
    recitals/enacting words (not clauses). In a fused sentence such as
    "By virtue of ..., it is hereby ordered that X" the recital ends where the
    operative words begin.
    """
    para = text[s:e]
    if re.match(r"\s*(?:Whereas|WHEREAS|W[ ]?HEREAS)\b", para):
        return (s, e), None
    lead = bool(RECITAL_LEAD.match(para))
    pronoun = bool(re.match(r"\s*I,? [A-Z]", para))  # "I, Franklin D. Roosevelt, President ..."
    m = OPERATIVE_PHRASE.search(para)
    if m is None:
        return ((s, e), None) if lead else (None, (s, e))
    tail = " ".join(para[m.start():].split())
    if ENACTING_ONLY.match(tail):
        return (s, e), None
    if not (lead or pronoun):
        return None, (s, e)
    cut = s + m.start()
    if re.match(r"(?i)(?:do|hereby|are|is)\b", para[m.start():]):
        # back up to the start of the clause holding the verb ("the lands ... are hereby");
        # only at a comma/semicolon followed by a space (not "$1,000,000").
        pron = [x.start() for x in re.finditer(r"\bI,?\s+(?=[A-Z])", para[:m.start()])]
        backs = [x.end() for x in re.finditer(r"[,;]\s+(?=[A-Z]|the |all |so much |there |any |each |such )", para[:m.start()])]
        subj_eo = [x.end() for x in re.finditer(r"[,;]\s+(?=(?:the\s)?Execu(?:[-­][ \t]*\n[ \t]*)?tive\s+[Oo]rders?\b|(?:Part|Section|Paragraph|Rule|Schedule)\s)", para[:m.start()])]
        lower = [x.end() for x in re.finditer(r"[,;]\s+(?=the |all |so much |there |any |each |such )", para[:m.start()])]
        # "I, WILLIAM J. CLINTON, President ..., find ... and hereby declare": the clause starts at "I,"
        if re.match(r"(?i)(?:do|hereby)\b", para[m.start():]) and pron:
            cut = s + pron[-1]
        elif subj_eo:
            cut = s + subj_eo[-1]
        elif lower:
            cut = s + lower[-1]
        else:
            cut = s + backs[-1] if backs else s
    while cut < e and text[cut] in " \t\n":
        cut += 1
    if cut <= s:
        return None, (s, e)
    return (s, cut), (cut, e)


def paragraphs(text: str, start: int, end: int):
    """Split [start,end) into paragraphs: blank-line blocks, or long lines (web transcriptions)."""
    seg = text[start:end]
    if re.search(r"\n[ \t]*\n", seg):
        out = []
        for m in re.finditer(r"(?s)(?:[^\n]|\n(?![ \t]*\n))+", seg):
            if m.group().strip():
                s, e = start + m.start(), start + m.end()
                out.append(_trim(text, s, e))
        return out
    lines = [l for l in seg.split("\n") if l.strip()]
    if lines and sum(len(l) for l in lines) / len(lines) > 180:
        out = []
        pos = start
        for ls, le, line in lines_with_offsets(text, start, end):
            if line.strip():
                out.append(_trim(text, ls, le))
        return out
    if not seg.strip():
        return []
    # Wrapped print text without blank lines: start a new paragraph at a line that
    # begins a recital ("WHEREAS", "NOW, THEREFORE", "And it is ...") after a line
    # that ended a sentence or clause.
    cuts = [start]
    prev = ""
    for ls, le, line in lines_with_offsets(text, start, end):
        if prev.rstrip().endswith((";", ":", ".", "; and", "; and,")) and re.match(
            r"\s*(?:W[ ]?HEREAS|Whereas|NOW,? THEREFORE|Now,? [Tt]herefore|AND,? IT IS|And,? it is)\b", line
        ):
            cuts.append(ls)
        if line.strip():
            prev = line
    cuts.append(end)
    out = [_trim(text, a, b) for a, b in zip(cuts, cuts[1:])]
    return [x for x in out if x[1] > x[0]]


def _trim_furniture(text, s, e):
    """Drop blank/furniture lines at both ends of [s,e), then whitespace."""
    s, e = _trim(text, s, e)
    while e > s:
        ls = text.rfind("\n", s, e)
        last = text[(ls + 1 if ls != -1 else s):e]
        if last.strip() and not is_furniture(last):
            break
        e = ls if ls != -1 else s
        s, e = _trim(text, s, e)
    while s < e:
        nl = text.find("\n", s, e)
        first = text[s:(nl if nl != -1 else e)]
        if first.strip() and not is_furniture(first):
            break
        s = nl + 1 if nl != -1 else e
        s, e = _trim(text, s, e)
    return s, e


def _trim(text, s, e):
    while s < e and text[s] in " \t\n\r":
        s += 1
    while e > s and text[e - 1] in " \t\n\r":
        e -= 1
    return (s, e)


EO_REF = re.compile(
    r"\b(?:Execu(?:[-­][ \t]*\n[ \t]*)?tive\s+Orders?|E\.\s?O\.|Ex\.\s+Ord\.)[ \t\n]+(?:Nos?\.?[ \t\n]*)?(\d{1,5})(?:[ \t]*-[ \t]*([A-Z])\b)?"
)
EO_REF_LIST = re.compile(r"(?:,?[ \t\n]+(?:and|or)?[ \t\n]*|,[ \t\n]*)(\d{3,5})\b")


def eo_refs(chunk: str, with_head: bool = False):
    """Order numbers cited in ``chunk``: (number, position) pairs, or with
    ``with_head`` (number, position, position of the "Executive Order(s)" words
    that introduce it), so items of a list ("Nos. 12887 and 12912") share the
    context of the list's head."""
    out = []
    for m in EO_REF.finditer(chunk):
        num = m.group(1) + ("-" + m.group(2) if m.group(2) else "")
        out.append((num, m.start(), m.start()) if with_head else (num, m.start()))
        pos = m.end()
        while True:
            mm = EO_REF_LIST.match(chunk, pos)
            if not mm:
                break
            out.append((mm.group(1), mm.start(1), m.start()) if with_head else (mm.group(1), mm.start(1)))
            pos = mm.end()
    return out


def _unquoted(chunk: str) -> str:
    """Remove quoted inserted text so targets/verbs come from the order's own words."""
    out = re.sub(r"(?s)(‘‘|“|``).*?(’’|”|''|$)", " ", chunk)
    return re.sub(r'(?s)(?<![A-Za-z])".*?("|$)', " ", out)


def classify(chunk: str, heading: str, parent_heading: str, self_number: str, context: str = ""):
    """Return (kind, related_orders[]) for one clause text.

    ``context`` is the lead-in of the parent unit (e.g. "The following executive
    actions are hereby revoked:"); its verb applies to the listed items."""
    own = _unquoted(chunk)[:1500]
    h = f"{heading} {parent_heading}".lower()
    refs = []
    for num, pos, head in eo_refs(own, with_head=True):
        if num.lstrip("0") == self_number.lstrip("0"):
            continue
        before = own[max(0, head - 45):head].lower()
        role = "mentioned_as_prior_amender" if re.search(r"(?:as amended by|amended by|as added by)[^.;]*$", before) else "target_candidate"
        ref = {"instrument_id": "EO:" + num, "role": role}
        if ref not in refs:
            refs.append(ref)
    targets = [r for r in refs if r["role"] == "target_candidate"]
    low = " ".join((own + " " + _unquoted(context)[-400:]).lower().split())
    # the clause's own words without its marker/heading ("Sec. 5. Effective date. This order ...")
    bare = re.sub(r"^(?:(?:sec(?:tion)?\.?\s*[\divx]+[a-z]?\s*\.?|\d+\.|\([a-z0-9]+\))\s*)+", "", low)
    if heading and bare.startswith(heading.lower()):
        bare = bare[len(heading):].lstrip(" .,:")
    if targets and re.search(r"\b(?:is|are) (?:hereby )?(?:further )?amended\b|\bamended to read\b|\bhereby amend|\bis amended by\b|\bare amended by\b|\bamend(?:s|ing)? (?:section|subsection|paragraph|part|executive order)", low):
        return "amends_other_order", refs
    if targets and re.search(r"\b(?:is|are) (?:hereby )?(?:revoked|superseded|rescinded|terminated|abolished)\b|\bhereby revoke|\bsupersedes?\b|\brevokes?\b", low):
        return "revokes_or_supersedes_other_order", refs
    if re.search(r"\bexecutive order of [a-z]+\.? \d{1,2},? \d{4}[^.]*\b(?:is|are) (?:hereby )?(?:revoked|superseded|amended)", low):
        return "revokes_or_amends_unnumbered_order", refs
    if re.search(r"general provisions|judicial review|construction|severability", h) or re.match(
        r"(?:\([a-z]\) )?(?:nothing in this order shall be construed|this order (?:shall be|is) (?:implemented consistent|not intended to)|this order is intended only|if any provision of this order)", bare
    ):
        return "general_provisions", refs
    if "definition" in h or re.match(r"(?:\([a-z0-9]\) )?(?:for (?:the )?purposes of this order|as used in this order)", bare):
        return "definitions", refs
    if re.search(r"\bpurpose\b|\bpolicy\b|\bfindings?\b", h):
        return "purpose_or_policy", refs
    if re.search(r"effective date", h) or re.search(r"^(?:\S+ )?(?:this order|the provisions of this order|this amendment) shall (?:become effective|take effect|be effective)", bare):
        return "effective_date", refs
    return "operative", refs


# A section heading right after the marker: "Sec. 2. Policy. ..." or the web-page
# form "Sec. 2\n. \nPolicy\n. ..." (heading and its period on separate lines).
HEADING_TEXT = re.compile(r"[ \t]*\n?[ \t]*([A-Z][^.\n]{1,80}?)[ \t]*\n?[ \t]*[.,][ \t]*(?:\n|(?=[A-Z(\"“‘])|$)")
VERBISH = re.compile(r"\b(?:shall|is|are|was|were|hereby|may|will|must|be|has|have)\b", re.I)


def _heading_after(text: str, pos: int, end: int) -> str:
    m = HEADING_TEXT.match(text, pos, min(end, pos + 120))
    if not m:
        return ""
    h = m.group(1).strip()
    # web-page form "Sec. 3\n. \nRecognizing Women Are ...\n." : the heading is set off by
    # its own line and period, so a verb inside it does not make it a sentence
    own_line = bool(re.match(r"[ \t]*\n", text[pos:m.start(1)])) and bool(re.match(r"[ \t]*\n[ \t]*\.", text[m.end(1):m.end()]))
    if (VERBISH.search(h) and not own_line) or len(h.split()) > (15 if own_line else 10):
        return ""
    return h


# ---------------------------------------------------------------------------
# Segmentation
# ---------------------------------------------------------------------------


def _label(kind, key):
    return {"sec": f"Sec. {key}", "dash": f"Sec. {key}", "num": f"para. {key}", "sub": f"({key})"}.get(kind, key)


def _scope_piece(kind, key):
    return {"sec": f"sec{key}", "dash": f"sec{key}", "num": f"para{key}", "part": f"part{key}"}.get(kind, key)


def _is_heading_only(para: str) -> bool:
    """A short ALL-CAPS line such as "CITIZENSHIP" or "PART I—GENERAL" (not a clause)."""
    s = para.strip()
    if not s or "\n" in s or len(s) > 90:
        return False
    if not re.search(r"[a-z]", s):
        return True
    # a short italic sub-heading such as "Immigrants" or "Contracts for Supplies"
    return len(s) <= 60 and len(s.split()) <= 6 and not s.endswith((".", ";", ":", ",")) and not VERBISH.search(s) and s[0].isupper()


def _merge_quoted(text, spans, inq):
    """Join paragraphs of quoted inserted text to the paragraph that introduces them."""
    out = []
    for ps, pe in spans:
        starts_quote = text[ps] in "\"“‘`"
        if out and (inq(ps) or (starts_quote and text[out[-1][0]:out[-1][1]].rstrip().endswith((":", "—", "-")))
                    or (starts_quote and inq(out[-1][1] - 1))):
            out[-1] = (out[-1][0], pe)
        else:
            out.append((ps, pe))
    return out


def ocr_noise(text: str, start: int, end: int) -> float:
    """Share of 1-letter tokens that are not ordinary words: high for spaced-out OCR."""
    chunk = re.sub(r"\([A-Za-z]{1,4}\)|['’]s\b", " ", text[start:end])
    toks = re.findall(r"[A-Za-z]+", chunk)
    if len(toks) < 40:
        return 0.0
    singles = sum(1 for t in toks if len(t) == 1 and t.islower() and t != "a")
    return singles / len(toks)


def _preamble(text, bs, pre_end, parts, recitals, units, inq):
    """Classify the paragraphs before the first numbered unit."""
    ops = []
    paras = [pp for pp in paragraphs(text, bs, pre_end) if not (parts and any(pp[0] <= p["start"] < pp[1] for p in parts))]
    for ps, pe in _merge_quoted(text, paras, inq):
        if _is_heading_only(text[ps:pe]):
            continue
        rec, op = split_recital(text, ps, pe)
        if rec:
            recitals.append(_trim(text, *rec))
        if op:
            ops.append(op)
    for k, op in enumerate(ops, 1):
        piece = "preamble-op" if len(ops) == 1 else f"preamble-op{k}"
        units.append((piece, "operative words before the numbered sections", op[0], op[1], "", "", True))


PLACEHOLDER = re.compile(r"(?i)\b(?:was|were|has not been|have not been) not (?:published|made public|received for publication)|\bnot (?:published|made public) in the Federal Register|\bnot printed in the Federal Register")


def segment(text: str, loc: Located, instrument_id: str) -> dict:
    """Split a located order into recitals and clause units (offsets into ``text``)."""
    number = instrument_id.split(":", 1)[1]
    bs, be = loc.body_start, loc.body_end
    warnings = list(loc.warnings)
    inq, unbalanced = _quote_state(text, bs, be)
    inq_for_merge = inq
    lines = _content_lines(text, bs, be)
    l1_warn = []
    l1, parts = _level1(text, bs, be, inq, lines, l1_warn)
    if not l1 and unbalanced:
        warnings.append("unbalanced_quotes_retry_without_quote_tracking")
        inq_for_merge = inq
        inq = lambda p: False  # noqa: E731
        l1_warn = []
        l1, parts = _level1(text, bs, be, inq, lines, l1_warn)
    warnings += l1_warn
    units = []        # (scope_piece, label, start, end, heading, parent_heading, flag)
    context_of = {}   # child start -> parent lead-in text
    recitals = []
    structure = "unnumbered_paragraphs"
    first_l1 = l1[0]["start"] if l1 else None

    if l1:
        structure = {"sec": "sections", "dash": "dash_numbered_sections", "num": "numbered_paragraphs"}[l1[0]["kind"]]
        _preamble(text, bs, first_l1, parts, recitals, units, inq)
        bounds = [c["start"] for c in l1] + [be]

        def part_for(pos):
            key = None
            for p in parts:
                if p["start"] < pos:
                    key = p["key"]
            return key
        for i, c in enumerate(l1):
            s, e = c["start"], bounds[i + 1]
            # do not swallow a following PART heading
            for p in parts:
                if s < p["start"] < e:
                    e = p["start"]
            s, e = _trim(text, s, e)
            heading = _heading_after(text, c["marker_end"], e)
            subs = _level2(text, s, e, inq, lines, c["marker_end"])
            piece = _scope_piece(c["kind"], c["key"])
            label = _label(c["kind"], c.get("printed", c["key"]))
            if not subs:
                rest = text[c["marker_end"]:e].strip()
                if heading and rest.startswith(heading):
                    rest = rest[len(heading):].strip(" .,\n\t")
                if len(re.sub(r"[^A-Za-z]", "", rest)) < 15:
                    continue  # heading-only unit, e.g. Carter-style "1-1. Establishment."
                units.append((piece, label, s, e, heading, "", False))
                continue
            intro_end = subs[0]["start"]
            intro = text[c["marker_end"]:intro_end]
            intro_words = intro.strip()
            if heading and intro_words.startswith(heading):
                intro_words = intro_words[len(heading):].strip(" .,\n\t")
            if len(re.sub(r"[^A-Za-z]", "", intro_words)) >= 15:
                units.append((piece, label + " (lead-in)", *_trim(text, s, intro_end), heading, "", "lead_in"))
            sb = [x["start"] for x in subs] + [e]
            for j, sub in enumerate(subs):
                ss, se = _trim(text, sub["start"], sb[j + 1])
                context_of[ss] = text[s:intro_end]
                units.append((f"{piece}({sub['key']})", f"{label}({sub['key']})", ss, se, "", heading, False))
        # part prefixes only when needed for uniqueness
        seen = {}
        for u in units:
            seen[u[0]] = seen.get(u[0], 0) + 1
        if any(v > 1 for v in seen.values()):
            new = []
            for u in units:
                prefix = part_for(u[2])
                new.append(((f"part{prefix}-" + u[0]) if prefix else u[0],) + u[1:])
            units = new
    else:
        # No numbered sections: maybe top-level (a)/(1) items, else paragraphs.
        tops = _level2(text, bs, be, inq, lines, bs)
        if len(tops) >= 2:
            structure = "top_level_lettered_items"
            _preamble(text, bs, tops[0]["start"], [], recitals, units, inq)
            sb = [x["start"] for x in tops] + [be]
            for j, sub in enumerate(tops):
                ss, se = _trim(text, sub["start"], sb[j + 1])
                units.append((f"({sub['key']})", f"({sub['key']})", ss, se, "", "", False))
        else:
            paras = paragraphs(text, bs, be)
            ops = []
            for ps, pe in _merge_quoted(text, paras, inq_for_merge):
                if _is_heading_only(text[ps:pe]):
                    continue
                rec, op = split_recital(text, ps, pe)
                if rec:
                    recitals.append(_trim(text, *rec))
                if op:
                    ops.append(op)
            if len(ops) == 1:
                structure = "single_operative_paragraph"
                units.append(("whole", "whole operative text", ops[0][0], ops[0][1], "", "", False))
            else:
                for k, op in enumerate(ops, 1):
                    units.append((f"p{k}", f"unnumbered paragraph {k}", op[0], op[1], "", "", False))
            if len(paras) == 1 and len(text[bs:be]) > 1500 and "\n" in text[bs:be]:
                warnings.append("long_unnumbered_text_paragraph_breaks_not_recoverable")

    noise = ocr_noise(text, bs, be)
    if noise > 0.04:
        warnings.append(f"ocr_text_noisy_{noise:.2f}")
    if len(re.findall(r"(?m)(?:-{5,}|_{6,})[ \t]*\d{3,5}[ \t]*$", text[bs:be])) >= 2:
        warnings.append("text_contains_contents_listing_fragments_columns_may_be_interleaved")

    # Annex / schedules printed after the signature but before the filing line
    tail_start = loc.body_end
    m = WHITE_HOUSE.search(text, tail_start, loc.doc_end)
    if m:
        after = text.find("\n", m.end())
        after = loc.doc_end if after == -1 else after
        # skip the date line
        for ls, le, line in lines_with_offsets(text, after + 1, loc.doc_end):
            if line.strip():
                if DATE_LINE.match(line):
                    after = le
                break
        annex_end = loc.doc_end
        fr = FR_DOC.search(text, after, loc.doc_end)
        if fr:
            annex_end = fr.start()
        content = [l for _, _, l in lines_with_offsets(text, after, annex_end) if l.strip() and not is_furniture(l)]
        if sum(len(l) for l in content) > 200:
            s, e = _trim(text, after, annex_end)
            units.append(("annex", "text printed after the signature (annex/schedule)", s, e, "", "", "annex"))

    clauses = []
    unit_info = []
    used = set()
    for piece, label, s, e, heading, parent_heading, flag in units:
        context = context_of.get(s, "")
        s, e = _trim_furniture(text, s, e)
        if e <= s:
            continue
        chunk = text[s:e]
        kind, refs = classify(chunk, heading, parent_heading, number, context)
        if flag is True:
            kind = "operative_in_preamble"
        elif flag == "lead_in" and kind == "operative":
            kind = "lead_in"
        elif flag == "annex":
            kind = "annex_after_signature"
        sid = f"{instrument_id}#{piece}"
        n = 2
        while sid in used:
            sid = f"{instrument_id}#{piece}-dup{n}"
            n += 1
        used.add(sid)
        furniture = [l for _, _, l in lines_with_offsets(text, s, e) if is_furniture(l)]
        clauses.append({
            "scope_id": sid,
            "label": label,
            "heading": heading or parent_heading or None,
            "clause_kind": kind,
            "related_orders": refs,
            "start": s,
            "end": e,
            "contains_page_furniture": bool(furniture),
        })
        unit_info.append((piece, flag, s, e))
    warnings += completeness_problems(text, bs, be, inq, lines, l1, unit_info)
    flat_body = " ".join(text[bs:be].split())
    if len(flat_body) < 400 and PLACEHOLDER.search(flat_body):
        warnings.append("source_says_order_text_not_published")
        clauses = []
    if not clauses:
        warnings.append("no_operative_unit_found")
    # Identity check: an order does not cite its own number in a recital ("Whereas
    # ... requested in Executive Order No. 2859 of May 11, 1918") or as an order
    # that is amended or revoked. That pattern means the page holds a LATER order
    # filed under this number. (Citing itself inside contract or form text it
    # prescribes, e.g. EO 11246's "Section 202 of Executive Order No. 11246", is normal.)
    body = text[bs:be]
    rec_spans = [(s - bs, e - bs) for s, e in recitals]
    own_doubt, own_other = False, False
    for n, p in eo_refs(body):
        if n.lstrip("0") != number.lstrip("0"):
            continue
        a = max(body.rfind(".", 0, p), body.rfind(";", 0, p), body.rfind("\n\n", 0, p))
        b = min([x for x in (body.find(".", p + 25), body.find(";", p)) if x != -1] or [len(body)])
        sentence = body[a + 1:b].lower()
        if any(s <= p < e for s, e in rec_spans) or re.search(
                r"\b(?:is|are) (?:hereby )?(?:further )?(?:amended|revoked|superseded|rescinded)\b|\bas amended\b|\bamending\b|\brevoking\b", sentence):
            own_doubt = True
        else:
            own_other = True
    if own_doubt:
        warnings.append("body_cites_its_own_order_number_identity_doubtful")
    elif own_other:
        warnings.append("note_body_cites_its_own_number_in_operative_text")
    return {
        "structure": structure,
        "clauses": clauses,
        "recitals": [{"start": s, "end": e} for s, e in recitals if e > s],
        "title": {"start": loc.doc_start, "end": loc.body_start},
        "signature_block": {"start": loc.body_end, "end": loc.doc_end},
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Identity evidence inside the located document: signer and dates
# ---------------------------------------------------------------------------

# Years each president could have signed (inclusive). Keys are the letters of a
# signature line, lower case; surname keys are used when the full name is absent.
PRESIDENT_YEARS = {
    "abrahamlincoln": [(1861, 1865)], "andrewjohnson": [(1865, 1869)], "usgrant": [(1869, 1877)],
    "ulyssessgrant": [(1869, 1877)], "rbhayes": [(1877, 1881)], "rutherfordbhayes": [(1877, 1881)],
    "jamesagarfield": [(1881, 1881)], "chesteraarthur": [(1881, 1885)], "grovercleveland": [(1885, 1889), (1893, 1897)],
    "benjharrison": [(1889, 1893)], "benjaminharrison": [(1889, 1893)], "williammckinley": [(1897, 1901)],
    "theodoreroosevelt": [(1901, 1909)], "williamhtaft": [(1909, 1913)], "wmhtaft": [(1909, 1913)],
    "woodrowwilson": [(1913, 1921)], "warrengharding": [(1921, 1923)], "calvincoolidge": [(1923, 1929)],
    "herberthoover": [(1929, 1933)], "franklindroosevelt": [(1933, 1945)], "harrystruman": [(1945, 1953)],
    "dwightdeisenhower": [(1953, 1961)], "johnfkennedy": [(1961, 1963)], "lyndonbjohnson": [(1963, 1969)],
    "richardnixon": [(1969, 1974)], "richardmnixon": [(1969, 1974)], "geraldrford": [(1974, 1977)],
    "jimmycarter": [(1977, 1981)], "ronaldreagan": [(1981, 1989)], "georgebush": [(1989, 1993)],
    "georgewbush": [(2001, 2009)], "williamjclinton": [(1993, 2001)], "barackobama": [(2009, 2017)],
    "donaldjtrump": [(2017, 2021), (2025, 2029)], "josephrbidenjr": [(2021, 2025)], "josephrbiden": [(2021, 2025)],
}
SURNAME_YEARS = {
    "lincoln": [(1861, 1865)], "johnson": [(1865, 1869), (1963, 1969)], "grant": [(1869, 1877)],
    "hayes": [(1877, 1881)], "garfield": [(1881, 1881)], "arthur": [(1881, 1885)],
    "cleveland": [(1885, 1889), (1893, 1897)], "harrison": [(1889, 1893)], "mckinley": [(1897, 1901)],
    "roosevelt": [(1901, 1909), (1933, 1945)], "taft": [(1909, 1913)], "wilson": [(1913, 1921)],
    "harding": [(1921, 1923)], "coolidge": [(1923, 1929)], "hoover": [(1929, 1933)], "truman": [(1945, 1953)],
    "eisenhower": [(1953, 1961)], "kennedy": [(1961, 1963)], "nixon": [(1969, 1974)], "ford": [(1974, 1977)],
    "carter": [(1977, 1981)], "reagan": [(1981, 1989)], "bush": [(1989, 1993), (2001, 2009)],
    "clinton": [(1993, 2001)], "obama": [(2009, 2017)], "trump": [(2017, 2021), (2025, 2029)], "biden": [(2021, 2025)],
}
YEAR_IN_DATE = re.compile(r"(?:" + MONTHS + r")\s*\d{1,2}\s*,\s*(\d{4})")


def signer_years(signature_line: str):
    """Year ranges for the president named in a signature line, or None if unknown."""
    collapsed = re.sub(r"[^a-z]", "", (signature_line or "").lower())
    if not collapsed:
        return None
    if collapsed in PRESIDENT_YEARS:
        return PRESIDENT_YEARS[collapsed]
    for name, years in SURNAME_YEARS.items():
        if collapsed.endswith(name) or collapsed.endswith(name + "jr"):
            return years
    return None


def identity_evidence(text: str, loc: Located) -> dict:
    """The signature line and the document's own date year, when printed.

    The date is taken from the heading ("... of December 28, 1994"), a date line
    under the title, or the date under "THE WHITE HOUSE"."""
    sig = None
    for ls, le, line in lines_with_offsets(text, loc.body_end, loc.doc_end):
        if is_signature_line(line) and not re.fullmatch(r"\s*\(Presidential Sig\.?\)\s*", line):
            sig = line.strip()
            break
    head = text[loc.doc_start:loc.body_start]
    year = None
    first = head.split("\n", 1)[0]
    m = re.match(r"\s*" + EXEC_ORDER + r"[ \t]*(?:N[ ]?o\.?[ \t]*)?\d(?:[ ]?\d){0,4}(?:[ \t]*[-‐–]?[ \t]*[A-Z]\b)?[ \t]+of[ \t]+(?:"
                 + MONTHS + r")\s*\d{1,2}\s*,\s*(\d{4})", first, re.I)
    if m:
        year = int(m.group(1))
    if year is None:
        for k, (ls, le, line) in enumerate(lines_with_offsets(head)):
            if k > 8:
                break
            if DATE_LINE.match(line):
                year = int(re.search(r"(\d{4})", line).group(1))
                break
    if year is None:
        wh = WHITE_HOUSE.search(text, loc.body_end, loc.doc_end)
        if wh:
            m = YEAR_IN_DATE.search(" ".join(text[wh.start():min(loc.doc_end, wh.end() + 80)].split()))
            year = int(m.group(1)) if m else None
    return {"signature_line": sig, "signer_years": signer_years(sig) if sig else None, "document_year": year}


def identity_doubts(evidence: dict, expected_year) -> list:
    """Warnings when the signer or the printed date does not fit the expected year (±1)."""
    out = []
    if not expected_year:
        return out
    y = int(expected_year)
    if evidence.get("document_year") and abs(evidence["document_year"] - y) > 1:
        out.append(f"identity_doubt_document_dated_{evidence['document_year']}_expected_{y}")
    yrs = evidence.get("signer_years")
    if yrs and not any(a - 1 <= y <= b + 1 for a, b in yrs):
        out.append("identity_doubt_signer_" + re.sub(r"[^A-Za-z]+", "_", evidence["signature_line"]).strip("_")
                   + f"_not_president_in_{y}")
    return out


# ---------------------------------------------------------------------------
# Completeness and noise checks (they only add warnings; they never move text)
# ---------------------------------------------------------------------------

LONG_CLAUSE_CHARS = 6000


def _sub_family(key: str) -> str:
    if key.isdigit():
        return "digit"
    if re.fullmatch(r"[ivx]+", key) and key not in ("v", "x"):
        return "roman"
    return "letter"


def completeness_problems(text, bs, be, inq, lines, l1, unit_info):
    """Warnings (prefix ``incomplete_``) for drafts that probably missed a split:

    * a "Sec. N." marker line outside quotes that does not start a unit;
    * a clause longer than LONG_CLAUSE_CHARS characters;
    * a clause holding two or more line-start sub-markers of the series it
      belongs to, e.g. "(b)" and "(c)" inside unit "(a)", or "(a)"/"(1)" inside
      a section that was not split at all.
    """
    out = []
    used_l1 = {c["start"] for c in l1}
    missed = 0
    for idx, (ls, cs, line) in enumerate(lines):
        m = _marker_at(text, cs, be)
        if m and m.group("sec") and m.group("secdot") and not inq(cs) and cs not in used_l1:
            missed += 1
    if missed:
        out.append(f"incomplete_section_markers_not_split_{missed}")
    long_units, unsplit = [], []
    for piece, flag, s, e in unit_info:
        if flag == "annex":
            continue
        if e - s > LONG_CLAUSE_CHARS:
            long_units.append(f"{piece}:{e - s}")
        if flag == "lead_in":
            continue
        own = re.search(r"\(([a-z]{1,2}|\d{1,3}|[ivx]+)\)$", piece)
        families = {_sub_family(own.group(1))} if own else {"letter", "digit"}
        n = 0
        for ls, cs, line in lines:
            if cs <= s or cs >= e:
                continue
            mm = SUB_MARKER.match(line)
            if mm and not inq(cs) and _sub_family(mm.group("key")) in families:
                n += 1
        if n >= 2:
            unsplit.append(f"{piece}:{n}")
    if long_units:
        out.append("incomplete_clause_over_6000_chars_" + ",".join(long_units[:5]))
    if unsplit:
        out.append("incomplete_unsplit_sub_markers_" + ",".join(unsplit[:5]))
    return out


# Phrases from an old Federal Register issue's masthead, contents pages or other
# documents; in a clause they mean the OCR columns of several items are mixed.
FR_MASTHEAD = re.compile(
    r"(?i)published\s+daily|superintendent\s+of\s+documents|division\s+of\s+the\s+federal\s+register|"
    r"administrative\s+committee|remit\s+money\s+order|single\s+copies|\bCONTENTS\b|"
    r"\bT\s?[Ii]\s?[Tt]\s?[Ll]\s?[Ee]\s+\d+\s*[—-]|\bchapter\s+[IVXL]+\s*[—-]|\bpart\s+\d+\s*[—-]|"
    r"\bORDER\s+GRANTING\b|\bsubscribers\b"
)
SMALL_CAPS_TITLE = re.compile(r"(?:\b[B-HJ-Z] [a-z]{2,}\b[^\n]*){2,}")


def ocr_interleave_signals(text: str, start: int, end: int) -> list:
    """Reasons to think an OCR text of an FR issue mixes columns of other items.

    Checked: masthead / contents / other-document phrases; spaced small-caps
    title lines ("W ithdrawing P ublic L ands") inside the body (another item's
    heading); a second enacting clause; and words broken one per line."""
    body = text[start:end]
    reasons = []
    hits = FR_MASTHEAD.findall(body)
    if hits:
        reasons.append("fr_masthead_or_contents_text")
    lines = [l.strip() for l in body.split("\n") if l.strip()]
    if any(SMALL_CAPS_TITLE.search(l) for l in lines):
        reasons.append("other_item_heading_inside_body")
    if len(re.findall(r"(?i)\bby\s+virtue\s+of\s+(?:and\s+pursuant\s+to\s+)?the\s+authority\b|\bby\s+the\s+authority\s+vested\b", body)) >= 2:
        reasons.append("second_enacting_clause_inside_body")
    if not re.search(r"(?i)\bordered\b|\bhereby\b|\bI\s+do\b|\bshall\b|\bdirect(?:ed)?\b|\bauthori[sz]ed\b|\bdesignated?\b|\bwithdrawn\b|\breserved\b", body):
        reasons.append("no_enacting_or_operative_words")
    if re.search(r"_{6,}", body):
        reasons.append("contents_leader_lines")
    if lines:
        one_word = sum(1 for l in lines if " " not in l and len(l) < 15)
        if len(lines) >= 6 and one_word / len(lines) > 0.15:
            reasons.append("words_broken_one_per_line")
        short = sum(1 for l in lines if len(l) < 25)
        if len(lines) >= 6 and short / len(lines) > 0.45:
            reasons.append("many_short_lines")
    return reasons


def reading_text(text: str, start: int, end: int) -> str:
    """The clause text with page-furniture lines removed (for reading only)."""
    return "\n".join(l for _, _, l in lines_with_offsets(text, start, end) if not is_furniture(l))
