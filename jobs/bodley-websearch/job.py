"""Bodley web pass: search the open web, by name, for every order that still lacks an accepted official copy.

Owner, 2026-11-11: "every single one we don't have a source for needs to just be googled and see where it comes up,
and notate where it could be found if you can't access it". Google's own search API is closed to new customers
(shut down 2027-01-01), so this uses the shared search layer (jobs/_lib/eo_websearch.py): every free engine that
answers, then the owner's paid Brave Search API key when the free engines found nothing worth reading for that order.

One pass: every target advances one query strategy (the first is "Executive Order No. N" with the signing year), the
best pages are read and scored for the order's number, date and wording, and each hit's URL is recorded even when
the page cannot be read. Owner, 2026-11-11: the per-run paid limit is lifted for this pass to the existing per-job
lifetime limit (2,500); the 5,000 all-jobs limit is unchanged. Leads only: nothing here changes a status or count.
"""
import csv, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "_lib"))
import eo_identity as ident  # noqa: E402
import eo_websearch as web  # noqa: E402

JOB = "bodley-websearch"
root = os.environ.get("REPO_ROOT") or os.path.abspath(os.path.join(HERE, "..", ".."))
out = os.environ.get("OUTPUT_DIR") or os.path.join(HERE, "output")
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
    d = dates.get(iid) or {}
    pri = 0 if "NO_OFFICIAL_SOURCE_LOCATED" in bl else (1 if r.get("provisional_status") in ("yes", "no") else 2)
    targets.append({"id": iid, "number": p[0], "suffix": p[1], "date": d.get("date", ""), "title": d.get("title", ""),
                    "president": d.get("president", ""), "kind": ",".join(sorted(bl & NEED)), "priority": pri})
print(f"targets: {len(targets)} (unnumbered skipped: {len(skipped)})", flush=True)

env = dict(os.environ)
env.setdefault("EO_PAID_SEARCHES_PER_RUN", "2500")
cache = env.get("JOB_CACHE_DIR") or os.path.join(out, "..", ".web-cache")
summary = web.run_campaign(JOB, root, out, targets, cache_dir=os.path.join(cache, "web"),
                           max_requests=int(env.get("JOB_MAX_REQUESTS", "24000")),
                           max_targets=int(env.get("JOB_MAX_TARGETS", str(len(targets)))),
                           env=env, universe_ids=set(ident.load_universe(root)))
summary["unnumbered_needing_copy_not_searched"] = skipped
with open(os.path.join(out, "WEB_SUMMARY.json"), "w", encoding="utf-8") as fh:
    json.dump(summary, fh, indent=2, sort_keys=True)

# Where each order turned up: the best URL per order, plus every hit host, readable or not.
state = json.load(open(os.path.join(out, "WEB_STATE.json"), encoding="utf-8"))
st = state.get("targets", state)
rows = []
for t in targets:
    s = st.get(t["id"]) or {}
    hits = s.get("hits") or []
    hosts = sorted({re.sub(r"^www\.", "", (h.get("url") or "").split("/")[2]) for h in hits if (h.get("url") or "").count("/") >= 2})
    rows.append({"id": t["id"], "date": t["date"], "needs": t["kind"], "best_score": s.get("best_score", ""),
                 "best_url": s.get("best_url", ""), "hits": len(hits), "hosts": ";".join(hosts[:25]),
                 "pages_read": len(s.get("read") or []), "engines_tried": ";".join(sorted(s.get("engines_tried") or []))})
with open(os.path.join(out, "WHERE_FOUND.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["id"]); w.writeheader(); w.writerows(rows)
lines = ["# Bodley web pass: where each order without an official copy turns up", "",
         f"{summary['advanced_this_run']} of {summary['targets_total']} orders searched this pass; "
         f"{summary['requests_used']} requests; {summary.get('paid_queries_this_run', 0)} paid queries; "
         f"{summary['targets_with_page_confirmed_lead']} orders with a page confirmed to name the order. "
         "`WHERE_FOUND.csv` lists every order with its best URL and every host it appeared on; `WEB_LEADS.csv` the "
         "confirmed pages. Leads only.", "", "| Engine | Status |", "|---|---|"]
lines += [f"| {k} | {v} |" for k, v in sorted(summary["engines"].items())]
open(os.path.join(out, "REPORT.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
print(json.dumps({k: v for k, v in summary.items() if k != "unnumbered_needing_copy_not_searched"}, indent=2))
