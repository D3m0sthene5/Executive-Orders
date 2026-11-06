"""Bounded regressions for sparse runner input closure construction."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

spec = importlib.util.spec_from_file_location("materialize_job_inputs", HERE / "materialize_job_inputs.py")
materializer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(materializer)


class CompactPatternTests(unittest.TestCase):
    def test_git_worktree_matches_before_and_after_compaction(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            def git(*args, data=None):
                return subprocess.run(["git", *args], cwd=root, input=data,
                                      capture_output=True, check=True).stdout
            git("init", "-q")
            names = ("jobs/a/file", "jobs/a/sub/file", "jobs/abc/file", "jobs/b/file",
                     "jobs/b/file[1]", "jobs/x", "extra/file", "extra/skip", "other/file")
            for name in names:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(name.encode())
            git("add", ".")
            git("-c", "user.email=test@example.com", "-c", "user.name=test", "commit", "-qm", "fixture")
            rules = {"/jobs/a/**", "/jobs/a/sub/**", "/jobs/a/file", "/jobs/a/sub/file",
                     "/jobs/abc/file", materializer.literal_pattern("jobs/b/file[1]"), "/extra/file"}
            bootstrap = b"/*\n!/*/\n/jobs/**\n!/jobs/*/**\n"

            def snapshot(rules):
                git("sparse-checkout", "set", "--no-cone", "--stdin", data=bootstrap)
                git("sparse-checkout", "add", "--stdin", data=("\n".join(rules) + "\n").encode())
                return ({name: (root / name).read_bytes() for name in names if (root / name).is_file()},
                        git("ls-files", "-t", "-z"))

            for extra in (set(), {"/jobs/**"}, {"/**"}):
                with self.subTest(extra=extra):
                    original = rules | extra
                    compact = materializer.compact_patterns(original)
                    self.assertLess(len(compact), len(original))
                    self.assertEqual(snapshot(sorted(original)), snapshot(compact))


class MaterializeInputsTests(unittest.TestCase):
    def setUp(self):
        # Exercise narrow mechanics against exact metadata in this checkout;
        # production uses the separately reviewed, frozen signatures.
        audited = {n: materializer.narrow_signature(n) for n in
                   ("example-hello", "early-ranger-transcriptions")}
        patch = mock.patch.object(materializer, "NARROW_SIGNATURES", audited)
        patch.start()
        self.addCleanup(patch.stop)

    def test_unaudited_mixed_selection_preserves_dynamic_outputs(self):
        entries, _, patterns = materializer.input_closure(["example-hello", "claim-checker"])
        self.assertIn("jobs/fr-pages/output/SOURCES.jsonl", entries)
        self.assertIn("jobs/app-executive-orders/output/MIRROR_DOCUMENTS.jsonl", entries)
        self.assertIn("/jobs/**", patterns["claim-checker"])
        self.assertEqual(materializer.fallback_jobs(["example-hello", "claim-checker"]),
                         {"claim-checker": "unaudited_job"})

    def test_changed_audited_code_uses_compatibility_fallback(self):
        with mock.patch.dict(materializer.NARROW_SIGNATURES, {"example-hello": "changed"}):
            self.assertEqual(materializer.fallback_jobs(["example-hello"]),
                             {"example-hello": "audited_version_changed"})
            entries, _, patterns = materializer.input_closure(["example-hello"])
            self.assertIn("jobs/claim-kit/output/INDEX.json", entries)
            self.assertIn("/jobs/**", patterns["example-hello"])

    def test_workflow_picks_before_cache_and_uses_narrow_bootstrap(self):
        workflow = (ROOT / ".github/workflows/run-jobs.yml").read_text(encoding="utf-8")
        self.assertIn("sparse-checkout-cone-mode: false", workflow)
        self.assertIn("            /*\n            !/*/\n", workflow)
        self.assertIn("            /jobs/**\n", workflow)
        self.assertIn("            !/jobs/*/output/**\n", workflow)
        self.assertNotIn("/jobs/*/job.py", workflow)
        choose = workflow.index("- name: Choose which jobs to run")
        execute = workflow.index("\n  execute:\n")
        cache = workflow.index("- name: Restore each job's bounded download cache")
        materialize = workflow.index("- name: Materialize selected job inputs and prior outputs")
        self.assertLess(choose, execute)
        self.assertLess(execute, cache)
        self.assertLess(cache, materialize)
        # Stations (and so their cache restores) exist only when the plan picked jobs.
        self.assertIn("    if: needs.plan.outputs.jobs != ''\n", workflow[execute:cache])
        self.assertIn("JOBS: ${{ matrix.jobs }}", workflow[materialize:])

    def test_literal_sparse_patterns_escape_path_metacharacters(self):
        self.assertEqual(materializer.literal_pattern("jobs/sample/a*b?.[x].txt"),
                         r"/jobs/sample/a\*b\?\.\[x].txt".replace(r"\.", "."))
        self.assertEqual(materializer.literal_pattern("jobs/sample/space name.txt"),
                         "/jobs/sample/space name.txt")
        self.assertEqual(materializer.literal_pattern("jobs/sample/trailing "),
                         r"/jobs/sample/trailing\ ")
        with self.assertRaises(ValueError):
            materializer.literal_pattern("jobs/sample/bad\nname")

    def test_selected_dependency_closure_is_exact_and_keeps_prior_output(self):
        names = ["example-hello", "early-ranger-transcriptions"]
        entries, by_job, patterns = materializer.input_closure(names)
        paths = set(entries)
        self.assertEqual(set(by_job), set(names))
        for name in names:
            self.assertIn(f"jobs/{name}/job.py", paths)
            self.assertTrue(any(p.startswith(f"jobs/{name}/output/") for p in paths),
                            f"selected job's prior output/custody missing: {name}")
        self.assertIn("jobs/example-hello/output/machine.json", paths)
        self.assertIn("jobs/early-ranger-original-items/output/PRIMARY_ITEM_METADATA.jsonl", paths)
        self.assertNotIn("jobs/claim-kit/output/INDEX.json", paths)
        self.assertLess(sum(map(len, patterns.values())), len(paths))
        self.assertEqual(materializer.entries_digest(entries),
                         materializer.entries_digest(dict(reversed(sorted(entries.items())))))

    def test_predecessor_outputs_are_in_the_declared_closure(self):
        entries, _, patterns = materializer.input_closure(["early-ranger-transcriptions"])
        paths = set(entries)
        self.assertIn("jobs/early-ranger-original-items/output/PRIMARY_ITEM_METADATA.jsonl", paths)
        self.assertIn("jobs/early-ranger-original-items/output/STATUS.json", paths)
        self.assertIn("/jobs/early-ranger-original-items/output/**", patterns["early-ranger-transcriptions"])


if __name__ == "__main__":
    unittest.main()
