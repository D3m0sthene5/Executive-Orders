"""Repetita main: list the LSA issues, read each issue's zip, merge rows (cumulative within a year, kept once at the
first issue that prints them), run the controls, write the outputs under a byte budget, resume across runs.

See README.md. Standard library only.
"""
from __future__ import annotations

import concurrent.futures
import csv
import datetime as dt
import json
import os
import shutil
import sys
import threading
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "_lib"))
import lsa  # noqa: E402
import prewar  # noqa: E402
from fetch_pool import FetchPool, FetchError  # noqa: E402

INT_COLS = ("title", "continuation_line", "year_assumed", "eo_mention", "span_start", "span_end", "n_issues")
MB = 1024 * 1024


def now_utc():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_jsonl(p):
    p = Path(p)
    if not p.is_file():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def load_prior(prior: Path):
    """What an earlier run committed: per-issue records, rows, fragments and sources, grouped by first issue."""
    issues = {r["issue"]: r for r in read_jsonl(prior / "ISSUES.jsonl")}
    rows = defaultdict(list)
    for p in sorted(prior.glob("LSA_EO_ROWS*.csv")):
        with open(p, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                for c in INT_COLS:
                    r[c] = int(r[c])
                rows[r["first_issue"]].append(r)
    frags = defaultdict(list)
    for p in sorted(prior.glob("FRAGMENTS*.jsonl")):
        for f in read_jsonl(p):
            d = f.get("data") or [{}]
            frags[d[0].get("first_issue")].append(f)
    srcs = defaultdict(list)
    for s in read_jsonl(prior / "SOURCES.jsonl"):
        srcs[s.get("lsa_issue")].append(s)
    return issues, rows, frags, srcs


def fetch_zip(pool, issue, tries=3):
    """(status, bytes|None, error). status: ok | not_found | failed."""
    url = lsa.PKG_ZIP.format(issue=issue)
    err = ""
    for k in range(tries):
        try:
            got = pool.fetch(url)
            # govinfo answers a package that does not exist with a redirect to /error (HTTP 200 page)
            if got["final_url"].rstrip("/").endswith("/error") or not got["body"].startswith(b"PK"):
                return "not_found", None, "no package at this address (redirected to govinfo error page)"
            return "ok", got, ""
        except FetchError as e:
            err = str(e)
            if err.startswith("HTTP 404"):
                return "not_found", None, err
            if err.startswith("blocked_by_robots"):
                return "failed", None, err
        except Exception as e:  # noqa: BLE001
            err = f"{type(e).__name__}: {e}"
        time.sleep(3 * (k + 1))
    return "failed", None, err[:200]


def main(repo: Path, out: Path, cache: Path, env=os.environ, transport=None, opener=None, today=None, prior_dir=None):
    started = time.monotonic()
    today = today or dt.date.today()
    out.mkdir(parents=True, exist_ok=True)
    smoke = env.get("JOB_SMOKE") == "1" or (env.get("JOB_SMOKE") != "0" and (HERE / "SMOKE").exists())
    force = env.get("JOB_FORCE") == "1"
    workers = max(1, min(int(env.get("JOB_WORKERS") or 4), 8))
    deadline = started + float(env.get("JOB_TIME_BUDGET_MIN") or 300) * 60
    budget = lsa.Budget(out)
    pool = FetchPool(cache / "lsa", workers=workers, per_host=min(workers, 4), transport=transport,
                     max_bytes=60_000_000, timeout=180, user_agent=lsa.UA, min_interval=0.25,
                     max_cache_bytes=int(env.get("JOB_CACHE_MB") or 256) * MB)
    print(f"repetita: smoke={smoke} workers={workers}", flush=True)

    issues, list_problems = lsa.list_issues(pool, today)
    if smoke:
        issues = [(i, False) for i in lsa.SMOKE_ISSUES]
    key, key_kind, key_name = lsa.api_key(env)
    if key_kind == "demo" and not smoke:
        key, key_kind = "", "demo_refused_for_full_run"
    cross = {"attempted": False}
    if key and (key_kind == "real" or smoke):
        try:
            api_ids = set(lsa.api_listing(key, opener=env.get("_API_OPENER")))
            mine = {i for i, _ in issues}
            cross = {"attempted": True, "api_issues": len(api_ids)}
            if not smoke:
                cross.update(in_api_not_in_listing=sorted(api_ids - mine)[:20],
                             in_listing_not_in_api=sorted(i for i, s in issues if not s and i not in api_ids)[:20])
        except Exception as e:  # noqa: BLE001
            cross = {"attempted": True, "error": f"{type(e).__name__}: {str(e)[:120]}".replace(key, "***")}
    route = {"bytes_route": "keyless: https://www.govinfo.gov/content/pkg/<issue>.zip (robots.txt permits /content/)",
             "listing_route": "keyless: www.govinfo.gov LSA year sitemaps",
             "api_key_present": key_kind in ("real", "demo", "demo_refused_for_full_run"), "api_key_kind": key_kind,
             "api_key_env_name": key_name or None,
             "api_crosscheck": cross,
             "note": "The govinfo API (key in X-Api-Key) is used only to cross-check the listing, and only with a real "
                     "API_DATA_GOV_KEY (or GOVINFO_API_KEY); DEMO_KEY is refused for a full run. The full run does not "
                     "wait for a key: it reads the keyless content URLs."}
    print(f"repetita: {len(issues)} issues listed ({sum(1 for _, s in issues if s)} speculative); problems {list_problems}", flush=True)

    prior_dir = Path(prior_dir or env.get("JOB_PRIOR_OUTPUT_DIR") or (HERE / "output"))
    p_issues, p_rows, p_frags, p_srcs = ({}, defaultdict(list), defaultdict(list), defaultdict(list))
    if not smoke and not force and prior_dir.is_dir():
        p_issues, p_rows, p_frags, p_srcs = load_prior(prior_dir)
    newest = {i for i, s in issues if not s}
    newest = set(sorted(newest)[-2:])
    todo = [(i, s) for i, s in issues if not (p_issues.get(i, {}).get("status") == "ok" and i not in newest)]
    carried = [i for i, _ in issues if i not in {t[0] for t in todo}]
    print(f"repetita: {len(todo)} to read, {len(carried)} carried from the previous run", flush=True)

    counters = Counter()
    lock = threading.Lock()

    def work(item):
        issue, spec = item
        if time.monotonic() > deadline:
            return {"issue": issue, "status": "deferred"}
        status, got, err = fetch_zip(pool, issue)
        with lock:
            counters["requested"] += 1
            counters[status] += 1
        if status != "ok":
            return {"issue": issue, "status": status, "speculative": spec, "error": err}
        retrieved = now_utc()
        res = lsa.process_zip(issue, got["body"], retrieved)
        meta, bodyp, _, _ = pool._paths(lsa.PKG_ZIP.format(issue=issue))
        for pth in (meta, bodyp):
            try:
                pth.unlink()
            except OSError:
                pass
        return {"issue": issue, "status": "ok" if not res["errors"] and res["members"] else "failed", "speculative": spec,
                "res": res, "zip_sha256": got["sha256"], "zip_bytes": got["bytes"], "retrieved": retrieved,
                "error": "; ".join(res["errors"])[:200]}

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        for n, r in enumerate(ex.map(work, todo), 1):
            results[r["issue"]] = r
            if n % 20 == 0 or n == len(todo):
                print(f"repetita: {n}/{len(todo)} read, {Counter(x['status'] for x in results.values())}", flush=True)

    # ------------------------------------------------------------------ merge, chronologically
    seen = {}
    final_rows, final_sources, issue_records = [], [], []
    for issue, spec in issues:
        date = lsa.issue_date_of(issue)
        r = results.get(issue)
        if r is None:  # carried
            rec = dict(p_issues[issue])
            rec["carried_forward"] = True
            issue_records.append(rec)
            for row in p_rows.get(issue, []):
                key = lsa.row_key(row)
                if key in seen:
                    ex_ = seen[key]
                    ex_["n_issues"] += row["n_issues"]
                    ex_["last_issue"] = max(ex_["last_issue"], row["last_issue"])
                else:
                    row["_frags"] = []
                    seen[key] = row
                    final_rows.append(row)
            # fragments are attached to the carried row that holds their key by (item, change, ref, span)
            for f in p_frags.get(issue, []):
                d = f["data"][0]
                for row in p_rows.get(issue, []):
                    if (row["eo_target"] == f["instrument_id"] and row["fr_ref"] == d["fr_ref"]
                            and f"{row['span_start']}-{row['span_end']}" == d["quote_span"]
                            and d["acting_id"] in row["acting"].split("|")):
                        row.setdefault("_frags", []).append(f)
                        break
            final_sources += p_srcs.get(issue, [])
            continue
        rec = {"issue": issue, "issue_date": date, "status": r["status"], "speculative": spec,
               "zip_url": lsa.PKG_ZIP.format(issue=issue)}
        if r["status"] != "ok":
            rec["error"] = r.get("error", "")
            issue_records.append(rec)
            continue
        res = r["res"]
        rec.update({"zip_sha256": r["zip_sha256"], "zip_bytes": r["zip_bytes"], "retrieved_utc": r["retrieved"],
                    "members": res["stats"].get("members", 0), "entries": res["stats"].get("entries", 0),
                    "leader_lines_independent": res["stats"].get("leader_lines_independent", 0),
                    "dropped_pending_lines": res["stats"].get("dropped_pending", 0),
                    "span_checks": res["stats"].get("span_checks", 0),
                    "span_check_failures": res["stats"].get("span_check_failures", 0),
                    "controls": [{"name": c["name"], "kind": c["kind"], "ok": c["ok"]} for c in res["controls"]],
                    "rows_before_dedupe": len(res["rows"]),
                    "title3_rows_before_dedupe": sum(1 for x in res["rows"] if x["title"] == 3),
                    "eo_mention_rows_before_dedupe": sum(1 for x in res["rows"] if x["eo_mention"])})
        zsrc = lsa.source_record(issue, "zip", rec["zip_url"], r["zip_sha256"], r["zip_bytes"], r["retrieved"],
                                 "package zip (html, pdf, mods, premis, dip)", {"members_read": res["stats"].get("members", 0)})
        msrc = {}
        used_titles = {x["title"] for x in res["rows"]}
        for m in res["members"]:
            if m["title"] in used_titles or m["title"] == 3:
                msrc[m["title"]] = lsa.source_record(
                    issue, f"title{m['title']}", lsa.MEMBER_URL.format(issue=issue, title=m["title"]), m["sha256"],
                    m["bytes"], r["retrieved"], f"{m['member']} (member of {issue}.zip, sha256 {r['zip_sha256'][:16]}...)",
                    {"zip_sha256": r["zip_sha256"]})
        final_sources += [zsrc] + [msrc[t] for t in sorted(msrc)]
        issue_records.append(rec)
        for row in res["rows"]:
            key = lsa.row_key(row)
            if key in seen:
                ex_ = seen[key]
                if ex_["last_issue"] != issue:
                    ex_["last_issue"] = max(ex_["last_issue"], issue)
                    ex_["n_issues"] += 1
                continue
            row["_frags"] = lsa.fragments_for(row, msrc[row["title"]]) if row["title"] in msrc else []
            seen[key] = row
            final_rows.append(row)

    final_rows.sort(key=lambda r: (r["first_issue"], r["title"], r["span_start"], str(r["fr_ref"])))
    fragments = [f for r in final_rows for f in r.get("_frags", [])]

    # ------------------------------------------------------------------ controls over everything
    ok_issues = [x for x in issue_records if x["status"] == "ok"]
    ctrl_rows = []
    for x in ok_issues:
        ctrl_rows += [dict(c, issue=x["issue"]) for c in x.get("controls", [])]
    neg = lsa.negative_controls(final_rows)
    # one public member URL per sampled issue must hash to the zip member's bytes
    sample = [x for x in ok_issues if not x.get("carried_forward")]
    pick = sample if len(sample) <= 3 else [sample[0], sample[len(sample) // 2], sample[-1]]
    member_checks = []
    for x in pick:
        s3 = next((s for s in final_sources if s["source_id"] == f"lsa:{x['issue']}:title3"), None)
        if not s3:
            member_checks.append({"name": "member_url_hash_equals_zip_member", "kind": "positive", "issue": x["issue"], "ok": False, "why": "no title3 source"})
            continue
        try:
            got = pool.fetch(s3["url"])
            member_checks.append({"name": "member_url_hash_equals_zip_member", "kind": "positive", "issue": x["issue"],
                                  "ok": got["sha256"] == s3["sha256"], "url": s3["url"], "direct_sha256": got["sha256"],
                                  "zip_member_sha256": s3["sha256"]})
        except Exception as e:  # noqa: BLE001
            member_checks.append({"name": "member_url_hash_equals_zip_member", "kind": "positive", "issue": x["issue"], "ok": False,
                                  "why": f"{type(e).__name__}: {e}"[:150]})
    all_checks = ctrl_rows + neg + member_checks
    planted = [c for c in ctrl_rows if c["name"].startswith("planted")]
    known = [c for c in ctrl_rows if c["name"].startswith("known_fact")]
    span_checks = sum(x.get("span_checks", 0) for x in ok_issues)
    span_fail = sum(x.get("span_check_failures", 0) for x in ok_issues)

    def rate(cs):
        return round(sum(1 for c in cs if not c["ok"]) / len(cs), 6) if cs else None
    controls = {
        "generated_utc": now_utc(),
        "design": "Planted controls run on every issue's own Title 3 bytes (a planted positive entry must be read with "
                  "its exact span; a planted line without a dot leader and one with a non-numeric reference must not "
                  "become entries; the planted block must add exactly one entry). Known facts: Title 3 entries whose "
                  "order, change and Federal Register citation are known from the orders themselves, in named issues. "
                  "Negatives: made-up and near-miss entries must be absent from every row. Member check: the public "
                  "html URL hashes to the same bytes as the zip member. Span check: every entry re-sliced from the "
                  "held bytes ends with its reference and starts with its item.",
        "planted": {"checks": len(planted), "failures": sum(1 for c in planted if not c["ok"]), "error_rate": rate(planted)},
        "known_facts": {"checks": len(known), "failures": sum(1 for c in known if not c["ok"]), "error_rate": rate(known),
                        "facts": [{k: v for k, v in c.items() if k in ("issue", "name", "ok")} for c in known]},
        "negatives_on_final_rows": {"checks": len(neg), "failures": sum(1 for c in neg if not c["ok"]), "error_rate": rate(neg), "detail": neg},
        "member_url_hash": {"checks": len(member_checks), "failures": sum(1 for c in member_checks if not c["ok"]), "detail": member_checks},
        "span_check": {"checks": span_checks, "failures": span_fail, "error_rate": round(span_fail / span_checks, 6) if span_checks else None},
        "control_error_rate": round((sum(1 for c in all_checks if not c["ok"]) + span_fail) / (len(all_checks) + span_checks), 6)
        if (all_checks or span_checks) else None,
        "control_error_rate_excluding_span_checks": rate(all_checks),
        "failed_controls": [c for c in all_checks if not c["ok"]][:50],
    }

    # ------------------------------------------------------------------ pre-1997
    pre_rows, pre_summary = [], None
    prior_pre = prior_dir / "PRE1997_SUMMARY.json"
    if env.get("JOB_SKIP_PRE1997") == "1":
        pre_summary = {"skipped": "JOB_SKIP_PRE1997"}
    elif not smoke and not force and prior_pre.is_file() and (prior_dir / "PRE1997_MANIFEST.csv").is_file():
        pre_summary = json.loads(prior_pre.read_text(encoding="utf-8"))
        with open(prior_dir / "PRE1997_MANIFEST.csv", newline="", encoding="utf-8") as fh:
            pre_rows = list(csv.DictReader(fh))
        pre_summary["carried_forward"] = True
    else:
        try:
            pre_rows, pre_summary = prewar.build(pool, lsa.UA, opener or prewar.open_stream, skip_hathi=False)
        except Exception as e:  # noqa: BLE001  the manifest never costs the LSA results
            pre_rows, pre_summary = [], {"error": f"{type(e).__name__}: {e}"[:300]}
        pre_summary["generated_utc"] = now_utc()

    # ------------------------------------------------------------------ write, small files first
    rows_out = [{k: v for k, v in r.items() if not k.startswith("_")} for r in final_rows]
    ok_n = sum(1 for x in issue_records if x["status"] == "ok")
    failed = [x for x in issue_records if x["status"] == "failed" or (x["status"] == "not_found" and not x.get("speculative"))]
    deferred = [x["issue"] for x in issue_records if x["status"] == "deferred"]
    not_found_spec = [x["issue"] for x in issue_records if x["status"] == "not_found" and x.get("speculative")]
    by_year = Counter(r["first_issue"][4:8] for r in rows_out)
    summary = {
        "job": "repetita-lsa", "generated_utc": now_utc(), "smoke": smoke, "seconds": round(time.monotonic() - started, 1),
        "issues_listed": len(issues), "issues_read_ok": ok_n, "issues_read_this_run": sum(1 for r in results.values() if r["status"] == "ok"),
        "issues_carried_forward": len(carried), "issues_failed": len(failed), "issues_deferred_by_time": len(deferred),
        "issues_not_found_speculative": len(not_found_spec), "failed_issues": [{"issue": x["issue"], "error": x.get("error", "")} for x in failed][:50],
        "rows": len(rows_out), "title3_rows": sum(1 for r in rows_out if r["title"] == 3),
        "eo_mention_rows": sum(1 for r in rows_out if r["eo_mention"]),
        "eo_category_rows_with_target": sum(1 for r in rows_out if r["eo_target"]),
        "eo_mention_rows_outside_title3": sum(1 for r in rows_out if r["eo_mention"] and r["title"] != 3),
        "rows_before_dedupe_this_run": sum(x.get("rows_before_dedupe", 0) for x in issue_records if not x.get("carried_forward")),
        "fragments": len(fragments), "sources": len(final_sources), "rows_by_first_issue_year": dict(sorted(by_year.items())),
        "entries_parsed_all_titles": sum(x.get("entries", 0) for x in ok_issues),
        "leader_lines_independent_all_titles": sum(x.get("leader_lines_independent", 0) for x in ok_issues),
        "requests": pool.requests, "bytes_downloaded": pool.bytes_downloaded, "fetch_counters": dict(counters),
        "list_problems": list_problems, "route": route,
        "control_error_rate": controls["control_error_rate"], "planted_error_rate": controls["planted"]["error_rate"],
        "known_fact_error_rate": controls["known_facts"]["error_rate"],
        "complete": not deferred and not failed, "pre1997": pre_summary,
        "limits": "Leads only. An LSA entry names a change and a Federal Register page this job does not hold. No "
                  "status, census, codebook or count change. Certified: 0.",
    }
    budget.write("CONTROLS.json", (json.dumps(controls, indent=1, sort_keys=True) + "\n").encode())
    budget.write("ISSUES.jsonl", lsa.jsonl_bytes(issue_records))
    budget.write("SOURCES.jsonl", lsa.jsonl_bytes(sorted(final_sources, key=lambda s: s["source_id"])))
    if pre_rows:
        budget.write("PRE1997_MANIFEST.csv", lsa.csv_bytes(pre_rows, prewar.MANIFEST_COLUMNS))
    if pre_summary is not None:
        budget.write("PRE1997_SUMMARY.json", (json.dumps(pre_summary, indent=1, sort_keys=True) + "\n").encode())
    row_files = lsa.write_sharded(budget, "LSA_EO_ROWS", ".csv", rows_out, lambda rs: lsa.csv_bytes(rs, lsa.ROW_COLUMNS),
                                  lambda r: r["first_issue"][4:8])
    frag_files = lsa.write_sharded(budget, "FRAGMENTS", ".jsonl", fragments, lsa.jsonl_bytes,
                                   lambda f: f["data"][0]["first_issue"][4:8])
    summary["row_files"], summary["fragment_files"] = row_files, frag_files
    summary["budget_refused"] = budget.refused
    budget.write("SUMMARY.json", (json.dumps(summary, indent=1, sort_keys=True) + "\n").encode())
    bj = {"generated_utc": now_utc(), "limit_total_bytes": budget.total, "limit_per_file_bytes": budget.per_file,
          "committed_bytes_before_this_file": budget.used(), "files": dict(sorted(budget.files.items())),
          "refused": budget.refused, "truncated": bool(budget.refused),
          "note": "Raw zips and html stay in the job cache and are never committed. log.txt and STATUS.json are the runner's."}
    data = (json.dumps(bj, indent=1) + "\n").encode()
    bj["committed_bytes_total_with_this_file"] = budget.used() + len(data) + 40
    budget.write("BUDGET.json", (json.dumps(bj, indent=1) + "\n").encode())
    print(json.dumps({k: v for k, v in summary.items() if k not in ("pre1997", "rows_by_first_issue_year", "failed_issues")}, indent=1))
    print("pre-1997:", json.dumps(pre_summary)[:1500])

    # ------------------------------------------------------------------ failure rules
    attempted = ok_n + len(failed)
    if budget.refused:
        sys.exit(f"byte budget exceeded; refused {budget.refused}")
    if not smoke and attempted and len(failed) > ok_n:
        sys.exit(f"most issue requests failed: {len(failed)} failed, {ok_n} ok")
    if smoke and failed:
        sys.exit(f"smoke: {len(failed)} of {len(issues)} issues failed: {failed[:3]}")
    if not rows_out:
        sys.exit("no rows parsed")
    if controls["control_error_rate"] is not None and controls["control_error_rate"] > 0.05:
        sys.exit(f"controls failed: error rate {controls['control_error_rate']}")
    if (counters["requested"] and counters["failed"] > counters["ok"]):
        sys.exit("most zip requests failed")
    return summary
