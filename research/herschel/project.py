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
    if head in {"done", "blocked", "failed", "upheld", "rejected", "not_reached"}:
        return head
    low = o.lower()
    if low.startswith(("not_applicable", "n/a", "not applicable")):
        return "not_applicable"
    if low.startswith("control_caught"):   # the planted control was caught; the verdict on the genuine item follows
        return "upheld" if "upheld" in low else "rejected" if "reject" in low else "done"
    return "failed"


def acquisition(o):
    o = o or ""
    return o.split(":", 1)[1].strip() if o.lower().startswith("blocked:") else ""


COST_GROUP = {s: "lifecycle_steps" for s in ("clause_inventory", "ending_or_current_basis", "savings_residuals",
                                              "counterevidence", "lifecycle", "lifecycle_claim")}
COST_GROUP.update({"review": "review", "review_status": "review", "review_text": "review", "review_lifecycle": "review",
                   "reveal": "review"})
GROUP_ORDER = ["admit", "provisional_status", "original_text", "replace_original", "lifecycle_steps", "shared_sources",
               "opus_media", "review"]
REVIEW_KIND = {"review": "review_claim", "review_lifecycle": "review_claim", "reveal": "review_claim",
               "review_status": "review_status", "review_text": "review_text"}
BLOCKER_LABELS = {
    "status_history": "no dated status-history record (claim kit refuses to start the order)",
    "status_adoption": "waits for a reviewed status proposal and owner adoption",
    "later_search": "no bounded machine search for later sources (undecided dossiers)",
    "tool_rule": "a claim-kit write rule blocks assembly",
    "raw_bytes": "source held only as a hash or custody record; bytes must be retained",
    "official_original": "official printing or page image of the order not held",
    "agency_records": "agency execution records (appointments, land status, board reports) not held",
    "legal_sources": "later law, notice or instrument needed for the ending or current basis",
    "order_text": "operative text or identification of the order not held",
    "opus_media": "zero-agent refetch of a cited FR issue",
    "other": "other",
}
BLOCKER_RULES = [
    ("knock_on", r"^depends on|\(depends on|upstream|^no claim|nothing (proposed|to review)|no (claim|approved status|"
                 r"reviewed status)|no claim or|not producible"),
    ("status_history", r"dated (status[- ])?history|no dated history|refused freeze|refuses to freeze|kit refused"),
    ("later_search", r"bounded[_ ](machine )?later|later-source search|machine_searches"),
    ("tool_rule", r"tool (policy|rule)|overlay-propose writes"),
    ("status_adoption", r"provisional[_ ]status|status proposal|status decision|status is adopted|owner adoption"),
    ("opus_media", r"opus[_ ]media|refetch"),
    ("raw_bytes", r"custody|retain|hash|only a custody|bytes|^fetch |git-lfs|lfs object|not retrieved|re-fetch"),
    ("official_original", r"nara|rg ?11|official (original|printing|copy|print)|gpo|page image|proquest|scan|"
                          r"state dep|slip|pamphlet|printing|compilation page|hoover|page check"),
    ("agency_records", r"appoint|land|blm|board report|csc|opm|execution|reinstatement|personnel|promotion|plat\b|"
                       r"resurvey|plo \d|public land order|transfer|sale|navy|forest|district records|interment|"
                       r"exemptions ended|performed|commission report"),
    ("legal_sources", r"resolution|congress|statute|stat\.|cfr|notice|continuation|revok|supersed|ending|current[- ]law|"
                      r"current[- ]status|amendment|later order|rules|\bact\b|term record|expir|final report"),
    ("order_text", r"operative text|identif|no held text|working text|text of eo|clause text"),
]


def blocker_class(text):
    t = (text or "").lower()
    for name, rx in BLOCKER_RULES:
        if re.search(rx, t):
            return name
    return "other"


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
    # A coordinator whose trace prices every worker has its worker telemetry fully accounted for already.
    for h, rows in usage.items():
        mine = [i for i, t in enumerate(workers) if t["_h"] == h]
        if mine and all(i in costs for i in mine):
            used.update((h, j) for j in range(len(rows)))
    claims = collections.defaultdict(list)   # (coordinator, telemetry row) -> workers that name it
    for i, t in enumerate(workers):
        if i in costs:
            continue
        rows = usage.get(t["_h"], [])
        name = t.get("worker") or ""
        sids = set(t.get("session_ids") or ([t["session_id"]] if t.get("session_id") else []))
        for j, r in enumerate(rows):
            if not is_coordination(r) and (
                    r.get("phase") == name or r.get("batch") == name or r.get("agent_id") == name
                    or any(s and (r.get("session_id") or "").startswith(s) for s in sids)):
                claims[(t["_h"], j)].append(i)
    # A session resumed by several workers (a reveal, a correction) is one telemetry row: split it among them.
    for (h, j), ws in claims.items():
        share = row_usd(usage[h][j]) / len(ws)
        for i in ws:
            costs[i] = (costs.get(i, (0.0, ""))[0] + share, "telemetry")
        used.add((h, j))
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
    left_by_h = collections.defaultdict(float)
    for key, v in pools.items():
        if waiting.get(key):
            for i in waiting[key]:
                costs[i] = (v / len(waiting[key]), "telemetry-pool")
        else:
            left_by_h[key[0]] += v
    # Conservation: worker telemetry no rule could attach still belongs to that coordinator's workers. It goes to the
    # coordinator's unpriced workers by duration, or, if none, to all its workers by duration, so no measured dollar
    # is dropped from the projection.
    def dur(t):
        a, b = ts(t.get("started_utc")), ts(t.get("ended_utc"))
        return max(1.0, (b - a).total_seconds()) if a and b else 1.0
    leftover = 0.0
    for h, v in left_by_h.items():
        mine = [i for i, t in enumerate(workers) if t["_h"] == h]
        target = [i for i in mine if i not in costs] or mine
        if not target:
            leftover += v
            continue
        tot = sum(dur(workers[i]) for i in target)
        for i in target:
            prev = costs.get(i, (0.0, ""))[0]
            costs[i] = (prev + v * dur(workers[i]) / tot, "telemetry-spread")
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
    # Cost groups: coordinators split the same work differently (H2 and H3 produced the four lifecycle steps as one
    # sheet; others ran one worker per step), so per-step dollars are compared at the level of these groups. Every
    # sampled order was reached at every open step, so totals are order-level Horvitz-Thompson estimates.
    def group_cost(r, g):
        return sum(v["usd"] for s, v in r["steps"].items() if COST_GROUP.get(s, s) == g)

    def order_level(field):
        return lambda rs: estimate(rs, N, lambda r: r[field])[0]
    proj = {"usd_total": interval(rows, order_level("usd"), args.boot),
            "usd_workers": interval(rows, order_level("worker_usd"), args.boot),
            "usd_coordination": interval(rows, order_level("overhead_usd"), args.boot),
            "worker_hours": interval(rows, lambda rs: estimate(rs, N, lambda r: r["seconds"] / 3600)[0], args.boot),
            "orders_all_steps_good": interval(
                rows, lambda rs: estimate(rs, N, lambda r: 1.0 if r["all_steps_good"] else 0.0)[0], args.boot),
            "borrowed_strata": sorted(estimate(rows, N, lambda r: 0.0)[1])}
    groups = sorted({COST_GROUP.get(s, s) for r in rows for s in r["steps"]},
                    key=lambda g: GROUP_ORDER.index(g) if g in GROUP_ORDER else 99)
    by_group = []
    for g in groups:
        c = interval(rows, lambda rs, g=g: estimate(rs, N, lambda r: group_cost(r, g))[0], args.boot)
        users = [r for r in rows if any(COST_GROUP.get(s, s) == g for s in r["steps"])]
        by_group.append({"cost_group": g, "orders_measured": len(users), "usd_point": c["point"], "usd_p10": c["p10"],
                         "usd_p90": c["p90"], "usd_round1": c["round1"], "usd_round2": c["round2"],
                         "usd_per_order_where_run": round(sum(group_cost(r, g) for r in users) / len(users), 3)
                         if users else None})
    # Outcome rates per research step (rows in ORDER_OUTCOMES), whatever worker produced them.
    by_step = []
    for s in [x for x in STEPS if x != "review"] + ["review_status", "review_text", "review_claim"]:
        def oc(r, s=s):
            v = [norm_outcome(val.get("outcome")) for k, val in r["steps"].items()
                 if (REVIEW_KIND.get(k, k) if s.startswith("review") else k) == s]
            v = [x for x in v if x not in {"not_reached", "not_applicable"}]
            return v[-1] if v else None
        el = [r for r in rows if r["reached"] and oc(r)]
        if not el:
            continue

        def share(test, s=s, oc=oc):
            return estimate(rows, N, lambda r: 1.0 if test(oc(r)) else 0.0, lambda r: r["reached"] and oc(r))[0]
        tr = share(lambda o: True)
        g, bl, fl = share(lambda o: o in GOOD), share(lambda o: o == "blocked"), \
            share(lambda o: o in {"failed", "rejected"})
        cc = sum(v for (h, st), v in cells.items() if st == s and h in N)
        by_step.append({"step": s, "census_cells_open": cc, "orders_measured": len(el),
                        "good_rate": round(g / tr, 3) if tr else None,
                        "blocked_rate": round(bl / tr, 3) if tr else None,
                        "failed_or_rejected_rate": round(fl / tr, 3) if tr else None,
                        "projected_good_cells": round(cc * g / tr) if tr and cc else None,
                        "projected_blocked_cells": round(cc * bl / tr) if tr and cc else None})
    by_group = [b for b in by_group if b["cost_group"] != "human_certification"]
    good_orders = [r for r in rows if r["all_steps_good"]]
    rng = random.Random(1789)
    gm = [r["usd"] for r in good_orders]
    reps = sorted(sum(rng.choice(gm) for _ in gm) / len(gm) for _ in range(args.boot)) if gm else []
    finish = {"orders_fully_good_in_sample": len(good_orders),
              "mean_usd_per_fully_good_order": round(sum(gm) / len(gm), 3) if gm else None,
              "p10": round(reps[int(0.1 * len(reps))], 3) if reps else None,
              "p90": round(reps[int(0.9 * len(reps)) - 1], 3) if reps else None,
              "basis": "mean total cost (workers + allocated coordination) of sampled orders whose every open step "
                       "succeeded; applies to an order once its blockers are cleared, if it then behaves like them"}
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
        seen = {re.sub(r"\s+", " ", acquisition(v.get("outcome")).lower())[:160] for v in r["steps"].values()} - {""}
        for a in seen:
            acq[a][r["stratum"]] += 1
    reached_n = collections.Counter(r["stratum"] for r in rows if r["reached"])

    def project_counts(c):
        return round(sum(N[h] * k / reached_n[h] for h, k in c.items() if reached_n[h]))
    acq_rows = sorted(({"acquisition": a, "sampled_orders": sum(c.values()), "projected_orders": project_counts(c),
                        "blocker_class": blocker_class(a), "strata": "|".join(sorted(c))} for a, c in acq.items()),
                      key=lambda x: -x["projected_orders"])
    # Root blockers per order: every class an order is blocked on, ignoring knock-on blocks. "sole" = the only root
    # class, so fixing it alone would let that order's agent steps proceed (they may still fail on the merits).
    any_c, sole_c = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
    for r in rows:
        if not r["reached"]:
            continue
        classes = {blocker_class(acquisition(v.get("outcome"))) for v in r["steps"].values()
                   if acquisition(v.get("outcome"))} - {"knock_on"}
        for c in classes:
            any_c[c][r["stratum"]] += 1
        if len(classes) == 1:
            sole_c[next(iter(classes))][r["stratum"]] += 1
        if not classes:
            any_c["none"][r["stratum"]] += 1
    blockers = sorted(({"blocker_class": c, "label": BLOCKER_LABELS.get(c, c),
                        "sampled_orders": sum(v.values()), "projected_orders": project_counts(v),
                        "projected_orders_sole_blocker": project_counts(sole_c.get(c, {}))}
                       for c, v in any_c.items()), key=lambda x: -x["projected_orders"])
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
    if t0 and t1:
        hrs = (t1 - t0).total_seconds() / 3600
        reached = sum(r["reached"] for r in rows)
        summary["measured_throughput"] = {
            "orders_per_hour_one_machine": round(reached / hrs, 1), "window_hours": round(hrs, 2),
            "machine": "one 8 GB, 2-CPU cloud session; memory, not API limits, capped parallel workers at about 18",
            "days_one_machine_for_census": round(sum(N.values()) / (reached / hrs) / 24, 1),
            "note": "at today's block rates; blocked steps end in minutes, so unblocked work will run slower"}
    summary["blockers"] = blockers
    summary["by_step"] = by_step
    summary["by_cost_group"] = by_group
    summary["cost_per_order_once_unblocked"] = finish
    # Census fact, not a sample estimate: undecided orders with no dated status history, which the claim kit refuses.
    idx_p = REPO / "jobs/status-history/output/INDEX.json"
    if idx_p.is_file() and not args.root:
        idx = {r["instrument_id"]: r for r in json.loads(idx_p.read_text())}
        und = [i for i, o in orders.items() if o.get("status") == "none" and o.get("stratum") != "ready"]
        summary["census_undecided_without_dated_history"] = {
            "undecided": len(und), "without_history": sum(1 for i in und if idx.get(i, {}).get("history") is None)}
    (OUT / "PROJECTION.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    for name, data in (("BY_STEP.csv", by_step), ("BY_COST_GROUP.csv", by_group), ("BY_STRATUM.csv", by_stratum), ("ACQUISITIONS.csv", acq_rows),
                       ("BLOCKERS.csv", blockers),
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
