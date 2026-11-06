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


if __name__ == "__main__":
    unittest.main()
