#!/usr/bin/env python3
"""Junto: scores token-saving finders by VERIFIED dollars saved per dollar spent.

Named for Benjamin Franklin's Junto (1727). Design: research/plans/JUNTO_DESIGN.md.

Subcommands (standard library only; run with `python3 -I jobs/junto/junto.py ...`):
  run       run registered finders over a data dir; append candidates and the run cost
  add-test  record a before-and-after test; the ONLY way a candidate becomes verified
  score     verified USD saved / (USD spent + prior) per finder -> output/SCOREBOARD.json
  allocate  effort shares for one meeting: exploitation by score + exploration share
  propose   blind-spot step: unpredicted measured waste -> new-finder proposals
  check     validate the ledger (schemas, privacy rules, verified lines tied to tests)

Hard rule: a saving counts only after a small before-and-after test that measured it.
Estimates, projections and "should save" never enter a score. Every finder output is
forced to status "unverified" on the way in. Ledger files are append-only JSON Lines;
the current state of an id is its line with the highest `rev`.

Exit codes: 0 ok; 2 bad input or refused request; 3 privacy refusal.
"""
import argparse, hashlib, json, math, os, re, subprocess, sys, tempfile, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
WRITTEN_BY = "astra"
SAVES_RATIO = 0.9  # a test "saves" only if after <= 0.9 * before per unit (design section 1)

DEFAULT_CONFIG = {
    "round_budget_usd": 10.0,       # the owner sets this
    "exploration_share": 0.20,
    "max_exploring_per_round": 3,
    "prior_s0_usd": 2.0,
    "exploitation_floor": 0.05,
    "dormant_min_resolved_tests": 2,
    "dormant_min_spent_usd": 10.0,
    "dormant_reentry_every_rounds": 5,
    "exploring_below_resolved_tests": 2,
    "waste_share_of_session": 0.05,
    "waste_usd": 1.00,
    "waste_rise": 0.20,
    "waste_min_rise_usd": 0.10,
}

RESOLVED_VERDICTS = ("saves", "no_saving", "quality_fell")
COST_PHASES = ("production", "build", "coordination", "monitoring", "review", "rework", "integration")
VALUE_BASES = ("api_token_value", "get_session.cost_usd", "local_script")
SECRET_RES = [re.compile(p) for p in (
    r"ghp_[A-Za-z0-9]{6,}", r"github_pat_", r"\bsk-[A-Za-z0-9_-]{8,}", r"\bxox[abprs]-", r"AKIA[0-9A-Z]{8,}",
    r"Bearer\s+\S", r"-----BEGIN", r"\b(token|key|sig|password|secret)=", r"@[A-Za-z0-9-]+\.[A-Za-z]{2,}",
    r"https?://\S*\?\S+")]
ABS_PATH_RE = re.compile(r"(^|[\s\"'(])(/(home|tmp|root|Users|var|etc|mnt)/|[A-Za-z]:\\)")
KEY_RE = re.compile(r"^[a-z][a-z0-9_]{1,48}$")
# Hamilton's rule: never echo a command that sets variables. Any NAME=value text is refused.
ASSIGN_RE = re.compile(r"(?<![\w.:/-])(?:export\s+)?[A-Za-z_][A-Za-z0-9_]*=(?!=)\S")
CAUSE_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{1,60}$")


sys.path.insert(0, str(ROOT))  # sibling import also works under python -I
from contracts import validate_contract


class Refusal(Exception):
    def __init__(self, msg, code=2):
        super().__init__(msg)
        self.code = code


# ---------------------------------------------------------------- ledger io
def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today():
    return datetime.now(timezone.utc).strftime("%Y%m%d")


class Ctx:
    def __init__(self, ledger=None, output=None):
        self.ledger = Path(ledger) if ledger else ROOT / "ledger"
        self.output = Path(output) if output else ROOT / "output"
        self.config = dict(DEFAULT_CONFIG)
        cfg = ROOT / "config.json"
        if cfg.exists():
            self.config.update({k: v for k, v in json.loads(cfg.read_text()).items() if k in DEFAULT_CONFIG})

    def p(self, name):
        return self.ledger / name

    def finders(self):
        f = self.p("finders.json")
        return json.loads(f.read_text()).get("finders", []) if f.exists() else []

    def rows(self, name):
        f = self.p(name)
        if not f.exists():
            return []
        out = []
        for i, line in enumerate(f.read_text().splitlines(), 1):
            if line.strip():
                try:
                    out.append(json.loads(line))
                except ValueError:
                    raise Refusal("%s line %d is not JSON" % (name, i))
        return out

    def current(self, name, idkey):
        cur = {}
        for r in self.rows(name):
            i = r.get(idkey)
            if i is not None and (i not in cur or r.get("rev", 0) >= cur[i].get("rev", 0)):
                cur[i] = r
        return cur

    def append(self, name, records):
        for r in records:
            bad = privacy_problems(r)
            if bad:
                raise Refusal("privacy refusal writing %s: %s" % (name, "; ".join(bad[:3])), 3)
        self.ledger.mkdir(parents=True, exist_ok=True)
        with open(self.p(name), "a") as fh:
            for r in records:
                fh.write(json.dumps(r, sort_keys=True) + "\n")

    def next_id(self, prefix, name, idkey):
        day = today()
        stem = "%s-%s-" % (prefix, day)
        n = 0
        for r in self.rows(name):
            i = str(r.get(idkey, ""))
            if i.startswith(stem):
                n = max(n, int(i[len(stem):] or 0))
        box = [n]
        return lambda: _bump(stem, box)


def _bump(stem, box):
    box[0] += 1
    return stem + str(box[0])


# ---------------------------------------------------------------- privacy
def _strings(o, path=""):
    if isinstance(o, str):
        yield path, o
    elif isinstance(o, dict):
        for k, v in o.items():
            yield from _strings(v, path + "." + str(k))
    elif isinstance(o, (list, tuple)):
        for i, v in enumerate(o):
            yield from _strings(v, "%s[%d]" % (path, i))


def privacy_problems(rec):
    """Design section 5: no secrets, emails, query-string URLs, absolute paths, long evidence."""
    bad = []
    for path, s in _strings(rec):
        for rx in SECRET_RES:
            if rx.search(s):
                bad.append("%s matches %s" % (path, rx.pattern[:20]))
                break
        else:
            if ABS_PATH_RE.search(s):
                bad.append("%s holds an absolute path" % path)
            elif ".evidence" in path and len(s) > 200:
                bad.append("%s longer than 200 characters" % path)
            elif ASSIGN_RE.search(s):
                bad.append("%s echoes a variable assignment" % path)
            elif (path.endswith("cause_key") or re.search(r"\.targets\[\d+\]$", path)) and not CAUSE_KEY_RE.match(s):
                bad.append("%s is not a cause key slug" % path)
    return bad


def inside_repo(p):
    p = Path(p).resolve()
    return p == REPO or REPO in p.parents


# ---------------------------------------------------------------- money
def arm_ppu(arm):
    return float(arm["usd"]) / float(arm["units"])


def quality_ok(test):
    """True/False for comparable observed quality; None means quality is unverified."""
    b, a = test["before"].get("quality") or {}, test["after"].get("quality") or {}

    def rate(q):
        if any(type(q.get(k)) is not int or q[k] < 0 for k in ("accepted", "rejected")):
            return None
        n = q["accepted"] + q["rejected"]
        return None if n <= 0 else q["rejected"] / n
    rb, ra = rate(b), rate(a)
    return None if rb is None or ra is None else ra <= rb + 1e-12


def rejection_interval(q):
    """Wilson 95% interval for the finite pilot; no independence claim across pilots."""
    n = q.get("accepted", 0) + q.get("rejected", 0)
    if n <= 0:
        return None
    p, z = q["rejected"] / n, 1.959963984540054
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [max(0, centre - half), min(1, centre + half)]


def finite_nonnegative(value):
    return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def measurement_gaps(test):
    """A numerical cost drop alone is insufficient for quality-preserving credit."""
    gaps = []
    if not test.get("unit_of_work") or not test.get("matched_on"):
        gaps.append("workload_match_unverified")
    for which in ("before", "after"):
        arm = test.get(which) or {}
        if arm.get("cost_coverage") != "complete" or set(arm.get("included_phases", [])) != set(COST_PHASES):
            gaps.append(which + "_total_cost_incomplete")
        if not arm.get("measurement_ref"):
            gaps.append(which + "_measurement_reference_missing")
        q = arm.get("quality") or {}
        if quality_ok(test) is None or (q.get("accepted", 0) + q.get("rejected", 0)) < arm.get("units", 0):
            gaps.append(which + "_quality_coverage_unverified")
    if test.get("before", {}).get("usd_basis") != test.get("after", {}).get("usd_basis"):
        gaps.append("cost_bases_differ")
    if not finite_nonnegative(test.get("test_cost_usd")):
        gaps.append("test_overhead_unknown")
    if test.get("contract_id") and test.get("registration_status") != "preregistered":
        gaps.append("contract_registration_unverified")
    return sorted(set(gaps))


def verdict_of(test):
    """Recomputed from the two measured arms; a stored verdict is never trusted."""
    try:
        b, a = test["before"], test["after"]
        if any(not finite_nonnegative(v) for v in (b["usd"], b["units"], a["usd"], a["units"])):
            return None
        if b["usd"] <= 0 or b["units"] <= 0 or a["units"] <= 0:
            return "inconclusive"
        if not all(math.isfinite(float(v)) for v in (b["usd"], b["units"], a["usd"], a["units"])):
            return None
        bp, ap = arm_ppu(b), arm_ppu(a)
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return None
    if ap <= SAVES_RATIO * bp + 1e-12:
        if quality_ok(test) is None:
            return "cost_reduction_quality_unverified"
        if not quality_ok(test):
            return "quality_fell"
        return "cost_reduction_measurement_incomplete" if measurement_gaps(test) else "saves"
    if ap >= bp:
        return "no_saving"
    return "inconclusive"


def test_valid(test):
    return bool(test) and test.get("phase") == "measured" and verdict_of(test) is not None


def delta_usd_saved(test):
    return (arm_ppu(test["before"]) - arm_ppu(test["after"])) * float(test["after"]["units"])


def origin_kind(c):
    """Seeds written by seed-candidate carry an origin object; NEYMAN's ledger rows carry an 'owner-seeded' string."""
    o = c.get("origin")
    if isinstance(o, dict):
        return o.get("kind", "finder")
    return "owner" if o == "owner-seeded" else "finder"


def test_finders(ctx, test, cands=None):
    cands = cands if cands is not None else ctx.current("candidates.jsonl", "candidate_id")
    if any(origin_kind(cands.get(cid) or {}) in ("owner", "agent")
           for cid in test.get("candidate_ids", [])):
        return []  # supplied ideas are not inventions credited to a mining finder
    seen = []
    for cid in test.get("candidate_ids", []):
        c = cands.get(cid) or {}
        f = c.get("finder_id") if origin_kind(c) == "finder" else None
        if f and f not in seen:
            seen.append(f)
    return seen


def valid_verified_lines(ctx):
    """Only lines tied to a measured test whose recomputed verdict is 'saves', capped by the
    measured delta, one per test, count. Returns [(line, test, [finder ids])]."""
    tests = ctx.current("tests.jsonl", "test_id")
    cands = ctx.current("candidates.jsonl", "candidate_id")
    out, used, used_after = [], set(), set()
    for v in ctx.rows("verified_savings.jsonl"):
        t = tests.get(v.get("test_id"))
        if t and t.get("contract_id"):
            contract = ctx.current("contracts.jsonl", "contract_id").get(t["contract_id"])
            if not contract or registration_status(ctx, contract, t.get("registration_commit"), t.get("measurement_started_at")) != "preregistered" or contract_gaps(ctx, contract, t):
                continue
        if not test_valid(t) or verdict_of(t) != "saves" or v.get("kind") != "test_realized":
            continue
        if v["test_id"] in used:
            continue
        try:
            usd = float(v["usd_saved"])
        except (KeyError, TypeError, ValueError):
            continue
        if not finite_nonnegative(usd) or usd <= 0 or usd > delta_usd_saved(t) + 0.01:
            continue
        after_s = set(t["after"].get("session_ids") or [])
        if not after_s or after_s & used_after:   # no measured session, or the same saving counted twice
            continue
        used.add(v["test_id"])
        used_after |= after_s
        out.append((v, t, test_finders(ctx, t, cands)))
    return out


# ---------------------------------------------------------------- score
def compute(ctx):
    """Known token valuation and coverage, without turning missing expenses into zero.

    Arm totals include production and all failed/rework attempts. Test cost is
    additional overhead outside those totals. Identical session-set receipts are
    counted once; conflicting/partially overlapping totals make coverage unknown.
    """
    cfg = ctx.config
    cands = ctx.current("candidates.jsonl", "candidate_id")
    tests = ctx.current("tests.jsonl", "test_id")
    row = {f["finder_id"]: {"finder_id": f["finder_id"], "name": f.get("name"),
            "stored_state": f.get("state", "exploring"), "added_at": f.get("added_at", ""),
            "spent_runs_usd": 0.0, "spent_tests_usd": 0.0, "unknown_cost_records": 0,
            "verified_usd": 0.0, "resolved_tests": 0, "candidates": {}} for f in ctx.finders()}
    overhead, unknown, cash_known = 0.0, 0, 0.0
    receipts, seen_sessions = {}, set()

    def add_cost(value, basis, finders, field, complete=True, receipt=None, sessions=()):
        nonlocal overhead, unknown, cash_known
        if receipt and receipt in receipts:
            if receipts[receipt] != (value, basis):
                unknown += 1
                for f in finders:
                    row[f]["unknown_cost_records"] += 1
            return
        if receipt:
            receipts[receipt] = (value, basis)
        overlaps = bool(set(sessions) & seen_sessions)
        seen_sessions.update(sessions)
        known = finite_nonnegative(value) and basis in VALUE_BASES
        if finite_nonnegative(value) and basis == "cash_charge":
            cash_known += value
        if not known or not complete or overlaps:
            unknown += 1
            for f in finders:
                row[f]["unknown_cost_records"] += 1
        if known and not overlaps:
            if finders:
                for f in finders:
                    row[f][field] += value / len(finders)
            else:
                overhead += value

    for r in ctx.current("runs.jsonl", "run_id").values():
        fs = [r["finder_id"]] if r.get("finder_id") in row else []
        add_cost(r.get("usd_spent"), r.get("usd_basis"), fs, "spent_runs_usd",
                 r.get("cost_coverage", "complete") == "complete", "run:" + r["run_id"])
    for c in cands.values():
        if c.get("finder_id") in row:
            counts = row[c["finder_id"]]["candidates"]
            counts[c.get("status", "unverified")] = counts.get(c.get("status", "unverified"), 0) + 1
    for t in tests.values():
        fs = [f for f in test_finders(ctx, t, cands) if f in row]
        # Failed/incomplete tests still incurred costs; do not filter on verdict.
        add_cost(t.get("test_cost_usd"), t.get("usd_basis", "get_session.cost_usd"), fs,
                 "spent_tests_usd", t.get("test_cost_usd") is not None, "test:" + t["test_id"])
        for which in ("before", "after"):
            arm = t.get(which) or {}
            sessions = sorted(set(arm.get("session_ids") or []))
            receipt = "sessions:" + json.dumps(sessions) if sessions else None
            add_cost(arm.get("usd"), arm.get("usd_basis"), fs, "spent_tests_usd",
                     arm.get("cost_coverage") == "complete", receipt, sessions)
        for f in fs:
            if verdict_of(t) in RESOLVED_VERDICTS:
                row[f]["resolved_tests"] += 1
    credited_total = 0.0
    for v, t, fs in valid_verified_lines(ctx):
        if t["before"].get("usd_basis") not in VALUE_BASES:
            continue
        credited_total += float(v["usd_saved"])
        fs = [f for f in fs if f in row]
        for f in fs:
            row[f]["verified_usd"] += float(v["usd_saved"]) / len(fs)
    s0 = float(cfg["prior_s0_usd"])
    for r in row.values():
        r["known_spent_usd"] = r["spent_runs_usd"] + r["spent_tests_usd"]
        r["spent_usd"] = None if r["unknown_cost_records"] else r["known_spent_usd"]
        r["score"] = None if r["spent_usd"] is None else r["verified_usd"] / (r["spent_usd"] + s0)
        if r["stored_state"] == "retired":
            r["state"] = "retired"
        elif r["score"] is None or r["resolved_tests"] < cfg["exploring_below_resolved_tests"]:
            r["state"] = "exploring"
        elif r["score"] == 0 and r["resolved_tests"] >= cfg["dormant_min_resolved_tests"] and r["spent_usd"] >= cfg["dormant_min_spent_usd"]:
            r["state"] = "dormant"
        else:
            r["state"] = "scored"
    known = sum(r["known_spent_usd"] for r in row.values()) + overhead
    spent = None if unknown else known
    return row, {"valuation_basis": "api_token_value", "verified_usd": credited_total,
                 "finder_credited_usd": sum(r["verified_usd"] for r in row.values()),
                 "known_spent_usd": known, "spent_usd": spent, "junto_overhead_usd": overhead,
                 "unknown_cost_records": unknown, "known_cash_charges_usd": cash_known,
                 "cash_charge_total_usd": None,
                 "net_after_known_expenses_usd": credited_total - known,
                 "verified_per_spent": credited_total / spent if spent else None,
                 "deployment_evidence": "pilot_results_only; broad deployment not established"}


def allocate_plan(ctx, row, budget, round_no):
    cfg = ctx.config
    alloc = {k: 0.0 for k in row}
    exploring = [r for r in row.values() if r["state"] == "exploring"]
    if round_no and round_no % int(cfg["dormant_reentry_every_rounds"]) == 0:
        exploring += [r for r in row.values() if r["state"] == "dormant"]
    exploring.sort(key=lambda r: (r["added_at"], r["finder_id"]))
    exploring = exploring[:int(cfg["max_exploring_per_round"])]
    pos = [r for r in row.values() if r["state"] == "scored" and r["score"] is not None and r["score"] > 0]
    explore_pool = budget * float(cfg["exploration_share"])
    exploit_pool = budget - explore_pool
    if not exploring:
        exploit_pool += explore_pool
        explore_pool = 0.0
    if not pos:
        explore_pool += exploit_pool
        exploit_pool = 0.0
    for r in exploring:
        alloc[r["finder_id"]] += explore_pool / len(exploring)
    if pos and exploit_pool > 0:
        floor = float(cfg["exploitation_floor"]) * exploit_pool
        total = sum(r["score"] for r in pos)
        free = exploit_pool - floor * len(pos)
        if free < 0:
            floor, free = exploit_pool / len(pos), 0.0
        for r in pos:
            alloc[r["finder_id"]] += floor + free * r["score"] / total
    unspent = budget - sum(alloc.values())
    return alloc, max(unspent, 0.0)


def write_scoreboard(ctx, row, total, alloc=None, extra=None):
    ctx.output.mkdir(parents=True, exist_ok=True)
    rows = []
    for r in sorted(row.values(), key=lambda r: (-(r["score"] or 0), r["finder_id"])):
        o = {k: (round(r[k], 4) if isinstance(r[k], float) else r[k]) for k in
             ("finder_id", "state", "spent_usd", "known_spent_usd", "unknown_cost_records", "verified_usd", "score", "resolved_tests", "candidates")}
        if alloc is not None:
            o["allowance_usd"] = round(alloc[r["finder_id"]], 2)
        rows.append(o)
    doc = {"schema": "junto.scoreboard/2", "written_at": now(), "written_by": WRITTEN_BY,
           "note": "Derived by junto.py; never hand-edited. Only verified savings enter a score; estimates never do.",
           "formula": "score = verified_usd / (spent_usd + prior_s0_usd)", "prior_s0_usd": ctx.config["prior_s0_usd"],
           "finders": rows, "junto_total": {k: round(v, 4) if isinstance(v, float) else v for k, v in total.items()}}
    if extra:
        doc.update(extra)
    (ctx.output / "SCOREBOARD.json").write_text(json.dumps(doc, indent=1) + "\n")
    return doc


# ---------------------------------------------------------------- run
def load_finder_output(path):
    text = Path(path).read_text()
    if not text.strip():
        return []
    try:
        doc = json.loads(text)
        if isinstance(doc, dict) and isinstance(doc.get("candidates"), list):
            return doc["candidates"]
    except ValueError:
        pass
    return [json.loads(l) for l in text.splitlines() if l.strip()]


def cmd_run(ctx, a):
    if inside_repo(a.data):
        raise Refusal("data dir is inside the repository; raw transcripts must stay outside", 3)
    if not Path(a.data).is_dir():
        raise Refusal("data dir not found")
    fins = [f for f in ctx.finders() if f.get("state") != "retired"]
    if a.finder:
        fins = [f for f in fins if f["name"] in a.finder or f["finder_id"] in a.finder]
        if not fins:
            raise Refusal("no registered finder matches")
    if not fins:
        raise Refusal("no registered finders")
    per_run = a.usd_spent / len(fins) if a.usd_spent is not None else None
    if a.usd_spent is not None and not finite_nonnegative(a.usd_spent):
        raise Refusal("usd-spent must be finite and nonnegative")
    basis = a.usd_basis or ("api_token_value" if a.usd_spent is not None else "unknown")
    known_runs = ctx.rows("runs.jsonl")
    run_new = ctx.next_id("R", "runs.jsonl", "run_id")
    cand_new = ctx.next_id("C", "candidates.jsonl", "candidate_id")
    summary, status = [], 0
    for f in fins:
        script = Path(f["script"])
        script = script if script.is_absolute() else REPO / script
        run_id = run_new()
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out.jsonl"
            cmd = [sys.executable, "-I", str(script), "--data", str(a.data), "--out", str(out), "--run-id", run_id]
            if a.profiles:
                cmd += ["--profiles", str(a.profiles)]
            t0 = time.time()
            pr = subprocess.run(cmd, capture_output=True, text=True)
            wall = round(time.time() - t0, 2)
            meta = {}
            rj = Path(str(out) + ".run.json")
            if rj.exists():
                meta = json.loads(rj.read_text())
            recs = load_finder_output(out) if pr.returncode == 0 and out.exists() else []
        digest = meta.get("data_digest")
        if pr.returncode == 0 and digest and any(r.get("finder_id") == f["finder_id"] and r.get("data_digest") == digest
                                                and r.get("finder_version") == f.get("version") and r.get("candidates_emitted")
                                                for r in known_runs) and not a.force:
            if True:   # even an unknown-cost duplicate attempt remains in the ledger
                ctx.append("runs.jsonl", [{"schema": "junto.run/1", "run_id": run_id, "rev": 0, "finder_id": f["finder_id"],
                                           "finder_version": f.get("version"), "wall_seconds": wall, "data_digest": digest,
                                           "inputs": meta.get("inputs", {}), "candidates_emitted": [], "skipped_duplicate": True,
                                           "usd_spent": round(per_run, 4) if per_run is not None else None, "usd_basis": basis, "exit_code": 0,
                                           "round_id": a.round_id, "written_at": now(), "written_by": WRITTEN_BY}])
            summary.append("%s: skipped, same data and version already run (use --force); cost %s logged" % (f["name"], per_run))
            continue
        ids, new = [], []
        for r in recs:
            r = dict(r)
            try:
                validate_contract(r)
            except ValueError as e:
                raise Refusal(str(e))
            cid = cand_new()
            ids.append(cid)
            r.update({"schema": "junto.candidate/1", "candidate_id": cid, "rev": 0, "finder_id": f["finder_id"],
                      "run_id": run_id, "status": "unverified", "status_ref": None,
                      "written_at": now(), "written_by": WRITTEN_BY})
            new.append(r)
        run = {"schema": "junto.run/1", "run_id": run_id, "rev": 0, "finder_id": f["finder_id"],
               "finder_version": f.get("version"), "wall_seconds": meta.get("wall_seconds", wall), "data_digest": digest,
               "inputs": meta.get("inputs", {}), "candidates_emitted": ids, "usd_spent": round(per_run, 4) if per_run is not None else None,
               "usd_basis": basis, "exit_code": pr.returncode, "round_id": a.round_id,
               "written_at": now(), "written_by": WRITTEN_BY}
        try:
            ctx.append("candidates.jsonl", new)
        except Refusal as e:  # design 5.8: nothing appended, the run (and its cost) is still logged
            run["candidates_emitted"], run["exit_code"] = [], 3
            ctx.append("runs.jsonl", [run])
            raise Refusal("%s: %s" % (f["name"], e), 3)
        if pr.returncode != 0:
            status = 2
        ctx.append("runs.jsonl", [run])
        summary.append("%s: exit %d, %d candidates (all unverified), usd_spent %s" % (f["name"], pr.returncode, len(ids), per_run))
    print("\n".join(summary[:20]))
    return status


# ---------------------------------------------------------------- add-test
def read_record(path):
    try:
        record = json.loads(Path(path).read_text())
    except (OSError, ValueError) as e:
        raise Refusal("cannot read JSON record: " + str(e))
    if not isinstance(record, dict):
        raise Refusal("record must be a JSON object")
    if privacy_problems(record):
        raise Refusal("record failed ledger privacy checks", 3)
    return record


def cmd_seed_candidate(ctx, a):
    rec = read_record(a.file)
    origin = rec.get("origin") or {}
    if not isinstance(origin, dict) or origin.get("kind") not in ("owner", "agent") or not origin.get("reference") or not origin.get("name"):
        raise Refusal("origin needs kind owner|agent, name, and a source reference")
    targets = rec.get("targets")
    if not isinstance(rec.get("saver_key"), str) or not KEY_RE.fullmatch(rec["saver_key"]) or not isinstance(rec.get("title"), str) or not rec["title"] or not isinstance(targets, list) or not targets or any(not isinstance(t, str) or not CAUSE_KEY_RE.fullmatch(t) for t in targets):
        raise Refusal("candidate needs a stable saver_key, title, and target cause keys")
    existing = ctx.current("candidates.jsonl", "candidate_id")
    if any(c.get("saver_key") == rec["saver_key"] and c.get("origin") == origin for c in existing.values()):
        raise Refusal("this origin and saver_key are already registered")
    cid = ctx.next_id("C", "candidates.jsonl", "candidate_id")()
    rec.update(schema="junto.candidate/2", candidate_id=cid, rev=0, finder_id=None,
               run_id=None, status="unverified", status_ref=None, written_at=now(), written_by=WRITTEN_BY)
    ctx.append("candidates.jsonl", [rec])
    print(cid + ": seeded, unverified; finder invention credit disabled")
    return 0


def contract_problems(c):
    required = ("contract_id", "candidate_ids", "sample", "baseline", "unit_of_work", "matched_on",
                "outcome_definition", "quality_condition", "budget_usd", "stop_rules", "result_paths")
    bad = ["missing " + k for k in required if k not in c or c[k] in (None, "", [], {})]
    sample = c.get("sample")
    if not isinstance(sample, list) or not sample or any(not isinstance(x, dict) or not isinstance(x.get("id"), str) or not x["id"] or
            not re.fullmatch(r"[0-9a-f]{64}", str(x.get("sha256", ""))) for x in sample):
        bad.append("sample must pin every member by id and SHA-256")
    elif len({x["id"] for x in sample}) != len(sample):
        bad.append("sample ids must be unique")
    if not isinstance(c.get("baseline"), dict) or not c.get("baseline", {}).get("measurement_ref"):
        bad.append("baseline needs a measurement_ref")
    ids = c.get("candidate_ids")
    if not isinstance(ids, list) or not ids or any(not isinstance(i, str) for i in ids) or len(set(ids)) != len(ids):
        bad.append("candidate_ids must contain distinct candidate ids")
    if any(not isinstance(c.get(k), str) or not c[k] for k in ("contract_id", "unit_of_work", "matched_on", "outcome_definition")):
        bad.append("contract_id, unit_of_work, matched_on, outcome_definition must be nonempty strings")
    q = c.get("quality_condition") or {}
    if not isinstance(q, dict) or q.get("metric") != "rejection_rate" or q.get("max_increase") != 0 or type(q.get("min_reviewed")) is not int or q.get("min_reviewed", 0) < 1:
        bad.append("quality condition requires rejection_rate, max_increase 0, min_reviewed >= 1")
    stop = c.get("stop_rules") or {}
    if not isinstance(stop, dict) or type(stop.get("max_attempts")) is not int or stop.get("max_attempts", 0) < 1 or stop.get("stop_on_quality_drop") is not True:
        bad.append("stop rules require positive max_attempts and stop_on_quality_drop true")
    if not finite_nonnegative(c.get("budget_usd")):
        bad.append("budget_usd must be finite and nonnegative")
    paths = c.get("result_paths")
    if not isinstance(paths, list) or not paths or any(not isinstance(p, str) or Path(p).is_absolute() or ".." in Path(p).parts for p in paths):
        bad.append("result_paths must be nonempty repository-relative paths")
    return bad


def cmd_register_test(ctx, a):
    rec = read_record(a.file)
    bad = contract_problems(rec)
    if bad:
        raise Refusal("; ".join(bad))
    if rec["contract_id"] in ctx.current("contracts.jsonl", "contract_id"):
        raise Refusal("contracts are frozen; use a new contract_id and supersedes to revise")
    candidates = ctx.current("candidates.jsonl", "candidate_id")
    if any(cid not in candidates for cid in rec["candidate_ids"]):
        raise Refusal("contract refers to an unknown candidate")
    keys = {candidates[cid]["saver_key"] for cid in rec["candidate_ids"]}
    if len(keys) != 1:
        raise Refusal("one contract covers one intervention saver_key")
    rec.update(schema="junto.contract/1", rev=0, saver_key=keys.pop(), written_at=now(), written_by=WRITTEN_BY)
    ctx.append("contracts.jsonl", [rec])
    print(rec["contract_id"] + ": frozen; commit before measuring; registration is not yet verified")
    return 0


def registration_status(ctx, contract, commit, started_at):
    """Verify a frozen contract was committed before the declared measurement start.

    Receipt times remain observed inputs, not cryptographic proof of execution.
    Shallow/missing history is unchecked, never silently prospective.
    """
    if not commit or not re.fullmatch(r"[0-9a-f]{40}", commit) or not started_at:
        return "unchecked"
    try:
        root = Path(subprocess.check_output(["git", "-C", str(ctx.ledger), "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL, text=True).strip())
        rel = ctx.p("contracts.jsonl").resolve().relative_to(root).as_posix()
        raw = subprocess.check_output(["git", "-C", str(root), "show", commit + ":" + rel], stderr=subprocess.DEVNULL, text=True)
        if contract not in [json.loads(line) for line in raw.splitlines() if line.strip()]:
            return "contract_not_at_commit"
        commit_time = subprocess.check_output(["git", "-C", str(root), "show", "-s", "--format=%cI", commit], text=True).strip()
        if datetime.fromisoformat(started_at.replace("Z", "+00:00")) <= datetime.fromisoformat(commit_time):
            return "not_preregistered"
        for path in contract["result_paths"]:
            if subprocess.run(["git", "-C", str(root), "cat-file", "-e", commit + ":" + path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
                return "results_already_present"
        return "preregistered"
    except (OSError, ValueError, TypeError, subprocess.CalledProcessError):
        return "unchecked"


def contract_gaps(ctx, contract, test=None):
    current = ctx.current("tests.jsonl", "test_id")
    order = list(dict.fromkeys(t.get("test_id") for t in ctx.rows("tests.jsonl")))
    if test and test.get("test_id") in order:
        order = order[:order.index(test["test_id"])]
    prior = [current[tid] for tid in order if current[tid].get("contract_id") == contract["contract_id"]]
    bad = []
    if len(prior) >= contract["stop_rules"]["max_attempts"]:
        bad.append("attempt_limit_reached")
    if any(verdict_of(t) == "quality_fell" for t in prior):
        bad.append("quality_stop_triggered")
    costs = [t.get("test_cost_usd") for t in prior]
    costs += [t.get(w, {}).get("usd") for t in prior for w in ("before", "after")]
    if any(not finite_nonnegative(v) for v in costs):
        bad.append("prior_cost_unknown")
    spent = sum(v for v in costs if finite_nonnegative(v))
    if spent >= contract["budget_usd"]:
        bad.append("budget_exhausted")
    if test:
        if test.get("sample") != sorted(contract["sample"], key=lambda item: item["id"]):
            bad.append("executed_sample_not_matched_to_pins")
        if test["candidate_ids"] != sorted(contract["candidate_ids"]) or test["unit_of_work"] != contract["unit_of_work"] or test["matched_on"] != contract["matched_on"]:
            bad.append("workload_differs_from_contract")
        for arm in (test["before"], test["after"]):
            if sum(arm.get("quality", {}).values()) < contract["quality_condition"]["min_reviewed"]:
                bad.append("quality_sample_incomplete")
        if test["after"].get("measurement_ref") not in contract["result_paths"]:
            bad.append("result_location_differs")
        if test["before"].get("measurement_ref") != contract["baseline"]["measurement_ref"]:
            bad.append("baseline_differs")
        total = [test.get("test_cost_usd"), test["before"].get("usd"), test["after"].get("usd")]
        if any(not finite_nonnegative(v) for v in total) or spent + sum(v for v in total if finite_nonnegative(v)) > contract["budget_usd"]:
            bad.append("cost_unknown_or_budget_exceeded")
    return sorted(set(bad))


def cmd_test_gate(ctx, a):
    contract = ctx.current("contracts.jsonl", "contract_id").get(a.contract)
    if not contract:
        raise Refusal("unknown contract " + a.contract)
    gaps = contract_gaps(ctx, contract)
    state = registration_status(ctx, contract, a.registration_commit, now())
    if state != "preregistered":
        gaps.append("registration_" + state)
    if gaps:
        raise Refusal("test stopped: " + ", ".join(gaps))
    print("test gate passed: " + contract["contract_id"] + "; advisory budget is not spending authorization")
    return 0


def parse_kv(s, what):
    out = {}
    for part in (s or "").split(","):
        if not part.strip():
            continue
        k, _, v = part.partition("=")
        k = k.strip()
        if not KEY_RE.match(k):
            raise Refusal("%s: bad cause key %r (lowercase letters, digits, underscore)" % (what, k))
        try:
            out[k] = float(v)
        except ValueError:
            raise Refusal("%s: %s needs a number" % (what, k))
    return out


def arm(a, which):
    usd, units = getattr(a, which + "_usd"), getattr(a, which + "_units")
    if usd is None or units is None:
        raise Refusal("a test needs MEASURED %s_usd and %s_units; estimates are not accepted" % (which, which))
    if not getattr(a, which + "_session"):
        raise Refusal("a test needs the %s arm's measured session id(s) (--%s-session); typed-in totals are not accepted"
                      % (which, which))
    if not finite_nonnegative(units) or not finite_nonnegative(usd) or units <= 0:
        raise Refusal("%s: units must be > 0 and usd >= 0" % which)
    q = {}
    acc, rej = getattr(a, which + "_accepted"), getattr(a, which + "_rejected")
    if acc is not None or rej is not None:
        if acc is None or rej is None or min(acc, rej) < 0:
            raise Refusal("both nonnegative accepted and rejected counts are required when quality is supplied")
        q = {"accepted": acc, "rejected": rej}
    return {"session_ids": getattr(a, which + "_session") or [], "usd": round(usd, 4), "usd_basis": a.usd_basis,
            "units": units, "usd_per_unit": round(usd / units, 6), "quality": q,
            "measurement_ref": getattr(a, which + "_measurement_ref"),
            "cost_coverage": "complete" if a.complete_costs else "unknown",
            "included_phases": list(COST_PHASES) if a.complete_costs else []}


def cmd_add_test(ctx, a):
    cands = ctx.current("candidates.jsonl", "candidate_id")
    ids = list(a.candidate or [])
    if not ids and a.saver_key:
        ids = [c["candidate_id"] for c in cands.values()
               if c.get("saver_key") == a.saver_key and c.get("status") in ("unverified", "test_proposed")]
    if not ids:
        raise Refusal("no candidates to test (pass --candidate C-... or --saver-key)")
    for i in ids:
        if i not in cands:
            raise Refusal("unknown candidate " + i)
        if cands[i].get("status") not in ("unverified", "test_proposed"):
            raise Refusal("%s is %s; only unverified or test_proposed candidates are tested" % (i, cands[i].get("status")))
    for i in ids:
        try:
            validate_contract(cands[i])
        except ValueError as e:
            raise Refusal(str(e))
        contract = cands[i].get("test_contract")
        if contract and contract["unit_of_work"] != a.unit_of_work:
            raise Refusal("test unit does not match prospective contract")
    keys = {cands[i]["saver_key"] for i in ids}
    if len(keys) != 1:
        raise Refusal("one test covers one saver_key; got %s" % sorted(keys))
    saver_key = keys.pop()
    before, after = arm(a, "before"), arm(a, "after")
    if set(before["session_ids"]) & set(after["session_ids"]):
        raise Refusal("the same session cannot be both arms")
    reused = {s for t in ctx.rows("tests.jsonl") for s in (t.get("after") or {}).get("session_ids", [])} & set(after["session_ids"])
    if reused:
        raise Refusal("after-arm session(s) already used by another test; one measured saving counts once: %s" % sorted(reused))
    if a.test_cost_usd is not None and not finite_nonnegative(a.test_cost_usd):
        raise Refusal("--test-cost-usd must be finite and nonnegative, or omitted when unknown")
    waste = {}
    if a.waste_before or a.waste_after:
        waste = {"before": parse_kv(a.waste_before, "waste-before"), "after": parse_kv(a.waste_after, "waste-after")}
    prior = [t for t in ctx.rows("tests.jsonl") if saver_key == t.get("saver_key") and t.get("rev", 0) == 0]
    n_inconclusive = sum(1 for t in prior if verdict_of(t) == "inconclusive")
    test_id = ctx.next_id("T", "tests.jsonl", "test_id")()
    rec = {"schema": "junto.test/1", "test_id": test_id, "rev": 0, "candidate_ids": sorted(ids), "saver_key": saver_key,
           "phase": "measured", "unit_of_work": a.unit_of_work, "before": before, "after": after,
           "matched_on": a.matched_on or "", "test_cost_usd": round(a.test_cost_usd, 2) if a.test_cost_usd is not None else None, "waste": waste,
           "usd_basis": a.usd_basis, "contract_id": a.contract,
           "evidence_scope": "quality_checked_pilot", "deployment_supported": False,
           "uncertainty": {"before_n": sum(before["quality"].values()) or None,
                           "after_n": sum(after["quality"].values()) or None,
                           "before_rejection_rate_95pct_interval": rejection_interval(before["quality"]),
                           "after_rejection_rate_95pct_interval": rejection_interval(after["quality"]),
                           "cost_replicates": 1, "cost_confidence_interval": None,
                           "note": "One matched comparison cannot establish broad deployment effects."},
           "quality_measured": bool(before["quality"] and after["quality"]),
           "unpredicted_waste": None, "written_at": now(), "written_by": WRITTEN_BY}
    if a.sample_manifest:
        sample = read_record(a.sample_manifest).get("sample")
        if not isinstance(sample, list) or any(not isinstance(x, dict) or not isinstance(x.get("id"), str) for x in sample):
            raise Refusal("sample manifest must contain a sample list with member ids and hashes")
        rec["sample"] = sorted(sample, key=lambda item: item["id"])
        rec["sample_manifest_sha256"] = hashlib.sha256(Path(a.sample_manifest).read_bytes()).hexdigest()
    if a.contract:
        contract = ctx.current("contracts.jsonl", "contract_id").get(a.contract)
        if not contract:
            raise Refusal("unknown contract " + a.contract)
        rec["registration_status"] = registration_status(ctx, contract, a.registration_commit, a.measurement_started_at)
        rec["registration_commit"] = a.registration_commit
        rec["measurement_started_at"] = a.measurement_started_at
        rec["contract_violations"] = contract_gaps(ctx, contract, rec)
        if rec["contract_violations"]:
            rec["registration_status"] = "contract_conditions_unmet"
    else:
        rec["registration_status"] = "retrospective_pilot"
    rec["measurement_gaps"] = measurement_gaps(rec)
    rec["verdict"] = verdict_of(rec)
    rec["quality_measured"] = quality_ok(rec) is not None
    rec["evidence_scope"] = "quality_checked_pilot" if rec["verdict"] == "saves" else "unverified_observation"
    rec["delta_usd_per_unit"] = round(arm_ppu(before) - arm_ppu(after), 6)
    new_status = {"saves": "verified", "no_saving": "refuted", "quality_fell": "refuted"}.get(rec["verdict"], "test_proposed")
    if rec["verdict"] == "inconclusive":  # one retest; a second inconclusive is refuted
        new_status = "refuted" if n_inconclusive >= 1 else "test_proposed"
    ctx.append("tests.jsonl", [rec])
    vid = None
    if rec["verdict"] == "saves":
        fs = test_finders(ctx, rec, cands)
        vid = ctx.next_id("V", "verified_savings.jsonl", "verified_id")()
        saved = round(delta_usd_saved(rec), 2)
        ctx.append("verified_savings.jsonl", [{
            "schema": "junto.verified/1", "verified_id": vid, "rev": 0, "test_id": test_id, "saver_key": saver_key,
            "candidate_ids": sorted(ids), "kind": "test_realized", "usd_saved": saved, "usd_basis": a.usd_basis,
            "evidence_scope": "quality_checked_pilot", "deployment_supported": False,
            "measurement": {"before_usd_per_unit": before["usd_per_unit"], "after_usd_per_unit": after["usd_per_unit"],
                            "units": after["units"], "session_ids": before["session_ids"] + after["session_ids"]},
            "credited_to": [{"finder_id": f, "share": round(1 / len(fs), 4)} for f in fs],
            "written_at": now(), "written_by": WRITTEN_BY}])
    ctx.append("candidates.jsonl", [dict(cands[i], rev=cands[i].get("rev", 0) + 1, status=new_status,
                                         status_ref=vid or test_id, written_at=now(), written_by=WRITTEN_BY) for i in sorted(ids)])
    print("%s %s: %s; before %.4f/unit, after %.4f/unit; candidates now %s%s" % (
        test_id, saver_key, rec["verdict"], before["usd_per_unit"], after["usd_per_unit"], new_status,
        ("; verified %s usd_saved %.2f" % (vid, saved)) if vid else ""))
    return 0


# ---------------------------------------------------------------- propose (blind spots)
def cmd_propose(ctx, a):
    cfg = ctx.config
    predicted = set()
    for f in ctx.finders():
        predicted.update(f.get("targets", []))
    for c in ctx.current("candidates.jsonl", "candidate_id").values():
        predicted.update(c.get("targets", []))
    tests = ctx.current("tests.jsonl", "test_id")
    props = ctx.current("finder_proposals.jsonl", "proposal_id")
    open_keys = {p["cause_key"] for p in props.values() if p.get("status") in ("open", "accepted")}
    new_p = ctx.next_id("P", "finder_proposals.jsonl", "proposal_id")
    made, out_lines = [], []
    for tid in sorted(tests):
        t = tests[tid]
        if a.test and tid != a.test:
            continue
        if not test_valid(t) or not t.get("waste") or t.get("unpredicted_waste") is not None:
            continue
        wb, wa = t["waste"].get("before", {}), t["waste"].get("after", {})
        tb, ta = float(t["before"]["usd"]), float(t["after"]["usd"])
        unpredicted = []
        for k in sorted(set(wb) | set(wa)):
            b, af = float(wb.get(k, 0.0)), float(wa.get(k, 0.0))
            share = max(b / tb if tb > 0 else 0.0, af / ta if ta > 0 else 0.0)
            rise = (af - b) / b if b > 0 else (float("inf") if af > 0 else 0.0)
            is_waste = share >= cfg["waste_share_of_session"] or max(b, af) >= cfg["waste_usd"] \
                or (rise >= cfg["waste_rise"] and af - b >= cfg["waste_min_rise_usd"])
            if is_waste and k not in predicted:
                arm_name = "after" if af > b else "before"
                unpredicted.append({"cause_key": k, "usd": round(max(b, af), 2), "share": round(share, 4), "arm": arm_name,
                                    "rise": None if rise == float("inf") else round(rise, 3)})
        if a.dry_run:
            out_lines.append("%s: %d unpredicted" % (tid, len(unpredicted)) + "".join(" %s($%.2f)" % (u["cause_key"], u["usd"]) for u in unpredicted))
            continue
        for u in unpredicted:
            if u["cause_key"] in open_keys:
                continue
            open_keys.add(u["cause_key"])
            pid = new_p()
            made.append({"schema": "junto.finder_proposal/1", "proposal_id": pid, "rev": 0, "test_id": tid,
                         "cause_key": u["cause_key"],
                         "evidence": {"session_ids": t["before"]["session_ids"] + t["after"]["session_ids"], "usd": u["usd"],
                                      "share": u["share"], "arm": u["arm"], "rise": u["rise"]},
                         "suggested_finder": {"name": u["cause_key"] + "_miner",
                                              "looks_for": "audited sessions where %s costs at least %d%% of the session or $%.2f, and which saver would cut it"
                                                           % (u["cause_key"], int(cfg["waste_share_of_session"] * 100), cfg["waste_usd"])},
                         "status": "open", "written_at": now(), "written_by": WRITTEN_BY})
        ctx.append("tests.jsonl", [dict(t, rev=t.get("rev", 0) + 1, unpredicted_waste=[u["cause_key"] for u in unpredicted],
                                        written_at=now(), written_by=WRITTEN_BY)])
        out_lines.append("%s: %d unpredicted waste key(s)" % (tid, len(unpredicted)) + "".join(" %s" % u["cause_key"] for u in unpredicted))
    if made:
        ctx.append("finder_proposals.jsonl", made)
    for p in made:
        out_lines.append("proposal %s: build %s for cause %s ($%.2f)" % (p["proposal_id"], p["suggested_finder"]["name"], p["cause_key"], p["evidence"]["usd"]))
    print("\n".join(out_lines[:20]) or "no tests with waste data to examine")
    return 0


# ---------------------------------------------------------------- score / allocate / check
def cmd_score(ctx, a):
    row, total = compute(ctx)
    write_scoreboard(ctx, row, total)
    for r in sorted(row.values(), key=lambda r: (-(r["score"] or 0), r["finder_id"])):
        print("%s %s known token value %.2f; total %s; pilot savings %.2f; score %s" % (
            r["finder_id"], r["state"], r["known_spent_usd"], r["spent_usd"], r["verified_usd"], r["score"]))
    print("junto token value: verified pilot %.2f; known expense %.2f; total %s; unknown records %d" % (
        total["verified_usd"], total["known_spent_usd"], total["spent_usd"], total["unknown_cost_records"]))
    return 0


def cmd_allocate(ctx, a):
    row, total = compute(ctx)
    budget = a.budget if a.budget is not None else float(ctx.config["round_budget_usd"])
    alloc, unspent = allocate_plan(ctx, row, budget, a.round)
    write_scoreboard(ctx, row, total, alloc, {"allocation": {"round": a.round, "budget_usd": round(budget, 2),
                                                             "unallocated_usd": round(unspent, 2)}})
    for fid, v in sorted(alloc.items(), key=lambda kv: (-kv[1], kv[0])):
        print("%-20s %-9s allowance $%.2f" % (fid, row[fid]["state"], v))
    print("budget $%.2f, unallocated $%.2f" % (budget, unspent))
    return 0


def cmd_check(ctx, a):
    errs = []
    fins = {f["finder_id"] for f in ctx.finders()}
    cur_tests = ctx.current("tests.jsonl", "test_id")
    for name, idk in (("runs.jsonl", "run_id"), ("candidates.jsonl", "candidate_id"), ("tests.jsonl", "test_id"),
                      ("verified_savings.jsonl", "verified_id"), ("finder_proposals.jsonl", "proposal_id"),
                      ("contracts.jsonl", "contract_id")):
        for i, r in enumerate(ctx.rows(name), 1):
            for k in ("schema", idk, "rev", "written_at", "written_by"):
                if k not in r:
                    errs.append("%s:%d missing %s" % (name, i, k))
            errs += ["%s:%d %s" % (name, i, b) for b in privacy_problems(r)]
            if name == "candidates.jsonl" and r.get("rev") == 0 and r.get("status") != "unverified":
                errs.append("%s:%d first line must be unverified" % (name, i))
            if name == "candidates.jsonl":
                try:
                    validate_contract(r)
                except ValueError as e:
                    errs.append(str(e))
            if name == "candidates.jsonl" and r.get("finder_id") not in fins and origin_kind(r) not in ("owner", "agent"):
                errs.append("%s:%d unregistered finder" % (name, i))
            if name == "contracts.jsonl":
                errs += ["%s:%d %s" % (name, i, problem) for problem in contract_problems(r)]
            if name == "verified_savings.jsonl" and not test_valid(cur_tests.get(r.get("test_id"))):
                errs.append("%s:%d verified saving without a measured test" % (name, i))
    good = {v["verified_id"] for v, _, _ in valid_verified_lines(ctx)}
    for v in ctx.rows("verified_savings.jsonl"):
        if v.get("verified_id") not in good:
            errs.append("verified line %s fails the test rule (not 'saves', over the measured delta, or duplicate)" % v.get("verified_id"))
    for c in ctx.current("candidates.jsonl", "candidate_id").values():
        if c.get("status") == "verified" and c.get("status_ref") not in good:
            errs.append("candidate %s is verified without a valid verified line" % c.get("candidate_id"))
    print("\n".join(errs[:20]) if errs else "ledger ok")
    return 2 if errs else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ledger", help="ledger dir (default jobs/junto/ledger)")
    ap.add_argument("--output", help="output dir (default jobs/junto/output)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run registered finders over a data dir")
    r.add_argument("--data", required=True, help="dir OUTSIDE the repo with saved transcripts pages and session totals")
    r.add_argument("--profiles", help="dir of Hamilton PROFILE_*.json")
    r.add_argument("--finder", action="append", help="only this finder (name or id); repeatable")
    r.add_argument("--usd-spent", type=float, help="what this run cost (get_session cost delta); split equally over finders run")
    r.add_argument("--usd-basis", help="get_session.cost_usd | actions_minutes | local_script")
    r.add_argument("--round-id")
    r.add_argument("--force", action="store_true", help="rerun even if same data+version already ran")
    t = sub.add_parser("add-test", help="record a measured before/after test")
    t.add_argument("--saver-key")
    t.add_argument("--candidate", action="append", help="candidate id; repeatable (default: all open ones with the saver key)")
    t.add_argument("--unit-of-work", required=True, help="e.g. accepted_claim, merged_pr, completed_phase")
    t.add_argument("--usd-basis", choices=("api_token_value", "cash_charge"), default="api_token_value")
    t.add_argument("--complete-costs", action="store_true", help="receipt totals cover production, build, coordination, monitoring, review, rework, integration")
    t.add_argument("--contract", help="frozen prospective contract id; omitted means retrospective pilot")
    t.add_argument("--registration-commit", help="40-character commit containing the frozen contract before execution")
    t.add_argument("--measurement-started-at", help="UTC ISO timestamp from the measurement receipt")
    t.add_argument("--sample-manifest", help="aggregate JSON identifying the sample actually used; required for contract credit")
    for w in ("before", "after"):
        t.add_argument("--%s-usd" % w, type=float, help="MEASURED total cost of the %s arm" % w)
        t.add_argument("--%s-units" % w, type=float, help="units of work done in the %s arm" % w)
        t.add_argument("--%s-session" % w, action="append", help="session id; repeatable")
        t.add_argument("--%s-accepted" % w, type=int)
        t.add_argument("--%s-rejected" % w, type=int)
        t.add_argument("--%s-measurement-ref" % w, help="aggregate measurement receipt location; never raw transcript text")
    t.add_argument("--test-cost-usd", type=float, help="additional test overhead OUTSIDE arm totals; omitted means unknown")
    t.add_argument("--matched-on", help="what was held fixed")
    t.add_argument("--waste-before", help="measured cost by cause key, e.g. model_writes=2.1,tool_output=1.5")
    t.add_argument("--waste-after", help="same, for the after arm")
    sub.add_parser("score", help="verified USD saved / (USD spent + prior), per finder")
    al = sub.add_parser("allocate", help="effort shares for one meeting")
    al.add_argument("--budget", type=float)
    al.add_argument("--round", type=int, default=1)
    p = sub.add_parser("propose", help="blind-spot step: propose finders for unpredicted waste")
    p.add_argument("--test")
    p.add_argument("--dry-run", action="store_true")
    sub.add_parser("check", help="validate the ledger")
    seed = sub.add_parser("seed-candidate", help="append an owner/agent supplied candidate without finder invention credit")
    seed.add_argument("--file", required=True, help="validated aggregate candidate JSON")
    contract = sub.add_parser("register-test", help="freeze a prospective test contract before execution")
    contract.add_argument("--file", required=True, help="contract JSON with sample pins, baseline, quality, budget, stops, results")
    gate = sub.add_parser("test-gate", help="exit nonzero unless prospective registration, budget and stop rules permit another attempt")
    gate.add_argument("--contract", required=True)
    gate.add_argument("--registration-commit", required=True)
    a = ap.parse_args(argv)
    ctx = Ctx(a.ledger, a.output)
    try:
        return {"run": cmd_run, "add-test": cmd_add_test, "score": cmd_score, "allocate": cmd_allocate,
                "propose": cmd_propose, "check": cmd_check, "seed-candidate": cmd_seed_candidate,
                "register-test": cmd_register_test, "test-gate": cmd_test_gate}[a.cmd](ctx, a)
    except Refusal as e:
        print("junto: %s" % e, file=sys.stderr)
        return e.code


if __name__ == "__main__":
    sys.exit(main())
