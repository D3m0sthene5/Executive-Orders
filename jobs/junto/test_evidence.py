"""Rumford (evidence.py): prices committed wave usage and measures cost at stake per saver."""
import csv
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import evidence as E  # noqa: E402

FIELDS = ["agent_id", "role", "model", "calls", "wall_seconds", "active_seconds", *E.TOKEN_FIELDS]


class RumfordTest(unittest.TestCase):
    def repo(self, rows_by_wave):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        (root / "jobs/necker-costs").mkdir(parents=True)
        shutil.copy(HERE.parents[1] / E.PRICES, root / E.PRICES)
        for wave, rows in rows_by_wave.items():
            d = root / "research/bentham/usage" / wave
            d.mkdir(parents=True)
            with open(d / "AGENT_USAGE.csv", "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=FIELDS)
                w.writeheader()
                for r in rows:
                    w.writerow({k: r.get(k, 0) for k in FIELDS})
        return root

    def test_prices_rows_and_flags_main_session_heavy_waves(self):
        # 1M output tokens on Opus 5.5 is $20; 1M on Sonnet 5.5 is $10.
        root = self.repo({"heavy": [{"role": "coordinator", "model": "claude-opus-5-5", "output": 1_000_000, "calls": 10},
                                    {"role": "general-purpose", "model": "claude-sonnet-5-5", "output": 1_000_000, "calls": 10}],
                          "lean": [{"role": "coordinator", "model": "claude-opus-5-5", "output": 100_000, "calls": 10},
                                   {"role": "general-purpose", "model": "claude-sonnet-5-5", "output": 1_000_000, "calls": 10}]})
        ev = E.measure(root)
        waves = {w["wave"]: w for w in ev["waves"]}
        self.assertAlmostEqual(waves["heavy"]["usd"], 30.0)
        self.assertAlmostEqual(waves["heavy"]["coordinator_share"], 0.667, places=3)
        lean = {s["saver_key"]: s for s in ev["savers"]}["lean_coordination"]
        self.assertEqual([w["wave"] for w in lean["waves"]], ["heavy"])  # 2/12 share is not flagged
        self.assertEqual(lean["cost_at_stake_usd"], 20.0)
        self.assertEqual(lean["status"], "unverified")  # never a saving

    def test_large_context_and_idle_cache_signals(self):
        root = self.repo({"w": [{"role": "coordinator", "model": "claude-opus-5-5", "calls": 2, "cache_read": 1_000_000,
                                 "cache_write_1h": 1_000_000, "wall_seconds": 1000, "active_seconds": 100}]})
        s = {x["saver_key"]: x for x in E.measure(root)["savers"]}
        self.assertAlmostEqual(s["revere_phase_handoff"]["cost_at_stake_usd"], 0.20)  # 1M cache reads at $0.20
        self.assertAlmostEqual(s["idle_cache_avoidance"]["cost_at_stake_usd"], 8.0)   # 1M 1-hour writes at $8

    def test_unpriced_models_are_reported_not_guessed_and_outputs_render(self):
        root = self.repo({"w": [{"role": "coordinator", "model": "gpt-x", "output": 5}]})
        out = root / "out"
        ev = E.write(root, out)
        self.assertEqual(ev["unpriced_models"], {"gpt-x": 1})
        self.assertIn("cost at stake", (out / "OPEN_TESTS.md").read_text())
        self.assertEqual(json.loads((out / "EVIDENCE.json").read_text())["schema"], "junto.rumford/1")


if __name__ == "__main__":
    unittest.main()
