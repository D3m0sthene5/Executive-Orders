"""Arsenale contracts: parallel stations, lock-free execution, fresh-only publication.

Real Git histories in temporary folders: one bare origin, one clone per station
(executing the same pinned input commit at the same time), and a publisher clone
at the latest tip. GitHub's lock service and artifact transport are not emulated;
the hosted runs recorded in the pull request are the acceptance evidence for those.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parents[1]
sys.path.insert(0, str(SCRIPTS))
import arsenale  # noqa: E402
import pick_jobs  # noqa: E402

BASH = shutil.which("bash")
JOB = (
    "import json, os, time\nfrom pathlib import Path\n"
    "out = Path(os.environ['OUTPUT_DIR'])\n"
    "start = time.time()\n"
    "time.sleep(float(os.environ.get('FIXTURE_SLEEP', '0')))\n"
    "{body}\n"
    "out.joinpath('TIMES.json').write_text(json.dumps({{'start': start, 'end': time.time()}}))\n"
)


def scope(roots=(), patterns=(), name="x"):
    return {"roots": list(roots), "patterns": list(patterns), "exclude": f"jobs/{name}/output"}


class PlanTests(unittest.TestCase):
    def plan(self, order, after=None, reads=None):
        after = after or {}
        reads = reads or {}
        scopes = {n: scope(reads.get(n, {}).get("roots", ()), reads.get(n, {}).get("patterns", ()), n) for n in order}
        for n in order:
            scopes[n]["roots"] += [f"jobs/{d}/output" for d in after.get(n, [])]
        return arsenale.plan(order, scopes, lambda n: after.get(n, []))

    def test_after_chain_shares_a_station_and_independent_jobs_run_apart(self):
        result = self.plan(["a", "b", "c", "d"], after={"c": ["a"], "d": ["c"]})
        self.assertEqual([s["jobs"] for s in result["stations"]], [["a", "c", "d"], ["b"]])
        self.assertEqual(result["check_order"], ["a", "b", "c", "d"])
        self.assertEqual(result["after_edges"], [("a", "c"), ("c", "d")])

    def test_cross_station_reader_is_checked_before_the_producer(self):
        # A digest-like reader of every job's STATUS sees other stations' base outputs.
        result = self.plan(["a", "digest", "z"], after={"digest": ["a"]},
                           reads={"digest": {"patterns": ["jobs/*/output/STATUS.json"]}})
        self.assertEqual([s["jobs"] for s in result["stations"]], [["a", "digest"], ["z"]])
        order = result["check_order"]
        self.assertLess(order.index("a"), order.index("digest"))
        self.assertLess(order.index("digest"), order.index("z"))
        self.assertIn(("z", "digest"), result["cross_station_reads"])

    def test_mutual_cross_station_reads_merge_stations(self):
        result = self.plan(["a", "b"], reads={"a": {"roots": ["jobs/b/output"]}, "b": {"patterns": ["jobs/a/*"]}})
        self.assertEqual([s["jobs"] for s in result["stations"]], [["a", "b"]])
        self.assertEqual(result["merged_for_order"], [["a", "b"]])

    def test_whole_tree_reader_cannot_run_beside_a_job_it_follows(self):
        result = self.plan(["p", "q", "valla"], after={"valla": ["p"]}, reads={"valla": {"patterns": ["*"]}})
        self.assertEqual([s["jobs"] for s in result["stations"]], [["p", "valla"], ["q"]])
        self.assertLess(result["check_order"].index("valla"), result["check_order"].index("q"))

    def test_reads_output_is_conservative_and_exact_where_literal(self):
        target = "prod"
        for declared, expected in [
            (scope(roots=["jobs/prod/output"]), True), (scope(roots=["jobs/prod"]), True),
            (scope(roots=["jobs"]), True), (scope(roots=["."]), True),
            (scope(roots=["jobs/producer/output"]), False), (scope(roots=["research/x"]), False),
            (scope(patterns=["jobs/*/output/SUMMARY.json"]), True), (scope(patterns=["*"]), True),
            (scope(patterns=["jobs/pr*/x"]), True), (scope(patterns=["jobs/_lib/*.py"]), False),
            (scope(patterns=["research/*"]), False), (scope(patterns=["jobs/prod/output/A.json"]), True),
            (scope(patterns=["jobs/prod-other/output/*"]), False)]:
            with self.subTest(declared=declared):
                self.assertIs(arsenale.reads_output(declared, target), expected)

    def test_real_repository_daily_selection_splits_and_orders(self):
        os.chdir(ROOT)
        daily = sorted(n for n in os.listdir("jobs") if not n.startswith("_") and pick_jobs.runnable(n)
                       and (ROOT / "jobs" / n / "DAILY").is_file())
        order = pick_jobs.ordered(pick_jobs.with_consumers(daily))
        result = arsenale.plan(order)
        self.assertEqual(sorted(j for s in result["stations"] for j in s["jobs"]), sorted(order))
        self.assertEqual(sorted(result["check_order"]), sorted(order))
        station_of = {j: s["station"] for s in result["stations"] for j in s["jobs"]}
        for producer, consumer in result["after_edges"]:
            self.assertEqual(station_of[producer], station_of[consumer])
            self.assertLess(result["check_order"].index(producer), result["check_order"].index(consumer))
        for producer, reader in result["cross_station_reads"]:
            self.assertLess(result["check_order"].index(reader), result["check_order"].index(producer))
        for station in result["stations"]:
            positions = [result["check_order"].index(j) for j in station["jobs"]]
            self.assertEqual(positions, sorted(positions))
        # Only declared edges join stations: a job no selected job depends on runs alone.
        for name in order:
            linked = any(name in (p, c) for p, c in result["after_edges"])
            if not linked and not any(name in merged for merged in result["merged_for_order"]):
                self.assertIn([name], [s["jobs"] for s in result["stations"]])


class RiquetSegmentTests(unittest.TestCase):
    """Long after.txt chains run in segments of at most SEGMENT_MINUTES estimated minutes."""

    def plan(self, order, after, minutes, budget=45):
        result = arsenale.plan(order, scopes={n: {"roots": [], "patterns": [], "exclude": f"jobs/{n}/output"} for n in order},
                               after_of=lambda n: after.get(n, []))
        return arsenale.segment(result, budget, lambda n: minutes.get(n))

    def test_long_chain_keeps_its_head_and_defers_the_rest_in_order(self):
        after = {"b": ["a"], "c": ["b"], "d": ["c"]}
        r = self.plan(["a", "b", "c", "d", "x"], after, {"a": 20, "b": 20, "c": 50, "d": 5, "x": 30})
        self.assertEqual([s["jobs"] for s in r["stations"]], [["a", "b"], ["x"]])
        self.assertEqual(r["deferred"], ["c", "d"])
        self.assertEqual(set(r["check_order"]), {"a", "b", "x"})
        self.assertEqual([s["station"] for s in r["stations"]], [1, 2])
        full = arsenale.plan(["a", "b", "c", "d", "x"], scopes={n: {"roots": [], "patterns": [], "exclude": f"jobs/{n}/output"}
                             for n in "abcdx"}, after_of=lambda n: after.get(n, []))
        self.assertEqual(r["check_order"], [j for j in full["check_order"] if j in {"a", "b", "x"}])  # filtered, not reordered

    def test_a_long_first_job_still_runs_and_unknown_jobs_use_the_default(self):
        r = self.plan(["a", "b"], {"b": ["a"]}, {"a": 200})
        self.assertEqual(r["stations"][0]["jobs"], ["a"])
        self.assertEqual(r["deferred"], ["b"])
        self.assertEqual(r["estimates"]["b"], arsenale.DEFAULT_JOB_MINUTES)
        short = self.plan(["a", "b", "c"], {"b": ["a"], "c": ["b"]}, {})  # 3 x 10 default minutes fit
        self.assertEqual(short["deferred"], [])

    def test_a_long_job_does_not_hold_short_stations_hostage(self):
        # publish waits for every station: a 90-minute head waits for a run of its own
        r = self.plan(["long", "a", "b"], {"b": ["a"]}, {"long": 90, "a": 20, "b": 20})
        self.assertEqual([s["jobs"] for s in r["stations"]], [["a", "b"]])
        self.assertEqual(r["deferred"], ["long"])
        self.assertEqual(r["long_heads"], ["long"])
        # when every station is headed by a long job, they run together: progress is guaranteed
        both = self.plan(["l1", "l2"], {}, {"l1": 90, "l2": 70})
        self.assertEqual(sorted(j for s in both["stations"] for j in s["jobs"]), ["l1", "l2"])
        self.assertEqual(both["deferred"], [])

    def test_every_segment_makes_progress_until_the_chain_is_done(self):
        after = {"b": ["a"], "c": ["b"], "d": ["c"], "e": ["d"]}
        minutes = {"a": 40, "b": 40, "c": 40, "d": 40, "e": 40, "z": 100}
        todo, runs = ["a", "b", "c", "d", "e", "z"], 0
        while todo:
            r = self.plan(todo, {k: [d for d in v if d in todo] for k, v in after.items()}, minutes)
            kept = [j for s in r["stations"] for j in s["jobs"]]
            self.assertTrue(kept)
            todo, runs = r["deferred"], runs + 1
            self.assertLess(runs, 10)
        self.assertEqual(runs, 6)  # five 40-minute links one by one, then the long job alone

    def test_budget_halves_with_each_requeue_generation_and_tolerates_bad_settings(self):
        with mock.patch.dict(os.environ, {"REQUEUE_DEPTH": "0", "ARSENALE_SEGMENT_MINUTES": "", "CONTINUATION": "0",
                                          "DIAGNOSTIC": "false"}):
            self.assertEqual(arsenale.segment_budget(), arsenale.SEGMENT_MINUTES)
            os.environ["REQUEUE_DEPTH"] = "2"
            self.assertEqual(arsenale.segment_budget(), arsenale.SEGMENT_MINUTES / 4)
            os.environ.update(REQUEUE_DEPTH="0", ARSENALE_SEGMENT_MINUTES="lots")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(arsenale.segment_budget(), arsenale.SEGMENT_MINUTES)
            os.environ.update(ARSENALE_SEGMENT_MINUTES="0")
            self.assertEqual(arsenale.segment_budget(), 0)

    def test_budget_zero_runs_everything(self):
        r = self.plan(["a", "b"], {"b": ["a"]}, {"a": 500, "b": 500}, budget=0)
        self.assertEqual(r["deferred"], [])
        self.assertEqual(r["stations"][0]["jobs"], ["a", "b"])

    def test_recorded_minutes_reads_the_last_published_status(self):
        with tempfile.TemporaryDirectory() as temporary, contextlib.chdir(temporary):
            for args in (["init", "-q", "-b", "main"], ["config", "user.email", "t@example.invalid"], ["config", "user.name", "t"]):
                subprocess.run(["git", *args], check=True)
            Path("jobs/a/output").mkdir(parents=True)
            for finished in ("01:30:30", "01:05:00"):  # a slow run, then a fast (cached) one
                Path("jobs/a/output/STATUS.json").write_text(json.dumps(
                    {"started_utc": "2026-11-07T01:00:00Z", "finished_utc": f"2026-11-07T{finished}Z"}))
                subprocess.run(["git", "add", "-A"], check=True)
                subprocess.run(["git", "commit", "-qm", "x"], check=True)
            self.assertAlmostEqual(arsenale.recorded_minutes("a"), 30.5)  # the longest recent run, not the latest
            self.assertAlmostEqual(arsenale.recorded_minutes("a", runs=1), 5.0)
            self.assertIsNone(arsenale.recorded_minutes("missing"))

    def test_plan_command_writes_the_deferred_output_and_respects_diagnostics(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "out"
            fake = {"stations": [{"station": 1, "jobs": ["a", "b"], "cache": "x"}], "order": ["a", "b"],
                    "check_order": ["a", "b"], "after_edges": [("a", "b")], "cross_station_reads": [], "merged_for_order": []}
            base = {"JOBS": "a b", "GITHUB_OUTPUT": str(out), "GITHUB_STEP_SUMMARY": str(Path(temporary) / "s.md")}
            with contextlib.chdir(temporary), mock.patch.object(arsenale, "plan", return_value=fake), \
                    mock.patch.object(arsenale, "recorded_minutes", return_value=40), \
                    mock.patch.object(arsenale, "git", return_value=subprocess.CompletedProcess([], 0, "abc\n", "")), \
                    contextlib.redirect_stdout(io.StringIO()):
                for env, expected in ((dict(base), "b"), (dict(base, DIAGNOSTIC="true"), ""),
                                      (dict(base, CONTINUATION=str(arsenale.MAX_CONTINUATIONS)), "")):
                    out.write_text("")
                    with mock.patch.dict(os.environ, env, clear=False):
                        os.environ.pop("ARSENALE_SEGMENT_MINUTES", None)
                        arsenale.command_plan(None)
                    values = dict(line.split("=", 1) for line in out.read_text().splitlines())
                    self.assertEqual(values["deferred"], expected, env)


class RequeueTests(unittest.TestCase):
    def test_deferred_jobs_continue_without_spending_requeue_depth(self):
        d = arsenale.requeue_plan([], 0, ["c"], "run-jobs.yml", "main", deferred=["c", "d"], continuation=0)
        self.assertEqual(d["command"], ["gh", "workflow", "run", "run-jobs.yml", "--ref", "main",
                                        "-f", "job=c d", "-f", "requeue_depth=0", "-f", "downstream=c",
                                        "-f", "continuation=1"])
        both = arsenale.requeue_plan(["a"], 1, [], "run-jobs.yml", "main", deferred=["a", "c"], continuation=3)
        self.assertEqual(both["jobs"], ["a", "c"])
        self.assertIn("requeue_depth=2", both["command"])
        self.assertIn("continuation=4", both["command"])
        capped = arsenale.requeue_plan(["a"], arsenale.MAX_REQUEUE_DEPTH, [], "run-jobs.yml", "main", deferred=["c"])
        self.assertEqual((capped["jobs"], capped["dropped_at_requeue_limit"]), (["c"], ["a"]))
        retry_only = arsenale.requeue_plan(["a"], 0, [], "run-jobs.yml", "main", continuation=2)
        self.assertIn("continuation=2", retry_only["command"])  # a retry inside a continuation keeps its count

    def test_deferred_jobs_after_a_failed_job_are_held_back(self):
        after = {"c": ["b"], "d": ["c"], "e": ["x"]}
        attempts = [{"job": "a", "publish_output": True}, {"job": "b", "publish_output": False}]
        self.assertEqual(arsenale.blocked_by_failures(["c", "d", "e"], attempts, lambda n: after.get(n, [])), ["c", "d"])

    def test_requeue_command_continues_deferred_jobs(self):
        with tempfile.TemporaryDirectory() as temporary, contextlib.chdir(temporary):
            arsenale.write_json(arsenale.REPORT, {"publication": {"outcome": "pushed", "refused": {}}})
            arsenale.write_json(arsenale.RECEIPTS / "ATTEMPTS.json", [{"job": "a", "publish_output": True}])
            ran = subprocess.CompletedProcess([], 0, "", "")
            with mock.patch.dict(os.environ, {"REQUEUE_DEPTH": "0", "BRANCH": "main", "DEFERRED": "b",
                                              "CONTINUATION": "0"}), \
                    mock.patch.object(arsenale, "after", return_value=["a"]), \
                    mock.patch.object(arsenale.subprocess, "run", return_value=ran) as run, \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(arsenale.main(["requeue", "--workflow", "run-jobs.yml"]), 0)
            self.assertIn("continuation=1", run.call_args.args[0])
            self.assertIn("job=b", run.call_args.args[0])
            # A run whose results never reached the branch does not continue.
            arsenale.write_json(arsenale.REPORT, {"publication": {"outcome": "push-failed", "refused": {}}})
            with mock.patch.dict(os.environ, {"REQUEUE_DEPTH": "0", "BRANCH": "main", "DEFERRED": "b"}), \
                    mock.patch.object(arsenale.subprocess, "run") as run, contextlib.redirect_stdout(io.StringIO()):
                arsenale.main(["requeue", "--workflow", "run-jobs.yml"])
            run.assert_not_called()
            self.assertEqual(arsenale.read_json(arsenale.REPORT)["requeue"]["reason"], "nothing_refused")

    def test_first_refusal_dispatches_exactly_the_refused_jobs(self):
        decision = arsenale.requeue_plan(["beta", "gamma"], 0, ["gamma"], "run-jobs.yml", "claude/x")
        self.assertTrue(decision["dispatch"])
        self.assertEqual(decision["command"], ["gh", "workflow", "run", "run-jobs.yml", "--ref", "claude/x",
                                               "-f", "job=beta gamma", "-f", "requeue_depth=1",
                                               "-f", "downstream=gamma"])

    def test_requeue_is_bounded(self):
        self.assertTrue(arsenale.requeue_plan(["beta"], 1, [], "run-jobs.yml", "main")["dispatch"])
        stop = arsenale.requeue_plan(["beta"], arsenale.MAX_REQUEUE_DEPTH, [], "run-jobs.yml", "main")
        self.assertFalse(stop["dispatch"])
        self.assertEqual(stop["reason"], "requeue_limit_reached")
        self.assertEqual(arsenale.requeue_plan([], 0, [], "run-jobs.yml", "main")["reason"], "nothing_refused")

    def test_refresh_requeue_reruns_the_fixed_reporting_selection(self):
        decision = arsenale.requeue_plan(["daily-digest"], 0, [], "refresh-readiness.yml", "main")
        self.assertEqual(decision["command"], ["gh", "workflow", "run", "refresh-readiness.yml", "--ref", "main",
                                               "-f", "requeue_depth=1"])

    def test_requeue_command_records_dispatch_and_limit(self):
        with tempfile.TemporaryDirectory() as temporary, contextlib.chdir(temporary):
            arsenale.write_json(arsenale.REPORT, {"publication": {"refused": {"beta": [{"reason": "inputs_changed"}]}}})
            ran = subprocess.CompletedProcess([], 0, "", "")
            with mock.patch.dict(os.environ, {"REQUEUE_DEPTH": "", "BRANCH": "b"}), \
                    mock.patch.object(arsenale.subprocess, "run", return_value=ran) as run, \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(arsenale.main(["requeue", "--workflow", "run-jobs.yml"]), 0)
            self.assertIn("requeue_depth=1", run.call_args.args[0])
            self.assertEqual(arsenale.read_json(arsenale.REPORT)["requeue"]["depth"], 1)
            with mock.patch.dict(os.environ, {"REQUEUE_DEPTH": "2", "BRANCH": "b"}), \
                    mock.patch.object(arsenale.subprocess, "run") as run, \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(arsenale.main(["requeue", "--workflow", "run-jobs.yml"]), 0)
            run.assert_not_called()
            self.assertEqual(arsenale.read_json(arsenale.REPORT)["requeue"]["reason"], "requeue_limit_reached")

    def test_picker_reruns_requeued_jobs_exactly_with_their_budget(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "out"
            env = dict(os.environ, EVENT="workflow_dispatch", INPUT_JOB="readiness-tracker clark-discovery",
                       DIAGNOSTIC="false", REQUEUE_DEPTH="1", INPUT_DOWNSTREAM="clark-discovery",
                       GITHUB_OUTPUT=str(output))
            subprocess.run([sys.executable, str(SCRIPTS / "pick_jobs.py")], cwd=ROOT, env=env, check=True,
                           capture_output=True)
            values = dict(line.split("=", 1) for line in output.read_text().splitlines())
            self.assertEqual(values["jobs"], "readiness-tracker clark-discovery")
            self.assertEqual(values["downstream"], "clark-discovery")
            output.unlink()
            subprocess.run([sys.executable, str(SCRIPTS / "pick_jobs.py")], cwd=ROOT, check=True, capture_output=True,
                           env=dict(env, REQUEUE_DEPTH="0", INPUT_DOWNSTREAM=""))
            ordinary = dict(line.split("=", 1) for line in output.read_text().splitlines())
            self.assertIn("domesday-register", ordinary["jobs"].split())  # consumers join an ordinary dispatch
            bad = subprocess.run([sys.executable, str(SCRIPTS / "pick_jobs.py")], cwd=ROOT, capture_output=True,
                                 env=dict(env, REQUEUE_DEPTH="x"), text=True)
            self.assertNotEqual(bad.returncode, 0)
            output.unlink()
            subprocess.run([sys.executable, str(SCRIPTS / "pick_jobs.py")], cwd=ROOT, check=True, capture_output=True,
                           env=dict(env, REQUEUE_DEPTH="0", CONTINUATION="1", INPUT_DOWNSTREAM=""))
            continued = dict(line.split("=", 1) for line in output.read_text().splitlines())
            self.assertEqual(continued["jobs"], "readiness-tracker clark-discovery")  # exactly the deferred jobs
            output.unlink()
            gone = subprocess.run([sys.executable, str(SCRIPTS / "pick_jobs.py")], cwd=ROOT, capture_output=True, text=True,
                                  env=dict(env, REQUEUE_DEPTH="0", CONTINUATION="1", INPUT_JOB="no-such-job readiness-tracker"))
            self.assertEqual(gone.returncode, 0, gone.stderr)  # a job removed since it was queued is skipped
            self.assertEqual(dict(l.split("=", 1) for l in output.read_text().splitlines())["jobs"], "readiness-tracker")


class StationFixture(unittest.TestCase):
    """origin (bare), stations s1/s2 at the pinned commit, publisher at the latest tip."""

    TOKEN = ("4242", "1")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="arsenale ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.origin = self.root / "origin.git"
        self.author = self.root / "author"
        self.sh(["git", "init", "--bare", "-b", "main", str(self.origin)], self.root)
        self.sh(["git", "-c", "core.autocrlf=false", "clone", str(self.origin), str(self.author)], self.root)
        self.configure(self.author)
        shutil.copytree(SCRIPTS, self.author / ".github/scripts", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT / "jobs/_lib", self.author / "jobs/_lib", ignore=shutil.ignore_patterns("__pycache__"))
        self.put(".github/workflows/run-jobs.yml", "# fixture runner\n")
        self.put("research/alpha/request.txt", "alpha input v1\n")
        self.put("research/beta/request.txt", "beta input v1\n")
        self.job("alpha", "out.joinpath('result.txt').write_text(Path('research/alpha/request.txt').read_text())",
                 needs="research/alpha\n")
        self.job("beta", "out.joinpath('result.txt').write_text(Path('research/beta/request.txt').read_text())",
                 needs="research/beta\n")
        self.job("gamma", "out.joinpath('result.txt').write_text('saw ' + Path('jobs/alpha/output/result.txt').read_text())",
                 after="alpha\n")
        for name in ("alpha", "beta", "gamma"):
            self.put(f"jobs/{name}/output/result.txt", f"{name} baseline\n")
        self.input_commit = self.commit("baseline")

    # -------------------------------------------------------------- helpers
    def sh(self, args, cwd, env=None, check=True):
        result = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                                env={**os.environ, "GIT_ALLOW_PROTOCOL": "file", "PYTHONDONTWRITEBYTECODE": "1",
                                     **(env or {})})
        if check and result.returncode:
            raise AssertionError(f"{args}: {result.returncode}\n{result.stdout}\n{result.stderr}")
        return result

    def configure(self, repo):
        for key, value in (("user.name", "Arsenale fixture"), ("user.email", "fixture@example.invalid"),
                           ("core.autocrlf", "false"), ("commit.gpgsign", "false")):
            self.sh(["git", "config", key, value], repo)

    def put(self, path, text, repo=None):
        target = (repo or self.author) / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")

    def job(self, name, body, needs="", after=""):
        self.put(f"jobs/{name}/job.py", JOB.format(body=body))
        if needs:
            self.put(f"jobs/{name}/needs.txt", needs)
        if after:
            self.put(f"jobs/{name}/after.txt", after)

    def commit(self, message, repo=None):
        repo = repo or self.author
        self.sh(["git", "add", "-A"], repo)
        self.sh(["git", "commit", "-qm", message], repo)
        self.sh(["git", "push", "-q", "origin", "HEAD:main"], repo)
        return self.sh(["git", "rev-parse", "HEAD"], repo).stdout.strip()

    # Clone with autocrlf off (as the freshness fixture does): a Windows runner's
    # global autocrlf=true would rewrite working files and change their hashes.
    def clone(self, name, commit):
        path = self.root / name
        self.sh(["git", "-c", "core.autocrlf=false", "clone", "-q", str(self.origin), str(path)], self.root)
        self.configure(path)
        self.sh(["git", "checkout", "-q", "--detach", commit], path)
        return path

    def env(self, jobs, **extra):
        return {"JOBS": " ".join(jobs), "GITHUB_RUN_ID": self.TOKEN[0], "GITHUB_RUN_ATTEMPT": self.TOKEN[1],
                "GITHUB_REF_NAME": "main", "GITHUB_SHA": self.input_commit,
                "ARSENALE_INPUT_COMMIT": self.input_commit, "RATTLE_HEARTBEAT_SECONDS": "60", **extra}

    def plan(self):
        planner = self.clone("planner", self.input_commit)
        output = self.root / "plan.outputs"
        self.sh([sys.executable, ".github/scripts/arsenale.py", "plan"], planner,
                 env=self.env(["alpha", "beta", "gamma"], GITHUB_OUTPUT=str(output)))
        values = dict(line.split("=", 1) for line in output.read_text().splitlines())
        return values, json.loads(values["matrix"])["include"]

    def execute(self, stations, sleep="2"):
        """Start every station at once, each in its own clone of the pinned commit."""
        running = []
        for station in stations:
            repo = self.clone(f"station-{station['station']}", self.input_commit)
            env = {**os.environ, "GIT_ALLOW_PROTOCOL": "file", "PYTHONDONTWRITEBYTECODE": "1",
                   **self.env(station["jobs"].split(), FIXTURE_SLEEP=sleep)}
            running.append((station, repo, subprocess.Popen(
                [sys.executable, ".github/scripts/run_jobs.py"], cwd=repo, env=env,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)))
        artifacts = self.root / "artifacts"
        for station, repo, process in running:
            log = process.communicate(timeout=120)[0]
            self.assertEqual(process.returncode, 0, log)
            out = artifacts / f"arsenale-{self.TOKEN[0]}-{self.TOKEN[1]}-station-{station['station']}"
            self.sh([sys.executable, ".github/scripts/arsenale.py", "bundle", "--station", str(station["station"]),
                      "--out", str(out)], repo, env=self.env(station["jobs"].split()))
        return artifacts, {station["station"]: repo for station, repo, _ in running}

    def publish(self, order, artifacts, hook=None, event="workflow_dispatch", extra=None):
        publisher = self.root / "publisher"
        self.sh(["git", "-c", "core.autocrlf=false", "clone", "-q", str(self.origin), str(publisher)], self.root)
        self.configure(publisher)
        if hook:
            target = publisher / ".git/hooks/pre-push"
            target.write_text(hook, encoding="utf-8", newline="\n")
            target.chmod(0o755)
        env = self.env(order, BRANCH="main", EVENT=event, RUN_URL="https://example.invalid/runs/4242",
                       ARSENALE_RETRY_SECONDS="0", GITHUB_STEP_SUMMARY=str(self.root / "summary.md"),
                       GITHUB_OUTPUT=str(self.root / "publish.outputs"), **(extra or {}))
        self.sh([sys.executable, ".github/scripts/arsenale.py", "collect", "--artifacts", str(artifacts)],
                 publisher, env=env)
        result = self.sh([sys.executable, ".github/scripts/arsenale.py", "publish"], publisher, env=env, check=False)
        report = json.loads((publisher / arsenale.REPORT).read_text())
        return result, report, publisher

    def show(self, path, ref="main"):
        return self.sh(["git", "--git-dir", str(self.origin), "show", f"{ref}:{path}"], self.root).stdout

    def subject(self, ref="main"):
        return self.sh(["git", "--git-dir", str(self.origin), "log", "-1", "--format=%s%n%b", ref],
                        self.root).stdout.strip()

    def advance(self, path, text):
        self.sh(["git", "pull", "-q", "--rebase", "origin", "main"], self.author)
        self.put(path, text)
        return self.commit("concurrent input change")


class ParallelPublicationTests(StationFixture):
    def test_stations_overlap_and_fresh_jobs_publish_in_one_commit(self):
        values, stations = self.plan()
        self.assertEqual(values["input_commit"], self.input_commit)
        self.assertEqual([s["jobs"] for s in stations], ["alpha gamma", "beta"])
        artifacts, repos = self.execute(stations)
        alpha = json.loads((repos[1] / "jobs/alpha/output/TIMES.json").read_text())
        beta = json.loads((repos[2] / "jobs/beta/output/TIMES.json").read_text())
        gamma = json.loads((repos[1] / "jobs/gamma/output/TIMES.json").read_text())
        self.assertLess(max(alpha["start"], beta["start"]), min(alpha["end"], beta["end"]), "stations did not overlap")
        self.assertGreaterEqual(gamma["start"], alpha["end"], "after.txt order broken inside a station")
        result, report, _ = self.publish(values["check_order"].split(), artifacts)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.subject(), "Results of job(s): alpha beta gamma\nRun: https://example.invalid/runs/4242")
        self.assertEqual(self.show("jobs/gamma/output/result.txt"), "saw alpha input v1\n")
        self.assertEqual(self.show("jobs/beta/output/result.txt"), "beta input v1\n")
        status = json.loads(self.show("jobs/beta/output/STATUS.json"))
        self.assertEqual(status["commit_run"], self.input_commit)
        self.assertEqual(report["publication"]["published"], ["alpha", "beta", "gamma"])
        self.assertEqual(report["publication"]["refused"], {})
        self.assertEqual([s["jobs"] for s in report["stations"]], [["alpha", "gamma"], ["beta"]])

    def test_input_changed_during_execution_is_refused_and_others_publish(self):
        values, stations = self.plan()
        artifacts, _ = self.execute(stations, sleep="0")
        self.advance("research/beta/request.txt", "beta input v2\n")
        result, report, _ = self.publish(values["check_order"].split(), artifacts)
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertEqual(self.subject().splitlines()[0], "Results of job(s): alpha gamma")
        self.assertEqual(self.show("jobs/beta/output/result.txt"), "beta baseline\n")
        self.assertEqual(self.show("jobs/alpha/output/result.txt"), "alpha input v1\n")
        refused = report["publication"]["refused"]
        self.assertEqual(list(refused), ["beta"])
        self.assertEqual(refused["beta"][0]["reason"], "inputs_changed")
        self.assertIn("research/beta/request.txt", json.dumps(refused["beta"]))
        self.assertIn("research/beta/request.txt", (self.root / "summary.md").read_text())

    def test_refresh_publishes_data_drift_as_of_its_input_commit(self):
        values, stations = self.plan()
        artifacts, _ = self.execute(stations, sleep="0")
        self.advance("research/beta/request.txt", "beta input v2\n")
        result, report, _ = self.publish(values["check_order"].split(), artifacts,
                                         extra={"ARSENALE_AS_OF_READOUT": "1"})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.subject().splitlines()[0], "Results of job(s): alpha beta gamma")
        self.assertIn("data inputs advanced since for: beta", self.subject())
        self.assertEqual(self.show("jobs/beta/output/result.txt"), "beta input v1\n")
        publication = report["publication"]
        self.assertEqual(publication["refused"], {})
        self.assertEqual(publication["published_as_of"]["beta"]["input_commit"], self.input_commit)
        self.assertIn("research/beta/request.txt", publication["published_as_of"]["beta"]["changed_paths_sample"])

    def test_per_job_as_of_readout_in_run_jobs(self):
        """Gutenberg item 7: jobs/<name>/AS_OF_READOUT opts one job into Hansard's rule outside the refresh workflow."""
        self.put("jobs/beta/AS_OF_READOUT", "daily-digest-like readout\n")
        self.input_commit = self.commit("beta reads everything; publish it as of its input commit")
        values, stations = self.plan()
        artifacts, _ = self.execute(stations, sleep="0")
        self.advance("research/beta/request.txt", "beta input v2\n")
        result, report, _ = self.publish(values["check_order"].split(), artifacts)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("data inputs advanced since for: beta", self.subject())
        self.assertIn("Per-job as-of readout", self.subject())
        self.assertEqual(report["publication"]["published_as_of"]["beta"]["input_commit"], self.input_commit)

    def test_per_job_as_of_does_not_extend_to_other_jobs(self):
        self.put("jobs/beta/AS_OF_READOUT", "only beta\n")
        self.input_commit = self.commit("beta only")
        values, stations = self.plan()
        artifacts, _ = self.execute(stations, sleep="0")
        self.advance("research/alpha/request.txt", "alpha input v2\n")
        result, report, _ = self.publish(values["check_order"].split(), artifacts)
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertIn("alpha", report["publication"]["refused"])
        self.assertNotIn("alpha", report["publication"].get("published_as_of", {}))

    def test_refresh_still_refuses_code_drift_and_its_consumers(self):
        self.assertTrue(arsenale.as_of_acceptable(
            [{"reason": "inputs_changed", "changed_path_count": 1,
              "changed_paths": [{"path": "jobs/repetita-lsa/output/FRAGMENTS.2009.jsonl"}]}], ["alpha"]))
        self.assertFalse(arsenale.as_of_acceptable(
            [{"reason": "inputs_changed", "changed_path_count": 1,
              "changed_paths": [{"path": "research/alpha/request.py"}]}], []))
        self.assertFalse(arsenale.as_of_acceptable(
            [{"reason": "inputs_changed", "changed_path_count": 1,
              "changed_paths": [{"path": "jobs/alpha/output/result.txt"}]}], ["alpha", "gamma"]))
        self.assertFalse(arsenale.as_of_acceptable([{"reason": "concurrent_output_advanced"}], []))
        self.assertFalse(arsenale.as_of_acceptable(
            [{"reason": "inputs_changed", "changed_path_count": 2,
              "changed_paths": [{"path": "research/x.csv"}]}], []))

    def test_refresh_mode_still_refuses_concurrent_publication(self):
        values, stations = self.plan()
        artifacts, _ = self.execute(stations, sleep="0")
        self.sh(["git", "pull", "-q", "--rebase", "origin", "main"], self.author)
        self.put("jobs/beta/output/result.txt", "another run published first\n")
        self.commit("Results of job(s): beta")
        result, report, _ = self.publish(values["check_order"].split(), artifacts,
                                         extra={"ARSENALE_AS_OF_READOUT": "1"})
        self.assertEqual(result.returncode, 3)
        self.assertEqual(report["publication"]["refused"]["beta"][0]["reason"], "concurrent_output_advanced")
        self.assertNotIn("published_as_of", report["publication"])

    def test_consumer_of_refused_producer_is_refused_too(self):
        values, stations = self.plan()
        artifacts, _ = self.execute(stations, sleep="0")
        self.advance("research/alpha/request.txt", "alpha input v2\n")
        result, report, publisher = self.publish(values["check_order"].split(), artifacts)
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertEqual(self.subject().splitlines()[0], "Results of job(s): beta")
        refused = report["publication"]["refused"]
        self.assertEqual(sorted(refused), ["alpha", "gamma"])
        self.assertEqual(refused["gamma"][-1]["because_refused"], ["alpha"])
        self.assertEqual(self.show("jobs/gamma/output/result.txt"), "gamma baseline\n")
        # The refused generations stay with the run's downloads.
        self.assertTrue((publisher / "oversized/refused/alpha/result.txt").is_file())

    def test_push_race_retries_rechecks_and_drops_only_the_newly_stale_job(self):
        values, stations = self.plan()
        artifacts, _ = self.execute(stations, sleep="0")
        racer = self.root / "racer.py"
        racer.write_text(
            "import subprocess, pathlib\nr = pathlib.Path(" + repr(str(self.author)) + ")\n"
            "subprocess.run(['git', 'pull', '-q', '--rebase', 'origin', 'main'], cwd=r, check=True)\n"
            "(r / 'research/beta/request.txt').write_text('beta raced during push\\n')\n"
            "(r / 'unrelated.txt').write_text('unrelated\\n')\n"
            "for a in (['add', '-A'], ['commit', '-qm', 'race'], ['push', '-q', 'origin', 'HEAD:main']):\n"
            "    subprocess.run(['git', *a], cwd=r, check=True)\n", encoding="utf-8")
        hook = ("#!/usr/bin/env bash\nrm -- \"$0\"\n\"" + sys.executable.replace("\\", "/") + "\" \""
                + str(racer).replace("\\", "/") + "\"\n")
        result, report, _ = self.publish(values["check_order"].split(), artifacts, hook=hook)
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertIn("Push rejected (attempt 1)", result.stdout)
        self.assertEqual(report["publication"]["push_attempts"], 2)
        self.assertEqual(self.subject().splitlines()[0], "Results of job(s): alpha gamma")
        self.assertEqual(self.show("unrelated.txt"), "unrelated\n")
        self.assertEqual(self.show("research/beta/request.txt"), "beta raced during push\n")
        self.assertEqual(self.show("jobs/beta/output/result.txt"), "beta baseline\n")
        self.assertEqual(list(report["publication"]["refused"]), ["beta"])

    def test_unrelated_push_race_publishes_everything_on_retry(self):
        values, stations = self.plan()
        artifacts, _ = self.execute(stations, sleep="0")
        racer = self.root / "racer.py"
        racer.write_text(
            "import subprocess, pathlib\nr = pathlib.Path(" + repr(str(self.author)) + ")\n"
            "(r / 'notes.txt').write_text('a note\\n')\n"
            "for a in (['add', '-A'], ['commit', '-qm', 'note'], ['push', '-q', 'origin', 'HEAD:main']):\n"
            "    subprocess.run(['git', *a], cwd=r, check=True)\n", encoding="utf-8")
        hook = ("#!/usr/bin/env bash\nrm -- \"$0\"\n\"" + sys.executable.replace("\\", "/") + "\" \""
                + str(racer).replace("\\", "/") + "\"\n")
        result, report, _ = self.publish(values["check_order"].split(), artifacts, hook=hook)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(report["publication"]["push_attempts"], 2)
        self.assertEqual(report["publication"]["published"], ["alpha", "beta", "gamma"])
        self.assertEqual(self.show("notes.txt"), "a note\n")

    def test_concurrent_publication_of_the_same_job_refuses_the_older_one(self):
        values, stations = self.plan()
        artifacts, _ = self.execute(stations, sleep="0")
        self.sh(["git", "pull", "-q", "--rebase", "origin", "main"], self.author)
        self.put("jobs/beta/output/result.txt", "another run published first\n")
        self.commit("Results of job(s): beta")
        result, report, _ = self.publish(values["check_order"].split(), artifacts)
        self.assertEqual(result.returncode, 3)
        self.assertEqual(report["publication"]["refused"]["beta"][0]["reason"], "concurrent_output_advanced")
        self.assertEqual(self.show("jobs/beta/output/result.txt"), "another run published first\n")

    @unittest.skipUnless(BASH, "bash is required for the shell entry point")
    def test_shell_entry_point_delegates_to_the_publisher(self):
        self.assertIn("exec python .github/scripts/arsenale.py publish",
                      (SCRIPTS / "commit_results.sh").read_text())

    def test_bundle_with_paths_outside_its_jobs_is_refused(self):
        values, stations = self.plan()
        artifacts, _ = self.execute(stations, sleep="0")
        bundle = next(artifacts.glob("*station-2")) / arsenale.BUNDLE
        evil = self.root / "evil.txt"
        evil.write_text("not a job output\n")
        with tarfile.open(bundle, "a") as tar:
            tar.add(evil, arcname="jobs/alpha/output/result.txt")
        result, report, _ = self.publish(values["check_order"].split(), artifacts)
        self.assertEqual(report["bundle_problems"][0]["reason"], "invalid_bundle")
        self.assertEqual(report["not_executed"], ["beta"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.show("jobs/alpha/output/result.txt"), "alpha input v1\n")
        self.assertEqual(self.show("jobs/beta/output/result.txt"), "beta baseline\n")

    def test_station_from_another_input_commit_is_refused(self):
        values, stations = self.plan()
        artifacts, _ = self.execute(stations, sleep="0")
        receipt = next(artifacts.glob("*station-2")) / arsenale.STATION
        data = json.loads(receipt.read_text())
        data["input_commit"] = "0" * 40
        receipt.write_text(json.dumps(data))
        _, report, _ = self.publish(values["check_order"].split(), artifacts)
        self.assertIn("different input commit", report["bundle_problems"][0]["detail"])
        self.assertNotIn("beta", report["publication"]["published"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
