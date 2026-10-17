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
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from collections import deque
from datetime import date, datetime, timezone
from pathlib import Path

# The contact part can be set by the owner (e.g. a public URL) with EO_USER_AGENT_CONTACT;
# no personal address is put here by default.
USER_AGENT = ("EO-afterlife-research/1.0 (owner-run research; "
              + (os.environ.get("EO_USER_AGENT_CONTACT") or "contact via repo") + ")")
LEGAL_CUTOFF = "2026-10-14"
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
    kind: str = "document"   # document | cdx | fr_api
    tier: str = "given"      # given | alternate | wayback_given | official | wayback_official | mirror
    page_hint: int | None = None


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
    m = re.fullmatch(r"(\d{1,2})\s*C\.?\s*F\.?\s*R\.?\s*(?:Part\s*)?(\d+)(?:\.(\w+))?", text, re.I)
    if m:
        return "CFR", {"title": int(m.group(1)), "part": int(m.group(2)), "section": m.group(3) or ""}
    return None, {}


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
        routes.append(Route("govinfo_link_uscode", f"https://www.govinfo.gov/link/uscode/{t}/{s}", "pdf", tier="official"))
        routes.append(Route("uscode_house_gov", f"https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title{t}-section{s}&num=0&edition=prelim", "html", tier="official"))
    elif kind == "CFR":
        t, part, sec = p["title"], p["part"], p["section"]
        q = {"link-type": "pdf", "year": "mostrecent"}
        if sec:
            q["sectionnum"] = sec
        routes.append(Route("govinfo_link_cfr", f"https://www.govinfo.gov/link/cfr/{t}/{part}?" + urllib.parse.urlencode(q), "pdf", tier="official"))
        target = f"section-{part}.{sec}" if sec else f"part-{part}"
        # eCFR point-in-time view on the legal cutoff date (eCFR history starts in 2017).
        routes.append(Route("ecfr_on_cutoff", f"https://www.ecfr.gov/on/{LEGAL_CUTOFF}/title-{t}/{target}", "html", tier="official"))
    return routes, kind, p


def mirror_routes(wanted: Wanted, kind, p):
    routes = [Route("mirror_hint", u, guess_expect(u), tier="mirror") for u in wanted.mirror_urls]
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
            if "/link/" in r.url or "/api/" in r.url:
                continue
            out.append(Route("wayback_cdx", cdx_url(r.url), "json", kind="cdx", tier=tier))
        return out

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


class Fetcher:
    """Polite HTTP client: robots.txt, per-host spacing, retries, disk cache."""

    def __init__(self, cache_dir, transport=None, sleep=time.sleep, clock=time.monotonic,
                 max_retries=3, timeout=120, max_bytes=1_500_000_000, max_requests=None,
                 offline=False, user_agent=USER_AGENT, log=print):
        self.cache_dir = Path(cache_dir)
        self.http_dir = self.cache_dir / "http"
        self.http_dir.mkdir(parents=True, exist_ok=True)
        self.transport = transport or urllib_transport
        self.sleep, self.clock = sleep, clock
        self.max_retries, self.timeout, self.max_bytes = max_retries, timeout, max_bytes
        self.max_requests, self.offline = max_requests, offline
        self.user_agent, self.log = user_agent, log
        self.requests = 0
        self.bytes_downloaded = 0
        self._last = {}
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
            return m
        return None

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
        hit = self.cached(url)
        if hit:
            att.update({k: hit.get(k) for k in ("final_url", "status", "bytes", "sha256", "content_type", "page_hint", "redirects") if k in hit})
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
                        att.update({k: hit.get(k) for k in ("bytes", "sha256", "content_type") if k in hit})
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
        reason = reject_reason(head, total, att["content_type"], att["final_url"], expect)
        if reason:
            tmp.unlink(missing_ok=True)
            att["reject_reason"] = reason
            att["error"] = "rejected_" + reason
            return att
        blob = self.blob_path(att["sha256"], att["content_type"] if head.lstrip()[:5] != b"%PDF-" else "pdf")
        blob.parent.mkdir(parents=True, exist_ok=True)
        os.replace(tmp, blob)
        meta = {k: att[k] for k in ("url", "final_url", "status", "bytes", "sha256", "content_type", "page_hint", "redirects")}
        meta["retrieved_utc"] = att["time_utc"]
        meta["blob"] = self.rel_cache(blob)
        mp = self.meta_path(att["url"])
        mp.parent.mkdir(parents=True, exist_ok=True)
        write_text_lf(mp, json.dumps(meta, indent=1))
        att["accepted"] = True
        att["path"] = str(blob)
        return att


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


def extract_text(path, content_type="", expect="any", page_hint=None, max_pages=40):
    """Plain text of a saved document and the page range used (for PDFs)."""
    with open(path, "rb") as fh:
        head = fh.read(8)
    if head.lstrip()[:5] == b"%PDF-":
        reader_n = len(pdf_reader(path).pages)
        if reader_n <= max_pages or not page_hint:
            first, last = 1, min(reader_n, max_pages)
        else:
            first, last = max(1, page_hint - 2), min(reader_n, page_hint + 5)
        n, pages = pdf_pages_text(path, first, last)
        text = "\n".join(f"=== PDF page {p} of {n} ===\n{t}" for p, t in pages)
        return text, {"pdf_pages_total": n, "pdf_first": first, "pdf_last": last}
    raw = Path(path).read_bytes().decode("utf-8", "replace")
    ctype = (content_type or "").lower()
    if "json" in ctype or expect == "json":
        return None, {}
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
    if "/on/" + LEGAL_CUTOFF in final_url:
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


def default_extract(wanted, route, att, fetcher):
    """Default content step: extract text; accept any real document."""
    if not att.get("path"):
        return {"ok": True, "text": None, "page_or_item": wanted.citation or route.url, "notes": "body not kept in cache"}
    text, info = extract_text(att["path"], att.get("content_type", ""), route.expect, att.get("page_hint"))
    if not info.get("pdf_pages_total") and (text is None or len(text.strip()) < 200):
        return {"ok": False, "reason": "no meaningful text in this page (landing, script or error page?)"}
    page = wanted.citation or ""
    name = urllib.parse.urlsplit(att["final_url"]).path.rsplit("/", 1)[-1]
    if info.get("pdf_pages_total"):
        page = f"{page}; {name} PDF pages {info['pdf_first']}-{info['pdf_last']} of {info['pdf_pages_total']}".strip("; ")
        if att.get("page_hint"):
            page += f" (govinfo link-service page hint {att['page_hint']})"
    elif not page:
        page = name
    notes = ""
    kind, p = parse_citation(wanted.citation)
    if kind in ("USC", "CFR"):
        notes = edition_note(kind, att["final_url"], att.get("time_utc", ""))
    if kind == "STAT" and text is not None and att.get("page_hint"):
        hint_text = ""
        m = re.search(rf"=== PDF page {att['page_hint']} of \d+ ===\n(.*?)(?:\n=== PDF page|\Z)", text, re.S)
        if m:
            hint_text = m.group(1)
        notes = ("printed page number %s %s on the hinted PDF page" %
                 (p["page"], "seen" if re.search(rf"\b{p['page']}\b", hint_text) else "NOT seen"))
    return {"ok": True, "text": text, "page_or_item": page, "notes": notes}


# --------------------------------------------------------------------------
# Was a failure definitive (the document is not there) or transient (try again)?
# --------------------------------------------------------------------------

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
        return "definitive"
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


def classify_failure(attempts, offline=False):
    """(outcome, why) for a walk that found nothing.

    outcome is 'exhausted' only when at least one route really answered and
    every route ended definitively; 'retry_later' when anything was transient
    or the run was offline; 'no_route' when no route could be built.
    """
    if not attempts:
        return "no_route", "no route could be built for this citation (no URL, unknown citation form)"
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
            if r.kind == "fr_api":
                new = self._from_fr_api(att)
                att["note"] = f"{len(new)} document links in API record"
                queue.extendleft(reversed(new))
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
        outcome, why = classify_failure(attempts, offline=getattr(self.fetcher, "offline", False))
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
