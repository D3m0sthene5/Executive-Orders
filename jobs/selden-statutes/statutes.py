"""Selden statutes: the Statutes at Large texts that act on or carry census orders, from govinfo's STATUTE
collection (volumes 1-64, 1789-1950, digitized by GPO in 2024; volume 65 on, 1951 on). Zero model tokens.

Two wanted classes, both built here from committed job outputs:
  acting  - statutes the finding jobs name as acting on an order (jobs/later-events EDGES acting PL:/STAT:/ACT:
            with a "N Stat. P" citation or a public-law number), with the sentence that cites the order located;
  basis   - statutes an open order's own held text cites as "N Stat. P" (the law it rests on, whose expiry or repeal
            may end it). The order's citing sentence is located in the order's own held text; the statute's text is
            held so a claim can quote it. Nothing here says that the statute ended or carries the order.

Route: govinfo link service /link/statute/{vol}/{page} (or /link/statute/{congress}/public/{law}) read without
following the redirect, then the granule PDF it names, through jobs/_lib/fetch_pool.py (robots.txt, pacing, sha256).
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
for p in ("_lib", "selden-common"):
    sys.path.insert(0, str(JOBS / p))
from fetch_pool import FetchPool, FetchError  # noqa: E402
import selden_common as S  # noqa: E402

csv.field_size_limit(min(2 ** 31 - 1, 10 ** 9))
UA = "EO-Road-System/1.0 (Selden acting-instrument texts; owner-run research)"
LINK_PAGE = "https://www.govinfo.gov/link/statute/{vol}/{page}?link-type=pdf"
LINK_LAW = "https://www.govinfo.gov/link/statute/{congress}/public/{law}?link-type=pdf"
STAT = re.compile(r"\b(\d{1,3})\s+Stat\.?\s*,?\s+(\d{1,5})\b")
PL = re.compile(r"PL:(\d{2,3})-(\d{1,4})$")
GRANULE = re.compile(r"/content/pkg/(STATUTE-\d+[A-Z]?)/pdf/(STATUTE-[\w-]+)\.pdf$")
GRADE = ("government_printed_statutes_at_large (govinfo digitized Statutes at Large granule PDF; text is its text "
         "layer)")
TEXT_PRODUCERS = ("jobs/fr-originals/data/full_run/FRAGMENTS.jsonl", "jobs/fr-originals/output/FRAGMENTS.jsonl",
                  "jobs/app-transcriptions/output/FRAGMENTS.jsonl", "jobs/hathi-gpo-orders/output/FRAGMENTS.jsonl",
                  "jobs/wikisource-texts/output/FRAGMENTS.jsonl")


def read_csv(p):
    if not Path(p).is_file():
        return []
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def order_texts(repo: Path, wanted_ids):
    """instrument_id -> [(text_path relative to repo, sha256 of the text file)] from producers' fragments."""
    out = defaultdict(list)
    for rel in TEXT_PRODUCERS:
        p = repo / rel
        if not p.is_file():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                d = json.loads(line)
            except ValueError:
                continue
            iid = d.get("instrument_id")
            data = d.get("data") if isinstance(d.get("data"), dict) else {}
            tp = data.get("text_path")
            if iid in wanted_ids and tp:
                q = p.parent / tp
                if q.is_file():
                    out[iid].append((q.relative_to(repo).as_posix(), data.get("sha256"), data.get("url")))
    return out


def wanted(repo: Path):
    rt = {r["instrument_id"]: r for r in read_csv(repo / "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv")}
    items = {}

    def item(key, **kw):
        return items.setdefault(key, dict(kw, acting_targets={}, basis_targets={}))
    for r in read_csv(repo / "jobs/later-events/output/EDGES.csv"):
        a, t = r["acting_id"], r["target_id"]
        if t not in rt or not a.split(":", 1)[0] in ("PL", "STAT", "ACT", "PUBRES"):
            continue
        m = STAT.search(r.get("acting_label") or "")
        if m:
            key = ("page", int(m.group(1)), int(m.group(2)))
        elif PL.match(a):
            c, n = PL.match(a).groups()
            key = ("law", int(c), int(n))
        else:
            continue
        it = item(key, label=r.get("acting_label") or a, actor=a)
        it["acting_targets"].setdefault(t, set()).add(r["mechanism"])
    open_ids = {i for i, r in rt.items() if r["step_ending_or_current_basis"] == "open"}
    texts = order_texts(repo, open_ids)
    for iid, paths in texts.items():
        for rel, sha, url in paths[:2]:
            text = (repo / rel).read_text(encoding="utf-8", errors="replace")
            olo, ohi, _ = S.own_span(text, iid)  # an FR page text may also print neighbouring documents
            for m in STAT.finditer(text, olo, ohi):
                vol, page = int(m.group(1)), int(m.group(2))
                if not 1 <= vol <= 140:
                    continue
                lo, hi = S.cites.sentence_bounds(text, m.start(), m.end())
                it = item(("page", vol, page), label=f"{vol} Stat. {page}", actor=f"STAT:{vol}-{page}")
                it["basis_targets"].setdefault(iid, {"order_text_path": rel, "order_text_url": url,
                                                     "order_text_sha256": S.sha256((repo / rel).read_bytes()),
                                                     "quote": text[lo:hi], "quote_span": f"{lo}-{hi}"})
    ready = {i for i, r in rt.items() if r["text_evidence_tier"] == "original_supported" and r["provisional_status"]}
    out = []
    for key, it in items.items():
        it["key"] = key
        it["priority"] = (-len(it["acting_targets"]) * 10 - len(set(it["basis_targets"]) & ready)
                          - len(it["basis_targets"]) / 100)
        out.append(it)
    out.sort(key=lambda i: (i["priority"], i["key"]))
    return out


class Run:
    def __init__(self, out, cache, workers=4, transport=None, max_requests=6000, max_minutes=240,
                 commit_bytes=60_000_000, max_pdf_commit=400_000, prior_dir=None):
        self.prior_dir = Path(prior_dir) if prior_dir else Path("/nonexistent")
        # Orders whose statutes are committed in full whatever their size (a claim-kit supplement needs held bytes).
        cf = HERE / "COMMIT_FOR"
        self.commit_for = set(cf.read_text().split()) if cf.is_file() else set()
        self.commit_for_cap, self.commit_for_bytes = 250_000_000, 0
        self.prior = {r.get("link_url"): r for r in S.read_jsonl(self.prior_dir / "SOURCES.jsonl")}
        self.out = out
        self.pool = FetchPool(cache / "statute", workers=workers, per_host=6, transport=transport,
                              max_bytes=80_000_000, timeout=120, user_agent=UA, min_interval=0.1,
                              max_cache_bytes=1024 ** 3)
        self.max_requests, self.deadline = max_requests, time.monotonic() + max_minutes * 60
        self.commit_bytes, self.max_pdf_commit, self.committed = commit_bytes, max_pdf_commit, 0
        self.lock = threading.Lock()
        self.sources, self.fragments, self.basis, self.rows, self.failures = [], [], [], [], []
        (out / "texts").mkdir(parents=True, exist_ok=True)
        (out / "pdf").mkdir(parents=True, exist_ok=True)

    def budget(self):
        return self.pool.requests < self.max_requests and time.monotonic() < self.deadline

    def link(self, it):
        kind, a, b = it["key"]
        url = LINK_PAGE.format(vol=a, page=b) if kind == "page" else LINK_LAW.format(congress=a, law=b)
        status, headers, body = self.pool.request(url)
        body.close()
        if status in (301, 302, 303, 307, 308) and headers.get("location"):
            return urllib.parse.urldefrag(urllib.parse.urljoin(url, headers["location"]))[0], url
        raise FetchError(f"link service HTTP {status}")

    def carried(self, it):
        kind, a, b = it["key"]
        url = LINK_PAGE.format(vol=a, page=b) if kind == "page" else LINK_LAW.format(congress=a, law=b)
        r = self.prior.get(url)
        if not r or not (self.prior_dir / r["text_path"]).is_file():
            return None
        if not r.get("cache_path") and self.wants_full(it):
            return None  # refetch so the whole PDF can be committed
        raw = (self.prior_dir / r["cache_path"]).read_bytes() if r.get("cache_path") and \
            (self.prior_dir / r["cache_path"]).is_file() else None
        if r.get("cache_path") and (raw is None or S.sha256(raw) != r["sha256"]):
            return None
        return r, (self.prior_dir / r["text_path"]).read_text(encoding="utf-8"), raw

    def wants_full(self, it):
        return bool(self.commit_for & (set(it["acting_targets"]) | set(it["basis_targets"])))

    def one(self, it):
        c = self.carried(it)
        if c:
            # Carried forward from the previous run with no request (granule PDFs are stable files).
            r, text, raw = c
            (self.out / r["text_path"]).write_text(text, encoding="utf-8")
            if raw is not None:
                (self.out / r["cache_path"]).write_bytes(raw)
                with self.lock:
                    self.committed += len(raw)
            name = r["granule"]
            targets = sorted(set(it["acting_targets"]) | set(it["basis_targets"]))
            ids = [r["instrument_ids"][0]] + [t for t in targets if t != r["instrument_ids"][0]]
            self.finish(it, dict(r, instrument_ids=ids, carried_forward=True), text, name, r["page_number_printed"],
                        r["url"])
            return
        target_url, link_url = self.link(it)
        m = GRANULE.search(target_url)
        if not m:
            raise FetchError("not a Statutes at Large granule PDF: " + target_url)
        got = self.pool.fetch(target_url)
        raw = got["body"]
        if not raw.startswith(b"%PDF"):
            raise FetchError("not a PDF")
        import io
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(raw))
        pages = []
        for i, pg in enumerate(reader.pages):
            try:
                pages.append(pg.extract_text() or "")
            except Exception as e:  # keep going on one bad page
                pages.append(f"[page text unreadable: {type(e).__name__}]")
        kind, a, b = it["key"]
        body = "".join(f"\n=== PDF page {i + 1} of {len(pages)} ===\n{t}" for i, t in enumerate(pages))
        header = (f"Selden statute text. Wanted: {it['label'][:150]}; granule {m.group(2)}; {target_url} sha256 "
                  f"{got['sha256']} ({len(pages)} PDF pages).\n")
        text = header + body
        # Identity check: the wanted page number printed in the text (running head or page number).
        identity = None
        if kind == "page":
            identity = bool(re.search(r"(?<![\d,])" + str(b) + r"(?![\d,])", body))
        name = m.group(2)
        (self.out / "texts" / f"{name}.txt").write_text(text, encoding="utf-8")
        cache_path = None
        with self.lock:
            if len(raw) <= self.max_pdf_commit and self.committed + len(raw) <= self.commit_bytes:
                self.committed += len(raw)
                cache_path = f"pdf/{name}.pdf"
            elif self.wants_full(it) and self.commit_for_bytes + len(raw) <= self.commit_for_cap:
                self.commit_for_bytes += len(raw)
                cache_path = f"pdf/{name}.pdf"
        if cache_path:
            (self.out / cache_path).write_bytes(raw)
        targets = sorted(set(it["acting_targets"]) | set(it["basis_targets"]))
        actor = it["actor"] if kind == "page" else f"PL:{a}-{b}"
        src = S.source_record(
            f"statute:{name}", actor, targets, target_url, got["sha256"], got["bytes"],
            "govinfo_link_statute_then_granule_pdf", f"{name} ({it['label'][:120]})", f"texts/{name}.txt", GRADE,
            "Statutes at Large granule PDF from govinfo (GPO). Text is the PDF's text layer; for volumes 1-64 it is "
            "GPO's 2024 digitization. A statute that an order cites is not thereby shown to end or carry it.",
            cache_path=cache_path, extra={"link_url": link_url, "granule": name, "package": m.group(1),
                                          "page_number_printed": identity, "pdf_pages": len(pages)})
        self.finish(it, src, text, name, identity, target_url)

    def finish(self, it, src, text, name, identity, target_url):
        kind, a, b = it["key"]
        actor = src["instrument_ids"][0]
        with self.lock:
            self.sources.append(src)
        for t, mechs in sorted(it["acting_targets"].items()):
            hits = S.find_citations(text, t)
            bh = S.best_hit(hits)
            self.rows.append({"statute": name, "target_id": t, "class": "acting", "located": bool(bh),
                              "mechanism_printed": bh["mechanism"] if bh else "", "lead": "|".join(sorted(mechs))})
            if bh:
                with self.lock:
                    self.fragments.append(S.fragment(t, actor, it["label"][:200], bh, src, "selden-statutes", "",
                                                     "the statute's own enactment date in the quoted text",
                                                     "selden_statute_sentence",
                                                     extra={"lead_mechanisms": sorted(mechs)}))
        for t, ref in sorted(it["basis_targets"].items()):
            with self.lock:
                self.basis.append({"instrument_id": t, "kind": "statute_cited_by_order", "statute": f"{a} Stat. {b}",
                                   "statute_source_id": src["source_id"], "statute_sha256": src["sha256"],
                                   "statute_url": target_url, "statute_text_path": f"texts/{name}.txt",
                                   "page_number_printed": identity, **ref,
                                   "note": "The order's own text cites this statute. Whether the order rests on it, "
                                           "and whether its expiry or repeal ended the order, is a legal reading."})
                self.rows.append({"statute": name, "target_id": t, "class": "basis", "located": True,
                                  "mechanism_printed": "", "lead": "cited by the order"})


def main(repo: Path, out: Path, cache: Path, transport=None, env=os.environ):
    out.mkdir(parents=True, exist_ok=True)
    items = wanted(repo)
    limit = int(env.get("JOB_LIMIT") or 0)
    todo = items[:limit] if limit else items
    run = Run(out, cache, workers=int(env.get("JOB_WORKERS") or 12), transport=transport,
              max_requests=int(env.get("JOB_MAX_REQUESTS") or 6000),
              max_minutes=float(env.get("JOB_TIME_BUDGET_MIN") or 60),
              prior_dir=env.get("JOB_PRIOR_OUTPUT_DIR") or (HERE / "output"))

    def safe(it):
        if not run.budget():
            return it, "budget"
        try:
            run.one(it)
            return it, None
        except Exception as e:
            return it, f"{type(e).__name__}: {e}"[:300]
    n = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=int(env.get("JOB_WORKERS") or 12)) as ex:
        for it, err in ex.map(safe, todo):
            n += 1
            if err:
                run.failures.append({"key": list(it["key"]), "label": it["label"][:120], "error": err,
                                     "targets": sorted(set(it["acting_targets"]) | set(it["basis_targets"]))[:20]})
            if n % 200 == 0:
                print(f"selden-statutes: {n}/{len(todo)}, {run.pool.requests} requests", flush=True)
    S.write_jsonl(out / "SOURCES.jsonl", sorted(run.sources, key=lambda r: r["source_id"]))
    S.write_jsonl(out / "FRAGMENTS.jsonl", sorted(run.fragments, key=lambda f: f["instrument_id"]))
    S.write_jsonl(out / "BASIS.jsonl", sorted(run.basis, key=lambda r: (r["instrument_id"], r["statute"])))
    S.write_jsonl(out / "FAILURES.jsonl", run.failures)
    held = [s for s in run.sources]
    summary = {
        "job": "selden-statutes", "generated_utc": S.now_utc(), "wanted_statutes": len(items),
        "wanted_acting": sum(1 for i in items if i["acting_targets"]),
        "wanted_orders_basis": len({t for i in items for t in i["basis_targets"]}),
        "attempted": n, "held": len(held), "pdf_committed": sum(1 for s in held if s.get("cache_path")),
        "page_number_printed": sum(1 for s in held if s.get("page_number_printed")),
        "page_number_not_printed": sum(1 for s in held if s.get("page_number_printed") is False),
        "orders_with_held_basis_statute": len({b["instrument_id"] for b in run.basis}),
        "acting_pairs_located": sum(1 for r in run.rows if r["class"] == "acting" and r["located"]),
        "acting_pairs": sum(1 for r in run.rows if r["class"] == "acting"),
        "requests": run.pool.requests, "bytes_downloaded": run.pool.bytes_downloaded,
        "committed_pdf_bytes": run.committed, "failures": len(run.failures),
        "failures_by_reason": dict(sorted(defaultdict(int, {}).items())),
        "limits": "Leads only. A cited statute is not shown to end or carry the order. No status, census, codebook "
                  "or count change. Certified: 0.",
    }
    reasons = defaultdict(int)
    for f in run.failures:
        reasons[f["error"].split(":")[0]] += 1
    summary["failures_by_reason"] = dict(reasons)
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return summary
