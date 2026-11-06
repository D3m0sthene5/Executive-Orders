"""Exercise the Actions summary with mixed and partially written run receipts."""
import json
import os
from pathlib import Path
import tempfile
import unittest

import job_summary


class SummaryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(temporary.name)
        self.env = dict(JOBS="check tracker missing", DIRECT_JOBS="check",
                        GITHUB_SHA="head", GITHUB_RUN_ID="13", GITHUB_RUN_ATTEMPT="2",
                        PUBLISH_OUTCOME="failure", PICK_OUTCOME="success")

    def put(self, path, data):
        file = Path(path)
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(json.dumps(data), encoding="utf-8")

    def test_failed_publication_and_mixed_execution_states(self):
        self.put(job_summary.RECEIPTS / "ATTEMPTS.json",
                 [dict(job="check", publish_output=True, exit_code=0),
                  dict(job="tracker", publish_output=False, exit_code=125)])
        self.put(job_summary.RECEIPTS / "publication-check.json",
                 dict(result="rejected", problems=[dict(job="check", reason="inputs_changed")]))
        times = dict(started_utc="2026-11-04T00:00:00Z", finished_utc="2026-11-04T00:01:07Z",
                     commit_run="head", run_url="https://example.org/actions/runs/13")
        self.put("jobs/check/output/STATUS.json", dict(times, job="check", exit_code=0, result="succeeded"))
        self.put("jobs/_attempts/tracker/13-2/STATUS.json", dict(times, job="tracker", exit_code=125,
                                                                 result="blocked", blocked_by=["check"]))
        self.put("jobs/missing/output/STATUS.json", dict(times, job="missing", exit_code=0, result="succeeded"))
        text = job_summary.render(self.env)
        self.assertIn("Publication step failed.", text)
        self.assertIn("`inputs_changed`", text)
        self.assertIn("| `check` | Direct selection | Succeeded | 1m 07s |", text)
        self.assertIn("| `tracker` | Downstream consumer | Blocked by check | 1m 07s |", text)
        self.assertIn("| `missing` | Downstream consumer | No current receipt | — |", text)

    def test_prior_run_time_excluded_and_diagnostics_labeled(self):
        self.put(job_summary.RECEIPTS / "ATTEMPTS.json", [dict(job="check", publish_output=True, exit_code=0)])
        self.put("jobs/check/output/STATUS.json", dict(job="check", exit_code=0, result="succeeded",
                 commit_run="head", run_url="https://example.org/actions/runs/12",
                 started_utc="2026-11-04T00:00:00Z", finished_utc="2026-11-04T00:01:07Z"))
        text = job_summary.render(dict(self.env, DIAGNOSTIC="true", PUBLISH_OUTCOME="skipped"))
        self.assertIn("publication disabled", text)
        self.assertIn("Succeeded | — |", text)

    def test_arsenale_refusal_requeue_and_stations(self):
        self.put(job_summary.RECEIPTS / "ATTEMPTS.json", [dict(job="check", publish_output=True, exit_code=0),
                                                         dict(job="tracker", publish_output=True, exit_code=0)])
        self.put(job_summary.RECEIPTS / "ARSENALE.json", dict(
            lock_acquired_utc="2026-11-06T10:00:00Z",
            stations=[dict(station=1, jobs=["check"], started_utc="2026-11-06T09:50:00Z",
                           finished_utc="2026-11-06T09:59:00Z")],
            publication=dict(published=["tracker"], refused={"check": [dict(reason="inputs_changed",
                                                                            because_refused=["src"])]}),
            requeue=dict(dispatch=True, depth=1, limit=2, jobs=["check"], returncode=0)))
        text = job_summary.render(dict(self.env, PUBLICATION="pushed"))
        self.assertIn("Published: `tracker`.", text)
        self.assertIn("- Freshness check refused `check`: `inputs_changed` (it read a refused candidate of src).", text)
        self.assertIn("- Re-queued `check` at depth 1 of 2 (dispatched).", text)
        self.assertIn("| 1 | `check` | 2026-11-06T09:50:00Z to 2026-11-06T09:59:00Z |", text)
        self.assertIn("Writer lock acquired at 2026-11-06T10:00:00Z", text)

    def test_empty_selection_vs_incomplete_selection(self):
        self.assertIn("No production jobs selected.", job_summary.render(dict(self.env, JOBS="")))
        self.assertIn("Job selection unavailable.", job_summary.render(dict(self.env, JOBS="", PICK_OUTCOME="failure")))
        self.assertIn("Outputs unchanged", job_summary.render(dict(self.env, PUBLICATION="unchanged", PUBLISH_OUTCOME="success")))


if __name__ == "__main__":
    unittest.main()
