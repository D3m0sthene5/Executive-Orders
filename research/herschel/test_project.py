"""Tests for project.py on a small synthetic survey. Run: python3 -I research/herschel/test_project.py"""
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import project  # noqa: E402


def fixture(root: Path):
    (root / "frame").mkdir()
    (root / "H1/telemetry").mkdir(parents=True)
    rows = [dict(instrument_id=f"EO:{i}", stratum=["none.1907-36", "no.1937-89"][i % 2],
                 open_steps="original_text|clause_inventory") for i in range(40)]
    rows.append(dict(instrument_id="EO:999", stratum="no.1990on", open_steps="clause_inventory"))
    with open(root / "frame/ORDERS.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with open(root / "frame/CELLS.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["instrument_id", "stratum", "step", "count"])
        for r in rows:
            for s in r["open_steps"].split("|"):
                w.writerow([r["instrument_id"], r["stratum"], s, 1])
    (root / "frame/ASSIGNMENTS.json").write_text(json.dumps({"coordinators": [
        {"name": "H1", "concurrency": 4, "orders": ["EO:0", "EO:1", "EO:2", "EO:3"]}]}))
    tr = [{"worker": "H1-w01", "step": "original_text", "model": "claude-sonnet-5-5", "orders": ["EO:0", "EO:1"],
           "started_utc": "2026-11-05T23:30:00Z", "ended_utc": "2026-11-05T23:40:00Z", "limit_events": [],
           "outcomes": {"EO:0": "done", "EO:1": "blocked:NARA scan"}, "usd": 2.0},
          {"worker": "H1-w02", "step": "clause_inventory", "model": "claude-sonnet-5-5", "orders": ["EO:0", "EO:1"],
           "started_utc": "2026-11-05T23:35:00Z", "ended_utc": "2026-11-05T23:50:00Z", "limit_events": ["429"],
           "outcomes": {"EO:0": "done", "EO:1": "done"}, "session_id": "abc"}]
    (root / "H1/TRACE.jsonl").write_text("\n".join(json.dumps(t) for t in tr) + "\n")
    with open(root / "H1/telemetry/AGENT_USAGE.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["agent_id", "role", "phase", "model", "fresh_input", "cache_read", "cache_write_5m",
                    "cache_write_1h", "cache_write_unclassified", "output", "session_id"])
        w.writerow(["main-abc", "producer", "x", "claude-sonnet-5-5", 0, 0, 0, 0, 0, 100000, "abc"])  # $1.50


class ProjectTests(unittest.TestCase):
    def test_projection(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fixture(root)
            project.main(["--root", str(root), "--boot", "50"])
            p = json.loads((root / "ATLAS/PROJECTION.json").read_text())
            self.assertEqual(p["reached_orders"], 2)
            self.assertEqual(p["workers_unpriced"], 0)
            self.assertAlmostEqual(p["measured_usd"], 3.5, places=2)
            # Both reached orders are none.1907-36 / no.1937-89 one each: each stratum mean is $1 + $0.75.
            self.assertAlmostEqual(p["projection"]["usd_workers"]["point"], 41 * 1.75, places=1)
            self.assertIn("no.1990on", p["projection"]["borrowed_strata"])
            acq = list(csv.DictReader(open(root / "ATLAS/ACQUISITIONS.csv")))
            self.assertEqual(acq[0]["acquisition"], "nara scan")
            self.assertEqual(int(acq[0]["projected_orders"]), 20)

    def test_unattempted_step_is_unmeasured_not_free(self):
        r = {"reached": True, "open_steps": ["original_text", "clause_inventory"],
             "steps": {"original_text": {"outcome": "done"}}}
        self.assertTrue(project.eligible_for("original_text")(r))
        self.assertFalse(project.eligible_for("clause_inventory")(r))
        self.assertTrue(project.eligible_for("opus_media")(r))


if __name__ == "__main__":
    unittest.main()
