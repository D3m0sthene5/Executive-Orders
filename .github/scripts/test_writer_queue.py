"""Writer queue contracts and native original-selection/latest-checkout receipts.

Arsenale holds the writer queue only in the publish job; plan and execute run
without it. These tests do not emulate GitHub's lock service. Hosted workflow
validation and actual serialized publication remain required acceptance evidence.
"""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / ".github/workflows/run-jobs.yml"
REFRESH = ROOT / ".github/workflows/refresh-readiness.yml"


def job_sections(source):
    """Split a workflow's jobs: block into {job id: text} without a YAML dependency."""
    body = source.split("\njobs:\n", 1)[1]
    parts = re.split(r"(?m)^  ([A-Za-z0-9_-]+):\n", body)
    return dict(zip(parts[1::2], parts[2::2]))


class QueueContract(unittest.TestCase):
    def test_lock_is_held_only_by_publish(self):
        run, refresh = RUN.read_text(), REFRESH.read_text()
        jobs = job_sections(run)
        self.assertEqual(list(jobs), ["plan", "execute", "publish"])
        self.assertNotIn("concurrency:", run.split("\njobs:\n", 1)[0])
        for name in ("plan", "execute"):
            self.assertNotIn("concurrency:", jobs[name], name)
            self.assertNotIn("repository-output-writer", jobs[name], name)
        publish = jobs["publish"]
        self.assertRegex(publish, r"(?m)^    needs: \[plan, execute\]$")
        self.assertRegex(publish, r"(?m)^      queue: max$")
        self.assertRegex(publish, r"(?m)^      cancel-in-progress: false$")
        self.assertIn("format('repository-output-writer-{0}', github.ref)", publish)
        # Only publish may write; stations run job code with a read-only token.
        self.assertRegex(run, r"(?m)^permissions:\n  contents: read$")
        self.assertIn("    permissions:\n      contents: read\n", jobs["execute"])
        self.assertIn("    permissions:\n      contents: write\n      actions: write\n", publish)
        self.assertNotIn("contents: write", jobs["plan"] + jobs["execute"])
        # The lock is acquired before the latest-tip checkout and kept through the push.
        self.assertLess(publish.index("    concurrency:"), publish.index("- uses: actions/checkout@v4"))
        self.assertLess(publish.index("- uses: actions/checkout@v4"), publish.index("bash .github/scripts/commit_results.sh"))
        refresh_jobs = job_sections(refresh)
        self.assertEqual(list(refresh_jobs), ["execute", "publish"])
        # Hansard: refreshes run one at a time with one waiting (latest wins), on
        # their own group so the writer lock is still held only by publish.
        refresh_head = refresh.split("\njobs:\n", 1)[0]
        self.assertIn("concurrency:\n  group: refresh-readiness-${{ github.ref }}\n  cancel-in-progress: false\n",
                      refresh_head)
        self.assertNotIn("queue:", refresh_head)
        self.assertNotIn("repository-output-writer", refresh_head)
        # Hansard: only the reporting refresh publishes data-drifted readouts as of
        # their input commit; production publication never does.
        self.assertIn("ARSENALE_AS_OF_READOUT: '1'", refresh_jobs["publish"])
        self.assertNotIn("ARSENALE_AS_OF_READOUT", run)
        self.assertNotIn("concurrency:", refresh_jobs["execute"])
        self.assertIn("group: repository-output-writer-refs/heads/main", refresh_jobs["publish"])
        self.assertRegex(refresh_jobs["publish"], r"(?m)^      queue: max$")
        self.assertRegex(refresh_jobs["publish"], r"(?m)^      cancel-in-progress: false$")
        self.assertIn("bash .github/scripts/commit_results.sh", refresh_jobs["publish"])
        self.assertNotIn("commit_results.sh", refresh_jobs["execute"])

    def test_shared_mutating_queue_and_diagnostic_isolation(self):
        run, refresh = RUN.read_text(), REFRESH.read_text()
        jobs = job_sections(run)
        self.assertIn("github.event_name == 'workflow_dispatch' && inputs.diagnostic", jobs["publish"])
        self.assertIn("format('read-only-job-diagnostic-{0}-{1}', github.run_id, github.run_attempt)", jobs["publish"])
        latest = "ref: ${{ github.event_name == 'workflow_dispatch' && inputs.diagnostic && github.sha || github.ref }}"
        self.assertIn(latest, jobs["plan"])
        self.assertIn(latest, jobs["publish"])
        # Every station executes the one commit the plan pinned (the tip at plan time).
        self.assertIn("ref: ${{ needs.plan.outputs.input_commit }}", jobs["execute"])
        self.assertIn('test "$execution_input_commit" = "$ARSENALE_INPUT_COMMIT"', jobs["execute"])
        self.assertIn("persist-credentials: ${{ !inputs.diagnostic }}", jobs["execute"])
        self.assertIn("persist-credentials: ${{ !inputs.diagnostic }}", jobs["publish"])
        self.assertIn("if: ${{ !inputs.diagnostic }}", jobs["publish"].split("- name: Commit results to the branch", 1)[1].split("\n      - ", 1)[0])
        self.assertIn("BEFORE: ${{ github.event.before }}", jobs["plan"])
        self.assertIn("AFTER: ${{ github.sha }}", jobs["plan"])
        self.assertIn("env GITHUB_SHA=\"$execution_input_commit\" bash .github/scripts/run_jobs.sh", jobs["execute"])
        self.assertIn("github.event.workflow_run.head_repository.full_name == github.repository", refresh)
        publish = job_sections(refresh)["publish"]
        self.assertLess(publish.index("github.ref == 'refs/heads/main'"), publish.index("    concurrency:"))

    def test_parallel_stations_and_bounded_requeue_are_wired(self):
        run = RUN.read_text()
        jobs = job_sections(run)
        execute = jobs["execute"]
        self.assertIn("matrix: ${{ fromJSON(needs.plan.outputs.matrix) }}", execute)
        self.assertIn("fail-fast: false", execute)
        self.assertIn("JOBS: ${{ matrix.jobs }}", execute)
        self.assertIn("python .github/scripts/arsenale.py plan", jobs["plan"])
        self.assertIn("python .github/scripts/arsenale.py bundle --station ${{ matrix.station }}", execute)
        self.assertIn("arsenale-${{ github.run_id }}-${{ github.run_attempt }}-station-${{ matrix.station }}", execute)
        self.assertIn("pattern: arsenale-${{ github.run_id }}-${{ github.run_attempt }}-station-*", jobs["publish"])
        self.assertIn("python .github/scripts/arsenale.py collect", jobs["publish"])
        self.assertIn("python .github/scripts/arsenale.py requeue --workflow run-jobs.yml", jobs["publish"])
        self.assertIn("REQUEUE_DEPTH: ${{ github.event.inputs.requeue_depth }}", jobs["plan"])
        self.assertIn("REQUEUE_DEPTH: ${{ github.event.inputs.requeue_depth }}", jobs["publish"])
        self.assertIn("requeue_depth:", run.split("\njobs:\n", 1)[0])
        # Station outputs, oversized files and receipts survive a failed job.
        for step in ("- name: Bundle this station's results", "- name: Hand the station's results to publish"):
            self.assertIn("if: always()", execute.split(step, 1)[1].split("\n      - ", 1)[0])
        self.assertIn("name: oversized-outputs-${{ github.run_id }}", jobs["publish"])
        self.assertIn("name: diagnostic-receipts-${{ github.run_id }}-${{ github.run_attempt }}", jobs["publish"])
        refresh = job_sections(REFRESH.read_text())
        self.assertIn("python .github/scripts/arsenale.py requeue --workflow refresh-readiness.yml", refresh["publish"])


class QueuedCheckout(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="eo queued writer ")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Queue fixture")
        self.git("config", "user.email", "queue-fixture@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.autocrlf", "false")
        shutil.copytree(ROOT / ".github/scripts", self.repo / ".github/scripts",
                        ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT / "jobs/_lib", self.repo / "jobs/_lib",
                        ignore=shutil.ignore_patterns("__pycache__"))
        (self.repo / ".github/workflows").mkdir()
        shutil.copyfile(RUN, self.repo / ".github/workflows/run-jobs.yml")
        self.job("alpha", "baseline")
        self.job("beta", "baseline")
        self.base = self.commit("baseline")
        self.job("alpha", "event")
        self.event = self.commit("original alpha push")
        self.job("alpha", "latest")
        self.job("beta", "later unrelated selection")
        self.latest = self.commit("later branch state while writer was queued")

    def git(self, *args):
        result = subprocess.run(["git", *args], cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout.strip()

    def commit(self, label):
        self.git("add", ".")
        self.git("commit", "-m", label)
        return self.git("rev-parse", "HEAD")

    def job(self, name, marker):
        folder = self.repo / "jobs" / name
        folder.mkdir(parents=True, exist_ok=True)
        source = (
            "import json,os\nfrom pathlib import Path\n"
            "p=Path(os.environ['OUTPUT_DIR']);p.mkdir(parents=True,exist_ok=True)\n"
            "p.joinpath('PROBE.json').write_text(json.dumps({"
            "'marker':" + repr(marker) + ","
            "'native_sha':os.environ.get('GITHUB_SHA')}))\n"
        )
        (folder / "job.py").write_text(source, encoding="utf-8", newline="\n")

    def pick(self, diagnostic=False):
        output = Path(self.temp.name) / ("diagnostic.outputs" if diagnostic else "push.outputs")
        env = dict(os.environ, EVENT="workflow_dispatch" if diagnostic else "push",
                   INPUT_JOB="alpha", DIAGNOSTIC="true" if diagnostic else "false",
                   BEFORE=self.base, AFTER=self.event, GITHUB_SHA=self.event,
                   DEFAULT_BRANCH="main", GITHUB_OUTPUT=str(output))
        result = subprocess.run([sys.executable, str(self.repo / ".github/scripts/pick_jobs.py")],
                                cwd=self.repo, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return dict(line.split("=", 1) for line in output.read_text().splitlines())

    def native(self, label, expected):
        env = dict(os.environ, JOBS="alpha", GITHUB_SHA=self.event,
                   GITHUB_REF_NAME="main", GITHUB_RUN_ID="queue-fixture-" + label,
                   GITHUB_RUN_ATTEMPT="1", PYTHONDONTWRITEBYTECODE="1")
        if os.name == "nt":
            # The native Python entrypoint is identical; GitHub's Linux shell
            # staging is exercised directly on the Ubuntu arm.
            env["GITHUB_SHA"] = self.git("rev-parse", "HEAD")
            command = [sys.executable, ".github/scripts/run_jobs.py"]
        else:
            match = re.search(
                r"(?m)^          execution_input_commit=.*\n          test .*\n          env GITHUB_SHA=.*\n",
                RUN.read_text())
            self.assertIsNotNone(match, "native receipt staging block disappeared")
            env["ARSENALE_INPUT_COMMIT"] = self.git("rev-parse", "HEAD")
            command = ["bash", "-e", "-o", "pipefail", "-c", textwrap.dedent(match.group())]
        result = subprocess.run(command, cwd=self.repo, env=env,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        output = self.repo / "jobs/alpha/output"
        probe = json.loads((output / "PROBE.json").read_text())
        status = json.loads((output / "STATUS.json").read_text())
        manifest = json.loads((output / "RUNNER_INPUTS.json").read_text())
        self.assertEqual(probe["native_sha"], expected)
        self.assertEqual(status["commit_run"], expected)
        self.assertEqual(manifest["base_commit"], expected)
        self.assertEqual(status["result"], "succeeded")
        self.assertFalse((self.repo / "jobs/beta/output").exists())
        return probe

    def test_queued_production_keeps_original_selection_but_executes_current_inputs(self):
        self.assertEqual(self.git("rev-parse", "HEAD"), self.latest)
        selection = self.pick()
        self.assertEqual(selection["jobs"], "alpha")
        self.assertEqual(selection["direct"], "alpha")
        self.assertEqual(self.native("production", self.latest)["marker"], "latest")

    def test_diagnostic_checkout_and_receipts_remain_pinned(self):
        self.git("checkout", "--detach", self.event)
        selection = self.pick(diagnostic=True)
        self.assertEqual(selection["jobs"], "alpha")
        self.assertEqual(self.native("diagnostic", self.event)["marker"], "event")


if __name__ == "__main__":
    unittest.main()
