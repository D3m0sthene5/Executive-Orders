"""Exercise combined declarations without granting another narrow certificate."""
from pathlib import Path
import unittest

import result_freshness as freshness
import materialize_job_inputs as materializer


class CombinedRoutes(unittest.TestCase):
    def selected(self, job):
        return freshness.tree('HEAD', freshness.scope(job))

    def test_census_adapter_code_and_workbench_sources_are_versioned(self):
        selected = self.selected('census-candidates')
        for name in ('job.py', 'roundtrip.py'):
            self.assertIn('jobs/early-ranger-workbench/' + name, selected)
        workbench = self.selected('early-ranger-workbench')
        for path in ('jobs/early-ranger-original-items/output/PRIMARY_ITEM_METADATA.jsonl',
                     'jobs/early-ranger-transcriptions/output/TRANSCRIPTION_INVENTORY.jsonl',
                     'jobs/early-ranger-full-pages/output/PAGE_IMAGE_CUSTODY.csv'):
            self.assertIn(path, workbench)
        self.assertFalse(any(p.startswith('jobs/early-ranger-workbench/output/') for p in workbench))

    def test_optional_diagnostic_code_is_versioned_without_derived_self_input(self):
        selected = self.selected('claim-kit')
        for name in ('after_completion.py', 'production_receipts.py', 'diagnose.py', 'survey.py'):
            self.assertIn('jobs/neyman/' + name, selected)
        self.assertFalse(any(p.startswith('research/neyman/production-diagnostics/') for p in selected))
        self.assertFalse(any(p.startswith('jobs/claim-kit/output/') for p in selected))

    def test_other_routes_keep_their_compatibility_fallback(self):
        result = materializer.fallback_jobs(['claim-kit', 'census-candidates', 'early-ranger-workbench'])
        self.assertEqual(set(result), {'claim-kit', 'census-candidates', 'early-ranger-workbench'})


if __name__ == '__main__':
    unittest.main()
