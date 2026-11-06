"""Duodecim: U.S. Code Table IV (Executive Orders) read across editions as a time series. Zero model tokens.

Named for the Twelve Tables (Table IV, "Table of the Executive Orders"). Table IV of the U.S. Code lists the
executive orders that implement general and permanent law as contained in the Code, with the U.S.C. title and
section where each appears (usually a note) and a status column (blank, or "Elim."). Read edition by edition it
shows when an order's listing entered, moved and left the table, and when the "Elim." marker first appears.

Where Table IV is held (verified 2026-11-06, see README.md and SOURCE_COVERAGE.json). Only routes that robots.txt
allows are fetched:
  * the current table, uscode.house.gov/tables/usctable4.html (updated through the 2024 Main Edition, 01/06/2025);
  * the University of North Texas End of Term web archive (webarchive.library.unt.edu), collection eot2012, read
    in "id_" mode (the original bytes, stable hash);
  * the Internet Archive's Wayback Machine, through its CDX listing (offline on 2026-11-06; the code path is
    exercised only by offline tests until it answers).
NOT fetched: webharvest.gov (its robots.txt disallows /congress*/ replay paths, eight end-of-term captures exist and
need an owner decision); the Library of Congress scans (pending owner decision: Hein terms); HathiTrust (robots
disallow /cgi/); govinfo's USCODE collection holds titles only, no Tables volume.

An "Elim." marker is a lead about the Code's editorial classification, not proof that an order ceased.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import html
import io
import json
import os
import re
import sys
import time
import urllib.parse
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
JOBS = HERE.parent
sys.path.insert(0, str(JOBS / "_lib"))
from fetch_pool import FetchPool, FetchError  # noqa: E402

JOB = "duodecim-tableiv"
UA = "EO-Road-System/1.0 (Duodecim Table IV; owner-run research)"
LIVE_URL = "https://uscode.house.gov/tables/usctable4.html"
ORIGINALS = ("http://uscode.house.gov/tables/usctable4.htm", "https://uscode.house.gov/tables/usctable4.htm")
WEBHARVEST_ROBOTS = "https://webharvest.gov/robots.txt"
UNT_COLLECTIONS = ("eot2008", "eot2012", "eot2016", "eot2020", "eot2024")
UNT_TIMEMAP = "https://webarchive.library.unt.edu/{coll}/timemap/json/{orig}"
UNT_REPLAY = "https://webarchive.library.unt.edu/{coll}/{ts}id_/{orig}"
IA_REPLAY = "https://web.archive.org/web/{ts}id_/{orig}"
MAX_IA_CAPTURES = 400
OLRC_ARCHIVE_PROBES = ("https://uscode.house.gov/download/annualhistoricalarchives/XHTML/{y}/{y}uscTable4.htm",
                       "https://uscode.house.gov/download/annualhistoricalarchives/XHTML/{y}/{y}usctable4.htm")
GOVINFO_SITEMAP = "https://www.govinfo.gov/sitemap/USCODE_sitemap_index.xml"
GOVINFO_YEAR = "https://www.govinfo.gov/sitemap/USCODE_{y}_sitemap.xml"
HATHI_PROBE = "https://babel.hathitrust.org/cgi/pt?id=uc1.31822006433388&seq=7"
IA_CDX = ("https://web.archive.org/cdx/search/cdx?url=uscode.house.gov/tables/usctable4.htm&output=json"
          "&fl=timestamp,original,mimetype,statuscode,digest&filter=statuscode:200&collapse=digest&limit=400")
CURRENT_LAW = "jobs/current-law/output"
UNIVERSE = "research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv"

MAX_TOTAL = 20 * 2 ** 20
MAX_FILE = 5 * 2 ** 20
SHARD = int(4.5 * 2 ** 20)
MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7, "aug": 8,
          "sept": 9, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8}
LABEL_RE = re.compile(r"[Uu]pdated\s+through\s+the\s+(\d{4})\s+(?:Main\s+)?Edition(?:\s*,?\s*(?:and\s+)?Supplement\s+"
                      r"([IVX]+))?\s*\((\d{1,2})/(\d{1,2})/(\d{4})\)")

ROW_FIELDS = ["edition_id", "row_index", "year", "month", "day", "date_partial", "eo_number", "eo_number_carried",
              "instrument_id", "title", "section", "section_kind", "status_text", "elim", "row_span", "flags"]
ROW_COLUMNS_NOTE = ("row_span is start-end byte offsets of the row's <tr>..</td> markup in the exact bytes whose "
                    "sha256 is the edition's source record (SOURCES.jsonl)")

EDITION_FIELDS = ["edition_id", "edition_label", "edition_date", "source", "captured_at", "capture_url",
                  "sha256", "bytes", "rows", "distinct_eos", "elim_rows", "duplicate_captures", "carried_forward"]


class BudgetError(RuntimeError):
    pass


def now_utc():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


# ---------------------------------------------------------------------------------------------- budget ----------

class Budget:
    """Counts bytes before writing; refuses a file over 5 MiB or a total over 20 MiB."""

    def __init__(self, out: Path, total=None, per_file=None):
        self.out, self.total_cap, self.file_cap = out, total or MAX_TOTAL, per_file or MAX_FILE
        self.files = {}

    def total(self):
        return sum(self.files.values())

    def write(self, name, data: bytes):
        if len(data) > self.file_cap:
            raise BudgetError(f"{name}: {len(data)} bytes is over the per-file cap {self.file_cap}")
        if self.total() - self.files.get(name, 0) + len(data) > self.total_cap:
            raise BudgetError(f"{name}: would take committed output over {self.total_cap} bytes")
        path = self.out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        self.files[name] = len(data)

    def write_sharded(self, stem, ext, lines, header=None):
        """Write text lines in shards of at most SHARD bytes: stem+ext, stem_2+ext, ... Returns the file names."""
        names, buf, size, n = [], [], 0, 1
        head = (header or "")
        for line in lines:
            b = len(line.encode("utf-8"))
            if buf and size + b + len(head.encode("utf-8")) > SHARD:
                names.append(self._flush(stem, ext, n, head, buf))
                buf, size, n = [], 0, n + 1
            buf.append(line)
            size += b
        if buf or not names:
            names.append(self._flush(stem, ext, n, head, buf))
        return names

    def _flush(self, stem, ext, n, head, buf):
        name = f"{stem}{ext}" if n == 1 else f"{stem}_{n}{ext}"
        self.write(name, (head + "".join(buf)).encode("utf-8"))
        return name

    def report(self):
        return {"total_bytes": self.total(), "max_file_bytes": max(self.files.values() or [0]),
                "caps": {"total": self.total_cap, "per_file": self.file_cap}, "files": dict(sorted(self.files.items()))}


def csv_text(fields, rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fields, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def csv_lines(fields, rows):
    """(header, lines) for write_sharded."""
    head = csv_text(fields, [])
    out = []
    for r in rows:
        buf = io.StringIO()
        csv.DictWriter(buf, fields, lineterminator="\n", extrasaction="ignore").writerow(r)
        out.append(buf.getvalue())
    return head, out


def jsonl_lines(rows):
    return [json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows]


# ------------------------------------------------------------------------------------------------ network ---------

def robots_rules(text, ua):
    """Allow/Disallow rules that apply to `ua` from a robots.txt body, with the `*` and `$` wildcards that the
    standard library's urllib.robotparser does not understand (webharvest.gov's rules use them). The group naming
    the agent's product token wins over `*`. Returns [(allow, pattern)]."""
    token = ua.split("/")[0].split()[0].lower()
    groups, cur, seen_rule = [], None, False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        k, v = (x.strip() for x in line.split(":", 1))
        k = k.lower()
        if k == "user-agent":
            if cur is None or seen_rule:
                cur, seen_rule = {"agents": [], "rules": []}, False
                groups.append(cur)
            cur["agents"].append(v.lower())
        elif k in ("allow", "disallow") and cur is not None:
            seen_rule = True
            if v:
                cur["rules"].append((k == "allow", v))
    named = [g for g in groups if any(a and a != "*" and a in token for a in g["agents"])]
    star = [g for g in groups if "*" in g["agents"]]
    return [r for g in (named or star) for r in g["rules"]]


def _rule_regex(pattern):
    out = "".join(".*" if c == "*" else re.escape(c) for c in pattern.rstrip("$"))
    return re.compile(out + ("$" if pattern.endswith("$") else ""))


def robots_allows(rules, path):
    """Longest matching rule wins; Allow wins a tie; no matching rule allows."""
    best = None
    for allow, pat in rules:
        if _rule_regex(pat).match(path):
            key = (len(pat), allow)
            if best is None or key > best[0]:
                best = (key, allow)
    return True if best is None else best[1]


class Fetcher:
    """One FetchPool per host (robots.txt, per-host pacing, cache). Every request is logged. A request is `core`
    (an item the job must hold), `optional` (an archive capture: its failure is recorded, and carried forward if
    held before, but cannot fail the run) or a `probe` (a coverage check whose 404 is a finding, not a failure).
    Every URL is checked against robots.txt twice: by FetchPool and by robots_allows() above, because the
    standard library ignores wildcards."""

    def __init__(self, cache: Path, transport=None, intervals=None, sleep=time.sleep, retries=4, backoff=30.0):
        self.cache, self.transport, self.sleep = Path(cache), transport, sleep
        self.retries, self.backoff = retries, backoff
        self.intervals = {"webharvest.gov": 10.0, "uscode.house.gov": 1.0, "www.govinfo.gov": 0.5,
                          "babel.hathitrust.org": 1.0, "web.archive.org": 5.0, "webarchive.library.unt.edu": 6.0}
        self.robots_cache = {}
        self.intervals.update(intervals or {})
        self.pools, self.log = {}, []
        self.times_path = self.cache / "retrieved_times.json"
        try:
            self.times = json.loads(self.times_path.read_text()) if self.times_path.is_file() else {}
        except (OSError, ValueError):
            self.times = {}

    def pool(self, host):
        if host not in self.pools:
            self.pools[host] = FetchPool(self.cache / host, workers=1, per_host=1, transport=self.transport,
                                         max_bytes=60_000_000, timeout=90, user_agent=UA,
                                         min_interval=self.intervals.get(host, 1.0), max_cache_bytes=2 * 1024 ** 3)
        return self.pools[host]

    def wildcard_guard(self, url):
        """(allowed, why). Fetches robots.txt once per host through the pool (cached, paced)."""
        sp = urllib.parse.urlsplit(url)
        origin = f"{sp.scheme}://{sp.netloc}"
        if origin not in self.robots_cache:
            pool = self.pool(sp.hostname)
            try:
                status, _h, body = pool.request(origin + "/robots.txt")
                raw = body.read()
                body.close()
            except Exception as e:
                return False, f"robots.txt unreadable: {type(e).__name__}"
            if status == 200:
                self.robots_cache[origin] = robots_rules(raw.decode("utf-8", "replace"), UA)
            elif status in (404, 410):
                self.robots_cache[origin] = []
            elif status in (401, 403):
                self.robots_cache[origin] = [(False, "/")]
            else:
                return False, f"robots.txt HTTP {status}"
        path = sp.path + (("?" + sp.query) if sp.query else "")
        if not robots_allows(self.robots_cache[origin], path):
            return False, "blocked_by_robots_txt (wildcard-aware check)"
        return True, ""

    def get(self, url, kind="core"):
        """-> dict(url, status, headers, raw, sha256, retrieved_utc, error). Never raises."""
        host = urllib.parse.urlsplit(url).hostname
        pool = self.pool(host)
        res = {"url": url, "status": 0, "headers": {}, "raw": b"", "sha256": "", "error": "", "kind": kind}
        ok, why = self.wildcard_guard(url)
        if not ok:
            res.update(error=why, retrieved_utc=now_utc())
            self.log.append({"url": url, "kind": kind, "status": 0, "bytes": 0, "sha256": "", "error": why,
                             "at": res["retrieved_utc"], "blocked": True})
            return res
        for attempt in range(1, self.retries + 1):
            hits = pool.cache_hits
            try:
                status, headers, body = pool.request(url)
                try:
                    raw = body.read()
                finally:
                    body.close()
            except FetchError as e:
                res["error"] = str(e)
                if "blocked_by_robots" in str(e):
                    break  # never retried: the site says no
                status, headers, raw = 0, {}, b""
            except Exception as e:  # network trouble: retry
                res["error"] = f"{type(e).__name__}: {e}"[:200]
                status, headers, raw = 0, {}, b""
            res.update(status=status, headers=headers, raw=raw)
            if status == 200:
                res["error"] = ""
                res["sha256"] = sha256(raw)
                key = sha256(url.encode())
                if pool.cache_hits > hits and key in self.times:
                    res["retrieved_utc"] = self.times[key]
                else:
                    res["retrieved_utc"] = self.times[key] = now_utc()
                break
            if status in (429, 500, 502, 503, 504, 0) and attempt < self.retries:
                self.sleep(self.backoff * attempt)
                continue
            if status and status != 200:
                res["error"] = f"HTTP {status}"
            break
        res.setdefault("retrieved_utc", now_utc())
        self.log.append({"url": url, "kind": kind, "status": res["status"], "bytes": len(res["raw"]),
                         "sha256": res["sha256"], "error": res["error"], "at": res["retrieved_utc"]})
        return res

    def robots_allowed(self, url):
        ok, why = self.wildcard_guard(url)
        return ok, why

    def save_times(self):
        try:
            self.times_path.parent.mkdir(parents=True, exist_ok=True)
            self.times_path.write_text(json.dumps(self.times))
        except OSError:
            pass

    def counts(self):
        core = [r for r in self.log if r["kind"] == "core"]
        failed = [r for r in core if r["status"] != 200]
        probes = [r for r in self.log if r["kind"] == "probe"]
        optional = [r for r in self.log if r["kind"] == "optional"]
        # a missing collection or archive page is an answer, not a failure; a server or network error is a failure
        probe_failed = [r for r in probes if r["status"] not in (200, 404)]
        return {"requests": len(self.log), "core": len(core), "core_failed": len(failed), "probes": len(probes),
                "probe_failed": len(probe_failed), "optional": len(optional),
                "optional_failed": len([r for r in optional if r["status"] != 200]),
                "failed_total": len(failed) + len(probe_failed)}


# ------------------------------------------------------------------------------------------------- parsing --------

def parse_label(text):
    m = LABEL_RE.search(text)
    if not m:
        return None
    year, supp, mo, da, yr = m.groups()
    date = f"{int(yr):04d}-{int(mo):02d}-{int(da):02d}"
    sid = ("+S" + supp) if supp else ""
    return {"label": re.sub(r"\s+", " ", m.group(0)), "main_year": int(year), "supplement": supp or "",
            "date": date, "edition_id": f"USC{year}{sid}@{date}"}


def section_kind(section):
    s = section.strip()
    if re.search(r"\bnts?\.?$", s) and not s.startswith("nt. prec") and not s.startswith("nts. prec"):
        return "note"
    if s.startswith(("nt. prec", "nts. prec")):
        return "note_preceding"
    if s.startswith("see "):
        return "see"
    if not s:
        return "empty"
    return "section_text"


def _cells(body):
    return [html.unescape(re.sub(r"<[^>]+>", "", c)).replace("\xa0", " ").strip()
            for c in re.findall(r"<td[^>]*>(.*?)</td>", body, re.S | re.I)]


def parse_table(raw: bytes):
    """Parse one Table IV page. Offsets are byte offsets (the page is read as latin-1 so characters = bytes).
    Tolerates rows without </tr>, single or double quotes, and the Wayback-style prefix/suffix."""
    text = raw.decode("latin-1")
    label = parse_label(re.sub(r"<[^>]+>", " ", text))
    legend = " ".join(html.unescape(re.sub(r"<[^>]+>", "", m)).strip()
                      for m in re.findall(r"class=[\"']tabledefinition[\"'][^>]*>(.*?)</p>", text, re.S))
    start = text.find("TABLE IV")
    if start < 0:
        return {"ok": False, "error": "no TABLE IV heading", "label": label, "rows": []}
    end_tbl = text.find("</table>", start)
    end_tbl = len(text) if end_tbl < 0 else end_tbl
    year = mon = day = None
    last_eo = None
    rows, bad, year_headers = [], 0, 0
    tr = [m for m in re.finditer(r"<tr\b([^>]*)>", text[:end_tbl]) if m.start() > start]
    for i, m in enumerate(tr):
        seg_end = tr[i + 1].start() if i + 1 < len(tr) else end_tbl
        body = text[m.end():seg_end]
        attrs = m.group(1).replace("'", '"')
        if 'class="year"' in body.replace("'", '"'):
            y = re.search(r">\s*(\d{4})\s*<", body)
            year, mon, day, year_headers = (y.group(1) if y else None), None, None, year_headers + 1
            continue
        if "usctable4row" not in attrs:
            continue
        last_td = body.rfind("</td>")
        span_end = m.end() + last_td + 5 if last_td >= 0 else seg_end
        cells = _cells(body)
        flags = []
        if len(cells) != 6:
            bad += 1
            rows.append({"span": (m.start(), span_end), "cells": cells, "malformed": True})
            continue
        if cells[0]:
            mon = cells[0]
        if cells[1]:
            day = cells[1]
        eo = cells[2]
        carried = False
        if eo:
            last_eo = eo
        else:
            eo, carried = (last_eo or ""), True
        if not eo:
            flags.append("no_eo_number")
        if not cells[4]:
            flags.append("empty_section")
        if not cells[3]:
            flags.append("empty_title")
        if not mon or not day:
            flags.append("date_incomplete")
        mnum = MONTHS.get((mon or "").lower().rstrip("."))
        partial = "-".join(x for x in (year, f"{mnum:02d}" if mnum else None,
                                        f"{int(day):02d}" if day and day.isdigit() else None) if x)
        status = cells[5]
        rows.append({"year": year or "", "month": mon or "", "day": day or "", "date_partial": partial,
                     "eo_number": eo, "eo_number_carried": carried, "title": cells[3], "section": cells[4],
                     "section_kind": section_kind(cells[4]), "status_text": status,
                     "elim": status.strip().rstrip(".").lower() == "elim", "span": (m.start(), span_end),
                     "flags": "|".join(flags), "malformed": False})
    good = [r for r in rows if not r.get("malformed")]
    # independent counts straight from the bytes, to check the parser
    region = text[start:end_tbl]
    return {"ok": True, "label": label, "legend": legend, "rows": good, "malformed": bad,
            "year_headers": year_headers,
            "raw_row_tags": len(re.findall(r"usctable4row", region)),
            "raw_elim_cells": len(re.findall(r"<td[^>]*>\s*Elim\.\s*</td>", region)),
            "parsed_elim": sum(1 for r in good if r["elim"]),
            "non_ascii_bytes_in_rows": sum(1 for b in raw[start:end_tbl] if b > 127),
            "table_start": start, "table_end": end_tbl}


# ------------------------------------------------------------------------------------------ identity / notes -----

def load_universe(repo: Path):
    path = repo / UNIVERSE
    if not path.is_file():
        raise FileNotFoundError(f"missing census {UNIVERSE}; list research/stage15/CENSUS in needs.txt")
    csv.field_size_limit(min(2 ** 31 - 1, 10 ** 9))
    with open(path, newline="", encoding="utf-8") as fh:
        ids = {r.get("id") or r.get("instrument_id") for r in csv.DictReader(fh)}
    ids.discard(None)
    if not ids:
        raise ValueError("empty census")
    return ids


def map_eo(universe, number):
    m = re.fullmatch(r"(\d{1,5})([A-Za-z]?)", number or "")
    if not m:
        return ""
    base, suf = m.groups()
    for cand in ([f"EO:{base}{suf.upper()}", f"EO:{base}{suf.lower()}"] if suf else [f"EO:{base}"]):
        if cand in universe:
            return cand
    return ""


def _norm_sec(s):
    return re.sub(r"\s+", " ", s.replace("–", "-").replace("—", "-")).strip()


def load_current_law_notes(repo: Path):
    """Printed executive-order notes held by jobs/current-law (read, not duplicated): eo number -> notes."""
    base = repo / CURRENT_LAW
    notes_path = base / "USC_EO_NOTES.jsonl"
    if not notes_path.is_file():
        return None
    by_eo = defaultdict(list)
    with open(notes_path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                n = json.loads(line)
                for s in n.get("subjects") or []:
                    by_eo[s].append(n)
    sources, members = {}, {}
    sp = base / "SOURCES.jsonl"
    if sp.is_file():
        for line in sp.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                sources[r["source_id"]] = {"url": r["url"], "sha256": r["sha256"], "bytes": r.get("bytes")}
    smp = base / "SUMMARY.json"
    if smp.is_file():
        s = json.loads(smp.read_text(encoding="utf-8"))
        for t in (s.get("usc") or {}).get("titles") or []:
            members[t["member"]] = t["sha256"]
        edition = (s.get("usc") or {}).get("label", "")
    else:
        edition = ""
    return {"by_eo": by_eo, "sources": sources, "members": members, "edition": edition}


def note_holding(row, notes):
    """How the current-law job's printed notes relate to a Table IV row of the current edition."""
    if notes is None:
        return {"note_text_held": "current_law_output_missing"}
    kind = row["section_kind"]
    cands = notes["by_eo"].get(row["eo_number"], [])
    want = None
    if kind == "note":
        sec = re.sub(r"\s+nts?\.?$", "", row["section"])
        want = f"{row['title']} U.S.C. {_norm_sec(sec)} note"
    chosen, how = None, ""
    for n in cands:
        if want and _norm_sec(n["citation"]) == want:
            chosen, how = n, "yes_exact_citation"
            break
    if not chosen and cands:
        # same title, any other printed note for this order
        same = [n for n in cands if _norm_sec(n["citation"]).startswith(row["title"] + " U.S.C.")]
        chosen, how = ((same or cands)[0], "yes_other_citation")
    if not chosen:
        return {"note_text_held": "no_printed_note_in_current_law" if kind in ("note", "note_preceding")
                else f"not_a_note_row_{kind}"}
    src = notes["sources"].get(chosen.get("source_id"), {})
    return {"note_text_held": how, "matched_citation": chosen["citation"], "note_id": chosen["note_id"],
            "note_text_sha256": sha256(chosen["text"].encode("utf-8")), "note_text_chars": len(chosen["text"]),
            "member": chosen.get("member", ""), "member_sha256": notes["members"].get(chosen.get("member", ""), ""),
            "current_law_source_url": src.get("url", ""), "current_law_source_sha256": src.get("sha256", ""),
            "current_law_edition": chosen.get("edition") or notes["edition"],
            "text_ref": f"jobs/current-law/output/USC_EO_NOTES.jsonl#note_id={chosen['note_id']}"}


# --------------------------------------------------------------------------------------------- editions ----------

def eo_sort_key(n):
    m = re.fullmatch(r"(\d+)(.*)", n)
    return (int(m.group(1)), m.group(2)) if m else (10 ** 9, n)


class Edition:
    def __init__(self, parsed, raw, capture):
        self.parsed, self.raw, self.capture = parsed, raw, capture
        lab = parsed["label"]
        self.id, self.date, self.label = lab["edition_id"], lab["date"], lab["label"]
        self.rows = parsed["rows"]
        self.sha = sha256(raw)
        self.raw_len = len(raw)
        self.signature = sha256(json.dumps([(r["eo_number"], r["date_partial"], r["title"], r["section"],
                                              r["status_text"]) for r in self.rows]).encode())
        self.duplicates = []
        self.carried = False

    def row_dicts(self, universe):
        out = []
        for i, r in enumerate(self.rows, 1):
            out.append({"edition_id": self.id, "row_index": i, "year": r["year"], "month": r["month"],
                        "day": r["day"], "date_partial": r["date_partial"], "eo_number": r["eo_number"],
                        "eo_number_carried": "yes" if r["eo_number_carried"] else "",
                        "instrument_id": map_eo(universe, r["eo_number"]), "title": r["title"],
                        "section": r["section"], "section_kind": r["section_kind"], "status_text": r["status_text"],
                        "elim": "yes" if r["elim"] else "", "row_span": f"{r['span'][0]}-{r['span'][1]}",
                        "flags": r["flags"]})
        return out


def _json_rows(raw):
    """Rows of a CDX / timemap JSON body as dicts. Accepts a JSON list whose first row is the header (Wayback,
    webharvest) or JSON lines of objects (UNT). Returns [] for anything else (an HTML error page)."""
    text = raw.decode("utf-8", "replace").strip()
    if not text:
        return []
    try:
        data = json.loads(text)
        if isinstance(data, list) and data and isinstance(data[0], list):
            return [dict(zip(data[0], r)) for r in data[1:]]
        if isinstance(data, dict):
            return [data]
        return []
    except ValueError:
        pass
    out = []
    for line in text.splitlines():
        try:
            d = json.loads(line)
        except ValueError:
            return []
        if isinstance(d, dict):
            out.append(d)
    return out


def discover_unt(fetcher, collections=UNT_COLLECTIONS):
    """Captures of Table IV in the UNT End of Term collections, from each collection's timemap. A `warc/revisit`
    row repeats an earlier capture's bytes and is skipped."""
    found, seen = [], set()
    for coll in collections:
        for orig in ORIGINALS:
            res = fetcher.get(UNT_TIMEMAP.format(coll=coll, orig=orig), kind="probe")
            if res["status"] != 200:
                continue
            for d in _json_rows(res["raw"]):
                mime = d.get("mime") or d.get("mimetype") or ""
                status = d.get("status") or d.get("statuscode")
                if str(status) != "200" or "html" not in mime:
                    continue
                key = (coll, d["timestamp"])
                if key in seen:
                    continue
                seen.add(key)
                o = d.get("url") or d.get("original") or orig
                found.append({"route": "unt_end_of_term_id_replay", "collection": coll, "ts": d["timestamp"],
                              "original": o, "digest": d.get("digest", ""),
                              "url": UNT_REPLAY.format(coll=coll, ts=d["timestamp"], orig=o)})
    return sorted(found, key=lambda c: c["ts"])


def discover_ia(fetcher, limit=MAX_IA_CAPTURES):
    """Captures the Wayback Machine lists for Table IV (one per distinct digest). [] when it is offline."""
    res = fetcher.get(IA_CDX, kind="probe")
    if res["status"] != 200:
        return [], res
    rows = [d for d in _json_rows(res["raw"]) if str(d.get("statuscode")) == "200" and "html" in (d.get("mimetype") or "html")]
    rows.sort(key=lambda d: d["timestamp"])
    if len(rows) > limit:  # keep the spread, not just the oldest
        step = len(rows) / limit
        rows = [rows[int(i * step)] for i in range(limit)]
    return [{"route": "internet_archive_id_replay", "collection": "wayback", "ts": d["timestamp"],
             "original": d["original"], "digest": d.get("digest", ""),
             "url": IA_REPLAY.format(ts=d["timestamp"], orig=d["original"])} for d in rows], res


def smoke_pick(captures):
    """Three captures for smoke mode: the oldest, the middle and the live current page."""
    older = captures[:]
    if len(older) <= 2:
        return older
    return [older[0], older[len(older) // 2], older[-1]]


def build_editions(fetcher, captures, prior=None):
    """Fetch and parse each capture. Returns (editions, failures)."""
    editions, failures, by_id = [], [], {}
    for n, cap in enumerate(captures, 1):
        if n % 20 == 0:
            print(f"duodecim: capture {n}/{len(captures)}, {len(editions)} editions held, {len(fetcher.log)} requests", flush=True)
        res = fetcher.get(cap["url"], kind="core" if cap["route"] == "olrc_live_page" else "optional")
        if res["status"] in (301, 302, 303, 307, 308) and cap["route"] == "internet_archive_id_replay":
            # Wayback answers a repeat capture with a redirect to the capture that holds the bytes
            tgt = urllib.parse.urljoin(cap["url"], res["headers"].get("location", ""))
            if urllib.parse.urlsplit(tgt).hostname == "web.archive.org" and "/web/" in tgt:
                res = fetcher.get(tgt, kind="optional")
                cap = dict(cap, redirected_from=cap["url"], url=tgt)
        fail = None
        if res["status"] != 200:
            fail = res["error"] or f"HTTP {res['status']}"
        else:
            parsed = parse_table(res["raw"])
            if not parsed["ok"] or not parsed["label"] or not parsed["rows"]:
                fail = parsed.get("error") or "label or rows not found"
        if fail:
            carried = (prior or {}).get(cap["url"])
            if carried:
                carried.carried = True
                editions.append(carried)
                failures.append({"url": cap["url"], "error": fail, "carried_forward_from_prior_output": True})
            else:
                failures.append({"url": cap["url"], "error": fail, "carried_forward_from_prior_output": False})
            continue
        ed = Edition(parsed, res["raw"], dict(cap, sha256=res["sha256"], bytes=len(res["raw"]),
                                               retrieved_utc=res["retrieved_utc"], headers=res["headers"]))
        prev = by_id.get(ed.id)
        if prev is None:
            by_id[ed.id] = ed
            editions.append(ed)
        elif prev.signature == ed.signature:
            prev.duplicates.append({"url": cap["url"], "sha256": ed.sha, "captured": cap["ts"]})
        else:
            ed.id = f"{ed.id}#{cap['ts']}"
            by_id[ed.id] = ed
            editions.append(ed)
    editions.sort(key=lambda e: (e.date, e.capture.get("ts", "")))
    return editions, failures


# ------------------------------------------------------------------------------------------------ timeseries ----

def loc_text(r):
    return f"{r['title']} U.S.C. {r['section']}".strip()


def timeseries(editions, universe):
    """Per EO number across editions. Returns (rows for TIMESERIES.csv, per-eo detail for fragments)."""
    first_ed = editions[0]
    per = defaultdict(lambda: defaultdict(list))  # eo -> edition_id -> rows
    for ed in editions:
        for i, r in enumerate(ed.rows, 1):
            per[r["eo_number"]][ed.id].append((i, r))
    out, detail = [], {}
    for eo in sorted(per, key=eo_sort_key):
        seq, listed, elim_any, elim_all = [], [], [], []
        changes, events = [], []
        prev_locs, prev_ed, prev_status = None, None, None
        for ed in editions:
            rs = per[eo].get(ed.id)
            if not rs:
                seq.append(f"{ed.date}:-")
                continue
            statuses = {("E" if r["elim"] else "L") for _, r in rs}
            code = "E" if statuses == {"E"} else ("L" if statuses == {"L"} else "M")
            seq.append(f"{ed.date}:{code}")
            listed.append(ed)
            if "E" in statuses:
                elim_any.append(ed)
            if statuses == {"E"}:
                elim_all.append(ed)
            locs = sorted({loc_text(r) for _, r in rs})
            if prev_locs is not None and locs != prev_locs:
                changes.append({"from_edition": prev_ed.date, "to_edition": ed.date, "removed": [x for x in prev_locs if x not in locs],
                                "added": [x for x in locs if x not in prev_locs]})
                events.append({"event_code": "location_changed", "edition": ed, "rows": rs,
                               "removed": [x for x in prev_locs if x not in locs], "added": [x for x in locs if x not in prev_locs]})
            prev_locs, prev_ed, prev_status = locs, ed, code
        gaps = 0
        present = [ed.id in per[eo] for ed in editions]
        for i in range(1, len(present) - 1):
            if not present[i] and any(present[:i]) and any(present[i + 1:]):
                gaps += 1
        first_listed = listed[0] if listed else None
        last_listed = listed[-1] if listed else None
        reverted = False
        seen_e = False
        for ed in editions:
            rs = per[eo].get(ed.id)
            if rs and all(r["elim"] for _, r in rs):
                seen_e = True
            elif rs and seen_e and not any(r["elim"] for _, r in rs):
                reverted = True
        cur = editions[-1]
        row = {
            "eo_number": eo, "instrument_id": map_eo(universe, eo),
            "editions_held": len(editions), "editions_listed": len(listed),
            "first_edition_listed": first_listed.date if first_listed else "",
            "first_listed_is_left_censored": "yes" if first_listed is first_ed else "no",
            "last_edition_listed": last_listed.date if last_listed else "",
            "listed_in_current_edition": "yes" if cur.id in per[eo] else "no",
            "dropped_after_edition": (last_listed.date if last_listed is not cur else "") if last_listed else "",
            "edition_gaps": gaps,
            "first_edition_with_elim_row": elim_any[0].date if elim_any else "",
            "first_edition_all_rows_elim": elim_all[0].date if elim_all else "",
            "elim_present_at_first_listing": "yes" if (elim_any and first_listed is elim_any[0]) else "no",
            "elim_in_current_edition": ("all" if (cur.id in per[eo] and all(r["elim"] for _, r in per[eo][cur.id]))
                                         else "some" if (cur.id in per[eo] and any(r["elim"] for _, r in per[eo][cur.id]))
                                         else "none" if cur.id in per[eo] else "absent"),
            "elim_then_not_elim": "yes" if reverted else "no",
            "location_changes": len(changes),
            "location_change_detail": json.dumps(changes, ensure_ascii=False) if changes else "",
            "status_sequence": ";".join(seq),
        }
        out.append(row)
        detail[eo] = {"row": row, "events": events, "per": per[eo], "first_listed": first_listed,
                      "last_listed": last_listed, "elim_first": elim_any[0] if elim_any else None}
    return out, detail


TS_FIELDS = ["eo_number", "instrument_id", "editions_held", "editions_listed", "first_edition_listed",
             "first_listed_is_left_censored", "last_edition_listed", "listed_in_current_edition",
             "dropped_after_edition", "edition_gaps", "first_edition_with_elim_row", "first_edition_all_rows_elim",
             "elim_present_at_first_listing", "elim_in_current_edition", "elim_then_not_elim", "location_changes",
             "location_change_detail", "status_sequence"]


# ------------------------------------------------------------------------------------------------- controls ------

# Read by hand from the held pages (raw HTML grep, independent of the parser): the current OLRC page and the UNT
# End of Term capture of 2012-11-07 (table updated through 2012-01-03), 2026-11-06. See README.md.
CUR = "current"
CONTROL_POSITIVES = [
    {"id": "P1a", "eo": "703", "edition": CUR, "expect": {"title": "16", "section": "668dd nt", "elim": False},
     "why": "1907 order, listed at 16 U.S.C. 668dd note with a blank status"},
    {"id": "P1b", "eo": "703", "edition": "2012-01-03", "expect": {"title": "16", "section": "668dd nt", "elim": False},
     "why": "the same listing in the 2012-01-03 edition"},
    {"id": "P2a", "eo": "5200", "edition": CUR, "expect": {"title": "7", "section": "452 nt", "elim": True},
     "why": "1929 order, listed with Elim."},
    {"id": "P2b", "eo": "5200", "edition": "2012-01-03", "expect": {"title": "7", "section": "452 nt", "elim": True},
     "why": "already Elim. in the 2012-01-03 edition"},
    {"id": "P3a", "eo": "1216", "edition": "2012-01-03", "expect": {"title": "16", "section": "431 nt", "elim": False},
     "why": "before title 54 was enacted the note was at 16 U.S.C. 431"},
    {"id": "P3d", "eo": "1216", "edition": CUR, "expect": {"title": "54", "section": "320301 nt", "elim": False},
     "why": "now at 54 U.S.C. 320301 note (a section change between the two editions)"},
    {"id": "P4a", "eo": "6237A", "edition": "2012-01-03", "expect": {"title": "50 App.", "section": "12 nt", "elim": False},
     "why": "a letter-suffixed number, listed without Elim. in 2012"},
    {"id": "P4c", "eo": "6237A", "edition": CUR, "expect": {"title": "50 App.", "section": "12 nt", "elim": True},
     "why": "the same row carries Elim. in the current edition (an Elim. transition)"},
    {"id": "P5", "eo": "14132", "edition": CUR, "expect": {"title": "5", "section": "5332 nt", "elim": False},
     "why": "the last row of the current edition (a continuation row with a blank date and carried number cells)"},
]
CONTROL_NEGATIVES = [
    {"id": "N1", "eo": "704", "edition": [CUR, "2012-01-03"], "why": "between listed 703 and 705"},
    {"id": "N2", "eo": "1217", "edition": [CUR, "2012-01-03"], "why": "next number after listed 1216"},
    {"id": "N3", "eo": "5201", "edition": [CUR, "2012-01-03"], "why": "next number after listed 5200"},
    {"id": "N4", "eo": "14999", "edition": ["*"], "why": "beyond the last order listed"},
    {"id": "N5", "eo": "99999", "edition": ["*"], "why": "impossible order number"},
]
ABSENT_CONTROLS = [
    {"id": "A1", "eo": "14132", "edition": "2012-01-03",
     "why": "present in the current edition, absent from the 2012-01-03 edition (which ends at order 13596)"},
]


def run_controls(editions):
    by_date = defaultdict(list)
    for ed in editions:
        by_date[ed.date].append(ed)
    current = [ed for ed in editions if ed.capture.get("route") == "olrc_live_page"]

    def eds_for(spec):
        if spec == CUR:
            return current
        if spec == "*":
            return editions
        return by_date.get(spec, [])

    results, errors, evaluated, skipped = [], 0, 0, 0

    def rows_for(ed, eo):
        return [r for r in ed.rows if r["eo_number"] == eo]

    for c in CONTROL_POSITIVES:
        eds = eds_for(c["edition"])
        if not eds:
            skipped += 1
            results.append({"id": c["id"], "eo": c["eo"], "edition": c["edition"], "result": "not_evaluated",
                            "reason": "edition not held in this run"})
            continue
        for ed in eds:
            rs = rows_for(ed, c["eo"])
            ok = bool(rs) and all(r["title"] == c["expect"]["title"] and r["section"] == c["expect"]["section"]
                                  and r["elim"] == c["expect"]["elim"] for r in rs)
            evaluated += 1
            errors += 0 if ok else 1
            results.append({"id": c["id"], "kind": "positive", "eo": c["eo"], "edition": ed.id,
                            "result": "pass" if ok else "FAIL", "expected": c["expect"],
                            "found": [{"title": r["title"], "section": r["section"], "status": r["status_text"]} for r in rs]})
    for c in CONTROL_NEGATIVES:
        got = {id(ed): ed for spec in c["edition"] for ed in eds_for(spec)}.values()
        if not got:
            skipped += 1
        for ed in got:
            hit = rows_for(ed, c["eo"])
            evaluated += 1
            errors += 1 if hit else 0
            results.append({"id": c["id"], "kind": "negative", "eo": c["eo"], "edition": ed.id,
                            "result": "FAIL" if hit else "pass", "found_rows": len(hit)})
    for c in ABSENT_CONTROLS:
        for ed in eds_for(c["edition"]):
            hit = rows_for(ed, c["eo"])
            evaluated += 1
            errors += 1 if hit else 0
            results.append({"id": c["id"], "kind": "absent_in_edition", "eo": c["eo"], "edition": ed.id,
                            "result": "FAIL" if hit else "pass", "found_rows": len(hit)})
    # the parser against independent counts straight from the bytes
    for ed in editions:
        if ed.carried:
            continue
        p = ed.parsed
        for name, a, b in (("row_tags_equal_parsed_rows", p["raw_row_tags"], len(ed.rows) + p["malformed"]),
                           ("elim_cells_equal_parsed_elim", p["raw_elim_cells"], p["parsed_elim"]),
                           ("no_malformed_rows", 0, p["malformed"])):
            evaluated += 1
            errors += 0 if a == b else 1
            results.append({"id": "S:" + name, "kind": "parser_self_check", "edition": ed.id,
                            "result": "pass" if a == b else "FAIL", "independent": a, "parsed": b})
    return {"evaluated": evaluated, "errors": errors, "not_evaluated_specs": skipped,
            "error_rate": round(errors / evaluated, 6) if evaluated else None,
            "planted_positive_specs": len(CONTROL_POSITIVES), "planted_negative_specs": len(CONTROL_NEGATIVES),
            "results": results}


# ----------------------------------------------------------------------------------------------- coverage -------

WEBHARVEST_SAMPLES = ("/congress112th/20121211232718id_/http://uscode.house.gov/tables/usctable4.htm",
                      "/congress112th/timemap/json/http://uscode.house.gov/tables/usctable4.htm")


def coverage(fetcher, unt_found, ia_found, ia_res, smoke, years=range(2010, 2025), govinfo_years=range(1994, 2025)):
    """Record every place Table IV might be held and what was found. Probes do not count as failures when the page
    is simply absent. Nothing is fetched from webharvest.gov except its robots.txt, and nothing from the Library of
    Congress."""
    cov = {"checked_utc": now_utc(), "sources": {}}
    cov["sources"]["olrc_current_table_iv"] = {"url": LIVE_URL, "covers": "one edition: the current table",
                                               "used": True}
    cov["sources"]["unt_end_of_term"] = {
        "what": "University of North Texas End of Term web archive (LOC/IA/CDL/GPO/UNT crawls), id_ replay",
        "collections_probed": list(UNT_COLLECTIONS), "robots": "generic agents allowed (named AI crawlers are not)",
        "captures_found": [{"collection": c["collection"], "timestamp": c["ts"], "original": c["original"],
                            "cdx_digest": c["digest"]} for c in unt_found], "used": True}
    cov["sources"]["internet_archive_wayback"] = {
        "cdx_url": IA_CDX, "cdx_status": ia_res["status"] if ia_res else None,
        "captures_listed": len(ia_found), "captures_used_cap": MAX_IA_CAPTURES,
        "conclusion": ("captures ingested (up to the cap, one per distinct digest)" if ia_found else
                       "no capture list (offline or error on the probe date); this route is exercised only by "
                       "offline tests until it answers"), "used": bool(ia_found)}
    cov["sources"]["library_of_congress_scans"] = {
        "status": "pending owner decision",
        "why": ("LOC holds U.S. Code editions and supplements 1934-1988, with executive-order tables (1940-1958 "
                "included/repealed/eliminated lists; Table IV or VI 1964-1988). The scans come from HeinOnline, whose "
                "item notices say Hein has not made them available for commercial purposes, including bulk download. "
                "The owner has not decided. This job makes no request to loc.gov. A smoke test of at most 3 items, "
                "slowly, is allowed; its text layer has scrambled columns and would need column-aware parsing or OCR."),
        "requests_made_by_job": 0, "used": False}
    if smoke:
        cov["probes_skipped_in_smoke"] = True
        return cov
    wh = fetcher.get(WEBHARVEST_ROBOTS, kind="probe")
    rules = robots_rules(wh["raw"].decode("utf-8", "replace"), UA) if wh["status"] == 200 else []
    cov["sources"]["webharvest_gov"] = {
        "what": "NARA/GPO end-of-term web harvests of uscode.house.gov (Archive-It replay)",
        "robots_status": wh["status"], "robots_rules_naming_congress": [("Allow: " if a else "Disallow: ") + p for a, p in rules if "congress" in p],
        "replay_and_timemap_paths_allowed": {p: robots_allows(rules, p) for p in WEBHARVEST_SAMPLES} if rules else None,
        "conclusion": ("robots.txt disallows the /congress*/ replay paths for generic agents (a wildcard rule that "
                       "the standard library's robotparser does not apply), so this job does not fetch them. Eight "
                       "end-of-term captures of the table are known to exist (see README); reading them needs an "
                       "owner decision, for example a person fetching them"), "used": False}
    olrc = {}
    for y in years:
        for pat in OLRC_ARCHIVE_PROBES:
            u = pat.format(y=y)
            r = fetcher.get(u, kind="probe")
            olrc[u] = r["status"]
    cov["sources"]["olrc_annual_historical_archives"] = {
        "pattern": OLRC_ARCHIVE_PROBES[0], "years_probed": [min(years), max(years)],
        "http_200": sorted(u for u, s in olrc.items() if s == 200), "http_404": sum(1 for s in olrc.values() if s == 404),
        "other": {u: s for u, s in olrc.items() if s not in (200, 404)},
        "note": "uscode.house.gov was running in a temporary format on 2026-11-06; the archive pages answered 404."}
    gov = {"sitemap_index_status": None, "years": {}, "non_title_packages": []}
    idx = fetcher.get(GOVINFO_SITEMAP, kind="probe")
    gov["sitemap_index_status"] = idx["status"]
    avail = set()
    if idx["status"] == 200:
        avail = {int(m) for m in re.findall(r"USCODE_(\d{4})_sitemap", idx["raw"].decode("utf-8", "replace"))}
    for y in govinfo_years:
        if avail and y not in avail:
            gov["years"][str(y)] = {"in_sitemap_index": False}
            continue
        r = fetcher.get(GOVINFO_YEAR.format(y=y), kind="probe")
        names = re.findall(r"USCODE-\d{4}-([A-Za-z0-9]+)", r["raw"].decode("utf-8", "replace")) if r["status"] == 200 else []
        names = sorted(set(names))
        non_title = [n for n in names if not re.fullmatch(r"title\d+[a-z]?", n)]
        gov["years"][str(y)] = {"status": r["status"], "packages": len(names), "non_title_packages": non_title}
        gov["non_title_packages"] += [f"{y}:{n}" for n in non_title]
    cov["sources"]["govinfo_uscode_collection"] = dict(
        gov, years_with_packages=sorted(int(y) for y, v in gov["years"].items() if v.get("packages")),
        conclusion="titles only; no Tables volume is published in the USCODE collection"
        if not gov["non_title_packages"] else "non-title packages exist; read them", used=False)
    ok, why = fetcher.robots_allowed(HATHI_PROBE)
    cov["sources"]["hathitrust_full_view"] = {
        "probe_url": HATHI_PROBE, "robots_allows_automated_fetch": ok, "robots_reason": why,
        "conclusion": ("not fetched: robots.txt disallows /cgi/ for generic agents, so the page reader is closed to "
                       "this job" if ok is False else "robots allow it; not ingested (no verified record id)"),
        "used": False}
    return cov


# ------------------------------------------------------------------------------------------------- outputs ------

def source_record(ed, notes_edition=""):
    cap = ed.capture
    live = cap.get("route") == "olrc_live_page"
    hdr = cap.get("headers") or {}
    rec = {
        "source_id": f"tableiv:{ed.id}", "instrument_ids": [], "url": cap["url"], "sha256": ed.sha, "bytes": ed.raw_len,
        "content_type": hdr.get("content-type", "text/html"), "retrieved_utc": cap.get("retrieved_utc", ""),
        "route": cap["route"], "page_or_item": f"U.S. Code Table IV (Executive Orders), {ed.label}",
        "text_path": None, "cache_path": None,
        "grade": "secondary_official_table (Office of the Law Revision Counsel, Table IV)",
        "acceptable_as_original": False, "role": "code_table_listing",
        "edition_id": ed.id, "edition_label": ed.label, "edition_date": ed.date,
        "rows_parsed": len(ed.rows),
        "notes": ("OLRC's Table IV as served on the retrieval date. Raw bytes are kept in the runner cache, not "
                  "committed; the sha256 is of those exact bytes and row spans are byte offsets into them. A "
                  "listing here is a lead to where the Code prints a note, not a finding about the order's force."
                  if live else
                  "Archive-It replay in id_ mode (original bytes) of OLRC's Table IV from a NARA/GPO end-of-term "
                  "web harvest. Raw bytes are kept in the runner cache, not committed; the sha256 is of those "
                  "exact bytes and row spans are byte offsets into them. The edition is the table's own "
                  "'updated through' statement, not the capture date."),
    }
    if not live:
        rec.update(capture_timestamp=cap["ts"], original_url=cap["original"], collection=cap.get("collection", ""),
                   archive_orig_last_modified=hdr.get("x-archive-orig-last-modified", ""),
                   cdx_digest=cap.get("digest", ""))
    else:
        rec.update(http_last_modified=hdr.get("last-modified", ""))
    if ed.duplicates:
        rec["duplicate_captures_with_identical_rows"] = ed.duplicates
    return rec


def row_text(r):
    date = " ".join(x for x in (r["month"], r["day"]) if x)
    return f"{r['year']} {date} | EO {r['eo_number']} | {r['title']} U.S.C. {r['section']} | {r['status_text']}".strip(" |")


def current_fragments(cur: Edition, universe, notes, src):
    ref = {"url": src["url"], "sha256": src["sha256"], "page_or_item": src["page_or_item"]}
    frags = {}
    holdings = []
    for i, r in enumerate(cur.rows, 1):
        iid = map_eo(universe, r["eo_number"])
        hold = note_holding(dict(r), notes)
        holdings.append({"eo_number": r["eo_number"], "instrument_id": iid, "title": r["title"], "section": r["section"],
                         "section_kind": r["section_kind"], "status_text": r["status_text"], "table_row_index": i,
                         "table_edition": cur.id, **hold,
                         "edition_gap": "table is updated through " + cur.date + "; the printed notes are from release point "
                                        + (hold.get("current_law_edition") or (notes or {}).get("edition") or "n/a")})
        if not iid or r["elim"]:
            continue
        e = {"system": "usc", "legal_basis_candidate":
             f"U.S. Code Table IV lists this order at {r['title']} U.S.C. {r['section']} ({cur.label})",
             "basis_code": {"note": "table_iv_listed_note", "note_preceding": "table_iv_listed_note_preceding",
                            "see": "table_iv_listed_see_reference"}.get(r["section_kind"], "table_iv_listed_in_section_text"),
             "where": f"USC {loc_text(r)}", "edition": cur.date, "snippet": row_text(r),
             "checked_through": cur.date, "currency_code": "table_iv_edition_date_not_cutoff",
             "mention_id": f"{cur.id}:{i}", "row_span": f"{r['span'][0]}-{r['span'][1]}", "source": ref,
             "note_text_held": {k: v for k, v in hold.items() if k in (
                 "matched_citation", "note_id", "note_text_sha256", "member_sha256", "current_law_source_url",
                 "current_law_source_sha256", "current_law_edition", "text_ref")} | {"status": hold["note_text_held"]}}
        f = frags.setdefault(iid, {"instrument_id": iid, "kind": "current_predicate_candidates", "data": [],
                                   "sources": [ref], "produced_by": JOB,
                                   "confidence_note": ("Table IV lists the order where the Code prints a note or text "
                                                       "implementing it (as of 'checked_through'). An editorial index "
                                                       "lead, not a finding; Elim. rows are not emitted here.")})
        f["data"].append(e)
    return list(frags.values()), holdings


def history_fragments(detail, universe, srcs):
    out = []
    for eo, d in detail.items():
        iid = map_eo(universe, eo)
        if not iid:
            continue
        data, used = [], {}

        def add(code, ed, rows, extra=None):
            ref = srcs[ed.id]
            used[ed.id] = {"source_id": ref["source_id"], "url": ref["url"], "sha256": ref["sha256"],
                           "page_or_item": "Table IV, " + ed.id}
            for idx, r in (rows or [(None, None)])[:3]:
                ent = {"event_code": code, "edition_id": ed.id, "edition_date": ed.date, "source_id": ref["source_id"]}
                if r:
                    ent.update({"where": f"USC {loc_text(r)}", "status_text": r["status_text"], "snippet": row_text(r),
                                "row_span": f"{r['span'][0]}-{r['span'][1]}", "mention_id": f"{ed.id}:{idx}"})
                if extra:
                    ent.update(extra)
                data.append(ent)
        if d["first_listed"]:
            add("first_listed_in_held_editions", d["first_listed"], d["per"][d["first_listed"].id],
                {"left_censored": d["row"]["first_listed_is_left_censored"] == "yes"})
        for ev in d["events"]:
            if ev["event_code"] == "location_changed":
                add("location_changed", ev["edition"], ev["rows"], {"removed": ev["removed"], "added": ev["added"]})
        if d["elim_first"]:
            add("elim_marker_first_seen", d["elim_first"], [x for x in d["per"][d["elim_first"].id] if x[1]["elim"]],
                {"caution": "editorial_classification_lead_not_proof_order_ceased"})
        if d["last_listed"] and d["last_listed"] is not d["first_listed"]:
            add("last_listed_in_held_editions", d["last_listed"], d["per"][d["last_listed"].id])
        out.append({"instrument_id": iid, "kind": "table_iv_history_candidates", "data": data,
                    "sources": list(used.values()), "produced_by": JOB,
                    "confidence_note": ("Table IV rows across held editions: what the table printed, not when the "
                                        "Code changed. Elim. is an editorial marker, a lead and not proof the order "
                                        "ceased. Not an event or a status.")})
    return out


def edition_row(ed):
    return {"edition_id": ed.id, "edition_label": ed.label, "edition_date": ed.date, "source": ed.capture.get("route", ""),
            "captured_at": ed.capture.get("ts", "") or ed.capture.get("retrieved_utc", ""),
            "capture_url": ed.capture["url"], "sha256": ed.sha, "bytes": ed.raw_len, "rows": len(ed.rows),
            "distinct_eos": len({r["eo_number"] for r in ed.rows}), "elim_rows": sum(1 for r in ed.rows if r["elim"]),
            "duplicate_captures": len(ed.duplicates), "carried_forward": "yes" if ed.carried else ""}


def load_prior(prior_dir: Path, captures):
    """Prior output -> {capture url: Edition-like} so an edition whose page cannot be fetched now is carried forward
    (flagged), never silently dropped. Rows and spans come from the prior TABLE_IV_ROWS*.csv."""
    prior = {}
    try:
        with open(prior_dir / "EDITIONS.csv", newline="", encoding="utf-8") as fh:
            eds = list(csv.DictReader(fh))
    except OSError:
        return prior
    rows_by = defaultdict(list)
    for p in sorted(prior_dir.glob("TABLE_IV_ROWS*.csv")):
        with open(p, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                rows_by[r["edition_id"]].append(r)
    for e in eds:
        rs = rows_by.get(e["edition_id"])
        if not rs or not e.get("capture_url"):
            continue
        parsed_rows = []
        for r in rs:
            a, b = r["row_span"].split("-")
            parsed_rows.append({"year": r["year"], "month": r["month"], "day": r["day"], "date_partial": r["date_partial"],
                                "eo_number": r["eo_number"], "eo_number_carried": bool(r["eo_number_carried"]),
                                "title": r["title"], "section": r["section"], "section_kind": r["section_kind"],
                                "status_text": r["status_text"], "elim": r["elim"] == "yes", "span": (int(a), int(b)),
                                "flags": r["flags"], "malformed": False})
        ed = Edition.__new__(Edition)
        ed.parsed = {"label": {"edition_id": e["edition_id"], "date": e["edition_date"], "label": e["edition_label"]},
                     "rows": parsed_rows, "malformed": 0, "raw_row_tags": len(parsed_rows), "raw_elim_cells": 0,
                     "parsed_elim": 0}
        ed.id, ed.date, ed.label, ed.rows = e["edition_id"], e["edition_date"], e["edition_label"], parsed_rows
        ed.raw, ed.sha, ed.signature, ed.duplicates, ed.carried = b"", e["sha256"], "", [], True
        srcs = {}
        sp = prior_dir / "SOURCES.jsonl"
        if sp.is_file():
            for line in sp.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    s = json.loads(line)
                    srcs[s["source_id"]] = s
        s = srcs.get(f"tableiv:{e['edition_id']}", {})
        ed.capture = {"url": e["capture_url"], "route": e["source"], "ts": s.get("capture_timestamp", e.get("captured_at", "")),
                      "original": s.get("original_url", ""), "collection": s.get("collection", ""),
                      "retrieved_utc": s.get("retrieved_utc", ""), "headers": {}, "digest": s.get("cdx_digest", ""),
                      "bytes": int(e["bytes"])}
        ed.raw_len = int(e["bytes"])
        prior[e["capture_url"]] = ed
    return prior


def main(repo: Path, out: Path, cache: Path, transport=None, env=os.environ, sleep=time.sleep, intervals=None):
    out.mkdir(parents=True, exist_ok=True)
    smoke = bool(env.get("JOB_SMOKE")) or (HERE / "SMOKE").is_file()
    t0 = time.monotonic()
    universe = load_universe(repo)
    notes = load_current_law_notes(repo)
    fetcher = Fetcher(cache, transport=transport, intervals=intervals, sleep=sleep,
                      retries=int(env.get("JOB_RETRIES") or 4), backoff=float(env.get("JOB_BACKOFF") or 30))
    live = {"route": "olrc_live_page", "url": LIVE_URL, "ts": "", "original": LIVE_URL, "collection": "", "digest": ""}
    colls = tuple(env["JOB_UNT_COLLECTIONS"].split(",")) if env.get("JOB_UNT_COLLECTIONS") else UNT_COLLECTIONS
    unt_found = discover_unt(fetcher, colls)
    if env.get("JOB_SKIP_IA"):
        ia_found, ia_res = [], None
    else:
        ia_found, ia_res = discover_ia(fetcher, int(env.get("JOB_MAX_IA") or MAX_IA_CAPTURES))
    captures = [live] + unt_found + ia_found
    if smoke:
        captures = smoke_pick(captures)
    prior = load_prior(Path(env.get("JOB_PRIOR_OUTPUT_DIR") or (HERE / "output")), captures)
    editions, failures = build_editions(fetcher, captures, prior)
    min_editions = int(env.get("JOB_MIN_EDITIONS") or (1 if smoke else 2))
    cov = coverage(fetcher, unt_found, ia_found, ia_res, smoke)
    fetcher.save_times()
    found = unt_found + ia_found
    for f in failures:
        print("capture failure:", json.dumps(f), flush=True)
    for r in fetcher.log:
        if r["kind"] == "core" and r["status"] != 200:
            print("core request failed:", json.dumps(r), flush=True)
    problems = []
    if len(editions) < min_editions:
        problems.append(f"only {len(editions)} editions parsed; at least {min_editions} expected")
    counts = fetcher.counts()
    attempted = counts["core"] + counts["probes"]
    if attempted == 0 or counts["failed_total"] * 2 > attempted:
        problems.append(f"most requests failed: {counts['failed_total']} of {attempted}")
    if not editions:
        problems.append("no edition parsed")
        raise SystemExit("; ".join(problems))
    cur = editions[-1]
    if cur.capture.get("route") != "olrc_live_page":
        problems.append("the current Table IV page (uscode.house.gov) is not held in this run")

    budget = Budget(out)
    try:
        return _write_outputs(locals_=dict(
            repo=repo, out=out, smoke=smoke, t0=t0, universe=universe, notes=notes, fetcher=fetcher, found=found,
            editions=editions, failures=failures, cov=cov, problems=problems, counts=counts, cur=cur, budget=budget))
    except BudgetError as e:
        rep = budget.report()
        rep.update(stopped=True, reason=str(e))
        (out / "BUDGET.json").write_text(json.dumps(rep, indent=1) + "\n", encoding="utf-8")
        raise SystemExit(f"budget stop: {e}")


def _write_outputs(locals_):
    g = locals_
    out, smoke, t0, universe, notes = g["out"], g["smoke"], g["t0"], g["universe"], g["notes"]
    fetcher, found, editions, failures = g["fetcher"], g["found"], g["editions"], g["failures"]
    cov, problems, counts, cur, budget = g["cov"], g["problems"], g["counts"], g["cur"], g["budget"]
    srcs = {ed.id: source_record(ed) for ed in editions}
    rows_all = [r for ed in editions for r in ed.row_dicts(universe)]
    head, lines = csv_lines(ROW_FIELDS, rows_all)
    row_files = budget.write_sharded("TABLE_IV_ROWS", ".csv", lines, head)
    ts_rows, detail = timeseries(editions, universe)
    head, lines = csv_lines(TS_FIELDS, ts_rows)
    budget.write_sharded("TIMESERIES", ".csv", lines, head)
    budget.write("EDITIONS.csv", csv_text(EDITION_FIELDS, [edition_row(ed) for ed in editions]).encode("utf-8"))
    cur_frags, holdings = current_fragments(cur, universe, notes, srcs[cur.id])
    hold_fields = ["eo_number", "instrument_id", "title", "section", "section_kind", "status_text", "table_row_index",
                   "table_edition", "note_text_held", "matched_citation", "note_id", "note_text_sha256",
                   "note_text_chars", "member", "member_sha256", "current_law_source_url",
                   "current_law_source_sha256", "current_law_edition", "text_ref", "edition_gap"]
    head, lines = csv_lines(hold_fields, holdings)
    budget.write_sharded("CURRENT_NOTE_HOLDINGS", ".csv", lines, head)
    budget.write_sharded("FRAGMENTS", ".jsonl", jsonl_lines(sorted(cur_frags, key=lambda f: f["instrument_id"])))
    hist = history_fragments(detail, universe, srcs)
    budget.write_sharded("FRAGMENTS_HISTORY", ".jsonl", jsonl_lines(sorted(hist, key=lambda f: f["instrument_id"])))
    budget.write("SOURCES.jsonl", "".join(jsonl_lines([srcs[e.id] for e in editions])).encode("utf-8"))
    budget.write("FETCH_LOG.jsonl", "".join(jsonl_lines(fetcher.log)).encode("utf-8"))
    budget.write("SOURCE_COVERAGE.json", (json.dumps(cov, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))

    controls = run_controls(editions)
    controls["generated_utc"] = now_utc()
    controls["method"] = ("Positives were read by hand from the held pages (raw HTML, not the parser) on 2026-11-06; "
                          "negatives are order numbers absent from every held page; parser self-checks compare the "
                          "parser with independent counts from the bytes. error_rate = FAIL / evaluated.")
    controls["smoke_mode"] = smoke
    if controls["errors"]:
        problems.append(f"controls failed: {controls['errors']} of {controls['evaluated']}")
    budget.write("CONTROLS.json", (json.dumps(controls, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))

    # measured association between Elim. and the printed notes (current edition vs jobs/current-law)
    assoc = Counter()
    for h in holdings:
        if h["section_kind"] == "note":
            assoc[("elim" if h["status_text"] else "listed", "note_held" if h["note_text_held"].startswith("yes") else "no_note")] += 1
    by_src = Counter(ed.capture["route"] for ed in editions)
    elim_eos = {eo for eo, d in detail.items() if d["row"]["first_edition_with_elim_row"]}
    cur_elim = {eo for eo, d in detail.items() if d["row"]["elim_in_current_edition"] in ("all", "some")}
    summary = {
        "job": JOB, "generated_utc": now_utc(), "smoke_mode": smoke, "elapsed_seconds": round(time.monotonic() - t0, 1),
        "editions_parsed": len(editions), "editions_parsed_by_source": dict(by_src),
        "editions": [{"edition_id": e.id, "label": e.label, "date": e.date, "rows": len(e.rows),
                      "distinct_eos": len({r["eo_number"] for r in e.rows}),
                      "elim_rows": sum(1 for r in e.rows if r["elim"]), "source": e.capture["route"],
                      "duplicate_captures": len(e.duplicates), "carried_forward": e.carried} for e in editions],
        "captures_discovered_unt": len([c for c in found if c["route"].startswith("unt")]),
        "captures_discovered_internet_archive": len([c for c in found if c["route"].startswith("internet")]),
        "capture_failures": failures,
        "routes": {"olrc_current": "used", "unt_end_of_term": "used", "internet_archive_wayback":
                   ("used" if any(c["route"].startswith("internet") for c in found) else "offline or empty on this run"),
                   "library_of_congress_scans": "pending owner decision (no request made; Hein terms)",
                   "webharvest_gov": "not fetched: robots.txt disallows /congress*/ replay paths; needs an owner decision",
                   "hathitrust": "not fetched: robots.txt disallows /cgi/",
                   "govinfo_uscode": "titles only; no Tables volume"},
        "eo_rows_total_all_editions": len(rows_all), "eo_rows_current_edition": len(cur.rows),
        "distinct_eos_any_edition": len(detail), "distinct_eos_current_edition": len({r["eo_number"] for r in cur.rows}),
        "eos_with_elim_row_in_any_edition": len(elim_eos), "eos_with_elim_row_in_current_edition": len(cur_elim),
        "eos_elim_first_seen_after_first_listing": sum(
            1 for d in detail.values() if d["row"]["first_edition_with_elim_row"] and d["row"]["elim_present_at_first_listing"] == "no"),
        "eos_elim_then_not_elim": sum(1 for d in detail.values() if d["row"]["elim_then_not_elim"] == "yes"),
        "eos_with_location_change": sum(1 for d in detail.values() if d["row"]["location_changes"]),
        "eos_dropped_from_table": sum(1 for d in detail.values() if d["row"]["dropped_after_edition"]),
        "eos_first_listed_left_censored": sum(1 for d in detail.values() if d["row"]["first_listed_is_left_censored"] == "yes"),
        "eos_not_in_census_universe": sum(1 for d in detail.values() if not d["row"]["instrument_id"]),
        "current_predicate_fragments": len(cur_frags), "history_fragments": len(hist),
        "current_note_holdings": dict(Counter(h["note_text_held"] for h in holdings)),
        "elim_vs_printed_note_current_edition_note_rows": {f"{k[0]}__{k[1]}": v for k, v in sorted(assoc.items())},
        "elim_legend_in_held_pages": sorted({e.parsed.get("legend", "")[:300] for e in editions if not e.carried}),
        "control_error_rate": controls["error_rate"], "controls_evaluated": controls["evaluated"],
        "controls_errors": controls["errors"],
        "requests": counts, "problems": problems,
        "limits": ("Leads only. An Elim. marker is an editorial classification in an index, not proof that an order "
                   "ceased (formal validity, operative force and editorial treatment are separate). A table row is "
                   "not the note's text. No status, census, codebook or count change. Certified: 0."),
    }
    budget.write("SUMMARY.json", (json.dumps(summary, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    rep = budget.report()
    rep["committed_bytes_estimate_with_runner_files"] = rep["total_bytes"] + 4096
    rep["stopped"] = False
    (out / "BUDGET.json").write_text(json.dumps(rep, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("editions_parsed", "editions_parsed_by_source", "eo_rows_total_all_editions",
                                              "distinct_eos_any_edition", "eos_with_elim_row_in_any_edition",
                                              "control_error_rate", "requests", "problems")}, indent=1))
    print("committed bytes", rep["total_bytes"], "max file", rep["max_file_bytes"])
    if problems:
        raise SystemExit("; ".join(problems))
    return summary
