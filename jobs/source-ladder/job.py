"""Source ladder job: fetch every queued source through the never-give-up ladder.

Runs the unit tests first and stops if they fail. See README.md.

Environment: OUTPUT_DIR (required), REPO_ROOT (default "."), JOB_LIMIT (max
items), JOB_CACHE_DIR (download cache, default <OUTPUT_DIR>/../source-ladder-cache),
JOB_MAX_REQUESTS (stop after this many HTTP requests), JOB_ONLY (comma list of item ids
or prefixes such as "USC::"), JOB_OFFLINE=1 (cache only, never proposes "exhausted"),
JOB_REFETCH=1 (walk items again even if the last committed output already found them),
JOB_CARRY_FORWARD=0 (ignore the last committed output).
"""
from __future__ import annotations

import csv
import json
import os
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

    queue_items, problems = ladder_queue.read_fetch_queue(repo / ladder_queue.FETCH_QUEUE, eo_index)
    shared = ladder_queue.shared_source_wanted(repo, eo_index, hints) if (repo / ladder_queue.SHARED).exists() else []
    opus, more = ladder_queue.opus_refetch_wanted(repo)
    problems += more
    items = queue_items + shared + opus
    only = [x.strip() for x in os.environ.get("JOB_ONLY", "").split(",") if x.strip()]
    if only:  # e.g. JOB_ONLY="USC::,CFR::" or JOB_ONLY="STAT::66 Stat. 259"
        items = [w for w in items if any(w.wanted_id == o or w.wanted_id.startswith(o) for o in only)]
    if limit is not None:
        items = items[:limit]

    # Items the last committed output already found are carried forward, not downloaded again.
    prior = None
    if os.environ.get("JOB_CARRY_FORWARD", "1") != "0":
        prior_dir = os.environ.get("JOB_PRIOR_OUTPUT_DIR")
        prior = (prior_output.PriorOutput.from_folder(prior_dir) if prior_dir
                 else prior_output.PriorOutput.from_git_head(repo, f"jobs/{name}/output"))
    carried = {} if os.environ.get("JOB_REFETCH") == "1" else previous_found(prior)
    print(f"Queue: {len(queue_items)} from FETCH_QUEUE.jsonl, {len(shared)} shared sources not yet retrieved, "
          f"{len(opus)} Opus originals to re-fetch; "
          f"working on {len(items)} ({sum(1 for w in items if w.wanted_id in carried)} already found in "
          f"{prior.label if prior else 'no earlier output'} and carried forward).")
    for p in problems:
        print("  problem:", p)

    fetcher = fetch_ladder.Fetcher(cache, max_requests=env_int("JOB_MAX_REQUESTS"), offline=offline)

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
        if res["source"]:
            src = res["source"]
            att = next(a for a in reversed(res["attempts"]) if a.get("accepted"))
            src["cache_path"] = fetcher.rel_cache(att["path"]) if att.get("path") else None
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
            print(f"  not found, {res['outcome']}: {res['why']}")
        results.append(row)

    done = {r["wanted_id"] for r in results}
    for w in items:
        if w.wanted_id not in done:
            row = base_row(w, 0)
            row["result"] = "not_attempted_budget"
            results.append(row)

    def write_jsonl(fname, rows):
        with open(out / fname, "w", encoding="utf-8", newline="\n") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")

    for a in attempts:
        a.pop("path", None)
    write_jsonl("SOURCES.jsonl", sources)
    write_jsonl("ATTEMPTS.jsonl", attempts)
    write_jsonl("EXHAUSTED_PROPOSED.jsonl", exhausted)
    with open(out / "RESULTS.csv", "w", encoding="utf-8", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=RESULT_COLUMNS, lineterminator="\n")
        wr.writeheader()
        wr.writerows(results)

    counts = Counter(r["result"] for r in results)
    summary = {
        "job": name, "run_date": date.today().isoformat(), "offline": offline,
        "items_in_queue": len(queue_items) + len(shared), "items_worked": len(items),
        "from_fetch_queue": len(queue_items), "from_stage20_shared_sources": len(shared),
        "found": counts.get("found", 0),
        "found_carried_forward": sum(1 for r in results if r["carried_forward_from"]),
        "exhausted_proposed_items": counts.get("exhausted_proposed", 0),
        "exhausted_proposed_lines": len(exhausted),
        "retry_later": counts.get("retry_later", 0), "no_route": counts.get("no_route", 0),
        "not_attempted_budget": counts.get("not_attempted_budget", 0),
        "orders_covered_by_found_sources": len({i for s in sources for i in s["instrument_ids"]}),
        "found_by_route": dict(Counter(s["route"] for s in sources)),
        "http_requests": fetcher.requests, "bytes_downloaded": fetcher.bytes_downloaded,
        "attempts_logged": len(attempts), "fetch_queue_problems": problems, "stopped_early": stopped,
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
    print(f"{fetcher.requests} HTTP requests, {fetcher.bytes_downloaded / 1e6:.1f} MB downloaded. Cache: {cache}")
    print("Nothing here changes a status or count; found files are source custody for human review.")


if __name__ == "__main__":
    main()
