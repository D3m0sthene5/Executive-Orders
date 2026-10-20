"""Source ladder job: fetch every queued source through the never-give-up ladder.

Runs the unit tests first and stops if they fail. See README.md.

Environment: OUTPUT_DIR (required), REPO_ROOT (default "."), JOB_LIMIT (max
items), JOB_CACHE_DIR (download cache, default <OUTPUT_DIR>/../source-ladder-cache),
JOB_MAX_REQUESTS (stop after this many HTTP requests), JOB_ONLY (comma list of item ids
or prefixes such as "USC::"), JOB_OFFLINE=1 (cache only, never proposes "exhausted"),
JOB_MAX_RANGE_REQUESTS (HTTP Range reads of large files, report-date lane; default 1500),
JOB_REFETCH=1 (walk items again even if the last committed output already found them),
JOB_CARRY_FORWARD=0 (ignore the last committed output).
"""
from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULT_COLUMNS = ["wanted_id", "citation", "step", "instrument_ids", "requested_by", "attempts", "result",
                  "why", "url", "sha256", "page_or_item", "route", "text_path", "carried_forward_from"]


def run_tests():
    r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(HERE), "-p", "test_*.py"], cwd=HERE)
    if r.returncode:
        sys.exit("Unit tests failed; the job did not run.")


def env_int(name):
    v = os.environ.get(name, "").strip()
    return int(v) if v else None


def previous_found(prior):
    """{wanted_id: (SOURCE record, text bytes or None)} found in an earlier committed output."""
    if prior is None:
        return {}
    found_ids = {r["wanted_id"] for r in prior.csv_rows("RESULTS.csv") if r.get("result") == "found"}
    out = {}
    for src in prior.jsonl("SOURCES.jsonl"):
        wid = src.get("wanted_id")
        if wid in found_ids and wid not in out:
            text = prior.read(src["text_path"]) if src.get("text_path") else None
            out[wid] = (src, text)
    return out


def prior_history(prior, history_file, latest_records):
    """Keep unsuccessful work and attempts across successive bounded runs."""
    records, seen = [], set()
    for row in (prior.jsonl(history_file) if prior else []) + list(latest_records):
        key = json.dumps(row, ensure_ascii=False, sort_keys=True)
        if key not in seen:
            seen.add(key)
            records.append(row)
    return records


def revalidate_previous(found, by_id):
    """Validate even offline and for retained sources outside this run's plan."""
    import fetch_ladder
    valid, stale, audit = {}, {}, []
    for wid, (source, text) in found.items():
        src = dict(source)
        current = by_id.get(wid)
        fallback = fetch_ladder.Wanted(
            wanted_id=wid, instrument_ids=src.get("instrument_ids") or [],
            urls=[src.get("requested_url") or src.get("url")], citation=src.get("citation") or "",
            extra={"parent_citation": src.get("embedded_in_request") or "",
                   "report_date": src.get("report_date_request"),
                   **{k: src[k] for k in ("as_of", "required_date", "edition_year") if k in src}})
        why = fetch_ladder.carried_defect(current or fallback, src, text)
        if not why and not re.fullmatch(r"[0-9a-fA-F]{64}", str(src.get("sha256") or "")):
            why = "invalid_receipt: missing or malformed source SHA-256"
        if not why and not fetch_ladder.request_contract.http_url(src.get("url")):
            why = "invalid_receipt: missing or malformed source URL"
        if current is None and src.get("carried_defect"):
            why = why or src["carried_defect"]
        src["evidence_tier"] = fetch_ladder.evidence_tier(src, text)
        audit.append({"wanted_id": wid, "sha256": src.get("sha256"), "url": src.get("url"),
                      "status": "rejected" if why else "passed_retrieval_checks",
                      "reason": why, "current_request_available": current is not None,
                      "evidence_tier": src["evidence_tier"],
                      "scope": "retrieval checks; no authentication or legal conclusion"})
        if why:
            stale[wid] = why
        else:
            src.pop("carried_defect", None)
            valid[wid] = (src, text)
    return valid, stale, audit


def preserve_rejected(prior, found, stale, out):
    """Keep invalid receipts and exact text outside the usable SOURCES catalog."""
    import fetch_ladder
    records, seen = [], set()

    def keep(record, text):
        key = (record.get("wanted_id"), record.get("sha256"), record.get("reason"))
        if key in seen:
            return
        seen.add(key)
        r = dict(record)
        if text is not None:
            rel = "rejected_texts/" + fetch_ladder.unique_file_name(
                str(r.get("wanted_id")) + ":" + str(r.get("sha256")))
            (out / rel).parent.mkdir(parents=True, exist_ok=True)
            (out / rel).write_bytes(text)
            r["preserved_text_path"] = rel
            r["preserved_text_sha256"] = fetch_ladder.sha256_bytes(text)
        records.append(r)

    if prior:
        for record in prior.jsonl("REJECTED_PRIOR_SOURCES.jsonl"):
            text = prior.read(record["preserved_text_path"]) if record.get("preserved_text_path") else None
            keep(record, text)
    for wid, why in stale.items():
        src, text = found[wid]
        keep({"wanted_id": wid, "sha256": src.get("sha256"), "url": src.get("url"),
              "reason": why, "source_record": src, "from": prior.label if prior else None,
              "status": "needs_revalidation", "usable_for_request": False}, text)
    return records


def main():
    run_tests()
    sys.path.insert(0, str(HERE))
    import eo_extract
    import fetch_ladder
    import ladder_queue
    import ofr_index
    import prior_output

    t0 = time.time()
    out = Path(os.environ["OUTPUT_DIR"]).resolve()
    repo = Path(os.environ.get("REPO_ROOT", ".")).resolve()
    name = os.environ.get("JOB_NAME", "source-ladder")
    cache = Path(os.environ.get("JOB_CACHE_DIR") or (out.parent / f"{name}-cache")).resolve()
    limit = env_int("JOB_LIMIT")
    offline = os.environ.get("JOB_OFFLINE") == "1"
    out.mkdir(parents=True, exist_ok=True)
    (out / "texts").mkdir(exist_ok=True)

    universe = set()
    uni_path = repo / "research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv"
    if uni_path.exists():
        universe = {r["id"] for r in ladder_queue.read_csv(uni_path)}
    try:
        eo_index = ofr_index.load_index(repo_root=repo, universe_ids=universe)
    except FileNotFoundError:
        eo_index = {}
        print("Note: OFR index snapshot (jobs/fr-originals/data/ofr_index) not found; EO citations get fewer routes.")
    hints = ladder_queue.load_hints(repo)

    request_audit = []
    queue_items, problems = ladder_queue.read_fetch_queue(repo / ladder_queue.FETCH_QUEUE, eo_index, audit=request_audit)
    shared = ladder_queue.shared_source_wanted(repo, eo_index, hints) if (repo / ladder_queue.SHARED).exists() else []
    opus, more = ladder_queue.opus_refetch_wanted(repo)
    problems += more
    # Read the prior output before selecting work: a bounded run retains held
    # evidence outside the selected requests and avoids spending its limit on it.
    prior = None
    if os.environ.get('JOB_CARRY_FORWARD','1') != '0':
        prior_dir = os.environ.get('JOB_PRIOR_OUTPUT_DIR')
        prior = (prior_output.PriorOutput.from_folder(prior_dir) if prior_dir
                 else prior_output.PriorOutput.from_git_head(repo, f'jobs/{name}/output'))
    all_prior_found = previous_found(prior)
    previous_unresolved = prior_history(
        prior, 'PREVIOUS_UNRESOLVED.jsonl',
        [r for r in prior.csv_rows('RESULTS.csv') if r.get('result') != 'found'] if prior else [])
    previous_attempts = prior_history(prior, 'PREVIOUS_ATTEMPTS.jsonl',
                                     prior.jsonl('ATTEMPTS.jsonl') if prior else [])
    items = queue_items + shared + opus
    # An earlier found record that fails today's checks (gzip bytes, a partial statute, a listing page, a current
    # edition for a dated question ...) is walked again instead of carried for ever. Until it is walked (outside a
    # bounded plan, or not reached) its original receipt and bytes are quarantined,
    # never published as a usable found source.
    by_id = {w.wanted_id: w for w in items}
    valid_prior, stale, revalidation_audit = revalidate_previous(all_prior_found, by_id)
    carried = {} if os.environ.get('JOB_REFETCH') == '1' else dict(valid_prior)
    rejected_prior = preserve_rejected(prior, all_prior_found, stale, out)
    if stale:
        print(f"{len(stale)} earlier found record(s) fail today's checks and will be walked again:")
        for wid, why in sorted(stale.items()):
            print(f"  {wid[:100]}: {why[:120]}")
    plan_path = os.environ.get('JOB_PLAN_FILE')
    plan_used = None
    if plan_path:
        from plan import select_plan
        plan_used = json.loads(Path(plan_path).read_text('utf-8'))
        items = select_plan(items, plan_used)
        budget = env_int('JOB_MAX_REQUESTS')
        os.environ['JOB_MAX_REQUESTS'] = str(min(budget, plan_used['max_requests']) if budget is not None else plan_used['max_requests'])
    elif os.environ.get('JOB_READINESS_PLAN','1') != '0' and not os.environ.get('JOB_ONLY') and limit is None:
        from plan import make_queue_first_plan, select_plan, UNSUCCESSFUL
        # Requests with no route at all cost no request: they are kept as recorded no_route failures
        # outside the plan, so they never take one of its 50 places.
        routable = [w for w in items if fetch_ladder.plan_routes(w)]
        unroutable = [w for w in items if w.wanted_id.startswith('queue:') and w.wanted_id not in carried
                      and not fetch_ladder.plan_routes(w)]
        # A request that ended no_route was never tried with a route: once a route exists (e.g. the report-date lane)
        # it ranks with the untried requests, not behind every untried one.
        tried = {r['wanted_id'] for r in previous_unresolved
                 if r.get('result') in UNSUCCESSFUL and r.get('result') != 'no_route'}
        plan_used = make_queue_first_plan(routable,set(carried),tried,repo/'jobs/readiness-tracker/output/READINESS_BY_ORDER.csv',
                                         limit=env_int('JOB_PLAN_LIMIT') or 50,budget=env_int('JOB_MAX_REQUESTS') or 300)
        # No-route items go first: they make no request, so a budget stop can never leave them unrecorded.
        items = unroutable + select_plan(routable,plan_used)
        os.environ['JOB_MAX_REQUESTS'] = str(plan_used['max_requests'])
    # Even explicit legacy selections get a finite request budget by default.
    os.environ.setdefault('JOB_MAX_REQUESTS','80')
    only = [x.strip() for x in os.environ.get("JOB_ONLY", "").split(",") if x.strip()]
    if only:  # e.g. JOB_ONLY="USC::,CFR::" or JOB_ONLY="STAT::66 Stat. 259"
        items = [w for w in items if any(w.wanted_id == o or w.wanted_id.startswith(o) for o in only)]
    if limit is not None:
        items = items[:limit]

    # Items the last committed output already found are carried forward, not downloaded again.
    print(f"Queue: {len(queue_items)} from FETCH_QUEUE.jsonl, {len(shared)} shared sources not yet retrieved, "
          f"{len(opus)} Opus originals to re-fetch; "
          f"working on {len(items)} ({sum(1 for w in items if w.wanted_id in carried)} already found in "
          f"{prior.label if prior else 'no earlier output'} and carried forward).")
    for p in problems:
        print("  problem:", p)

    sys.path.insert(0, str(repo / "jobs/_lib"))
    from fetch_pool import FetchPool, prune
    pool = FetchPool(cache / "pool", workers=env_int("JOB_WORKERS") or 12,
                     user_agent=fetch_ladder.USER_AGENT, min_interval=1.0, offline=offline,
                     max_cache_bytes=int(os.environ.get("JOB_CACHE_MB","2048"))*1024*1024//2)
    class PooledFetcher(fetch_ladder.Fetcher):
        def _wait(self, host):
            # Host spacing and robots crawl delay are shared by the pool.
            pass
    # Bounded in requests (JOB_MAX_REQUESTS) and in total bytes (JOB_MAX_DOWNLOAD_MB, default 800).
    max_mb = env_int("JOB_MAX_DOWNLOAD_MB") or 800
    fetcher = PooledFetcher(cache / "ladder", transport=pool.request,
                            max_requests=env_int("JOB_MAX_REQUESTS"), max_total_bytes=max_mb * 1_000_000, offline=offline,
                            max_range_requests=env_int("JOB_MAX_RANGE_REQUESTS") or 1500)
    # Fetch one best route per item concurrently. The original ladder still validates
    # identity, expected hashes, document bytes, and every subsequent fallback.
    # A bounded request-budget run stays sequential so prefetch cannot overspend it.
    prefetch_urls = []
    if not offline and env_int("JOB_MAX_REQUESTS") is None:
        for w in items:
            if w.wanted_id in carried:
                continue
            plan = fetch_ladder.plan_routes(w)
            if plan:
                prefetch_urls.append(plan[0].url)
        pool.prefetch(prefetch_urls)

    def extract(wanted, route, att, f):
        kind, _ = fetch_ladder.parse_citation(wanted.citation)
        if kind == "EO":
            return eo_extract.eo_extract(wanted, route, att, f)
        return fetch_ladder.default_extract(wanted, route, att, f)

    ladder = fetch_ladder.Ladder(fetcher, extract=extract)
    sources, attempts, exhausted, results = [], [], [], []
    stopped = ""

    def base_row(w, n_attempts):
        return {"wanted_id": w.wanted_id, "citation": w.citation, "step": w.step,
                "instrument_ids": " | ".join(w.instrument_ids), "requested_by": w.requested_by,
                "attempts": n_attempts, "result": "", "why": "", "url": "", "sha256": "",
                "page_or_item": "", "route": "", "text_path": "", "carried_forward_from": ""}

    def save_text(w, src, text):
        rel = "texts/" + fetch_ladder.unique_file_name(w.wanted_id)
        fetch_ladder.write_text_lf(out / rel, text)
        src["text_path"] = rel

    # Bounded plans must not erase evidence acquired by an earlier pass. Keep
    # exact prior bytes and receipts even when those requests are outside this
    # pass. These are carried evidence, not new acquisitions or readiness gains.
    if prior:
        from plan import retain_unselected
        old_sources, old_results = retain_unselected(prior, valid_prior, {w.wanted_id for w in items}, out)
        sources.extend(old_sources)
        results.extend(old_results)
        selected = {w.wanted_id for w in items}
        previous_rows = {r["wanted_id"]: r for r in prior.csv_rows("RESULTS.csv")} if prior else {}
        for wid, reason in stale.items():
            if wid not in selected:
                row = dict(previous_rows[wid], result="needs_revalidation", why=reason,
                           attempts=0, text_path="", carried_forward_from="")
                results.append(row)

    for n, w in enumerate(items, 1):
        print(f"[{n}/{len(items)}] {w.wanted_id} ({len(w.instrument_ids)} orders)")
        row = base_row(w, 0)
        if w.wanted_id in carried:
            src, text = carried[w.wanted_id]
            src = dict(src)
            src["instrument_ids"] = list(w.instrument_ids)   # the citing orders as listed now
            src["carried_forward_from"] = prior.label
            if text is not None:
                rel = "texts/" + fetch_ladder.unique_file_name(w.wanted_id)
                (out / rel).write_bytes(text)          # exact bytes of the committed text
                src["text_path"] = rel
            else:
                src["text_path"] = None
            sources.append(src)
            row.update(result="found", url=src["url"], sha256=src["sha256"], page_or_item=src["page_or_item"],
                       route=src["route"], text_path=src["text_path"] or "", carried_forward_from=prior.label)
            results.append(row)
            print(f"  carried forward from {prior.label}: {src['url']}")
            continue
        try:
            res = ladder.walk(w)
        except fetch_ladder.BudgetExceeded as exc:
            stopped = str(exc)
            print("  stopping:", stopped)
            break
        attempts.extend(res["attempts"])
        row["attempts"] = len(res["attempts"])
        superseded = None
        if w.wanted_id in stale:
            old_src = all_prior_found[w.wanted_id][0]
            superseded = {"url": old_src.get("url"), "sha256": old_src.get("sha256"),
                          "page_or_item": old_src.get("page_or_item"), "from": prior.label, "why": stale[w.wanted_id]}
        if res["source"]:
            src = res["source"]
            if superseded:
                src["supersedes_defective_source"] = superseded
            att = next(a for a in reversed(res["attempts"]) if a.get("accepted"))
            src["cache_path"] = (Path(att["path"]).relative_to(cache).as_posix()) if att.get("path") else None
            if res["text"]:
                header = (f"Wanted: {w.wanted_id}\nCited by: {', '.join(w.instrument_ids)}\nSource: {src['url']}\n"
                          f"SHA-256 of the downloaded file: {src['sha256']}\nLocation: {src['page_or_item']}\n"
                          "Machine-extracted text (from a scan's text layer for older documents). "
                          "Not an authenticated transcription; check the PDF.\n\n")
                save_text(w, src, header + res["text"])
            sources.append(src)
            row.update(result="found", url=src["url"], sha256=src["sha256"], page_or_item=src["page_or_item"],
                       route=src["route"], text_path=src["text_path"] or "")
            print(f"  found via {src['route']}: {src['url']} ({src['bytes']} bytes)")
        elif res["outcome"] == "exhausted":
            exhausted.extend(res["exhausted"])
            row["result"] = "exhausted_proposed"
            print(f"  every route ended definitively ({len(res['attempts'])} attempts); proposed as exhausted")
        else:
            row.update(result=res["outcome"], why=res["why"])
            if superseded:
                row["why"] = (f"{res['why']} | earlier record not carried ({superseded['why'][:160]}): "
                              f"{superseded['url']} sha256 {superseded['sha256']}")
            print(f"  not found, {res['outcome']}: {res['why']}")
        results.append(row)
        prune(cache / "ladder", int(os.environ.get("JOB_CACHE_MB","2048"))*1024*1024//2)

    done = {r["wanted_id"] for r in results}
    for w in items:
        if w.wanted_id not in done:
            row = base_row(w, 0)
            row["result"] = "not_attempted_budget"
            if w.wanted_id in stale:
                old_src = all_prior_found[w.wanted_id][0]
                row["why"] = (f"earlier record not carried ({stale[w.wanted_id][:160]}): "
                              f"{old_src.get('url')} sha256 {old_src.get('sha256')}")
            results.append(row)

    def write_jsonl(fname, rows):
        with open(out / fname, "w", encoding="utf-8", newline="\n") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")

    for a in attempts:
        a.pop("path", None)
    write_jsonl("SOURCES.jsonl", sources)
    write_jsonl("QUEUE_AUDIT.jsonl", request_audit)
    write_jsonl("UNRESOLVED_REQUESTS.jsonl", [a for a in request_audit if a["status"] in ("invalid", "unresolved")])
    write_jsonl("SOURCE_REVALIDATION.jsonl", revalidation_audit)
    write_jsonl("REJECTED_PRIOR_SOURCES.jsonl", rejected_prior)
    if plan_used:
        fetch_ladder.write_text_lf(out/'SOURCE_PLAN.json',json.dumps(plan_used,sort_keys=True,indent=2)+'\n')
    write_jsonl("ATTEMPTS.jsonl", attempts)
    write_jsonl("EXHAUSTED_PROPOSED.jsonl", exhausted)
    if prior:
        write_jsonl('PREVIOUS_UNRESOLVED.jsonl', previous_unresolved)
        write_jsonl('PREVIOUS_ATTEMPTS.jsonl', previous_attempts)
    with open(out / "RESULTS.csv", "w", encoding="utf-8", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=RESULT_COLUMNS, lineterminator="\n")
        wr.writeheader()
        wr.writerows(results)

    counts = Counter(r["result"] for r in results)
    summary = {
        "job": name, "run_date": date.today().isoformat(), "offline": offline,
        "items_in_queue": len(queue_items) + len(shared) + len(opus), "items_worked": len(items),
        "from_fetch_queue": len(queue_items), "from_stage20_shared_sources": len(shared),
        "from_opus_refetch": len(opus),
        "found": counts.get("found", 0),
        "new_sources_found": sum(not s.get('carried_forward_from') for s in sources),
        "distinct_new_source_hashes": len({s['sha256'] for s in sources if not s.get('carried_forward_from')}),
        "found_carried_forward": sum(1 for r in results if r["carried_forward_from"]),
        "earlier_found_failing_todays_checks": len(stale),
        "earlier_found_carried_with_defect": sum(1 for s in sources if s.get("carried_defect")),
        "quarantined_prior_sources": len(rejected_prior),
        "retained_prior_failure_records": len(previous_unresolved),
        "retained_prior_attempt_records": len(previous_attempts),
        "needs_revalidation": counts.get("needs_revalidation", 0),
        "source_evidence_tiers": dict(Counter(s.get("evidence_tier", "unclassified") for s in sources)),
        "request_validation": dict(Counter(a["status"] for a in request_audit)),
        "unresolved_request_tasks": sum(t.get("status") == "unresolved" for a in request_audit for t in a["tasks"]),
        "exhausted_proposed_items": counts.get("exhausted_proposed", 0),
        "exhausted_proposed_lines": len(exhausted),
        "retry_later": counts.get("retry_later", 0), "no_route": counts.get("no_route", 0),
        "not_attempted_budget": counts.get("not_attempted_budget", 0),
        "orders_covered_by_found_sources": len({i for s in sources for i in s["instrument_ids"]}),
        "found_by_route": dict(Counter(s["route"] for s in sources)),
        "pool_network_requests": pool.requests, "pool_cache_hits": pool.cache_hits, "prefetched_urls": len(prefetch_urls),
        "http_requests": fetcher.requests, "bytes_downloaded": fetcher.bytes_downloaded,
        "range_requests": fetcher.range_requests, "range_bytes": fetcher.range_bytes,
        "report_date_items": sum(1 for w in items if w.extra.get("report_date")),
        "report_date_records_found": sum(1 for s in sources if s.get("report_date_request") and not s.get("carried_forward_from")),
        "max_download_mb": max_mb,
        "embedded_cite_items": sum(1 for w in items if w.extra.get("parent_wanted_id")),
        "attempts_logged": len(attempts), "fetch_queue_problems": problems, "stopped_early": stopped,
        "source_plan": plan_used,
        "seconds": round(time.time() - t0, 1),
        "caution": "Source custody and leads only. No legal conclusion, status or count is changed.",
    }
    fetch_ladder.write_text_lf(out / "SUMMARY.json", json.dumps(summary, indent=1) + "\n")
    print()
    print(f"Done in {summary['seconds']} s. Worked {len(items)} items: {summary['found']} found "
          f"({summary['found_carried_forward']} carried forward from the last committed output), "
          f"{summary['exhausted_proposed_items']} with every route ending definitively (proposed as exhausted, "
          f"{len(exhausted)} order lines), {summary['retry_later']} to retry later (a passing failure such as "
          f"a timeout, a block or an offline run; NOT proposed as exhausted), {summary['no_route']} with no route, "
          f"{summary['not_attempted_budget']} not attempted.")
    print(f"{fetcher.requests} HTTP requests ({fetcher.range_requests} Range reads of large files), "
          f"{fetcher.bytes_downloaded / 1e6:.1f} MB downloaded. Cache: {cache}")
    print("Nothing here changes a status or count; found files are source custody for human review.")


if __name__ == "__main__":
    main()
