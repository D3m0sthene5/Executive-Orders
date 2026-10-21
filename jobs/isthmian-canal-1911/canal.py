"""Index the 1911 compilation "Executive Orders Relating to the Isthmian Canal Commission" by its
table of contents, cut the body into one text per document, check each date against the body's
closing dateline, and compare the President's orders with the census.

The volume prints no executive order numbers, no headings in the body and no closing tags. So:
- documents are found from the contents (PDF pages 6-13): one entry per document, with its
  printed page; a document runs from its page to the page before the next entry's page;
- the EO number of a presidential order comes only from the committed, hand-reviewed crosswalk
  (data/ic1911_crosswalk.csv), never from this code.

The job reads the committed text layer (data/ic1911_pages.jsonl), never the network.
Machine leads only: nothing here admits, merges, dates or changes a census identity or a status.
"""

import csv
import difflib
import hashlib
import json
import pathlib
import re

OFFSET = 13                      # PDF page = printed page + 13
CONTENTS_PDF_PAGES = (6, 13)
JOB_NAME = "isthmian-canal-1911"
ROUTE = "official/ic_compilation_1911"

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]
MONTH_NO = {m: i for i, m in enumerate(MONTHS, 1)}
# Contents abbreviations, with the OCR misreads seen in this volume ("Mai-." is Mar., "Dcic." is Dec.)
SHORT_NO = {"Jan": 1, "Feb": 2, "Mar": 3, "Mai": 3, "Apr": 4, "May": 5, "June": 6, "July": 7, "Aug": 8,
            "Sept": 9, "Oct": 10, "Nov": 11, "Dec": 12, "Dcic": 12}
# Short month misreads that a fuzzy match cannot safely catch ("Hay I4, 1909" is May 14)
MONTH_MISREADS = {"hay": "May", "ajml": "April"}

CATEGORY = {
    ("Order", "president"): "presidential_order",
    ("Order", "secretary_of_war"): "secretary_of_war_order",
    ("Letter", "president"): "presidential_letter",
    ("Letter", "secretary_of_war"): "secretary_of_war_letter",
    ("Proclamation", "president"): "proclamation",
    ("Action", "commission"): "commission_action",
    ("Circular", "war_department"): "war_department_circular",
}
PRESIDENTIAL = ("presidential_order", "presidential_letter", "proclamation")

# ---- contents ---------------------------------------------------------------------------------
CONTENTS_SKIP = re.compile(r"(?i)^(table of .*|page\.?|\S{0,5}\s*contents\W*\s*\S{0,5}|[ivxl]{1,4}|ni)$")
ENTRY_START = re.compile(r"^\W*(Letter|Order|Proclamation|Action|Circular)\b")
# "Order of the President", "Order, of the President", "Order of tiie President", "secretary of W^ar"
ISSUER = re.compile(r"^\W*(Letter|Order|Proclamation|Action|Circular)\s*,?\s+of\s+(?:t\w{1,3}\s+)?"
                    r"(President|[Ss]ecretary\s+of\s+W\W{0,2}ar|commission|War\s+Department)\b")
LINE_END_PAGE = re.compile(r"(?:^|\s)([0-9Il]{1,3})\s*$")
CONTENTS_DATE = re.compile(r"^\W*(Jan|Feb|Mar|Mai|Apr|May|June|July|Aug|Sept|Oct|Nov|Dec|Dcic)\W{0,3}\s*"
                           r"(\d{1,2}|\d\.\d)\s*,\s*([^,]{2,7}?)\s*[,.]")

# ---- body pages -------------------------------------------------------------------------------
# Even pages: "6 EXECUTIVE ORDERS." (OCR: OEDEES, ORDEJRS, "EXEGUTlVi: UKDERS", "2Q4", "118 •").
EVEN_HEAD = re.compile(r"^\W*[\w\"'-]{0,4}\W{0,3}\s*EXE\S*\s+\S{3,9}\s*$")
# Odd pages: "ISTHMIAN CANAL COMMISSION. 7" (OCR: C0MMI6SI0N, CAXAL, rSTHMTAK, "COMMISSION. * 213").
ODD_HEAD = re.compile(r"(?i)^\W*\S?STHM\S*\s+CA\S*\s+C\S{0,2}M\S*((?:\s+\S{1,4}){0,2})\s*$")
BARE_NUMBER = re.compile(r"^\W*(\d{1,3})\s*$")
# GPO signature mark at the foot of every 16th page: "98987—11 2", ".98987—11—4"
GPO_FOOTER = re.compile(r"^\W*98987\s*[—–-]\s*11(?:\s*[—–-]\s*|\s+)\d{1,2}\s*$")
TITLE_LINES = re.compile(r"^\s*(RELATING TO THE|ISTHMIAN CANAL COMMISSION\.?)\s*$")
NOISE_LINE = re.compile(r"^\W*\w?\W*$")   # stray marks at a page foot: "I", "O", "a", "L.'"
# A document's last line is a closing: signature, dateline, office or place line.
CLOSING_LINE = re.compile(r"(?i)(secretary\s+of|s\S{1,3}etary\s+of\s+war|the\s+president\.?\s*$|enclosure|^\W*t\.\s*r\.|"
                          r"congress\.\)$|ofwar|washington\W+d\W*\s*[cgo]\W*$|^\W*\d{1,2}\s*,\s*19\d\d\.?\s*$|commission\.\s*$)")
# A page that begins a new document begins with an address, dateline, title or enacting words.
OPENING_LINE = re.compile(r"(?i)^\W*(war\s+department|(the\s+)?white\s+house|united\s+states\s+civil|by\s+(direction|authority|virtue)|"
                          r"it\s+is\s+(hereby\s+)?ordered|under\s+(the\s+)?authority|mr\.?\s+president|my\s+dear|sirs?\b|executive\s+order)")
CAPS_TITLE = re.compile(r"^[A-Z][A-Z0-9 ,.;:'\"()-]{7,}$")

# ---- body dates -------------------------------------------------------------------------------
BODY_DATE = re.compile(r"\b([A-Za-z][A-Za-z^]{2,9})\.?,?\s+(lf>|[0-9IlSO|]{1,2}|[A-Z])\s*,?\s*"
                       r"(1\s?9\s?[0-9OoIlS]\s?[0-9OoIlSJ^]{1,2})")
WHITE_HOUSE_STRICT = re.compile(r"White\s+House,\s*(?:\n\s*Washington,(?:\s*D\.\s*C\.,)?\s*)?$")
WHITE_HOUSE_OCR = re.compile(r"(?i)\S{0,3}h\S?te\s+\S{2,9}\s*(?:\n\s*\S*ington\s*,?(?:\s*D\W{0,2}\s*C\W{0,2})?\s*)?$")
DIGIT_FIX = str.maketrans({"I": "1", "l": "1", "|": "1", "O": "0", "o": "0", "S": "8"})
REF_DATE = re.compile(r"\b(?:Jan|Feb|Mar|Apr|May|June|July|Aug|Sept|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2}),\s*(19[01]\d)")

# A signature line may open with a seal mark or a complimentary close: "Very sincerely yours, Wm. H. Taft."
SIG_PREFIX = r"^\W*(?:\[seal\.?\]\s*)?(?:(?:[Vv]ery\s+)?(?:[Rr]espectfully|[Ss]incerely|[Tt]ruly|[Cc]ordially)(?:\s+yours)?,?\s*)?"
SIGNERS = [
    ("Theodore Roosevelt", re.compile(SIG_PREFIX + r"(?:Theodore|T\.)\s*[RH]o\w*e\w*t\b|^\W*T\.\s*R\.\s*$")),
    ("William H. Taft", re.compile(SIG_PREFIX + r"['^]?(?:Wm|\^YM|YM)\W{0,2}\s*H?\W{0,2}\s*(?:IT\s+)?Taft\b")),
    ("Luke E. Wright", re.compile(r"Luke\s+E\.?\s+Wright")),
    ("J. M. Dickinson", re.compile(r"J\.\s*M\.\s*Dickinson")),
    ("Henry L. Stimson", re.compile(r"Stimson")),
    ("Robert Shaw Oliver", re.compile(r"Oliver,?\s*$")),
    ("Alvey A. Adee", re.compile(r"Adee")),
]
TAFT_PRESIDENT_FROM = "1909-03-04"
BY_DIRECTION = re.compile(r"(?i)by\s+(?:the\s+)?direct\w*\s+of\s+the\s+Pres\w*")
APPROVED = re.compile(r"(?i)approved[:.,]?\s*(?:for the President|\n?\s*(?:Theodore|T\.)\s+[RH]oosevelt|\n?\s*Wm\.?\s*H\.?\s*Taft)")
AFFECT_VERB = re.compile(r"(?i)\b(amend\w*|revok\w*|repeal\w*|supersed\w*|modify\w*|modifi\w*)\b")
CONFLICT_REVOKED = re.compile(r"(?i)orders?\s+in\s+conf\S*\s+(?:here)?with\s+(?:are|is)\s+(?:hereby\s+)?revoked")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def load_pages(path: pathlib.Path) -> dict[int, str]:
    pages = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            pages[int(d["page"])] = d["text"]
    return pages


# ---- contents ---------------------------------------------------------------------------------

def page_token(tok: str) -> int | None:
    """'119' -> 119; 'Ill' -> 111 (OCR); a word without a digit is not a page number."""
    if tok == "Ill" or re.search(r"\d", tok):
        return int(tok.replace("I", "1").replace("l", "1"))
    return None


def year_candidates(raw: str) -> tuple[list[int], bool]:
    """Years 1904-1911 that a contents year token can be. Returns (candidates, repaired)."""
    s = re.sub(r"\s", "", raw).translate(str.maketrans({"O": "0", "o": "0", "I": "1", "l": "1", "i": "1"}))
    if re.fullmatch(r"19(?:0[4-9]|1[01])", s):
        return [int(s)], s != raw
    pat = re.sub(r"[^0-9]+", "?", s)
    if len(pat) > 4:
        return [], True
    pat = pat.ljust(4, "?")  # a digit lost at the end ("19U")
    return [y for y in range(1904, 1912) if all(p in ("?", c) for p, c in zip(pat, str(y)))], True


def parse_contents(pages: dict[int, str]) -> list[dict]:
    """One dict per contents entry, in book order."""
    entries = []
    for p in range(CONTENTS_PDF_PAGES[0], CONTENTS_PDF_PAGES[1] + 1):
        for raw in pages.get(p, "").split("\n"):
            s = raw.strip().lstrip("■").strip()
            if not s or CONTENTS_SKIP.match(s):
                continue
            if ENTRY_START.match(s):
                entries.append({"lines": [s], "contents_pdf_page": p})
            elif entries:
                entries[-1]["lines"].append(s)
    out = []
    for seq, e in enumerate(entries, 1):
        text = norm_space(" ".join(e["lines"]))
        page, page_line = None, None
        for i, l in enumerate(e["lines"]):
            m = LINE_END_PAGE.search(l)
            if m and page_token(m.group(1)) is not None:
                page, page_line = page_token(m.group(1)), i
        im = ISSUER.match(text)
        kind = ENTRY_START.match(text).group(1)
        issuer = ""
        if im:
            w = im.group(2).lower()
            issuer = ("president" if w == "president" else "commission" if w == "commission"
                      else "war_department" if w.startswith("war") else "secretary_of_war")
        # the same text without the page number (which can sit mid-entry: "... and 119" / "prescribing ...")
        lines_wo = list(e["lines"])
        if page_line is not None:
            lines_wo[page_line] = LINE_END_PAGE.sub("", lines_wo[page_line])
        text_wo = norm_space(" ".join(lines_wo))
        rest = text_wo[ISSUER.match(text_wo).end():] if im else text_wo
        dm = CONTENTS_DATE.match(rest)
        month = day = None
        years, repaired, raw_date = [], False, ""
        subject = rest
        if dm:
            month = SHORT_NO[dm.group(1)]
            day = int(dm.group(2).replace(".", ""))
            years, repaired = year_candidates(dm.group(3))
            repaired = repaired or dm.group(1) in ("Mai", "Dcic") or "." in dm.group(2)
            raw_date = dm.group(0).strip(" ,.")
            subject = rest[dm.end():]
        subject = re.sub(r"(\w)- ([a-z])", r"\1\2", subject)          # "commis- sioners"
        subject = re.sub(r"[\s.,'<»_^\-]+$", "", subject.lstrip(" ,.")).strip()
        out.append({
            "seq": seq, "kind": kind, "issuer": issuer,
            "category": CATEGORY.get((kind, issuer), "unclassified"),
            "month": month, "day": day, "year_candidates": years, "contents_date_ocr_repaired": repaired,
            "contents_date_raw": raw_date, "printed_page": page,
            "page_mid_entry": page_line is not None and page_line < len(e["lines"]) - 1,
            "contents_pdf_page": e["contents_pdf_page"], "contents_text": text, "subject": subject,
        })
    return out


# ---- body ---------------------------------------------------------------------------------------

def page_lines(text: str, pdf_page: int) -> tuple[list[str], dict]:
    """Body lines of one page without its running head, GPO footer and (page 1) title and number."""
    lines = [l.rstrip() for l in text.split("\n")]
    info = {"head": "", "head_number": None, "footer": False}
    kept = []
    for l in lines:
        if GPO_FOOTER.match(l.strip()):
            info["footer"] = True
            continue
        kept.append(l)
    lines = kept
    first = next((i for i, l in enumerate(lines) if l.strip()), None)
    if first is not None:
        h = lines[first].strip()
        n = None
        if BARE_NUMBER.match(h):
            n = BARE_NUMBER.match(h).group(1)
        elif EVEN_HEAD.match(h):
            n = re.match(r"^\W*([\w\"'-]{0,4})", h).group(1)
        elif ODD_HEAD.match(h):
            n = ODD_HEAD.match(h).group(1).split()[-1] if ODD_HEAD.match(h).group(1).split() else ""
        else:
            h = None
        if h is not None:
            info["head"] = h
            info["head_number"] = int(n) if n and n.isdigit() else None
            del lines[first]
            nxt = next((i for i, l in enumerate(lines) if l.strip()), None)
            if BARE_NUMBER.match(h) and nxt is not None and (EVEN_HEAD.match(lines[nxt].strip()) or ODD_HEAD.match(lines[nxt].strip())):
                info["head"] += " / " + lines[nxt].strip()   # "214" / "EXECUTIVE ORDERS."
                del lines[nxt]
    printed = pdf_page - OFFSET
    if printed == 1:
        while lines and (not lines[0].strip() or TITLE_LINES.match(lines[0])):
            lines.pop(0)
    if lines and lines[-1].strip() == str(printed):
        lines.pop()
    while lines and NOISE_LINE.match(lines[-1]) and not lines[-1].strip().isdigit():
        lines.pop()
    return lines, info


def is_dateline(line: str) -> bool:
    """A line that ends with a date and has at most a short place or 'Approved' before it."""
    m = None
    for m in BODY_DATE.finditer(line):
        pass
    return bool(m and re.fullmatch(r"\W*", line[m.end():]) and len(line[:m.start()]) <= 45
                and read_month(m.group(1)) is not None)


def split_shared_page(lines: list[str]) -> int | None:
    """Index of the first closing dateline on a page shared by two documents (split after it)."""
    for i, l in enumerate(lines):
        if is_dateline(l) and i < len(lines) - 1:
            return i
    return None


def read_month(tok: str) -> int | None:
    t = re.sub(r"[^a-z]", "", tok.lower())
    if t in MONTH_MISREADS:
        return MONTH_NO[MONTH_MISREADS[t]]
    for m in MONTHS:
        if t == m.lower():
            return MONTH_NO[m]
    if len(t) >= 5:
        best = difflib.get_close_matches(t, [m.lower() for m in MONTHS], n=1, cutoff=0.7)
        if best:
            return MONTH_NO[best[0].capitalize()]
    return None


def read_body_date(m) -> tuple[str, str]:
    """(YYYY-MM-DD or '', reading) for a BODY_DATE match. reading: exact, ocr, damaged_day."""
    mon = read_month(m.group(1))
    if mon is None:
        return "", ""
    y = re.sub(r"\s", "", m.group(3)).translate(DIGIT_FIX).replace("J^", "4").replace("J", "4")
    if not re.fullmatch(r"19(?:0[4-9]|1[01])", y[:4]) or len(y) != 4:
        return "", ""
    d_raw = m.group(2)
    d = d_raw.translate(DIGIT_FIX)
    exact = m.group(1) in MONTHS and d_raw.isdigit() and m.group(3).isdigit()
    if not d.isdigit() or not 1 <= int(d) <= 31:
        return "%s-%02d-??" % (y, mon), "damaged_day"
    return "%s-%02d-%02d" % (y, mon, int(d)), "exact" if exact else "ocr"


def body_dates(text: str) -> list[dict]:
    """Every date in a document's text, classed as White House signature line, other dateline or mention."""
    out = []
    for m in BODY_DATE.finditer(text):
        date, reading = read_body_date(m)
        if not date:
            continue
        before = text[max(0, m.start() - 60):m.start()]
        line_start = text.rfind("\n", 0, m.start()) + 1
        line_end = text.find("\n", m.end())
        line = text[line_start:line_end if line_end >= 0 else len(text)]
        if WHITE_HOUSE_STRICT.search(before) and reading == "exact":
            where = "white_house_strict"
        elif WHITE_HOUSE_OCR.search(before):
            where = "white_house_ocr"
        elif is_dateline(line):
            where = "dateline"
        else:
            where = "mention"
        out.append({"date": date, "reading": reading, "where": where})
    return out


def date_check(expected: str, found: list[dict]) -> str:
    """How the body supports the document's date (best level first)."""
    for level in ("white_house_strict", "white_house_ocr", "dateline"):
        if any(f["where"] == level and f["date"] == expected for f in found):
            return level
    if any(f["date"] == expected for f in found):
        return "mention_only"
    if expected and any(f["where"] != "mention" and f["date"].endswith("??") and f["date"][:7] == expected[:7] for f in found):
        return "damaged_day"
    if any(f["where"] != "mention" for f in found):
        return "body_dateline_differs"
    return "not_found"


CONFIRMED = ("white_house_strict", "white_house_ocr", "dateline")


def signers(lines: list[str], date: str) -> list[str]:
    found = []
    for l in lines:
        s = l.strip()
        if len(s) > 45:
            continue
        for name, pat in SIGNERS:
            if pat.search(s):
                if name == "William H. Taft":
                    name += " (President)" if date and date >= TAFT_PRESIDENT_FROM else " (Secretary of War)"
                if name not in found:
                    found.append(name)
    return found


def is_closing(line: str) -> bool:
    """A document's last line: a signature, dateline, office or place line."""
    s = line.strip()
    return bool(s) and (is_dateline(s) or bool(CLOSING_LINE.search(s))
                        or any(p.search(s) for _, p in SIGNERS) and len(s) <= 45)


def is_opening(line: str) -> bool:
    """A line that can begin a document: address, dateline, title in capitals or enacting words."""
    s = line.strip()
    return bool(OPENING_LINE.match(s) or CAPS_TITLE.match(s) or is_dateline(s) or re.match(r"^To\s+[A-Z]", s))


def tail_end(lines: list[str]) -> int | None:
    """Index of the last line of a previous document's tail at the top of a page: its signature line,
    plus any White House or bare dateline right after it. None when no signature comes first."""
    for i, l in enumerate(lines):
        s = l.strip()
        if len(s) <= 45 and any(p.search(s) for _, p in SIGNERS):
            j = i
            while j + 1 < len(lines) and (re.search(r"(?i)h\S?te\s+\S{2,9}", lines[j + 1])
                                          or re.fullmatch(r"\W*\S+\.?\s+\S{1,3},?\s*19\S\S\W*", lines[j + 1].strip())
                                          or re.match(r"(?i)^\W*approved\b", lines[j + 1].strip())):
                j += 1
            return j
        if i > 0 and OPENING_LINE.match(s):
            return None
    return None


def build_documents(pages: dict[int, str]) -> tuple[list[dict], dict]:
    """Contents entries with their body spans, texts, dates and flags."""
    entries = parse_contents(pages)
    last_pdf = max(p for p, t in pages.items() if p > OFFSET and t.strip())
    body = {}
    heads = {}
    for pdf in range(OFFSET + 1, last_pdf + 1):
        body[pdf], heads[pdf] = page_lines(pages.get(pdf, ""), pdf)
    last_printed = max(p - OFFSET for p in body if any(l.strip() for l in body[p]))
    stats = {"pages_monotonic": all(entries[i]["printed_page"] <= entries[i + 1]["printed_page"]
                                    for i in range(len(entries) - 1))}
    # 1. spans: from the entry's page to the page before the next entry's page
    for i, e in enumerate(entries):
        nxt = entries[i + 1]["printed_page"] if i + 1 < len(entries) else last_printed + 1
        e["end_page"] = max(e["printed_page"], nxt - 1)
        e["boundary"] = []
        e["lines"] = [(pp, l) for pp in range(e["printed_page"], e["end_page"] + 1) for l in body.get(pp + OFFSET, [])]
    # 2. two entries starting on the same page: split after the first closing dateline
    for i in range(len(entries) - 1):
        a, b = entries[i], entries[i + 1]
        if a["printed_page"] != b["printed_page"]:
            continue
        p0 = a["printed_page"]
        page = [l for pp, l in a["lines"] if pp == p0]
        cut = split_shared_page(page)
        if cut is None:
            a["boundary"].append("shared_start_page_unsplit")
            b["boundary"].append("shared_start_page_unsplit")
            continue
        a["lines"] = [(p0, l) for l in page[:cut + 1]]
        b["lines"] = [(p0, l) for l in page[cut + 1:]] + [(pp, l) for pp, l in b["lines"] if pp != p0]
        a["boundary"].append("shared_start_page_split_at_dateline")
        b["boundary"].append("shared_start_page_split_at_dateline")
    # 3. a document whose last page has no closing line, and whose successor's first page does not
    #    begin like a document: its tail (up to the signature) sits at the top of that page
    for i in range(len(entries) - 1):
        a, b = entries[i], entries[i + 1]
        if a["printed_page"] == b["printed_page"]:
            continue
        last = next((l for _, l in reversed(a["lines"]) if l.strip()), "")
        p0 = b["printed_page"]
        first_page = [l for pp, l in b["lines"] if pp == p0]
        first = next((l for l in first_page if l.strip()), "")
        if is_closing(last) or is_opening(first):
            continue
        j = tail_end(first_page)
        if j is None:
            a["boundary"].append("no_closing_line_unsplit")
            b["boundary"].append("previous_document_may_continue_here")
            continue
        a["lines"] += [(p0, l) for l in first_page[:j + 1]]
        a["end_page"] = p0
        b["lines"] = [(p0, l) for l in first_page[j + 1:]] + [(pp, l) for pp, l in b["lines"] if pp != p0]
        a["boundary"].append("tail_on_next_documents_first_page")
        b["boundary"].append("starts_below_previous_documents_tail")
    for e in entries:
        e["boundary"] = "|".join(e["boundary"])
        e["unsplit"] = "unsplit" in e["boundary"] or "may_continue" in e["boundary"]
        lines = [l for _, l in e["lines"]]
        e["lines"] = lines
        e["pdf_pages"] = (e["printed_page"] + OFFSET, e["end_page"] + OFFSET)
        text = "\n".join(lines)
        found = body_dates(text)
        e["body_dates"] = found
        # date: contents month/day; the year from the contents, or (when damaged) the one the body confirms
        e["date"], e["date_source"] = "", ""
        if e["month"]:
            cands = ["%d-%02d-%02d" % (y, e["month"], e["day"]) for y in e["year_candidates"]]
            if len(cands) == 1:
                e["date"], e["date_source"] = cands[0], "contents"
            elif cands:
                ok = [c for c in cands if date_check(c, found) in CONFIRMED]
                if len(ok) == 1:
                    e["date"], e["date_source"] = ok[0], "contents_year_from_body"
                else:
                    e["date_source"] = "contents_year_unreadable"
            if e["contents_date_ocr_repaired"] and e["date_source"] == "contents":
                e["date_source"] = "contents_ocr_repaired"
        else:
            closing = [f for f in found if f["where"] in CONFIRMED and not f["date"].endswith("??")]
            if len({f["date"] for f in closing}) == 1:
                e["date"], e["date_source"] = closing[0]["date"], "body_only_no_contents_date"
        e["date_check"] = date_check(e["date"], found) if e["date"] else "no_date"
        if e["date_source"] == "body_only_no_contents_date":
            e["date_check"] = "body_only"
        e["signers"] = signers(lines, e["date"])
        e["by_direction_of_president"] = bool(BY_DIRECTION.search(text)) if e["category"] == "secretary_of_war_order" else False
        e["approved_by_president"] = bool(APPROVED.search(text)) if e["category"] == "secretary_of_war_order" else False
        e["white_house_line"] = bool(re.search(r"(?i)\S{0,3}h\S?te\s+\S{1,3}[o0][uv]\S{0,3}", text))
        e["needs_page_check"] = (e["date_check"] not in CONFIRMED) or e["unsplit"]
        e["confidence"] = "medium" if e["needs_page_check"] else "high"
    heads_numbered = {p: h["head_number"] for p, h in heads.items() if h["head_number"] is not None}
    stats["head_number_mismatches"] = sorted((p, n) for p, n in heads_numbered.items() if n != p - OFFSET)
    stats["head_numbers_read"] = len(heads_numbered)
    stats["heads_stripped"] = sum(1 for h in heads.values() if h["head"])
    stats["body_pages_with_text"] = sum(1 for p in body if any(l.strip() for l in body[p]) or heads[p]["head"])
    stats["gpo_footers"] = sorted(p for p, h in heads.items() if h["footer"])
    return entries, stats


# ---- census and crosswalk ---------------------------------------------------------------------------

def load_csv(path: pathlib.Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def census_state(c: dict | None, date: str) -> tuple[str, str]:
    de = (c or {}).get("date_effective", "").strip()
    if not c:
        return "NOT_IN_CENSUS", de
    if not de:
        return "census_date_blank", de
    if not date:
        return "volume_date_unread", de
    if len(de) == 4:
        return ("census_year_only" if de == date[:4] else "YEAR_CONFLICT"), de
    return ("census_exact_date" if de == date else "DATE_CONFLICT"), de


def file_id(iid: str) -> str:
    return iid.replace(":", "_").replace("½", "-half")


def slug(e: dict) -> str:
    return f"{e['date'] or 'undated'}_{e['category']}_seq{e['seq']:03d}"


def write_csv(path, rows, fields):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


STOP_WORDS = set("""the of and to in for on by as with from that this order orders amending amended amend relative relating
canal zone isthmian isthmus commission certain under which shall made other than into""".split())
DOC_REFERENCE = re.compile(r"(?i)^(?:order|orders|a\s+previous\s+order|former\s+ones)\b")
# In a body: "the Executive Order of June 24, 1904, ..., is hereby revoked"
BODY_REFERENCE = re.compile(
    r"(?is)\b(?:executive\s+)?order\s+(?:No\.\s*\d+\s+)?(?:of|dated)\s+(%s)\.?\s+(\d{1,2}),?\s*(19[01]\d)\b"
    r"((?:(?!\border\s+of\b).){0,200}?)\b(?:is|are|be)\s+(?:and\s+the\s+same\s+(?:is|are)\s+)?(?:hereby\s+)?"
    r"(amended|revoked|repealed|superseded|modified|rescinded)" % "|".join(MONTHS))


def content_words(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]{4,}", s.lower()) if w not in STOP_WORDS}


def by_subject(words: set[str], cands: list[dict], min_words: int = 2) -> tuple[dict | None, int]:
    """The one candidate whose contents subject shares at least min_words words, and at least half of its own
    words, with the reference, and more than any other candidate does; (None, number tied) otherwise."""
    scored = []
    for t in cands:
        tw = content_words(t["subject"])
        n = len(words & tw)
        if n >= min_words and tw and n / len(tw) >= 0.5:
            scored.append((n, t))
    scored.sort(key=lambda x: -x[0])
    if not scored:
        return None, 0
    if len(scored) == 1 or scored[0][0] > scored[1][0]:
        return scored[0][1], 1
    return None, sum(1 for n, _ in scored if n == scored[0][0])


def resolve_target(d: dict, refs: list[str], words: set[str], names_document: bool, docs: list[dict],
                   by_date: dict) -> tuple[list[dict], str]:
    """The document of this volume that an amend/revoke/... reference names, or why there is none.
    By the date it cites when it cites one (subject words break a tie between same-day documents);
    otherwise, for a reference to an 'order', by subject words alone. Never forced."""
    if refs:
        cands = [t for r in refs for t in by_date.get(r, []) if t["seq"] != d["seq"]]
        if not cands:
            return [], "referenced_date_not_in_volume"
        if len(cands) == 1:
            return cands, "date_unique_in_volume"
        best, _ = by_subject(words, cands, min_words=1)
        if best:
            return [best], "date_then_subject_words"
        return [], "ambiguous_%d_documents_of_that_date" % len(cands)
    if not names_document:
        return [], "target_is_rules_code_or_regulations_not_a_document_here"
    best, tied = by_subject(words, [t for t in docs if t["seq"] < d["seq"]])
    if best:
        return [best], "subject_words_only"
    return [], ("ambiguous_%d_documents_share_the_subject_words" % tied) if tied else "unresolved"


def affected_rows(docs: list[dict], ids_by_seq: dict) -> list[dict]:
    """Amend / revoke / repeal / supersede / modify leads: one row for the contents wording of each
    document, one for each dated reference in its body, and a flag for 'all orders in conflict
    herewith are revoked'."""
    by_date = {}
    for d in docs:
        if d["date"]:
            by_date.setdefault(d["date"], []).append(d)
    rows = []

    def row(d, source, action, refs, text, targets, status, conflict=False):
        rows.append({
            "seq": d["seq"], "date": d["date"], "category": d["category"],
            "instrument_ids": "|".join(ids_by_seq.get(d["seq"], [])), "source": source, "action": action,
            "revokes_conflicting_orders_clause": "yes" if conflict else "", "reference_text": norm_space(text)[:200],
            "referenced_dates": "|".join(refs), "target_resolution": status,
            "target_seq": "|".join(str(t["seq"]) for t in targets),
            "target_date": "|".join(t["date"] for t in targets),
            "target_ids": "|".join(i for t in targets for i in ids_by_seq.get(t["seq"], [])),
            "target_category": "|".join(t["category"] for t in targets),
            "target_subject": "|".join(t["subject"] for t in targets)})

    for d in docs:
        body = re.sub(r"-\n", "", "\n".join(d["lines"]))
        conflict = bool(CONFLICT_REVOKED.search(body))
        m = AFFECT_VERB.search(d["subject"])
        if m:
            phrase = d["subject"][m.end():].strip(" ,")
            refs = []
            for r in REF_DATE.finditer(phrase):
                mon = SHORT_NO.get(r.group(0)[:4].rstrip(".")) or SHORT_NO.get(r.group(0)[:3])
                refs.append("%s-%02d-%02d" % (r.group(2), mon, int(r.group(1))))
            targets, status = resolve_target(d, refs, content_words(REF_DATE.sub(" ", phrase)),
                                             bool(DOC_REFERENCE.match(phrase)), docs, by_date)
            row(d, "contents", m.group(1).lower(), refs, d["subject"], targets, status, conflict)
        elif conflict:
            row(d, "body_clause", "revokes_conflicting_orders", [], "all orders in conflict herewith are revoked", [], "", True)
        for b in BODY_REFERENCE.finditer(body):
            ref = "%s-%02d-%02d" % (b.group(3), MONTH_NO[b.group(1)], int(b.group(2)))
            targets, status = resolve_target(d, [ref], content_words(b.group(4)), True, docs, by_date)
            row(d, "body", b.group(5).lower(), [ref], b.group(0), targets, status)
    return rows


def run(repo_root, job_dir, out_dir):
    repo, job_dir, out = pathlib.Path(repo_root), pathlib.Path(job_dir), pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    prov = json.loads((job_dir / "data" / "PROVENANCE.json").read_text(encoding="utf-8"))
    vol = prov["volume"]
    text_path = job_dir / vol["text"]
    text_sha = sha256_bytes(text_path.read_bytes())
    if text_sha != vol["text_sha256"]:
        raise SystemExit(f"{vol['text']}: sha256 {text_sha} does not match PROVENANCE.json")
    for key in ("crosswalk", "wpa_not_in_volume"):
        p = job_dir / vol[key]
        if sha256_bytes(p.read_bytes()) != vol[key + "_sha256"]:
            raise SystemExit(f"{vol[key]}: sha256 does not match PROVENANCE.json")
    pdf = repo / vol["pdf"]
    if not pdf.exists():
        pdf_check = "pdf_not_checked_out"
    else:
        with open(pdf, "rb") as fh:
            start = fh.read(64)
        if start.startswith(b"version https://git-lfs"):
            pdf_check = "pdf_is_lfs_pointer_text_layer_hash_verified"
        else:
            pdf_check = "match" if sha256_bytes(pdf.read_bytes()) == vol["pdf_sha256"] else "MISMATCH"
            if pdf_check == "MISMATCH":
                raise SystemExit(f"{vol['pdf']}: sha256 does not match PROVENANCE.json")

    census = {r["id"].upper(): r for r in load_csv(repo / prov["census"])}
    rp = repo / prov["readiness"]
    readiness = {r["instrument_id"].upper(): r for r in load_csv(rp)} if rp.exists() else {}
    crosswalk = load_csv(job_dir / vol["crosswalk"])
    not_in_volume = load_csv(job_dir / vol["wpa_not_in_volume"])

    docs, stats = build_documents(load_pages(text_path))
    by_seq = {d["seq"]: d for d in docs}
    ids_by_seq, lord_by_seq, xw_by_id = {}, {}, {}
    for x in crosswalk:
        s = int(x["seq"])
        if x["instrument_id"]:
            ids_by_seq.setdefault(s, []).append(x["instrument_id"])
            xw_by_id[x["instrument_id"]] = x
        if x["lord_seq"]:
            lord_by_seq[s] = x

    texts = out / "texts"
    texts.mkdir(parents=True, exist_ok=True)
    doc_rows, order_rows, fragments, leads, match_rows = [], [], [], [], []
    short = vol["short"]
    for d in docs:
        body_text = "\n".join(d["lines"]).strip() + "\n"
        body_sha = sha256_bytes(body_text.encode("utf-8"))
        ids = ids_by_seq.get(d["seq"], [])
        lord = lord_by_seq.get(d["seq"])
        names = [f"texts/{file_id(i)}.txt" for i in ids] or \
                ([f"texts/LORD_{lord['lord_seq']}.txt"] if lord else [f"texts/{slug(d)}.txt"])
        pp = "PDF pages %d-%d" % d["pdf_pages"]
        printed = "printed pages %d-%d" % (d["printed_page"], d["end_page"])
        evidence = f"{short}, {printed}, {pp}"
        identity = ("EO number from the committed crosswalk (the volume prints none): " + ", ".join(ids)) if ids else \
                   (f"not numbered; matched by hand to Lord 1943 unnumbered list seq {lord['lord_seq']}" if lord else "not numbered")
        file_hashes = {}
        for iid, fname in zip(ids or [""] * len(names), names):
            title = f"{iid}: " if iid else (f"LORD:{lord['lord_seq']}: " if lord else "")
            header = (f"# {title}{d['contents_text']} (contents entry {d['seq']})\n"
                      f"# Source: {vol['title']} ({vol['published']}); {vol['digitized_by']}\n"
                      f"# PDF: {vol['pdf']} sha256 {vol['pdf_sha256']}\n"
                      f"# {pp}; {printed}; date {d['date'] or 'unread'} ({d['date_source']}); body date check {d['date_check']}; "
                      f"confidence {d['confidence']}\n"
                      f"# Identity: {identity}"
                      + (". This printed entry holds both orders; the text is the whole entry" if len(ids) > 1 else "") + "\n"
                      f"# Text: OCR text layer of the scan ({vol['extractor']}), running heads and GPO footers removed. "
                      f"Not human-verified. Body sha256 {body_sha}\n\n")
            (out / fname).write_text(header + body_text, encoding="utf-8", newline="\n")
            file_hashes[fname] = sha256_bytes((out / fname).read_bytes())
        doc_rows.append({
            "seq": d["seq"], "category": d["category"], "kind": d["kind"], "date": d["date"], "date_source": d["date_source"],
            "contents_date_raw": d["contents_date_raw"], "date_check": d["date_check"],
            "body_closing_dates": "|".join(sorted({f["date"] for f in d["body_dates"] if f["where"] != "mention"})),
            "printed_pages": "%d-%d" % (d["printed_page"], d["end_page"]), "pdf_pages": "%d-%d" % d["pdf_pages"],
            "pages": d["end_page"] - d["printed_page"] + 1, "boundary": d["boundary"],
            "signers": "|".join(d["signers"]), "white_house_line": "yes" if d["white_house_line"] else "",
            "by_direction_of_president": "yes" if d["by_direction_of_president"] else "",
            "approved_by_president": "yes" if d["approved_by_president"] else "",
            "instrument_ids": "|".join(ids), "lord_seq": lord["lord_seq"] if lord else "",
            "needs_page_check": "yes" if d["needs_page_check"] else "", "confidence": d["confidence"],
            "subject": d["subject"], "contents_text": d["contents_text"], "text_path": "|".join(names),
            "text_sha256": file_hashes[names[0]] if len(names) == 1 else "",
            "body_sha256": body_sha, "chars": len(body_text)})
        d["_names"], d["_sha"], d["_evidence"] = names, body_sha, evidence

        if d["category"] in PRESIDENTIAL:
            for iid, fname in zip(ids or [""], names):
                c = census.get(iid.upper()) if iid else None
                state, de = census_state(c, d["date"]) if iid else ("NOT_IN_CENSUS", "")
                rd = readiness.get(iid.upper(), {}) if iid else {}
                order_rows.append({
                    "instrument_id": iid, "lord_seq": lord["lord_seq"] if lord else "", "seq": d["seq"],
                    "category": d["category"], "date": d["date"], "date_check": d["date_check"],
                    "subject": d["subject"], "pdf_pages": "%d-%d" % d["pdf_pages"],
                    "printed_pages": "%d-%d" % (d["printed_page"], d["end_page"]), "signers": "|".join(d["signers"]),
                    "confidence": d["confidence"], "census": state, "census_date_effective": de,
                    "provisional_status": rd.get("provisional_status", ""),
                    "original_text_step_before": rd.get("step_original_text", ""), "blockers_before": rd.get("blockers", ""),
                    "text_path": fname, "text_sha256": file_hashes[fname], "body_sha256": body_sha, "chars": len(body_text)})
                if c:
                    fragments.append({
                        "instrument_id": iid, "kind": "original_representation", "produced_by": JOB_NAME,
                        "confidence_note": (f"Machine location lead, confidence {d['confidence']}. "
                                            + ("Contents date confirmed by the body's closing dateline; "
                                               if d["date_check"] in CONFIRMED else "Contents date NOT confirmed by a closing dateline in the body; ")
                                            + "official compilation printed by the Government Printing Office for the Isthmian Canal Commission (1911), "
                                              "University of Florida copy via HathiTrust; text is the scan's OCR layer. The volume prints no EO "
                                              "numbers: the identification rests on a hand-reviewed same-date and subject match to the WPA "
                                              "numbered list. Identity, boundaries and wording are NOT human-verified; this is not a legal conclusion."),
                        "data": {"url": vol["handle_url"], "sha256": vol["pdf_sha256"], "page_or_item": evidence,
                                 "route": ROUTE, "location_confidence": d["confidence"], "location_verified": False,
                                 "needs_page_check": d["needs_page_check"], "signing_date": d["date"], "title": d["subject"],
                                 "text_path": fname, "text_sha256": file_hashes[fname], "body_sha256": body_sha,
                                 "source_id": f"{JOB_NAME}:{iid}:{vol['pdf_sha256'][:12]}"},
                        "sources": [{"url": vol["handle_url"], "sha256": vol["pdf_sha256"], "page_or_item": evidence}]})
                if iid and state in ("NOT_IN_CENSUS", "census_date_blank", "YEAR_CONFLICT", "DATE_CONFLICT"):
                    leads.append({"lead": state, "instrument_id": iid, "seq": d["seq"], "date_in_volume": d["date"],
                                  "census_date_effective": de, "evidence": evidence, "text_path": fname,
                                  "note": "date confirmed by closing dateline" if d["date_check"] in CONFIRMED else "date needs page check"})
                if not iid:
                    leads.append({"lead": "NOT_IN_CENSUS", "instrument_id": "", "lord_seq": lord["lord_seq"] if lord else "",
                                  "seq": d["seq"], "date_in_volume": d["date"], "evidence": evidence, "text_path": fname,
                                  "note": f"unnumbered {d['category'].replace('_', ' ')}: {d['subject']}. "
                                          + ("A proclamation, not an executive order; listed so the census owner can decide scope. "
                                             if d["category"] == "proclamation" else "")
                                          + f"The census holds {sum(1 for k in census if k.startswith('EO:UN'))} undated, "
                                          "untitled EO:UN/EO:UNN ids that could not be compared"})
        # WPA / Lord match table: every presidential document and every Secretary of War order 'by direction'
        if d["category"] in PRESIDENTIAL or d["by_direction_of_president"] or lord:
            for iid in ids or [""]:
                x = xw_by_id.get(iid) or lord or {}
                wd = x.get("wpa_date", "")
                agrees = ""
                if iid:
                    agrees = "yes" if wd == d["date"] else ("wpa_partial_year_agrees" if len(wd) == 4 and d["date"].startswith(wd) else "NO")
                match_rows.append({
                    "seq": d["seq"], "category": d["category"], "date": d["date"],
                    "match": "numbered_eo" if iid else ("lord_unnumbered" if lord else "unmatched"),
                    "instrument_id": iid, "lord_seq": lord["lord_seq"] if lord else "",
                    "wpa_date": wd, "wpa_date_agrees_with_volume": agrees, "wpa_citations": x.get("wpa_citations", ""),
                    "list_text": x.get("wpa_text", "") or x.get("lord_summary", ""),
                    "lord_date": lord.get("lord_date", "") if lord else "", "basis": x.get("basis", ""),
                    "subject": d["subject"]})
        if lord:
            leads.append({"lead": "LORD_UNNUMBERED_MATCH", "instrument_id": "", "lord_seq": lord["lord_seq"], "seq": d["seq"],
                          "date_in_volume": d["date"], "evidence": evidence, "text_path": names[0],
                          "note": f"{d['category'].replace('_', ' ')}; Lord {lord['lord_date'] or 'undated'} "
                                  f"({lord['lord_pairing']}): {lord['lord_summary'][:120]}"})
        if d["by_direction_of_president"]:
            leads.append({"lead": "SECWAR_ORDER_BY_DIRECTION_OF_PRESIDENT_CANDIDATE", "instrument_id": "",
                          "lord_seq": lord["lord_seq"] if lord else "", "seq": d["seq"], "date_in_volume": d["date"],
                          "evidence": evidence, "text_path": names[0],
                          "note": "Secretary of War order issued 'by direction of the President' (Lord counts one such order as an "
                                  "unnumbered EO). Candidate only: " + d["subject"][:120]})
    for r in not_in_volume:
        iid = r["instrument_id"]
        c = census.get(iid.upper())
        leads.append({"lead": "IN_LIST_NOT_IN_VOLUME", "instrument_id": iid, "seq": "", "date_in_volume": "",
                      "census_date_effective": (c or {}).get("date_effective", ""),
                      "evidence": f"WPA numbered list: {r['wpa_date'] or r['wpa_year']} {r['wpa_citations']}".strip(),
                      "text_path": "", "in_census": "yes" if c else "no",
                      "note": "canal-related order in the WPA list within the volume's dates that the volume does not print: "
                              + r["wpa_text"][:140]})
    for r in leads:
        if "in_census" not in r:
            r["in_census"] = "yes" if r["instrument_id"] and r["instrument_id"].upper() in census else ("no" if r["instrument_id"] else "")

    affected = affected_rows(docs, ids_by_seq)
    for r in affected:
        tids = [t for t in r["target_ids"].split("|") if t]
        r["target_provisional_status"] = "|".join(readiness.get(t.upper(), {}).get("provisional_status", "") for t in tids)

    write_csv(out / "IC1911_DOCUMENTS.csv", doc_rows, list(doc_rows[0].keys()))
    write_csv(out / "IC1911_ORDERS.csv", order_rows, list(order_rows[0].keys()))
    write_csv(out / "IC1911_WPA_LORD_MATCH.csv", match_rows, list(match_rows[0].keys()))
    write_csv(out / "IC1911_AFFECTED_DOCUMENTS.csv", affected,
              ["seq", "date", "category", "instrument_ids", "source", "action", "revokes_conflicting_orders_clause",
               "reference_text", "referenced_dates", "target_resolution", "target_seq", "target_date", "target_ids",
               "target_category", "target_subject", "target_provisional_status"])
    write_csv(out / "CENSUS_LEADS.csv", leads, ["lead", "instrument_id", "lord_seq", "seq", "date_in_volume",
                                                "census_date_effective", "in_census", "evidence", "text_path", "note"])
    with open(out / "FRAGMENTS.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for f in fragments:
            fh.write(json.dumps(f, ensure_ascii=False, sort_keys=True) + "\n")

    count = lambda rows, k: {v: sum(1 for r in rows if r[k] == v) for v in sorted({r[k] for r in rows})}
    pres = [d for d in docs if d["category"] == "presidential_order"]
    numbered = [r for r in order_rows if r["instrument_id"]]
    decided = [r for r in numbered if r["provisional_status"]]
    inversions = [(docs[i]["seq"], docs[i + 1]["seq"]) for i in range(len(docs) - 1)
                  if docs[i]["date"] and docs[i + 1]["date"] and docs[i + 1]["date"] < docs[i]["date"]]
    summary = {
        "leads_only": "Nothing is admitted, merged, dated or changed in the census or in any status.",
        "volume": vol["title"], "pdf_check": pdf_check, "text_sha256": text_sha,
        "census": prov["census"], "census_sha256": sha256_bytes((repo / prov["census"]).read_bytes()),
        "readiness_read": rp.exists(),
        "contents_entries": len(docs), "categories": count(docs, "category"),
        "page_offset": OFFSET, "head_numbers_read": stats["head_numbers_read"],
        "head_number_mismatches_pdf_page_and_number": stats["head_number_mismatches"],
        "running_heads_stripped": stats["heads_stripped"], "gpo_footers_stripped": len(stats["gpo_footers"]),
        "contents_pages_monotonic": stats["pages_monotonic"],
        "span_pages": {str(n): sum(1 for d in docs if d["end_page"] - d["printed_page"] + 1 == n)
                       for n in sorted({d["end_page"] - d["printed_page"] + 1 for d in docs})},
        "boundaries": {k: [d["seq"] for d in docs if d["boundary"] == k] for k in sorted({d["boundary"] for d in docs if d["boundary"]})},
        "contents_date_ocr_repaired": [d["seq"] for d in docs if d["contents_date_ocr_repaired"]],
        "date_source": count(docs, "date_source"),
        "date_order_inversions_seq_pairs": inversions,
        "presidential_order_date_check": count(pres, "date_check"),
        "presidential_order_dates_confirmed": sum(1 for d in pres if d["date_check"] in CONFIRMED),
        "presidential_orders_needs_page_check": [d["seq"] for d in pres if d["needs_page_check"]],
        "all_documents_date_check": count(docs, "date_check"),
        "secretary_of_war_orders": {
            "by_direction_of_president": sum(1 for d in docs if d["by_direction_of_president"]),
            "approved_by_president_only": sum(1 for d in docs if d["approved_by_president"] and not d["by_direction_of_president"]),
            "secretary_only": sum(1 for d in docs if d["category"] == "secretary_of_war_order"
                                  and not d["by_direction_of_president"] and not d["approved_by_president"])},
        "crosswalk_eo_ids": len(xw_by_id), "crosswalk_seqs": len(ids_by_seq),
        "presidential_orders_without_eo_id": [d["seq"] for d in pres if d["seq"] not in ids_by_seq],
        "lord_matches": {str(s): x["lord_seq"] for s, x in sorted(lord_by_seq.items())},
        "wpa_date_check": count([r for r in match_rows if r["instrument_id"]], "wpa_date_agrees_with_volume"),
        "census_state_of_eo_ids": count(numbered, "census"),
        "readiness_provisional_status": {k or "blank": v for k, v in count(numbered, "provisional_status").items()},
        "original_text_step_before": count(numbered, "original_text_step_before"),
        "decided_orders_original_text_step_open": [r["instrument_id"] for r in decided if r["original_text_step_before"] != "done"],
        "fragments": len(fragments), "texts_written": sum(len(d["_names"]) for d in docs),
        "census_leads": count(leads, "lead"),
        "affected_document_leads": len(affected),
        "affected_targets_resolved": sum(1 for r in affected if r["target_seq"]),
        "census_unnumbered_ids_not_comparable": sum(1 for k in census if k.startswith("EO:UN")),
    }
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary
