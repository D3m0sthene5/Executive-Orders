"""Current smoke validation retains stale-review refusals and exact-claim holds."""
import copy
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


if __name__ == '__main__':
    unittest.main()
