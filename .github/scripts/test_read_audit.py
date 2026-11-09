"""Quo Warranto (read_audit.py): a job whose code reads an undeclared path must fail; declared reads pass.

Gutenberg, 2026-11-09. Each test pins one way a too-narrow declaration could let a stale result publish.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import read_audit as QW  # noqa: E402


def scope(roots=(), patterns=()):
    return {"roots": list(roots), "patterns": list(patterns), "exclude": "jobs/j/output"}


class CheckTest(unittest.TestCase):
    def test_file_must_be_declared(self):
        rec = {"opened": ["research/a/x.csv", "jobs/j/job.py", "jobs/other/output/T.csv"]}
        v = QW.check("j", rec, scope(["jobs/j", "research/a"]))["violations"]
        self.assertEqual(v, [{"kind": "file", "path": "jobs/other/output/T.csv"}])
        self.assertEqual(QW.check("j", rec, scope(["jobs/j", "research/a"], ["jobs/*/output/T.csv"]))["verdict"],
                         "covered")

    def test_own_output_cache_git_bytecode_ignored(self):
        rec = {"opened": ["jobs/j/output/OLD.json", ".git/HEAD", ".job-cache/j/x", "jobs/z/__pycache__/m.pyc"]}
        self.assertEqual(QW.check("j", rec, scope())["verdict"], "covered")

    def test_glob_must_be_covered_as_pattern_not_by_todays_files(self):
        """A glob finds tomorrow's files too; listing today's matches as literal inputs is too narrow."""
        rec = {"opened": ["jobs/p/output/FRAGMENTS.jsonl"], "globs": ["jobs/*/output/FRAGMENTS*.jsonl"]}
        narrow = scope(patterns=["jobs/p/output/FRAGMENTS.jsonl"])
        self.assertEqual([x["kind"] for x in QW.check("j", rec, narrow)["violations"]], ["glob"])
        self.assertEqual(QW.check("j", rec, scope(patterns=["jobs/*/output/FRAGMENTS*.jsonl"]))["verdict"], "covered")
        self.assertEqual(QW.check("j", rec, scope(patterns=["jobs/*/output/**"]))["verdict"], "covered")
        # a pattern with ? or [ cannot be shown to cover a glob
        self.assertEqual(QW.check("j", {"globs": ["jobs/*/x"]}, scope(patterns=["jobs/?/x"]))["verdict"],
                         "undeclared_reads")

    def test_glob_under_root(self):
        self.assertEqual(QW.check("j", {"globs": ["research/readiness/claims/*.jsonl"]},
                                  scope(["research/readiness"]))["verdict"], "covered")

    def test_listing_outside_any_glob(self):
        rec = {"listed": ["research/readiness/claims"]}
        self.assertEqual(QW.check("j", rec, scope())["verdict"], "undeclared_reads")
        self.assertEqual(QW.check("j", rec, scope(patterns=["research/readiness/claims/*"]))["verdict"], "covered")
        # a directory a recorded glob walks is judged by the glob
        rec = {"listed": ["jobs", "jobs/p/output"], "globs": ["jobs/*/output/FRAGMENTS*.jsonl"]}
        self.assertEqual(QW.check("j", rec, scope(patterns=["jobs/*/output/FRAGMENTS*.jsonl"]))["verdict"], "covered")
        # ... but not a directory the glob cannot reach
        rec = {"listed": ["jobs/p/data"], "globs": ["jobs/*/output/FRAGMENTS*.jsonl"]}
        self.assertEqual(QW.check("j", rec, scope(patterns=["jobs/*/output/FRAGMENTS*.jsonl"]))["verdict"],
                         "undeclared_reads")

    def test_children(self):
        tests = {"executable": sys.executable, "argv": [sys.executable, "-m", "unittest", "-v", "t"]}
        other = {"executable": sys.executable, "argv": [sys.executable, "helper.py"]}
        self.assertEqual(QW.check("j", {"children": [tests]}, scope())["verdict"], "covered")
        self.assertEqual(QW.check("j", {"children": [other]}, scope())["violations"][0]["kind"], "unaudited_python_child")
        self.assertEqual(QW.check("j", {"children": [{"hook_error": "open"}]}, scope())["verdict"], "undeclared_reads")


class RunTest(unittest.TestCase):
    """End to end: the hook sees reads in the job, its threads, globs and pathlib."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        (self.repo / "jobs/j").mkdir(parents=True)
        (self.repo / "research/a").mkdir(parents=True)
        (self.repo / "research/b").mkdir(parents=True)
        (self.repo / "research/a/x.txt").write_text("x")
        (self.repo / "research/b/secret.txt").write_text("y")
        (self.repo / "jobs/j/job.py").write_text(
            "import glob, os, threading\nfrom pathlib import Path\n"
            "R = Path(os.environ['REPO_ROOT'])\n"
            "open(R / 'research/a/x.txt').read()\n"
            "t = threading.Thread(target=lambda: (R / 'research/b/secret.txt').read_text()); t.start(); t.join()\n"
            "glob.glob(str(R / 'research/a/*.txt'))\n"
            "list((R / 'research').glob('*/notes*.md'))\n"
            "(R / 'jobs/j/output').mkdir(exist_ok=True); (R / 'jobs/j/output/o.txt').write_text('written')\n")

    def tearDown(self):
        self.tmp.cleanup()

    def record(self):
        rec = self.repo / "rec.json"
        env = {**os.environ, "REPO_ROOT": str(self.repo)}
        p = subprocess.run([sys.executable, str(HERE / "read_audit.py"), "run", "--record", str(rec), "--",
                            str(self.repo / "jobs/j/job.py")], env=env, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(rec.read_text())

    def test_reads_recorded_including_threads_and_globs(self):
        r = self.record()
        self.assertIn("research/a/x.txt", r["opened"])
        self.assertIn("research/b/secret.txt", r["opened"])  # read in a thread
        self.assertNotIn("jobs/j/output/o.txt", r["opened"])  # a write is not a read
        self.assertIn("research/a/*.txt", r["globs"])
        self.assertIn("research/*/notes*.md", r["globs"])

    def test_undeclared_read_fails_declared_passes(self):
        r = self.record()
        narrow = scope(["jobs/j", "research/a"])
        v = QW.check("j", r, narrow, repo=self.repo)
        self.assertEqual(v["verdict"], "undeclared_reads")
        self.assertIn({"kind": "file", "path": "research/b/secret.txt"}, v["violations"])
        self.assertIn({"kind": "glob", "path": "research/*/notes*.md"}, v["violations"])
        ok = scope(["jobs/j", "research/a", "research/b"], ["research/*/notes*.md"])
        self.assertEqual(QW.check("j", r, ok, repo=self.repo)["verdict"], "covered")

    def test_job_exit_code_kept(self):
        (self.repo / "jobs/j/job.py").write_text("import sys\nsys.exit('refused')\n")
        rec = self.repo / "rec.json"
        p = subprocess.run([sys.executable, str(HERE / "read_audit.py"), "run", "--record", str(rec), "--",
                            str(self.repo / "jobs/j/job.py")], env={**os.environ, "REPO_ROOT": str(self.repo)},
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 1)
        self.assertTrue(rec.is_file())


class RunnerWiringTest(unittest.TestCase):
    def test_runner_enforces_unless_report(self):
        src = (HERE / "run_jobs.py").read_text(encoding="utf-8")
        for needle in ('read_audit.py"), "run"', '!= "report"', "code = verdict"):
            self.assertTrue(needle in src, needle)


if __name__ == "__main__":
    unittest.main()
