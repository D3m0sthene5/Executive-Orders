"""Llull tests (standard library only).  Run:  python3 -I jobs/llull/test_llull.py

Core claims proved here:
  1. a forecast whose reference class has no measured base rate is refused (and `check` fails on an
     unmeasured seeded row);
  2. a forecast above the Domesday census ceiling is flagged and not registered without --accept-flag;
  3. the Brier, interval-score and Murphy-decomposition math is right;
  plus: proxy units are refused, outcomes need a committed source, the shipped census reproduces the
  postmortem pool sizes, and the premortem fails a structured plan whose number exceeds the ceiling.
"""
import contextlib, io, json, math, shutil, subprocess, sys, tempfile, unittest
sys.dont_write_bytecode = True
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import llull  # noqa: E402

SEED = Path(__file__).resolve().parent / "ledger"
CENSUS = {"census_id": "D-test-1", "pool": "Y2", "pool_size": 2000, "ceiling_strict": 60, "ceiling_leads": 400}


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = llull.main(list(argv))
    return code, out.getvalue(), err.getvalue()


def jl(path):
    return llull.read_jsonl(path)


def seed_ledger(led):
    """Copy the shipped seeds. Base-rate rows sourced from the shipped ledger's own outcomes are dropped: the test
    ledger has no such outcomes."""
    for n in ("postmortems.json", "pools.json"):
        shutil.copy(SEED / n, led / n)
    d = json.loads((SEED / "base_rates.json").read_text())
    d["rows"] = [r for r in d["rows"] if not llull.OUTCOME_ID_RE.match(r["source"])]
    (led / "base_rates.json").write_text(json.dumps(d))


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.led = self.tmp / "ledger"
        self.led.mkdir()
        seed_ledger(self.led)
        llull.append_jsonl(self.led / "censuses.jsonl", dict(CENSUS))
        self.args = ["--ledger", str(self.led)]

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def fc(self, *extra):
        return run(*self.args, "forecast", "--plan-id", "T1", "--planner", "claude:test", *extra)


class TestUnmeasuredRefused(Base):
    def test_unknown_class_refused(self):
        code, _, err = self.fc("--quantity", "upheld_per_attempt", "--p10", "0.0", "--p50", "0.5", "--p90", "1.0",
                               "--reference-class", "upheld_per_attempt.nothing_measured_here")
        self.assertEqual(code, 2)
        self.assertIn("no measured base rate", err)
        self.assertEqual(jl(self.led / "forecasts.jsonl"), [])

    def test_row_without_value_or_source_is_unmeasured(self):
        for bad in ({"key": "k", "value": None, "source": "x"}, {"key": "k", "value": 0.5, "source": ""},
                    {"key": "k", "value": 0.5, "source": "x", "num": 1, "den": 4}, {"key": "k", "value": "0.5", "source": "x"}):
            self.assertIsNotNone(llull.measured_problem(bad), bad)
        self.assertIsNone(llull.measured_problem({"key": "k", "value": 0.25, "source": "x", "num": 1, "den": 4}))
        # an invented row put in the ledger's base_rates.json is refused by forecast and by check
        d = json.loads((self.led / "base_rates.json").read_text())
        d["rows"].append({"key": "hit_rate.invented", "pool": "none", "unit": "share", "value": None,
                          "source": "", "n_studies": 0, "postmortem_id": "P17"})
        (self.led / "base_rates.json").write_text(json.dumps(d))
        code, _, err = self.fc("--quantity", "hit_rate", "--p10", "0.0", "--p50", "0.85", "--p90", "1.0",
                               "--reference-class", "hit_rate.invented")
        self.assertEqual(code, 2)
        self.assertIn("value is not a measured number", err)
        self.assertEqual(run(*self.args, "check")[0], 4)

    def test_new_class_needs_reason_and_wide_interval(self):
        base = ["--quantity", "accepted_items", "--p10", "40", "--p50", "50", "--p90", "60", "--reference-class", "new:x"]
        self.assertEqual(self.fc(*base)[0], 2)                                    # no reason
        code, _, err = self.fc(*base, "--reason", "no data")
        self.assertEqual(code, 2)                                                 # too narrow: needs [0.1x, 2x]
        self.assertIn("fewer than 3 studies", err)
        code, out, _ = self.fc("--quantity", "accepted_items", "--p10", "2", "--p50", "20", "--p90", "50",
                               "--reference-class", "new:x", "--reason", "no data", "--census-id", "D-test-1")
        self.assertEqual(code, 0)
        self.assertIn("0.036", out)                                               # shrunk-by-measured-miss-ratio note

    def test_shipped_base_rates_are_all_measured_with_real_sources(self):
        rates = llull.load_base_rates(SEED / "base_rates.json")
        self.assertGreaterEqual(len(rates), 15)
        for k, r in rates.items():
            self.assertIsNone(llull.measured_problem(r), k)
            if not r["source"].startswith("jobs/llull/") and not llull.OUTCOME_ID_RE.match(r["source"]):
                self.assertIsNone(llull.repo_path_ok(r["source"]), k)
        self.assertAlmostEqual(rates["upheld_per_attempt.modern_claim_no_held_end"]["value"], 0.06)
        self.assertAlmostEqual(rates["measured_over_forecast.all_misses"]["value"], 0.036)

    def test_shipped_ledger_checks_clean(self):
        code, out, _ = run("check")
        self.assertEqual(code, 0, out)


class TestCeiling(Base):
    Q = ["--quantity", "upheld_per_attempt", "--reference-class", "upheld_per_attempt.modern_claim_no_held_end"]

    def test_flag_function(self):
        # 0.5 is above both the strict share (60/2000 = 3%) and the leads share (400/2000 = 20%)
        self.assertIn("PREREQUISITE_COVERAGE_EXCEEDED_EVEN_COUNTING_LEADS", llull.ceiling_flags("upheld_per_attempt", 0.5, CENSUS))
        self.assertEqual(llull.ceiling_flags("upheld_per_attempt", 0.1, CENSUS), ["PREREQUISITE_COVERAGE_EXCEEDED"])   # above 3%, below 20%
        self.assertEqual(llull.ceiling_flags("upheld_per_attempt", 0.03, CENSUS), [])                    # at the ceiling
        self.assertEqual(llull.ceiling_flags("ready_orders_gained", 61, CENSUS), ["PREREQUISITE_COVERAGE_EXCEEDED"])    # counts: 60
        self.assertEqual(llull.ceiling_flags("ready_orders_gained", 60, CENSUS), [])
        self.assertEqual(llull.ceiling_flags("ready_orders_gained", 100, CENSUS, unlock_p90=40), [])      # unlock step adds room
        self.assertEqual(llull.ceiling_flags("usd_total", 10 ** 9, CENSUS), [])                           # costs are not capped

    def test_forecast_above_ceiling_is_flagged_and_not_registered(self):
        code, out, _ = self.fc(*self.Q, "--p10", "0.0", "--p50", "0.5", "--p90", "1.0", "--deviation", "hoped",
                               "--census-id", "D-test-1")
        self.assertEqual(code, 3)
        self.assertIn("PREREQUISITE_COVERAGE_EXCEEDED", out)
        self.assertEqual(jl(self.led / "forecasts.jsonl"), [])

    def test_accepted_flag_stays_on_the_record(self):
        code, _, _ = self.fc(*self.Q, "--p10", "0.0", "--p50", "0.5", "--p90", "1.0", "--deviation", "hoped",
                             "--census-id", "D-test-1", "--accept-flag", "owner wants the original target kept visible")
        self.assertEqual(code, 0)
        rec = jl(self.led / "forecasts.jsonl")[0]
        self.assertIn("PREREQUISITE_COVERAGE_EXCEEDED", rec["flags"])
        self.assertEqual(rec["census_ceiling"]["ceiling_strict"], 60)
        self.assertEqual(run(*self.args, "check")[0], 0)

    def test_forecast_inside_ceiling_registers_clean(self):
        code, _, _ = self.fc(*self.Q, "--p10", "0.0", "--p50", "0.015", "--p90", "0.03", "--deviation", "capped at the ceiling",
                             "--census-id", "D-test-1")
        self.assertEqual(code, 0)
        self.assertEqual(jl(self.led / "forecasts.jsonl")[0]["flags"], [])

    def test_proxy_units_refused(self):
        for q in ("payload_tokens_saved", "bytes", "certificates"):
            code, _, err = self.fc("--quantity", q, "--p10", "0", "--p50", "1", "--p90", "2", "--reference-class", "new:x",
                                   "--reason", "r")
            self.assertEqual(code, 2, q)
            self.assertIn("not an allowed outcome unit", err)

    def test_p50_far_from_outside_view_needs_deviation(self):
        base = ["--quantity", "upheld_per_attempt", "--reference-class", "upheld_per_attempt.modern_claim_no_held_end",
                "--p10", "0.0", "--p50", "0.5", "--p90", "1.0"]
        code, _, err = self.fc(*base)
        self.assertEqual(code, 2)
        self.assertIn("deviation", err)


class TestReviewFixes(Base):
    def test_rate_interval_must_be_a_share(self):
        code, _, err = self.fc("--quantity", "hit_rate", "--p10", "0.085", "--p50", "0.85", "--p90", "1.7",
                               "--reference-class", "new:x", "--reason", "r")
        self.assertEqual(code, 2)
        self.assertIn("must lie in [0, 1]", err)
        # the widening rule stops at 1 for shares: [0.085, 1.0] is wide enough for p50 0.85
        code, _, _ = self.fc("--quantity", "hit_rate", "--p10", "0.085", "--p50", "0.85", "--p90", "1.0",
                             "--reference-class", "new:x", "--reason", "r", "--accept-flag", "no census")
        self.assertEqual(code, 0)

    def test_wrong_binaries_are_not_calibrated(self):
        for i in range(5):
            run(*self.args, "forecast", "--plan-id", "T%d" % i, "--planner", "claude:b", "--quantity", "upheld_per_attempt",
                "--event", "upheld >= 0.5", "--prob", "0.9", "--reference-class", "upheld_per_attempt.modern_claim_no_held_end")
        for f in jl(self.led / "forecasts.jsonl"):
            run(*self.args, "outcome", "--forecast", f["forecast_id"], "--measured", "0", "--source", "research/plans/LLULL_DESIGN.md")
        with patch.object(llull, "registration_status", return_value=("preregistered", "verified fixture")):
            run(*self.args, "score")
        e = json.loads((self.tmp / "output" / "CALIBRATION.json").read_text())["planners"]["claude:b"]
        self.assertAlmostEqual(e["brier"], 0.81)
        self.assertEqual(e["trust"], "unproven")  # five metrics share one underlying experiment
        self.assertEqual(e["n_experiments"], 1)

    def test_check_fails_a_quote_missing_from_its_source(self):
        d = json.loads((self.led / "base_rates.json").read_text())
        row = next(r for r in d["rows"] if r["key"] == "hit_rate.type_tribunal")
        row["evidence"] = [{"source": row["source"], "quote": "hit rate 0.85 (an invented number)"}]
        (self.led / "base_rates.json").write_text(json.dumps(d))
        code, out, _ = run(*self.args, "check")
        self.assertEqual(code, 4)
        self.assertIn("not found in", out)


class TestOutcomeAndScore(Base):
    def register(self, **kw):
        a = ["--quantity", "accepted_items", "--p10", "2", "--p50", "20", "--p90", "50", "--reference-class", "new:t",
             "--reason", "none", "--census-id", "D-test-1"]
        return self.fc(*a)

    def test_outcome_needs_repo_source_and_is_once_only(self):
        self.register()
        fid = jl(self.led / "forecasts.jsonl")[0]["forecast_id"]
        args = [*self.args, "outcome", "--forecast", fid, "--measured", "3"]
        self.assertEqual(run(*args, "--source", "/etc/passwd")[0], 2)
        self.assertEqual(run(*args, "--source", "no/such/file.md")[0], 2)
        self.assertEqual(run(*args, "--source", "research/plans/LLULL_DESIGN.md")[0], 0)
        self.assertEqual(run(*args, "--source", "research/plans/LLULL_DESIGN.md")[0], 2)

    def test_score_per_planner(self):
        self.register()
        fid = jl(self.led / "forecasts.jsonl")[0]["forecast_id"]
        run(*self.args, "outcome", "--forecast", fid, "--measured", "3", "--source", "research/plans/LLULL_DESIGN.md")
        with patch.object(llull, "registration_status", return_value=("preregistered", "verified fixture")):
            self.assertEqual(run(*self.args, "score")[0], 0)
        cal = json.loads((self.tmp / "output" / "CALIBRATION.json").read_text())
        e = cal["planners"]["claude:test"]
        self.assertEqual(e["coverage_p10_p90"], 1.0)              # 3 is inside [2, 50]
        self.assertEqual(e["trust"], "unproven")                  # fewer than 5 resolved
        self.assertAlmostEqual(e["median_log_ratio"], math.log(3 / 20))
        self.assertAlmostEqual(e["mean_norm_interval_score"], 48 / 3)               # width 48, outcome inside, over y = 3


class TestMath(unittest.TestCase):
    def test_brier(self):
        self.assertAlmostEqual(llull.brier([1.0], [1]), 0.0)
        self.assertAlmostEqual(llull.brier([0.0], [1]), 1.0)
        self.assertAlmostEqual(llull.brier([0.5, 0.5], [1, 0]), 0.25)
        self.assertAlmostEqual(llull.brier([0.8, 0.2, 0.9], [1, 0, 0]), (0.04 + 0.04 + 0.81) / 3)
        with self.assertRaises(ValueError):
            llull.brier([], [])

    def test_interval_score(self):
        self.assertAlmostEqual(llull.interval_score(10, 20, 15), 10)                 # inside: just the width
        self.assertAlmostEqual(llull.interval_score(10, 20, 5), 10 + 10 * 5)         # (2/0.2) x miss distance
        self.assertAlmostEqual(llull.interval_score(10, 20, 26), 10 + 10 * 6)
        self.assertAlmostEqual(llull.norm_interval_score(10, 20, 5, "count"), 60 / 5)
        self.assertAlmostEqual(llull.norm_interval_score(0.0, 0.5, 0.06, "rate"), 0.5 / 0.06)

    def test_log_ratio_floors_zero_outcomes(self):
        self.assertAlmostEqual(llull.log_ratio(0, 50, "count"), math.log(0.5 / 50))
        self.assertAlmostEqual(llull.log_ratio(6, 3, "count"), math.log(2))

    def test_murphy_identity(self):
        probs = [0.1] * 10 + [0.9] * 10
        outs = [1] + [0] * 9 + [1] * 8 + [0] * 2
        m = llull.murphy(probs, outs)
        self.assertAlmostEqual(llull.brier(probs, outs), m["reliability"] - m["resolution"] + m["uncertainty"])
        self.assertAlmostEqual(m["uncertainty"], 0.45 * 0.55)                         # base rate 9/20
        self.assertAlmostEqual(m["reliability"], 0.5 * (0.9 - 0.8) ** 2)             # only the 0.9 bin is off (0.8 observed)

    def test_evsi_is_bounded_by_evpi_and_nonnegative(self):
        a, b = 3.0, 17.0
        util = lambda q: 100 * (q - 0.2)
        v0, v1, evsi = llull.evsi_probe(20, a, b, util)
        ev = llull.evpi(a, b, util)
        self.assertGreaterEqual(evsi, 0.0)
        self.assertLessEqual(evsi, ev + 1e-6)
        self.assertGreater(ev, 0.0)
        self.assertAlmostEqual(llull.evsi_probe(0, a, b, util)[2], 0.0)             # an empty probe tells nothing


class TestCensusAndWheel(unittest.TestCase):
    INPUTS = ["jobs/readiness-tracker/output/READINESS_BY_ORDER.csv", "jobs/claim-kit/output",
              "jobs/current-law/output/ORDERS_CURRENT_LAW.csv", "jobs/status-history/output/INDEX.json",
              "jobs/later-events/output/CATALOG_INDEX.csv"]
    KEEP = ("READINESS_BY_ORDER.csv", "ACTING_PROVISIONS", "OWN_TERMS", "ORDERS_CURRENT_LAW.csv", "INDEX.json",
            "CATALOG_INDEX.csv")

    def materialise(self, commit, d):
        """The census inputs exactly as committed at `commit` (git show), so the test does not drift with the data."""
        names = (llull.git("ls-tree", "-r", "--name-only", commit, "--", *self.INPUTS) or "").split()
        for n in names:
            if Path(n).name.startswith(self.KEEP):
                result = subprocess.run(["git", "-C", str(llull.REPO), "show", "%s:%s" % (commit, n)], capture_output=True)
                if result.returncode:
                    self.skipTest("historical census blob unavailable in this sparse clone: " + n)
                blob = result.stdout
                (d / n).parent.mkdir(parents=True, exist_ok=True)
                (d / n).write_bytes(blob)
        return llull.Data(repo=d)

    def test_recorded_censuses_reproduce_at_their_commit(self):
        recs = [c for c in jl(SEED / "censuses.jsonl") if c.get("gates_rev") == llull.GATES_REV]
        latest = {c["pool"]: c for c in recs if c["pool"] in ("Y1", "Y2", "X1")}   # built-in pools; custom ones are recorded too
        self.assertEqual(set(latest), {"Y1", "Y2", "X1"})
        commit = {c["commit"] for c in latest.values()}
        if len(commit) != 1 or llull.git("cat-file", "-t", next(iter(commit))) != "commit":
            self.skipTest("census commit not available in this clone")
        d = Path(tempfile.mkdtemp())
        try:
            D = self.materialise(next(iter(commit)), d)
            for pool, rec in latest.items():
                c = llull.run_census(pool, rec["requires"], D)
                self.assertEqual((c["pool_size"], c["ceiling_strict"], c["ceiling_leads"]),
                                 (rec["pool_size"], rec["ceiling_strict"], rec["ceiling_leads"]), pool)
        finally:
            shutil.rmtree(d, ignore_errors=True)
        y1, y2, x1 = latest["Y1"], latest["Y2"], latest["X1"]
        self.assertEqual((y1["pool_size"], y1["ceiling_strict"]), (4274, 3952))      # funnel plan: 4,274; 3,952 with text
        self.assertEqual(x1["ceiling_strict"], 32)                                   # the postmortem's "32 by EO<7532 today"
        self.assertLess(y2["ceiling_strict"] / y2["pool_size"], 0.05)                # ~2%, against a 50% target
        self.assertLess(y2["ceiling_leads"] / y2["pool_size"], 0.25)                 # ~18% even counting leads

    def test_ending_gate_needs_an_ending_verb_and_whole_scope(self):
        D = llull.Data()
        D._c["acting"] = ({"EO:9001"}, {"EO:9001", "EO:9002"})
        D._c["term"] = {"EO:9003"}
        row = lambda i: {"instrument_id": i, "provisional_status": "no"}
        self.assertEqual([llull.g_ending_instrument(row(i), D) for i in ("EO:9001", "EO:9002", "EO:9003", "EO:9004")],
                         ["held", "no", "held", "no"])
        d = Path(tempfile.mkdtemp())
        try:
            (d / "jobs/claim-kit/output").mkdir(parents=True)
            acts = [{"names_target": True, "target_id": "EO:1", "scope": "whole", "effective_date": "1950-01-01", "verb": "revoke"},
                    {"names_target": True, "target_id": "EO:2", "scope": "whole", "effective_date": "1950-01-01", "verb": "transfer"},
                    {"names_target": True, "target_id": "EO:3", "scope": "partial", "effective_date": "1950-01-01", "verb": "revoke"}]
            terms = [{"instrument_id": "EO:4", "scope_id": "EO:4#whole", "computed_end_candidate": "1950-01-01"},
                     {"instrument_id": "EO:5", "scope_id": "EO:5#sec4-b", "computed_end_candidate": "1950-01-01"}]
            (d / "jobs/claim-kit/output/ACTING_PROVISIONS.jsonl").write_text("".join(json.dumps(a) + "\n" for a in acts))
            (d / "jobs/claim-kit/output/OWN_TERMS.jsonl").write_text("".join(json.dumps(t) + "\n" for t in terms))
            D2 = llull.Data(repo=d)
            self.assertEqual(D2.acting()[0], {"EO:1"})
            self.assertEqual(D2.term_end(), {"EO:4"})
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_joint_is_not_the_product(self):
        D = llull.Data()
        D._c["tracker"] = []
        rows = [{"instrument_id": "EO:%d" % (8000 + i), "provisional_status": "yes", "step_original_text": "done" if i < 5 else "open",
                 "ready_for_human_review": "no", "claim_present": "no"} for i in range(10)]
        c = llull.run_census("Y2", ["status_present", "original_text_held"], D, rows=rows)
        self.assertEqual((c["ceiling_strict"], c["pool_size"]), (5, 10))

    def test_wheel_fails_a_structured_plan_that_exceeds_the_ceiling(self):
        census = dict(CENSUS)
        spec = {"plan_id": "t", "steps": [{"step": "get 250 claims accepted", "requires": ["status_present"]},
                                           {"step": "fetch a thing", "requires": ["no_such_gate"]}]}
        d = Path(tempfile.mkdtemp())
        try:
            p = d / "plan.json"
            p.write_text(json.dumps(spec))
            w = llull.run_wheel(p, census)
            fails = [c for c in w["questions"] if c["state"] == "auto_fail"]
            self.assertTrue(any("above the Y2 observed joint prerequisite coverage of 60" in c["evidence"] and c["state"] == "fires" for c in w["questions"]))
            self.assertTrue(any("not a registered gate" in c["evidence"] for c in fails))
            self.assertLessEqual(len(w["questions"]), 12)
            self.assertEqual(w["questions"][0]["state"], "auto_fail")
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_rank_refuses_unmeasured_inputs_and_runs_measuring_checks_first(self):
        rates = llull.load_base_rates(SEED / "base_rates.json")
        cen = {"Y2": {"pool_size": 2000, "ceiling_strict": 200, "ceiling_leads": 400}}
        run_a = {"id": "run", "tier": "run", "pool": "Y2", "reference_class": "upheld_per_attempt.modern_claim_no_held_end",
                 "n_attempts": 200, "ready_per_success": 0.5, "ready_per_success_source": "x", "cost_per_attempt": 1.0,
                 "cost_source": "x"}
        probe = dict(run_a, id="probe", tier="probe", informs="run", n_attempts=30)
        bad = dict(run_a, id="bad", ready_per_success=None)
        zero = {"id": "measure", "tier": "zero_agent", "informs": "run", "measures": "ready_per_success"}
        spec = {"planning": {"max_cost_per_ready": 10}, "actions": [run_a, probe, bad, zero]}
        ranked, unranked = llull.rank_actions(spec, rates, cen)
        self.assertEqual([u["id"] for u in unranked], ["bad"])
        self.assertEqual(ranked[0]["id"], "measure")
        self.assertEqual({r["id"] for r in ranked}, {"measure", "run", "probe"})


# ---------------------------------------------------------------- repairs found on first use (2026-10-20)

def tracker_row(i, **kw):
    row = {"instrument_id": "EO:%d" % i, "provisional_status": "", "ready_for_human_review": "no", "claim_present": "no",
           "step_original_text": "done", "step_ending_or_current_basis": "open", "step_clause_inventory": "open"}
    row.update(kw)
    return row


class TestCustomPools(Base):
    def pools_file(self, pools):
        p = self.tmp / "pools.json"
        p.write_text(json.dumps({"pools": pools}))
        return p

    def data(self, rows):
        D = llull.Data()
        D._c["tracker"] = rows
        return D

    def test_custom_pool_filters_and_builtin_pools_survive(self):
        rows = [tracker_row(8000 + i, provisional_status="no" if i < 6 else "yes", claim_present="yes" if i % 2 else "no")
                for i in range(10)] + [tracker_row(100 + i) for i in range(4)]
        pools = llull.load_pools(self.pools_file({
            "CLM": {"title": "claims", "where": {"claim_present": "yes"}, "default_requires": ["status_present"]},
            "CLM_NO": {"title": "claims, NO", "from": "CLM", "where": {"provisional_status": "no"},
                       "default_requires": ["original_text_held"]},
            "OLD": {"title": "old", "eo_lt": 7532, "default_requires": ["original_text_held"]},
            "NOT_NO": {"title": "x", "where": {"provisional_status": {"not": "no"}}, "eo_gte": 7532,
                       "default_requires": ["status_present"]}}))
        D = self.data(rows)
        c = llull.run_census("CLM", pools=pools, D=D)
        self.assertEqual((c["pool_size"], c["ceiling_strict"], c["pool_kind"]), (5, 5, "custom"))
        self.assertEqual(c["pool_def"]["where"], {"claim_present": "yes"})          # the definition travels with the record
        self.assertEqual(llull.run_census("CLM_NO", pools=pools, D=D)["pool_size"], 3)    # from another pool
        self.assertEqual(llull.run_census("OLD", pools=pools, D=D)["pool_size"], 4)
        self.assertEqual(llull.run_census("NOT_NO", pools=pools, D=D)["pool_size"], 4)
        self.assertEqual(llull.run_census("X1", D=D)["pool_size"], 4)               # built-ins still work
        self.assertEqual(llull.run_census("Y2", D=D)["pool_size"], 5)               # status yes/no, text, no claim

    def test_open_steps_and_gate_states_filters(self):
        rows = [tracker_row(8000, step_ending_or_current_basis="open", step_clause_inventory="done"),
                tracker_row(8001), tracker_row(8002, step_ending_or_current_basis="done", step_clause_inventory="done")]
        pools = llull.load_pools(self.pools_file({
            "LAST": {"title": "one open", "open_steps_max": 1, "default_requires": ["original_text_held"]},
            "DONE": {"title": "ending done", "gate_states": {"ending_step_done": ["held"]},
                     "default_requires": ["original_text_held"]}}))
        D = self.data(rows)
        self.assertEqual(llull.run_census("LAST", pools=pools, D=D)["pool_size"], 2)   # 8000 has 1 open, 8002 has 0
        self.assertEqual(llull.run_census("DONE", pools=pools, D=D)["pool_size"], 1)

    def test_pools_file_cannot_redefine_builtin_or_use_unknown_keys(self):
        for bad in ({"Y2": {"title": "x", "default_requires": ["status_present"]}},
                    {"Z": {"title": "x", "default_requires": ["status_present"], "sql": "select"}},
                    {"Z": {"title": "x", "default_requires": ["no_such_gate"]}}, {"Z": {"title": "x"}}):
            with self.assertRaises(llull.Refusal):
                llull.load_pools(self.pools_file(bad))
        with self.assertRaises(llull.Refusal):
            llull.run_census("NOPE", ["status_present"], llull.Data(), pools={})

    def test_cli_census_records_a_custom_pool(self):
        pf = self.pools_file({"LAST": {"title": "one open", "where": {"claim_present": "yes", "ready_for_human_review": "no"},
                                       "open_steps_max": 1, "default_requires": ["original_text_held"]}})
        code, out, _ = run(*self.args, "--pools", str(pf), "census", "--pool", "LAST", "--record")
        self.assertEqual(code, 0, out)
        rec = jl(self.led / "censuses.jsonl")[-1]
        self.assertEqual((rec["pool"], rec["pool_kind"]), ("LAST", "custom"))
        self.assertIn("pool_def", rec)
        code, out, _ = run(*self.args, "--pools", str(pf), "census", "--list")
        self.assertIn("[custom]", out)
        self.assertEqual(run(*self.args, "--pools", str(pf), "census", "--pool", "NOPE")[0], 2)

    def test_shipped_pools_load_and_craigellachie_pool_is_23(self):
        pools = llull.load_pools(SEED / "pools.json")
        self.assertTrue({"CRAIG", "NEAR", "Y2LEAD", "X1S", "X1T"} <= set(pools))
        self.assertEqual(llull.run_census("CRAIG", pools=pools)["pool_size"], 23)


class TestRankUsesTheRatesOwnPopulation(unittest.TestCase):
    def setUp(self):
        self.rates = {"upheld_per_attempt.x": {"key": "upheld_per_attempt.x", "value": 0.06, "num": 3, "den": 50,
                                               "source": "s", "population": "Y2"},
                      "upheld_per_attempt.nopop": {"key": "upheld_per_attempt.nopop", "value": 0.06, "num": 3, "den": 50,
                                                   "source": "s"}}
        self.cen = {"Y2": {"pool_size": 2000, "ceiling_strict": 40, "ceiling_leads": 400},
                    "Y2LEAD": {"pool_size": 400, "ceiling_strict": 40, "ceiling_leads": 400}}

    def run_one(self, pool, rc="upheld_per_attempt.x"):
        run_a = {"id": "run", "tier": "run", "pool": pool, "reference_class": rc, "n_attempts": 500, "ready_per_success": 1.0,
                 "ready_per_success_source": "x", "cost_per_attempt": 1.0, "cost_source": "x"}
        ranked, un = llull.rank_actions({"planning": {"max_cost_per_ready": 60}, "actions": [run_a]}, self.rates, self.cen)
        self.assertEqual(un, [])
        return ranked[0]

    def test_same_pool_as_the_rate_takes_no_census_share(self):
        r = self.run_one("Y2")
        self.assertEqual(r["share"], 1.0)
        self.assertAlmostEqual(r["e_ready"], 500 * 0.06, places=6)        # the rate already contains the gate failures
        self.assertIn("already inside the rate", r["share_basis"])

    def test_a_richer_sub_pool_is_not_discounted_below_the_rate(self):
        # Y2LEAD holds its prerequisites 5x as often as Y2 (0.1 vs 0.02). Multiplying the Y2 rate by Y2LEAD's own
        # share (the repair's first version) cut E_ready 10x for the BETTER pool; the ratio, capped at 1, keeps the rate
        r = self.run_one("Y2LEAD")
        self.assertEqual(r["share"], 1.0)
        self.assertAlmostEqual(r["e_ready"], 500 * 0.06, places=6)
        self.assertIn("capped at 1", r["share_basis"])

    def test_a_poorer_pool_is_discounted_by_the_share_ratio(self):
        self.cen["POOR"] = {"pool_size": 1000, "ceiling_strict": 4, "ceiling_leads": 10}
        r = self.run_one("POOR")
        self.assertAlmostEqual(r["share"], 0.004 / 0.02)
        self.assertAlmostEqual(r["e_ready"], 500 * 0.2 * 0.06, places=6)
        self.assertIn("rate's population Y2", r["share_basis"])

    def test_zero_share_population_is_unranked(self):
        self.cen["Y2"] = {"pool_size": 2000, "ceiling_strict": 0, "ceiling_leads": 400}
        run_a = {"id": "run", "tier": "run", "pool": "Y2LEAD", "reference_class": "upheld_per_attempt.x", "n_attempts": 5,
                 "ready_per_success": 1.0, "ready_per_success_source": "x", "cost_per_attempt": 1.0, "cost_source": "x"}
        ranked, un = llull.rank_actions({"planning": {"max_cost_per_ready": 60}, "actions": [run_a]}, self.rates, self.cen)
        self.assertEqual(ranked, [])
        self.assertIn("undefined", un[0]["reasons"][0])

    def test_hand_worked_example(self):
        # Bowditch Y2: 3 of 50 upheld on random Y2 draws -> Beta(3, 47), q0 = 0.06. Run 500 attempts on Y2 at
        # 0.924 min each, 1 ready per success: E_ready = 500 * 1.0 * 1 * 0.06 = 30; cost 462; rank 30/462.
        # Probe 50 at the same cost: E_ready 3, cost 46.2. util(q) = 500 (q - 0.924/60) > 0 for every posterior mean
        # (3 + x)/100 >= 0.03 > 0.0154, so no probe result changes the decision: EVSI = 0.
        self.cen["Y2"] = {"pool_size": 2060, "ceiling_strict": 38, "ceiling_leads": 363}
        run_a = {"id": "run", "tier": "run", "pool": "Y2", "reference_class": "upheld_per_attempt.x", "n_attempts": 500,
                 "ready_per_success": 1.0, "ready_per_success_source": "x", "cost_per_attempt": 0.924, "cost_source": "x"}
        probe = dict(run_a, id="probe", tier="probe", informs="run", n_attempts=50)
        ranked, un = llull.rank_actions({"planning": {"max_cost_per_ready": 60}, "actions": [run_a, probe]}, self.rates, self.cen)
        got = {r["id"]: r for r in ranked}
        self.assertEqual(un, [])
        self.assertAlmostEqual(got["run"]["e_ready"], 30.0, places=9)
        self.assertAlmostEqual(got["run"]["rank"], 30 / 462, places=9)
        self.assertAlmostEqual(got["probe"]["e_ready"], 3.0, places=9)
        self.assertAlmostEqual(got["probe"]["evsi"], 0.0, places=9)
        self.assertAlmostEqual(got["probe"]["rank"], 3 / 46.2, places=9)

    def test_x1_pilot_rates_are_not_labelled_random_x1_draws(self):
        # the X1 pilot ran only the 52 orders with status and held text: labelling its rates "X1" would give an X1
        # action share 1.0, overstating E_ready ~250x (8,032 / 32), the inverse of the 55x defect
        rows = llull.load_base_rates(SEED / "base_rates.json")
        for k in ("rejected_per_submitted.x1_pilot", "hit_rate.type_tribunal", "hit_rate.extinction_event"):
            self.assertNotEqual(rows[k].get("population"), "X1", k)
        self.assertEqual(rows["eligible_share.pre1937_orders"]["population"], "X1")   # this one is a share OF X1

    def test_unrecorded_population_falls_back_to_the_census_share(self):
        r = self.run_one("Y2", "upheld_per_attempt.nopop")
        self.assertAlmostEqual(r["share"], 0.02)
        self.assertIn("unrecorded population", r["share_basis"])

    def test_old_55x_undercount_is_gone(self):
        # strict share 38/2060 = 1.8% applied to a rate measured on random Y2 draws cut E_ready ~55x
        self.cen["Y2"] = {"pool_size": 2060, "ceiling_strict": 38, "ceiling_leads": 363}
        self.assertAlmostEqual(self.run_one("Y2")["e_ready"] / (500 * 0.06), 1.0, places=6)


class TestOutcomeBaseRates(Base):
    def setUp(self):
        super().setUp()
        self.fc("--quantity", "upheld_per_attempt", "--p10", "0.0", "--p50", "0.03", "--p90", "0.1", "--deviation", "x",
                "--reference-class", "upheld_per_attempt.modern_claim_no_held_end", "--census-id", "D-test-1",
                "--accept-flag", "test")
        self.fid = jl(self.led / "forecasts.jsonl")[0]["forecast_id"]
        self.src = "research/plans/LLULL_DESIGN.md"

    def outcome(self, v):
        self.assertEqual(run(*self.args, "outcome", "--forecast", self.fid, "--measured", str(v), "--source", self.src)[0], 0)
        return jl(self.led / "outcomes.jsonl")[-1]["outcome_id"]

    def baserate(self, oid, *extra, key="upheld_per_attempt.llull_t"):
        return run(*self.args, "baserate", "--outcome", oid, "--key", key, "--population", "Y2", "--pool-desc", "t", *extra)

    def test_outcome_becomes_a_base_rate_with_the_outcome_id_as_source(self):
        oid = self.outcome(0.0)
        code, out, err = self.baserate(oid, "--num", "0", "--den", "23")
        self.assertEqual(code, 0, err)
        row = llull.load_base_rates(self.led / "base_rates.json")["upheld_per_attempt.llull_t"]
        self.assertEqual((row["source"], row["value"], row["population"]), (oid, 0.0, "Y2"))
        self.assertIsNone(llull.measured_problem(row))
        self.assertEqual(run(*self.args, "check")[0], 0)
        # and it is usable as a reference class (no postmortem, no quoted file needed)
        code, _, err = self.fc("--quantity", "upheld_per_attempt", "--p10", "0", "--p50", "0.0", "--p90", "0.03",
                               "--reference-class", "upheld_per_attempt.llull_t", "--census-id", "D-test-1")
        self.assertEqual(code, 0, err)

    def test_refusals(self):
        oid = self.outcome(0.06)
        self.assertEqual(self.baserate("O-20260101-9")[0], 2)                                   # unknown outcome
        self.assertEqual(self.baserate(oid, "--num", "1", "--den", "50")[0], 2)                 # num/den != measured
        self.assertEqual(self.baserate(oid, key="hit_rate.llull_t")[0], 2)                      # wrong quantity
        self.assertEqual(self.baserate(oid, "--num", "3", "--den", "50")[0], 0)
        self.assertEqual(self.baserate(oid, "--num", "3", "--den", "50")[0], 2)                 # duplicate key
        self.assertEqual(run(*self.args, "baserate", "--outcome", oid, "--key", "upheld_per_attempt.z", "--population",
                             "NOPE", "--pool-desc", "t")[0], 2)                                 # unknown population

    def test_check_fails_when_the_row_disagrees_with_its_outcome(self):
        oid = self.outcome(0.06)
        self.assertEqual(self.baserate(oid, "--num", "3", "--den", "50")[0], 0)
        d = json.loads((self.led / "base_rates.json").read_text())
        row = next(r for r in d["rows"] if r["key"] == "upheld_per_attempt.llull_t")
        row.update(value=0.5, num=1, den=2)
        (self.led / "base_rates.json").write_text(json.dumps(d))
        code, out, _ = run(*self.args, "check")
        self.assertEqual(code, 4)
        self.assertIn("outcome %s measured 0.06" % oid, out)

    def test_check_rejects_old_identifiers_left_inside_derived_from(self):
        oid = self.outcome(0.06)
        self.assertEqual(self.baserate(oid, "--num", "3", "--den", "50")[0], 0)
        d = json.loads((self.led / "base_rates.json").read_text())
        row = next(r for r in d["rows"] if r["key"] == "upheld_per_attempt.llull_t")
        self.assertEqual(llull.outcome_rate_problems(row["key"], row, llull.Ledger(self.led)), [])
        correct = dict(row["derived_from"])
        for field, value in (("outcome_id", "O-20260101-999"), ("forecast_id", "L-20260101-999")):
            row["derived_from"] = {**correct, field: value}
            (self.led / "base_rates.json").write_text(json.dumps(d))
            code, out, _ = run(*self.args, "check")
            self.assertEqual(code, 4)
            self.assertIn("derived_from identifiers disagree", out)

    def test_binary_outcomes_are_not_rates(self):
        run(*self.args, "forecast", "--plan-id", "B", "--planner", "claude:t", "--quantity", "upheld_per_attempt", "--event",
            "e", "--prob", "0.3", "--reference-class", "upheld_per_attempt.modern_claim_no_held_end")
        fid = jl(self.led / "forecasts.jsonl")[-1]["forecast_id"]
        run(*self.args, "outcome", "--forecast", fid, "--measured", "0", "--source", self.src)
        oid = jl(self.led / "outcomes.jsonl")[-1]["outcome_id"]
        self.assertEqual(self.baserate(oid)[0], 2)


def git_commit(root, files):
    """Write {path: text} under root and commit them together in a throwaway git repository."""
    root = Path(root)
    if not (root / ".git").exists():
        subprocess.run(["git", "init", "-q", str(root)], check=True)
    for path, text in files.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(text)
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.email=t@t.t", "-c", "user.name=t", "commit", "-q", "-m", "c"], check=True)


class TestNotPreregistered(unittest.TestCase):
    """The forecast and its run committed together (or the run first) cannot be proven forecast-first: the entry is
    marked not_preregistered and left out of scoring, and `check` does not fail."""
    FC = "jobs/llull/ledger/forecasts.jsonl"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.old = llull.REPO
        llull.REPO = self.tmp.resolve()
        self.led = self.tmp / "jobs/llull/ledger"
        self.led.mkdir(parents=True)
        shutil.copy(SEED / "postmortems.json", self.led / "postmortems.json")
        (self.led / "base_rates.json").write_text(json.dumps({"rows": []}))   # the seed rows cite files absent from this repo
        self.args = ["--ledger", str(self.led)]

    def tearDown(self):
        llull.REPO = self.old
        shutil.rmtree(self.tmp, ignore_errors=True)

    def forecast(self, fid, run_dir):
        return {"forecast_id": fid, "rev": 1, "kind": "interval", "quantity": "accepted_items", "p10": 1.0, "p50": 5.0,
                "p90": 9.0, "reference_class": "new:t", "flags": [], "planner": {"agent": "a", "model": "m"},
                "run_dirs": [run_dir] if run_dir else [], "registered_commit": "x"}

    def outcome(self, fid, oid, v=7.0):
        return {"outcome_id": oid, "forecast_id": fid, "measured": v, "source": "runs/%s/OUT.json" % fid}

    def lines(self, *recs):
        return "".join(json.dumps(r) + "\n" for r in recs)

    def test_together_is_marked_not_failed_and_excluded_from_scoring(self):
        f1, f2 = self.forecast("L-1", "runs/L-1"), self.forecast("L-2", "runs/L-2")
        (self.led / "outcomes.jsonl").write_text(self.lines(self.outcome("L-1", "O-1"), self.outcome("L-2", "O-2")))
        git_commit(self.tmp, {self.FC: self.lines(f1)})                                    # L-1 forecast first
        git_commit(self.tmp, {"runs/L-1/OUT.json": "{}"})                                  # then its run
        git_commit(self.tmp, {self.FC: self.lines(f1, f2), "runs/L-2/OUT.json": "{}"})     # L-2: together
        led = llull.Ledger(self.led)
        self.assertEqual(llull.registration_status(f1, led)[0], "preregistered")
        st, why = llull.registration_status(f2, led)
        self.assertEqual(st, "not_preregistered", why)
        code, out, _ = run(*self.args, "check")
        self.assertEqual(code, 0, out)                                  # not a failure
        self.assertIn("not_preregistered: L-2", out)
        self.assertNotIn("not_preregistered: L-1:", out)
        self.assertEqual(run(*self.args, "check", "--mark")[0], 0)
        self.assertEqual([m["forecast_id"] for m in jl(self.led / "registration.jsonl")], ["L-2"])
        run(*self.args, "check", "--mark")
        self.assertEqual(len(jl(self.led / "registration.jsonl")), 1)  # marking is idempotent
        res = llull.score_all(led)
        self.assertEqual((res["n_resolved"], res["n_scored"]), (2, 1))
        self.assertIn("L-2", res["not_preregistered_excluded"])
        self.assertEqual(res["planners"]["a:m"]["n_interval"], 1)       # only the preregistered forecast is scored

    def test_run_committed_before_the_forecast_is_not_preregistered(self):
        f = self.forecast("L-5", "runs/L-5")
        git_commit(self.tmp, {"runs/L-5/OUT.json": "{}"})
        git_commit(self.tmp, {self.FC: self.lines(f)})
        self.assertEqual(llull.registration_status(f, llull.Ledger(self.led))[0], "not_preregistered")
        self.assertEqual(run(*self.args, "check")[0], 0)

    def test_outcome_file_committed_with_the_forecast_is_not_preregistered(self):
        f = self.forecast("L-3", "")
        f["run_dirs"] = []
        (self.led / "outcomes.jsonl").write_text(self.lines(self.outcome("L-3", "O-3")))
        git_commit(self.tmp, {self.FC: self.lines(f), "runs/L-3/OUT.json": "{}"})
        self.assertEqual(llull.registration_status(f, llull.Ledger(self.led))[0], "not_preregistered")
        self.assertEqual(run(*self.args, "check")[0], 0)

    def test_uncommitted_forecast_is_unchecked_and_excluded(self):
        git_commit(self.tmp, {"README": "x"})
        f = self.forecast("L-4", "runs/L-4")
        (self.led / "forecasts.jsonl").write_text(self.lines(f))
        self.assertEqual(llull.registration_status(f, llull.Ledger(self.led))[0], "unchecked")
        (self.led / "outcomes.jsonl").write_text(self.lines(self.outcome("L-4", "O-4")))
        scored = llull.score_all(llull.Ledger(self.led))
        self.assertEqual(scored["n_scored"], 0)
        self.assertIn("L-4", scored["unchecked_excluded"])

    def test_committed_forecast_with_uncommitted_run_is_unchecked(self):
        f = self.forecast("L-4", "runs/L-4")
        git_commit(self.tmp, {self.FC: self.lines(f)})
        self.assertEqual(llull.registration_status(f, llull.Ledger(self.led))[0], "unchecked")

    def test_post_run_forecast_revision_cannot_borrow_original_registration(self):
        f = self.forecast("L-4", "runs/L-4")
        git_commit(self.tmp, {self.FC: self.lines(f)})
        git_commit(self.tmp, {"runs/L-4/OUT.json": "{}"})
        revised = dict(f, p50=7.0)
        git_commit(self.tmp, {self.FC: self.lines(revised)})
        (self.led / "outcomes.jsonl").write_text(self.lines(self.outcome("L-4", "O-4")))
        ledger = llull.Ledger(self.led)
        self.assertEqual(llull.registration_status(revised, ledger)[0], "unchecked")
        self.assertEqual(llull.score_all(ledger)["n_scored"], 0)

    def test_outcome_source_before_forecast_is_retrospective(self):
        f = self.forecast("L-4", "runs/L-4")
        git_commit(self.tmp, {"old-result.json": "{}"})
        git_commit(self.tmp, {self.FC: self.lines(f)})
        git_commit(self.tmp, {"runs/L-4/OUT.json": "{}"})
        o = self.outcome("L-4", "O-4")
        o["source"] = "old-result.json"
        (self.led / "outcomes.jsonl").write_text(self.lines(o))
        self.assertEqual(llull.registration_status(f, llull.Ledger(self.led))[0], "not_preregistered")


class TestOutcomeCorrections(Base):
    def setUp(self):
        super().setUp()
        self.L = llull.Ledger(self.led)
        self.f = {"forecast_id": "F", "rev": 1, "kind": "interval", "quantity": "hit_rate",
                  "p10": 0.03, "p50": 0.3, "p90": 0.6, "planner": {"agent": "a", "model": "m"}, "flags": []}
        llull.append_jsonl(self.L.forecasts, self.f)

    def test_correction_appends_and_current_score_uses_adjudicated_value(self):
        args = [*self.args, "outcome", "--forecast", "F", "--source", "research/plans/LLULL_DESIGN.md"]
        self.assertEqual(run(*args, "--measured", "0.8")[0], 0)
        original = jl(self.L.outcomes)[0]
        self.assertEqual(run(*args, "--corrects", original["outcome_id"], "--correction-reason", "wrong clause credit",
                             "--measured", "0.7", "--experiment-id", "single-probe")[0], 0)
        rows = jl(self.L.outcomes)
        self.assertEqual(rows[0], original)
        self.assertEqual(len(rows), 2)
        self.assertEqual(llull.current_outcomes(self.L)["F"]["measured"], 0.7)
        with patch.object(llull, "registration_status", return_value=("preregistered", "verified fixture")):
            cal = llull.score_all(self.L)
        self.assertEqual((cal["n_outcome_records"], cal["n_current_outcomes"], cal["n_scored"]), (2, 1, 1))
        self.assertAlmostEqual(cal["planners"]["a:m"]["median_log_ratio"], math.log(0.7 / 0.3))

    def test_incomplete_gate_correction_is_untested_not_zero_or_one(self):
        args = [*self.args, "outcome", "--forecast", "F", "--source", "research/plans/LLULL_DESIGN.md"]
        run(*args, "--measured", "1")
        oid = jl(self.L.outcomes)[0]["outcome_id"]
        code, _, err = run(*args, "--corrects", oid, "--correction-reason", "missing two of three plants",
                           "--resolution-status", "untested")
        self.assertEqual(code, 0, err)
        cal = llull.score_all(self.L)
        self.assertEqual(cal["n_scored"], 0)
        self.assertEqual(cal["unresolved_outcomes"], {"F": "untested"})
        self.assertIsNone(llull.current_outcomes(self.L)["F"]["measured"])

    def test_unlinked_or_unpinned_duplicate_outcome_is_refused(self):
        llull.append_jsonl(self.L.outcomes, {"forecast_id": "F", "outcome_id": "O-1", "measured": 0.8})
        llull.append_jsonl(self.L.outcomes, {"forecast_id": "F", "outcome_id": "O-2", "measured": 0.7})
        with self.assertRaises(llull.Refusal):
            llull.score_all(self.L)

    def test_unchecked_forecast_cannot_enter_selfscore(self):
        llull.append_jsonl(self.L.outcomes, {"forecast_id": "F", "outcome_id": "O-1", "measured": 0.8})
        scored = llull.selfscore_all(self.L, "rule", is_after=lambda _: True)
        self.assertEqual(scored["n_out_of_sample"], 0)
        self.assertEqual(scored["n_unchecked"], 1)


class TestSelfScore(Base):
    def setUp(self):
        super().setUp()
        self.registration = patch.object(llull, "registration_status", return_value=("preregistered", "verified fixture"))
        self.registration.start()
        self.addCleanup(self.registration.stop)

    def put(self, fid, flags, p10, p90, measured, commit):
        f = {"forecast_id": fid, "rev": 1, "kind": "interval", "quantity": "accepted_items", "p10": p10, "p50": (p10 + p90) / 2,
             "p90": p90, "reference_class": "new:t", "flags": flags, "planner": {"agent": "a", "model": "m"},
             "registered_commit": commit}
        llull.append_jsonl(self.led / "forecasts.jsonl", f)
        llull.append_jsonl(self.led / "outcomes.jsonl", {"outcome_id": "O-" + fid, "forecast_id": fid, "measured": measured,
                                                         "source": "research/plans/LLULL_DESIGN.md"})

    def test_only_out_of_sample_misses_count(self):
        self.put("L-1", ["PREREQUISITE_COVERAGE_EXCEEDED"], 10, 20, 0, "old")          # miss, flagged, but registered before the rule
        self.put("L-2", ["PREREQUISITE_COVERAGE_EXCEEDED"], 10, 20, 1, "new")          # miss, flagged: counts
        self.put("L-3", [], 10, 20, 2, "new")                            # miss, not flagged: counts against recall
        self.put("L-4", [], 10, 20, 15, "new")                           # not a miss
        self.put("L-5", ["NO_CENSUS_CAP"], 10, 20, 99, "new")            # miss, NO_CENSUS_CAP is not a miss warning
        res = llull.selfscore_all(llull.Ledger(self.led), "rule", is_after=lambda c: c == "new")
        self.assertEqual((res["n_in_sample"], res["n_out_of_sample"]), (1, 4))
        self.assertEqual(res["n_misses_out_of_sample"], 3)
        self.assertEqual(res["n_flagged_misses"], 1)
        self.assertAlmostEqual(res["share_flagged"], 1 / 3)
        self.assertEqual(res["trust"], "unproven")                        # fewer than 5 out-of-sample misses
        self.assertEqual([m["forecast_id"] for m in res["misses_in_sample"]], ["L-1"])

    def test_no_misses_gives_no_share_and_binary_miss_rule(self):
        res = llull.selfscore_all(llull.Ledger(self.led), "rule", is_after=lambda c: True)
        self.assertIsNone(res["share_flagged"])
        self.assertTrue(llull.is_miss({"kind": "binary", "prob": 0.7}, {"measured": 0}))
        self.assertFalse(llull.is_miss({"kind": "binary", "prob": 0.2}, {"measured": 0}))
        self.assertFalse(llull.is_miss({"kind": "binary", "prob": 0.7}, {"measured": 1}))

    def test_default_rule_compares_resolved_hashes(self):
        # registered_commit is stored short, rule_commit full: a forecast registered AT the rule commit is in-sample
        rc = llull.git("rev-parse", "HEAD")
        self.put("L-1", ["PREREQUISITE_COVERAGE_EXCEEDED"], 10, 20, 0, rc[:9])
        self.put("L-2", [], 10, 20, 0, "not-a-commit")
        res = llull.selfscore_all(llull.Ledger(self.led), rc)
        self.assertEqual((res["n_in_sample"], res["n_out_of_sample"]), (2, 0))
        parent = llull.git("rev-parse", "HEAD~1")
        if parent:
            res = llull.selfscore_all(llull.Ledger(self.led), parent)
            self.assertEqual(res["n_out_of_sample"], 1)                   # HEAD is a strict descendant of HEAD~1

    def test_cli_writes_selfscore(self):
        self.put("L-1", [], 10, 20, 0, "x")
        code, out, _ = run(*self.args, "selfscore", "--rule-commit", "deadbeef")
        self.assertEqual(code, 0, out)
        self.assertTrue((self.tmp / "output" / "SELFSCORE.json").exists())


class TestPremortemDiscriminates(unittest.TestCase):
    def wheel(self, steps, census=None, rates=None, suffix=".json"):
        d = Path(tempfile.mkdtemp())
        try:
            p = d / ("plan" + suffix)
            p.write_text(json.dumps({"steps": steps}) if suffix == ".json" else steps)
            return llull.run_wheel(p, census, rates=rates if rates is not None else llull.load_base_rates(SEED / "base_rates.json"))
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def modes(self, w):
        return {c["mode"] for c in w["questions"]}

    def test_a_clean_plan_gets_no_questions(self):
        w = self.wheel([{"step": "list the orders held in the tracker", "requires": ["status_present"]}], dict(CENSUS))
        self.assertEqual(w["questions"], [])
        self.assertEqual(w["quiet"], w["cells"])

    def test_different_plans_get_different_questions(self):
        a = self.wheel([{"step": "claim 250 upheld", "requires": ["status_present"]}], dict(CENSUS))
        b = self.wheel([{"step": "fetch pages from govinfo and say it cuts review cost", "requires": []}], dict(CENSUS))
        c = self.wheel([{"step": "report payload tokens saved", "requires": []}], dict(CENSUS))
        self.assertEqual(self.modes(a), {"UNMEASURED_PREREQUISITE"})
        self.assertIn("ACCESS_ASSUMPTION", self.modes(b))
        self.assertEqual(self.modes(c), {"PROXY_UNIT"})
        self.assertEqual(len({frozenset(self.modes(x)) for x in (a, b, c)}), 3)

    def test_every_question_has_plan_specific_evidence_and_ranks_by_past_misses(self):
        w = self.wheel([{"step": "scale to 900 upheld claims at a 50% rate, fetch govinfo", "requires": ["status_present", "original_text_held"]}],
                       dict(CENSUS, flags=["ASSUMED_INDEPENDENCE"], product_of_marginals=90.0))
        self.assertTrue(w["questions"])
        for c in w["questions"]:
            self.assertTrue(c["evidence"], c)
            self.assertIn(c["state"], ("auto_fail", "fires", "cannot_run"))
        rest = [c for c in w["questions"] if c["state"] != "auto_fail"]
        self.assertEqual([c["past_misses"] for c in rest], sorted((c["past_misses"] for c in rest), reverse=True))
        self.assertEqual(w["questions"][0]["state"], "fires")  # coverage is not a proved bound

    def test_cannot_run_when_the_check_has_no_census(self):
        w = self.wheel([{"step": "draft 500 orders as claims", "requires": []}], census=None)
        q = [c for c in w["questions"] if c["mode"] == "UNMEASURED_PREREQUISITE"]
        self.assertEqual([c["state"] for c in q], ["cannot_run"])
        self.assertIn("no census", q[0]["evidence"])

    def test_selection_bias_fires_only_on_a_population_mismatch(self):
        rates = {"upheld_per_attempt.x": {"key": "upheld_per_attempt.x", "value": 0.06, "source": "s", "population": "Y2"}}
        fires = self.wheel([{"step": "run it", "reference_class": "upheld_per_attempt.x", "pool": "X1"}], rates=rates)
        quiet = self.wheel([{"step": "run it", "reference_class": "upheld_per_attempt.x", "pool": "Y2"}], rates=rates)
        self.assertIn("SELECTION_BIAS", self.modes(fires))
        self.assertNotIn("SELECTION_BIAS", self.modes(quiet))

    def test_review_leniency_and_cost_shift_and_policy(self):
        w = self.wheel([{"step": "review claims, which saves effort", "producer_model": "claude-sonnet", "reviewer_model": "claude-opus"},
                        {"step": "review claims", "producer_model": "claude-sonnet", "reviewer_model": "gpt-9"},
                        {"step": "waive the rule if the owner approves"},
                        {"step": "waive the rule per HANDOFF/notes.md line 4", "approval": "HANDOFF/notes.md"}])
        got = {(c["mode"], c["step"]): c["state"] for c in w["questions"]}
        self.assertEqual(got[("REVIEW_LENIENCY", "review claims, which saves effort")], "fires")
        self.assertNotIn(("REVIEW_LENIENCY", "review claims"), got)       # different families: the check passes
        self.assertEqual(got[("COST_SHIFT", "review claims, which saves effort")], "fires")
        self.assertEqual(got[("POLICY_COUNTED_UNAPPROVED", "waive the rule if the owner approves")], "fires")
        self.assertNotIn(("POLICY_COUNTED_UNAPPROVED", "waive the rule per HANDOFF/notes.md line 4"), got)

    def test_prose_targets_under_a_heading_are_checked_against_the_census(self):
        # Bowditch Y2's brief stated its pass test in a paragraph under a heading; the first wheel never read it
        y2 = "## Probe pass test (funnel Y2)\nAccepted (upheld) claims per attempted order >= 50%, and rejections <= 11%.\n"
        craig = "## The pool (why these 23)\nL-1 puts upheld per attempt at p10 0.015, p50 0.15 and p90 0.35.\n"
        y1 = "## Probe measures\nReviewer disagreement <= 11% and median minutes per accepted status.\n"
        cen = dict(CENSUS)                                                # strict share 60/2000 = 3%
        for text, fires in ((y2, True), (craig, True), (y1, False)):
            w = self.wheel(text, cen, suffix=".md")
            q = [c for c in w["questions"] if c["mode"] == "UNMEASURED_PREREQUISITE"]
            self.assertEqual(bool(q), fires, (text, q))
            if q:
                self.assertIn("strict prerequisite share 3.0%", q[0]["evidence"])
        self.assertIn("0.15 (p50)", self.wheel(craig, cen, suffix=".md")["questions"][0]["evidence"])

    def test_negated_fetch_is_not_an_access_question(self):
        w = self.wheel("- Never fetch a source by hand, ever, in this plan.\n", None, suffix=".md")
        self.assertNotIn("ACCESS_ASSUMPTION", self.modes(w))
        self.assertNotIn("UNCONSIDERED_ROUTE", self.modes(w))

    def test_shipped_examples_differ(self):
        ex = Path(__file__).resolve().parent / "examples" / "plan_y2_rerun.json"
        w1 = llull.run_wheel(ex, dict(CENSUS), rates=llull.load_base_rates(SEED / "base_rates.json"))
        w2 = self.wheel([{"step": "count the orders already ready", "requires": ["status_present"]}], dict(CENSUS))
        self.assertGreater(len(w1["questions"]), 0)
        self.assertNotEqual([c["mode"] for c in w1["questions"]], [c["mode"] for c in w2["questions"]])


if __name__ == "__main__":
    unittest.main()
