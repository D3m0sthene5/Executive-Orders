"""Selden FR acting: the Federal Register pages (1936-1993) that print the later non-EO instruments named as acting
on census orders (Public Land Orders, proclamations, agency orders and notices, reorganization plans), with the
issue's custody checked against GPO's published SHA-256 and the sentence citing each target order located.

Zero model tokens. Wanted list (built here, not by hand): every edge in jobs/later-events/output/EDGES.csv and
jobs/shepard-citations/output/EDGES.csv whose acting instrument is not an executive order, whose relation is an
ending or modifying one, whose target is a census order, and whose Federal Register citation (BLM's PLO table, or the
printed label) falls in volumes 1-58 (1936-1993). Executive orders as acting instruments are the order-originals
lane (fr-originals, Tischendorf, Mabillon) and are left out.

Route per page: govinfo link service -> daily-issue PDF (jobs/_lib/fetch_pool.py: robots.txt, pacing, size bound,
sha256) -> page text and instrument location with jobs/fr-pages/frpages.py (source-ladder's printed-page locator)
-> GPO PREMIS SHA-256 for the issue (jobs/official-fixity/fixity.py) -> target sentence with
jobs/selden-common/selden_common.py. Pages already held by jobs/fr-pages are read offline from their committed
text, with no request.
"""
from __future__ import annotations

import concurrent.futures
import csv
import json
import os
import re
import sys
import threading
import time
import urllib.parse
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
JOBS = HERE.parent
for p in ("_lib", "selden-common", "fr-pages", "source-ladder", "official-fixity"):
    sys.path.insert(0, str(JOBS / p))
from fetch_pool import FetchPool, FetchError  # noqa: E402
import selden_common as S  # noqa: E402
import frpages  # noqa: E402  (read-only reuse: link service, page text, instrument locator, page extract)
import fixity  # noqa: E402  (read-only reuse: GPO PREMIS reader)

csv.field_size_limit(min(2 ** 31 - 1, 10 ** 9))
UA = "EO-Road-System/1.0 (Selden acting-instrument texts; owner-run research)"
LINK = "https://www.govinfo.gov/link/fr/{vol}/{page}"
ISSUE = re.compile(r"/content/pkg/(FR-\d{4}-\d{2}-\d{2})/pdf/(FR-\d{4}-\d{2}-\d{2})\.pdf$")
FR_IN_LABEL = re.compile(r"\b(\d{1,2})\s*F\.?\s?R\.?\s*(\d{1,5})\b")
NON_EO = ("PLO", "PROC", "NOTICE", "REORG_PLAN", "TRANSFER_ORDER", "MEMORANDUM", "PRES_DETERMINATION",
          "CANAL_ZONE_ORDER", "FS_REG", "ACT", "STAT", "PL")
GRADE = ("government_printed_federal_register_issue (govinfo scan of the daily Federal Register; text is the scan's "
         "OCR layer)")


def read_csv(p):
    if not Path(p).is_file():
        return []
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def wanted(repo: Path):
    rt = {r["instrument_id"] for r in read_csv(repo / "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv")}
    dates = S.order_dates(repo)
    plo = {r["plo_id"]: r for r in read_csv(repo / "jobs/shepard-citations/output/PLO_TABLE.csv")}
    items = {}
    for origin in ("jobs/later-events/output/EDGES.csv", "jobs/shepard-citations/output/EDGES.csv"):
        for r in read_csv(repo / origin):
            a, t = r["acting_id"], r["target_id"]
            prefix = a.split(":", 1)[0] if a else ""
            if t not in rt or (a and prefix not in NON_EO):
                continue
            if S.mech_class(r["mechanism"]) not in ("ending", "modifying") and r["mechanism"] != "continuation":
                continue
            vol = page = None
            if a.startswith("PLO:") and a in plo and plo[a]["fr_volume"]:
                vol, page = int(plo[a]["fr_volume"]), int(plo[a]["fr_page"])
            else:
                m = FR_IN_LABEL.search(r.get("acting_label") or "")
                if m:
                    vol, page = int(m.group(1)), int(m.group(2))
            if not vol or not (1 <= vol <= 58):
                continue
            actor = a or f"FRPAGE:{vol}-{page}"
            key = (vol, page)
            it = items.setdefault(key, {"vol": vol, "page": page, "actor": actor, "label": "", "targets": {},
                                        "origins": set()})
            if len(r.get("acting_label") or "") > len(it["label"]):
                it["label"] = r["acting_label"]
            tgt = it["targets"].setdefault(t, {"mechanisms": set(), "date": dates.get(t, "")})
            tgt["mechanisms"].add(r["mechanism"])
            it["origins"].add(r["evidence_type"])
    out = []
    for (vol, page), it in sorted(items.items()):
        it["origins"] = sorted(it["origins"])
        for t in it["targets"].values():
            t["mechanisms"] = sorted(t["mechanisms"])
        out.append(it)
    # Most target orders first, then oldest page.
    out.sort(key=lambda i: (-len(i["targets"]), i["vol"], i["page"]))
    return out


def fr_pages_held(repo: Path):
    """(vol, page) -> (source record, text) for pages jobs/fr-pages already holds as committed extracts."""
    base = repo / "jobs/fr-pages/output"
    held = {}
    for r in S.read_jsonl(base / "SOURCES.jsonl"):
        tp = base / (r.get("text_path") or "")
        cp = base / (r.get("cache_path") or "")
        if r.get("fr_volume") and tp.is_file() and cp.is_file() and S.sha256(cp.read_bytes()) == r.get("sha256"):
            held[(int(r["fr_volume"]), int(r["fr_page"]))] = (r, tp.read_text(encoding="utf-8"))
    return held


def _pdf_text(raw, wanted=None):
    return frpages.pdf_pages(raw, wanted)


class Run:
    def __init__(self, out: Path, cache: Path, workers=4, transport=None, max_requests=3000, max_minutes=240,
                 max_download=30_000_000_000, commit_extract_bytes=80_000_000, premis=None, extract_procs=2):
        self.out = out
        self.pool = FetchPool(cache / "govinfo", workers=workers, per_host=6, transport=transport,
                              max_bytes=450_000_000, timeout=180, user_agent=UA, min_interval=0.1,
                              max_cache_bytes=2 * 1024 ** 3)
        self.max_requests, self.max_download = max_requests, max_download
        self.deadline = time.monotonic() + max_minutes * 60
        self.commit_extract_bytes, self.committed = commit_extract_bytes, 0
        self.premis = premis or (lambda pkg: fixity.check_one(
            {"package": pkg, "filename": pkg + ".pdf", "url": f"https://www.govinfo.gov/content/pkg/{pkg}/pdf/{pkg}.pdf",
             "shas": set(), "ids": set(), "found_in": set()}))
        self.lock = threading.Lock()
        self.sources, self.fragments, self.rows, self.failures = [], [], [], []
        self.procs = concurrent.futures.ProcessPoolExecutor(extract_procs) if extract_procs else None
        (out / "texts").mkdir(parents=True, exist_ok=True)
        (out / "captures").mkdir(parents=True, exist_ok=True)

    def budget(self):
        return (self.pool.requests < self.max_requests and self.pool.bytes_downloaded < self.max_download
                and time.monotonic() < self.deadline)

    def link(self, vol, page):
        url = LINK.format(vol=vol, page=page)
        status, headers, body = self.pool.request(url)
        body.close()
        if status in (301, 302, 303, 307, 308) and headers.get("location"):
            nxt = urllib.parse.urljoin(url, headers["location"])
            frag = urllib.parse.urlsplit(nxt).fragment or ""
            m = re.search(r"page=(\d+)", frag)
            return urllib.parse.urldefrag(nxt)[0], (int(m.group(1)) if m else None)
        raise FetchError(f"link service HTTP {status}")

    def page_texts(self, raw, wanted=None):
        if self.procs:
            return self.procs.submit(_pdf_text, raw, wanted).result()
        return _pdf_text(raw, wanted)

    def emit(self, it, text, src, cite_src, how, conf, notes):
        """Locate each target's sentence in the held page text and write fragments and rows."""
        lo, hi, own = S.own_span(text, it["actor"])
        for t, info in sorted(it["targets"].items()):
            # Only the instrument's own text counts: the page may also print neighbouring documents.
            hits = S.find_citations(text, t, info["date"] or None, within=(lo, hi))
            if not hits and info["date"]:
                hits = [dict(h, flags_extra=["date_only_citation"]) for h in
                        S.find_citations(text, t, info["date"], allow_date_only=True, within=(lo, hi))]
            if not own:
                hits = [dict(h, mechanism_class="mention", flags_extra=(h.get("flags_extra") or []) +
                             ["instrument_heading_not_found_neighbouring_text_possible"]) for h in hits]
            b = S.best_hit(hits)
            row = {"actor": it["actor"], "fr": f"{it['vol']} FR {it['page']}", "target_id": t,
                   "lead_mechanisms": "|".join(info["mechanisms"]), "route": how, "location_confidence": conf,
                   "located": bool(b), "mechanism_printed": b["mechanism"] if b else "",
                   "acting_on_target": S.acting_on_target(b) if b else False,
                   "date_matches_target": b["date_match"] if b else "", "citation_form": b["form"] if b else "",
                   "source_sha256": cite_src["sha256"], "quote": S.cites.squeeze(b["quote"])[:300] if b else ""}
            self.rows.append(row)
            if not b:
                continue
            flags = list(b.get("flags_extra") or [])
            if conf != "high":
                flags.append(f"instrument_location_{conf}")
            self.fragments.append(S.fragment(
                t, it["actor"], it["label"][:200] or f"instrument printed at {it['vol']} FR {it['page']}", b, cite_src,
                "selden-fr-acting", "", "see the instrument's own date in the quoted page", "selden_fr_page_sentence",
                flags=flags, extra={"fr_citation": f"{it['vol']} FR {it['page']}", "lead_mechanisms": info["mechanisms"],
                                    "issue_sha256": src.get("sha256"), "gpo_premis_match": src.get("gpo_premis_match"),
                                    "location_notes": notes}))

    def offline(self, it, rec, text):
        src = dict(rec)
        self.emit(it, text, src, {"source_id": "fr-pages:" + rec["sha256"][:12], "url": rec["url"],
                                  "sha256": rec["sha256"], "page_or_item": rec.get("page_or_item"),
                                  "text_path": "../../fr-pages/output/" + rec["text_path"]},
                  "fr-pages committed extract (no request)", rec.get("location_confidence") or "", rec.get(
                      "location_notes") or [])

    def one(self, it):
        vol, page = it["vol"], it["page"]
        issue_url, hint = self.link(vol, page)
        m = ISSUE.search(issue_url)
        if not m:
            raise FetchError("not a daily-issue PDF: " + issue_url)
        pkg = m.group(1)
        got = self.pool.fetch(issue_url)
        raw = got["body"]
        if not raw.startswith(b"%PDF"):
            raise FetchError("not a PDF")
        job = {"page": page, "plo": int(it["actor"].split(":")[1]) if it["actor"].startswith("PLO:") else None,
               "printed_id": it["actor"]}
        first = None
        if hint:
            # Read only a window around the link service's page hint first (a 1980s issue has 300-500 pages).
            pages = self.page_texts(raw, list(range(max(0, hint - 4), hint + 5)))
            first, last, notes, conf = frpages.locate(pages, job, hint)
            if first is not None:
                notes = notes + ["window_read_around_link_hint"]
        if first is None:
            pages = self.page_texts(raw)
            first, last, notes, conf = frpages.locate(pages, job, hint)
        if first is None:
            raise FetchError("cited page not found in issue: " + ";".join(notes))
        body = "".join(f"\n=== PDF page {i + 1} of {len(pages)} ===\n{pages[i]}" for i in range(first, last + 1))
        header = (f"Selden acting-instrument page text. Instrument: {it['actor']} ({it['label'][:150]})\n"
                  f"Cited at {vol} FR {page}; issue {issue_url} sha256 {got['sha256']}; PDF pages {first + 1}-{last + 1}"
                  f" of {len(pages)}; location {conf} ({', '.join(notes)})\n")
        text = header + body
        name = f"FR_{vol}_{page}.txt"
        (self.out / "texts" / name).write_text(text, encoding="utf-8")
        pr = self.premis(pkg)
        gpo = pr.get("gpo_sha256") or ""
        match = bool(gpo) and gpo == got["sha256"]
        targets = sorted(it["targets"])
        src = S.source_record(
            f"fr-issue:{pkg}", it["actor"], targets, issue_url + f"#page={first + 1}", got["sha256"], got["bytes"],
            "govinfo_link_fr_then_daily_issue_pdf", f"{vol} FR {page}; {pkg}.pdf PDF pages {first + 1}-{last + 1} of "
            f"{len(pages)}", f"texts/{name}", GRADE,
            "Whole daily-issue PDF hashed; only the instrument's pages' OCR text is kept. GPO publishes the issue's "
            "SHA-256 in its PREMIS record; gpo_premis_match says whether our bytes are GPO's.",
            extra={"issue_url": issue_url, "gpo_premis_sha256": gpo, "gpo_premis_match": match,
                   "gpo_premis_result": pr.get("result"), "premis_url": pr.get("premis_url"),
                   "issue_pdf_pages": [first + 1, last + 1], "issue_page_count": len(pages),
                   "location_confidence": conf, "location_notes": notes, "fr_volume": vol, "fr_page": page,
                   "printed_instrument_id": it["actor"]})
        cite = src
        ext, tool = frpages.extract_pdf(raw, first, last)
        with self.lock:
            fits = self.committed + len(ext) <= self.commit_extract_bytes and len(ext) <= 1_500_000
            if fits:
                self.committed += len(ext)
        if fits:
            esha = S.sha256(ext)
            (self.out / "captures" / f"{esha}.pdf").write_bytes(ext)
            cite = S.source_record(
                f"fr-extract:{esha[:16]}", it["actor"], targets, issue_url + f"#page={first + 1}", esha, len(ext),
                "govinfo_daily_issue_pdf_page_extract", src["page_or_item"] + " (committed as a page extract)",
                f"texts/{name}", GRADE, f"PDF pages {first + 1}-{last + 1} extracted with {tool} from the issue PDF "
                f"whose sha256 is issue_sha256 (GPO PREMIS match: {match}); re-download the issue to re-derive.",
                cache_path=f"captures/{esha}.pdf",
                extra={"issue_url": issue_url, "issue_sha256": got["sha256"], "gpo_premis_match": match,
                       "extract_tool": tool, "location_confidence": conf, "printed_instrument_id": it["actor"]})
        with self.lock:
            self.sources.append(src)
            if cite is not src:
                self.sources.append(cite)
            self.emit(it, text, src, cite, "govinfo issue PDF", conf, notes)


def controls(rows_by_text, repo):
    """Positives: BLM's PLO table names the order by number in the PLO's subject (independent of the page OCR)."""
    plo = {r["plo_id"]: r for r in read_csv(repo / "jobs/shepard-citations/output/PLO_TABLE.csv")}
    pos = []
    for key, (actor, text) in rows_by_text.items():
        r = plo.get(actor)
        if not r:
            continue
        for ref in (r.get("eo_refs") or "").split("|"):
            m = re.match(r"(EO:\d+)(?:@[\d-]+)?=(\w+)", ref)
            if m and S.mech_class(m.group(2)) in ("ending", "modifying"):
                pos.append((m.group(1), actor, S.mech_class(m.group(2)), key))
    return S.run_controls(pos, {k: v[1] for k, v in rows_by_text.items()})


def main(repo: Path, out: Path, cache: Path, transport=None, premis=None, env=os.environ, extract_procs=2):
    out.mkdir(parents=True, exist_ok=True)
    items = wanted(repo)
    held = fr_pages_held(repo)
    limit = int(env.get("JOB_LIMIT") or 0)
    run = Run(out, cache, workers=int(env.get("JOB_WORKERS") or 8), transport=transport,
              max_requests=int(env.get("JOB_MAX_REQUESTS") or 3000),
              max_minutes=float(env.get("JOB_TIME_BUDGET_MIN") or 130), premis=premis, extract_procs=extract_procs)
    prior_dir = Path(env.get("JOB_PRIOR_OUTPUT_DIR") or (HERE / "output"))
    prior = {}
    for r in S.read_jsonl(prior_dir / "SOURCES.jsonl"):
        if r.get("source_id", "").startswith("fr-issue:") and r.get("fr_volume"):
            prior.setdefault((int(r["fr_volume"]), int(r["fr_page"])), {})["issue"] = r
        elif r.get("source_id", "").startswith("fr-extract:"):
            m = re.search(r"(\d+) FR (\d+)", r.get("page_or_item") or "")
            if m:
                prior.setdefault((int(m.group(1)), int(m.group(2))), {})["extract"] = r
    todo, offline_n, carried_n = [], 0, 0
    for it in items:
        pk = (it["vol"], it["page"])
        pr = prior.get(pk) or {}
        tp = prior_dir / (pr.get("issue", {}).get("text_path") or "-")
        if pr.get("issue") and tp.is_file():
            # Carried forward from the previous run with no request; the locator re-reads the kept page text.
            text = tp.read_text(encoding="utf-8")
            (out / "texts" / tp.name).write_text(text, encoding="utf-8")
            src = pr["issue"]
            cite = src
            ex = pr.get("extract")
            if ex and (prior_dir / ex["cache_path"]).is_file() and S.sha256((prior_dir / ex["cache_path"]).read_bytes()) == ex["sha256"]:
                (out / ex["cache_path"]).write_bytes((prior_dir / ex["cache_path"]).read_bytes())
                run.committed += ex["bytes"]
                cite = ex
            run.sources.append(src)
            if cite is not src:
                run.sources.append(cite)
            run.emit(it, text, src, cite, "carried forward from the previous run", src.get("location_confidence") or "",
                     src.get("location_notes") or [])
            carried_n += 1
            continue
        if pk in held:
            rec, text = held[(it["vol"], it["page"])]
            run.offline(it, rec, text)
            offline_n += 1
        else:
            todo.append(it)
    if limit:
        todo = todo[:limit]

    def safe(it):
        if not run.budget():
            return it, "budget"
        try:
            run.one(it)
            return it, None
        except (FetchError, ValueError, OSError) as e:
            return it, f"{type(e).__name__}: {e}"[:300]
        except Exception as e:  # a malformed PDF must not stop the run
            return it, f"{type(e).__name__}: {e}"[:300]
    n = 0
    shard = env["SELDEN_SHARD"] if "SELDEN_SHARD" in env else (
        (HERE / "SHARD").read_text().strip() if (HERE / "SHARD").is_file() else "")
    if shard:
        k, nsh = map(int, shard.split("/"))
        todo = todo[k::nsh]
    with concurrent.futures.ThreadPoolExecutor(max_workers=int(env.get("JOB_WORKERS") or 8)) as ex:
        for it, err in ex.map(safe, todo):
            n += 1
            if err:
                run.failures.append({"actor": it["actor"], "fr": f"{it['vol']} FR {it['page']}",
                                     "targets": sorted(it["targets"]), "error": err})
            if n % 50 == 0:
                print(f"selden-fr-acting: {n}/{len(todo)} pages, {run.pool.requests} requests, "
                      f"{run.pool.bytes_downloaded / 1e9:.2f} GB", flush=True)
    if run.procs:
        run.procs.shutdown()
    texts = {}
    for p in sorted((out / "texts").glob("FR_*.txt")):
        m = re.match(r"FR_(\d+)_(\d+)\.txt", p.name)
        it = next((i for i in items if (i["vol"], i["page"]) == (int(m.group(1)), int(m.group(2)))), None)
        if it:
            texts[p.name] = (it["actor"], p.read_text(encoding="utf-8"))
    for (vp), (rec, text) in held.items():
        it = next((i for i in items if (i["vol"], i["page"]) == vp), None)
        if it:
            texts["fr-pages:" + rec["text_path"]] = (it["actor"], text)
    ctl = controls(texts, repo)
    if not ctl["passed"]:
        for f in run.fragments:
            for row in f["data"]:
                row["mechanism"] = "cross_reference"
                row["flags"] = sorted(set(row["flags"]) | {"controls_failed_this_run"})
    S.write_jsonl(out / "SOURCES.jsonl", sorted(run.sources, key=lambda r: r["source_id"]))
    S.write_jsonl(out / "FRAGMENTS.jsonl", sorted(run.fragments, key=lambda f: (f["instrument_id"],
                                                                                 f["data"][0]["acting_id"])))
    S.write_jsonl(out / "FAILURES.jsonl", run.failures)
    S.write_jsonl(out / "WANTED.jsonl", [dict(i, targets={k: v for k, v in i["targets"].items()}) for i in items])
    (out / "CONTROLS.json").write_text(json.dumps(ctl, indent=1) + "\n", encoding="utf-8")
    if run.rows:
        with open(out / "LOCATED.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, list(run.rows[0]))
            w.writeheader()
            w.writerows(sorted(run.rows, key=lambda r: (r["target_id"], r["actor"])))
    issues = [s for s in run.sources if s["source_id"].startswith("fr-issue:")]
    summary = {
        "job": "selden-fr-acting", "generated_utc": S.now_utc(), "wanted_pages": len(items),
        "wanted_orders": len({t for i in items for t in i["targets"]}),
        "wanted_by_type": dict(sorted(defaultdict(int, {}).items())),
        "pages_read_offline_from_fr_pages": offline_n, "pages_carried_forward": carried_n, "pages_attempted": n, "pages_held": len(issues) + offline_n,
        "issues_gpo_premis_match": sum(1 for s in issues if s.get("gpo_premis_match")),
        "issues_gpo_premis_other": dict(defaultdict(int)),
        "pairs": len(run.rows), "pairs_located": sum(1 for r in run.rows if r["located"]),
        "pairs_acting_on_target": sum(1 for r in run.rows if r["acting_on_target"]),
        "orders_with_located_acting_sentence": len({r["target_id"] for r in run.rows if r["acting_on_target"]}),
        "extracts_committed_bytes": run.committed, "requests": run.pool.requests,
        "bytes_downloaded": run.pool.bytes_downloaded, "failures": len(run.failures),
        "controls": {k: v for k, v in ctl.items() if k not in ("misses", "false_hits")},
        "limits": "Leads only. OCR text; location and citation are machine reads. No status, census, codebook or count "
                  "change. Certified: 0.",
    }
    types = defaultdict(int)
    for i in items:
        types[i["actor"].split(":", 1)[0]] += 1
    summary["wanted_by_type"] = dict(sorted(types.items()))
    other = defaultdict(int)
    for s in issues:
        other[s.get("gpo_premis_result") or "none"] += 1
    summary["issues_gpo_premis_other"] = dict(other)
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return summary
