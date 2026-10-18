"""Federal Register originals job. Runs the unit tests first. See README.md.

Environment: OUTPUT_DIR (required), REPO_ROOT (default "."), JOB_LIMIT (max
orders, in priority order), JOB_CACHE_DIR (default <OUTPUT_DIR>/../fr-originals-cache),
JOB_TIME_BUDGET_MIN, JOB_MAX_REQUESTS, JOB_ONLY_IDS (comma list), JOB_KEEP_PDFS (1 keep / 0 delete scanned
issues after use), JOB_RETRY_NOT_FOUND=1, JOB_OFFLINE=1, JOB_CARRY_FORWARD=0 (do not
seed from data/full_run/ and the last committed output/).
On GitHub (GITHUB_ACTIONS=true) the defaults come from settings.json.
JOB_LIMIT counts only orders that still need work; orders already finished
(in the cache or in committed results) are always kept in the outputs.

Opt-in RECHECK mode (fr_recheck.py, pdfplumber): JOB_RECHECK=1, or "recheck": true in
settings.json. It rechecks found orders whose result is not high (needs_page_check true);
JOB_RECHECK_LIMIT (default: all; settings "recheck_github_limit" on GitHub),
JOB_RECHECK_ONLY_IDS, JOB_RECHECK_REDO=1. In recheck mode no new orders are located
unless JOB_LIMIT is given. The default run is unchanged.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run_tests():
    r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(HERE), "-p", "test_*.py"], cwd=HERE)
    if r.returncode:
        sys.exit("Unit tests failed; the job did not run.")


def env(name, default=None):
    v = os.environ.get(name, "").strip()
    return v if v else default


def main():
    run_tests()
    out = Path(os.environ["OUTPUT_DIR"]).resolve()
    repo = Path(env("REPO_ROOT", ".")).resolve()
    sys.path.insert(0, str(repo / "jobs" / "source-ladder"))
    sys.path.insert(0, str(HERE))
    import fetch_ladder
    import fr_originals
    import ofr_index
    import prior_output

    name = env("JOB_NAME", "fr-originals")
    cache = Path(env("JOB_CACHE_DIR") or (out.parent / f"{name}-cache")).resolve()
    settings = json.loads((HERE / "settings.json").read_text(encoding="utf-8"))
    on_github = env("GITHUB_ACTIONS") == "true"
    limit = env("JOB_LIMIT")
    limit = int(limit) if limit else (settings["github_default_limit"] if on_github else None)
    budget = env("JOB_TIME_BUDGET_MIN")
    budget = float(budget) if budget else (settings["github_time_budget_minutes"] if on_github else None)
    keep = env("JOB_KEEP_PDFS")
    keep = (keep == "1") if keep is not None else (settings["github_keep_issue_pdfs"] if on_github else True)
    max_req = env("JOB_MAX_REQUESTS")
    recheck = (env("JOB_RECHECK") == "1") if env("JOB_RECHECK") is not None else bool(settings.get("recheck", False))
    if recheck and env("JOB_LIMIT") is None:
        limit = 0  # recheck mode: only recheck, unless JOB_LIMIT asks for new orders too

    universe = set()
    if (repo / fr_originals.PATHS["universe"]).exists():
        universe = {r["id"] for r in fr_originals.read_csv(repo / fr_originals.PATHS["universe"])}
    index = ofr_index.load_index(index_dir=HERE / "data" / "ofr_index", universe_ids=universe)
    plan = full_plan = fr_originals.build_plan(repo, index)
    only = [x.strip() for x in (env("JOB_ONLY_IDS") or "").split(",") if x.strip()]
    if only:  # a targeted run, e.g. JOB_ONLY_IDS=EO:9337,EO:10586
        plan = [p for p in plan if p["instrument_id"] in set(only)]
    print(f"OFR index: {len(index)} orders. In scope: {len(plan)} "
          f"({sum(1 for p in plan if p['decided'])} decided first). "
          f"This run: {limit if limit is not None else 'all'} orders; keep scanned PDFs: {keep}; cache: {cache}")

    ctx_spec = {"repo": str(repo), "cache": str(cache), "offline": env("JOB_OFFLINE") == "1",
                "max_requests": int(max_req) if max_req else None}
    ctx = fr_originals.make_ctx(**ctx_spec)
    fetcher = ctx["fetcher"]
    workers = env("JOB_WORKERS")
    workers = int(workers) if workers else settings.get("github_workers", 4) if on_github \
        else fr_originals.default_workers(False)
    print(f"Worker processes: {workers} (set JOB_WORKERS to change; 1 = one order at a time)")
    # Results committed earlier are never thrown away: the owner's full PC run
    # (data/full_run/) and the last committed output/ seed the state folder first.
    prior_found = 0
    if env("JOB_CARRY_FORWARD", "1") != "0":
        priors = []
        if env("JOB_PRIOR_OUTPUT_DIR"):  # e.g. the output folder of a PC run kept outside the repo
            priors.append(prior_output.PriorOutput.from_folder(env("JOB_PRIOR_OUTPUT_DIR")))
        if (HERE / "data" / "full_run" / "SOURCES.jsonl").is_file():
            priors.append(prior_output.PriorOutput.from_folder(HERE / "data" / "full_run",
                                                                label=f"jobs/{name}/data/full_run"))
        priors.append(prior_output.PriorOutput.from_git_head(repo, f"jobs/{name}/output"))
        carried, prior_found = fr_originals.carry_forward(ctx, full_plan, priors)
        import fr_recheck
        fr_recheck.carry_forward_recheck(ctx, full_plan, priors)
    states, info = fr_originals.run(ctx, plan, limit=limit, time_budget_s=budget * 60 if budget else None,
                                    retry_not_found=env("JOB_RETRY_NOT_FOUND") == "1", keep_pdfs=keep,
                                    workers=workers, ctx_spec=ctx_spec)
    extra = {"settings_used": {"limit": limit, "time_budget_minutes": budget, "keep_issue_pdfs": keep,
                               "on_github": on_github, "only_ids": only}}
    import fr_recheck
    rinfo = None
    if recheck:
        rlimit = env("JOB_RECHECK_LIMIT")
        rlimit = int(rlimit) if rlimit else (settings.get("recheck_github_limit") if on_github else None)
        ronly = [x.strip() for x in (env("JOB_RECHECK_ONLY_IDS") or "").split(",") if x.strip()]
        print(f"RECHECK mode (pdfplumber): rechecking medium/low finds; limit {rlimit if rlimit is not None else 'all'}.")
        _, rinfo = fr_recheck.run_recheck(ctx, plan, states, limit=rlimit,
                                          time_budget_s=budget * 60 if budget else None, keep_pdfs=keep,
                                          only=ronly, redo=env("JOB_RECHECK_REDO") == "1")
        extra["settings_used"].update(recheck=True, recheck_limit=rlimit, recheck_only_ids=ronly)
    s = fr_originals.write_outputs(out, ctx, plan, states, info, extra, full_plan=full_plan,
                                   prior_found=prior_found)
    if recheck or fr_recheck.recheck_dir(ctx).is_dir():
        rs = fr_recheck.write_recheck_outputs(out, ctx, full_plan, states, rinfo)
        print(f"Recheck: {rs['orders_rechecked_total']} orders rechecked so far: {rs['upgraded_to_high']} upgraded to "
              f"high, {rs['stayed']} stayed as they were, {rs['errors']} errors (of {rs['orders_eligible_now']} "
              "medium/low orders in the outputs). See RECHECK.jsonl / RECHECK_SUMMARY.json.")
        if recheck:
            s["recheck"] = {k: rs[k] for k in ("orders_eligible_now", "orders_rechecked_total", "upgraded_to_high",
                                              "stayed", "errors", "by_base_confidence_and_result",
                                              "upgrades_by_evidence_kind", "upgraded_with_other_pages_than_base",
                                              "heading_found_off_the_cited_page", "this_run") if k in rs}
            s["recheck"]["details"] = "RECHECK_SUMMARY.json (examples, stay reasons) and RECHECK.jsonl (evidence per order)"
            import fetch_ladder as _fl
            _fl.write_text_lf(out / "SUMMARY.json", json.dumps(s, indent=1) + "\n")
    est = s["full_run_estimate"]
    print()
    print(f"Done in {info['stats'].get('seconds')} s. This run worked {info['selected']} orders; "
          f"{info.get('already_finished', 0)} were already finished. {s['orders_completed_in_outputs']} orders in the outputs: "
          f"{s['found']} originals found ({s['found_decided']} of them decided orders; by confidence "
          f"{s['found_by_confidence']}), {s['reused_stage21_captures']} reused from Stage 21, "
          f"{s['not_found']} not found {s['not_found_by_reason']}.")
    if s["stopped_early"]:
        print(f"Stopped early: {s['stopped_early']}; {s['pending_not_reached']} selected orders left for the next run.")
    if info["stats"].get("parallel_workers"):
        print(f"{workers} worker processes; downloads were counted inside the workers.")
    else:
        print(f"{fetcher.requests} HTTP requests, {fetcher.bytes_downloaded / 1e6:.0f} MB downloaded.")
    if est["of_which_need_network"] == 0:
        print("Full-run projection: nothing left that needs a download.")
    elif est["decades_without_a_measured_issue"] or any(not d["measured"] for d in est["by_decade"].values())             or est["estimated_hours"] is None:
        print(f"Full-run projection: {est['of_which_need_network']} orders still need a download. Not enough data "
              "yet for a projection (some decades have no measured issue); see README: about 130 GB and 8-16 hours.")
    else:
        print(f"Full-run projection: {est['orders_not_yet_done']} orders left, about {est['estimated_download_gb']} GB "
              f"and {est['estimated_hours']} hours (rough).")
    if s["shrink_check"] != "ok":
        print(s["shrink_check"])
    print("These are source-custody and location leads only; no status or count is changed.")


if __name__ == "__main__":
    main()
