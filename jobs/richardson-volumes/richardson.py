"""Find the executive orders printed in Richardson's *Messages and Papers of the Presidents* and
locate every WPA numbered and Lord unnumbered citation into each volume.

Each volume is listed in data/PROVENANCE.json. The job reads the committed text layer of the scan
(data/richardson_vNN_pages.jsonl), never the network. Per volume it:
  1. maps PDF pages to printed pages and checks the map against the running heads;
  2. strips running heads, sheet signatures ("M P-VOL IX-5") and OCR specks;
  3. cuts the volume into its own sections ("EXECUTIVE ORDERS", "PROCLAMATIONS", ...) and checks
     the executive-order sections against the volume's table of contents;
  4. splits each executive-order section into documents at datelines, signatures and openings;
  5. dates each document (approval date, then dateline, then "this 4th day of May");
  6. resolves every citation "VI R 122" (WPA numbered list) and "IX Richardson 612" (Lord's
     unnumbered list) to a document on the cited page: match, ambiguous or unmatched, never forced;
  7. compares the result with the census and the readiness tracker.

Machine leads only: nothing here admits, merges, dates or changes a census identity or a status.
Richardson is a printed compilation (GPO 1896-99), not the signed original.
"""

import collections
import csv
import hashlib
import json
import math
import pathlib
import re
import unicodedata

csv.field_size_limit(10 ** 8)

MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
MONTH_NO = {m.lower(): i for i, m in enumerate(MONTHS.split("|"), 1)}
SHORT_NO = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
            "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12}
ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10}

# Greek and Cyrillic letters the OCR uses for Latin ones ("ScorТ", "STANTΟΝ", "О. Е. ВАВСоск").
LOOKALIKE = str.maketrans({
    "Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I", "Κ": "K", "Μ": "M", "Ν": "N", "Ο": "O",
    "Ρ": "P", "Τ": "T", "Υ": "Y", "Χ": "X", "ο": "o", "ν": "v", "ι": "i", "α": "a", "κ": "k", "ρ": "p", "τ": "t",
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H", "О": "O", "Р": "P", "С": "C", "Т": "T",
    "У": "Y", "Х": "X", "Ѕ": "S", "І": "I", "Ј": "J", "а": "a", "е": "e", "о": "o", "р": "p", "с": "c",
    "у": "y", "х": "x", "ѕ": "s", "і": "i", "ј": "j", "ԁ": "d", "ɑ": "a", " ": " ", "—": "-",
    "–": "-", "‐": "-", "‑": "-", "’": "'", "‘": "'", "“": '"', "”": '"'})
OCR_DIGITS = str.maketrans("IlΙOΟoS", "1110005")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


OCR_WORDS = [(re.compile(r"\bMarcharch\b"), "March")]


def norm(s: str) -> str:
    """Latin letters for OCR lookalikes and a few OCR word repairs ("Marcharch"); the text itself is never changed,
    only what the regexes see."""
    s = s.translate(LOOKALIKE)
    for pat, rep_ in OCR_WORDS:
        s = pat.sub(rep_, s)
    return s


def fold(s: str) -> str:
    """norm() plus diacritics removed ("Richarăson" -> "Richarason")."""
    return "".join(c for c in unicodedata.normalize("NFKD", norm(s)) if not unicodedata.combining(c))


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def ocr_int(s: str):
    s = s.translate(OCR_DIGITS).replace(".", "").replace(",", "").replace("·", "").replace(" ", "")
    return int(s) if s.isdigit() else None


def iso(year, month, day) -> str:
    mo = MONTH_NO.get(str(month).lower()) if not str(month).isdigit() else int(month)
    d = ocr_int(str(day)) if not isinstance(day, int) else day
    if not mo or not d or not 1 <= d <= 31:
        return ""
    return "%s-%02d-%02d" % (year, mo, d)


# ----------------------------------------------------------------------------- text layer

def load_pages(path: pathlib.Path) -> list:
    pages = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            pages.append((int(d["page"]), d["text"]))
    return pages


def is_fragmented(text: str) -> bool:
    """A page whose OCR words come one or two per line (more than 30% of 20+ lines)."""
    ls = [l for l in text.split("\n") if l.strip()]
    return len(ls) >= 20 and sum(1 for l in ls if len(l.split()) <= 2) / len(ls) > 0.3


def rejoin(text: str) -> str:
    """Rebuild the reading flow of a fragmented page. Runs of one- and two-word lines are joined; a piece that
    starts with punctuation gives the punctuation to the line before; a piece continues the line before unless that
    line ends a sentence (".", ":", ";") or the piece opens a bracket. The first line (the running head) stays alone."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return text
    pieces, buf = [], []
    for l in lines[1:]:
        if len(l.split()) <= 2:
            buf.append(l)
            continue
        if buf:
            pieces.append(" ".join(buf))
            buf = []
        pieces.append(l)
    if buf:
        pieces.append(" ".join(buf))
    out = [lines[0]]
    for piece in pieces:
        m = re.match(r"^([,.;:]+)\s*(.*)$", piece)
        if m and len(out) > 1:
            out[-1] += " " + m.group(1)
            piece = m.group(2)
        if not piece:
            continue
        if len(out) > 1 and not re.search(r"[.:;\]]\s*$", out[-1]) and not piece.startswith("[") and not out[-1].endswith("*"):
            out[-1] += " " + piece
        else:
            out.append(piece)
    return "\n".join(out)


def best_layer(pages, raw_pages):
    """pypdf text, except on fragmented pages where the committed pdftotext -raw text is rejoined.
    pypdf has already merged words there ("inthe office ofregister"), so its own text can't be rejoined."""
    raw = dict(raw_pages)
    out, used = [], []
    for pno, text in pages:
        if is_fragmented(text) and pno in raw:
            out.append((pno, rejoin(raw[pno])))
            used.append(pno)
        else:
            out.append((pno, text))
    return out, used


# ----------------------------------------------------------------------------- page map

HEAD_NUM = r"([0-9IlΙOΟoS][0-9IlΙOΟoS., ·]{0,5}?)"


def head_patterns(vol):
    names = "|".join(re.escape(n).replace(r"\ ", r"\s*") for n in vol["president_heads"])
    even = re.compile(r"^\s*" + HEAD_NUM + r"\s*[.,·]?\s*(?:Messages|[MN]essages|and\s+[PF]apers)\b.*[PF]resi\s*dents\s*[.,:;]?\s*$")
    odd = re.compile(r"^\s*(?:" + names + r")\s*[.,·:]?\s*(?:" + HEAD_NUM + r")?\s*[.,:;*]?\s*$")
    return even, odd


def printed_of(vol, pdf):
    for lo, hi, off in vol["page_offsets"]:
        if lo <= pdf <= hi:
            return pdf - off
    return None


def page_map(vol, pages):
    """Printed page per PDF page from the configured offsets, checked against every running head
    whose number the OCR left readable."""
    even, odd = head_patterns(vol)
    pm, read, agree, disagree, unread = {}, 0, 0, [], []
    for pno, text in pages:
        pr = printed_of(vol, pno)
        if pr is None:
            continue
        pm[pno] = pr
        first = next((norm(l) for l in text.split("\n") if l.strip()), "")
        m = even.match(first) or odd.match(first)
        n = ocr_int(m.group(1)) if m and m.group(1) else None
        if n is None:
            unread.append(pno)
            continue
        read += 1
        if n == pr:
            agree += 1
        else:
            disagree.append((pno, n, pr, first[:50]))
    return pm, {"pages_mapped": len(pm), "heads_read": read, "heads_agree": agree,
                "heads_disagree": len(disagree), "disagreements": disagree[:20], "pages_without_readable_head": len(unread)}


# ----------------------------------------------------------------------------- page furniture and sections

SIGMARK = re.compile(r"^\s*M\s*\.?\s*P\s*\.?\s*[-—–]?\s*V\s*O\s*L\b.*$", re.I)
SPECK = re.compile(r"^\s*(?:[*!|.\-'`•·,:;]{1,3}|[A-Za-z]|[*!|.\-'`•·,:;]?\d[*!|.\-'`•·,:;]|\d[*!|.\-'`•·,:;]?\d?[*!|'`•·]+)\s*$")
FOOT_DIGITS = re.compile(r"^\s*[0-9IlΙOΟ]{1,3}\s*$")
SECTION = re.compile(
    r"^\s*((?:FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH)\s+ANNUAL\s*,?\s+MESSAGE|(?:FIRST\s+|SECOND\s+)?INAUGURAL\s*,?\s+ADDRESS|"
    r"SPECIAL\s+SESSION\s+MESSAGE|EXECUTIVE\s+ORDERS?|PROCLAMATIONS?|SPECIAL\s+MESSAGES?|VETO\s+MESSAGES?|BIOGRAPHICAL\s+SKETCH|"
    r"DEATH\s+OF\s+PRESIDENT\s+LINCOLN|IMPEACHMENT\s+OF\s+ANDREW\s+JOHNSON.*|ADDENDA)\s*[.,·]*\s*$")


def body_stream(vol, pages, pm):
    """(pdf, printed, line) for every body line: running head, sheet signatures and specks removed."""
    even, odd = head_patterns(vol)
    stream, dropped = [], collections.Counter()
    for pno, text in pages:
        if pno not in pm:
            continue
        lines = [l.rstrip() for l in text.split("\n")]
        nz = [i for i, l in enumerate(lines) if l.strip()]
        drop = set()
        title_page = len(nz) > 1 and re.match(r"^\s*(?:March|April)\s+\d{1,2}\s*,\s*1\d\d\d\s*,?\s*(?:to|TO)\b", norm(lines[nz[1]]))
        if nz and not title_page and (even.match(norm(lines[nz[0]])) or odd.match(norm(lines[nz[0]]))):
            drop.add(nz[0])
            dropped["running_head"] += 1
        for i in [j for j in nz if j not in drop][:3]:
            if len(lines[i].strip()) <= 3 and not re.match(r"^\s*[IVX]+\.\s*$", lines[i]):
                drop.add(i)  # OCR specks under the running head ("T", "11", "Te")
                dropped["speck"] += 1
        for i in nz[-2:]:
            if len(nz) > 2 and FOOT_DIGITS.match(lines[i]):
                drop.add(i)  # page number at the foot of a section-opening page, or an OCR speck
                dropped["foot_number"] += 1
        for i in nz:
            if i in drop:
                continue
            if SIGMARK.match(norm(lines[i])):
                drop.add(i)
                dropped["sheet_signature"] += 1
            elif SPECK.match(lines[i]):
                drop.add(i)
                dropped["speck"] += 1
        for i in nz:
            if i not in drop:
                stream.append((pno, pm[pno], lines[i]))
    return stream, dict(dropped)


def find_sections(vol, stream):
    """Cut the stream at the volume's own section headings. Inside an executive-order section a line
    'EXECUTIVE ORDER.' is a document title, not a new section. A section also ends at a president's
    title page ('Grover Cleveland' / 'March 4, 1893, to ...')."""
    names = [n for n in vol["president_heads"]]
    title = re.compile(r"^\s*(?:%s)\s*$" % "|".join(re.escape(n).replace(r"\ ", r"\s*") for n in names), re.I)
    sections, cur = [], None
    for k, (pdf, pr, l) in enumerate(stream):
        nl = norm(l)
        if title.match(nl) and k + 1 < len(stream) and re.match(r"^\s*(?:March|April)\s+\d", norm(stream[k + 1][2])):
            if cur:
                cur["end"] = k
            cur = {"name": "TITLE PAGE", "start": k, "end": len(stream), "printed_start": pr, "pdf_start": pdf}
            sections.append(cur)
            continue
        m = SECTION.match(nl)
        if not m:
            continue
        name = re.sub(r"[\s,]+", " ", m.group(1)).strip().upper()
        is_eo = name.startswith("EXECUTIVE ORDER")
        if cur and cur["name"].startswith("EXECUTIVE ORDER") and is_eo:
            continue  # a document title inside an executive-order section
        if cur and cur["name"].startswith("PROCLAMATION") and name.startswith("PROCLAMATION") and k - cur["start"] <= 3:
            continue
        if cur:
            cur["end"] = k
        cur = {"name": name, "start": k + 1, "end": len(stream), "printed_start": pr, "pdf_start": pdf}
        sections.append(cur)
    cuts = vol.get("section_last_page", {})
    for s in sections:
        s["kind"] = "orders" if any(s["name"].startswith(x) for x in vol["order_sections"]) else "other"
        last = cuts.get(s["name"])
        if last:
            while s["end"] > s["start"] and stream[s["end"] - 1][1] > last:
                s["end"] -= 1
        s["printed_end"] = stream[s["end"] - 1][1] if s["end"] > s["start"] else s["printed_start"]
    return sections


# ----------------------------------------------------------------------------- documents

MONTH_RE = r"((?i:%s))" % MONTHS
DAY_RE = r"([0-9IlΙOΟ]{1,2})"
NOT_START = (r"(?!(?i:Done|Given|Approved|In|By|Signed|Dated|Attest|Received|Witness|Issued|Effective|On|At|Since|Until|After|Before|"
             r"From|Of|To|And|The|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b)")
# "EXECUTIVE MANSION , Washington , D. C. , May 24 , 1895 ." / "WASHINGTON , April 25 , 1861 .Lieutenant-General SCOTT ." /
# "JULY 26 , 1889 ." / "• DECEMBER II , 1893 ."
DATELINE = re.compile(r"^[•·.*]?\s*" + NOT_START + r"((?:[A-Z][A-Za-z.'\-]*(?:\s+[A-Za-z.'\-]+){0,5}\s*,\s*){0,5})"
                      + MONTH_RE + r"\s*\.?\s*" + DAY_RE + r"\s*[,.]?\s*(1[789]\d\d)\s*[.,:;*]?\s*(.*)$")
PLACE_WORD = re.compile(r"(?i)washington|mansion|department|office|city|\bD\s*\.\s*C\b|headquarters|chamber|commission|bureau|"
                        r"new\s+york|boston|treasury|navy|\bwar\b|\bstate\b|executive|light\s*-?\s*house|board")
OFFICE = re.compile(
    r"^(EXECUTIVE\s+(MANSION|CHAMBER|OFFICE|DEPARTMENT)|EXECUTIVE\s+OF\s+THE\s+UNITED\s+STATES|(WAR|NAVY|STATE|TREASURY|INTERIOR|POST\s*-?\s*OFFICE)\s+DEPARTMENT|"
    r"DEPARTMENT\s+OF\s+[A-Z ]+|ATTORNEY\s*-?\s*GENERAL'?S\s+OFFICE|(ASSISTANT\s+)?ADJUTANT\s*-\s*GENERAL'?S\s+OFFICE|HEADQUARTERS[A-Z ,'.\-]*|"
    r"WASHINGTON(\s+CITY)?(\s*,\s*D\s*\.\s*C\s*\.)?|Washington(\s+City)?(\s*,\s*D\s*\.\s*C\s*\.)?|OFFICE\s+OF\s+[A-Z ,'\-]+|[A-Z ]*BUREAU[A-Z ,]*|"
    r"(UNITED\s+STATES\s+)?CIVIL\s*-?\s*SERVICE\s+COMMISSION|[A-Z][A-Z ]+\s+COMMISSION|NAVY\s+YARD[A-Z ,]*|LIGHT\s*-?\s*HOUSE\s+BOARD|"
    r"CUSTOM\s*-?\s*HOUSE[A-Z ,]*|[A-Z][A-Z ]+\s+SERVICE)\s*,?\s*$")
TITLE_KW = re.compile(r"(?i)\b(ORDERS?|NO\s*\.|CIRCULAR|PROCLAMATION|THANKS|ANNOUNCEMENT|EXECUTIVE|PRESIDENT|INSTRUCTIONS|REGULATIONS|RULES?|"
                      r"MEMORANDUM|RESPECTING|RELATING|CONCERNING|AMENDMENTS?|CIVIL\s*-?\s*SERVICE|CLASSIFICATION|LETTER|NOTICE|"
                      r"RESERVATION|MODIFICATION|EXTENSION|REVOCATION|WITHDRAWING|WITHDRAWAL)\b")
RANK = (r"(?:Hon\s*\.|Honorable|His\s+Excellency|Mr\s*\.|Messrs\s*\.|General|Major|Brigadier|Lieutenant|Colonel|Captain|Commodore|Admiral|"
        r"Rear\s*-?\s*Admiral|Governor|Brevet|Surgeon|To\s+the|To\s+[A-Z])")
ROLE = (r"(?:(?:Acting|Assistant|First\s+Assistant|Second\s+Assistant)\s+)?(?:Secretary\s+of\s+(?:State|War|the\s+Navy|Navy|the\s+Treasury|Treasury|the\s+Interior|Interior|Agriculture)|"
        r"Private\s+Secretary|Secretary|Adjutant\s*-?\s*General|Postmaster\s*-?\s*General|Attorney\s*-?\s*General(?:\s+ad\s+interim)?|"
        r"Commissioners?(?:\s+of\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)?|"
        r"Chief\s+Clerk|Quartermaster\s*-?\s*General|Surgeon\s*-?\s*General|Supervising\s+Surgeon\s*-?\s*General|General\s*-?\s*in\s*-?\s*Chief|"
        r"(?:Brevet\s+)?(?:Major|Brigadier|Lieutenant)\s*-?\s*General(?:\s*,?\s*Commanding)?|Judge\s*-?\s*Advocate\s*-?\s*General|Public\s+Printer|"
        r"President(?:\s+of\s+the\s+(?:United\s+States|Commission|Board))?|President\s+United\s+States|Chairman|Collector[^:]{0,30}|"
        r"Chief\s+of\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)")
ROLE_LINE = re.compile(r"^(?:(?P<name>[A-Z][A-Z.' \-]{2,}[A-Z.])\s*,\s*)?" + ROLE + r"(?P<rest>[^:]{0,30})$")
BY_LINE = re.compile(r"^(?:By\s+(?:the\s+President|order|command|direction)[^:]{0,80}:|Official\s*:|Attest\s*:)")
BY_THE_PRESIDENT_TITLE = re.compile(r"(?i)^by\s+the\s+president\s+of\s+the\s+united\s+states\s*[.:]?\s*$")
LETTER_CLOSE = re.compile(r"(?i)(?:very\s+)?respectfully\s*,?(?:\s*yours)?\s*,?\s*$|yours\s*,?\s*(?:very\s+)?truly\s*,?\s*$|obedient\s+servant\s*,?\s*$|"
                          r"I\s+(?:am|remain)\s*,?\s*(?:sir|gentlemen|sincerely)?\s*,?.*$")
LETTER_END_INLINE = re.compile(r"(?i:servant|respectfully|truly|sincerely)\s*,?\s*[A-Z][A-Z.' \-]{2,}[A-Z.]\s*,\s*" + ROLE + r"[^:]{0,20}$")
NESTED_HINT = re.compile(r"(?i)(order|orders|proclamation|announcement|letter|following|received|published|announced|directs|as\s+follows)\b[^.]{0,120}:\s*$")
APPROVED = re.compile(r"^\s*Approved\s*[,:.]?\s*" + MONTH_RE + r"\s*\.?\s*" + DAY_RE + r"\s*,\s*(1[789]\d\d)")
CLOSING_APPROVAL = re.compile(r"(?i)\b(?:foregoing|above|within)\b.{0,120}\bapprov")
HEREWITH = re.compile(r"(?i)herewith|here\s*to\s+annexed|hereunto\s+annexed|as\s+follows\s*[:.]|the\s+following\s+(?:rules|regulations|amendments|provisions)|"
                      r"are\s+hereby\s+(?:approved|promulgated|prescribed)")
THIS_DAY = re.compile(r"(?:this|on\s+the|the)\s+(\d{1,2}|[0-9IlΙOΟ]{1,2})\s*(?:st|d|th|nd|rd)?\s+day\s+of\s+" + MONTH_RE
                      + r"\s*,?\s*(?:in\s+the\s+year\s+of\s+our\s+Lord\s+)?(?:A\s*\.\s*D\s*\.\s*)?(1[789]\d\d)")
LETTERHEAD = re.compile(r"(?:DEPARTMENT|COMMISSION|OFFICE|Washington|WASHINGTON|BUREAU|HEADQUARTERS|MANSION)\b.{0,60}?" + MONTH_RE
                        + r"\s*\.?\s*" + DAY_RE + r"\s*,\s*(1[789]\d\d)")


def sig_regex(vol, printed=None):
    """The President's signature, for the president whose part of the volume holds the printed page."""
    pats = []
    for s in vol["signatures"]:
        lo, hi = s["printed"]
        if printed is None or lo <= printed <= hi:
            pats.append(r"\s*".join(re.escape(tok) for tok in re.findall(r"[A-Za-z]+|\.", s["name"])))
    return re.compile(r"(?:^|[\s.:,;\]])(?P<sig>" + "|".join(pats)
                      + r")\s*(?:,\s*President(?:\s+(?:of\s+the\s+)?United\s+States)?\s*)?[.,:;]*\s*$")


def caps(s, share=0.8):
    letters = [c for c in s if c.isalpha()]
    return bool(letters) and sum(c.isupper() for c in letters) / len(letters) > share


def is_name(s):
    """A signature name such as 'EDWIN M. STANTON ,' or 'By order : L. THOMAS ,'. An addressee with a rank or
    'Hon.' in front ('Major -General H. W. HALLECK ,') opens a letter instead."""
    s = BY_LINE.sub("", s).strip()
    if re.match(r"^" + RANK + r"\b", s):
        return False
    return (bool(s) and caps(s) and len(s.split()) <= 6 and not OFFICE.match(s) and not TITLE_KW.search(s)
            and bool(re.search(r"[A-Z]{3,}", s)) and bool(re.search(r"[.,]\s*$", s)) and not DATELINE.match(s))


def is_role_line(s):
    m = ROLE_LINE.match(s)
    return bool(m) and not re.search(r"[A-Z]{3,}", m.group("rest") or "") and not s.rstrip().endswith(":")


def is_title(s):
    """A caps title line ('AMENDMENT OF CIVIL - SERVICE RULES .', 'General ORDERS , No. 398 .')."""
    if BY_THE_PRESIDENT_TITLE.match(s):
        return True
    return (caps(s) or (caps(s, 0.5) and TITLE_KW.search(s))) and not is_name(s) and bool(TITLE_KW.search(s) or len(s.split()) >= 5)


def split_runs(lines):
    """On rejoined pages a signature can run into the next dateline ('U. S. GRANT . EXECUTIVE MANSION , ...');
    split such lines so that every dateline starts a line."""
    pat = re.compile(r"(?<=[.\]])\s+(?=(?:EXECUTIVE\s+MANSION|EXECUTIVE\s+OFFICE|(?:WAR|NAVY|STATE|TREASURY)\s+DEPARTMENT|DEPARTMENT\s+OF\s+[A-Z]+|"
                     r"WASHINGTON|HEADQUARTERS|GENERAL\s+ORDERS)\b[^\n]{0,80}?(?i:%s)\s*\d)" % MONTHS)
    out = []
    for pdf, pr, l in lines:
        parts = pat.split(l) if len(l) > 60 else [l]
        out.extend((pdf, pr, p) for p in parts)
    return out


def real_prev(lines, k):
    j = k - 1
    while j >= 0 and len(lines[j].strip()) <= 3:
        j -= 1
    return j


def prev_kind(lines, k, sig):
    j = real_prev(lines, k)
    if j < 0:
        return "start"
    p = norm(lines[j]).strip()
    if sig.search(p) or is_role_line(p) or is_name(p):
        return "signature"
    if OFFICE.match(p) and p.endswith(","):
        return "office"
    if caps(p) or is_title(p):
        return "title"
    if re.search(r"[.:\]*;\"”]\s*$", p):
        return "end"
    return "prose"


def dateline_at(lines, k, pk):
    """The dateline match at line k, or None. pk describes the previous real line (prev_kind)."""
    s = norm(lines[k]).strip()
    m = DATELINE.match(s)
    if not m or len(s) - len(m.group(5)) > 130:
        return None
    pieces, tail = m.group(1), m.group(5)
    if tail and not re.match(r"^[A-Z\[\"'*(•]", tail):
        return None  # "July 4, 1890, the day on which ..." is prose
    if pieces:
        if not (PLACE_WORD.search(pieces) or caps(pieces)):
            return None
        if pk == "prose":
            return None  # a date at line start after unfinished prose is a reference inside a text
    elif pk not in ("start", "signature", "title", "office", "end"):
        return None  # a bare date only after a signature, a caps title, a finished sentence or a section start
    return m


def end_block(lines, i, sig, starts):
    """If line i ends a document, return the index of the last line of its signature block, else None."""
    s = norm(lines[i]).strip()
    prev = norm(lines[i - 1]).strip() if i > 0 else ""
    hit = bool(sig.search(s)) or (bool(LETTER_CLOSE.search(prev)) and is_name(s)) or bool(LETTER_END_INLINE.search(s))
    if not hit and is_role_line(s) and len(s) < 70 and (ROLE_LINE.match(s).group("name") or is_name(prev)):
        hit = True
    if not hit:
        return None
    last = max([a for a in starts if a <= i], default=None)
    if last is not None and i - starts[last] <= 3 and not sig.search(s):
        return None  # an addressee printed right under a dateline ("Secretary of War .")
    k = i
    while k + 1 < len(lines):
        if (k + 1) in starts:
            break
        nx = norm(lines[k + 1]).strip()
        if DATELINE.match(nx) and not APPROVED.match(nx):
            break
        if ((BY_LINE.match(nx) and len(nx) < 90) or is_role_line(nx) or (sig.search(nx) and len(nx) < 45)
                or APPROVED.match(nx) or re.match(r"^\s*Approved\s*[.,:]?\s*$", nx)):
            k += 1
            continue
        if is_name(nx) and k + 2 < len(lines) and (is_role_line(norm(lines[k + 2]).strip()) or sig.search(norm(lines[k + 2]))):
            k += 1
            continue
        if is_name(nx) and BY_LINE.match(norm(lines[k]).strip()):
            k += 1
            continue
        break
    return k


def find_starts(lines, sig):
    """Datelines that open a document, each with the header lines above it (titles, office lines, a
    '[From ...]' note, an addressee). Returns ({first line: dateline line}, closings, nested starts)."""
    n = len(lines)
    starts, nested, closings = {}, set(), {}
    for k in range(n):
        m = dateline_at(lines, k, prev_kind(lines, k, sig))
        if not m:
            continue
        nxt = " ".join(norm(x) for x in lines[k:k + 4])
        after = norm(lines[k + 1]).strip() if k + 1 < len(lines) else ""
        before = norm(lines[k - 1]).strip() if k > 0 else ""
        bare_closing = not m.group(1) and k > 0 and (re.search(r"(?i)\bapprove", before) or (sig.search(after) and len(after) < 40)
                                                     or bool(sig.search(m.group(5) or "")))
        if k > 0 and (CLOSING_APPROVAL.search(nxt[:260]) or bare_closing):
            closings[k] = m  # "EXECUTIVE MANSION, May 5, 1892. The foregoing ... approved": a closing, not a start
            continue
        j, addressee = k, False
        while j - 1 >= 0 and k - j < 10 and (j - 1) not in starts:
            p = norm(lines[j - 1]).strip()
            if sig.search(p) or is_role_line(p) or BY_LINE.match(p) or NESTED_HINT.search(p):
                break  # "I. The following order has been received from the President :" belongs to the wrapper
            if p.startswith("[From") or (p.endswith("]") and j - 2 >= 0 and norm(lines[j - 2]).strip().startswith("[From")):
                j -= 1
                continue
            if re.fullmatch(r"[*\s.]+", p) or len(p) <= 3:
                j -= 1
                continue
            header_only = all(OFFICE.match(norm(x).strip()) for x in lines[j:k])
            if not addressee and header_only and len(p) < 80 and re.match(r"^[A-Z\"']", p) and (
                    p.endswith(":") or (re.search(r"[,.]$", p) and re.match(r"^" + RANK, p))):
                pp = real_prev(lines, j - 1)
                ppl = norm(lines[pp]).strip() if pp >= 0 else ""
                if pp < 0 or re.search(r"[.:\]*;\"”,]\s*$", ppl) or caps(ppl):
                    j -= 1  # addressee printed above the dateline ("Lieutenant-General WINFIELD SCOTT :", "Hon. EDWIN M. STANTON ,")
                    addressee = True
                    continue
                break
            if OFFICE.match(p) and p.endswith(","):
                j -= 1
                continue
            if is_title(p) or (caps(p) and j - 2 >= 0 and is_title(norm(lines[j - 2]).strip())):
                j -= 1
                continue
            break
        starts[j] = k
        before = " ".join(norm(x).strip() for x in lines[max(0, j - 3):j])
        if before and NESTED_HINT.search(before[-200:]):
            nested.add(j)
    return starts, closings, nested


def segment(vol, lines, sig):
    """Split one executive-order section (a list of text lines) into document spans: a document starts at a
    dateline with its header, or after the previous document's signature block."""
    n = len(lines)
    starts, closings, nested = find_starts(lines, sig)
    bounds, ends = set(starts) | {0}, set()
    i = 0
    while i < n:
        e = end_block(lines, i, sig, starts)
        if e is None:
            i += 1
            continue
        # a closing approval right after a Commission's or a Department's signature belongs to the same document
        follow = [t for t in range(e + 1, min(n, e + 4)) if t not in starts]
        if follow and any(t in closings or CLOSING_APPROVAL.search(norm(lines[t])) or APPROVED.match(norm(lines[t])) for t in follow):
            for t in range(e + 1, min(n, e + 6)):
                if t in starts:
                    break
                if sig.search(norm(lines[t])):
                    e = t
                    break
        ends.add(e)
        bounds.add(e + 1)
        i = e + 1
    order = sorted(b for b in bounds if b < n)
    units = []
    for a, b in zip(order, order[1:] + [n]):
        units.append({"start": a, "end": b, "dateline": starts.get(a), "nested": a in nested,
                      "end_marker": any(a <= e < b for e in ends),
                      "closings": [(c, closings[c]) for c in sorted(closings) if a <= c < b], "attachments": 0})
    # rules or regulations printed after the signature of the order that approves them "herewith"
    merged = []
    for u in units:
        p = merged[-1] if merged else None
        if (p and u["dateline"] is None and not u["end_marker"] and p["end_marker"] and not u["nested"]
                and HEREWITH.search(" ".join(norm(x) for x in lines[p["start"]:p["end"]]))):
            p["end"] = u["end"]
            p["attachments"] += 1
            continue
        merged.append(u)
    return merged


# ----------------------------------------------------------------------------- dating and describing a document

BY_DIRECTION = re.compile(r"(?i)by\s+(?:order|direction|command)\s+of\s+the\s+President|by\s+the\s+President\s*:|the\s+President\s+(?:directs|orders|is\s+pleased|has\s+directed)|"
                          r"by\s+the\s+President'?s?\s+(?:direction|order)|in\s+compliance\s+with\s+the\s+(?:instructions|orders?)\s+of\s+the\s+President")
QUOTED_ORDER = re.compile(r"(?i)following\s+Executive\s+order\s+(?:was|has\s+been)\s+(?:issued|made|promulgated)[^:]{0,100}:\s*$")


def date_match_iso(m, y=4, mo=2, d=3):
    return iso(m.group(y), m.group(mo), m.group(d))


def date_document(lines, unit, sig):
    """(date, date_from, dateline date, approval date, all datelines). The approval date wins: a regulation dated by
    its Department takes effect when the President approves it. The first date in the body is never used
    ('approved January 16, 1883' is the Civil Service Act, cited in dozens of orders)."""
    text = [norm(l).strip() for l in lines]
    approval = ""
    for l in reversed(text[-8:]):
        m = APPROVED.match(l)
        if m:
            approval = date_match_iso(m, 3, 1, 2)
            break
    if not approval:
        for c, m in unit.get("closings", []):
            approval = date_match_iso(m)
    if not approval:
        for k in range(max(0, len(text) - 3), len(text)):
            m = re.match(r"^\s*" + MONTH_RE + r"\s*" + DAY_RE + r"\s*,\s*(1[789]\d\d)\s*\.\s*(.*)$", text[k])
            if m and (sig.search(m.group(4) or "") or (k + 1 < len(text) and sig.search(text[k + 1]))):
                approval = date_match_iso(m, 3, 1, 2)  # "APRIL 3 , 1879 . R. B. HAYES ."
    opening = ""
    if unit.get("dateline") is not None:
        m = DATELINE.match(norm(unit["lines_all"][unit["dateline"]]).strip())
        if m:
            opening = date_match_iso(m)
    if not opening:
        for k, l in enumerate(text[:10]):
            m = DATELINE.match(l)
            if m and (m.group(1) or k == 0 or caps(l)):
                opening = date_match_iso(m)
                break
    alld = []
    for k, l in enumerate(text):
        m = DATELINE.match(l)
        if m and (m.group(1) and (PLACE_WORD.search(m.group(1)) or caps(m.group(1))) or caps(l)):
            d = date_match_iso(m)
            if d and d not in alld:
                alld.append(d)
    if approval:
        return approval, "approval", opening, approval, alld
    if opening:
        return opening, "dateline", opening, "", alld
    for l in text[:5]:
        m = LETTERHEAD.search(l)
        if m:
            return date_match_iso(m, 3, 1, 2), "dept_dateline", "", "", alld
    joined = re.sub(r"\[\s*SEAL\s*\.?\s*\]", " ", re.sub(r"\bist\b", "1st", " ".join(text)))
    days = list(THIS_DAY.finditer(joined))
    if days:
        m = days[-1]
        return iso(m.group(3), m.group(2), m.group(1)), "day_of_clause", "", "", alld
    return "", "", "", "", alld


def describe(lines, sig):
    body = " ".join(norm(l).strip() for l in lines)
    top = " ".join(norm(l).strip() for l in lines[:6])
    if sig.search(body) or any(sig.search(norm(l)) for l in lines):
        signer = "president"
    elif BY_DIRECTION.search(body):
        signer = "by_direction_of_president"
    else:
        signer = "department_or_other"
    if re.search(r"(?i)GENERAL\s+(?:COURT\s*-?\s*MARTIAL\s+)?ORDERS?\s*,?\s*NO", top):
        form = "general_orders"
    elif re.search(r"(?i)SPECIAL\s+ORDERS?\s*,?\s*NO", top):
        form = "special_orders"
    elif re.search(r"(?i)\bCIRCULAR\b", top):
        form = "circular"
    elif re.search(r"(?i)\bANNOUNCEMENT\b", top):
        form = "announcement"
    elif re.search(r"(?i)(?:MY\s+DEAR\s+SIR|\bSIR\s*:|GENTLEMEN\s*:|obedient\s+servant|respectfully\s*,|Yours\s*,?\s*truly)", body[:3000]):
        form = "letter"
    elif re.search(r"(?i)To\s+all\s+(?:who|whom)", body[:400]):
        form = "commission_or_warrant"
    elif re.search(r"(?i)\bRULES?\b|\bREGULATIONS\b|\bCLASSIFICATION\b", top):
        form = "rules_or_regulations"
    else:
        form = "order"
    title = []
    for l in lines:
        s = norm(l).strip()
        if OFFICE.match(s) or DATELINE.match(s) or sig.search(s) or s.startswith("[From"):
            break
        if (is_title(s) or caps(s)) and len(title) < 8:
            title.append(clean(s))
        else:
            break
    return signer, form, clean(" ".join(title))[:160]


# ----------------------------------------------------------------------------- one volume's documents

def volume_documents(vol, pages, pm):
    """All documents of a volume: every unit of its executive-order sections, orders quoted in messages, and the
    configured documents that have no dateline of their own."""
    stream, dropped = body_stream(vol, pages, pm)
    secs = find_sections(vol, stream)
    docs = []

    def add(span, unit, section, kind, sig):
        lines = [x[2] for x in span]
        unit = dict(unit, lines_all=lines) if "lines_all" not in unit else unit
        date, date_from, opening, approval, alld = date_document(lines, dict(unit, lines_all=lines), sig)
        signer, form, title = describe(lines, sig)
        words = len(" ".join(lines).split())
        is_order = words >= 15 and bool(date or unit.get("end_marker") or words >= 150) and kind != "residue"
        if kind == "unit" and not is_order:
            kind = "residue"
        weak = []
        if not date:
            weak.append("undated")
        if kind == "unit" and not unit.get("end_marker"):
            weak.append("no_signature_found")
        if len(lines) > 300:
            weak.append("over_300_lines")
        if unit.get("nested"):
            weak.append("printed_inside_another_document")
        if kind in ("in_message", "configured"):
            weak.append(kind)
        if date_from in ("day_of_clause", "dept_dateline"):
            weak.append("date_from_" + date_from)
        docs.append({
            "volume": vol["key"], "section": section["name"], "section_printed_start": section["printed_start"],
            "kind": "order" if kind == "unit" else kind, "is_order": is_order,
            "date": date, "date_from": date_from, "date_dateline": opening, "date_approval": approval,
            "datelines_all": "|".join(alld), "pdf_first": span[0][0], "pdf_last": span[-1][0],
            "printed_first": span[0][1], "printed_last": span[-1][1], "lines": lines, "n_lines": len(lines), "words": words,
            "signer": signer, "form": form, "title": title,
            "first_line": clean(lines[0])[:120] if lines else "", "last_line": clean(lines[-1])[:120] if lines else "",
            "nested": bool(unit.get("nested")), "attachments": unit.get("attachments", 0),
            "end_marker": bool(unit.get("end_marker")),
            "confidence": "high" if not weak and is_order else "medium", "weak": weak})

    for s in secs:
        if s["end"] <= s["start"]:
            continue
        sig = sig_regex(vol, s["printed_start"])
        if s["kind"] == "orders":
            seg = split_runs(stream[s["start"]:s["end"]])
            lines = [x[2] for x in seg]
            for u in segment(vol, lines, sig):
                add(seg[u["start"]:u["end"]], dict(u, lines_all=lines[u["start"]:u["end"]],
                                                    dateline=None if u["dateline"] is None else u["dateline"] - u["start"],
                                                    closings=[(c - u["start"], m) for c, m in u["closings"]]), s, "unit", sig)
        else:
            # an order quoted in full inside a message: "the following Executive order was issued on the 4th day of September, 1890:"
            seg = stream[s["start"]:s["end"]]
            for k in range(len(seg)):
                window = " ".join(norm(x[2]).strip() for x in seg[max(0, k - 2):k + 1])
                if not QUOTED_ORDER.search(window):
                    continue
                end = next((t for t in range(k + 1, min(len(seg), k + 120)) if sig.search(norm(seg[t][2]))), None)
                if end is None:
                    continue
                span = seg[k + 1:end + 1]
                m = THIS_DAY.search(window) or re.search(MONTH_RE + r"\s*" + DAY_RE + r"\s*,\s*(1[789]\d\d)", window)
                add(span, {"end_marker": True}, s, "in_message", sig)
                d = docs[-1]
                if m:
                    d["date"] = iso(m.group(3), m.group(2), m.group(1)) if m.re is THIS_DAY else iso(m.group(3), m.group(1), m.group(2))
                    d["date_from"] = "message_introduction"
                    d["weak"] = [w for w in d["weak"] if w != "undated"]
                d["intro"] = clean(window)[-200:]
                d["note"] = "quoted in a message; the message goes on after the order, so the end of the order is not marked"
    for x in vol.get("extra_documents", []):
        sig = sig_regex(vol, x["printed"])
        idx = [i for i, (pdf, pr, l) in enumerate(stream) if pr == x["printed"] and re.search(x["start_regex"], norm(l))]
        if not idx:
            docs.append({"volume": vol["key"], "kind": "configured_not_found", "note": x["note"]})
            continue
        a = idx[0]
        b = next((t for t in range(a + 1, min(len(stream), a + 600)) if re.search(x["end_regex"], norm(stream[t][2]))), None)
        if b is None:
            docs.append({"volume": vol["key"], "kind": "configured_not_found", "note": x["note"]})
            continue
        sec = next((s for s in secs if s["start"] <= a < s["end"]), {"name": "", "printed_start": x["printed"]})
        add(stream[a:b], {"end_marker": False}, sec, "configured", sig)
        d = docs[-1]
        d["date"], d["date_from"], d["note"] = x["date"], "configured", x["note"]
        d["weak"] = [w for w in d["weak"] if w != "undated"]
    for a, b in zip(docs, docs[1:]):
        if (a.get("nested") and b.get("kind") == "order" and b.get("lines") and not b.get("date")
                and re.match(r"^\s*(?:II|III|IV|V|VI)\s*\.", norm(b["lines"][0]))):
            b["kind"], b["is_order"], b["confidence"] = "continuation", False, ""
            b["note"] = "a later paragraph of the General Orders that printed the order before it; not an order of its own"
    docs = [d for d in docs if d.get("kind") != "configured_not_found"] + [d for d in docs if d.get("kind") == "configured_not_found"]
    n = 0
    for d in docs:
        if "lines" not in d:
            continue
        n += 1
        d["doc_id"] = "%s-%03d" % (vol["key"], n)
        if d["kind"] != "order" or not d["is_order"] or d["weak"]:
            d["confidence"] = "medium" if d["is_order"] else ""
    return docs, secs, stream, dropped


# ----------------------------------------------------------------------------- the WPA and Lord lists

# "VI R 122"; the OCR once reads "VII E 218" for EO 9
WPA_CITE = re.compile(r"(?<![IVXLA-Za-z])(VIII|VII|VI|IX|X)\s*[RE]\b\.?\s*(\d{1,3})(?:\s*-\s*(\d{1,3}))?")
LORD_NORM = re.compile(r"[RrKk]ich\s*-?\s*a?\s*r\s*-?\s*[a-z]{0,2}\s*-?\s*son")
LORD_CITE = re.compile(r"(?<![A-Za-z])(VIII|VII|VI|IX|IV|V|X|III|II|I)\s*\.?\s*Richardson\s*\.?\s*,?\s*(\d{1,3})(?:\s*-\s*(\d{1,3}))?")
WPA_SUB = re.compile(r"(?<![\w.\[])(\d{1,4}(?:-\d{1,4})?(?:\s*,\s*\d{1,4})*(?:-\d{1,4})?)\s*:\s*\*?\s*"
                     r"(Jan|Feb|Mar|Apr|May|June|July|Aug|Sept|Oct|Nov|Dec)\.?\s*(\d{1,2})")


def md_iso(year, md):
    m = re.match(r"\s*([A-Za-z]+)\.?\s*(\d{1,2})\b", md or "")
    if not (m and str(year).isdigit()):
        return ""
    k = m.group(1).lower()
    mo = SHORT_NO.get(k) or SHORT_NO.get(k[:4]) or SHORT_NO.get(k[:3])
    day = int(m.group(2))
    return "%s-%02d-%02d" % (year, mo, day) if mo and 1 <= day <= 31 else ""


def expand_label(label):
    """'36, 37' -> 36, 37; '40-42' -> 40, 41, 42; '28-1' (b < a) -> the suffix order 28-1; '92-92-3' -> 92, 92-1 .. 92-3."""
    ids = []
    for part in re.split(r"\s*,\s*", label):
        nums = part.split("-")
        if len(nums) == 1:
            ids.append(nums[0])
        elif len(nums) == 2:
            a, b = int(nums[0]), int(nums[1])
            ids += ["%d-%d" % (a, b)] if b < a else [str(x) for x in range(a, b + 1)]
        elif len(nums) == 3:
            a = int(nums[0])
            ids += [str(a)] + ["%d-%d" % (a, k) for k in range(1, int(nums[2]) + 1)]
    return ids


def wpa_items(rows):
    """Numbered entries, with the parsed rows that merged several entries ('28-1: Jan. 30 ...') split again.
    A split-off entry carries its own month and day; its year is the parent row's year, flagged as inherited."""
    out = []
    for r in rows:
        text, year = r["text"], r["year"]
        cuts = list(WPA_SUB.finditer(text))
        segs, prev, head = [], 0, (r["number"] + (r["suffix"] or ""), r["month_day"])
        for m in cuts:
            segs.append((head, text[prev:m.start()]))
            head, prev = (m.group(1), "%s %s" % (m.group(2), m.group(3))), m.end()
        segs.append((head, text[prev:]))
        seen = set()
        for k, ((label, md), seg) in enumerate(segs):
            ids = [label] if k == 0 else expand_label(label)
            cits = [(m.group(1), int(m.group(2)), int(m.group(3)) if m.group(3) else None) for m in WPA_CITE.finditer(seg)]
            seen.update((v, p) for v, p, _ in cits)
            for i in ids:
                out.append({"list": "WPA numbered", "entry": "EO:" + i, "row": r["id"], "year": year, "iso": md_iso(year, md),
                            "summary": clean(seg), "cits": cits, "split": k > 0, "found_in": "text"})
        head_item = next(o for o in out if o["row"] == r["id"] and not o["split"])
        own = {(v, p) for v, p, _ in head_item["cits"]}
        for m in WPA_CITE.finditer(r.get("citations_joined", "")):
            k_ = (m.group(1), int(m.group(2)))
            if k_ in seen and k_ not in own:
                holder = next((o["entry"] for o in out if o["row"] == r["id"] and o["split"] and k_ in {(v, q) for v, q, _ in o["cits"]}), "")
                head_item.setdefault("moved", []).append((m.group(1), int(m.group(2)), holder))
        # a citation the parser put in citations_joined but that is not in any text segment belongs to the row's head entry
        for m in WPA_CITE.finditer(r.get("citations_joined", "")):
            key = (m.group(1), int(m.group(2)))
            if key not in seen:
                head_item = next(o for o in out if o["row"] == r["id"] and not o["split"])
                head_item["cits"].append((m.group(1), int(m.group(2)), int(m.group(3)) if m.group(3) else None))
                head_item["found_in"] = "citations_joined"
                seen.add(key)
    return out


def lord_items(rows):
    """Unnumbered entries citing Richardson. Diacritics and OCR ('Richarăson', 'kichardson') are folded first. A parsed
    row sometimes swallows the previous entry ('<entry A> ... IX Richardson 612 <entry B>'): the summary is split after
    every citation in it, and an earlier piece carries no date of its own (the row's date belongs to its last entry)."""
    out = []
    for r in rows:
        summ = LORD_NORM.sub("Richardson", fold(clean(r["summary"])))
        cj = LORD_NORM.sub("Richardson", fold(r["citations_joined"] + " ; " + r.get("citation_text", "")))
        row_cits = list(dict.fromkeys((m.group(1), int(m.group(2)), int(m.group(3)) if m.group(3) else None) for m in LORD_CITE.finditer(cj)))
        emb = list(LORD_CITE.finditer(summ))
        if not row_cits and not emb:
            continue
        iso_ = md_iso(r["year"], r["date"]) if r["date"] else ""
        pieces, last = [], 0
        for m in emb:
            pieces.append((summ[last:m.end()], (m.group(1), int(m.group(2)), int(m.group(3)) if m.group(3) else None)))
            last = m.end()
        tail = summ[last:].strip()
        has_tail = len(tail) > 40  # text after the last citation in the summary: the row's own entry
        items = [(txt, c, "summary") for txt, c in pieces]
        emb_keys = {(c[0], c[1]) for _, c in pieces}
        rest = [c for c in row_cits if (c[0], c[1]) not in emb_keys]
        if not rest and has_tail and pieces:
            rest = row_cits  # "<entry A> IX Richardson 612 <entry B>" with B's citation, the same page, in the citation column
        items += [(tail if has_tail else summ, c, "citations") for c in rest]
        split = len(items) > 1
        for k, (txt, c, src) in enumerate(items):
            own_date = src == "citations" or (k == len(pieces) - 1 and not has_tail and not rest)
            out.append({"list": "Lord unnumbered", "entry": "Lord:" + r["seq"] + (chr(97 + k) if split else ""), "row": r["seq"],
                        "year": r["year"], "iso": iso_ if own_date else "", "pairing": r["pairing"], "summary": txt.strip(),
                        "cits": [c], "split": split, "found_in": src, "lord_page": r["page"]})
    return out


# ----------------------------------------------------------------------------- matching a citation to a document

STOP = set("the of and to in on for by a an as be is are was from that with at or this its their all any said rule rules "
           "civil service amended amend include included section clause hereby following which shall order orders executive "
           "president united states department".split())
RULE_KEY = re.compile(r"\b(Special\s+Departmental|Special\s+Customs|Special\s+Indian|Departmental|Customs|Postal|Railway\s+Mail|Indian|General|"
                      r"Internal\s*-?\s*Revenue|Government\s+Printing\s+Office)\s+Rule\s*(?:No\.?\s*)?([IVX]+|\d+)\b", re.I)
ROMAN_OF = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V", "6": "VI", "7": "VII", "8": "VIII", "9": "IX", "10": "X", "11": "XI"}


def toks(s):
    # crude stemming so "fireman"/"firemen" and "engravers"/"engraver" meet
    return {re.sub(r"men$", "man", re.sub(r"(?<=[a-z]{3})s$", "", w)) for w in re.findall(r"[a-z]{4,}", fold(s).lower()) if w not in STOP}


def rule_keys(text):
    return {(re.sub(r"\s+", " ", m.group(1).lower()), ROMAN_OF.get(m.group(2), m.group(2).upper()))
            for m in RULE_KEY.finditer(re.sub(r"\s+", " ", text))}


class Matcher:
    """Resolves a citation (printed page, date or '', summary) to the documents of one volume."""

    def __init__(self, vol, docs, page_range):
        self.vol, self.lo, self.hi = vol, page_range[0], page_range[1]
        self.docs = [d for d in docs if d.get("is_order")]
        self.tok = {d["doc_id"]: toks(" ".join(d["lines"])) for d in self.docs}
        self.df = collections.Counter()
        for t in self.tok.values():
            self.df.update(t)

    def dates(self, d):
        return ({d["date"], d["date_dateline"], d["date_approval"]} | set(d["datelines_all"].split("|"))) - {""}

    def score(self, summary, d):
        """Overlap of summary words with the document, weighted by rarity across the volume's documents; a large bonus
        when the summary names the same rule the document's opening lines amend; long documents are penalised, or the
        1896 codification would win every tie."""
        st, dt = toks(summary), self.tok[d["doc_id"]]
        if not dt:
            return 0.0
        raw = sum(math.log((1 + len(self.docs)) / (1 + self.df[w])) for w in st & dt)
        raw /= 1 + max(0.0, math.log(len(dt) / 150))
        head = " ".join(norm(x) for x in d["lines"][:6])
        return raw + 12.0 * len(rule_keys(summary) & rule_keys(head))

    def on_page(self, p):
        return [d for d in self.docs if d["printed_first"] <= p <= d["printed_last"]]

    def resolve(self, p, iso_, summary, year=""):
        """(status, method, [doc ids], note). status is match, ambiguous or unmatched; nothing is forced."""
        if not (self.lo <= p <= self.hi):
            return "unmatched", "page_outside_volume", [], "printed pages %d-%d" % (self.lo, self.hi)
        cands = self.on_page(p)
        if iso_:
            same = [d for d in cands if iso_ in self.dates(d)]
            if len(same) == 1:
                return "match", "date_and_page", [same[0]["doc_id"]], ""
            if len(same) > 1:
                ranked = sorted(same, key=lambda d: -self.score(summary, d))
                sc = [round(self.score(summary, d), 1) for d in ranked]
                if sc[0] > sc[1] * 1.2 + 0.5:
                    return "match", "date_page_and_subject", [ranked[0]["doc_id"]], "%d documents of that date on the page; subject %s vs %s" % (len(same), sc[0], sc[1])
                full = [d for d in same if not (d["last_line"].rstrip().endswith(":") and d["n_lines"] <= 12)]
                if len(full) == 1:
                    return "match", "date_page_not_wrapper", [full[0]["doc_id"]], "%d documents of that date on the page; the other is a General Orders wrapper that prints it" % len(same)
                pres = [d for d in full if d["signer"] == "president"]
                if len(pres) == 1:
                    return "match", "date_page_presidential", [pres[0]["doc_id"]], "%d documents of that date on the page; only one is signed by the President" % len(same)
                return "ambiguous", "same_date_same_page", [d["doc_id"] for d in same], "%d documents of that date; the subject does not separate them" % len(same)
            near = [d for d in self.docs if iso_ in self.dates(d) and (abs(d["printed_first"] - p) <= 1 or abs(d["printed_last"] - p) <= 1)]
            if len(near) == 1:
                return "match", "date_adjacent_page", [near[0]["doc_id"]], "the document of that date is on pp. %s-%s" % (near[0]["printed_first"], near[0]["printed_last"])
            elsewhere = [d for d in self.docs if iso_ in self.dates(d)]
            if len(elsewhere) == 1:
                return "match", "date_on_other_page", [elsewhere[0]["doc_id"]], "cited p. %d; the only document of that date is on pp. %s-%s" % (p, elsewhere[0]["printed_first"], elsewhere[0]["printed_last"])
        if not cands:
            return "unmatched", "no_order_on_page", [], "no document of an executive-order section on p. %d" % p
        ranked = sorted(cands, key=lambda d: -self.score(summary, d))
        sc = [round(self.score(summary, d), 1) for d in ranked] + [0.0]
        yr = str(iso_[:4] if iso_ else year or "")
        if sc[0] >= 4 and sc[0] >= sc[1] * 1.3 + 1:
            d0 = ranked[0]
            if iso_ and d0["date"] and d0["date"][:4] != iso_[:4]:
                if d0["date"][5:] == iso_[5:]:
                    return "match", "subject_list_year_wrong", [d0["doc_id"]], "month and day agree; the volume prints %s, the list %s" % (d0["date"], iso_)
                return "ambiguous", "subject_but_year_conflict", [d0["doc_id"]], "document dated %s, list %s; subject %s vs %s" % (d0["date"], iso_, sc[0], sc[1])
            if iso_:
                return "match", "subject_date_differs", [d0["doc_id"]], "list %s, document %s; subject %s vs %s" % (iso_, d0["date"] or "undated", sc[0], sc[1])
            return "match", "subject_on_page", [d0["doc_id"]], "subject %s vs %s" % (sc[0], sc[1])
        if yr.isdigit() and not iso_:
            same_year = [d for d in cands if d["date"][:4] == yr]
            if len(same_year) == 1:
                return "match", "only_order_of_that_year_on_page", [same_year[0]["doc_id"]], ""
        if iso_:
            return "unmatched", "date_not_found", [], "documents on the page: " + "; ".join("%s %s" % (d["doc_id"], d["date"] or "undated") for d in cands)
        return "ambiguous", "subject_does_not_separate", [d["doc_id"] for d in ranked[:4]], "subject scores %s" % sc[:3]


# ----------------------------------------------------------------------------- census, readiness, outputs

ENDING = re.compile(r"(?i)\b(revoked|revokes|revoke|rescinded|rescinds|rescind|superseded|supersedes|abolished|abolishes|withdrawn|"
                    r"hereby\s+repealed|annulled|suspended|terminated|discontinued|instead\s+of|amended|extended|modified|restored)\b")
COMPILATION_NOTE = ("Richardson's Compilation of the Messages and Papers of the Presidents is a printed compilation (GPO 1896-99) "
                    "transcribed from department records and newspapers; it is NOT the signed original.")


def load_census(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return {r["id"].upper(): r for r in csv.DictReader(fh)}


def load_csv(path):
    with open(path, encoding="utf-8-sig", newline="", errors="replace") as fh:
        return list(csv.DictReader(fh))


def write_csv(path, rows, fields):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def census_state(census, cid, date):
    c = census.get(cid.upper())
    if not c:
        return "NOT_IN_CENSUS", ""
    de = (c.get("date_effective") or "").strip()
    if not de:
        return "census_date_blank", de
    if not date:
        return "census_has_date_volume_undated", de
    if re.fullmatch(r"\d{4}", de):
        return ("census_year_only" if de == date[:4] else "YEAR_CONFLICT"), de
    return ("census_exact_date" if de == date else ("DATE_CONFLICT" if de[:4] == date[:4] else "YEAR_CONFLICT")), de


def eo_key(cid):
    m = re.match(r"EO:(\d+)(?:-(\d+))?([A-Z]?)", cid.upper())
    return (int(m.group(1)), int(m.group(2) or 0), m.group(3)) if m else (10 ** 9, 0, cid)


def slug(s, n=48):
    s = re.sub(r"[^a-z0-9]+", "-", fold(s).lower()).strip("-")
    return s[:n].rstrip("-") or "untitled"


def check_text(job_dir, rel, want):
    got = sha256_bytes((job_dir / rel).read_bytes())
    if got != want:
        raise SystemExit(f"{rel}: sha256 {got} does not match PROVENANCE.json")
    return got


def pdf_status(repo, vol):
    pdf = repo / vol["pdf"]
    if not pdf.exists():
        return "pdf_not_checked_out"
    with open(pdf, "rb") as fh:
        head = fh.read(64)
    if head.startswith(b"version https://git-lfs"):
        return "pdf_is_lfs_pointer_text_layer_hash_verified"
    h = hashlib.sha256()
    with open(pdf, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    if h.hexdigest() != vol["pdf_sha256"]:
        raise SystemExit(f"{vol['pdf']}: sha256 does not match PROVENANCE.json")
    return "match"


DATE_ONLY_MIN_SCORE = 4.0


def run_volume(vol, repo, job_dir, out, census, readiness, witems, litems, lists_present):
    key, roman = vol["key"], vol["volume"]
    text_sha = check_text(job_dir, vol["text"], vol["text_sha256"])
    raw_sha = check_text(job_dir, vol["raw_text"], vol["raw_text_sha256"])
    pdf_check = pdf_status(repo, vol)
    pages, rejoined = best_layer(load_pages(job_dir / vol["text"]), load_pages(job_dir / vol["raw_text"]))
    pm, pmstat = page_map(vol, pages)
    if pmstat["heads_read"] == 0 or pmstat["heads_agree"] / pmstat["heads_read"] < 0.99:
        raise SystemExit(f"{key}: only {pmstat['heads_agree']} of {pmstat['heads_read']} running heads agree with the page offsets")
    docs, secs, stream, dropped = volume_documents(vol, pages, pm)
    order_secs = [s for s in secs if s["kind"] == "orders"]
    got = [[s["printed_start"], s["printed_end"]] for s in order_secs]
    want = vol["contents_order_sections"]
    if [g[0] for g in got] != [w[0] for w in want]:
        raise SystemExit(f"{key}: executive-order sections start on {[g[0] for g in got]}, the contents say {[w[0] for w in want]}")
    by_id = {d["doc_id"]: d for d in docs}
    orders = [d for d in docs if d["is_order"]]
    lo, hi = min(pm.values()), max(pm.values())
    matcher = Matcher(vol, docs, (lo, hi))
    y0, y1 = vol["years"]

    # ---- every WPA and Lord citation into this volume
    cites = []
    for it in witems + litems:
        for v, p, p2 in it["cits"]:
            if v != roman:
                continue
            row = {"volume": key, "list": it["list"], "entry": it["entry"], "list_row": it["row"], "entry_date": it["iso"],
                   "entry_year": it["year"], "cited": f"{roman} {'R' if it['list'].startswith('WPA') else 'Richardson'} {p}" + (f"-{p2}" if p2 else ""),
                   "printed_page": p, "pdf_page": next((q for q, r in pm.items() if r == p), ""), "found_in": it["found_in"],
                   "split_from_merged_row": "yes" if it["split"] else "", "summary": it["summary"][:300]}
            yr = int(it["year"]) if str(it["year"]).isdigit() else None
            if yr is not None and not (y0 - 1 <= yr <= y1 + 1):
                st, how, ids, note = ("unmatched", "entry_year_outside_volume", [],
                                      f"the entry's year {yr} is outside this volume ({y0}-{y1}); '{roman} R' is probably a misread "
                                      "of another source (for example 'I IR', Executive Orders Relating to Indian Reservations vol. I)")
            else:
                st, how, ids, note = matcher.resolve(p, it["iso"], it["summary"], it["year"])
                for q in range(p + 1, (p2 or p) + 1):
                    if st == "match":
                        break
                    st, how, ids, note = matcher.resolve(q, it["iso"], it["summary"], it["year"])
                if not (st == "match" and how.startswith("date")) and it["split"] and it["iso"] and it["list"].startswith("WPA"):
                    nxt = str(int(it["iso"][:4]) + 1) + it["iso"][4:]
                    st2, how2, ids2, note2 = matcher.resolve(p, nxt, it["summary"], it["year"])
                    if st2 == "match" and how2.startswith("date"):
                        st, how, ids = st2, how2 + "_year_after_parent_row", ids2
                        note = f"dated {nxt}: the split-off entry inherited its parent row's year {it['iso'][:4]}"
            row.update({"status": st, "method": how, "doc_ids": "|".join(ids), "doc_dates": "|".join(by_id[i]["date"] for i in ids),
                        "doc_pages": "|".join("%s-%s" % (by_id[i]["printed_first"], by_id[i]["printed_last"]) for i in ids), "note": note})
            cites.append(row)

    # ---- numbered orders of the volume's years that the WPA list gives no Richardson citation for: date-only candidates
    cited_entries = {c["entry"] for c in cites}
    date_only = []
    for it in witems:
        yr = int(it["year"]) if str(it["year"]).isdigit() else None
        if it["entry"] in cited_entries or yr is None or not (y0 <= yr <= y1) or not it["iso"]:
            continue
        if any(v != roman for v, _, _ in it["cits"]) and it["cits"]:
            continue  # cited to another Richardson volume
        same = sorted([d for d in orders if it["iso"] in matcher.dates(d)], key=lambda d: -matcher.score(it["summary"], d))
        sc = [round(matcher.score(it["summary"], d), 1) for d in same] + [0.0]
        if same and sc[0] >= DATE_ONLY_MIN_SCORE and sc[0] > sc[1] * 1.2 + 0.5:
            st, ids = "match", [same[0]["doc_id"]]
        elif same:
            st, ids = "ambiguous", [d["doc_id"] for d in same]
        else:
            st, ids = "unmatched", []
        if st == "match":
            note = "the WPA entry cites no printed source in Richardson; matched on the date and the subject (score %s vs %s)" % (sc[0], sc[1])
        elif same:
            note = ("the WPA entry cites no printed source in Richardson; %d orders of that date, and the subject does not single one "
                    "out (scores %s)" % (len(same), sc[:3]))
        else:
            note = "the WPA entry cites no printed source in Richardson and no order of that date is printed here"
        date_only.append({"volume": key, "list": "WPA numbered (no Richardson citation)", "entry": it["entry"], "list_row": it["row"],
                          "entry_date": it["iso"], "entry_year": it["year"], "cited": "", "printed_page": "", "pdf_page": "",
                          "found_in": "", "split_from_merged_row": "yes" if it["split"] else "", "summary": it["summary"][:300],
                          "status": st, "method": "date_only_no_citation", "doc_ids": "|".join(ids),
                          "doc_dates": "|".join(by_id[i]["date"] for i in ids),
                          "doc_pages": "|".join("%s-%s" % (by_id[i]["printed_first"], by_id[i]["printed_last"]) for i in ids),
                          "note": note})

    # ---- per document: which list entries point at it
    wpa_of, lord_of, dateonly_of = collections.defaultdict(list), collections.defaultdict(list), collections.defaultdict(list)
    for c in cites:
        if c["status"] != "match":
            continue
        for i in c["doc_ids"].split("|"):
            (wpa_of if c["list"].startswith("WPA") else lord_of)[i].append(c["entry"])
    for c in date_only:
        if c["status"] == "match":
            dateonly_of[c["doc_ids"]].append(c["entry"])

    texts = out / "texts"
    texts.mkdir(parents=True, exist_ok=True)
    rows, fragments, leads, endings = [], [], [], []
    for d in docs:
        cited_ids = set(wpa_of.get(d["doc_id"], []))
        wids = sorted(cited_ids | set(dateonly_of.get(d["doc_id"], [])), key=eo_key)
        lseq = sorted(set(lord_of.get(d["doc_id"], [])), key=lambda s: [int(x) if x.isdigit() else x for x in re.findall(r"\d+|[a-z]", s)])
        body = "\n".join(d["lines"]).strip() + "\n"
        bsha = sha256_bytes(body.encode("utf-8"))
        tpath = ""
        if d["is_order"]:
            if wids:
                name = "EO_" + "_".join(w[3:] for w in wids)
            else:
                name = f"{d['date'] or 'undated'}_{slug(d['title'] or d['first_line'])}_{d['doc_id']}"
            tpath = f"texts/{key}/{name}.txt"
            (texts / key).mkdir(exist_ok=True)
            pp = "PDF pages %s-%s" % (d["pdf_first"], d["pdf_last"])
            pr = "printed pages %s-%s" % (d["printed_first"], d["printed_last"])
            header = (f"# {d['doc_id']}: {d['title'] or d['first_line']}" + (f" [{', '.join(wids)}]" if wids else "") + "\n"
                      f"# Source: {vol['title']} ({vol['published']}); {vol['digitized_by']}\n"
                      f"# PDF: {vol['pdf']} sha256 {vol['pdf_sha256']}\n"
                      f"# {pp}; {pr}; section {d['section']}; date {d['date'] or 'not found'} ({d['date_from'] or 'none'}); "
                      f"confidence {d['confidence']}" + (f" ({', '.join(d['weak'])})" if d["weak"] else "") + "\n"
                      f"# {COMPILATION_NOTE}\n"
                      f"# Text: OCR text layer of the scan ({vol['extractor']}); running heads, sheet signatures and specks removed. "
                      f"Boundaries are machine-found and not human-verified. Body sha256 {bsha}\n\n")
            (out / tpath).write_text(header + body, encoding="utf-8", newline="\n")
        states = []
        for w in wids:
            st, de = census_state(census, w, d["date"])
            rd = readiness.get(w.upper(), {})
            states.append({"id": w, "state": st, "census": de, "provisional_status": rd.get("provisional_status", ""),
                           "original_text": rd.get("step_original_text", "")})
        row = {"doc_id": d["doc_id"], "volume": key, "kind": d["kind"], "is_order": "yes" if d["is_order"] else "no",
               "date": d["date"], "date_from": d["date_from"], "date_dateline": d["date_dateline"], "date_approval": d["date_approval"],
               "datelines_all": d["datelines_all"], "pdf_pages": "%s-%s" % (d["pdf_first"], d["pdf_last"]),
               "printed_pages": "%s-%s" % (d["printed_first"], d["printed_last"]), "section": d["section"],
               "section_printed_start": d["section_printed_start"], "signer": d["signer"], "form": d["form"], "title": d["title"],
               "first_line": d["first_line"], "last_line": d["last_line"], "lines": d["n_lines"], "words": d["words"],
               "printed_inside_another": "yes" if d["nested"] else "", "attachments_merged": d["attachments"] or "",
               "wpa_ids": "|".join(wids), "lord_entries": "|".join(lseq),
               "wpa_date_only_candidates": "|".join(dateonly_of.get(d["doc_id"], [])),
               "census": "|".join(f"{s['id']}:{s['state']}" for s in states),
               "provisional_status": "|".join(f"{s['id']}:{s['provisional_status']}" for s in states if s["provisional_status"]),
               "original_text_step_before": "|".join(f"{s['id']}:{s['original_text']}" for s in states if s["original_text"]),
               "confidence": d["confidence"], "needs_page_check": "yes" if d["is_order"] and d["confidence"] != "high" else "",
               "weak_points": "|".join(d["weak"]), "note": d.get("note", ""), "text_path": tpath, "text_sha256": bsha if tpath else ""}
        rows.append(row)
        page_or_item = f"{vol['short']}, printed pages {d['printed_first']}-{d['printed_last']}, PDF pages {d['pdf_first']}-{d['pdf_last']}"
        for s in states:
            if s["state"] != "NOT_IN_CENSUS":
                fragments.append({
                    "instrument_id": s["id"].upper(), "kind": "original_representation", "produced_by": "richardson-volumes",
                    "confidence_note": (f"Machine location lead, confidence {d['confidence']}"
                                        + (f" ({', '.join(d['weak'])})" if d["weak"] else "") + ". "
                                        + (f"The WPA numbered list cites this page of Richardson vol. {roman} for the order and the cited page "
                                           "prints a document of that date. " if s["id"] in cited_ids else
                                           "The WPA numbered list gives no printed source for the order; this document has its date and "
                                           "shares its subject words, so the identification is a candidate only. ")
                                        + COMPILATION_NOTE + " Text is the scan's OCR layer. Identity, boundaries and wording are NOT "
                                        "human-verified; this is not a legal conclusion."),
                    "data": {"url": vol["handle_url"], "sha256": vol["pdf_sha256"], "page_or_item": page_or_item,
                             "route": "compilation/richardson_messages_and_papers", "source_kind": "printed compilation, not the signed original",
                             "location_confidence": d["confidence"] if s["id"] in cited_ids else "medium",
                             "location_verified": False, "identified_by": "wpa_citation" if s["id"] in cited_ids else "date_and_subject_only",
                             "needs_page_check": d["confidence"] != "high" or s["id"] not in cited_ids, "signing_date": d["date"], "title": d["title"],
                             "text_path": tpath, "text_sha256": bsha, "source_id": f"richardson-volumes:{s['id'].upper()}:{vol['pdf_sha256'][:12]}"},
                    "sources": [{"url": vol["handle_url"], "sha256": vol["pdf_sha256"], "page_or_item": page_or_item}]})
            lead = {"census_year_only": "DATE_FILL", "census_date_blank": "DATE_FILL_census_blank", "YEAR_CONFLICT": "YEAR_CONFLICT",
                    "DATE_CONFLICT": "DATE_CONFLICT", "NOT_IN_CENSUS": "NOT_IN_CENSUS_numbered"}.get(s["state"])
            if lead:
                leads.append({"volume": key, "instrument_id": s["id"].upper(), "lead": lead, "date_in_volume": d["date"],
                              "census_date_effective": s["census"], "doc_id": d["doc_id"], "evidence": page_or_item, "text_path": tpath,
                              "note": "date from " + (d["date_from"] or "none")
                              + ("" if s["id"] in cited_ids else "; identified by date and subject only (the WPA entry cites no page)")})
        if d["is_order"] and not wids and (lseq or d["signer"] != "department_or_other"):
            leads.append({"volume": key, "instrument_id": "", "lead": "NOT_IN_CENSUS_unnumbered", "date_in_volume": d["date"],
                          "census_date_effective": "", "doc_id": d["doc_id"], "evidence": page_or_item, "text_path": tpath,
                          "note": ("Lord " + ", ".join(lseq) if lseq else "cited by neither list") + f"; signer {d['signer']}; {d['title'] or d['first_line']}"[:240]})
        if d["is_order"]:
            for sent in re.split(r"(?<=[.;:])\s+", " ".join(norm(x).strip() for x in d["lines"])):
                m = ENDING.search(sent)
                if m and len(sent) > 25:
                    endings.append({"volume": key, "doc_id": d["doc_id"], "date": d["date"], "wpa_ids": "|".join(wids),
                                    "lord_entries": "|".join(lseq), "verb": m.group(1).lower(), "sentence": clean(sent)[:400],
                                    "printed_pages": "%s-%s" % (d["printed_first"], d["printed_last"]), "text_path": tpath})

    # ---- census side: orders of the volume's years that the census holds but the volume does not show
    matched_ids = {w.upper() for r in rows for w in r["wpa_ids"].split("|") if w}
    matched_ids |= {c["entry"].upper() for c in date_only if c["status"] != "unmatched"}
    wpa_date = {}
    for it in witems:
        if it["iso"] and not it["split"]:
            wpa_date.setdefault(it["entry"].upper(), it["iso"])
        elif it["iso"]:
            wpa_date.setdefault(it["entry"].upper(), it["iso"])
    span_lo, span_hi = vol["span"]
    wpa_cited_here = {c["entry"].upper() for c in cites}
    for cid, c in census.items():
        de = (c.get("date_effective") or "")[:4]
        if not (cid.startswith("EO:") and de.isdigit() and y0 <= int(de) <= y1) or cid in matched_ids:
            continue
        if not re.fullmatch(r"EO:\d+(-\d+)?[A-Z]?", cid):
            continue
        wd = wpa_date.get(cid, "")
        if wd and not (span_lo <= wd <= span_hi):
            continue  # the WPA list dates it outside this volume (an 1897 order of the next President)
        leads.append({"volume": key, "instrument_id": cid, "lead": "IN_CENSUS_NOT_FOUND_IN_VOLUME", "date_in_volume": "",
                      "census_date_effective": c.get("date_effective", ""), "doc_id": "", "evidence": vol["short"], "text_path": "",
                      "note": "the WPA list cites this volume for it but the citation did not resolve" if cid in wpa_cited_here
                      else "the WPA list cites no page of this volume for it; Richardson may not print it"})
    # ---- corrections to the parsed lists
    for c in cites:
        fix = {"entry_year_outside_volume": "WPA parse: citation probably belongs to another source",
               "subject_list_year_wrong": "list year one off: month and day agree with the printed order",
               "date_on_other_page": "cited page differs from the page that prints the order",
               "date_adjacent_page": "cited page is next to the page that prints the order"}.get(c["method"].replace("_year_after_parent_row", ""))
        if c["method"].endswith("_year_after_parent_row"):
            fix = "WPA parse: split-off entry inherited the parent row's year"
        if c["split_from_merged_row"] and c["list"].startswith("Lord") and c["status"] == "match":
            fix = fix or "Lord parse: entry split from a row that swallowed the previous entry"
        if fix:
            leads.append({"volume": key, "instrument_id": c["entry"], "lead": "LIST_PARSE_CORRECTION", "date_in_volume": c["doc_dates"],
                          "census_date_effective": "", "doc_id": c["doc_ids"], "evidence": f"{c['list']} {c['cited']}",
                          "text_path": "", "note": f"{fix}. {c['note']}".strip()[:300]})
    for it in witems:
        for v, p, holder in it.get("moved", []):
            if v == roman:
                leads.append({"volume": key, "instrument_id": it["entry"], "lead": "LIST_PARSE_CORRECTION", "date_in_volume": "",
                              "census_date_effective": census.get(it["entry"].upper(), {}).get("date_effective", ""), "doc_id": "",
                              "evidence": f"WPA numbered list, parsed row {it['row']}", "text_path": "",
                              "note": f"WPA parse: the parsed row lists {v} R {p} under {it['entry']}, but the citation belongs to {holder or 'an entry'} split off from the same row"})
    for c in date_only:
        if c["status"] == "ambiguous" and c["entry"].upper() in census:
            leads.append({"volume": key, "instrument_id": c["entry"].upper(), "lead": "CANDIDATE_TEXT_DATE_ONLY", "date_in_volume": c["doc_dates"],
                          "census_date_effective": census[c["entry"].upper()].get("date_effective", ""), "doc_id": c["doc_ids"],
                          "evidence": f"{vol['short']}, printed pages {c['doc_pages']}", "text_path": "",
                          "note": c["note"]})

    # ---- the cited pages' own text
    pdir = out / "pages" / key
    pdir.mkdir(parents=True, exist_ok=True)
    page_text = collections.defaultdict(list)
    for pdf, pr, l in stream:
        page_text[pr].append(l)
    for c in cites:
        p = c["printed_page"]
        if p in page_text:
            path = f"pages/{key}/p{p:03d}.txt"
            if not (out / path).exists():
                body = "\n".join(page_text[p]).strip() + "\n"
                pdf = c["pdf_page"]
                (out / path).write_text(
                    f"# {vol['short']}, printed page {p} (PDF page {pdf}); {vol['handle_url']}\n# PDF sha256 {vol['pdf_sha256']}\n"
                    f"# OCR text layer, running head removed. {COMPILATION_NOTE}\n# Body sha256 {sha256_bytes(body.encode('utf-8'))}\n\n" + body,
                    encoding="utf-8", newline="\n")
            c["page_text_path"] = path
        else:
            c["page_text_path"] = ""
    for c in date_only:
        c["page_text_path"] = ""

    order_fields = list(rows[0].keys())
    write_csv(out / f"{key}_ORDERS.csv", rows, order_fields)
    st = lambda lst, name: dict(collections.Counter(c[name] for c in lst))
    wc = [c for c in cites if c["list"].startswith("WPA")]
    lc = [c for c in cites if c["list"].startswith("Lord")]
    census_ids = sorted({f["instrument_id"] for f in fragments}, key=eo_key)
    decided = [r for r in rows if r["provisional_status"]]
    summary = {
        "volume": key, "title": vol["title"], "pdf_check": pdf_check, "text_sha256": text_sha, "raw_text_sha256": raw_sha,
        "pages_rejoined_from_pdftotext_raw": len(rejoined), "page_map": {k: v for k, v in pmstat.items() if k != "disagreements"},
        "page_furniture_removed": dropped,
        "order_sections": len(order_secs), "order_sections_printed": got, "order_sections_contents": want,
        "order_section_ends_agree_with_contents": sum(1 for g, w in zip(got, want) if g[1] == w[1]),
        "units": len(docs), "orders": len(orders), "residue_units": sum(1 for d in docs if not d["is_order"]),
        "orders_by_kind": st(orders, "kind"), "orders_by_signer": st(orders, "signer"), "orders_by_form": st(orders, "form"),
        "orders_by_date_from": st(orders, "date_from"), "orders_undated": sum(1 for d in orders if not d["date"]),
        "confidence": st(orders, "confidence"), "orders_printed_inside_another": sum(1 for d in orders if d["nested"]),
        "wpa_citations": len(wc), "wpa_entries_citing": len({c["entry"] for c in wc}), "wpa_status": st(wc, "status"), "wpa_methods": st(wc, "method"),
        "lord_citations": len(lc), "lord_rows_citing": len({c["list_row"] for c in lc}), "lord_status": st(lc, "status"), "lord_methods": st(lc, "method"),
        "wpa_date_only_candidates": st(date_only, "status"),
        "orders_with_wpa_number": sum(1 for r in rows if r["wpa_ids"]),
        "wpa_numbers_located": len({w for r in rows for w in r["wpa_ids"].split("|") if w}),
        "orders_with_lord_entry": sum(1 for r in rows if r["lord_entries"]),
        "unnumbered_orders": sum(1 for r in rows if r["is_order"] == "yes" and not r["wpa_ids"]),
        "unnumbered_orders_cited_by_lord": sum(1 for r in rows if r["is_order"] == "yes" and not r["wpa_ids"] and r["lord_entries"]),
        "orders_cited_by_neither_list": sum(1 for r in rows if r["is_order"] == "yes" and not r["wpa_ids"] and not r["lord_entries"]),
        "census_ids_with_text": len(census_ids), "census_ids": census_ids,
        "decided_orders_with_text": len(decided),
        "decided_orders_original_text_step_open": sum(1 for r in decided if ":open" in r["original_text_step_before"]),
        "fragments": len(fragments), "census_leads": st(leads, "lead"), "ending_leads": len(endings),
        "lists_read": lists_present,
    }
    return summary, cites + date_only, fragments, leads, endings


def run(repo_root, job_dir, out_dir, lists_dir=None):
    repo, job_dir, out = pathlib.Path(repo_root), pathlib.Path(job_dir), pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    prov = json.loads((job_dir / "data" / "PROVENANCE.json").read_text(encoding="utf-8"))
    census = load_census(repo / prov["census"])
    readiness = {}
    rp = repo / prov["readiness"]
    if rp.exists():
        readiness = {r["instrument_id"].upper(): r for r in load_csv(rp)}
    # The parsed WPA lists: the wpa-lists job's output when present, else the committed subset of it (data/lists_subset).
    fb = prov["lists_fallback"]
    candidates = ([("given", pathlib.Path(lists_dir))] if lists_dir else []) + [("wpa-lists output", repo / prov["wpa_lists"])]
    used = next(((how, d) for how, d in candidates if (d / "NUMBERED_ENTRIES.csv").exists() and (d / "UNNUMBERED_ENTRIES.csv").exists()), None)
    if used is None:
        used = ("committed subset (wpa-lists output absent)", job_dir / fb["dir"])
        for name, want in fb["sha256"].items():
            check_text(job_dir, f"{fb['dir']}/{name}", want)
    ld = used[1]
    wpath, lpath = ld / "NUMBERED_ENTRIES.csv", ld / "UNNUMBERED_ENTRIES.csv"
    lists = {"source": used[0], "dir": str(ld), "numbered_sha256": sha256_bytes(wpath.read_bytes()),
             "unnumbered_sha256": sha256_bytes(lpath.read_bytes())}
    witems = wpa_items(load_csv(wpath))
    litems = lord_items(load_csv(lpath))
    summary = {"leads_only": "Nothing is admitted, merged, dated or changed in the census or in any status.",
               "source_note": COMPILATION_NOTE, "census": prov["census"], "readiness_read": rp.exists(),
               "lists": lists, "wpa_entries_parsed": len(witems), "lord_entries_citing_richardson": len(litems), "volumes": []}
    all_cites, all_frag, all_leads, all_end = [], [], [], []
    for vol in prov["volumes"]:
        s, c, f, l, e = run_volume(vol, repo, job_dir, out, census, readiness, witems, litems, lists["source"])
        summary["volumes"].append(s)
        all_cites += c
        all_frag += f
        all_leads += l
        all_end += e
    # citations into Richardson volumes this job does not hold yet
    have = {v["volume"] for v in prov["volumes"]}
    other = collections.Counter()
    for it in witems + litems:
        for v, p, _ in it["cits"]:
            if v not in have:
                other[f"{it['list']}: vol. {v}"] += 1
    summary["citations_to_volumes_not_in_job"] = dict(sorted(other.items()))
    cite_fields = ["volume", "list", "entry", "list_row", "entry_date", "entry_year", "cited", "printed_page", "pdf_page", "status", "method",
                   "doc_ids", "doc_dates", "doc_pages", "note", "found_in", "split_from_merged_row", "summary", "page_text_path"]
    write_csv(out / "CITATIONS.csv", all_cites, cite_fields)
    with open(out / "FRAGMENTS.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for f in all_frag:
            fh.write(json.dumps(f, ensure_ascii=False, sort_keys=True) + "\n")
    write_csv(out / "CENSUS_LEADS.csv", all_leads, ["volume", "instrument_id", "lead", "date_in_volume", "census_date_effective",
                                                     "doc_id", "evidence", "text_path", "note"])
    write_csv(out / "ENDING_LEADS.csv", all_end, ["volume", "doc_id", "date", "wpa_ids", "lord_entries", "verb", "sentence",
                                                   "printed_pages", "text_path"])
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary
