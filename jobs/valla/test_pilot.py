"""Current smoke validation retains stale-review refusals and exact-claim holds."""
import copy
import json
from unittest import mock
from pathlib import Path
import tempfile
import unittest

import pilot
import valla as V


class CurrentCorrectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.review = self.repo / 'research/review.json'
        self.review.parent.mkdir(parents=True)
        self.review.write_text('{"verdict": "hold"}\n')
        self.expected = {'EO:1': {'path': 'research/readiness/claims/one.jsonl',
                                  'line': 1, 'claim_sha256': 'a' * 64}}
        self.holds = self.repo / 'research/readiness/SOURCE_AUDIT_HOLDS.jsonl'
        self.holds.parent.mkdir(parents=True)
        self.hold = {'instrument_id': 'EO:1', 'state': 'unresolved',
                     'claim_sha256': 'a' * 64, 'review_path': 'research/review.json',
                     'review_sha256': V.file_sha(self.review)}
        self.holds.write_text(V.canon(self.hold) + '\n')
        self.packet = {'valla_context': {'automatic_approvals': 0,
            'whole_case_review_required': True, 'claims': {'EO:1': {
                'claim_ref': self.expected['EO:1'], 'invalidated_conclusion_pointers': [],
                'component_reviews': [{'valid': False, 'attestation_id': 'Q1',
                    'reason': 'dependency changed: jobs/claim-kit/BATCH.md'}]}}}}

    def test_stale_component_remains_refused_with_verified_hold(self):
        original = copy.deepcopy(self.packet)
        proof = pilot.correction_safety(self.repo, self.packet, self.expected)
        self.assertEqual(self.packet, original)
        self.assertFalse(proof['EO:1']['component_reviews'][0]['valid'])
        self.assertEqual(proof['EO:1']['hold_review_paths'], ['research/review.json'])

    def test_missing_hold_and_stale_claim_are_rejected(self):
        self.holds.write_text('')
        with self.assertRaisesRegex(ValueError, 'exact-claim hold'):
            pilot.correction_safety(self.repo, self.packet, self.expected)
        self.hold['claim_sha256'] = 'b' * 64
        self.holds.write_text(V.canon(self.hold) + '\n')
        with self.assertRaisesRegex(ValueError, 'exact-claim hold'):
            pilot.correction_safety(self.repo, self.packet, self.expected)

    def test_changed_evidence_and_automatic_approval_are_rejected(self):
        self.review.write_text('changed')
        with self.assertRaisesRegex(ValueError, 'artifact changed'):
            pilot.correction_safety(self.repo, self.packet, self.expected)
        self.packet['valla_context']['automatic_approvals'] = 1
        with self.assertRaisesRegex(ValueError, 'zero approvals'):
            pilot.correction_safety(self.repo, self.packet, self.expected)


class AdoptedReplacementTests(unittest.TestCase):
    OLD_PATH = 'research/readiness/claims/old.jsonl'
    NEW_PATH = 'research/readiness/claims/novellae-new.jsonl'

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name).resolve()
        target = self.repo / self.NEW_PATH
        target.parent.mkdir(parents=True)
        target.write_text('{"instrument_id": "EO:1"}\n')
        self.frozen = {'path': self.OLD_PATH, 'line': 2, 'claim_sha256': 'a' * 64}
        self.current = {'path': self.NEW_PATH, 'line': 1, 'claim_sha256': 'b' * 64}
        self.receipt = {'schema': pilot.ADOPTION_SCHEMA, 'decision': 'D-1',
            'publication': {'path': self.NEW_PATH, 'sha256': V.file_sha(target)},
            'claims': [{'instrument_id': 'EO:1', 'claim_sha256': 'b' * 64, 'line': 1,
                        'replaces': dict(self.frozen)}]}
        self.receipt_rel = 'research/excavator/run/REPLACEMENT_ADOPTION.json'
        self.write()

    def write(self):
        path = self.repo / self.receipt_rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.receipt))

    def find(self):
        return pilot.adopted_replacement(self.repo, 'EO:1', self.frozen, self.current)

    def test_recorded_adoption_is_recognized_with_receipt_path(self):
        self.assertEqual(self.find(), self.receipt_rel)

    def test_unrecorded_or_mismatched_changes_are_not_adoptions(self):
        self.receipt['claims'][0]['replaces']['claim_sha256'] = 'c' * 64
        self.write()
        self.assertIsNone(self.find())
        self.receipt['claims'][0]['replaces']['claim_sha256'] = 'a' * 64
        self.receipt['claims'][0]['claim_sha256'] = 'd' * 64
        self.write()
        self.assertIsNone(self.find())
        (self.repo / self.receipt_rel).unlink()
        self.assertIsNone(self.find())

    def test_tampered_publication_is_not_an_adoption(self):
        (self.repo / self.NEW_PATH).write_text('changed\n')
        self.assertIsNone(self.find())

    def sample_repo(self):
        sample_dir = self.repo / 'research/valla/pilot-2026-10-20'
        sample_dir.mkdir(parents=True)
        sample = {'patterns_sha256': V.file_sha(V.HERE / 'premises.json'), 'seed': ['EO:1'],
                  'claims': {'EO:1': self.frozen}}
        (sample_dir / 'SAMPLE.json').write_text(json.dumps(sample))

    def run_pilot(self):
        active = {'EO:1': {'ref': self.current, 'claim': {}}}
        with mock.patch.object(V, 'pins', return_value={}), \
                mock.patch.object(V, 'active_claims', return_value=(active, [])), \
                mock.patch.object(V, 'build', side_effect=RuntimeError('past the claim check')):
            with self.assertRaises((ValueError, RuntimeError)) as caught:
                pilot.run(self.repo, self.repo / 'out', 'r1')
        return caught.exception

    def test_run_skips_and_lists_adopted_order_but_fails_other_changes(self):
        self.sample_repo()
        self.assertIsInstance(self.run_pilot(), RuntimeError)
        listed = json.loads((self.repo / 'out/EXEMPTED_ADOPTED_REPLACEMENTS.json').read_text())
        self.assertEqual(listed['EO:1']['adoption_receipt'], self.receipt_rel)
        (self.repo / self.receipt_rel).unlink()
        (self.repo / 'out').rename(self.repo / 'out-old')
        error = self.run_pilot()
        self.assertIsInstance(error, ValueError)
        self.assertIn('pilot claim changed: EO:1', str(error))


if __name__ == '__main__':
    unittest.main()
