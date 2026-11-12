"""Bodley web pass: search the open web, by name, for every order that still lacks an accepted official copy.

Owner, 2026-11-11: "every single one we don't have a source for needs to just be googled and see where it comes up,
and notate where it could be found if you can't access it". Google's own search API is closed to new customers
(shut down 2027-01-01), so this uses the shared search layer (jobs/_lib/eo_websearch.py): every free engine that
answers, then the owner's paid Brave Search API key when the free engines found nothing worth reading for that order.

Batched and checkpointed (the first single-shot run hit the 350-minute limit and published nothing): the state, the
leads and the paid ledger are written every BATCH orders, and no new order is started after STOP_AFTER seconds, so
every run publishes and the next run continues where this one stopped (state carried forward from the committed
output). Owner, 2026-11-11: per-run paid limit lifted to the per-job lifetime limit (2,500); 5,000 all-jobs limit kept.
Leads only: nothing here changes a status or count.
"""
import csv, json, os, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "_lib"))
import eo_identity as ident  # noqa: E402
import eo_websearch as web  # noqa: E402

JOB = os.environ.get("JOB_NAME") or "bodley-web-1"
m = re.match(r"bodley-web-(\d+)$", JOB)
SHARD, SHARDS = (int(m.group(1)), 5) if m else (1, 1)
T0 = time.time()
STOP_AFTER = int(os.environ.get("BODLEY_STOP_AFTER", str(int(4.5 * 3600))))
BATCH = 50
root = os.environ.get("REPO_ROOT") or os.path.abspath(os.path.join(HERE, "..", ".."))
out = os.environ.get("OUTPUT_DIR") or os.path.join(HERE, "output")
os.makedirs(out, exist_ok=True)
NEED = {"NO_OFFICIAL_SOURCE_LOCATED", "ONLY_COMPILED_TRANSCRIPTION_FOUND", "ORIGINAL_FOUND_NEEDS_PAGE_CHECK"}

readiness = ident.load_readiness(root)
dates = ident.load_dates(root)
targets, skipped = [], []
for iid, r in readiness.items():
    bl = {b.split(":")[0] for b in (r.get("blockers") or "").split("|") if b}
    if not bl & NEED:
        continue
    p = ident.parse_eo_id(iid)
    if not p:
        skipped.append(iid); continue
    if p[0] % SHARDS != SHARD - 1:
        continue
    d = dates.get(iid) or {}
    pri = 0 if "NO_OFFICIAL_SOURCE_LOCATED" in bl else (1 if r.get("provisional_status") in ("yes", "no") else 2)
    targets.append({"id": iid, "number": p[0], "suffix": p[1], "date": d.get("date", ""), "title": d.get("title", ""),
                    "president": d.get("president", ""), "kind": ",".join(sorted(bl & NEED)), "priority": pri})
by_id = {t["id"]: t for t in targets}
print(f"shard {SHARD}/{SHARDS} ({JOB}); targets: {len(targets)} (unnumbered skipped: {len(skipped)})", flush=True)

env = dict(os.environ)
per_run = int(env.get("EO_PAID_SEARCHES_PER_RUN", "500" if SHARDS > 1 else "2500"))
per_job = int(env.get("EO_PAID_SEARCHES_PER_JOB", str(web.PAID_PER_JOB_DEFAULT)))
total = int(env.get("EO_PAID_SEARCHES_TOTAL", str(web.PAID_TOTAL_DEFAULT)))
paid_mine, paid_all = web.load_paid_ledgers(root, JOB)
allowance = max(0, min(per_run, per_job - paid_mine, total - paid_all))
prior, prior_from = web.load_prior_state(root, JOB)
states = {k: v for k, v in prior.items() if isinstance(v, dict)}
cache = env.get("JOB_CACHE_DIR") or os.path.join(out, "..", ".web-cache")
searcher = web.Searcher(os.path.join(cache, "web"), max_requests=int(env.get("JOB_MAX_REQUESTS", "60000")), env=env,
                        paid_allowance=allowance)
engines = searcher.ready_engines()
print(f"engines ready: {[e['name'] for e in engines]}; paid allowance {allowance} (lifetime used {paid_mine}, all jobs {paid_all})", flush=True)

HIT_FIELDS = ["instrument_id", "score", "page_score", "engine", "strategy", "title", "url", "date", "why", "page_why",
              "page_quote", "page_sha256", "found_utc", "snippet"]

def checkpoint(advanced, final=False):
    stamp = searcher.now()
    json.dump({"job": JOB, "updated_utc": stamp, "prior_state_from": prior_from, "targets": states},
              open(os.path.join(out, "WEB_STATE.json"), "w", encoding="utf-8"), indent=1, sort_keys=True)
    used = sum(searcher.paid_used.values())
    json.dump({"job": JOB, "updated_utc": stamp, "this_run": dict(sorted(searcher.paid_used.items())), "this_run_total": used,
               "this_run_allowance": allowance, "lifetime_paid_queries": paid_mine + used,
               "lifetime_by_engine": {k: v for k, v in sorted(searcher.paid_used.items())},
               "caps": {"per_run": per_run, "per_job": per_job, "total_all_jobs": total},
               "rule": "Paid engines are asked only after the free engines found nothing worth reading for that step; "
                       "counts are queries sent (cached replies may be counted too, so the ledger errs high)."},
              open(os.path.join(out, web.PAID_LEDGER), "w", encoding="utf-8"), indent=1, sort_keys=True)
    hits, leads, rows = [], [], []
    for iid, st in sorted(states.items()):
        for h in st.get("hits") or []:
            row = {"instrument_id": iid, **{k: h.get(k, "") for k in HIT_FIELDS if k != "instrument_id"}}
            row["page_score"] = "" if h.get("page_score") is None else h["page_score"]
            hits.append(row)
            if (h.get("page_score") or 0) >= 60: leads.append(row)
    for name, rr in (("WEB_HITS.csv", hits), ("WEB_LEADS.csv", leads)):
        with open(os.path.join(out, name), "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=HIT_FIELDS); w.writeheader(); w.writerows(rr)
    for t in targets:
        st = states.get(t["id"]) or {}
        hh = st.get("hits") or []
        hosts = sorted({re.sub(r"^www\.", "", (h.get("url") or "").split("/")[2]) for h in hh if (h.get("url") or "").count("/") >= 2})
        rows.append({"id": t["id"], "date": t["date"], "needs": t["kind"], "searched": "yes" if st else "no",
                     "best_score": st.get("best_score", ""), "best_url": st.get("best_url", ""), "hits": len(hh),
                     "hosts": ";".join(hosts[:25]), "pages_read": len(st.get("read") or [])})
    with open(os.path.join(out, "WHERE_FOUND.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["id"]); w.writeheader(); w.writerows(rows)
    status = {e["name"]: searcher.engine_status.get(e["name"], "not_tried") for e in searcher.engines}
    summary = {"targets_total": len(targets), "searched_ever": sum(1 for t in targets if t["id"] in states),
               "advanced_this_run": advanced, "never_searched": sum(1 for t in targets if t["id"] not in states),
               "requests_used": searcher.requests_used, "paid_queries_this_run": used, "paid_allowance_this_run": allowance,
               "hits_total": len(hits), "leads_page_confirmed": len(leads),
               "orders_with_page_confirmed_lead": len({r["instrument_id"] for r in leads}),
               "seconds": round(time.time() - T0), "final": final, "engines": status,
               "unnumbered_needing_copy_not_searched": len(skipped)}
    json.dump(summary, open(os.path.join(out, "WEB_SUMMARY.json"), "w", encoding="utf-8"), indent=2, sort_keys=True)
    return summary

picked = web.pick_targets(states, targets, len(targets))
picked = [t for t in picked if not states.get(t["id"])] or picked  # this pass: orders never searched first
advanced = 0
for t in picked:
    if time.time() - T0 > STOP_AFTER or not searcher.budget_left():
        print("stopping: time or request budget", flush=True); break
    states[t["id"]] = web.advance(searcher, t, states.get(t["id"]) or web.new_state(t), engines)
    advanced += 1
    if advanced % BATCH == 0:
        s = checkpoint(advanced)
        print(f"checkpoint: {advanced} orders, {s['requests_used']} requests, {s['paid_queries_this_run']} paid, "
              f"{s['orders_with_page_confirmed_lead']} with confirmed page, {s['seconds']} s", flush=True)
s = checkpoint(advanced, final=True)
lines = ["# Bodley web pass: where each order without an official copy turns up", "",
         f"{s['searched_ever']} of {s['targets_total']} orders searched so far ({s['advanced_this_run']} this run, "
         f"{s['never_searched']} still waiting); {s['requests_used']} requests and {s['paid_queries_this_run']} paid Brave "
         f"queries this run; {s['orders_with_page_confirmed_lead']} orders with a page confirmed to name the order. "
         "`WHERE_FOUND.csv`: every order with its best URL and every host it appeared on. Leads only.", "",
         "| Engine | Status |", "|---|---|"] + [f"| {k} | {v} |" for k, v in sorted(s["engines"].items())]
open(os.path.join(out, "REPORT.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
print(json.dumps(s, indent=2))
