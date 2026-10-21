"""Lewis, online stage: hunt the open web for an official original of every order in scope.

Runs after the offline routing (lewis.py). Targets are the orders in ROUTES.csv; those whose best
route is a manual lead (ProQuest phrase search, a volume index, NARA) go first, then everything
else, round-robin across runs, so no order is ever left behind. Each run advances a bounded number
of targets one query strategy across every engine that answers, reads the best pages, and carries
the state forward. See jobs/_lib/eo_websearch.py for the rules.

Environment: JOB_MAX_REQUESTS (default 1500), JOB_MAX_TARGETS (default 100), JOB_CACHE_DIR.
"""
from __future__ import annotations

import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "_lib"))
import eo_identity as ident  # noqa: E402
import eo_websearch as web  # noqa: E402

JOB = "lewis-originals"
PRIORITY = {"proquest_phrase_search": 0, "nara_rg11": 0, "gpo_bound_volumes": 1, "ofr_hoover_compilation": 1,
            "federal_register": 2, "proquest_supplied_link": 3, "proquest_local": 4}


def targets_from_routes(routes, dates):
    out = []
    for r in routes:
        p = ident.parse_eo_id(r["instrument_id"])
        if not p:
            continue
        d = dates.get(r["instrument_id"]) or {}
        out.append({"id": r["instrument_id"], "number": p[0], "suffix": p[1], "date": r.get("date") or d.get("date", ""),
                    "title": r.get("title") or d.get("title", ""), "president": d.get("president", ""),
                    "kind": r.get("best_route", ""), "priority": PRIORITY.get(r.get("best_route", ""), 5)})
    return out


def run(root, out_dir, transport=None, env=None, engines=None):
    routes_path = os.path.join(out_dir, "ROUTES.csv")
    routes = ident.read_csv(routes_path)
    dates = ident.load_dates(root)
    targets = targets_from_routes(routes, dates)
    universe = set(ident.load_universe(root))
    env = os.environ if env is None else env
    cache = env.get("JOB_CACHE_DIR") or os.path.join(out_dir, "..", ".web-cache")
    summary = web.run_campaign(JOB, root, out_dir, targets, cache_dir=os.path.join(cache, "web"),
                               max_requests=int(env.get("JOB_MAX_REQUESTS", "1500")),
                               max_targets=int(env.get("JOB_MAX_TARGETS", "100")),
                               transport=transport, env=env, engines=engines, universe_ids=universe)
    with open(os.path.join(out_dir, "WEB_SUMMARY.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
    append_report(os.path.join(out_dir, "REPORT.md"), summary)
    return summary


def append_report(path, s):
    lines = ["", "## Web search (online stage)", "",
             f"{s['advanced_this_run']} of {s['targets_total']} targets advanced this run ({s['never_searched']} never searched yet); "
             f"{s['requests_used']} of {s['max_requests']} requests used. {s['hits_total']} hits on file, "
             f"{s['leads_page_confirmed']} pages confirmed to name the order ({s['targets_with_page_confirmed_lead']} orders): "
             "`WEB_LEADS.csv`. State in `WEB_STATE.json` carries forward; nothing is marked exhausted by the machine.", "",
             "| Engine | Status |", "|---|---|"]
    for k, v in sorted(s["engines"].items()):
        lines.append(f"| {k} | {v} |")
    with open(path, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    root = os.environ.get("REPO_ROOT") or os.path.abspath(os.path.join(HERE, "..", ".."))
    out = os.environ.get("OUTPUT_DIR") or os.path.join(HERE, "output")
    print(json.dumps(run(root, out), indent=2))
