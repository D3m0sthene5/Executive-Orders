"""Writer queue contracts and native original-selection/latest-checkout receipts.

These tests do not emulate GitHub's lock service. Hosted workflow validation and
actual serialized publication remain required acceptance evidence.
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


class QueueContract(unittest.TestCase):
    def test_shared_mutating_queue_and_diagnostic_isolation(self):
        run, refresh = RUN.read_text(), REFRESH.read_text()
        for source in (run, refresh):
            self.assertRegex(source, r"(?m)^      queue: max$")
            self.assertRegex(source, r"(?m)^      cancel-in-progress: false$")
        self.assertIn("format('repository-output-writer-{0}', github.ref)", run)
        self.assertIn("group: repository-output-writer-refs/heads/main", refresh)
        self.assertIn("github.event_name == 'workflow_dispatch' && inputs.diagnostic", run)
        self.assertIn("format('read-only-job-diagnostic-{0}-{1}', github.run_id, github.run_attempt)", run)
        self.assertIn("ref: ${{ github.event_name == 'workflow_dispatch' && inputs.diagnostic && github.sha || github.ref }}", run)
        self.assertIn("persist-credentials: ${{ !inputs.diagnostic }}", run)
        self.assertIn("BEFORE: ${{ github.event.before }}", run)
        self.assertIn("AFTER: ${{ github.sha }}", run)
        self.assertIn("env GITHUB_SHA=\"$execution_input_commit\" bash .github/scripts/run_jobs.sh", run)
        self.assertIn("github.event.workflow_run.head_repository.full_name == github.repository", refresh)
        self.assertLess(refresh.index("github.ref == 'refs/heads/main'"), refresh.index("    concurrency:"))


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
                r"(?m)^          execution_input_commit=.*\n          env GITHUB_SHA=.*\n",
                RUN.read_text())
            self.assertIsNotNone(match, "native receipt staging block disappeared")
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
