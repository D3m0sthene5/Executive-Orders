"""overlay-check runs the completion checker offline before blind review (Kean F-20261112-lind-stage0)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import batch  # noqa: E402


class ActualCheckOffline(unittest.TestCase):
    def test_downloads_are_off_and_unpassed_claims_are_returned(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / 'jobs/claim-checker').mkdir(parents=True)
            (repo / 'jobs/claim-checker/checker.py').write_text('', encoding='utf-8')
            seen = {}

            def fake_run(args, cwd, env, stdout, stderr):
                seen.update(env)
                out = Path(env['OUTPUT_DIR'])
                (out / 'SUMMARY.json').write_text(json.dumps({'claims_checked': 2, 'claims_all_checks_passed': 1}))
                (out / 'PER_CLAIM.json').write_text(json.dumps({'claims': [
                    {'instrument_id': 'EO:1', 'all_checks_passed': True},
                    {'instrument_id': 'EO:2', 'all_checks_passed': False,
                     'unverified': ['source_held:custody_record_only@whole_order_end.source']}]}))
                return subprocess.CompletedProcess(args, 0)
            with mock.patch.object(subprocess, 'run', fake_run):
                summary, not_passed = batch.actual_check_offline(repo, repo / 'C.jsonl', repo / 'out', repo / 'cache')
            self.assertEqual(seen['CLAIM_CHECKER_VERIFY_DOWNLOADS'], '0')
            self.assertEqual(summary['claims_checked'], 2)
            self.assertEqual([r['instrument_id'] for r in not_passed], ['EO:2'])
            self.assertIn('custody_record_only', not_passed[0]['unverified'][0])

    def test_missing_checker_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'unavailable'):
                batch.actual_check_offline(Path(tmp), Path(tmp) / 'C.jsonl', Path(tmp) / 'o', Path(tmp) / 'c')


if __name__ == '__main__':
    unittest.main()
