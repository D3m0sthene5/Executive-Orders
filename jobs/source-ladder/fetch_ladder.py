"""The never-give-up source ladder, as a reusable module.

Give it a wanted document (order ids, candidate URLs, an optional citation
such as "66 Stat. 259", "2 FR 63", "31 U.S.C. 1552", "5 CFR 352" or
"EO 9337") and it walks, in order:

  1. the given URLs, with retry and backoff;
  2. alternate forms of those URLs (http->https, www/bare host, govinfo
     /app/details <-> /content/pkg, federalregister.gov API JSON);
  3. the Wayback Machine for the given URLs (CDX API, then id_ original bytes);
  4. other official copies worked out from the citation (govinfo link
     service and package URLs for FR, STATUTE, USCODE, CFR; uscode.house.gov;
     eCFR);
  5. the Wayback Machine for those official URLs;
  6. reputable mirrors (Wikisource, Cornell LII, American Presidency Project
     hint URLs passed in by the caller).

A request that asks for the date a report was submitted (emergency board, commission, task force) gets a
report-date lane instead (report_dates.py): the National Mediation Board table and report PDF, the Weekly
Compilation of Presidential Documents (1993-2009) or the Public Papers of the Presidents (before 1993, read by
HTTP Range). It returns the transmittal RECORD with hashes and the verbatim lines that carry dates; it never
asserts the date.

Every request is logged. Bot, CAPTCHA and error pages are failures, never
documents. A success becomes a SOURCE RECORD (see README.md); when every
route fails the caller gets an "exhausted" proposal in the format of
research/readiness/EXHAUSTED.jsonl.

Nothing here is a legal conclusion: a fetched file is source custody only.

Other jobs import this with:
    sys.path.insert(0, str(REPO_ROOT / "jobs" / "source-ladder"))
    import fetch_ladder
"""
from __future__ import annotations

import dataclasses
import hashlib
import html
import html.parser
import io
import json
import os
import re
import socket
import time
import zlib
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from collections import deque
from datetime import date, datetime, timezone
import datetime as dt
from datetime import date as dt_date
from pathlib import Path

try:
    import embedded_cites
    import report_dates
except ImportError:  # loaded by file path from another job's folder
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import embedded_cites
    import report_dates

# The contact part can be set by the owner (e.g. a public URL) with EO_USER_AGENT_CONTACT;
# no personal address is put here by default.
USER_AGENT = ("EO-afterlife-research/1.0 (owner-run research; "
              + (os.environ.get("EO_USER_AGENT_CONTACT") or "contact via repo") + ")")
LEGAL_CUTOFF = "2026-10-14"
CFR_FIRST_GOVINFO_YEAR = 1996     # govinfo annual CFR editions (the link service answers 400 before 1997 for Title 5)
USC_FIRST_GOVINFO_YEAR = 1994     # govinfo U.S. Code editions
RANGE_MIN_INTERVAL = 0.25         # Range reads of ONE open file (blocks of one download), not separate pages
DEFAULT_MIN_INTERVAL = 1.0
HOST_MIN_INTERVAL = {"web.archive.org": 1.5, "archive.org": 1.5}
MAX_REDIRECTS = 6
CHUNK = 1 << 16

# Text that marks a bot wall, CAPTCHA or error page (checked on non-PDF bodies).
BOT_MARKERS = (
    "captcha", "g-recaptcha", "hcaptcha", "cf-chl", "challenge-platform",
    "just a moment...", "attention required!", "access denied",
    "request rejected", "are you a robot", "unusual traffic",
    "enable javascript and cookies", "unblock.federalregister.gov",
    "verify you are human", "bot detection",
)
NOT_FOUND_MARKERS = (
    "<title>page not found", "<title>404", "<title>error", "page you requested could not be found",
    "wayback machine doesn't have that page archived", "hrm. the wayback machine has not archived",
    "this page is not available on the web",
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def safe_name(text: str) -> str:
    """A filename-safe version of an id like 'EO:3016-N' or 'STAT::66 Stat. 259'."""
    out = re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("_")
    return out[:120] or "item"


def unique_file_name(text: str, ext=".txt") -> str:
    """safe_name plus a short hash of the full text, so two long ids never share a file."""
    return safe_name(text)[:100] + "_" + sha256_bytes(text.encode("utf-8"))[:10] + ext


def write_text_lf(path, text: str):
    """Write UTF-8 text with '\n' line endings on every system (Windows would write CRLF)."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


# --------------------------------------------------------------------------
# Wanted documents and routes
# --------------------------------------------------------------------------

@dataclasses.dataclass
class Wanted:
    wanted_id: str
    instrument_ids: list
    urls: list = dataclasses.field(default_factory=list)
    citation: str = ""
    step: str = "original_text"
    requested_by: str = ""
    expect: str = "any"                    # pdf | html | json | xml | text | any
    mirror_urls: list = dataclasses.field(default_factory=list)
    eo_record: dict | None = None          # OFR index record when the citation is an EO
    extra: dict = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class Route:
    route: str          # ladder step name, recorded in ATTEMPTS and SOURCES
    url: str
    expect: str = "any"
    kind: str = "document"   # document | cdx | fr_api | rp_index | peb_index | wcpd_issue | ppp_year | ppp_range
    tier: str = "given"      # given | alternate | wayback_given | official | wayback_official | mirror
    page_hint: int | None = None
    meta: dict | None = None  # report-date lane: {"rd": "peb_report" | "wcpd_doc" | ..., ...}


RP_INDEX_YEARS = (2024, 2023)   # latest Code editions on govinfo that carry the Title 5 Appendix
TIER_ORDER = ("given", "alternate", "wayback_given", "official", "wayback_official", "mirror")


def guess_expect(url: str) -> str:
    path = urllib.parse.urlsplit(url).path.lower()
    if path.endswith(".pdf"):
        return "pdf"
    if path.endswith(".json") or "/api/v1/" in path:
        return "json"
    if path.endswith(".xml"):
        return "xml"
    if path.endswith(".txt"):
        return "text"
    if path.endswith((".htm", ".html")):
        return "html"
    return "any"


def parse_citation(citation: str):
    """Return (type, parts) for a citation, or (None, {}).

    Accepts the Stage 20 'TYPE::...' keys too, e.g. 'STAT::66 Stat. 259'.
    """
    if not citation:
        return None, {}
    text = citation.strip()
    if "::" in text:
        prefix, text = text.split("::", 1)
        if prefix.upper() == "EO":
            text = "EO " + text
    text = text.strip().rstrip(").;, ")
    m = re.fullmatch(r"(?:EO|E\.\s*O\.|Executive\s+Order)\s*(?:No\.?\s*)?(\d{1,5})(?:-?([A-Za-z]))?", text, re.I)
    if m:
        return "EO", {"number": str(int(m.group(1))) + (m.group(2) or "").upper()}
    m = re.fullmatch(r"(\d{1,3})\s*Stat\.?\s*(\d{1,5})", text, re.I)
    if m:
        return "STAT", {"volume": int(m.group(1)), "page": int(m.group(2))}
    m = re.fullmatch(r"(\d{1,3})\s*F\.?\s*R\.?\s*(\d{1,6})", text, re.I)
    if m:
        return "FR", {"volume": int(m.group(1)), "page": int(m.group(2))}
    m = re.fullmatch(r"(\d{1,2})\s*U\.?\s*S\.?\s*C\.?\s*(?:§+\s*)?(\d+[A-Za-z]*(?:-\d+[A-Za-z]*)?)(\([^)]*\))*(?:\(.*)?", text, re.I)
    if m:
        section = m.group(2).split("-")[0]
        return "USC", {"title": int(m.group(1)), "section": section, "as_cited": text}
    m = re.fullmatch(r"(\d{1,2})\s*C\.?\s*F\.?\s*R\.?\s*(?:Part\s*)?(\d+(?:-\d+)?)(?:\.(\w+))?", text, re.I)
    if m:
        part = int(m.group(2)) if m.group(2).isdigit() else m.group(2)   # "102-74" (41 CFR chapter 102) stays text
        return "CFR", {"title": int(m.group(1)), "part": part, "section": m.group(3) or ""}
    m = re.fullmatch(r"Pub(?:lic)?\.?\s*L(?:aw|\.)?\s*(\d{1,3})-(\d{1,4})", text, re.I)
    if m:
        return "PLAW", {"congress": int(m.group(1)), "number": int(m.group(2))}
    m = re.fullmatch(r"Reorg(?:anization|\.)\s*Plan\s+No\.?\s*(\d+)\s+of\s+(\d{4})", text, re.I)
    if m:
        return "RP", {"number": int(m.group(1)), "year": int(m.group(2))}
    return None, {}


# --------------------------------------------------------------------------
# Dated questions and the Code / CFR edition (never let a current edition answer an earlier question)
# --------------------------------------------------------------------------

CURRENT_CUE_RX = re.compile(r"\b(?:current(?:ly)?|in force today|as of today|now in effect|up to date)\b", re.I)
_CITE_NUMBERS_RX = re.compile(
    r"\b\d{1,3}\s*(?:U\.?\s?S\.?\s?C\.?|C\.?\s?F\.?\s?R\.?|Stat\.?|F\.?\s?R\.?)\s*(?:App\.?\s*)?(?:Part\s*|\u00a7+\s*)?[\w.()-]+"
    r"|(?:\bsecs?\.|\bsections?|\u00a7+|\bparts?|\bchapters?|\bPub(?:lic)?\.?\s*L(?:aw|\.)?|\bNo\.|\bEO|\bExecutive\s+Order|\bProclamation)\s*[\d-]+", re.I)
_YEAR_RX = re.compile(r"\b(1[789]\d\d|20[0-2]\d)\b")


def question_text(wanted: "Wanted") -> str:
    """The wording of the question: the whole queue line for an item split out of it."""
    return (wanted.extra or {}).get("parent_citation") or wanted.citation or ""


def request_year(wanted: "Wanted"):
    """The year a request is dated to (the latest year it names), or None when it is undated or asks for current law.

    Years inside citations ('50 U.S.C. 1801', 'Pub. L. 98-525', 'EO 12335') do not count. An explicit
    extra['as_of'] ('current' or a year) wins."""
    ex = wanted.extra or {}
    as_of = ex.get("as_of")
    if as_of == "current":
        return None
    if as_of:
        return int(str(as_of)[:4])
    text = question_text(wanted)
    if CURRENT_CUE_RX.search(text) or CURRENT_CUE_RX.search(ex.get("queue_note") or ""):
        return None
    years = [int(y) for y in _YEAR_RX.findall(_CITE_NUMBERS_RX.sub(" ", text))]
    years = [y for y in years if y <= int(LEGAL_CUTOFF[:4])]
    return max(years) if years else None


def is_dated_earlier(wanted: "Wanted") -> bool:
    y = request_year(wanted)
    return y is not None and y < int(LEGAL_CUTOFF[:4])


def historical_gap(wanted: "Wanted") -> str:
    """Why a dated CFR / U.S. Code request has no govinfo edition to stand on (empty when it has one)."""
    kind, _ = parse_citation(wanted.citation)
    if kind not in ("CFR", "USC") or not is_dated_earlier(wanted):
        return ""
    y = request_year(wanted)
    first = CFR_FIRST_GOVINFO_YEAR if kind == "CFR" else USC_FIRST_GOVINFO_YEAR
    if y >= first:
        return ""
    name = "CFR" if kind == "CFR" else "U.S. Code"
    return (f"historical_{name.lower().replace('.', '').replace(' ', '_')}_not_on_govinfo: the request is dated {y}, before the first "
            f"govinfo annual {name} edition ({first}); a current edition may not stand in for it. Route to the Federal "
            "Register issues of the year, the Statutes at Large or the agency's annual report instead.")


def edition_conflict(wanted: "Wanted", final_url: str, route_url: str = ""):
    """A reason when the copy is a current edition and the request is dated earlier; else ''.

    A numbered govinfo edition passes when it is no later than the year after the question (a CFR title is
    revised once a year, so the edition after the event is the one that shows its effect). A Wayback capture
    of a current page passes only when the capture itself is no later than that year."""
    y = request_year(wanted)
    kind, _ = parse_citation(wanted.citation)
    if y is None or y >= int(LEGAL_CUTOFF[:4]) or kind not in ("USC", "CFR"):
        return ""
    limit = y + 1
    for u in (final_url or "", route_url or ""):
        wb = re.match(r"https?://web\.archive\.org/web/(\d{4})\d*(?:[a-z_]+)?/(.*)$", u)
        inner = wb.group(2) if wb else u
        m = re.search(r"(?:USCODE|CFR)-(\d{4})", inner)
        if m:
            if int(m.group(1)) > limit:
                return f"current_edition_for_dated_request: {m.group(1)} edition does not answer a question dated {y}"
            continue
        on = re.search(r"ecfr\.gov/on/(\d{4})-", inner)
        if on:
            if int(on.group(1)) > limit:
                return f"current_edition_for_dated_request: eCFR text of {on.group(1)} does not answer a question dated {y}"
            continue
        current = (re.search(r"ecfr\.gov|uscode\.house\.gov/view|law\.cornell\.edu", inner)
                   or (re.search(r"govinfo\.gov/link/(?:cfr|uscode)/", inner) and not re.search(r"year=\d{4}", inner)))
        if current:
            if wb and int(wb.group(1)) <= limit:
                continue
            what = f"a {wb.group(1)} capture of a current page" if wb else "a current, unnumbered edition"
            return f"current_edition_for_dated_request: {what} does not answer a question dated {y}"
    return ""


# --------------------------------------------------------------------------
# Report-date lane routes
# --------------------------------------------------------------------------

def report_spec(wanted: "Wanted"):
    return (wanted.extra or {}).get("report_date")


def report_routes(wanted: "Wanted"):
    """Index-first routes for a request that asks when a report was submitted (see report_dates.py)."""
    spec = report_spec(wanted)
    if not spec:
        return []
    lane, routes = spec.get("lane"), []
    if lane == "nmb":
        routes.append(Route("nmb_peb_table", report_dates.NMB_PEB_URL, "html", kind="peb_index", tier="official"))
    elif lane == "wcpd" and spec.get("anchor"):
        for issue in report_dates.wcpd_issue_dates(spec["anchor"]):
            routes.append(Route("wcpd_issue_mods", report_dates.wcpd_mods_url(issue), "xml", kind="wcpd_issue",
                                tier="official", meta={"issue": issue}))
    elif lane == "ppp":
        years = []
        if spec.get("anchor"):
            years.append(int(spec["anchor"][:4]))
            if spec["anchor"][5:7] == "01":
                years.append(int(spec["anchor"][:4]) - 1)
        elif spec.get("year"):
            years.append(int(spec["year"]))
        for y in years:
            routes.append(Route("ppp_year_sitemap", f"https://www.govinfo.gov/sitemap/PPP_{y}_sitemap.xml", "xml",
                                kind="ppp_year", tier="official", meta={"year": y}))
    return routes


def alternate_forms(url: str):
    """Other spellings of the same official URL (deduplicated, excluding url)."""
    out = []
    parts = urllib.parse.urlsplit(url)
    host = parts.hostname or ""
    scheme_https = parts._replace(scheme="https")
    if parts.scheme == "http":
        out.append(("alt_https", urllib.parse.urlunsplit(scheme_https)))
    base = scheme_https
    if host.startswith("www."):
        out.append(("alt_bare_host", urllib.parse.urlunsplit(base._replace(netloc=host[4:]))))
    elif host and host.count(".") == 1:
        out.append(("alt_www_host", urllib.parse.urlunsplit(base._replace(netloc="www." + host))))
    path = parts.path
    if host.endswith("govinfo.gov"):
        m = re.match(r"^/app/details/([^/]+)/([^/?#]+)", path)
        if m:
            out.append(("alt_govinfo_content_pdf", f"https://www.govinfo.gov/content/pkg/{m.group(1)}/pdf/{m.group(2)}.pdf"))
        m = re.match(r"^/app/details/([^/?#]+)/?$", path)
        if m:
            out.append(("alt_govinfo_content_pdf", f"https://www.govinfo.gov/content/pkg/{m.group(1)}/pdf/{m.group(1)}.pdf"))
        m = re.match(r"^/content/pkg/([^/]+)/pdf/([^/?#]+)\.pdf$", path)
        if m:
            out.append(("alt_govinfo_html", f"https://www.govinfo.gov/content/pkg/{m.group(1)}/html/{m.group(2)}.htm"))
    if host.endswith("federalregister.gov"):
        m = re.match(r"^/(?:documents|d)/(?:\d{4}/\d\d/\d\d/)?([0-9A-Za-z-]+?-\d+|[A-Z0-9]+-\d+)(?:/|$)", path)
        if m:
            out.append(("alt_federalregister_api_json", f"https://www.federalregister.gov/api/v1/documents/{m.group(1)}.json"))
    seen, uniq = {url}, []
    for route, u in out:
        if u not in seen:
            seen.add(u)
            uniq.append((route, u))
    return uniq


def cdx_url(url: str) -> str:
    q = urllib.parse.urlencode({"url": url, "output": "json", "limit": "-3",
                                "filter": "statuscode:200",
                                "fl": "timestamp,original,mimetype,statuscode,digest"})
    return "https://web.archive.org/cdx/search/cdx?" + q


def official_routes(wanted: Wanted):
    """Official locations worked out from the citation (and an EO index record)."""
    kind, p = parse_citation(wanted.citation)
    routes = []
    rec = wanted.eo_record or {}
    if kind == "EO" and rec:
        if rec.get("pdf_url"):
            routes.append(Route("ofr_index_pdf_url", rec["pdf_url"], "pdf", tier="official"))
        doc, pub = rec.get("document_number"), rec.get("publication_date")
        if doc and pub:
            routes.append(Route("govinfo_fr_granule_pdf", f"https://www.govinfo.gov/content/pkg/FR-{pub}/pdf/{doc}.pdf", "pdf", tier="official"))
        fr = parse_citation(rec.get("citation") or "")
        issue = Route("govinfo_fr_issue_pdf", f"https://www.govinfo.gov/content/pkg/FR-{pub}/pdf/FR-{pub}.pdf", "pdf", tier="official") \
            if pub and pub < "1995-01-01" else None
        link = Route("govinfo_link_fr", f"https://www.govinfo.gov/link/fr/{fr[1]['volume']}/{fr[1]['page']}", "pdf", tier="official") \
            if fr[0] == "FR" else None
        # From 1994 a daily issue scan is often 300+ MB, so ask the link service first
        # (it usually lands on the small per-document PDF); before 1994 the issue is the route.
        ordered = [link, issue] if pub and pub >= "1994-01-01" else [issue, link]
        routes.extend(r for r in ordered if r)
        if rec.get("full_text_xml_url"):
            routes.append(Route("federalregister_full_text_xml", rec["full_text_xml_url"], "xml", tier="official"))
        if rec.get("html_url"):
            routes.append(Route("federalregister_html", rec["html_url"], "html", tier="official"))
    elif kind == "FR":
        routes.append(Route("govinfo_link_fr", f"https://www.govinfo.gov/link/fr/{p['volume']}/{p['page']}", "pdf", tier="official"))
    elif kind == "STAT":
        v, pg = p["volume"], p["page"]
        routes.append(Route("govinfo_link_statute", f"https://www.govinfo.gov/link/statute/{v}/{pg}", "pdf", tier="official"))
        routes.append(Route("govinfo_statute_granule_pdf", f"https://www.govinfo.gov/content/pkg/STATUTE-{v}/pdf/STATUTE-{v}-Pg{pg}.pdf", "pdf", tier="official"))
    elif kind == "USC":
        t, s = p["title"], p["section"]
        if is_dated_earlier(wanted):
            # A question dated before today is answered by the edition of its own year, never the current Code.
            y = request_year(wanted)
            if y >= USC_FIRST_GOVINFO_YEAR:
                routes.append(Route("govinfo_link_uscode_edition", f"https://www.govinfo.gov/link/uscode/{t}/{s}?link-type=pdf&year={y}", "pdf", tier="official"))
        else:
            routes.append(Route("govinfo_link_uscode", f"https://www.govinfo.gov/link/uscode/{t}/{s}", "pdf", tier="official"))
            routes.append(Route("uscode_house_gov", f"https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title{t}-section{s}&num=0&edition=prelim", "html", tier="official"))
    elif kind == "CFR" and is_dated_earlier(wanted):
        t, part, sec = p["title"], p["part"], p["section"]
        y = request_year(wanted)
        if y >= CFR_FIRST_GOVINFO_YEAR:
            q = {"link-type": "pdf", "year": str(y)}
            if sec:
                q["sectionnum"] = sec
            routes.append(Route("govinfo_link_cfr_edition", f"https://www.govinfo.gov/link/cfr/{t}/{part}?" + urllib.parse.urlencode(q), "pdf", tier="official"))
    elif kind == "CFR":
        t, part, sec = p["title"], p["part"], p["section"]
        q = {"link-type": "pdf", "year": "mostrecent"}
        if sec:
            q["sectionnum"] = sec
        routes.append(Route("govinfo_link_cfr", f"https://www.govinfo.gov/link/cfr/{t}/{part}?" + urllib.parse.urlencode(q), "pdf", tier="official"))
        target = f"section-{part}.{sec}" if sec else f"part-{part}"
        # (No eCFR renderer-API route: ecfr.gov/robots.txt disallows /api/renderer/v1/content/ and
        # /api/versioner/v1/full/, and the ladder obeys robots.txt. The /on/ page below is disallowed too and is
        # recorded as blocked_by_robots_txt; CFR text comes from the govinfo annual edition above.)
        # eCFR point-in-time view on the legal cutoff date (eCFR history starts in 2017).
        routes.append(Route("ecfr_on_cutoff", f"https://www.ecfr.gov/on/{LEGAL_CUTOFF}/title-{t}/{target}", "html", tier="official"))
    elif kind is None and wanted.urls and wanted.citation:
        # Prose citation WITH a given link: if the link fails, fall back to the official route of an embedded
        # statute / Code / CFR cite, but ONLY one that names the same document as a given link (e.g. the link is
        # STATUTE-93-Pg668.pdf and the line cites 93 Stat. 668). Another cite in the line is a different
        # document, and accepting it would mark the request found with something it did not ask for. A link to
        # a dated Code/CFR edition (USCODE-1976-..., CFR-1990-...) gets no current-edition fallback either.
        # (Federal Register cites are skipped: in prose they are usually the page where an order was printed.
        # URL-less prose is split into items instead, see ladder_queue.embedded_children.)
        for c in embedded_cites.find_embedded(wanted.citation, limit=3):
            if c["kind"] in ("STAT", "PLAW", "USC", "CFR") and any(link_names_cite(u, c) for u in wanted.urls):
                routes.extend(official_routes(Wanted(wanted_id="", instrument_ids=[], citation=c["cite"],
                                                     extra={"parent_citation": wanted.citation,
                                                            "queue_note": (wanted.extra or {}).get("queue_note", "")}))[0])
    elif kind == "PLAW":
        c, n = p["congress"], p["number"]
        # The slip-law collection starts with the 104th Congress; the Statutes at Large link service
        # resolves any Congress's public law number to the page of its enrolled text.
        if c >= 104:
            routes.append(Route("govinfo_link_plaw", f"https://www.govinfo.gov/link/plaw/{c}/public/{n}?link-type=pdf", "pdf", tier="official"))
        routes.append(Route("govinfo_link_statute_publaw", f"https://www.govinfo.gov/link/statute/{c}/public/{n}", "pdf", tier="official"))
    elif kind == "RP":
        # Index step, not a source: the Title 5 Appendix prints each plan's Federal Register and Statutes at
        # Large cites in its heading. Ladder.walk reads them and queues the original-publication routes.
        for year in RP_INDEX_YEARS:
            routes.append(Route("uscode_title5_appendix_index",
                                f"https://www.govinfo.gov/content/pkg/USCODE-{year}-title5/pdf/USCODE-{year}-title5-app.pdf",
                                "pdf", kind="rp_index", tier="official"))
    routes.extend(report_routes(wanted))
    return routes, kind, p


def link_names_cite(url: str, cite: dict) -> bool:
    """True when a given link is a copy of the document an embedded cite names (see official_routes)."""
    u, k, p = urllib.parse.unquote(url or ""), cite["kind"], cite["parts"]
    if k == "STAT":
        return bool(re.search(rf"STATUTE-{p['volume']}(?:-Pg{p['page']}(?:-\d+)?)?\.pdf", u))
    if k == "PLAW":
        vols = embedded_cites.stat_volumes_of_congress(p["congress"])
        m = re.search(r"STATUTE-(\d+)", u)
        return bool(m and int(m.group(1)) in vols) or f"PLAW-{p['congress']}publ{p['number']}" in u
    if k == "USC":
        if re.search(r"USCODE-\d{4}", u):
            return False
        return f"title{p['title']}-section{p['section']}&" in u + "&" or f"/uscode/{p['title']}/{p['section']}" in u
    if k == "CFR":
        if re.search(r"CFR-\d{4}", u):
            return False
        if "ecfr.gov" not in u and "govinfo.gov/link/cfr" not in u:
            return False
        tail = f"section-{p['part']}.{p['section']}" if p["section"] else f"part-{p['part']}"
        return f"title-{p['title']}/" in u and (u.endswith(tail) or f"/{tail}/" in u or f"/{tail}?" in u)
    return False


def mirror_routes(wanted: Wanted, kind, p):
    routes = [Route("mirror_hint", u, guess_expect(u), tier="mirror") for u in wanted.mirror_urls]
    if kind in ("USC", "CFR") and is_dated_earlier(wanted):
        return routes        # Cornell LII shows the current text; it cannot answer an earlier-dated question
    if kind == "EO":
        n = re.sub(r"[A-Z]$", "", p["number"])
        routes.append(Route("mirror_wikisource", f"https://en.wikisource.org/wiki/Executive_Order_{n}", "html", tier="mirror"))
    elif kind == "USC":
        routes.append(Route("mirror_cornell_lii", f"https://www.law.cornell.edu/uscode/text/{p['title']}/{p['section']}", "html", tier="mirror"))
    elif kind == "CFR":
        tail = f"{p['part']}.{p['section']}" if p["section"] else f"part-{p['part']}"
        routes.append(Route("mirror_cornell_lii", f"https://www.law.cornell.edu/cfr/text/{p['title']}/{tail}", "html", tier="mirror"))
    return routes


def plan_routes(wanted: Wanted, wayback_limit: int = 3, tiers=TIER_ORDER):
    """Every route the ladder will try, in order (only the tiers named)."""
    given = [Route("given", u, wanted.expect if wanted.expect != "any" else guess_expect(u), tier="given")
             for u in wanted.urls if u]
    alternates = []
    for r in given:
        for route, u in alternate_forms(r.url):
            exp = "json" if route.endswith("api_json") else ("html" if route == "alt_govinfo_html" else r.expect)
            alternates.append(Route(route, u, exp, kind="fr_api" if route.endswith("api_json") else "document", tier="alternate"))
    official, kind, p = official_routes(wanted)
    mirrors = mirror_routes(wanted, kind, p)

    def wayback_for(rs, tier):
        out = []
        for r in rs:
            if len(out) >= wayback_limit:
                break
            if "/link/" in r.url or "/api/" in r.url or r.kind in ("rp_index", "peb_index", "wcpd_issue", "ppp_year", "ppp_range"):
                # (an index-only step: a Wayback copy of the Title 5 Appendix would be taken as the plan itself)
                continue
            out.append(Route("wayback_cdx", cdx_url(r.url), "json", kind="cdx", tier=tier))
        return out

    # A live official Code/CFR page is preferred to an old Wayback capture of the same page.
    live_first = bool(official) and any((urllib.parse.urlsplit(r.url).hostname or "") in ("uscode.house.gov", "www.ecfr.gov", "ecfr.gov")
                                        for r in given)
    if live_first:
        plan = given + alternates + official + wayback_for(given, "wayback_given") \
            + wayback_for(official, "wayback_official") + mirrors
    else:
        plan = given + alternates + wayback_for(given, "wayback_given") + official \
            + wayback_for(official, "wayback_official") + mirrors
    seen, uniq = set(), []
    for r in plan:
        if r.tier in tiers and r.url not in seen:
            seen.add(r.url)
            uniq.append(r)
    return uniq


# --------------------------------------------------------------------------
# Validation: never take an error page for a document
# --------------------------------------------------------------------------

GZIP_MAGIC = b"\x1f\x8b"


def replacement_ratio(data: bytes) -> float:
    """Share of U+FFFD in the start of a body read as UTF-8 (a compressed or binary body scores 30-45%)."""
    text = data[:20_000].decode("utf-8", "replace")
    return text.count("\ufffd") / max(1, len(text))


def is_encoded_body(head: bytes, content_type: str, content_encoding: str) -> str:
    """'gzip' or 'deflate' when a body was stored compressed and must be decoded before hashing/extracting.

    Wayback `id_` links return the archived response bytes, so a page originally served with
    Content-Encoding: gzip arrives as gzip bytes. A .gz FILE that was asked for as such is left alone."""
    enc, ctype = (content_encoding or "").lower(), (content_type or "").lower()
    if head[:2] == GZIP_MAGIC and (("gzip" in enc) or not any(x in ctype for x in ("gzip", "zip"))):
        return "gzip"
    if "deflate" in enc and head[:1] == b"\x78":
        return "deflate"
    return ""


def inflate_file(src, dst, limit, kind="gzip"):
    """Decode a gzip (all members) or zlib file into dst, bounded by `limit` bytes.

    Returns (sha256 hex, bytes, first 300 KB). Raises ValueError for corrupt, truncated or oversize data."""
    wbits = 16 + zlib.MAX_WBITS if kind == "gzip" else zlib.MAX_WBITS
    h, total, head = hashlib.sha256(), 0, b""
    dec, fed = zlib.decompressobj(wbits), False
    pending = b""
    with open(src, "rb") as fi, open(dst, "wb") as fo:
        while True:
            blk = pending or fi.read(CHUNK)
            pending = b""
            if not blk:
                break
            try:
                while blk:
                    fed = True
                    out = dec.decompress(blk, 1 << 20)
                    if out:
                        total += len(out)
                        if total > limit:
                            raise ValueError(f"decoded body larger than {limit} bytes")
                        h.update(out)
                        fo.write(out)
                        if len(head) < 300_000:
                            head += out[: 300_000 - len(head)]
                    if dec.eof:
                        rest = dec.unused_data
                        dec, fed = zlib.decompressobj(wbits), False
                        blk = rest if (kind == "gzip" and rest[:2] == GZIP_MAGIC) else b""
                    else:
                        blk = dec.unconsumed_tail
            except zlib.error as exc:
                raise ValueError(f"undecodable_{kind}: {exc}") from exc
    if fed and not dec.eof:
        raise ValueError(f"truncated_{kind}")
    if total == 0:
        raise ValueError(f"empty_after_{kind}_decode")
    return h.hexdigest(), total, head


def reject_reason(head: bytes, total: int, content_type: str, final_url: str, expect: str):
    """Return why a response is not a real document, or None if it looks real."""
    host = (urllib.parse.urlsplit(final_url).hostname or "").lower()
    path = urllib.parse.urlsplit(final_url).path
    if host.endswith("govinfo.gov") and path.startswith("/error"):
        return "govinfo_error_page"
    if host == "unblock.federalregister.gov":
        return "federalregister_unblock_page"
    if total == 0:
        return "empty_body"
    ctype = (content_type or "").lower()
    is_pdf = head.lstrip()[:5] == b"%PDF-"
    if expect == "pdf":
        if not is_pdf:
            return "not_a_pdf" if "html" not in ctype else "html_instead_of_pdf"
        if total < 300:
            return "tiny_pdf"
        return None
    if is_pdf:
        return None if expect in ("any", "text") else f"pdf_instead_of_{expect}"
    if replacement_ratio(head) > 0.05 or head[:20_000].count(b"\x00") > 200:
        return "binary_or_undecodable_text"      # e.g. a gzip body that was never decoded
    low = head[:200_000].decode("utf-8", "replace").lower()
    for marker in BOT_MARKERS:
        if marker in low:
            return "bot_or_captcha_page:" + marker
    for marker in NOT_FOUND_MARKERS:
        if marker in low:
            return "not_found_page"
    looks_html = "html" in ctype or low.lstrip().startswith(("<!doctype html", "<html"))
    if expect == "json":
        try:
            json.loads(head.decode("utf-8")) if total <= len(head) else None
        except (ValueError, UnicodeDecodeError):
            return "invalid_json"
        return "html_instead_of_json" if looks_html else None
    if looks_html and total < 1500:
        return "tiny_html"
    if expect == "xml" and looks_html:
        return "html_instead_of_xml"
    if total < 200:
        return "tiny_body"
    return None


# --------------------------------------------------------------------------
# HTTP: polite, cached, logged
# --------------------------------------------------------------------------

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect())


def urllib_transport(url, headers, timeout):
    """Return (status, lowercased headers, readable). Never follows redirects."""
    req = urllib.request.Request(url, headers=headers)
    try:
        resp = _OPENER.open(req, timeout=timeout)
        status = resp.status
    except urllib.error.HTTPError as err:
        resp, status = err, err.code
    return status, {k.lower(): v for k, v in resp.headers.items()}, resp


class BudgetExceeded(Exception):
    pass


class RangeBudgetExceeded(Exception):
    """The per-run budget of HTTP Range reads is spent. Only the Range-read route fails (a passing failure);
    unlike BudgetExceeded it does not stop the run, so the other items are still walked."""


class Fetcher:
    """Polite HTTP client: robots.txt, per-host spacing, retries, disk cache."""

    def __init__(self, cache_dir, transport=None, sleep=time.sleep, clock=time.monotonic,
                 max_retries=3, timeout=120, max_bytes=1_500_000_000, max_requests=None,
                 max_total_bytes=None, offline=False, user_agent=USER_AGENT, log=print,
                 range_transport=None, max_range_requests=1500):
        self.cache_dir = Path(cache_dir)
        self.http_dir = self.cache_dir / "http"
        self.http_dir.mkdir(parents=True, exist_ok=True)
        self.transport = transport or urllib_transport
        self.sleep, self.clock = sleep, clock
        self.max_retries, self.timeout, self.max_bytes = max_retries, timeout, max_bytes
        self.max_requests, self.offline = max_requests, offline
        self.max_total_bytes = max_total_bytes          # whole-run download ceiling (None = unlimited)
        self.user_agent, self.log = user_agent, log
        self.requests = 0
        self.bytes_downloaded = 0
        # HTTP Range reads of one large open file (Public Papers volumes) are counted apart from page
        # requests: they would use the whole 300-request budget on one case. They are bounded per case
        # (report_dates.PPP_CASE_*), per run (max_range_requests) and by the whole-run byte ceiling.
        self.range_transport = range_transport or urllib_transport
        self.max_range_requests = max_range_requests
        self.range_requests = 0
        self.range_bytes = 0
        self._last = {}
        self._last_range = {}
        self._robots = {}

    # ----- cache -----
    # Per-URL metadata lives in http/<key>.json; bodies are stored once by
    # their sha256 in blobs/, so the same PDF reached by two URLs is kept once.
    def meta_path(self, url):
        key = sha256_bytes(url.encode("utf-8"))
        return self.http_dir / key[:2] / (key + ".json")

    def blob_path(self, sha, content_type=""):
        ext = ".pdf" if "pdf" in (content_type or "") else ".bin"
        return self.cache_dir / "blobs" / sha[:2] / (sha + ext)

    def cached(self, url):
        meta = self.meta_path(url)
        if not meta.exists():
            return None
        m = json.loads(meta.read_text(encoding="utf-8"))
        blob = self.cache_dir / m.get("blob", "")
        if m.get("blob") and blob.exists():
            if not m.get("content_encoding"):
                m = self._redecode_cached(url, m, blob)
            return m
        return None

    def _redecode_cached(self, url, m, blob):
        """A cache entry written before gzip bodies were decoded: decode its raw blob now, offline, and rewrite the
        entry (raw hash kept as raw_sha256). Returns the entry, or None when the body cannot be decoded."""
        with open(blob, "rb") as fh:
            head = fh.read(16)
        kind = is_encoded_body(head, m.get("content_type", ""), "")
        if not kind:
            return m
        tmp = self.cache_dir / "tmp" / (sha256_bytes((url + "redecode").encode()) + ".dec")
        tmp.parent.mkdir(parents=True, exist_ok=True)
        try:
            dsha, dtotal, dhead = inflate_file(blob, tmp, self.max_bytes, kind)
        except ValueError:
            tmp.unlink(missing_ok=True)
            return None
        if reject_reason(dhead, dtotal, m.get("content_type", ""), m.get("final_url", url), "any"):
            tmp.unlink(missing_ok=True)
            return None
        dblob = self.blob_path(dsha, "pdf" if dhead.lstrip()[:5] == b"%PDF-" else m.get("content_type", ""))
        dblob.parent.mkdir(parents=True, exist_ok=True)
        os.replace(tmp, dblob)
        m = dict(m, raw_sha256=m["sha256"], raw_bytes=m["bytes"], raw_blob=m["blob"], content_encoding=kind,
                 sha256=dsha, bytes=dtotal, blob=self.rel_cache(dblob))
        write_text_lf(self.meta_path(url), json.dumps(m, indent=1))
        return m

    def rel_cache(self, path):
        try:
            return Path(path).resolve().relative_to(self.cache_dir.resolve()).as_posix()
        except ValueError:
            return Path(path).as_posix()

    def forget_body(self, path):
        """Delete a cached body to save disk; its sha256 stays in the metadata.

        A later request for the same URL downloads it again.
        """
        p = Path(path)
        if p.exists() and self.cache_dir.resolve() in p.resolve().parents:
            p.unlink()
            return True
        return False

    # ----- politeness -----
    def _wait(self, host):
        interval = HOST_MIN_INTERVAL.get(host, DEFAULT_MIN_INTERVAL)
        rp = self._robots.get(host)
        if rp is not None:
            delay = rp.crawl_delay(self.user_agent)
            if delay:
                interval = max(interval, float(delay))
        last = self._last.get(host)
        if last is not None:
            gap = self.clock() - last
            if gap < interval:
                self.sleep(interval - gap)
        self._last[host] = self.clock()

    def _count(self):
        if self.max_requests is not None and self.requests >= self.max_requests:
            raise BudgetExceeded(f"request budget of {self.max_requests} reached")
        if self.max_total_bytes is not None and self.bytes_downloaded >= self.max_total_bytes:
            raise BudgetExceeded(f"download budget of {self.max_total_bytes} bytes reached")
        self.requests += 1

    def allowed(self, url):
        parts = urllib.parse.urlsplit(url)
        host = parts.hostname or ""
        if host not in self._robots:
            rp = urllib.robotparser.RobotFileParser()
            robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
            try:
                self._count()
                self._wait(host)
                status, _, resp = self.transport(robots_url, {"User-Agent": self.user_agent}, 30)
                body = resp.read(500_000) if status == 200 else b""
                if status == 200:
                    rp.parse(body.decode("utf-8", "replace").splitlines())
                elif status in (401, 403):
                    rp.disallow_all = True
                else:
                    rp.allow_all = True       # 404 etc.: no robots rules
            except BudgetExceeded:
                raise
            except Exception:                  # unreachable robots.txt: allow, like most crawlers
                rp.allow_all = True
            self._robots[host] = rp
        return self._robots[host].can_fetch(self.user_agent, url)

    # ----- fetching -----
    def fetch(self, url, route="", expect="any"):
        """Fetch url (following redirects). Returns an attempt dict.

        attempt["accepted"] is True only for a real document; then
        attempt["path"] is the cached file.
        """
        att = {"route": route, "url": url, "final_url": url, "time_utc": now_utc(),
               "status": None, "error": "", "bytes": 0, "sha256": "", "content_type": "",
               "from_cache": False, "accepted": False, "reject_reason": "", "page_hint": None,
               "redirects": []}
        if not url.startswith("https://"):
            att["error"] = "not_https"
            return att
        frag = re.search(r"page=(\d+)", urllib.parse.urlsplit(url).fragment or "")
        if frag:
            att["page_hint"] = int(frag.group(1))          # '#page=295' is the requester's page; the server ignores it
        hit = self.cached(url)
        if hit:
            att.update({k: hit.get(k) for k in ("final_url", "status", "bytes", "sha256", "content_type", "redirects",
                                                 "raw_sha256", "raw_bytes", "content_encoding") if k in hit})
            if hit.get("page_hint") is not None:
                att["page_hint"] = hit["page_hint"]
            att["time_utc"] = hit.get("retrieved_utc", att["time_utc"])
            att["from_cache"] = True
            att["accepted"] = True
            att["path"] = str(self.cache_dir / hit["blob"])
            return att
        if self.offline:
            att["error"] = "offline_and_not_cached"
            return att
        current = url
        try:
            for hop in range(MAX_REDIRECTS + 1):
                if not self.allowed(current):
                    att["error"] = "blocked_by_robots_txt"
                    return att
                status, headers, resp = self._request(current)
                att["status"] = status
                if status in (301, 302, 303, 307, 308):
                    loc = headers.get("location", "")
                    resp.close()
                    nxt = urllib.parse.urljoin(current, loc)
                    frag = urllib.parse.urlsplit(nxt).fragment
                    m = re.search(r"page=(\d+)", frag or "")
                    if m and att["page_hint"] is None:
                        att["page_hint"] = int(m.group(1))
                    nxt = urllib.parse.urldefrag(nxt)[0]
                    att["redirects"].append(nxt)
                    att["final_url"] = nxt
                    reason = reject_reason(b"x", 1, "", nxt, "any")
                    if reason in ("govinfo_error_page", "federalregister_unblock_page"):
                        att["error"] = "redirect_to_error_page"
                        att["reject_reason"] = reason
                        return att
                    if not nxt.startswith("https://"):
                        nxt = "https://" + nxt.split("://", 1)[-1]
                        att["final_url"] = nxt
                    hit = self.cached(nxt)
                    if hit:  # the redirect target was downloaded before (e.g. link service -> issue)
                        att.update({k: hit.get(k) for k in ("bytes", "sha256", "content_type", "raw_sha256", "raw_bytes",
                                                             "content_encoding") if k in hit})
                        att["status"] = hit.get("status", 200)
                        att["time_utc"] = hit.get("retrieved_utc", att["time_utc"])
                        att["from_cache"] = True
                        att["accepted"] = True
                        att["path"] = str(self.cache_dir / hit["blob"])
                        att["note"] = "redirect target already in the download cache"
                        return att
                    current = nxt
                    continue
                if status != 200:
                    resp.close()
                    att["error"] = f"http_{status}"
                    return att
                return self._save(att, resp, headers, expect)
            att["error"] = "too_many_redirects"
            return att
        except BudgetExceeded:
            raise
        except Exception as exc:  # network failures after retries
            att["error"] = f"{type(exc).__name__}: {exc}"[:300]
            return att

    def _request(self, url):
        host = urllib.parse.urlsplit(url).hostname or ""
        delay = 2.0
        for n in range(self.max_retries + 1):
            self._count()
            self._wait(host)
            try:
                status, headers, resp = self.transport(url, {"User-Agent": self.user_agent, "Accept": "*/*"}, self.timeout)
            except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError, OSError) as exc:
                if n == self.max_retries:
                    raise
                self.log(f"    retry {n + 1} after {type(exc).__name__} for {url}")
                self.sleep(delay)
                delay *= 2
                continue
            if status in (429, 500, 502, 503, 504) and n < self.max_retries:
                resp.close()
                wait = delay
                ra = headers.get("retry-after", "")
                if ra.isdigit():
                    wait = min(max(float(ra), delay), 180.0)
                self.log(f"    retry {n + 1} after HTTP {status} for {url} (waiting {wait:.0f}s)")
                self.sleep(wait)
                delay *= 2
                continue
            return status, headers, resp
        raise RuntimeError("unreachable")

    def _save(self, att, resp, headers, expect):
        tmp_dir = self.cache_dir / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp = tmp_dir / (sha256_bytes((att["url"] + now_utc()).encode()) + ".part")
        h, total, head = hashlib.sha256(), 0, b""
        try:
            with open(tmp, "wb") as out:
                while True:
                    block = resp.read(CHUNK)
                    if not block:
                        break
                    total += len(block)
                    if total > self.max_bytes:
                        raise ValueError(f"body larger than {self.max_bytes} bytes")
                    if len(head) < 300_000:
                        head += block[: 300_000 - len(head)]
                    h.update(block)
                    out.write(block)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise
        finally:
            resp.close()
        self.bytes_downloaded += total
        att.update({"bytes": total, "sha256": h.hexdigest(), "content_type": headers.get("content-type", "")})
        # A body stored compressed (Wayback `id_` returns the archived gzip bytes) is decoded BEFORE it is hashed
        # as a document or read as text. The raw hash and size are kept beside the decoded ones.
        enc = is_encoded_body(head, att["content_type"], headers.get("content-encoding", ""))
        raw_blob = None
        if enc:
            dec_tmp = tmp_dir / (tmp.name + ".dec")
            try:
                dsha, dtotal, dhead = inflate_file(tmp, dec_tmp, self.max_bytes, enc)
            except ValueError as exc:
                tmp.unlink(missing_ok=True)
                dec_tmp.unlink(missing_ok=True)
                att["reject_reason"] = "undecodable_" + enc
                att["error"] = f"rejected_undecodable_{enc}: {exc}"[:300]
                return att
            raw_blob = self.blob_path(att["sha256"], "gzip")
            raw_blob.parent.mkdir(parents=True, exist_ok=True)
            os.replace(tmp, raw_blob)
            att.update({"raw_sha256": att["sha256"], "raw_bytes": total, "content_encoding": enc,
                        "sha256": dsha, "bytes": dtotal})
            tmp, head, total = dec_tmp, dhead, dtotal
        reason = reject_reason(head, total, att["content_type"], att["final_url"], expect)
        if reason:
            tmp.unlink(missing_ok=True)
            if raw_blob is not None:
                raw_blob.unlink(missing_ok=True)
            att["reject_reason"] = reason
            att["error"] = "rejected_" + reason
            return att
        blob = self.blob_path(att["sha256"], att["content_type"] if head.lstrip()[:5] != b"%PDF-" else "pdf")
        blob.parent.mkdir(parents=True, exist_ok=True)
        os.replace(tmp, blob)
        meta = {k: att[k] for k in ("url", "final_url", "status", "bytes", "sha256", "content_type", "page_hint", "redirects")}
        if enc:
            meta.update({k: att[k] for k in ("raw_sha256", "raw_bytes", "content_encoding")})
            meta["raw_blob"] = self.rel_cache(raw_blob)
        meta["retrieved_utc"] = att["time_utc"]
        meta["blob"] = self.rel_cache(blob)
        mp = self.meta_path(att["url"])
        mp.parent.mkdir(parents=True, exist_ok=True)
        write_text_lf(mp, json.dumps(meta, indent=1))
        att["accepted"] = True
        att["path"] = str(blob)
        return att

    # ----- HTTP Range reads of one large file (report-date lane) -----
    def _range_wait(self, host):
        interval = RANGE_MIN_INTERVAL
        rp = self._robots.get(host)
        if rp is not None:
            delay = rp.crawl_delay(self.user_agent)
            if delay:
                interval = max(interval, float(delay))
        last = self._last_range.get(host)
        if last is not None and self.clock() - last < interval:
            self.sleep(interval - (self.clock() - last))
        self._last_range[host] = self.clock()

    def _range_get(self, url, start, end):
        """Bytes start..end (inclusive) of url, as a 206 response. Retries 429/5xx; follows up to 3 redirects."""
        host = urllib.parse.urlsplit(url).hostname or ""
        delay, current = 2.0, url
        for n in range(self.max_retries + 4):
            if self.max_range_requests is not None and self.range_requests >= self.max_range_requests:
                raise RangeBudgetExceeded(f"range request budget of {self.max_range_requests} reached")
            if self.max_total_bytes is not None and self.bytes_downloaded >= self.max_total_bytes:
                raise BudgetExceeded(f"download budget of {self.max_total_bytes} bytes reached")
            self.range_requests += 1
            self._range_wait(host)
            hdrs = {"User-Agent": self.user_agent, "Accept": "*/*", "Accept-Encoding": "identity",
                    "Range": f"bytes={start}-{end}"}
            try:
                status, headers, resp = self.range_transport(current, hdrs, self.timeout)
            except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError, OSError):
                if n >= self.max_retries:
                    raise
                self.sleep(delay)
                delay *= 2
                continue
            try:
                if status in (301, 302, 303, 307, 308):
                    nxt = urllib.parse.urljoin(current, headers.get("location", ""))
                    if not nxt.startswith("https://") or not self.allowed(nxt):
                        raise IOError("range read redirected to a non-https or disallowed location")
                    current = urllib.parse.urldefrag(nxt)[0]
                    continue
                if status in (429, 500, 502, 503, 504) and n < self.max_retries:
                    self.sleep(delay)
                    delay *= 2
                    continue
                if status != 206:
                    raise IOError(f"range read answered HTTP {status} (a server that ignores Range would send the whole file)")
                body = resp.read(end - start + 2)
            finally:
                resp.close()
            self.range_bytes += len(body)
            self.bytes_downloaded += len(body)
            return body, headers
        raise IOError("range read failed after retries")

    def open_range(self, url, max_bytes=None, max_requests=None):
        """(RangeFile, info) for a large remote file; info has size, last_modified, etag, final_url.

        One bytes=0-0 request learns the size from Content-Range. Nothing is written to disk."""
        if self.offline:
            raise IOError("offline_and_not_cached")
        if not url.startswith("https://") or not self.allowed(url):
            raise PermissionError("blocked_by_robots_txt" if url.startswith("https://") else "not_https")
        body, headers = self._range_get(url, 0, 0)
        m = re.fullmatch(r"bytes 0-0/(\d+)", headers.get("content-range", "").strip())
        if not m:
            raise IOError("no Content-Range total in the range answer")
        info = {"size": int(m.group(1)), "last_modified": headers.get("last-modified", ""),
                "etag": headers.get("etag", ""), "content_type": headers.get("content-type", ""), "url": url}
        rf = report_dates.RangeFile(lambda a, b: self._range_get(url, a, b)[0], info["size"],
                                    max_bytes=max_bytes or report_dates.PPP_CASE_BYTES,
                                    max_requests=max_requests or report_dates.PPP_CASE_REQUESTS)
        return rf, info


# --------------------------------------------------------------------------
# Text extraction
# --------------------------------------------------------------------------

class _TextParser(html.parser.HTMLParser):
    SKIP = {"script", "style", "noscript", "head", "nav", "footer"}
    BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "section", "article", "table", "pre"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def html_to_text(raw: str) -> str:
    p = _TextParser()
    p.feed(raw)
    text = "".join(p.parts)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


def pdf_reader(path):
    try:
        import pypdf  # pinned in requirements.txt
    except ImportError as exc:
        raise RuntimeError("pypdf is not installed: python -m pip install --user -r jobs/source-ladder/requirements.txt") from exc
    import logging
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    return pypdf.PdfReader(str(path), strict=False)


def pdf_pages_text(path, first=None, last=None):
    """Text of PDF pages first..last (1-based, inclusive). Returns (n_pages, [(page, text)])."""
    reader = pdf_reader(path)
    n = len(reader.pages)
    first = max(1, first or 1)
    last = min(n, last or n)
    out = []
    for i in range(first - 1, last):
        try:
            out.append((i + 1, reader.pages[i].extract_text() or ""))
        except Exception as exc:  # damaged page: keep going, say so
            out.append((i + 1, f"[text extraction failed on this page: {type(exc).__name__}]"))
    return n, out


def merge_ranges(ranges, gap=5):
    """Merge [(a, b)] page ranges that overlap or lie within `gap` pages of each other."""
    out = []
    for a, b in sorted((min(a, b), max(a, b)) for a, b in ranges):
        if out and a <= out[-1][1] + gap:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def ranges_from_text(text):
    """'PDF pages 63-95' / 'PDF page 5' / 'PDF pages 319-320; ... PDF pages 321-330' -> merged [(a, b)]."""
    found = []
    for m in re.finditer(r"\bPDF\s+pages?\s+(\d+)(?:\s*(?:-|\u2013|to|through)\s*(\d+))?", text or "", re.I):
        a = int(m.group(1))
        found.append((a, int(m.group(2)) if m.group(2) else a))
    return merge_ranges(found)


def extract_text(path, content_type="", expect="any", page_hint=None, max_pages=40, page_ranges=None,
                 all_pages_max=0):
    """Plain text of a saved document and the page range(s) used (for PDFs).

    Choice of PDF pages, in order: explicit `page_ranges` [(a, b)] (1-based); the whole document when it has at
    most `all_pages_max` pages (statutes: a Public Law is read in full); the whole document when it is short;
    a window around `page_hint`; else the first `max_pages` pages. info['pdf_partial'] says whether pages were left out."""
    with open(path, "rb") as fh:
        head = fh.read(8)
    if head.lstrip()[:5] == b"%PDF-":
        reader_n = len(pdf_reader(path).pages)
        if page_ranges:
            spans = [(max(1, a), min(reader_n, b)) for a, b in page_ranges if a <= reader_n]
            spans = spans or [(1, min(reader_n, max_pages))]
        elif reader_n <= max(max_pages, all_pages_max):
            spans = [(1, reader_n)]
        elif page_hint:
            spans = [(max(1, page_hint - 2), min(reader_n, page_hint + 5))]
        else:
            spans = [(1, min(reader_n, max_pages))]
        pages = []
        for first, last in spans:
            n, got = pdf_pages_text(path, first, last)
            pages.extend(got)
        text = "\n".join(f"=== PDF page {p} of {reader_n} ===\n{t}" for p, t in pages)
        info = {"pdf_pages_total": reader_n, "pdf_first": spans[0][0], "pdf_last": spans[-1][1],
                "pdf_spans": spans, "pdf_partial": sum(b - a + 1 for a, b in spans) < reader_n}
        return text, info
    raw_bytes = Path(path).read_bytes()
    raw = raw_bytes.decode("utf-8", "replace")
    ctype = (content_type or "").lower()
    if "json" in ctype or expect == "json":
        return None, {}
    if replacement_ratio(raw_bytes) > 0.05:
        return None, {"undecodable": True}
    if "html" in ctype or "xml" in ctype or raw.lstrip()[:1] == "<":
        return html_to_text(raw), {}
    return raw, {}


# --------------------------------------------------------------------------
# The ladder
# --------------------------------------------------------------------------

def edition_note(kind, final_url, retrieved_utc=""):
    """Say which edition a USC/CFR copy is, and flag one dated after the legal cutoff."""
    m = re.search(r"(?:USCODE|CFR)-(\d{4})", final_url)
    cutoff_year = int(LEGAL_CUTOFF[:4])
    if "/on/" + LEGAL_CUTOFF in final_url or "/enhanced/" + LEGAL_CUTOFF + "/" in final_url:
        edition = f"eCFR point-in-time text for {LEGAL_CUTOFF}"
        flag = ""
    elif m:
        edition = f"{m.group(1)} edition"
        flag = (" EDITION AFTER THE LEGAL CUTOFF 2026-10-14: the text in force on the cutoff may differ."
                if int(m.group(1)) > cutoff_year else "")
    else:
        edition = "current (unnumbered) edition"
        flag = (f" Retrieved {retrieved_utc[:10]}, after the legal cutoff 2026-10-14: the text in force on the "
                "cutoff may differ." if retrieved_utc[:10] > LEGAL_CUTOFF else "")
    return (f"{edition} of the {kind}; the text in force when the order was issued may differ "
            f"(check the historical edition and its notes).{flag} ")


def rp_index_cites(text: str, number: int, year: int):
    """{'fr': (vol, page), 'stat': (vol, page)} printed in the Title 5 Appendix heading of a plan (may be empty)."""
    flat = re.sub(r"\s+", " ", text)
    head = re.compile(rf"REORGANIZATION PLAN NO\. {number} OF {year} (?=(.{{0,160}}))")
    sent = re.compile(rf"Reorg(?:anization|\.) Plan No\. {number} of {year}, (?=(.{{0,100}}))", re.I)
    starts = re.compile(r"(?:Eff\.|\d{1,3} ?F\.?R\.?|\d{1,3} Stat\.)")
    for rx in (head, sent):
        for m in rx.finditer(flat):
            chunk = m.group(1)
            if not starts.match(chunk):
                continue
            fr = re.search(r"(\d{1,3}) ?F\.? ?R\.? ?(\d{1,6})", chunk)
            st = re.search(r"(\d{1,3}) Stat\. ?(\d{1,5})", chunk)
            if fr or st:
                out = {}
                if fr:
                    out["fr"] = (int(fr.group(1)), int(fr.group(2)))
                if st:
                    out["stat"] = (int(st.group(1)), int(st.group(2)))
                return out
    return {}


# Pages that LIST documents (a search request, not the instrument): never taken as the document.
LISTING_URL_RXS = (
    re.compile(r"congress\.gov/public-laws(?:/\d+(?:st|nd|rd|th)-congress)?/?$", re.I),
    re.compile(r"federalregister\.gov/presidential-documents/executive-orders(?:/\d{4})?/?$", re.I),
    re.compile(r"uscode\.house\.gov/(?:browse|download)(?:[/.][^?]*)?/?$", re.I),
    re.compile(r"govinfo\.gov/app/(?:collection|browse)\b", re.I),
    # A NARA Guide to Federal Records entry describes a record group; it is a finding aid, not a record in it.
    re.compile(r"archives\.gov/research/guide-fed-records/", re.I),
)
USC_MENU_LINE_RX = re.compile(
    r"^\s*(?:Current|\d{4}\s+(?:Main\s+Ed\.|Ed\.(?:\s+and\s+Supplement\s+[IVX]+)?)(?:\s*\(\d{1,2}/\d{1,2}/\d{4}\))?"
    r"|Result\s+\d+\s+of\s+\d+|Back to Original Document|<<\s*Previous|Next\s*>>|\[Print(?: selection)?\](?:\s*\[OLRC Home\]Help)?"
    r"|\[OLRC Home\]Help)\s*$", re.I)


def strip_original_url(url: str) -> str:
    """The page a Wayback `id_` link captured (or the url itself)."""
    return re.sub(r"^https?://web\.archive\.org/web/\d+(?:[a-z_]+)?/", "", url or "")


def is_listing_url(url: str) -> bool:
    u = strip_original_url(url).split("#", 1)[0].split("?", 1)[0]
    return any(rx.search(u) for rx in LISTING_URL_RXS)


def strip_uscode_menu(text: str) -> str:
    """Drop the uscode.house.gov editions menu and navigation lines that html_to_text keeps as leading text."""
    kept = [ln for ln in text.splitlines() if not USC_MENU_LINE_RX.match(ln)]
    return re.sub(r"\n\s*\n+", "\n\n", "\n".join(kept)).strip()


def looks_toc_only(text: str) -> bool:
    """True when the extracted pages are a table of contents / index of sections with (almost) no operative text."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("=== PDF page")]
    if len(lines) < 15:
        return False
    tocish = sum(1 for ln in lines
                 if re.match(r"^(?:SEC\.|Sec\.|SECS\.|TITLE|Title|SUBTITLE|Subtitle|PART|Part|CHAPTER|Chapter)\s*[\dIVXLA-Z]+", ln)
                 or re.search(r"\.{4,}\s*\d+$", ln))
    operative = len(re.findall(r"\b(?:shall|is amended|are amended|is hereby|are hereby|means|authorized to)\b", text))
    pages = max(1, len(re.findall(r"^=== PDF page", text, re.M)))
    return tocish / len(lines) >= 0.5 and operative / pages < 1.5


def requested_section(wanted) -> str:
    """'1632' from 'sec. 1632 of Pub. L. 98-525' (the section a request wants), or ''."""
    text = question_text(wanted)
    m = re.search(r"\bsec(?:tion)?s?\.?\s*(\d+[A-Za-z]?)\s+of\b", text, re.I)
    return m.group(1) if m else ""


def wayback_capture_date(url: str) -> str:
    m = re.match(r"https?://web\.archive\.org/web/(\d{4})(\d\d)(\d\d)", url or "")
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""


def pdf_target_pages(wanted, route, att):
    """(explicit page ranges, statute-like?) for a PDF: 'PDF pages a-b' in the request, #page= hints, Stat. cites."""
    texts = [question_text(wanted)] + [wanted.citation or ""]
    ranges = []
    for t in texts:
        ranges.extend(ranges_from_text(t))
    final = att.get("final_url") or route.url
    statute_like = bool(re.search(r"/(?:STATUTE|PLAW)-", final)) or parse_citation(wanted.citation)[0] in ("STAT", "PLAW")
    hint = att.get("page_hint")
    if not hint:
        fm = re.search(r"page=(\d+)", urllib.parse.urlsplit(route.url).fragment or "")
        hint = int(fm.group(1)) if fm else None
    kind, p = parse_citation(wanted.citation)
    first = re.search(r"STATUTE-\d+-Pg(\d+)", final)
    if not hint and kind == "STAT" and first and p["page"] >= int(first.group(1)):
        hint = p["page"] - int(first.group(1)) + 1               # PDF page of the cited Stat. page in a granule
    return merge_ranges(ranges), statute_like, hint


TEXT_HEADER_END = "Not an authenticated transcription; check the PDF.\n\n"


def _spans_of(page_or_item: str):
    """([(a, b)], total) from '... PDF pages 1-40 of 169' or '... PDF pages 1-5,9-12 of 80', else ([], 0)."""
    m = re.search(r"PDF pages? ([\d,\s-]+) of (\d+)", page_or_item or "")
    if not m:
        return [], 0
    spans = []
    for part in m.group(1).split(","):
        a, _, b = part.strip().partition("-")
        if a.isdigit():
            spans.append((int(a), int(b) if b.isdigit() else int(a)))
    return spans, int(m.group(2))


def carried_defect(wanted, src, text=None) -> str:
    """Why a source found by an EARLIER run fails today's checks, so it must be walked again ('' when it passes).

    Carry-forward otherwise keeps a found record for ever, and the PANIZZI-2 fixes (gzip bodies, partial
    statutes, tables of contents, editions lists, listing pages, current editions for dated questions) would never
    reach the records that showed the defects. The old record is not deleted: the job keeps its hash in the new
    record or row (`supersedes_defective_source`)."""
    if src.get("report_date_request"):
        return ""
    url = src.get("url") or ""
    if is_listing_url(url):
        return "index_page: the URL lists documents or describes a record group; it is not the instrument asked for"
    conflict = edition_conflict(wanted, url, url)
    if conflict:
        return conflict
    body = ""
    if text is not None:
        body = text.decode("utf-8", "replace") if isinstance(text, (bytes, bytearray)) else str(text)
        body = body.split(TEXT_HEADER_END, 1)[-1]
    if body:
        if replacement_ratio(body.encode("utf-8")) > 0.05:
            return "binary_or_undecodable_text: the kept text is compressed or binary bytes read as text"
        if "uscode.house.gov" in strip_original_url(url):
            stripped = strip_uscode_menu(body)
            if "\u00a7" not in stripped and len(stripped) < 600:
                return "index_page: the uscode.house.gov editions list, not the section or note"
        if looks_toc_only(body):
            return "toc_only: the extracted pages are a table of contents, not the text"
    spans, total = _spans_of(src.get("page_or_item", ""))
    statute = bool(re.search(r"/(?:STATUTE|PLAW)-", url))
    if total:
        # 'PDF pages a-b' named in the request (question or citation, as pdf_target_pages reads them).
        asked = merge_ranges(ranges_from_text(question_text(wanted)) + ranges_from_text(wanted.citation or ""))
        wanted_ranges = asked or ([(1, total)] if statute and total <= 500 else [])
        covered = set()
        for a, b in spans:
            covered.update(range(a, b + 1))
        missing = [(a, b) for a, b in wanted_ranges if a <= total
                   and any(p not in covered for p in range(a, min(b, total) + 1))]
        if missing and statute:
            return (f"partial_extraction: a statute PDF of {total} pages was kept as pages "
                    f"{','.join(f'{a}-{b}' for a, b in spans)}; today's ladder reads it in full")
        if missing:
            # MABILLON (2026-10-20): an older run kept the first 40 pages of an FR issue although the request named
            # the pages (EO 11490: 'PDF pages 63-95', kept 1-40 of 96). Today's ladder reads the named pages.
            return (f"partial_extraction: a PDF of {total} pages was kept as pages "
                    f"{','.join(f'{a}-{b}' for a, b in spans)}; the request names PDF pages "
                    f"{','.join(f'{a}-{b}' for a, b in missing)}, which today's ladder reads")
    return ""


def report_extract(wanted, route, att):
    """Content step for the report-date lane: the record must name the body and be a report. No date is asserted."""
    spec = report_spec(wanted) or {}
    rd = (route.meta or {}).get("rd", "")
    path = att["path"]
    if rd == "peb_report":
        text, info = extract_text(path, att.get("content_type", ""), "pdf", page_ranges=[(1, 8)])
        pages = re.split(r"=== PDF page (\d+) of \d+ ===\n", text or "")
        page_texts = [(int(pages[k]), pages[k + 1]) for k in range(1, len(pages) - 1, 2)]
    elif rd in ("wcpd_doc", "wcpd_digest", "ppp_pages"):
        raw = Path(path).read_bytes().decode("utf-8", "replace")
        text = html_to_text(raw) if rd != "ppp_pages" else raw
        page_texts = [(1, text)] if rd != "ppp_pages" else [
            (int(m.group(1)), m.group(3)) for m in re.finditer(r"=== PDF page (\d+) of (\d+)[^\n]*===\n(.*?)(?=\n=== PDF page|\Z)", text, re.S)]
    else:
        return {"ok": False, "reason": "unknown report-date route"}
    if not text or len(re.sub(r"=== PDF page \d+ of \d+[^\n]*===", "", text).strip()) < 200:
        # (page markers alone are not text: an older board report scanned without a text layer ends here)
        return {"ok": False, "reason": "rd_no_meaningful_text: no text layer in the pages read (a scan without OCR?)"}
    ok, why = report_dates.report_text_ok(text, spec)
    if not ok:
        return {"ok": False, "reason": "rd_not_the_report_record: " + why}
    meta = route.meta or {}
    if rd == "peb_report":
        # Two boards can be created the same day (Long Island Rail Road, PEBs 205/206): the NMB table alone cannot
        # tell their reports apart, so a report that names a different order (by number or by date) is refused.
        mism = report_dates.peb_order_mismatch(text, spec)
        if mism:
            return {"ok": False, "reason": "rd_not_the_report_record: " + mism}
    basis = {k: meta[k] for k in meta if k != "rd"}
    leads = report_dates.front_matter_date_lines(page_texts, max_pages=8 if rd == "ppp_pages" else 4)
    if rd == "wcpd_digest":
        toks = spec.get("body_tokens") or []
        leads = [{"page": 1, "line": re.sub(r"\s+", " ", ln).strip()[:300]} for ln in text.splitlines()
                 if "report" in ln.lower() and any(t in ln.lower() for t in toks)][:8] or leads
    name = urllib.parse.urlsplit(att["final_url"]).path.rsplit("/", 1)[-1]
    item = {"peb_report": f"{name} PDF pages 1-8 (front matter; transmittal letter)",
            "wcpd_doc": f"{name} (Weekly Compilation of Presidential Documents, issue {meta.get('issue', '')})",
            "wcpd_digest": f"{name} (Weekly Compilation Digest, issue {meta.get('issue', '')})",
            "ppp_pages": f"{meta.get('book', '')} PDF pages {meta.get('first_page')}-{meta.get('last_page')} "
                         f"(Public Papers of the Presidents, read by HTTP Range)"}[rd]
    return {"ok": True, "text": text, "page_or_item": item,
            "notes": ("Report-date record, custody only: the job asserts no date. The dated lines below are verbatim "
                      "leads; whether one is the transmittal letter, the date received, or only recommendations is a "
                      "reviewer question. " + (meta.get("index_note") or "")).strip(),
            "report_date_leads": leads, "report_date_basis": basis, "report_date_request": spec}


def default_extract(wanted, route, att, fetcher):
    """Default content step: extract text; accept any real document that is the one asked for."""
    if re.search(r"govinfo\.gov/metadata/(?:pkg|granule)/", (att.get("final_url") or "") + " " + route.url) \
            and not (route.meta or {}).get("rd"):
        # PREMIS/MODS fixity metadata: keep the attempt (bytes, hash) but never count it as the document itself.
        return {"ok": False, "reason": "govinfo metadata file (PREMIS/MODS) is not the requested document"}
    if parse_citation(wanted.citation)[0] == "RP" and "USCODE-" in (att.get("final_url") or "") + route.url:
        # The U.S. Code Title 5 Appendix is a compilation: an index for the plan's cites, never its original.
        return {"ok": False, "reason": "a U.S. Code compilation is not a Reorganization Plan's original publication"}
    if (route.meta or {}).get("rd"):
        return report_extract(wanted, route, att) if att.get("path") else {"ok": False, "reason": "rd_no_body"}
    # A listing of laws or documents is a search request, not the instrument ("not found", never exhausted).
    if is_listing_url(att.get("final_url") or "") or is_listing_url(route.url):
        return {"ok": False, "reason": "index_page: the URL lists documents; it is not the instrument asked for"}
    conflict = edition_conflict(wanted, att.get("final_url") or "", route.url)
    if conflict:
        return {"ok": False, "reason": conflict}
    if not att.get("path"):
        return {"ok": True, "text": None, "page_or_item": wanted.citation or route.url, "notes": "body not kept in cache"}
    ranges, statute_like, hint = pdf_target_pages(wanted, route, att)
    text, info = extract_text(att["path"], att.get("content_type", ""), route.expect, hint,
                              page_ranges=ranges or None, all_pages_max=500 if statute_like else 0)
    if info.get("undecodable"):
        return {"ok": False, "reason": "binary_or_undecodable_text: the body is not readable text (compressed or binary)"}
    url_host = strip_original_url(att.get("final_url") or route.url)
    if text and "uscode.house.gov" in url_host:
        text = strip_uscode_menu(text)
        if "\u00a7" not in text and len(text) < 600:
            return {"ok": False, "reason": "index_page: the uscode.house.gov editions list, not the section or note"}
    if not info.get("pdf_pages_total") and (text is None or len(text.strip()) < 200):
        return {"ok": False, "reason": "no meaningful text in this page (landing, script or error page?)"}
    page = wanted.citation or ""
    name = urllib.parse.urlsplit(att["final_url"]).path.rsplit("/", 1)[-1]
    if info.get("pdf_pages_total"):
        spans = ",".join(f"{a}-{b}" for a, b in info["pdf_spans"])
        page = f"{page}; {name} PDF pages {spans} of {info['pdf_pages_total']}".strip("; ")
        if info["pdf_partial"]:
            page += " (PARTIAL: other pages not extracted)"
        if att.get("page_hint"):
            page += f" (page hint {att['page_hint']})"
    elif not page:
        page = name
    notes = ""
    kind, p = parse_citation(wanted.citation)
    final_url = att.get("final_url") or ""
    edition_kind = kind if kind in ("USC", "CFR") else ("USC" if "USCODE-" in final_url else ("CFR" if re.search(r"/CFR-\d{4}", final_url) else None))
    if edition_kind:       # also for a prose request whose route landed on a numbered Code/CFR edition
        notes = edition_note(edition_kind, final_url, att.get("time_utc", ""))
    cap = wayback_capture_date(att.get("final_url") or "") or wayback_capture_date(route.url)
    if cap:
        stale = cap < LEGAL_CUTOFF
        notes += (f"Wayback capture of {cap}" + (f" is {( date.fromisoformat(LEGAL_CUTOFF) - date.fromisoformat(cap)).days} days older "
                  f"than the legal cutoff {LEGAL_CUTOFF}; the live page may differ. " if stale else ". "))
    if kind == "PLAW" and text is not None:
        c, n = p["congress"], p["number"]
        seen = re.search(rf"PUBLIC\s+LAW\s+(?:{c}\s*[-\u2013]\s*)?{n}\b", text, re.I)
        notes = "public law %d-%d %s in the extracted pages (check the PDF)" % (c, n, "seen" if seen else "NOT seen")
    if kind == "STAT" and text is not None and att.get("page_hint"):
        hint_text = ""
        m = re.search(rf"=== PDF page {att['page_hint']} of \d+ ===\n(.*?)(?:\n=== PDF page|\Z)", text, re.S)
        if m:
            hint_text = m.group(1)
        notes = ("printed page number %s %s on the hinted PDF page" %
                 (p["page"], "seen" if re.search(rf"\b{p['page']}\b", hint_text) else "NOT seen"))
    if info.get("pdf_pages_total") and text is not None:
        sec = requested_section(wanted)
        if sec:
            has = bool(re.search(rf"\bSEC(?:TION|\.)\s*{re.escape(sec)}\b", text, re.I))
            notes += f"section {sec} {'seen' if has else 'NOT seen'} in the extracted pages. "
            if not has and info["pdf_partial"]:
                return {"ok": False, "reason": f"partial_extraction: section {sec} is not in the extracted pages "
                                              f"{page.split(';')[-1].strip()}"}
        if looks_toc_only(text):
            return {"ok": False, "reason": "toc_only: the extracted pages are a table of contents, not the text"}
    return {"ok": True, "text": text, "page_or_item": page, "notes": notes.strip()}


# --------------------------------------------------------------------------
# Was a failure definitive (the document is not there) or transient (try again)?
# --------------------------------------------------------------------------

NOT_PROOF_OF_ABSENCE = ("index_page", "toc_only", "partial_extraction", "binary_or_undecodable", "rd_",
                        "current_edition_for_dated_request")
TRANSIENT_HTTP = {401, 403, 408, 425, 429}   # 401/403: a login or bot wall, or a block of this machine


def attempt_outcome(a):
    """'ok', 'definitive' or 'transient' for one logged attempt.

    definitive: HTTP 404/410 and similar, a govinfo /error redirect, robots.txt
    disallow, a validated rejection (not a PDF, a not-found page), or a content
    check that failed. transient: offline, network errors, timeouts, 429, 5xx,
    401/403, CAPTCHA or bot walls, the size limit, anything unknown.
    """
    if a.get("accepted"):
        return "ok"
    err = str(a.get("error") or "")
    rr = str(a.get("reject_reason") or "")
    if rr.startswith("content_check"):
        # These say "this copy cannot be used", not "the document is not there": never a basis for exhaustion.
        if rr[len("content_check:"):].strip().startswith(NOT_PROOF_OF_ABSENCE):
            return "transient"
        return "definitive"
    if rr.startswith("undecodable_") or rr == "binary_or_undecodable_text":
        return "transient"
    if err == "offline_and_not_cached":
        return "transient"
    if err.startswith("http_"):
        code = int(err[5:]) if err[5:].isdigit() else 0
        return "transient" if (code in TRANSIENT_HTTP or code >= 500 or code == 0) else "definitive"
    if err == "redirect_to_error_page":
        return "transient" if rr == "federalregister_unblock_page" else "definitive"
    if err in ("blocked_by_robots_txt", "not_https", "too_many_redirects"):
        return "definitive"
    if err.startswith("rejected_"):
        return "transient" if (rr.startswith("bot_or_captcha") or rr == "federalregister_unblock_page") else "definitive"
    return "transient"


def classify_failure(attempts, offline=False, no_route_note=""):
    """(outcome, why) for a walk that found nothing.

    outcome is 'exhausted' only when at least one route really answered and
    every route ended definitively; 'retry_later' when anything was transient
    or the run was offline; 'no_route' when no route could be built (no_route_note says why, e.g. a dated
    CFR question that predates the first govinfo edition).
    """
    if not attempts:
        return "no_route", no_route_note or "no route could be built for this citation (no URL, unknown citation form)"
    if offline:
        return "retry_later", "offline run (JOB_OFFLINE=1): nothing new was requested"
    transient = [a for a in attempts if attempt_outcome(a) == "transient"]
    real = [a for a in attempts if a.get("status") is not None or a.get("from_cache")
            or a.get("error") == "blocked_by_robots_txt"]
    if transient:
        kinds = sorted({str(a.get("reject_reason") or a.get("error") or a.get("status"))[:60] for a in transient})
        return "retry_later", f"{len(transient)} route(s) failed for a passing reason: " + "; ".join(kinds[:5])
    if not real:
        return "retry_later", "no route got an answer from a server"
    return "exhausted", ""


class Ladder:
    def __init__(self, fetcher, extract=default_extract, log=print, wayback_limit=3, tiers=TIER_ORDER):
        self.fetcher, self.extract, self.log = fetcher, extract, log
        self.wayback_limit, self.tiers = wayback_limit, tiers

    def walk(self, wanted: Wanted, routes=None):
        """Try every route until one gives an accepted document.

        Returns {"source": dict|None, "text": str|None, "attempts": [...],
                 "exhausted": dict|None}.
        """
        queue = deque(routes if routes is not None else plan_routes(wanted, self.wayback_limit, self.tiers))
        seen, attempts = set(), []
        while queue:
            r = queue.popleft()
            if r.url in seen:
                continue
            seen.add(r.url)
            if r.kind == "ppp_range":
                att = self._range_read(r, wanted)
            else:
                att = self.fetcher.fetch(r.url, r.route, r.expect)
            att["wanted_id"] = wanted.wanted_id
            att["instrument_ids"] = list(wanted.instrument_ids)
            att["tier"] = r.tier
            attempts.append(att)
            if not att["accepted"]:
                continue
            if r.kind == "cdx":
                new = self._from_cdx(att)
                att["note"] = f"{len(new)} Wayback captures listed"
                queue.extendleft(reversed(new))
                continue
            if r.kind == "rp_index":
                new, note = self._from_rp_index(att, wanted)
                att["note"] = note
                if not new:
                    # Not listed (or unreadable): a passing failure, so it can never be proposed as exhausted.
                    att["accepted"] = False
                    att["error"] = "rp_not_found_in_title5_appendix"
                    continue
                queue = deque(x for x in queue if x.kind != "rp_index")   # the other edition is not needed
                queue.extendleft(reversed(new))
                continue
            if r.kind == "fr_api":
                new = self._from_fr_api(att)
                att["note"] = f"{len(new)} document links in API record"
                queue.extendleft(reversed(new))
                continue
            if r.kind in ("peb_index", "wcpd_issue", "ppp_year"):
                # Index steps of the report-date lane: they list where the transmittal record may be and are never
                # kept as the source. An index that yields nothing is a passing failure (rd_*), never exhaustion.
                step = {"peb_index": self._from_peb_index, "wcpd_issue": self._from_wcpd_issue,
                        "ppp_year": self._from_ppp_year}[r.kind]
                new, late, note = step(att, wanted, r)
                att["note"] = note
                if not new and not late:
                    att["accepted"] = False
                    att["error"] = "rd_nothing_matched"
                    att["reject_reason"] = "rd_nothing_matched: " + note
                    continue
                queue.extendleft(reversed(new))
                queue.extend(late)
                continue
            try:
                result = self.extract(wanted, r, att, self.fetcher)
            except Exception as exc:
                result = {"ok": False, "reason": f"extraction_error: {type(exc).__name__}: {exc}"[:300]}
            if not result.get("ok"):
                att["accepted"] = False
                att["reject_reason"] = "content_check: " + result.get("reason", "")
                continue
            return {"source": self.source_record(wanted, r, att, result), "text": result.get("text"),
                    "attempts": attempts, "exhausted": None, "result": result, "outcome": "found", "why": ""}
        note = historical_gap(wanted) or (report_dates.no_route_reason(report_spec(wanted)) if report_spec(wanted) else "")
        outcome, why = classify_failure(attempts, offline=getattr(self.fetcher, "offline", False), no_route_note=note)
        return {"source": None, "text": None, "attempts": attempts, "outcome": outcome, "why": why,
                "exhausted": self.exhausted_records(wanted, attempts) if outcome == "exhausted" else None}

    def _from_cdx(self, att):
        if not att.get("path"):
            return []
        try:
            rows = json.loads(Path(att["path"]).read_text(encoding="utf-8") or "[]")
        except ValueError:
            return []
        out = []
        for row in rows[1:][::-1]:              # newest first
            if len(row) >= 2 and str(row[0]).isdigit():
                original = row[1]
                exp = guess_expect(original)
                if len(row) > 2 and "pdf" in str(row[2]):
                    exp = "pdf"
                out.append(Route("wayback_id_", f"https://web.archive.org/web/{row[0]}id_/{original}", exp,
                                 tier=att.get("tier", "wayback_given")))
        return out[:2]

    def _from_rp_index(self, att, wanted):
        """Original-publication routes for a Reorganization Plan, read from the Title 5 Appendix heading.

        The Appendix is a current compilation: it is used ONLY to learn the plan's Federal Register and
        Statutes at Large cites. It is never kept as the source (a compilation is not the original)."""
        kind, p = parse_citation(wanted.citation)
        if kind != "RP" or not att.get("path"):
            return [], "not a Reorganization Plan citation"
        try:
            _, pages = pdf_pages_text(att["path"])
        except Exception as exc:
            return [], f"index unreadable: {type(exc).__name__}"
        cites = rp_index_cites("\n".join(t for _, t in pages), p["number"], p["year"])
        out = []
        if cites.get("stat"):
            v, pg = cites["stat"]
            out.append(Route("govinfo_link_statute_from_rp_index", f"https://www.govinfo.gov/link/statute/{v}/{pg}", "pdf", tier="official"))
        if cites.get("fr"):
            v, pg = cites["fr"]
            out.append(Route("govinfo_link_fr_from_rp_index", f"https://www.govinfo.gov/link/fr/{v}/{pg}", "pdf", tier="official"))
        if not out:
            return [], f"Reorganization Plan No. {p['number']} of {p['year']} has no Stat./FR cite in this Appendix edition"
        return out, "index lists " + "; ".join(f"{k.upper()} {v[0]}/{v[1]}" for k, v in cites.items() if v)

    # ----- report-date lane: index steps -----
    def _from_peb_index(self, att, wanted, route):
        spec = report_spec(wanted)
        html_text = Path(att["path"]).read_bytes().decode("utf-8", "replace")
        rows = report_dates.parse_peb_table(html_text)
        if not rows:
            return [], [], "the NMB emergency-board table could not be parsed (0 rows)"
        cands = report_dates.match_peb(rows, spec)
        ties = [c["peb"] for c in cands if c["score"] == cands[0]["score"]] if cands else []
        out = []
        for c in cands:
            r = c["row"]
            tie_note = (f" Boards {', '.join(map(str, ties))} match the order equally; check that this report names "
                        "the order (number or date) before relying on it.") if len(ties) > 1 else ""
            for pdf in r["pdfs"][:2]:
                out.append(Route("nmb_peb_report", pdf, "pdf", tier="official", meta={
                    "rd": "peb_report", "peb": c["peb"], "match_basis": c["basis"], "carrier_overlap": c["carrier_overlap"],
                    "nmb_table_created": r["created"], "nmb_table_closed": r["closed"], "nmb_table_carriers": r["carriers"],
                    "equal_candidates": ties if len(ties) > 1 else [],
                    "index_note": "NMB table dates (created/closed) are an index, not proof of the transmittal date." + tie_note}))
        return out, [], (f"{len(rows)} boards in the NMB table; matched PEB " + ", ".join(str(c["peb"]) for c in cands)
                         if cands else f"{len(rows)} boards in the NMB table; none matched the order dates {sorted(spec.get('eo_dates', {}).values()) or spec.get('text_dates')}")

    def _from_wcpd_issue(self, att, wanted, route):
        spec = report_spec(wanted)
        items = report_dates.parse_wcpd_mods(Path(att["path"]).read_bytes())
        hits, digests = report_dates.rank_wcpd_titles(items, spec)
        issue = (route.meta or {}).get("issue", "")
        out = [Route("wcpd_document", h["htm"], "html", tier="official", meta={
            "rd": "wcpd_doc", "issue": issue, "title": h["title"], "title_score": h["score"],
            "index_note": f"Listed in the MODS of Weekly Compilation issue {issue}."}) for h in hits]
        late = [Route("wcpd_digest", d["htm"], "html", tier="official", meta={
            "rd": "wcpd_digest", "issue": issue, "title": d["title"],
            "index_note": f"Digest granule of issue {issue}; used only when no titled item names the report."}) for d in digests]
        # A Digest is only a fallback: queue it after the other issues.
        if out:
            late = []
        return out, late, f"issue {issue}: {len(items)} documents, {len(hits)} title match(es)"

    def _from_ppp_year(self, att, wanted, route):
        text = Path(att["path"]).read_bytes().decode("utf-8", "replace")
        books = list(dict.fromkeys(re.findall(r"/app/details/(PPP-\d{4}-book\d+)", text)))
        books.sort(key=lambda b: int(b.rsplit("book", 1)[1]))
        out = [Route("ppp_range_read", f"https://www.govinfo.gov/content/pkg/{b}/pdf/{b}.pdf", "pdf", kind="ppp_range",
                     tier="official", meta={"rd": "ppp_pages", "book": b, "year": (route.meta or {}).get("year")}) for b in books]
        return out, [], f"{len(books)} Public Papers volume(s) for {(route.meta or {}).get('year')}: {', '.join(books)}"

    def _range_read(self, route, wanted):
        """Read a few pages of a Public Papers volume by HTTP Range and keep their text (hashed) as the record.

        The whole volume (0.7-1.0 GB) is never downloaded and its sha256 is not computed; the Content-Length,
        Last-Modified and ETag of the file are recorded as its fixity anchor. Bounded per case and per run."""
        att = {"route": route.route, "url": route.url, "final_url": route.url, "time_utc": now_utc(), "status": None,
               "error": "", "bytes": 0, "sha256": "", "content_type": "text/plain", "from_cache": False,
               "accepted": False, "reject_reason": "", "page_hint": None, "redirects": []}
        spec = report_spec(wanted)
        meta = route.meta or {}
        f = self.fetcher
        try:
            import logging
            import pypdf
            logging.getLogger("pypdf").setLevel(logging.ERROR)
            rf, info = f.open_range(route.url)
        except BudgetExceeded:
            raise
        except RangeBudgetExceeded as exc:
            att["error"] = att["reject_reason"] = f"rd_range_budget_reached: {exc}"[:300]
            return att
        except PermissionError as exc:
            att["error"] = "blocked_by_robots_txt" if "robots" in str(exc) else f"PermissionError: {exc}"[:300]
            return att
        except Exception as exc:
            att["error"] = f"{type(exc).__name__}: {exc}"[:300]
            return att
        att["status"] = 206
        year = int(meta.get("year") or spec.get("year"))
        target = spec.get("window", [None])[0] if spec.get("window") else spec.get("anchor")
        target = dt_date.fromisoformat(target) if target else dt_date(year, 7, 1)
        cache: dict = {}
        try:
            reader = pypdf.PdfReader(rf, strict=True)
            n = len(reader.pages)

            def page_text(i):
                if i not in cache:
                    try:
                        cache[i] = reader.pages[i].extract_text() or ""
                    except (report_dates.RangeLimit, BudgetExceeded, RangeBudgetExceeded, PermissionError):
                        raise
                    except Exception:
                        cache[i] = ""
                return cache[i]

            lo, hi, probes = report_dates.ppp_bisect(n, page_text, year, target)
            # Does this volume cover the date at all? (A year has several books.)
            near = [report_dates.ppp_head_date(page_text(q), year) for q in range(max(0, lo - 1), min(n, hi + 4))]
            near = [d for d in near if d]
            tol = dt.timedelta(days=45)
            if not near or not (min(near) <= target + tol and max(near) >= target - tol):
                att["error"] = "rd_volume_does_not_cover_date"
                att["reject_reason"] = "rd_volume_does_not_cover_date: running heads near the bisection point are " + \
                    (", ".join(sorted({d.isoformat() for d in near})[:4]) or "absent")
                att["note"] = f"{meta.get('book')}: {n} pages; bisected to PDF page {lo + 1}; {rf.requests} range requests"
                att["range_requests"], att["range_bytes"] = rf.requests, rf.bytes_read
                return att
            window = spec.get("window")
            stop = dt_date.fromisoformat(window[1]) + dt.timedelta(days=2) if window else None
            scan = report_dates.ppp_scan(n, page_text, year, lo, hi, spec, forward_first=bool(window),
                                         back=30 if window else 140, fwd=90 if window else 40, stop_after=stop)
        except report_dates.RangeLimit as exc:
            att["error"] = "rd_range_limit"
            att["reject_reason"] = "rd_range_limit: " + str(exc)
            att["range_requests"], att["range_bytes"] = rf.requests, rf.bytes_read
            return att
        except RangeBudgetExceeded as exc:
            att["error"] = att["reject_reason"] = f"rd_range_budget_reached: {exc}"[:300]
            att["range_requests"], att["range_bytes"] = rf.requests, rf.bytes_read
            return att
        except BudgetExceeded:
            raise
        except Exception as exc:
            att["error"] = f"rd_range_read_failed: {type(exc).__name__}: {exc}"[:300]
            att["reject_reason"] = att["error"]
            att["range_requests"], att["range_bytes"] = getattr(rf, "requests", 0), getattr(rf, "bytes_read", 0)
            return att
        hits = scan["strong"] or scan["weak"][:2]
        att["range_requests"], att["range_bytes"] = rf.requests, rf.bytes_read
        att["note"] = (f"{meta.get('book')}: {n} pages, bisected to PDF page {lo + 1}-{hi + 1} ({len(probes)} probes), "
                       f"scanned {len(scan['scanned'])} pages, {len(scan['strong'])} strong / {len(scan['weak'])} weak hit(s); "
                       f"{rf.requests} range requests, {rf.bytes_read} bytes")
        if not hits:
            att["error"] = "rd_not_found_in_window"
            att["reject_reason"] = "rd_not_found_in_window: " + att["note"]
            return att
        p = hits[0]
        first, last = max(0, p - 2), min(n - 1, p + 2)
        parts = []
        for q in range(first, last + 1):
            d = report_dates.ppp_head_date(page_text(q), year)
            parts.append(f"=== PDF page {q + 1} of {n} (running head date: {d.isoformat() if d else 'none'}) ===\n{page_text(q)}")
        body = (f"Public Papers of the Presidents, {meta.get('book')}, read by HTTP Range from {route.url}\n"
                f"File Content-Length {info['size']}, Last-Modified {info['last_modified']}, ETag {info['etag']}; "
                f"the whole file was not downloaded or hashed.\n" + "\n".join(parts))
        sha = sha256_bytes(body.encode("utf-8"))
        out = f.cache_dir / "ranges" / sha[:2] / (sha + ".txt")
        write_text_lf(out, body)
        meta.update({"first_page": first + 1, "last_page": last + 1, "matched_pdf_page": p + 1,
                     "file_content_length": info["size"], "file_last_modified": info["last_modified"],
                     "file_etag": info["etag"], "strong_hit": bool(scan["strong"]),
                     "range_requests": rf.requests, "range_bytes": rf.bytes_read,
                     "index_note": "Range read; assembled page text hashed, whole file not hashed (Content-Length/Last-Modified recorded)."})
        route.meta = meta
        att.update({"accepted": True, "path": str(out), "bytes": len(body.encode("utf-8")), "sha256": sha,
                    "final_url": route.url})
        return att

    def _from_fr_api(self, att):
        if not att.get("path"):
            return []
        try:
            rec = json.loads(Path(att["path"]).read_text(encoding="utf-8"))
        except ValueError:
            return []
        out = []
        for field, exp in (("pdf_url", "pdf"), ("full_text_xml_url", "xml"), ("body_html_url", "html")):
            u = rec.get(field)
            if isinstance(u, str) and u.startswith("https://"):
                out.append(Route("federalregister_api_" + field, u, exp, tier="alternate"))
        return out

    @staticmethod
    def source_record(wanted, route, att, result, text_path=None, produced_by="source-ladder"):
        return {
            "source_id": f"{produced_by}:{safe_name(wanted.wanted_id)}:{att['sha256'][:12]}",
            "instrument_ids": list(wanted.instrument_ids),
            "url": att["final_url"] if att["final_url"].startswith("https://") else att["url"],
            "requested_url": att["url"],
            "sha256": att["sha256"],
            "bytes": att["bytes"],
            "content_type": att.get("content_type", ""),
            "retrieved_utc": att["time_utc"],
            "route": f"{route.tier}/{route.route}",
            "page_or_item": result.get("page_or_item") or wanted.citation,
            "text_path": text_path,
            "cache_path": None,
            "notes": result.get("notes", ""),
            "wanted_id": wanted.wanted_id,
            "citation": wanted.citation,
            **({"embedded_in_request": wanted.extra["parent_citation"][:300]}
               if wanted.extra.get("parent_citation") else {}),
            **({"raw_sha256": att["raw_sha256"], "raw_bytes": att["raw_bytes"],
                "content_encoding_decoded": att["content_encoding"]} if att.get("content_encoding") else {}),
            **({k: result[k] for k in ("report_date_leads", "report_date_basis", "report_date_request") if k in result}),
            **({"expected_sha256": wanted.extra["expected_sha256"],
                "matches_expected_sha256": att["sha256"] == wanted.extra["expected_sha256"]}
               if wanted.extra.get("expected_sha256") else {}),
        }

    @staticmethod
    def exhausted_records(wanted, attempts, recorded_by="source-ladder job", today=None):
        searched = []
        for a in attempts:
            outcome = a.get("reject_reason") or a.get("error") or (f"http_{a['status']}" if a.get("status") else "")
            if a.get("note"):
                outcome = outcome or a["note"]
            searched.append(f"{a.get('tier', '')}/{a['route']}: {a['url']} -> {outcome or 'no usable document'}")
        if not searched:
            searched = ["no route could be built for this citation (no URL, unknown citation form)"]
        day = today or date.today().isoformat()
        net = sum(1 for a in attempts if a.get("status") is not None and not a.get("from_cache"))
        cached = sum(1 for a in attempts if a.get("from_cache"))
        official = sum(1 for a in attempts if a.get("tier") in ("given", "alternate", "official"))
        weak = "" if official else (" WEAK: no official online route is known for this citation "
                                    "(e.g. an order older than the 1936 Federal Register), so only "
                                    "mirrors were tried.")
        note = (f"[{wanted.wanted_id}] Automatic ladder found no usable copy of "
                f"{wanted.citation or wanted.wanted_id}: {len(attempts)} route(s) tried, {net} answered over the "
                f"network in this run and {cached} from the download cache, every one ending definitively "
                f"(not found, error page, robots.txt or wrong content).{weak} PROPOSED only: "
                "a human should still try a general web search, NARA, LoC and presidential libraries "
                "before accepting this as exhausted.")
        return [{"instrument_id": i, "step": wanted.step, "searched": searched,
                 "recorded_by": recorded_by, "recorded_on": day, "note": note}
                for i in wanted.instrument_ids]
