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


class GutenbergKeanTest(unittest.TestCase):
    """Item 5: Junto reads Kean measures for waves with no usage table, and prefers per-call usd_list."""

    def test_kean_wave_and_usd_list(self):
        import json as _j
        import shutil
        import tempfile
        from pathlib import Path as _P
        here = _P(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as t:
            root = _P(t)
            for rel in ("jobs/necker-costs/PRICES.json", "jobs/kean/kean.py"):
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(here / rel, root / rel)
            reg = root / "jobs/kean/register"
            reg.mkdir(parents=True)
            (reg / "findings.jsonl").write_text(_j.dumps({"id": "F-1", "rev": 0, "date": "2026-11-09", "measures": {
                "wave": "w-kean", "usd": {"total": 10.0, "by_role": {"coordinator": 8.0, "worker": 2.0},
                                          "basis": "list_price"}}}) + "\n")
            u = root / "research/bentham/usage/w-csv"
            u.mkdir(parents=True)
            (u / "AGENT_USAGE.csv").write_text(
                "role,model,fresh_input,cache_read,cache_write_5m,cache_write_1h,cache_write_unclassified,output,"
                "calls,wall_seconds,active_seconds,usd_list\n"
                "coordinator,claude-opus-5-5,0,1000000,0,0,0,0,1,10,10,7.5\n")
            sys.path.insert(0, str(here / "jobs/junto"))
            import evidence as E
            e = E.measure(root)
            w = {x["wave"]: x for x in e["waves"]}
            self.assertEqual(w["w-csv"]["usd"], 7.5)  # usd_list kept, not the 0.20 table price
            self.assertEqual(w["w-kean"]["coordinator_share"], 0.8)
            lean = next(s for s in e["savers"] if s["saver_key"] == "lean_coordination")
            self.assertEqual({x["wave"] for x in lean["waves"]}, {"w-csv", "w-kean"})


class GutenbergReadyTests(unittest.TestCase):
    def test_every_saver_has_a_ready_two_arm_test_on_a_real_candidate(self):
        import json as _j
        from pathlib import Path as _P
        here = _P(__file__).resolve().parent
        sys.path.insert(0, str(here))
        import evidence as E
        ids = {_j.loads(l)["candidate_id"] for l in (here / "ledger/candidates.jsonl").read_text().splitlines() if l.strip()}
        for key, s in E.SAVERS.items():
            for field in ("tool", "candidate", "arms", "matched_on", "measure", "add_test"):
                self.assertTrue(s.get(field), (key, field))
            self.assertEqual(set(s["arms"]), {"before", "after"})
            self.assertIn(s["candidate"], ids, key)
            self.assertIn("--candidate " + s["candidate"], s["add_test"])
            self.assertTrue((here.parents[1] / s["tool"].split(" ")[0]).exists(), s["tool"])
        text = E.render(E.measure(here.parents[1]))
        self.assertEqual(text.count("### `"), len(E.SAVERS))
        self.assertIn("No saving is claimed", text)
