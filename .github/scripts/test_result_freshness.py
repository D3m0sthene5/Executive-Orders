"""Offline freshness/race fixtures; all mutations stay in temporary repositories."""
from __future__ import annotations

import importlib.util
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parent
BASH = shutil.which("bash") or str(Path(os.environ.get("ProgramFiles", "/")) / "Git/bin/bash.exe")
spec = importlib.util.spec_from_file_location("freshness", SCRIPTS / "result_freshness.py")
freshness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(freshness)
sys.path.insert(0, str(SCRIPTS))
import run_jobs


class OutputFileLimitTests(unittest.TestCase):
    def test_default_and_strict_github_ceiling(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            self.assertEqual(run_jobs.output_file_limit(folder), 95 * 1024 * 1024)
            config = folder / "MAX_OUTPUT_FILE_BYTES"
            for value in (1, 104612053, 104857599):
                config.write_text(str(value) + "\n", encoding="utf-8")
                self.assertEqual(run_jobs.output_file_limit(folder), value)
            for value in ("0", "-1", "104857600", "104857601", "1.5", "NaN", "", "+1"):
                with self.subTest(value=value):
                    config.write_text(value, encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "Invalid MAX_OUTPUT_FILE_BYTES"):
                        run_jobs.output_file_limit(folder)

    def test_retention_only_opt_in_covers_exact_pl9735_pdf(self):
        jobs = SCRIPTS.parents[1] / "jobs"
        self.assertEqual([p.parent.name for p in jobs.glob("*/MAX_OUTPUT_FILE_BYTES")], ["astra-source-retention"])
        limit = run_jobs.output_file_limit(jobs / "astra-source-retention")
        self.assertGreater(104612053, run_jobs.LIMIT)
        self.assertGreaterEqual(limit, 104612053)
        self.assertLess(limit, 100 * 1024 * 1024)


class FreshnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get("RUNNER_FIXTURE_TMP"))
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.remote = self.root / "remote.git"
        self.repo = self.root / "runner"
        self.writer = self.root / "writer"
        self.cmd("git", "init", "--bare", str(self.remote), cwd=self.root)
        self.cmd("git", "-c", "core.autocrlf=false", "clone", str(self.remote), str(self.repo), cwd=self.root)
        self.config(self.repo)
        for name in ("run_jobs.sh", "run_jobs.py", "commit_results.sh", "result_freshness.py"):
            self.put(".github/scripts/" + name, (SCRIPTS / name).read_text(encoding="utf-8"))
        self.put("jobs/_lib/cache_cap.py", "# Fixture has no download cache.\n")
        self.put(".github/workflows/run-jobs.yml", "# fixture runner\n")
        self.put("inputs/request.json", "old input\n")
        self.put("jobs/source/job.py", "import os\nfrom pathlib import Path\nPath(os.environ['OUTPUT_DIR'], 'result.txt').write_text(Path('inputs/request.json').read_text())\n")
        self.put("jobs/source/needs.txt", "inputs\n")
        self.put("jobs/source/output/result.txt", "baseline source\n")
        self.put("jobs/consumer/job.py", "import os\nfrom pathlib import Path\nPath(os.environ['OUTPUT_DIR'], 'result.txt').write_text(Path('jobs/source/output/result.txt').read_text())\n")
        self.put("jobs/consumer/after.txt", "source\n")
        self.put("jobs/consumer/output/result.txt", "baseline consumer\n")
        self.put("jobs/other/output/result.txt", "unrelated baseline\n")
        self.commit(self.repo, "baseline")
        self.cmd("git", "branch", "-M", "main")
        self.cmd("git", "push", "-u", "origin", "main")
        self.cmd("git", "-c", "core.autocrlf=false", "clone", "--branch", "main", str(self.remote), str(self.writer), cwd=self.root)
        self.config(self.writer)
        self.old_cwd = Path.cwd()
        os.chdir(self.repo)
        self.addCleanup(os.chdir, self.old_cwd)

    def config(self, repo):
        self.cmd("git", "config", "user.name", "Runner fixture", cwd=repo)
        self.cmd("git", "config", "user.email", "fixture@example.invalid", cwd=repo)
        self.cmd("git", "config", "core.autocrlf", "false", cwd=repo)

    def cmd(self, *args, cwd=None, env=None, check=True, input=None):
        result = subprocess.run(args, cwd=cwd or getattr(self, "repo", None),
                                env={**os.environ, "GIT_ALLOW_PROTOCOL": "file", **(env or {})}, input=input,
                                capture_output=True, text=True)
        if check and result.returncode:
            raise AssertionError(f"{args}: {result.returncode}\n{result.stdout}\n{result.stderr}")
        return result

    def put(self, path, data, repo=None):
        p = (repo or self.repo) / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(data, encoding="utf-8", newline="\n")
        return p

    def commit(self, repo, message):
        self.cmd("git", "add", "-A", cwd=repo)
        self.cmd("git", "commit", "-qm", message, cwd=repo)

    def advance(self, path, data):
        self.put(path, data, self.writer)
        self.commit(self.writer, "concurrent update")
        self.cmd("git", "push", "origin", "main", cwd=self.writer)
        self.cmd("git", "fetch", "origin", "main")

    def dynamic_consumer(self):
        declaration = SCRIPTS.parent.parent / "jobs/claim-kit/inputs.txt"
        self.put("jobs/consumer/inputs.txt", declaration.read_text(encoding="utf-8"))
        self.commit(self.repo, "declare the dynamic producer catalogue")
        self.cmd("git", "push", "origin", "main")
        self.cmd("git", "pull", "--ff-only", cwd=self.writer)

    def capture(self, name="source", value="generated\n"):
        destination = self.repo / "oversized" / "runner-freshness" / (name + "-inputs.json")
        freshness.capture(name, destination)
        self.put(f"jobs/{name}/output/result.txt", value)
        shutil.copyfile(destination, self.repo / "jobs" / name / "output" / freshness.MANIFEST)
        return json.loads(destination.read_text(encoding="utf-8"))

    def check(self, names=("source",)):
        report = self.repo / "oversized/runner-freshness/check.json"
        with contextlib.redirect_stdout(io.StringIO()):
            code = freshness.check("origin/main", list(names), report)
        self.retain(report)
        return code, json.loads(report.read_text(encoding="utf-8"))

    def retain(self, report):
        if destination := os.environ.get("RUNNER_FIXTURE_REPORTS"):
            path = Path(destination) / (self._testMethodName + ".json")
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(report, path)

    def shell(self, script, jobs="source", extra=None, repo=None):
        repo = repo or self.repo
        env = {**os.environ, "JOBS": jobs, "BRANCH": "main", "RUN_URL": "https://example.invalid/fixture",
               "EVENT": "workflow_dispatch", "GITHUB_STEP_SUMMARY": str(repo / "summary.md"),
               "PYTHONDONTWRITEBYTECODE": "1", **(extra or {})}
        result = self.cmd(BASH, ".github/scripts/" + script, cwd=repo, env=env, check=False)
        if (report := repo / "oversized/runner-freshness/publication-check.json").exists():
            self.retain(report)
        return result

    def test_capture_records_actual_modified_input(self):
        self.put("inputs/request.json", "uncommitted actual bytes\n")
        manifest = self.capture()
        oid = self.cmd("git", "hash-object", "inputs/request.json").stdout.strip()
        self.assertEqual(manifest["inputs"]["inputs/request.json"], "100644:" + oid)
        self.assertNotEqual(self.check()[0], 0)

    def test_capture_manifest_matches_full_tree_baseline_input_digest(self):
        manifest = self.capture()
        baseline = freshness.select(freshness.tree(manifest["base_commit"]), manifest["scope"])
        self.assertEqual(manifest["inputs"], baseline)
        self.assertEqual(manifest["inputs_sha256"], freshness.digest(baseline))

    def test_scoped_tree_matches_full_tree_for_fnmatch_cross_directory_patterns(self):
        paths = {
            "HANDOFF/notes-astra.md": "note\n",
            "HANDOFF/other.md": "other\n",
            "catalog/a/nested/item1.txt": "one\n",
            "catalog/b/item2.txt": "two\n",
            "catalog/c/nested/itemx.txt": "exclude\n",
            "rootmatch.md": "root\n",
            "other/rootmatch.md": "other root\n",
        }
        for path, data in paths.items():
            self.put(path, data)
        self.commit(self.repo, "add scoped path fixtures")
        cases = [("HANDOFF/notes-*.md", ["HANDOFF"]),
                 ("catalog/[ab]/**/item?.txt", ["catalog"]),
                 ("*.md", ["."])]
        for pattern, expected_prefixes in cases:
            with self.subTest(pattern=pattern):
                declared = {"roots": [], "patterns": [pattern], "exclude": "\0"}
                expected = freshness.select(freshness.tree("HEAD"), declared)
                self.assertEqual(freshness.literal_prefixes(declared), expected_prefixes)
                self.assertEqual(freshness.tracked_entries("HEAD", declared), expected)
                self.assertEqual(freshness.tree("HEAD", declared), expected)

    def test_scoped_working_set_preserves_added_modified_deleted_and_untracked_inputs(self):
        self.put("inputs/change.txt", "old\n")
        self.put("inputs/delete.txt", "remove\n")
        self.commit(self.repo, "add scoped working fixtures")
        self.put("inputs/change.txt", "modified\n")
        (self.repo / "inputs/delete.txt").unlink()
        self.put("inputs/new/deep/item.txt", "untracked\n")
        declared = {"roots": ["inputs"], "patterns": [], "exclude": "jobs/consumer/output"}
        result = freshness.working(declared)
        self.assertNotIn("inputs/delete.txt", result)
        self.assertIn("inputs/change.txt", result)
        self.assertIn("inputs/new/deep/item.txt", result)
        self.assertEqual(result["inputs/change.txt"].split(":", 1)[1],
                         self.cmd("git", "hash-object", "inputs/change.txt").stdout.strip())

    def test_scoped_working_set_rejects_stage_conflicts(self):
        self.put("inputs/conflict.txt", "base\n")
        self.commit(self.repo, "add conflict fixture")
        oid = self.cmd("git", "hash-object", "inputs/conflict.txt").stdout.strip()
        self.cmd("git", "update-index", "--force-remove", "inputs/conflict.txt")
        self.cmd("git", "update-index", "--index-info", input=f"100644 {oid} 1\tinputs/conflict.txt\n")
        declared = {"roots": ["inputs"], "patterns": [], "exclude": "jobs/consumer/output"}
        with self.assertRaisesRegex(ValueError, "Unmerged input: inputs/conflict.txt"):
            freshness.working(declared)

    def test_output_cap_is_per_job_keeps_boundary_and_moves_oversized_bytes(self):
        self.put("jobs/source/MAX_OUTPUT_FILE_BYTES", "16\n")
        script = ("import os\nfrom pathlib import Path\n"
                  "out=Path(os.environ['OUTPUT_DIR'])\n"
                  "(out/'boundary.bin').write_bytes(b'A'*16)\n"
                  "(out/'oversized.bin').write_bytes(b'B'*17)\n")
        self.put("jobs/source/job.py", script)
        self.put("jobs/other/job.py", script)
        result = self.shell("run_jobs.sh", "source other")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        output = self.repo / "jobs/source/output"
        self.assertEqual((output / "boundary.bin").read_bytes(), b'A' * 16)
        self.assertFalse((output / "oversized.bin").exists())
        self.assertEqual((self.repo / "oversized/source/oversized.bin").read_bytes(), b'B' * 17)
        status = json.loads((output / "STATUS.json").read_text())
        self.assertEqual(status["max_output_file_bytes"], 16)
        self.assertEqual(status["oversized_files_moved_to_run_download"], ["oversized.bin"])
        other = self.repo / "jobs/other/output"
        self.assertEqual((other / "oversized.bin").read_bytes(), b'B' * 17)
        self.assertEqual(json.loads((other / "STATUS.json").read_text())["max_output_file_bytes"], run_jobs.LIMIT)
        manifest = json.loads((output / freshness.MANIFEST).read_text())
        self.assertIn("jobs/source/MAX_OUTPUT_FILE_BYTES", manifest["inputs"])

    def test_unsafe_output_cap_fails_before_generation_and_preserves_previous_output(self):
        self.put("jobs/source/MAX_OUTPUT_FILE_BYTES", "104857600\n")
        result = self.shell("run_jobs.sh", "source consumer")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Invalid MAX_OUTPUT_FILE_BYTES", result.stdout)
        self.assertEqual((self.repo / "jobs/source/output/result.txt").read_text(), "baseline source\n")
        records = json.loads((self.repo / "oversized/runner-freshness/ATTEMPTS.json").read_text())
        self.assertEqual([r["publish_output"] for r in records], [False, False])
        self.assertTrue((self.repo / records[0]["attempt_path"] / "STATUS.json").exists())

    def test_failed_generation_preserves_output_blocks_consumers_and_publishes_independent_job(self):
        self.put("jobs/source/job.py", "import os\nfrom pathlib import Path\nPath(os.environ['OUTPUT_DIR'], 'result.txt').write_text('incomplete replacement')\nraise SystemExit(7)\n")
        self.put("jobs/other/job.py", "import os\nfrom pathlib import Path\nPath(os.environ['OUTPUT_DIR'], 'result.txt').write_text('independent success\\n')\n")
        self.commit(self.repo, "exercise failure retention")
        self.cmd("git", "push", "origin", "main")
        result = self.shell("run_jobs.sh", "source consumer other")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.repo / "jobs/source/output/result.txt").read_text(), "baseline source\n")
        self.assertEqual((self.repo / "jobs/consumer/output/result.txt").read_text(), "baseline consumer\n")
        records = json.loads((self.repo / "oversized/runner-freshness/ATTEMPTS.json").read_text())
        self.assertEqual([r["publish_output"] for r in records], [False, False, True])
        failed = self.repo / records[0]["attempt_path"]
        blocked = self.repo / records[1]["attempt_path"]
        self.assertEqual((failed / "result.txt").read_text(), "incomplete replacement")
        self.assertEqual(json.loads((blocked / "STATUS.json").read_text())["blocked_by"], ["source"])
        published = self.shell("commit_results.sh", "source consumer other")
        self.assertEqual(published.returncode, 0, published.stdout + published.stderr)
        self.assertEqual(self.cmd("git", "show", "origin/main:jobs/source/output/result.txt").stdout, "baseline source\n")
        self.assertEqual(self.cmd("git", "show", "origin/main:jobs/other/output/result.txt").stdout, "independent success\n")
        self.assertEqual(self.cmd("git", "show", "origin/main:" + records[0]["attempt_path"] + "/result.txt").stdout, "incomplete replacement")

    def test_all_failed_attempts_publish_receipts_without_promoting_output(self):
        self.put("jobs/source/job.py", "raise SystemExit(9)\n")
        self.commit(self.repo, "exercise failed-only publication")
        self.cmd("git", "push", "origin", "main")
        self.assertNotEqual(self.shell("run_jobs.sh").returncode, 0)
        published = self.shell("commit_results.sh")
        self.assertEqual(published.returncode, 0, published.stdout + published.stderr)
        self.assertEqual(self.cmd("git", "show", "origin/main:jobs/source/output/result.txt").stdout, "baseline source\n")

    def test_setup_failure_preserves_output_and_next_run_can_recover(self):
        self.put("jobs/source/inputs.txt", "../outside/**\n")
        failed = self.shell("run_jobs.sh", "source consumer")
        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual((self.repo / "jobs/source/output/result.txt").read_text(), "baseline source\n")
        self.put("jobs/source/inputs.txt", "inputs/**\n")
        recovered = self.shell("run_jobs.sh", "source consumer")
        self.assertEqual(recovered.returncode, 0, recovered.stdout + recovered.stderr)
        self.assertEqual((self.repo / "jobs/consumer/output/result.txt").read_text(), "old input\n")

    def test_changed_declared_input_rejects_old_runner_before_push(self):
        self.capture()
        self.advance("inputs/request.json", "newer request\n")
        before = self.cmd("git", "rev-parse", "origin/main").stdout
        result = self.shell("commit_results.sh")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("inputs/request.json", (self.repo / "summary.md").read_text())
        self.assertEqual(before, self.cmd("git", "rev-parse", "origin/main").stdout)
        self.assertTrue((self.repo / "oversized/runner-freshness/source-inputs.json").exists())

    def test_old_finisher_cannot_replace_output_from_newer_input(self):
        old = self.shell("run_jobs.sh")
        self.assertEqual(old.returncode, 0, old.stdout + old.stderr)
        self.advance("inputs/request.json", "newer input output must survive\n")
        for script in ("run_jobs.sh", "commit_results.sh"):
            newer = self.shell(script, repo=self.writer)
            self.assertEqual(newer.returncode, 0, newer.stdout + newer.stderr)
        older = self.shell("commit_results.sh")
        self.assertNotEqual(older.returncode, 0)
        self.assertIn("inputs_changed", older.stdout)
        self.assertEqual(self.cmd("git", "show", "origin/main:jobs/source/output/result.txt").stdout,
                         "newer input output must survive\n")

    def test_changed_job_and_shared_code_rejected(self):
        for path in ("jobs/source/job.py", "jobs/_lib/cache_cap.py", ".github/workflows/run-jobs.yml"):
            with self.subTest(path=path):
                self.capture()
                self.advance(path, "# updated code\n")
                code, report = self.check()
                self.assertEqual(code, 3)
                self.assertTrue(any(p["reason"] == "inputs_changed" for p in report["problems"]))

    def test_new_file_in_declared_missing_directory_rejected(self):
        self.put("jobs/source/needs.txt", "inputs\nnot-yet-present\n")
        self.commit(self.repo, "declare missing directory")
        self.cmd("git", "push", "origin", "main")
        self.cmd("git", "pull", "--ff-only", cwd=self.writer)
        self.capture()
        self.advance("not-yet-present/evidence.txt", "new evidence\n")
        self.assertEqual(self.check()[0], 3)

    def test_trigger_glob_is_versioned(self):
        self.put("jobs/source/triggers.txt", "inputs/*.json\n")
        self.put("jobs/source/needs.txt", "# triggers are declared reads too\n")
        self.commit(self.repo, "use trigger declaration")
        self.cmd("git", "push", "origin", "main")
        self.cmd("git", "pull", "--ff-only", cwd=self.writer)
        self.capture()
        self.advance("inputs/request.json", "new trigger bytes\n")
        self.assertEqual(self.check()[0], 3)

    def test_unrelated_commit_and_output_reconcile_without_overwrite(self):
        self.capture()
        self.advance("jobs/other/output/result.txt", "new unrelated result\n")
        self.assertEqual(self.check()[0], 0)
        result = self.shell("commit_results.sh")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.cmd("git", "show", "origin/main:jobs/other/output/result.txt").stdout, "new unrelated result\n")
        self.assertEqual(self.cmd("git", "show", "origin/main:jobs/source/output/result.txt").stdout, "generated\n")

    def test_concurrent_output_advance_cannot_be_hidden_by_chain_overlay(self):
        self.capture("source", "older acquisition\n")
        self.capture("consumer", "older acquisition\n")
        self.advance("jobs/source/output/result.txt", "newer acquisition\n")
        code, report = self.check(("source", "consumer"))
        self.assertEqual(code, 3)
        self.assertTrue(any(p["reason"] == "concurrent_output_advanced" for p in report["problems"]))

    def test_nonselected_predecessor_advance_rejected(self):
        self.capture("consumer")
        self.advance("jobs/source/output/result.txt", "new upstream evidence\n")
        self.assertEqual(self.check(("consumer",))[0], 3)

    def test_dynamic_new_source_job_data_rejects_stale_consumer(self):
        self.dynamic_consumer()
        self.capture("consumer")
        self.advance("jobs/new-producer/data/nested/SOURCES.jsonl", "newly discovered source\n")
        code, report = self.check(("consumer",))
        self.assertEqual(code, 3)
        self.assertTrue(any(item.get("path") == "jobs/new-producer/data/nested/SOURCES.jsonl"
                            for problem in report["problems"] for item in problem.get("changed_paths", [])))

    def test_dynamic_changed_nonpredecessor_data_rejects_stale_consumer(self):
        self.put("jobs/other/data/held.txt", "old held evidence\n")
        self.dynamic_consumer()
        self.capture("consumer")
        self.advance("jobs/other/data/held.txt", "changed held evidence\n")
        self.assertEqual(self.check(("consumer",))[0], 3)

    def test_dynamic_changed_nonpredecessor_output_rejects_stale_consumer(self):
        self.dynamic_consumer()
        self.capture("consumer")
        self.advance("jobs/other/output/result.txt", "new dynamic output evidence\n")
        self.assertEqual(self.check(("consumer",))[0], 3)

    def test_dynamic_new_nonpredecessor_output_rejects_stale_consumer(self):
        self.dynamic_consumer()
        self.capture("consumer")
        self.advance("jobs/brand-new/output/FRAGMENTS.jsonl", "new producer fragment\n")
        self.assertEqual(self.check(("consumer",))[0], 3)

    def test_dynamic_declaration_allows_same_invocation_chain(self):
        self.dynamic_consumer()
        run = self.shell("run_jobs.sh", "source consumer")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(self.check(("source", "consumer"))[0], 0)
        published = self.shell("commit_results.sh", "source consumer")
        self.assertEqual(published.returncode, 0, published.stdout + published.stderr)

    def later_dynamic_producer(self):
        self.put("jobs/example-hello/job.py", "import os\nfrom pathlib import Path\nPath(os.environ['OUTPUT_DIR'], 'result.txt').write_text('new later output\\n')\n")
        self.put("jobs/example-hello/output/result.txt", "captured earlier baseline\n")
        self.dynamic_consumer()
        run = self.shell("run_jobs.sh", "consumer example-hello")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_dynamic_later_producer_preserves_consumers_actual_base_snapshot(self):
        self.later_dynamic_producer()
        code, report = self.check(("consumer", "example-hello"))
        self.assertEqual(code, 0)
        self.assertEqual(report["input_generations"]["consumer"]["example-hello"], "captured_base")
        published = self.shell("commit_results.sh", "consumer example-hello")
        self.assertEqual(published.returncode, 0, published.stdout + published.stderr)

    def test_dynamic_later_base_snapshot_does_not_hide_concurrent_output_advance(self):
        self.later_dynamic_producer()
        self.advance("jobs/example-hello/output/result.txt", "newer concurrent evidence\n")
        code, report = self.check(("consumer", "example-hello"))
        self.assertEqual(code, 3)
        self.assertTrue(any(p["reason"] == "concurrent_output_advanced" for p in report["problems"]))

    def test_dynamic_later_base_snapshot_does_not_hide_new_external_source(self):
        self.later_dynamic_producer()
        self.advance("jobs/new-external/data/SOURCES.jsonl", "new source after capture\n")
        code, report = self.check(("consumer", "example-hello"))
        self.assertEqual(code, 3)
        self.assertTrue(any(item["path"] == "jobs/new-external/data/SOURCES.jsonl"
                            for problem in report["problems"] for item in problem.get("changed_paths", [])))

    def test_prepare_materializes_only_matching_sparse_declarations(self):
        self.put("hidden/needed/held.txt", "read this declared evidence\n")
        self.put("hidden/unrelated/private.txt", "do not materialize\n")
        self.put("jobs/consumer/inputs.txt", "hidden/needed/**\n")
        self.commit(self.repo, "declare one sparse input tree")
        self.cmd("git", "sparse-checkout", "set", ".github", "jobs")
        self.assertFalse((self.repo / "hidden/needed/held.txt").exists())
        prepared = self.cmd(sys.executable, ".github/scripts/result_freshness.py", "prepare", "consumer")
        self.assertIn("Materialized", prepared.stdout)
        self.assertTrue((self.repo / "hidden/needed/held.txt").exists())
        self.assertFalse((self.repo / "hidden/unrelated/private.txt").exists())
        self.assertFalse((self.repo / "inputs/request.json").exists())
        manifest = self.capture("consumer")
        self.assertIn("hidden/needed/held.txt", manifest["inputs"])

    def test_dynamic_catalogue_is_acquired_by_runner_in_sparse_checkout(self):
        self.put("jobs/other/data/deep/held.txt", "dynamic source\n")
        self.dynamic_consumer()
        self.cmd("git", "sparse-checkout", "set", ".github", "jobs/consumer", "jobs/source", "jobs/_lib")
        self.assertFalse((self.repo / "jobs/other/data/deep/held.txt").exists())
        run = self.shell("run_jobs.sh", "consumer")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue((self.repo / "jobs/other/data/deep/held.txt").exists())
        manifest = json.loads((self.repo / "jobs/consumer/output/RUNNER_INPUTS.json").read_bytes())
        self.assertIn("jobs/other/data/deep/held.txt", manifest["inputs"])

    def test_chain_accepts_exact_same_invocation_predecessor_bytes(self):
        run = self.shell("run_jobs.sh", "source consumer")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        source = json.loads((self.repo / "jobs/source/output/RUNNER_INPUTS.json").read_text())
        consumer = json.loads((self.repo / "jobs/consumer/output/RUNNER_INPUTS.json").read_text())
        self.assertIn("jobs/source/output/RUNNER_INPUTS.json", consumer["inputs"])
        self.assertEqual(source["inputs"]["inputs/request.json"], "100644:" + self.cmd("git", "hash-object", "inputs/request.json").stdout.strip())
        self.assertEqual(self.check(("source", "consumer"))[0], 0)
        published = self.shell("commit_results.sh", "source consumer")
        self.assertEqual(published.returncode, 0, published.stdout + published.stderr)

    def test_consumer_does_not_accept_predecessor_changed_after_its_capture(self):
        self.capture("source")
        self.capture("consumer")
        self.put("jobs/source/output/result.txt", "changed after consumer\n")
        self.assertEqual(self.check(("source", "consumer"))[0], 3)

    def test_missing_provenance_fails_closed(self):
        code, report = self.check()
        self.assertEqual(code, 3)
        self.assertEqual(report["problems"][0]["reason"], "missing_or_invalid_manifest")

    def test_incomplete_provenance_retains_actionable_rejection(self):
        self.put("jobs/source/output/RUNNER_INPUTS.json", json.dumps(
            {"schema": 1, "job": "source", "inputs": {}, "inputs_sha256": freshness.digest({})}))
        code, report = self.check()
        self.assertEqual(code, 3)
        self.assertEqual(report["problems"][0]["reason"], "missing_or_invalid_manifest")

    def test_absent_sparse_input_is_not_falsely_recorded_as_consumed(self):
        self.cmd("git", "sparse-checkout", "set", ".github", "jobs")
        self.assertFalse((self.repo / "inputs/request.json").exists())
        with self.assertRaisesRegex(ValueError, "absent from sparse checkout"):
            self.capture()

    def test_daily_digest_versions_its_dynamic_corpus_reads(self):
        declared = freshness.scope("daily-digest")
        entries = {"jobs/other/output/SUMMARY.json": "a", "jobs/other/output/STATUS.json": "b",
                   "jobs/other/output/unrelated.txt": "c", "HANDOFF/notes-astra.md": "d"}
        self.assertEqual(set(freshness.select(entries, declared)),
                         {"jobs/other/output/SUMMARY.json", "jobs/other/output/STATUS.json", "HANDOFF/notes-astra.md"})

    def test_input_race_after_first_check_rechecked_on_push_rejection(self):
        self.capture()
        race = self.root / "race.py"
        race.write_text("from pathlib import Path\nimport subprocess\nr=Path(" + repr(str(self.writer)) + ")\n"
                        "p=r/'inputs/request.json'\np.write_text('new input during push\\n')\n"
                        "for args in [('add','-A'),('commit','-qm','racing input'),('push','origin','main')]:\n"
                        " subprocess.run(['git',*args],cwd=r,check=True)\n", encoding="utf-8")
        hook = self.repo / ".git/hooks/pre-push"
        # The competing writer clone has no hook; this fires once in the runner.
        hook.write_text("#!/usr/bin/env bash\nrm -- \"$0\"\n\"" + sys.executable.replace("\\", "/") + "\" \"" + str(race).replace("\\", "/") + "\"\n", encoding="utf-8", newline="\n")
        hook.chmod(0o755)
        result = self.shell("commit_results.sh")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Push rejected", result.stdout)
        self.assertIn("inputs_changed", result.stdout)
        self.assertEqual(self.cmd("git", "show", "origin/main:jobs/source/output/result.txt").stdout, "baseline source\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
