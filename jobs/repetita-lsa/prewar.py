"""Repetita, part 2: which pre-1997 List of CFR Sections Affected (LSA) and Code of Federal Regulations (CFR) volumes
are full view, and where. No bulk download of volumes. HeinOnline is never touched.

Sources, all documented bulk or API routes that robots.txt permits for this agent:
  * HathiTrust "hathifiles" (https://www.hathitrust.org/hathifiles): the monthly tab-separated catalog of every
    volume with its access status (allow = full view). Streamed, filtered, never stored whole.
  * HathiTrust Bibliographic API (https://catalog.hathitrust.org/api/volumes/...): per-record rights, used as a second
    reading of the hathifile's access column.
  * Internet Archive advancedsearch.php and metadata API, plus one smoke read of an OCR text.

HathiTrust page images and the Data API sit under babel.hathitrust.org/cgi/, which that host's robots.txt disallows
for this agent, so no Hathi volume is read here: the manifest only lists them.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import zlib
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_lib"))
from fetch_pool import FetchError  # noqa: E402

HATHI_LIST = "https://www.hathitrust.org/files/hathifiles/hathi_file_list.json"
BIB_API = "https://catalog.hathitrust.org/api/volumes/brief/recordnumber/{key}.json"
IA_SEARCH = "https://archive.org/advancedsearch.php?"
IA_META = "https://archive.org/metadata/{id}"
IA_TEXT = "https://archive.org/download/{id}/{id}_djvu.txt"
BABEL_PT = "https://babel.hathitrust.org/cgi/pt?id={htid}&seq=1"
LSA_TITLE = re.compile(rb"sections affected|parts affected", re.I)
ANY_TITLE = re.compile(rb"sections affected|parts affected|code of federal regulations|codification of presidential", re.I)
CFR_T3 = re.compile(r"(?i)\btitles?\s*0?3\b(?!\d)|\bv\.\s*3\b|president")
MANIFEST_COLUMNS = ["source", "id", "series", "access", "rights", "title", "description", "year", "oclc", "lccn",
                    "us_gov_doc", "bib_key", "bib_api_rights", "rights_stated", "url"]
HATHI_FIELDS = 26
KEEP_CFR_MAX = 6000


def series_of(title: str) -> str:
    t = title.lower()
    if re.search(r"sections affected|parts affected", t):
        return "lsa"
    if "codification of presidential" in t:
        return "codification"
    if "code of federal regulations" in t:
        return "cfr"
    return ""


def year_of(*cands) -> int | None:
    for c in cands:
        m = re.search(r"\b(1[89]\d\d|20\d\d)\b", str(c or ""))
        if m:
            return int(m.group(1))
    return None


def open_stream(url, ua, timeout=180):
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    return urllib.request.urlopen(req, timeout=timeout)


def scan_hathifile(opener, url, ua, log=print):
    """Stream the gzipped hathifile, keep the matching rows. Returns (rows, stats). opener(url, ua) -> file-like."""
    h = hashlib.sha256()
    nbytes = 0
    stats = Counter()
    rows = []
    cfr_kept = 0
    dec = zlib.decompressobj(31)
    tail = b""
    resp = opener(url, ua)
    status = getattr(resp, "status", 200)
    if status != 200:
        raise FetchError(f"hathifile HTTP {status}")
    first = True
    while True:
        chunk = resp.read(1 << 20)
        if not chunk:
            break
        h.update(chunk)
        nbytes += len(chunk)
        data = tail + dec.decompress(chunk)
        parts = data.split(b"\n")
        tail = parts.pop()
        for line in parts:
            stats["lines"] += 1
            if first:
                f = line.split(b"\t")
                if len(f) != HATHI_FIELDS or f[1] not in (b"allow", b"deny"):
                    raise FetchError("hathifile layout not the documented 26 fields")
                first = False
            if not ANY_TITLE.search(line):
                continue
            f = line.decode("utf-8", "replace").split("\t")
            if len(f) < 20:
                stats["malformed"] += 1
                continue
            title = f[11]
            s = series_of(title)
            if not s:
                continue
            desc = f[4]
            year = year_of(f[16], desc, f[12])
            if year is not None and year >= 1997:
                stats["year_1997_or_later"] += 1
                continue
            row = {"source": "hathitrust", "id": f[0], "series": s, "access": f[1], "rights": f[2],
                   "title": title[:200], "description": desc[:120], "year": year or "", "oclc": f[7][:40],
                   "lccn": f[10][:30], "us_gov_doc": f[15], "bib_key": f[3], "bib_api_rights": "",
                   "rights_stated": "", "url": "https://babel.hathitrust.org/cgi/pt?id=" + urllib.parse.quote(f[0])}
            stats[f"{s}_volumes"] += 1
            if f[1] == "allow":
                stats[f"{s}_full_view"] += 1
            if s == "cfr":
                # CFR volumes are numerous: list full-view volumes that read as Title 3 or the President; count the rest.
                if f[1] == "allow" and CFR_T3.search(desc + " " + title) and cfr_kept < KEEP_CFR_MAX:
                    cfr_kept += 1
                    rows.append(row)
                continue
            rows.append(row)
    tail_data = tail + dec.flush()
    stats["lines"] += 1 if tail_data.strip() else 0
    stats["bytes"] = nbytes
    stats["sha256"] = h.hexdigest()
    return rows, dict(stats)


def hathi_bib_check(pool, rows, limit=20):
    """Second reading of access: the Bibliographic API's rights string for each distinct LSA/codification record."""
    keys = []
    for r in rows:
        if r["series"] in ("lsa", "codification") and r["bib_key"] not in keys:
            keys.append(r["bib_key"])
    out = {"checked": 0, "failed": 0, "agree": 0, "disagree": 0, "records": {}}
    for k in keys[:limit]:
        try:
            body = pool.fetch(BIB_API.format(key=k))["body"]
            d = json.loads(body.decode("utf-8", "replace"))
        except Exception as e:  # noqa: BLE001
            out["failed"] += 1
            out["records"][k] = f"{type(e).__name__}: {e}"[:120]
            continue
        out["checked"] += 1
        items = (d.get("items") or []) if isinstance(d, dict) else []
        rights = {i.get("htid"): i.get("usRightsString", "") for i in items if isinstance(i, dict)}
        out["records"][k] = {"items": len(rights), "full_view": sum(1 for v in rights.values() if v.lower().startswith("full"))}
        for r in rows:
            if r["bib_key"] == k and r["id"] in rights:
                r["bib_api_rights"] = rights[r["id"]]
                full_api = rights[r["id"]].lower().startswith("full")
                if full_api == (r["access"] == "allow"):
                    out["agree"] += 1
                else:
                    out["disagree"] += 1
    return out


def ia_search(pool, query, pages=3, rows=200):
    out = []
    for page in range(1, pages + 1):
        params = [("q", query), ("rows", rows), ("page", page), ("output", "json")]
        params += [("fl[]", f) for f in ("identifier", "title", "date", "publisher", "creator", "mediatype", "licenseurl",
                                        "rights", "year")]
        url = IA_SEARCH + urllib.parse.urlencode(params)
        d = json.loads(pool.fetch(url)["body"].decode("utf-8", "replace"))
        docs = d.get("response", {}).get("docs", [])
        out += docs
        if len(docs) < rows:
            break
    return out


IA_QUERIES = [
    'title:("sections affected") AND (title:CFR OR title:"Code of Federal Regulations")',
    'title:("CFR parts affected")',
    'title:("codification of presidential proclamations")',
    'title:("Code of Federal Regulations") AND (title:"Title 3" OR title:"the President")',
    'title:("parts affected") AND title:("Federal Register")',
]


def ia_manifest(pool, log=print):
    rows, seen, stats = [], set(), {"queries": 0, "failed_queries": 0, "docs": 0}
    for q in IA_QUERIES:
        stats["queries"] += 1
        try:
            docs = ia_search(pool, q)
        except Exception as e:  # noqa: BLE001
            stats["failed_queries"] += 1
            log(f"ia query failed: {type(e).__name__}: {e}"[:200])
            continue
        stats["docs"] += len(docs)
        for d in docs:
            ident = d.get("identifier")
            title = d.get("title") or ""
            if isinstance(title, list):
                title = " ".join(title)
            s = series_of(title)
            if not ident or not s or ident in seen:
                continue
            year = year_of(d.get("year"), d.get("date"), title)
            if year is not None and year >= 1997:
                continue
            seen.add(ident)
            pub = d.get("publisher") or ""
            if isinstance(pub, list):
                pub = "; ".join(pub)
            stated = " ".join(str(d.get(k) or "") for k in ("licenseurl", "rights")).strip()
            rows.append({"source": "internet_archive", "id": ident, "series": s, "access": "open (IA item)", "rights": "",
                         "title": title[:200], "description": ("publisher: " + pub)[:120], "year": year or "",
                         "oclc": "", "lccn": "", "us_gov_doc": "", "bib_key": "", "bib_api_rights": "",
                         "rights_stated": stated[:120], "url": "https://archive.org/details/" + ident})
    return rows, stats


def smoke_read_ia(pool, rows, log=print):
    """Read one IA OCR text end to end: size, sha256, counts. The text itself is not kept."""
    pick = next((r for r in rows if r["series"] == "lsa" and r["source"] == "internet_archive"), None)
    if not pick:
        return {"attempted": False, "reason": "no Internet Archive LSA item listed"}
    ident = pick["id"]
    out = {"attempted": True, "id": ident, "title": pick["title"], "url": IA_TEXT.format(id=ident)}
    try:
        meta = json.loads(pool.fetch(IA_META.format(id=ident))["body"].decode("utf-8", "replace"))
        md = meta.get("metadata", {})
        out["metadata_rights_fields"] = {k: md.get(k) for k in ("licenseurl", "rights", "possible-copyright-status",
                                                              "publisher", "date", "scanningcenter") if md.get(k)}
        out["has_djvu_txt"] = any(f.get("name", "").endswith("_djvu.txt") for f in meta.get("files", []))
        got = pool.fetch(IA_TEXT.format(id=ident))
        text = got["body"].decode("utf-8", "replace")
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        out.update({"ok": True, "final_url": got["final_url"], "bytes": got["bytes"], "sha256": got["sha256"],
                    "nonblank_lines": len(lines),
                    "executive_order_mentions": len(re.findall(r"Executive\s+Order|\bE\.\s?O\.", text)),
                    "title_3_mentions": len(re.findall(r"(?i)\btitle\s+3\b", text)),
                    "first_lines": [ln[:90] for ln in lines[:3]],
                    "note": "Smoke read only. The text layer is OCR of a Readex microprint copy of a GPO publication; "
                            "nothing from it is committed."})
    except Exception as e:  # noqa: BLE001
        out.update({"ok": False, "error": f"{type(e).__name__}: {e}"[:200]})
    return out


def hathi_read_check(pool, rows):
    """Record what robots.txt says about reading a Hathi volume page. Nothing is fetched."""
    pick = next((r for r in rows if r["source"] == "hathitrust" and r["access"] == "allow"
                 and r["series"] in ("lsa", "codification")), None)
    if not pick:
        return {"attempted": False, "reason": "no full-view Hathi LSA or codification volume listed"}
    url = BABEL_PT.format(htid=urllib.parse.quote(pick["id"]))
    try:
        pool.allowed(url)
        return {"attempted": True, "htid": pick["id"], "url": url, "robots": "allowed",
                "note": "allowed by robots.txt but not read: this run lists volumes only"}
    except FetchError as e:
        return {"attempted": True, "htid": pick["id"], "url": url, "robots": str(e),
                "note": "not read. HathiTrust's Data API also needs OAuth credentials the owner has not issued."}


def polite_retry(pool, url, fn, tries=3, wait=30, log=print):
    """Run fn(); if the host answers a robots.txt or page request with a 403 (hathitrust.org sits behind a
    Cloudflare challenge that is answered at random to non-browser clients), forget the cached robots verdict and try
    again after a pause, at most `tries` times. The challenge itself is never answered or evaded."""
    origin = "{0.scheme}://{0.netloc}".format(urllib.parse.urlsplit(url))
    for k in range(tries):
        try:
            return fn()
        except FetchError as e:
            if k == tries - 1 or not ("robots" in str(e) or "403" in str(e)):
                raise
            log(f"{url}: {e}; pausing {wait}s before try {k + 2}")
            pool.robots.pop(origin, None)
            time.sleep(wait)


def build(pool, ua, opener=open_stream, log=print, skip_hathi=False, wait=30):
    """Returns (manifest_rows, summary)."""
    summary = {"hathi": {}, "internet_archive": {}}
    rows = []
    if not skip_hathi:
        try:
            lst = json.loads(polite_retry(pool, HATHI_LIST, lambda: pool.fetch(HATHI_LIST), wait=wait, log=log)["body"].decode("utf-8", "replace"))
            fulls = sorted((e for e in lst if e.get("full")), key=lambda e: e["filename"])
            pick = fulls[-1]
            polite_retry(pool, pick["url"], lambda: pool.allowed(pick["url"]), wait=wait, log=log)
            t0 = time.time()
            last = None
            for attempt in range(3):
                try:
                    hrows, st = scan_hathifile(opener, pick["url"], ua, log)
                    last = None
                    break
                except Exception as e:  # noqa: BLE001
                    last = e
                    log(f"hathifile attempt {attempt + 1} failed: {type(e).__name__}: {e}"[:200])
                    time.sleep(5 * (attempt + 1))
            if last:
                raise last
            st.update({"file": pick["filename"], "url": pick["url"], "listed_size": pick.get("size"),
                       "seconds": round(time.time() - t0, 1)})
            summary["hathi"] = {"scan": st}
            summary["hathi"]["bib_api"] = hathi_bib_check(pool, hrows)
            rows += hrows
        except Exception as e:  # noqa: BLE001
            summary["hathi"] = {"error": f"{type(e).__name__}: {e}"[:300]}
    try:
        irows, ist = ia_manifest(pool, log)
        summary["internet_archive"] = ist
        rows += irows
    except Exception as e:  # noqa: BLE001
        summary["internet_archive"] = {"error": f"{type(e).__name__}: {e}"[:300]}
    rows.sort(key=lambda r: (r["source"], r["series"], str(r["year"]), r["id"]))
    summary["smoke_read_internet_archive"] = smoke_read_ia(pool, rows, log)
    summary["hathi_read_check"] = hathi_read_check(pool, rows)
    by = defaultdict(int)
    for r in rows:
        key = f"{r['source']}:{r['series']}:{'full_view' if r['access'] in ('allow', 'open (IA item)') else 'not_full_view'}"
        by[key] += 1
    summary["manifest_rows"] = len(rows)
    summary["manifest_by_source_series_access"] = dict(sorted(by.items()))
    years = Counter(r["year"] for r in rows if r["series"] == "lsa" and r["access"] in ("allow", "open (IA item)") and r["year"])
    summary["lsa_full_view_years"] = {str(k): v for k, v in sorted(years.items())}
    return rows, summary
