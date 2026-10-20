"""Junto tests (standard library only).  Run:  python3 -I -m unittest jobs/junto/test_junto.py
or:  python3 -I jobs/junto/test_junto.py

Core claims proved here:
  1. an unverified candidate never contributes to a score, however large its estimate;
  2. a verified saving requires a measured test record (a hand-written verified line is ignored
     and flagged by `check`; an estimate-only test is refused).
"""
import contextlib, io, json, os, shutil, subprocess, sys, tempfile, unittest
sys.dont_write_bytecode = True
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junto  # noqa: E402

SEED = Path(__file__).resolve().parent / "ledger"


def jl(path):
    p = Path(path)
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.led, self.out = self.tmp / "ledger", self.tmp / "output"
        self.led.mkdir()
        # Allocation examples deliberately use their three-finder fixture, not
        # whichever additional domain finders are currently registered.
        fixture=json.loads((SEED / "finders.json").read_text())
        fixture["finders"]=[f for f in fixture["finders"] if f["finder_id"] in
                            {"F-hamilton", "F-friction", "F-wasted_work"}]
        (self.led / "finders.json").write_text(json.dumps(fixture))
        for n in ("runs", "candidates", "tests", "verified_savings", "finder_proposals"):
            (self.led / (n + ".jsonl")).write_text("")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def j(self, *args):
        buf, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
            rc = junto.main(["--ledger", str(self.led), "--output", str(self.out)] + list(args))
        return rc, buf.getvalue() + err.getvalue()

    def cand(self, cid, finder, key, est=1000.0, targets=None):
        rec = {"schema": "junto.candidate/1", "candidate_id": cid, "rev": 0, "finder_id": finder, "run_id": "R-1",
               "saver_key": key, "title": "t", "targets": targets or ["coordinator_context"], "evidence": [],
               "estimate": {"usd_per_session": est, "basis": "assumed"}, "status": "unverified", "status_ref": None,
               "written_at": "2026-10-20T00:00:00Z", "written_by": "claude"}
        with open(self.led / "candidates.jsonl", "a") as fh:
            fh.write(json.dumps(rec) + "\n")

    def board(self):
        return {r["finder_id"]: r for r in json.loads((self.out / "SCOREBOARD.json").read_text())["finders"]}

    TEST = ["add-test", "--unit-of-work", "completed_phase", "--test-cost-usd", "1.00", "--before-session", "session_before",
            "--before-accepted", "2", "--before-rejected", "0", "--after-accepted", "2", "--after-rejected", "0",
            "--matched-on", "same frozen two cases and review procedure", "--complete-costs",
            "--before-measurement-ref", "measurements/before.json", "--after-measurement-ref", "measurements/after.json"]
    _n = 0

    @property
    def GOOD(self):  # each test gets a fresh measured after-arm session
        Base._n += 1
        return ["--before-usd", "20", "--before-units", "2", "--after-usd", "10", "--after-units", "2",
                "--after-session", "session_after_%d" % Base._n]


class UnverifiedNeverScores(Base):
    def test_huge_estimate_scores_zero(self):
        self.cand("C-1", "F-hamilton", "revere", est=1e9)
        self.cand("C-2", "F-friction", "preflight", est=1e6)
        rc, _ = self.j("score")
        self.assertEqual(rc, 0)
        b = self.board()
        self.assertEqual(b["F-hamilton"]["score"], 0)
        self.assertEqual(b["F-hamilton"]["verified_usd"], 0)
        self.assertEqual(b["F-friction"]["score"], 0)
        self.assertEqual(b["F-hamilton"]["candidates"], {"unverified": 1})

    def test_forged_verified_candidate_status_does_not_score(self):
        self.cand("C-1", "F-hamilton", "revere", est=500.0)
        rec = jl(self.led / "candidates.jsonl")[0]
        rec.update(rev=1, status="verified", status_ref="V-20261020-1")
        with open(self.led / "candidates.jsonl", "a") as fh:
            fh.write(json.dumps(rec) + "\n")
        self.j("score")
        self.assertEqual(self.board()["F-hamilton"]["score"], 0)
        rc, out = self.j("check")
        self.assertEqual(rc, 2)
        self.assertIn("verified without a valid verified line", out)

    def test_run_forces_unverified(self):
        fake = self.tmp / "fake_finder.py"
        fake.write_text(
            "import argparse, json\n"
            "ap = argparse.ArgumentParser()\n"
            "[ap.add_argument(f) for f in ('--data', '--out', '--run-id', '--profiles')]\n"
            "a = ap.parse_args()\n"
            "c = {'saver_key': 'x', 'title': 't', 'targets': ['coordinator_context'], 'evidence': [], 'status': 'verified',\n"
            "     'estimate': {'usd_per_session': 99999.0, 'basis': 'claimed'}}\n"
            "open(a.out, 'w').write(json.dumps(c) + '\\n')\n"
            "json.dump({'data_digest': 'd1', 'inputs': {}}, open(a.out + '.run.json', 'w'))\n")
        reg = json.loads((self.led / "finders.json").read_text())
        reg["finders"] = [dict(reg["finders"][0], script=str(fake))]
        (self.led / "finders.json").write_text(json.dumps(reg))
        data = self.tmp / "data"
        data.mkdir()
        rc, out = self.j("run", "--data", str(data), "--usd-spent", "0.50")
        self.assertEqual(rc, 0, out)
        c = jl(self.led / "candidates.jsonl")
        self.assertEqual([x["status"] for x in c], ["unverified"])
        self.assertEqual(jl(self.led / "runs.jsonl")[0]["usd_spent"], 0.5)
        self.j("score")
        self.assertEqual(self.board()["F-hamilton"]["score"], 0)
        self.assertAlmostEqual(self.board()["F-hamilton"]["spent_usd"], 0.5)

    def test_data_dir_inside_repo_refused(self):
        rc, _ = self.j("run", "--data", str(junto.ROOT))
        self.assertEqual(rc, 3)


class VerifiedNeedsTest(Base):
    def test_estimate_only_test_refused(self):
        self.cand("C-1", "F-hamilton", "revere")
        rc, out = self.j(*self.TEST, "--saver-key", "revere", "--before-usd", "20", "--before-units", "2")
        self.assertEqual(rc, 2)
        self.assertIn("MEASURED", out)
        self.assertEqual(jl(self.led / "tests.jsonl"), [])
        self.assertEqual(jl(self.led / "verified_savings.jsonl"), [])

    def test_measured_test_verifies_and_scores(self):
        self.cand("C-1", "F-hamilton", "revere")
        rc, out = self.j(*self.TEST, "--saver-key", "revere", *self.GOOD)
        self.assertEqual(rc, 0, out)
        v = jl(self.led / "verified_savings.jsonl")
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0]["usd_saved"], 10.0)  # (10 - 5 per unit) * 2 units
        self.assertTrue(v[0]["test_id"].startswith("T-"))
        cur = junto.Ctx(self.led, self.out).current("candidates.jsonl", "candidate_id")["C-1"]
        self.assertEqual(cur["status"], "verified")
        self.j("score")
        f = self.board()["F-hamilton"]
        self.assertEqual(f["verified_usd"], 10.0)
        self.assertAlmostEqual(f["spent_usd"], 31.0)           # both arms plus incremental test overhead
        self.assertAlmostEqual(f["score"], 10.0 / (31.0 + 2.0), places=3)  # verified / (spent + S0)
        self.assertEqual(self.j("check")[0], 0)

    def test_test_without_sessions_refused(self):
        self.cand("C-1", "F-hamilton", "revere")
        rc, out = self.j("add-test", "--unit-of-work", "u", "--test-cost-usd", "0", "--saver-key", "revere",
                         "--before-usd", "20", "--before-units", "2", "--after-usd", "10", "--after-units", "2")
        self.assertEqual(rc, 2)
        self.assertIn("session id", out)
        self.assertEqual(jl(self.led / "verified_savings.jsonl"), [])

    def test_same_after_session_counts_once(self):
        self.cand("C-1", "F-hamilton", "a")
        self.cand("C-2", "F-friction", "b", targets=["friction_tool_error"])
        arms = ["--before-usd", "20", "--before-units", "2", "--after-usd", "10", "--after-units", "2", "--after-session", "s_x"]
        self.assertEqual(self.j(*self.TEST, "--saver-key", "a", *arms)[0], 0)
        rc, out = self.j(*self.TEST, "--saver-key", "b", *arms)
        self.assertEqual(rc, 2)
        self.assertIn("already used", out)
        # a hand-copied verified line for a second test on the same session is not counted either
        t = jl(self.led / "tests.jsonl")[0]
        v = jl(self.led / "verified_savings.jsonl")[0]
        with open(self.led / "tests.jsonl", "a") as fh:
            fh.write(json.dumps(dict(t, test_id="T-dup", candidate_ids=["C-2"], saver_key="b")) + "\n")
        with open(self.led / "verified_savings.jsonl", "a") as fh:
            fh.write(json.dumps(dict(v, verified_id="V-dup", test_id="T-dup")) + "\n")
        self.j("score")
        self.assertEqual(self.board()["F-friction"]["verified_usd"], 0)
        self.assertEqual(self.j("check")[0], 2)

    def test_hand_written_verified_line_without_test_is_ignored(self):
        self.cand("C-1", "F-hamilton", "revere")
        with open(self.led / "verified_savings.jsonl", "a") as fh:
            fh.write(json.dumps({"schema": "junto.verified/1", "verified_id": "V-1", "rev": 0, "test_id": "T-missing",
                                 "kind": "test_realized", "usd_saved": 4134.0, "written_at": "x", "written_by": "claude"}) + "\n")
        self.j("score")
        self.assertEqual(self.board()["F-hamilton"]["verified_usd"], 0)
        rc, out = self.j("check")
        self.assertEqual(rc, 2)
        self.assertIn("without a measured test", out)

    def test_inflated_line_for_real_test_is_ignored(self):
        self.cand("C-1", "F-hamilton", "revere")
        self.j(*self.TEST, "--saver-key", "revere", *self.GOOD)
        lines = jl(self.led / "verified_savings.jsonl")
        lines[0]["usd_saved"] = 999.0
        (self.led / "verified_savings.jsonl").write_text(json.dumps(lines[0]) + "\n")
        self.j("score")
        self.assertEqual(self.board()["F-hamilton"]["verified_usd"], 0)

    def test_small_gain_is_inconclusive_and_not_verified(self):
        self.cand("C-1", "F-hamilton", "revere")
        rc, out = self.j(*self.TEST, "--saver-key", "revere", "--before-usd", "20", "--before-units", "2",
                         "--after-usd", "19", "--after-units", "2", "--after-session", "s_small")  # 5% cheaper: below the 10% rule
        self.assertIn("inconclusive", out)
        self.assertEqual(jl(self.led / "verified_savings.jsonl"), [])
        self.j("score")
        self.assertEqual(self.board()["F-hamilton"]["verified_usd"], 0)

    def test_quality_drop_blocks_verification(self):
        self.cand("C-1", "F-hamilton", "revere")
        rc, out = self.j(*self.TEST, "--saver-key", "revere", *self.GOOD, "--before-accepted", "9", "--before-rejected", "1",
                         "--after-accepted", "5", "--after-rejected", "5")
        self.assertIn("quality_fell", out)
        self.assertEqual(jl(self.led / "verified_savings.jsonl"), [])

    def test_shared_saver_key_splits_cost_and_credit(self):
        self.cand("C-1", "F-hamilton", "revere")
        self.cand("C-2", "F-friction", "revere", targets=["friction_tool_error"])
        self.j(*self.TEST, "--saver-key", "revere", *self.GOOD)
        self.j("score")
        b = self.board()
        self.assertEqual(b["F-hamilton"]["verified_usd"], 5.0)
        self.assertEqual(b["F-friction"]["verified_usd"], 5.0)
        self.assertAlmostEqual(b["F-friction"]["spent_usd"], 15.5)


class AllocationAndBlindSpots(Base):
    def test_allocate_all_exploration_when_no_score(self):
        rc, _ = self.j("allocate", "--budget", "9")
        self.assertEqual(rc, 0)
        a = {k: v["allowance_usd"] for k, v in self.board().items()}
        self.assertEqual(sorted(a.values()), [3.0, 3.0, 3.0])

    def test_allocate_splits_exploitation_by_score(self):
        # F-hamilton resolves two tests (leaves exploring) with savings; the others stay exploring.
        for i, key in enumerate(("a", "b")):
            self.cand("C-%d" % i, "F-hamilton", key)
            self.j(*self.TEST, "--saver-key", key, *self.GOOD)
        self.j("allocate", "--budget", "10")
        b = self.board()
        self.assertEqual(b["F-hamilton"]["state"], "scored")
        self.assertAlmostEqual(b["F-hamilton"]["allowance_usd"], 8.0)   # 80% exploitation
        self.assertAlmostEqual(b["F-friction"]["allowance_usd"], 1.0)   # 20% exploration, two finders
        self.assertAlmostEqual(b["F-wasted_work"]["allowance_usd"], 1.0)

    def test_blindspot_proposes_only_for_unpredicted_waste(self):
        self.cand("C-1", "F-hamilton", "revere")
        self.j(*self.TEST, "--saver-key", "revere", *self.GOOD,
               "--waste-before", "model_writes=3.0,coordinator_context=9.0,tiny_thing=0.01",
               "--waste-after", "model_writes=2.5,coordinator_context=3.0,tiny_thing=0.01")
        rc, out = self.j("propose")
        self.assertEqual(rc, 0, out)
        p = jl(self.led / "finder_proposals.jsonl")
        self.assertEqual([x["cause_key"] for x in p], ["model_writes"])  # predicted + trivial keys skipped
        self.assertEqual(p[0]["status"], "open")
        self.j("propose")
        self.assertEqual(len(jl(self.led / "finder_proposals.jsonl")), 1)  # idempotent
        self.assertEqual(self.j("check")[0], 0)

    def test_privacy_refuses_variable_assignment_and_bad_cause_key(self):
        self.cand("C-1", "F-hamilton", "revere")
        rc, _ = self.j(*self.TEST, "--saver-key", "revere", *self.GOOD, "--matched-on", "ran FOO_DIR=x python3 job.py")
        self.assertEqual(rc, 3)
        self.assertTrue(junto.privacy_problems({"targets": ["Bash (sets variables, then runs a script)"]}))
        self.assertTrue(junto.privacy_problems({"evidence": [{"cause_key": "export X=1"}]}))
        self.assertFalse(junto.privacy_problems({"targets": ["coordinator_context"], "basis": "score = a / (b + c)"}))

    def test_rerun_skip_still_logs_cost(self):
        fake = self.tmp / "fake_finder.py"
        fake.write_text(
            "import argparse, json\n"
            "ap = argparse.ArgumentParser()\n"
            "[ap.add_argument(f) for f in ('--data', '--out', '--run-id', '--profiles')]\n"
            "a = ap.parse_args()\n"
            "open(a.out, 'w').write(json.dumps({'saver_key': 'x', 'title': 't', 'targets': ['narration']}) + '\\n')\n"
            "json.dump({'data_digest': 'd1', 'inputs': {}}, open(a.out + '.run.json', 'w'))\n")
        reg = json.loads((self.led / "finders.json").read_text())
        reg["finders"] = [dict(reg["finders"][0], script=str(fake))]
        (self.led / "finders.json").write_text(json.dumps(reg))
        data = self.tmp / "data"
        data.mkdir()
        self.j("run", "--data", str(data), "--usd-spent", "0.40")
        rc, out = self.j("run", "--data", str(data), "--usd-spent", "0.40")
        self.assertIn("skipped", out)
        self.assertEqual(len(jl(self.led / "candidates.jsonl")), 1)
        self.j("score")
        self.assertAlmostEqual(self.board()["F-hamilton"]["spent_usd"], 0.8)

    def test_privacy_refuses_secret_and_paths(self):
        self.cand("C-1", "F-hamilton", "revere")
        rc, out = self.j(*self.TEST, "--saver-key", "revere", *self.GOOD, "--matched-on", "path /home/user/x token=abc")
        self.assertEqual(rc, 3)
        self.assertEqual(jl(self.led / "tests.jsonl"), [])


class AuditRegressions(Base):
    def test_missing_quality_is_cost_observation_not_verified_saving(self):
        self.cand("C-1", "F-hamilton", "revere")
        rc, out = self.j("add-test", "--saver-key", "revere", "--unit-of-work", "case",
                         "--test-cost-usd", "0", "--before-session", "before", *self.GOOD,
                         "--matched-on", "same cases", "--complete-costs",
                         "--before-measurement-ref", "before.json", "--after-measurement-ref", "after.json")
        self.assertEqual(rc, 0, out)
        self.assertIn("cost_reduction_quality_unverified", out)
        self.assertEqual(jl(self.led / "verified_savings.jsonl"), [])
        test = jl(self.led / "tests.jsonl")[0]
        self.assertFalse(test["quality_measured"])
        self.assertEqual(test["evidence_scope"], "unverified_observation")
        self.assertEqual(junto.Ctx(self.led).current("candidates.jsonl", "candidate_id")["C-1"]["status"], "test_proposed")

    def test_zero_quality_counts_are_unknown_not_perfect(self):
        self.cand("C-1", "F-hamilton", "revere")
        rc, out = self.j(*self.TEST, "--saver-key", "revere", *self.GOOD,
                         "--before-accepted", "0", "--before-rejected", "0", "--after-accepted", "0", "--after-rejected", "0")
        self.assertEqual(rc, 0, out)
        self.assertIn("quality_unverified", out)
        self.assertEqual(jl(self.led / "verified_savings.jsonl"), [])

    def test_negative_quality_and_nan_cost_refused(self):
        self.cand("C-1", "F-hamilton", "revere")
        self.assertEqual(self.j(*self.TEST, "--saver-key", "revere", *self.GOOD, "--after-rejected", "-1")[0], 2)
        self.assertEqual(self.j(*self.TEST, "--saver-key", "revere", *self.GOOD, "--after-usd", "nan")[0], 2)
        self.assertEqual(jl(self.led / "tests.jsonl"), [])

    def test_quality_sample_smaller_than_completed_work_cannot_verify(self):
        self.cand("C-1", "F-hamilton", "revere")
        rc, out = self.j(*self.TEST, "--saver-key", "revere", *self.GOOD, "--after-accepted", "1")
        self.assertEqual(rc, 0, out)
        self.assertIn("measurement_incomplete", out)
        self.assertEqual(jl(self.led / "verified_savings.jsonl"), [])

    def test_unmatched_or_incomplete_cost_comparison_remains_unverified(self):
        self.cand("C-1", "F-hamilton", "revere")
        args = list(self.TEST)
        args.remove("--complete-costs")
        rc, out = self.j(*args, "--saver-key", "revere", *self.GOOD)
        self.assertEqual(rc, 0, out)
        self.assertIn("measurement_incomplete", out)
        self.j("score")
        self.assertIsNone(self.board()["F-hamilton"]["spent_usd"])
        self.assertEqual(self.board()["F-hamilton"]["known_spent_usd"], 31)

    def test_unknown_test_overhead_stays_unknown(self):
        self.cand("C-1", "F-hamilton", "revere")
        args = list(self.TEST)
        i = args.index("--test-cost-usd")
        del args[i:i+2]
        self.assertEqual(self.j(*args, "--saver-key", "revere", *self.GOOD)[0], 0)
        self.j("score")
        self.assertIsNone(self.board()["F-hamilton"]["score"])
        self.assertEqual(self.board()["F-hamilton"]["known_spent_usd"], 30)

    def test_failed_quality_test_costs_include_both_arms(self):
        self.cand("C-1", "F-hamilton", "revere")
        self.j(*self.TEST, "--saver-key", "revere", *self.GOOD, "--after-accepted", "1", "--after-rejected", "1")
        self.j("score")
        f = self.board()["F-hamilton"]
        self.assertEqual(f["spent_usd"], 31)
        self.assertEqual(f["verified_usd"], 0)

    def test_unknown_run_cost_and_mixed_cash_basis_not_added_as_token_value(self):
        ctx = junto.Ctx(self.led, self.out)
        ctx.append("runs.jsonl", [{"run_id":"unknown", "finder_id":"F-hamilton", "usd_spent":None, "usd_basis":"unknown"},
                                  {"run_id":"cash", "finder_id":"F-hamilton", "usd_spent":3, "usd_basis":"cash_charge"}])
        row, total = junto.compute(ctx)
        self.assertIsNone(row["F-hamilton"]["spent_usd"])
        self.assertEqual(total["known_spent_usd"], 0)
        self.assertEqual(total["known_cash_charges_usd"], 3)
        self.assertIsNone(total["cash_charge_total_usd"])

    def test_pilot_is_not_deployment_and_reports_small_sample_uncertainty(self):
        self.cand("C-1", "F-hamilton", "revere")
        self.j(*self.TEST, "--saver-key", "revere", *self.GOOD)
        t = jl(self.led / "tests.jsonl")[0]
        self.assertFalse(t["deployment_supported"])
        self.assertEqual(t["registration_status"], "retrospective_pilot")
        self.assertGreater(t["uncertainty"]["after_rejection_rate_95pct_interval"][1], 0.6)
        self.assertIsNone(t["uncertainty"]["cost_confidence_interval"])

    def test_nonfinite_forged_verified_credit_is_rejected(self):
        self.cand("C-1", "F-hamilton", "revere")
        self.j(*self.TEST, "--saver-key", "revere", *self.GOOD)
        v = jl(self.led / "verified_savings.jsonl")[0]
        v["usd_saved"] = float("nan")
        (self.led / "verified_savings.jsonl").write_text(json.dumps(v) + "\n")
        self.assertEqual(junto.valid_verified_lines(junto.Ctx(self.led)), [])


class SeedAndContractTests(Base):
    def seed(self):
        path = self.tmp / "seed.json"
        path.write_text(json.dumps({"saver_key":"owner_revere", "title":"Owner supplied phase comparison",
            "targets":["coordinator_context"], "origin":{"kind":"owner", "name":"project_owner", "reference":"research/plans/OWNER_PROMPT.md"}}))
        rc, out = self.j("seed-candidate", "--file", str(path))
        self.assertEqual(rc, 0, out)
        return jl(self.led / "candidates.jsonl")[0]["candidate_id"]

    def contract(self, cid, **updates):
        rec = {"contract_id":"PILOT-1", "candidate_ids":[cid],
            "sample":[{"id":"case1", "sha256":"1"*64},{"id":"case2", "sha256":"2"*64}],
            "baseline":{"measurement_ref":"measurements/before.json"}, "unit_of_work":"completed_phase",
            "matched_on":"same frozen two cases and review procedure", "outcome_definition":"API token value per completed phase",
            "quality_condition":{"metric":"rejection_rate", "max_increase":0, "min_reviewed":2},
            "budget_usd":40, "stop_rules":{"max_attempts":1,"stop_on_quality_drop":True},
            "result_paths":["measurements/after.json"]}
        rec.update(updates)
        path = self.tmp / "contract.json"
        path.write_text(json.dumps(rec))
        return path

    def commit_fixture(self, results_present=False):
        subprocess.run(["git", "init", "-q", str(self.tmp)], check=True)
        if results_present:
            (self.tmp / "measurements").mkdir(exist_ok=True)
            (self.tmp / "measurements/after.json").write_text("{}")
        subprocess.run(["git", "-C", str(self.tmp), "add", "."], check=True)
        env = dict(os.environ, GIT_AUTHOR_DATE="2000-01-01T00:00:00Z", GIT_COMMITTER_DATE="2000-01-01T00:00:00Z")
        subprocess.run(["git", "-C", str(self.tmp), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "Synthetic prospective fixture"], env=env, check=True)
        return subprocess.check_output(["git", "-C", str(self.tmp), "rev-parse", "HEAD"], text=True).strip()

    def test_seeded_saving_does_not_credit_a_finder_with_inventing_it(self):
        cid = self.seed()
        self.assertEqual(self.j(*self.TEST, "--candidate", cid, *self.GOOD)[0], 0)
        row, total = junto.compute(junto.Ctx(self.led))
        self.assertEqual(total["verified_usd"], 10)
        self.assertEqual(total["finder_credited_usd"], 0)
        self.assertEqual(total["known_spent_usd"], 31)
        self.assertTrue(all(x["verified_usd"] == 0 for x in row.values()))
        self.assertEqual(self.j("check")[0], 0)

    def test_duplicate_seed_and_unpinned_contract_refused(self):
        cid = self.seed()
        self.assertEqual(self.j("seed-candidate", "--file", str(self.tmp / "seed.json"))[0], 2)
        self.assertEqual(self.j("register-test", "--file", str(self.contract(cid, sample=[{"id":"case1"}])))[0], 2)

    def test_contract_is_frozen_and_uncommitted_registration_cannot_verify(self):
        cid = self.seed()
        path = self.contract(cid)
        self.assertEqual(self.j("register-test", "--file", str(path))[0], 0)
        self.assertEqual(self.j("register-test", "--file", str(path))[0], 2)
        self.j(*self.TEST, "--candidate", cid, *self.GOOD, "--contract", "PILOT-1", "--sample-manifest", str(path))
        self.assertEqual(jl(self.led / "verified_savings.jsonl"), [])
        self.assertEqual(jl(self.led / "tests.jsonl")[0]["registration_status"], "unchecked")

    def test_committed_contract_and_stop_gate_are_enforced(self):
        cid = self.seed()
        self.j("register-test", "--file", str(self.contract(cid)))
        commit = self.commit_fixture()
        self.assertEqual(self.j("test-gate", "--contract", "PILOT-1", "--registration-commit", commit)[0], 0)
        rc, out = self.j(*self.TEST, "--candidate", cid, *self.GOOD, "--contract", "PILOT-1",
                         "--registration-commit", commit, "--measurement-started-at", "2000-01-02T00:00:00Z", "--sample-manifest", str(self.tmp / "contract.json"))
        self.assertEqual(rc, 0, out)
        self.assertEqual(len(junto.valid_verified_lines(junto.Ctx(self.led))), 1)
        rc, out = self.j("test-gate", "--contract", "PILOT-1", "--registration-commit", commit)
        self.assertEqual(rc, 2)
        self.assertIn("attempt_limit_reached", out)

    def test_existing_results_and_wrong_baseline_prevent_prospective_credit(self):
        cid = self.seed()
        self.j("register-test", "--file", str(self.contract(cid)))
        commit = self.commit_fixture(results_present=True)
        rc, out = self.j(*self.TEST, "--candidate", cid, *self.GOOD, "--contract", "PILOT-1",
                         "--registration-commit", commit, "--measurement-started-at", "2000-01-02T00:00:00Z", "--sample-manifest", str(self.tmp / "contract.json"))
        self.assertEqual(rc, 0, out)
        self.assertEqual(jl(self.led / "tests.jsonl")[0]["registration_status"], "results_already_present")
        self.assertEqual(jl(self.led / "verified_savings.jsonl"), [])

    def test_budget_violation_retains_cost_record_but_no_credit(self):
        cid = self.seed()
        self.j("register-test", "--file", str(self.contract(cid, budget_usd=5)))
        commit = self.commit_fixture()
        self.j(*self.TEST, "--candidate", cid, *self.GOOD, "--contract", "PILOT-1",
               "--registration-commit", commit, "--measurement-started-at", "2000-01-02T00:00:00Z", "--sample-manifest", str(self.tmp / "contract.json"))
        t = jl(self.led / "tests.jsonl")[0]
        self.assertIn("cost_unknown_or_budget_exceeded", t["contract_violations"])
        self.assertEqual(jl(self.led / "verified_savings.jsonl"), [])
        self.assertEqual(junto.compute(junto.Ctx(self.led))[1]["known_spent_usd"], 31)

    def test_changed_sample_keeps_result_unverified(self):
        cid = self.seed()
        self.j("register-test", "--file", str(self.contract(cid)))
        commit = self.commit_fixture()
        changed = self.tmp / "changed_sample.json"
        changed.write_text(json.dumps({"sample":[{"id":"different_case", "sha256":"3"*64}]}))
        self.j(*self.TEST, "--candidate", cid, *self.GOOD, "--contract", "PILOT-1",
               "--registration-commit", commit, "--measurement-started-at", "2000-01-02T00:00:00Z",
               "--sample-manifest", str(changed))
        self.assertIn("executed_sample_not_matched_to_pins", jl(self.led / "tests.jsonl")[0]["contract_violations"])
        self.assertEqual(jl(self.led / "verified_savings.jsonl"), [])


if __name__ == "__main__":
    unittest.main()
