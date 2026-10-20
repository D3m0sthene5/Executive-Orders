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
import argparse, hashlib, json, os, re, subprocess, sys, tempfile, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
WRITTEN_BY = "claude"
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
import math


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
    """None means unmeasured/invalid quality; it can never verify savings."""
    rates=[]
    for arm in (test.get("before",{}), test.get("after",{})):
        q=arm.get("quality") or {}
        values=[q.get("accepted"),q.get("rejected")]
        if any(type(v) is not int or v<0 for v in values) or sum(values)<=0:
            return None
        rates.append(values[1]/sum(values))
    return rates[1] <= rates[0]+1e-12


def verdict_of(test):
    """Recomputed from the two measured arms; a stored verdict is never trusted."""
    try:
        b, a = test["before"], test["after"]
        if float(b["usd"]) <= 0 or float(b["units"]) <= 0 or float(a["units"]) <= 0 or float(a["usd"]) < 0:
            return "inconclusive"
        if not all(math.isfinite(float(v)) for v in (b["usd"], b["units"], a["usd"], a["units"])):
            return None
        bp, ap = arm_ppu(b), arm_ppu(a)
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return None
    if ap <= SAVES_RATIO * bp + 1e-12:
        quality = quality_ok(test)
        return "inconclusive" if quality is None else ("saves" if quality else "quality_fell")
    if ap >= bp:
        return "no_saving"
    return "inconclusive"


def test_valid(test):
    return bool(test) and test.get("phase") == "measured" and verdict_of(test) is not None


def delta_usd_saved(test):
    return (arm_ppu(test["before"]) - arm_ppu(test["after"])) * float(test["after"]["units"])


def test_finders(ctx, test, cands=None):
    cands = cands if cands is not None else ctx.current("candidates.jsonl", "candidate_id")
    seen = []
    for cid in test.get("candidate_ids", []):
        f = (cands.get(cid) or {}).get("finder_id")
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
        if not test_valid(t) or verdict_of(t) != "saves" or v.get("kind") != "test_realized":
            continue
        if v["test_id"] in used:
            continue
        try:
            usd = float(v["usd_saved"])
        except (KeyError, TypeError, ValueError):
            continue
        if usd <= 0 or usd > delta_usd_saved(t) + 0.01:
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
    cfg = ctx.config
    fins = ctx.finders()
    cands = ctx.current("candidates.jsonl", "candidate_id")
    tests = ctx.current("tests.jsonl", "test_id")
    row = {f["finder_id"]: {"finder_id": f["finder_id"], "name": f.get("name"), "stored_state": f.get("state", "exploring"),
                            "added_at": f.get("added_at", ""), "spent_runs_usd": 0.0, "spent_tests_usd": 0.0,
                            "verified_usd": 0.0, "resolved_tests": 0, "candidates": {}} for f in fins}
    overhead = 0.0
    for r in ctx.rows("runs.jsonl"):
        usd = float(r.get("usd_spent") or 0.0)
        if r.get("finder_id") in row:
            row[r["finder_id"]]["spent_runs_usd"] += usd
        elif r.get("finder_id") == "F-junto":
            overhead += usd
    for c in cands.values():
        if c.get("finder_id") in row:
            d = row[c["finder_id"]]["candidates"]
            d[c.get("status", "unverified")] = d.get(c.get("status", "unverified"), 0) + 1
    for t in tests.values():
        if not test_valid(t):
            continue
        fs = [f for f in test_finders(ctx, t, cands) if f in row]
        if not fs:
            continue
        for f in fs:
            row[f]["spent_tests_usd"] += float(t.get("test_cost_usd") or 0.0) / len(fs)
            if verdict_of(t) in RESOLVED_VERDICTS:
                row[f]["resolved_tests"] += 1
    for v, t, fs in valid_verified_lines(ctx):
        fs = [f for f in fs if f in row]
        for f in fs:
            row[f]["verified_usd"] += float(v["usd_saved"]) / len(fs)
    s0 = float(cfg["prior_s0_usd"])
    for r in row.values():
        r["spent_usd"] = r["spent_runs_usd"] + r["spent_tests_usd"]
        r["score"] = r["verified_usd"] / (r["spent_usd"] + s0)
        if r["stored_state"] == "retired":
            r["state"] = "retired"
        elif r["resolved_tests"] < cfg["exploring_below_resolved_tests"]:
            r["state"] = "exploring"
        elif r["score"] == 0 and r["resolved_tests"] >= cfg["dormant_min_resolved_tests"] \
                and r["spent_usd"] >= cfg["dormant_min_spent_usd"]:
            r["state"] = "dormant"
        else:
            r["state"] = "scored"
    tot_ver = sum(r["verified_usd"] for r in row.values())
    tot_spent = sum(r["spent_usd"] for r in row.values()) + overhead
    return row, {"verified_usd": tot_ver, "spent_usd": tot_spent, "junto_overhead_usd": overhead,
                 "verified_per_spent": tot_ver / tot_spent if tot_spent > 0 else 0.0}


def allocate_plan(ctx, row, budget, round_no):
    cfg = ctx.config
    alloc = {k: 0.0 for k in row}
    exploring = [r for r in row.values() if r["state"] == "exploring"]
    if round_no and round_no % int(cfg["dormant_reentry_every_rounds"]) == 0:
        exploring += [r for r in row.values() if r["state"] == "dormant"]
    exploring.sort(key=lambda r: (r["added_at"], r["finder_id"]))
    exploring = exploring[:int(cfg["max_exploring_per_round"])]
    pos = [r for r in row.values() if r["state"] == "scored" and r["score"] > 0]
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
    for r in sorted(row.values(), key=lambda r: (-r["score"], r["finder_id"])):
        o = {k: (round(r[k], 4) if isinstance(r[k], float) else r[k]) for k in
             ("finder_id", "state", "spent_usd", "verified_usd", "score", "resolved_tests", "candidates")}
        if alloc is not None:
            o["allowance_usd"] = round(alloc[r["finder_id"]], 2)
        rows.append(o)
    doc = {"schema": "junto.scoreboard/1", "written_at": now(), "written_by": WRITTEN_BY,
           "note": "Derived by junto.py; never hand-edited. Only verified savings enter a score; estimates never do.",
           "formula": "score = verified_usd / (spent_usd + prior_s0_usd)", "prior_s0_usd": ctx.config["prior_s0_usd"],
           "finders": rows, "junto_total": {k: round(v, 4) for k, v in total.items()}}
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
    per_run = (a.usd_spent or 0.0) / len(fins)
    basis = a.usd_basis or ("get_session.cost_usd" if a.usd_spent else "local_script")
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
            if per_run > 0:   # the finder still ran and cost money: log it, with no candidates
                ctx.append("runs.jsonl", [{"schema": "junto.run/1", "run_id": run_id, "rev": 0, "finder_id": f["finder_id"],
                                           "finder_version": f.get("version"), "wall_seconds": wall, "data_digest": digest,
                                           "inputs": meta.get("inputs", {}), "candidates_emitted": [], "skipped_duplicate": True,
                                           "usd_spent": round(per_run, 4), "usd_basis": basis, "exit_code": 0,
                                           "round_id": a.round_id, "written_at": now(), "written_by": WRITTEN_BY}])
            summary.append("%s: skipped, same data and version already run (use --force); cost %.2f logged" % (f["name"], per_run))
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
               "inputs": meta.get("inputs", {}), "candidates_emitted": ids, "usd_spent": round(per_run, 4),
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
        summary.append("%s: exit %d, %d candidates (all unverified), usd_spent %.2f" % (f["name"], pr.returncode, len(ids), per_run))
    print("\n".join(summary[:20]))
    return status


# ---------------------------------------------------------------- add-test
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
    if not math.isfinite(units) or not math.isfinite(usd) or units <= 0 or usd < 0:
        raise Refusal("%s: units must be > 0 and usd >= 0" % which)
    q = {}
    acc, rej = getattr(a, which + "_accepted"), getattr(a, which + "_rejected")
    if acc is not None or rej is not None:
        if acc is None or rej is None or acc < 0 or rej < 0:
            raise Refusal("quality needs explicit nonnegative accepted and rejected counts in both arms")
        q = {"accepted": acc, "rejected": rej}
    return {"session_ids": getattr(a, which + "_session") or [], "usd": round(usd, 4), "usd_basis": "get_session.cost_usd",
            "units": units, "usd_per_unit": round(usd / units, 6), "quality": q}


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
    if a.test_cost_usd is None or a.test_cost_usd < 0:
        raise Refusal("--test-cost-usd is required (what the test cost Junto, 0 if nothing)")
    waste = {}
    if a.waste_before or a.waste_after:
        waste = {"before": parse_kv(a.waste_before, "waste-before"), "after": parse_kv(a.waste_after, "waste-after")}
    prior = [t for t in ctx.rows("tests.jsonl") if saver_key == t.get("saver_key") and t.get("rev", 0) == 0]
    n_inconclusive = sum(1 for t in prior if verdict_of(t) == "inconclusive")
    test_id = ctx.next_id("T", "tests.jsonl", "test_id")()
    rec = {"schema": "junto.test/1", "test_id": test_id, "rev": 0, "candidate_ids": sorted(ids), "saver_key": saver_key,
           "phase": "measured", "unit_of_work": a.unit_of_work, "before": before, "after": after,
           "matched_on": a.matched_on or "", "test_cost_usd": round(a.test_cost_usd, 2), "waste": waste,
           "quality_measured": bool(before["quality"] and after["quality"]),
           "unpredicted_waste": None, "written_at": now(), "written_by": WRITTEN_BY}
    rec["verdict"] = verdict_of(rec)
    rec["delta_usd_per_unit"] = round(arm_ppu(before) - arm_ppu(after), 6)
    new_status = {"saves": "verified", "no_saving": "refuted", "quality_fell": "refuted"}.get(rec["verdict"])
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
            "candidate_ids": sorted(ids), "kind": "test_realized", "usd_saved": saved, "usd_basis": "get_session.cost_usd",
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
    for r in sorted(row.values(), key=lambda r: (-r["score"], r["finder_id"])):
        print("%-20s %-9s spent $%6.2f verified $%6.2f score %.4f (tests resolved %d)" % (
            r["finder_id"], r["state"], r["spent_usd"], r["verified_usd"], r["score"], r["resolved_tests"]))
    print("junto total: verified $%.2f / spent $%.2f" % (total["verified_usd"], total["spent_usd"]))
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
                      ("verified_savings.jsonl", "verified_id"), ("finder_proposals.jsonl", "proposal_id")):
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
            if name == "candidates.jsonl" and r.get("finder_id") not in fins:
                errs.append("%s:%d unregistered finder" % (name, i))
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
    for w in ("before", "after"):
        t.add_argument("--%s-usd" % w, type=float, help="MEASURED total cost of the %s arm" % w)
        t.add_argument("--%s-units" % w, type=float, help="units of work done in the %s arm" % w)
        t.add_argument("--%s-session" % w, action="append", help="session id; repeatable")
        t.add_argument("--%s-accepted" % w, type=int)
        t.add_argument("--%s-rejected" % w, type=int)
    t.add_argument("--test-cost-usd", type=float, help="what the test cost Junto")
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
    a = ap.parse_args(argv)
    ctx = Ctx(a.ledger, a.output)
    try:
        return {"run": cmd_run, "add-test": cmd_add_test, "score": cmd_score, "allocate": cmd_allocate,
                "propose": cmd_propose, "check": cmd_check}[a.cmd](ctx, a)
    except Refusal as e:
        print("junto: %s" % e, file=sys.stderr)
        return e.code


if __name__ == "__main__":
    sys.exit(main())
