"""Herschel, step 3: project the deep sample's measurements onto every open order-step in the census.

What it reads (all committed or regenerable):
  frame/ORDERS.csv, frame/CELLS.csv          the census (census.py)
  frame/ASSIGNMENTS.json, ASSIGNMENTS_R2.json which order went to which coordinator, in which round
  H*/TRACE.jsonl                             one line per worker: step, model, orders, times, outcomes, limits
  H*/ORDER_OUTCOMES.csv                      one row per order and step (preferred over TRACE outcomes)
  H*/telemetry/AGENT_USAGE.csv               per-session tokens written by jobs/bentham/sessions.py
  telemetry/COORDINATORS.csv                 the coordinators' own tokens (sessions.py over the integrator session)
  H*/CERTIFICATION_READING*.json|csv         minutes a careful reader needed per dossier (H3 micro-sample)

How it projects:
  Each sampled order stands for N_h / n_h orders of its stratum (N_h orders in the census, n_h sampled orders that
  a coordinator reached; both rounds pooled). Totals are stratified Horvitz-Thompson estimates. A worker's cost is
  split equally over its orders. A coordinator's own cost is spread over its orders in proportion to their worker
  cost and reported separately. Tokens are priced with jobs/bentham/measure.py (API list prices, one cache-write
  price), so totals are API-equivalent dollars, not invoices.
  Uncertainty: a stratified bootstrap over reached orders (80% interval), and the gap between round 1 and round 2
  estimates (interpenetrating subsamples). A stratum with no reached order borrows the pooled mean of its status
  group and is flagged.

Writes ATLAS/: PROJECTION.json, BY_STEP.csv, BY_STRATUM.csv, ACQUISITIONS.csv, CONCURRENCY.csv, ORDERS_MEASURED.csv.
Run: python3 -I research/herschel/project.py [--boot 2000]
"""
from __future__ import annotations

import argparse
import collections
import csv
import glob
import json
import random
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
FRAME = HERE / "frame"
OUT = HERE / "ATLAS"
sys.path.insert(0, str(REPO / "jobs/bentham"))
csv.field_size_limit(10**9)
import measure as M  # noqa: E402

GOOD = {"done", "upheld"}
STEPS = ["admit", "provisional_status", "original_text", "replace_original", "clause_inventory",
         "ending_or_current_basis", "savings_residuals", "counterevidence", "shared_sources", "opus_media", "review"]


def read_csv(path):
    if not Path(path).is_file():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ts(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


def family(model):
    m = (model or "").lower()
    return "opus" if "opus" in m else "sonnet" if "sonnet" in m else "haiku" if "haiku" in m else "opus"


def row_usd(r):
    def n(k):
        try:
            return float(r.get(k) or 0)
        except ValueError:
            return 0.0
    tok = {"fresh_input": n("fresh_input"), "cache_read": n("cache_read"), "output": n("output"),
           "cache_write": n("cache_write_5m") + n("cache_write_1h") + n("cache_write_unclassified")}
    fam = family(r.get("model"))
    prices = M.PRICE_TABLE if fam in M.PRICE_TABLE else {**M.PRICE_TABLE, fam: M.PRICE_TABLE["sonnet"]}
    return M.usd(fam, tok, prices)


def norm_outcome(o):
    o = (o or "").strip()
    if not o:
        return "not_reached"
    head = o.split(":", 1)[0].strip().lower()
    return head if head in {"done", "blocked", "failed", "upheld", "rejected", "not_reached"} else "failed"


def acquisition(o):
    o = o or ""
    return o.split(":", 1)[1].strip() if o.lower().startswith("blocked:") else ""


def load():
    orders = {r["instrument_id"]: r for r in read_csv(FRAME / "ORDERS.csv")}
    assigned = {}
    for fname, rnd in (("ASSIGNMENTS.json", 1), ("ASSIGNMENTS_R2.json", 2)):
        p = FRAME / fname
        if p.is_file():
            for c in json.loads(p.read_text())["coordinators"]:
                for iid in c["orders"]:
                    assigned[iid] = {"coordinator": c["name"], "round": rnd, "concurrency": c["concurrency"]}
    workers, outcomes, usage, limits = [], {}, {}, []
    for hdir in sorted(glob.glob(str(HERE / "H[0-9]*"))):
        h = Path(hdir).name
        for r in read_csv(Path(hdir) / "telemetry/AGENT_USAGE.csv"):
            usage.setdefault(h, []).append(r)
        tp = Path(hdir) / "TRACE.jsonl"
        if tp.is_file():
            for line in tp.read_text(encoding="utf-8").splitlines():
                try:
                    t = json.loads(line)
                except ValueError:
                    continue
                t["_h"] = h
                workers.append(t)
                for ev in t.get("limit_events") or []:
                    limits.append({"coordinator": h, "worker": t.get("worker"), "event": ev})
        for r in read_csv(Path(hdir) / "ORDER_OUTCOMES.csv"):
            outcomes[(r["instrument_id"], r["step"])] = {"outcome": r.get("outcome", ""), "worker": r.get("worker", "")}
    return orders, assigned, workers, outcomes, usage, limits


COORDINATOR_IDS = set()   # filled from telemetry/PHASE_MAP.json: the coordinators' own agent ids


def is_coordination(r):
    return r.get("phase") == "coordination" or r.get("agent_id") in COORDINATOR_IDS


def match_workers(workers, usage):
    """Price every worker. Order of preference: a cost the trace records; a telemetry row whose phase or batch names
    the worker or whose session the trace names; the unused telemetry row of the same coordinator whose phase is the
    worker's step and whose start is nearest the worker's start (within 15 minutes). Workers still unmatched share
    equally whatever telemetry of their step and coordinator stayed unmatched."""
    used = set()
    costs = {}
    for i, t in enumerate(workers):
        for k in ("usd", "cost_usd", "total_cost_usd"):
            if isinstance(t.get(k), (int, float)):
                costs[i] = (float(t[k]), "trace")
                break
    for i, t in enumerate(workers):
        if i in costs:
            continue
        rows = usage.get(t["_h"], [])
        name = t.get("worker") or ""
        sids = set(t.get("session_ids") or ([t["session_id"]] if t.get("session_id") else []))
        hit = [j for j, r in enumerate(rows) if not is_coordination(r) and (
            r.get("phase") == name or r.get("batch") == name or r.get("agent_id") == name
            or any(s and (r.get("session_id") or "").startswith(s) for s in sids))]
        if hit:
            costs[i] = (sum(row_usd(rows[j]) for j in hit), "telemetry")
            used.update((t["_h"], j) for j in hit)
    for i, t in sorted(((i, t) for i, t in enumerate(workers) if i not in costs),
                       key=lambda it: str(it[1].get("started_utc"))):
        rows = usage.get(t["_h"], [])
        st = ts(t.get("started_utc"))
        best, gap = None, 900.0
        for j, r in enumerate(rows):
            if (t["_h"], j) in used or is_coordination(r) or r.get("phase") != t.get("step"):
                continue
            rs = ts(r.get("started_utc"))
            if st and rs and abs((rs - st).total_seconds()) < gap:
                best, gap = j, abs((rs - st).total_seconds())
        if best is not None:
            costs[i] = (row_usd(rows[best]), "telemetry-time")
            used.add((t["_h"], best))
    pools = collections.defaultdict(float)
    for h, rows in usage.items():
        for j, r in enumerate(rows):
            if (h, j) not in used and not is_coordination(r):
                pools[(h, r.get("phase"))] += row_usd(r)
    waiting = collections.defaultdict(list)
    for i, t in enumerate(workers):
        if i not in costs:
            waiting[(t["_h"], t.get("step"))].append(i)
    leftover = 0.0
    for key, v in pools.items():
        if waiting.get(key):
            for i in waiting[key]:
                costs[i] = (v / len(waiting[key]), "telemetry-pool")
        else:
            leftover += v
    return costs, leftover


def coordinator_costs(usage):
    """Coordinator cost per coordinator: its own telemetry if it wrote any, else the integrator's measurement."""
    out = {}
    for h, rows in usage.items():
        c = [r for r in rows if is_coordination(r)]
        if c:
            out[h] = sum(row_usd(r) for r in c)
    for r in read_csv(HERE / "telemetry/COORDINATORS.csv"):
        h = r.get("phase", "")
        if h.startswith("H") and h not in out:
            out[h] = out.get(h + "*", 0.0) + row_usd(r)
        elif not h.startswith("H"):
            out[h] = out.get(h, 0.0) + row_usd(r)
    return out


def build_measured(orders, assigned, workers, outcomes, usage):
    per = collections.defaultdict(lambda: {"steps": collections.defaultdict(lambda: {"usd": 0.0, "seconds": 0.0,
                                                                                     "outcome": ""}),
                                           "worker_usd": 0.0})
    costs, leftover = match_workers(workers, usage)
    unpriced = 0
    for i, t in enumerate(workers):
        usd, _src = costs.get(i, (None, "unpriced"))
        if usd is None:
            unpriced += 1
            usd = 0.0
        ids = [i for i in (t.get("orders") or [])]
        if not ids:
            continue
        a, b = ts(t.get("started_utc")), ts(t.get("ended_utc"))
        secs = (b - a).total_seconds() if a and b else 0.0
        step = t.get("step") or "unknown"
        for iid in ids:
            rec = per[iid]["steps"][step]
            rec["usd"] += usd / len(ids)
            rec["seconds"] += secs / len(ids)
            o = (t.get("outcomes") or {}).get(iid, "")
            if o:
                rec["outcome"] = o
            per[iid]["worker_usd"] += usd / len(ids)
    for (iid, step), o in outcomes.items():
        per[iid]["steps"][step]["outcome"] = o["outcome"]
    coord = coordinator_costs(usage)
    by_h_worker = collections.defaultdict(float)
    for iid, a in assigned.items():
        by_h_worker[a["coordinator"]] += per[iid]["worker_usd"] if iid in per else 0.0
    rows = []
    for iid, a in assigned.items():
        o = orders.get(iid, {})
        p = per.get(iid)
        steps = p["steps"] if p else {}
        open_steps = [s for s in (o.get("open_steps") or "").split("|") if s]
        outs = {s: steps[s]["outcome"] for s in steps}
        reached = any(norm_outcome(v) != "not_reached" for v in outs.values())
        wu = p["worker_usd"] if p else 0.0
        hw = by_h_worker[a["coordinator"]]
        overhead = coord.get(a["coordinator"], 0.0) * (wu / hw) if hw else 0.0
        all_good = bool(open_steps) and all(norm_outcome(outs.get(s)) in GOOD for s in open_steps) and \
            norm_outcome(outs.get("review", "upheld")) in GOOD | {"not_reached"}
        rows.append({"instrument_id": iid, "stratum": o.get("stratum", ""), "round": a["round"],
                     "coordinator": a["coordinator"], "reached": reached, "open_steps": open_steps,
                     "steps": {s: dict(v) for s, v in steps.items()}, "worker_usd": wu, "overhead_usd": overhead,
                     "usd": wu + overhead, "seconds": sum(v["seconds"] for v in steps.values()),
                     "all_steps_good": all_good})
    coord["unattributed_worker_telemetry"] = leftover
    return rows, coord, unpriced


def stratum_status(h):
    return h.split(".", 1)[0]


OPEN_ALIASES = {"lifecycle_claim": ["clause_inventory", "ending_or_current_basis", "savings_residuals",
                                     "counterevidence"]}


def eligible_for(step):
    """Rows that measure `step`: reached, and either the step was not open (it costs nothing) or it was attempted.
    A step left not_reached inside a reached order is unmeasured, not free."""
    def ok(r):
        if not r["reached"]:
            return False
        if step == "review":
            return "review" in r["steps"] and norm_outcome(r["steps"]["review"].get("outcome")) != "not_reached" \
                or not any(norm_outcome(r["steps"].get(s, {}).get("outcome")) == "not_reached" for s in r["open_steps"])
        if step in r["steps"]:
            return norm_outcome(r["steps"][step].get("outcome")) != "not_reached"
        return not set(OPEN_ALIASES.get(step, [step])) & set(r["open_steps"])
    return ok


def estimate(rows, N, keyfn, eligible=None):
    """Stratified Horvitz-Thompson total of keyfn(row) over the census. Returns (total, borrowed strata)."""
    eligible = eligible or (lambda r: r["reached"])
    by = collections.defaultdict(list)
    for r in rows:
        if eligible(r):
            by[r["stratum"]].append(keyfn(r))
    pooled = collections.defaultdict(list)
    for h, v in by.items():
        pooled[stratum_status(h)] += v
    total, borrowed = 0.0, []
    for h, n_pop in N.items():
        v = by.get(h)
        if not v:
            v = pooled.get(stratum_status(h)) or [x for vs in by.values() for x in vs]
            borrowed.append(h)
        if v:
            total += n_pop * sum(v) / len(v)
    return total, borrowed


def resample(rows, rng):
    """One stratified bootstrap replicate: reached orders resampled with replacement within each stratum."""
    by = collections.defaultdict(list)
    for r in rows:
        if r["reached"]:
            by[r["stratum"]].append(r)
    return [rng.choice(v) for v in by.values() for _ in v]


def interval(rows, fn, boots, seed=1785):
    """Point, 80% bootstrap interval, and the round-1-only and round-2-only estimates of fn(rows)."""
    rng = random.Random(seed)
    reps = sorted(fn(resample(rows, rng)) for _ in range(boots)) if boots else []
    r2rows = [r for r in rows if r["round"] == 2]
    return {"point": round(fn(rows), 2),
            "p10": round(reps[int(0.1 * len(reps))], 2) if reps else None,
            "p90": round(reps[max(0, int(0.9 * len(reps)) - 1)], 2) if reps else None,
            "round1": round(fn([r for r in rows if r["round"] == 1]), 2),
            "round2": round(fn(r2rows), 2) if any(r["reached"] for r in r2rows) else None}


def concurrency(workers):
    """Global concurrency timeline across all coordinators and per-worker duration at each level."""
    spans = [(ts(t.get("started_utc")), ts(t.get("ended_utc")), t) for t in workers]
    spans = [s for s in spans if s[0] and s[1] and s[1] >= s[0]]
    rows = []
    for a, b, t in spans:
        live = sum(1 for a2, b2, _ in spans if a2 <= a < b2)
        n = max(1, len(t.get("orders") or []))
        rows.append({"worker": t.get("worker"), "coordinator": t["_h"], "step": t.get("step"),
                     "model": t.get("model"), "global_concurrency_at_start": live,
                     "own_concurrency_at_start": t.get("concurrent_workers_at_start"),
                     "seconds": round((b - a).total_seconds(), 1),
                     "seconds_per_order": round((b - a).total_seconds() / n, 1),
                     "limit_events": len(t.get("limit_events") or [])})
    peak = 0
    if spans:
        events = sorted([(a, 1) for a, _, _ in spans] + [(b, -1) for _, b, _ in spans])
        cur = 0
        for _, d in events:
            cur += d
            peak = max(peak, cur)
    return rows, peak, (min(s[0] for s in spans), max(s[1] for s in spans)) if spans else (None, None)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--root", help="folder holding frame/ and H*/ (default: this folder); for tests")
    args = ap.parse_args(argv)
    global HERE, FRAME, OUT
    if args.root:
        HERE = Path(args.root).resolve()
        FRAME, OUT = HERE / "frame", HERE / "ATLAS"
    pm = HERE / "telemetry/PHASE_MAP.json"
    if pm.is_file():
        COORDINATOR_IDS.update(k for k, v in json.loads(pm.read_text()).items() if v.startswith("H"))
    orders, assigned, workers, outcomes, usage, limits = load()
    rows, coord, unpriced = build_measured(orders, assigned, workers, outcomes, usage)
    deep_strata = {o["stratum"] for o in orders.values() if o["stratum"] != "ready"}
    N = collections.Counter(o["stratum"] for o in orders.values() if o["stratum"] in deep_strata)
    cells = collections.Counter()
    for c in read_csv(FRAME / "CELLS.csv"):
        cells[(c["stratum"], c["step"])] += int(c["count"] or 1)
    OUT.mkdir(exist_ok=True)

    steps_seen = sorted({s for r in rows for s in r["steps"]} | {s for r in rows for s in r["open_steps"]},
                        key=lambda s: STEPS.index(s) if s in STEPS else 99)
    def step_key(s, field):
        return lambda r: r["steps"].get(s, {}).get(field, 0.0)

    def outcome_is(s, test):
        return lambda r: 1.0 if test(norm_outcome(r["steps"].get(s, {}).get("outcome"))) else 0.0

    def total(field, extra=None):
        def fn(rs):
            t = sum(estimate(rs, N, step_key(s, field), eligible_for(s))[0] for s in steps_seen)
            return t + (estimate(rs, N, extra)[0] if extra else 0.0)
        return fn
    proj = {"usd_total": interval(rows, total("usd", lambda r: r["overhead_usd"]), args.boot),
            "usd_workers": interval(rows, total("usd"), args.boot),
            "usd_coordination": interval(rows, lambda rs: estimate(rs, N, lambda r: r["overhead_usd"])[0], args.boot),
            "worker_hours": interval(rows, lambda rs: total("seconds")(rs) / 3600, args.boot),
            "orders_all_steps_good": interval(
                rows, lambda rs: estimate(rs, N, lambda r: 1.0 if r["all_steps_good"] else 0.0,
                                          lambda r: r["reached"] and not any(
                                              norm_outcome(r["steps"].get(s, {}).get("outcome")) == "not_reached"
                                              for s in r["open_steps"]))[0], args.boot),
            "borrowed_strata": sorted(estimate(rows, N, lambda r: 0.0)[1])}
    by_step = []
    for s in steps_seen:
        el = eligible_for(s)
        c = interval(rows, lambda rs, s=s, el=el: estimate(rs, N, step_key(s, "usd"), el)[0], args.boot)
        g = estimate(rows, N, outcome_is(s, lambda o: o in GOOD), el)[0]
        tr = estimate(rows, N, outcome_is(s, lambda o: o != "not_reached"), el)[0]
        bl = estimate(rows, N, outcome_is(s, lambda o: o == "blocked"), el)[0]
        fl = estimate(rows, N, outcome_is(s, lambda o: o in {"failed", "rejected"}), el)[0]
        measured = sum(1 for r in rows if el(r) and s in r["steps"])
        mins = [r["steps"][s]["seconds"] / 60 for r in rows if el(r) and s in r["steps"]]
        by_step.append({"step": s, "census_cells": sum(v for (h, st), v in cells.items() if st == s),
                        "orders_measured": measured, "usd_point": c["point"], "usd_p10": c["p10"],
                        "usd_p90": c["p90"], "usd_round1": c["round1"], "usd_round2": c["round2"],
                        "projected_attempts": round(tr), "projected_good": round(g), "projected_blocked": round(bl),
                        "projected_failed_or_rejected": round(fl),
                        "good_rate": round(g / tr, 3) if tr else None,
                        "usd_per_attempt": round(c["point"] / tr, 3) if tr else None,
                        "worker_minutes_per_order": round(sum(mins) / len(mins), 1) if mins else None})
    by_stratum = []
    for h in sorted(N):
        rs = [r for r in rows if r["stratum"] == h]
        rr = [r for r in rs if r["reached"]]
        by_stratum.append({"stratum": h, "census_orders": N[h], "sampled": len(rs), "reached": len(rr),
                           "mean_usd_per_order": round(sum(r["usd"] for r in rr) / len(rr), 3) if rr else None,
                           "mean_worker_minutes_per_order": round(sum(r["seconds"] for r in rr) / len(rr) / 60, 1)
                           if rr else None,
                           "share_all_steps_good": round(sum(r["all_steps_good"] for r in rr) / len(rr), 3)
                           if rr else None,
                           "projected_usd": round(N[h] * sum(r["usd"] for r in rr) / len(rr), 0) if rr else None})
    acq = collections.defaultdict(lambda: collections.Counter())
    for r in rows:
        if not r["reached"]:
            continue
        for s, v in r["steps"].items():
            a = acquisition(v.get("outcome"))
            if a:
                acq[re.sub(r"\s+", " ", a.lower())[:160]][r["stratum"]] += 1
    reached_n = collections.Counter(r["stratum"] for r in rows if r["reached"])
    acq_rows = sorted(({"acquisition": a, "sampled_orders": sum(c.values()),
                        "projected_orders": round(sum(N[h] * k / reached_n[h] for h, k in c.items() if reached_n[h])),
                        "strata": "|".join(sorted(c))} for a, c in acq.items()),
                      key=lambda x: -x["projected_orders"])
    conc_rows, peak, (t0, t1) = concurrency(workers)
    # Wall time at a given concurrency: projected worker-hours / k, inflated by the slowdown seen at that level.
    base = [r["seconds_per_order"] for r in conc_rows if r["global_concurrency_at_start"] <= 8]
    wall = {}
    wh = proj["worker_hours"]["point"]
    for k in (4, 8, 16, 32, 64):
        near = [r["seconds_per_order"] for r in conc_rows if abs(r["global_concurrency_at_start"] - k) <= k / 4]
        infl = (sum(near) / len(near)) / (sum(base) / len(base)) if near and base else None
        wall[str(k)] = {"days": round(wh / k / 24 * (infl or 1), 1), "slowdown_measured": None if infl is None
                        else round(infl, 2), "basis": "measured" if near else "extrapolated, no workers at this level"}
    cert = []
    for p in glob.glob(str(HERE / "H*/CERT*READING*")):
        if p.endswith(".jsonl"):
            for line in Path(p).read_text(encoding="utf-8").splitlines():
                try:
                    cert.append(json.loads(line))
                except ValueError:
                    pass
        elif p.endswith(".json"):
            try:
                d = json.loads(Path(p).read_text())
                cert += d if isinstance(d, list) else d.get("orders", [])
            except ValueError:
                pass
        elif p.endswith(".csv"):
            cert += read_csv(p)
    def mfield(c):
        return c.get("est_human_minutes") or c.get("minutes") or c.get("reading_minutes")
    mins = [float(mfield(c)) for c in cert if mfield(c)]
    allowance = None
    ap_ = REPO / "jobs/bentham/data/ALLOWANCE.json"
    if ap_.is_file():
        allowance = json.loads(ap_.read_text())
    summary = {"generated_by": "research/herschel/project.py", "price_table": M.PRICE_TABLE,
               "census_orders_open": sum(N.values()), "sampled_orders": len(rows),
               "reached_orders": sum(r["reached"] for r in rows), "workers": len(workers),
               "workers_unpriced": unpriced, "coordinator_usd": {k: round(v, 2) for k, v in coord.items()},
               "measured_usd": round(sum(r["usd"] for r in rows), 2),
               "peak_global_concurrency": peak, "run_window": [str(t0), str(t1)], "limit_events": limits,
               "projection": proj, "wall_clock_days_at_concurrency": wall,
               "human_certification": {"dossiers_read": len(mins),
                                       "mean_minutes": round(sum(mins) / len(mins), 1) if mins else None,
                                       "projected_hours_all_orders": round(len(orders) * sum(mins) / len(mins) / 60)
                                       if mins else None},
               "allowance": allowance,
               "notes": ["API-equivalent dollars at list prices, one cache-write price (Bentham's convention).",
                         "Orders not reached are treated as missing at random within their stratum.",
                         "A worker's cost is split equally across its orders.",
                         "Ready orders (1,331) are excluded from token projection; they need human certification."]}
    (OUT / "PROJECTION.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    for name, data in (("BY_STEP.csv", by_step), ("BY_STRATUM.csv", by_stratum), ("ACQUISITIONS.csv", acq_rows),
                       ("CONCURRENCY.csv", conc_rows)):
        if data:
            with open(OUT / name, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(data[0]))
                w.writeheader()
                w.writerows(data)
    with open(OUT / "ORDERS_MEASURED.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["instrument_id", "stratum", "round", "coordinator", "reached", "step", "outcome", "usd", "seconds"])
        for r in rows:
            for s in sorted(set(r["open_steps"]) | set(r["steps"])):
                v = r["steps"].get(s, {})
                w.writerow([r["instrument_id"], r["stratum"], r["round"], r["coordinator"], r["reached"], s,
                            v.get("outcome", "not_reached"), round(v.get("usd", 0.0), 4), round(v.get("seconds", 0.0))])
    print(json.dumps({k: summary[k] for k in ("sampled_orders", "reached_orders", "workers", "workers_unpriced",
                                              "measured_usd", "peak_global_concurrency")}, indent=2))
    print(json.dumps(proj, indent=2))


if __name__ == "__main__":
    main()
