"""Selden FR citers: every Federal Register document from 1994 to the legal cutoff that cites an open census order,
with the official text kept and the citing sentence located as an exact span. Zero model tokens.

Route: the Federal Register API full-text search (federalregister.gov/api/v1, the Office of the Federal Register's
own index, 1994 on) for "Executive Order N", then each hit's full text from federalregister.gov. Requests go through
jobs/_lib/fetch_pool.FetchPool (HTTPS only, robots.txt obeyed, per-host throttle, every body hashed).

Outputs (OUTPUT_DIR):
  SOURCES.jsonl     one record per kept document text (sha256 of the kept bytes, text_path = cache_path)
  FRAGMENTS.jsonl   later_event_candidates: one per (target, citing document) with the located sentence span
  CITATIONS.csv     every located citation, kept or not, with its printed relation word
  SEARCHES.jsonl    one bounded search record per target order (query, window, hits, examined, located)
  CONTROLS.json     planted positive and negative controls and the measured error rates
  STATE.json        targets searched and documents examined, carried to the next run
  SUMMARY.json
No status, census, codebook or count changes. A located sentence is a lead, not a legal finding.
"""
from __future__ import annotations

import csv
import html
import http.client
import json
import os
import re
import sys
import time
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
JOBS = HERE.parent
sys.path.insert(0, str(JOBS / "_lib"))
sys.path.insert(0, str(JOBS / "selden-common"))
from fetch_pool import FetchPool, FetchError  # noqa: E402
import selden_common as S  # noqa: E402

FR_API = "https://www.federalregister.gov/api/v1/documents.json"
FIELDS = ["document_number", "title", "type", "publication_date", "signing_date", "citation", "raw_text_url",
          "pdf_url", "html_url", "executive_order_number"]  # every name must be a valid API field: one bad name
# makes every search an HTTP 400 (first shard run, 2026-11-06)
FR_START = "1994-01-01"
UA = "EO-Road-System/1.0 (Selden acting-instrument texts; owner-run research)"
GRADE = ("fr_document_full_text (federalregister.gov full text of a Federal Register document, built from GPO's "
         "XML; the govinfo PDF is the official edition)")
PRES_TYPES = {"Presidential Document"}


def retry(fn, tries=6, pause=3.0):
    last = None
    for i in range(tries):
        try:
            try:
                return fn()
            except FetchError:
                raise
            except (OSError, http.client.HTTPException, ValueError) as e:
                raise FetchError("network: " + type(e).__name__ + ": " + str(e)) from e
        except FetchError as e:
            last = e
            m = str(e)
            if m.startswith("HTTP 429"):
                time.sleep(pause * 4 * (2 ** min(i, 4)))
                continue
            if "robots" in m or m.startswith("HTTP 4") or "exceeds bound" in m or "offline" in m:
                break
            time.sleep(pause * (i + 1))
    raise last


def plain(raw: bytes) -> str:
    """The text the spans index into: the kept bytes decoded as UTF-8 (no other transformation)."""
    return raw.decode("utf-8", "replace")


def read_csv(p):
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_targets(repo: Path):
    rt = read_csv(repo / "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv")
    cat = {r["id"]: r for r in read_csv(repo / "jobs/later-events/output/CATALOG_INDEX.csv")}
    hist = set()
    p = repo / "jobs/status-history/output/FRAGMENTS.jsonl"
    if p.is_file():
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                hist.add(json.loads(line).get("instrument_id"))
            except ValueError:
                pass
    dates = S.order_dates(repo)
    out = []
    for r in rt:
        iid = r["instrument_id"]
        eo = S.parse_eo(iid)
        if not eo or eo[1] or eo[2]:
            continue  # suffixed numbers are searched by a later route
        if r["step_ending_or_current_basis"] != "open" and r["step_counterevidence"] != "open":
            continue
        c = cat.get(iid, {})
        c.setdefault("signing_date", dates.get(iid, ""))
        ready = r["text_evidence_tier"] == "original_supported" and (r["provisional_status"] or iid in hist)
        out.append({"id": iid, "number": eo[0], "signing_date": c.get("signing_date") or dates.get(iid, ""),
                    "publication_date": c.get("publication_date") or "", "own_doc": c.get("document_number") or "",
                    "priority": 0 if ready else 1})
    # Ready orders first, newest first (they have the most later citers), then the rest.
    out.sort(key=lambda t: (t["priority"], -int(t["number"])))
    docnum_to_eo = {c["document_number"]: iid for iid, c in cat.items() if c.get("document_number")}
    return out, docnum_to_eo, cat


def control_pairs(repo: Path, cat, limit=80):
    """Positives: OFR editorial notes (independent of full-text search) saying a 1994-or-later order revoked,
    superseded or amended an earlier census order. The acting order's own FR text must cite the target."""
    seen, out = set(), []
    for r in read_csv(repo / "jobs/later-events/output/EDGES.csv"):
        a, t = r["acting_id"], r["target_id"]
        if not (a.startswith("EO:") and t.startswith("EO:")) or r["evidence_type"] not in (
                "ofr_note_on_target", "ofr_note_on_acting"):
            continue
        ca = cat.get(a)
        if not ca or (ca.get("publication_date") or "") < FR_START or not ca.get("raw_text_url"):
            continue
        cls = S.mech_class(r["mechanism"])
        if cls not in ("ending", "modifying") or (a, t) in seen:
            continue
        seen.add((a, t))
        out.append((t, a, cls, ca["raw_text_url"]))
    out.sort(key=lambda x: (x[1], x[0]))
    step = max(1, len(out) // limit)
    return out[::step][:limit]


class Run:
    def __init__(self, out: Path, cache: Path, workers=4, transport=None, max_requests=12000, max_minutes=280,
                 commit_bytes=200_000_000, max_doc_bytes=400_000, per_order_docs=40, prior=None, interval=0.1):
        self.out, self.max_requests, self.deadline = out, max_requests, time.monotonic() + max_minutes * 60
        self.commit_bytes, self.max_doc_bytes, self.per_order_docs = commit_bytes, max_doc_bytes, per_order_docs
        # At the shared pool's ceiling (owner, 2026-11-06: download as fast as allowed): 6 requests in flight per
        # host, 0.1 s apart, robots.txt still obeyed; orders are processed on `workers` threads.
        self.pool = FetchPool(cache / "fr", workers=workers, per_host=6, transport=transport,
                              max_bytes=12_000_000, timeout=90, user_agent=UA, min_interval=interval,
                              max_cache_bytes=1024 ** 3)
        self.prior = prior or {}
        self.committed = 0
        self.sources, self.fragments, self.citations, self.searches, self.failures = {}, [], [], [], []
        self.doc_text = {}   # docnum -> (raw, meta) for this run
        import threading
        self.lock = threading.RLock()
        (out / "texts").mkdir(parents=True, exist_ok=True)

    def budget(self):
        return self.pool.requests < self.max_requests and time.monotonic() < self.deadline

    def search(self, t):
        lo = max(FR_START, t["publication_date"] or FR_START)
        docs, page, total = [], 1, 1
        q0 = [("conditions[term]", f'"Executive Order {t["number"]}"'),
              ("conditions[publication_date][gte]", lo), ("conditions[publication_date][lte]", S.LEGAL_CUTOFF),
              ("per_page", "1000"), ("order", "oldest")] + [("fields[]", f) for f in FIELDS]
        urls = []
        while page <= total and page <= 10:
            url = FR_API + "?" + urllib.parse.urlencode(q0 + [("page", str(page))])
            urls.append(url)
            raw = retry(lambda: self.pool.fetch(url))["body"]
            d = json.loads(raw.decode("utf-8"))
            total = int(d.get("total_pages") or 1)
            docs += [r for r in (d.get("results") or []) if isinstance(r, dict) and r.get("document_number")]
            if not d.get("count"):
                break
            page += 1
        return docs, urls, lo

    def text_of(self, doc):
        num = doc["document_number"]
        if num in self.doc_text:
            return self.doc_text[num]
        url = doc.get("raw_text_url")
        if not url:
            raise FetchError("no raw_text_url")
        got = retry(lambda: self.pool.fetch(url))
        self.doc_text[num] = (got["body"], {"url": url, "sha256": got["sha256"], "bytes": got["bytes"]})
        return self.doc_text[num]

    def keep(self, doc, raw, meta, targets, acting_id):
        with self.lock:
            return self._keep(doc, raw, meta, targets, acting_id)

    def _keep(self, doc, raw, meta, targets, acting_id):
        num = doc["document_number"]
        if num in self.sources:
            self.sources[num]["instrument_ids"] = sorted(set(self.sources[num]["instrument_ids"]) | set(targets),
                                                         key=lambda x: (x != acting_id, x))
            return self.sources[num]
        if len(raw) > self.max_doc_bytes or self.committed + len(raw) > self.commit_bytes:
            return None
        name = f"fr-{re.sub(r'[^A-Za-z0-9._-]', '_', num)}.txt"
        (self.out / "texts" / name).write_bytes(raw)
        self.committed += len(raw)
        rec = S.source_record(
            f"fr:doc:{num}", acting_id, targets, meta["url"], meta["sha256"], meta["bytes"],
            "fr_api_fulltext_search_then_document_text",
            f"{doc.get('citation') or ''}; FR Doc. {num}; {doc.get('type') or ''}: {doc.get('title') or ''}".strip(),
            f"texts/{name}", GRADE,
            "Full text of a later Federal Register document that prints a census order's number. Kept because it "
            f"prints a relation word near the citation, is a presidential document, or is the newest citer. "
            f"published={doc.get('publication_date')}; signed={doc.get('signing_date')}; pdf={doc.get('pdf_url')}; "
            f"html={doc.get('html_url')}. Leads only.",
            cache_path=f"texts/{name}",
            retrieved=(self.prior.get(num) or {}).get("retrieved_utc") if (self.prior.get(num) or {}).get(
                "sha256") == meta["sha256"] else None,
            extra={"publication_date": doc.get("publication_date"), "fr_document_type": doc.get("type"),
                   "pdf_url": doc.get("pdf_url")})
        self.sources[num] = rec
        return rec

    def process(self, t, docnum_to_eo):
        docs, urls, lo = self.search(t)
        docs = [d for d in docs if d["document_number"] != t["own_doc"]]
        # Presidential documents first, then newest agency documents.
        docs.sort(key=lambda d: (d.get("type") not in PRES_TYPES, -(int(d["publication_date"].replace("-", "")) if
                                                                     d.get("publication_date") else 0)))
        examined, located, acting, newest_mention_kept = 0, 0, 0, False
        for doc in docs[: self.per_order_docs]:
            if not self.budget():
                break
            try:
                raw, meta = self.text_of(doc)
            except FetchError as e:
                self.failures.append({"target": t["id"], "document": doc["document_number"], "error": str(e)[:200]})
                continue
            examined += 1
            text = plain(raw)
            hits = S.find_citations(text, t["id"], t["signing_date"] or None)
            if not hits:
                continue
            located += 1
            b = S.best_hit(hits)
            acts = S.acting_on_target(b)
            acting += acts
            num = doc["document_number"]
            acting_id = docnum_to_eo.get(num) or ("FRDOC:" + num)
            pres = doc.get("type") in PRES_TYPES
            want = pres or acts or not newest_mention_kept
            src = self.keep(doc, raw, meta, [t["id"]], acting_id) if want else None
            if src and not acts and not pres:
                newest_mention_kept = True
            self.citations.append({
                "target_id": t["id"], "acting_id": acting_id, "document_number": num, "fr_type": doc.get("type"),
                "publication_date": doc.get("publication_date"), "citation": doc.get("citation"),
                "mechanism_printed": b["mechanism"], "mechanism_class": b["mechanism_class"],
                "acting_on_target": acts, "negated": b["negated"], "target_printed_as_actor": b["actor_named"],
                "date_matches_target": b["date_match"], "sentences_citing": len(hits),
                "kept_text": bool(src), "url": meta["url"], "sha256": meta["sha256"],
                "quote": S.cites.squeeze(b["quote"])[:400]})
            if src:
                self.fragments.append(S.fragment(
                    t["id"], acting_id, f"FR Doc. {num} ({doc.get('citation') or ''}): {doc.get('title') or ''}"[:200],
                    b, src, "selden-fr-citers", doc.get("signing_date") or doc.get("publication_date"),
                    "signing date printed by the FR API" if doc.get("signing_date") else
                    "publication date (not an effective date)", "selden_fr_fulltext_sentence",
                    flags=([] if pres else ["agency_document_not_presidential"]),
                    extra={"fr_document_type": doc.get("type"), "publication_date": doc.get("publication_date")}))
        self.searches.append({
            "instrument_id": t["id"], "repository": "Federal Register full text (federalregister.gov API v1, 1994 on)",
            "query_or_scope": f'documents whose full text matches "Executive Order {t["number"]}", published '
                              f'{lo} to {S.LEGAL_CUTOFF}', "checked_on": S.now_utc()[:10], "query_urls": urls,
            "hits": len(docs), "examined": examined, "complete": examined >= min(len(docs), self.per_order_docs)
            and len(docs) <= self.per_order_docs, "documents_citing": located, "documents_acting_on_target": acting,
            "limits": "Full-text search covers 1994 on only; a hit list over the per-order cap is marked incomplete; "
                      "absence of a hit is bounded to this query and is not proof that no instrument acted."})


def controls(run: Run, pairs):
    texts, positives = {}, []
    for (t, a, cls, url) in pairs:
        if not run.budget():
            break
        try:
            got = retry(lambda: run.pool.fetch(url))
        except FetchError as e:
            run.failures.append({"control": a, "error": str(e)[:200]})
            continue
        texts[a] = plain(got["body"])
        positives.append((t, a, cls, a))
    return S.run_controls(positives, texts)


def main(repo: Path, out: Path, cache: Path, transport=None, env=os.environ):
    out.mkdir(parents=True, exist_ok=True)
    prior_dir = Path(env.get("JOB_PRIOR_OUTPUT_DIR") or (HERE / "output"))
    # Earlier outputs to carry forward: this job's previous output, then any runner-shard outputs copied into
    # data/shards/<k>/ (parallel runner branches; see README). Later directories add what earlier ones lack.
    priors = [prior_dir] + sorted(p for p in (HERE / "data" / "shards").glob("*") if p.is_dir())
    prior_src = {}
    for d in priors:
        for r in S.read_jsonl(d / "SOURCES.jsonl"):
            prior_src.setdefault(r.get("source_id", "")[7:], r)
    run = Run(out, cache, workers=int(env.get("JOB_WORKERS") or 12), transport=transport,
              max_requests=int(env.get("JOB_MAX_REQUESTS") or 40000),
              max_minutes=float(env.get("JOB_TIME_BUDGET_MIN") or 300),
              commit_bytes=int(env.get("SELDEN_COMMIT_BYTES") or 120_000_000), prior=prior_src)
    targets, docnum_to_eo, cat = load_targets(repo)
    limit = int(env.get("JOB_LIMIT") or 0)
    ctl = controls(run, control_pairs(repo, cat, int(env.get("SELDEN_CONTROLS") or 80)))
    (out / "CONTROLS.json").write_text(json.dumps(ctl, indent=1) + "\n", encoding="utf-8")
    if not ctl["passed"]:
        print("controls failed: every acting fragment is downgraded to cross_reference", flush=True)
    done_before = set()
    carried, relocated = 0, 0
    seen_frag, seen_search, seen_cite = set(), set(), set()
    for d in priors:
        if (d / "STATE.json").is_file():
            try:
                done_before |= set(json.loads((d / "STATE.json").read_text(encoding="utf-8")).get("searched") or [])
            except ValueError:
                pass
        # Carry earlier results forward (texts re-copied so the output stays self-contained).
        for r in S.read_jsonl(d / "SOURCES.jsonl"):
            key = r["source_id"][7:]
            p = d / r.get("cache_path", "")
            if key in run.sources:
                run.sources[key]["instrument_ids"] = sorted(set(run.sources[key]["instrument_ids"]) |
                                                           set(r.get("instrument_ids") or []),
                                                           key=lambda x: (x != r["instrument_ids"][0], x))
                continue
            if r.get("cache_path") and p.is_file() and S.sha256(p.read_bytes()) == r["sha256"]:
                (out / r["cache_path"]).parent.mkdir(parents=True, exist_ok=True)
                (out / r["cache_path"]).write_bytes(p.read_bytes())
                run.sources[key] = r
                run.committed += r.get("bytes") or 0
                carried += 1
        for f in S.read_jsonl(d / "FRAGMENTS.jsonl"):
            row = f["data"][0]
            fk = (f["instrument_id"], row["source_id"])
            if fk in seen_frag:
                continue
            seen_frag.add(fk)
            if row.get("located_by") != S.LOCATOR_VERSION and row.get("text_path") and (out / row["text_path"]).is_file():
                # A new locator version re-reads the kept text: no request.
                text = plain((out / row["text_path"]).read_bytes())
                b = S.best_hit(S.find_citations(text, f["instrument_id"]))
                if not b:
                    continue
                src = {"source_id": row["source_id"], "url": row["source_url"], "sha256": row["source_sha256"],
                       "page_or_item": row.get("page_or_item"), "text_path": row["text_path"]}
                keep = {k: row[k] for k in ("fr_document_type", "publication_date") if k in row}
                f = S.fragment(f["instrument_id"], row["acting_id"], row["acting_label"], b, src, "selden-fr-citers",
                               row["date_candidate"], row["date_basis"], row["evidence_type"],
                               flags=[x for x in row.get("flags", []) if x == "agency_document_not_presidential"],
                               extra=keep)
                relocated += 1
            run.fragments.append(f)
        for r in S.read_jsonl(d / "SEARCHES.jsonl"):
            if r["instrument_id"] not in seen_search:
                seen_search.add(r["instrument_id"])
                run.searches.append(r)
        if (d / "CITATIONS.csv").is_file():
            for r in read_csv(d / "CITATIONS.csv"):
                ck = (r["target_id"], r["document_number"])
                if ck not in seen_cite:
                    seen_cite.add(ck)
                    run.citations.append(r)
    todo = [t for t in targets if t["id"] not in done_before]
    if limit:
        todo = todo[:limit]
    shard = env["SELDEN_SHARD"] if "SELDEN_SHARD" in env else (
        (HERE / "SHARD").read_text().strip() if (HERE / "SHARD").is_file() else "")
    if shard:  # "k/n": this runner takes every n-th order starting at k (parallel runner branches)
        k, nsh = map(int, shard.split("/"))
        todo = todo[k::nsh]
    import concurrent.futures
    n = 0

    def one(t):
        if not run.budget():
            return t, "budget"
        try:
            run.process(t, docnum_to_eo)
            return t, None
        except (FetchError, ValueError, OSError) as e:
            return t, str(e)[:200]
    with concurrent.futures.ThreadPoolExecutor(max_workers=int(env.get("SELDEN_ORDER_THREADS") or 12)) as ex:
        for t, err in ex.map(one, todo):
            if err == "budget":
                continue
            if err:
                run.failures.append({"target": t["id"], "error": err})
            else:
                done_before.add(t["id"])
            n += 1
            if n % 200 == 0:
                print(f"selden-fr-citers: {n}/{len(todo)} targets, {run.pool.requests} requests, "
                      f"{len(run.fragments)} fragments", flush=True)
    if not ctl["passed"]:
        for f in run.fragments:
            for row in f["data"]:
                row["mechanism"] = "cross_reference"
                row["flags"] = sorted(set(row["flags"]) | {"controls_failed_this_run"})
    S.write_jsonl(out / "SOURCES.jsonl", sorted(run.sources.values(), key=lambda r: r["source_id"]))
    S.write_jsonl(out / "FRAGMENTS.jsonl", sorted(run.fragments, key=lambda f: (f["instrument_id"],
                                                                                 f["data"][0]["source_id"])))
    S.write_jsonl(out / "SEARCHES.jsonl", sorted(run.searches, key=lambda r: r["instrument_id"]))
    S.write_jsonl(out / "FAILURES.jsonl", run.failures)
    cols = ["target_id", "acting_id", "document_number", "fr_type", "publication_date", "citation",
            "mechanism_printed", "mechanism_class", "acting_on_target", "negated", "target_printed_as_actor",
            "date_matches_target", "sentences_citing", "kept_text", "url", "sha256", "quote"]
    with open(out / "CITATIONS.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(run.citations, key=lambda r: (r["target_id"], r["document_number"])))
    (out / "STATE.json").write_text(json.dumps({"searched": sorted(done_before)}, indent=0) + "\n", encoding="utf-8")
    acting_rows = [r for r in run.citations if str(r["acting_on_target"]) in ("True", "true")]
    summary = {
        "job": "selden-fr-citers", "generated_utc": S.now_utc(), "legal_cutoff": S.LEGAL_CUTOFF,
        "targets_total": len(targets), "targets_searched_total": len(done_before), "targets_searched_this_run": n,
        "requests": run.pool.requests, "bytes_downloaded": run.pool.bytes_downloaded,
        "documents_examined_this_run": len(run.doc_text), "sources_kept": len(run.sources),
        "sources_carried": carried, "fragments_relocated_with_new_locator": relocated, "committed_text_bytes": run.committed,
        "citations": len(run.citations), "citations_acting_on_target": len(acting_rows),
        "orders_with_a_citing_document": len({r["target_id"] for r in run.citations}),
        "orders_with_an_acting_citation": len({r["target_id"] for r in acting_rows}),
        "fragments": len(run.fragments), "failures": len(run.failures),
        "controls": {k: v for k, v in ctl.items() if k not in ("misses", "false_hits")},
        "limits": "Leads only: a printed relation word near a citation. 1994 on only (full-text search coverage).",
    }
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return summary
