"""Actual status schemas retain findings without inheriting legal approval."""
import csv
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

import prior_research as prior


class StatusContinuityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.iid = 'EO:13975'
        self.folder = 'research/session/overlay/EO_13975/proposal-v1'
        self.decision_path = self.folder + '/STATUS_DECISION.json'
        self.cross_path = 'research/session/lean/CROSS_FAMILY_REVIEW.json'
        self.source = 'jobs/held/EO_14005.txt'
        self.write_text(self.source, 'Section 14(a). Executive Order 13975 is hereby revoked.')
        self.ruling_path = 'research/readiness/owner_rulings/2026-10-21-status-proposal-adoption.md'
        self.write_text(self.ruling_path, 'Status only. Different family review required.')
        history = {'instrument_id': self.iid}
        history['fingerprint'] = prior.canonical_sha(history)
        self.evidence = {'schema': 'eo-status-overlay-evidence/v1', 'instrument_id': self.iid,
            'history_packet': {'history': history}, 'history_sha256': history['fingerprint'],
            'source_fingerprints': {self.source: self.digest(self.source)}}
        self.evidence['fingerprint'] = prior.canonical_sha(self.evidence)
        self.write(self.folder + '/EVIDENCE.json', self.evidence)
        self.decision = {'schema': 'eo-status-history-decision/v1', 'instrument_id': self.iid,
            'agent': 'producer', 'recommended_provisional_status': 'no', 'approved': True,
            'evidence_sha256': self.evidence['fingerprint'], 'history_sha256': history['fingerprint'],
            'basis_evidence_ids': ['ACT:EO:13975>EO:14005'], 'material_gaps': [],
            'rationale': 'EO14005 section14(a), not the erroneous EO14006 catalog attribution.'}
        self.write(self.decision_path, self.decision)
        self.review = {'schema': 'eo-status-overlay-review/v1', 'instrument_id': self.iid,
            'decision_sha256': prior.canonical_sha(self.decision), 'evidence_sha256': self.evidence['fingerprint'],
            'history_sha256': history['fingerprint'], 'decision': 'accept', 'reviewer': 'other',
            'notice': 'Provisional status only.'}
        self.write(self.folder + '/STATUS_REVIEW.json', self.review)
        self.cross = {'schema': 'sinclair-cross-family-lean-review/v1',
            'reviewer': {'identity': 'independent', 'model_family': 'another'},
            'ruling': {'path': self.ruling_path, 'sha256': self.digest(self.ruling_path)},
            'verdicts': [{'instrument_id': self.iid, 'producer': 'producer', 'verdict': 'uphold',
                'reviewer': 'independent', 'scope': 'Provisional only, not first cessation.',
                'input_files': [{'path': self.decision_path, 'sha256': self.digest(self.decision_path)},
                    {'path': self.folder + '/EVIDENCE.json', 'sha256': self.digest(self.folder + '/EVIDENCE.json')}],
                'evidence_canonical_fingerprint': self.evidence['fingerprint'],
                'sources': [{'path': self.source, 'sha256': self.digest(self.source)}],
                'checklist': {'q2': {'locus': 'EO14005 section14(a)', 'source': self.source},
                    'q7': {'reason': 'Correct catalog14006 to14005; not all procurement effects.'}},
                'd6': {'assessment': 'EO14006 does not revoke13975.',
                    'coverage': 'Held sources only; no exhaustive absence finding.'}}]}
        self.write(self.cross_path, self.cross)
        path = self.repo/'research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv'
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=['instrument_id', 'provisional_substantive_status', 'decision_origin'])
            writer.writeheader();writer.writerow({'instrument_id': self.iid,
                'provisional_substantive_status': 'no', 'decision_origin': self.cross_path})
        self.dossiers = {self.iid: {'instrument_id': self.iid, 'clauses': [], 'fingerprint': 'd'*64}}

    def write_text(self, path, value):
        p = self.repo/path;p.parent.mkdir(parents=True, exist_ok=True);p.write_text(value)

    def write(self, path, value):
        self.write_text(path, json.dumps(value)+'\n')

    def digest(self, path):
        return prior.sha((self.repo/path).read_bytes())

    def collect(self):
        return prior.collect(self.repo, self.dossiers)

    def item(self):
        return self.collect()['orders'][self.iid]['status_research'][0]

    def test_exact_producer_and_scoped_corrections_reach_brief(self):
        context = self.collect();item = context['orders'][self.iid]['status_research'][0]
        self.assertEqual([r['version_binding'] for r in item['reviews']], ['exact', 'exact'])
        self.assertEqual(item['evidence']['canonical_binding'], 'exact')
        self.assertEqual(item['adoption']['state'], 'recorded_provisional_status_for_review')
        rendered = json.dumps(prior.brief(context, self.iid))
        self.assertIn('Correct catalog14006 to14005', rendered)
        self.assertIn('no exhaustive absence finding', rendered)
        self.assertFalse(item['automatic_approval'])
        self.assertTrue(all(r['full_lifecycle_approved'] is False for r in item['reviews']))
        self.assertEqual(context['automatic_approvals'], 0)

    def test_changed_and_missing_source_are_explicit_reconciliation(self):
        before = self.collect()
        self.write_text(self.source, 'Changed source')
        changed = self.item()
        self.assertTrue(any(t['path'] == self.source and t['state'] == 'changed' for t in changed['reconciliation_tasks']))
        (self.repo/self.source).unlink()
        missing = self.item()
        self.assertTrue(any(t['path'] == self.source and t['state'] == 'missing' for t in missing['reconciliation_tasks']))
        self.assertNotEqual(before['input_file_pins'], self.collect()['input_file_pins'])

    def test_stale_producer_review_keeps_rejected_version_visible(self):
        changed = deepcopy(self.decision);changed['rationale'] = 'Unsupported different theory.'
        self.write(self.decision_path, changed)
        self.assertTrue(all(r['version_binding'] == 'stale_or_mismatched' for r in self.item()['reviews']))
        self.assertTrue(any('stale or mismatched review' in q for q in self.item()['remaining_questions']))

    def test_wrong_instrument_never_binds_cross_family_review(self):
        changed = deepcopy(self.decision);changed['instrument_id'] = 'EO:14006'
        self.write(self.decision_path, changed)
        order = self.collect()['orders'][self.iid]
        self.assertEqual(order['status_research'], [])
        self.assertTrue(order['unattached_status_reviews'])
        self.assertTrue(all(r['version_binding'] != 'exact' for r in order['unattached_status_reviews']))

    def test_unadopted_proposal_still_carries_research_without_adoption(self):
        (self.repo/'research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv').unlink()
        item = self.item()
        self.assertEqual(item['adoption']['state'], 'not_recorded_in_current_authority')
        self.assertFalse(item['adoption']['legal_approval_inferred'])
        self.assertEqual(len(item['reviews']), 2)

    def test_missing_review_is_not_inferred_from_adopted_row_or_producer_approval(self):
        (self.repo/self.cross_path).unlink();(self.repo/self.folder/'STATUS_REVIEW.json').unlink()
        item = self.item()
        self.assertEqual(item['reviews'], [])
        self.assertEqual(item['adoption']['state'], 'current_status_present_version_reconciliation_required')
        self.assertTrue(any('No matching status review' in q for q in item['remaining_questions']))
        self.assertFalse(item['automatic_approval'])

    def test_changed_evidence_and_current_ruling_are_not_silently_reused(self):
        changed = deepcopy(self.evidence);changed['history_sha256'] = 'bad'
        self.write(self.folder + '/EVIDENCE.json', changed)
        self.write_text(self.ruling_path, 'Changed ruling')
        item = self.item()
        self.assertEqual(item['evidence']['canonical_binding'], 'stale_or_mismatched')
        self.assertTrue(all(r['version_binding'] != 'exact' for r in item['reviews']))
        self.assertTrue(any(t['path'] == self.ruling_path and t['state'] == 'changed' for t in item['reconciliation_tasks']))


if __name__ == '__main__':
    unittest.main()
