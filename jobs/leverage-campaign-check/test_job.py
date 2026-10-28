"""The offline replay must never mutate canonical output hardlinks."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location("campaign_job", Path(__file__).with_name("job.py"))
job = importlib.util.module_from_spec(spec)
spec.loader.exec_module(job)


class IsolationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.out = self.root / "jobs/leverage-campaign-check/output"
        self.out.mkdir(parents=True)
        (self.out / "sentinel.txt").write_text("prior wrapper output")
        self.inputs = self.root / "research/input.txt"
        self.inputs.parent.mkdir()
        self.inputs.write_text("held source")
        self.canonical = []
        for name in job.JOBS:
            folder = self.root / "jobs" / name
            (folder / "output").mkdir(parents=True)
            p = folder / "output/SUMMARY.json"
            p.write_text('{"canonical":true}')
            self.canonical.append(p)
            (folder / "job.py").write_text(
                'import json,os\nfrom pathlib import Path\n'
                'root=Path(os.environ["REPO_ROOT"])\n'
                'assert (root/"research/input.txt").read_text()=="held source"\n'
                'assert not (root/"jobs/leverage-campaign-check/output").exists()\n'
                'out=Path(os.environ["OUTPUT_DIR"])\n'
                '(out/"SUMMARY.json").write_text(json.dumps({"replayed":True}))\n'
            )
        self.env = patch.dict(os.environ, REPO_ROOT=str(self.root), OUTPUT_DIR=str(self.out))
        self.env.start()
        self.addCleanup(self.env.stop)

    def assert_preserved(self):
        self.assertEqual(self.inputs.read_text(), "held source")
        self.assertFalse((self.out / "replay").exists())
        for path in self.canonical:
            self.assertEqual(json.loads(path.read_text()), {"canonical": True})

    def test_real_subprocess_success_is_output_isolated(self):
        job.main()
        self.assert_preserved()
        result = json.loads((self.out / "VALIDATION.json").read_text())
        self.assertTrue(result["success"])
        self.assertEqual(len(result["commands"]), len(job.JOBS))
        self.assertTrue(json.loads((self.out / "readiness-tracker/SUMMARY.json").read_text())["replayed"])

    def test_failure_retains_receipt_and_stops_consumers(self):
        p = self.root / "jobs/claim-checker/job.py"
        p.write_text(p.read_text() + 'raise SystemExit(7)\n')
        with self.assertRaises(RuntimeError):
            job.main()
        self.assert_preserved()
        result = json.loads((self.out / "VALIDATION.json").read_text())
        self.assertFalse(result["success"])
        self.assertEqual([x["exit_code"] for x in result["commands"]], [7])
        self.assertFalse((self.out / "readiness-tracker").exists())

    def test_timeout_retains_failure_receipt_and_cleanup(self):
        with patch.object(job.subprocess, "run", side_effect=subprocess.TimeoutExpired("test", 1800)):
            with self.assertRaises(RuntimeError):
                job.main()
        self.assert_preserved()
        result = json.loads((self.out / "VALIDATION.json").read_text())
        self.assertFalse(result["success"])
        self.assertEqual(result["commands"][0]["exit_code"], 124)
        self.assertTrue(result["commands"][0]["timed_out"])


if __name__ == "__main__":
    unittest.main()
