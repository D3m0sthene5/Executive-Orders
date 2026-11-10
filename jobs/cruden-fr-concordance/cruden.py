"""Cruden: a concordance of the 1936-1993 Federal Register and the Statutes at Large by executive-order number.

Named for Alexander Cruden, whose Complete Concordance (1737) listed every place each word of the Bible appears, so a
reader could find every passage by one word. This job does the same for an order's number: for each target order it
asks govinfo's full-text search which Federal Register issues (1936-1993, the years selden-fr-citers does not reach)
and which Statutes at Large pages print "Executive Order No. N", downloads each hit once, and locates every sentence
that cites the order with jobs/selden-common (Selden's locator: citation forms, relation words, negation, the target
printed as actor, planted near-miss controls). Zero model tokens.

Discovery only. A located sentence is a lead to what a later document says, never a finding that it ended or changed
the order. A target with no hit, or with hits but no acting sentence, gets a search record and nothing else: a
concordance's silence is never evidence about an order (D-20261028-evidence-decides). Every fragment is tied to its
target by the printed number, and, where the citation prints a date, by that date agreeing with the target's own;
a printed date that disagrees, or another issuer ("Executive Order No. 885 of the Governor General of the Philippine
Islands"), refuses the match. No status, census, codebook or count changes. Human-certified: 0.
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
UA = "EO-Road-System/1.0 (Cruden concordance of the Federal Register by order number; owner-run research)"
SEARCH_URL = "https://api.govinfo.gov/search"
FR_PDF = "https://www.govinfo.gov/content/pkg/{pkg}/pdf/{pkg}.pdf"
GRANULE_PDF = "https://www.govinfo.gov/content/pkg/{pkg}/pdf/{gran}.pdf"
FR_FIRST, FR_LAST = "1936-03-14", "1993-12-31"
PRODUCER = "cruden-fr-concordance"
GRADE_FR = ("government_printed_federal_register_issue (govinfo scan of the daily Federal Register; text is the scan's "
            "OCR layer)")
GRADE_STAT = "government_printed_statutes_at_large_page (govinfo scan; text is the scan's OCR layer)"

# Another issuer of numbered "executive orders" printed right after the citation (Philippine governors-general,
# territorial governors, the Canal Zone governor, the High Commissioner): the number names some other series.
OTHER_ISSUER = re.compile(
    r"^.{0,40}?\b(?:of|by|issued\s+by)\s+the\s+(?:Governor[\s-]*General|Governor|High\s+Commissioner|Commissioner|"
    r"President\s+of\s+the\s+(?:Commonwealth|Philippines)|Mayor|Secretary)\b|"
    r"^.{0,80}?\b(?:Philippine|Puerto\s+Rico|Porto\s+Rico|Commonwealth\s+of\s+the|Territory\s+of|Manila|"
    r"San\s+Juan|Canal\s+Zone\s+Governor)\b", re.I | re.S)
# Headings of the printed instrument whose text holds the sentence (searched backwards from the citation). A heading
# is bracketed ('[Public Land Order 945]', the Federal Register's label) or starts a line in capitals ('PUBLIC LAND
# ORDER 945', 'EXECUTIVE ORDER 10524'); a citation in running text ('pursuant to Executive Order No. 10355') is not.
def _heading(words, digits):
    def spaced(ws):
        return r"\s+".join(r"\s?".join(re.escape(c) for c in w) for w in ws)
    mixed, caps = spaced(words), spaced([w.upper() for w in words])
    return re.compile(r"(?:\[\s*(?i:" + mixed + r")|(?:^|\n)[ \t]*" + caps + r")\s*(?:N\s?[Oo]\.?\s*)?("
                      + digits + r")\b")


HEADINGS = [
    ("PLO", _heading(["Public", "Land", "Order"], r"\d{1,4}")),
    ("PROC", _heading(["Proclamation"], r"\d{4}")),
    ("EO", _heading(["Executive", "Order"], r"\d{4,5}")),
]


def now_utc():
    return S.now_utc()


def read_csv(p):
    if not Path(p).is_file():
        return []
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


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


def query(target, collection, after_date):
    q = f"collection:{collection} AND (" + " OR ".join(forms(target)) + ")"
    if collection == "FR":
        lo = max(after_date or FR_FIRST, FR_FIRST)
        q += f" AND publishdate:range({lo},{FR_LAST})"
    return q


class Searcher:
    """govinfo's documented search API (POST, key in the X-Api-Key header, never in a URL or log)."""

    def __init__(self, key, opener=None, min_interval=0.75, max_searches=2500):
        self.key, self.opener = key, opener or urllib.request.urlopen
        self.min_interval, self.max_searches = min_interval, max_searches
        self.n, self.last, self.stopped = 0, 0.0, ""
        self.lock = threading.Lock()

    def search(self, q, page_size=100):
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
                           "sorts": [{"field": "publishdate", "sortOrder": "ASC"}]}).encode()
        req = urllib.request.Request(SEARCH_URL, data=body, method="POST",
                                     headers={"Content-Type": "application/json", "User-Agent": UA,
                                              "X-Api-Key": self.key})
        try:
            with self.opener(req, timeout=60) as r:
                raw = r.read(5_000_001)
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
                pages = r.stdout.decode("utf-8", "replace").split("\f")
                if pages and not pages[-1].strip():
                    pages = pages[:-1]
                return pages, "pdftotext"
    import frpages
    return frpages.pdf_pages(raw), "pypdf"


def extract_pages(raw, first, last):
    import frpages
    return frpages.extract_pdf(raw, first, last)


# ---- location ------------------------------------------------------------------------------------------------------

def identity_check(hit, text, target_date):
    """None when the citation may name the target; else the reason it names something else."""
    if hit["date_stated"] and target_date and hit["date_stated"] != target_date:
        return "printed_date_disagrees_with_target"
    after = text[hit["cite_end"]:hit["cite_end"] + 160]
    if OTHER_ISSUER.search(after):
        return "another_issuer_printed_with_the_number"
    return None


def acting_instrument(text, cite_start, target=None):
    """(acting_id, label): the nearest instrument heading printed before the citation with no filing line in between,
    else (None, None) and the caller uses the page as a NOTICE id. A heading that prints the target's own number is a
    title line citing it ('REVOKING EXECUTIVE ORDER NO. 5214'), not the acting instrument, and is skipped."""
    tnum = (S.parse_eo(target) or ("",))[0] if target else ""
    best = None
    for kind, rx in HEADINGS:
        for m in rx.finditer(text, 0, cite_start):
            if kind == "EO" and m.group(1) == tnum:
                continue
            if best is None or m.start() > best[1]:
                best = (kind, m.start(), m.group(1))
    if best and not S.FILING.search(text, best[1], cite_start):
        kind, _, num = best
        return f"{kind}:{num}", {"PLO": "Public Land Order", "PROC": "Proclamation", "EO": "Executive Order"}[kind] + f" {num}"
    return None, None


def locate(text, target, target_date):
    """[(hit, refusal_reason_or_None)] for every sentence of `text` citing the target by number."""
    out = []
    num, suf = (S.parse_eo(target) or ("", "", ""))[:2]
    for h in S.find_citations(text, target, target_date):
        if h["form"] != "number":
            # Selden's fallbacks read lists and split OCR; Cruden keeps only a printed 'Executive Order (No.) N'.
            continue
        # Selden keeps one hit per sentence (the first citation). A title line and the dated citation can share a
        # sentence, so every citation of the target inside it is read: one printed date equal to the target's
        # confirms it; printed dates that all disagree refuse it; another issuer after any citation refuses it.
        seg = text[h["start"]:h["end"]]
        dates, ends = [], []
        for (s, e, n, sx, d) in S.cites.eo_number_mentions(seg):
            if n == num and (sx or "") == suf:
                ends.append(h["start"] + e)
                if d:
                    dates.append(d.isoformat() if hasattr(d, "isoformat") else d)
        if target_date and target_date in dates:
            h = dict(h, date_stated=target_date, date_match=True)
        elif dates:
            h = dict(h, date_stated=dates[0], date_match=(dates[0] == target_date) if target_date else None)
        why = identity_check(h, text, target_date)
        if not why:
            for e in ends:
                if OTHER_ISSUER.search(text[e:e + 160]):
                    why = "another_issuer_printed_with_the_number"
                    break
        out.append((h, why))
    return out


# ---- the run -------------------------------------------------------------------------------------------------------

class Run:
    def __init__(self, repo, out, cache, env, transport=None, opener=None, premis=None):
        self.repo, self.out, self.env = Path(repo), Path(out), env
        g = lambda k, d: type(d)(env.get(k) or d)  # noqa: E731
        self.max_packages = g("JOB_MAX_PACKAGES", 1500)
        self.max_download = int(g("JOB_MAX_DOWNLOAD_GB", 12.0) * 1e9)
        self.deadline = time.monotonic() + g("JOB_TIME_BUDGET_MIN", 280.0) * 60
        self.per_target_cap = {"FR": g("CRUDEN_FR_HITS_PER_TARGET", 40), "STATUTE": g("CRUDEN_STAT_HITS_PER_TARGET", 20)}
        self.commit_extract_bytes, self.committed = g("CRUDEN_COMMIT_MB", 80) * 1_000_000, 0
        key, self.key_kind = api_key(env)
        self.searcher = Searcher(key, opener=opener, min_interval=g("CRUDEN_SEARCH_INTERVAL", 0.75),
                                 max_searches=g("JOB_MAX_SEARCHES", 2500 if self.key_kind == "real" else 25))
        self.pool = FetchPool(Path(cache) / "govinfo", workers=g("JOB_WORKERS", 6), per_host=6, transport=transport,
                              max_bytes=450_000_000, timeout=240, user_agent=UA, min_interval=0.1,
                              max_cache_bytes=3 * 1024 ** 3)
        self.premis = premis
        self.lock = threading.Lock()
        self.searches, self.sources, self.fragments, self.located, self.failures = [], [], [], [], []
        (self.out / "texts").mkdir(parents=True, exist_ok=True)
        (self.out / "captures").mkdir(parents=True, exist_ok=True)
        self.extractor = None

    def budget(self):
        return self.pool.bytes_downloaded < self.max_download and time.monotonic() < self.deadline

    def fixity(self, pkg):
        if self.premis:
            return self.premis(pkg)
        import fixity
        return fixity.check_one({"package": pkg, "filename": pkg + ".pdf", "url": FR_PDF.format(pkg=pkg),
                                 "shas": set(), "ids": set(), "found_in": set()})

    # one package (an FR issue or a Statutes page granule), all its targets
    def one(self, unit):
        coll, pkg, gran = unit["collection"], unit["package"], unit.get("granule") or ""
        url = FR_PDF.format(pkg=pkg) if coll == "FR" else GRANULE_PDF.format(pkg=pkg, gran=gran)
        got = self.pool.fetch(url)
        raw = got["body"]
        if not raw.startswith(b"%PDF"):
            raise FetchError("not a PDF")
        pages, tool = pdf_pages(raw)
        per_page = defaultdict(list)  # page index -> [(target, hit, refusal)]
        for t, tdate in sorted(unit["targets"].items()):
            any_cite = False
            for i, ptxt in enumerate(pages):
                if not ptxt or not S.printed_anywhere(ptxt, S.parse_eo(t)[0]):
                    continue
                for h, why in locate(ptxt, t, tdate):
                    any_cite = True
                    per_page[i].append((t, h, why))
            if not any_cite:
                self.located.append({"target_id": t, "collection": coll, "package": pkg, "granule": gran,
                                     "pdf_page": "", "located": False, "refused": "", "acting_id": "",
                                     "mechanism_printed": "", "acting_on_target": False, "date_stated": "",
                                     "date_match": "", "quote": "",
                                     "note": "search hit, but no sentence prints 'Executive Order (No.) N' in the OCR"})
        gpo, match, presult = "", False, ""
        if coll == "FR":
            pr = self.fixity(pkg)
            gpo = pr.get("gpo_sha256") or ""
            match = bool(gpo) and gpo == got["sha256"]
            # check_one compares against hashes it was given (none here); report our own comparison instead.
            presult = "match" if match else ("mismatch" if gpo else (pr.get("result") or "unchecked"))
        recs = []
        for i in sorted(per_page):
            first, last = i, min(len(pages) - 1, i + 1)
            text = "".join(f"\n=== PDF page {j + 1} of {len(pages)} ===\n{pages[j]}" for j in range(first, last + 1))
            stem = f"{gran or pkg}_p{i + 1}"
            header = (f"Cruden page text. {coll} {gran or pkg}, PDF pages {first + 1}-{last + 1} of {len(pages)}; "
                      f"source {url} sha256 {got['sha256']}; text by {tool}.\n")
            full = header + text
            (self.out / "texts" / f"{stem}.txt").write_text(full, encoding="utf-8")
            targets = sorted({t for t, _, _ in per_page[i]})
            issue_src = S.source_record(
                f"cruden:{coll.lower()}:{gran or pkg}:p{i + 1}", "NOTICE:" + (gran or pkg), targets, url + f"#page={first + 1}",
                got["sha256"], got["bytes"], "govinfo_search_then_content_pdf",
                f"{gran or pkg}.pdf PDF pages {first + 1}-{last + 1} of {len(pages)}", f"texts/{stem}.txt",
                GRADE_FR if coll == "FR" else GRADE_STAT,
                "Whole PDF hashed; the cited pages' OCR text is kept. For a Federal Register issue GPO publishes the "
                "issue's SHA-256 in its PREMIS record; gpo_premis_match says whether these bytes are GPO's.",
                extra={"collection": coll, "package": pkg, "granule": gran, "gpo_premis_sha256": gpo,
                       "gpo_premis_match": match, "gpo_premis_result": presult, "issue_date": unit.get("date") or "",
                       "pdf_pages": [first + 1, last + 1], "page_count": len(pages), "text_tool": tool})
            cite = issue_src
            ext, etool = extract_pages(raw, first, last)
            with self.lock:
                fits = self.committed + len(ext) <= self.commit_extract_bytes and len(ext) <= 1_500_000
                if fits:
                    self.committed += len(ext)
            if fits:
                esha = S.sha256(ext)
                (self.out / "captures" / f"{esha}.pdf").write_bytes(ext)
                cite = S.source_record(
                    f"cruden-extract:{esha[:16]}", "NOTICE:" + (gran or pkg), targets, url + f"#page={first + 1}", esha,
                    len(ext), "govinfo_content_pdf_page_extract", issue_src["page_or_item"] + " (committed extract)",
                    f"texts/{stem}.txt", issue_src["grade"],
                    f"PDF pages {first + 1}-{last + 1} extracted with {etool} from the PDF whose sha256 is "
                    f"source_sha256 (GPO PREMIS match: {match}); re-download it to re-derive.",
                    cache_path=f"captures/{esha}.pdf",
                    extra={"collection": coll, "source_sha256": got["sha256"], "gpo_premis_match": match,
                           "extract_tool": etool})
            recs.append(issue_src)
            if cite is not issue_src:
                recs.append(cite)
            off = len(header) + len(f"\n=== PDF page {first + 1} of {len(pages)} ===\n")
            for t, h, why in per_page[i]:
                h = dict(h, start=h["start"] + off, end=h["end"] + off, cite_start=h["cite_start"] + off,
                         cite_end=h["cite_end"] + off)
                actor, label = acting_instrument(full, h["cite_start"], t)
                if actor is None or actor == t:
                    actor = "NOTICE:" + (f"{gran}" if gran else f"{pkg}/p{i + 1}")
                    label = (f"document printed on PDF page {i + 1} of {gran or pkg} (instrument kind not identified "
                             "by machine)")
                acting = S.acting_on_target(h) and not why
                row = {"target_id": t, "collection": coll, "package": pkg, "granule": gran, "pdf_page": i + 1,
                       "located": True, "refused": why or "", "acting_id": actor,
                       "mechanism_printed": h["mechanism"], "acting_on_target": acting,
                       "date_stated": h["date_stated"] or "", "date_match": "" if h["date_match"] is None else h["date_match"],
                       "quote": S.cites.squeeze(h["quote"])[:300], "note": ""}
                self.located.append(row)
                if why:
                    continue  # names some other order: kept in LOCATED.csv, never published as a lead
                flags = ["publication_date_not_instrument_date"]
                if h["date_match"] is None:
                    flags.append("identity_by_number_only_no_date_printed")
                    eo = S.parse_eo(t)
                    if eo and int(eo[0]) < 1000:
                        # Short numbers collide with other numbered series; without a printed date the
                        # sentence is a pointer only.
                        h = dict(h, mechanism_class="mention")
                        flags.append("short_number_identity_unconfirmed")
                if actor.startswith("NOTICE:"):
                    flags.append("acting_instrument_not_identified")
                self.fragments.append(S.fragment(
                    t, actor, label, h, cite, PRODUCER, unit.get("date") or "",
                    "publication date of the issue or volume printing the sentence (not the instrument's signing "
                    "or effective date)", "cruden_fr_number_search" if coll == "FR" else "cruden_statute_number_search",
                    flags=flags, extra={"collection": coll, "package": pkg, "granule": gran, "pdf_page": i + 1,
                                        "source_sha256": got["sha256"], "gpo_premis_match": match}))
        with self.lock:
            self.sources.extend(recs)
        return {"bytes": got["bytes"], "pages": len(pages)}


def load_targets(repo, env):
    p = Path(env.get("CRUDEN_TARGETS") or (Path(repo) / "jobs/linnaeus-types/output/CRUDEN_TARGETS.csv"))
    return [r["instrument_id"] for r in read_csv(p)]


def control_targets(repo, exclude, n=30, seed=1737):
    """Planted positives: BLM's PLO table names a pre-1937 order by number with an ending word, in a PLO printed in
    the Federal Register by 1993 (independent of the page OCR Cruden reads). The concordance must find a sentence
    citing the order in some Federal Register issue."""
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
                if eo and int(eo[0]) >= 1000 and int(eo[0]) < 7532:
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


def main(repo: Path, out: Path, cache: Path, env=os.environ, transport=None, opener=None, premis=None):
    repo, out = Path(repo), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    started = now_utc()
    targets = load_targets(repo, env)
    dates = S.order_dates(repo)
    limit = int(env.get("JOB_LIMIT") or 0)
    collections_ = [c for c in (env.get("CRUDEN_COLLECTIONS") or "FR,STATUTE").split(",") if c]
    run = Run(repo, out, cache, env, transport=transport, opener=opener, premis=premis)
    controls = control_targets(repo, set(targets), n=int(env.get("CRUDEN_CONTROLS") or 30))
    control_ids = {t for t, _ in controls}

    # carry forward: earlier searches and the (target, package) pairs already read
    prior = Path(env.get("JOB_PRIOR_OUTPUT_DIR") or (HERE / "output"))
    prior_searches = {(r["target_id"], r["collection"]): r for r in S.read_jsonl(prior / "SEARCHES.jsonl")
                      if r.get("status") == "searched"}
    done_pairs = {(r["target_id"], r["package"], r.get("granule") or "") for r in read_csv(prior / "LOCATED.csv")}
    carried = carry_forward(prior, out, run)

    order = [t for t, _ in controls] + targets
    if limit:
        order = order[:limit + len(controls)]
    # 1. searches
    for t in order:
        for coll in collections_:
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
                hits = res["hits"][:run.per_target_cap[coll]]
                rec.update(status="searched", count=res["count"], hits=hits, response_sha256=res["sha256"],
                           complete=(res["count"] or 0) <= len(hits))
            except (FetchError, ValueError, OSError) as e:
                rec.update(status="not_searched_error", error=str(e)[:200])
            run.searches.append(rec)
    # 2. units: one per package/granule, all targets that hit it and are not yet read there
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
            k = (rec["collection"], h["package"], gran or "")
            if (rec["target_id"], h["package"], gran or "") in done_pairs:
                continue
            u = units.setdefault(k, {"collection": k[0], "package": k[1], "granule": k[2], "date": h.get("date"),
                                     "targets": {}})
            u["targets"][rec["target_id"]] = rec.get("target_date") or None
    # controls first, then the units serving most targets, then oldest
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
    # 3. controls: planted positives must be found; near-miss negatives must never be
    ctl = measure_controls(run, controls)
    if not ctl["passed"]:
        for f in run.fragments:
            for row in f["data"]:
                row["mechanism"] = "cross_reference"
                row["flags"] = sorted(set(row["flags"]) | {"controls_failed_this_run"})
    # control targets' fragments are measurements, not leads for the target set
    fr_out = [f for f in run.fragments if f["instrument_id"] not in control_ids]
    write(out, run, fr_out, ctl, targets, control_ids, started, carried, n, len(todo))
    return json.loads((out / "SUMMARY.json").read_text(encoding="utf-8"))


def carry_forward(prior, out, run):
    """Earlier fragments, sources, located rows and their committed texts and extracts, re-hashed."""
    n = 0
    if not prior.is_dir() or prior.resolve() == out.resolve():
        return 0
    for r in S.read_jsonl(prior / "SOURCES.jsonl"):
        tp = prior / (r.get("text_path") or "-")
        if not tp.is_file():
            continue
        (out / "texts").mkdir(parents=True, exist_ok=True)
        (out / tp.relative_to(prior)).write_bytes(tp.read_bytes())
        cp = r.get("cache_path")
        if cp:
            src = prior / cp
            if not src.is_file() or S.sha256(src.read_bytes()) != r["sha256"]:
                continue  # an extract that no longer hashes is dropped, not trusted
            (out / cp).write_bytes(src.read_bytes())
            run.committed += r["bytes"]
        run.sources.append(r)
    keep = {r["source_id"] for r in run.sources}
    for f in S.read_jsonl(prior / "FRAGMENTS.jsonl"):
        if all(row.get("source_id") in keep for row in f.get("data") or []):
            for row in f["data"]:
                row["flags"] = sorted(set(row.get("flags") or []) - {"controls_failed_this_run"})
            run.fragments.append(f)
            n += 1
    for r in read_csv(prior / "LOCATED.csv"):
        run.located.append(r)
    return n


def measure_controls(run, controls):
    found = 0
    misses = []
    loc = defaultdict(list)
    for r in run.located:
        loc[r["target_id"]].append(r)
    for t, plo in controls:
        rows = [r for r in loc.get(t, []) if str(r.get("located")) == "True" and not r.get("refused")]
        if rows:
            found += 1
        else:
            s = [x for x in run.searches if x["target_id"] == t and x["collection"] == "FR"]
            misses.append({"target": t, "plo": plo, "search_status": s[0].get("status") if s else "none",
                           "hits": s[0].get("count") if s else None})
    texts = {}
    pos = []
    for f in run.fragments:
        row = f["data"][0]
        tp = run.out / (row.get("text_path") or "-")
        if f["instrument_id"] in {t for t, _ in controls} and tp.is_file():
            texts[row["text_path"]] = tp.read_text(encoding="utf-8")
            pos.append((f["instrument_id"], row["acting_id"], "ending", row["text_path"]))
    neg = S.run_controls(pos, texts, seed=1737) if pos else {"negatives": 0, "false_locations": 0, "false_hits": []}
    searched = sum(1 for t, _ in controls if any(x["target_id"] == t and x.get("status") == "searched"
                                                  for x in run.searches))
    return {"planted_positives": len(controls), "positives_searched": searched, "positives_located": found,
            "recall": round(found / searched, 4) if searched else None, "misses": misses[:40],
            "near_miss_negatives": neg.get("negatives", 0), "false_locations": neg.get("false_locations", 0),
            "false_hits": neg.get("false_hits", [])[:40],
            "passed": searched > 0 and neg.get("false_locations", 0) == 0}


def write(out, run, fr_out, ctl, targets, control_ids, started, carried, attempted, todo_n):
    seen = set()
    sources = []
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
            "mechanism_printed", "acting_on_target", "date_stated", "date_match", "quote", "note"]
    with open(out / "LOCATED.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, cols, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(sorted(run.located, key=lambda r: (r["target_id"], r["collection"], r["package"],
                                                       r.get("granule") or "", str(r.get("pdf_page")))))
    tset = set(targets)
    srch = [r for r in run.searches if r["target_id"] in tset]
    by_coll = {}
    for coll in sorted({r["collection"] for r in srch}):
        rs = [r for r in srch if r["collection"] == coll]
        ok = [r for r in rs if r.get("status") == "searched"]
        hit = {r["target_id"] for r in ok if r.get("count")}
        acting = {f["instrument_id"] for f in frs if f["data"][0].get("collection") == coll
                  and f["data"][0]["mechanism"] != "cross_reference"}
        cited = {f["instrument_id"] for f in frs if f["data"][0].get("collection") == coll}
        by_coll[coll] = {"targets_searched": len(ok), "targets_not_searched": len(rs) - len(ok),
                         "targets_with_hits": len(hit), "targets_with_located_citation": len(cited),
                         "targets_with_acting_sentence": len(acting),
                         "searches_incomplete_over_cap": sum(1 for r in ok if r.get("complete") is False)}
    fam = {r["instrument_id"]: r["family"] for r in read_csv(run.repo / "jobs/linnaeus-types/output/CRUDEN_TARGETS.csv")}
    acting_all = {f["instrument_id"] for f in frs if f["data"][0]["mechanism"] != "cross_reference"}
    cited_all = {f["instrument_id"] for f in frs}
    by_family = defaultdict(Counter)
    searched_all = {r["target_id"] for r in srch if r.get("status") == "searched"}
    for t in targets:
        f = fam.get(t, "")
        by_family[f]["targets"] += 1
        by_family[f]["searched"] += t in searched_all
        by_family[f]["cited"] += t in cited_all
        by_family[f]["acting"] += t in acting_all
    refused = Counter(r["refused"] for r in run.located if r.get("refused"))
    summary = {
        "job": PRODUCER, "generated_utc": now_utc(), "started_utc": started, "key_kind": run.key_kind,
        "targets": len(targets), "control_targets": len(control_ids), "searches_made_this_run": run.searcher.n,
        "search_stopped": run.searcher.stopped, "units_planned": todo_n, "units_attempted": attempted,
        "units_failed": len(run.failures), "bytes_downloaded": run.pool.bytes_downloaded,
        "fragments": len(frs), "fragments_carried_forward": carried, "by_collection": by_coll,
        "orders_with_located_citation": len(cited_all), "orders_with_acting_sentence": len(acting_all),
        "citations_refused_identity": dict(refused), "by_family": {k: dict(v) for k, v in sorted(by_family.items())},
        "extracts_committed_bytes": run.committed,
        "controls": {k: v for k, v in ctl.items() if k not in ("misses", "false_hits")},
        "limits": ("Leads only. govinfo's search index and the OCR decide what is found; an order with no hit is "
                   "unsearched-equivalent, never evidence that nothing acted on it. No status, census, codebook or "
                   "count change. Certified: 0."),
    }
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("targets", "searches_made_this_run", "units_attempted", "fragments",
                                                "orders_with_acting_sentence", "controls")}, indent=1), flush=True)
