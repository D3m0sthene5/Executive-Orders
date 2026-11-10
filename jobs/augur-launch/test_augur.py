"""augur.py: a wave plan launches only when the project's own lessons and measurements allow it.

The decisive test replays the plan that actually ran on 2026-11-09/10 and checks that Augur refuses it for the
reasons that wave failed. The other tests pin each rule on a minimal repository.
"""
import copy
import json
import tempfile
import unittest
from pathlib import Path

import augur

LIMITS = {"chain_budget_units": 5_000_000, "spend_per_claim_units": 3_000_000, "no_claim_minutes": 40,
          "context_kill_tokens": 120000, "reviews_per_hour": 6, "coordinator_units_per_hour": 1_000_000}


def make_repo(root, findings=(), runs=()):
    root = Path(root)
    (root / "jobs/bentham/output").mkdir(parents=True)
    (root / "jobs/kean/register").mkdir(parents=True)
    (root / "jobs/augur-launch").mkdir(parents=True)
    plan = {"ranked": [
        {"id": "production.claim_ready.yes.fr", "orders": 351, "rate": {"value": 0.2333}, "cost_usd": 116.71, "per_usd": 0.70},
        {"id": "production.claim_ready.no.fr", "orders": 1034, "rate": {"value": 0.0333}, "cost_usd": 343.8, "per_usd": 0.10},
        {"id": "probe.production.decided.prefr", "orders": 30, "per_usd": float("inf")}],
        "unranked": [{"id": "production.decided.prefr", "orders": 1250}]}
    (root / augur.BENTHAM_PLAN).write_text(json.dumps(plan), encoding="utf-8")
    (root / augur.FINDINGS).write_text("".join(json.dumps(f) + "\n" for f in findings), encoding="utf-8")
    (root / augur.CONFIGS).write_text(json.dumps({"runs": list(runs)}), encoding="utf-8")
    return root


SCRIPTED_PASSED = [{"fingerprint": "claude-scripted|anthropic|anthropic", "stage": 1, "passed": True,
                    "finding": "F-20261108-cujas-usage"}]


def good_plan():
    plan = {"wave": "test", "author": "claude-opus-5-5", "stage": 1,
            "objective": {"metric": "filed_dossiers_per_unit"},
            "actions": [{"id": "production.claim_ready.yes.fr", "orders": 60, "lanes": 2}],
            "configuration": {"orchestrator": "claude-scripted", "coordinator_model": "claude-opus-5-5",
                              "producer_model": "claude-sonnet-5-5"},
            "limits": dict(LIMITS),
            "premortem": [{"failure": f"failure mode number {i} described concretely", "guard": f"guard number {i} that stops it in the loop"}
                          for i in range(3)],
            "acknowledged_findings": {}}
    return plan


def sign(plan, reviewer="gpt-6.1-sol", verdict="approve"):
    plan = copy.deepcopy(plan)
    plan["review"] = {"reviewer": reviewer, "verdict": verdict, "plan_sha256": augur.plan_sha(plan)}
    return plan


class AugurRuleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = make_repo(self.tmp.name, runs=SCRIPTED_PASSED)

    def tearDown(self):
        self.tmp.cleanup()

    def refusals(self, plan):
        return augur.check(plan, self.repo)[0]

    def test_a_measured_ranked_reviewed_plan_passes_with_a_forecast(self):
        no, receipt = augur.check(sign(good_plan()), self.repo)
        self.assertEqual(no, [])
        self.assertEqual(receipt["verdict"], "PASS")
        self.assertAlmostEqual(receipt["forecast"]["expected_filed"], 14.0, places=0)   # 60 x 0.2333

    def test_spend_objective_is_refused(self):
        plan = good_plan()
        plan["objective"] = {"metric": "filed_dossiers_per_unit", "note": "burn the weekly allowance overnight"}
        self.assertTrue(any("spend" in r for r in self.refusals(sign(plan))))
        plan["objective"] = {"metric": "tokens_used"}
        self.assertTrue(any("outcome metric" in r for r in self.refusals(sign(plan))))

    def test_action_outside_bentham_and_low_yield_and_unmeasured_are_refused(self):
        for action, words in ((("decided-below-7532-range", 30, 1), "not in Bentham"),
                              (("production.claim_ready.no.fr", 60, 1), "below the floor"),
                              (("production.decided.prefr", 31, 1), "unmeasured"),
                              (("production.decided.prefr", 30, 2), "unmeasured")):
            plan = good_plan()
            plan["actions"] = [{"id": action[0], "orders": action[1], "lanes": action[2]}]
            self.assertTrue(any(words in r for r in self.refusals(sign(plan))), action)

    def test_novel_configuration_starts_at_stage_zero(self):
        plan = good_plan()
        plan["configuration"]["orchestrator"] = "brand-new-chain"
        self.assertTrue(any("stage 0 at most" in r for r in self.refusals(sign(plan))))
        plan["stage"] = 0
        plan["actions"] = [{"id": "production.claim_ready.yes.fr", "orders": 30, "lanes": 1}]
        self.assertEqual(self.refusals(sign(plan)), [])

    def test_stage_caps_lanes_orders_and_budget(self):
        plan = good_plan()
        plan["actions"] = [{"id": "production.claim_ready.yes.fr", "orders": 301, "lanes": 4}]
        plan["limits"]["chain_budget_units"] = 50_000_000
        text = " ".join(self.refusals(sign(plan)))
        for words in ("allows 3 lanes", "allows 300 orders", "allows a budget"):
            self.assertIn(words, text)

    def test_missing_limits_premortem_and_review_are_refused(self):
        plan = good_plan()
        del plan["limits"]["chain_budget_units"]
        plan["premortem"] = plan["premortem"][:2]
        text = " ".join(self.refusals(plan))          # unsigned
        for words in ("limits missing: chain_budget_units", "premortem needs", "review must be bound"):
            self.assertIn(words, text)

    def test_review_must_be_another_family_and_bound_to_this_plan(self):
        self.assertTrue(any("author's model family" in r for r in self.refusals(sign(good_plan(), reviewer="claude-sonnet-5-5"))))
        self.assertEqual(self.refusals(sign(good_plan(), reviewer="owner")), [])
        signed = sign(good_plan())
        signed["actions"][0]["orders"] = 61                 # edited after review
        self.assertTrue(any("review must be bound" in r for r in self.refusals(signed)))
        self.assertTrue(any("not approve" in r for r in self.refusals(sign(good_plan(), verdict="reject"))))

    def test_matching_lessons_must_each_be_answered(self):
        finding = {"id": "F-1", "rev": 0, "date": "2026-11-09", "verdict": "failed", "keywords": ["coordinator"],
                   "tried": "x", "result": "y", "lesson": "coordinators must not do clerical work"}
        other = {"id": "F-2", "rev": 0, "date": "2026-11-09", "verdict": "worked", "keywords": ["coordinator"],
                 "tried": "x", "result": "y", "lesson": "a success is not a warning"}
        with tempfile.TemporaryDirectory() as d:
            repo = make_repo(d, findings=[finding, other], runs=SCRIPTED_PASSED)
            plan = good_plan()
            no = augur.check(sign(plan), repo)[0]
            self.assertEqual([r for r in no if "unanswered lesson" in r][0][:24], "unanswered lesson F-1 [f")
            self.assertFalse(any("F-2" in r for r in no))
            plan["acknowledged_findings"] = {"F-1": "too short"}
            self.assertTrue(any("F-1" in r for r in augur.check(sign(plan), repo)[0]))
            plan["acknowledged_findings"] = {"F-1": "workers do judgment; scripts do every clerical step"}
            self.assertEqual(augur.check(sign(plan), repo)[0], [])


class MissingInputTests(unittest.TestCase):
    def test_missing_bentham_plan_or_kean_register_refuses_instead_of_crashing(self):
        with tempfile.TemporaryDirectory() as d:
            repo = make_repo(d, runs=SCRIPTED_PASSED)
            (Path(repo) / augur.BENTHAM_PLAN).unlink()
            (Path(repo) / augur.FINDINGS).unlink()
            no = augur.check(sign(good_plan()), repo)[0]
        text = " ".join(no)
        self.assertIn("Bentham's plan is unreadable or missing", text)
        self.assertIn("the Kean register is unreadable or missing", text)


class LastNightTests(unittest.TestCase):
    """The plan that ran on 2026-11-09/10, written as an Augur plan, is refused for the reasons it failed."""

    def test_the_overnight_codex_wave_is_refused(self):
        findings = [
            {"id": "F-20261109-gutenberg-carnot", "rev": 0, "date": "2026-11-09", "verdict": "partly_worked",
             "keywords": ["carnot", "coordinator", "waste"], "tried": "", "result": "",
             "lesson": "Run the next wave with PROTOCOL.md as the after arm of lean_coordination."},
            {"id": "F-20261107-haloander-undecided-probe", "rev": 0, "date": "2026-11-07", "verdict": "partly_worked",
             "keywords": ["undecided", "probe"], "tried": "", "result": "0 of 30 filed", "lesson": "undecided below 7532 does not file"}]
        with tempfile.TemporaryDirectory() as d:
            repo = make_repo(d, findings=findings, runs=SCRIPTED_PASSED + [
                {"fingerprint": "claude-scripted|anthropic|anthropic", "stage": 2, "passed": True, "finding": "F-x"}])
            plan = {"wave": "mommsen-2026-11-10", "author": "claude-opus-5-5", "stage": 2,
                    "objective": {"metric": "filed_dossiers_per_unit", "note": "use the Codex allowance overnight"},
                    "actions": [{"id": "decided-not-ready-below-7532", "orders": 1236, "lanes": 3},
                                {"id": "production.claim_ready.no.fr", "orders": 1034, "lanes": 1},
                                {"id": "status_assignment.undecided.below-7532", "orders": 6300, "lanes": 1}],
                    "configuration": {"orchestrator": "savigny-supervisor", "coordinator_model": "gpt-6.1-sol",
                                      "producer_model": "gpt-6.1-sol"},
                    "limits": {}, "premortem": [], "acknowledged_findings": {}}
            no = augur.check(plan, repo)[0]
        text = " ".join(no)
        for words in ("spend or activity",             # the objective drifted to using the allowance
                      "not in Bentham",                # invented pools
                      "below the floor",               # no.fr: 0.10 dossiers per dollar
                      "stage 0 at most",               # a never-run configuration at full scale
                      "limits missing",                # no budget
                      "premortem needs",               # no pre-mortem
                      "review must be bound",          # author approved his own plan
                      "unanswered lesson F-20261109-gutenberg-carnot"):
            self.assertIn(words, text)


if __name__ == "__main__":
    unittest.main()
