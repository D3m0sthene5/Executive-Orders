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


class RequeueTests(unittest.TestCase):
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
        self.sh(["git", "clone", str(self.origin), str(self.author)], self.root)
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

    def clone(self, name, commit):
        path = self.root / name
        self.sh(["git", "clone", "-q", str(self.origin), str(path)], self.root)
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

    def publish(self, order, artifacts, hook=None, event="workflow_dispatch"):
        publisher = self.root / "publisher"
        self.sh(["git", "clone", "-q", str(self.origin), str(publisher)], self.root)
        self.configure(publisher)
        if hook:
            target = publisher / ".git/hooks/pre-push"
            target.write_text(hook, encoding="utf-8", newline="\n")
            target.chmod(0o755)
        env = self.env(order, BRANCH="main", EVENT=event, RUN_URL="https://example.invalid/runs/4242",
                       ARSENALE_RETRY_SECONDS="0", GITHUB_STEP_SUMMARY=str(self.root / "summary.md"),
                       GITHUB_OUTPUT=str(self.root / "publish.outputs"))
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
