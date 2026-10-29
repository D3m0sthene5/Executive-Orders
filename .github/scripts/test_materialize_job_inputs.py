"""Bounded regressions for sparse runner input closure construction."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

spec = importlib.util.spec_from_file_location("materialize_job_inputs", HERE / "materialize_job_inputs.py")
materializer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(materializer)


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
        self.assertIn("            /jobs/**\n", workflow)
        self.assertIn("            !/jobs/*/output/**\n", workflow)
        self.assertNotIn("/jobs/*/job.py", workflow)
        choose = workflow.index("- name: Choose which jobs to run")
        cache = workflow.index("- name: Restore each job's bounded download cache")
        materialize = workflow.index("- name: Materialize selected job inputs and prior outputs")
        self.assertLess(choose, cache)
        self.assertLess(cache, materialize)
        cache_step = workflow[cache:materialize]
        self.assertIn("if: steps.pick.outputs.jobs != ''", cache_step)

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
