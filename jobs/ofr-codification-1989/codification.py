"""Read the Office of the Federal Register's 1989 Codification of Presidential Proclamations and Executive Orders.

The book (April 13, 1945 - January 20, 1989) prints the text of every proclamation and Executive order that
still had general effect on January 20, 1989, AS AMENDED to that day, and ends with disposition tables that
give the status on that day of every order of 1945-1989 and of earlier orders those orders affected.

The job reads two committed files, never the network:
- data/codification_1989_pages.jsonl: the PDF's text layer (Google OCR), one line per PDF page;
- data/codification_1989_eo_table_chunks.jsonl: the positioned OCR chunks of the Executive Orders
  disposition table (PDF pages 1032-1103), because the plain text layer scrambles that table's columns.

The codified texts are editorial, as-amended texts, NOT the original orders, so this job never emits
original_representation fragments. It is a status-lead job: what was codified (in force) on 20 Jan 1989,
what was revoked or superseded by then and by which document, exact dates from the SOURCE lines, and
how all that compares with the census and the project's provisional statuses.

Machine leads only: nothing here admits, merges, dates or changes a census identity or a status.
"""

import bisect
import collections
import csv
import hashlib
import json
import pathlib
import re
import statistics

JOB = "ofr-codification-1989"
SNAPSHOT = "1989-01-20"
MON = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7, "aug": 8,
       "sept": 9, "sep": 9, "oct": 10, "nov": 11, "dec": 12, "january": 1, "february": 2, "march": 3, "april": 4,
       "august": 8, "september": 9, "october": 10, "november": 11, "december": 12}

# ------------------------------------------------------------------ body: SOURCE lines and documents
# All body regexes run on whitespace-squashed text: 153 pages come out of pypdf a few words per line.
SOURCE_RE = re.compile(r"SOURCE:?Theprovisionsof(ExecutiveOrder|Proclamation)(\d{1,5}(?:-?[A-Z](?![a-z]))?)"
                       r"(?:of([A-Z][a-z]{2,8})\.?(\d{1,2}),(1[789]\d\d))?")
HEAD_RE = re.compile(r"(ExecutiveOrder|Proclamation)(\d{1,5}(?:-?[A-Z](?![a-z]))?)[-—–]")
CHAPTER_RE = re.compile(r"(?<!SUB)CHAPTER(\d{1,2})[-—–]")
SUBCHAPTER_RE = re.compile(r"SUBCHAPTER([A-Z])[-—–]")
FR_RE = re.compile(r"(\d{1,2})FR(\d{1,6})")
CFR_RE = re.compile(r"3CFR,?(\d{4}(?:[-–—]\d{4})?)Comp\.?,?p\.?(\d{1,4})")
NOT_IN_FR_RE = re.compile(r"do(?:es)?notappearintheFederalRegister(?:system)?")
RESTATED_RE = re.compile(r"(?:were|was)((?:revised|amended)?(?:and)?restated)intheirentiretyby(ExecutiveOrder|Proclamation)"
                         r"(\d{1,5}[A-Z]?)(?:of([A-Z][a-z]{2,8})\.?(\d{1,2}),(1[789]\d\d))?")
DATED_REF_RE = re.compile(r"(?:EO|ExecutiveOrder(?:No\.?)?)(\d{3,5})of([A-Z][a-z]{2,8})\.?(\d{1,2}),(1[789]\d\d)")
# Bracketed editorial notes inside a codified text that record a change ("[Sec. 2 amended by EO 11000 ...]").
AMEND_NOTE_RE = re.compile(r"\[[^\]]{0,400}?\b(amended|added|revoked|redesignated|superseded|revised|deleted|removed|renumbered)",
                           re.I | re.S)
# Running heads: verso "Codification of Presidential Proclamations and Executive Orders"; recto "Chapter 5- Federal ...".
RUNNING_HEAD = re.compile(r"^\s*(Codification\s*of\s*Presidential\s*Proclamations\s*and\s*Executive\s*Orders\s*$"
                          r"|Chapter\s*\d{1,2}\s*[-—–])")
PAGE_NO = re.compile(r"^\D{0,14}?(\d{1,4})\D{0,14}$")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def squash(s: str) -> str:
    return re.sub(r"\s+", "", s)


def clean(s: str) -> str:
    s = re.sub(r"\s+", " ", s or "").strip()
    return re.sub(r"\s+([,.;:)])", r"\1", s)


def iso(mon: str | None, day, year) -> str:
    m = MON.get((mon or "").lower().rstrip("."))
    if not m or not day or not year:
        return ""
    try:
        d, y = int(day), int(year)
    except ValueError:
        return ""
    return "%04d-%02d-%02d" % (y, m, d) if 1 <= d <= 31 else ""


def doc_id(kind: str, number: str) -> str:
    n = number.replace("-", "")
    m = re.fullmatch(r"(\d+)([A-Za-z]?)", n)
    if m:
        n = str(int(m.group(1))) + m.group(2).upper()
    return ("EO:" if kind.startswith("Exec") else "Proc:") + n


def load_pages(path):
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            out.append((int(d["page"]), d["text"]))
    return out


def is_fragmented(lines) -> bool:
    """pypdf breaks some pages into a few words per line."""
    ls = [l for l in lines if l.strip()]
    return len(ls) >= 10 and sum(1 for l in ls if len(l.split()) <= 2) / len(ls) > 0.35


def body_stream(pages, first: int, last: int, offset: int):
    """Body lines without running heads and printed page numbers: [(pdf_page, printed_page, line)] plus page stats."""
    stream, stats = [], {"pages": 0, "printed_read": 0, "printed_inferred": 0, "empty": 0, "fragmented": [],
                         "recto_titles": collections.defaultdict(collections.Counter)}
    for pno, text in pages:
        if not first <= pno <= last:
            continue
        stats["pages"] += 1
        lines = [l.rstrip() for l in text.split("\n")]
        while lines and not lines[-1].strip():
            lines.pop()
        if not [l for l in lines if l.strip()]:
            stats["empty"] += 1
            continue
        printed = str(pno - offset)
        m = PAGE_NO.match(lines[-1].strip())
        if m and int(m.group(1)) == pno - offset:
            lines.pop()
            stats["printed_read"] += 1
        else:
            stats["printed_inferred"] += 1
        while lines and not lines[0].strip():
            lines.pop(0)
        if lines and RUNNING_HEAD.match(lines[0]):
            rh = re.match(r"^\s*Chapter\s*(\d{1,2})\s*[-—–]\s*(.+?)\s*$", lines[0])
            if rh:
                stats["recto_titles"][rh.group(1)][clean(rh.group(2))] += 1
            lines.pop(0)
        if is_fragmented(lines):
            stats["fragmented"].append(pno)
        for l in lines:
            stream.append((pno, printed, l))
    return stream, stats


def parse_source_rest(rest: str) -> dict:
    """Facts in the squashed text that follows 'SOURCE: The provisions of Executive Order N of <date>'."""
    end = rest.find("unlessotherwisenoted")
    rest = rest[:end] if 0 <= end < 600 else rest[:400]
    fr = FR_RE.search(rest)
    cfr = CFR_RE.search(rest)
    rs = RESTATED_RE.search(rest)
    out = {"fr_citation": f"{fr.group(1)} FR {fr.group(2)}" if fr else "",
           "cfr_compilation": f"3 CFR, {cfr.group(1)} Comp., p. {cfr.group(2)}" if cfr else "",
           "not_in_fr_system": "yes" if NOT_IN_FR_RE.search(rest) else "",
           "restated": "", "restated_by": "", "restated_by_date": "", "codified_text_fr": ""}
    if rs:
        out["restated"] = {"revisedandrestated": "revised and restated", "amendedandrestated": "amended and restated"
                           }.get(rs.group(1), rs.group(1))
        out["restated_by"] = doc_id(rs.group(2), rs.group(3))
        out["restated_by_date"] = iso(rs.group(4), rs.group(5), rs.group(6))
        later = FR_RE.search(rest, rs.end())
        out["codified_text_fr"] = f"{later.group(1)} FR {later.group(2)}" if later else ""
    return out


def find_documents(stream, recto_titles=None):
    """Every codified document, anchored on its SOURCE line. The document starts at its heading
    ('Executive Order 10860 -Coat of arms ...') when one is found shortly before the SOURCE line, and ends at
    the next document or chapter heading (the book has no closing tag)."""
    parts = [squash(l) for _, _, l in stream]
    starts, pos = [], 0
    for p in parts:
        starts.append(pos)
        pos += len(p)
    sq = "".join(parts)

    def line_of(off):
        return max(0, bisect.bisect_right(starts, off) - 1)

    heads = list(HEAD_RE.finditer(sq))
    head_starts = [h.start() for h in heads]
    chapters = [(m.start(), "chapter", m.group(1)) for m in CHAPTER_RE.finditer(sq)]
    chapters += [(m.start(), "subchapter", m.group(1)) for m in SUBCHAPTER_RE.finditer(sq)]
    chapters.sort()
    sources = list(SOURCE_RE.finditer(sq))
    docs = []
    for k, s in enumerate(sources):
        iid = doc_id(s.group(1), s.group(2))
        prev_src = sources[k - 1].end() if k else 0
        start, heading_found = s.start(), False
        i = bisect.bisect_left(head_starts, s.start()) - 1
        while i >= 0 and heads[i].start() >= prev_src and s.start() - heads[i].start() <= 1500:
            h = heads[i]
            if doc_id(h.group(1), h.group(2)) == iid:
                start, heading_found = h.start(), True
                break
            i -= 1
        facts = parse_source_rest(sq[s.end():s.end() + 700])
        docs.append({"instrument_id": iid, "kind": "EO" if iid.startswith("EO:") else "Proc",
                     "date": iso(s.group(3), s.group(4), s.group(5)), "start": start, "source_at": s.start(),
                     "heading_found": heading_found, **facts})
    docs.sort(key=lambda d: d["start"])
    cuts = sorted([d["start"] for d in docs] + [c[0] for c in chapters])
    chapter_titles = {}
    for off, level, num in chapters:
        line = stream[line_of(off)][2]
        m = re.search(r"(?:SUB)?CHAPTER\s*%s\s*[-—–]+\s*(.*)$" % re.escape(num), line)
        title = clean(m.group(1)) if m else ""
        chapter_titles.setdefault((level, num), title)
    for d in docs:
        j = bisect.bisect_right(cuts, d["source_at"])
        end = cuts[j] if j < len(cuts) else len(sq)
        first_line, end_line = line_of(d["start"]), line_of(end) if end < len(sq) else len(stream)
        if end_line <= first_line:
            end_line = first_line + 1
        span = stream[first_line:end_line]
        chap = [c for c in chapters if c[0] <= d["start"]]
        ch = next((c for c in reversed(chap) if c[1] == "chapter"), None)
        sub = next((c for c in reversed(chap) if c[1] == "subchapter" and (not ch or c[0] > ch[0])), None)
        src_line = line_of(d["source_at"])
        title_lines = [l for _, _, l in stream[first_line:src_line]] if d["heading_found"] else []
        title = clean(" ".join(title_lines))
        title = re.sub(r"^.*?(?:Executive\s*Order|Proclamation)\s*\d{1,5}(?:\s*-?\s*[A-Z](?![a-z]))?\s*[-—–]+\s*", "", title, count=1)
        src_text = clean(" ".join(l for _, _, l in stream[src_line:src_line + 25]))
        src_text = src_text[src_text.find("SOURCE"):] if "SOURCE" in src_text else src_text
        cut = (re.search(r"otherwise\s*noted\s*\.", src_text)
               or re.search(r"Federal\s*Register(?:\s*system)?\s*\.", src_text))
        src_text = src_text[:cut.end()] if cut else src_text[:300]
        d.update({
            "lines": span, "pdf_pages": (span[0][0], span[-1][0]), "printed_pages": (span[0][1], span[-1][1]),
            "chapter": ch[2] if ch else "",
            "chapter_title": ((recto_titles or {}).get(ch[2]) or collections.Counter({chapter_titles.get(("chapter", ch[2]), ""): 1})
                              ).most_common(1)[0][0] if ch else "",
            "subchapter": sub[2] if sub else "",
            "subchapter_title": chapter_titles.get(("subchapter", sub[2]), "") if sub else "",
            "heading_title": title[:300], "source_text": src_text,
            "heading_mid_line": d["heading_found"] and squash(stream[first_line][2])[:12] != sq[d["start"]:d["start"] + 12],
        })
    return docs, {"headings": len(heads), "chapter_headings": sum(1 for c in chapters if c[1] == "chapter"),
                  "subchapter_headings": sum(1 for c in chapters if c[1] == "subchapter")}


def document_text(lines, fragmented_pages) -> str:
    """The document's lines; pages that pypdf fragmented into a few words per line are joined into paragraphs."""
    out, buf, buf_page = [], [], None
    for pno, _, l in lines:
        if pno in fragmented_pages:
            if buf_page not in (None, pno):
                out.append(" ".join(buf))
                buf = []
            buf.append(l.strip())
            buf_page = pno
            continue
        if buf:
            out.append(" ".join(buf))
            buf, buf_page = [], None
        out.append(l)
    if buf:
        out.append(" ".join(buf))
    return re.sub(r"[ \t]+", " ", "\n".join(out)).strip() + "\n"


def dated_references(stream):
    """'EO 6585 of Feb. 6, 1934' and 'Executive Order No. 9397 of Nov. 22, 1943' anywhere in the body."""
    refs, where = collections.defaultdict(collections.Counter), {}
    page_text = collections.defaultdict(list)
    for pno, _, l in stream:
        page_text[pno].append(l)
    for pno in sorted(page_text):
        sq = squash(" ".join(page_text[pno]))
        for m in DATED_REF_RE.finditer(sq):
            d = iso(m.group(2), m.group(3), m.group(4))
            if not d:
                continue
            iid = "EO:" + str(int(m.group(1)))
            refs[iid][d] += 1
            where.setdefault((iid, d), pno)
    return refs, where


# ------------------------------------------------------------------ disposition table (positioned chunks)
MONTHS = r"(Jan|Feb|Mar|Apr|May|June|July|Aug|Sept|Oct|Nov|Dec)"
NUM_RE = re.compile(r"^\s*(\d{1,5})(?:(-\d{1,2})(?=[\s.…]|$)|\s?-?\s?([A-Z])(?![a-zA-Z])|\s*(½))?")
DATE_FULL = re.compile(r"^\s*%s\s*\.?\s*(\d{1,2})\s*,\s*(1[789]\d\d)" % MONTHS)
DATE_MD = re.compile(r"^\s*%s\s*\.?\s*(\d{1,2})?\s*[.…]*\s*$" % MONTHS)
YEAR_PART = re.compile(r"^\s*(\d{1,2})?\s*,\s*(1[789]\d\d)\s*[.…]*\s*$")
SWALLOWED_DATE = re.compile(r"%s\s*\.?\s*(\d{1,2})\s*$" % MONTHS)
LEADERS = re.compile(r"^[\s.…,]*")
# Disposition phrases (OCR glues words: 'Revokedby', 'Supersedebdy', 'Codifiedat', 'Publiclands').
# Passive 'Amended by', 'Modified by', past-tense 'Amended EO' (italic list of what a dead order had affected)
# and 'Revoked in part by' belong to the Amendments column and are NOT here.
DISP_KW = re.compile(
    r"(?:(?<![a-z])[A-Z][a-z]{3,}\s*terminated\s*by|Revoked\s*by|Supersede\s*d\s*by|Supersedebdy|Codified|Public\s*lands|Temporary|Hortatory|Executed\s*and|"
    r"Obsolete|Tariff|Selective\s*Service|Authority|Nullified|Terminated\s*by|Expired|Eliminated|Replaced\s*by|"
    r"See\s*note|Amends|Revokes|Supersedes|Modifies|Extends|Continues|Supplements|Implements|Terminates|"
    r"Nullifies|Discontinues|Abolishes|Abolished|Repealed)")
AMEND_KW = re.compile(r"^\s*(?:Amended|Ratified|Modified|Extended|Continued|Clarified|Supplemented|Revoked\s*in\s*part|"
                      r"Superseded\s*in\s*part|Revoked\s*EO|Superseded\s*EO|Suspended|Corrected|Implemented|Interpreted)")
NO_ARG_DISP = re.compile(r"^(Temporary|Hortatory|Tariff|Public\s*lands|Executed\s*and\s*obsolete|Selective\s*Service|Obsolete)"
                         r"[\s.…]*(\d{1,5}[A-Z]?)\s*$")
LEADER_NUMBER = re.compile(r"^(.*?)(?:\s*[.…]{2,}|(?:^|\s)[.…])\s*(\d{3,5}[A-Z]?)\s*\.?\s*$")
# A capitalised word after a list of numbers inside an Amendments chunk starts a free-text disposition.
FREE_TEXT_START = re.compile(r"(?<=[\d.,;]\s)([A-Z][a-z]{3,})")
RUNNING_HEADS = re.compile(r"^\s*(Codification\s*of\s*Presidential\s*Proclamations\s*and\s*Executive\s*Orders|"
                           r"Executive\s*Orders|Proclamations|Index)\s*$")
# '. EO 12220' in the amendments column: a full stop, then a bare document reference with no verb of its own.
WRAPPED_DISP_REF = re.compile(r"^[.]\s*((?:EOS?s?|Procs?)\s*\.?\s*\d{1,5}(?:\s*,\s*\d{1,5})*)\s*$")
# EO numbers in the 9538-12667 run that the book's table does not print at all (checked against the page images
# on 2026-10-17: the rows either side are contiguous on the printed page). Number -> PDF page.
NOT_PRINTED_IN_TABLE = {10217: 1063, 10275: 1064, 10288: 1064, 10595: 1069}
TRAILING_NUMBER = re.compile(r"^(.*(?:EOS?s?|Procs?)\s*\.?\s*(?:\d{1,5}\s*,\s*)*)(\d{5,10})\s*$")
# Two rows in one OCR piece: '2768......... Revokedby EO 34612786 Revokedby EO 3461'. The text before a second status
# phrase ends in the first row's acting number with the next row's number glued on (or after a space).
MERGED_HEAD = re.compile(r"^(?P<pre>.*(?:EOS?s?|Procs?)\s*\.?\s*(?:\d{1,5}\s*,\s*)*)(?P<digits>\d{4,10})"
                         r"(?:\s+(?P<next>\d{3,5}[A-Z]?))?[\s.…]*$")
MERGED_NOARG_HEAD = re.compile(r"^(?P<pre>(?:Temporary|Hortatory|Tariff|Public\s*lands|Executed\s*and\s*obsolete|Obsolete)"
                               r"[\s.…]*?)\s*(?P<next>\d{3,5}[A-Z]?)[\s.…]*$")
# A lone 1-2 digit OCR piece in the disposition column that is not next to any other text on its line
# ('1' on PDF 1045 and 1089: the page images print nothing there). About 3.2 pt per character.
STRAY_DIGITS = re.compile(r"^\s*\d{1,2}\s*$")
STRAY_GAP = 20.0
CHAR_W = 3.2
# Ending verbs inside a disposition, for the mechanism of each acting document named after them
# ('Superseded by EO 11640. Revoked by EO 11788': 11640 supersession, 11788 revocation).
ENDING_VERB = re.compile(r"Revoked\s*by|Supersede\s*d\s*by|Supersedebdy|Supersededy|Nullified\s*by|[Tt]erminated\s*by|"
                         r"Replaced\s*by|Eliminated\s*by")


def first_disp_kw(t: str):
    """Position of the first disposition phrase that is not part of 'Revoked in part by' and the like."""
    for m in DISP_KW.finditer(t):
        if re.match(r"Revoked\s*by", m.group(0)) and re.search(r"in\s*part\s*$", t[:m.start()]):
            continue
        return m.start()
    return None


def anchor_key(m) -> str:
    n = str(int(m.group(1)))
    if m.group(2):
        return "EO:" + n + m.group(2)
    if m.group(3):
        return "EO:" + n + m.group(3)
    if m.group(4):
        return "EO:" + n + "½"
    return "EO:" + n


def key_number(key: str):
    m = re.match(r"EO:(\d+)", key)
    return int(m.group(1)) if m else None


def key_order(key: str):
    """Order within the table: 6810 < 6810A, 2245 < 2245½ < 2246, 9 < 9-2 < 10."""
    m = re.match(r"EO:(\d+)(.*)$", key)
    return (int(m.group(1)), m.group(2)) if m else None


def parse_table_page(page: dict, census_upper: set, is_first: bool, offset: int = 11, max_eo: int | None = None):
    """One page of the Executive Orders disposition table -> (anchors, orphans, stats)."""
    pno = page["page"]
    chunks = page["chunks"]
    # The printed page number is the lowest chunk on the page (y about 95-103 here, not below 40).
    printed = ""
    lowest = min((c[1] for c in chunks), default=0)
    for x, y, t in chunks:
        if re.fullmatch(r"\s*\d{3,4}\s*", t) and int(t) == pno - offset and y < 110 and y <= lowest + 0.1:
            printed = t.strip()
    chunks = [c for c in chunks if not (printed and c[2].strip() == printed and c[1] < 110)]
    printed_read = bool(printed)
    printed = printed or str(pno - offset)
    ymax = 625.0
    if is_first:
        heads = [y for x, y, t in chunks if t.strip() == "Executive Orders"]
        if not heads:
            return [], [], {"page": pno, "skipped": "no Executive Orders heading"}
        ymax = min(ymax, heads[0] - 1)
    ch = [(x, y, re.sub(r"^[\s·•*'`]+", "", t.replace("\n", " "))) for x, y, t in chunks if 40 < y < ymax]
    ch = [c for c in ch if c[2].strip()]
    # running heads that the OCR split into several chunks on one line ('Codification', ' of', ' Presidential ...')
    by_line = collections.defaultdict(list)
    for c in ch:
        by_line[round(c[1])].append(c)
    drop = set()
    for y0, cs in by_line.items():
        cs = sorted(cs + by_line.get(y0 + 1, []), key=lambda c: c[0])
        if len(cs) > 1 and RUNNING_HEADS.match(" ".join(c[2] for c in cs)):
            drop |= {id(c) for c in cs}
    ch = [c for c in ch if id(c) not in drop]
    ch = [c for c in ch if not re.match(r"^\s*(Numbe\s*r\s*or\s*Date|Number|Amendments|Disposition)\b", c[2])
          and not RUNNING_HEADS.match(c[2])]
    if not ch:
        return [], [], {"page": pno, "skipped": "empty"}
    xs = [x for x, y, t in ch if x < 100 and (NUM_RE.match(t) or DATE_FULL.match(t) or DATE_MD.match(t))]
    if not xs:
        return [], [], {"page": pno, "skipped": "no number column"}
    numx = min(xs)
    kwx = collections.Counter(round(x) for x, y, t in ch if x > numx + 150 and first_disp_kw(t.strip()) == 0)
    dispx = float(kwx.most_common(1)[0][0]) if kwx else numx + 210
    amx_c = collections.Counter(round(x) for x, y, t in ch if numx + 40 < x < dispx - 40 and AMEND_KW.match(t))
    amx = float(amx_c.most_common(1)[0][0]) if amx_c else dispx - 140

    def isolated(c0):
        x0, y0 = c0[0], c0[1]
        for c1 in ch:
            if c1 is c0 or abs(c1[1] - y0) > 2.6 or c1[0] < dispx - 6:
                continue
            if c1[0] < x0 and c1[0] + CHAR_W * len(c1[2].rstrip()) >= x0 - STRAY_GAP:
                return False
            if x0 <= c1[0] <= x0 + CHAR_W * len(c0[2].strip()) + STRAY_GAP:
                return False
        return True

    stray = [c0 for c0 in ch if c0[0] >= dispx - 6 and STRAY_DIGITS.match(c0[2]) and isolated(c0)]
    stray_dropped = [{"page": pno, "x": c0[0], "y": c0[1], "text": c0[2].strip()} for c0 in stray]
    ch = [c0 for c0 in ch if not any(c0 is s0 for s0 in stray)]

    anchors, disp_parts, amend_parts, md_frags, year_frags, orphans = [], [], [], [], [], []

    def add_anchor(key, y, raw, flags, x=numx):
        anchors.append({"key": key, "y": y, "raw": raw.strip(), "flags": list(flags), "page": pno, "printed": printed,
                        "disp": [], "amend": [], "disp_dy": None, "x": x})

    def split_content(x, y, t, from_anchor=False):
        t = t.strip()
        if not t:
            return
        if not from_anchor and x > amx + 20 and WRAPPED_DISP_REF.match(t):
            # '. EO 12220': the period closes the amendments list and the bare 'EO 12220' is the wrapped end of the
            # disposition ('See note at | EO 12220, Chapter 15'; 'Revokedby | EO 11788'); OCR made it one chunk
            disp_parts.append((dispx + 6, y, WRAPPED_DISP_REF.match(t).group(1), False, "wrapped_reference_from_amendments_column"))
            return
        k = first_disp_kw(t)
        if k is None and x < dispx - 3:
            # free text after an amendments list, placed by its estimated x (about 3.2 pt per character)
            for m in FREE_TEXT_START.finditer(t):
                if abs(x + 3.2 * m.start() - dispx) <= 30 and not AMEND_KW.match(t[m.start():]):
                    amend_parts.append((x, y, t[:m.start()].strip()))
                    disp_parts.append((dispx, y, t[m.start():].strip(), True, "free_text_split_by_position"))
                    return
        if k is None:
            if from_anchor and not AMEND_KW.match(t):
                disp_parts.append((dispx, y, t, True, "free_text_in_anchor_chunk"))
            else:
                amend_parts.append((x, y, t))
            return
        if t[:k].strip(" .…,"):
            amend_parts.append((x, y, t[:k].strip()))
        disp_parts.append((dispx, y, t[k:].strip(), True, "split_from_chunk"))

    def anchor_chunk(x, y, t, flags=()):
        m = DATE_FULL.match(t)
        if m:
            add_anchor("date:" + iso(m.group(1), m.group(2), m.group(3)), y, t[:m.end()], flags)
            rest = t[m.end():]
        else:
            m = NUM_RE.match(t)
            add_anchor(anchor_key(m), y, t[:m.end()], flags)
            rest = t[m.end():]
        rest = LEADERS.sub("", rest)
        if not rest:
            return
        if NUM_RE.match(rest) and (rest[:1].isdigit()):
            # two anchors glued: '5924...........5925' or '314....325A'
            anchor_chunk(x, y - pitch_guess, rest, flags=("anchor_glued_to_anchor_above_y_estimated",))
            return
        split_content(x, y, rest, from_anchor=True)

    pitch_guess = 7.0
    for x, y, t in ch:
        s = t.strip()
        if x < numx + 12:
            if DATE_FULL.match(s) or (NUM_RE.match(s) and s[:1].isdigit() and not YEAR_PART.match(s)):
                anchor_chunk(x, y, s)
            elif DATE_MD.match(s):
                m = DATE_MD.match(s)
                md_frags.append({"y": y, "mon": m.group(1), "day": m.group(2), "raw": s, "how": "number_column"})
            elif YEAR_PART.match(s):
                m = YEAR_PART.match(s)
                year_frags.append({"y": y, "day": m.group(1), "year": m.group(2), "raw": s})
            else:
                rest = LEADERS.sub("", s)
                if rest:
                    split_content(x, y, rest)
        elif x < numx + 30 and YEAR_PART.match(s):
            m = YEAR_PART.match(s)
            year_frags.append({"y": y, "day": m.group(1), "year": m.group(2), "raw": s})
        elif x >= dispx - 6:
            disp_parts.append((x, y, s, False, ""))
        else:
            split_content(x, y, s)

    # Month-day swallowed by a disposition chunk of the same row: 'Revokedby EO 9521Dec. 31' + ', 1896'.
    for yf in year_frags:
        if any(abs(md["y"] - yf["y"]) <= 2.5 for md in md_frags):
            continue
        for i, (x, y, t, forced, how) in enumerate(disp_parts):
            m = SWALLOWED_DATE.search(t)
            if m and abs(y - yf["y"]) <= 2.5 and m.start() > 0:
                md_frags.append({"y": y, "mon": m.group(1), "day": m.group(2), "raw": m.group(0),
                                 "how": "swallowed_by_disposition"})
                disp_parts[i] = (x, y, t[:m.start()].strip(), forced, how)
                break
    used_years = set()
    for md in md_frags:
        best = min((yf for yf in year_frags if id(yf) not in used_years), key=lambda yf: abs(yf["y"] - md["y"]), default=None)
        flags = ["date_joined_from_fragments"] + (["month_day_swallowed_by_disposition"] if md["how"] != "number_column" else [])
        if best is None or abs(best["y"] - md["y"]) > 2.5:
            add_anchor("date:%s %s, ?" % (md["mon"], md["day"] or "?"), md["y"], md["raw"], flags + ["year_not_found"])
            continue
        used_years.add(id(best))
        day = md["day"] or best["day"]
        if md["day"] and best["day"] and md["day"] != best["day"]:
            flags.append("two_days_read")
        add_anchor("date:" + (iso(md["mon"], day, best["year"]) or "%s %s, %s" % (md["mon"], day, best["year"])),
                   md["y"], md["raw"] + " " + best["raw"], flags)
    for yf in year_frags:
        if id(yf) not in used_years:
            orphans.append({"page": pno, "y": yf["y"], "text": "YEAR_FRAGMENT:" + yf["raw"]})

    anchors.sort(key=lambda a: -a["y"])
    diffs = [a["y"] - b["y"] for a, b in zip(anchors, anchors[1:]) if 5 <= a["y"] - b["y"] <= 9]
    pitch = statistics.median(diffs) if diffs else 7.0
    for a in anchors:
        if "anchor_glued_to_anchor_above_y_estimated" in a["flags"]:
            # re-place with the measured pitch (the parser guessed 7.0 before the pitch was known)
            a["y"] = a["y"] + pitch_guess - pitch

    # The next row's number glued onto a disposition: 'Revokedby EO 8036641', 'Temporary11383'.
    def fits(n_key, y_new):
        n = key_order(n_key)
        if n is None:
            return False
        if any(abs(a["y"] - y_new) <= 2.5 for a in anchors):
            return False
        above = [key_order(a["key"]) for a in anchors if a["y"] > y_new and key_order(a["key"]) is not None]
        below = [key_order(a["key"]) for a in anchors if a["y"] < y_new and key_order(a["key"]) is not None]
        return (not above or above[-1] < n) and (not below or n < below[0])

    # A row's own number can be glued onto the end of its disposition or amendments chunk, while the number
    # column shows only a dot leader: 'Revokedby EO 8036641' (EO 8036; row 641), 'Supersededby EO 105909980',
    # 'Temporary11383', 'Continuedby EO 10348 ...9989'. It is split off only when exactly one split puts a
    # number where the page has none and keeps the page's numbers in order (same row first, then next row).
    def glued_candidates(t, column):
        m = NO_ARG_DISP.match(t) if column == "disp" else None
        if m:
            return [(m.group(1), m.group(2))]
        m = LEADER_NUMBER.match(t)
        if m:
            return [(m.group(1), m.group(2))]
        m = TRAILING_NUMBER.match(t) if column == "disp" else None
        if m and (len(m.group(2)) >= 6 or int(m.group(2)) > 12700):
            digits = m.group(2)
            return [(m.group(1) + digits[:k], digits[k:]) for k in (3, 4, 5)
                    if k < len(digits) and digits[k] != "0" and int(digits[:k]) <= 12700]
        return []

    # Two rows in one OCR piece: '2768......... Revokedby EO 34612786 Revokedby EO 3461' is printed as two rows,
    # '2768 ... Revoked by EO 3461' and '2786 ... Revoked by EO 3461'. Where a second status phrase follows a number,
    # the number is split into the first row's acting number and the next row's number. The split is made only when
    # exactly one way of splitting puts the next number where the page has none, in the page's order, with an acting
    # number no higher than the table's last EO. The second row takes the rest of the piece as its disposition.
    def merged_candidates(t):
        k0 = first_disp_kw(t)
        if k0 is None:
            return []
        out = []
        for m in DISP_KW.finditer(t):
            if m.start() <= k0:
                continue
            head, tail = t[:m.start()], t[m.start():]
            cands = []
            g = MERGED_HEAD.match(head)
            if g and g.group("next"):
                cands.append((g.group("pre") + g.group("digits"), g.group("next")))
            elif g:
                d = g.group("digits")
                cands += [(g.group("pre") + d[:k], d[k:]) for k in (3, 4, 5)
                          if k < len(d) and d[k] != "0" and (max_eo is None or int(d[:k]) <= max_eo)]
            g = MERGED_NOARG_HEAD.match(head)
            if g:
                cands.append((g.group("pre"), g.group("next")))
            if cands:
                out.append((cands, tail))
        return out

    merged_splits = []
    for i in range(len(disp_parts)):
        part = disp_parts[i]
        x, y, t = part[:3]
        for cands, tail in merged_candidates(t):
            y_new = y - pitch
            ok = [(head, num) for head, num in cands if fits("EO:" + num, y_new)]
            if len(ok) != 1:
                continue
            head, num = ok[0]
            how = ";".join(h for h in (part[4] if len(part) > 4 else "", "merged_ocr_piece_split") if h)
            disp_parts[i] = (x, y, head.strip(), True, how)
            add_anchor(anchor_key(NUM_RE.match(num)), y_new, num, ["row_split_from_merged_ocr_piece"])
            new = anchors[-1]
            new.update({"disp": [tail.strip()], "disp_dy": 0.0, "disp_how": "row_split_from_merged_ocr_piece",
                        "disp_free_text": first_disp_kw(tail.strip()) != 0})
            anchors.sort(key=lambda a: -a["y"])
            merged_splits.append({"page": pno, "piece": t, "first_row_text": head.strip(), "second_row": new["key"],
                                  "second_row_text": tail.strip()})
            break

    for column, parts in (("disp", disp_parts), ("amend", amend_parts)):
        for i, part in enumerate(parts):
            x, y, t = part[:3]
            cand = glued_candidates(t, column)
            for y_new, flag in ((y, f"anchor_glued_to_end_of_{column}_chunk"),
                                (y - pitch, f"anchor_glued_to_{column}_above_y_estimated")):
                ok = [(head, num) for head, num in cand if fits("EO:" + num, y_new)]
                if len(ok) == 1:
                    head, num = ok[0]
                    parts[i] = (x, y, head.strip()) + tuple(part[3:])
                    add_anchor(anchor_key(NUM_RE.match(num)), y_new, num, [flag])
                    anchors.sort(key=lambda a: -a["y"])
                    break

    # '½' read as '2' (22452 -> 2245½): the number breaks the page's order and the census has the ½ identity.
    nums = [(i, key_number(a["key"])) for i, a in enumerate(anchors) if key_number(a["key"]) is not None]
    for j, (i, n) in enumerate(nums):
        a = anchors[i]
        prev_n = nums[j - 1][1] if j else None
        next_n = nums[j + 1][1] if j + 1 < len(nums) else None
        in_order = (prev_n is None or prev_n <= n) and (next_n is None or n <= next_n)
        if not in_order and a["key"] == "EO:%d" % n and str(n).endswith("2"):
            half = "EO:%d½" % (n // 10)
            if half.upper() in census_upper and (prev_n is None or prev_n <= n // 10) and (next_n is None or n // 10 <= next_n):
                a["key"] = half
                a["flags"].append("half_read_as_2")
    nums = [key_number(a["key"]) for a in anchors if key_number(a["key"]) is not None]
    for a in anchors:
        n = key_number(a["key"])
        if n is None:
            continue
        i = nums.index(n)
        if (i and nums[i - 1] > n) or (i + 1 < len(nums) and n > nums[i + 1]):
            a["flags"].append("out_of_page_order")

    # ---- pair disposition lines and amendment lines with anchors
    def lines_of(parts):
        parts = sorted(parts, key=lambda p: -p[1])
        out = []
        for p in parts:
            if out and abs(out[-1]["parts"][-1][1] - p[1]) <= 1.6:
                out[-1]["parts"].append(p)
            else:
                out.append({"y": p[1], "parts": [p]})
        for ln in out:
            finish_line(ln)
        return out

    def finish_line(ln):
        ln["parts"].sort(key=lambda p: p[0])
        real = [p for p in ln["parts"] if p[2].strip(" .…,;:")]
        ln["x0"] = (real or ln["parts"])[0][0]
        ln["text"] = " ".join(p[2] for p in ln["parts"] if p[2])
        ln["forced"] = any(len(p) > 3 and p[3] for p in ln["parts"])
        ln["how"] = ";".join(sorted({p[4] for p in ln["parts"] if len(p) > 4 and p[4]}))

    def starts_row(ln, col_x, field):
        return ln["x0"] < col_x + 3.5 or ln["forced"] or (
            field == "disp" and first_disp_kw(ln["text"]) == 0 and ln["x0"] < col_x + 5)

    # A row's text can run onto a second OCR chunk on the same printed line that sits a little higher than the
    # chunk that starts it: 'Revokedby EOs 9521' (y 549.4) + ', 10697' (x 327, y 551.1) beside the number 9303
    # (y 551.0). Taken alone, the indented piece looks like a wrapped line of the row above. A piece within
    # SAME_LINE_DY of a row's number whose y was measured (not estimated) is on that row's line, whatever its
    # indent, so it is joined to the line that starts that row.
    SAME_LINE_DY = 1.5

    def join_same_line_pieces(lines, col_x, field):
        measured = [a for a in anchors if not any(f.endswith("y_estimated") for f in a["flags"])]
        starts = [ln for ln in lines if ln["text"].strip(" .…,") and starts_row(ln, col_x, field)]
        start_ids = {id(ln) for ln in starts}

        def nearest(y, pool, dy):
            near = [a for a in pool if abs(a["y"] - y) <= dy]
            return min(near, key=lambda a: abs(a["y"] - y)) if near else None

        out = []
        for ln in lines:
            if id(ln) in start_ids or not ln["text"].strip(" .…,"):
                out.append(ln)
                continue
            a = nearest(ln["y"], measured, SAME_LINE_DY)
            own = [m for m in starts if abs(m["y"] - a["y"]) <= 3.6 and nearest(m["y"], anchors, 3.6) is a] if a else []
            if not own:
                out.append(ln)
                continue
            m = min(own, key=lambda m: abs(m["y"] - a["y"]))
            m["parts"] += ln["parts"]
            finish_line(m)
            m["joined_same_line_piece"] = True
            same_line_joins.append({"page": pno, "field": field, "row": a["key"], "piece": ln["text"]})
        return out

    same_line_joins = []

    def attach(lines, col_x, field, name):
        lines = join_same_line_pieces(lines, col_x, field)
        cur, prev_y = None, None
        for ln in lines:
            if not ln["text"].strip(" .…,"):
                continue
            starts = starts_row(ln, col_x, field)
            if starts:
                near = sorted((a for a in anchors if abs(a["y"] - ln["y"]) <= 3.6), key=lambda a: abs(a["y"] - ln["y"]))
                free = [a for a in near if not a[field]]
                if free:
                    cur = free[0]
                    cur[field].append(ln["text"])
                    if field == "disp":
                        cur["disp_dy"] = abs(cur["y"] - ln["y"])
                        cur["disp_how"] = ln["how"]
                        cur["disp_free_text"] = first_disp_kw(ln["text"]) != 0
                        if "merged_ocr_piece_split" in ln["how"]:
                            cur["flags"].append("merged_ocr_piece_split")
                    prev_y = ln["y"]
                    continue
                orphans.append({"page": pno, "y": ln["y"], "text": f"{name}_START:" + ln["text"]})
                cur = None
                continue
            if cur is not None and prev_y is not None and prev_y - ln["y"] <= pitch * 1.6:
                cur[field][-1] += " " + ln["text"]
                prev_y = ln["y"]
            elif cur is None and prev_y is None and (not anchors or ln["y"] > anchors[0]["y"] + 1.0):
                # wrapped text at the top of the page, before its first row: it continues the last row of the page before
                carry[field].append(ln["text"])
            else:
                orphans.append({"page": pno, "y": ln["y"], "text": f"{name}_CONT:" + ln["text"]})

    carry = {"disp": [], "amend": []}
    attach(lines_of(disp_parts), dispx, "disp", "DISPOSITION")
    attach(lines_of(amend_parts), amx, "amend", "AMENDMENTS")
    stats = {"page": pno, "printed": printed, "printed_read": printed_read, "numx": numx, "dispx": dispx, "amx": amx, "pitch": round(pitch, 2),
             "anchors": len(anchors), "with_disposition": sum(1 for a in anchors if a["disp"]), "carry": carry,
             "same_line_joins": same_line_joins, "merged_row_splits": merged_splits, "stray_digits_dropped": stray_dropped}
    return anchors, orphans, stats


CATEGORIES = [  # (squashed lowercase prefix, category, group)
    ("codifiedatchapter", "codified_here", "in_force_1989"),
    ("codified", "codified_elsewhere", "in_force_1989"),
    ("revokedby", "revoked", "ended_by_1989"),
    ("supersededby", "superseded", "ended_by_1989"),
    ("supersedebdy", "superseded", "ended_by_1989"),
    ("supersededy", "superseded", "ended_by_1989"),
    ("nullified", "nullified", "ended_by_1989"),
    ("terminatedby", "terminated", "ended_by_1989"),
    ("eliminated", "eliminated", "ended_by_1989"),
    ("replacedby", "replaced", "ended_by_1989"),
    ("expired", "expired", "ended_by_1989"),
    ("abolished", "abolished", "ended_by_1989"),
    ("abolishes", "abolishes_other_document", "effect_merged_into_other_document"),
    ("authority", "authority", "ended_by_1989"),
    ("temporary", "temporary", "ended_by_1989"),
    ("executedand", "executed_obsolete", "ended_by_1989"),
    ("obsolete", "executed_obsolete", "ended_by_1989"),
    ("hortatory", "hortatory", "no_operative_effect"),
    ("publiclands", "public_lands", "excluded_not_ended"),
    ("tariff", "tariff", "excluded_not_ended"),
    ("selectiveservice", "selective_service", "excluded_not_ended"),
    ("amends", "amends_other_document", "effect_merged_into_other_document"),
    ("revokes", "revokes_other_document", "effect_merged_into_other_document"),
    ("supersedes", "supersedes_other_document", "effect_merged_into_other_document"),
    ("modifies", "modifies_other_document", "effect_merged_into_other_document"),
    ("extends", "extends_other_document", "effect_merged_into_other_document"),
    ("continues", "continues_other_document", "effect_merged_into_other_document"),
    ("supplements", "supplements_other_document", "effect_merged_into_other_document"),
    ("implements", "implements_other_document", "effect_merged_into_other_document"),
    ("terminates", "terminates_other_document", "effect_merged_into_other_document"),
    ("nullifies", "nullifies_other_document", "effect_merged_into_other_document"),
    ("discontinues", "discontinues_other_document", "effect_merged_into_other_document"),
    ("seenote", "see_note", "other"),
    ("see", "see_note", "other"),
]
ENDED_FREE_TEXT = re.compile(r"terminat|abolish|expir|ceased|dissolved|no longer|discontinued|completed", re.I)


def categorise(disposition: str):
    s = squash(disposition).lower().lstrip(".,…")
    if not s:
        return "MISSING", "missing"
    for prefix, cat, group in CATEGORIES:
        if s.startswith(prefix):
            if cat == "authority" and "maintained" in s:
                return "authority_maintained", "other"
            return cat, group
    if ENDED_FREE_TEXT.search(disposition):
        return "free_text_ended", "ended_by_1989"
    return "free_text", "other"


def acting_documents(text: str) -> list[str]:
    """Documents named in a disposition: EO, Proc, PLO, Pub. L., act of <date>, U.S.C., CFR."""
    out = []
    for m in re.finditer(r"\b(EOS?s?|Procs?)\s*\.?\s*((?:\d{1,5}(?:-?[A-Z](?![a-z])|½)?\s*(?:,|and|&)?\s*)+)", text):
        kind = "EO" if m.group(1).upper().startswith("EO") else "Proc"
        for n in re.findall(r"\d{1,5}(?:-?[A-Z](?![a-z])|½)?", m.group(2)):
            out.append(f"{kind}:{n.replace('-', '') if re.search('[A-Z]', n) else n}")
    out += ["PLO:" + n for n in re.findall(r"\bPLO\s*(\d{1,5})", text)]
    out += ["Pub.L." + n.replace(" ", "") for n in re.findall(r"Pub\s*\.?\s*L\s*\.?\s*(\d{2,3}\s*-\s*\d{1,4})", text)]
    out += ["act of " + clean(n) for n in re.findall(r"[Aa]ct\s*of\s*([A-Z][a-z]{2,8}\.?\s*\d{1,2}\s*,\s*\d{4})", text)]
    out += [f"{a} U.S.C. {b}" for a, b in re.findall(r"(\d{1,2})\s*U\s*\.?\s*S\s*\.?\s*C\s*\.?\s*([\d\w-]+)", text)]
    out += [f"{a} CFR {b}" for a, b in re.findall(r"(\d{1,2})\s*CFR\s*([\d.]+\d)", text)]
    seen = []
    for o in out:
        if o not in seen:
            seen.append(o)
    return seen


MECH = {"revoked": ("revocation", ""), "nullified": ("revocation", "nullified"), "superseded": ("supersession", ""),
        "replaced": ("supersession", "replaced"), "terminated": ("termination", ""), "eliminated": ("termination", "eliminated")}


def verb_mechanism(verb: str):
    v = squash(verb).lower()
    for prefix, cat in (("revoked", "revoked"), ("supersede", "superseded"), ("nullified", "nullified"),
                        ("terminated", "terminated"), ("replaced", "replaced"), ("eliminated", "eliminated")):
        if v.startswith(prefix):
            return MECH[cat]
    return None


def mechanism_by_actor(disposition: str, category: str) -> dict:
    """(mechanism, qualifier) for each acting document: that of the nearest ending verb before it ('Superseded by
    EO 11640. Revoked by EO 11788' -> 11640 supersession, 11788 revocation); the row's own category when no verb
    precedes it."""
    out = {}
    cuts = [(m.start(), verb_mechanism(m.group(0))) for m in ENDING_VERB.finditer(disposition)]
    segs = [(0, MECH.get(category))] + cuts
    for (start, mech), (end, _) in zip(segs, segs[1:] + [(len(disposition), None)]):
        for actor in acting_documents(disposition[start:end]):
            out.setdefault(actor, mech or MECH.get(category))
    return out


def parse_table(pages, census_upper: set, offset: int = 11, max_eo: int | None = None, known_ids: set | None = None):
    """known_ids: when given, an EO named as the acting document must be one of these ids (the census), or it is
    flagged and not treated as the order that ended the row. max_eo: the last EO number of the table's period;
    a higher acting EO number is a misread and is treated the same way."""
    rows, orphans, stats = [], [], []
    for i, page in enumerate(pages):
        a, o, s = parse_table_page(page, census_upper, i == 0, offset, max_eo)
        for field, texts in s.pop("carry", {}).items():
            if not texts:
                continue
            if rows and rows[-1][field]:
                rows[-1][field][-1] += " " + " ".join(texts)
                if "continued_on_next_page" not in rows[-1]["flags"]:
                    rows[-1]["flags"].append("continued_on_next_page")
            else:
                o += [{"page": page["page"], "y": 999, "text": f"{field.upper()}_CARRY_UNATTACHED:" + t} for t in texts]
        rows += a
        orphans += o
        stats.append(s)
    if max_eo is not None:   # the last EO of the period, or the table's own highest row if that is higher
        max_eo = max([max_eo] + [key_number(r["key"]) for r in rows if key_number(r["key"]) is not None])
    for seq, a in enumerate(rows, 1):
        if a["disp"] and AMEND_KW.match(a["disp"][0]):
            # amendments text that the OCR ran into the disposition column: 'Ratifiedby EO 12294 Codified at ...'
            k = first_disp_kw(a["disp"][0])
            if k:
                a["amend"].append(a["disp"][0][:k].strip())
                a["disp"][0] = a["disp"][0][k:]
                a["flags"].append("amendments_text_in_disposition_column")
        disp = re.sub(r",(?:\s*,)+", ",", clean(" | ".join(a["disp"]))).lstrip(" ,.;…")   # '10858,, 10968' -> '10858, 10968'
        cat, group = categorise(disp)
        cm = re.search(r"Chapter\s*(\d{1,2})\s*,?\s*(?:p\s*\.?\s*(\d{1,4}))?", disp) if cat == "codified_here" else None
        if a["disp"]:
            conf = "high" if (a["disp_dy"] or 0) <= 1.6 and not a["flags"] and not a.get("disp_free_text") else "medium"
            if any(f.endswith("y_estimated") for f in a["flags"]) or "year_not_found" in a["flags"]:
                conf = "low"
        else:
            conf = "none"
        acting = acting_documents(disp) if group != "in_force_1989" else []
        # documents that ended the row: not those named only in a trailing 'See note at EO 12220, Chapter 15'
        ending = acting_documents(re.split(r"See\s*note", disp)[0]) if acting else []
        if a["key"] in acting:
            # the book names the row's own order as the acting document (EO 11818 'Revoked by EO 11818'): a printing
            # error reproduced as printed, flagged, and never emitted as a later-event candidate
            a["flags"].append("acting_document_is_the_row_itself")
        # acting EO numbers that cannot be right: above the table's last EO, or not a census identity
        rejected = []
        for x in ending:
            if not x.startswith("EO:") or x == a["key"]:
                continue
            n = key_number(x)
            if max_eo is not None and n is not None and n > max_eo:
                rejected.append(x)
                a["flags"].append("acting_number_beyond_table_period")
            elif known_ids is not None and x.upper() not in known_ids:
                rejected.append(x)
                a["flags"].append("acting_document_not_in_census")
        if rejected and conf == "high":
            conf = "medium"
        a.update({"seq": seq, "disposition": disp, "amendments": clean(" | ".join(a["amend"])), "category": cat,
                  "group": group, "codified_chapter": cm.group(1) if cm else "",
                  "codified_page": (cm.group(2) or "") if cm else "",
                  "acting": acting, "ending_acting": [x for x in ending if x != a["key"] and x not in rejected],
                  "rejected_acting": rejected, "pairing_confidence": conf})
    return rows, orphans, stats


# ------------------------------------------------------------------ comparisons and outputs
def load_csv(path, key):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return {r[key].upper(): r for r in csv.DictReader(fh)}


def write_csv(path, rows, fields):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def census_state(c, date):
    if not c:
        return "NOT_IN_CENSUS"
    de = (c.get("date_effective") or "").strip()
    if not de:
        return "census_date_blank"
    if not date:
        return "no_date_in_source"
    if len(de) == 4:
        return "census_year_only" if de == date[:4] else "YEAR_CONFLICT"
    return "census_exact_date" if de == date else "DATE_CONFLICT"


def run(repo_root, job_dir, out_dir):
    repo, job_dir, out = pathlib.Path(repo_root), pathlib.Path(job_dir), pathlib.Path(out_dir)
    prov = json.loads((job_dir / "data" / "PROVENANCE.json").read_text(encoding="utf-8"))
    book = prov["book"]
    for key in ("text", "table_chunks"):
        got = sha256_bytes((job_dir / book[key]).read_bytes())
        if got != book[key + "_sha256"]:
            raise SystemExit(f"{book[key]}: sha256 {got} does not match PROVENANCE.json")
    pdf = repo / book["pdf"]
    if not pdf.exists():
        pdf_check = "pdf_not_checked_out"
    else:
        with open(pdf, "rb") as fh:
            head = fh.read(100)
        if head.startswith(b"version https://git-lfs"):
            pdf_check = "pdf_is_lfs_pointer_text_layer_hash_verified"
        else:
            h = hashlib.sha256()
            with open(pdf, "rb") as fh:
                for block in iter(lambda: fh.read(1 << 20), b""):
                    h.update(block)
            if h.hexdigest() != book["pdf_sha256"]:
                raise SystemExit(f"{book['pdf']}: sha256 does not match PROVENANCE.json")
            pdf_check = "match"
    out.mkdir(parents=True, exist_ok=True)   # only once the inputs are known to be the right ones

    census = load_csv(repo / prov["census"], "id")
    census_upper = set(census)
    readiness, rp = {}, repo / prov["readiness"]
    if rp.exists():
        readiness = load_csv(rp, "instrument_id")
    nara_unnumbered, np_ = [], repo / prov["unnumbered_rows"]
    if np_.exists():
        with open(np_, encoding="utf-8-sig", newline="") as fh:
            nara_unnumbered = list(csv.DictReader(fh))
    lord, lp = [], repo / prov["lord_leads"]
    if lp.exists():
        with open(lp, encoding="utf-8-sig", newline="") as fh:
            lord = list(csv.DictReader(fh))
    edges, ep = [], repo / prov["later_events_edges"]
    if ep.exists():
        with open(ep, encoding="utf-8-sig", newline="") as fh:
            edges = list(csv.DictReader(fh))

    lay = book["layout"]
    pages = load_pages(job_dir / book["text"])
    stream, body_stats = body_stream(pages, lay["body_pdf_pages"][0], lay["body_pdf_pages"][1], lay["printed_page_offset"])
    titles = body_stats.pop("recto_titles")
    # chapters without a recto running head: take the title from the CONTENTS pages
    contents = " ".join(t for pno, t in pages if lay["contents_pdf_pages"][0] <= pno <= lay["contents_pdf_pages"][1])
    for m in re.finditer(r"Chapter\s*(\d{1,2})\s*[-—–]\s*([A-Z][A-Za-z ,]+?[a-z])[ \t]*(?:[.…]|\n|\d|$)", contents):
        if m.group(1) not in titles:
            titles[m.group(1)][clean(m.group(2))] += 1
    docs, head_stats = find_documents(stream, titles)
    fragmented = set(body_stats["fragmented"])
    with open(job_dir / book["table_chunks"], encoding="utf-8") as fh:
        tpages = [json.loads(l) for l in fh]
    trows, orphans, tstats = parse_table(tpages, census_upper, lay["printed_page_offset"],
                                         max_eo=lay["complete_eo_run"][1], known_ids=census_upper)

    handle, pdf_sha = book["handle_url"], book["pdf_sha256"]
    short = book["short"]
    # ---- codified documents
    eo_docs = [d for d in docs if d["kind"] == "EO"]
    source_dates = {d["instrument_id"]: d["date"] for d in docs if d["date"]}
    table_by_key = collections.defaultdict(list)
    for r in trows:
        table_by_key[r["key"].upper()].append(r)
    texts = out / "texts"
    texts.mkdir(parents=True, exist_ok=True)
    codified_rows, seen = [], collections.Counter()
    for d in eo_docs:
        iid = d["instrument_id"]
        seen[iid] += 1
        body = document_text(d["lines"], fragmented)
        body_sha = sha256_bytes(body.encode("utf-8"))
        frag_pages = sorted({p for p, _, _ in d["lines"]} & fragmented)
        conf = "high" if d["heading_found"] and not frag_pages and not d["heading_mid_line"] else "medium"
        fname = "texts/%s%s.txt" % (iid.replace(":", "_"), "" if seen[iid] == 1 else "_%d" % seen[iid])
        pp, pr = "PDF pages %d-%d" % d["pdf_pages"], "printed pages %s-%s" % d["printed_pages"]
        header = (f"# {iid}: {d['heading_title'] or '(heading not found; text starts at the SOURCE line)'}\n"
                  f"# AS AMENDED TO JAN 20, 1989; EDITORIAL CODIFICATION; NOT THE ORIGINAL TEXT.\n"
                  f"# Source: {book['title']} ({book['published']}); {book['digitized_by']}\n"
                  f"# PDF: {book['pdf']} sha256 {pdf_sha}\n"
                  f"# {pp}; {pr}; chapter {d['chapter']} ({d['chapter_title']})"
                  f"{'; subchapter ' + d['subchapter'] + ' (' + d['subchapter_title'] + ')' if d['subchapter'] else ''}; "
                  f"confidence {conf}\n"
                  f"# SOURCE line: {d['source_text']}\n"
                  f"# Text: OCR text layer of the scan ({book['extractor']}), running heads and page numbers removed"
                  f"{'; PDF pages ' + ','.join(map(str, frag_pages)) + ' came out a few words per line and were joined into paragraphs' if frag_pages else ''}. "
                  f"Not human-verified. Body sha256 {body_sha}\n\n")
        (out / fname).write_text(header + body, encoding="utf-8", newline="\n")
        c = census.get(iid.upper())
        cs = census_state(c, d["date"])
        rd = readiness.get(iid.upper(), {})
        trs = table_by_key.get(iid.upper(), [])
        tcod = [r for r in trs if r["category"] == "codified_here"]
        checks = []
        if not trs:
            checks.append("not_found_in_disposition_table")
        elif not tcod:
            checks.append("table_disposition_not_codified_here:" + "/".join(r["category"] for r in trs))
        else:
            t = tcod[0]
            if t["codified_chapter"] and t["codified_chapter"] != d["chapter"]:
                checks.append(f"table_chapter_{t['codified_chapter']}_vs_body_chapter_{d['chapter']}")
            if t["codified_page"] and not (int(d["printed_pages"][0]) <= int(t["codified_page"]) <= int(d["printed_pages"][1])):
                checks.append(f"table_page_{t['codified_page']}_outside_body_pages_{d['printed_pages'][0]}-{d['printed_pages'][1]}")
        if cs in ("YEAR_CONFLICT", "DATE_CONFLICT", "NOT_IN_CENSUS"):
            checks.append("census_" + cs)
        if rd.get("provisional_status") == "no":
            checks.append("decided_NO_but_codified_in_force_1989")
        n_amend = len(AMEND_NOTE_RE.findall(re.sub(r"\s+", " ", body)))
        codified_rows.append({
            "instrument_id": iid, "census_id": (c or {}).get("id", ""), "date": d["date"],
            "fr_citation": d["fr_citation"], "cfr_compilation": d["cfr_compilation"],
            "not_in_fr_system": d["not_in_fr_system"], "restated": d["restated"], "restated_by": d["restated_by"],
            "restated_by_date": d["restated_by_date"], "codified_text_fr": d["codified_text_fr"],
            "chapter": d["chapter"], "chapter_title": d["chapter_title"], "subchapter": d["subchapter"],
            "subchapter_title": d["subchapter_title"], "heading_title": d["heading_title"],
            "pdf_pages": "%d-%d" % d["pdf_pages"], "printed_pages": "%s-%s" % d["printed_pages"],
            "heading_found": "yes" if d["heading_found"] else "no", "fragmented_pages": ",".join(map(str, frag_pages)),
            "confidence": conf, "amendment_notes": n_amend,
            "table_disposition": " || ".join(r["disposition"] for r in trs),
            "table_pdf_page": ",".join(str(r["page"]) for r in trs),
            "census": cs, "census_date_effective": (c or {}).get("date_effective", ""),
            "provisional_status": rd.get("provisional_status", ""),
            "step_original_text": rd.get("step_original_text", ""),
            "step_ending_or_current_basis": rd.get("step_ending_or_current_basis", ""),
            "agreement": "agrees" if not checks else "CHECK", "checks": "|".join(checks),
            "source_text": d["source_text"], "text_path": fname, "text_sha256": body_sha, "chars": len(body)})

    # ---- dated references inside the codified texts
    refs, ref_where = dated_references(stream)
    ref_rows = []
    for iid, cnt in sorted(refs.items(), key=lambda kv: int(kv[0][3:])):
        date, n = cnt.most_common(1)[0]
        c = census.get(iid)
        ref_rows.append({"instrument_id": iid, "date": date, "mentions": n, "variant_dates": len(cnt),
                         "all_dates": "|".join(f"{d}x{k}" for d, k in sorted(cnt.items())),
                         "census": census_state(c, date), "census_date_effective": (c or {}).get("date_effective", ""),
                         "source_line_date": source_dates.get(iid, ""),
                         "agrees_with_source_line": ("" if iid not in source_dates else
                                                     "yes" if source_dates[iid] == date else "NO"),
                         "first_pdf_page": ref_where[(iid, date)]})

    # ---- unnumbered date rows: NARA online-codification rows held by the census, and Lord's 1943 list
    nara_by_date = collections.defaultdict(list)
    for r in nara_unnumbered:
        nara_by_date[r["reference_date"]].append(r)
    date_rows = [r for r in trows if r["key"].startswith("date:")]
    by_date_seen = collections.Counter()
    unnumbered_rows = []
    for r in date_rows:
        date = r["key"][5:]
        by_date_seen[date] += 1
        cands = nara_by_date.get(date, [])
        if len(cands) == 1:
            state, cid, note = "match", cands[0]["instrument_id"], ""
        elif len(cands) > 1:
            k = by_date_seen[date] - 1
            state, cid = "ambiguous_same_date", ""
            order_hint = cands[k]["instrument_id"] if k < len(cands) else ""
            note = (f"{len(cands)} census rows share this date ({', '.join(c['instrument_id'] for c in cands)}); "
                    f"by order on the page this would be {order_hint}, not asserted")
        else:
            state, cid, note = "unmatched", "", ""
        lm = []
        if re.fullmatch(r"\d{4}-\d\d-\d\d", date):
            y, m_, d_ = date.split("-")
            lm = [l["candidate_id"] for l in lord if l.get("year_hint_UNVERIFIED") == str(int(y))
                  and l.get("month") == str(int(m_)) and l.get("day") == str(int(d_))]
        c = census.get(cid.upper()) if cid else None
        unnumbered_rows.append({
            "table_row": r["seq"], "date": date, "raw": r["raw"], "pdf_page": r["page"], "printed_page": r["printed"],
            "disposition": r["disposition"], "category": r["category"], "amendments": r["amendments"],
            "pairing_confidence": r["pairing_confidence"], "flags": "|".join(r["flags"]),
            "nara_census_match": state, "census_id": cid, "census_date_effective": (c or {}).get("date_effective", ""),
            "nara_editorial_category": next((x["editorial_category"] for x in cands if x["instrument_id"] == cid), ""),
            "note": note, "lord_1943_match": "match" if len(lm) == 1 else ("ambiguous" if lm else "unmatched"),
            "lord_candidate_ids": "|".join(lm)})
        r["census_id"] = cid

    # ---- table rows vs census and readiness
    for r in trows:
        if r["key"].startswith("EO:"):
            c = census.get(r["key"].upper())
            r["census_id"] = (c or {}).get("id", "")
        r["in_census"] = "yes" if r.get("census_id") else "no"
        rd = readiness.get((r.get("census_id") or "").upper(), {})
        r["provisional_status"] = rd.get("provisional_status", "")
        r["step_ending_or_current_basis"] = rd.get("step_ending_or_current_basis", "")

    # acting-document dates: the book's own SOURCE lines first, else the OFR catalog date that later-events carries
    acting_date = {}
    for e in edges:
        a, d = e.get("acting_id", ""), e.get("date_candidate", "")
        if a and re.fullmatch(r"\d{4}-\d\d-\d\d", d or "") and "signing_date" in (e.get("date_basis") or ""):
            acting_date.setdefault(a.upper(), d)
    post_1989 = collections.defaultdict(list)
    for e in edges:
        t, d = (e.get("target_id") or "").upper(), e.get("date_candidate") or ""
        if t and e.get("mechanism") in ("revocation", "supersession", "termination") and d > SNAPSHOT:
            post_1989[t].append(f"{e.get('acting_id')} {e.get('mechanism')} {d}")
    # Independent check of the pairing: does the OFR online disposition data (read by jobs/later-events) name the
    # same acting document for the same target?
    le_actors = collections.defaultdict(set)
    for e in edges:
        t, a = (e.get("target_id") or "").upper(), (e.get("acting_id") or "").upper()
        if t and a and e.get("mechanism") in ("revocation", "supersession", "termination"):
            le_actors[t].add(a)
    for r in trows:
        acts = {a.upper() for a in r["ending_acting"] if a.startswith("EO:")}
        cid = (r.get("census_id") or "").upper()
        if r["category"] not in ("revoked", "superseded") or not acts or not cid or not edges:
            r["later_events_check"] = ""
        elif not le_actors.get(cid):
            r["later_events_check"] = "later_events_has_no_ending_edge"
        elif acts & le_actors[cid]:
            r["later_events_check"] = "same_acting_order"
        else:
            r["later_events_check"] = "DIFFERENT_acting_order:" + "|".join(sorted(le_actors[cid]))[:80]

    status_leads, fragments = [], collections.defaultdict(list)
    for r in trows:
        r["acting_documents"] = "|".join(r["acting"])
        r["rejected_acting_documents"] = "|".join(r["rejected_acting"])
    for r in trows:
        cid = r.get("census_id") or ""
        ps = r["provisional_status"]
        lead = ""
        if ps == "no" and r["group"] == "in_force_1989":
            later = post_1989.get(cid.upper(), [])
            lead = "DECIDED_NO_BUT_IN_FORCE_1989" + ("_LATER_ENDING_KNOWN" if later else "_NO_LATER_ENDING_IN_LATER_EVENTS")
            r["later_endings"] = "; ".join(later[:5])
        elif ps == "yes" and r["group"] == "ended_by_1989":
            lead = "DECIDED_YES_BUT_ENDED_BY_1989"
        elif cid and not ps and r["group"] in ("ended_by_1989", "in_force_1989"):
            lead = "UNDECIDED_" + ("ENDED_BY_1989" if r["group"] == "ended_by_1989" else "IN_FORCE_1989")
        if lead:
            status_leads.append(dict(r, lead=lead))
        actors = [a for a in r["ending_acting"] if a.startswith(("EO:", "Proc:"))]
        if cid and r["category"] in MECH and actors and r["pairing_confidence"] in ("high", "medium"):
            by_actor = mechanism_by_actor(r["disposition"], r["category"])
            page_or_item = f"{short}, Executive Orders disposition table, printed page {r['printed'] or '?'}, PDF page {r['page']}"
            for a in actors[:3]:
                d = source_dates.get(a.upper()) or acting_date.get(a.upper(), "")
                basis = ("acting document date from its SOURCE line in this codification" if a.upper() in source_dates else
                         "acting order signing_date from OFR catalog (jobs/later-events EDGES.csv)" if d else "")
                flags = ["status_as_of_1989-01-20", "ocr_table_cell_not_human_verified"]
                if r["pairing_confidence"] != "high":
                    flags.append("needs_page_check")
                if not d:
                    flags.append("acting_document_date_not_attached")
                if len(actors) > 1:
                    flags.append("several_acting_documents_named")
                mechanism, qualifier = by_actor.get(a) or MECH[r["category"]]
                if mechanism != MECH[r["category"]][0]:
                    flags.append("mechanism_from_its_own_verb_not_the_rows_first")
                fragments[cid].append({
                    "actor": a, "mechanism": mechanism, "qualifier": qualifier,
                    "date_candidate": d or None, "date_basis": [basis] if basis else [], "date_candidates_conflicting": [],
                    "stated_effective_date_candidates": [], "evidence_types": ["ofr_codification_1989_table"],
                    "edge_ids": ["OC89-" + sha256_bytes(f"{cid}|{a}|{r['disposition']}|{r['page']}".encode())[:12]],
                    "flags": flags, "quote": r["disposition"][:300], "quote_kind": "ocr_table_cell",
                    "source": {"url": handle, "sha256": pdf_sha, "page_or_item": page_or_item},
                    "status": "CANDIDATE_UNVERIFIED"})

    # ---- census leads
    leads = []
    for r in codified_rows:
        if r["census"] in ("census_year_only", "census_date_blank") and r["date"]:
            leads.append({"instrument_id": r["instrument_id"], "lead": "EXACT_DATE_FROM_SOURCE_LINE_" + r["census"].upper(),
                          "date_in_source": r["date"], "census_date_effective": r["census_date_effective"],
                          "evidence": f"{short}, SOURCE line, printed page {r['printed_pages'].split('-')[0]}, PDF page {r['pdf_pages'].split('-')[0]}"})
        elif r["census"] in ("YEAR_CONFLICT", "DATE_CONFLICT", "NOT_IN_CENSUS"):
            leads.append({"instrument_id": r["instrument_id"], "lead": r["census"] + "_SOURCE_LINE", "date_in_source": r["date"],
                          "census_date_effective": r["census_date_effective"],
                          "evidence": f"{short}, SOURCE line, PDF page {r['pdf_pages'].split('-')[0]}"})
    for r in ref_rows:
        if r["source_line_date"]:
            continue
        if r["census"] == "NOT_IN_CENSUS":
            lead = "NOT_IN_CENSUS_DATED_REFERENCE"
        elif r["census"] in ("YEAR_CONFLICT", "DATE_CONFLICT"):
            lead = r["census"] + "_DATED_REFERENCE"
        elif r["census"] in ("census_year_only", "census_date_blank") and r["variant_dates"] == 1:
            lead = "EXACT_DATE_FROM_DATED_REFERENCE_" + r["census"].upper()
        else:
            continue
        leads.append({"instrument_id": r["instrument_id"], "lead": lead, "date_in_source": r["date"],
                      "census_date_effective": r["census_date_effective"],
                      "evidence": f"{short}, reference 'EO {r['instrument_id'][3:]} of <date>' in a codified text, "
                                  f"{r['mentions']} mention(s), first on PDF page {r['first_pdf_page']}"})
    for u in unnumbered_rows:
        if u["census_id"] and not u["census_date_effective"]:
            lead = "UNNUMBERED_ROW_DATE_FOR_BLANK_CENSUS_DATE"
        elif u["census_id"]:
            continue
        elif u["nara_census_match"] == "ambiguous_same_date":
            lead = "UNNUMBERED_ROW_AMBIGUOUS_CENSUS_MATCH"
        else:
            lead = "UNNUMBERED_ROW_NOT_MATCHED_TO_CENSUS"
        leads.append({"instrument_id": u["census_id"] or "date:" + u["date"], "lead": lead, "date_in_source": u["date"],
                      "census_date_effective": u["census_date_effective"],
                      "evidence": f"{short}, Executive Orders disposition table, PDF page {u['pdf_page']}; {u['note']}".rstrip("; ")})
    for r in trows:
        if r["key"].startswith("EO:") and not r.get("census_id"):
            leads.append({"instrument_id": r["key"], "lead": "NOT_IN_CENSUS_DISPOSITION_TABLE", "date_in_source": "",
                          "census_date_effective": "",
                          "evidence": f"{short}, Executive Orders disposition table, PDF page {r['page']}; raw '{r['raw']}'; flags {'|'.join(r['flags'])}"})
    lo, hi = lay["complete_eo_run"]
    table_keys = {r["key"].upper() for r in trows}
    for cid, c in census.items():
        m = re.fullmatch(r"EO:(\d+)([A-Z]?)", cid)
        if m and lo <= int(m.group(1)) <= hi and cid not in table_keys:
            n = int(m.group(1))
            seen_on = NOT_PRINTED_IN_TABLE.get(n) if not m.group(2) else None
            leads.append({"instrument_id": c["id"], "lead": "IN_CENSUS_NOT_FOUND_IN_TABLE_(PARSER_OR_SOURCE)", "date_in_source": "",
                          "census_date_effective": c.get("date_effective", ""),
                          "evidence": f"{short}: the table lists every EO {lo}-{hi}; this one was not read" + (
                              f"; the page image (PDF page {seen_on}) shows the book does not print this number: the rows "
                              f"either side of it are contiguous" if seen_on else "")})
    run_numbers = {key_number(r["key"]) for r in trows if r["key"].startswith("EO:")}
    run_gaps = [n for n in range(lo, hi + 1) if n not in run_numbers]

    # ---- write
    write_csv(out / "CODIFIED_1989.csv", codified_rows, list(codified_rows[0].keys()))
    disp_fields = ["seq", "page", "printed", "y", "key", "census_id", "in_census", "raw", "amendments", "disposition",
                   "category", "group", "codified_chapter", "codified_page", "acting_documents", "rejected_acting_documents",
                   "pairing_confidence",
                   "flags", "later_events_check", "provisional_status", "step_ending_or_current_basis"]
    for r in trows:
        r["flags"] = r["flags"] if isinstance(r["flags"], str) else "|".join(r["flags"])
    write_csv(out / "DISPOSITION_1989.csv", trows, disp_fields)
    write_csv(out / "DISPOSITION_ORPHANS.csv", orphans, ["page", "y", "text"])
    write_csv(out / "STATUS_LEADS.csv", status_leads,
              ["census_id", "lead", "provisional_status", "category", "group", "disposition", "acting_documents",
               "later_endings", "pairing_confidence", "page", "printed", "step_ending_or_current_basis"])
    write_csv(out / "UNNUMBERED_ROWS.csv", unnumbered_rows, list(unnumbered_rows[0].keys()) if unnumbered_rows else ["date"])
    write_csv(out / "REFERENCE_DATES.csv", ref_rows, list(ref_rows[0].keys()) if ref_rows else ["instrument_id"])
    write_csv(out / "CENSUS_LEADS.csv", leads, ["instrument_id", "lead", "date_in_source", "census_date_effective", "evidence"])
    frag_rows = []
    for cid in sorted(fragments, key=lambda k: (key_number(k) or 0, k)):
        items = fragments[cid]
        srcs, seen_src = [], set()
        for it in items:
            k = it["source"]["page_or_item"]
            if k not in seen_src:
                seen_src.add(k)
                srcs.append(it["source"])
        frag_rows.append({
            "instrument_id": cid, "kind": "later_event_candidates", "produced_by": JOB,
            "confidence_note": ("Machine-read leads from the Executive Orders disposition table of the OFR 1989 Codification "
                                "(status as of January 20, 1989), Google OCR via HathiTrust; rows paired by position on the page. "
                                "date_candidate is the acting document's signing date when known, not a proven effective date. "
                                "The book's codified texts are as-amended editorial texts and are NOT offered as originals. "
                                "Every item needs a human to read the cited page; this is not a legal conclusion."),
            "data": items, "sources": srcs})
    with open(out / "FRAGMENTS.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for f in frag_rows:
            fh.write(json.dumps(f, ensure_ascii=False, sort_keys=True) + "\n")

    cats = collections.Counter(r["category"] for r in trows)
    groups = collections.Counter(r["group"] for r in trows)
    eo_keys = {r["key"] for r in trows if r["key"].startswith("EO:")}
    lead_count = collections.Counter(l["lead"] for l in leads)
    summary = {
        "leads_only": "Nothing is admitted, merged, dated or changed in the census or in any status.",
        "not_originals": "Codified texts are as amended to 1989-01-20 (editorial); no original_representation fragments are emitted.",
        "book": book["title"], "pdf_check": pdf_check, "text_sha256": book["text_sha256"],
        "table_chunks_sha256": book["table_chunks_sha256"], "readiness_read": rp.exists(),
        "later_events_edges_read": ep.exists(), "unnumbered_census_rows_read": np_.exists(), "lord_leads_read": lp.exists(),
        "body": {
            "pdf_pages": lay["body_pdf_pages"], "pages_with_text": body_stats["pages"] - body_stats["empty"],
            "near_empty_pages": body_stats["empty"], "printed_page_read": body_stats["printed_read"],
            "printed_page_inferred": body_stats["printed_inferred"], "fragmented_pages": len(fragmented),
            "source_lines": len(docs), "eo_source_lines": len(eo_docs),
            "proclamation_source_lines": len(docs) - len(eo_docs),
            "eo_distinct": len({d["instrument_id"] for d in eo_docs}),
            "eo_duplicates": sorted(k for k, v in seen.items() if v > 1),
            "eo_with_exact_date": sum(1 for d in eo_docs if d["date"]),
            "eo_without_date": sorted(d["instrument_id"] for d in eo_docs if not d["date"]),
            "eo_not_in_fr_system": sum(1 for d in eo_docs if d["not_in_fr_system"]),
            "eo_restated": sum(1 for d in eo_docs if d["restated"]),
            "eo_heading_found": sum(1 for d in eo_docs if d["heading_found"]),
            "eo_heading_not_found": sorted(d["instrument_id"] for d in docs if not d["heading_found"]),
            "eo_confidence": dict(collections.Counter(r["confidence"] for r in codified_rows)),
            "eo_with_amendment_notes": sum(1 for r in codified_rows if r["amendment_notes"]),
            "eo_by_decade": dict(sorted(collections.Counter((r["date"][:3] + "0s") if r["date"] else "no date" for r in codified_rows).items())),
            "census_state": dict(collections.Counter(r["census"] for r in codified_rows)),
            "provisional_status": dict(collections.Counter(r["provisional_status"] or "undecided" for r in codified_rows)),
            "agreement": dict(collections.Counter(r["agreement"] for r in codified_rows)),
            "checks": dict(collections.Counter(c.split(":")[0] for r in codified_rows for c in r["checks"].split("|") if c)),
            **head_stats},
        "disposition_table": {
            "pdf_pages": [tpages[0]["page"], tpages[-1]["page"]], "rows": len(trows),
            "numbered_rows": sum(1 for r in trows if r["key"].startswith("EO:")),
            "distinct_numbered_keys": len(eo_keys), "date_rows": len(date_rows),
            "rows_without_disposition": sum(1 for r in trows if not r["disposition"]),
            "orphan_fragments": len(orphans),
            "orphans_by_kind": dict(collections.Counter(o["text"].split(":")[0] for o in orphans)),
            "pairing_confidence": dict(collections.Counter(r["pairing_confidence"] for r in trows)),
            "categories": dict(cats.most_common()), "groups": dict(groups.most_common()),
            "complete_eo_run": [lo, hi], "complete_eo_run_gaps": run_gaps,
            "numbered_keys_in_census": sum(1 for k in eo_keys if k.upper() in census_upper),
            "numbered_keys_not_in_census": sorted(k for k in eo_keys if k.upper() not in census_upper),
            "codified_here_rows": cats.get("codified_here", 0),
            "codified_here_not_in_body": sorted({r["key"] for r in trows if r["category"] == "codified_here"}
                                                - {d["instrument_id"] for d in eo_docs}),
            "body_eos_not_codified_here_in_table": sorted({d["instrument_id"] for d in eo_docs}
                                                          - {r["key"] for r in trows if r["category"] == "codified_here"}),
            "flags": dict(collections.Counter(f for r in trows for f in r["flags"].split("|") if f)),
            "same_line_pieces_joined": [j for p in tstats for j in p.get("same_line_joins", [])],
            "merged_row_splits": [j for p in tstats for j in p.get("merged_row_splits", [])],
            "stray_digit_pieces_dropped": [j for p in tstats for j in p.get("stray_digits_dropped", [])],
            "rejected_acting_documents": {r["key"]: r["rejected_acting_documents"] for r in trows if r["rejected_acting_documents"]},
            "later_events_check_on_revoked_superseded": dict(collections.Counter(
                r["later_events_check"].split(":")[0] for r in trows if r["later_events_check"])),
        },
        "unnumbered_rows": {"rows": len(unnumbered_rows),
                            "nara_census_match": dict(collections.Counter(u["nara_census_match"] for u in unnumbered_rows)),
                            "lord_1943_match": dict(collections.Counter(u["lord_1943_match"] for u in unnumbered_rows))},
        "reference_dates": {"distinct_eos": len(ref_rows),
                            "without_source_line": sum(1 for r in ref_rows if not r["source_line_date"]),
                            "disagree_with_source_line": sum(1 for r in ref_rows if r["agrees_with_source_line"] == "NO"),
                            "census_state_without_source_line": dict(collections.Counter(r["census"] for r in ref_rows if not r["source_line_date"]))},
        "status_leads": dict(collections.Counter(l["lead"] for l in status_leads)),
        "census_leads": dict(lead_count),
        "fragments": {"instruments": len(frag_rows), "items": sum(len(f["data"]) for f in frag_rows),
                      "items_with_date": sum(1 for f in frag_rows for i in f["data"] if i["date_candidate"])},
        "table_pages": tstats,
    }
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary
