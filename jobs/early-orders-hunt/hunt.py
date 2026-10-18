"""Early-orders hunt: go and get the printed texts of 18th- and 19th-century executive orders.

Clifford Lord's 1943 *List and Index of Presidential Executive Orders, Unnumbered Series* is the only
census of orders before the numbered series (1862) and of the unnumbered ones after it. Each entry gives
a date, a one-line summary and, usually, where the order's text was printed:

    X Richardson App. 83      Richardson's Messages and Papers (GPO 1896-99), vol. X, appendix p. 83
    1898 MR 23                War Department, Military Reservations ... (GPO 1898), p. 23
    1880 GLO 53               Annual Report of the Commissioner of the General Land Office for 1880, p. 53

Those books are public-domain government publications with page-level OCR on the Internet Archive. This
job reads Lord's citations, fetches each cited book once (checking the Archive's published checksum),
maps printed page numbers to scanned pages, cuts out the passage on the cited page that carries the
order's date or subject, and saves it with exact provenance. Leads whose citations point nowhere
fetchable get bounded, cached catalog searches at the Library of Congress instead.

Everything here is a lead. A printed compilation is not the signed original; a page hit is not an
identity; nothing is admitted to the census or changes any status. No model tokens are spent.

Environment: HUNT_MAX_REQUESTS (default 160), HUNT_MAX_BOOKS (default 12), HUNT_BOOKS (comma-separated
keys to restrict to), HUNT_LIVE_ROUTES (default 24, 0 disables), HUNT_YEAR_MAX (default 1899),
HUNT_OFFLINE=1 (no network at all), JOB_CACHE_DIR (download cache; bytes there are never evidence).
"""
from __future__ import annotations

import collections
import csv
import gzip
import hashlib
import io
import json
import os
import pathlib
import re
import sys
import tempfile
import time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_lib"))
from fetch_pool import FetchError, FetchPool  # noqa: E402

USER_AGENT = "EO-EarlyOrdersHunt/1.0 (noncommercial legal-history research; github.com/D3m0sthene5/Executive-Orders)"
IA_METADATA = "https://archive.org/metadata/{ident}"
IA_DOWNLOAD = "https://archive.org/download/{ident}/{name}"
IA_SEARCH = "https://archive.org/advancedsearch.php"
LOC_COLLECTION = "https://www.loc.gov/collections/{slug}/"
LEGAL_CUTOFF = "2026-10-14"

ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10}
ROMAN_OF = {v: k for k, v in ROMAN.items()}
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
          "november", "december"]
MONTH_NO = {m: i for i, m in enumerate(MONTHS, 1)}
MONTH_NO.update({"jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "sept": 9,
                 "oct": 10, "nov": 11, "dec": 12})
STOP = set("""the of and to in for a an by at on from with under as that this which be is are was were or its
their his her any all such said same other certain described lands land acres acre part parts section sections
township range county counties state states territory united ordered order orders executive president
established reserved reservation reserve military purposes purpose made act approved stat dated date
secretary department war navy interior treasury within near about between according addressed""".split())

# Presidential manuscript collections at the Library of Congress with digitized papers, by term. These are
# places to look, not claims that any particular order is there.
LOC_PAPERS = [
    (1789, 1797, "george-washington-papers"), (1801, 1809, "thomas-jefferson-papers"),
    (1809, 1817, "james-madison-papers"), (1817, 1825, "james-monroe-papers"),
    (1829, 1837, "andrew-jackson-papers"), (1837, 1841, "martin-van-buren-papers"),
    (1841, 1841, "william-henry-harrison-papers"), (1841, 1845, "john-tyler-papers"),
    (1845, 1849, "james-k-polk-papers"), (1849, 1850, "zachary-taylor-papers"),
    (1850, 1853, "millard-fillmore-papers"), (1853, 1857, "franklin-pierce-papers"),
    (1857, 1861, "james-buchanan-papers"), (1861, 1865, "abraham-lincoln-papers"),
    (1865, 1869, "andrew-johnson-papers"), (1869, 1877, "ulysses-s-grant-papers"),
    (1877, 1881, "rutherford-b-hayes-papers"), (1881, 1881, "james-a-garfield-papers"),
    (1881, 1885, "chester-a-arthur-papers"), (1885, 1889, "grover-cleveland-papers"),
    (1889, 1893, "benjamin-harrison-papers"), (1893, 1897, "grover-cleveland-papers"),
    (1897, 1901, "william-mckinley-papers"),
]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha1_bytes(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def env_int(name, default):
    try:
        return max(0, int(os.environ.get(name, "") or default))
    except ValueError:
        return default


# ----------------------------------------------------------------------------- citations

# Lord's forms, with the OCR damage the lists show: "Richard- son", "Richardson App .", "1 Stat.L. 136",
# "( 1898 MR 23 ; 1907 MR 40 )", "1880 GLO 53", "Kappler I 823", "Annals , 2 Cong . , 1 sess . , 1247".
RICH_RE = re.compile(r"(?<![A-Za-z])(VIII|VII|VI|IX|IV|V|X|III|II|I)\s*[.,]?\s*Rich(?:ard)?\s*-?\s*(?:ard)?\s*-?\s*son"
                     r"\s*[.,]?\s*(App(?:e|\.|endix)?\s*\.?\s*)?(\d{1,3})(?:\s*-\s*(\d{1,3}))?", re.I)
MR_RE = re.compile(r"(1[89]\d\d)\s*MR\s*[.,]?\s*(\d{1,3})")
GLO_RE = re.compile(r"(1[89]\d\d)\s*GLO\s*[.,]?\s*(\d{1,4})")
STAT_RE = re.compile(r"(\d{1,2})\s*Stat\s*\.?\s*L?\s*\.?\s*(\d{1,4})")
ANNALS_RE = re.compile(r"Annals\s*,?\s*(\d{1,2})\s*Cong\s*\.?\s*,?\s*(\d)\s*sess\s*\.?\s*,?\s*(\d{1,4})", re.I)
ASP_RE = re.compile(r"Amer\s*\.?\s*St\s*\.?\s*Papers\s*,?\s*([A-Za-z ]{3,30}?)\s*,?\s*(I{1,3}|IV|V|VI{0,3}|IX|X)\s*,\s*(\d{1,4})")
KAPPLER_RE = re.compile(r"Kappler\s*,?\s*(I{1,3}|IV|V)?\s*,?\s*(\d{1,4})")
SPARKS_RE = re.compile(r"(I{1,3}|IV|V|VI{0,3}|IX|X|XI|XII)\s*Sparks\s*,?\s*(\d{1,4})")
DOC_RE = re.compile(r"\b(H|S)\s*\.\s*(?:Ex\s*\.\s*)?(?:Doc|Rept?|Misc\s*\.?\s*Doc)\s*\.?\s*(\d{1,4})", re.I)
INTELL_RE = re.compile(r"(North\s+American\s+)?Intelligencer\s*,?\s*([A-Z][a-z]{2,8}\.?\s*\d{1,2}\s*,\s*1[78]\d\d)")


def parse_citations(text: str) -> list:
    """Every printed-source citation in a Lord entry, normalised. Book-backed kinds carry a book_key."""
    out, seen = [], set()
    t = (text or "").replace("\n", " ")

    def add(kind, raw, **fields):
        key = (kind, tuple(sorted(fields.items())))
        if key in seen:
            return
        seen.add(key)
        out.append({"kind": kind, "raw": raw.strip(), **fields})

    for m in RICH_RE.finditer(t):
        vol = ROMAN[m.group(1).upper()]
        appendix = bool(m.group(2))
        add("richardson", m.group(0), volume=vol, appendix=appendix, page=int(m.group(3)),
            page_end=int(m.group(4)) if m.group(4) else None, book_key=f"RICH_{ROMAN_OF[vol]}",
            section="appendix" if appendix else "main")
    for m in MR_RE.finditer(t):
        add("mr", m.group(0), year=int(m.group(1)), page=int(m.group(2)), book_key=f"MR_{m.group(1)}", section="main")
    for m in GLO_RE.finditer(t):
        add("glo", m.group(0), year=int(m.group(1)), page=int(m.group(2)), book_key=f"GLO_{m.group(1)}", section="main")
    for m in STAT_RE.finditer(t):
        vol, page = int(m.group(1)), int(m.group(2))
        add("statutes_at_large", m.group(0), volume=vol, page=page,
            route=f"https://www.loc.gov/item/llsl-v{vol}/", route_note="Library of Congress Statutes at Large volume; find the printed page in the viewer")
    for m in ANNALS_RE.finditer(t):
        add("annals_of_congress", m.group(0), congress=int(m.group(1)), session=int(m.group(2)), column=int(m.group(3)),
            route="https://memory.loc.gov/ammem/amlaw/lwac.html", route_note="A Century of Lawmaking: Annals of Congress, by Congress and session; column number as cited")
    for m in ASP_RE.finditer(t):
        add("american_state_papers", m.group(0), series=m.group(1).strip(), volume=ROMAN.get(m.group(2).upper()), page=int(m.group(3)),
            route="https://memory.loc.gov/ammem/amlaw/lwsp.html", route_note="A Century of Lawmaking: American State Papers, by series and volume")
    for m in KAPPLER_RE.finditer(t):
        add("kappler", m.group(0), volume=ROMAN.get((m.group(1) or "").upper()), page=int(m.group(2)),
            route="https://dc.library.okstate.edu/digital/collection/kapplers", route_note="Kappler, Indian Affairs: Laws and Treaties (Oklahoma State University digital edition)")
    for m in SPARKS_RE.finditer(t):
        add("sparks_washington", m.group(0), volume=ROMAN.get(m.group(1).upper()), page=int(m.group(2)),
            route="https://archive.org/search?query=Sparks+%22Writings+of+George+Washington%22", route_note="Jared Sparks, The Writings of George Washington; volumes on the Internet Archive")
    for m in DOC_RE.finditer(t):
        add("congressional_document", m.group(0), chamber="House" if m.group(1).upper() == "H" else "Senate", number=int(m.group(2)),
            route="https://www.govinfo.gov/app/collection/serialset", route_note="Congressional Serial Set (govinfo) or HathiTrust; Congress and session are in the entry")
    for m in INTELL_RE.finditer(t):
        add("newspaper", m.group(0), title=("North American Intelligencer" if m.group(1) else "National Intelligencer"), issue=m.group(2),
            route="https://www.loc.gov/collections/chronicling-america/", route_note="Chronicling America (Library of Congress) full-text newspaper search by date")
    return out


# ----------------------------------------------------------------------------- leads

def parse_lord_date(year, date_text):
    """'Aug 28' + 1790 -> ('1790-08-28', 'day'); 'Sept. 287' (OCR) -> ('1790-09', 'month'); '' -> (year, 'year')."""
    y = int(year)
    s = (date_text or "").strip().replace(".", " ")
    m = re.match(r"^([A-Za-z]{3,9})\s*(\d{1,2})?(?!\d)", s)
    if not m or m.group(1).lower() not in MONTH_NO:
        return f"{y:04d}", "year"
    mo = MONTH_NO[m.group(1).lower()]
    d = int(m.group(2)) if m.group(2) else None
    if d and 1 <= d <= 31:
        return f"{y:04d}-{mo:02d}-{d:02d}", "day"
    return f"{y:04d}-{mo:02d}", "month"


def keywords(summary: str, n=8) -> list:
    words = re.findall(r"[A-Za-z][A-Za-z'\-]{4,}", summary or "")
    out = []
    for w in words:
        lw = w.lower().strip("'-")
        if lw in STOP or lw in out or len(lw) < 5:
            continue
        out.append(lw)
        if len(out) >= n:
            break
    return out


def load_lord_entries(repo: pathlib.Path, job_dir: pathlib.Path, year_max: int):
    live = repo / "jobs" / "wpa-lists" / "output" / "UNNUMBERED_ENTRIES.csv"
    vendored = job_dir / "data" / "lord_subset" / "UNNUMBERED_ENTRIES_pre1900.csv"
    path = live if live.is_file() else vendored
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    leads = []
    for r in rows:
        if not (r.get("year") or "").isdigit() or int(r["year"]) > year_max:
            continue
        date, precision = parse_lord_date(r["year"], r.get("date"))
        blob = (r.get("summary") or "") + " " + (r.get("citation_text") or "")
        leads.append({
            "lead_id": f"LORD:U:{int(r['seq']):04d}", "origin": "lord_1943_unnumbered_list",
            "year": int(r["year"]), "date": date, "date_precision": precision, "lord_page": r.get("page", ""),
            "summary": re.sub(r"\s+", " ", (r.get("summary") or "")).strip(),
            "citations": parse_citations(blob), "keywords": keywords(r.get("summary") or ""),
            "known_primary_url": "",
        })
    return leads, {"source": "jobs/wpa-lists/output" if path == live else "committed subset (wpa-lists output absent)",
                   "path": str(path.relative_to(repo)) if path.is_relative_to(repo) else str(path),
                   "sha256": sha256_bytes(path.read_bytes()), "rows_read": len(rows), "leads": len(leads)}


def load_stage14_leads(repo: pathlib.Path, year_max: int):
    path = repo / "research" / "stage14" / "LORD" / "LORD_CHRONOLOGICAL_REVIEW_LEADS.csv"
    if not path.is_file():
        return [], {"path": str(path), "present": False}
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    leads = []
    for r in rows:
        y = r.get("year_hint_UNVERIFIED") or ""
        if not y.isdigit() or int(y) > year_max:
            continue
        mo, d = r.get("month") or "", r.get("day") or ""
        if mo.isdigit() and d.isdigit() and 1 <= int(mo) <= 12 and 1 <= int(d) <= 31:
            date, precision = f"{int(y):04d}-{int(mo):02d}-{int(d):02d}", "day"
        else:
            date, precision = f"{int(y):04d}", "year"
        excerpt = r.get("source_excerpt_UNVERIFIED") or ""
        leads.append({
            "lead_id": r["candidate_id"], "origin": "stage14_lord_scan_ocr", "year": int(y), "date": date,
            "date_precision": precision, "lord_page": r.get("pdf_page", ""), "lord_scan_url": r.get("loc_page_url", ""),
            "summary": re.sub(r"\s+", " ", excerpt).strip()[:400], "citations": parse_citations(excerpt),
            "keywords": keywords(excerpt), "known_primary_url": "",
        })
    return leads, {"path": "research/stage14/LORD/LORD_CHRONOLOGICAL_REVIEW_LEADS.csv", "present": True,
                   "sha256": sha256_bytes(path.read_bytes()), "rows_read": len(rows), "leads": len(leads)}


def load_stage18_candidates(repo: pathlib.Path):
    path = repo / "research" / "stage18" / "data" / "EARLY_SOURCE_CANDIDATES.csv"
    if not path.is_file():
        return [], {"path": str(path), "present": False}
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    leads = []
    for r in rows:
        date = r.get("date") or ""
        leads.append({
            "lead_id": r["candidate_id"], "origin": "stage18_curated_candidate", "year": int(date[:4]) if date[:4].isdigit() else None,
            "date": date, "date_precision": "day" if len(date) == 10 else "year", "lord_page": "",
            "summary": r.get("document_identity") or "", "citations": [], "keywords": keywords(r.get("document_identity") or ""),
            "known_primary_url": r.get("primary_source_url") or "", "inclusion_state": r.get("inclusion_state") or "",
        })
    return leads, {"path": "research/stage18/data/EARLY_SOURCE_CANDIDATES.csv", "present": True,
                   "sha256": sha256_bytes(path.read_bytes()), "leads": len(leads)}


# ----------------------------------------------------------------------------- Internet Archive

class Budget:
    def __init__(self, max_requests):
        self.max_requests = max_requests
        self.spent = 0
        self.refused = 0

    def take(self, n=1):
        if self.spent + n > self.max_requests:
            self.refused += n
            return False
        self.spent += n
        return True


def make_pool(cache_dir, offline, transport=None):
    return FetchPool(cache_dir, workers=4, per_host=3, transport=transport, max_bytes=120_000_000, timeout=120,
                     user_agent=USER_AGENT, min_interval=0.5, offline=offline)


def fetch_json(pool, budget, url):
    if not budget.take():
        raise FetchError("request budget exhausted")
    r = pool.fetch(url)
    return json.loads(r["body"].decode("utf-8")), r


def ia_metadata(pool, budget, ident):
    data, r = fetch_json(pool, budget, IA_METADATA.format(ident=ident))
    if not data or "metadata" not in data:
        raise FetchError("no metadata for " + ident)
    files = {f["name"]: f for f in data.get("files", [])}
    return data["metadata"], files, r


def check_edition(meta, verify) -> dict:
    """Does the Archive item describe the edition Lord cites? Title words, year and publisher from metadata."""
    title = " ".join(meta.get("title", []) if isinstance(meta.get("title"), list) else [str(meta.get("title", ""))]).lower()
    pub = str(meta.get("publisher", "")).lower()
    years = set(int(y) for y in re.findall(r"\b(1[89]\d\d|20\d\d)\b", " ".join(str(meta.get(k, "")) for k in ("date", "year"))))
    ok_title = all(w in title for w in verify.get("title_words", []))
    ok_year = (not verify.get("year_any")) or bool(years & set(verify["year_any"]))
    ok_pub = (not verify.get("publisher_any")) or any(p in pub for p in verify["publisher_any"])
    return {"title_ok": ok_title, "year_ok": ok_year, "publisher_ok": ok_pub, "title": title[:120], "publisher": pub[:80],
            "years_in_metadata": sorted(years), "edition_ok": ok_title and ok_year and ok_pub}


def report_year_on_title_pages(pages, want_year, first=40) -> dict:
    """GLO reports: the fiscal year the report covers is printed on the title page ('for the fiscal year ended
    June 30, 1880'). Looks at the first pages for that year, and for any other 'year ended' year."""
    found, others = False, set()
    for _, text in pages[:first]:
        for m in re.finditer(r"(?:year|years)\s+(?:ended|ending)\s+(?:June\s+30\s*,?\s*)?(1[89]\d\d)", text, re.I):
            y = int(m.group(1))
            if y == want_year:
                found = True
            else:
                others.add(y)
        if re.search(r"\b" + str(want_year) + r"\b", text) and re.search(r"(?i)general\s+land\s+office", text):
            found = True
    return {"report_year_found": found, "other_years_seen": sorted(others)[:6]}


def djvu_pages(xml_bytes: bytes) -> list:
    """[(image_number, text)] from an Internet Archive DjVuXML file. Words on a line are joined with one space."""
    pages = []
    n = 0
    for _, el in ET.iterparse(io.BytesIO(xml_bytes), events=("end",)):
        if el.tag != "OBJECT":
            continue
        n += 1
        lines = []
        for ln in el.iter("LINE"):
            words = [(w.text or "").strip() for w in ln.findall("WORD")]
            words = [w for w in words if w]
            if words:
                lines.append(" ".join(words))
        pages.append((n, "\n".join(lines)))
        el.clear()
    return pages


# ----------------------------------------------------------------------------- printed page map

HEAD_EVEN = re.compile(r"^\s*([0-9]{1,4})\s+[A-Za-z]")
HEAD_ODD = re.compile(r"[A-Za-z.,;:'\"]\s+([0-9]{1,4})\s*[.,]?\s*$")
HEAD_LONE = re.compile(r"^\s*([0-9]{1,4})\s*$")
HEAD_SECTION = re.compile(r"^\s*(Appendix|Index)\b", re.I)


def head_number(text: str):
    """(section, printed number) read from the running head of a page, or (section, None)."""
    lines = [l for l in text.split("\n") if l.strip()][:2]
    section = "main"
    for l in lines:
        m = HEAD_SECTION.match(l)
        if m:
            section = m.group(1).lower()
            break
    for l in lines:
        for pat in (HEAD_EVEN, HEAD_ODD, HEAD_LONE):
            m = pat.search(l)
            if m:
                n = int(m.group(1))
                if 1 <= n <= 2000:
                    return section, n
    return section, None


def printed_page_map(pages: list, window=12) -> tuple:
    """Printed page number for each scanned image. Reads every readable running head, takes the locally most
    common offset (image minus printed) so OCR misreads and plates don't shift the map, and reports how many
    heads agree with the result. Returns ({image: (section, printed)}, stats)."""
    heads = {}
    for img, text in pages:
        section, n = head_number(text)
        heads[img] = (section, n)
    readable = [(img, s, n) for img, (s, n) in heads.items() if n is not None]
    pm, agree, disagree = {}, 0, []
    for i, (img, s, n) in enumerate(readable):
        lo, hi = max(0, i - window), min(len(readable), i + window + 1)
        neighbours = [(im, sc, nn) for im, sc, nn in readable[lo:hi] if sc == s]
        offsets = collections.Counter(im - nn for im, sc, nn in neighbours)
        off, votes = offsets.most_common(1)[0]
        if votes < 3 and len(neighbours) >= 3:
            disagree.append((img, s, n, "no consistent offset nearby"))
            continue
        printed = img - off
        if printed == n:
            agree += 1
        else:
            disagree.append((img, s, n, printed))
        pm[img] = (s, printed, off)
    # Fill pages without a readable head from the nearest mapped page of the same run.
    mapped = sorted(pm)
    for img, _ in pages:
        if img in pm or not mapped:
            continue
        before = max((m for m in mapped if m < img), default=None)
        after = min((m for m in mapped if m > img), default=None)
        ref = before if before is not None and (after is None or img - before <= after - img) else after
        s, _, off = pm[ref]
        if abs(ref - img) <= 6:
            pm[img] = (s, img - off, off)
    stats = {"pages": len(pages), "heads_read": len(readable), "heads_agree": agree, "heads_disagree": len(disagree),
             "disagreements": [list(d) for d in disagree[:15]], "pages_mapped": len(pm),
             "sections": sorted(set(s for s, _, _ in pm.values()))}
    return {img: (s, p) for img, (s, p, _) in pm.items()}, stats


def inverse_map(pm: dict) -> dict:
    inv = collections.defaultdict(list)
    for img, (s, p) in pm.items():
        inv[(s, p)].append(img)
    return {k: sorted(v) for k, v in inv.items()}


# ----------------------------------------------------------------------------- finding the order on the page

def date_patterns(date: str, precision: str) -> list:
    y = date[:4]
    if precision == "year":
        return [re.compile(r"\b" + y + r"\b")]
    mo = int(date[5:7])
    name = MONTHS[mo - 1]
    month_re = name[:3] + r"[a-z]*\.?"
    if precision == "month":
        return [re.compile(r"(?i)\b" + month_re + r"\s+\d{1,2}\s*,?\s*" + y), re.compile(r"(?i)\b" + month_re + r"\s*,?\s*" + y)]
    d = int(date[8:10])
    return [re.compile(r"(?i)\b" + month_re + r"\s+" + str(d) + r"(?:st|d|nd|rd|th)?\s*,?\s*(?:A\.?\s*D\.?\s*)?" + y),
            re.compile(r"(?i)\b" + str(d) + r"(?:st|d|nd|rd|th)?\s+(?:day\s+of\s+)?" + month_re + r"\s*,?\s*(?:A\.?\s*D\.?\s*)?" + y),
            re.compile(r"(?i)\b" + month_re + r"\s+" + str(d) + r"\b")]


def locate(lead: dict, page_texts: list) -> dict:
    """Where on the cited page (or its neighbours) does the lead's date or subject appear? page_texts is
    [(image, text)] for the cited page first, then neighbours. Returns the best hit."""
    pats = date_patterns(lead["date"], lead["date_precision"])
    kws = lead.get("keywords") or []
    best = None
    for rank, (img, text) in enumerate(page_texts):
        low = text.lower()
        kw_hits = [k for k in kws if k in low]
        date_hit = None
        for p in pats:
            m = p.search(text)
            if m:
                date_hit = m
                break
        score = (3 if date_hit else 0) + min(len(kw_hits), 3) - (1 if rank else 0)
        if date_hit and len(kw_hits) >= 1:
            grade = "page_date_and_subject"
        elif date_hit:
            grade = "page_and_date"
        elif len(kw_hits) >= 2:
            grade = "page_and_subject"
        else:
            grade = "page_only"
        if date_hit:
            anchor = (date_hit.start(), date_hit.end())
        elif kw_hits:
            k0 = low.find(kw_hits[0])
            anchor = (k0, k0 + len(kw_hits[0]))
        else:
            anchor = None
        hit = {"image": img, "grade": grade, "score": score, "date_span": (date_hit.start(), date_hit.end()) if date_hit else None,
               "anchor": anchor, "keyword_hits": kw_hits, "neighbour_rank": rank}
        if best is None or hit["score"] > best["score"]:
            best = hit
    return best


def excerpt(text: str, anchor, kind: str, max_lines=70) -> tuple:
    """The passage around the anchor: for Richardson, from the nearest title/dateline above to the next
    signature or blank-run below; for the reservation and land-office books, the entry paragraph. Returns
    (excerpt_text, first_line_index, last_line_index)."""
    lines = text.split("\n")
    if anchor is None:
        return "\n".join(lines[:max_lines]), 0, min(len(lines), max_lines) - 1
    # line index of the anchor offset
    pos, idx = 0, 0
    for i, l in enumerate(lines):
        if pos + len(l) >= anchor[0]:
            idx = i
            break
        pos += len(l) + 1
    if kind == "richardson":
        start = idx
        for i in range(idx, max(-1, idx - 25), -1):
            l = lines[i].strip()
            if re.match(r"^[A-Z][A-Z .,'\-]{6,}$", l) or re.search(r"(?i)^(executive\s+(mansion|order)|by\s+the\s+president|united\s+states\s*,|washington\s*,|war\s+department|treasury\s+department|department\s+of\s+state)", l):
                start = i
                break
        end = idx
        for i in range(idx + 1, min(len(lines), idx + max_lines)):
            l = lines[i].strip()
            end = i
            if re.search(r"(?:WASHINGTON|ADAMS|JEFFERSON|MADISON|MONROE|JACKSON|VAN\s+BUREN|HARRISON|TYLER|POLK|TAYLOR|FILLMORE|PIERCE|BUCHANAN|LINCOLN|JOHNSON|GRANT|HAYES|GARFIELD|ARTHUR|CLEVELAND|McKINLEY)\s*\.?\s*$", l) \
                    or re.search(r"(?i)^by\s+(order|command|direction)\s+of\s+the\s+president", l) or re.match(r"^\[From\b", l):
                break
    else:
        start = idx
        for i in range(idx, max(-1, idx - 30), -1):
            l = lines[i].strip()
            if re.match(r"^[A-Z][A-Z0-9 .,'\-()]{4,}\.?$", l) and len(l.split()) <= 9:
                start = i
                break
        end = idx
        for i in range(idx + 1, min(len(lines), idx + max_lines)):
            l = lines[i].strip()
            if re.match(r"^[A-Z][A-Z0-9 .,'\-()]{4,}\.?$", l) and len(l.split()) <= 9:
                break
            end = i
    return "\n".join(lines[start:end + 1]), start, end


# ----------------------------------------------------------------------------- the hunt

def load_books(job_dir: pathlib.Path) -> dict:
    data = json.loads((job_dir / "data" / "BOOKS.json").read_text(encoding="utf-8"))
    return {b["key"]: b for b in data["books"]}


def rank_books(leads: list, books: dict) -> list:
    """Books ordered by the leads they would unlock; a pre-1862 lead counts three times."""
    weight = collections.Counter()
    leads_by_book = collections.defaultdict(set)
    for lead in leads:
        for c in lead["citations"]:
            k = c.get("book_key")
            if k and k in books:
                weight[k] += 3 if (lead.get("year") or 9999) < 1862 else 1
                leads_by_book[k].add(lead["lead_id"])
    order = sorted(weight, key=lambda k: (-weight[k], k))
    return [{"book_key": k, "weight": weight[k], "leads": len(leads_by_book[k])} for k in order]


def held_pages_from_repo(repo: pathlib.Path, rel: str):
    path = repo / rel
    if not path.is_file():
        return None
    pages = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            pages.append((int(d["page"]), d["text"]))
    return pages, {"source": rel, "sha256": sha256_bytes(path.read_bytes())}


def fetch_copy(ident: str, book: dict, pool, budget) -> dict:
    """One Internet Archive copy of a book: metadata, edition check, page text with the Archive's checksum."""
    out = {"ia_identifier": ident, "status": "", "edition": {}, "custody": {}, "pages": None}
    try:
        meta, files, mr = ia_metadata(pool, budget, ident)
    except FetchError as e:
        out.update(status="metadata_fetch_failed", error=str(e))
        return out
    out["edition"] = check_edition(meta, book.get("verify", {}))
    xml_name = ident + "_djvu.xml"
    if xml_name not in files:
        out.update(status="no_page_text_file", files_seen=sorted(files)[:20])
        return out
    if not budget.take():
        out["status"] = "request_budget_exhausted"
        return out
    try:
        r = pool.fetch(IA_DOWNLOAD.format(ident=ident, name=xml_name))
    except FetchError as e:
        out.update(status="page_text_fetch_failed", error=str(e))
        return out
    published_sha1 = files[xml_name].get("sha1")
    actual_sha1 = sha1_bytes(r["body"])
    pages = djvu_pages(r["body"])
    pdf = files.get(ident + ".pdf", {})
    out["custody"] = {
        "metadata_url": IA_METADATA.format(ident=ident), "metadata_sha256": mr["sha256"],
        "page_text_url": r["url"], "page_text_bytes": r["bytes"], "page_text_sha256": r["sha256"], "page_text_sha1": actual_sha1,
        "archive_published_sha1": published_sha1, "sha1_matches_archive": (published_sha1 == actual_sha1) if published_sha1 else None,
        "pdf_url": IA_DOWNLOAD.format(ident=ident, name=ident + ".pdf") if pdf else None, "pdf_bytes": int(pdf["size"]) if pdf.get("size") else None,
        "pdf_archive_sha1": pdf.get("sha1"), "pdf_fetched": False,
        "item_url": "https://archive.org/details/" + ident, "scanned_by": meta.get("scanner") or meta.get("contributor") or meta.get("sponsor"),
    }
    if book["kind"] == "glo":
        out["edition"].update(report_year_on_title_pages(pages, book["verify"].get("report_year")))
    out.update(status="fetched", pages=pages)
    return out


def get_book(book: dict, pool, budget, out_books: pathlib.Path, repo: pathlib.Path, log) -> dict:
    """One book's page text, from the repo when already held, else from the Internet Archive: the preferred
    copy first, then the alternates until one is complete enough (at least `verify.min_pages` scanned pages;
    an 84-page extract of a 500-page report is not the book Lord cited). Every copy tried is recorded."""
    rec = {"book_key": book["key"], "kind": book["kind"], "label": book["label"], "status": "", "ia_identifier": book.get("ia_identifier"),
           "retrieved_utc": None, "pages": 0, "custody": {}, "edition": {}, "page_map": {}, "copies_tried": []}
    held = book.get("held_in_repo")
    if held:
        got = held_pages_from_repo(repo, held)
        if got:
            pages, custody = got
            rec.update(status="held_in_repo", pages=len(pages), custody=custody)
            return rec, pages
    candidates = [i for i in [book.get("ia_identifier")] + list(book.get("ia_alternates") or []) if i]
    if not candidates:
        rec["status"] = "no_identifier_yet"
        return rec, None
    min_pages = int(book.get("verify", {}).get("min_pages", 150))
    best = None
    for ident in candidates:
        copy = fetch_copy(ident, book, pool, budget)
        rec["copies_tried"].append({"ia_identifier": ident, "status": copy["status"], "pages": len(copy["pages"]) if copy["pages"] else 0,
                                    "edition_ok": copy["edition"].get("edition_ok"), "error": copy.get("error")})
        if copy["status"] != "fetched":
            if copy["status"] == "request_budget_exhausted":
                break
            continue
        if len(copy["pages"]) >= min_pages:
            best = copy
            break
        if best is None:
            best = copy
            log(f"  {book['key']}: {ident} has only {len(copy['pages'])} pages (fewer than {min_pages}); trying the alternates")
    if best is None:
        rec["status"] = rec["copies_tried"][-1]["status"] if rec["copies_tried"] else "no_identifier_yet"
        rec["error"] = rec["copies_tried"][-1].get("error") if rec["copies_tried"] else None
        return rec, None
    pages = best["pages"]
    rec.update(status="fetched" if len(pages) >= min_pages else "fetched_short_copy", retrieved_utc=now_utc(), pages=len(pages),
               ia_identifier=best["ia_identifier"], custody=best["custody"], edition=best["edition"])
    log(f"  {book['key']}: {len(pages)} pages from {best['ia_identifier']}; sha1 {'matches' if rec['custody']['sha1_matches_archive'] else 'NOT matched'} the Archive's")
    return rec, pages


def discover_candidates(book: dict, pool, budget) -> list:
    """For a book without a known Archive copy: list candidate items (never fetched here)."""
    if book["kind"] == "glo":
        q = f'title:("general land office") AND mediatype:texts AND (year:{book["verify"]["report_year"]} OR year:{book["verify"]["report_year"] + 1} OR date:[{book["verify"]["report_year"]}-01-01 TO {book["verify"]["report_year"] + 1}-12-31])'
    else:
        q = " AND ".join(f"title:({w})" for w in book["verify"].get("title_words", []))
    url = IA_SEARCH + "?" + urllib.parse.urlencode([("q", q), ("fl[]", "identifier"), ("fl[]", "title"), ("fl[]", "date"),
                                                   ("fl[]", "publisher"), ("rows", "12"), ("output", "json")])
    try:
        data, _ = fetch_json(pool, budget, url)
    except FetchError as e:
        return [{"error": str(e), "query": q}]
    return [{"identifier": d.get("identifier"), "title": str(d.get("title", ""))[:100], "date": str(d.get("date", ""))[:10],
             "publisher": str(d.get("publisher", ""))[:60], "query": q} for d in data.get("response", {}).get("docs", [])]


def resolve(lead: dict, cit: dict, book_rec: dict, pages_by_img: dict, inv: dict, out_texts: pathlib.Path) -> dict:
    """One citation of one lead against a held book: locate the page, find the date or subject, cut the passage."""
    res = {"lead_id": lead["lead_id"], "book_key": cit["book_key"], "citation": cit["raw"], "section": cit.get("section", "main"),
           "printed_page": cit["page"], "image": None, "grade": "", "keyword_hits": "", "text_file": "", "excerpt_sha256": "", "note": ""}
    if book_rec is None or book_rec.get("status") not in ("fetched", "fetched_short_copy", "held_in_repo"):
        res["grade"] = "book_not_held"
        res["note"] = (book_rec or {}).get("status", "not_in_registry")
        return res
    section = cit.get("section", "main")
    imgs = inv.get((section, cit["page"]))
    if not imgs and section == "appendix":
        imgs = inv.get(("main", cit["page"]))
        res["note"] = "appendix page not mapped as such; main-section page used"
    if not imgs:
        res["grade"] = "page_not_mapped"
        return res
    img = imgs[0]
    neighbours = [(i, pages_by_img[i]) for i in (img, img + 1, img - 1) if i in pages_by_img]
    hit = locate(lead, neighbours)
    res["image"] = hit["image"]
    res["grade"] = hit["grade"]
    res["keyword_hits"] = "|".join(hit["keyword_hits"])
    text = pages_by_img[hit["image"]]
    body, first, last = excerpt(text, hit["anchor"], book_rec["kind"])
    res["excerpt_sha256"] = sha256_bytes(body.encode("utf-8"))
    name = f"{lead['lead_id'].replace(':', '_')}__{cit['book_key']}_p{cit['page']}.txt"
    header = [
        f"# lead: {lead['lead_id']}  date: {lead['date']} ({lead['date_precision']})",
        f"# Lord summary: {lead['summary'][:300]}",
        f"# citation: {cit['raw']}  ->  {book_rec['label']}",
        f"# printed page {cit['page']} ({section}); scanned image {hit['image']}; page lines {first}-{last}",
        f"# source: {book_rec['custody'].get('page_text_url') or book_rec['custody'].get('source')}  sha256 {book_rec['custody'].get('page_text_sha256') or book_rec['custody'].get('sha256')}",
        f"# grade: {hit['grade']}  keywords: {res['keyword_hits']}",
        "# This is OCR of a printed compilation, a lead for original_text, never the signed original. Exact slice follows the marker line.",
        "----- EXACT SLICE -----",
    ]
    (out_texts / name).write_text("\n".join(header) + "\n" + body + "\n", encoding="utf-8")
    res["text_file"] = "texts/" + name
    return res


def live_routes(leads: list, pool, budget, max_routes: int, out_resp: pathlib.Path, log) -> tuple:
    """Bounded Library of Congress catalog searches for pre-1862 leads with a day-precise date and no text
    yet. Each response is saved by hash. A hit is a catalog record to inspect, never a found order."""
    routes, hits = [], []
    if max_routes <= 0:
        return routes, hits
    todo = sorted((l for l in leads if l.get("year") and l["year"] < 1862 and l["date_precision"] == "day" and not l.get("texts")),
                  key=lambda l: (l["year"], l["lead_id"]))
    for lead in todo:
        if len(routes) >= max_routes:
            break
        y = lead["year"]
        slugs = ["chronicling-america"] + [s for lo, hi, s in LOC_PAPERS if lo <= y <= hi][:1]
        q = " ".join(lead["keywords"][:3]) or "president order"
        d = lead["date"]
        try:
            end = (date.fromisoformat(d) + timedelta(days=20)).isoformat()
        except ValueError:  # an OCR day such as February 30: fall back to the whole year
            d, end = d[:4] + "-01-01", d[:4] + "-12-31"
        for slug in slugs:
            if len(routes) >= max_routes:
                break
            params = [("q", q), ("fo", "json"), ("c", "5"), ("at", "results,pagination")]
            if slug == "chronicling-america":
                params.append(("dates", f"{d}/{end}"))
            else:
                params.append(("dates", f"{d[:4]}/{d[:4]}"))
            url = LOC_COLLECTION.format(slug=slug) + "?" + urllib.parse.urlencode(params)
            route = {"lead_id": lead["lead_id"], "collection": slug, "query": q, "date_window": f"{d}/{end}" if slug == "chronicling-america" else d[:4],
                     "url": url, "state": "", "results": 0, "total": None, "response_file": ""}
            if not budget.take():
                route["state"] = "request_budget_exhausted"
                routes.append(route)
                continue
            try:
                r = pool.fetch(url)
                data = json.loads(r["body"].decode("utf-8"))
                results = data.get("results", []) or []
                route.update(state="searched", results=len(results), total=(data.get("pagination") or {}).get("of"))
                fname = f"loc_{r['sha256'][:16]}.json.gz"
                with gzip.open(out_resp / fname, "wb") as gz:
                    gz.write(r["body"])
                route["response_file"] = "responses/" + fname
                for item in results[:5]:
                    hits.append({"lead_id": lead["lead_id"], "collection": slug, "date": item.get("date", ""),
                                 "title": str(item.get("title", ""))[:160], "id": item.get("id", ""),
                                 "note": "catalog record to inspect; not an identified order"})
            except (FetchError, ValueError) as e:
                route["state"] = "failed: " + str(e)[:120]
            routes.append(route)
    log(f"  live routes: {sum(1 for r in routes if r['state'] == 'searched')} searched, {len(hits)} catalog records saved")
    return routes, hits


def write_csv(path: pathlib.Path, rows: list, fields: list):
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v) for k, v in r.items()})


def run(repo_root, job_dir, output_dir, transport=None) -> dict:
    repo, job_dir, out = pathlib.Path(repo_root).resolve(), pathlib.Path(job_dir), pathlib.Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    for sub in ("texts", "books", "responses"):
        (out / sub).mkdir(exist_ok=True)
    offline = os.environ.get("HUNT_OFFLINE") == "1"
    year_max = env_int("HUNT_YEAR_MAX", 1899)
    max_books = env_int("HUNT_MAX_BOOKS", 12)
    max_live = env_int("HUNT_LIVE_ROUTES", 24)
    budget = Budget(env_int("HUNT_MAX_REQUESTS", 160))
    only = set(k.strip() for k in os.environ.get("HUNT_BOOKS", "").split(",") if k.strip())
    cache_dir = os.environ.get("JOB_CACHE_DIR") or os.path.join(tempfile.gettempdir(), "early-orders-hunt-cache")
    log_lines = []

    def log(msg):
        print(msg)
        log_lines.append(msg)

    t0 = time.time()
    books = load_books(job_dir)
    lord, lord_src = load_lord_entries(repo, job_dir, year_max)
    s14, s14_src = load_stage14_leads(repo, year_max)
    s18, s18_src = load_stage18_candidates(repo)
    leads = lord + s14 + s18
    log(f"Leads: {len(lord)} Lord list entries ({lord_src['source']}), {len(s14)} Lord scan date markers, {len(s18)} curated candidates; years to {year_max}.")

    citations = []
    for lead in leads:
        for c in lead["citations"]:
            citations.append({"lead_id": lead["lead_id"], "year": lead["year"], **c})
    kinds = collections.Counter(c["kind"] for c in citations)
    log(f"Citations parsed: {len(citations)} ({', '.join(f'{k} {v}' for k, v in kinds.most_common())}).")

    ranking = rank_books(leads, books)
    if only:
        ranking = [r for r in ranking if r["book_key"] in only]
    pool = make_pool(cache_dir, offline, transport)
    book_recs, pages_of, inv_of = {}, {}, {}
    fetched = 0
    for r in ranking:
        key = r["book_key"]
        book = books[key]
        if fetched >= max_books and not book.get("held_in_repo"):
            book_recs[key] = {"book_key": key, "kind": book["kind"], "label": book["label"], "status": "deferred_book_budget",
                              "ia_identifier": book.get("ia_identifier"), "custody": {}, "edition": {}, "page_map": {}}
            continue
        if offline and not book.get("held_in_repo"):
            book_recs[key] = {"book_key": key, "kind": book["kind"], "label": book["label"], "status": "offline",
                              "ia_identifier": book.get("ia_identifier"), "custody": {}, "edition": {}, "page_map": {}}
            continue
        rec, pages = get_book(book, pool, budget, out / "books", repo, log)
        if rec["status"] in ("fetched", "fetched_short_copy"):
            fetched += 1
        if pages:
            pm, stats = printed_page_map(pages)
            rec["page_map"] = stats
            pages_of[key] = dict(pages)
            inv_of[key] = inverse_map(pm)
            with gzip.open(out / "books" / f"{key}_pages.jsonl.gz", "wt", encoding="utf-8") as gz:
                for img, text in pages:
                    s, p = pm.get(img, ("", None))
                    gz.write(json.dumps({"image": img, "section": s, "printed": p, "text": text}, ensure_ascii=False) + "\n")
            rec["pages_file"] = f"books/{key}_pages.jsonl.gz"
        elif rec["status"] == "no_identifier_yet" and not offline:
            rec["candidates"] = discover_candidates(book, pool, budget)
        book_recs[key] = rec
        (out / "books" / f"{key}.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")

    resolved = []
    for lead in leads:
        lead["texts"] = []
        for c in lead["citations"]:
            k = c.get("book_key")
            if not k:
                continue
            rec = book_recs.get(k) or {"book_key": k, "status": "not_in_registry" if k not in books else "not_fetched_this_run"}
            res = resolve(lead, c, rec, pages_of.get(k, {}), inv_of.get(k, {}), out / "texts")
            res["year"] = lead["year"]
            resolved.append(res)
            if res["text_file"]:
                lead["texts"].append(res["text_file"])

    routes, hits = live_routes(leads, pool, budget, 0 if offline else max_live, out / "responses", log)

    # ------------------------------------------------------------------ outputs
    write_csv(out / "LEADS.csv", [{**l, "citations": len(l["citations"]), "texts": len(l.get("texts", [])),
                                   "keywords": "|".join(l["keywords"]), "citation_kinds": "|".join(sorted(set(c["kind"] for c in l["citations"])))} for l in leads],
              ["lead_id", "origin", "year", "date", "date_precision", "lord_page", "summary", "citations", "citation_kinds", "texts", "keywords", "known_primary_url", "lord_scan_url", "inclusion_state"])
    write_csv(out / "CITATIONS.csv", citations, ["lead_id", "year", "kind", "raw", "book_key", "section", "volume", "appendix", "page", "page_end", "congress", "session", "column", "series", "chamber", "number", "title", "issue", "route", "route_note"])
    write_csv(out / "RESOLVED.csv", resolved, ["lead_id", "year", "book_key", "citation", "section", "printed_page", "image", "grade", "keyword_hits", "text_file", "excerpt_sha256", "note"])
    write_csv(out / "BOOKS.csv", [{**{k: v for k, v in r.items() if k not in ("custody", "edition", "page_map", "candidates")},
                                   "edition_ok": (r.get("edition") or {}).get("edition_ok"), "report_year_found": (r.get("edition") or {}).get("report_year_found"),
                                   "sha1_matches_archive": (r.get("custody") or {}).get("sha1_matches_archive"),
                                   "heads_agree": (r.get("page_map") or {}).get("heads_agree"), "heads_read": (r.get("page_map") or {}).get("heads_read"),
                                   "weight": next((x["weight"] for x in ranking if x["book_key"] == r["book_key"]), 0)}
                                  for r in book_recs.values()],
              ["book_key", "kind", "label", "status", "ia_identifier", "pages", "weight", "edition_ok", "report_year_found", "sha1_matches_archive", "heads_read", "heads_agree", "pages_file", "retrieved_utc", "error"])
    write_csv(out / "LIVE_ROUTES.csv", routes, ["lead_id", "collection", "query", "date_window", "url", "state", "results", "total", "response_file"])
    write_csv(out / "LIVE_HITS.csv", hits, ["lead_id", "collection", "date", "title", "id", "note"])

    grades = collections.Counter(r["grade"] for r in resolved)
    pre1862 = [l for l in leads if l.get("year") and l["year"] < 1862]
    summary = {
        "leads_only": "Nothing is admitted to the census, dated, merged or changed. Every text here is OCR of a printed compilation, a lead for the original_text step, never the signed original. A page hit is not an identity.",
        "legal_cutoff": LEGAL_CUTOFF, "run_utc": now_utc(), "seconds": round(time.time() - t0, 1), "offline": offline,
        "inputs": {"lord_list": lord_src, "lord_scan_leads": s14_src, "curated_candidates": s18_src},
        "leads": {"total": len(leads), "pre_1862": len(pre1862), "with_any_citation": sum(1 for l in leads if l["citations"]),
                  "with_a_book_citation": sum(1 for l in leads if any(c.get("book_key") for c in l["citations"])),
                  "with_text_cut": sum(1 for l in leads if l.get("texts")),
                  "pre_1862_with_text_cut": sum(1 for l in pre1862 if l.get("texts"))},
        "citations": {"total": len(citations), "by_kind": dict(kinds)},
        "books": {"ranked": ranking, "fetched": fetched, "held_in_repo": sum(1 for r in book_recs.values() if r["status"] == "held_in_repo"),
                  "status": {k: r["status"] for k, r in book_recs.items()},
                  "copies_tried": {k: r.get("copies_tried") for k, r in book_recs.items() if len(r.get("copies_tried") or []) > 1},
                  "sha1_mismatches": [k for k, r in book_recs.items() if (r.get("custody") or {}).get("sha1_matches_archive") is False],
                  "edition_not_ok": [k for k, r in book_recs.items() if r.get("edition") and not r["edition"].get("edition_ok")]},
        "resolved": {"citations_against_books": len(resolved), "by_grade": dict(grades), "texts_written": sum(1 for r in resolved if r["text_file"])},
        "live": {"routes": len(routes), "searched": sum(1 for r in routes if r["state"] == "searched"), "catalog_records": len(hits)},
        "requests": {"budget": budget.max_requests, "spent": budget.spent, "refused": budget.refused, "pool_requests": pool.requests,
                     "bytes_downloaded": pool.bytes_downloaded, "cache_hits": pool.cache_hits},
    }
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "REPORT.md").write_text(report_md(summary, book_recs, resolved, leads), encoding="utf-8")
    return summary


def report_md(summary, book_recs, resolved, leads) -> str:
    L = summary["leads"]
    lines = ["# Early orders hunt", "",
             f"Run {summary['run_utc']} ({'offline' if summary['offline'] else 'live'}, {summary['seconds']} s). "
             f"{L['total']} leads from Lord's list and scan ({L['pre_1862']} before 1862); {L['with_a_book_citation']} cite a book this job knows; "
             f"**{L['with_text_cut']} leads now have a printed text cut from a cited page ({L['pre_1862_with_text_cut']} of them before 1862).**", "",
             summary["leads_only"], "", "## Books", "", "| Book | Status | Pages | Edition | Archive sha1 | Heads agree | Unlock weight |", "|---|---|---:|---|---|---|---:|"]
    weights = {r["book_key"]: r["weight"] for r in summary["books"]["ranked"]}
    for k in sorted(book_recs, key=lambda k: -weights.get(k, 0)):
        r = book_recs[k]
        ed = r.get("edition") or {}
        pm = r.get("page_map") or {}
        edtxt = ("ok" if ed.get("edition_ok") else "CHECK") if ed else "-"
        if "report_year_found" in ed:
            edtxt += f"; report year {'found' if ed['report_year_found'] else 'NOT found'}"
        sha = r.get("custody", {}).get("sha1_matches_archive")
        lines.append(f"| {k} | {r['status']} | {r.get('pages', 0)} | {edtxt} | {'match' if sha else ('-' if sha is None else 'MISMATCH')} | "
                     f"{pm.get('heads_agree', '-')}/{pm.get('heads_read', '-')} | {weights.get(k, 0)} |")
    g = summary["resolved"]["by_grade"]
    lines += ["", "## Citations resolved against the books", "",
              "| Grade | Count | Meaning |", "|---|---:|---|",
              f"| page_date_and_subject | {g.get('page_date_and_subject', 0)} | the cited page carries the lead's date and its subject words |",
              f"| page_and_date | {g.get('page_and_date', 0)} | the cited page carries the lead's date |",
              f"| page_and_subject | {g.get('page_and_subject', 0)} | the cited page carries two or more of the lead's subject words |",
              f"| page_only | {g.get('page_only', 0)} | the page was found but neither date nor subject was read on it; the slice is the page head |",
              f"| page_not_mapped | {g.get('page_not_mapped', 0)} | the book is held but that printed page number was not mapped to a scan |",
              f"| book_not_held | {g.get('book_not_held', 0)} | the book was not fetched (budget, no identifier, offline, or failure) |", ""]
    pre = [r for r in resolved if r["text_file"] and (r.get("year") or 9999) < 1862]
    if pre:
        lines += ["## Pre-1862 texts cut this run (first 40)", "", "| Lead | Date | Citation | Grade | File |", "|---|---|---|---|---|"]
        dates = {l["lead_id"]: l["date"] for l in leads}
        for r in sorted(pre, key=lambda r: (dates.get(r["lead_id"], ""), r["lead_id"]))[:40]:
            lines.append(f"| {r['lead_id']} | {dates.get(r['lead_id'], '')} | {r['citation']} | {r['grade']} | {r['text_file']} |")
        lines.append("")
    lines += ["## Live catalog routes", "",
              f"{summary['live']['searched']} of {summary['live']['routes']} Library of Congress collection searches ran; {summary['live']['catalog_records']} catalog records saved in LIVE_HITS.csv. "
              "A record is something to open and read, not a found order; a search with no results proves nothing.", "",
              "## Requests", "", f"Budget {summary['requests']['budget']}, spent {summary['requests']['spent']}, refused {summary['requests']['refused']}; "
              f"{summary['requests']['bytes_downloaded']:,} bytes downloaded, {summary['requests']['cache_hits']} cache hits.", "",
              "## Next", "",
              "- Read each `texts/*.txt` slice against its scan image before relying on it; graded `page_only` slices need the page read by eye.",
              "- Books with status `no_identifier_yet` list Archive candidates in `books/<key>.json`; confirm one is the GPO edition Lord used and put its identifier in `data/BOOKS.json`.",
              "- A fetched Richardson volume's `books/RICH_*_pages.jsonl.gz` is in the shape `jobs/richardson-volumes/data/*_pages.jsonl` expects, so that job can take it with one PROVENANCE entry.",
              "- Nothing here changes the census: identity, signer capacity and inclusion stay with the reviewer."]
    return "\n".join(lines) + "\n"


def print_summary(s: dict):
    L, B, R = s["leads"], s["books"], s["resolved"]
    print(f"Leads {L['total']} ({L['pre_1862']} pre-1862); {L['with_a_book_citation']} cite a known book; texts cut for {L['with_text_cut']} leads ({L['pre_1862_with_text_cut']} pre-1862).")
    print(f"Books fetched {B['fetched']}, held in repo {B['held_in_repo']}; statuses: {B['status']}")
    print(f"Resolved {R['citations_against_books']} citations: {R['by_grade']}")
    print(f"Live: {s['live']}; requests: {s['requests']}")
    print("Leads only: nothing admitted, dated, merged or changed.")
