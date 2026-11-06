import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate

ROOT = Path(os.environ.get("REPO_ROOT") or Path(__file__).resolve().parents[2])
DISP = ROOT / "research/excavator/claude-tribonian-2026-11-04/evidence/DISPOSITION.json"
# Placeholder economics for the replay: $1 per attempted order, next-best action yields 0.30 dossiers per USD.
COST, NEXT = 1.0, 0.30


def B(name, att, filed, miss=0, usd=0.0):
    return {"batch": name, "attempted": att, "submitted": filed, "filed": filed, "controls_missed": miss, "usd": usd}


def replay(window=None):
    d = json.loads(DISP.read_text())
    seen, rows = [], []
    for x in d["batches"]:
        if not x["batch"].startswith("o") or not x.get("attempted"):
            continue
        seen.append(B(x["batch"], x["attempted"], x["claims_filed"]))
        rows.append((x["batch"], x["claims_filed"], gate.decide(seen, 0.47, 20, COST, NEXT, window=window)))
    return rows


class GateTests(unittest.TestCase):
    def test_posterior_hand_check(self):
        self.assertEqual(gate.posterior(0.5, 20, 2, 60), (12.0, 68.0))

    def test_beta_cdf_known_values(self):
        self.assertAlmostEqual(gate.beta_cdf(0.3, 1, 1), 0.3, 9)
        self.assertAlmostEqual(gate.beta_cdf(0.5, 2, 2), 0.5, 9)
        self.assertAlmostEqual(gate.beta_cdf(0.25, 2, 1), 0.0625, 9)  # x^2

    def test_exact_vs_monte_carlo(self):
        a, b = gate.posterior(0.47, 20, 12, 30)
        e = gate.prob_better(a, b, 1.0, 0.3)
        m = gate.prob_better(a, b, 1.0, 0.3, samples=40000, seed=1, method="mc")
        self.assertAlmostEqual(e, m, delta=0.01)

    def test_mc_deterministic(self):
        x = gate.prob_better(9, 11, 1, .4, samples=2000, seed=5, method="mc")
        self.assertEqual(x, gate.prob_better(9, 11, 1, .4, samples=2000, seed=5, method="mc"))

    def test_collapse_stops(self):
        r = gate.decide([B("a", 30, 1), B("b", 30, 1)], 0.47, 20, 1.0, 0.30)
        self.assertEqual(r["decision"], "STOP")
        self.assertLess(r["prob_better"], 0.2)

    def test_near_prior_continues(self):
        r = gate.decide([B("a", 30, 14), B("b", 30, 14)], 0.47, 20, 1.0, 0.30)
        self.assertEqual(r["decision"], "CONTINUE")
        self.assertLess(r["interval80"][0], r["posterior_mean"])
        self.assertLess(r["posterior_mean"], r["interval80"][1])

    def test_controls_miss_stops_even_when_yield_high(self):
        r = gate.decide([B("a", 40, 38, miss=1)], 0.47, 20, 1.0, 0.30)
        self.assertEqual(r["decision"], "STOP")
        self.assertIn("control", r["reason"])

    def test_pilot_below_min_attempts(self):
        r = gate.decide([B("a", 20, 0)], 0.47, 20, 1.0, 0.30)
        self.assertEqual(r["decision"], "PILOT")

    def test_bad_inputs(self):
        with self.assertRaises(ValueError):
            gate.posterior(0.5, 20, 5, 3)

    def test_cli_json_and_csv(self):
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "b.csv"
            f.write_text("batch,attempted,submitted,filed,controls_missed,usd\nx,30,2,2,0,5\ny,30,1,1,0,5\n")
            out = subprocess.run([sys.executable, "-I", str(Path(gate.__file__)), "--batches", str(f), "--prior-rate",
                                  "0.47", "--cost-per-attempt", "1", "--next-best", "0.3", "--json"],
                                 capture_output=True, text=True, check=True).stdout
            self.assertEqual(json.loads(out)["decision"], "STOP")

    def test_tribonian_replay(self):
        if not DISP.exists():
            self.skipTest("disposition not present")
        rows = replay()
        window = replay(window=2)
        first_stop = next((n for n, _, r in window if r["decision"] == "STOP"), None)
        print("\nTribonian replay (prior 0.47, strength 20, $1/attempt, next-best 0.30 dossiers/USD, stop<0.2)")
        for (n, f, c), (_, _, w) in zip(rows, window):
            print(f"  {n}: filed {f:2d}/30  cumulative {c['decision']:8s} p={c['prob_better']:.2f}"
                  f"   last-2-batches {w['decision']:8s} p={w['prob_better']:.2f}")
        self.assertTrue(all(c["decision"] == "CONTINUE" for _, _, c in rows))  # cumulative gate never reacts
        self.assertEqual(first_stop, "o23")
        self.assertIsNotNone(first_stop)


if __name__ == "__main__":
    unittest.main()
