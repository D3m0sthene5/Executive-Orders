"""Llull tests (standard library only).  Run:  python3 -I -m unittest jobs/llull/test_llull.py
or:  python3 -I jobs/llull/test_llull.py

Core claims proved here:
  1. a forecast whose reference class has no measured base rate is refused (and `check` fails on an
     unmeasured seeded row);
  2. a forecast above the Domesday census ceiling is flagged and not registered without --accept-flag;
  3. the Brier, interval-score and Murphy-decomposition math is right;
  plus: proxy units are refused, outcomes need a committed source, the shipped census reproduces the
  postmortem pool sizes, and the premortem fails a structured plan whose number exceeds the ceiling.
"""
import contextlib, io, json, math, shutil, sys, tempfile, unittest
sys.dont_write_bytecode = True
from pathlib import Path

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


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.led = self.tmp / "ledger"
        self.led.mkdir()
        for n in ("base_rates.json", "postmortems.json"):
            shutil.copy(SEED / n, self.led / n)
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
            if not r["source"].startswith("jobs/llull/"):
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
        self.assertIn("CEILING_EXCEEDED_EVEN_COUNTING_LEADS", llull.ceiling_flags("upheld_per_attempt", 0.5, CENSUS))
        self.assertEqual(llull.ceiling_flags("upheld_per_attempt", 0.1, CENSUS), ["CEILING_EXCEEDED"])   # above 3%, below 20%
        self.assertEqual(llull.ceiling_flags("upheld_per_attempt", 0.03, CENSUS), [])                    # at the ceiling
        self.assertEqual(llull.ceiling_flags("ready_orders_gained", 61, CENSUS), ["CEILING_EXCEEDED"])    # counts: 60
        self.assertEqual(llull.ceiling_flags("ready_orders_gained", 60, CENSUS), [])
        self.assertEqual(llull.ceiling_flags("ready_orders_gained", 100, CENSUS, unlock_p90=40), [])      # unlock step adds room
        self.assertEqual(llull.ceiling_flags("usd_total", 10 ** 9, CENSUS), [])                           # costs are not capped

    def test_forecast_above_ceiling_is_flagged_and_not_registered(self):
        code, out, _ = self.fc(*self.Q, "--p10", "0.0", "--p50", "0.5", "--p90", "1.0", "--deviation", "hoped",
                               "--census-id", "D-test-1")
        self.assertEqual(code, 3)
        self.assertIn("CEILING_EXCEEDED", out)
        self.assertEqual(jl(self.led / "forecasts.jsonl"), [])

    def test_accepted_flag_stays_on_the_record(self):
        code, _, _ = self.fc(*self.Q, "--p10", "0.0", "--p50", "0.5", "--p90", "1.0", "--deviation", "hoped",
                             "--census-id", "D-test-1", "--accept-flag", "owner wants the original target kept visible")
        self.assertEqual(code, 0)
        rec = jl(self.led / "forecasts.jsonl")[0]
        self.assertIn("CEILING_EXCEEDED", rec["flags"])
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
    def test_pools_reproduce_postmortem_counts(self):
        if not (llull.REPO / "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv").exists():
            self.skipTest("repository outputs not present")
        D = llull.Data()
        y2 = llull.run_census("Y2", D=D)
        self.assertEqual(y2["pool_size"], 2063)                                      # y2_predictor pool
        self.assertLess(y2["ceiling_strict"] / y2["pool_size"], 0.05)                # ~3%, against a 50% target
        self.assertLess(y2["ceiling_leads"] / y2["pool_size"], 0.25)                 # ~19% even counting leads
        self.assertGreater(y2["ceiling_leads"], y2["ceiling_strict"])
        self.assertEqual(llull.run_census("X1", D=D)["ceiling_strict"], 32)          # the postmortem's "32 by EO<7532 today"
        y1 = llull.run_census("Y1", D=D)
        self.assertEqual((y1["pool_size"], y1["ceiling_strict"]), (4274, 3952))      # funnel plan: 4,274; 3,952 with text

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
            self.assertTrue(any("above the Y2 joint ceiling of 60" in c["evidence"] for c in fails))
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


if __name__ == "__main__":
    unittest.main()
