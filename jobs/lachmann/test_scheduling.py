"""Actual producer -> Lachmann -> tracker scheduling without acquisition fanout."""
import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('lachmann_picker', ROOT / '.github/scripts/pick_jobs.py')
picker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(picker)


class Scheduling(unittest.TestCase):
    def test_selected_witness_producers_reach_lachmann_before_tracker(self):
        with patch.dict(os.environ, {}, clear=False):
            previous = Path.cwd()
            try:
                os.chdir(ROOT)
                for producer in picker.job_list('lachmann', 'after.txt'):
                    with self.subTest(producer=producer):
                        self.assertTrue(picker.runnable(producer))
                        selected = picker.ordered(picker.with_consumers([producer]))
                        self.assertLess(selected.index(producer), selected.index('lachmann'))
                        self.assertLess(selected.index('lachmann'), selected.index('readiness-tracker'))
                direct = picker.ordered(picker.with_consumers(['lachmann']))
                self.assertTrue(set(picker.job_list('lachmann', 'after.txt')).isdisjoint(direct))
            finally:
                os.chdir(previous)

    def test_vendor_and_interpretation_edits_select_lachmann_but_outputs_do_not(self):
        previous = Path.cwd()
        try:
            os.chdir(ROOT)
            for relative in ('jobs/csc-annual-reports/data/review/FRAGMENTS.jsonl',
                             'jobs/pinakes-proquest-ingest/data/review/texts/EO_1.txt',
                             'jobs/claim-kit/working_text.py'):
                with self.subTest(path=relative):
                    self.assertIn('lachmann', picker.for_changes([relative]))
            self.assertNotIn('lachmann', picker.for_changes([
                'jobs/pinakes-proquest-ingest/output/FRAGMENTS.jsonl']))
        finally:
            os.chdir(previous)


if __name__ == '__main__':
    unittest.main()
