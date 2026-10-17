"""Match the Opus Stage 11 evidence media (PDFs and page images) to orders by content.

Plain-language overview is in README.md. In short:

1. Read every member of OPUS_STAGE11_EVIDENCE_ORIGINALS.zip straight from the
   zip (nothing is unpacked to disk), check its SHA-256 against the Stage 20
   member map, and pull out its text: the PDF text layer first (pypdf), then OCR
   for pages without one, but only when tesseract is installed.
2. Read the Opus case records inside OPUS_STAGE11_FINITE_STATUS_DELTA_COMPLETE.zip
   (evidence.jsonl, status_proposals.jsonl, reviews.jsonl, *.meta.json, the status
   records) and build, per order, its quotes, cited hashes/files/URLs and cited
   Federal Register / Statutes at Large pages.
3. For every (member, order) pair, look for independent signals and grade the pair.

Everything written is a LEAD for human checking, never a legal conclusion.
"""

import bisect
import collections
import csv
import datetime
import hashlib
import io
import json
import logging
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import unicodedata
import zipfile

JOB_NAME = "opus-media-match"
EXTRACTOR_VERSION = "opus-media-match/text-v1"
LEGAL_CUTOFF = "2026-10-14"

RELEASE_DIR = "releases/opus_stage11_complete"
MEDIA_ZIP = RELEASE_DIR + "/OPUS_STAGE11_EVIDENCE_ORIGINALS.zip"
COMPLETE_ZIP = RELEASE_DIR + "/OPUS_STAGE11_FINITE_STATUS_DELTA_COMPLETE.zip"
MEMBER_MAP = "research/stage20/output/OPUS_ORIGINAL_MEDIA_MEMBER_MAP.csv"
INTEGRITY_JSON = "research/stage20/output/OPUS_ORIGINAL_MEDIA_INTEGRITY.json"
FULL_844 = "research/stage20/output/OPUS_FULL_844.jsonl"
NOTE_LEADS = "research/stage20/output/OPUS_NOTE_LEADS.jsonl"
PKG = "OPUS_STAGE11_FINITE_STATUS_DELTA/"
ARCHIVE_ID_PREFIX = "opus_stage11_evidence_originals"

# Signal families. A pair is "unique_supported" when it has a specific verbatim
# quote, or at least two families of which at least one comes from the page text.
CONTENT_FAMILIES = ("eo_number_in_text", "quote_in_text", "citation_in_text")
# cites_same_document: the order's records cite the whole upstream document (e.g. a whole
# Federal Register issue) that this member is only a page excerpt of. Never order-specific.
BOOKKEEPING_FAMILIES = ("opus_record_link", "filename_match", "cites_same_document")
# A citation or a file name only says "this file is the document the order cites";
# at least one signal must tie the file to this particular order.
CASE_SPECIFIC_FAMILIES = ("eo_number_in_text", "quote_in_text", "opus_record_link")

MIN_SPECIFIC_QUOTE_CHARS = 40   # collapsed letters/digits left after removing boilerplate
GENERIC_QUOTE_MAX_MEMBERS = 6   # a quote found verbatim in more distinct files is boilerplate
# A verbatim quote is enough on its own only when it is long and found in very few files.
STANDALONE_QUOTE_MIN_CHARS = 100
STANDALONE_QUOTE_MAX_FILES = 2
NEAR_CHUNK = 24
NEAR_MIN_FRACTION = 0.75
NEAR_MIN_CHUNKS = 3
PAGE_TEXT_MIN_CHARS = 40        # collapsed chars below which a page "has no text"

BOILERPLATE = sorted({
    "byvirtueoftheauthorityvestedinmebytheconstitutionandstatutesoftheunitedstatesofamerica",
    "byvirtueoftheauthorityvestedinmebytheconstitutionandthelawsoftheunitedstatesofamerica",
    "byvirtueoftheauthorityvestedinmebytheconstitutionandthelawsoftheunitedstates",
    "byvirtueoftheauthorityvestedinmeaspresidentoftheunitedstates",
    "byvirtueoftheauthorityvestedinme",
    "aspresidentoftheunitedstatesofamerica",
    "aspresidentoftheunitedstates",
    "presidentoftheunitedstatesofamerica",
    "presidentoftheunitedstates",
    "itisherebyorderedasfollows",
    "itisherebyordered",
    "beitenactedbythesenateandhouseofrepresentativesoftheunitedstatesofamericaincongressassembled",
    "thewhitehouse",
    "isherebyrevoked",
    "isherebyamended",
}, key=len, reverse=True)

MONTHS = ("january", "february", "march", "april", "may", "june", "july", "august",
          "september", "october", "november", "december")

log = logging.getLogger(JOB_NAME)


# --------------------------------------------------------------------------- text helpers

def collapse(text):
    """Lowercase letters and digits only. Makes letter-spaced or hyphen-broken
    text layers ("Exec utive Order", "pro-\\nvided") comparable with clean quotes."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text.lower() if ("a" <= ch <= "z") or ("0" <= ch <= "9"))


def despace(text):
    return re.sub(r"\s+", "", text or "").lower()


def _spaced(word):
    return r"\s?".join(re.escape(c) for c in word)


_EO_PREFIX = re.compile(
    r"(?:" + _spaced("executive") + r"\s*" + _spaced("order") + r"(?:\s?s)?"
    r"|" + _spaced("exec") + r"\.?\s*" + _spaced("order") + r"(?:\s?s)?"
    r"|(?-i:\bE\.\s?O\.)|(?-i:\bEO\b))"
    r"\s*(?:,?\s*(?:nos?|numbers?)\s*\.?\s*|#\s*)?",
    re.I,
)
# An order-number suffix letter ("9616A", "6711A", "2245½") is part of the number: EO:9616
# and EO:9616A are different orders. A capital letter written straight after the digits
# ("9616A and ...") is a suffix. One written after a space ("9 6 1 6 A" in a letter-spaced
# text layer) is taken as a suffix only when the suffixed order is known, because it may also
# be the first letter of the next word; and never when single letters follow ("9054 A N D").
_SUFFIX = (r"(?:(?P<suf>(?-i:[A-Z])|½)(?![A-Za-z])"
           r"|[ ](?P<sufs>(?-i:[A-Z])|½)(?![A-Za-z])(?![ ][A-Za-z](?![A-Za-z])))?")
_NUM_FIRST = re.compile(r"(?P<num>\d(?:[ ]?\d){0,5})(?!\d)" + _SUFFIX)
_NUM_CONT = re.compile(
    r"\s*(?:,|;|&|\band\b|\bor\b)\s*(?:(?:and|or)\s+)?(?:nos?\.?\s*)?(?P<num>\d(?:[ ]?\d){2,5})(?!\d)" + _SUFFIX,
    re.I,
)


def norm_number(digits, suffix=None):
    """Canonical order number: digits without leading zeros, plus an upper-case suffix."""
    d = (digits or "").replace(" ", "").lstrip("0") or "0"
    return d + (suffix or "").upper()


def _resolve_number(raw, known, suffix=None):
    """raw may contain single spaces from letter-spaced text layers ("1 1 234").
    Return the longest left-to-right concatenation that is a known order number.
    A number printed with a suffix letter only ever resolves to the suffixed order."""
    suffix = (suffix or "").upper()
    if known is None:
        return norm_number(raw.split(" ")[0], suffix)
    best = None
    acc = ""
    groups = raw.split(" ")
    for k, g in enumerate(groups):
        acc += g
        last = k == len(groups) - 1
        cand = norm_number(acc, suffix if last else "")
        if cand in known:
            best = cand
    return best


def find_eo_numbers(text, known):
    """Return {number: count} of known order numbers written as "Executive Order
    No. 9054", "E.O. 9054", "Exec. Order 9054", "Executive Orders Nos. 1, 2 and 3"."""
    found = collections.Counter()
    if not text:
        return found
    for m in _EO_PREFIX.finditer(text):
        pos = m.end()
        mm = _NUM_FIRST.match(text, pos)
        while mm:
            num = _resolve_number(mm.group("num"), known, mm.group("suf"))
            if mm.group("sufs"):
                spaced = _resolve_number(mm.group("num"), known, mm.group("sufs"))
                num = spaced or _resolve_number(mm.group("num"), known)
            if num:
                found[num] += 1
            pos = mm.end()
            mm = _NUM_CONT.match(text, pos)
    return found


_HEADING_LINE = re.compile(r"^executiveorder(?:no\.?|number)?(\d{1,5})([a-z]|½)?[-.:—–]*$")
_SIGNATURE_NO = re.compile(
    _spaced("white") + r"\s+" + _spaced("house") + r"[\s,.]*[^\[\]]{0,60}?\[\s?N\s?o\s?\.?\s?(\d(?:[ ]?\d){2,5})\s?([A-Z])?\s?\]",
    re.I)
_HEADING_ONLY = re.compile(r"^executiveorder[.:]?$")
_NO_LINE = re.compile(r"^(?:no\.?|number)?(\d{1,5})([a-z]|½)?[.:]?$")


def find_eo_headings(text, known):
    """Order numbers printed as a heading line ("EXECUTIVE ORDER 9054", or
    "EXECUTIVE ORDER" followed by a "No. 9054" line), as the Federal Register prints
    an order's own text."""
    out = set()
    lines = [despace(x) for x in (text or "").splitlines()]
    lines = [x for x in lines if x]
    for i, line in enumerate(lines):
        m = _HEADING_LINE.match(line)
        num = None
        if m:
            num = norm_number(m.group(1), m.group(2))
        elif _HEADING_ONLY.match(line) and i + 1 < len(lines):
            m2 = _NO_LINE.match(lines[i + 1])
            if m2:
                num = norm_number(m2.group(1), m2.group(2))
        # "EXECUTIVE ORDER 9616A" is a heading of EO:9616A only, never of EO:9616
        if num and (known is None or num in known):
            out.add(num)
    # 1936-1940s Federal Register: the number is printed after the signature,
    # "THE WHITE HOUSE, December 11, 1936. [No. 7504]". (Proclamations end with
    # "By the President: ... Secretary of State. [No. 2211]" and are not matched.)
    for m in _SIGNATURE_NO.finditer(text or ""):
        num = norm_number(m.group(1), m.group(2))
        if known is None or num in known:
            out.add(num)
    return out


_FR_CITE = re.compile(
    r"(?<![\d.])(\d{1,2})\s?(?:F\s?\.?\s?R\s?\.?|P\s?\.\s?R\s?\.|Fed\.?\s?Reg\.?)\s?(\d{1,5})(?!\d)")
_STAT_CITE = re.compile(r"(?<![\d.])(\d{1,3})\s?S\s?t\s?a\s?t\s?\.?\s?,?\s?(\d{1,4})(?!\d)", re.I)


def find_fr_cites(text):
    out = set()
    for m in _FR_CITE.finditer(text or ""):
        v, p = int(m.group(1)), int(m.group(2))
        if 1 <= v <= 91 and p >= 1:
            out.add((v, p))
    return out


def find_stat_cites(text):
    out = set()
    for m in _STAT_CITE.finditer(text or ""):
        v, p = int(m.group(1)), int(m.group(2))
        if 1 <= v <= 140 and p >= 1:
            out.add((v, p))
    return out


_DATE_DESPACED = re.compile(r"(" + "|".join(MONTHS) + r")\.?(\d{1,2}),?(\d{4})")


def _mkdate(month, day, year):
    try:
        return datetime.date(int(year), MONTHS.index(month) + 1, int(day)).isoformat()
    except ValueError:
        return None


_FR_VOL = re.compile(r"vol(?:ume)?\.?(\d{1,2})[,.]")
_STAT_VOL = [re.compile(r"\[\s?(\d{1,3})\s?S\s?t\s?a\s?t", re.I),
             re.compile(r"(\d{1,3})\s?S\s?T\s?A\s?T\s?\.?\s?\]", re.I)]


def page_header_features(page_text):
    """What a page's running head says about where it was printed.

    Returns {"fr_date": ISO date or None, "fr_vol": int or None, "fr_pages": set,
    "stat_vol": int or None, "stat_pages": set}."""
    out = {"fr_date": None, "fr_vol": None, "fr_pages": set(), "stat_vol": None, "stat_pages": set()}
    lines = [x for x in (page_text or "").splitlines() if x.strip()][:6]
    head = "\n".join(lines)
    dhead = despace(head)
    if "federalregister" in dhead:
        m = _DATE_DESPACED.search(dhead)
        year = None
        if m:
            out["fr_date"] = _mkdate(m.group(1), m.group(2), m.group(3))
            year = int(m.group(3)) if out["fr_date"] else None
        mv = _FR_VOL.search(dhead)
        if mv:
            out["fr_vol"] = int(mv.group(1))
        elif year and year >= 1936:
            out["fr_vol"] = year - 1935
        skip = set()
        if m:
            skip.update({m.group(2), m.group(3)})
        for line in lines[:3]:
            if "regist" not in despace(line) and not re.search(r"^\s*\d{1,5}\s*$", line):
                continue
            for n in re.findall(r"(?<![\d,.])(\d{2,5})(?![\d,])", line):
                if n in skip or (mv and n == mv.group(1)):
                    continue
                if year and n == str(year):
                    continue
                out["fr_pages"].add(int(n))
    first = lines[0] if lines else ""
    for rx in _STAT_VOL:
        mv = rx.search(first)
        if mv:
            out["stat_vol"] = int(mv.group(1))
            # page number: first or last token of the running head; a trailing
            # number right after a comma is the year of the session dates
            m1 = re.match(r"^\s*(\d{1,4})(?!\d)", first)
            if m1 and m1.end() <= mv.start():
                out["stat_pages"].add(int(m1.group(1)))
            rest = first[mv.end():]
            m2 = re.search(r"(?<![\d,])(\d{1,4})\s*$", rest)
            if m2 and not re.search(r",\s*$", rest[:m2.start()]):
                out["stat_pages"].add(int(m2.group(1)))
            break
    return out


def page_dates_in_text(page_text):
    """FR issue dates printed in the page head (used as a content check against
    the FR dates the case's own records cite)."""
    h = page_header_features(page_text)
    return {h["fr_date"]} if h["fr_date"] else set()


# --------------------------------------------------------------------------- file names

_FN_DATE = re.compile(r"(?<!\d)((?:1[89]|20)\d{2})-(\d{2})-(\d{2})(?!\d)")
_FN_STAT = re.compile(r"stat(?:ute)?[_-]?(\d{1,3})[_-](?:pg)?(\d{1,4})(?!\d)", re.I)
_FN_EO = re.compile(r"(?<![a-z])eo[_-]?(\d{3,5})(?!\d)([a-z](?![a-z]))?", re.I)
_FN_DOC = re.compile(r"(?<!\d)((?:19|20)\d{2}|\d{2})-(\d{5})(?!\d)")
_FN_PAGES = re.compile(r"(?:^|[._-])p(?:age|g)?[-_]?(\d{1,4})(?:-(\d{1,4}))?", re.I)


def norm_doc(prefix, num):
    if len(prefix) == 2:
        y = int(prefix)
        prefix = str(1900 + y if y >= 90 else 2000 + y)
    return f"{prefix}-{num}"


def filename_features(path):
    """Clues in the Opus file name, e.g. fr_1946-05-29.p19-20.pdf or stat_55_838.pdf.
    These come from Opus's own naming, so they count as bookkeeping, not content."""
    base = path.rsplit("/", 1)[-1]
    stem = base.rsplit(".", 1)[0] if "." in base else base
    feats = {"fr_dates": set(), "stat": set(), "eo": set(), "fr_docs": set(), "pages": None}
    low = base.lower()
    is_fr = bool(re.match(r"^(?:r_)?(?:fr|fof)[_-]", low)) or "/fr" in path.lower()
    for m in _FN_DATE.finditer(base):
        if is_fr:
            feats["fr_dates"].add(f"{m.group(1)}-{m.group(2)}-{m.group(3)}")
    for m in _FN_STAT.finditer(base):
        feats["stat"].add((int(m.group(1)), int(m.group(2))))
    for m in _FN_EO.finditer(base):
        feats["eo"].add(norm_number(m.group(1), m.group(2)))
    no_dates = _FN_DATE.sub(" ", base)
    if is_fr:
        for m in _FN_DOC.finditer(no_dates):
            feats["fr_docs"].add(norm_doc(m.group(1), m.group(2)))
    mp = None
    for mp in _FN_PAGES.finditer(stem):
        pass
    if mp and not _FN_STAT.search(base):
        feats["pages"] = (int(mp.group(1)), int(mp.group(2) or mp.group(1)))
    return feats


def member_key(path):
    """Shared stem of an Opus cache file and its siblings (.meta.json, .txt)."""
    base = path.rsplit("/", 1)[-1]
    stem = base.split(".", 1)[0]
    stem = re.sub(r"[_-](?:p|page|render|raw|excerpt)[-_]?\d.*$", "", stem, flags=re.I)
    stem = re.sub(r"[_-](?:excerpt)$", "", stem, flags=re.I)
    return stem if len(stem) >= 6 else None


# --------------------------------------------------------------------------- quotes

_ELLIPSIS = re.compile(r"\.\s?\.\s?\.|\u2026|\[\s?\.\.\.\s?\]|\[\u2026\]")


def quote_segments(quote):
    segs = [collapse(s) for s in _ELLIPSIS.split(quote or "")]
    return tuple(s for s in segs if len(s) >= 12)


def specific_length(segs):
    total = 0
    for s in segs:
        for bp in BOILERPLATE:
            s = s.replace(bp, "")
        total += len(s)
    return total


class PageText:
    """A member's per-page collapsed text joined into one string with offsets,
    so a quote that crosses a page break is still found and located."""

    def __init__(self, pages):
        self.pages = pages
        self.collapsed = [collapse(p) for p in pages]
        self.offsets = []
        pos = 0
        for c in self.collapsed:
            self.offsets.append(pos)
            pos += len(c)
        self.full = "".join(self.collapsed)

    def locate(self, seg):
        """1-based page numbers covering the first occurrence of seg, or None."""
        i = self.full.find(seg)
        if i < 0:
            return None
        a = bisect.bisect_right(self.offsets, i) - 1
        b = bisect.bisect_right(self.offsets, i + len(seg) - 1) - 1
        return list(range(a + 1, b + 2))

    def verbatim(self, segs):
        pages = []
        for s in segs:
            loc = self.locate(s)
            if loc is None:
                return None
            pages.extend(loc)
        return sorted(set(pages))

    def near(self, segs):
        chunks = []
        for s in segs:
            chunks.extend(s[i:i + NEAR_CHUNK] for i in range(0, len(s) - NEAR_CHUNK + 1, NEAR_CHUNK))
        if len(chunks) < NEAR_MIN_CHUNKS:
            return None
        pages = []
        hit = 0
        for c in chunks:
            loc = self.locate(c)
            if loc:
                hit += 1
                pages.extend(loc)
        if hit / len(chunks) >= NEAR_MIN_FRACTION:
            return sorted(set(pages))
        return None


# --------------------------------------------------------------------------- text extraction

def write_text_lf(path, text):
    """UTF-8 with LF line ends on every OS, so a PC run and a GitHub run of the same
    input give the same bytes."""
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sniff_kind(data, name):
    if not data:
        return "empty"
    head = data[:1024].lstrip()
    if data[:5] == b"%PDF-":
        return "pdf"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if head[:1] == b"<" and re.search(rb"<\s*(html|head|body|title|\?xml|!doctype)", head, re.I):
        return "html_saved_under_media_name"
    return "unknown"


def html_to_text(data):
    t = data.decode("utf-8", "replace")
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    t = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), t)
    t = t.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&nbsp;", " ")
    return re.sub(r"[ \t]+", " ", t).strip()


def pdf_pages_text(data):
    import pypdf  # pinned in requirements.txt
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    reader = pypdf.PdfReader(io.BytesIO(data))
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception as e:  # a broken page must not stop the job
            pages.append("")
            log.warning("text extraction failed on a page: %s", e)
    return pages


class Ocr:
    """Optional OCR through tesseract (and pdftoppm for PDF pages). Used only when
    both are on PATH; otherwise pages are counted as needing OCR."""

    def __init__(self, enabled=True, max_pages=2000, max_pages_per_member=40, tmpdir=None):
        t = shutil.which("tesseract") if enabled else None
        r = shutil.which("pdftoppm") if enabled else None
        self.tesseract = [t] if t else None   # command prefixes (lists), replaceable in tests
        self.pdftoppm = [r] if r else None
        self.max_pages = max_pages
        self.max_per_member = max_pages_per_member
        self.used = 0
        self.failures = 0          # pages whose OCR failed (tool error or timeout) in this run
        self.failure_notes = []    # a few examples for SUMMARY.json
        self.timeout = 300
        self.tmpdir = tmpdir

    @property
    def images(self):
        return bool(self.tesseract)

    @property
    def pdfs(self):
        return bool(self.tesseract and self.pdftoppm)

    def budget_left(self):
        return self.used < self.max_pages

    def _fail(self, what, err):
        self.failures += 1
        if len(self.failure_notes) < 20:
            self.failure_notes.append(f"{what}: {type(err).__name__}: {err}"[:200])

    def _tess(self, image_path):
        """OCR one image. Returns the text, or None when tesseract failed (the page then
        stays 'needs OCR' and is retried on the next run)."""
        self.used += 1
        r = subprocess.run(self.tesseract + [str(image_path), "stdout", "-l", "eng", "--psm", "3"],
                           capture_output=True, timeout=self.timeout)
        if r.returncode != 0:
            raise RuntimeError("tesseract exit %d: %s" % (r.returncode, r.stderr.decode("utf-8", "replace")[:120]))
        return r.stdout.decode("utf-8", "replace")

    def image_text(self, data, suffix, label=""):
        with tempfile.TemporaryDirectory(dir=self.tmpdir) as d:
            p = pathlib.Path(d) / ("img" + suffix)
            p.write_bytes(data)
            try:
                return self._tess(p)
            except Exception as e:  # one bad image must not stop the job
                self._fail(f"{label} image", e)
                return None

    def pdf_page_texts(self, data, page_numbers, label=""):
        """OCR the given 1-based PDF pages one at a time; a failure on one page is
        counted and does not lose the other pages."""
        out = {}
        with tempfile.TemporaryDirectory(dir=self.tmpdir) as d:
            pdf = pathlib.Path(d) / "doc.pdf"
            pdf.write_bytes(data)
            for n in page_numbers[: self.max_per_member]:
                if not self.budget_left():
                    break
                prefix = pathlib.Path(d) / f"p{n}"
                try:
                    subprocess.run(self.pdftoppm + ["-f", str(n), "-l", str(n), "-r", "200", "-gray", "-png",
                                    str(pdf), str(prefix)], capture_output=True, timeout=self.timeout)
                    imgs = sorted(pathlib.Path(d).glob(f"p{n}*.png"))
                    if not imgs:
                        raise RuntimeError("pdftoppm produced no image")
                    try:
                        out[n] = self._tess(imgs[0])
                    finally:
                        for i in imgs:
                            i.unlink()
                except Exception as e:
                    self._fail(f"{label} page {n}", e)
        return out


def extract_member_text(data, kind, ocr, cache_dir, sha):
    """Return dict(method, pages, pages_without_text, ocr_pages, error). Uses the
    cache (keyed by sha256 + extractor version) when possible."""
    cache_file = None
    cached = None
    if cache_dir:
        cache_file = pathlib.Path(cache_dir) / "text" / f"{sha}.json"
        if cache_file.exists():
            try:
                cached = json.loads(cache_file.read_text(encoding="utf-8"))
                if cached.get("version") != EXTRACTOR_VERSION:
                    cached = None
            except Exception:
                cached = None
    res = cached or {"version": EXTRACTOR_VERSION, "kind": kind, "method": "none", "pages": [],
                     "ocr_pages": [], "error": None}
    if cached is None:
        try:
            if kind == "pdf":
                res["pages"] = pdf_pages_text(data)
                res["method"] = "pdf_text_layer(pypdf)"
            elif kind in ("png", "jpg"):
                res["pages"] = [""]
                res["method"] = "image"
            elif kind == "html_saved_under_media_name":
                res["pages"] = [html_to_text(data)]
                res["method"] = "html_markup_stripped"
        except Exception as e:
            res["error"] = f"{type(e).__name__}: {e}"[:300]
            res["pages"] = []
            res["method"] = "failed"
    # OCR any page that still has no usable text, if OCR is available.
    blank = [i + 1 for i, p in enumerate(res["pages"]) if len(collapse(p)) < PAGE_TEXT_MIN_CHARS
             and (i + 1) not in res["ocr_pages"]]
    if blank and ocr is not None and ocr.budget_left():
        try:
            if kind in ("png", "jpg") and ocr.images:
                t = ocr.image_text(data, "." + kind, label=sha[:12])
                if t is not None:
                    res["pages"][0] = t
                    res["ocr_pages"] = [1]
            elif kind == "pdf" and ocr.pdfs:
                got = ocr.pdf_page_texts(data, blank, label=sha[:12])
                for n, t in got.items():
                    res["pages"][n - 1] = t
                    res["ocr_pages"].append(n)
        except Exception as e:
            res["error"] = (res.get("error") or "") + f" OCR failed: {type(e).__name__}: {e}"[:200]
    if cache_file is not None:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        write_text_lf(cache_file, json.dumps(res, ensure_ascii=False))
    res["pages_without_text"] = [i + 1 for i, p in enumerate(res["pages"])
                                 if len(collapse(p)) < PAGE_TEXT_MIN_CHARS]
    return res


# --------------------------------------------------------------------------- case model

_HEX64 = re.compile(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])")
_URL = re.compile(r"https?://[^\s\"'<>)\]]+")
_TMP_TAIL = re.compile(r"/s11/((?:shards|reviews)/.+)$")
_URL_FR_DATE = [re.compile(r"FR-(\d{4}-\d{2}-\d{2})"),
                re.compile(r"federalregister\.gov/(?:documents|d)/(\d{4})/(\d{2})/(\d{2})/")]
_URL_STAT = re.compile(r"STATUTE-(\d{1,3})-Pg(\d{1,4})", re.I)
_URL_DOC = re.compile(r"(?<![\d-])((?:19|20)\d{2}|\d{2})-(\d{5})(?=\.pdf|/|$|\b)")


def order_number(instrument_id):
    """"EO:09054" -> "9054"; "EO:9616A" -> "9616A" (the suffix is kept, so 9616 and
    9616A never share signals)."""
    m = re.match(r"EO:(\d+)([A-Za-z]|½)?(?![A-Za-z0-9])", instrument_id or "")
    if not m:
        return None
    return norm_number(m.group(1), m.group(2))


def number_sort_key(num):
    m = re.match(r"(\d+)(.*)$", num or "")
    return (int(m.group(1)), m.group(2)) if m else (0, num or "")


def _walk_strings(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _walk_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_strings(v)
    elif isinstance(obj, str):
        yield obj


def _path_tail(value, base_dir):
    m = _TMP_TAIL.search(value)
    if m:
        return "evidence/" + m.group(1)
    if base_dir and not value.startswith(("/", "http")) and re.match(r"^(?:cache|srch|view|conv)/", value):
        return base_dir.rstrip("/") + "/" + value
    return None


class Case:
    def __init__(self, iid):
        self.id = iid
        self.num = order_number(iid)
        self.accepted = False
        self.evidence_dir = None
        self.review_dir = None
        self.quotes = []          # dicts: segs, spec, evidence_id, url, own_text
        self.hashes = set()
        self.paths = set()
        self.urls = set()
        self.fr_dates = set()
        self.fr_cites = set()
        self.stat_cites = set()
        self.fr_docs = set()
        self._texts = []

    def add_record(self, rec, base_dir):
        for s in _walk_strings(rec):
            for h in _HEX64.findall(s):
                self.hashes.add(h)
            t = _path_tail(s, base_dir)
            if t:
                self.paths.add(t)
            for u in _URL.findall(s):
                self.urls.add(u.rstrip(".,;"))
        self._texts.append(json.dumps(rec, ensure_ascii=False))

    def add_quote(self, quote, evidence_id, url, title, local_file):
        segs = quote_segments(quote)
        if not segs:
            return
        spec = specific_length(segs)
        own = False
        if self.num:
            blob = " ".join(x or "" for x in (evidence_id, url, title, local_file))
            # "eo9616" must not count as the own text of EO:9616A, nor "eo9616a" of EO:9616
            tail = r"(?![\dA-Za-z])" if not self.num[-1].isdigit() else r"(?!\d)(?![A-Za-z](?![A-Za-z]))"
            own = bool(re.search(r"(?<!\d)0*" + re.escape(self.num) + tail, blob, re.I))
        self.quotes.append({"segs": segs, "spec": spec, "evidence_id": evidence_id, "url": url,
                            "own_text": own})

    def finish(self):
        text = "\n".join(self._texts)
        self.fr_cites |= find_fr_cites(text)
        self.stat_cites |= find_stat_cites(text)
        for s in list(self.urls) + list(self.paths):
            for rx in _URL_FR_DATE:
                for m in rx.finditer(s):
                    self.fr_dates.add("-".join(m.groups()) if len(m.groups()) == 3 else m.group(1))
            for m in _URL_STAT.finditer(s):
                self.stat_cites.add((int(m.group(1)), int(m.group(2))))
        for p in self.paths:
            f = filename_features(p)
            self.fr_dates |= f["fr_dates"]
            self.stat_cites |= f["stat"]
            self.fr_docs |= f["fr_docs"]
        for u in self.urls:
            if "federalregister.gov" in u or "govinfo.gov" in u:
                for m in _URL_DOC.finditer(u):
                    self.fr_docs.add(norm_doc(m.group(1), m.group(2)))
        self._texts = []
        # de-duplicate quotes
        seen = set()
        uniq = []
        for q in self.quotes:
            if q["segs"] in seen:
                continue
            seen.add(q["segs"])
            uniq.append(q)
        self.quotes = uniq


def _jsonl(data):
    out = []
    for line in data.decode("utf-8", "replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


UNPACKAGED = set()   # files the Opus release left out (too large / HTML); filled by load_cases
UNPACKAGED_INFO = {}  # path -> {"sha256", "bytes"} of those files, from UNPACKAGED_LARGE_ORIGINALS.jsonl
MEDIA_EXT = (".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".gif")


def load_cases(complete_zip_path, accepted_ids, note_leads=None):
    """Build Case objects for every order in the Stage 11 records. Returns
    (cases: dict id -> Case, metas: dict path -> meta dict)."""
    UNPACKAGED.clear()
    UNPACKAGED_INFO.clear()
    cases = {}

    def case(i):
        if i not in cases:
            cases[i] = Case(i)
        return cases[i]

    metas = {}
    with zipfile.ZipFile(complete_zip_path) as z:
        names = [n for n in z.namelist() if n.startswith(PKG)]
        rel = {n: n[len(PKG):] for n in names}
        # status records: evidence and review folders per order
        for f in ("STAGE11_STATUS_RECORDS.jsonl", "STAGE11_ACCEPTED.jsonl"):
            if PKG + f in rel:
                for r in _jsonl(z.read(PKG + f)):
                    i = r.get("instrument_id")
                    if not isinstance(i, str):
                        continue
                    c = case(i)
                    c.evidence_dir = c.evidence_dir or r.get("evidence_dir")
                    c.review_dir = c.review_dir or r.get("review_dir")
                    c.add_record({k: v for k, v in r.items() if k not in ("evidence_dir", "review_dir")}, None)
        # producer evidence + proposals per shard
        for n, r_ in rel.items():
            if not r_.endswith("/evidence.jsonl") or "/shards/" not in r_:
                continue
            shard_dir = r_.rsplit("/", 1)[0] + "/"
            evid = {}
            for e in _jsonl(z.read(n)):
                if isinstance(e.get("evidence_id"), str):
                    evid[e["evidence_id"]] = e
            sp = PKG + shard_dir + "status_proposals.jsonl"
            if sp not in rel:
                continue
            for p in _jsonl(z.read(sp)):
                i = p.get("instrument_id")
                if not isinstance(i, str):
                    continue
                c = case(i)
                c.evidence_dir = c.evidence_dir or shard_dir
                c.add_record(p, shard_dir)
                linked = {s for s in _walk_strings(p) if s in evid}
                for eid in sorted(linked):
                    e = evid[eid]
                    c.add_record(e, shard_dir)
                    if e.get("quote"):
                        c.add_quote(e["quote"], eid, e.get("url"), e.get("source_title"), e.get("local_file"))
        # reviewer evidence
        for n, r_ in rel.items():
            if not r_.endswith("/reviews.jsonl") or "/reviews/" not in r_:
                continue
            rdir = r_.rsplit("/", 1)[0] + "/"
            for rv in _jsonl(z.read(n)):
                i = rv.get("instrument_id")
                if not isinstance(i, str):
                    continue
                c = case(i)
                c.review_dir = c.review_dir or rdir
                c.add_record(rv, rdir)
                for k, e in enumerate(rv.get("reviewer_evidence") or []):
                    if isinstance(e, dict) and e.get("quote"):
                        c.add_quote(e["quote"], f"{rdir}reviewer_evidence[{k}]", e.get("url"),
                                    e.get("source_title"), e.get("local_file"))
        # cache meta files (URL + hashes of the full document an excerpt was cut from)
        for n, r_ in rel.items():
            if r_.endswith(".meta.json") and "/cache/" in r_:
                try:
                    m = json.loads(z.read(n).decode("utf-8", "replace"))
                except Exception:
                    continue
                if isinstance(m, dict):
                    metas[r_] = m
        up = PKG + "evidence/UNPACKAGED_LARGE_ORIGINALS.jsonl"
        if up in rel:
            for r in _jsonl(z.read(up)):
                if isinstance(r.get("path"), str):
                    UNPACKAGED.add(r["path"])
                    UNPACKAGED_INFO[r["path"]] = {"sha256": r.get("sha256"), "bytes": r.get("bytes")}
    if note_leads:
        for r in note_leads:
            i = r.get("instrument_id")
            if isinstance(i, str) and i in cases:
                cases[i].add_record({"explicit_references": r.get("explicit_references_not_verified"),
                                     "review_problems": r.get("review_problems_verbatim"),
                                     "inferential": r.get("what_remains_inferential_verbatim")}, None)
    for i, c in cases.items():
        c.accepted = i in accepted_ids
        c.finish()
    for i in accepted_ids:
        if i not in cases:
            c = case(i)
            c.accepted = True
            c.finish()
    return cases, metas


# --------------------------------------------------------------------------- matching

def page_ranges(pages):
    pages = sorted(set(pages))
    out = []
    for p in pages:
        if out and p == out[-1][1] + 1:
            out[-1][1] = p
        else:
            out.append([p, p])
    return ",".join(f"{a}" if a == b else f"{a}-{b}" for a, b in out)


class MemberFeatures:
    def __init__(self, path, sha, pages, known_numbers):
        self.path = path
        self.sha = sha
        self.pt = PageText(pages)
        self.fn = filename_features(path)
        self.key = member_key(path)
        self.dir = path.rsplit("/", 1)[0] + "/"
        self.eo_pages = collections.defaultdict(set)
        self.heading_pages = collections.defaultdict(set)
        self.page_headings = collections.defaultdict(set)   # pdf page -> order numbers printed as headings
        self.fr_cite_pages = collections.defaultdict(set)
        self.stat_cite_pages = collections.defaultdict(set)
        self.fr_date_pages = collections.defaultdict(set)
        self.fr_vol_pages = collections.defaultdict(dict)    # vol -> {printed page: pdf page}
        self.stat_vol_pages = collections.defaultdict(dict)
        heads = [page_header_features(t) for t in pages]
        vols = collections.Counter(h["stat_vol"] for h in heads if h["stat_vol"])
        if vols:
            dom = vols.most_common(1)[0][0]
            for h, text in zip(heads, pages):
                if h["stat_vol"] and h["stat_vol"] != dom:
                    # running head glued together, e.g. "84155 Stat .]" = page 841, vol 55
                    first = next((x for x in text.splitlines() if x.strip()), "")
                    mg = re.match(r"^\s*(\d{1,4}?)" + str(dom) + r"\s?S\s?t\s?a\s?t", first, re.I)
                    if mg and mg.group(1):
                        h["stat_vol"] = dom
                        h["stat_pages"] = {int(mg.group(1))}
        for i, text in enumerate(pages, start=1):
            h = heads[i - 1]
            for n in find_eo_numbers(text, known_numbers):
                self.eo_pages[n].add(i)
            for n in find_eo_headings(text, known_numbers):
                self.heading_pages[n].add(i)
                self.page_headings[i].add(n)
                self.eo_pages[n].add(i)
            for c in find_fr_cites(text):
                self.fr_cite_pages[c].add(i)
            for c in find_stat_cites(text):
                self.stat_cite_pages[c].add(i)
            if h["fr_date"]:
                self.fr_date_pages[h["fr_date"]].add(i)
            if h["fr_vol"]:
                for p in h["fr_pages"]:
                    self.fr_vol_pages[h["fr_vol"]][p] = i
            if h["stat_vol"]:
                for p in h["stat_pages"]:
                    self.stat_vol_pages[h["stat_vol"]][p] = i

    def printed_page_hit(self, table, vol, page):
        """PDF pages covering printed page `page` of volume `vol`, using the
        running-head page numbers found in this member."""
        pages = table.get(vol)
        if not pages:
            return None
        if page in pages:
            return [pages[page]]
        lo, hi = min(pages), max(pages)
        if lo <= page <= hi and hi - lo <= 400:
            below = max(p for p in pages if p <= page)
            return [pages[below]]
        return None


_WHOLE_PACKAGE_URL = re.compile(r"/content/pkg/([^/]+)/pdf/\1\.pdf$", re.I)
_WHOLE_FR_ISSUE = re.compile(r"(?:^|/)FR-\d{4}-\d{2}-\d{2}\.pdf$", re.I)


def is_whole_package_url(url):
    """True for URLs of a whole govinfo package, such as a whole Federal Register issue
    (.../pkg/FR-1948-07-14/pdf/FR-1948-07-14.pdf) or a whole Statutes volume."""
    u = (url or "").split("?", 1)[0].split("#", 1)[0]
    return bool(_WHOLE_PACKAGE_URL.search(u) or _WHOLE_FR_ISSUE.search(u))


def member_is_whole_package_excerpt(sha, metas_for_member):
    """The member's .meta.json says it was cut from a whole-package download whose
    bytes (sha256) differ from the member's own bytes."""
    for _, m in metas_for_member:
        url = m.get("final_url") or m.get("url")
        if is_whole_package_url(url) and m.get("sha256") and m.get("sha256") != sha:
            return True
    return False


def score_pair(mf, case, metas_for_member, quote_hits):
    """Collect signals for one (member, order) pair.

    quote_hits: list of (quote dict, pages, mode) for this case found in this member.
    Returns dict with families, details, pages, or None if no signal."""
    fam = collections.OrderedDict()
    pages = set()

    def add(family, detail, pgs=()):
        fam.setdefault(family, []).append(detail + (f"@p{page_ranges(pgs)}" if pgs else ""))
        pages.update(pgs)

    # content: order number on the page
    if case.num and case.num in mf.eo_pages:
        hp = mf.heading_pages.get(case.num, set())
        add("eo_number_in_text", "heading" if hp else "mention", sorted(hp or mf.eo_pages[case.num]))
    # content: quotes from this order's records
    verbatim_specific = False
    own_quote_pages = set()
    notes = []
    for q, qp, mode in quote_hits:
        others = set()
        for p in qp:
            others |= mf.page_headings.get(p, set())
        if others and case.num not in others and not (case.num and case.num in mf.eo_pages):
            # the quote sits on a page that prints other orders and never names this one:
            # most likely stock wording shared by sibling orders, so it is not counted
            notes.append(f"quote_on_page_of_other_orders:{q['evidence_id']}@p{page_ranges(qp)}")
            continue
        add("quote_in_text", f"{mode}:{q['evidence_id']}:len{q['spec']}", qp)
        # A quote of the order's own text found in a document that never names the
        # order (e.g. the statute whose words the order repeats) is not enough alone.
        if mode == "verbatim" and q["spec"] >= STANDALONE_QUOTE_MIN_CHARS \
                and q.get("files", 1) <= STANDALONE_QUOTE_MAX_FILES \
                and not (q["own_text"] and not (case.num and case.num in mf.eo_pages)):
            verbatim_specific = True
        if q["own_text"]:
            own_quote_pages.update(qp)
    # content: citations printed on / heading the page
    for c in sorted(case.fr_cites):
        hit = mf.printed_page_hit(mf.fr_vol_pages, c[0], c[1])
        if hit:
            add("citation_in_text", f"fr_page_head={c[0]}FR{c[1]}", hit)
        elif c in mf.fr_cite_pages and case.num and case.num in mf.eo_pages:
            add("citation_in_text", f"fr_cite_mentioned={c[0]}FR{c[1]}", sorted(mf.fr_cite_pages[c]))
    for c in sorted(case.stat_cites):
        hit = mf.printed_page_hit(mf.stat_vol_pages, c[0], c[1])
        if hit:
            add("citation_in_text", f"stat_page_head={c[0]}Stat{c[1]}", hit)
    for d in sorted(case.fr_dates):
        if d in mf.fr_date_pages:
            add("citation_in_text", f"fr_issue_date_head={d}", sorted(mf.fr_date_pages[d]))
    # bookkeeping: Opus's own records point at this file
    links = []
    if mf.sha in case.hashes:
        links.append("member_sha256_in_case_records")
    if mf.path in case.paths:
        links.append("member_path_in_case_records")
    # Links through the .meta.json or a sibling file only show that the order's records cite
    # the same upstream document. When this member is a page excerpt of a whole Federal
    # Register issue (or another whole govinfo package), citing that issue says nothing
    # about these particular pages, so the link is not order-specific unless a cited
    # FR/Stat page is printed in the excerpt's running heads.
    doc_links = []
    for mp, m in metas_for_member:
        if (m.get("url") and m["url"] in case.urls) or (m.get("final_url") and m["final_url"] in case.urls) \
                or (m.get("sha256") and m["sha256"] in case.hashes) \
                or (m.get("text_sha256") and m["text_sha256"] in case.hashes):
            doc_links.append("via_meta:" + mp.rsplit("/", 1)[-1])
            break
    if not links and not doc_links and mf.key:
        for p in case.paths:
            if p.startswith(mf.dir) and p[len(mf.dir):].startswith(mf.key) and "/" not in p[len(mf.dir):]:
                doc_links.append("sibling_file_in_case_records:" + p.rsplit("/", 1)[-1])
                break
    page_head_hit = any(d.startswith(("fr_page_head=", "stat_page_head=")) for d in fam.get("citation_in_text", []))
    whole_doc_excerpt = member_is_whole_package_excerpt(mf.sha, metas_for_member)
    for l_ in links:
        add("opus_record_link", l_)
    for l_ in doc_links:
        if whole_doc_excerpt and not links and not page_head_hit:
            add("cites_same_document", l_ + ":excerpt_of_whole_package")
        else:
            add("opus_record_link", l_)
    # bookkeeping: file name
    fn = mf.fn
    if case.num and case.num in fn["eo"]:
        add("filename_match", f"eo={case.num}")
    for d in sorted(fn["fr_dates"] & case.fr_dates):
        add("filename_match", f"fr_date={d}")
    for s in sorted(fn["stat"] & case.stat_cites):
        add("filename_match", f"stat={s[0]}Stat{s[1]}")
    for d in sorted(fn["fr_docs"] & case.fr_docs):
        add("filename_match", f"fr_doc={d}")
    if not fam:
        return None if not notes else {"grade": "ambiguous", "families": [], "details": {}, "pages": [],
                                        "content_verified": None, "role": "cited_source", "heading_pages": [],
                                        "own_quote_pages": [], "notes": notes}
    families = list(fam)
    content = [f for f in families if f in CONTENT_FAMILIES]
    specific = [f for f in families if f in CASE_SPECIFIC_FAMILIES]
    if verbatim_specific or (len(families) >= 2 and content and specific):
        grade = "unique_supported"
    else:
        grade = "ambiguous"
    heading = case.num in mf.heading_pages if case.num else False
    role = "cited_source"
    if heading and (own_quote_pages or (case.num in fn["eo"])):
        role = "order_text_candidate"
    return {"grade": grade, "families": families, "details": fam, "pages": sorted(pages),
            "content_verified": bool(content), "role": role,
            "heading_pages": sorted(mf.heading_pages.get(case.num, ())) if case.num else [],
            "own_quote_pages": sorted(own_quote_pages), "notes": notes}


def find_quote_hits(pt, quotes_index, near_cases, cases):
    """quotes_index: list of (case_id, quote) with specific length >= threshold.
    Verbatim search runs over every quote; near-verbatim only for near_cases."""
    hits = collections.defaultdict(list)
    for cid, q in quotes_index:
        pg = pt.verbatim(q["segs"])
        if pg:
            hits[cid].append((q, pg, "verbatim"))
    for cid in near_cases:
        c = cases.get(cid)
        if not c:
            continue
        done = {id(x[0]) for x in hits.get(cid, [])}
        for q in c.quotes:
            if id(q) in done or q["spec"] < MIN_SPECIFIC_QUOTE_CHARS:
                continue
            pg = pt.near(q["segs"])
            if pg:
                hits[cid].append((q, pg, "near"))
    return hits


# --------------------------------------------------------------------------- driver

def select_members(infos, limit):
    if not limit or limit >= len(infos):
        return infos
    step = len(infos) / limit
    return [infos[int(k * step)] for k in range(limit)]


def read_member_map(path):
    out = {}
    if path and pathlib.Path(path).exists():
        with open(path, encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                out[r["manifest_path"]] = r
    return out


def read_accepted(full844_path, complete_zip_path):
    ids = set()
    if full844_path and pathlib.Path(full844_path).exists():
        with open(full844_path, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    ids.add(json.loads(line)["instrument_id"])
    if not ids:
        with zipfile.ZipFile(complete_zip_path) as z:
            ids = {r["instrument_id"] for r in _jsonl(z.read(PKG + "STAGE11_ACCEPTED.jsonl"))}
    return ids


def metas_for(path, sha, metas_by_sha, metas_by_dir_key):
    """The Opus cache .meta.json records that describe a file: by its sha256, and by a
    sibling .meta.json with the same stem in the same folder."""
    out = list(metas_by_sha.get(sha, [])) if sha else []
    key = member_key(path)
    if key:
        for x in metas_by_dir_key.get((path.rsplit("/", 1)[0] + "/", key), []):
            if x not in out:
                out.append(x)
    return out


def normalize_url(u):
    u = (u or "").strip().rstrip(".,;)")
    if u.startswith("http://"):
        u = "https://" + u[len("http://"):]
    return u.rstrip("/")


def meta_urls(m):
    return {normalize_url(m[k]) for k in ("url", "final_url") if isinstance(m.get(k), str) and m[k].startswith("http")}


_MEDIA_URL_EXT = re.compile(r"\.(?:pdf|png|jpe?g|tiff?|gif)$", re.I)


def is_media_url(u):
    """URLs that serve a PDF or image: ending in .pdf/.png/..., govinfo package /pdf/
    paths, and govinfo /link/ service URLs (which redirect to the PDF)."""
    path = (u or "").split("?", 1)[0].split("#", 1)[0]
    if _MEDIA_URL_EXT.search(path):
        return True
    return "govinfo.gov/" in path and ("/pdf/" in path or "/link/" in path)


def meta_is_media(m):
    ct = str(m.get("content_type") or "").lower()
    return ct.startswith(("application/pdf", "image/")) or any(is_media_url(u) for u in meta_urls(m))


def metas_by_stem_prefix(path, metas_by_dir):
    """.meta.json records in the same folder whose stem is the file's stem or a prefix of
    it (fr_1985-04-17.meta.json describes fr_1985-04-17_eo12509_pp3-9.txt)."""
    d, base = path.rsplit("/", 1) if "/" in path else ("", path)
    out = []
    for key, lst in metas_by_dir.get(d + "/", {}).items():
        if base == key or base.startswith((key + ".", key + "_", key + "-")):
            out.extend(lst)
    return out


def case_media_citations(case, metas_by_dir, packaged_urls, unpackaged_urls, packaged_names=None):
    """What PDFs/images an order's records cite, as local files and as URLs, and which of
    them have no bytes in the companion zip.

    A record may cite a PDF only by URL, or by a local .txt conversion whose .meta.json
    says the upstream was a PDF: then Opus kept only a text extract and the original
    media must be re-fetched. That is different from 'cites no media at all'."""
    media_paths = sorted(x for x in case.paths if x.lower().endswith(MEDIA_EXT))
    paths_not_packaged = [x for x in media_paths if x in UNPACKAGED]
    media_urls = {normalize_url(u) for u in case.urls if is_media_url(u)}
    text_kept = set()
    for p in case.paths:
        if p.lower().endswith(MEDIA_EXT):
            continue
        for _, m in metas_by_stem_prefix(p, metas_by_dir):
            if meta_is_media(m):
                us = meta_urls(m)
                media_urls |= us
                text_kept |= us
    # A URL counts as in the companion for this order when a companion file is the whole
    # document that URL served, or is a copy/excerpt kept in this order's own evidence or
    # review folder. An excerpt of a whole FR issue kept for another order does not count:
    # it usually holds other pages.
    dirs = tuple(d for d in (case.evidence_dir, case.review_dir) if d)
    in_companion = set()
    for u in media_urls:
        if any(whole or (dirs and d.startswith(dirs)) for d, whole in (packaged_urls or {}).get(u, ())):
            in_companion.add(u)
    # A companion file with no .meta.json still counts when its file name is the URL's file
    # name and it sits in this order's own evidence or review folder.
    for u in media_urls - in_companion:
        name = u.split("?", 1)[0].rsplit("/", 1)[-1].lower()
        if dirs and name and any(d.startswith(dirs) for d in (packaged_names or {}).get(name, ())):
            in_companion.add(u)
    elsewhere = {u for u in media_urls - in_companion if (packaged_urls or {}).get(u)}
    not_in = media_urls - in_companion - unpackaged_urls
    return {"media_paths": media_paths, "paths_not_packaged": paths_not_packaged, "media_urls": media_urls,
            "media_urls_in_companion": in_companion, "urls_not_in_companion": not_in,
            # Opus downloaded these originals but the release left them out (UNPACKAGED list)
            "urls_not_packaged": (media_urls & unpackaged_urls) - in_companion,
            "kept_only_as_text": text_kept & not_in,
            # only an excerpt kept for another order's folder exists (usually other pages)
            "only_other_orders_excerpt": elsewhere & not_in}


def order_text_span(heading_pages, own_quote_pages, max_gap=3):
    """Pages where an order's own printing sits: its heading page plus the neighbouring
    pages that carry quotes of its own text (gaps of at most max_gap pages), e.g.
    "PDF pages 1-2 (heading on p1)". Quote pages before the heading count too, because
    1930s orders print their number in the signature block at the end."""
    heading_pages = sorted(set(heading_pages))
    if not heading_pages:
        return "PDF/image page(s) unknown"
    start = heading_pages[0]
    end = heading_pages[-1]
    quotes = sorted(set(own_quote_pages))
    for p in quotes:
        if p > end and p - end <= max_gap:
            end = p
    for p in reversed(quotes):
        if p < start and start - p <= max_gap:
            start = p
    span = f"PDF page {start}" if start == end else f"PDF pages {start}-{end}"
    return span + f" (heading on p{page_ranges(heading_pages)})"


CONTENT_TYPES = {"pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg",
                 "html_saved_under_media_name": "text/html", "empty": "application/x-empty"}
DEFECTS = {"html_saved_under_media_name": "access_denied_or_error_html", "empty": "empty_file"}


def source_record(path, sha, size, kind, retrieved, text_rel, archival_id, container, upstream, res,
                  instrument_ids):
    """One shared-format source record for an archived member.

    `url` is filled only when the member's bytes are known to be exactly what that URL
    served (sha256 equal to the .meta.json sha256). For page excerpts, and for members
    whose upstream hash is unknown, the URL goes in `upstream_url` and `url` is null, so
    no merger can pair the URL with bytes it never served. Error pages and empty files
    are flagged usable_as_document=false and never carry a url."""
    m = upstream[1] if upstream else {}
    up_url = m.get("final_url") or m.get("url") or None
    up_sha = m.get("sha256") if isinstance(m.get("sha256"), str) else None
    same = (up_sha == sha) if up_sha else None
    defect = DEFECTS.get(kind)
    url = up_url if (same is True and not defect and (up_url or "").startswith("https://")) else None
    notes = []
    if defect:
        notes.append("NOT the document: the archived bytes are "
                     + ("an HTML error/access-denied page" if kind != "empty" else "0 bytes (an empty file)")
                     + " saved under a media file name; the upstream URL must be re-fetched.")
    notes.append("sha256/bytes are of the archived member bytes.")
    if same is False:
        notes.append("The upstream URL served a different, usually larger document (upstream_sha256); "
                     "this member is a page excerpt or conversion of it, so url is null and the claim-safe "
                     "reference is archival_id + local_file_sha256.")
    elif same is None and up_url:
        notes.append("The Opus .meta.json gives no sha256 for the upstream bytes, so it is not known whether "
                     "this member is exactly what upstream_url served; url is null.")
    notes.append("retrieved_utc is when this job read the member from the release zip; upstream_retrieved_utc "
                 "is when Opus fetched the upstream URL.")
    notes.append(f"Text: {res['method']}"
                 f"{' + OCR pages ' + page_ranges(res['ocr_pages']) if res['ocr_pages'] else ''}.")
    return {
        "source_id": f"opus-media:{path}",
        "instrument_ids": [] if defect else instrument_ids,
        "url": url,
        "sha256": sha, "bytes": size,
        "content_type": CONTENT_TYPES.get(kind, "application/octet-stream"),
        "retrieved_utc": retrieved,
        "route": ("opus_stage11_evidence_originals_zip_member (read in place); upstream URL from the Opus "
                  "cache .meta.json when present" + ("; FAILED CAPTURE" if defect else "")),
        "page_or_item": f"zip member {PKG}{path}",
        "text_path": text_rel,  # for an error page: what the page said
        "cache_path": None,
        "archival_id": archival_id,
        "local_file_sha256": sha,
        "archive_container": container,
        "upstream_url": up_url if (up_url or "").startswith(("https://", "http://")) else None,
        "upstream_sha256": up_sha,
        "upstream_retrieved_utc": m.get("retrieved_utc") or None,
        "sha256_is_of_url_bytes": same,
        "usable_as_document": not defect,
        "defect": defect,
        "notes": " ".join(notes),
    }


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run(repo_root, output_dir, cache_dir=None, limit=None, ocr_enabled=True, paths=None, progress=print,
        ocr_max_pages=2000):
    repo_root = pathlib.Path(repo_root)
    out = pathlib.Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    P = {"media_zip": MEDIA_ZIP, "complete_zip": COMPLETE_ZIP, "member_map": MEMBER_MAP,
         "full_844": FULL_844, "note_leads": NOTE_LEADS, "integrity": INTEGRITY_JSON}
    P.update(paths or {})
    rp = {k: (repo_root / v if v else None) for k, v in P.items()}
    started = utc_now()

    accepted = read_accepted(rp["full_844"], rp["complete_zip"])
    leads = []
    if rp["note_leads"] and rp["note_leads"].exists():
        leads = [json.loads(x) for x in rp["note_leads"].read_text(encoding="utf-8").splitlines() if x.strip()]
    progress(f"Reading Opus case records from {P['complete_zip']} ...")
    cases, metas = load_cases(rp["complete_zip"], accepted, leads)
    known = {c.num for c in cases.values() if c.num}
    nquotes = sum(len(c.quotes) for c in cases.values())
    progress(f"  {len(cases)} orders in the Stage 11 records ({len(accepted)} accepted), {nquotes} quotes, "
             f"{len(metas)} cache meta files.")
    quotes_index = [(c.id, q) for c in cases.values() for q in c.quotes if q["spec"] >= MIN_SPECIFIC_QUOTE_CHARS]
    metas_by_sha = collections.defaultdict(list)
    metas_by_dir_key = collections.defaultdict(list)
    metas_by_dir = {}  # folder -> {meta stem: [(path, meta)]}
    for mp, m in metas.items():
        for k in ("excerpt_sha256", "sha256", "excerpt_pdf_sha256"):
            if isinstance(m.get(k), str):
                metas_by_sha[m[k]].append((mp, m))
        key = member_key(mp)
        if key:
            metas_by_dir_key[(mp.rsplit("/", 1)[0] + "/", key)].append((mp, m))
        mkey = mp.rsplit("/", 1)[-1][: -len(".meta.json")]
        metas_by_dir.setdefault(mp.rsplit("/", 1)[0] + "/", {}).setdefault(mkey, []).append((mp, m))

    member_map = read_member_map(rp["member_map"])
    integrity = {}
    if rp["integrity"] and rp["integrity"].exists():
        integrity = json.loads(rp["integrity"].read_text(encoding="utf-8"))
    media_zip_sha = sha256_file(rp["media_zip"])
    media_zip_bytes = rp["media_zip"].stat().st_size
    expected_zip_sha = integrity.get("media_archive_sha256")
    ocr = Ocr(enabled=ocr_enabled, max_pages=ocr_max_pages, tmpdir=cache_dir)
    progress(f"OCR: {'tesseract' if ocr.images else 'not available'}"
             f"{' + pdftoppm' if ocr.pdfs else ''}{'' if ocr_enabled else ' (disabled)'}")

    text_dir = out / "text"
    text_dir.mkdir(exist_ok=True)
    member_rows, match_rows, sources, fragments = [], [], [], []
    by_case = collections.defaultdict(lambda: {"unique": [], "ambiguous": [], "order_text": [], "record_link": []})
    kinds = collections.Counter()
    sha_ok = sha_bad = sha_unknown = 0
    pages_needing_ocr = 0
    members_needing_ocr = 0
    members_ocr_done = 0
    members_no_text_at_all = 0
    pages_ocr_done = 0
    feats_cache = {}
    quote_member_shas = collections.defaultdict(set)
    pending = []  # (info, sha, res, mf, quote_hits)

    with zipfile.ZipFile(rp["media_zip"]) as zm:
        infos = sorted([i for i in zm.infolist() if not i.is_dir()], key=lambda i: i.filename)
        total_members = len(infos)
        chosen = select_members(infos, limit)
        progress(f"Media members: {total_members}; processing {len(chosen)}.")
        for n, info in enumerate(chosen, start=1):
            path = info.filename[len(PKG):] if info.filename.startswith(PKG) else info.filename
            data = zm.read(info)
            sha = sha256_bytes(data)
            mm = member_map.get(path)
            if mm is None:
                sha_unknown += 1
                sha_status = "not_in_member_map"
            elif mm["sha256"] == sha:
                sha_ok += 1
                sha_status = "matches_member_map"
            else:
                sha_bad += 1
                sha_status = "MISMATCH_member_map"
            kind = sniff_kind(data, path)
            kinds[kind] += 1
            if sha in feats_cache:
                res, mf_pages = feats_cache[sha]
            else:
                res = extract_member_text(data, kind, ocr, cache_dir, sha)
                mf_pages = res["pages"]
                feats_cache[sha] = (res, mf_pages)
            mf = MemberFeatures(path, sha, mf_pages, known)
            metas_for_member = metas_for(path, sha, metas_by_sha, metas_by_dir_key)
            # candidate orders for near-quote search: any order whose records or folders touch this file
            near = set()
            for c in cases.values():
                if (c.evidence_dir and mf.dir.startswith(c.evidence_dir)) or \
                        (c.review_dir and mf.dir.startswith(c.review_dir)) or \
                        sha in c.hashes or path in c.paths or (c.num and c.num in mf.eo_pages):
                    near.add(c.id)
            qh = find_quote_hits(mf.pt, quotes_index, near, cases)
            for cid, lst in qh.items():
                for q, pg, mode in lst:
                    if mode == "verbatim":
                        quote_member_shas[q["segs"]].add(sha)
            pending.append((info, path, sha, sha_status, kind, res, mf, metas_for_member, qh, near))
            if n % 25 == 0 or n == len(chosen):
                progress(f"  read {n}/{len(chosen)} members")

    # second pass: drop boilerplate quotes (found verbatim in many different files), score, write
    generic = {segs for segs, shas in quote_member_shas.items() if len(shas) > GENERIC_QUOTE_MAX_MEMBERS}
    for c in cases.values():
        for q in c.quotes:
            q["files"] = len(quote_member_shas.get(q["segs"], ()))
    retrieved = utc_now()
    written_text = set()
    for info, path, sha, sha_status, kind, res, mf, metas_for_member, qh, near in pending:
        pages = res["pages"]
        no_text = res["pages_without_text"]
        need_ocr = len(no_text) if kind in ("pdf", "png", "jpg") else 0
        if need_ocr:
            members_needing_ocr += 1
            if need_ocr == len(pages):
                members_no_text_at_all += 1
            pages_needing_ocr += need_ocr
        if res["ocr_pages"]:
            members_ocr_done += 1
            pages_ocr_done += len(res["ocr_pages"])
        text_rel = None
        if any(p.strip() for p in pages):
            text_rel = f"text/{sha}.txt"
            if sha not in written_text:
                write_text_lf(out / text_rel, "\f".join(pages))
                written_text.add(sha)
        upstream = None
        for mp, m in metas_for_member:
            if m.get("excerpt_sha256") == sha or m.get("sha256") == sha or m.get("excerpt_pdf_sha256") == sha:
                upstream = (mp, m)
                break
        if upstream is None and metas_for_member:
            upstream = metas_for_member[0]
        up_url = upstream[1].get("final_url") or upstream[1].get("url") if upstream else None
        up_sha = upstream[1].get("sha256") if upstream else None

        member_pairs = []
        cand = set(qh) | near
        for c in cases.values():
            if c.id in cand:
                continue
            if (c.num and c.num in mf.eo_pages) or sha in c.hashes or path in c.paths:
                cand.add(c.id)
            elif mf.fn["fr_dates"] & c.fr_dates or mf.fn["stat"] & c.stat_cites or mf.fn["fr_docs"] & c.fr_docs \
                    or (c.num and c.num in mf.fn["eo"]):
                cand.add(c.id)
            elif any(d in mf.fr_date_pages for d in c.fr_dates):
                cand.add(c.id)
            elif any(mf.printed_page_hit(mf.stat_vol_pages, v, p) for v, p in c.stat_cites) or \
                    any(mf.printed_page_hit(mf.fr_vol_pages, v, p) for v, p in c.fr_cites):
                cand.add(c.id)
        for cid in sorted(cand, key=lambda x: (order_number(x) or "", x)):
            c = cases[cid]
            hits = [(q, pg, mode) for q, pg, mode in qh.get(cid, []) if q["segs"] not in generic]
            s = score_pair(mf, c, metas_for_member, hits)
            if not s:
                continue
            dir_hint = bool((c.evidence_dir and mf.dir.startswith(c.evidence_dir)) or
                            (c.review_dir and mf.dir.startswith(c.review_dir)))
            member_pairs.append((c, s, dir_hint))

        best = "unmatched"
        if any(s["grade"] == "unique_supported" for _, s, _ in member_pairs):
            best = "unique_supported"
        elif member_pairs:
            best = "ambiguous"
        reason = ""
        if not member_pairs:
            if kind == "empty":
                reason = "empty file (0 bytes)"
            elif kind == "html_saved_under_media_name":
                reason = "the saved bytes are a web page (often an access-denied page), not the document"
            elif need_ocr and not any(len(collapse(p)) >= PAGE_TEXT_MIN_CHARS for p in pages):
                reason = "no text layer; needs OCR"
            else:
                reason = "no signal for any Stage 11 order"
        n_unique = sum(1 for _, s, _ in member_pairs if s["grade"] == "unique_supported")
        n_amb = len(member_pairs) - n_unique
        archival_id = f"{ARCHIVE_ID_PREFIX}:{path}"
        member_rows.append({
            "member_path": path, "sha256": sha, "bytes": info.file_size, "kind": kind,
            "sha256_check": sha_status, "text_method": res["method"] + (" + OCR" if res["ocr_pages"] else ""),
            "pages": len(pages), "text_chars": sum(len(p) for p in pages),
            "pages_without_text": len(no_text), "needs_ocr": "yes" if need_ocr else "no",
            "ocr_pages_done": len(res["ocr_pages"]), "text_path": text_rel or "",
            "upstream_url": up_url or "", "upstream_sha256": up_sha or "",
            "filename_fr_dates": "|".join(sorted(mf.fn["fr_dates"])),
            "filename_stat": "|".join(f"{v} Stat. {p}" for v, p in sorted(mf.fn["stat"])),
            "filename_eo": "|".join(sorted(mf.fn["eo"])),
            "orders_numbered_on_pages": "|".join(sorted(mf.eo_pages, key=number_sort_key)[:60]),
            "fr_issue_dates_in_page_heads": "|".join(sorted(mf.fr_date_pages)),
            "best_grade": best, "unique_supported_orders": n_unique, "ambiguous_orders": n_amb,
            "note": reason or (res.get("error") or ""),
        })
        sources.append(source_record(
            path=path, sha=sha, size=info.file_size, kind=kind, retrieved=retrieved, text_rel=text_rel,
            archival_id=archival_id, container={"path": P["media_zip"], "sha256": media_zip_sha,
                                                 "bytes": media_zip_bytes},
            upstream=upstream, res=res,
            instrument_ids=sorted(c.id for c, s, _ in member_pairs if s["grade"] == "unique_supported")))
        if not member_pairs:
            match_rows.append({"member_path": path, "sha256": sha, "instrument_id": "", "in_accepted_844": "",
                               "grade": "unmatched", "role": "", "signal_families": "", "signals": "",
                               "page_refs": "", "content_verified": "no", "directory_hint": "",
                               "text_method": res["method"], "notes": reason})
        for c, s, dir_hint in member_pairs:
            sig = "; ".join(f"{f}:{d}" for f, ds in s["details"].items() for d in ds)
            match_rows.append({
                "member_path": path, "sha256": sha, "instrument_id": c.id,
                "in_accepted_844": "yes" if c.accepted else "no", "grade": s["grade"], "role": s["role"],
                "signal_families": "|".join(s["families"]), "signals": sig,
                "page_refs": page_ranges(s["pages"]), "content_verified": "yes" if s["content_verified"] else "no",
                "directory_hint": "yes" if dir_hint else "no", "text_method": res["method"],
                "notes": "; ".join(([] if s["content_verified"] is not False else
                                    ["bookkeeping signals only; page content not confirmed"
                                     + ("; needs OCR" if need_ocr else "")]) + s.get("notes", [])),
            })
            b = by_case[c.id]
            if s["grade"] == "unique_supported":
                b["unique"].append(path)
                if s["role"] == "order_text_candidate":
                    b["order_text"].append(path)
            else:
                b["ambiguous"].append(path)
            if "opus_record_link" in s["families"]:
                b["record_link"].append(path)
            if s["grade"] == "unique_supported" and s["role"] == "order_text_candidate":
                where = [order_text_span(s["heading_pages"] or s["pages"], s["own_quote_pages"])
                         + f" of archived member {path}"]
                if mf.fn["fr_dates"]:
                    where.append("Federal Register issue " + "/".join(sorted(mf.fn["fr_dates"])) + " (file name)")
                fr_pp = sorted(pp for v in mf.fr_vol_pages.values() for pp in v)
                if fr_pp:
                    where.append(f"printed FR page(s) {page_ranges(fr_pp)} (page heads)")
                ref = {"archival_id": archival_id, "local_file_sha256": sha, "sha256": sha,
                       "page_or_item": "; ".join(where)}
                if up_url and up_url.startswith("https://"):
                    ref["upstream_url"] = up_url
                    ref["upstream_sha256"] = up_sha
                fragments.append({
                    "instrument_id": c.id, "kind": "original_representation",
                    "data": dict(ref, status="candidate_unverified",
                                 match_signals=[f"{f}:{d}" for f, ds in s["details"].items() for d in ds]),
                    "sources": [ref],
                    "confidence_note": ("Machine content match: the order's number is printed as a heading on the page "
                                        "and a quote from the order's own Opus evidence, or the Opus file name, agrees. "
                                        "A person must read the page and confirm it is this order's original text, "
                                        "complete, and the official printing. Not a legal finding."),
                    "produced_by": JOB_NAME,
                })

    # per-order status
    # Which upstream URLs have bytes in the companion zip, and which belong to originals
    # left out as too large. Uses every zip member (via the Stage 20 hash list and a peek
    # at each member's first bytes), not only the ones read under JOB_LIMIT. Error pages
    # and empty files saved under media names do not count as packaged originals.
    packaged_urls = collections.defaultdict(list)   # url -> [(member folder, member is the whole document)]
    unpackaged_urls = set()
    packaged_names = collections.defaultdict(set)   # lower-case file name -> folders holding it
    with zipfile.ZipFile(rp["media_zip"]) as zm:
        for info in infos:
            mpath = info.filename[len(PKG):] if info.filename.startswith(PKG) else info.filename
            with zm.open(info) as fh:
                if DEFECTS.get(sniff_kind(fh.read(1024), mpath)):
                    continue
            mdir = mpath.rsplit("/", 1)[0] + "/" if "/" in mpath else ""
            if mdir:
                packaged_names[mpath.rsplit("/", 1)[1].lower()].add(mdir)
            msha = (member_map.get(mpath) or {}).get("sha256")
            for _, m in metas_for(mpath, msha, metas_by_sha, metas_by_dir_key) + metas_by_stem_prefix(mpath, metas_by_dir):
                for u in meta_urls(m):
                    packaged_urls[u].append((mdir, bool(msha and m.get("sha256") == msha)))
    # Expected bytes of each left-out original, so a re-fetch can prove it got the same file.
    expected_by_url = {}
    for upath in UNPACKAGED:
        for _, m in metas_for(upath, None, metas_by_sha, metas_by_dir_key) + metas_by_stem_prefix(upath, metas_by_dir):
            unpackaged_urls.update(meta_urls(m))
            # The .meta.json sha256 is of the bytes Opus downloaded from the URL (the list's
            # own sha256 is of whichever file was left out, often only the text extract).
            ctype = str(m.get("content_type") or "").lower()
            local = str(m.get("local_file") or "").lower()
            if ctype.startswith(("application/pdf", "image/")) or local.endswith((".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff")):
                for u in meta_urls(m):
                    expected_by_url.setdefault(u, {"sha256": m.get("sha256"), "bytes": m.get("bytes"),
                                                   "opus_path": m.get("local_file") or upath})
    refetch = {}  # url -> {"instrument_ids": set, "reasons": set}
    case_rows = []
    for c in sorted(cases.values(), key=lambda x: (not x.accepted, number_sort_key(x.num), x.id)):
        b = by_case.get(c.id, {"unique": [], "ambiguous": [], "order_text": [], "record_link": []})
        status = "unique_supported" if b["unique"] else ("ambiguous_only" if b["ambiguous"] else "no_member_signal")
        mc = case_media_citations(c, metas_by_dir, packaged_urls, unpackaged_urls, packaged_names)
        cited_media = mc["media_paths"]
        not_packaged = mc["paths_not_packaged"]
        n_unpk = len(not_packaged) + len(mc["urls_not_packaged"])
        if not cited_media and not mc["media_urls"]:
            gap = "none_cited"
        elif mc["urls_not_in_companion"]:
            gap = "originals_not_in_companion"     # Opus kept only a text extract, or nothing
        elif n_unpk:
            gap = "cited_files_not_packaged"       # Opus kept them; the release left them out (size)
        else:
            gap = ""                               # every cited PDF/image has bytes in the companion
        if status != "no_member_signal":
            note = ""
        elif gap == "none_cited":
            note = ("the order's Opus records cite no PDF or image, neither as a file nor as a URL (only HTML/XML/JSON/"
                    "text sources), so the companion has nothing to match; candidate for 'not applicable' for this "
                    "matching step only (the owner decides). It does not mean no official printed copy exists")
        elif gap == "originals_not_in_companion":
            note = (f"its records cite {len(mc['urls_not_in_companion'])} PDF/image URL(s) whose original bytes are "
                    f"not in the companion zip for this order (Opus kept only a text extract for "
                    f"{len(mc['kept_only_as_text'])} of them; for {len(mc['only_other_orders_excerpt'])} the companion "
                    "holds only an excerpt kept for another order, usually other pages); the originals must be "
                    "re-fetched from the URL, so this is NOT 'not applicable'"
                    + (f"; {n_unpk} more were downloaded by Opus but left out of the release as too large "
                       "(UNPACKAGED_LARGE_ORIGINALS.jsonl)" if n_unpk else ""))
        elif gap == "cited_files_not_packaged":
            note = (f"{n_unpk} PDF/image original(s) its records cite were downloaded by Opus but left out of the "
                    "release as too large (UNPACKAGED_LARGE_ORIGINALS.jsonl); re-fetch them from the URL in their "
                    ".meta.json, so this is NOT 'not applicable'")
        else:
            note = "its records cite PDF/image files or URLs that are in the companion, but none of those files gave a signal"
        resolved = (status == "unique_supported" and not b["ambiguous"] and not mc["urls_not_in_companion"]
                    and not n_unpk)
        # Every cited original missing from the companion goes on the re-fetch list.
        missing = {u: "left_out_of_release_too_large" for u in mc["urls_not_packaged"]}
        for path_ in not_packaged:
            for _, m in metas_for(path_, None, metas_by_sha, metas_by_dir_key) + metas_by_stem_prefix(path_, metas_by_dir):
                for u in meta_urls(m):
                    if u.startswith("https://"):
                        missing.setdefault(u, "left_out_of_release_too_large")
        for u in mc["urls_not_in_companion"]:
            missing.setdefault(u, "original_not_kept_by_opus")
        for u, why in missing.items():
            r = refetch.setdefault(u, {"instrument_ids": set(), "reasons": set()})
            r["instrument_ids"].add(c.id)
            r["reasons"].add(why)
        case_rows.append({
            "instrument_id": c.id, "in_accepted_844": "yes" if c.accepted else "no", "media_status": status,
            "all_cited_media_resolved": "yes" if resolved else "no",
            "unique_supported_members": len(set(b["unique"])), "ambiguous_members": len(set(b["ambiguous"])),
            "order_text_candidate_members": len(set(b["order_text"])),
            "unique_supported_cited_source_members": len(set(b["unique"]) - set(b["order_text"])),
            "members_linked_by_opus_records": len(set(b["record_link"])),
            "example_unique_supported_members": " | ".join(sorted(set(b["unique"]))[:5]),
            "media_files_cited_in_case_records": len(cited_media),
            "cited_media_not_packaged": len(not_packaged),
            "media_urls_cited_in_case_records": len(mc["media_urls"]),
            "cited_media_urls_not_in_companion": len(mc["urls_not_in_companion"]),
            "cited_media_urls_not_packaged": len(mc["urls_not_packaged"]),
            "cited_media_kept_only_as_text": len(mc["kept_only_as_text"]),
            "cited_media_only_excerpt_kept_for_other_order": len(mc["only_other_orders_excerpt"]),
            "media_gap": gap,
            "example_media_urls_missing": " | ".join(sorted(mc["urls_not_in_companion"] | mc["urls_not_packaged"])[:3]),
            "note": note,
        })

    def write_csv(name, rows, fields):
        with open(out / name, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
            w.writeheader()
            for r in rows:
                w.writerow(r)

    match_fields = ["member_path", "sha256", "instrument_id", "in_accepted_844", "grade", "role",
                    "signal_families", "signals", "page_refs", "content_verified", "directory_hint",
                    "text_method", "notes"]
    write_csv("MATCHES.csv", match_rows, match_fields)
    write_csv("MEMBERS.csv", member_rows, list(member_rows[0].keys()) if member_rows else ["member_path"])
    write_csv("OPUS_CASE_MEDIA_STATUS.csv", case_rows, list(case_rows[0].keys()) if case_rows else ["instrument_id"])
    with open(out / "SOURCES.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for s in sources:
            fh.write(json.dumps(s, ensure_ascii=False, sort_keys=True) + "\n")
    with open(out / "FRAGMENTS.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for f in fragments:
            fh.write(json.dumps(f, ensure_ascii=False, sort_keys=True) + "\n")
    # Re-fetch list for the source-ladder job (it reads this file automatically).
    accepted_ids = {c.id for c in cases.values() if c.accepted}
    refetch_rows = []
    for u, r in refetch.items():
        exp = expected_by_url.get(u) or {}
        ids = sorted(r["instrument_ids"])
        refetch_rows.append({
            "url": u, "instrument_ids": ids, "accepted_844_ids": [i for i in ids if i in accepted_ids],
            "reasons": sorted(r["reasons"]), "expected_sha256": exp.get("sha256"),
            "expected_bytes": exp.get("bytes"), "opus_path": exp.get("opus_path"),
        })
    refetch_rows.sort(key=lambda x: (-len(x["accepted_844_ids"]), -len(x["instrument_ids"]), x["url"]))
    with open(out / "REFETCH_LIST.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for row in refetch_rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    acc_rows = [r for r in case_rows if r["in_accepted_844"] == "yes"]
    grades = collections.Counter(r["grade"] for r in match_rows)
    summary = {
        "job": JOB_NAME, "started_utc": started, "finished_utc": utc_now(), "legal_cutoff": LEGAL_CUTOFF,
        "limit": limit,
        "inputs": {
            "media_zip": {"path": P["media_zip"], "sha256": media_zip_sha, "bytes": media_zip_bytes,
                          "matches_stage20_integrity_record": (media_zip_sha == expected_zip_sha) if expected_zip_sha else None},
            "complete_zip": P["complete_zip"], "member_map": P["member_map"], "accepted_list": P["full_844"],
        },
        "members_in_zip": total_members, "members_processed": len(pending),
        "distinct_sha256_processed": len({p[2] for p in pending}),
        "member_kinds": dict(kinds),
        "sha256_check": {"matches_member_map": sha_ok, "mismatch": sha_bad, "not_in_member_map": sha_unknown},
        "text": {
            "members_with_some_text": sum(1 for r in member_rows if r["text_path"]),
            "members_needing_ocr": members_needing_ocr, "pages_needing_ocr": pages_needing_ocr,
            "members_needing_ocr_with_no_text_at_all": members_no_text_at_all,
            "members_needing_ocr_for_some_blank_pages_only": members_needing_ocr - members_no_text_at_all,
            "ocr_available": {"images": ocr.images, "pdf_pages": ocr.pdfs, "enabled": ocr_enabled},
            "members_ocr_done": members_ocr_done, "pages_ocr_done": pages_ocr_done,
            "ocr_pages_attempted_this_run": ocr.used, "ocr_failures_this_run": ocr.failures,
            "ocr_failure_examples": ocr.failure_notes,
        },
        "stage11_orders_in_records": len(cases), "quotes_indexed": len(quotes_index),
        "refetch_list": {"urls": len(refetch_rows),
                         "urls_with_expected_sha256": sum(1 for r in refetch_rows if r["expected_sha256"]),
                         "accepted_orders_covered": len({i for r in refetch_rows for i in r["accepted_844_ids"]})},
        "boilerplate_quotes_dropped": len(generic),
        "pairs_by_grade": {k: v for k, v in grades.items() if k != "unmatched"},
        "members_by_best_grade": dict(collections.Counter(r["best_grade"] for r in member_rows)),
        "unmatched_members": grades.get("unmatched", 0),
        "accepted_844": {
            "orders": len(acc_rows),
            "with_unique_supported_member": sum(1 for r in acc_rows if r["media_status"] == "unique_supported"),
            "ambiguous_only": sum(1 for r in acc_rows if r["media_status"] == "ambiguous_only"),
            "no_member_signal": sum(1 for r in acc_rows if r["media_status"] == "no_member_signal"),
            "no_member_signal_because_records_cite_no_media_at_all": sum(
                1 for r in acc_rows if r["media_status"] == "no_member_signal" and r["media_gap"] == "none_cited"),
            "no_member_signal_because_cited_originals_not_in_companion": sum(
                1 for r in acc_rows if r["media_status"] == "no_member_signal"
                and r["media_gap"] == "originals_not_in_companion"),
            "no_member_signal_because_cited_files_not_packaged": sum(
                1 for r in acc_rows if r["media_status"] == "no_member_signal"
                and r["media_gap"] == "cited_files_not_packaged"),
            "no_member_signal_other": sum(
                1 for r in acc_rows if r["media_status"] == "no_member_signal" and not r["media_gap"]),
            "with_all_cited_media_resolved": sum(1 for r in acc_rows if r["all_cited_media_resolved"] == "yes"),
            "with_cited_media_urls_not_in_companion": sum(1 for r in acc_rows if r["cited_media_urls_not_in_companion"]),
            "with_order_text_candidate": sum(1 for r in acc_rows if r["order_text_candidate_members"]),
            "with_member_linked_by_opus_records": sum(1 for r in acc_rows if r["members_linked_by_opus_records"]),
        },
        "fragments_written": len(fragments),
        "sources": {
            "records": len(sources),
            "usable_as_document_false": sum(1 for x in sources if not x["usable_as_document"]),
            "url_set_bytes_verified_equal_to_url": sum(1 for x in sources if x["url"]),
            "excerpts_or_conversions_url_null": sum(1 for x in sources if x["sha256_is_of_url_bytes"] is False),
            "upstream_sha_unknown_url_null": sum(1 for x in sources if x["sha256_is_of_url_bytes"] is None
                                                 and x["upstream_url"]),
        },
        "qualification": ("Machine leads only. A unique_supported pair means the page content and at least one other "
                          "independent signal (or a specific verbatim quote) tie the file to the order; it does NOT "
                          "mean one order per file (one statute page can support dozens of orders). It does not "
                          "establish authenticity, completeness, the first effective end, or any legal status, and "
                          "it changes no provisional status, ledger or count."),
    }
    if limit:
        summary["note_on_limit"] = (f"JOB_LIMIT={limit}: only {len(pending)} of {total_members} members were read, "
                                    "so the per-order counts are partial.")
    write_text_lf(out / "SUMMARY.json", json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    return summary
