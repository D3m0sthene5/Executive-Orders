import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import unittest

import bentham as B  # noqa: E402

MEASURED = {
    "rates": [{"key": "r.big", "value": 0.5, "num": 50, "den": 100, "source": "x"},
              {"key": "r.thin", "value": 0.0, "num": 0, "den": 7, "source": "x"}],
    "costs": {"wave": {"usd": 0.65, "per": "attempted_order"}},
}


class ScoreTests(unittest.TestCase):
    def test_production_score(self):
        s = B.score(MEASURED, {"id": "p", "kind": "production", "orders": 100, "rate_key": "r.big", "cost_key": "wave"})
        self.assertEqual(s["expected_now"], 50.0)
        self.assertAlmostEqual(s["cost_usd"], 65.0)
        self.assertAlmostEqual(s["per_usd"], 50 / 65)

    def test_thin_rate_is_unranked_with_probe(self):
        s = B.score(MEASURED, {"id": "y", "kind": "production", "orders": 300, "rate_key": "r.thin", "cost_key": "wave"})
        self.assertTrue(s["unranked"])
        self.assertNotIn("per_usd", s)
        self.assertAlmostEqual(s["probe_cost_usd"], 30 * 0.65, places=2)

    def test_free_acquisition_with_fecundity_ranks_first(self):
        acq = {"id": "a", "kind": "acquisition", "orders": 0, "cost_override_usd": 0,
               "unlocks": [{"orders": 10, "rate_key": "r.big", "delay_days": 0}]}
        prod = {"id": "p", "kind": "production", "orders": 100, "rate_key": "r.big", "cost_key": "wave"}
        ranked, unranked = B.order_plan([B.score(MEASURED, acq), B.score(MEASURED, prod)])
        self.assertEqual([s["id"] for s in ranked], ["a", "p"])
        self.assertEqual(ranked[0]["per_usd"], math.inf)
        self.assertEqual(ranked[0]["fecundity"], 5.0)

    def test_discount_and_budget(self):
        self.assertAlmostEqual(B.discount(60), 0.5)
        acts = [B.score(MEASURED, {"id": f"p{i}", "kind": "production", "orders": 100, "rate_key": "r.big",
                                   "cost_key": "wave"}) for i in range(3)]
        ranked, _ = B.order_plan(acts, budget=140)
        self.assertEqual([s["within_budget"] for s in ranked], [True, True, False])

    def test_cost_units_price_agent_acquisitions(self):
        s = B.score(MEASURED, {"id": "c", "kind": "acquisition", "orders": 0, "cost_key": "wave", "cost_units": 10,
                               "unlocks": [{"orders": 10, "rate_key": "r.big", "delay_days": 0}]})
        self.assertAlmostEqual(s["cost_usd"], 6.5)



class JuntoSaversInPlan(unittest.TestCase):
    def test_junto_savers_are_listed_and_absent_evidence_is_harmless(self):
        import json, tempfile
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "EVIDENCE.json"
            path.write_text(json.dumps({"savers": [{"saver_key": "lean_coordination", "cost_at_stake_usd": 12.5,
                                                    "status": "unverified"}, {"saver_key": "x", "cost_at_stake_usd": 0}]}))
            savers = B.junto_savers(path)
            self.assertEqual([s["saver_key"] for s in savers], ["lean_coordination"])
            self.assertEqual(B.junto_savers(Path(d) / "missing.json"), [])
            text = B.report({"ranked": [], "unranked": [], "budget_usd": 0, "discount_half_life_days": 60, "allowance": {}, "sensitivity": [], "junto_savers": savers})
            self.assertIn("`lean_coordination`", text)
            self.assertIn("not savings until", text)

if __name__ == "__main__":
    unittest.main()


class JustinianB6Test(unittest.TestCase):
    """Window-token costs, probes for unmeasured strata, and rank flips (Justinian, 2026-11-06)."""

    def test_window_tokens_both_weightings(self):
        import measure as M
        w = M.window_tokens({"fresh_input": 10, "cache_read": 1000, "cache_write": 20, "output": 70}, 10)
        self.assertEqual(w["cache_read_weight_1.0"], 110.0)
        self.assertEqual(w["cache_read_weight_0.1"], 20.0)

    def test_unmeasured_stratum_becomes_a_ranked_probe(self):
        probes = B.probes_for([{"id": "status_assignment.undecided", "kind": "status_assignment", "orders": 500,
                                "probe_cost_usd": 19.0, "notes": ["no measured yield"]},
                               {"id": "zero_agent.x", "kind": "zero_agent", "orders": 0, "probe_cost_usd": None}])
        self.assertEqual([p["id"] for p in probes], ["probe.status_assignment.undecided"])
        self.assertEqual(probes[0]["orders"], B.PROBE_ORDERS)
        ranked, _ = B.order_plan(probes)
        self.assertEqual(ranked[0]["id"], "probe.status_assignment.undecided")

    def test_window_rank_flip_detected(self):
        measured = {"costs": {"cheap_usd": {"window_tokens": {"cache_read_weight_1.0": 1000.0, "cache_read_weight_0.1": 1000.0}},
                              "cheap_tokens": {"window_tokens": {"cache_read_weight_1.0": 10.0, "cache_read_weight_0.1": 10.0}}}}
        ranked = [{"id": "a", "cost_key": "cheap_usd", "orders": 1, "value": 2.0, "cost_usd": 1.0},
                  {"id": "b", "cost_key": "cheap_tokens", "orders": 1, "value": 1.0, "cost_usd": 1.0}]
        flips = B.window_rank_flips(measured, ranked)["flips"]
        self.assertTrue(any(f["window_order"] == ["b", "a"] for f in flips))
