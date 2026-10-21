"""Open-ended web search for executive orders, shared by Lewis and Clark.

Design rules, in the order they matter:

1. No fixed list of sources. Engines come from ENGINES below plus `search_engines.json` next to this
   file, which the owner can extend with any search page or API: a URL template with `{q}` and
   optional `{year}`, how to read the results (generic HTML links, an RSS feed, or a JSON path), and
   any environment variables it needs. Every engine that can answer is tried for every query.
2. Nothing is ever given up on by the machine. A target keeps a state record (which query
   strategies and engines have been tried, what was found, which pages still wait to be read) that
   is carried forward from the last committed output, so each daily run advances every open target
   one more step. Only a person records exhaustion, in research/readiness/EXHAUSTED.jsonl.
3. Hits are followed, not just listed. A promising page is fetched, read for the order's own text
   (number, date, operative wording) and for links to documents or further pages; those go on the
   target's frontier for the next step. Any page read is also harvested for every executive-order
   number it names, which is how orders nobody recorded surface.
4. The fetcher is the project's FetchPool: HTTPS only, robots.txt obeyed, per-host throttling,
   byte bounds, every response cached and hashed. An engine blocked by robots is reported by name
   and tried again next run; a key the owner has not supplied is reported as `needs_key`.
5. Nothing here changes a count, a census entry, a custody grade or a legal status. A hit is a
   lead with a URL, a quote and a score, for a person to read.
"""
from __future__ import annotations

import base64
import datetime as dt
import html as htmllib
import json
import os
import re
import sys
import threading
import time
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import eo_identity as ident  # noqa: E402
import fetch_pool  # noqa: E402

ENGINES_FILE = os.path.join(HERE, "search_engines.json")
MAX_PAGE_BYTES = 6_000_000
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]

# Built-in engines. `kind`: how to read the response. `url`: template with {q} (URL-encoded query) and
# optional {year}. `env`: environment variables that must be set; `headers` may reference them as
# {ENV:NAME}. `host_only`: result links on the engine's own host are ignored unless listed here.
ENGINES = [
    # General web search, keyless. robots.txt decides at run time; blocked ones are reported.
    {"name": "duckduckgo_html", "kind": "html", "url": "https://html.duckduckgo.com/html/?q={q}", "unwrap": "uddg"},
    {"name": "duckduckgo_lite", "kind": "html", "url": "https://lite.duckduckgo.com/lite/?q={q}", "unwrap": "uddg"},
    {"name": "bing_rss", "kind": "rss", "url": "https://www.bing.com/search?q={q}&format=rss"},
    {"name": "mojeek_html", "kind": "html", "url": "https://www.mojeek.com/search?q={q}"},
    {"name": "brave_html", "kind": "html", "url": "https://search.brave.com/search?q={q}&source=web"},
    {"name": "marginalia", "kind": "html", "url": "https://search.marginalia.nu/search?query={q}"},
    {"name": "yandex_html", "kind": "html", "url": "https://yandex.com/search/?text={q}"},
    # General web search, keyed (secrets passed by the workflow when the owner adds them).
    {"name": "google_cse", "kind": "json", "env": ["GOOGLE_CSE_KEY", "GOOGLE_CSE_CX"],
     "url": "https://www.googleapis.com/customsearch/v1?key={ENV:GOOGLE_CSE_KEY}&cx={ENV:GOOGLE_CSE_CX}&q={q}&num=10",
     "json": {"items": "items", "title": "title", "url": "link", "snippet": "snippet"}},
    {"name": "bing_api", "kind": "json", "env": ["BING_SEARCH_KEY"], "headers": {"Ocp-Apim-Subscription-Key": "{ENV:BING_SEARCH_KEY}"},
     "url": "https://api.bing.microsoft.com/v7.0/search?q={q}&count=10",
     "json": {"items": "webPages.value", "title": "name", "url": "url", "snippet": "snippet"}},
    {"name": "brave_api", "kind": "json", "env": ["BRAVE_SEARCH_KEY"], "headers": {"X-Subscription-Token": "{ENV:BRAVE_SEARCH_KEY}", "Accept": "application/json"},
     "url": "https://api.search.brave.com/res/v1/web/search?q={q}&count=10",
     "json": {"items": "web.results", "title": "title", "url": "url", "snippet": "description"}},
    {"name": "serpapi_google", "kind": "json", "env": ["SERPAPI_KEY"],
     "url": "https://serpapi.com/search.json?engine=google&q={q}&api_key={ENV:SERPAPI_KEY}",
     "json": {"items": "organic_results", "title": "title", "url": "link", "snippet": "snippet"}},
    # Libraries, archives and government catalogs, keyless.
    {"name": "loc_newspapers", "kind": "json", "url": "https://www.loc.gov/collections/chronicling-america/?q={q}&fo=json&c=10{loc_dates}",
     "json": {"items": "results", "title": "title", "url": "id", "snippet": "description", "date": "date"}},
    {"name": "loc_books", "kind": "json", "url": "https://www.loc.gov/books/?q={q}&fo=json&c=10",
     "json": {"items": "results", "title": "title", "url": "id", "snippet": "description", "date": "date"}},
    {"name": "loc_manuscripts", "kind": "json", "url": "https://www.loc.gov/manuscripts/?q={q}&fo=json&c=10",
     "json": {"items": "results", "title": "title", "url": "id", "snippet": "description", "date": "date"}},
    {"name": "internet_archive", "kind": "json",
     "url": "https://archive.org/advancedsearch.php?q={q}&fl%5B%5D=identifier&fl%5B%5D=title&fl%5B%5D=date&fl%5B%5D=description&rows=10&output=json",
     "json": {"items": "response.docs", "title": "title", "url": "identifier", "snippet": "description", "date": "date"},
     "url_prefix": "https://archive.org/details/"},
    {"name": "google_books", "kind": "json", "url": "https://www.googleapis.com/books/v1/volumes?q={q}&maxResults=10",
     "json": {"items": "items", "title": "volumeInfo.title", "url": "volumeInfo.infoLink", "snippet": "searchInfo.textSnippet",
              "date": "volumeInfo.publishedDate"}},
    {"name": "hathitrust_catalog", "kind": "html", "url": "https://catalog.hathitrust.org/Search/Home?lookfor={q}&type=all",
     "host_only": ["catalog.hathitrust.org", "babel.hathitrust.org", "hdl.handle.net"]},
    {"name": "federal_register_api", "kind": "json",
     "url": "https://www.federalregister.gov/api/v1/documents.json?conditions%5Bterm%5D={q}&per_page=10&order=oldest",
     "json": {"items": "results", "title": "title", "url": "html_url", "snippet": "abstract", "date": "publication_date"}},
    {"name": "wikisource_search", "kind": "html", "url": "https://en.wikisource.org/w/index.php?search={q}&ns0=1&fulltext=1",
     "host_only": ["en.wikisource.org"]},
    {"name": "wikipedia_search", "kind": "html", "url": "https://en.wikipedia.org/w/index.php?search={q}&ns0=1&fulltext=1",
     "host_only": ["en.wikipedia.org"]},
    {"name": "presidency_project", "kind": "html", "url": "https://www.presidency.ucsb.edu/advanced-search?field-keywords={q}&items_per_page=25",
     "host_only": ["www.presidency.ucsb.edu"]},
    {"name": "govinfo_search_page", "kind": "html", "url": "https://www.govinfo.gov/app/search/%7B%22query%22%3A%22{q}%22%2C%22offset%22%3A0%7D",
     "host_only": ["www.govinfo.gov"]},
    # Keyed government catalogs.
    {"name": "nara_catalog", "kind": "json", "env": ["NARA_API_KEY"], "headers": {"x-api-key": "{ENV:NARA_API_KEY}"},
     "url": "https://catalog.archives.gov/api/v2/records/search?q={q}&limit=10",
     "json": {"items": "body.hits.hits", "title": "_source.record.title", "url": "_source.metadata.naId", "snippet": "_source.record.scopeAndContentNote"},
     "url_prefix": "https://catalog.archives.gov/id/"},
]


def load_engines(path=ENGINES_FILE):
    """Built-ins plus the owner's additions from search_engines.json (same fields; name wins on clash)."""
    engines = {e["name"]: dict(e) for e in ENGINES}
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as fh:
                extra = json.load(fh)
            for e in extra if isinstance(extra, list) else extra.get("engines", []):
                if isinstance(e, dict) and e.get("name") and e.get("url"):
                    engines[e["name"]] = {**engines.get(e["name"], {}), **e}
        except (OSError, ValueError):
            pass
    return list(engines.values())


def engine_ready(engine, env=None):
    """'' when usable; 'needs_key' when an environment variable it needs is unset; 'disabled' when told so."""
    env = os.environ if env is None else env
    if engine.get("disabled"):
        return "disabled"
    for name in engine.get("env", []):
        if not env.get(name):
            return "needs_key"
    return ""


def build_url(engine, query, year=None, env=None):
    env = os.environ if env is None else env
    q = urllib.parse.quote(query, safe="")
    url = engine["url"]
    for m in re.findall(r"\{ENV:([A-Z0-9_]+)\}", url):
        url = url.replace("{ENV:" + m + "}", urllib.parse.quote(env.get(m, ""), safe=""))
    loc_dates = f"&dates={year}/{year}" if year and "{loc_dates}" in url else ""
    url = url.replace("{loc_dates}", loc_dates).replace("{year}", str(year or "")).replace("{q}", q)
    return url


def build_headers(engine, env=None):
    env = os.environ if env is None else env
    out = {}
    for k, v in (engine.get("headers") or {}).items():
        for m in re.findall(r"\{ENV:([A-Z0-9_]+)\}", v):
            v = v.replace("{ENV:" + m + "}", env.get(m, ""))
        out[k] = v
    return out


# --- reading results ------------------------------------------------------------------------------

def _get(obj, path):
    for part in path.split("."):
        if isinstance(obj, dict):
            obj = obj.get(part)
        elif isinstance(obj, list) and part.isdigit():
            obj = obj[int(part)] if int(part) < len(obj) else None
        else:
            return None
    return obj


def _text(v):
    if v is None:
        return ""
    if isinstance(v, list):
        return " ".join(_text(x) for x in v[:3])
    if isinstance(v, dict):
        return " ".join(_text(x) for x in list(v.values())[:3])
    return str(v)


def parse_json_results(engine, body):
    try:
        data = json.loads(body.decode("utf-8", "replace"))
    except ValueError:
        return [], "not_json"
    spec = engine.get("json") or {}
    items = _get(data, spec.get("items", "items")) or []
    if not isinstance(items, list):
        return [], "items_not_a_list"
    hits = []
    for it in items:
        if not isinstance(it, dict):
            continue
        url = _text(_get(it, spec.get("url", "url"))).strip()
        if url and not url.startswith("http"):
            url = engine.get("url_prefix", "") + url
        if not url.startswith("http"):
            continue
        hits.append({"title": clean_text(_text(_get(it, spec.get("title", "title")))),
                     "url": url, "snippet": clean_text(_text(_get(it, spec.get("snippet", "snippet"))))[:600],
                     "date": _text(_get(it, spec["date"])) if spec.get("date") else ""})
    return hits, ""


_TAG = re.compile(r"<[^>]+>")
_A = re.compile(r"<a\s[^>]*?href\s*=\s*[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", re.I | re.S)
_ITEM = re.compile(r"<item>(.*?)</item>", re.S)


def clean_text(s):
    s = htmllib.unescape(_TAG.sub(" ", s or ""))
    return re.sub(r"\s+", " ", s).strip()


def unwrap_redirect(href):
    """Search engines wrap result links: DuckDuckGo (uddg=), Bing (u=a1<base64>), Google (/url?q=)."""
    p = urllib.parse.urlsplit(href)
    qs = urllib.parse.parse_qs(p.query)
    if "uddg" in qs:
        return qs["uddg"][0]
    if p.path.startswith("/url") and "q" in qs:
        return qs["q"][0]
    if p.path.startswith("/ck/a") and "u" in qs and qs["u"][0].startswith("a1"):
        raw = qs["u"][0][2:]
        try:
            return base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)).decode("utf-8", "replace")
        except Exception:
            return href
    return href


def parse_html_results(engine, body, base_url):
    html = body.decode("utf-8", "replace")
    engine_host = urllib.parse.urlsplit(base_url).hostname or ""
    keep_hosts = set(engine.get("host_only") or [])
    hits, seen = [], set()
    for m in _A.finditer(html):
        href = htmllib.unescape(m.group(1).strip())
        if href.startswith(("#", "javascript:", "mailto:")):
            continue
        href = urllib.parse.urljoin(base_url, href)
        href = unwrap_redirect(href)
        host = urllib.parse.urlsplit(href).hostname or ""
        if not href.startswith("http") or not host:
            continue
        if keep_hosts:
            if host not in keep_hosts:
                continue
            # on a site's own search page, skip its navigation
            if re.search(r"(Special:|/w/index\.php\?|/login|/search\?|/advanced-search|\?page=|/app/search)", href):
                continue
        elif host == engine_host or host.endswith("." + engine_host.split(".", 1)[-1]) and "duckduckgo" in host:
            continue
        elif host.endswith(("bing.com", "microsoft.com", "mojeek.com", "brave.com", "marginalia.nu", "yandex.com", "yandex.ru", "duckduckgo.com")):
            continue
        text = clean_text(m.group(2))
        if not text or len(text) < 3 or href in seen:
            continue
        seen.add(href)
        after = clean_text(html[m.end(): m.end() + 1500])
        hits.append({"title": text[:200], "url": href, "snippet": after[:400], "date": ""})
    return hits, ""


def parse_rss_results(engine, body):
    xml = body.decode("utf-8", "replace")
    hits = []
    for m in _ITEM.finditer(xml):
        chunk = m.group(1)
        t = re.search(r"<title>(.*?)</title>", chunk, re.S)
        l = re.search(r"<link>(.*?)</link>", chunk, re.S)
        d = re.search(r"<description>(.*?)</description>", chunk, re.S)
        if l:
            hits.append({"title": clean_text(t.group(1)) if t else "", "url": clean_text(l.group(1)),
                         "snippet": clean_text(d.group(1))[:600] if d else "", "date": ""})
    return hits, ("" if hits or "<rss" in xml or "<feed" in xml else "not_rss")


# --- query strategies ------------------------------------------------------------------------------

def long_date(iso):
    d = ident.parse_date(iso) if iso and len(iso) >= 10 else None
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}" if d else ""


def title_core(title):
    """Six distinctive words of a title, without the number and boilerplate."""
    t = re.sub(r"^.*?—", "", title or "")
    t = re.sub(r"(?i)executive order( no\.?)? ?\d+[A-Za-z½]*", "", t)
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z'-]+", t)
             if w.lower() not in {"the", "of", "and", "for", "to", "in", "a", "an", "by", "on", "with", "as", "at",
                                  "from", "relating", "concerning", "regarding", "amending", "amendment", "certain",
                                  "order", "orders", "executive", "no", "providing", "prescribing", "establishing"}]
    return " ".join(words[:6])


def query_strategies(target):
    """Escalating queries for one target: {'id','number','suffix','date','title','president','kind'}.

    Each strategy is (label, query, year). Later ones are broader. A person adds a strategy by adding a
    line here; the state file remembers which index each target has reached, so a new line is tried
    on the next run for every target.
    """
    n, sfx = target["number"], target.get("suffix") or ""
    shown = f"{n}{('-' + sfx) if sfx and sfx != '½' else (' 1/2' if sfx == '½' else '')}"
    date = target.get("date") or ""
    year = date[:4] if date[:4].isdigit() else None
    ld = long_date(date)
    core = title_core(target.get("title") or "")
    pres = target.get("president") or ""
    out = [("number_phrase", f'"Executive Order No. {shown}"', year),
           ("number_bare", f'"Executive Order {shown}"', year)]
    if ld:
        out.append(("number_and_date", f'"Executive Order" {shown} "{ld}"', year))
        out.append(("date_phrase", f'"Executive order of {ld}"', year))
    if core:
        out.append(("title_words", f'"Executive Order" {shown} {core}', year))
        out.append(("title_only", f'executive order {core} {year or ""}'.strip(), year))
    out.append(("eo_abbrev", f'"E.O. {shown}"', year))
    if pres:
        out.append(("president_number", f'{pres} "Executive Order" {shown}', year))
    if sfx and sfx != "½":
        out.append(("suffix_attached", f'"Executive Order {n}{sfx}"', year))
        out.append(("suffix_spaced", f'"Executive Order {n} {sfx}"', year))
    if year:
        out.append(("year_only", f'"Executive Order No. {shown}" {year}', None))
    out.append(("pdf_only", f'"Executive Order No. {shown}" filetype:pdf', year))
    return out


# --- scoring and page reading ----------------------------------------------------------------------

# Editorial or volunteer transcriptions the project already harvests (app-executive-orders, wikisource-texts).
TRANSCRIPTION_HOSTS = ("presidency.ucsb.edu", "wikisource.org", "wikipedia.org")
ORDER_MARKERS = re.compile(r"(?i)(by virtue of the authority|it is hereby ordered|is hereby (revoked|amended)|the white house|"
                           r"executive order|hereby ordered|be it ordered|signed by the president)")
LINK_DOC = re.compile(r"(?i)\.(pdf|djvu|txt|xml)(\?|$)|/download/|/content/pkg/|/details/|docview|/item/|babel\.hathitrust|/resource/")


def number_regex(number, suffix=""):
    s = re.escape(str(number))
    tail = ""
    if suffix == "½":
        tail = r"\s?(?:½|1/2)"
    elif suffix:
        tail = r"\s?-?\s?" + re.escape(suffix)
    return re.compile(r"(?i)(executive\s+order|e\.\s?o\.|\bEO)\s*(?:no\.?|number|№)?\s*" + s + tail + r"(?![\d])")


def score_hit(hit, target, page_text=None):
    """0-100: does this hit look like the order itself or a document that prints it?"""
    text = " ".join([hit.get("title", ""), hit.get("snippet", ""), hit.get("url", "")])
    if page_text:
        text += " " + page_text[:200_000]
    score, why = 0, []
    if number_regex(target["number"], target.get("suffix", "")).search(text):
        score += 40
        why.append("number_named")
    elif re.search(r"(?<!\d)" + re.escape(str(target["number"])) + r"(?!\d)", text):
        score += 10
        why.append("number_present")
    ld = long_date(target.get("date", ""))
    if ld and ld.lower() in text.lower():
        score += 25
        why.append("date_named")
    elif target.get("date", "")[:4] and target["date"][:4] in text:
        score += 5
        why.append("year_present")
    core = title_core(target.get("title", "")).lower().split()
    if core:
        found = sum(1 for w in core if w in text.lower())
        if found >= max(2, len(core) // 2):
            score += 15
            why.append("title_words")
    if page_text and ORDER_MARKERS.search(page_text):
        score += 10
        why.append("order_wording")
    if LINK_DOC.search(hit.get("url", "")):
        score += 5
        why.append("document_url")
    host = urllib.parse.urlsplit(hit.get("url", "")).hostname or ""
    if any(h in host for h in ("govinfo.gov", "archives.gov", "loc.gov", "hathitrust.org", "archive.org", "federalregister.gov", "congress.gov")):
        score += 5
        why.append("official_or_library_host")
    if target.get("wants") == "original" and any(h in host for h in TRANSCRIPTION_HOSTS):
        score = min(score, 35)  # a transcription the project already has: a lead to cite, never the original Lewis wants
        why.append("transcription_host_already_held")
    return min(score, 100), "|".join(why)


def page_to_text(body, content_type=""):
    """Plain text from HTML or PDF bytes (PDF needs pypdf; otherwise '')."""
    head = body[:5]
    if head == b"%PDF-":
        try:
            import io
            import pypdf
            r = pypdf.PdfReader(io.BytesIO(body))
            return "\n".join((p.extract_text() or "") for p in r.pages[:60])
        except Exception:
            return ""
    html = body.decode("utf-8", "replace")
    html = re.sub(r"(?is)<(script|style|nav|footer|header)[^>]*>.*?</\1>", " ", html)
    return clean_text(html)


def page_links(body, base_url, limit=40):
    """Outbound links from a page that look like documents or further pages about orders."""
    html = body.decode("utf-8", "replace")
    out, seen = [], set()
    for m in _A.finditer(html):
        href = urllib.parse.urljoin(base_url, htmllib.unescape(m.group(1).strip()))
        text = clean_text(m.group(2))
        if not href.startswith("https") or href in seen or href.split("#")[0] == base_url.split("#")[0]:
            continue
        if LINK_DOC.search(href) or re.search(r"(?i)executive\s+order", text):
            seen.add(href)
            out.append({"url": href, "text": text[:160]})
            if len(out) >= limit:
                break
    return out


# --- the searcher -------------------------------------------------------------------------------

class Searcher:
    """Runs queries across every ready engine and reads pages, within a request budget.

    `transport` is injected for tests. Every HTTP exchange is appended to `sources` (url, status,
    sha256, bytes, time) so a hit can be traced to the exact response that produced it.
    """

    def __init__(self, cache_dir, max_requests=300, transport=None, env=None, engines=None, offline=False, now=None):
        self.pool = fetch_pool.FetchPool(cache_dir, workers=4, per_host=2, transport=transport, min_interval=1.0,
                                         offline=offline, max_bytes=MAX_PAGE_BYTES,
                                         user_agent="EO-Road-System/1.0 (+https://github.com/D3m0sthene5/Executive-Orders; research)")
        self.max_requests = max_requests
        self.env = os.environ if env is None else env
        self.engines = engines if engines is not None else load_engines()
        self.sources = []
        self.engine_status = {}
        self._lock = threading.Lock()
        self.reserved = 0  # fetches started; robots.txt reads are extra (one per host) and not counted here
        self.now = now or (lambda: dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))

    @property
    def requests_used(self):
        return self.pool.requests

    def budget_left(self):
        return self.reserved < self.max_requests

    def _reserve(self):
        """Atomically take one unit of budget; False when none is left (parallel callers cannot overrun)."""
        with self._lock:
            if self.reserved >= self.max_requests:
                return False
            self.reserved += 1
            return True

    def ready_engines(self):
        out = []
        for e in self.engines:
            why = engine_ready(e, self.env)
            if why:
                self.engine_status.setdefault(e["name"], why)
            else:
                out.append(e)
        return out

    def _record(self, url, status, body, kind, error="", engine=""):
        rec = {"url": url, "status": status, "sha256": fetch_pool.sha(body) if body else "", "bytes": len(body or b""),
               "retrieved_utc": self.now(), "kind": kind, "engine": engine, "error": error}
        self.sources.append(rec)
        return rec

    def _fetch(self, url, headers=None):
        """status, body, error. Redirects are followed to 7 hops; robots and budget are enforced."""
        if not self._reserve():
            return 0, b"", "budget_exhausted"
        current = url
        try:
            for _ in range(7):
                status, hs, stream = self.pool.request(current, headers=headers)
                if status in (301, 302, 303, 307, 308):
                    stream.close()
                    current = urllib.parse.urljoin(current, hs.get("location", ""))
                    continue
                try:
                    body = stream.read(MAX_PAGE_BYTES + 1)
                finally:
                    stream.close()
                return status, body[:MAX_PAGE_BYTES], ""
            return 0, b"", "redirect_limit"
        except fetch_pool.FetchError as exc:
            return 0, b"", str(exc)
        except Exception as exc:  # network errors are retryable facts, never findings
            return 0, b"", type(exc).__name__ + ": " + str(exc)[:120]

    SKIP_FOR_RUN = ("blocked_by_robots_txt", "http_401", "http_403", "http_429", "timeout", "unreachable")

    def search(self, engine, query, year=None):
        """One query on one engine -> {'engine','query','url','status','hits','error'}.

        An engine that this run has already found blocked, rate-limited or unreachable is skipped for the
        rest of the run without a request (it is tried again next run), so dead engines cost nothing."""
        url = build_url(engine, query, year, self.env)
        prior = self.engine_status.get(engine["name"], "")
        if prior in self.SKIP_FOR_RUN:
            return {"engine": engine["name"], "query": query, "url": url, "status": 0, "hits": [], "error": "skipped_this_run:" + prior}
        status, body, error = self._fetch(url, build_headers(engine, self.env))
        hits, perr = [], ""
        if status == 200 and body:
            kind = engine.get("kind", "html")
            if kind == "json":
                hits, perr = parse_json_results(engine, body)
            elif kind == "rss":
                hits, perr = parse_rss_results(engine, body)
            else:
                hits, perr = parse_html_results(engine, body, url)
        elif status and not error:
            error = f"HTTP {status}"
        self._record(url, status, body, "search", error or perr, engine["name"])
        name = engine["name"]
        if error == "blocked_by_robots_txt":
            self.engine_status[name] = "blocked_by_robots_txt"
        elif error.startswith("HTTP 4") and status in (401, 403, 429):
            self.engine_status[name] = f"http_{status}"
        elif "timed out" in error or "timeout" in error.lower():
            self.engine_status[name] = "timeout"
        elif error.startswith(("URLError", "ConnectionResetError", "OSError", "ConnectionRefusedError")) or "robots unavailable" in error:
            self.engine_status[name] = "unreachable"
        elif error == "budget_exhausted":
            pass
        elif not error and not perr:
            self.engine_status[name] = "ok"
        elif perr:
            self.engine_status.setdefault(name, "unreadable:" + perr)
        else:
            self.engine_status.setdefault(name, "error")
        return {"engine": name, "query": query, "url": url, "status": status, "hits": hits, "error": error or perr}

    def read_page(self, url):
        """Fetch a hit and return (text, links, record)."""
        status, body, error = self._fetch(url)
        rec = self._record(url, status, body, "page", error)
        if status != 200 or not body:
            return "", [], rec
        return page_to_text(body), page_links(body, url), rec


# --- target state ----------------------------------------------------------------------------------

def new_state(target):
    return {"id": target["id"], "strategy_index": 0, "steps": 0, "engines_tried": {}, "hits": [], "frontier": [],
            "read": [], "best_score": 0, "best_url": "", "last_run": "", "first_run": "", "notes": []}


def advance(searcher, target, state, engines, max_pages=3, min_follow_score=45):
    """One step for one target: the next query strategy on every ready engine, then read the best unread hits."""
    strategies = query_strategies(target)
    if not strategies:
        return state
    idx = state["strategy_index"] % len(strategies)
    label, query, year = strategies[idx]
    stamp = searcher.now()
    state["first_run"] = state["first_run"] or stamp
    known = {h["url"] for h in state["hits"]}
    if not searcher.budget_left():
        state["notes"].append(f"{stamp} budget exhausted before {label}")
        return state
    # every engine is a different host, so the queries run in parallel under the pool's per-host limits
    results = searcher.pool.map(lambda e: searcher.search(e, query, year), engines)
    for engine, res in zip(engines, results):
        if res["error"] == "budget_exhausted":
            state["notes"].append(f"{stamp} budget stopped before {engine['name']} on {label}")
            continue
        state["engines_tried"][engine["name"]] = state["engines_tried"].get(engine["name"], 0) + 1
        for h in res["hits"]:
            if h["url"] in known:
                continue
            known.add(h["url"])
            sc, why = score_hit(h, target)
            state["hits"].append({**h, "engine": engine["name"], "strategy": label, "query": query, "score": sc, "why": why,
                                  "found_utc": stamp, "page_score": None})
            if sc >= min_follow_score and h["url"] not in state["read"]:
                state["frontier"].append(h["url"])
    # read the most promising unread pages
    order = sorted(state["hits"], key=lambda h: -h["score"])
    for h in order:
        if max_pages <= 0 or not searcher.budget_left():
            break
        if h["url"] in state["read"] or h["score"] < min_follow_score:
            continue
        text, links, rec = searcher.read_page(h["url"])
        state["read"].append(h["url"])
        max_pages -= 1
        if not text:
            h["page_score"] = -1
            h["page_error"] = rec.get("error", "")
            continue
        sc, why = score_hit(h, target, text)
        h["page_score"], h["page_why"], h["page_sha256"] = sc, why, rec["sha256"]
        m = number_regex(target["number"], target.get("suffix", "")).search(text)
        if m:
            h["page_quote"] = ident.sentence_around(text, m.start(), m.end())[:400]
        h["page_numbers_named"] = sorted({ident.canon_id(x["number"], x["suffix"]) for x in ident.find_mentions(text)})[:200]
        for link in links[:15]:
            if link["url"] not in known and link["url"] not in state["read"]:
                known.add(link["url"])
                lsc, lwhy = score_hit({"title": link["text"], "url": link["url"], "snippet": ""}, target)
                state["hits"].append({"title": link["text"], "url": link["url"], "snippet": "", "date": "", "engine": "followed_link",
                                      "strategy": label, "query": h["url"], "score": lsc, "why": lwhy, "found_utc": stamp, "page_score": None})
    best = max(state["hits"], key=lambda h: (h.get("page_score") or 0, h["score"]), default=None)
    if best:
        state["best_score"] = max(best.get("page_score") or 0, best["score"])
        state["best_url"] = best["url"]
    state["frontier"] = [u for u in state["frontier"] if u not in state["read"]][:50]
    state["strategy_index"] = idx + 1
    state["steps"] += 1
    state["last_run"] = stamp
    return state


def rescore_state(state, target):
    """Apply the current scoring rules to hits carried forward from earlier runs (rules change; evidence stays)."""
    if not target:
        return state
    for h in state.get("hits", []):
        sc, why = score_hit(h, target)
        h["score"], h["why"] = sc, why
        if h.get("page_score") not in (None, -1) and "transcription_host_already_held" in why:
            h["page_score"] = min(h["page_score"], 35)
            if "transcription_host_already_held" not in (h.get("page_why") or ""):
                h["page_why"] = ((h.get("page_why") or "") + "|transcription_host_already_held").strip("|")
    best = max(state.get("hits", []), key=lambda h: (h.get("page_score") or 0, h["score"]), default=None)
    if best:
        state["best_score"] = max(best.get("page_score") or 0, best["score"])
        state["best_url"] = best["url"]
    return state


def pick_targets(states, targets, limit):
    """Round-robin: targets never searched first, then the fewest steps, then the oldest last run."""
    def key(t):
        s = states.get(t["id"])
        pr = t.get("priority", 5)
        return (0, pr, "", t["id"]) if s is None else (1 + s["steps"], pr, s["last_run"], t["id"])
    return sorted(targets, key=key)[:limit]


# --- a campaign: many targets, one run, state carried forward -------------------------------------

def load_prior_extra(root, job, key):
    """One extra top-level key of the last committed WEB_STATE.json (e.g. the list-page cursor)."""
    for getter in (_prior_state_git, _prior_state_folder):
        data = getter(root, job)
        if isinstance(data, dict) and key in data:
            return data[key]
    return None


def _prior_state_git(root, job):
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(HERE), "source-ladder"))
        import prior_output  # noqa: E402
        raw = prior_output.PriorOutput.from_git_head(root, f"jobs/{job}/output").read("WEB_STATE.json")
        return json.loads(raw.decode("utf-8") if isinstance(raw, bytes) else raw) if raw else None
    except Exception:
        return None


def _prior_state_folder(root, job):
    path = os.path.join(root, "jobs", job, "output", "WEB_STATE.json")
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def load_prior_state(root, job):
    """The last committed WEB_STATE.json of this job (git HEAD, else the folder), so progress accumulates."""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(HERE), "source-ladder"))
        import prior_output  # noqa: E402
        prior = prior_output.PriorOutput.from_git_head(root, f"jobs/{job}/output")
        raw = prior.read("WEB_STATE.json")
        if raw:
            data = json.loads(raw.decode("utf-8") if isinstance(raw, bytes) else raw)
            if isinstance(data, dict) and isinstance(data.get("targets"), dict):
                return data["targets"], "git_head"
    except Exception:
        pass
    path = os.path.join(root, "jobs", job, "output", "WEB_STATE.json")
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data.get("targets"), dict):
                return data["targets"], "folder"
        except (OSError, ValueError):
            pass
    return {}, "none"


def run_campaign(job, root, out_dir, targets, *, cache_dir, max_requests=300, max_targets=40, transport=None,
                 env=None, engines=None, offline=False, universe_ids=None, now=None, extra_state=None):
    """Advance up to `max_targets` targets one step each, within `max_requests`, and write the campaign files.

    targets: list of {'id','number','suffix','date','title','president','kind', ...extra}. Writes WEB_STATE.json
    (all targets, carried forward), WEB_HITS.csv (every hit), WEB_LEADS.csv (hits whose page named the order),
    WEB_NUMBERS_NAMED.csv (every order number any page read names, with whether the census has it),
    SOURCES.jsonl (every HTTP exchange), ENGINES.json (which engines answered, were blocked, need keys).
    """
    import csv
    os.makedirs(out_dir, exist_ok=True)
    prior, prior_from = load_prior_state(root, job)
    states = {k: v for k, v in prior.items() if isinstance(v, dict)}
    by_id = {t["id"]: t for t in targets}
    for iid, st in states.items():
        rescore_state(st, by_id.get(iid))
    searcher = Searcher(cache_dir, max_requests=max_requests, transport=transport, env=env, engines=engines,
                        offline=offline, now=now)
    engines_ready = searcher.ready_engines()
    picked = pick_targets(states, targets, max_targets)
    advanced = 0
    for t in picked:
        if not searcher.budget_left():
            break
        st = states.get(t["id"]) or new_state(t)
        states[t["id"]] = advance(searcher, t, st, engines_ready)
        advanced += 1
    stamp = searcher.now()
    # files
    with open(os.path.join(out_dir, "WEB_STATE.json"), "w", encoding="utf-8") as fh:
        json.dump({"job": job, "updated_utc": stamp, "prior_state_from": prior_from, "targets": states, **(extra_state or {})},
                  fh, indent=1, sort_keys=True)
    hit_fields = ["instrument_id", "score", "page_score", "engine", "strategy", "title", "url", "date", "why", "page_why",
                  "page_quote", "page_sha256", "found_utc", "snippet"]
    lead_rows, hit_rows, named = [], [], {}
    for iid, st in sorted(states.items(), key=lambda kv: (ident.parse_eo_id(kv[0]) or (0, ""), kv[0])):
        for h in st["hits"]:
            row = {"instrument_id": iid, **{k: h.get(k, "") for k in hit_fields if k != "instrument_id"}}
            row["page_score"] = "" if h.get("page_score") is None else h["page_score"]
            hit_rows.append(row)
            if (h.get("page_score") or 0) >= 60:
                lead_rows.append(row)
            for n in h.get("page_numbers_named") or []:
                named.setdefault(n, set()).add(h["url"])
    hit_rows.sort(key=lambda r: (r["instrument_id"], -(r["page_score"] if r["page_score"] != "" else -1), -r["score"]))
    lead_rows.sort(key=lambda r: (-(r["page_score"] or 0), r["instrument_id"]))
    for name, rows in (("WEB_HITS.csv", hit_rows), ("WEB_LEADS.csv", lead_rows)):
        with open(os.path.join(out_dir, name), "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=hit_fields)
            w.writeheader()
            w.writerows(rows)
    uni = set(universe_ids or [])
    with open(os.path.join(out_dir, "WEB_NUMBERS_NAMED.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["instrument_id", "in_census", "pages_naming_it", "example_url"])
        for n in sorted(named, key=lambda x: ident.parse_eo_id(x) or (0, "")):
            w.writerow([n, "yes" if n in uni else "no", len(named[n]), sorted(named[n])[0]])
    with open(os.path.join(out_dir, "SOURCES.jsonl"), "w", encoding="utf-8") as fh:
        for s in searcher.sources:
            fh.write(json.dumps(s, sort_keys=True) + "\n")
    status = {e["name"]: searcher.engine_status.get(e["name"], "not_tried") for e in searcher.engines}
    with open(os.path.join(out_dir, "ENGINES.json"), "w", encoding="utf-8") as fh:
        json.dump({"updated_utc": stamp, "engines": status}, fh, indent=1, sort_keys=True)
    summary = {
        "targets_total": len(targets), "targets_with_state": len(states), "advanced_this_run": advanced,
        "never_searched": sum(1 for t in targets if t["id"] not in states),
        "requests_used": searcher.requests_used, "fetches_budgeted": searcher.reserved, "max_requests": max_requests,
        "cache_hits": searcher.pool.cache_hits,
        "hits_total": len(hit_rows), "leads_page_confirmed": len(lead_rows),
        "targets_with_page_confirmed_lead": len({r["instrument_id"] for r in lead_rows}),
        "numbers_named_not_in_census": sum(1 for n in named if n not in uni),
        "engines": status, "prior_state_from": prior_from,
        "what_this_is_not": "Leads only: a page naming the order with its date is a place to read, not an original, a census entry or a finding.",
    }
    return summary
