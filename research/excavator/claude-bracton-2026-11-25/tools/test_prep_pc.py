"""prep_pc.prepare_outcome reads kit prepare's exit code together with the PREPARE.json it wrote."""
import json
from pathlib import Path
import tempfile
import unittest

import prep_pc


class PrepareOutcomeTests(unittest.TestCase):
    def packet(self, check):
        d = Path(tempfile.mkdtemp()); self.addCleanup(lambda: __import__('shutil').rmtree(d))
        if check is not None:
            (d / 'PREPARE.json').write_text(json.dumps({'dispatch_check': check}))
        return d

    def test_partly_blocked_exit_one_is_a_usable_packet(self):
        d = self.packet({'ok': False, 'dispatchable_ids': ['EO:2'], 'source_blocked_ids': ['EO:1']})
        self.assertEqual(prep_pc.prepare_outcome(1, d)[0], 'partly_blocked')

    def test_all_blocked_and_clean_runs(self):
        self.assertEqual(prep_pc.prepare_outcome(1, self.packet({'ok': False, 'dispatchable_ids': []}))[0], 'all_blocked')
        self.assertEqual(prep_pc.prepare_outcome(0, self.packet({'ok': True, 'dispatchable_ids': ['EO:1']}))[0], 'ok')

    def test_refusal_crash_or_missing_receipt_fails(self):
        self.assertEqual(prep_pc.prepare_outcome(2, self.packet({'ok': False, 'dispatchable_ids': ['EO:2']}))[0], 'failed')
        self.assertEqual(prep_pc.prepare_outcome(1, self.packet(None))[0], 'failed')  # a traceback also exits 1
        self.assertEqual(prep_pc.prepare_outcome(1, self.packet({'ok': True, 'dispatchable_ids': ['EO:1']}))[0], 'failed')


if __name__ == '__main__':
    unittest.main()
