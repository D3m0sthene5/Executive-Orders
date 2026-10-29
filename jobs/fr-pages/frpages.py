"""fr-pages: fetch the exact Federal Register pages that print wanted instruments, so claims can quote them as held.

Input: data/WANTED.jsonl, one wanted instrument per line:
    {"want_id": "...", "plo": 936, "fr": "19 FR 769", "targets": ["EO:7185", ...], "why": "...", "from": "..."}
"fr" may be omitted when "plo" is given: the citation is then taken from jobs/shepard-citations/output/PLO_TABLE.csv.
A bare citation (no "plo", "printed_id" optional) is fetched as a page.

Route, cheapest stable official file first:
  1. the previous run's committed capture and text (JOB_PRIOR_OUTPUT_DIR), re-hashed: no request;
  2. govinfo's link service https://www.govinfo.gov/link/fr/<vol>/<page>, read without following the redirect, which
     names the daily-issue PDF (1936-1993) or the single document's PDF (1994 on) and sometimes a #page= hint;
  3. optional (settings try_issue_slice): archives.federalregister.gov/issue_slice/<y>/<m>/<d>/<p>-<p>.pdf, kept
     only if two downloads give the same sha256 (a slice that is regenerated on request cannot be re-proven);
  4. the PDF the link service named (content/pkg/FR-YYYY-MM-DD/pdf/...), downloaded whole, sha256 kept.
Only the pages holding the instrument are extracted to texts/. The PDF's bytes are committed (captures/<sha>.pdf)
only when it is at most commit_max_bytes; otherwise the record keeps url + sha256 + bytes, which a re-download
re-proves. Every fetch goes through jobs/_lib/fetch_pool.py (robots.txt, pacing, bounded size, sha256 cache).

Outputs: texts/FR_<vol>_<page>.txt, captures/, SOURCES.jsonl (shared source-record format), FAILURES.jsonl,
SUMMARY.json. A located page is a location lead with a confidence label, not an authenticated transcription.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
import os
import re
import shutil
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
JOBS = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(JOBS, "_lib"))
sys.path.insert(0, os.path.join(JOBS, "source-ladder"))
import fetch_pool  # noqa: E402
import fr_pages as L  # noqa: E402  (source-ladder's page locator: printed page numbers, filing lines)

csv.field_size_limit(min(2**31 - 1, 10**9))
USER_AGENT = "EO-afterlife-research/1.0 (fr-pages; bounded research job)"
PLO_TABLE = "jobs/shepard-citations/output/PLO_TABLE.csv"
SHEPARD_EDGES = "jobs/shepard-citations/output/EDGES.csv"
LINK = "https://www.govinfo.gov/link/fr/{vol}/{page}"
SLICE = "https://archives.federalregister.gov/issue_slice/{y}/{m}/{d}/{p}-{p}.pdf"
ISSUE_RE = re.compile(r"/FR-(\d{4})-(\d{2})-(\d{2})/")
FR_CITE = re.compile(r"^\s*(\d{1,3})\s*F\.?\s?R\.?\s*(\d{1,6})\s*$")
MAX_DOC_PAGES = 6
DEFAULTS = {"max_requests": 120, "max_download_bytes": 4_000_000_000, "max_issue_bytes": 450_000_000,
            "commit_max_bytes": 16_000_000, "commit_total_bytes": 200_000_000, "min_interval_seconds": 1.0,
            "try_issue_slice": False, "auto_from_shepard": {"enabled": False, "max_items": 25}}


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_jsonl(path):
    out = []
    if path and os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            for n, line in enumerate(fh, 1):
                line = line.strip()
                if line and not line.startswith("#"):
                    try:
                        out.append(json.loads(line))
                    except ValueError:
                        out.append({"_bad_line": n})
    return out


def load_settings(job_dir):
    s = json.loads(json.dumps(DEFAULTS))
    path = os.path.join(job_dir, "settings.json")
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            s.update({k: v for k, v in json.load(fh).items() if not k.startswith("_")})
    if os.environ.get("JOB_MAX_REQUESTS"):
        s["max_requests"] = int(os.environ["JOB_MAX_REQUESTS"])
    return s


def plo_index(root):
    out = {}
    path = os.path.join(root, PLO_TABLE)
    if os.path.isfile(path):
        with open(path, encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                if r.get("plo_number", "").isdigit():
                    out[int(r["plo_number"])] = r
    return out


def auto_wanted(root, plos, max_items):
    """Wanted PLO pages taken from Shepard's leads: PLOs named as revoking/ending census orders, most targets first."""
    path = os.path.join(root, SHEPARD_EDGES)
    if not os.path.isfile(path):
        return []
    by = {}
    with open(path, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            a = r.get("acting_id", "")
            if a.startswith("PLO:") and a[4:].isdigit() and r.get("target_in_universe") == "yes" and \
                    r.get("mechanism") in ("revocation", "rescission", "supersession", "termination"):
                by.setdefault(int(a[4:]), set()).add(r["target_id"])
    ranked = sorted(by.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    return [{"want_id": f"auto:PLO:{n}", "plo": n, "targets": sorted(t), "why": "Shepard lead: PLO named as ending these orders",
             "from": SHEPARD_EDGES} for n, t in ranked if n in plos and plos[n].get("fr_volume")][:max_items]


def resolve(wanted, plos):
    """(jobs, failures). jobs: one per distinct (vol, page): vol, page, printed_id, plo, targets, want_ids, flags."""
    jobs, failures = {}, []
    for w in wanted:
        if w.get("_bad_line"):
            failures.append({"want_id": f"line {w['_bad_line']}", "reason": "malformed_json"})
            continue
        flags = []
        plo = w.get("plo")
        vol = page = None
        if w.get("fr"):
            m = FR_CITE.match(str(w["fr"]))
            if not m:
                failures.append({"want_id": w.get("want_id"), "reason": "unreadable_fr_citation", "fr": w["fr"]})
                continue
            vol, page = int(m.group(1)), int(m.group(2))
        if plo is not None:
            row = plos.get(int(plo))
            if row and row.get("fr_volume"):
                tv, tp = int(row["fr_volume"]), int(row["fr_page"])
                if vol is None:
                    vol, page = tv, tp
                    flags.append("fr_citation_from_blm_plo_table")
                elif (tv, tp) != (vol, page):
                    flags.append(f"blm_plo_table_cites_{tv}_FR_{tp}")
            elif vol is None:
                failures.append({"want_id": w.get("want_id"), "reason": "plo_not_in_plo_table_and_no_fr_citation",
                                 "plo": plo, "targets": w.get("targets", [])})
                continue
        if vol is None:
            failures.append({"want_id": w.get("want_id"), "reason": "no_fr_citation_and_no_plo"})
            continue
        printed = f"PLO:{int(plo)}" if plo is not None else (w.get("printed_id") or f"FR-PAGE:{vol}-{page}")
        key = (vol, page)
        job = jobs.setdefault(key, {"vol": vol, "page": page, "printed_id": printed, "plo": plo, "targets": [],
                                    "want_ids": [], "flags": [], "why": []})
        if job["printed_id"] != printed:
            job["flags"].append("several_printed_ids_wanted_on_this_page:" + printed)
        job["targets"] = sorted(set(job["targets"]) | set(w.get("targets") or []))
        job["want_ids"].append(w.get("want_id") or f"{printed}@{vol}FR{page}")
        job["flags"] = sorted(set(job["flags"] + flags))
        if w.get("why"):
            job["why"].append(w["why"])
    return [jobs[k] for k in sorted(jobs)], failures


def heading_pattern(job):
    if job.get("plo") is not None:
        return re.compile(r"P\s?u\s?b\s?l\s?i\s?c\s+L\s?a\s?n\s?d\s+O\s?r\s?d\s?e\s?r\s*(?:N\s?o\.?\s*)?"
                          + L.digits_pattern(str(int(job["plo"]))) + r"(?![\d])", re.I)
    pid = job.get("printed_id") or ""
    m = re.match(r"EO:(\d+)", pid)
    if m:
        return re.compile(r"E\s?X\s?E\s?C\s?U\s?T\s?I\s?V\s?E\s+O\s?R\s?D\s?E\s?R\s*(?:N\s?o\.?\s*)?"
                          + L.digits_pattern(m.group(1)) + r"(?![\d])", re.I)
    return None


def locate(page_texts, job, page_hint=None):
    """(first_idx, last_idx, notes, confidence) of the instrument's pages; indexes are 0-based PDF pages."""
    page_map = L.printed_page_map(page_texts)
    idx, how = L.find_printed_page(page_texts, page_map, job["page"])
    notes = [how]
    if idx is None:
        if page_hint and 1 <= page_hint <= len(page_texts) and not page_map:
            idx, how = page_hint - 1, "link_service_page_hint_only"
            notes.append(how)
        else:
            return None, None, notes, "not_found"
    pat = heading_pattern(job)
    start, found = idx, None
    if pat:
        for j in [idx, idx + 1, idx - 1, idx + 2]:
            if 0 <= j < len(page_texts) and pat.search(page_texts[j] or ""):
                found = j
                break
    if found is not None:
        start = found
        m = pat.search(page_texts[found])
        end = None
        for j in range(found, min(len(page_texts), found + MAX_DOC_PAGES)):
            pos = m.end() if j == found else 0
            if L.FILING.search(page_texts[j] or "", pos):
                end = j
                break
        if end is None:
            end = min(len(page_texts) - 1, found + 1)
            notes.append("filing_line_not_found_next_page_included")
        notes.append(f"heading_found_on_pdf_page_{found + 1}")
        conf = "high" if how == "printed_page_number_matched" and "filing_line_not_found_next_page_included" not in notes else "medium"
        return start, end, notes, conf
    notes.append("instrument_heading_not_found_cited_page_and_next_taken" if pat else "no_instrument_number_cited_page_and_next_taken")
    return idx, min(len(page_texts) - 1, idx + 1), notes, ("medium" if how == "printed_page_number_matched" else "low")


def pdf_pages(raw, wanted=None):
    """Text of the PDF's pages: all of them, or only the indexes in `wanted` (others '')."""
    import pypdf
    reader = pypdf.PdfReader(io.BytesIO(raw))
    n = len(reader.pages)
    out = [""] * n
    for i in (range(n) if wanted is None else [i for i in wanted if 0 <= i < n]):
        try:
            out[i] = reader.pages[i].extract_text() or ""
        except Exception as exc:
            out[i] = f"[page text unreadable: {type(exc).__name__}]"
    return out


class Fetcher:
    def __init__(self, cache, settings, transport=None, extract=pdf_pages, log=print):
        self.s = settings
        self.pool = fetch_pool.FetchPool(cache, workers=1, per_host=1, transport=transport,
                                         max_bytes=settings["max_issue_bytes"], user_agent=USER_AGENT,
                                         min_interval=settings["min_interval_seconds"])
        self.extract = extract
        self.log = log
        self.slice_failures = 0

    def budget_left(self):
        return self.pool.requests < self.s["max_requests"] and self.pool.bytes_downloaded < self.s["max_download_bytes"]

    def link(self, vol, page):
        """(target url, page hint, attempt) from the govinfo link service, without downloading the target."""
        url = LINK.format(vol=vol, page=page)
        att = {"url": url, "route": "official/govinfo_link_fr"}
        status, headers, body = self.pool.request(url)
        body.close()
        att["status"] = status
        if status in (301, 302, 303, 307, 308) and headers.get("location"):
            nxt = urllib.parse.urljoin(url, headers["location"])
            m = re.search(r"page=(\d+)", urllib.parse.urlsplit(nxt).fragment or "")
            target = urllib.parse.urldefrag(nxt)[0]
            if not target.startswith("https://www.govinfo.gov/") or "/error" in target:
                att["error"] = "unexpected_redirect:" + target
                return None, None, att
            att["location"] = target
            return target, int(m.group(1)) if m else None, att
        if status == 200:
            return url, None, att
        att["error"] = f"HTTP {status}"
        return None, None, att

    def slice(self, issue_date, page):
        """A stable single-page slice from archives.federalregister.gov, or None."""
        if not self.s.get("try_issue_slice") or self.slice_failures >= 3 or not issue_date:
            return None, {"route": "archives_issue_slice", "skipped": True}
        y, m, d = issue_date.split("-")
        url = SLICE.format(y=int(y), m=int(m), d=int(d), p=page)
        att = {"url": url, "route": "official/archives_issue_slice"}
        try:
            first = self.pool.fetch(url)
            for p in self.pool._paths(url):  # second, uncached download to test that the bytes are stable
                p.unlink(missing_ok=True)
            second = self.pool.fetch(url)
        except Exception as exc:
            self.slice_failures += 1
            att["error"] = f"{type(exc).__name__}: {exc}"
            return None, att
        if not first["body"].startswith(b"%PDF") or first["sha256"] != second["sha256"]:
            self.slice_failures += 1
            att["error"] = "not_a_pdf" if not first["body"].startswith(b"%PDF") else "sha256_differs_between_downloads"
            return None, att
        att["sha256"] = first["sha256"]
        return first, att

    def download(self, url):
        att = {"url": url, "route": "official/govinfo_fr_pdf"}
        got = self.pool.fetch(url)
        if not got["body"].startswith(b"%PDF"):
            raise fetch_pool.FetchError("not a PDF")
        att.update(sha256=got["sha256"], bytes=got["bytes"])
        return got, att


def text_header(job, url, sha, pages_note):
    return (f"Wanted: {', '.join(job['want_ids'])}\nPrinted instrument: {job['printed_id']}\n"
            f"Wanted for: {', '.join(job['targets']) or '(no target named)'}\nSource: {url}\n"
            f"SHA-256 of the downloaded file: {sha}\nLocation: {job['vol']} FR {job['page']}; {pages_note}\n"
            "Machine-extracted text layer (OCR for 1936-1993 scans). Not an authenticated transcription; "
            "it may include parts of neighbouring documents. Check the PDF pages.\n")


def process(job, fetcher, out_dir, prior, committed_bytes, log=print):
    """One wanted page. Returns (source record or None, failure or None, bytes newly committed)."""
    vol, page = job["vol"], job["page"]
    text_rel = f"texts/FR_{vol}_{page}.txt"
    old = prior.get((vol, page))
    if old and not os.environ.get("FR_PAGES_REFRESH"):
        pdir = old["_prior_dir"]
        tsrc = os.path.join(pdir, old.get("text_path", ""))
        ok = os.path.isfile(tsrc)
        cap = os.path.join(pdir, old["cache_path"]) if old.get("cache_path") else None
        if ok and cap:
            with open(cap, "rb") as fh:
                ok = sha256(fh.read()) == old.get("sha256")
        if ok:
            rec = {k: v for k, v in old.items() if k != "_prior_dir"}
            os.makedirs(os.path.join(out_dir, "texts"), exist_ok=True)
            shutil.copyfile(tsrc, os.path.join(out_dir, rec["text_path"]))
            if cap:
                os.makedirs(os.path.join(out_dir, "captures"), exist_ok=True)
                dst = os.path.join(out_dir, rec["cache_path"])
                if not os.path.exists(dst):
                    shutil.copyfile(cap, dst)
            rec["instrument_ids"] = [job["printed_id"]] + [t for t in job["targets"] if t != job["printed_id"]]
            rec["wanted_ids"] = job["want_ids"]
            rec["carried_forward"] = True
            return rec, None, 0
    if not fetcher.budget_left():
        return None, {"want_ids": job["want_ids"], "fr": f"{vol} FR {page}", "reason": "request_or_byte_budget_exhausted",
                      "permanent": False}, 0
    attempts = []
    try:
        target, hint, att = fetcher.link(vol, page)
        attempts.append(att)
        if not target:
            raise fetch_pool.FetchError(att.get("error") or "link service gave no target")
        m = ISSUE_RE.search(target)
        issue_date = "-".join(m.groups()) if m else ""
        got, satt = fetcher.slice(issue_date, page)
        attempts.append(satt)
        route = "official/archives_issue_slice" if got else "official/govinfo_link_fr"
        if got is None:
            got, datt = fetcher.download(target)
            attempts.append(datt)
        raw = got["body"]
        window = range(max(0, hint - 6), hint + 8) if hint else None  # read the hinted pages first
        pages = fetcher.extract(raw, window)
        first, last, notes, conf = locate(pages, job, hint)
        if first is None and window is not None:
            pages = fetcher.extract(raw, None)
            first, last, notes, conf = locate(pages, job, hint)
        if first is None:
            return None, {"want_ids": job["want_ids"], "fr": f"{vol} FR {page}", "url": got["url"], "sha256": got["sha256"],
                          "reason": "printed_page_not_found_in_pdf", "notes": notes, "attempts": attempts, "permanent": False}, 0
    except Exception as exc:
        return None, {"want_ids": job["want_ids"], "fr": f"{vol} FR {page}", "reason": f"{type(exc).__name__}: {exc}",
                      "attempts": attempts, "permanent": False}, 0
    name = urllib.parse.urlsplit(got["url"]).path.rsplit("/", 1)[-1]
    pages_note = f"{name} PDF pages {first + 1}-{last + 1} of {len(pages)}"
    body = text_header(job, got["url"], got["sha256"], pages_note)
    for i in range(first, last + 1):
        body += f"\n=== PDF page {i + 1} of {len(pages)} ===\n{(pages[i] or '').rstrip()}\n"
    os.makedirs(os.path.join(out_dir, "texts"), exist_ok=True)
    with open(os.path.join(out_dir, text_rel), "w", encoding="utf-8") as fh:
        fh.write(body)
    with open(os.path.join(out_dir, text_rel), "rb") as fh:
        text_sha = sha256(fh.read())
    rec = {"url": got["url"], "requested_url": LINK.format(vol=vol, page=page), "sha256": got["sha256"],
           "bytes": got["bytes"], "content_type": "application/pdf", "retrieved_utc": now(), "route": route,
           "text_path": text_rel, "text_sha256": text_sha,
           "page_or_item": f"{vol} FR {page}; {pages_note}",
           "instrument_ids": [job["printed_id"]] + [t for t in job["targets"] if t != job["printed_id"]],
           "printed_instrument_id": job["printed_id"], "wanted_ids": job["want_ids"],
           "fr_volume": vol, "fr_page": page, "location_confidence": conf, "location_notes": notes,
           "needs_page_check": conf != "high", "flags": job["flags"],
           "role": "official_federal_register_page_of_a_later_instrument",
           "note": ("Official Federal Register PDF. instrument_ids lists the printed instrument first, then the orders it "
                    "is wanted for (so the page is never taken as an order's own original text). Not a legal finding.")}
    if hint:
        rec["link_page_hint"] = hint
    added = 0
    if got["bytes"] <= fetcher.s["commit_max_bytes"] and committed_bytes + got["bytes"] <= fetcher.s["commit_total_bytes"]:
        rel = f"captures/{got['sha256']}.pdf"
        dst = os.path.join(out_dir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst):
            with open(dst, "wb") as fh:
                fh.write(got["body"])
            added = got["bytes"]
        rec["cache_path"] = rel
    else:
        rec["custody"] = "record_only: bytes above the commit cap; re-download the url and compare sha256"
    log(f"{vol} FR {page} ({job['printed_id']}): {conf}, {pages_note}, {got['bytes']} bytes"
        + (" committed" if rec.get("cache_path") else " not committed"))
    return rec, None, added


def load_prior(prior_dir):
    out = {}
    for rec in read_jsonl(os.path.join(prior_dir, "SOURCES.jsonl")) if prior_dir else []:
        if rec.get("fr_volume") and rec.get("fr_page"):
            rec["_prior_dir"] = prior_dir
            out[(int(rec["fr_volume"]), int(rec["fr_page"]))] = rec
    return out


def run(root, job_dir, out_dir, cache_dir, prior_dir="", transport=None, extract=pdf_pages, log=print):
    settings = load_settings(job_dir)
    plos = plo_index(root)
    wanted = read_jsonl(os.path.join(job_dir, "data", "WANTED.jsonl"))
    auto = settings.get("auto_from_shepard") or {}
    if auto.get("enabled"):
        wanted += auto_wanted(root, plos, int(auto.get("max_items", 25)))
    jobs, failures = resolve(wanted, plos)
    fetcher = Fetcher(cache_dir, settings, transport=transport, extract=extract, log=log)
    prior = load_prior(prior_dir)
    records, committed = [], 0
    for job in jobs:
        rec, fail, added = process(job, fetcher, out_dir, prior, committed, log)
        committed += added
        if rec:
            records.append(rec)
        if fail:
            failures.append(fail)
    with open(os.path.join(out_dir, "SOURCES.jsonl"), "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    with open(os.path.join(out_dir, "FAILURES.jsonl"), "w", encoding="utf-8") as fh:
        for f in failures:
            fh.write(json.dumps(f, sort_keys=True) + "\n")
    summary = {"job": "fr-pages", "generated_utc": now(), "wanted_lines": len(wanted), "distinct_pages": len(jobs),
               "pages_held": len(records), "carried_forward": sum(1 for r in records if r.get("carried_forward")),
               "committed_pdfs": sum(1 for r in records if r.get("cache_path")),
               "record_only": sum(1 for r in records if not r.get("cache_path")),
               "bytes_committed_this_run": committed,
               "by_confidence": {c: sum(1 for r in records if r.get("location_confidence") == c) for c in ("high", "medium", "low")},
               "failures": len(failures), "requests": fetcher.pool.requests,
               "bytes_downloaded": fetcher.pool.bytes_downloaded, "cache_hits": fetcher.pool.cache_hits,
               "settings": settings, "plo_table_rows_available": len(plos),
               "note": "Location leads with confidence labels; a person checks the PDF pages. No status, count or codebook change."}
    with open(os.path.join(out_dir, "SUMMARY.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return summary
