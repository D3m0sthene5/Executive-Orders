"""Tests for the Rattle Watch in run_jobs.py: heartbeat, stall stop, usual duration and push web budgets."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import pick_jobs  # noqa: E402
import run_jobs  # noqa: E402


class StallRule(unittest.TestCase):
    def test_needs_silence_and_idle_cpu_and_network_across_the_window(self):
        idle = [(0, 5.0, 1000), (600, 5.2, 1000), (1200, 5.4, 2000)]
        self.assertTrue(run_jobs.is_stalled(idle, silent_seconds=1200, stall_seconds=1200))
        self.assertFalse(run_jobs.is_stalled(idle, silent_seconds=1100, stall_seconds=1200))  # printed recently
        busy_cpu = [(0, 5.0, 1000), (1200, 65.0, 1000)]
        self.assertFalse(run_jobs.is_stalled(busy_cpu, 1200, 1200))
        busy_net = [(0, 5.0, 0), (1200, 5.0, 50_000_000)]
        self.assertFalse(run_jobs.is_stalled(busy_net, 1200, 1200))
        too_early = [(0, 5.0, 0), (600, 5.0, 0)]
        self.assertFalse(run_jobs.is_stalled(too_early, 1200, 1200))

    def test_never_stops_without_cpu_readings(self):
        self.assertFalse(run_jobs.is_stalled([(0, None, 0), (1200, None, 0)], 1200, 1200))

    def test_heartbeat_line_names_usual_duration_silence_and_activity(self):
        line = run_jobs.heartbeat_line("clark-discovery", 1320, 2820, 1200,
                                       [(1260, 10.0, 0), (1320, 41.0, 4_200_000)])
        self.assertEqual(line, "[Rattle Watch] clark-discovery: 22m elapsed (last successful run 47m), "
                               "last output 20m ago, CPU 31.0s in the last 60s, network 4.2 MB in the last 60s")


class WatchedProcess(unittest.TestCase):
    def run_child(self, code, watch):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "log.txt"
            started = time.monotonic()
            result = run_jobs.command([sys.executable, "-c", code], log, dict(os.environ), watch)
            return result, log.read_text(encoding="utf-8"), time.monotonic() - started

    def test_silent_idle_job_is_stopped_quickly(self):
        watch = {"name": "hung", "heartbeat": 0.2, "stall_minutes": 1 / 60, "usual": None,
                 "cpu": lambda pid: 1.0, "net": lambda: 0}
        code, log, took = self.run_child("import time; print('started', flush=True); time.sleep(60)", watch)
        self.assertEqual(code, run_jobs.STALL_EXIT)
        self.assertIn("started", log)
        self.assertIn("Rattle Watch stopped hung", log)
        self.assertLess(took, 20)

    def test_quiet_job_that_keeps_working_is_not_stopped(self):
        counter = {"cpu": 0.0}

        def cpu(pid):
            counter["cpu"] += 5.0  # the job keeps using CPU while printing nothing
            return counter["cpu"]

        watch = {"name": "busy", "heartbeat": 0.2, "stall_minutes": 1 / 60, "usual": 30.0, "cpu": cpu, "net": lambda: 0}
        code, log, _ = self.run_child("import time; time.sleep(2.5); print('done', flush=True)", watch)
        self.assertEqual(code, 0)
        self.assertIn("done", log)

    def test_unwatched_commands_behave_as_before(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "log.txt"
            self.assertEqual(run_jobs.command([sys.executable, "-c", "print('x')"], log, dict(os.environ)), 0)
            self.assertIn("x", log.read_text(encoding="utf-8"))


class JobSettings(unittest.TestCase):
    def test_stall_minutes_file_and_bounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.assertEqual(run_jobs.stall_minutes(folder), run_jobs.STALL_MINUTES)
            (folder / "STALL_MINUTES").write_text("45\n")
            self.assertEqual(run_jobs.stall_minutes(folder), 45)
            (folder / "STALL_MINUTES").write_text("0\n")
            with self.assertRaises(ValueError):
                run_jobs.stall_minutes(folder)

    def test_last_success_seconds_reads_prior_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            prior = Path(tmp)
            self.assertIsNone(run_jobs.last_success_seconds(prior))
            (prior / "STATUS.json").write_text(json.dumps({"result": "succeeded", "started_utc": "2026-10-22T18:00:00Z",
                                                           "finished_utc": "2026-10-22T18:47:00Z"}))
            self.assertEqual(run_jobs.last_success_seconds(prior), 47 * 60)
            (prior / "STATUS.json").write_text(json.dumps({"result": "failed", "started_utc": "2026-10-22T18:00:00Z",
                                                           "finished_utc": "2026-10-22T18:47:00Z"}))
            self.assertIsNone(run_jobs.last_success_seconds(prior))

    def test_web_search_jobs_are_recognised_by_their_triggers(self):
        root = SCRIPTS.parents[1] / "jobs"
        for name in ("clark-discovery", "lewis-originals"):
            if (root / name).is_dir():
                self.assertTrue(run_jobs.is_web_search_job(root / name), name)
        if (root / "readiness-tracker").is_dir():
            self.assertFalse(run_jobs.is_web_search_job(root / "readiness-tracker"))

    def test_downstream_only_excludes_directly_selected_jobs(self):
        self.assertEqual(pick_jobs.downstream_only(["readiness-tracker"], ["readiness-tracker", "clark-discovery", "lewis-originals"]),
                         ["clark-discovery", "lewis-originals"])
        self.assertEqual(pick_jobs.downstream_only(["clark-discovery"], ["clark-discovery"]), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
