"""Opt-in RECHECK pass for medium/low-confidence Federal Register finds (pdfplumber).

The default locator (source-ladder/fr_pages.py) reads the pypdf text layer of
a scanned daily issue. Federal Register pages are printed in two or three
columns, and pypdf's text order often mixes neighbouring columns (and the
table of contents) together, so some orders are labelled `medium` or `low`
even though the page shows them plainly.

This pass, run only when asked (JOB_RECHECK=1 or settings.json "recheck":
true), takes the orders whose result is NOT high (needs_page_check true),
fetches only that order's issue again through the existing fetch module and
cache, and uses pdfplumber word coordinates to rebuild each page in reading
order, column by column (recursive XY-cut on the word boxes). In that order it
looks for:

- the order's heading ("EXECUTIVE ORDER 10193", "Executive Order 12890 of
  ...") at the start of a column line, not a reference ("amending Executive
  Order 10193") and not a contents entry ("10193 ........ 9031"); or, for the
  1937-1945 style, a bare "EXECUTIVE ORDER" heading followed (with no other
  document's filing line in between) by the order's closing tag "[No. 8336]";
- the order's end: the first filing line "[F. R. Doc. ... Filed ...]" after
  it, with no other document's heading or closing tag in between;
- the printed FR page number in the running head of the page where the
  heading is.

It re-grades with that evidence. An order is upgraded to `high` ONLY when the
heading (or bare heading + closing tag) for this order number AND the filing
line are both located in reading order, the heading is on the cited FR page
(that page number printed in the page's running head, or the default
locator's exact printed-page match), the issue date in the file name matches
the OFR publication date, and the downloaded bytes are the same (sha256) as
the result being rechecked. Anything less: the result stays as it was, with
the evidence recorded. A `high` result is never rechecked, downgraded or
overwritten.

Results are kept in <cache>/recheck/<id>.json (resumable) and written as
RECHECK.jsonl and RECHECK_SUMMARY.json. For an upgraded order the output
FRAGMENTS.jsonl carries a new fragment (same format, location_confidence
high, needs_page_check false, plus recheck_evidence) in place of the old one,
and texts/EO_<n>.recheck.txt holds the reading-order text from heading to
filing line. SOURCES.jsonl keeps the original locator's record (with an added
`recheck` field). These are location leads only; no person has looked.

An upgrade is an overlay applied at output time (overlay()) from a valid
record of the current RECHECK_VERSION with its text; the order's state always
keeps the default locator's result (fr_originals.strip_recheck_overlay), so
an upgrade can be withdrawn by dropping or invalidating its record.
"""
from __future__ import annotations

import json
import re
import time
from collections import Counter
from datetime import date
from pathlib import Path

RECHECK_VERSION = 1
PRODUCED_BY = "fr-originals"
WINDOW_AFTER = 3          # same window as the default locator: cited page, the 3 after it, the one before
MAX_SPAN = 25             # pages searched for the filing line after the heading
TAG_TO_FILING_LINES = 3   # the filing line must follow the closing tag within this many lines
BACK_LINES = 2000         # how far back from a closing tag the bare heading is looked for

try:  # Shared patterns of the default locator (source-ladder/fr_pages.py).
    import fr_pages
except ImportError:  # pragma: no cover - the job always puts source-ladder on sys.path
    fr_pages = None


def pdfplumber_available():
    try:
        import pdfplumber  # noqa: F401  (MIT; pinned in requirements.txt)
        return True
    except ImportError:
        return False


# --------------------------------------------------------------------------
# Layout: words -> lines in reading order (recursive XY-cut)
# --------------------------------------------------------------------------

def _median(vals, default=0.0):
    vals = sorted(vals)
    if not vals:
        return default
    m = len(vals) // 2
    return vals[m] if len(vals) % 2 else (vals[m - 1] + vals[m]) / 2


def _rows(words, tol):
    """Cluster words into rows by their top coordinate."""
    rows = []
    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if rows and abs(w["top"] - rows[-1]["top"]) <= tol:
            rows[-1]["words"].append(w)
            rows[-1]["bottom"] = max(rows[-1]["bottom"], w["bottom"])
        else:
            rows.append({"top": w["top"], "bottom": w["bottom"], "words": [w]})
    return rows


def _coverage(words, x0, x1):
    width = int(x1 - x0) + 2
    cov = [0] * width
    for w in words:
        a = max(0, int(w["x0"] - x0))
        b = min(width - 1, int(w["x1"] - x0))
        for x in range(a, b + 1):
            cov[x] += 1
    return cov


def _vertical_cut(words, max_cross, min_gap=3.0, tol=3.0, min_rows=3):
    """x of the best vertical gutter whose crossing word count is <= max_cross, or None.

    A gutter must have at least min_rows rows of text on each side (so the
    spaces between the words of a signature or a short line are not columns)."""
    x0 = min(w["x0"] for w in words)
    x1 = max(w["x1"] for w in words)
    span = x1 - x0
    if span < 60:
        return None
    cov = _coverage(words, x0, x1)
    lo, hi = int(span * 0.12), int(span * 0.88)
    cands = []
    i = lo
    while i < hi:
        if cov[i] <= max_cross:
            j = i
            while j < hi and cov[j] <= max_cross:
                j += 1
            if j - i >= min_gap:
                cands.append(((j - i, -max(cov[i:j])), x0 + (i + j) / 2.0))
            i = j
        else:
            i += 1
    for _, cut in sorted(cands, reverse=True):
        left = [w for w in words if (w["x0"] + w["x1"]) / 2 < cut]
        right = [w for w in words if (w["x0"] + w["x1"]) / 2 >= cut]
        if len(_rows(left, tol)) >= min_rows and len(_rows(right, tol)) >= min_rows:
            return cut
    return None


def _crossing(words, cut):
    return [w for w in words if w["x0"] < cut - 1 < cut + 1 < w["x1"]]


def _horizontal_cuts(rows, min_gap):
    """y positions of full-width whitespace between consecutive rows."""
    cuts = []
    bottom = None
    for r in rows:
        if bottom is not None and r["top"] - bottom >= min_gap:
            cuts.append((bottom + r["top"]) / 2.0)
        bottom = r["bottom"] if bottom is None else max(bottom, r["bottom"])
    return cuts


def _leaf_lines(words, tol):
    out = []
    for r in _rows(words, tol):
        ws = sorted(r["words"], key=lambda w: w["x0"])
        out.append({"top": round(r["top"], 1), "x0": round(ws[0]["x0"], 1), "x1": round(ws[-1]["x1"], 1),
                    "text": " ".join(w["text"] for w in ws)})
    return out


def xy_cut(words, tol, min_hgap, depth=0, blocks=None, min_vgap=3.0):
    """Split words into reading-order blocks. Returns list of word lists."""
    if blocks is None:
        blocks = []
    if not words:
        return blocks
    if depth > 14 or len(words) < 4:
        blocks.append(words)
        return blocks
    # 1. a clean column gutter (no word crosses it)
    cut = _vertical_cut(words, 0, min_gap=min_vgap, tol=tol)
    if cut is None:
        rows = _rows(words, tol)
        tolerant = _vertical_cut(words, 2, min_gap=min_vgap, tol=tol)
        # 2. a full-width whitespace band next to the words that cross the best gutter
        #    (a heading printed across two columns): cut there first
        if tolerant is not None:
            # only real spanning text (a wide word well over both sides), not an OCR word
            # that strays a few points into a narrow gutter
            cross = [w for w in _crossing(words, tolerant)
                     if w["x1"] - w["x0"] >= 20 and tolerant - w["x0"] >= 8 and w["x1"] - tolerant >= 8]
            ys = _horizontal_cuts(rows, min_hgap)
            if cross and ys:
                ctop = min(w["top"] for w in cross)
                cbot = max(w["bottom"] for w in cross)
                above = [y for y in ys if y <= ctop]
                below = [y for y in ys if y >= cbot]
                y = max(above) if above else (min(below) if below else None)
                if y is not None:
                    top = [w for w in words if (w["top"] + w["bottom"]) / 2 < y]
                    bot = [w for w in words if (w["top"] + w["bottom"]) / 2 >= y]
                    if top and bot:
                        xy_cut(top, tol, min_hgap, depth + 1, blocks, min_vgap)
                        xy_cut(bot, tol, min_hgap, depth + 1, blocks, min_vgap)
                        return blocks
            # 3. a gutter crossed only by one or two (OCR-merged) words
            cut = tolerant
        if cut is None:
            # 4. no gutter: cut at full-width whitespace only if the parts have gutters
            ys = _horizontal_cuts(rows, min_hgap)
            for y in ys:
                top = [w for w in words if (w["top"] + w["bottom"]) / 2 < y]
                bot = [w for w in words if (w["top"] + w["bottom"]) / 2 >= y]
                if top and bot and (_vertical_cut(top, 0, min_gap=min_vgap, tol=tol) is not None or _vertical_cut(bot, 0, min_gap=min_vgap, tol=tol) is not None):
                    xy_cut(top, tol, min_hgap, depth + 1, blocks, min_vgap)
                    xy_cut(bot, tol, min_hgap, depth + 1, blocks, min_vgap)
                    return blocks
            blocks.append(words)
            return blocks
    left = [w for w in words if (w["x0"] + w["x1"]) / 2 < cut]
    right = [w for w in words if (w["x0"] + w["x1"]) / 2 >= cut]
    xy_cut(left, tol, min_hgap, depth + 1, blocks, min_vgap)
    xy_cut(right, tol, min_hgap, depth + 1, blocks, min_vgap)
    return blocks


# A contents / codification-guide entry: "Alaska, withdrawal ________ 593" (leaders; a bare
# number such as "1925" on its own line is not one: titles wrap like that).
LEADER_END = re.compile(r"(?:[._—–\-]\s*){3,}\s*[\d,* ]*$")
CONTENTS_LOOKAHEAD = 5


def _in_contents(lines, k):
    """True when line k is a contents entry, or a heading-like line followed (within a few lines
    of the same block) by one: "Executive Order" / "Creating an Emergency Board ..._____"."""
    if lines[k].get("leader"):
        return True
    for j in range(k + 1, min(len(lines), k + 1 + CONTENTS_LOOKAHEAD)):
        if lines[j].get("block") != lines[k].get("block") or lines[j].get("page") != lines[k].get("page"):
            break
        if lines[j].get("leader"):
            return True
    return False


MONTH_WORD = re.compile(r"^\W{0,2}(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\W{0,2}$", re.I)
DAY_WORD = re.compile(r"^\d{1,2}\W{0,2}$")
YEAR_WORD = re.compile(r"^\W{0,2}(?:19[3-9]\d|20[0-3]\d)\W{0,2}$")


def _date_token(row, i):
    """True when word i of a running-head row is the day or the year of the issue date
    ("Thursday, April 17, 1941", also with the comma lost): a page number equal to the
    year (6 FR 1941) must not be confirmed by the date. A page number printed after the
    date ("... April 17, 1941 1941") is still read."""
    t = row[i]["text"]
    if DAY_WORD.match(t) and i > 0 and MONTH_WORD.match(row[i - 1]["text"]):
        return True
    if YEAR_WORD.match(t) and i > 1 and DAY_WORD.match(row[i - 1]["text"]) and MONTH_WORD.match(row[i - 2]["text"]):
        return True
    return False


def layout_words(words, page_index=0):
    """Reading-order layout of one page from pdfplumber-style word dicts
    (text, x0, x1, top, bottom). Returns {"lines": [...], "head_numbers": set,
    "head_text": str, "blocks": n}."""
    words = [w for w in words if str(w.get("text", "")).strip()]
    if not words:
        return {"page": page_index, "lines": [], "head_numbers": [], "head_text": "", "blocks": 0}
    heights = [w["bottom"] - w["top"] for w in words if w["bottom"] > w["top"]]
    h = _median(heights, 8.0)
    tol = max(1.5, h * 0.45)
    rows = _rows(words, tol)
    # Running head: the top row (and the bottom row), read for printed page numbers.
    head = rows[0]["words"]
    foot = rows[-1]["words"] if len(rows) > 2 and len(rows[-1]["words"]) <= 6 else []
    head_text = " ".join(w["text"] for w in sorted(head, key=lambda w: w["x0"]))
    nums = set()
    for row in (head, foot):
        row = sorted(row, key=lambda w: w["x0"])
        for i, w in enumerate(row):
            if _date_token(row, i):  # "April 17, 1941": the day and the year are not page numbers
                continue
            for m in re.finditer(r"(?<![\d,.])(\d{1,5})(?![\d,])", w["text"]):
                v = int(m.group(1))
                if v > 0:
                    nums.add(v)
    body = [w for w in words if w not in head]
    lines = [{"page": page_index, "block": -1, "top": round(rows[0]["top"], 1), "x0": round(min(w["x0"] for w in head), 1),
              "text": head_text, "running_head": True}]
    # Gutters in the scans can be as narrow as 3 pt (measured: 0.75 x text height lost most columns),
    # so a cut also needs three rows of text on each side (see _vertical_cut).
    blocks = xy_cut(body, tol, max(3.0, h * 0.6), min_vgap=3.0)
    for b, blk in enumerate(blocks):
        for ln in _leaf_lines(blk, tol):
            ln.update(page=page_index, block=b)
            if LEADER_END.search(ln["text"]):
                ln["leader"] = True
            lines.append(ln)
    return {"page": page_index, "lines": lines, "head_numbers": sorted(nums), "head_text": head_text,
            "blocks": len(blocks)}


class PdfLayouts:
    """Lazy {page_index: layout} over one PDF, read with pdfplumber (opened once).

    Use as a context manager; .get(i) lays out page i on first use."""

    def __init__(self, path):
        import logging
        import pdfplumber
        logging.getLogger("pdfminer").setLevel(logging.ERROR)
        self._pdf = pdfplumber.open(str(path))
        self.n = len(self._pdf.pages)
        self._cache = {}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def close(self):
        if self._pdf is not None:
            self._pdf.close()
            self._pdf = None

    def get(self, i, default=None):
        if not 0 <= i < self.n:
            return default
        if i not in self._cache:
            page = self._pdf.pages[i]
            try:
                words = page.extract_words(x_tolerance=3, y_tolerance=3, keep_blank_chars=False)
                self._cache[i] = layout_words(words, i)
            except Exception as exc:  # damaged page: say so, keep going
                self._cache[i] = {"page": i, "lines": [], "head_numbers": [], "head_text": "", "blocks": 0,
                                  "error": type(exc).__name__}
            page.flush_cache()
        return self._cache[i]

    def pages_done(self):
        return sorted(self._cache)


def pdf_layouts(path, page_indexes):
    """{page_index: layout} for the given 0-based pages (eager; for tools and tests)."""
    with PdfLayouts(path) as lay:
        return {i: lay.get(i) for i in sorted(set(page_indexes)) if 0 <= i < lay.n}, lay.n


# --------------------------------------------------------------------------
# Finding the order in reading order
# --------------------------------------------------------------------------

LEADERS = re.compile(r"(?:[._—–\-]\s*){3,}\s*\d+\s*$|\.\s*\.\s*\.")
# A line that is only "EXECUTIVE ORDER" / "Executive Order" (the 1937-1945 heading before the
# title; the number is in the closing tag). Not "Executive Orders:" (contents).
GENERIC_HEADING = re.compile(r"^\W{0,3}E\s?X\s?E\s?C\s?U\s?T\s?I\s?V\s?E\s+O\s?R\s?D\s?E\s?R(?!\s?[sS])\W{0,3}$", re.I)
PROCLAMATION_HEADING = re.compile(r"^\W{0,3}P\s?R\s?O\s?C\s?L\s?A\s?M\s?A\s?T\s?I\s?O\s?N\b\W*(?:\d[\d\s]*\W*)?$")
ANY_TAG_LINE = re.compile(r"^\W{0,2}\[\s*N\s?o\.?\s*\d{3,5}\s?[A-Za-z]?\s?[\]1lI|)3J}]?\W{0,2}$")
NUMBERED_HEADING_ANY = re.compile(r"^\W{0,3}E\s?X\s?E\s?C\s?U\s?T\s?I\s?V\s?E\s+O\s?R\s?D\s?E\s?R\s*(?:N\s?o\.?\s*)?(\d(?:\s?\d){3,4})", re.I)
# "Executive Order 12890 of January 1, 1994" as the whole line (the modern heading form).
MODERN_HEADING_TAIL = re.compile(r"\s*of\s+[A-Z][a-z]+\.?\s+\d{1,2},?\s*\d{4}\W*$")
# The modern heading has no "No." before the number; "Executive Order No. 10269 of July 6, 1951"
# at the start of a line is a wrapped reference in running text, not a heading.
NO_BEFORE_NUMBER = re.compile(r"N\s?o\.?\s*$", re.I)


def _modern_tail(head_part, rest):
    """True when `rest` is the modern "of <date>" heading tail and the heading has no "No."."""
    return bool(MODERN_HEADING_TAIL.match(rest)) and not NO_BEFORE_NUMBER.search(head_part)
# The previous line ends in a word that makes the next line's "Executive Order ..." a reference.
# Only a bare word at the end ("... amending", "... pursuant to"): not "p. in.]" or "1940."
REFERENCE_PREV = re.compile(r"\b(?:amend\w*|revok\w*|supersed\w*|terminat\w*|modif\w*|rescind\w*|suspend\w*|"
                            r"pursuant\s+to|under|by|of|in|to|and|see|with)\s*[,\-]?\s*$", re.I)


def _prev_is_reference(lines, k):
    return (k > 0 and lines[k - 1].get("block") == lines[k].get("block")
            and lines[k - 1].get("page") == lines[k].get("page") and not lines[k - 1].get("running_head")
            and bool(REFERENCE_PREV.search(lines[k - 1]["text"])))


def _heading_line_kind(lines, k, number):
    """For line k: 'own' (this order's numbered heading), 'reference', 'contents', 'midline' or None."""
    text = lines[k]["text"]
    pats = dict(fr_pages.marker_patterns(number))
    m = pats["heading"].search(text)
    if not m:
        return None
    prefix = text[:m.start()]
    if len(re.sub(r"[\W_]", "", prefix)) > 2 and not fr_pages.HEADING_PREFIX_OK.match(prefix):
        return "reference" if fr_pages.REFERENCE_BEFORE.search(prefix) else "midline"
    if LEADERS.search(text[m.end():]):
        return "contents"
    if prefix.strip() == "" and _prev_is_reference(lines, k):
        return "reference"
    rest = text[m.end():]
    # A short tail ("<", "]") or the modern "of January 1, 1994"; a long running line is a mention.
    head_part = re.sub(r"[\d\s]+$", "", text[:m.end()].rstrip())
    if len(re.sub(r"[\W_]", "", rest)) > 3 and not _modern_tail(head_part, rest):
        return "midline"
    return "own"


def _tag_line(text, number):
    """'strict' for "[No. 8336]", 'bracket_ocr_damaged' for "[No. 83363" / "[No. 8336" (whole line), else None."""
    d = fr_pages.digits_pattern(number)
    if not re.search(r"[A-Za-z]$", number):
        d += r"(?![ \t]?[-‐-—][ \t]?[A-Za-z])"
    t = text.strip()
    # The opening "[" is required: OCR damage seen so far is on the closing bracket only, and
    # without it a wrapped reference line such as "No. 8792)." would pass for a closing tag.
    if re.fullmatch(rf"\W{{0,2}}\[\s*N\s?o\.?\s*{d}\s?[\]1lI|)]\W{{0,2}}", t):
        return "strict"
    m = re.fullmatch(rf"\W{{0,2}}\[\s*N\s?o\.?\s*{d}\s?([3J}}]?)\W{{0,2}}", t)
    if m:
        base = re.match(r"\d+", number).group(0)
        # "83363" for 8336 can only be a damaged "]" if 83363 is not itself an order number in scope.
        if not m.group(1) or not m.group(1).isdigit() or int(base + m.group(1)) > 15000:
            return "bracket_ocr_damaged"
    return None


def _is_filing(text):
    m = fr_pages.FILING.search(text)
    return bool(m) and len(re.sub(r"\s", "", text[:m.start()])) <= 3


def _is_generic_heading(lines, k):
    t = lines[k]["text"].strip()
    return bool(GENERIC_HEADING.match(t)) and not _prev_is_reference(lines, k) and not _in_contents(lines, k)


def _other_document_start(lines, k, number):
    """Text of line k when it starts another document (a different order's heading, a bare
    EXECUTIVE ORDER heading, a proclamation heading, or another closing tag), else None.
    A wrapped reference in running text ("... amending" / "Executive Order No. 9001 of ...")
    is not a heading: a heading line holds the heading only, and no reference word precedes it."""
    line = lines[k]
    t = line["text"].strip()
    if line.get("running_head"):
        return None
    prev_ref = _prev_is_reference(lines, k)
    m = NUMBERED_HEADING_ANY.match(t)
    if m:
        got = re.sub(r"\s", "", m.group(1))
        base = re.match(r"\d+", number).group(0)
        rest = t[m.end():]
        short = len(re.sub(r"[\W_]", "", rest)) <= 3 or _modern_tail(t[:m.start(1)], rest)
        if got != base and not LEADERS.search(t) and not prev_ref and short and not _in_contents(lines, k):
            return t
    if _is_generic_heading(lines, k):
        return t
    if PROCLAMATION_HEADING.match(t) and not prev_ref and not _in_contents(lines, k):
        return t
    if ANY_TAG_LINE.match(t) and _tag_line(t, number) is None:
        return t
    return None


class _Stream:
    """Reading-order lines of consecutive pages, extended on demand."""

    def __init__(self, layouts, first, last_limit):
        self.layouts, self.next_page, self.last_limit = layouts, first, last_limit
        self.lines = []

    def extend_to(self, page):
        """Lay out pages up to `page`; False when no page is left to add."""
        added = False
        while self.next_page <= min(page, self.last_limit):
            lay = self.layouts.get(self.next_page)
            if lay:
                self.lines.extend(lay["lines"])
            self.next_page += 1
            added = True
        return added


def find_in_reading_order(layouts, number, cited_idx, n_pages, base_exact_page_match=False):
    """Locate the order in reading-order lines. layouts: anything with .get(page_index)
    returning a layout (a dict, or PdfLayouts). Pages are laid out only as far as needed.

    Returns an evidence dict (no network)."""
    ev = {"cited_pdf_page": cited_idx + 1, "heading": None, "closing_tag": None, "filing_line": None,
          "start_pdf_page": None, "end_pdf_page": None, "conflict": None, "skipped_mentions": [],
          "cited_page_number_in_running_head": None, "heading_on_cited_page": False}
    window = [cited_idx + k for k in range(WINDOW_AFTER + 1)] + [cited_idx - 1]
    lo, hi = max(0, cited_idx - 1), min(n_pages - 1, cited_idx + WINDOW_AFTER + MAX_SPAN)
    st = _Stream(layouts, lo, hi)
    st.extend_to(cited_idx + WINDOW_AFTER)
    lines = st.lines
    start_k = None
    kind = None
    # 1. this order's numbered heading, searched page by page in the default locator's order
    for p in window:
        for k, ln in enumerate(lines):
            if ln["page"] != p or ln.get("running_head"):
                continue
            hk = _heading_line_kind(lines, k, number)
            if hk == "own" and _in_contents(lines, k):
                hk = "contents"
            if hk == "own":
                start_k, kind = k, "numbered_heading"
                break
            if hk:
                ev["skipped_mentions"].append({"pdf_page": p + 1, "why": hk, "text": ln["text"][:120]})
        if start_k is not None:
            break
    tag_k = None
    if start_k is None:
        # 2. 1937-1945 style: bare heading ... [No. 8336]
        for p in window:
            for k, ln in enumerate(lines):
                if ln["page"] != p or ln.get("running_head"):
                    continue
                tk = _tag_line(ln["text"], number)
                if tk:
                    tag_k = k
                    ev["closing_tag"] = {"pdf_page": p + 1, "text": ln["text"].strip()[:80], "kind": tk,
                                         "line_top": ln.get("top"), "block": ln.get("block")}
                    break
            if tag_k is not None:
                break
        if tag_k is None:
            ev["missing"] = "neither the order's numbered heading nor its closing tag was found in reading order"
            return ev
        for k in range(tag_k - 1, max(-1, tag_k - BACK_LINES), -1):
            ln = lines[k]
            if ln.get("running_head"):
                continue
            t = ln["text"].strip()
            if _is_generic_heading(lines, k):
                start_k, kind = k, "bare_heading_then_closing_tag"
                break
            if _is_filing(t):
                ev["conflict"] = f"another document's filing line comes between the closing tag and any heading: {t[:80]}"
                return ev
            other = _other_document_start(lines, k, number)
            if other:
                ev["conflict"] = f"another document starts between the heading and the closing tag: {other[:80]}"
                return ev
        if start_k is None:
            ev["missing"] = "closing tag found, but no bare EXECUTIVE ORDER heading before it in reading order"
            return ev
    h = lines[start_k]
    ev["heading"] = {"pdf_page": h["page"] + 1, "text": h["text"].strip()[:120], "kind": kind,
                     "line_top": h.get("top"), "block": h.get("block")}
    ev["start_pdf_page"] = h["page"] + 1
    lay = layouts.get(h["page"]) or {}
    ev["heading_on_cited_page"] = h["page"] == cited_idx
    # 3. the end: the first filing line after the heading (after the tag in tag style)
    k = (tag_k if tag_k is not None else start_k) + 1
    end_k = None
    while True:
        if k >= len(lines):
            if not st.extend_to(st.next_page):
                break
            continue
        ln = lines[k]
        t = ln["text"].strip()
        if not ln.get("running_head"):
            if _is_filing(t):
                end_k = k
                break
            other = _other_document_start(lines, k, number)
            if other:
                ev["conflict"] = f"another document starts before any filing line: {other[:80]} (PDF page {ln['page'] + 1})"
                return ev
            if tag_k is not None and k - tag_k > TAG_TO_FILING_LINES:
                break
        k += 1
    if end_k is None:
        ev["missing"] = ("no filing line right after the closing tag" if tag_k is not None
                         else f"no filing line within {MAX_SPAN} pages after the heading")
        return ev
    f = lines[end_k]
    ev["filing_line"] = {"pdf_page": f["page"] + 1, "text": f["text"].strip()[:120], "line_top": f.get("top"),
                         "block": f.get("block")}
    ev["end_pdf_page"] = f["page"] + 1
    ev["text_lines"] = [(ln["page"], ln["text"]) for ln in lines[start_k:end_k + 1] if not ln.get("running_head")]
    ev["head_numbers_on_heading_page"] = lay.get("head_numbers", [])
    ev["running_head_text"] = lay.get("head_text", "")[:120]
    ev["base_exact_printed_page_match"] = bool(base_exact_page_match)
    return ev


# --------------------------------------------------------------------------
# One order
# --------------------------------------------------------------------------

def _cited(record):
    m = re.fullmatch(r"\s*(\d+)\s*FR\s*(\d+)\s*", (record or {}).get("citation") or "")
    return (int(m.group(1)), int(m.group(2))) if m else (None, None)


def _issue_date(url):
    m = re.search(r"/FR-(\d{4}-\d\d-\d\d)\.pdf$", url.split("?", 1)[0])
    return m.group(1) if m else None


def grade(ev, record, src, sha_now):
    """(upgrade: bool, reasons_missing: list) from the evidence."""
    missing = []
    _, fr_page = _cited(record)
    if sha_now != src.get("sha256"):
        missing.append("downloaded bytes differ from the result being rechecked (sha256)")
    if ev.get("conflict"):
        missing.append(ev["conflict"])
    if ev.get("missing"):
        missing.append(ev["missing"])
    if not ev.get("heading"):
        missing.append("order's heading not located")
    if not ev.get("filing_line"):
        missing.append("filing line not located")
    if ev.get("heading") and not ev.get("heading_on_cited_page"):
        missing.append(f"heading is on PDF page {ev['heading']['pdf_page']}, not the cited page (PDF page {ev['cited_pdf_page']})")
    if ev.get("heading") and ev.get("heading_on_cited_page"):
        read = fr_page in (ev.get("head_numbers_on_heading_page") or [])
        ev["cited_page_number_in_running_head"] = read
        if not read and not ev.get("base_exact_printed_page_match"):
            missing.append(f"FR page {fr_page} not read in the running head of the heading's page")
    issue = _issue_date(src.get("url", "").split("id_/", 1)[-1])
    ev["issue_date_in_url"] = issue
    ev["ofr_publication_date"] = (record or {}).get("publication_date")
    if issue != ev["ofr_publication_date"]:
        missing.append(f"issue date {issue} differs from the OFR publication date {ev['ofr_publication_date']}")
    tw = ev.get("ofr_title_words_found")
    if tw:
        k, n = (int(x) for x in tw.split("/"))
        if n >= 3 and 3 * k < n:  # an extra brake only: the title is not what upgrades
            missing.append(f"only {tw} of the OFR title's words appear near the heading")
    if ev.get("start_pdf_page") and ev.get("end_pdf_page") and ev["end_pdf_page"] - ev["start_pdf_page"] + 1 > 12:
        missing.append("long page range (over 12 pages)")
    return (not missing), missing


def _base_range(src):
    m = re.search(r"PDF pages (\d+)-(\d+)", src.get("page_or_item") or "")
    return (int(m.group(1)), int(m.group(2))) if m else (None, None)


def recheck_text(iid, src, ev, record):
    lines = ev.get("text_lines") or []
    head = (f"Instrument: {iid}\nSource: {src['url']}\nSHA-256 of the downloaded file: {src['sha256']}\n"
            f"Location: {record.get('citation')}, PDF pages {ev['start_pdf_page']}-{ev['end_pdf_page']} "
            "(confidence high, from the pdfplumber recheck)\n"
            "Reading-order text rebuilt from the scan's OCR word positions (pdfplumber), from the order's heading "
            "to its filing line. May contain recognition errors, and page furniture printed in between (running "
            "heads are left out; a masthead or contents column may remain). Not an authenticated transcription: "
            "check the PDF pages.\n\n")
    body, page = [], None
    for p, t in lines:
        if p != page:
            body.append(f"=== PDF page {p + 1} ===")
            page = p
        body.append(t)
    return head + "\n".join(body) + "\n"


def upgraded_fragment(base_frag, item, src, ev, text_name):
    rec = item.get("record") or {}
    frag = json.loads(json.dumps(base_frag))
    page_or_item = f"{rec.get('citation') or item['instrument_id']}, PDF pages {ev['start_pdf_page']}-{ev['end_pdf_page']}"
    d = frag["data"]
    base = {"location_confidence": d.get("location_confidence"), "page_or_item": d.get("page_or_item"),
            "text_path": d.get("text_path")}
    d.update({"page_or_item": page_or_item, "text_path": f"texts/{text_name}", "location_confidence": "high",
              "location_verified": False, "needs_page_check": False,
              "recheck_evidence": evidence_summary(ev, base)})
    for s in frag.get("sources") or []:
        if s.get("sha256") == src["sha256"]:
            s["page_or_item"] = page_or_item
    frag["confidence_note"] = (
        "Machine location lead, confidence high after the pdfplumber recheck (the first locator said "
        f"{base['location_confidence']}): in column reading order the order's heading"
        + (" and closing tag" if ev["heading"]["kind"] == "bare_heading_then_closing_tag" else "")
        + " and its filing line were both found, on the cited FR page of the issue named by the OFR index. "
        "Official govinfo scan of the printed Federal Register; text is the scan's OCR layer and may contain "
        "errors. Identity, page boundaries and wording are NOT human-verified; this is not a legal conclusion.")
    return frag


def title_overlap(title, text_lines, first_lines=14):
    """'k/n': how many of the OFR title's longer words appear near the heading (spaces removed,
    because OCR letter-spaces headings). Recorded as a cross-check only; not used to grade."""
    words = sorted({w for w in re.findall(r"[a-z]{5,}", (title or "").lower())})
    if not words or not text_lines:
        return None
    near = re.sub(r"[^a-z]", "", " ".join(t for _, t in text_lines[:first_lines]).lower())
    return f"{sum(1 for w in words if w in near)}/{len(words)}"


def evidence_summary(ev, base=None):
    keep = ("cited_pdf_page", "heading", "closing_tag", "filing_line", "start_pdf_page", "end_pdf_page",
            "heading_on_cited_page", "cited_page_number_in_running_head", "base_exact_printed_page_match",
            "head_numbers_on_heading_page", "running_head_text", "issue_date_in_url", "ofr_publication_date",
            "conflict", "missing", "ofr_title_words_found")
    out = {k: ev.get(k) for k in keep if ev.get(k) is not None}
    if ev.get("skipped_mentions"):
        out["skipped_mentions"] = ev["skipped_mentions"][:5]
    out["method"] = "pdfplumber word coordinates, recursive XY-cut reading order"
    out["recheck_version"] = RECHECK_VERSION
    if base is not None:
        out["base"] = base
    return out


def eligible(st):
    """Only found orders whose result is NOT high, from a scanned daily issue."""
    import eo_extract
    if not st or st.get("status") != "found":
        return False, "not found"
    src = st.get("source") or {}
    frag = st.get("fragment") or {}
    d = frag.get("data") or {}
    if src.get("location_confidence") == "high" or d.get("location_confidence") == "high" \
            or d.get("needs_page_check") is False:
        return False, "already high (never rechecked)"
    if not eo_extract.issue_pdf(src.get("url", "").split("id_/", 1)[-1]):
        return False, "not a scanned daily issue (per-document PDF or other copy)"
    return True, ""


def recheck_order(ctx, item, st, log=print):
    """Recheck one order. Returns (recheck record, fetch attempt); never touches the order's state."""
    import eo_extract
    import fetch_ladder
    iid = item["instrument_id"]
    src = st["source"]
    rec = item.get("record") or {}
    number = iid.split(":", 1)[1]
    a, b = _base_range(src)
    row = {"recheck_version": RECHECK_VERSION, "instrument_id": iid, "checked_utc": fetch_ladder.now_utc(),
           "url": src["url"], "base_sha256": src["sha256"], "base_confidence": src.get("location_confidence"),
           "base_page_or_item": src.get("page_or_item"), "fr_citation": rec.get("citation"),
           "publication_date": rec.get("publication_date"), "result": "stays", "new_confidence": src.get("location_confidence"),
           "page_or_item": None, "reasons": [], "evidence": None, "fragment": None, "text_file": None}
    att = ctx["fetcher"].fetch(src["url"], route="recheck/" + (src.get("route") or ""), expect="pdf")
    row["fetch"] = {k: att.get(k) for k in ("from_cache", "status", "error", "bytes", "sha256")}
    if not att.get("accepted") or not att.get("path"):
        row["result"] = "error"
        row["reasons"] = [f"issue could not be fetched again: {att.get('error') or att.get('reject_reason') or att.get('status')}"]
        return row, att
    path = att["path"]
    texts = eo_extract.pdf_texts(path, att.get("sha256"))
    n = len(texts)
    _, fr_page = _cited(rec)
    # The cited page: the default locator's printed-page map (pypdf text) ...
    page_map = fr_pages.printed_page_map(texts) if fr_page else {}
    idx, how = fr_pages.find_printed_page(texts, page_map, fr_page) if fr_page else (None, "no_fr_page_given")
    t0 = time.time()
    with PdfLayouts(path) as lay:
        # ... cross-checked against the page number pdfplumber reads in the running heads near it.
        near = set()
        for c in (idx, (a - 1) if a else None, (att.get("page_hint") or 0) - 1 if att.get("page_hint") else None):
            if c is not None:
                near.update(range(max(0, c - 2), min(n, c + 3)))
        hits = [i for i in sorted(near) if fr_page and fr_page in (lay.get(i) or {}).get("head_numbers", [])]
        head_idx = hits[0] if len(hits) == 1 else None
        disagreement = None
        if idx is None and head_idx is not None:
            idx, how = head_idx, "pdfplumber_running_head"
        elif idx is not None and head_idx is not None and head_idx != idx:
            disagreement = (f"printed page {fr_page} is PDF page {idx + 1} by the pypdf page map but PDF page "
                            f"{head_idx + 1} by the running head pdfplumber reads")
        if idx is None and att.get("page_hint") and 1 <= att["page_hint"] <= n:
            idx, how = att["page_hint"] - 1, "govinfo_link_service_page_hint"
        if idx is None and a:
            idx, how = a - 1, "base_result_first_page"
        if idx is None:
            row["reasons"] = ["cited FR page not found in the issue"]
            return row, att
        ev = find_in_reading_order(lay, number, idx, n, base_exact_page_match=(how == "printed_page_number_matched"))
        ev["pages_laid_out"] = len(lay.pages_done())
    if disagreement:
        ev["conflict"] = ev.get("conflict") or disagreement
    ev["ofr_title_words_found"] = title_overlap(rec.get("title"), ev.get("text_lines"))
    ev["cited_page_found_by"] = how
    ok, missing = grade(ev, rec, src, att.get("sha256"))
    row["evidence"] = evidence_summary(ev)
    row["evidence"].update(cited_page_found_by=how, pages_laid_out=ev["pages_laid_out"],
                           layout_seconds=round(time.time() - t0, 2))
    if ev.get("start_pdf_page") and ev.get("end_pdf_page"):
        row["page_or_item"] = f"{rec.get('citation')}, PDF pages {ev['start_pdf_page']}-{ev['end_pdf_page']}"
        row["agrees_with_base_pages"] = (a, b) == (ev["start_pdf_page"], ev["end_pdf_page"])
        row["overlaps_base_pages"] = bool(a) and not (ev["end_pdf_page"] < a or ev["start_pdf_page"] > b)
    row["reasons"] = missing
    if ok:
        import fr_originals
        name = fr_originals.text_name(iid).replace(".txt", ".recheck.txt")
        row.update(result="upgraded", new_confidence="high", text_file=name)
        row["fragment"] = upgraded_fragment(st["fragment"], item, src, ev, name)
        row["_text"] = recheck_text(iid, src, ev, rec)
    return row, att


# --------------------------------------------------------------------------
# State, run, outputs, carry forward
# --------------------------------------------------------------------------

def recheck_dir(ctx):
    return Path(ctx["state_dir"]).parent / "recheck"


def _rpath(ctx, iid):
    import fetch_ladder
    return recheck_dir(ctx) / (fetch_ladder.safe_name(iid) + ".json")


def load_recheck(ctx, iid):
    p = _rpath(ctx, iid)
    if p.is_file():
        r = json.loads(p.read_text(encoding="utf-8"))
        if r.get("recheck_version") == RECHECK_VERSION:
            return r
    return None


def save_recheck(ctx, row):
    import fetch_ladder
    text = row.pop("_text", None)
    d = recheck_dir(ctx)
    d.mkdir(parents=True, exist_ok=True)
    if text is not None and row.get("text_file"):
        (d / "texts").mkdir(parents=True, exist_ok=True)
        fetch_ladder.write_text_lf(d / "texts" / row["text_file"], text)
    fetch_ladder.write_text_lf(_rpath(ctx, row["instrument_id"]), json.dumps(row, ensure_ascii=False, indent=1))


def select(ctx, plan, states, only=(), redo=False):
    out, skipped = [], Counter()
    for it in plan:
        iid = it["instrument_id"]
        if only and iid not in only:
            continue
        st = states.get(iid)
        ok, why = eligible(st)
        if not ok:
            if st and st.get("status") == "found":
                skipped[why] += 1
            continue
        prev = load_recheck(ctx, iid)
        if prev and not redo and prev.get("result") != "error" and prev.get("base_sha256") == st["source"]["sha256"]:
            skipped["already rechecked"] += 1
            continue
        out.append(it)
    return out, skipped


def run_recheck(ctx, plan, states, limit=None, time_budget_s=None, keep_pdfs=True, only=(), redo=False, log=print):
    """Recheck eligible orders (grouped by issue, so each issue is fetched once)."""
    import fetch_ladder
    t0 = time.time()
    todo, skipped = select(ctx, plan, states, only=set(only), redo=redo)
    selected = todo[:limit] if limit is not None else todo
    by_url = {}
    for it in selected:
        by_url.setdefault(states[it["instrument_id"]]["source"]["url"], []).append(it)
    stats = Counter()
    rows, stopped = [], ""
    if not pdfplumber_available():
        log("RECHECK: pdfplumber is not installed (python -m pip install --user -r jobs/fr-originals/requirements.txt); "
            f"{len(selected)} eligible orders were not rechecked.")
        return rows, {"selected": len(selected), "stopped": "pdfplumber not installed", "stats": {"not_installed": 1},
                      "skipped": dict(skipped), "seconds": 0, "pending": [i["instrument_id"] for i in selected]}
    done = set()
    n = 0
    for url, group in by_url.items():
        if time_budget_s is not None and time.time() - t0 > time_budget_s:
            stopped = f"time budget of {time_budget_s / 60:.0f} minutes reached"
            break
        blob = None
        try:
            for it in group:
                n += 1
                iid = it["instrument_id"]
                try:
                    row, att = recheck_order(ctx, it, states[iid], log=log)
                except fetch_ladder.BudgetExceeded:
                    raise
                except Exception as exc:  # a damaged PDF must not stop the pass
                    row, att = ({"recheck_version": RECHECK_VERSION, "instrument_id": iid, "result": "error",
                                 "base_sha256": states[iid]["source"]["sha256"],
                                 "base_confidence": states[iid]["source"].get("location_confidence"),
                                 "reasons": [f"{type(exc).__name__}: {exc}"[:300]], "checked_utc": fetch_ladder.now_utc()},
                                {})
                blob = att.get("path") or blob
                if att.get("accepted") and not att.get("from_cache"):
                    stats["issue_downloads"] += 1
                save_recheck(ctx, row)
                rows.append(row)
                done.add(iid)
                stats[row["result"]] += 1
                log(f"[recheck {n}/{len(selected)}] {iid}: {row['base_confidence']} -> {row['new_confidence'] if row['result'] != 'error' else 'error'}"
                    f" ({row['result']}{'; ' + row['reasons'][0][:110] if row['reasons'] else ''})")
        except fetch_ladder.BudgetExceeded as exc:
            stopped = str(exc)
            break
        finally:
            if not keep_pdfs and blob and ctx["fetcher"].forget_body(blob):
                stats["issue_pdfs_deleted_after_use"] += 1
    return rows, {"selected": len(selected), "stopped": stopped, "stats": dict(stats), "skipped": dict(skipped),
                  "seconds": round(time.time() - t0, 1),
                  "pending": [i["instrument_id"] for i in selected if i["instrument_id"] not in done]}


def all_records(ctx, plan):
    out = {}
    for it in plan:
        r = load_recheck(ctx, it["instrument_id"])
        if r:
            out[it["instrument_id"]] = r
    return out


def overlay(ctx, plan, states):
    """{iid: (upgraded fragment, text file name, record)} for recheck upgrades that still match
    the order's current result (same bytes, base result still medium/low) and whose record is of
    the current RECHECK_VERSION (load_recheck) and has its reading-order text. Empty when no
    recheck ran. This is the ONLY place an upgrade is applied: the order's state always keeps the
    default locator's result (fr_originals.strip_recheck_overlay), so dropping or invalidating a
    record withdraws its upgrade on the next run."""
    out = {}
    if not recheck_dir(ctx).is_dir():
        return out
    for iid, r in all_records(ctx, plan).items():
        st = states.get(iid)
        if r.get("result") != "upgraded" or not st or st.get("status") != "found" or not r.get("fragment"):
            continue
        if not eligible(st)[0] or st["source"].get("sha256") != r.get("base_sha256"):
            continue
        if not r.get("text_file") or not recheck_text_path(ctx, r["text_file"]).is_file():
            continue
        out[iid] = (r["fragment"], r.get("text_file"), r)
    return out


def recheck_text_path(ctx, name):
    return recheck_dir(ctx) / "texts" / name


def write_recheck_outputs(out, ctx, plan, states, info=None):
    """RECHECK.jsonl (every recheck record so far) and RECHECK_SUMMARY.json."""
    import fetch_ladder
    out = Path(out)
    recs = all_records(ctx, plan)
    rows = []
    for it in plan:
        r = recs.get(it["instrument_id"])
        if r:
            rows.append(r)
    with open(out / "RECHECK.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    eligible_now = sum(1 for it in plan if eligible(states.get(it["instrument_id"]))[0])
    res = Counter(r.get("result") for r in rows)
    by_base = Counter((r.get("base_confidence"), r.get("result")) for r in rows)
    reasons = Counter()
    for r in rows:
        if r.get("result") == "stays" and r.get("reasons"):
            reasons[re.sub(r"\d+", "N", r["reasons"][0])[:120]] += 1
    kinds = Counter((r.get("evidence") or {}).get("heading", {}).get("kind") for r in rows if r.get("result") == "upgraded")
    summary = {
        "job": PRODUCED_BY, "mode": "recheck", "recheck_version": RECHECK_VERSION, "run_date": date.today().isoformat(),
        "library": "pdfplumber (MIT) word coordinates; reading order by recursive XY-cut",
        "orders_eligible_now": eligible_now,
        "orders_rechecked_total": len(rows),
        "upgraded_to_high": res.get("upgraded", 0), "stayed": res.get("stays", 0), "errors": res.get("error", 0),
        "by_base_confidence_and_result": {f"{k[0]}->{k[1]}": v for k, v in sorted(by_base.items(), key=str)},
        "upgrades_by_evidence_kind": dict(kinds),
        "upgrades_with_page_range_different_from_base": sum(1 for r in rows if r.get("result") == "upgraded"
                                                             and r.get("agrees_with_base_pages") is False),
        "stay_reasons_first": dict(reasons.most_common(15)),
        # Where the recheck disagrees with the first locator or with the OFR citation (examples).
        "upgraded_with_other_pages_than_base": [
            {"instrument_id": r["instrument_id"], "base": r.get("base_page_or_item"), "recheck": r.get("page_or_item")}
            for r in rows if r.get("result") == "upgraded" and r.get("agrees_with_base_pages") is False][:25],
        "heading_found_off_the_cited_page": [
            {"instrument_id": r["instrument_id"], "cited_pdf_page": (r.get("evidence") or {}).get("cited_pdf_page"),
             "heading_pdf_page": ((r.get("evidence") or {}).get("heading") or {}).get("pdf_page"),
             "running_head": (r.get("evidence") or {}).get("running_head_text")}
            for r in rows if r.get("result") == "stays" and (r.get("evidence") or {}).get("heading")
            and not (r.get("evidence") or {}).get("heading_on_cited_page")][:25],
        "examples_upgraded": [
            {"instrument_id": r["instrument_id"], "base_confidence": r.get("base_confidence"),
             "page_or_item": r.get("page_or_item"),
             "heading": ((r.get("evidence") or {}).get("heading") or {}).get("text"),
             "closing_tag": ((r.get("evidence") or {}).get("closing_tag") or {}).get("text"),
             "filing_line": ((r.get("evidence") or {}).get("filing_line") or {}).get("text"),
             "ofr_title_words_found": (r.get("evidence") or {}).get("ofr_title_words_found")}
            for r in rows if r.get("result") == "upgraded"][:12],
        "never": "A high result is never rechecked, downgraded or overwritten; an upgrade needs the heading (or bare "
                 "heading + closing tag) for this order number AND the filing line, on the cited FR page of the "
                 "OFR-dated issue, with unchanged bytes.",
        "caution": "Location leads only, not human-verified. Nothing here changes a provisional status, ledger or count.",
    }
    if info:
        summary["this_run"] = {k: info.get(k) for k in ("selected", "stopped", "stats", "skipped", "seconds")}
        summary["this_run"]["pending_not_reached"] = len(info.get("pending") or [])
    fetch_ladder.write_text_lf(out / "RECHECK_SUMMARY.json", json.dumps(summary, indent=1) + "\n")
    return summary


def carry_forward_recheck(ctx, plan, priors, log=print):
    """Seed <cache>/recheck/ from earlier committed RECHECK.jsonl (and the .recheck.txt texts)."""
    import fetch_ladder
    plan_ids = {p["instrument_id"] for p in plan}
    n = 0
    for prior in priors:
        rows = prior.jsonl("RECHECK.jsonl")
        if not rows:
            continue
        texts = None
        for r in rows:
            iid = r.get("instrument_id")
            if iid not in plan_ids or r.get("recheck_version") != RECHECK_VERSION or load_recheck(ctx, iid):
                continue
            if r.get("result") == "upgraded" and r.get("text_file"):
                if texts is None:
                    texts = prior.texts()
                body = texts.get(r["text_file"])
                if body is None:
                    continue  # an upgrade without its text is not carried
                d = recheck_dir(ctx) / "texts"
                d.mkdir(parents=True, exist_ok=True)
                (d / r["text_file"]).write_bytes(body)
            r = dict(r)
            r["carried_forward_from"] = prior.label
            recheck_dir(ctx).mkdir(parents=True, exist_ok=True)
            fetch_ladder.write_text_lf(_rpath(ctx, iid), json.dumps(r, ensure_ascii=False, indent=1))
            n += 1
    if n:
        log(f"Carried forward {n} recheck records.")
    return n
