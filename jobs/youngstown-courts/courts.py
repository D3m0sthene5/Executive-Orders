"""Youngstown courts: court decisions that print an executive order's number, from CourtListener's public bulk files.

Why bulk and not the API: the REST API answers 401 without a token, and with one the documented default limits are 5
requests a minute, 50 an hour and 125 a day, so one search per order (14,900 orders) is out of reach. The bulk CSVs
(S3 bucket com-courtlistener-storage, quarterly, Public Domain Mark) need no account. This job streams the one
55 GB opinions file in block-aligned segments (jobs/youngstown-courts/bz2seg.py), finds every opinion whose text
prints a register order's number, classifies the sentence by transparent rules, joins cluster, docket, court and
citation tables, and commits only the located spans and small tables. Zero model tokens.

Every hit is a lead for a person and the claim kit, never a legal status.
"""
from __future__ import annotations

import concurrent.futures
import csv
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "_lib"))
import analyze  # noqa: E402
import bulk  # noqa: E402
import bz2seg  # noqa: E402
import controls  # noqa: E402
import scan  # noqa: E402
from fetch_pool import FetchPool, FetchError, http_transport  # noqa: E402

UA = "EO-Road-System/1.0 (Youngstown court-decision leads; owner-run research; +https://github.com/D3m0sthene5/Executive-Orders)"
MIB = 1024 * 1024
FILE_CAP, TOTAL_CAP = 5 * MIB, 20 * MIB
CAPS = {"hits": int(4.8 * MIB), "fragments": int(4.8 * MIB), "sources": int(4.8 * MIB)}
EST = {"hits": 1800, "fragments": 4300, "sources": 1250}
TABLES = {"opinions": "opinions", "clusters": "opinion-clusters", "dockets": "dockets", "citations": "citations",
          "courts": "courts"}
SOURCE_TAG = "courtlistener_bulk"
API_SEARCH = "https://www.courtlistener.com/api/rest/v4/search/"


def log(msg):
    print(msg, flush=True)


# ---- config -------------------------------------------------------------------------------------------------------

def load_config(env):
    cfg = {"mode": "smoke", "snapshot": "latest", "seg_mb": 256, "smoke_windows": 6, "smoke_window_mb": 48,
           "focus_orders": [], "mentions_per_order": 3, "api_requests": 40, "reserve_minutes": 80}
    p = HERE / "config.json"
    if p.is_file():
        cfg.update(json.loads(p.read_text(encoding="utf-8")))
    if env.get("JOB_MODE"):
        cfg["mode"] = env["JOB_MODE"]
    if env.get("JOB_SEG_MB"):
        cfg["seg_mb"] = float(env["JOB_SEG_MB"])
    if cfg["mode"] not in ("smoke", "full"):
        raise SystemExit("config mode must be smoke or full")
    return cfg


# ---- worker side --------------------------------------------------------------------------------------------------

_G = {}


def worker_init(g):
    _G.clear()
    _G.update(g)


def _source(task, stats):
    transport = _G.get("transport") or http_transport
    return bulk.HttpSource(task["url"], transport, UA, stats=stats, known=(task["size"], task["etag"], task["last_modified"]),
                           sleep=_G.get("sleep", time.sleep))


def run_task(task):
    """One segment of one bulk table. Returns a small summary; the full result goes to a cache file."""
    cache = Path(_G["cache"])
    key = bulk.seg_key(task["url"], task["etag"], task["start_bit"], task["end_bit"], task["kind"] + task.get("tag", ""))
    path = bulk.seg_path(cache, task["kind"], task["idx"], key)
    stats = {"requests": 0, "failures": 0}
    held = bulk.load_json_gz(path) if path.is_file() else None
    if held is not None:
        out = {"idx": task["idx"], "kind": task["kind"], "cached": True, "path": str(path), "requests": 0, "failures": 0,
               "compressed_bytes": task.get("compressed_bytes", 0)}
        if task["kind"] == "opn" and held.get("analysis") != analyze.ANALYSIS_VERSION:
            out.update(reanalyze(held, cache, _G["keys"]))
            held["analysis"] = analyze.ANALYSIS_VERSION
            bulk.save_json_gz(path, held)
        return out
    src = _source(task, stats)
    level = task["level"]
    kind = task["kind"]
    c = Counter()
    if kind == "opn":
        keys = _G["keys"]
        header = task["header"]
        records, unreg = [], Counter()

        def handle(raw):
            row = bulk.parse_row(raw, header)
            if row is None:
                c["rows_unparsed"] += 1
                return
            c["rows_parsed"] += 1
            rec, un, notes, rawtext = analyze.analyze_row(row, keys)
            unreg.update(un)
            for k, v in notes.items():
                c[k] += v
            if rec:
                records.append(rec)
                analyze.save_raw(cache, rec["oid"], rawtext)
        sc = bulk.scan_segment(src, level, task["start_bit"], task["end_bit"], task["final"], bulk.prefilter_select, handle,
                               eos_bit=task.get("eos"))
        result = {"records": records, "unreg": dict(unreg), "counters": dict(c), "scan": sc, "analysis": analyze.ANALYSIS_VERSION}
    elif kind in ("clu", "dok"):
        header = task["header"]
        wanted = set(task["wanted"])
        store = {}

        def handle(raw):
            row = bulk.parse_row(raw, header)
            if row is None:
                c["rows_unparsed"] += 1
                return
            rid = int(row["id"])
            if kind == "clu":
                store[rid] = {"case_name": row["case_name"], "date_filed": row["date_filed"], "slug": row["slug"],
                              "docket_id": int(row["docket_id"] or 0), "status": row["precedential_status"]}
            else:
                store[rid] = {"court_id": row["court_id"], "docket_number": row["docket_number"]}
        sc = bulk.scan_segment(src, level, task["start_bit"], task["end_bit"], task["final"], bulk.id_select(wanted), handle,
                               eos_bit=task.get("eos"))
        result = {"store": {str(k): v for k, v in store.items()}, "counters": dict(c), "scan": sc}
    elif kind == "cit":
        wanted = set(task["wanted"])
        store = defaultdict(list)
        dec = bz2seg.SegmentDecoder(src, task["start_bit"], task["end_bit"], level, final=task["final"], eos_bit=task.get("eos"))
        carry = b""
        t0 = time.monotonic()
        for chunk in dec.chunks():
            data = carry + chunk
            lines = data.split(b"\n")
            carry = lines.pop()
            for ln in lines:
                parts = ln.split(b",")
                if len(parts) < 6:
                    continue
                try:
                    cid = int(parts[5].strip(b'"'))
                except ValueError:
                    continue
                if cid in wanted:
                    store[str(cid)].append([int(parts[4].strip(b'"') or 0),
                                            " ".join(x.strip(b'"').decode("utf-8", "replace") for x in parts[1:4])])
        result = {"store": dict(store), "counters": {}, "scan": {"decoded_bytes": dec.decoded, "compressed_bytes": dec.compressed_read,
                                                                 "seconds": round(time.monotonic() - t0, 1)}}
    else:
        raise ValueError(kind)
    bulk.save_json_gz(path, result)
    return {"idx": task["idx"], "kind": kind, "cached": False, "path": str(path), "requests": stats["requests"],
            "failures": stats["failures"], "compressed_bytes": result["scan"].get("compressed_bytes", 0),
            "decoded_bytes": result["scan"].get("decoded_bytes", 0), "seconds": result["scan"].get("seconds", 0)}


def reanalyze(held, cache, keys):
    """Re-run the analysis of a cached opinions segment from the held raw texts: no download. A record whose text the
    cache lost keeps its earlier result and is counted."""
    n = missing = dropped = 0
    keep = []
    for rec in held["records"]:
        ok, text = analyze.load_text(cache, rec)
        if text is None or not ok:
            missing += 1
            keep.append(rec)
            continue
        orders, _ = analyze.analyze_text(text, keys)
        if not orders:
            dropped += 1  # a rule change (e.g. dash numbers such as 2020-04) no longer finds a register order here
            continue
        rec["orders"], rec["analysis"] = orders, analyze.ANALYSIS_VERSION
        keep.append(rec)
        n += 1
    held["records"] = keep
    return {"reanalyzed_records": n, "reanalysis_text_missing": missing, "reanalysis_records_dropped": dropped}


def cached_plan(cache, key, build):
    """Segment plans are cached so a re-analysis run does not probe the 55 GB file again."""
    p = Path(cache) / "plan" / (bulk.hashlib.sha256(key.encode()).hexdigest()[:20] + ".json")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    plan = build()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(plan), encoding="utf-8")
    return plan


def run_tasks(tasks, workers, g, deadline, label):
    """Run tasks (in order) on `workers` processes, stop submitting at the deadline. Returns (summaries, failures,
    skipped_for_time)."""
    done, failed = [], []
    total = len(tasks)
    log(f"[{label}] {total} segments, {workers} worker(s)")
    if workers <= 1:
        worker_init(g)
        for i, t in enumerate(tasks):
            if time.monotonic() > deadline:
                skipped = total - i
                break
            try:
                done.append(run_task(t))
            except Exception as e:
                failed.append({"kind": t["kind"], "idx": t["idx"], "error": f"{type(e).__name__}: {str(e)[:200]}"})
            log(f"[{label}] {i + 1}/{total} segments")
        return done, failed, total - len(done) - len(failed)
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers, initializer=worker_init, initargs=(g,)) as ex:
        pending, it, n = {}, iter(tasks), 0
        while True:
            while len(pending) < workers and time.monotonic() <= deadline:
                t = next(it, None)
                if t is None:
                    break
                pending[ex.submit(run_task, t)] = t
            if not pending:
                break
            fin, _ = concurrent.futures.wait(pending, return_when=concurrent.futures.FIRST_COMPLETED)
            for f in fin:
                t = pending.pop(f)
                n += 1
                try:
                    done.append(f.result())
                except Exception as e:
                    failed.append({"kind": t["kind"], "idx": t["idx"], "error": f"{type(e).__name__}: {str(e)[:200]}"})
                log(f"[{label}] {n}/{total} segments ({len(failed)} failed)")
    return done, failed, max(0, total - len(done) - len(failed))


# ---- planning -----------------------------------------------------------------------------------------------------

def pick_snapshot(objs_by_table, want):
    """Newest snapshot date present for the opinions table (and every other table, when it has the same date)."""
    def dates(objs, name):
        out = {}
        for k, lm, sz in objs:
            m = re.fullmatch(r"bulk-data/" + re.escape(name) + r"-(\d{4}-\d\d-\d\d)\.csv\.bz2", k)
            if m and sz > 1000:
                out[m.group(1)] = (k, lm, sz)
        return out
    per = {t: dates(objs_by_table[t], TABLES[t]) for t in TABLES}
    if want != "latest":
        date = want
    else:
        date = max(per["opinions"])
    chosen = {}
    for t in TABLES:
        if date in per[t]:
            chosen[t] = per[t][date]
        elif per[t]:
            chosen[t] = per[t][max(per[t])]
        else:
            raise SystemExit(f"no bulk file for {t}")
    return date, chosen


def plan_full(src, level, seg_bytes):
    bounds = bz2seg.block_boundaries(src, seg_bytes, level)
    eos = bz2seg.end_of_stream_bit(src)
    if eos is None:
        raise bulk.BulkError("no end-of-stream marker found at the end of " + src.url)
    segs = []
    for k, sb in enumerate(bounds):
        last = k + 1 == len(bounds)
        segs.append({"start_bit": sb, "end_bit": eos if last else bounds[k + 1], "final": last, "eos": eos})
    return segs


def plan_windows(src, level, k, window_bytes):
    """k evenly spaced windows of the file (smoke): independent segments, each ends at a block start."""
    segs = []
    eos = bz2seg.end_of_stream_bit(src)
    for i in range(k):
        pos = int(src.size * (i + 0.5) / k)
        sb = bz2seg.block_at(src, pos, level)
        eb = bz2seg.block_at(src, pos + window_bytes, level)
        if sb is None or eb is None or eb <= sb:
            continue
        segs.append({"start_bit": sb, "end_bit": eb, "final": False, "eos": eos})
    return segs


def tasks_for(kind, obj, src, level, header, segs, extra=None):
    out = []
    for i, s in enumerate(segs):
        t = {"kind": kind, "idx": i, "url": src.url, "size": src.size, "etag": src.etag, "last_modified": src.last_modified,
             "level": level, "header": header, "compressed_bytes": (s["end_bit"] - s["start_bit"]) // 8, **s}
        if extra:
            t.update(extra)
            if "wanted" in extra:
                # the cached result holds only the wanted ids it was built for: key it by them, or a smaller run's cache
                # would stand in for a larger one (it did, once: the first full run reused the smoke run's cluster rows)
                t["tag"] = "w" + bulk.hashlib.sha256(json.dumps(sorted(extra["wanted"])).encode()).hexdigest()[:12]
        out.append(t)
    return out


# ---- optional routes ----------------------------------------------------------------------------------------------

def cap_probe(pool=None):
    """Harvard's Caselaw Access Project static host is NOT used and is not contacted, not even for its robots file.
    Recorded for the reader: its robots.txt was found to read "User-agent: * / Disallow: /" on 2026-11-06, and its
    federal text is already in CourtListener's opinion rows (xml_harvard). The Hugging Face mirror is an option the owner
    has not decided on; it is not used."""
    return {"host": "static.case.law", "used": False, "contacted_by_this_job": False, "robots": "disallow_all (found 2026-11-06)",
            "reason": "robots.txt disallows every path; CourtListener already carries CAP's text",
            "huggingface_mirror": "option only, awaiting an owner decision; not used"}


class ApiRefused(SystemExit):
    """The CourtListener API answered 401 or 403, or its robots file refused us: with a token present that is a failure
    to report, not a step to skip."""


def robots_unavailable_4xx(pool, url):
    """True only when fetch_pool refused url because the host's robots.txt answered 401 or 403 (disallow_all set, no
    parsed rules), never for an explicit Disallow rule."""
    try:
        origin, _ = pool._origin(url)
        rp = pool.robots.get(origin)
    except (AttributeError, TypeError, ValueError):
        return False
    return bool(rp is not None and getattr(rp, "disallow_all", False) and getattr(rp, "wild", "x") is None)


def api_crosscheck(pool, token, orders, limit, transport, sleep=time.sleep):
    """Token only. Phrase-search counts from CourtListener's search index for a few orders, beside the bulk-scan counts.
    Requests are 13 s apart (the documented default is 5 a minute, 50 an hour, 125 a day). Never prints or returns the
    token. A 401 or 403, a robots refusal, or every request failing raises ApiRefused with the status, so the first live
    use of the token cannot pass silently; a 429 stops the step with the partial result."""
    if not token:
        return {"ran": False, "reason": "COURTLISTENER_TOKEN not set"}
    robots_basis, refusal = "robots.txt allows", None
    try:
        pool.allowed(API_SEARCH)
    except FetchError as err:
        refusal = str(err)
        if robots_unavailable_4xx(pool, API_SEARCH):
            # Owner, 2026-11-09 (A-20261107-courtlistener-robots): a robots file answered with 401/403 is "unavailable"
            # under RFC 9309 section 2.3.1.3, which lets a crawler access the site; and this is CourtListener's documented
            # REST API, called with the owner's own token at its documented rate. Only this API, only on a 4xx robots
            # answer; an explicit Disallow rule, a 5xx or a network failure still blocks, and fetch_pool's default for
            # every other job is unchanged.
            robots_basis = "robots.txt answered 4xx (RFC 9309 unavailable); documented authenticated API, owner ruling"
            log("API cross-check proceeds: " + robots_basis)
            refusal = None
    if refusal is not None:
        # A policy refusal, not a token failure: no request is made. It is recorded where a reader looks (log, SUMMARY,
        # CONTROLS) so the owner can decide; the job's real results are not held back by it. On 2026-11-07 the robots
        # file of www.courtlistener.com answered HTTP 403 (CloudFront) to the runner, which the fetch pool reads as
        # "disallow all".
        log("API CROSS-CHECK NOT RUN: COURTLISTENER_TOKEN is set but the robots check of www.courtlistener.com failed ("
            + refusal[:140] + "); no request was made")
        return {"ran": False, "blocked_by_robots": True, "reason": "robots check of www.courtlistener.com failed",
                "detail": refusal[:140], "token_used": False}
    out, used = [], 0
    for eo, bulk_clusters in orders:
        if used >= limit:
            break
        num = eo.split(":", 1)[1]
        url = API_SEARCH + "?type=o&page_size=1&q=" + f'%22Executive+Order+{num}%22'
        used += 1
        try:
            status, hs, body = transport(url, {"User-Agent": UA, "Authorization": "Token " + token, "Accept": "application/json"}, 60)
            try:
                raw = body.read(2_000_000)
            finally:
                body.close()
        except Exception as e:
            out.append({"eo": eo, "error": type(e).__name__})
            continue
        if status in (401, 403):
            detail = ""
            try:
                detail = str(json.loads(raw).get("detail", ""))[:120]
            except ValueError:
                pass
            raise ApiRefused(f"COURTLISTENER_TOKEN was refused by the CourtListener API: HTTP {status} on the first live use"
                             f" ({detail or 'no detail'}). Check the secret and the account, then re-run.")
        if status == 429:
            out.append({"eo": eo, "error": "HTTP 429 (rate limited); stopped"})
            break
        if status != 200:
            out.append({"eo": eo, "error": f"HTTP {status}"})
            continue
        try:
            d = json.loads(raw)
            count = d.get("count")
            count = count if isinstance(count, int) else None
        except ValueError:
            count = None
        out.append({"eo": eo, "search_index_count": count, "bulk_scan_clusters": bulk_clusters})
        sleep(13)
    ok = [r for r in out if "error" not in r]
    if used and not ok and not any(r.get("error", "").startswith("HTTP 429") for r in out):
        raise ApiRefused("COURTLISTENER_TOKEN is set but every API cross-check request failed: " +
                         "; ".join(sorted({r.get("error", "") for r in out}))[:200])
    return {"ran": True, "requests": used, "answered": len(ok), "counts_present": sum(1 for r in ok if r["search_index_count"] is not None),
            "rows": out, "robots_basis": robots_basis,
            "note": "The search index tokenises numbers and matches phrases loosely; a count is a rough bound, not a recall test."}


def cached_crosscheck(cache, pool, token, orders, limit, transport, sleep=time.sleep):
    """api_crosscheck once per question: a finished answer is kept in the cache and reused, so a re-run spends no API quota.
    A failure (ApiRefused) is never cached."""
    key = bulk.hashlib.sha256(json.dumps([orders, limit, API_SEARCH]).encode()).hexdigest()[:16]
    p = Path(cache) / "api" / f"crosscheck-{key}.json"
    try:
        held = json.loads(p.read_text(encoding="utf-8"))
        held["from_cache"] = True
        return held
    except (OSError, ValueError):
        pass
    res = api_crosscheck(pool, token, orders, limit, transport, sleep=sleep)
    if res.get("ran"):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(res), encoding="utf-8")
    res["from_cache"] = False
    return res


# ---- main ---------------------------------------------------------------------------------------------------------

def main(repo: Path, out: Path, cache: Path, env=os.environ, transport=None):
    t_start = time.monotonic()
    cfg = load_config(env)
    mode = cfg["mode"]
    workers = int(env.get("JOB_WORKERS") or 2)
    budget_min = float(env.get("JOB_TIME_BUDGET_MIN") or 320)
    deadline = t_start + budget_min * 60
    out.mkdir(parents=True, exist_ok=True)
    transport = transport or http_transport
    token = env.get("COURTLISTENER_TOKEN", "")
    stats = {"requests": 0, "failures": 0}
    dates, keys = analyze.load_register(HERE / "data" / "ORDER_DATES.csv")
    log(f"mode={mode} orders in register snapshot: {len(dates)}; workers={workers}; token {'present' if token else 'absent'}")

    # offline controls first: they cost nothing and a failure here means the rules are broken
    cases = controls.fixtures()
    ctl = {"fixtures": controls.locator_and_class_controls(cases, keys), "negatives": controls.negative_controls(keys, dates),
           "structure": controls.structure_controls(keys), "stream": controls.stream_controls(cases, keys)}
    hard = []
    if ctl["fixtures"]["locator"]["recall"] != 1.0:
        hard.append("locator missed a hand-marked citation")
    if ctl["negatives"]["false_hits"]:
        hard.append("negative control produced a registered order")
    if ctl["structure"]["wrong"]:
        hard.append("citation structure control failed")
    if ctl["stream"]["recall"] != 1.0 or ctl["stream"]["false_rows"]:
        hard.append("stream control failed")
    if hard:
        raise SystemExit("controls failed: " + "; ".join(hard))
    log("offline controls passed")

    # routes: robots through the fetch pool, listings, snapshot
    pool = FetchPool(cache / "http", workers=2, per_host=2, transport=transport, user_agent=UA, min_interval=0.2)
    try:
        pool.allowed(bulk.BUCKET + "/bulk-data/")
    except FetchError as e:
        raise SystemExit("bulk host refused by robots.txt: " + str(e))
    objs = {t: bulk.list_objects(transport, "bulk-data/" + TABLES[t] + "-", UA) for t in TABLES}
    date, chosen = pick_snapshot(objs, cfg["snapshot"])
    log("snapshot " + date + ": " + ", ".join(f"{t} {chosen[t][2] / 1e9:.2f} GB" for t in TABLES))
    cap = cap_probe(pool)
    log("second source CAP: not used (robots disallow all)")

    g = {"keys": keys, "cache": str(cache), "transport": None if workers > 1 else transport}
    srcs = {t: bulk.HttpSource(bulk.BUCKET + "/" + chosen[t][0], transport, UA, stats=stats) for t in TABLES}
    bulk_info = {t: {"key": chosen[t][0], "etag": srcs[t].etag, "last_modified": srcs[t].last_modified, "size": srcs[t].size,
                     "date": date} for t in TABLES}
    op_src = srcs["opinions"]
    level = bz2seg.stream_level(op_src)
    seg_bytes = int(float(cfg["seg_mb"]) * MIB)
    pk = f"{op_src.url}|{op_src.etag}|{mode}|{seg_bytes}|{cfg['smoke_windows']}|{cfg['smoke_window_mb']}"
    plan = cached_plan(cache, "opn|" + pk, lambda: {
        "header": bulk.decode_header(op_src, level),
        "segs": (plan_windows(op_src, level, int(cfg["smoke_windows"]), int(cfg["smoke_window_mb"]) * MIB) if mode == "smoke"
                 else plan_full(op_src, level, seg_bytes))})
    op_header, segs = plan["header"], plan["segs"]
    total_compressed = sum((s["end_bit"] - s["start_bit"]) // 8 for s in segs)
    log(f"opinions: {len(segs)} segments, {total_compressed / 1e9:.2f} GB of compressed data to read")
    p1_deadline = deadline - (min(cfg["reserve_minutes"], budget_min * 0.3) * 60 if mode == "full" else 0)
    tasks = tasks_for("opn", None, op_src, level, op_header, segs)
    done, failed, skipped = run_tasks(tasks, workers, g, p1_deadline, "opinions")

    records, unreg, counters, scan_totals = [], Counter(), Counter(), Counter()
    for d in done:
        res = bulk.load_json_gz(Path(d["path"]))
        if res is None:
            failed.append({"kind": "opn", "idx": d["idx"], "error": "result file unreadable"})
            continue
        records.extend(res["records"])
        unreg.update(res["unreg"])
        counters.update(res["counters"])
        for k, v in res["scan"].items():
            if isinstance(v, (int, float)):
                scan_totals[k] += v
    reanalyzed = sum(d.get("reanalyzed_records", 0) for d in done)
    reanalysis_missing = sum(d.get("reanalysis_text_missing", 0) for d in done)
    stats["reanalysis_records_dropped"] = sum(d.get("reanalysis_records_dropped", 0) for d in done)
    stats["reanalyzed_records"], stats["reanalysis_text_missing"] = reanalyzed, reanalysis_missing
    for d in done:
        stats["requests"] += d.get("requests", 0)
        stats["failures"] += d.get("failures", 0)
    log(f"opinions pass: {len(done)} segments done, {len(failed)} failed, {skipped} not started; "
        f"{len(records)} opinions print a register order")
    if tasks and len(failed) * 2 > len(tasks):
        raise SystemExit(f"most segments failed ({len(failed)} of {len(tasks)}): {failed[:3]}")

    # pass 2: cluster, docket, citation and court metadata for the hit clusters only
    wanted_clusters = sorted({r["cid"] for r in records})
    clusters, dockets, citations, courts = {}, {}, defaultdict(list), {}
    failed2 = []
    if wanted_clusters:
        def table_tasks(kind, tname, wanted, seg_mb):
            src = srcs[tname]
            lv = bz2seg.stream_level(src)
            pl = cached_plan(cache, f"{kind}|{src.url}|{src.etag}|{int(seg_mb * MIB)}", lambda: {
                "header": bulk.decode_header(src, lv) if kind != "cit" else None, "segs": plan_full(src, lv, int(seg_mb * MIB))})
            return tasks_for(kind, None, src, lv, pl["header"], pl["segs"], {"wanted": wanted})
        dl2 = deadline
        dn, fl, sk = run_tasks(table_tasks("clu", "clusters", wanted_clusters, float(cfg["seg_mb"])), workers, g, dl2, "clusters")
        failed2 += fl
        for d in dn:
            res = bulk.load_json_gz(Path(d["path"]))
            for k, v in (res or {"store": {}})["store"].items():
                clusters[int(k)] = v
            stats["requests"] += d.get("requests", 0)
            stats["failures"] += d.get("failures", 0)
        wanted_dockets = sorted({c["docket_id"] for c in clusters.values() if c["docket_id"]})
        t2 = table_tasks("dok", "dockets", wanted_dockets, float(cfg["seg_mb"])) + table_tasks("cit", "citations", wanted_clusters, 4096)
        dn, fl, sk2 = run_tasks(t2, workers, g, dl2, "dockets+citations")
        failed2 += fl
        for d in dn:
            res = bulk.load_json_gz(Path(d["path"]))
            store = (res or {"store": {}})["store"]
            if d["kind"] == "dok":
                for k, v in store.items():
                    dockets[int(k)] = v
            else:
                for k, v in store.items():
                    citations[int(k)] = sorted(v, key=lambda x: (x[0] not in (1, 2, 3, 4, 5, 8), x[0]))
            stats["requests"] += d.get("requests", 0)
            stats["failures"] += d.get("failures", 0)
        csrc = srcs["courts"]
        import bz2 as _bz2
        text = _bz2.decompress(csrc.read_range(0, csrc.size - 1)).decode("utf-8", "replace")
        rows = bulk.parse_table(text)
        hdr = rows[0]
        for r in rows[1:]:
            if len(r) == len(hdr):
                d = dict(zip(hdr, r))
                courts[d["id"]] = {"name": d["full_name"] or d["short_name"], "jurisdiction": d["jurisdiction"]}
    citations = {k: ["" if not c[1] else c[1] for c in v] for k, v in citations.items()}

    bstats = Counter()
    rows = analyze.build_rows(records, clusters, dockets, courts, citations, dates, bstats)
    focus = set(cfg.get("focus_orders") or []) if mode == "smoke" else set()
    return finish(repo, out, cache, cfg, mode, date, bulk_info, cap, ctl, records, rows, bstats, unreg, counters, scan_totals,
                  segs, done, failed, failed2, skipped, total_compressed, stats, dates, keys, cases, token, pool, transport,
                  focus, t_start, workers, level)


# ---- outputs ------------------------------------------------------------------------------------------------------

def finish(repo, out, cache, cfg, mode, date, bulk_info, cap, ctl, records, rows, bstats, unreg, counters, scan_totals, segs,
           done, failed, failed2, skipped, total_compressed, stats, dates, keys, cases, token, pool, transport, focus,
           t_start, workers, level):
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if len(records) >= 50:
        lost = bstats["no_cluster_metadata"] / len(records), bstats["no_docket_metadata"] / max(1, len(records))
        if lost[0] > 0.2 or lost[1] > 0.2:
            raise SystemExit(f"pass 2 metadata is missing for most hits: no cluster row for {bstats['no_cluster_metadata']} and no "
                             f"docket row for {bstats['no_docket_metadata']} of {len(records)} opinions (a stale or partial table cache?)")
    out_rows = [r for r in rows if not focus or r["eo"] in focus]
    mcap = int(cfg["mentions_per_order"])
    chosen, omitted, _ = analyze.select_rows(
        out_rows, {**CAPS, "mentions_per_order": mcap,
                   "cost": lambda r, seen: {"hits": EST["hits"], "fragments": EST["fragments"],
                                            "sources": EST["sources"] * sum(1 for o in r["oids"] if o not in seen)}})
    chosen.sort(key=lambda r: (int(re.match(r"EO:(\d+)", r["eo"]).group(1)), r["eo"], analyze.priority(r)))
    hits_buf, frag_buf, src_buf = [analyze.csv_line(analyze.HIT_COLUMNS, dict(zip(analyze.HIT_COLUMNS, analyze.HIT_COLUMNS)))], [], {}
    sizes = {"hits": len(hits_buf[0].encode()), "fragments": 0, "sources": 0}
    written, integrity_bad, text_missing = [], 0, 0
    src_rows = defaultdict(list)
    held_cache = {}
    for r in chosen:
        text, ok = analyze.row_texts(r, cache)
        if text is None:
            text_missing += 1
            omitted["held_text_missing_from_cache"] += 1
            continue
        if not ok:
            integrity_bad += 1
        hit, quote, span, m = analyze.hit_record(r, text, bulk_info["opinions"])
        sid = f"courtlistener:opinion:{r['deciding']['oid']}"
        frag = analyze.fragment_record(r, hit, quote, span, m, sid)
        hl, fl = analyze.csv_line(analyze.HIT_COLUMNS, hit), analyze.jsonl_line(frag)
        new_src = [rec for rec in r["recs"] if rec["oid"] not in held_cache]
        sl = sum(len(analyze.jsonl_line(analyze.source_record(rec, [r], bulk_info["opinions"], now)).encode()) for rec in new_src)
        if (sizes["hits"] + len(hl.encode()) > CAPS["hits"] or sizes["fragments"] + len(fl.encode()) > CAPS["fragments"]
                or sizes["sources"] + sl > CAPS["sources"]):
            omitted["byte_budget_at_write"] += 1
            continue
        sizes["hits"] += len(hl.encode())
        sizes["fragments"] += len(fl.encode())
        sizes["sources"] += sl
        hits_buf.append(hl)
        frag_buf.append(fl)
        for rec in r["recs"]:
            held_cache.setdefault(rec["oid"], rec)
        for rec in r["recs"]:
            src_rows[rec["oid"]].append(r)
        written.append(r)
    for oid, rs in sorted(src_rows.items()):
        src_buf[oid] = analyze.jsonl_line(analyze.source_record(held_cache[oid], rs, bulk_info["opinions"], now))
    (out / "COURT_HITS.csv").write_text("".join(hits_buf), encoding="utf-8", newline="")
    (out / "FRAGMENTS.jsonl").write_text("".join(frag_buf), encoding="utf-8", newline="")
    (out / "SOURCES.jsonl").write_text("".join(src_buf[k] for k in sorted(src_buf)), encoding="utf-8", newline="")

    # per-order tally of every court hit found (committed or not)
    tally = {}
    for r in out_rows:
        t = tally.setdefault(r["eo"], Counter())
        t["clusters"] += 1
        t["federal_signal"] += 1 if r["fed"] else 0
        t[r["class"]] += 1
        t["level" + str(r["level"])] += 1
    committed = Counter(r["eo"] for r in written)
    dates_by = defaultdict(list)
    for r in out_rows:
        if r["date"]:
            dates_by[r["eo"]].append(r["date"])
    tcols = ["eo", "order_date", "clusters", "federal_signal", "enjoined_vacated_invalidated", "upheld", "interpreted",
             "mentioned", "scotus", "appellate", "district", "other", "first_decision", "last_decision", "committed_hits"]
    lines = [",".join(tcols) + "\n"]
    for eo in sorted(tally, key=lambda e: (int(re.match(r"EO:(\d+)", e).group(1)), e)):
        t = tally[eo]
        ds = sorted(dates_by[eo])
        lines.append(analyze.csv_line(tcols, {
            "eo": eo, "order_date": dates.get(eo, ""), "clusters": t["clusters"], "federal_signal": t["federal_signal"],
            "enjoined_vacated_invalidated": t["enjoined_vacated_invalidated"], "upheld": t["upheld"],
            "interpreted": t["interpreted"], "mentioned": t["mentioned"], "scotus": t["level0"], "appellate": t["level1"],
            "district": t["level2"], "other": t["level3"], "first_decision": ds[0] if ds else "",
            "last_decision": ds[-1] if ds else "", "committed_hits": committed[eo]}))
    (out / "ORDER_TALLY.csv").write_text("".join(lines), encoding="utf-8", newline="")

    # controls that need the real hits
    complete = mode == "full" and not failed and not failed2 and not skipped
    if mode == "full":
        ctl["bulk_stream_recall"] = {"rows": controls.stream_recall_in_hits(cases, rows), "complete_run": complete,
                                     "note": "A planted opinion missing here with complete_run true means the bulk scan missed it."}
    else:
        ctl["bulk_stream_recall"] = {"rows": [], "complete_run": False,
                                     "note": "Smoke reads six windows of the file; the planted opinions are not expected in them. "
                                             "Run mode full to test the scan against the real opinions."}
    # the planted opinions' orders first, then the orders with the most bulk hits
    asked = []
    for e in [eo for c in cases for eo in c["expected_pair_class"]] + sorted(tally, key=lambda e: -tally[e]["clusters"]):
        if e not in [a for a, _ in asked]:
            asked.append((e, tally[e]["clusters"] if e in tally else 0))
    ctl["api_crosscheck"] = (cached_crosscheck(cache, pool, token, asked[:int(cfg["api_requests"])], int(cfg["api_requests"]), transport)
                             if token else {"ran": False, "reason": "COURTLISTENER_TOKEN not set"})
    ctl["opinion_level"] = controls.opinion_controls()
    ctl["measured_error_rate"] = {
        "locator_recall_on_hand_marked_citations": ctl["fixtures"]["locator"]["recall"],
        "mention_class_error_rate_vs_hand_labels": ctl["fixtures"]["mention_class"]["error_rate"],
        "opinion_class_agreement_sentence_level": f"{ctl['fixtures']['opinion_class']['agree']} of {ctl['fixtures']['opinion_class']['planted_positives']}",
        "opinion_level_planted_before_after": ctl["opinion_level"]["summary"]["planted"],
        "opinion_level_held_out_before_after": ctl["opinion_level"]["summary"]["held_out"],
        "false_hit_rate_on_negatives": ctl["negatives"]["false_hit_rate"],
        "stream_control_recall": ctl["stream"]["recall"]}
    ctl["generated_utc"] = now
    (out / "CONTROLS.json").write_text(json.dumps(ctl, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    class_counts = Counter(r["class"] for r in out_rows)
    fed_counts = Counter(r["class"] for r in out_rows if r["fed"])
    elapsed = time.monotonic() - t_start
    cbytes = scan_totals.get("compressed_bytes", 0)
    sec_decode = scan_totals.get("seconds", 0) or 1
    rate = cbytes / sec_decode if cbytes else 0
    full_hours = None
    if mode == "smoke" and rate:
        full_hours = round(bulk_info["opinions"]["size"] / rate / max(1, workers) / 3600, 2)
    summary = {
        "job": "youngstown-courts", "generated_utc": now, "mode": mode, "complete": complete,
        "bulk_snapshot": date, "bulk": bulk_info, "workers": workers,
        "opinions_segments_planned": len(segs), "opinions_segments_done": len(done), "opinions_segments_failed": len(failed),
        "opinions_segments_not_started": skipped,
        "opinions_segments_from_cache": sum(1 for d in done if d.get("cached")), "compressed_bytes_read": cbytes,
        "compressed_bytes_planned": total_compressed,
        "fraction_of_opinions_file_read": round(total_compressed / bulk_info["opinions"]["size"], 4),
        "decoded_bytes": scan_totals.get("decoded_bytes", 0), "rows_with_candidate_text": scan_totals.get("rows_selected", 0),
        "rows_parsed": counters.get("rows_parsed", 0), "rows_unparsed": counters.get("rows_unparsed", 0),
        "row_start_lost": scan_totals.get("row_start_lost", 0), "rows_unterminated": scan_totals.get("rows_unterminated", 0),
        "opinions_printing_a_register_order": len(records), "order_clusters_found": len(rows),
        "order_clusters_in_scope": len(out_rows), "focus_orders": sorted(focus),
        "clusters_by_class": dict(class_counts), "clusters_by_class_with_federal_signal": dict(fed_counts),
        "orders_with_a_hit": len({r["eo"] for r in out_rows}),
        "dropped": dict(bstats), "unregistered_numbers_cited_top": dict(unreg.most_common(25)),
        "unregistered_number_mentions": sum(unreg.values()),
        "committed": {"court_hits": len(written), "opinions_held": len(src_buf), "bytes": sizes},
        "omitted": dict(omitted), "integrity_failures_raw_vs_recorded_sha": integrity_bad,
        "held_text_missing_from_cache": text_missing,
        "analysis_version": analyze.ANALYSIS_VERSION,
        "reanalyzed_records_from_cache": stats.get("reanalyzed_records", 0),
        "reanalysis_text_missing": stats.get("reanalysis_text_missing", 0),
        "reanalysis_records_dropped": stats.get("reanalysis_records_dropped", 0),
        "clusters_by_opinion_class": dict(Counter(r["op_class"] for r in out_rows)),
        "clusters_by_effective_class": dict(Counter(r["eff_class"] for r in out_rows)),
        "clusters_with_conflicting_cues": sum(1 for r in out_rows if r["deciding"]["orders"][r["eo"]].get("op", {}).get("conflict")),
        "requests": stats["requests"], "request_failures": stats["failures"],
        "failed_segments": failed[:10] + failed2[:10],
        "seconds": round(elapsed), "projected_full_run_hours_on_this_machine_class": full_hours,
        "second_source": cap,
        "token": "COURTLISTENER_TOKEN present" if token else "COURTLISTENER_TOKEN absent (not needed for the bulk scan)",
        "limits": "Leads only. A rule class is words in one sentence, not what a court held. No status, census, codebook or "
                  "count change. Certified: 0.",
    }
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "FAILURES.jsonl").write_text("".join(analyze.jsonl_line(f) for f in failed + failed2), encoding="utf-8")

    # budget
    files = {p.name: p.stat().st_size for p in sorted(out.iterdir()) if p.is_file()}
    total = sum(files.values())
    budget = {"files": files, "total_bytes": total, "total_cap": TOTAL_CAP, "per_file_cap": FILE_CAP,
              "over_per_file_cap": [n for n, s in files.items() if s > FILE_CAP], "within_budget": total <= TOTAL_CAP and
              all(s <= FILE_CAP for s in files.values()), "omitted_for_bytes": {k: v for k, v in omitted.items() if "byte" in k}}
    (out / "BUDGET.json").write_text(json.dumps(budget, indent=1) + "\n", encoding="utf-8")
    log(json.dumps({k: summary[k] for k in ("mode", "complete", "opinions_segments_done", "opinions_printing_a_register_order",
                                           "order_clusters_found", "clusters_by_class", "requests", "request_failures", "seconds")}))
    if not budget["within_budget"]:
        raise SystemExit("BUDGET exceeded: " + json.dumps(budget["over_per_file_cap"]))
    if stats["requests"] >= 10 and stats["failures"] * 2 > stats["requests"]:
        raise SystemExit(f"most requests failed ({stats['failures']} of {stats['requests']})")
    if not done:
        raise SystemExit("no opinions segment was read")
    return summary
