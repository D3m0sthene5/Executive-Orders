"""Find one executive order's own pages inside a Federal Register PDF.

Works on govinfo's scanned daily issues (1936-1994, text layer from the scan)
and on per-document PDFs (1994 on). It reads the printed page numbers from
the running heads ("64 FEDERAL REGISTER, January 12, 1937", "Federal Register
/ Vol. 53, No. 5 / ... 487"), goes to the cited FR page, then confirms the
order by its number ("EXECUTIVE ORDER 10586", "Executive Order 12890 of ...",
or the 1930s closing tag "[No. 7532]") and ends at the first filing line
("[F. R. Doc. ...]" / "[FR Doc. ...]") after it.

Safeguards (version 2, after review):
- If the printed page numbers are read and the cited page is not in this
  PDF, the PDF is the wrong issue: nothing is taken from it, so the ladder
  moves on (e.g. to the govinfo link service).
- The order's marker is looked for on the cited page first, then the three
  pages after it, then the page before it. It is never taken from far away
  in the issue while the cited page is known.
- A heading counts only where it starts a line and is not a reference to the
  order ("AMENDING EXECUTIVE ORDER NO. 10153", "pursuant to Executive Order
  10153"). "No. 9337" style tags preceded by words such as "Docket" are
  ignored, and a tag is ignored when another document's filing line falls
  between the cited page and the tag.
- Every "medium" label says why in the notes.

The result is a LOCATION LEAD with a confidence label, not an authenticated
original. A human still checks the pages.
"""
from __future__ import annotations

import re

LOCATOR_VERSION = 2
MAX_SPAN = 25          # pages searched for the closing filing line
LONG_SPAN = 12         # longer page ranges are labelled medium (check the end)
WINDOW_AFTER = 3       # pages after the cited page searched for the order's marker
MIN_PAGES_FOR_WRONG_ISSUE = 3   # printed page numbers needed before calling a PDF the wrong issue
# The filing line that closes every FR document: "[F. R. Doc. 37-94; Filed ...]",
# "[FR Doc. 88-498 Filed ...]". OCR reads "[F" as "fP", "(F", "P H", "F R" etc.
FILING = re.compile(r"(?:[\[\(|]\s*|\b)[fl1I]?\s?[FP]\.?\s?[RHK]\.?\s*D\s?o\s?c\.?\s*\d", re.I)
# Modern issues also print "Billing code 3195-01-M" right after a presidential document.
BILLING = re.compile(r"B\s?i\s?l\s?l\s?i\s?n\s?g\s+c\s?o\s?d\s?e", re.I)
EXTRA_PAGES_IF_NO_END = 2
HEADING_ANY = re.compile(r"E\s?X\s?E\s?C\s?U\s?T\s?I\s?V\s?E\s+O\s?R\s?D\s?E\s?R", re.I)
CONTENTS = re.compile(r"^\s*(?:CONTENTS|Contents)\b|\bContents\s*$|/\s*Contents\b", re.M)

# Words that, right before "Executive Order NNNN", make it a reference, not the order's own heading.
REFERENCE_BEFORE = re.compile(
    r"(?:\b(?:amend\w*|revok\w*|supersed\w*|terminat\w*|modif\w*|rescind\w*|suspend\w*|implement\w*|"
    r"under|pursuant\s+to|by|of|in|to|see|and|or|with|per|from|cited|issued|than|as)\b)\W*$", re.I)
# Same check for the end of the previous line (only the strongest words).
REFERENCE_PREV_LINE = re.compile(
    r"(?:\b(?:amend\w*|revok\w*|supersed\w*|pursuant\s+to|under|by|of|in|to|and)\b)\W*$", re.I)
# Text allowed before a real heading on its line: page furniture of presidential documents.
HEADING_PREFIX_OK = re.compile(
    r"^\W*(?:Title\s*3\W*(?:The\s+President\W*)?|Presidential\s+Documents\W*|The\s+President\W*)?$", re.I)
# Words that make "No. 9337" some other kind of number (an FCC docket, a file, a case ...).
TAG_EXCLUDE_BEFORE = re.compile(
    r"\b(?:docket|file|case|project|serial|form|claim|application|permit|licen[cs]e|order|orders|contract|"
    r"grant|patent|report|bulletin|circular|release|amendment|regulation|regulations|notice|decision|"
    r"opinion|proclamation|plan|lot|tract|survey|award|schedule|ruling|petition|appeal|docket\s+no)\W*$",
    re.I)


def digits_pattern(number: str) -> str:
    """'10586' -> '1\\s?0\\s?5\\s?8\\s?6' (OCR sometimes splits digits)."""
    base = re.match(r"\d+", number).group(0)
    suffix = number[len(base):]
    pat = r"\s?".join(base)
    if suffix:
        pat += r"\s?-?\s?" + re.escape(suffix)
    return pat


# After a plain number: no letter suffix such as "-A" or "A]", because "7700-A"
# is a different order (EO 7700A) from EO 7700.
LETTER_SUFFIX = re.compile(r"[ \t]?[-‐-—][ \t]?[A-Za-z](?![A-Za-z])|[A-Za-z](?![A-Za-z])")
NO_SUFFIX = r"(?![ \t]?[-‐-—][ \t]?[A-Za-z](?![A-Za-z]))(?![A-Za-z](?![A-Za-z]))"


def marker_patterns(number: str):
    d = digits_pattern(number)
    tail = r"(?![\d])" + ("" if re.search(r"[A-Za-z]$", number) else NO_SUFFIX)
    return [
        ("heading", re.compile(rf"E\s?X\s?E\s?C\s?U\s?T\s?I\s?V\s?E\s+O\s?R\s?D\s?E\s?R\s*(?:N\s?o\.?\s*)?{d}{tail}", re.I)),
        # "[No. 7532]"; OCR often reads the closing bracket as 1, l, I or |
        ("closing_number_tag", re.compile(rf"\[?\s*N\s?o\.?\s*{d}\s?[\]1lI|)](?![\d])", re.I)),
        ("number_tag", re.compile(rf"\bN\s?o\.\s*{d}{tail}")),
    ]


def fuzzy_heading(text: str, number: str):
    """'EXECUTIVE ORDER 9#37' for 9337: a heading whose number differs from
    the wanted one in at most one OCR-damaged (non-digit) character. Returns a
    match span or None. References ('amending Executive Order ...') are skipped."""
    base = re.match(r"\d+", number).group(0)
    if len(base) < 4:
        return None
    for m in re.finditer(HEADING_ANY.pattern + r"\s*(?:N\s?o\.?\s*)?(\S(?:\s{0,2}\S){%d})" % (len(base) - 1), text, re.I):
        got = re.sub(r"\s", "", m.group(1))[: len(base)]
        tail = text[m.end(1): m.end(1) + 1]
        if len(got) != len(base) or tail.isdigit():
            continue
        if not re.search(r"[A-Za-z]$", number) and LETTER_SUFFIX.match(text, m.end(1)):
            continue
        diffs = [(a, b) for a, b in zip(got, base) if a != b]
        if len(diffs) == 1 and not diffs[0][0].isdigit() and heading_context(text, m.start()) != "reference":
            return m.start(), m.end()
    return None


def header_numbers(text: str):
    """Integers printed in the running head/foot of a page (candidate page numbers)."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    region = lines[:2] + lines[-1:]
    nums = set()
    for ln in region:
        for m in re.finditer(r"(?<![\d,.])(\d{1,5})(?![\d,])", ln):
            v = int(m.group(1))
            if v > 0:
                nums.add(v)
    return nums


def printed_page_map(page_texts):
    """{pdf_index: printed_page} for pages whose number is confirmed by a neighbour.

    A candidate number counts only if a nearby page carries the number that
    the same offset predicts, which filters out years, volume numbers etc.
    """
    cands = [header_numbers(t) for t in page_texts]
    out = {}
    n = len(page_texts)
    for i in range(n):
        best = None
        for c in sorted(cands[i]):
            support = sum(1 for j in range(max(0, i - 3), min(n, i + 4))
                          if j != i and (c + (j - i)) in cands[j])
            if support and (best is None or support > best[1]):
                best = (c, support)
        if best:
            out[i] = best[0]
    return out


def find_printed_page(page_texts, page_map, target):
    """PDF index (0-based) of printed FR page `target`, and how it was found."""
    for i, p in sorted(page_map.items()):
        if p == target:
            return i, "printed_page_number_matched"
    if not page_map:
        return None, "no_page_numbers_read"
    lower = [(i, p) for i, p in page_map.items() if p < target]
    upper = [(i, p) for i, p in page_map.items() if p > target]
    if lower:
        i, p = max(lower, key=lambda x: x[1])
        est = i + (target - p)
        if upper:
            ui, up = min(upper, key=lambda x: x[1])
            if est >= ui or (up - target) != (ui - est):
                est = None
        if est is not None and 0 <= est < len(page_texts):
            return est, "interpolated_from_neighbouring_page_numbers"
    if upper:
        i, p = min(upper, key=lambda x: x[1])
        est = i - (p - target)
        if 0 <= est < len(page_texts):
            return est, "counted_back_from_next_numbered_page"
    return None, "printed_page_outside_this_pdf"


def first_match(page_texts, pattern, start, end, after=None):
    """First (page_index, offset) match of pattern within pages start..end."""
    for i in range(max(0, start), min(len(page_texts), end + 1)):
        text = page_texts[i]
        pos = after[1] if after and after[0] == i else 0
        if after and i < after[0]:
            continue
        m = pattern.search(text, pos)
        if m:
            return i, m.start(), m.end()
    return None


def is_contents_page(text):
    return bool(CONTENTS.search(text[:400]))


def heading_context(text, start):
    """'heading' (starts a line), 'reference' (a mention of the order) or 'midline'."""
    line_start = text.rfind("\n", 0, start) + 1
    prefix = text[line_start:start]
    if REFERENCE_BEFORE.search(prefix):
        return "reference"
    if HEADING_PREFIX_OK.match(prefix) or len(re.sub(r"[\W_]", "", prefix)) <= 2:
        prev = text[max(0, line_start - 60):max(0, line_start - 1)]
        if prefix.strip() == "" and REFERENCE_PREV_LINE.search(prev):
            return "reference"
        return "heading"
    return "midline"


def tag_context_ok(text, start):
    line_start = text.rfind("\n", 0, start) + 1
    prefix = text[line_start:start].rstrip(" [(")
    return not TAG_EXCLUDE_BEFORE.search(prefix)


def filing_between(page_texts, idx, mi, mstart):
    """True if a filing line closes some document between the cited page and a marker."""
    if mi <= idx:
        return False
    for j in range(idx + 1, mi):
        if FILING.search(page_texts[j]) or BILLING.search(page_texts[j]):
            return True
    head = page_texts[mi][:mstart]
    return bool(FILING.search(head) or BILLING.search(head))


def start_after_filing(page_texts, idx, mi, mstart):
    """For a closing tag that follows another document's filing line: the page of the
    'Executive Order' heading that starts the order after that filing line, if the
    tag is on the cited page or the next one. None otherwise."""
    if mi > idx + 1:
        return None
    last = None
    for j in range(idx + 1, mi + 1):
        text = page_texts[j] if j != mi else page_texts[j][:mstart]
        for pat in (FILING, BILLING):
            for m in pat.finditer(text):
                if last is None or (j, m.end()) > last:
                    last = (j, m.end())
    if last is None:
        return None
    for j in range(last[0], mi + 1):
        lo = last[1] if j == last[0] else 0
        hi = mstart if j == mi else len(page_texts[j])
        if HEADING_ANY.search(page_texts[j][lo:hi]):
            return j
    return None


def find_marker(page_texts, number, pages, idx=None):
    """Search the given pages in order. Returns (marker or None, skipped_count).

    marker = (kind, page_index, start, end, start_page or None). Kinds, best
    first on each page: heading, closing_number_tag, number_tag, heading_midline.
    """
    pats = dict(marker_patterns(number))
    skipped = 0
    n = len(page_texts)
    for i in pages:
        if not 0 <= i < n:
            continue
        text = page_texts[i]
        contents = is_contents_page(text)
        found = {}
        if not contents:
            for m in pats["heading"].finditer(text):
                ctx = heading_context(text, m.start())
                if ctx == "reference":
                    skipped += 1
                    continue
                kind = "heading" if ctx == "heading" else "heading_midline"
                if kind not in found:
                    found[kind] = (kind, i, m.start(), m.end(), None)
                if kind == "heading":
                    break
        for kind in ("closing_number_tag", "number_tag"):
            if contents and kind == "number_tag":
                continue
            for m in pats[kind].finditer(text):
                if not tag_context_ok(text, m.start()):
                    skipped += 1
                    continue
                begin = None
                if idx is not None and filing_between(page_texts, idx, i, m.start()):
                    if kind == "closing_number_tag":
                        begin = start_after_filing(page_texts, idx, i, m.start())
                    if begin is None:
                        skipped += 1
                        continue
                found[kind] = (kind, i, m.start(), m.end(), begin)
                break
        for kind in ("heading", "closing_number_tag", "number_tag", "heading_midline"):
            if kind in found:
                return found[kind], skipped
    return None, skipped


def locate_order(page_texts, number: str, fr_page: int | None = None, page_hint: int | None = None,
                 single_document: bool = False):
    """Locate an order. page_texts: list of page strings (index 0 = PDF page 1).

    Returns a dict:
      found (bool), first_page/last_page (1-based PDF pages), confidence
      (high/medium/low), method, marker_kind, printed_page_found, notes,
      locator_version.
    """
    n = len(page_texts)
    res = {"found": False, "first_page": None, "last_page": None, "confidence": "none",
           "method": "", "marker_kind": None, "printed_page_found": None, "notes": [],
           "locator_version": LOCATOR_VERSION}
    if n == 0:
        res["notes"].append("PDF has no pages")
        return res

    if single_document:
        marker, skipped = find_marker(page_texts, number, range(n))
        res.update(found=True, first_page=1, last_page=n, method="whole_per_document_pdf")
        if marker:
            res["marker_kind"] = marker[0]
            # In a per-document PDF the URL already names the document; any own marker is enough.
            res["confidence"] = "high"
        else:
            res["confidence"] = "medium"
            res["notes"].append(f"medium because: order number {number} not seen as a heading or tag in the text layer"
                                + (f" (only {skipped} reference-style mention(s))" if skipped else ""))
        return res

    idx, how = (None, "no_fr_page_given")
    page_map = {}
    if fr_page:
        page_map = printed_page_map(page_texts)
        idx, how = find_printed_page(page_texts, page_map, fr_page)
    if idx is None and page_hint and 1 <= page_hint <= n:
        idx, how = page_hint - 1, "govinfo_link_service_page_hint"
    res["printed_page_found"] = idx is not None
    res["method"] = how

    if idx is None and how == "printed_page_outside_this_pdf" and len(page_map) < MIN_PAGES_FOR_WRONG_ISSUE:
        how = res["method"] = "too_few_page_numbers_read"
    if idx is None and how == "printed_page_outside_this_pdf":
        lo, hi = min(page_map.values()), max(page_map.values())
        res["notes"].append(f"cited FR page {fr_page} is not in this PDF (its printed pages run about {lo}-{hi}); "
                            "probably the wrong issue, so nothing is taken from it")
        return res

    medium = []
    if idx is not None:
        order = [idx + k for k in range(WINDOW_AFTER + 1)] + [idx - 1]
        marker, skipped = find_marker(page_texts, number, order, idx)
        if not marker:
            for i in order:
                if 0 <= i < n:
                    span = fuzzy_heading(page_texts[i], number)
                    if span:
                        marker = ("heading_ocr_damaged", i, span[0], span[1], None)
                        break
    else:
        # No page anchor at all: search the whole PDF, but only for strong markers.
        marker, skipped = find_marker(page_texts, number, range(n))
        if marker and marker[0] not in ("heading", "closing_number_tag"):
            marker = None
        if marker:
            medium.append(f"the cited FR page could not be found in this PDF ({how.replace('_', ' ')})"
                          if fr_page else "no FR page was given; the order was found by its number alone")
            res["method"] = "order_number_marker_only"
    if skipped:
        res["notes"].append(f"{skipped} other mention(s) of the number skipped (references, docket-style or "
                            "other numbers, or past another document's filing line)")

    if marker:
        kind, mi, mstart, mend, begin = marker
        res["marker_kind"] = kind
        if begin is not None:
            start = begin
            medium.append("the closing tag follows another document's filing line, so the order is taken to "
                          f"start at the 'Executive Order' heading after it (PDF page {begin + 1})")
        elif kind.startswith("heading"):
            start = mi
        elif idx is not None and idx <= mi:
            start = idx
        else:
            # closing tag style: walk back to the nearest generic heading (max 3 pages)
            start = mi
            for j in range(mi, max(-1, mi - 4), -1):
                if HEADING_ANY.search(page_texts[j][: mstart if j == mi else None]):
                    start = j
                    break
        if kind == "heading_ocr_damaged":
            medium.append("order number read with one OCR-damaged character next to an EXECUTIVE ORDER heading")
        if kind == "heading_midline":
            medium.append("the order's heading is not at the start of a line")
        if kind == "number_tag":
            medium.append(f"the number was seen only as 'No. {number}', not as a heading or closing tag")
        if idx is not None and start != idx:
            where = "before" if start < idx else "after"
            medium.append(f"the order's start was found on PDF page {start + 1}, {abs(start - idx)} page(s) {where} "
                          f"the cited FR page (PDF page {idx + 1})")
        after = (mi, mend if kind.startswith("heading") else mstart)
        end_hit = (first_match(page_texts, FILING, mi, min(n - 1, mi + MAX_SPAN), after=after)
                   or first_match(page_texts, BILLING, mi, min(n - 1, mi + MAX_SPAN), after=after))
        if end_hit:
            end = end_hit[0]
        else:
            end = min(n - 1, mi + EXTRA_PAGES_IF_NO_END)
            medium.append(f"no filing line ([F. R. Doc. ...]) found after the order; last page uncertain, "
                          f"so {end - mi} following page(s) are included")
        end = max(start, end)
        if end - start + 1 > LONG_SPAN:
            medium.append(f"long page range ({end - start + 1} pages); check where the order ends")
        res.update(found=True, first_page=start + 1, last_page=end + 1,
                   confidence="medium" if medium else "high")
        if medium:
            res["notes"].append("medium because: " + "; ".join(medium))
        return res

    if idx is not None:
        anchor = None
        h = HEADING_ANY.search(page_texts[idx])
        if h:
            anchor = (idx, h.end())
        end_hit = first_match(page_texts, FILING, idx, min(n - 1, idx + MAX_SPAN), after=anchor)
        end = end_hit[0] if end_hit else idx
        res.update(found=True, first_page=idx + 1, last_page=end + 1, confidence="low")
        res["notes"].append(f"low because: order number {number} not seen in the text layer (OCR?); "
                            f"pages chosen from the FR page number only ({how})")
        return res
    res["notes"].append("neither the cited FR page nor the order number could be found in this PDF")
    return res
