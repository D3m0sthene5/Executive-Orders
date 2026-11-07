"""Offline tests for byte_budget: a throwaway git repository, no network."""
import contextlib
import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import byte_budget as B  # noqa: E402


def git(repo, *args):
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@t", GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)
    subprocess.run(["git", "-C", str(repo)] + list(args), check=True, capture_output=True, env=env)


def run_cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = B.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class Repo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = pathlib.Path(self.tmp.name)
        git(self.repo, "init", "-q", "-b", "main")
        (self.repo / "base.txt").write_bytes(b"base\n" * 100)
        git(self.repo, "add", "base.txt")
        git(self.repo, "commit", "-q", "-m", "base")
        git(self.repo, "tag", "base")

    def commit(self, name, size, seed=b"x"):
        p = self.repo / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes((seed * size)[:size])
        git(self.repo, "add", name)
        git(self.repo, "commit", "-q", "-m", name)


class PushTests(Repo):
    def test_counts_only_new_blobs(self):
        self.commit("a.bin", 1000, b"a")
        self.commit("sub/b.bin", 2000, b"b")
        blobs = B.new_blobs(self.repo, "base")
        self.assertEqual(sorted(s for s, _, _ in blobs), [1000, 2000])
        self.assertEqual({p for _, p, _ in blobs}, {"a.bin", "sub/b.bin"})

    def test_within_budget_exits_zero_and_over_budget_exits_one(self):
        self.commit("a.bin", 600_000, b"a")
        code, out, _ = run_cli("--repo", str(self.repo), "--base", "base", "--max-push-mib", "1")
        self.assertEqual(code, 0, out)
        self.commit("b.bin", 600_000, b"b")
        code, out, _ = run_cli("--repo", str(self.repo), "--base", "base", "--max-push-mib", "1")
        self.assertEqual(code, 1)
        self.assertIn("over the 1 MiB budget", out)

    def test_single_big_blob_trips_the_per_file_limit(self):
        self.commit("big.bin", 3 * B.MIB, b"z")
        code, out, _ = run_cli("--repo", str(self.repo), "--base", "base", "--max-file-mib", "2")
        self.assertEqual(code, 1)
        self.assertIn("big.bin", out)
        self.assertIn("per-file limit", out)

    def test_nothing_new_is_zero_bytes(self):
        code, out, _ = run_cli("--repo", str(self.repo), "--base", "HEAD")
        self.assertEqual(code, 0)
        self.assertIn("0.00 MiB", out)

    def test_unknown_base_is_exit_two(self):
        code, _, err = run_cli("--repo", str(self.repo), "--base", "no-such-ref")
        self.assertEqual(code, 2)
        self.assertIn("cannot measure", err)

    def test_identical_content_is_counted_once(self):
        self.commit("one.bin", 5000, b"q")
        self.commit("two.bin", 5000, b"q")      # same blob, two paths
        self.assertEqual(sum(s for s, _, _ in B.new_blobs(self.repo, "base")), 5000)


class OutputTests(Repo):
    def make_output(self, files):
        out = self.repo / "jobs" / "demo" / "output"
        for name, size in files.items():
            p = out / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"y" * size)
        return out

    def test_measure_dir(self):
        out = self.make_output({"a.json": 10, "raw/b.pdf": 30})
        total, count, files = B.measure_dir(out)
        self.assertEqual((total, count, files[0]), (40, 2, (30, "raw/b.pdf")))
        self.assertEqual(B.measure_dir(self.repo / "nope")[:2], (0, 0))

    def test_job_output_total_and_per_file_limits(self):
        self.make_output({"a.json": 600_000, "b.json": 600_000})
        code, out, _ = run_cli("--repo", str(self.repo), "--no-push", "--job", "demo", "--max-output-mib", "1")
        self.assertEqual(code, 1)
        self.assertIn("over the 1 MiB budget", out)
        code, _, _ = run_cli("--repo", str(self.repo), "--no-push", "--job", "demo", "--max-output-mib", "2")
        self.assertEqual(code, 0)
        code, out, _ = run_cli("--repo", str(self.repo), "--no-push", "--job", "demo", "--max-output-mib", "2",
                               "--max-file-mib", "0.5")
        self.assertEqual(code, 1)
        self.assertIn("per-file limit", out)

    def test_exclude_leaves_out_a_legacy_folder(self):
        out = self.make_output({"a.json": 100, "raw/old.pdf": 3_000_000})
        self.assertEqual(B.measure_dir(out, ["raw"])[:2], (100, 1))
        code, _, _ = run_cli("--repo", str(self.repo), "--no-push", "--job", "demo", "--max-output-mib", "1")
        self.assertEqual(code, 1)
        code, _, _ = run_cli("--repo", str(self.repo), "--no-push", "--job", "demo", "--max-output-mib", "1",
                             "--exclude", "raw")
        self.assertEqual(code, 0)

    def test_defaults_are_25_20_and_5_mib(self):
        self.assertEqual((B.DEFAULT_PUSH_MIB, B.DEFAULT_OUTPUT_MIB, B.DEFAULT_FILE_MIB), (25, 20, 5))

    def test_write_json(self):
        out = self.make_output({"a.json": 100})
        dst = self.repo / "BUDGET.json"
        code, _, _ = run_cli("--repo", str(self.repo), "--no-push", "--output-dir", str(out), "--write-json", str(dst))
        self.assertEqual(code, 0)
        data = json.loads(dst.read_text())
        self.assertTrue(data["ok"])
        self.assertEqual(data["reports"][0]["bytes"], 100)


if __name__ == "__main__":
    unittest.main()
