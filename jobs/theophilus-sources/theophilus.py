"""Theophilus: gather the official sources that keep YES orders operating.

Pure parsing and fetching helpers plus ``run``. No model calls, no status writes.
Every request goes through jobs/_lib/fetch_pool.FetchPool (HTTPS only, robots.txt
obeyed, throttled, hashed). Standard library only.
"""
from __future__ import annotations
import csv, datetime as dt, hashlib, html, http.client, io, json, os, re, sys, time, urllib.parse, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
JOBS = HERE.parent
sys.path.insert(0, str(JOBS / "_lib"))
sys.path.insert(1, str(JOBS / "current-law"))
from fetch_pool import FetchPool, FetchError  # noqa: E402
import eo_refs  # noqa: E402

FR_API = "https://www.federalregister.gov/api/v1/documents.json"
FR_FIELDS = ["document_number", "title", "publication_date", "signing_date", "citation", "pdf_url",
             "raw_text_url", "html_url", "executive_order_notes"]
ECFR_TITLES = "https://www.ecfr.gov/api/versioner/v1/titles.json"
ECFR_FULL = "https://www.ecfr.gov/api/versioner/v1/full/{date}/title-{title}.xml?{query}"
GOVINFO_BULK = "https://www.govinfo.gov/bulkdata/ECFR/title-{title}/ECFR-title{title}.xml"
USC_ZIP = "https://uscode.house.gov/download/releasepoints/us/pl/{congress}/{law}/xml_usc{code}@{rp}.zip"
USC_VIEW = "https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title{t}-section{s}&num=0&edition=prelim"
RATE_TRIES = 7
RATE_PAUSE = 10.0
MAX_PART_TEXT = 6_000_000
MAX_NOTICE = 8_000_000
MAX_BULK = 400_000_000

NOTICE_NOTE = ("Official Federal Register text of a yearly continuation notice. instrument_ids lists census orders whose "
               "number the notice text names. A mention is not a legal finding and not proof that the emergency still "
               "covers that order.")


def now_utc():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


# ------------------------------------------------------------------ inputs --
def load_register(path):
    return {r["instrument_id"] for r in csv.DictReader(open(path, encoding="utf-8", newline=""))}


def split_cites(cell):
    return [c.strip() for c in (cell or "").split(";") if c.strip()]


def parse_citation(cite):
    """-> ('usc', title, section) | ('cfr', title, part, section_or_None) | ('bad', reason)."""
    c = re.sub(r"\s+", " ", cite.replace("–", "-").replace("—", "-").replace("‑", "-")).strip()
    m = re.fullmatch(r"(\d{1,2}) U\.S\.C\. (\d+[A-Za-z]*(?:-\d+[A-Za-z]*)*)(?: note)?", c)
    if m:
        return ("usc", int(m.group(1)), m.group(2))
    m = re.fullmatch(r"(\d{1,2}) CFR part ([0-9A-Za-z-]+)(?:,.*)?", c)
    if m:
        return ("cfr", int(m.group(1)), m.group(2), None)
    m = re.fullmatch(r"(\d{1,2}) CFR (\d[0-9A-Za-z-]*\.[0-9A-Za-z.-]+)", c)
    if m:
        return ("cfr", int(m.group(1)), m.group(2).split(".")[0], m.group(2))
    if "U.S.C." in c:
        return ("bad", "usc_citation_not_a_single_section")
    if "CFR" in c:
        return ("bad", "cfr_citation_form_not_parsed")
    return ("bad", "citation_form_not_parsed")


def eligible_orders(readiness_csv, current_csv):
    """YES orders, readiness row not ready, CURRENT_BASIS_UNPROVED among blockers."""
    ok = set()
    for r in csv.DictReader(open(readiness_csv, encoding="utf-8", newline="")):
        if "CURRENT_BASIS_UNPROVED" in (r.get("blockers") or "").split("|") and \
                (r.get("ready_for_human_review") or "").strip().lower() != "yes":
            ok.add(r["instrument_id"])
    out = {}
    for r in csv.DictReader(open(current_csv, encoding="utf-8", newline="")):
        if r["instrument_id"] in ok and (r.get("provisional_status") or "").strip().lower() == "yes":
            out[r["instrument_id"]] = (split_cites(r.get("usc_predicate_citations")),
                                       split_cites(r.get("cfr_predicate_citations")))
    return out


def plan_sections(orders):
    """-> (usc {(title, sec): set(ids)}, cfr {(title, part, sec|None): set(ids)}, bad [(iid, cite, reason)])."""
    usc, cfr, bad = {}, {}, []
    for iid, (ucs, ccs) in sorted(orders.items()):
        for cite in ucs + ccs:
            p = parse_citation(cite)
            if p[0] == "usc":
                usc.setdefault((p[1], p[2]), set()).add(iid)
            elif p[0] == "cfr":
                cfr.setdefault((p[1], p[2], p[3]), set()).add(iid)
            else:
                bad.append((iid, cite, p[1]))
    return usc, cfr, bad


# ------------------------------------------------------------ notice text --
def notice_plain_text(raw):
    t = raw.decode("utf-8", "replace")
    if re.search(r"<[a-zA-Z/][^>]*>", t):
        t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    return t


def mentioned_orders(text, register):
    """Census ids whose number the text names (mention only)."""
    ids = set()
    for h in eo_refs.find_eo_refs(text):
        base, suf = str(h["number"]), (h["suffix"] or "").upper()
        for cand in (f"EO:{base}{suf}", f"EO:{base}"):
            if cand in register:
                ids.add(cand)
                break
    return sorted(ids)


def parse_fr_page(raw):
    d = json.loads(raw.decode("utf-8"))
    res = [r for r in (d.get("results") or []) if isinstance(r, dict)]
    return int(d.get("total_pages") or 1), res


def is_continuation(title):
    return "continuation of the national emergency" in (title or "").lower()


# ------------------------------------------------------------- XML helpers --
BLOCK = {"p", "heading", "num", "chapeau", "continuation", "content", "subsection", "paragraph", "subparagraph",
         "clause", "subclause", "item", "section", "tr", "signature", "note", "quotedContent", "level", "subsubsection",
         "head", "hd", "fp", "cita", "auth", "source", "extract", "div", "div5", "div8", "div6", "div7", "div9", "ednote"}


def local(tag):
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def elem_text(el):
    parts = []

    def walk(e):
        lt = local(e.tag)
        blk = lt.lower() in BLOCK
        if blk:
            parts.append("\n")
        if e.text:
            parts.append(e.text)
        for c in e:
            walk(c)
            if c.tail:
                parts.append(c.tail)
        if blk:
            parts.append("\n")
    walk(el)
    t = re.sub(r"[ \t\r\f\v]+", " ", "".join(parts))
    return re.sub(r"\n\s*\n+", "\n", t).strip() + "\n"


def extract_usc_sections(stream, title, wanted):
    """{section: text} for wanted section numbers of one USLM title stream."""
    want, found, depth = set(wanted), {}, 0
    prefix = f"/us/usc/t{title}/s"
    for ev, el in ET.iterparse(stream, events=("start", "end")):
        if local(el.tag) != "section":
            continue
        ident = el.get("identifier") or ""
        if ev == "start":
            depth += 1
            continue
        depth -= 1
        if depth == 0:
            if ident.startswith(prefix) and "/" not in ident[len(prefix):]:
                sec = ident[len(prefix):]
                if sec in want:
                    found[sec] = elem_text(el)
            el.clear()
    return found


def extract_cfr(stream, wanted):
    """{(part, section|None): text|None} from eCFR-schema XML (versioner or bulk).

    None means the target exceeded MAX_PART_TEXT. wanted is a set of (part, section|None)."""
    parts_w = {p for p, s in wanted if s is None}
    secs_w = {s for p, s in wanted if s is not None}
    found, act_p, act_s = {}, None, None
    for ev, el in ET.iterparse(stream, events=("start", "end")):
        lt = local(el.tag).upper()
        if lt not in ("DIV5", "DIV8"):
            continue
        typ, n = (el.get("TYPE") or "").upper(), (el.get("N") or "")
        sec_id = re.sub(r"^\s*\u00a7+\s*", "", n).strip()
        if ev == "start":
            if lt == "DIV5" and typ == "PART" and n.strip() in parts_w and act_p is None:
                act_p = (el, (n.strip(), None))
            elif lt == "DIV8" and typ == "SECTION" and sec_id in secs_w and act_s is None:
                act_s = (el, (sec_id.split(".")[0], sec_id))
            continue
        for slot in ("p", "s"):
            act = act_p if slot == "p" else act_s
            if act is not None and el is act[0]:
                txt = elem_text(el)
                found[act[1]] = txt if len(txt.encode()) <= MAX_PART_TEXT else None
                if slot == "p":
                    act_p = None
                else:
                    act_s = None
        if act_p is None and act_s is None:
            el.clear()
    return found


# ------------------------------------------------------------------- pools --
def retry(fn, tries=3, pause=2.0):
    last = None
    i = -1
    while i + 1 < tries:
        i += 1
        try:
            try:
                return fn()
            except FetchError:
                raise
            except (OSError, http.client.HTTPException, ValueError) as e:  # timeouts, resets, TLS, bad URLs
                raise FetchError("network: " + type(e).__name__ + ": " + str(e)) from e
        except FetchError as e:
            last = e
            msg = str(e)
            if msg.startswith("HTTP 429") and i < RATE_TRIES - 1:
                tries = max(tries, RATE_TRIES)
                time.sleep(RATE_PAUSE * (2 ** min(i, 4)))
                continue
            if "robots" in msg or msg.startswith("HTTP 4") or "exceeds bound" in msg or "offline" in msg:
                break
            time.sleep(pause * (i + 1))
    raise last


def reason_of(e):
    m = str(e)
    if "robots" in m:
        return "blocked_by_robots_txt"
    if m.startswith("HTTP "):
        return "http_" + m[5:8]
    if "exceeds bound" in m:
        return "download_exceeds_bound"
    if m.startswith("network:"):
        return "network_error"
    return "fetch_error"


class Run:
    def __init__(self, out, cache, workers, transport=None, interval=1.0, previous=None, usc_rp="119-121"):
        self.out, self.workers, self.usc_rp = Path(out), workers, usc_rp
        self.fresh_cache = Path(cache) / ("api-" + dt.date.today().isoformat())
        mk = lambda sub, mb: FetchPool(Path(cache) / sub, workers=workers, per_host=min(workers, 4), transport=transport,
                                       max_bytes=mb, min_interval=interval, timeout=120,
                                       user_agent="EO-Road-System/1.0 (Theophilus; owner-run research)",
                                       max_cache_bytes=4 * 1024 ** 3)
        self.api = FetchPool(self.fresh_cache, workers=workers, per_host=min(workers, 4), transport=transport,
                             max_bytes=MAX_NOTICE, min_interval=interval, timeout=120,
                             user_agent="EO-Road-System/1.0 (Theophilus; owner-run research)")
        self.small, self.big = mk("small", MAX_NOTICE), mk("big", MAX_BULK)
        self.small.per_host = min(self.small.per_host, 2)
        self.small.workers = min(self.small.workers, 2)
        self.sources, self.failures = [], []
        self.previous = previous or {}
        (self.out / "texts").mkdir(parents=True, exist_ok=True)

    def fail(self, kind, key, reason, detail="", ids=()):
        self.failures.append({"kind": kind, "key": key, "reason": reason, "detail": str(detail)[:300],
                              "instrument_ids": sorted(ids)})

    def add(self, source_id, ids, url, text_name, raw, route, item, notes, extracted_from=None):
        """Record one held text. A notice keeps instrument_ids = the orders it names. A U.S. Code or
        CFR section is declared by its own identity (``extracted_from`` given): see section_identity."""
        (self.out / "texts" / text_name).write_bytes(raw)
        h = sha(raw)
        prev = self.previous.get(source_id)
        when = prev["retrieved_utc"] if prev and prev.get("sha256") == h else now_utc()
        rec = {"source_id": source_id, "instrument_ids": sorted(set(ids)), "url": url, "sha256": h,
               "bytes": len(raw), "content_type": "text/plain", "retrieved_utc": when, "route": route,
               "page_or_item": item, "text_path": f"texts/{text_name}",
               "cache_path": f"texts/{text_name}", "notes": notes}
        if extracted_from is not None:
            rec.update(section_identity(ids, item, *extracted_from))
        self.sources.append(rec)

    # ---- notices
    def notices(self, register):
        docs, page, total = {}, 1, 1
        while page <= total:
            q = [("conditions[type][]", "PRESDOCU"), ("conditions[term]", '"continuation of the national emergency"'),
                 ("per_page", "1000"), ("page", str(page))] + [("fields[]", f) for f in FR_FIELDS]
            url = FR_API + "?" + urllib.parse.urlencode(q)
            try:
                raw = retry(lambda: self.api.fetch(url))["body"]
                total, res = parse_fr_page(raw)
            except (FetchError, ValueError) as e:
                self.fail("notice_list", f"page {page}", reason_of(e) if isinstance(e, FetchError) else "bad_json", e)
                break
            for r in res:
                if r.get("document_number") and is_continuation(r.get("title")):
                    docs.setdefault(r["document_number"], r)
            page += 1
        stats = {"listed": len(docs), "fetched": 0, "named": set()}

        def one(item):
            num, r = item
            url = r.get("raw_text_url")
            if not url:
                return num, r, None, ("no_raw_text_url", "")
            try:
                return num, r, retry(lambda: self.small.fetch(url))["body"], None
            except FetchError as e:
                return num, r, None, (reason_of(e), e)
        for num, r, raw, err in self.small.map(one, sorted(docs.items())):
            if err:
                self.fail("notice", num, err[0], err[1])
                continue
            ids = mentioned_orders(notice_plain_text(raw), register)
            stats["fetched"] += 1
            stats["named"].update(ids)
            self.add(f"fr:notice:{num}", ids, r["raw_text_url"], f"fr-{num}.txt", raw, "fr_api_presidential_notice_raw_text",
                     f"{r.get('citation') or ''} {r.get('title') or ''}".strip(),
                     NOTICE_NOTE + f" title={r.get('title')!r}; published={r.get('publication_date')}; "
                     f"signed={r.get('signing_date')}; html={r.get('html_url')}; pdf={r.get('pdf_url')}.")
        return stats

    # ---- U.S. Code
    def usc(self, plan):
        by_title = {}
        for (t, s), ids in plan.items():
            by_title.setdefault(t, {})[s] = ids
        cong, law = self.usc_rp.split("-")

        def one(title):
            code = f"{title:02d}"
            url = USC_ZIP.format(congress=cong, law=law, code=code, rp=self.usc_rp)
            try:
                raw = retry(lambda: self.big.fetch(url))["body"]
                zf = zipfile.ZipFile(io.BytesIO(raw))
                names = [n for n in zf.namelist() if n.lower().endswith(".xml")]
                member = next((n for n in names if os.path.basename(n).lower() == f"usc{code}.xml"), names[0] if names else None)
                if member is None:
                    raise ValueError("no xml in zip")
                with zf.open(member) as f:
                    found = extract_usc_sections(f, title, set(by_title[title]))
                return title, url, sha(raw), found, None
            except FetchError as e:
                return title, url, "", {}, (reason_of(e), e)
            except (zipfile.BadZipFile, ValueError, ET.ParseError) as e:
                return title, url, "", {}, ("bad_zip_or_xml", e)
        for title, url, zsha, found, err in self.big.map(one, sorted(by_title)):
            for sec, ids in sorted(by_title[title].items()):
                if err:
                    self.fail("usc", f"{title} U.S.C. {sec}", err[0], err[1], ids)
                elif sec not in found:
                    self.fail("usc", f"{title} U.S.C. {sec}", "section_not_found_in_title_xml", url, ids)
                else:
                    self.add(f"usc:{self.usc_rp}:t{title}:s{sec}", ids, USC_VIEW.format(t=title, s=sec),
                             f"usc-t{title}-s{sec}.txt", found[sec].encode(), "usc_release_point_zip_section",
                             f"{title} U.S.C. {sec}",
                             f"Section element with its notes, extracted from OLRC release point {self.usc_rp} "
                             f"({url}, zip sha256 {zsha}). Current-law leads cite this section as a possible current basis; "
                             "no legal finding.", extracted_from=(url, zsha))

    # ---- CFR
    def ecfr_date(self, title_no):
        today = dt.date.today().isoformat()
        try:
            d = json.loads(retry(lambda: self.api.fetch(ECFR_TITLES))["body"].decode())
        except (FetchError, ValueError):
            return today, "titles_unavailable"
        for t in d.get("titles") or []:
            if t.get("number") == title_no:
                return (t.get("up_to_date_as_of") or t.get("latest_issue_date") or (d.get("meta") or {}).get("date")
                        or today), "titles.json"
        return ((d.get("meta") or {}).get("date") or today), "titles.json_meta"

    def cfr(self, plan):
        by_title = {}
        for (t, p, s), ids in plan.items():
            by_title.setdefault(t, {})[(p, s)] = ids
        state = {"versioner_blocked": False}

        def one(title):
            items = by_title[title]
            date, dsrc = self.ecfr_date(title)
            res, errs = {}, {}
            if not state["versioner_blocked"]:
                for (p, s) in sorted(items, key=lambda k: (k[0], k[1] or "")):
                    q = urllib.parse.urlencode({"part": p, **({"section": s} if s else {})})
                    url = ECFR_FULL.format(date=date, title=title, query=q)
                    try:
                        raw = retry(lambda: self.small.fetch(url))["body"]
                        got = extract_cfr(io.BytesIO(raw), {(p, s)})
                        if (p, s) in got:
                            res[(p, s)] = (got[(p, s)], url, sha(raw), "ecfr_versioner_full_xml")
                        else:
                            errs[(p, s)] = ("target_not_in_versioner_xml", url)
                    except FetchError as e:
                        errs[(p, s)] = (reason_of(e), e)
                        if "robots" in str(e):
                            state["versioner_blocked"] = True
                            break
                    except ET.ParseError as e:
                        errs[(p, s)] = ("bad_xml", e)
            missing = {k for k in items if k not in res}
            if missing:
                url = GOVINFO_BULK.format(title=title)
                try:
                    raw = retry(lambda: self.big.fetch(url))["body"]
                    got = extract_cfr(io.BytesIO(raw), missing)
                    for k in missing:
                        if k in got:
                            res[k] = (got[k], url, sha(raw), "govinfo_ecfr_bulk_title_xml")
                            errs.pop(k, None)
                        else:
                            errs[k] = ("target_not_in_title_xml", url)
                except (FetchError, ET.ParseError) as e:
                    for k in missing:
                        errs[k] = (reason_of(e) if isinstance(e, FetchError) else "bad_xml", e)
            return title, date, dsrc, items, res, errs
        for title, date, dsrc, items, res, errs in self.big.map(one, sorted(by_title)):
            for (p, s), ids in sorted(items.items(), key=lambda kv: (kv[0][0], kv[0][1] or "")):
                label = f"{title} CFR {s}" if s else f"{title} CFR part {p}"
                if (p, s) in res:
                    text, url, rsha, route = res[(p, s)]
                    if text is None:
                        self.fail("cfr", label, "part_exceeds_text_bound", MAX_PART_TEXT, ids)
                        continue
                    name = f"cfr-t{title}-{s}.txt" if s else f"cfr-t{title}-part{p}.txt"
                    human = f"https://www.ecfr.gov/on/{date}/title-{title}/" + (f"section-{s}" if s else f"part-{p}")
                    self.add(f"cfr:t{title}:{s or 'part' + p}", ids, human, name, text.encode(), route, label,
                             f"Text extracted from {url} (response sha256 {rsha}); eCFR date {date} ({dsrc}). "
                             "Bulk-title route reflects the current GovInfo copy, not necessarily this date. "
                             "Current-law leads cite this CFR text as a possible current basis; no legal finding.",
                             extracted_from=(url, rsha))
                else:
                    r = errs.get((p, s), ("unknown", ""))
                    self.fail("cfr", label, r[0], r[1], ids)


SECTION_IDENTITY_NOTE = (
    "instrument_ids is empty because this is the text of a U.S. Code or CFR section, not of any order. "
    "mentioned_instrument_ids lists the orders whose current-law leads cite this section; "
    "extracted_from is the official artifact (url, sha256) the text was cut from, and citation names the section.")
_FROM_RE = (re.compile(r"Text extracted from (\S+) \(response sha256 ([0-9a-f]{64})\)"),
            re.compile(r"\((https://\S+\.zip), zip sha256 ([0-9a-f]{64})\)"))


def section_identity(ids, citation, origin_url, origin_sha):
    """Fields that declare a section text by its own identity (Respondendi fix F3, 2026-11-10).

    A singleton instrument_ids made the claim kit read a CFR section as the citing order's own text
    (and its mention scan invent ACT records). The citing orders move to mentioned_instrument_ids."""
    return {"instrument_ids": [], "mentioned_instrument_ids": sorted(set(ids)), "citation": citation,
            "item_extract": "citation", "extracted_from": {"url": origin_url, "sha256": origin_sha},
            "identity_note": SECTION_IDENTITY_NOTE}


def redeclare(row):
    """Rewrite one SOURCES.jsonl row of an earlier run to section_identity (idempotent, offline)."""
    if row.get("source_id", "").split(":")[0] not in ("usc", "cfr") or row.get("item_extract"):
        return row
    for pattern in _FROM_RE:
        m = pattern.search(row.get("notes") or "")
        if m:
            out = dict(row)
            out.update(section_identity(row.get("instrument_ids") or [], row.get("page_or_item"), m.group(1), m.group(2)))
            return out
    return row


def redeclare_file(path):
    path = Path(path)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    new = [redeclare(r) for r in rows]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in new:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=False) + "\n")
    return sum(1 for a, b in zip(rows, new) if a is not b)


def write_outputs(run, orders, notice_stats, usc_plan, cfr_plan, bad):
    out = run.out
    srcs = sorted(run.sources, key=lambda r: r["source_id"])
    with open(out / "SOURCES.jsonl", "w", encoding="utf-8") as f:
        for r in srcs:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=False) + "\n")
    fails = run.failures + [{"kind": "citation", "key": c, "reason": r, "detail": "", "instrument_ids": [i]}
                            for i, c, r in bad]
    fails.sort(key=lambda r: (r["kind"], r["key"], r["reason"]))
    with open(out / "FAILURES.jsonl", "w", encoding="utf-8") as f:
        for r in fails:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    covered = {i for r in srcs if r["source_id"].split(":")[0] in ("usc", "cfr")
               for i in r.get("mentioned_instrument_ids", r["instrument_ids"])}
    reasons = {}
    for r in fails:
        reasons[r["reason"]] = reasons.get(r["reason"], 0) + 1
    summary = {
        "job": "theophilus-sources",
        "generated_utc": now_utc(),
        "notices": {"listed": notice_stats["listed"], "fetched": notice_stats["fetched"]},
        "orders_named_in_notices": len(notice_stats["named"]),
        "eligible_yes_orders": len(orders),
        "usc_sections_planned": len(usc_plan), "cfr_targets_planned": len(cfr_plan),
        "sections_fetched": {"usc": sum(1 for r in srcs if r["source_id"].startswith("usc:")),
                             "cfr": sum(1 for r in srcs if r["source_id"].startswith("cfr:"))},
        "yes_orders_covered_by_sections": len(covered),
        "failures_total": len(fails), "failures_by_reason": dict(sorted(reasons.items())),
        "usc_release_point": run.usc_rp,
        "limits": "No legal finding. Notices before 1994 are not in the Federal Register API and are left for a later route.",
    }
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n")
    return summary


def run_job(repo, out, cache, workers, transport=None, interval=1.0, previous_path=None):
    repo, out = Path(repo), Path(out)
    jobs = repo / "jobs"
    register = load_register(jobs / "domesday-register/output/REGISTER.csv")
    orders = eligible_orders(jobs / "readiness-tracker/output/READINESS_BY_ORDER.csv",
                             jobs / "current-law/output/ORDERS_CURRENT_LAW.csv")
    rp = "119-121"
    try:
        rp = json.loads((jobs / "current-law/output/SUMMARY.json").read_text())["usc"]["release_point"] or rp
    except (OSError, ValueError, KeyError):
        pass
    previous = {}
    if previous_path and Path(previous_path).is_file():
        for line in open(previous_path, encoding="utf-8"):
            try:
                r = json.loads(line)
                previous[r["source_id"]] = r
            except (ValueError, KeyError):
                pass
    run = Run(out, cache, workers, transport, interval, previous, rp)
    usc_plan, cfr_plan, bad = plan_sections(orders)
    print(f"eligible YES orders {len(orders)}; usc sections {len(usc_plan)}; cfr targets {len(cfr_plan)}; "
          f"unparsed citations {len(bad)}", flush=True)
    ns = run.notices(register)
    print("notices", ns["listed"], ns["fetched"], flush=True)
    run.usc(usc_plan)
    run.cfr(cfr_plan)
    s = write_outputs(run, orders, ns, usc_plan, cfr_plan, bad)
    print(json.dumps(s, indent=1), flush=True)
    return s


if __name__ == "__main__" and len(sys.argv) == 3 and sys.argv[1] == "--redeclare":
    print("rows redeclared:", redeclare_file(sys.argv[2]))
