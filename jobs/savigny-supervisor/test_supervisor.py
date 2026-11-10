"""supervisor.py: every limit acts on measurements, and every turn is a fresh session.

The real scheduling loop runs with a fake Codex (a short sleep), an injected meter and a controllable clock.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import supervisor as S

LIMITS = {"chain_budget_units": 1000, "spend_per_claim_units": 100, "no_claim_minutes": 30,
          "context_kill_tokens": 120000, "reviews_per_hour": 6, "coordinator_units_per_hour": 50}


class Clock:
    def __init__(self):
        self.t = 1_000_000.0

    def __call__(self):
        return self.t


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "_savigny"
        (self.root / "prompts").mkdir(parents=True)
        for name in ("savigny.md", "savigny-turn.md", "lane.md", "lane-turn.md"):
            (self.root / "prompts" / name).write_text("prompt {AGENT} {TURN} {N}", encoding="utf-8")
        (self.root / "lanes.json").write_text(json.dumps({"lanes": {"mommsen-1": None}}), encoding="utf-8")
        (self.root / "limits.json").write_text(json.dumps(LIMITS), encoding="utf-8")
        self.clock = Clock()
        self.readings = {"_savigny": {"units": 0}, "mommsen-1": {"units": 0, "filed": 0, "reviews_last_hour": 0}}
        self.chains = []
        self.old = S.STAGGER, S.SHORT_TURN
        S.STAGGER = S.SHORT_TURN = 0

    def tearDown(self):
        for c in self.chains:
            self.finish(c)
        S.STAGGER, S.SHORT_TURN = self.old
        self.tmp.cleanup()

    def chain(self):
        c = S.Chain(self.root, fake=True, metered=lambda: json.loads(json.dumps(self.readings)), clock=self.clock)
        c.turn_context = lambda agent: 0
        self.chains.append(c)
        return c

    def run_steps(self, c, n=3):
        for _ in range(n):
            c.last_meter = -10 ** 9
            c.step()

    def inbox(self, box="claude"):
        path = self.root / "inbox" / f"{box}.jsonl"
        return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []

    def finish(self, c):
        for agent in list(c.running):
            c.kill(agent)
        c.reap()

    def test_refuses_to_start_without_every_limit(self):
        for key in LIMITS:
            (self.root / "limits.json").write_text(json.dumps({k: v for k, v in LIMITS.items() if k != key}),
                                                   encoding="utf-8")
            with self.assertRaises(SystemExit) as e:
                S.Chain(self.root, fake=True)
            self.assertIn(key, str(e.exception))

    def test_spend_without_a_claim_pauses_the_lane_and_kills_its_turn(self):
        c = self.chain()
        self.run_steps(c, 1)
        self.assertIn("mommsen-1", c.running)
        self.readings["mommsen-1"]["units"] = 101
        self.run_steps(c, 1)
        self.assertTrue((self.root / "PAUSE-mommsen-1").exists())
        self.assertNotIn("mommsen-1", c.running)
        self.assertEqual(self.inbox()[-1]["reason"], "spend without a claim")

    def test_a_new_verified_claim_resets_the_spend_allowance(self):
        c = self.chain()
        self.run_steps(c, 1)
        for units in (90, 180, 270):            # each step spends 90, under the 100 cap, and files one claim
            self.readings["mommsen-1"].update(units=units, filed=self.readings["mommsen-1"]["filed"] + 1)
            self.run_steps(c, 1)
        self.assertFalse((self.root / "PAUSE-mommsen-1").exists())
        self.finish(c)

    def test_time_without_a_claim_pauses_the_lane(self):
        c = self.chain()
        self.run_steps(c, 1)
        self.clock.t += 31 * 60
        self.run_steps(c, 1)
        self.assertEqual(json.loads(json.dumps(self.inbox()[-1]))["reason"], "time without a claim")

    def test_auto_review_burst_pauses_the_lane(self):
        c = self.chain()
        self.run_steps(c, 1)
        self.readings["mommsen-1"]["reviews_last_hour"] = 7
        self.run_steps(c, 1)
        self.assertIn("auto-review burst", self.inbox()[-1]["reason"])

    def test_chain_budget_stops_everything(self):
        c = self.chain()
        self.run_steps(c, 1)
        self.readings["_savigny"]["units"] = 600
        self.readings["mommsen-1"]["units"] = 400
        self.readings["mommsen-1"]["filed"] = 5   # filing does not buy budget
        self.run_steps(c, 1)
        self.assertTrue((self.root / "STOP").exists())
        self.assertEqual(c.running, {})
        self.assertEqual(self.inbox()[-1]["event"], "budget_stop")

    def test_context_over_the_cap_kills_the_turn_not_the_lane(self):
        c = self.chain()
        self.run_steps(c, 1)
        c.turn_context = lambda agent: 150000 if agent == "mommsen-1" else 0
        self.run_steps(c, 1)
        events = [e for e in self.inbox() if e.get("event") == "context_kill"]
        self.assertEqual(events[0]["agent"], "mommsen-1")
        self.assertFalse((self.root / "PAUSE-mommsen-1").exists())
        self.finish(c)

    def test_coordinator_runs_only_when_there_is_news(self):
        c = self.chain()
        self.run_steps(c, 2)
        self.assertNotIn("_savigny", c.running)          # nothing has happened yet
        self.finish(c)                                     # a lane turn ends: that is news
        self.clock.t += S.COORD_MIN_GAP + 1
        self.run_steps(c, 1)
        self.assertIn("_savigny", c.running)
        self.finish(c)

    def test_every_turn_is_a_fresh_session(self):
        c = S.Chain(self.root, fake=False, metered=lambda: self.readings, clock=self.clock)
        c.codex = lambda: "codex.exe"
        cmd = c.command("mommsen-1", self.root / "last.md")
        self.assertEqual(cmd[:2], ["codex.exe", "exec"])
        self.assertNotIn("resume", cmd)

    def test_paused_lane_is_not_restarted(self):
        c = self.chain()
        (self.root / "PAUSE-mommsen-1").write_text("x", encoding="utf-8")
        self.run_steps(c, 2)
        self.assertNotIn("mommsen-1", c.running)


if __name__ == "__main__":
    unittest.main()
