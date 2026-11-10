"""meter.py: spend and verified claims from token logs and claim files, never from an agent's own report."""
import datetime
import json
import os
import tempfile
import time
import unittest
from pathlib import Path

import meter


def rollout(home, name, started, cwd, model, totals, contexts, mentions=""):
    """A minimal Codex rollout file: a meta line, one token_count line per call (cumulative totals)."""
    day = home / "sessions" / "2026" / "11" / "10"
    day.mkdir(parents=True, exist_ok=True)
    path = day / f"rollout-{name}.jsonl"
    lines = [{"timestamp": started, "type": "session_meta", "payload": {"cwd": cwd, "model": model, "note": mentions}}]
    run = {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0}
    for ctx, (inp, cached, out) in zip(contexts, totals):
        run = {"input_tokens": inp, "cached_input_tokens": cached, "output_tokens": out}
        lines.append({"type": "event_msg", "payload": {"type": "token_count", "info": {
            "total_token_usage": run, "last_token_usage": {"input_tokens": ctx}}}})
    path.write_text("\n".join(json.dumps(l) for l in lines) + "\n", encoding="utf-8")
    return path


class MeterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_units_weigh_cache_input_and_output(self):
        self.assertEqual(meter.units(1000, 100, 10), 0.1 * 1000 + 100 + 4 * 10)

    def test_rollout_totals_last_and_max_context(self):
        p = rollout(self.home, "a", "2026-11-10T05:00:00Z", r"C:\Users\x\eo-wt\mommsen-2", "gpt-6.1-sol",
                    [(100, 50, 5), (400, 300, 9)], [80, 300])
        s = meter.read_rollout(p)
        self.assertEqual((s["calls"], s["input"], s["cached"], s["output"]), (2, 400, 300, 9))
        self.assertEqual((s["last_context"], s["max_context"]), (300, 300))

    def test_attribution_by_working_directory_then_by_mentions(self):
        lanes = ["mommsen-1", "mommsen-2", "_savigny"]
        own = meter.read_rollout(rollout(self.home, "b", "2026-11-10T05:00:00Z", r"C:\Users\x\eo-wt\mommsen-2",
                                         "m", [(1, 0, 0)], [1]))
        self.assertEqual(meter.attribute(own, lanes), "mommsen-2")
        worker = meter.read_rollout(rollout(self.home, "c", "2026-11-10T05:00:00Z", r"C:\Users\x\eo-wt", "m",
                                            [(1, 0, 0)], [1], mentions=r"cd C:\Users\x\eo-wt\mommsen-1\research"))
        self.assertEqual(meter.attribute(worker, lanes), "mommsen-1")
        stranger = meter.read_rollout(rollout(self.home, "d", "2026-11-10T05:00:00Z", r"C:\elsewhere", "m",
                                              [(1, 0, 0)], [1]))
        self.assertIsNone(meter.attribute(stranger, lanes))
        prefix = meter.read_rollout(rollout(self.home, "e", "2026-11-10T05:00:00Z", r"C:\Users\x\eo-wt\mommsen-10",
                                            "m", [(1, 0, 0)], [1]))
        self.assertIsNone(meter.attribute(prefix, ["mommsen-1"]))   # mommsen-10 is not mommsen-1

    def test_filed_claims_counts_distinct_orders_in_both_name_forms(self):
        tree = self.home / "wt"
        claims = tree / "research/readiness/claims"
        claims.mkdir(parents=True)
        (claims / "mommsen-3-2026-11-10-a.jsonl").write_text(
            json.dumps({"instrument_id": "EO:1"}) + "\n" + json.dumps({"instrument_id": "EO:2"}) + "\n", encoding="utf-8")
        (claims / "mommsen3-2026-11-10-b.jsonl").write_text(json.dumps({"instrument_id": "EO:2"}) + "\nnot json\n",
                                                             encoding="utf-8")
        (claims / "papinian-x.jsonl").write_text(json.dumps({"instrument_id": "EO:9"}) + "\n", encoding="utf-8")
        self.assertEqual(meter.filed_claims(tree, "mommsen-3"), {"EO:1", "EO:2"})

    def test_lane_report_sums_spend_counts_reviews_and_skips_old_sessions(self):
        now = datetime.datetime(2026, 11, 10, 6, 0, tzinfo=datetime.timezone.utc)
        rollout(self.home, "f", "2026-11-10T05:30:00Z", r"C:\Users\x\eo-wt\mommsen-1", "gpt-6.1-sol",
                [(1000, 900, 10)], [500])
        rollout(self.home, "g", "2026-11-10T05:40:00Z", r"C:\Users\x\eo-wt\mommsen-1", "codex-auto-review",
                [(100, 0, 0)], [100])
        rollout(self.home, "h", "2026-11-10T03:00:00Z", r"C:\Users\x\eo-wt\mommsen-1", "gpt-6.1-sol",
                [(10 ** 9, 0, 0)], [10 ** 6])
        r = meter.lane_report(["mommsen-1"], "2026-11-10T05:00:00Z", self.home, now=now)["mommsen-1"]
        self.assertEqual(r["sessions"], 2)
        self.assertEqual(r["units"], round(meter.units(900, 100, 10) + meter.units(0, 100, 0)))
        self.assertEqual((r["reviews"], r["reviews_last_hour"], r["max_context"]), (1, 1, 500))


if __name__ == "__main__":
    unittest.main()
