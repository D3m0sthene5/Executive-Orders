"""Federal Register originals: the official printed text of every order in the FR.

For each order in the frozen OFR index (jobs/fr-originals/data/ofr_index):
- reuse a Stage 21 captured PDF if there is one;
- otherwise fetch the official govinfo copy through the source ladder
  (per-document PDF for 1994 on; the scanned daily issue for 1936-1994),
  find the order's own pages and save only their text.

Each order's result is saved in a state folder in the cache, so a stopped
run resumes where it left off. Outputs are rebuilt from that state each run
and always cover every order finished so far (this run, earlier runs, and
earlier committed results carried forward), so a small run never shrinks them.
Machine output = source custody and location leads, never legal conclusions.
"""
from __future__ import annotations

import csv

import json
import re
import shutil
import time
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

# 2: page locator v2 (wrong-issue rejection, windowed markers, reference filter).
STATE_VERSION = 2
PRODUCED_BY = "fr-originals"
PATHS = {
    "universe": "research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv",
    "decided": "research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv",
    "custody": "research/stage21/original_sources/CASE_ORIGINAL_SOURCE_CUSTODY.csv",
    "crosswalk": "research/stage21/sources_index/OFFICIAL_SOURCE_CASE_CROSSWALK.csv",
}
NOT_FOUND_COLUMNS = ["instrument_id", "decided", "fr_citation", "publication_date", "signing_date", "reason",
                     "permanent", "detail", "routes_tried", "last_url_tried", "downloaded_sha256"]


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def id_sort_key(iid):
    m = re.match(r"EO:(\d+)(.*)$", iid)
    return (int(m.group(1)), m.group(2)) if m else (10**9, iid)


def text_name(iid):
    import fetch_ladder
    return "EO_" + fetch_ladder.safe_name(iid.split(":", 1)[-1]) + ".txt"


# --------------------------------------------------------------------------
# Planning
# --------------------------------------------------------------------------

def build_plan(repo, index):
    """Every order in scope, decided orders first. Returns list of dicts."""
    repo = Path(repo)
    decided = set()
    if (repo / PATHS["decided"]).exists():
        decided = {r["instrument_id"] for r in read_csv(repo / PATHS["decided"])}
    universe = {}
    if (repo / PATHS["universe"]).exists():
        universe = {r["id"]: r for r in read_csv(repo / PATHS["universe"])}
    plan = []
    for iid, entry in index.items():
        plan.append({"instrument_id": iid, "decided": iid in decided, "record": entry["primary"],
                     "others": entry["others"], "category": "ofr_index"})
    for iid, row in universe.items():
        if iid in index:
            continue
        year = (row.get("date_effective") or "")[:4]
        if year == "1936":
            plan.append({"instrument_id": iid, "decided": iid in decided, "record": None, "others": [],
                         "category": "fr_volume_1_1936"})
        elif year.isdigit() and year >= "1937" and row.get("included_in_bibliography") == "1":
            plan.append({"instrument_id": iid, "decided": iid in decided, "record": None, "others": [],
                         "category": "not_in_ofr_index"})
    # Orders that need the network come first (decided before the rest); the
    # no-network NOT_FOUND categories (not in the index, 1936, 'not received for
    # publication', no FR citation) go last so JOB_LIMIT is spent on real work.
    plan.sort(key=lambda p: (not needs_network(p), not p["decided"], id_sort_key(p["instrument_id"])))
    return plan


def needs_network(item):
    rec = item.get("record") or {}
    return (item["category"] == "ofr_index" and bool(rec.get("citation"))
            and not rec.get("not_received_for_publication"))


def load_custody(repo):
    repo = Path(repo)
    out = {}
    if (repo / PATHS["custody"]).exists():
        for r in read_csv(repo / PATHS["custody"]):
            if r.get("custody_state", "").startswith("PDF_BYTES_CAPTURED") and r.get("source_repository_path"):
                out[r["instrument_id"]] = r
    return out


def load_crosswalk_pdfs(repo):
    repo = Path(repo)
    out = {}
    if (repo / PATHS["crosswalk"]).exists():
        for r in read_csv(repo / PATHS["crosswalk"]):
            if r.get("PDF_candidate", "").startswith("https://"):
                out[r["instrument_id"]] = r["PDF_candidate"]
    return out


def issue_key(item):
    """The daily issue an order needs (pre-1995 scans), or None for per-document PDFs."""
    rec = item.get("record") or {}
    if rec.get("pdf_url") or not rec.get("citation") or rec.get("not_received_for_publication"):
        return None
    pub = rec.get("publication_date") or ""
    return pub if pub and pub < "1995-01-01" else None


# --------------------------------------------------------------------------
# One order
# --------------------------------------------------------------------------

def not_found(item, reason, permanent, detail="", attempts=()):
    rec = item.get("record") or {}
    last = attempts[-1] if attempts else {}
    shas = [a["sha256"] for a in attempts if a.get("sha256")]
    return {
        "instrument_id": item["instrument_id"], "decided": "yes" if item["decided"] else "no",
        "fr_citation": rec.get("citation") or "", "publication_date": rec.get("publication_date") or "",
        "signing_date": rec.get("signing_date") or "", "reason": reason, "permanent": "yes" if permanent else "no",
        "detail": detail, "routes_tried": len(attempts), "last_url_tried": last.get("url", ""),
        "downloaded_sha256": shas[-1] if shas else "",
    }


def fragment_for(item, src, loc_note):
    rec = item.get("record") or {}
    ref = {"url": src["url"], "sha256": src["sha256"], "page_or_item": src["page_or_item"]}
    data = dict(ref)
    conf = src.get("location_confidence")
    data.update({"source_id": src["source_id"], "text_path": src["text_path"],
                 "fr_citation": rec.get("citation"), "publication_date": rec.get("publication_date"),
                 "signing_date": rec.get("signing_date"), "title": rec.get("title"),
                 "location_confidence": conf, "route": src["route"],
                 # No person has checked the pages. Job 8 must not count a fragment whose
                 # needs_page_check is true as satisfying original_text without a page check.
                 "location_verified": False, "needs_page_check": conf != "high"})
    return {"instrument_id": item["instrument_id"], "kind": "original_representation", "data": data,
            "sources": [ref], "confidence_note": loc_note, "produced_by": PRODUCED_BY}


def confidence_note(loc, scanned):
    conf = (loc or {}).get("confidence", "unknown")
    base = {
        "high": "Order's printed FR page and its number were both found; pages end at the filing line.",
        "medium": "Order found, but one check is weaker (number OCR-damaged, page found by number only, or per-document PDF without the number in its text layer).",
        "low": "Pages chosen from the printed FR page number only; the order's number was not found in the text layer.",
    }.get(conf, "Location confidence unknown.")
    kind = ("Official govinfo scan of the printed Federal Register; text is the scan's OCR layer and may contain errors and neighbouring documents."
            if scanned else "Official govinfo per-document PDF of the Federal Register printing.")
    check = (" Needs a page check before it counts as the original." if conf != "high" else "")
    return (f"Machine location lead, confidence {conf}. {base} {kind}{check} "
            "Identity, page boundaries and wording are NOT human-verified; this is not a legal conclusion.")


def text_header(iid, src):
    return (f"Instrument: {iid}\nSource: {src['url']}\nSHA-256 of the downloaded file: {src['sha256']}\n"
            f"Location: {src['page_or_item']} (confidence {src.get('location_confidence')})\n"
            "Machine-extracted text layer of the official PDF (OCR for 1936-1994 scans). May contain "
            "recognition errors and parts of neighbouring documents on the same pages. Not an "
            "authenticated transcription: check the PDF pages.\n\n")


def reuse_stage21(repo, item, custody_row, fetcher):
    """Record a Stage 21 captured PDF (already in the repo) as this order's source."""
    import eo_extract
    import fetch_ladder
    import fr_pages
    path = Path(repo) / custody_row["source_repository_path"]
    if not path.exists():
        return None
    sha = fetch_ladder.sha256_file(path)
    if sha != custody_row.get("sha256_source_bytes_if_present"):
        return {"error": f"stage21 file {custody_row['source_repository_path']} sha256 differs from custody record"}
    texts = eo_extract.pdf_texts(path, sha)
    number = item["instrument_id"].split(":", 1)[1]
    loc = fr_pages.locate_order(texts, number, single_document=True)
    rec = item.get("record") or {}
    a, b = loc["first_page"], loc["last_page"]
    raw_time = custody_row.get("attempted_utc", "")
    src = {
        "source_id": f"{PRODUCED_BY}:{item['instrument_id']}:{sha[:12]}",
        "instrument_ids": [item["instrument_id"]],
        "url": custody_row["official_PDF_candidate_URL"], "requested_url": custody_row["official_PDF_candidate_URL"],
        "sha256": sha, "bytes": path.stat().st_size, "content_type": "application/pdf",
        "retrieved_utc": normalise_utc(raw_time),
        "route": "reuse/stage21_original_sources",
        "page_or_item": f"{rec.get('citation') or item['instrument_id']}, PDF pages {a}-{b}",
        "text_path": f"texts/{text_name(item['instrument_id'])}", "cache_path": None,
        "repo_path": custody_row["source_repository_path"],
        "notes": (f"Bytes already preserved in the repo at {custody_row['source_repository_path']} (Stage 21 custody; "
                  f"Stage 21 recorded retrieval time {raw_time}); "
                  f"{len(texts)} PDF pages; marker {loc['marker_kind']}; " + "; ".join(loc["notes"])).strip("; "),
        "location_confidence": loc["confidence"],
    }
    body = "\n".join(f"=== PDF page {i} of {len(texts)} ===\n{texts[i - 1]}" for i in range(a, b + 1))
    return {"source": src, "text": body, "loc": loc, "scanned": False}


def normalise_utc(text):
    """'2026-10-17T17:49:56.920745+00:00' -> '2026-10-17T17:49:56Z' (other text is kept as is)."""
    try:
        dt = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except ValueError:
        return text
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def routes_for(item, extra_pdf=None):
    import fetch_ladder
    rec = item["record"]
    w = fetch_ladder.Wanted(wanted_id=item["instrument_id"], instrument_ids=[item["instrument_id"]],
                            citation="EO " + item["instrument_id"].split(":", 1)[1], step="original_text",
                            expect="pdf", eo_record=rec, requested_by=PRODUCED_BY)
    if extra_pdf and extra_pdf != rec.get("pdf_url"):
        w.urls = [extra_pdf]
    routes = [r for r in fetch_ladder.plan_routes(w, tiers=("given", "alternate", "wayback_given", "official", "wayback_official"))
              if not r.route.startswith("federalregister_") and r.route != "alt_govinfo_html"]
    return w, routes


def process_order(ctx, item):
    """Return a state dict for one order (network only through ctx['ladder'])."""
    import eo_extract
    import fetch_ladder
    iid = item["instrument_id"]
    rec = item.get("record")
    state = {"state_version": STATE_VERSION, "instrument_id": iid, "status": "not_found", "permanent": True,
             "source": None, "fragment": None, "not_found": None, "attempts": [], "text_file": None,
             "processed_utc": fetch_ladder.now_utc()}
    if item["category"] == "fr_volume_1_1936":
        state["not_found"] = not_found(item, "fr_volume_1_1936_not_in_ofr_index", True,
                                       "The universe dates this order to 1936. The Federal Register began on 14 March 1936; volume 1 is on govinfo, but the OFR index (which starts in 1937) gives no citation. Orders signed before 14 March 1936 were never in the FR. Locate by signing date (later job).")
        return state
    if item["category"] == "not_in_ofr_index":
        state["not_found"] = not_found(item, "not_in_ofr_index", True,
                                       "Order is in the project universe (1937 or later) but not in the frozen OFR executive-order index.")
        return state
    custody = ctx["custody"].get(iid)
    if custody:
        got = reuse_stage21(ctx["repo"], item, custody, ctx["fetcher"])
        if got and "source" in got:
            return finish_found(ctx, item, state, got["source"], got["text"], got["loc"], got["scanned"], [])
    if rec.get("not_received_for_publication"):
        state["not_found"] = not_found(item, "ofr_index_not_received_for_publication", True,
                                       "The OFR index marks this order 'not received for publication', so it was probably never printed in the Federal Register (OFR catalog statement, not verified here). Other routes: NARA, presidential libraries, APP.")
        return state
    if not rec.get("citation"):
        state["not_found"] = not_found(item, "ofr_index_has_no_fr_citation", True, "No FR volume/page in the OFR index.")
        return state
    wanted, routes = routes_for(item, ctx["crosswalk"].get(iid))
    res = ctx["ladder"].walk(wanted, routes=routes)
    attempts = res["attempts"]
    if res["source"]:
        src = res["source"]
        loc = res["result"].get("location") or {}
        accepted = next(a for a in reversed(attempts) if a.get("accepted"))
        src["source_id"] = f"{PRODUCED_BY}:{iid}:{src['sha256'][:12]}"
        src["cache_path"] = ctx["fetcher"].rel_cache(accepted["path"]) if accepted.get("path") else None
        src["location_confidence"] = loc.get("confidence")
        src.pop("wanted_id", None)
        src.pop("citation", None)
        original = src["url"].split("id_/", 1)[-1]
        scanned = eo_extract.issue_pdf(original)
        if scanned:
            ctx["issue_blobs"].add(accepted.get("path"))
        return finish_found(ctx, item, state, src, res["text"], loc, scanned, attempts)
    content_fail = [a for a in attempts if str(a.get("reject_reason", "")).startswith("content_check")]
    downloaded = [a for a in attempts if a.get("sha256")]
    # Only a failure where every route ended definitively is permanent; a timeout,
    # a block or an offline run is tried again on the next run.
    definitive = res.get("outcome") == "exhausted"
    if content_fail:
        reason, permanent, detail = ("downloaded_but_order_not_located", definitive, content_fail[-1]["reject_reason"][:300])
    elif downloaded:
        reason, permanent, detail = ("downloads_rejected", definitive, "; ".join(sorted({a.get('reject_reason') or a.get('error') for a in downloaded}))[:300])
    else:
        reason, permanent, detail = ("every_route_failed", definitive, "; ".join(sorted({a.get('error') or str(a.get('status')) for a in attempts}))[:300])
    if not definitive and res.get("why"):
        detail = (detail + " | retry later: " + res["why"])[:400]
    state["permanent"] = permanent
    state["attempts"] = clean_attempts(attempts)
    state["not_found"] = not_found(item, reason, permanent, detail, attempts)
    return state


def clean_attempts(attempts):
    out = []
    for a in attempts:
        a = dict(a)
        a.pop("path", None)
        out.append(a)
    return out


def finish_found(ctx, item, state, src, text, loc, scanned, attempts):
    iid = item["instrument_id"]
    name = text_name(iid)
    src["text_path"] = f"texts/{name}"
    ctx["state_texts"].mkdir(parents=True, exist_ok=True)
    fetch_ladder_write(ctx["state_texts"] / name, text_header(iid, src) + (text or ""))
    state.update(status="found", permanent=True, source=src, text_file=name,
                 fragment=fragment_for(item, src, confidence_note(loc, scanned)),
                 attempts=clean_attempts(attempts))
    return state


# --------------------------------------------------------------------------
# The run
# --------------------------------------------------------------------------

def fetch_ladder_write(path, text):
    import fetch_ladder
    fetch_ladder.write_text_lf(path, text)


def write_state(state_dir, st):
    fetch_ladder_write(state_path(state_dir, st["instrument_id"]), json.dumps(st, ensure_ascii=False, indent=1))


def state_done(st, retry_not_found=False):
    return bool(st) and (st["status"] == "found" or (st["permanent"] and not retry_not_found))


def state_path(state_dir, iid):
    import fetch_ladder
    return Path(state_dir) / (fetch_ladder.safe_name(iid) + ".json")


def load_state(state_dir, iid):
    p = state_path(state_dir, iid)
    if p.exists():
        s = json.loads(p.read_text(encoding="utf-8"))
        if s.get("state_version") == STATE_VERSION:
            return s
    return None


def make_ctx(repo, cache, offline=False, max_requests=None):
    """Everything process_order needs: one downloader, the source ladder, state folders."""
    import eo_extract
    import fetch_ladder
    repo, cache = Path(repo), Path(cache)
    fetcher = fetch_ladder.Fetcher(cache, max_requests=max_requests, offline=offline)
    return {
        "repo": repo, "fetcher": fetcher,
        "ladder": fetch_ladder.Ladder(fetcher, extract=eo_extract.eo_extract),
        "custody": load_custody(repo), "crosswalk": load_crosswalk_pdfs(repo),
        "state_dir": cache / "state", "state_texts": cache / "state" / "texts", "issue_blobs": set(),
    }


def default_workers(on_github, cpus=None):
    """Parallel worker processes: every hardware thread on a PC (no cap), 4 on GitHub's
    2-CPU runner (its workers mostly wait on downloads)."""
    import os
    cpus = cpus or os.cpu_count() or 1
    return 4 if on_github else max(1, cpus)


# ---- parallel workers (one process each; they share the cache and per-order state files) ----
_WORKER = {}


def _init_worker(spec, keep_pdfs, extra_paths):
    import sys as _sys
    for x in reversed(extra_paths):
        if x not in _sys.path:
            _sys.path.insert(0, x)
    _WORKER["ctx"] = make_ctx(spec["repo"], spec["cache"], spec.get("offline", False), spec.get("max_requests"))
    _WORKER["keep_pdfs"] = keep_pdfs


def _work_group(group):
    """Process all orders of one issue in a worker. Returns [(state, info)]."""
    import fetch_ladder
    ctx, out = _WORKER["ctx"], []
    try:
        for it in group:
            t = time.time()
            req0, bytes0 = ctx["fetcher"].requests, ctx["fetcher"].bytes_downloaded
            try:
                st = process_order(ctx, it)
            except fetch_ladder.BudgetExceeded as exc:
                out.append((None, {"stopped": str(exc), "instrument_id": it["instrument_id"]}))
                break
            st["seconds"] = round(time.time() - t, 2)
            st["fresh_bytes"] = ctx["fetcher"].bytes_downloaded - bytes0
            write_state(ctx["state_dir"], st)
            out.append((st, {"network": ctx["fetcher"].requests > req0, "seconds": time.time() - t,
                             "bytes": st["fresh_bytes"]}))
    finally:
        if not _WORKER["keep_pdfs"]:
            for b in list(ctx["issue_blobs"]):
                if b:
                    ctx["fetcher"].forget_body(b)
            ctx["issue_blobs"].clear()
    return out


def run(ctx, plan, limit=None, time_budget_s=None, retry_not_found=False, keep_pdfs=True, log=print,
        workers=1, ctx_spec=None):
    """Process the plan (resuming from state). Returns (states, run_stats).

    workers > 1 (with ctx_spec = {"repo", "cache", "offline", "max_requests"}) processes whole
    issues in that many worker processes at once; each order's result is identical to a
    one-process run, because every worker runs the same process_order on the same cache."""
    import fetch_ladder
    t0 = time.time()
    state_dir = ctx["state_dir"]
    state_dir.mkdir(parents=True, exist_ok=True)
    # Orders already finished (this cache, or carried forward) are loaded, not redone;
    # JOB_LIMIT counts only the orders that still need work.
    finished, todo = {}, []
    for it in plan:
        st = load_state(state_dir, it["instrument_id"])
        if state_done(st, retry_not_found):
            finished[it["instrument_id"]] = st
        else:
            todo.append(it)
    selected = todo[:limit] if limit is not None else todo
    by_issue = {}
    for it in selected:
        k = issue_key(it)
        if k:
            by_issue.setdefault(k, []).append(it)
    states, done_ids = dict(finished), set(finished)
    stats = Counter()
    stats["resumed_from_state"] = len(finished)
    issue_bytes, fresh_seconds = [], []
    stopped = ""

    def handle(it):
        iid = it["instrument_id"]
        t = time.time()
        req0, bytes0 = ctx["fetcher"].requests, ctx["fetcher"].bytes_downloaded
        st = process_order(ctx, it)
        st["seconds"] = round(time.time() - t, 2)
        st["fresh_bytes"] = ctx["fetcher"].bytes_downloaded - bytes0
        write_state(state_dir, st)
        if ctx["fetcher"].requests > req0:
            stats["orders_with_network"] += 1
            fresh_seconds.append(time.time() - t)
        if ctx["fetcher"].bytes_downloaded > bytes0 and issue_key(it):
            issue_bytes.append(ctx["fetcher"].bytes_downloaded - bytes0)
        return st

    if workers > 1 and ctx_spec:
        return _run_parallel(ctx, selected, by_issue, states, done_ids, stats, issue_bytes, fresh_seconds,
                             t0, time_budget_s, keep_pdfs, log, workers, ctx_spec, len(finished))
    n = 0
    for it in selected:
        if it["instrument_id"] in done_ids:
            continue
        if time_budget_s is not None and time.time() - t0 > time_budget_s:
            stopped = f"time budget of {time_budget_s / 60:.0f} minutes reached"
            break
        group = by_issue.get(issue_key(it), [it]) if issue_key(it) else [it]
        try:
            for g in group:
                if g["instrument_id"] in done_ids:
                    continue
                n += 1
                st = handle(g)
                states[g["instrument_id"]] = st
                done_ids.add(g["instrument_id"])
                tag = st["status"] if st["status"] == "found" else "not found: " + st["not_found"]["reason"]
                conf = f" ({st['source'].get('location_confidence')})" if st["status"] == "found" else ""
                log(f"[{n}/{len(selected)}] {g['instrument_id']}: {tag}{conf}")
        except fetch_ladder.BudgetExceeded as exc:
            stopped = str(exc)
            break
        finally:
            if not keep_pdfs:
                for p in list(ctx["issue_blobs"]):
                    if p and ctx["fetcher"].forget_body(p):
                        stats["issue_pdfs_deleted_after_use"] += 1
                ctx["issue_blobs"].clear()
    pending = [it["instrument_id"] for it in selected if it["instrument_id"] not in done_ids]
    stats["seconds"] = round(time.time() - t0, 1)
    return states, {"stats": dict(stats), "pending": pending, "stopped": stopped, "selected": len(selected),
                    "already_finished": len(finished), "issue_bytes": issue_bytes, "fresh_seconds": fresh_seconds}


def _run_parallel(ctx, selected, by_issue, states, done_ids, stats, issue_bytes, fresh_seconds,
                  t0, time_budget_s, keep_pdfs, log, workers, ctx_spec, already_finished):
    import sys as _sys
    from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
    groups, seen = [], set()
    for it in selected:  # whole issues, in plan order (decided orders first)
        if it["instrument_id"] in seen or it["instrument_id"] in done_ids:
            continue
        g = by_issue.get(issue_key(it), [it]) if issue_key(it) else [it]
        g = [x for x in g if x["instrument_id"] not in done_ids and x["instrument_id"] not in seen]
        seen.update(x["instrument_id"] for x in g)
        groups.append(g)
    spec = dict(ctx_spec)
    if spec.get("max_requests"):
        spec["max_requests"] = max(1, spec["max_requests"] // workers)
    log(f"Parallel run: {len(groups)} issue groups ({len(seen)} orders) over {workers} worker processes.")
    stopped, n, nxt, running = "", 0, 0, {}
    with ProcessPoolExecutor(max_workers=workers, initializer=_init_worker,
                             initargs=(spec, keep_pdfs, list(_sys.path))) as pool:
        while nxt < len(groups) or running:
            while not stopped and nxt < len(groups) and len(running) < workers * 2:
                if time_budget_s is not None and time.time() - t0 > time_budget_s:
                    stopped = f"time budget of {time_budget_s / 60:.0f} minutes reached"
                    break
                running[pool.submit(_work_group, groups[nxt])] = groups[nxt]
                nxt += 1
            if not running:
                break
            finished_now, _ = wait(running, return_when=FIRST_COMPLETED)
            for fut in finished_now:
                running.pop(fut)
                for st, info in fut.result():
                    if st is None:
                        stopped = stopped or info["stopped"]
                        continue
                    n += 1
                    states[st["instrument_id"]] = st
                    done_ids.add(st["instrument_id"])
                    if info["network"]:
                        stats["orders_with_network"] += 1
                        fresh_seconds.append(info["seconds"])
                    if info["bytes"] > 0:
                        issue_bytes.append(info["bytes"])
                    tag = st["status"] if st["status"] == "found" else "not found: " + st["not_found"]["reason"]
                    conf = f" ({st['source'].get('location_confidence')})" if st["status"] == "found" else ""
                    log(f"[{n}/{len(seen)}] {st['instrument_id']}: {tag}{conf}")
            if stopped:
                nxt = len(groups)  # submit nothing more; let running groups finish
    pending = [it["instrument_id"] for it in selected if it["instrument_id"] not in done_ids]
    stats["seconds"] = round(time.time() - t0, 1)
    stats["parallel_workers"] = workers
    return states, {"stats": dict(stats), "pending": pending, "stopped": stopped, "selected": len(selected),
                    "already_finished": already_finished, "issue_bytes": issue_bytes, "fresh_seconds": fresh_seconds}


def write_outputs(out, ctx, plan, states, run_info, extra_summary=None, full_plan=None, prior_found=0):
    """Write the outputs for EVERY order finished so far in the full plan (never only this run's)."""
    out = Path(out)
    (out / "texts").mkdir(parents=True, exist_ok=True)
    full_plan = full_plan or plan
    all_states = {}
    for p in full_plan:
        st = states.get(p["instrument_id"]) or load_state(ctx["state_dir"], p["instrument_id"])
        if st:
            all_states[p["instrument_id"]] = st
    order = [p["instrument_id"] for p in full_plan if p["instrument_id"] in all_states]
    sources, fragments, missing, attempts = [], [], [], []
    for iid in order:
        st = all_states[iid]
        attempts.extend(st.get("attempts") or [])
        if st["status"] == "found":
            sources.append(st["source"])
            fragments.append(st["fragment"])
            src_text = ctx["state_texts"] / (st.get("text_file") or "")
            if st.get("text_file") and src_text.is_file():
                shutil.copyfile(src_text, out / "texts" / st["text_file"])
        else:
            missing.append(st["not_found"])

    def jsonl(name, rows):
        with open(out / name, "w", encoding="utf-8", newline="\n") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")

    jsonl("SOURCES.jsonl", sources)
    jsonl("FRAGMENTS.jsonl", fragments)
    jsonl("ATTEMPTS.jsonl", attempts)
    with open(out / "NOT_FOUND.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=NOT_FOUND_COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(missing)

    plan_by_id = {p["instrument_id"]: p for p in full_plan}
    conf = Counter(s.get("location_confidence") for s in sources)
    routes = Counter(s["route"] for s in sources)
    reasons = Counter(m["reason"] for m in missing)
    decided_found = sum(1 for s in sources if plan_by_id[s["instrument_ids"][0]]["decided"])
    done_states = {i: st for i, st in all_states.items() if state_done(st)}
    estimate = estimate_full_run(full_plan, done_states)
    carried = sum(1 for st in all_states.values() if st.get("carried_forward_from"))
    summary = {
        "job": PRODUCED_BY, "run_date": date.today().isoformat(),
        "orders_in_scope": len(full_plan),
        "orders_in_scope_decided": sum(1 for p in full_plan if p["decided"]),
        "orders_selected_this_run": run_info["selected"],
        "orders_already_finished_before_this_run": run_info.get("already_finished", 0),
        "orders_completed_in_outputs": len(order),
        "orders_carried_forward_from_committed_results": carried,
        "found": len(sources), "found_decided": decided_found,
        "found_needing_page_check": sum(1 for s in sources if s.get("location_confidence") != "high"),
        "found_by_confidence": dict(conf), "found_by_route": dict(routes),
        "reused_stage21_captures": routes.get("reuse/stage21_original_sources", 0),
        "not_found": len(missing), "not_found_by_reason": dict(reasons),
        "pending_not_reached": len(run_info["pending"]), "stopped_early": run_info["stopped"],
        "run_stats": run_info["stats"],
        "http_requests": ctx["fetcher"].requests, "bytes_downloaded": ctx["fetcher"].bytes_downloaded,
        "full_run_estimate": estimate,
        "prior_committed_found": prior_found,
        "shrink_check": ("ok" if len(sources) >= prior_found else
                         f"WARNING: {prior_found} orders were found in the committed results but only "
                         f"{len(sources)} are in this output"),
        "caution": "Source custody and location leads only. Nothing here changes a provisional status, ledger or count.",
    }
    if extra_summary:
        summary.update(extra_summary)
    fetch_ladder_write(out / "SUMMARY.json", json.dumps(summary, indent=1) + "\n")
    return summary


# --------------------------------------------------------------------------
# Carry forward: never lose results committed earlier
# --------------------------------------------------------------------------

def carry_forward(ctx, full_plan, priors, log=print):
    """Seed the state folder with orders finished in earlier committed results.

    priors: prior_output.PriorOutput objects, best first (the owner's full PC
    run in data/full_run/, then the last committed output/). A found order is
    taken unless this cache already has it as found; a not-found row only when
    this cache has nothing for the order. Returns (counts, prior_found).
    """
    plan_ids = {p["instrument_id"] for p in full_plan}
    stats = Counter()
    prior_found = 0
    for prior in priors:
        sources = prior.jsonl("SOURCES.jsonl")
        if not sources and prior.read("NOT_FOUND.csv") is None:
            continue
        prior_found = max(prior_found, len({s["instrument_ids"][0] for s in sources if s.get("instrument_ids")}))
        frags = {f["instrument_id"]: f for f in prior.jsonl("FRAGMENTS.jsonl")}
        texts = None
        for src in sources:
            iid = (src.get("instrument_ids") or [None])[0]
            if iid not in plan_ids:
                continue
            st = load_state(ctx["state_dir"], iid)
            if st and st["status"] == "found":
                continue
            if texts is None:
                texts = prior.texts()
            name = Path(src["text_path"]).name if src.get("text_path") else None
            body = texts.get(name) if name else None
            if body is not None:
                ctx["state_texts"].mkdir(parents=True, exist_ok=True)
                (ctx["state_texts"] / name).write_bytes(body)
            else:
                name = None
                stats["carried_without_text"] += 1
            frag = frags.get(iid)
            if frag:
                frag = json.loads(json.dumps(frag))
                frag["data"].setdefault("location_verified", False)
                frag["data"].setdefault("needs_page_check", src.get("location_confidence") != "high")
            write_state(ctx["state_dir"], {
                "state_version": STATE_VERSION, "instrument_id": iid, "status": "found", "permanent": True,
                "source": src, "fragment": frag, "not_found": None, "attempts": [], "text_file": name,
                "processed_utc": src.get("retrieved_utc"), "carried_forward_from": prior.label})
            stats["found_carried"] += 1
        for row in prior.csv_rows("NOT_FOUND.csv"):
            iid = row.get("instrument_id")
            if iid not in plan_ids or load_state(ctx["state_dir"], iid):
                continue
            row = {k: row.get(k, "") for k in NOT_FOUND_COLUMNS}
            write_state(ctx["state_dir"], {
                "state_version": STATE_VERSION, "instrument_id": iid, "status": "not_found",
                "permanent": row["permanent"] == "yes", "source": None, "fragment": None, "not_found": row,
                "attempts": [], "text_file": None, "processed_utc": None, "carried_forward_from": prior.label})
            stats["not_found_carried"] += 1
        log(f"Carried forward from {prior.label}: {stats['found_carried']} found and "
            f"{stats['not_found_carried']} not-found orders so far.")
    return dict(stats), prior_found


def estimate_full_run(plan, states):
    """Project disk and time for the orders not done yet, from what is done.

    Scanned-issue sizes are averaged per decade from the issues already
    fetched (a 1937 issue is ~5 MB, a 1993 issue can be ~300 MB).
    """
    import eo_extract
    done = {i: st for i, st in states.items()}
    size_by_decade, seen = {}, set()
    fresh_s, fresh_b, doc_s = 0.0, 0, []
    for p in plan:
        st = done.get(p["instrument_id"])
        if not st:
            continue
        if st.get("fresh_bytes"):
            fresh_s += st.get("seconds", 0)
            fresh_b += st["fresh_bytes"]
        src = st.get("source") or {}
        if st["status"] == "found" and eo_extract.issue_pdf(src.get("url", "").split("id_/")[-1]):
            if src["sha256"] not in seen:
                seen.add(src["sha256"])
                dec = (p["record"].get("publication_date") or "")[:3]
                size_by_decade.setdefault(dec, []).append(src["bytes"])
        elif st["status"] == "found" and st.get("fresh_bytes"):
            doc_s.append(st.get("seconds", 0))
    remaining = [p for p in plan if p["instrument_id"] not in done]
    need = [p for p in remaining if p["category"] == "ofr_index" and (p.get("record") or {}).get("citation")
            and not p["record"].get("not_received_for_publication")]
    issues = {}
    for p in need:
        k = issue_key(p)
        if k:
            issues.setdefault(k[:3], set()).add(k)
    docs = sum(1 for p in need if not issue_key(p))
    all_sizes = [b for v in size_by_decade.values() for b in v]
    overall = sum(all_sizes) / len(all_sizes) if all_sizes else None
    est_bytes, unknown = 0, []
    per_decade = {}
    for dec, keys in sorted(issues.items()):
        sizes = size_by_decade.get(dec)
        avg = sum(sizes) / len(sizes) if sizes else overall
        if avg is None:
            unknown.append(dec + "0s")
            continue
        per_decade[dec + "0s"] = {"issues": len(keys), "avg_issue_mb": round(avg / 1e6, 1), "measured": bool(sizes)}
        est_bytes += len(keys) * avg
    est_bytes += docs * 2e5
    rate = (fresh_b / fresh_s) if fresh_s and fresh_b else None
    doc_avg = sum(doc_s) / len(doc_s) if doc_s else 3.0
    hours = ((est_bytes - docs * 2e5) / rate + docs * doc_avg) / 3600 if rate else None
    return {
        "orders_not_yet_done": len(remaining), "of_which_need_network": len(need),
        "distinct_scanned_issues_still_needed": sum(len(v) for v in issues.values()),
        "per_document_pdfs_still_needed": docs, "by_decade": per_decade,
        "decades_without_a_measured_issue": unknown,
        "estimated_download_gb": round(est_bytes / 1e9, 1) if all_sizes else None,
        "measured_mb_per_second_including_text_extraction": round(rate / 1e6, 2) if rate else None,
        "estimated_hours": round(hours, 1) if hours else None,
        "note": "Rough projection from the orders done so far; decades with no measured issue use the overall average.",
    }
