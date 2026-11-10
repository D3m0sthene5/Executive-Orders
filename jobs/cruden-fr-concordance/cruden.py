"""Cruden: a concordance of the 1936-1993 Federal Register and the Statutes at Large by executive-order number.

Named for Alexander Cruden, whose Complete Concordance (1737) listed every place each word of the Bible appears, so a
reader could find every passage by one word. This job does the same for an order's number: for each target order it
asks govinfo's full-text search which Federal Register issues (1936-1993, the years selden-fr-citers does not reach)
and which Statutes at Large pages print "Executive Order No. N", downloads each hit once, and locates every sentence
that cites the order with jobs/selden-common (Selden's locator: citation forms, relation words, negation, the target
printed as actor). Zero model tokens.

Discovery only. A located sentence is a lead to what a later document says, never a finding that it ended or changed
the order. A target with no hit, or with hits but no acting sentence, gets a search record and nothing else: a
concordance's silence is never evidence about an order (D-20261028-evidence-decides).

Identity (cruden-locate-3, after two passes of the 2026-11-10 hostile review). A sentence is published with its printed relation
only when a citation in it prints a date equal to the target's own date. A sentence whose printed dates all disagree,
whose number runs into more digits or a letter, that sits inside the order's own printing, or that names another
issuer, is refused (kept in LOCATED.csv, never published). A sentence with no printed date, an index or contents
entry, an exception or savings sentence, or bytes that cannot be re-hashed is published as a pointer only
(mechanism cross_reference). The acting instrument is named only when the citation lies inside that instrument's own
printed span (a standalone heading through its filing line); otherwise the page is the actor (NOTICE:...). No status,
census, codebook or count changes. Human-certified: 0.
"""
from __future__ import annotations

import concurrent.futures
import csv
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
JOBS = HERE.parent
for p in ("_lib", "selden-common", "fr-pages", "official-fixity"):
    sys.path.insert(0, str(JOBS / p))
from fetch_pool import FetchPool, FetchError  # noqa: E402
import selden_common as S  # noqa: E402  (read-only reuse: locator, fragment and source records, controls)

csv.field_size_limit(min(2 ** 31 - 1, 10 ** 9))
LOCATOR = "cruden-locate-4"
UA = "EO-Road-System/1.0 (Cruden concordance of the Federal Register by order number; owner-run research)"
SEARCH_URL = "https://api.govinfo.gov/search"
FR_PDF = "https://www.govinfo.gov/content/pkg/{pkg}/pdf/{pkg}.pdf"
GRANULE_PDF = "https://www.govinfo.gov/content/pkg/{pkg}/pdf/{gran}.pdf"
FR_FIRST, FR_LAST = "1936-03-14", "1993-12-31"
PRODUCER = "cruden-fr-concordance"
MIN_RECALL = 0.6  # planted positives that must be located for a run's controls to pass
MIN_PUBLISHED_RECALL = 0.4  # planted positives whose dated sentence must also be published as acting
GRADE_FR = ("government_printed_federal_register_issue (govinfo scan of the daily Federal Register; text is the scan's "
            "OCR layer)")
GRADE_STAT = "government_printed_statutes_at_large_page (govinfo scan; text is the scan's OCR layer)"

MONTHS = ("January|February|March|April|May|June|July|August|September|October|November|December|"
          r"Jan\.?|Feb\.?|Mar\.?|Apr\.?|Jun\.?|Jul\.?|Aug\.?|Sept?\.?|Oct\.?|Nov\.?|Dec\.?")
DATE_RE = re.compile(r"\b(" + MONTHS + r")\s+(\d{1,2})\s*,?\s*(1[6-9]\d\d|20\d\d)(?!\d)")
DATE_DMY = re.compile(r"\b(\d{1,2})\s+(" + MONTHS + r")\s*,?\s*(1[6-9]\d\d|20\d\d)(?!\d)")
MON = {m[:3].lower(): i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct",
                                               "nov", "dec"], 1)}
# Another issuer of numbered "executive orders": grammar after the number ('of the Governor General', 'of the State of
# California'), or the issuer printed just before it ("Governor's Executive Order", "Canal Zone Executive Order",
# "by his Executive Order"). Subject words ('lands in the Territory of Alaska') do not count.
ISSUER_WORDS = (r"Governor[\s-]*General|Governor|Military\s+Governor|High\s+Commissioner|Commissioner|Mayor|"
                r"Tribal\s+Council|Council|Secretary|Commonwealth|State\s+of\s+\w+|Territory\s+of\s+\w+|"
                r"Philippine\s+Islands|Government\s+of\s+the\s+Philippine|Canal\s+Zone|Puerto\s+Rico|Porto\s+Rico|Hawaii")
ISSUER_AFTER = re.compile(r"^[\s,]*(?:No\.?\s*)?(?:of\s+\w+\s+\d{1,2},?\s+\d{4},?\s*)?(?:of|by|issued\s+by)\s+(?:the\s+)?"
                          r"(?:" + ISSUER_WORDS + r")\b", re.I)
ISSUER_BEFORE = re.compile(r"(?:Governor'?s|Governor[\s-]*General'?s|Commissioner'?s|Mayor'?s|Canal\s+Zone|Philippine|"
                           r"Puerto\s+Rico|Porto\s+Rico|Commonwealth|Territorial|State|Tribal|Military\s+Governor'?s)"
                           r"\s*(?:\(\s*)?$", re.I)
POSSESSIVE_BEFORE = re.compile(r"\b(?:his|its)\s*$", re.I)  # 'by his Executive Order': unclear issuer, pointer only
# Exception and savings wording that can keep the target out of an act (review N5: 'subject to valid existing
# rights', 'save', 'exclud' are ordinary in acting sentences and no longer demote them).
EXCEPTION = re.compile(r"\bexcept\b|\bexcepting\b|\bother\s+than\b|with\s+the\s+exception\s+of|"
                       r"not\s+so\s+as\s+to\s+affect|shall\s+not\s+(?:be\s+)?(?:affect|revoke|modify|appl)|"
                       r"does\s+not\s+(?:otherwise\s+)?(?:affect|revoke|modify|amend)|nothing\s+in\s+this", re.I)
# A filing line whose OCR is damaged ('[P. E. Doe. 50-1234; Filed') still carries the filing time or 'Filed, <date>'.
LOOSE_FILING = re.compile(r"Filed,?\s+[A-Z][a-z]{2,4}\.?\s+\d{1,2},\s+\d{4}|\d{1,2}:\d{2}\s*[ap]\.\s?m\.")
# A new document's agency header ends the previous instrument's span (review finding 2).
AGENCY_HEADER = re.compile(r"(?m)^[ \t]*(?:TITLE\s+\d+|Chapter\s+[IVXL]+|(?:DEPARTMENT|BUREAU|OFFICE|COMMISSION|"
                           r"ADMINISTRATION|BOARD|AGENCY|DIVISION|CORPS|SERVICE|AUTHORITY|COUNCIL)\b[A-Z ,.&'-]*|"
                           r"[A-Z][A-Z .,&'-]{3,}\s+(?:SERVICE|BUREAU|ADMINISTRATION|COMMISSION|DEPARTMENT|OFFICE)|"
                           r"(?:Department|Bureau|Office)\s+of\s+[A-Z][\w ]+|[A-Z][a-z]+\s+Service)[ \t]*$")
SPAN_CAP = 6000  # characters from a heading to a citation it may govern
LEADER = re.compile(r"(?:[._]\s?){4,}\s*\d{1,5}\s*$|_{3,}\s*\d{1,5}\b", re.M)  # contents / index leaders


def _spaced(ws):
    return r"\s+".join(r"\s?".join(re.escape(c) for c in w) for w in ws)


def _heading(words, digits):
    """A standalone heading line: '[Public Land Order 945]' or a capital line 'PUBLIC LAND ORDER 2100'."""
    mixed, caps = _spaced(words), _spaced([w.upper() for w in words])
    return re.compile(r"(?m)^[ \t]*(?:\[\s*(?i:" + mixed + r")\s*(?:N\s?[Oo]\.?\s*)?(" + digits + r")\s*\]|"
                      + caps + r"\s*(?:N\s?[Oo]\.?\s*)?(" + digits + r"))[ \t]*$")


HEADINGS = [
    ("PLO", _heading(["Public", "Land", "Order"], r"\d{1,4}")),
    ("PROC", _heading(["Proclamation"], r"\d{4}")),
    ("EO", _heading(["Executive", "Order"], r"\d{4,5}")),
    # 1936-37 form: 'EXECUTIVE ORDER' (or 'PROCLAMATION') on its own line, the title, then '[No. 7500]' on its own
    # line. The tag alone does not say which series: tag_kind() decides from the title block around it.
    ("TAG", re.compile(r"(?m)^[ \t]*\[\s*N\s?[Oo]\.?\s*(\d{4,5})\s*[\]1lI|]\s*$")),
]
TAG_EO = re.compile(r"(?m)^[ \t]*" + _spaced(["EXECUTIVE", "ORDER"]) + r"[ \t]*$")
TAG_PROC = re.compile(r"(?m)^[ \t]*(?:A\s+)?" + _spaced(["PROCLAMATION"]) + r"[ \t]*$")
# A relation word whose subject is a regulation, section or table ('Section 1.1(c), Customs Regulations, is amended by
# deleting "Hyder (E. O. 3808)"'): it changes the regulation, not the order (third review, run 42867104942).
REG_SUBJECT = re.compile(r"(?:\bs?ection|\bsections|§|\bsec\.|\bpart|\bparagraph|\bsubparagraph|\btable|\bregulations?|\brules?|"
                         r"\bschedule|\bsubdivision|\bcolumn)\b[^;]{0,200}?\b(?:is|are)\s+(?:hereby\s+)?(?:further\s+)?"
                         r"(?:amended|revised|modified|extended|corrected|redesignated)\b", re.I)
# The order cited as the authority or the description another act relies on, not the order acted on.
AUTHORITY_BEFORE = re.compile(r"(?:pursuant\s+to|in\s+accordance\s+with|under(?:\s+the\s+authority\s+of)?|"
                              r"by\s+virtue\s+of|as\s+provided\s+in|as\s+directed\s+by|delegated\s+by|vested\s+in\s+"
                              r"(?:me|him|the\s+\w+)\s+by|described\s+in|including\s+(?:the\s+)?territory\s+described\s+in|"
                              r"authorized\s+by|prescribed\s+(?:by|in)|issued\s+under)\s*(?:section\s+[\w().]+\s+of\s+)?"
                              r"(?:the\s+)?$", re.I)
# 'the name of which was by Executive Order No. N changed', 'as modified by E. O. N': the target is the actor.
BY_BEFORE = re.compile(r"\bby\s+(?:(?:E\.\s?O\.|Ex\.\s?Ord\.|Executive\s+Orders?)\s*(?:Nos?\.?\s*)?[\d-]+[A-Z]?[^;]{0,80}?"
                       r"\band\s+)?(?:the\s+)?$", re.I)
# A citation in parentheses ('St. Paul (E.O. 4295, Aug. 26, 1925)', '(as continued by ...)') is a reference.
PAREN_BEFORE = re.compile(r"\(\s*(?:see\s+|as\s+\w+\s+by\s+|including\s+)?$", re.I)


def tag_kind(text, start, end):
    """'EO', 'PROC' or None for a bare '[No. N]' tag: the series named by a standalone 'EXECUTIVE ORDER' or
    '(A) PROCLAMATION' line in the title block (300 characters before the tag, 600 after). Both or neither: None."""
    lo, hi = max(0, start - 300), min(len(text), end + 600)
    eo, proc = bool(TAG_EO.search(text, lo, hi)), bool(TAG_PROC.search(text, lo, hi))
    if eo and not proc:
        return "EO"
    if proc and not eo:
        return "PROC"
    return None
CONTINUES = re.compile(r"(?:\band|\bor|\bof|\bto|\bby|,|;|:|-|revoking|amending|modifying|superseding|see)\s*$", re.I)


def now_utc():
    return S.now_utc()


def read_csv(p):
    if not Path(p).is_file():
        return []
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def tool_versions():
    v = {"pypdf": "", "pdftotext": ""}
    try:
        import pypdf
        v["pypdf"] = pypdf.__version__
    except ImportError:
        pass
    exe = shutil.which("pdftotext")
    if exe:
        try:
            r = subprocess.run([exe, "-v"], capture_output=True, timeout=30)
            v["pdftotext"] = (r.stderr or r.stdout).decode("utf-8", "replace").splitlines()[0].strip()
        except (OSError, subprocess.SubprocessError, IndexError):
            v["pdftotext"] = "unknown"
    return v


# ---- queries -----------------------------------------------------------------------------------------------------

def forms(target):
    """The printed forms govinfo is asked for. Suffixed numbers ('2656A') also as '2656-A'."""
    eo = S.parse_eo(target)
    if not eo:
        return []
    num, suf, _ = eo
    nums = [num + suf, f"{num}-{suf}"] if suf else [num]
    out = []
    for n in nums:
        out += [f'"Executive Order No. {n}"', f'"Executive Order {n}"', f'"E. O. {n}"', f'"E.O. {n}"']
    return out


def next_day(iso):
    try:
        return (dt.date.fromisoformat(iso) + dt.timedelta(days=1)).isoformat()
    except (TypeError, ValueError):
        return None


def query(target, collection, target_date):
    """FR: from the day after the order's own date, so its own first printing on the day is not asked for (its
    printing a few days later is refused by the own-printing rule)."""
    q = f"collection:{collection} AND (" + " OR ".join(forms(target)) + ")"
    if collection == "FR":
        lo = max(next_day(target_date) or FR_FIRST, FR_FIRST)
        q += f" AND publishdate:range({lo},{FR_LAST})"
    return q


class Searcher:
    """govinfo's documented search API (POST, key in the X-Api-Key header, never in a URL or log)."""

    def __init__(self, key, opener=None, min_interval=1.0, max_searches=2500):
        self.key, self.opener = key, opener or urllib.request.urlopen
        self.min_interval, self.max_searches = min_interval, max_searches
        self.n, self.last, self.stopped, self.rate_limit = 0, 0.0, "", ""
        self.lock = threading.Lock()

    def search(self, q, page_size=100, order="ASC"):
        with self.lock:
            if self.stopped:
                raise FetchError("search stopped: " + self.stopped)
            if self.n >= self.max_searches:
                raise FetchError("search budget spent")
            wait = self.last + self.min_interval - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self.last = time.monotonic()
            self.n += 1
        body = json.dumps({"query": q, "pageSize": str(page_size), "offsetMark": "*",
                           "sorts": [{"field": "publishdate", "sortOrder": order}]}).encode()
        req = urllib.request.Request(SEARCH_URL, data=body, method="POST",
                                     headers={"Content-Type": "application/json", "User-Agent": UA,
                                              "X-Api-Key": self.key})
        try:
            with self.opener(req, timeout=60) as r:
                raw = r.read(5_000_001)
                hdr = getattr(r, "headers", None)
                if hdr is not None:
                    lim, rem = hdr.get("X-RateLimit-Limit"), hdr.get("X-RateLimit-Remaining")
                    with self.lock:
                        self.rate_limit = lim or self.rate_limit
                        if rem is not None and rem.isdigit() and int(rem) < 5:
                            self.stopped = f"rate limit nearly spent (limit {lim}, remaining {rem}); next run continues"
        except urllib.error.HTTPError as e:
            if e.code in (429, 403):
                with self.lock:
                    self.stopped = f"HTTP {e.code} from the search API"
            raise FetchError(f"search HTTP {e.code}")
        if len(raw) > 5_000_000:
            raise FetchError("search response too large")
        d = json.loads(raw)
        hits = []
        for x in d.get("results") or []:
            hits.append({"package": x.get("packageId") or "", "granule": x.get("granuleId") or "",
                         "date": x.get("dateIssued") or "", "title": (x.get("title") or "")[:200]})
        return {"count": d.get("count"), "hits": hits, "sha256": S.sha256(raw)}


def api_key(env):
    for name in ("API_DATA_GOV_KEY", "GOVINFO_API_KEY"):
        v = (env.get(name) or "").strip()
        if v:
            return v, ("demo" if v == "DEMO_KEY" else "real")
    return "DEMO_KEY", "demo"


# ---- page text -----------------------------------------------------------------------------------------------------

def pdf_pages(raw):
    """Page texts. pdftotext (poppler) when installed (about ten times faster on 400-page issues), else pypdf."""
    exe = shutil.which("pdftotext")
    if exe:
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "in.pdf"
            src.write_bytes(raw)
            r = subprocess.run([exe, "-enc", "UTF-8", str(src), "-"], capture_output=True, timeout=600)
            if r.returncode == 0:
                pages = r.stdout.decode("utf-8", "replace").replace("\r\n", "\n").split("\f")
                if pages and not pages[-1].strip():
                    pages = pages[:-1]
                return pages, "pdftotext"
    import frpages
    return [p.replace("\r\n", "\n") for p in frpages.pdf_pages(raw)], "pypdf"


def extract_pages(raw, first, last):
    import frpages
    return frpages.extract_pdf(raw, first, last)


# ---- location ------------------------------------------------------------------------------------------------------

def _iso(y, m, d):
    try:
        return dt.date(int(y), MON[m[:3].lower()], int(d)).isoformat()
    except (KeyError, ValueError):
        return None


ATTACHED = re.compile(r"\s*,?\s*(?:(?:of|dated|approved|signed|issued|promulgated)\s+(?:on\s+)?)?")


def dates_after(text, end):
    """Dates attached to a citation: 'of October 30, 1929', 'dated ...', 'approved March 9, 1951', 'of 5 January
    1914', or the contents form ', Oct. 30, 1929'. A date further on ('effective March 9, 1951', '(8 F.R. 5516,
    April 27, 1943)', 'as modified by the act of March 9, 1951') is not the order's date and is not read (review N2)."""
    m = ATTACHED.match(text, end)
    pos = m.end() if m else end
    out = []
    d1 = DATE_RE.match(text, pos)
    if d1:
        out.append(_iso(d1.group(3), d1.group(1), d1.group(2)))
    d2 = DATE_DMY.match(text, pos)
    if d2:
        out.append(_iso(d2.group(3), d2.group(2), d2.group(1)))
    return [d for d in out if d]


SPLIT_MONTH = re.compile(r"\s*,?\s*(?:of|dated)\s+(" + MONTHS + r")(?:\s+(\d{1,2})\s*,?)?\s*(?=\S)")


def split_date_confirms(text, end, target_date):
    """True when an attached date that the scan's column interleave split ('of February [other column] 24, 1913';
    'of June 8, [other column] 1936') reassembles into exactly the target's date. Confirm only: a reassembled date
    that differs proves nothing and never refuses (review 3: dates split across Federal Register columns)."""
    if not target_date:
        return False
    m = SPLIT_MONTH.match(text, end)
    if not m:
        return False
    rest = text[m.end():m.end() + 160]
    if m.group(2):
        y = re.search(r"(?<!\d)(1[6-9]\d\d|20\d\d)(?!\d)", rest)
        cand = _iso(y.group(1), m.group(1), m.group(2)) if y else None
    else:
        dy = re.search(r"(?<![\d,])(\d{1,2}),\s?(1[6-9]\d\d|20\d\d)(?!\d)", rest)
        cand = _iso(dy.group(2), m.group(1), dy.group(1)) if dy else None
    return cand == target_date


def boundary_problem(text, s, e, num, suf):
    """(refusal, pointer) when the printed number may not be exactly the target's. Refused: it runs on into digits
    ('1085 6', '1,885' read as 1) or sits inside a longer number ('10,885' read as 885), or carries an attached letter
    or fraction the target lacks ('2656A', '2656-A', '2656-a', '2656½'). Pointer only: a single capital letter after a
    space ('2656 A' or '1885 A further withdrawal' cannot be told apart). A list member ('Nos. 1884, 1885 and 1886')
    is neither (review N1)."""
    m = None
    for m in re.finditer(r"(?<!\d)" + re.escape(num) + r"(?!\d)", text[s:e]):
        pass
    if m is None:
        return None, None
    a, b = s + m.start(), s + m.end()
    after, before = text[b:b + 4], text[max(0, a - 4):a]
    if re.match(r" \d(?!\d{3})|,\d{3}(?!\d)", after):
        return "number_runs_on", None
    if re.search(r"(?<![\d,])\d{1,3},$|(?<![\d,])\d{1,2} $", before):
        return "number_inside_longer_number", None
    if not suf:
        if re.match(r"-?[A-Za-z](?![A-Za-z])|-?½|-?1/2", after):
            return "number_carries_suffix_target_lacks", None
        if re.match(r" [A-Z](?![A-Za-z])", after):
            return None, "possible_letter_suffix"
    return None, None


def own_printing(text, cite_start, num, target_date, issue_date, acting):
    """The citation lies in the order's own printing: under its own heading line (the whole line: '[No. N]',
    'EXECUTIVE ORDER N', '[Executive Order N]') with no filing line between, or, in an issue within 45 days of the order
    and with no relation word governing the citation, on a line that starts with the order's number (review N3)."""
    pat = re.compile(r"(?m)^[ \t]*(?:\[\s*N\s?[Oo]\.?\s*" + num + r"\s*[\]1lI|]|" + _spaced(["EXECUTIVE", "ORDER"])
                     + r"\s*(?:N\s?[Oo]\.?\s*)?" + num + r"|\[\s*(?i:executive\s+order)\s*(?:no\.?\s*)?" + num
                     + r"\s*\])[ \t]*$")
    for m in pat.finditer(text):
        if m.start() > cite_start:
            break
        if m.end() >= cite_start or not (S.FILING.search(text, m.end(), cite_start)
                                         or LOOSE_FILING.search(text, m.end(), cite_start)):
            return True
    if acting:
        return False
    try:
        near = 0 <= (dt.date.fromisoformat(issue_date) - dt.date.fromisoformat(target_date)).days <= 45
    except (TypeError, ValueError):
        near = False
    if near:
        line_start = text.rfind("\n", 0, cite_start) + 1
        if re.match(r"\s*(?:Executive\s+Order|E\.\s?O\.)\s*(?:No\.?\s*)?" + num + r"\b", text[line_start:cite_start + 40],
                    re.I):
            return True
    return False


def locate(text, target, target_date, issue_date=None):
    """[(hit, refusal_or_None, pointer_reasons)] for every sentence of `text` citing the target by number.

    A refusal means the sentence does not name the target (kept in LOCATED.csv only). Pointer reasons mean it may name
    the target but must not be read as acting on it (published as cross_reference)."""
    out = []
    num, suf = (S.parse_eo(target) or ("", "", ""))[:2]
    for h in S.find_citations(text, target, target_date):
        if h["form"] != "number":
            continue  # Selden's fallbacks read lists and split OCR; Cruden keeps only 'Executive Order (No.) N'
        seg_lo, seg_hi = h["start"], h["end"]
        cites = []
        for (s, e, n, sx, d) in S.cites.eo_number_mentions(text[seg_lo:seg_hi]):
            if n == num and (sx or "") == suf:
                cites.append((seg_lo + s, seg_lo + e, d.isoformat() if hasattr(d, "isoformat") else d))
        if not cites:
            cites = [(h["cite_start"], h["cite_end"], h["date_stated"])]
        dates = []
        for s, e, d in cites:
            if d:
                dates.append(d)
            dates += dates_after(text, e)
        confirmed = bool(target_date) and target_date in dates
        split_confirmed = False
        if not confirmed and target_date and not dates:
            split_confirmed = any(split_date_confirms(text, e, target_date) for _, e, _ in cites)
            confirmed = split_confirmed
        why, pointer = None, []
        for s, e, _ in cites:
            r, p = boundary_problem(text, s, e, num, suf)
            why = why or r
            if p and p not in pointer:
                pointer.append(p)
        if not target_date and not why:
            pointer.append("target_date_unknown")  # nothing to confirm or disagree with
        elif not why and dates and not confirmed:
            why = "printed_date_disagrees_with_target"
        if not why and not confirmed:
            for s, e, _ in cites:
                before = re.sub(r"(?i)\s*(?:the\s+)?$", "", text[max(0, s - 60):s])
                if ISSUER_AFTER.search(text[e:e + 90]) or ISSUER_BEFORE.search(before):
                    why = "another_issuer_printed_with_the_number"
                    break
                if POSSESSIVE_BEFORE.search(before):
                    # 'The Governor-General ..., by his Executive Order No. N': the issuer named earlier in the
                    # sentence decides; otherwise the possessive is unclear and the sentence is a pointer only
                    if re.search(ISSUER_WORDS, text[max(seg_lo, s - 150):s], re.I):
                        why = "another_issuer_printed_with_the_number"
                        break
                    if "possessive_issuer_unclear" not in pointer:
                        pointer.append("possessive_issuer_unclear")
        if not why and own_printing(text, h["cite_start"], num, target_date, issue_date, S.acting_on_target(h)):
            why = "inside_the_orders_own_printing"
        if not why:
            if not confirmed:
                pointer.append("identity_unconfirmed_no_matching_printed_date")
            line = text[text.rfind("\n", 0, h["cite_start"]) + 1:text.find("\n", h["cite_end"]) % (len(text) + 1)]
            if (LEADER.search(line) or LEADER.search(text[h["cite_end"]:h["cite_end"] + 120].split("\n")[0])
                    or LEADER.search(text[seg_lo:seg_hi])):
                pointer.append("contents_or_index_entry")
            if EXCEPTION.search(text[seg_lo:seg_hi]):
                pointer.append("exception_or_saving_wording_in_sentence")
            for m in REG_SUBJECT.finditer(text, seg_lo, seg_hi):
                # 'Section 2 of Executive Order No. N is amended' amends the order: the target sits inside the subject
                if not any(m.start() <= s < m.end() for s, _, _ in cites):
                    pointer.append("relation_governs_a_regulation_not_the_order")
                    break
            if any(AUTHORITY_BEFORE.search(text[max(seg_lo, s - 70):s]) for s, _, _ in cites):
                pointer.append("order_cited_as_authority_or_description")
            if all(BY_BEFORE.search(text[max(seg_lo, s - 140):s]) for s, _, _ in cites):
                pointer.append("order_printed_as_actor")
            if all(PAREN_BEFORE.search(text[max(seg_lo, s - 30):s]) for s, _, _ in cites):
                pointer.append("order_cited_in_parenthesis")
        if split_confirmed and not why:
            pointer = [p for p in pointer if p != "identity_unconfirmed_no_matching_printed_date"]
        h = dict(h, date_stated=(target_date if confirmed else (dates[0] if dates else None)),
                 date_match=True if confirmed else (False if dates else None),
                 date_reassembled_from_split_columns=split_confirmed)
        out.append((h, why, pointer))
    return out


def acting_instrument(text, cite_start, target=None, allow_tag=True):
    """(acting_id, label) only when the citation lies in that instrument's own printed span: the nearest standalone
    heading line before it, at most SPAN_CAP characters away, with no filing line (strict or damaged) and no new
    document's agency header between, whose previous line does not run on into it ('... AND', 'Prior orders:'). A
    heading that prints the target's own number is skipped. Else (None, None): the caller names the page."""
    tnum = (S.parse_eo(target) or ("",))[0] if target else ""
    best = None
    for kind, rx in HEADINGS:
        for m in rx.finditer(text, max(0, cite_start - SPAN_CAP), cite_start):
            n = next(g for g in m.groups() if g)
            if kind == "TAG":
                # a Statutes at Large margin tag may belong to the neighbouring proclamation: never an actor there
                kind = tag_kind(text, m.start(), m.end()) if allow_tag else None
                if kind is None:
                    continue  # a bare '[No. N]' whose series the title block does not name
            if kind == "EO" and n == tnum:
                continue
            prev = text[:m.start()].rstrip().rsplit("\n", 1)[-1]
            if CONTINUES.search(prev):
                continue
            if best is None or m.start() > best[1]:
                best = (kind, m.start(), m.end(), n)
    if not best:
        return None, None
    kind, start, end, n = best
    between = text[end:cite_start]
    if S.FILING.search(between) or LOOSE_FILING.search(between) or AGENCY_HEADER.search(between):
        return None, None
    return f"{kind}:{n}", {"PLO": "Public Land Order", "PROC": "Proclamation", "EO": "Executive Order"}[kind] + f" {n}"


# ---- the run -------------------------------------------------------------------------------------------------------

class Run:
    def __init__(self, repo, out, cache, env, transport=None, opener=None, premis=None):
        self.repo, self.out, self.env = Path(repo), Path(out), env
        g = lambda k, d: type(d)(env.get(k) or d)  # noqa: E731
        self.max_packages = g("JOB_MAX_PACKAGES", 1500)
        self.max_download = int(g("JOB_MAX_DOWNLOAD_GB", 25.0) * 1e9)
        self.deadline = time.monotonic() + g("JOB_TIME_BUDGET_MIN", 280.0) * 60
        self.per_target_cap = {"FR": g("CRUDEN_FR_HITS_PER_TARGET", 40), "STATUTE": g("CRUDEN_STAT_HITS_PER_TARGET", 20)}
        self.commit_bytes, self.committed = g("CRUDEN_COMMIT_MB", 80) * 1_000_000, 0
        key, self.key_kind = api_key(env)
        self.searcher = Searcher(key, opener=opener, min_interval=g("CRUDEN_SEARCH_INTERVAL", 0.25),
                                 max_searches=g("JOB_MAX_SEARCHES", 6000 if self.key_kind == "real" else 25))
        self.pool = FetchPool(Path(cache) / "govinfo", workers=g("JOB_WORKERS", 6), per_host=6, transport=transport,
                              max_bytes=450_000_000, timeout=240, user_agent=UA, min_interval=0.1,
                              max_cache_bytes=3 * 1024 ** 3)
        self.premis = premis
        self.tools = tool_versions()
        self.lock = threading.Lock()
        self.searches, self.sources, self.fragments, self.located, self.failures = [], [], [], [], []
        (self.out / "texts").mkdir(parents=True, exist_ok=True)
        (self.out / "captures").mkdir(parents=True, exist_ok=True)

    def budget(self):
        return self.pool.bytes_downloaded < self.max_download and time.monotonic() < self.deadline

    def fixity(self, pkg):
        if self.premis:
            return self.premis(pkg)
        import fixity
        return fixity.check_one({"package": pkg, "filename": pkg + ".pdf", "url": FR_PDF.format(pkg=pkg),
                                 "shas": set(), "ids": set(), "found_in": set()})

    def reserve(self, n):
        with self.lock:
            if self.committed + n <= self.commit_bytes and n <= 1_500_000:
                self.committed += n
                return True
            return False

    def one(self, unit):
        """One FR issue or Statutes page, all its targets. Everything is built locally and published at the end, so a
        failure part way leaves no orphan record."""
        coll, pkg, gran = unit["collection"], unit["package"], unit.get("granule") or ""
        idate = unit.get("date") or ""
        url = FR_PDF.format(pkg=pkg) if coll == "FR" else GRANULE_PDF.format(pkg=pkg, gran=gran)
        got = self.pool.fetch(url)
        raw = got["body"]
        if not raw.startswith(b"%PDF"):
            raise FetchError("not a PDF")
        pages, tool = pdf_pages(raw)
        tool_v = f"{tool} {self.tools.get(tool) or ''}".strip()
        per_page = defaultdict(list)
        located, sources, fragments = [], [], []
        for t, tdate in sorted(unit["targets"].items()):
            num = S.parse_eo(t)[0]
            found = False
            for i, ptxt in enumerate(pages):
                if not ptxt or not S.printed_anywhere(ptxt, num):
                    continue
                for h, why, pointer in locate(ptxt, t, tdate, idate):
                    found = True
                    per_page[i].append((t, h, why, pointer))
            if not found:
                located.append({"target_id": t, "collection": coll, "package": pkg, "granule": gran, "pdf_page": "",
                                "located": False, "refused": "", "acting_id": "", "mechanism_printed": "",
                                "published_mechanism": "", "date_stated": "", "date_match": "", "quote": "",
                                "note": "search hit, but no sentence prints 'Executive Order (No.) N' in the OCR"})
        gpo, match, presult = "", False, "not_applicable"
        if coll == "FR" and per_page:
            pr = self.fixity(pkg)
            gpo = pr.get("gpo_sha256") or ""
            match = bool(gpo) and gpo == got["sha256"]
            # check_one compares against hashes it was given (none here); report our own comparison instead.
            presult = "match" if match else ("mismatch" if gpo else (pr.get("result") or "unchecked"))
        whole_committed = None
        if coll == "STATUTE" and per_page and self.reserve(len(raw)):
            whole_committed = f"captures/{got['sha256']}.pdf"
        for i in sorted(per_page):
            first, last = max(0, i - 1), min(len(pages) - 1, i + 1)
            parts, off = [], None
            header = (f"Cruden page text. {coll} {gran or pkg}, PDF pages {first + 1}-{last + 1} of {len(pages)}; "
                      f"source {url} sha256 {got['sha256']}; text by {tool_v}.\n")
            pos = len(header)
            for j in range(first, last + 1):
                mark = f"\n=== PDF page {j + 1} of {len(pages)} ===\n"
                if j == i:
                    off = pos + len(mark)
                parts.append(mark + pages[j])
                pos += len(mark) + len(pages[j])
            full = header + "".join(parts)
            tsha = S.sha256(full.encode("utf-8"))
            stem = f"{gran or pkg}_p{i + 1}_{tsha[:12]}"
            tpath = f"texts/{stem}.txt"
            targets = sorted({x[0] for x in per_page[i]})
            common = {"collection": coll, "package": pkg, "granule": gran, "issue_date": idate,
                      "pdf_pages": [first + 1, last + 1], "cited_pdf_page": i + 1, "page_count": len(pages),
                      "text_tool": tool_v, "text_sha256": tsha, "locator": LOCATOR}
            whole = S.source_record(
                f"cruden:{coll.lower()}:{gran or pkg}:p{i + 1}:{tsha[:12]}", "NOTICE:" + (gran or pkg), targets,
                url + f"#page={i + 1}", got["sha256"], got["bytes"], "govinfo_search_then_content_pdf",
                f"{gran or pkg}.pdf PDF page {i + 1} of {len(pages)} (text of pages {first + 1}-{last + 1})", tpath,
                GRADE_FR if coll == "FR" else GRADE_STAT,
                "Whole PDF hashed; the cited page's OCR text is kept (text_sha256). For a Federal Register issue GPO "
                "publishes the issue's SHA-256 in its PREMIS record; gpo_premis_match says whether these bytes are "
                "GPO's.", cache_path=whole_committed,
                extra=dict(common, gpo_premis_sha256=gpo, gpo_premis_match=match, gpo_premis_result=presult))
            cite = whole
            if not whole_committed:
                ext, etool = extract_pages(raw, i, i)
                if self.reserve(len(ext)):
                    esha = S.sha256(ext)
                    cite = S.source_record(
                        f"cruden-extract:{esha[:16]}:{tsha[:8]}", "NOTICE:" + (gran or pkg), targets,
                        url + f"#page={i + 1}", esha, len(ext), "govinfo_content_pdf_page_extract",
                        whole["page_or_item"] + " (committed extract of the cited page)", tpath, whole["grade"],
                        f"PDF page {i + 1} extracted with {etool} from the PDF whose sha256 is source_sha256 (GPO "
                        f"PREMIS match: {match}); re-download it to re-derive.", cache_path=f"captures/{esha}.pdf",
                        extra=dict(common, source_sha256=got["sha256"], gpo_premis_match=match, extract_tool=etool,
                                   extract_bytes=ext))
            verifiable = bool(cite.get("cache_path")) or match
            sources.append((whole, cite, full, raw if whole_committed else None))
            for t, h, why, pointer in per_page[i]:
                h = dict(h, start=h["start"] + off, end=h["end"] + off, cite_start=h["cite_start"] + off,
                         cite_end=h["cite_end"] + off)
                actor, label = acting_instrument(full, h["cite_start"], t, allow_tag=(coll == "FR"))
                if actor is None or actor == t:
                    actor = "NOTICE:" + (gran if gran else f"{pkg}/p{i + 1}")
                    label = f"document printed on PDF page {i + 1} of {gran or pkg} (instrument not identified by machine)"
                if not verifiable and not why:
                    why = "bytes_not_verifiable"  # neither committed nor a GPO PREMIS match: never published
                reasons = list(pointer)
                if reasons:
                    h = dict(h, mechanism_class="mention")
                published = "" if why else (h["mechanism"] if S.acting_on_target(h) else "cross_reference")
                located.append({"target_id": t, "collection": coll, "package": pkg, "granule": gran, "pdf_page": i + 1,
                                "located": True, "refused": why or "", "acting_id": actor,
                                "mechanism_printed": h["mechanism"], "published_mechanism": published,
                                "date_stated": h["date_stated"] or "",
                                "date_match": "" if h["date_match"] is None else h["date_match"],
                                "quote": S.cites.squeeze(h["quote"])[:300], "note": "|".join(reasons)})
                if why:
                    continue  # names something else: kept in LOCATED.csv, never published as a lead
                flags = ["publication_date_not_instrument_date"] + reasons
                if h.get("date_reassembled_from_split_columns"):
                    flags.append("date_reassembled_from_split_columns")
                if actor.startswith("NOTICE:"):
                    flags.append("acting_instrument_not_identified")
                fragments.append(S.fragment(
                    t, actor, label, h, cite, PRODUCER, idate,
                    "publication date of the issue or volume printing the sentence (not the instrument's signing or "
                    "effective date)", "cruden_fr_number_search" if coll == "FR" else "cruden_statute_number_search",
                    flags=flags, extra={"collection": coll, "package": pkg, "granule": gran, "pdf_page": i + 1,
                                        "source_sha256": got["sha256"], "gpo_premis_match": match,
                                        "text_sha256": tsha, "locator": LOCATOR}))
        with self.lock:  # publish the unit at once
            for whole, cite, full, rawbytes in sources:
                (self.out / whole["text_path"]).write_text(full, encoding="utf-8", newline="")
                if rawbytes is not None:
                    (self.out / whole["cache_path"]).write_bytes(rawbytes)
                if cite is not whole:
                    (self.out / cite["cache_path"]).write_bytes(cite.pop("extract_bytes"))
                self.sources.append(whole)
                if cite is not whole:
                    self.sources.append(cite)
            self.located.extend(located)
            self.fragments.extend(fragments)
        return {"bytes": got["bytes"], "pages": len(pages)}


def target_dates(repo):
    """Signing dates: domesday-register and the OFR catalog (Selden's order_dates), then, for numbered orders they
    lack, the Lord 1944 WPA list's year and month-day when the list has exactly one entry for the number."""
    dates = S.order_dates(repo)
    wpa = defaultdict(set)
    for r in read_csv(Path(repo) / "jobs/x1-class-engine/data/WPA_NUMBERED_ENTRIES.csv"):
        m = re.match(r"([A-Za-z]{3,5})\.?\s+(\d{1,2})", r.get("month_day") or "")
        if m and (r.get("year") or "").isdigit():
            d = _iso(r["year"], m.group(1), m.group(2))
            if d:
                wpa[r["id"]].add(d)
    for iid, ds in wpa.items():
        if iid not in dates and len(ds) == 1:
            dates[iid] = next(iter(ds))
    return dates


def load_targets(repo, env):
    p = Path(env.get("CRUDEN_TARGETS") or (Path(repo) / "jobs/linnaeus-types/output/CRUDEN_TARGETS.csv"))
    return [r["instrument_id"] for r in read_csv(p)]


def control_targets(repo, exclude, n=30, seed=1737):
    """Planted positives: BLM's PLO table names a pre-1937 order by number with an ending word, in a PLO printed in
    the Federal Register by 1993 (independent of the page OCR Cruden reads). The concordance must locate a sentence
    citing the order, with its date, in some Federal Register issue."""
    import random
    rows = []
    for r in read_csv(Path(repo) / "jobs/shepard-citations/output/PLO_TABLE.csv"):
        try:
            vol = int(r.get("fr_volume") or 0)
        except ValueError:
            continue
        if not (1 <= vol <= 58):
            continue
        for ref in (r.get("eo_refs") or "").split("|"):
            m = re.match(r"(EO:\d+)(?:@[\d-]+)?=(\w+)", ref)
            if m and S.mech_class(m.group(2)) == "ending" and m.group(1) not in exclude:
                eo = S.parse_eo(m.group(1))
                if eo and 1000 <= int(eo[0]) < 7532:
                    rows.append((m.group(1), r["plo_id"]))
    rows = sorted(set(rows))
    rng = random.Random(seed)
    rng.shuffle(rows)
    seen, out = set(), []
    for t, plo in rows:
        if t not in seen:
            seen.add(t)
            out.append((t, plo))
        if len(out) >= n:
            break
    return out


# Fixed identity negatives, run every run: each must be refused or published only as a pointer.
IDENTITY_NEGATIVES = [
    ("EO:885", "1908-06-12", "under Executive Order No. 885 of the Governor General of the Philippine Islands, issued "
                             "at Manila, October 12, 1935, the allotment is hereby revoked."),
    ("EO:1885", "1913-11-01", "The Governor's Executive Order No. 1885 is hereby revoked."),
    ("EO:1885", "1913-11-01", "Canal Zone Executive Order No. 1885 is hereby revoked."),
    ("EO:1885", "1913-11-01", "Executive Order No. 1885 of the State of California is hereby revoked."),
    ("EO:1085", "1909-06-01", "Executive Order No. 1085 6 of May 1, 1950, is hereby revoked."),
    ("EO:885", "1908-06-12", "Executive Order No. 10,885 is hereby revoked."),
    ("EO:2656", "1917-07-01", "Executive Order No. 2656 A of July 1, 1917, is hereby revoked."),
    ("EO:3000", "1918-11-11", "Executive Order No. 3000 of May 5, 1931, is hereby revoked."),
    ("EO:1885", "1913-11-01", "Executive Order No. 1885, approved March 9, 1951, is hereby revoked."),
    ("EO:1885", "1913-11-01", "All prior withdrawals are hereby revoked except Executive Order No. 1885 of November 1, "
                              "1913."),
    ("EO:1885", "1913-11-01", "Executive Order No. 1885 is hereby revoked."),
    ("EO:8200", "1939-07-29", "EXECUTIVE ORDER 8200\nPARTIAL REVOCATION OF EXECUTIVE ORDER NO. 5886\nBy virtue of the "
                              "authority vested in me, Executive Order No. 5886 is hereby revoked in part."),
]


def identity_negatives():
    bad = []
    for t, d, txt in IDENTITY_NEGATIVES:
        for h, why, pointer in locate(txt, t, d, "1939-08-01" if t == "EO:8200" else "1960-01-01"):
            if not why and not pointer and S.acting_on_target(h):
                bad.append({"target": t, "text": txt[:120]})
    return {"identity_negatives": len(IDENTITY_NEGATIVES), "identity_negatives_published_as_acting": len(bad),
            "identity_failures": bad}


def prior_valid(prior):
    try:
        s = json.loads((prior / "SUMMARY.json").read_text(encoding="utf-8"))
        c = json.loads((prior / "CONTROLS.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False, "no prior summary or controls"
    if s.get("locator") != LOCATOR:
        return False, f"prior locator {s.get('locator')!r} is not {LOCATOR}"
    if not c.get("passed"):
        return False, "prior controls did not pass"
    return True, ""


def main(repo: Path, out: Path, cache: Path, env=os.environ, transport=None, opener=None, premis=None):
    repo, out = Path(repo), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    started = now_utc()
    targets = load_targets(repo, env)
    dates = target_dates(repo)
    limit = int(env.get("JOB_LIMIT") or 0)
    collections_ = [c for c in (env.get("CRUDEN_COLLECTIONS") or "FR,STATUTE").split(",") if c]
    run = Run(repo, out, cache, env, transport=transport, opener=opener, premis=premis)
    controls = control_targets(repo, set(targets), n=int(env.get("CRUDEN_CONTROLS") or 30))
    control_ids = {t for t, _ in controls}

    # carry forward: searches whose query is unchanged always; read pages, fragments and sources only when the prior
    # run used this locator and its controls passed (otherwise every hit is read again)
    prior = Path(env.get("JOB_PRIOR_OUTPUT_DIR") or (HERE / "output"))
    prior_searches = {}
    for r in S.read_jsonl(prior / "SEARCHES.jsonl"):
        if r.get("status") == "searched" and r.get("query") == query(r["target_id"], r["collection"],
                                                                     dates.get(r["target_id"])):
            if (r.get("count") or 0) > 100 and "response_sha256_desc" not in r:
                continue  # chosen before the latest-half fix (review N7): ask again
            prior_searches[(r["target_id"], r["collection"])] = r
    ok, why_not = prior_valid(prior)
    carried, done_pairs = (carry_forward(prior, out, run, control_ids) if ok else (0, set()))

    order = [t for t, _ in controls] + targets
    if limit:
        order = order[:limit + len(controls)]
    for coll in collections_:  # every target in the Federal Register first, then the Statutes at Large
        for t in order:
            key = (t, coll)
            if key in prior_searches:
                run.searches.append(dict(prior_searches[key], carried_forward=True))
                continue
            rec = {"target_id": t, "collection": coll, "control": t in control_ids,
                   "target_date": dates.get(t, ""), "query": query(t, coll, dates.get(t)), "searched_utc": now_utc()}
            if not run.budget():
                rec.update(status="not_searched_budget")
                run.searches.append(rec)
                continue
            try:
                res = run.searcher.search(rec["query"])
                hits, count = res["hits"], res["count"]
                if count is not None and count > len(hits):
                    late = run.searcher.search(rec["query"], order="DESC")
                    seen = {(h["package"], h["granule"]) for h in hits}
                    # DESC arrives newest first: reverse it so the list stays in date order and the tail is the
                    # newest (review N7)
                    hits = hits + [h for h in reversed(late["hits"]) if (h["package"], h["granule"]) not in seen]
                    rec["response_sha256_desc"] = late["sha256"]
                cap = run.per_target_cap[coll]
                if len(hits) > cap:  # earliest and latest halves: revocations sit late, first mentions early
                    hits = hits[:cap // 2] + hits[-(cap - cap // 2):]
                rec.update(status="searched", count=count, hits=hits, response_sha256=res["sha256"],
                           complete=count is not None and count <= len(hits))
            except (FetchError, ValueError, OSError) as e:
                rec.update(status="not_searched_error", error=str(e)[:200])
            run.searches.append(rec)
    units = {}
    for rec in run.searches:
        if rec.get("status") != "searched":
            continue
        for h in rec.get("hits") or []:
            if not h.get("package"):
                continue
            gran = h.get("granule") if rec["collection"] == "STATUTE" else ""
            if rec["collection"] == "STATUTE" and not gran:
                continue
            if (rec["target_id"], h["package"], gran or "") in done_pairs:
                continue
            k = (rec["collection"], h["package"], gran or "")
            u = units.setdefault(k, {"collection": k[0], "package": k[1], "granule": k[2], "date": h.get("date"),
                                     "targets": {}})
            u["targets"][rec["target_id"]] = rec.get("target_date") or None
    todo = sorted(units.values(), key=lambda u: (not (set(u["targets"]) & control_ids), -len(u["targets"]),
                                                  u["date"] or "", u["package"], u["granule"]))
    todo = todo[:run.max_packages]

    def safe(u):
        if not run.budget():
            return u, "budget"
        try:
            run.one(u)
            return u, None
        except Exception as e:  # one bad PDF must not stop the run
            return u, f"{type(e).__name__}: {e}"[:300]
    n = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=int(env.get("JOB_WORKERS") or 6)) as ex:
        for u, err in ex.map(safe, todo):
            n += 1
            if err:
                run.failures.append({"collection": u["collection"], "package": u["package"], "granule": u["granule"],
                                     "targets": sorted(u["targets"]), "error": err})
            if n % 50 == 0:
                print(f"cruden: {n}/{len(todo)} units, {run.pool.bytes_downloaded / 1e9:.2f} GB, "
                      f"{len(run.fragments)} fragments", flush=True)
    ctl = measure_controls(run, controls)
    ctl["carry_forward"] = "used" if ok else f"not used: {why_not}"
    if not ctl["passed"]:
        # every fragment of this run is a pointer; the next run carries none of them and reads every hit again
        for f in run.fragments:
            for row in f["data"]:
                row["mechanism"] = "cross_reference"
                row["flags"] = sorted(set(row["flags"]) | {"controls_failed_this_run"})
    fr_out = [f for f in run.fragments if f["instrument_id"] not in control_ids]
    write(out, run, fr_out, ctl, targets, control_ids, started, carried, n, len(todo))
    return json.loads((out / "SUMMARY.json").read_text(encoding="utf-8"))


def carry_forward(prior, out, run, control_ids):
    """Earlier sources, fragments and located rows, each re-verified: a text whose sha256 differs from its record's
    text_sha256, or a committed PDF whose bytes differ from its sha256, is dropped with everything that cites it, and
    its (target, package) pairs are read again. Control targets are never carried: their units are read every run."""
    if not prior.is_dir() or prior.resolve() == out.resolve():
        return 0, set()
    keep = {}
    for r in S.read_jsonl(prior / "SOURCES.jsonl"):
        tp = prior / (r.get("text_path") or "-")
        if not tp.is_file() or S.sha256(tp.read_bytes()) != r.get("text_sha256"):
            continue
        cp = r.get("cache_path")
        if cp:
            src = prior / cp
            if not src.is_file() or S.sha256(src.read_bytes()) != r["sha256"]:
                continue
        if set(r.get("instrument_ids") or []) & control_ids:
            continue
        keep[r["source_id"]] = r
    n, cited = 0, set()
    for f in S.read_jsonl(prior / "FRAGMENTS.jsonl"):
        rows = f.get("data") or []
        if f.get("instrument_id") in control_ids or not all(x.get("source_id") in keep for x in rows):
            continue
        run.fragments.append(f)
        cited |= {x["source_id"] for x in rows}
        n += 1
    for sid, r in keep.items():
        (out / r["text_path"]).write_bytes((prior / r["text_path"]).read_bytes())
        if r.get("cache_path"):
            (out / r["cache_path"]).write_bytes((prior / r["cache_path"]).read_bytes())
            run.committed += r["bytes"]
        run.sources.append(r)
    # A (target, package) pair is done only if every page it was located on survived verification (review N6);
    # otherwise the whole unit is read again for that target and its rows are rebuilt (duplicates are removed on
    # write).
    good_pages = {(r.get("package"), r.get("granule") or "", str(r.get("cited_pdf_page"))) for r in keep.values()}
    rows, bad = [], set()
    for r in read_csv(prior / "LOCATED.csv"):
        if r["target_id"] in control_ids:
            continue
        pair = (r["target_id"], r["package"], r.get("granule") or "")
        if r.get("located") == "True" and (r["package"], r.get("granule") or "", str(r.get("pdf_page"))) not in good_pages:
            bad.add(pair)
            continue
        rows.append((pair, r))
    pairs = set()
    for pair, r in rows:
        if pair in bad:
            continue
        run.located.append(r)
        pairs.add(pair)
    run.fragments = [f for f in run.fragments
                     if (f["instrument_id"], f["data"][0].get("package"), f["data"][0].get("granule") or "") not in bad]
    return len(run.fragments), pairs


def measure_controls(run, controls):
    loc = defaultdict(list)
    for r in run.located:
        loc[r["target_id"]].append(r)
    found, misses = 0, []
    for t, plo in controls:
        rows = [r for r in loc.get(t, []) if str(r.get("located")) == "True" and not r.get("refused")
                and str(r.get("date_match")) == "True"]
        if rows:
            found += 1
        else:
            s = [x for x in run.searches if x["target_id"] == t and x["collection"] == "FR"]
            misses.append({"target": t, "plo": plo, "search_status": s[0].get("status") if s else "none",
                           "hits": s[0].get("count") if s else None})
    texts, pos = {}, []
    for f in run.fragments:
        row = f["data"][0]
        tp = run.out / (row.get("text_path") or "-")
        if f["instrument_id"] in {t for t, _ in controls} and tp.is_file():
            texts[row["text_path"]] = tp.read_text(encoding="utf-8")
            pos.append((f["instrument_id"], row["acting_id"], "ending", row["text_path"]))
    neg = S.run_controls(pos, texts, seed=1737) if pos else {"negatives": 0, "false_locations": 0, "false_hits": []}
    searched = sum(1 for t, _ in controls if any(x["target_id"] == t and x.get("status") == "searched"
                                                  for x in run.searches))
    recall = round(found / searched, 4) if searched else None
    # What would have been published for the planted positives (review N5): a dated sentence demoted to a pointer
    # by over-broad wording rules counts as a miss here.
    published = sum(1 for t, _ in controls if any(
        str(r.get("located")) == "True" and not r.get("refused")
        and r.get("published_mechanism") not in ("", "cross_reference") for r in loc.get(t, [])))
    pub_recall = round(published / searched, 4) if searched else None
    idn = identity_negatives()
    return {"planted_positives": len(controls), "positives_searched": searched, "positives_located_with_date": found,
            "recall": recall, "min_recall": MIN_RECALL, "positives_published_acting": published,
            "published_recall": pub_recall, "min_published_recall": MIN_PUBLISHED_RECALL, "misses": misses[:40],
            "near_miss_negatives": neg.get("negatives", 0), "false_locations": neg.get("false_locations", 0),
            "false_hits": neg.get("false_hits", [])[:40], **idn,
            "passed": bool(searched) and recall is not None and recall >= MIN_RECALL
            and pub_recall >= MIN_PUBLISHED_RECALL
            and neg.get("false_locations", 0) == 0 and idn["identity_negatives_published_as_acting"] == 0}


def write(out, run, fr_out, ctl, targets, control_ids, started, carried, attempted, todo_n):
    seen, sources = set(), []
    for s in sorted(run.sources, key=lambda r: r["source_id"]):
        if s["source_id"] not in seen:
            seen.add(s["source_id"])
            sources.append(s)
    S.write_jsonl(out / "SOURCES.jsonl", sources)
    frs, fseen = [], set()
    for f in sorted(fr_out, key=lambda f: (f["instrument_id"], f["data"][0]["source_id"], f["data"][0]["quote_span"])):
        k = (f["instrument_id"], f["data"][0]["source_id"], f["data"][0]["quote_span"])
        if k not in fseen:
            fseen.add(k)
            frs.append(f)
    S.write_jsonl(out / "FRAGMENTS.jsonl", frs)
    S.write_jsonl(out / "SEARCHES.jsonl", sorted(run.searches, key=lambda r: (r["target_id"], r["collection"])))
    S.write_jsonl(out / "FAILURES.jsonl", run.failures)
    (out / "CONTROLS.json").write_text(json.dumps(ctl, indent=1) + "\n", encoding="utf-8")
    cols = ["target_id", "collection", "package", "granule", "pdf_page", "located", "refused", "acting_id",
            "mechanism_printed", "published_mechanism", "date_stated", "date_match", "quote", "note"]
    uniq = {}
    for r in run.located:  # a re-read pair can repeat a carried row
        uniq.setdefault(tuple(str(r.get(c, "")) for c in cols), r)
    with open(out / "LOCATED.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, cols, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(sorted(uniq.values(), key=lambda r: (r["target_id"], r["collection"], r["package"],
                                                         r.get("granule") or "", str(r.get("pdf_page")))))
    tset = set(targets)
    srch = [r for r in run.searches if r["target_id"] in tset]

    def acting(f):
        return f["data"][0]["mechanism"] != "cross_reference"
    by_coll = {}
    for coll in sorted({r["collection"] for r in srch}):
        rs = [r for r in srch if r["collection"] == coll]
        ok = [r for r in rs if r.get("status") == "searched"]
        by_coll[coll] = {
            "targets_queried": len(ok), "targets_not_queried": len(rs) - len(ok),
            "targets_with_search_hits": len({r["target_id"] for r in ok if r.get("count")}),
            "targets_with_located_citation": len({f["instrument_id"] for f in frs if f["data"][0].get("collection") == coll}),
            "targets_with_dated_acting_sentence": len({f["instrument_id"] for f in frs
                                                       if f["data"][0].get("collection") == coll and acting(f)}),
            "queries_truncated_at_cap": sum(1 for r in ok if r.get("complete") is False)}
    fam = {r["instrument_id"]: r["family"] for r in read_csv(run.repo / "jobs/linnaeus-types/output/CRUDEN_TARGETS.csv")}
    acting_all = {f["instrument_id"] for f in frs if acting(f)}
    cited_all = {f["instrument_id"] for f in frs}
    queried = {r["target_id"] for r in srch if r.get("status") == "searched"}
    by_family = defaultdict(Counter)
    for t in targets:
        f = fam.get(t, "")
        by_family[f]["targets"] += 1
        by_family[f]["queried"] += t in queried
        by_family[f]["located_citation"] += t in cited_all
        by_family[f]["dated_acting_sentence"] += t in acting_all
    refused = Counter(r["refused"] for r in run.located if r.get("refused"))
    pointers = Counter(x for r in run.located for x in (r.get("note") or "").split("|")
                       if r.get("located") == "True" and x and not r.get("refused"))
    summary = {
        "job": PRODUCER, "locator": LOCATOR, "generated_utc": now_utc(), "started_utc": started,
        "key_kind": run.key_kind, "tools": run.tools,
        "targets": len(targets), "control_targets": len(control_ids), "searches_made_this_run": run.searcher.n,
        "search_stopped": run.searcher.stopped, "search_rate_limit": run.searcher.rate_limit,
        "units_planned": todo_n, "units_attempted": attempted, "units_failed": len(run.failures),
        "bytes_downloaded": run.pool.bytes_downloaded, "fragments": len(frs), "fragments_carried_forward": carried,
        "by_collection": by_coll, "orders_with_located_citation": len(cited_all),
        "orders_with_dated_acting_sentence": len(acting_all), "citations_refused": dict(refused),
        "citations_published_as_pointer_only": dict(pointers),
        "by_family": {k: dict(v) for k, v in sorted(by_family.items())}, "committed_bytes": run.committed,
        "controls": {k: v for k, v in ctl.items() if k not in ("misses", "false_hits", "identity_failures")},
        "limits": ("Leads only. 'queried' means govinfo was asked, not that the order was covered: the index and the "
                   "OCR decide what is found, and an order with no hit or no located sentence is never evidence that "
                   "nothing acted on it. No status, census, codebook or count change. Certified: 0."),
    }
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("targets", "searches_made_this_run", "units_attempted", "fragments",
                                                "orders_with_dated_acting_sentence", "controls")}, indent=1), flush=True)
