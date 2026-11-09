"""Carnot's failure modes, each pinned: watcher terminal states and back-off, worker cost lines that Bentham reads,
handoff packets built from git only, and the context check's unknown and over-threshold cases."""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "bentham"))
import await_run as A  # noqa: E402
import handoff as H  # noqa: E402
import worker as W  # noqa: E402


class Clock:
    def __init__(self):
        self.t = 0.0
        self.sleeps = []

    def now(self):
        return self.t

    def sleep(self, s):
        self.sleeps.append(s)
        self.t += s


def http(code):
    return urllib.error.HTTPError("u", code, "x", {}, io.BytesIO(b""))


class AwaitTests(unittest.TestCase):
    def run_(self, responses, **kw):
        it = iter(responses)
        c = Clock()

        def fetch(repo, run, token):
            r = next(it)
            if isinstance(r, Exception):
                raise r
            return r
        code, line = A.wait("o/r", 7, fetch_fn=fetch, sleep=c.sleep, clock=c.now, **kw)
        return code, line, c

    def test_every_terminal_state_prints_a_line(self):
        for conclusion in ("success", "failure", "cancelled", "timed_out", None):
            code, line, _ = self.run_([{"status": "in_progress"}, {"status": "completed", "conclusion": conclusion,
                                                                     "run_attempt": 2}])
            self.assertEqual(code, 0)
            self.assertIn(f"completed {conclusion}", line)
            self.assertIn("attempt 2", line)

    def test_not_found_timeout_and_errors(self):
        self.assertEqual(self.run_([http(404)])[0], 2)
        code, line, _ = self.run_([{"status": "queued"}] * 100, interval=600, max_hours=0.5)
        self.assertEqual(code, 3)
        self.assertIn("timeout", line)
        code, line, _ = self.run_([urllib.error.URLError("down")] * 10)
        self.assertEqual(code, 4)

    def test_rate_limit_backs_off_and_interval_floor(self):
        _, _, c = self.run_([http(403), http(429), {"status": "completed", "conclusion": "success"}], interval=5)
        self.assertEqual(c.sleeps, [120, 240])  # floor 60, doubled on each rate-limit answer


class WorkerTests(unittest.TestCase):
    def fake(self, payload, code=0):
        def runner(cmd, capture_output, text):
            self.cmd = cmd
            return subprocess.CompletedProcess(cmd, code, stdout=json.dumps(payload) if payload else "", stderr="")
        return runner

    def test_cost_line_is_what_bentham_reads(self):
        import sessions
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "prompt.txt"
            p.write_text("do the bounded task")
            sid = "12345678-aaaa-bbbb-cccc-1234567890ab"
            rc = W.run("producer-b01", "claude-sonnet-5-5", p, Path(t) / "COSTS.log", t,
                       runner=self.fake({"type": "result", "session_id": sid, "total_cost_usd": 0.42, "num_turns": 3}))
            self.assertEqual(rc, 0)
            self.assertIn("--model", self.cmd)
            rep = sessions.read_reported([Path(t) / "COSTS.log", Path(t) / "producer-b01.json"])
            self.assertEqual(rep[sid]["usd"], 0.42)
            self.assertEqual(len(rep), 1)  # the launched and done lines are not cost lines

    def test_failure_is_logged_and_nonzero(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "prompt.txt"
            p.write_text("x")
            self.assertEqual(W.run("b", "m", p, Path(t) / "C.log", t, runner=self.fake(None, code=2)), 2)
            self.assertEqual(W.run("c", "m", p, Path(t) / "C.log", t,
                                   runner=self.fake({"session_id": "s", "total_cost_usd": 1, "is_error": True})), 1)
            log = (Path(t) / "C.log").read_text()
            self.assertEqual(log.count(" failed "), 2)
            with self.assertRaises(SystemExit):
                W.run("bad label!", "m", p, Path(t) / "C.log", t, runner=self.fake({}))


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = Path(self.tmp.name) / "cfg"
        self.proj = self.cfg / "projects" / "-w"
        self.proj.mkdir(parents=True)
        self.env = dict(os.environ)
        os.environ["CLAUDE_CONFIG_DIR"] = str(self.cfg)
        os.environ["HOME"] = self.tmp.name

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.env)
        self.tmp.cleanup()

    def write(self, sid, calls, tail=""):
        recs = [{"type": "user", "message": {"content": "SECRET prompt text"}}]
        for i, (inp, read, wr) in enumerate(calls):
            recs.append({"type": "assistant", "message": {"id": f"m{i}", "model": "claude-opus-5-5", "usage": {
                "input_tokens": inp, "cache_read_input_tokens": read, "cache_creation_input_tokens": wr}}})
        (self.proj / f"{sid}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in recs) + tail)

    def test_unknown_is_never_zero(self):
        code, ctx = H.context()
        self.assertEqual((code, ctx["verdict"], ctx["tokens_per_call"]), (6, "unknown", None))

    def test_threshold_and_live_partial_line(self):
        self.write("aaaaaaaa-1", [(1, 100_000, 10), (2, 350_000, 100)], tail='{"type": "assistant", "mess')
        code, ctx = H.context()
        self.assertEqual((code, ctx["verdict"], ctx["tokens_per_call"]), (5, "hand_off", 350_102))
        code, ctx = H.context(threshold=400_000)
        self.assertEqual(code, 0)

    def test_packet_lists_uncommitted_and_carries_no_transcript_text(self):
        self.write("bbbbbbbb-2", [(1, 10, 1)])
        text, dirty, ctx = H.packet("phase-x", "resume at step 3", notes=["n1"], runs=["123"])
        self.assertNotIn("SECRET", text)
        self.assertIn("HEAD `", text)
        self.assertIn("await_run.py --run 123", text)
        self.assertIn("resume at step 3", text)
        self.assertIn(f"Uncommitted files ({len(dirty)})", text)

    def test_require_clean_refuses_dirty_tree(self):
        repo = Path(self.tmp.name) / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / "half-written.txt").write_text("x")
        old = H.REPO
        H.REPO = repo
        try:
            self.assertEqual(H.main(["write", "--phase", "p", "--next", "n", "--require-clean",
                                     "--out", str(repo / "packets")]), 7)
            self.assertEqual(H.main(["write", "--phase", "p", "--next", "n", "--out", str(repo / "packets")]), 0)
            self.assertIn("half-written.txt", next((repo / "packets").glob("*.md")).read_text())
        finally:
            H.REPO = old


if __name__ == "__main__":
    unittest.main()
