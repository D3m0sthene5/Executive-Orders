"""Offline fixture for output_branch_check.py (Justinian, 2026-11-06)."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().with_name("output_branch_check.py")


class OutputBranchCheck(unittest.TestCase):
    def run_git(self, *args):
        subprocess.run(["git", *args], cwd=self.repo, check=True, capture_output=True)

    def put(self, path, value):
        p = self.repo / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(value) if not isinstance(value, str) else value, encoding="utf-8")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.run_git("init", "-q", "-b", "main")
        self.run_git("config", "user.email", "f@example.invalid")
        self.run_git("config", "user.name", "fixture")
        self.put("jobs/a/output/STATUS.json", {"branch": "claude/old"})  # already on main: not this PR's doing
        self.run_git("add", "-A")
        self.run_git("commit", "-qm", "base")
        self.run_git("checkout", "-q", "-b", "feature")

    def check(self):
        return subprocess.run([sys.executable, str(SCRIPT), "--base", "main", "--target", "main"],
                              cwd=self.repo, capture_output=True, text=True)

    def test_clean_pull_request_passes(self):
        self.put("jobs/a/job.py", "print(1)\n")
        self.run_git("add", "-A")
        self.run_git("commit", "-qm", "code only")
        self.assertEqual(self.check().returncode, 0)

    def test_branch_output_refused_with_fix(self):
        self.put("jobs/b/output/STATUS.json", {"branch": "feature"})
        self.put("jobs/b/output/deep/STATUS.json", {"branch": "feature"})  # not a job STATUS
        self.run_git("add", "-A")
        self.run_git("commit", "-qm", "branch run")
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("jobs/b/output/STATUS.json", result.stdout)
        self.assertNotIn("deep", result.stdout)
        self.assertIn("git checkout main -- jobs/b/output", result.stdout)

    def test_main_generated_output_passes(self):
        self.put("jobs/a/output/STATUS.json", {"branch": "main"})
        self.run_git("add", "-A")
        self.run_git("commit", "-qm", "merged main output")
        self.assertEqual(self.check().returncode, 0)


if __name__ == "__main__":
    unittest.main()
