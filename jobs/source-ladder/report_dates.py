"""Report-date lane (PANIZZI-2, 2026-10-20): find the RECORD of a report's transmittal, never assert the date.

Many order endings are written "N days after the report is submitted" (emergency boards, commissions,
task forces). To date such an ending a claim producer needs the transmittal record: the board or
commission report's own front matter, the Weekly Compilation of Presidential Documents, or the Public
Papers of the Presidents. This module holds the pure parts of that search (no network):

  * classify a queue request as a report-date request and build a SPEC (body name, order numbers and signing
    dates, a due date or window if the request gives one);
  * Presidential Emergency Boards: parse the National Mediation Board table and rank the boards that belong
    to an order (created within 3 days of the order, or the order falls inside the board's life);
  * 1993-2009: pick the Weekly Compilation issues around the date, read an issue's MODS list of documents,
    rank titles against the body name;
  * before 1993: a seekable file over HTTP Range requests so pypdf can read a few pages of a 0.7-1.0 GB
    Public Papers volume, and the running-head bisection that finds the pages for a date;
  * verbatim date lines from the front matter of a found record.

What it returns is custody: URLs, hashes, the page text and the verbatim lines that carry dates. The job
never writes a "report_date" field. Whether a dated line is the transmittal letter, the date a report was
received, or only a set of recommendations is a reviewer question per order. A found document is custody,
not authentication.
"""
from __future__ import annotations

import datetime as dt
import html as htmllib
import io
import re
import xml.etree.ElementTree as ET

NMB_PEB_URL = "https://nmb.gov/NMB_Application/index.php/peb/"
WCPD_FIRST = dt.date(1993, 1, 25)          # first Weekly Compilation issue on govinfo (Clinton)
WCPD_LAST = dt.date(2009, 1, 19)           # last Weekly Compilation issue (Bush); DCPD follows
MAX_WCPD_ISSUES = 20                       # one MODS file (~100 KB) per issue
PPP_BLOCK = 1 << 16                        # 64 KB per Range request
PPP_CASE_BYTES = 40_000_000                # per-case ceiling for Range reads
PPP_CASE_REQUESTS = 600

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
     "november", "december"], 1)}
MON_ABBR = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
            "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12}

ISO_RX = re.compile(r"\b(1[789]\d\d|20[0-2]\d)-(\d\d)-(\d\d)\b")
TEXT_DATE_RX = re.compile(
    r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|"
    r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s*(\d{1,2}),?\s*(1[789]\d\d|20[0-2]\d)\b", re.I)   # 'FEBRUARY 9, 1979' on title pages
NUM_DATE_RX = re.compile(r"\b(\d{1,2})/(\d{1,2})/(1[789]\d\d|20[0-2]\d)\b")

BODY_RX = re.compile(
    r"((?:(?:[A-Z][A-Za-z'’\-]*|advisory|of|and)\s+){0,7}?"
    r"(?:Commission|Committee|Board|Task\s+Force|Task\s+Group|Panel|Council|Group)"
    r"(?:\s+(?:on|for|of|to)\s+(?:the\s+)?[A-Z][A-Za-z'’\-]*"
    r"(?:(?:\s+(?:of|and|the|on|for))*\s+[A-Z][A-Za-z'’\-]*){0,8})?)")
GENERIC = {"the", "of", "and", "on", "for", "to", "a", "an", "in", "president", "presidents", "presidential",
           "national", "commission", "committee", "board", "task", "force", "group", "panel", "council",
           "report", "final", "special", "advisory", "united", "states", "american", "emergency",
           "executive", "order", "date", "submitted", "mediation", "company", "co", "corp", "inc", "railroad", "railway"}


def _date(y, m, d):
    try:
        return dt.date(int(y), int(m), int(d))
    except ValueError:
        return None


def parse_dates(text):
    """ISO dates written in text (ISO, 'July 15, 2022' or 'm/d/yyyy'), in order of appearance, deduplicated."""
    found = []
    for m in ISO_RX.finditer(text or ""):
        found.append((m.start(), _date(*m.groups())))
    for m in TEXT_DATE_RX.finditer(text or ""):
        mon = MONTHS.get(m.group(1).lower()) or MON_ABBR.get(m.group(1).lower().rstrip("."))
        found.append((m.start(), _date(m.group(3), mon, m.group(2)) if mon else None))
    for m in NUM_DATE_RX.finditer(text or ""):
        found.append((m.start(), _date(m.group(3), m.group(1), m.group(2))))
    out, seen = [], set()
    for _, d in sorted(found, key=lambda x: x[0]):
        if d and d not in seen:
            seen.add(d)
            out.append(d.isoformat())
    return out


def parse_mdy(text):
    m = NUM_DATE_RX.search(text or "")
    return _date(m.group(3), m.group(1), m.group(2)) if m else None


def tokens(text, drop_generic=True):
    out = []
    for t in re.findall(r"[a-z0-9]+", (text or "").lower().replace("’", "'").replace("'s", "")):
        if len(t) < 3 and not t.isdigit():
            continue
        if drop_generic and t in GENERIC:
            continue
        out.append(t)
    return out


STRUCTURAL = {"the", "of", "and", "on", "for", "to", "a", "an", "in", "president", "presidents", "presidential", "s"}


def body_words(name):
    """Words of a body's name in order, minus structural glue ('The President's Special Review Board' -> special review board)."""
    out = []
    for t in re.findall(r"[a-z0-9]+", (name or "").lower().replace("\u2019", "'").replace("'s", "")):
        if t not in STRUCTURAL:
            out.append(t)
    return out


def norm_text(text):
    """Lowercase, un-hyphenate line breaks, drop apostrophes, collapse whitespace: for phrase matching in scanned text."""
    t = re.sub(r"\u00ad\s*", "", text or "")          # soft hyphen at a line end
    t = re.sub(r"(?<=\w)-\s*\n\s*(?=[a-z])", "", t)
    t = t.lower().replace("\u2019", "'").replace("'s", "")
    return re.sub(r"\s+", " ", t)


def body_hit(text, words):
    """2 when the body's words occur in order (up to 3 other words between), 1 when all occur anywhere, else 0."""
    if not words:
        return 0
    t = norm_text(text)
    rx = r"\b" + r"\b(?:\W+\w+){0,3}?\W+\b".join(re.escape(w) for w in words) + r"\b"
    if re.search(rx, t):
        return 2
    return 1 if all(re.search(rf"\b{re.escape(w)}\b", t) for w in words) else 0


def eo_numbers(text):
    return list(dict.fromkeys(str(int(n)) for n in re.findall(
        r"(?:\bEO|E\.\s?O\.|Executive\s+Order)\s*(?:No\.?)?\s*(\d{4,5})\b", text or "", re.I)))


# --------------------------------------------------------------------------
# Is this queue request asking for a report's transmittal date?
# --------------------------------------------------------------------------

def is_report_date_request(text):
    """True for 'date the commission submitted its report', 'actual emergency-board report submission' ...

    Needs the word report and a submission word and 'date' or 'actual'; or an emergency board with a report.
    A request for a statute section that merely 'requires reports' is not one."""
    t = text or ""
    if not re.search(r"\breports?\b", t, re.I):
        return False
    created = re.search(r"(?:emergency[- ]board|\bPEB\b|board of inquiry)\b.{0,60}\b(?:created|established|appointed)\b", t, re.I)
    submit = re.search(r"\b(?:submit\w*|submission|transmit\w*|transmittal|presentation|presented|delivered)\b", t, re.I)
    datey = re.search(r"\bdates?\b|\bactual\w*", t, re.I)
    return bool(created or (submit and datey))


LOWER_BODY_RX = re.compile(
    r"((?:(?:[A-Z][A-Za-z'\u2019\-]*|in|of|and|for|on)\s+){1,7}(?:advisory\s+)?(?:commission|committee|task force|board))\b")
LEAD_JUNK_RX = re.compile(r"^(?:(?:actual|date|dates|final|of|and|advisory|the)\s+)+", re.I)


def body_name(text):
    """The commission/committee/board named in a request, or '' (best effort)."""
    for m in BODY_RX.finditer(text or ""):
        name = LEAD_JUNK_RX.sub("", re.sub(r"\s+", " ", m.group(1)).strip())
        if len(tokens(name)) >= 1 and not re.fullmatch(r"(?:the\s+)?(?:Board|Commission|Committee)", name, re.I):
            return name
    for m in LOWER_BODY_RX.finditer(text or ""):         # 'Women in American History commission'
        name = LEAD_JUNK_RX.sub("", re.sub(r"\s+", " ", m.group(1)).strip())
        if len(tokens(name)) >= 1:
            return name
    return ""


def build_spec(text, instrument_ids=(), eo_dates=None, note=""):
    """The search specification for a report-date request, or None. No network, no dates asserted.

    eo_dates: {'12335': '1981-12-28'} signing dates of the orders named, from the OFR index when known.
    note: the queue line's note; it decides whether the request is a report-date request (a line may say so
    only there) and supplies a body name if the citation has none, but its dates are never used."""
    if not is_report_date_request(f"{text} {note}"):
        return None
    t = text
    eo_dates = dict(eo_dates or {})
    nums = list(dict.fromkeys([i.split(":", 1)[1] for i in instrument_ids if str(i).startswith("EO:")] + eo_numbers(t)))
    if re.search(r"emergency[- ]board|\bPEB\b", t, re.I):
        kind = "peb"
    elif re.search(r"board of inquiry", t, re.I):
        kind = "inquiry"
    else:
        kind = "commission"
    body = "" if kind == "peb" else (body_name(t) or body_name(note))
    if kind == "commission" and not body:
        kind = "agency"          # e.g. 'the Secretary of the Interior submitted ... to the President'
    window = None
    m = re.search(r"week of (\d{4}-\d\d-\d\d)\s*(?:to|-|through)\s*(\d{4}-\d\d-\d\d)", t, re.I)
    if m:
        window = [m.group(1), m.group(2)]
    due = None
    dm = re.search(r"\b(?:due|deadline)\b(.{0,90})", t, re.I)
    if dm:
        ds = [d for d in (m2.group(0) for m2 in ISO_RX.finditer(dm.group(1)))]
        if ds:
            due = max(ds)
    text_dates = parse_dates(t)
    signing = [eo_dates[n] for n in nums if n in eo_dates]
    if kind == "inquiry" and not window and not due and signing:
        # A Taft-Hartley board of inquiry reports within days of its creation: search the month after the order.
        d0 = dt.date.fromisoformat(signing[0])
        window = [d0.isoformat(), (d0 + dt.timedelta(days=30)).isoformat()]
        anchor, basis = window[0], "board_of_inquiry_month_after_signing"
    elif window:
        anchor, basis = window[0], "window_in_request"
    elif due:
        anchor, basis = due, "due_date_in_request"
    elif text_dates:
        anchor, basis = text_dates[0], "date_in_request"
    elif signing:
        anchor, basis = signing[0], "order_signing_date"
    else:
        anchor, basis = None, "none"
    # approximate year of the report (for choosing Weekly Compilation vs Public Papers)
    year = int(anchor[:4]) if anchor else None
    if year is None:
        ym = re.search(r"\b(1[89]\d\d|20[0-2]\d)\b", t)
        year = int(ym.group(1)) if ym else None
    return {"kind": kind, "body": body, "body_tokens": tokens(body), "body_words": body_words(body), "eo_numbers": nums, "eo_dates": eo_dates,
            "due": due, "window": window, "text_dates": text_dates, "anchor": anchor, "anchor_basis": basis,
            "year": year, "request_tokens": tokens(re.sub(r"\bEO\s*\d+", " ", t)),
            "lane": lane_for(kind, anchor, year, basis)}


def lane_for(kind, anchor, year, basis=""):
    if kind == "peb":
        return "nmb"
    if kind == "agency":
        return "none"
    if basis == "order_signing_date":
        return "none"      # only the date the body was created: the report date cannot be bracketed
    if kind in ("commission", "inquiry"):
        d = dt.date.fromisoformat(anchor) if anchor else (dt.date(year, 7, 1) if year else None)
        if d is None:
            return "none"
        if d < WCPD_FIRST:
            return "ppp"
        if d <= WCPD_LAST:
            return "wcpd"
        return "dcpd"
    return "none"


def no_route_reason(spec):
    lane = spec.get("lane")
    if lane == "none" and spec.get("anchor_basis") == "order_signing_date" and spec.get("kind") in ("commission", "inquiry"):
        return ("report_date_cannot_be_bracketed: the request gives no due date, window or year (only the order's signing "
                "date); add the due date from the order text, then the Weekly Compilation / Public Papers lane can search")
    if lane == "none":
        return ("report_addressed_to_an_agency_head_or_no_body_named: no presidential-documents route; "
                "needs the report's own front matter or the agency's record")
    if lane == "dcpd":
        return ("report_after_2009_01_19: Daily Compilation (DCPD) needs the govinfo search API (key) or "
                "a date-window package listing; not built")
    if lane == "ppp" and not spec.get("anchor") and not spec.get("year"):
        return "report_date_lane_needs_a_date_or_year_in_the_request"
    return ""


# --------------------------------------------------------------------------
# Presidential Emergency Boards (nmb.gov)
# --------------------------------------------------------------------------

def parse_peb_table(page_html):
    """Rows of the NMB table: peb number, carriers, type, unions, craft, created, closed, comment, pdfs."""
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", page_html or "", re.S | re.I):
        cells = [htmllib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", c))).strip()
                 for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)]
        pdfs = re.findall(r'href="([^"]+\.pdf)"', tr)
        if cells and re.fullmatch(r"\d{1,3}", cells[0] or ""):
            pad = cells + [""] * (8 - len(cells))
            rows.append({"peb": int(pad[0]), "carriers": pad[1], "type": pad[2], "unions": pad[3], "craft": pad[4],
                         "created": pad[5], "closed": pad[6], "comment": pad[7],
                         "pdfs": [htmllib.unescape(p) for p in pdfs]})
    return rows


def match_peb(rows, spec, limit=2):
    """Boards that belong to the order(s) in spec, best first. Index matching only: a lead, not proof.

    Basis A: the board was created within 3 days of an order's signing date (or a date written in the
    request). Basis B: an order date falls inside the board's life (amending/extending orders) AND the
    request names a carrier/union the table row also names. Equal best scores are all returned (two Long
    Island Rail Road boards were created the same day) so each report is fetched and the title page decides."""
    dates = []
    for d in list(spec.get("eo_dates", {}).values()) + list(spec.get("text_dates", [])):
        try:
            dates.append(dt.date.fromisoformat(d))
        except (TypeError, ValueError):
            pass
    rtoks = set(spec.get("request_tokens", []))
    out = []
    for r in rows:
        created, closed = parse_mdy(r.get("created")), parse_mdy(r.get("closed"))
        if not created or not r.get("pdfs"):
            continue
        overlap = len(rtoks & set(tokens(" ".join([r.get("carriers", ""), r.get("unions", ""), r.get("craft", "")]))))
        best = None
        for d in dates:
            gap = abs((created - d).days)
            if gap <= 3:
                s = (100 - gap, "created_within_3_days_of_order_date")
            elif closed and created - dt.timedelta(days=3) <= d <= closed + dt.timedelta(days=7) and overlap:
                s = (40, "order_date_inside_board_life_and_carrier_named")
            else:
                continue
            if best is None or s[0] > best[0]:
                best = s
        if best:
            out.append({"peb": r["peb"], "score": best[0] + 5 * overlap, "basis": best[1], "carrier_overlap": overlap,
                        "row": r})
    out.sort(key=lambda c: (-c["score"], c["peb"]))
    if not out:
        return []
    top = out[0]["score"]
    keep = [c for c in out if c["score"] == top][:limit]
    if len(keep) < limit:
        keep += [c for c in out if c["score"] != top][: limit - len(keep)]
    return keep


DATE_LINE_RX = re.compile(
    r"\b(?:Jan|Feb|Mar|Apr|May|June?|July?|Aug|Sept?|Oct|Nov|Dec)[a-z]*\.?\s*\d{1,2},?\s*\d{4}\b"
    r"|\b\d{1,2}/\d{1,2}/\d{4}\b|\b\d{4}-\d\d-\d\d\b", re.I)


def front_matter_date_lines(page_texts, max_pages=4, limit=14):
    """Verbatim lines carrying a date from the first pages of a found record, with their page numbers.

    page_texts: [(page_number, text)]. These are leads for a reviewer; none is chosen or labelled."""
    out = []
    for page, text in page_texts[:max_pages]:
        for line in (text or "").splitlines():
            ln = re.sub(r"\s+", " ", line).strip()
            if ln and DATE_LINE_RX.search(ln):
                out.append({"page": page, "line": ln[:240]})
                if len(out) >= limit:
                    return out
    return out


def peb_order_mismatch(text, spec):
    """Why an emergency-board report belongs to a different order than the request's ('' when it may be the one).

    The first pages usually say 'Executive Order No. 12491' (older reports) or 'Executive Order dated July 15,
    2022' (recent ones). A named number or date that matches none of the request's orders is a mismatch; a report
    that names neither is not refused (the NMB index match stands, flagged for the reviewer)."""
    want_nums = set(spec.get("eo_numbers") or [])
    named = set(eo_numbers(text))
    if named and want_nums and not (named & want_nums):
        return f"names Executive Order {', '.join(sorted(named))}, not {', '.join(sorted(want_nums))}"
    if named & want_nums:
        return ""
    want_dates = set((spec.get("eo_dates") or {}).values()) | set(spec.get("text_dates") or [])
    dated = set()
    for m in re.finditer(r"Executive\s+Order\s+(?:No\.?\s*)?dated\s+([A-Z][a-z]+\.?\s*\d{1,2},?\s*\d{4})", text or "", re.I):
        dated.update(parse_dates(m.group(1)))
    if dated and want_dates and not (dated & want_dates):
        return f"names an Executive Order dated {', '.join(sorted(dated))}, not {', '.join(sorted(want_dates))}"
    return ""


def report_text_ok(text, spec):
    """Content check for a candidate transmittal record (the body is named and it is a report)."""
    low = (text or "").lower()
    if "report" not in low:
        return False, "no_word_report"
    words = spec.get("body_words") or []
    if words:
        if not body_hit(text, words):
            return False, f"body_name_missing({' '.join(words)})"
        # A multi-page range may contain the named commission in an amendment
        # and an unrelated report in the next item. Require a local association;
        # the old whole-range test accepted EO12627's deadline extension as the
        # Privatization Commission's transmittal record (PPP1988 book1 p294).
        # This remains a retrieval heuristic, never a finding of performance.
        if not any(body_hit(text[max(0, m.start() - 500):m.end() + 500], words)
                   for m in re.finditer(r"\breport\b", text or "", re.I)):
            return False, "report_not_local_to_named_body"
    elif spec.get("kind") == "peb":
        if not re.search(r"emergency board|report to the president", low):
            return False, "not_an_emergency_board_report"
    return True, ""


# --------------------------------------------------------------------------
# Weekly Compilation of Presidential Documents, 1993-2009 (govinfo WCPD)
# --------------------------------------------------------------------------

def wcpd_issue_dates(anchor, back=100, forward=45, cap=MAX_WCPD_ISSUES):
    """Monday issue dates around an anchor, nearest-before first. Issues exist only 1993-01-25..2009-01-19."""
    a = dt.date.fromisoformat(anchor)
    start, end = a - dt.timedelta(days=back), a + dt.timedelta(days=forward)
    d = start + dt.timedelta(days=(7 - start.weekday()) % 7)      # first Monday on/after start
    days = []
    while d <= end:
        if WCPD_FIRST <= d <= WCPD_LAST:
            days.append(d)
        d += dt.timedelta(days=7)
    centre = a - dt.timedelta(days=3)
    days.sort(key=lambda x: (abs((x - centre).days), x))
    return [x.isoformat() for x in days[:cap]]


def wcpd_mods_url(issue):
    return f"https://www.govinfo.gov/metadata/pkg/WCPD-{issue}/mods.xml"


def parse_wcpd_mods(xml_bytes):
    """[{'title', 'htm', 'granule'}] for the documents of one Weekly Compilation issue."""
    text = xml_bytes.decode("utf-8", "replace") if isinstance(xml_bytes, bytes) else xml_bytes
    out = []
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return out
    ns = {"m": "http://www.loc.gov/mods/v3"}
    for item in root.iter("{http://www.loc.gov/mods/v3}relatedItem"):
        if item.get("type") != "constituent":
            continue
        ti = item.find("m:titleInfo/m:title", ns)
        title = (ti.text or "").strip() if ti is not None else ""
        htm = ""
        for u in item.iter("{http://www.loc.gov/mods/v3}url"):
            if (u.text or "").strip().endswith(".htm"):
                htm = u.text.strip()
                break
        if not htm:
            for r in item.iter("{http://www.loc.gov/mods/v3}relatedItem"):
                h = r.get("{http://www.w3.org/1999/xlink}href", "")
                if h.endswith(".htm"):
                    htm = h
                    break
        if title and htm:
            out.append({"title": title, "htm": htm, "granule": item.get("ID", "")})
    return out


def rank_wcpd_titles(items, spec, limit=3):
    """Titles that look like the receipt of the body's report; plus the week's Digest granule as a fallback.

    Returns (title_hits, digest_hits). A title must say report and name the body (words in order)."""
    words = spec.get("body_words") or []
    hits, digests = [], []
    for it in items:
        low = it["title"].lower()
        if low.startswith("digest of other white house announcements"):
            digests.append(it)
            continue
        if "report" not in low or not words:
            continue
        hit = body_hit(it["title"], words)
        if hit < 2:
            continue
        recv = bool(re.search(r"receiv|transmit|submi|present", low))
        hits.append({**it, "score": 1.0 + (0.25 if recv else 0)})
    hits.sort(key=lambda h: -h["score"])
    return hits[:limit], digests[:1]


# --------------------------------------------------------------------------
# Public Papers of the Presidents before 1993: pypdf over HTTP Range requests
# --------------------------------------------------------------------------

class RangeLimit(Exception):
    """The per-case byte or request ceiling for Range reads was reached."""


class RangeFile(io.RawIOBase):
    """A read-only seekable file over HTTP Range requests. `get(start, end)` returns the bytes
    start..end inclusive. Blocks are cached, counted and bounded; nothing is written to disk."""

    SKIP_MIN = 100_000          # a single read at least this long right after an /Image dictionary is image data

    def __init__(self, get, size, block=PPP_BLOCK, max_bytes=PPP_CASE_BYTES, max_requests=PPP_CASE_REQUESTS,
                 skip_images=True):
        super().__init__()
        self._get, self.size, self.block = get, int(size), block
        self.max_bytes, self.max_requests = max_bytes, max_requests
        self.skip_images = skip_images
        self.pos, self.cache, self.bytes_read, self.requests, self.skipped_bytes = 0, {}, 0, 0, 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else (self.pos + off if whence == 1 else self.size + off)
        return self.pos

    def _block(self, i):
        if i not in self.cache:
            a = i * self.block
            b = min(self.size, a + self.block) - 1
            if self.requests >= self.max_requests or self.bytes_read + (b - a + 1) > self.max_bytes:
                raise RangeLimit(f"range read ceiling reached ({self.requests} requests, {self.bytes_read} bytes)")
            data = self._get(a, b)
            if len(data) != b - a + 1:
                raise IOError(f"short range read: wanted {b - a + 1} bytes at {a}, got {len(data)}")
            self.requests += 1
            self.bytes_read += len(data)
            self.cache[i] = data
        return self.cache[i]

    def _just_after_image_dict(self):
        """True when the 600 bytes before the current position (already fetched) hold an /Image dictionary."""
        a = max(0, self.pos - 600)
        buf = bytearray()
        for i in range(a // self.block, (self.pos - 1) // self.block + 1):
            if i not in self.cache:
                return False
            buf += self.cache[i]
        off = a - (a // self.block) * self.block
        return b"/Image" in bytes(buf[off:off + (self.pos - a)])

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        if self.skip_images and n >= self.SKIP_MIN and self.pos > 0 and self._just_after_image_dict():
            # A scanned page's image stream (hundreds of KB). pypdf loads a stream when it resolves the page's
            # XObject, though text extraction never decodes an image. Return zeros of the right length and move on:
            # the bytes that follow (endstream, the next object) are read for real.
            n = min(n, self.size - self.pos)
            self.pos += n
            self.skipped_bytes += n
            return b"\x00" * n
        out = bytearray()
        while n > 0 and self.pos < self.size:
            i, o = divmod(self.pos, self.block)
            chunk = self._block(i)[o:o + n]
            if not chunk:
                break
            out += chunk
            self.pos += len(chunk)
            n -= len(chunk)
        return bytes(out)

    def readinto(self, b):
        d = self.read(len(b))
        b[:len(d)] = d
        return len(d)


_MON = r"(Jan|Feb|Mar|Apr|May|June?|July?|Aug|Sept?|Oct|Nov|Dec)"
HEAD_RX = re.compile(
    _MON + r"\.? (\d{1,2})\s*/\s*Administration"
    r"|Administration of [^/\n]+, \d{4}\s*/\s*" + _MON + r"\.? (\d{1,2})")


def ppp_head_date(text, year):
    """Date from a Public Papers running head ('Feb. 26 / Administration of ...'), or None."""
    m = HEAD_RX.search((text or "")[:240])
    if not m:
        return None
    mon, day = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
    return _date(year, MON_ABBR[mon.lower()], day)


def ppp_bisect(n_pages, page_text, year, target, first=8, span=3):
    """(lo, hi) 0-based page indexes bracketing the first page dated >= target. page_text(i) -> str.

    Running heads are absent on front matter, blank pages and appendices, so a probe looks at the next
    `span` pages; an undated probe narrows toward the front. Returns (lo, hi, probes)."""
    def head(p):
        for q in range(p, min(n_pages, p + span)):
            d = ppp_head_date(page_text(q), year)
            if d:
                return d
        return None
    lo, hi, probes = first, n_pages - 1, []
    while hi - lo > 6:
        mid = (lo + hi) // 2
        d = head(mid)
        probes.append((mid + 1, d.isoformat() if d else None))
        if d is None or d >= target:
            hi = mid
        else:
            lo = mid
    return lo, hi, probes


STRONG_RX = re.compile(r"(?:receiv|transmit|submi|present)\w*[^.]{0,100}\breport|\breport[^.]{0,60}(?:presented|submitted|transmitted)", re.I)


def ppp_scan(n_pages, page_text, year, lo, hi, spec, forward_first=False, back=70, fwd=24, stop_after=None):
    """Find the pages that name the body and speak of its report, scanning from the bisection point.

    A due date: scan backward from the target (reports come in on or before it), then forward. A request window
    (week of A to B): scan forward from the window start until a running head passes `stop_after`, then backward.
    A page must say 'report' and name the body (its words in order). A STRONG page also has a
    receiving/transmitting/submitting phrase near 'report'; the scan stops at the first strong page.
    Returns {'strong': [...], 'weak': [...], 'scanned': [...]} (0-based pages)."""
    words = spec.get("body_words") or []
    res = {"strong": [], "weak": [], "scanned": []}
    if not words:
        return res
    fwd_pages = list(range(hi + 3, min(n_pages, hi + 3 + fwd)))
    bwd_pages = list(range(min(n_pages - 1, hi + 2), max(-1, lo - back), -1))
    if forward_first:
        fwd_pages = list(range(max(0, lo), min(n_pages, lo + fwd)))
        bwd_pages = list(range(lo - 1, max(-1, lo - back), -1))
    order = (fwd_pages + bwd_pages) if forward_first else (bwd_pages + fwd_pages)
    past_stop = False
    for p in order:
        if forward_first and p in fwd_pages and past_stop:
            continue
        low = page_text(p)
        res["scanned"].append(p)
        d = ppp_head_date(low, year)
        if forward_first and stop_after and d and d > stop_after and p in fwd_pages:
            past_stop = True
        if "report" in low.lower() and body_hit(low, words) == 2:
            if STRONG_RX.search(norm_text(low)):
                res["strong"].append(p)
                break
            res["weak"].append(p)
    return res
