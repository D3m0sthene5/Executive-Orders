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
        base = {'schema': 'eo-claim-kit-dossier/v1', 'instrument_id': self.iid,
            'whole_order_status': None, 'clauses': []}
        base['fingerprint'] = prior.canonical_sha(base)
        self.evidence = {'schema': 'eo-status-overlay-evidence/v1', 'instrument_id': self.iid,
            'history_packet': {'history': history}, 'history_sha256': history['fingerprint'],
            'base_dossier': base,
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
        self.assertEqual(self.item()['adoption']['state'], 'current_status_present_version_reconciliation_required')

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

    def test_history_must_reproduce_its_own_pin_even_when_evidence_is_resealed(self):
        changed = deepcopy(self.evidence)
        changed['history_packet']['history']['new_assertion'] = 'Unreviewed assertion'
        changed['fingerprint'] = prior.canonical_sha({k:v for k,v in changed.items() if k != 'fingerprint'})
        self.write(self.folder + '/EVIDENCE.json', changed)
        decision = {**self.decision, 'evidence_sha256': changed['fingerprint']}
        self.write(self.decision_path, decision)
        self.assertEqual(self.item()['evidence']['canonical_binding'], 'stale_or_mismatched')

    def test_wrong_evidence_manifest_member_requires_reconciliation(self):
        wrong = deepcopy(self.evidence);wrong['instrument_id'] = 'EO:14006'
        wrong['fingerprint'] = prior.canonical_sha({k:v for k,v in wrong.items() if k != 'fingerprint'})
        other = self.folder + '/WRONG_EVIDENCE.json';self.write(other, wrong)
        cross = deepcopy(self.cross)
        cross['verdicts'][0]['input_files'][1] = {'path': other, 'sha256': self.digest(other)}
        self.write(self.cross_path, cross)
        item = self.item();review = next(r for r in item['reviews'] if r['path'] == self.cross_path)
        self.assertEqual(item['evidence']['canonical_binding'], 'exact')
        self.assertEqual(review['version_binding'], 'stale_or_mismatched')
        self.assertEqual(review['dependency_state'], 'reconciliation_required')
        self.assertEqual(item['adoption']['state'], 'current_status_present_version_reconciliation_required')
        self.assertTrue(any(p['path'] == self.folder + '/EVIDENCE.json' and p['state'] == 'missing_review_input'
                            for p in item['reconciliation_tasks']))

    def test_required_manifest_evidence_hash_cannot_be_absent(self):
        cross = deepcopy(self.cross);cross['verdicts'][0]['input_files'][1].pop('sha256')
        self.write(self.cross_path, cross)
        item = self.item();review = next(r for r in item['reviews'] if r['path'] == self.cross_path)
        self.assertEqual(review['version_binding'], 'stale_or_mismatched')
        self.assertEqual(review['dependency_state'], 'reconciliation_required')
        self.assertEqual(item['adoption']['state'], 'current_status_present_version_reconciliation_required')
        self.assertTrue(any(p['state'] == 'missing_or_invalid_review_input_sha256' for p in item['reconciliation_tasks']))

    def test_resealed_wrong_instrument_base_dossier_cannot_bind(self):
        evidence = deepcopy(self.evidence);evidence['base_dossier']['instrument_id'] = 'EO:14006'
        evidence['base_dossier']['fingerprint'] = prior.canonical_sha(evidence['base_dossier'])
        evidence['fingerprint'] = prior.canonical_sha({k:v for k,v in evidence.items() if k != 'fingerprint'})
        self.write(self.folder + '/EVIDENCE.json', evidence)
        decision = {**self.decision, 'evidence_sha256': evidence['fingerprint']};self.write(self.decision_path, decision)
        review = {**self.review, 'decision_sha256': prior.canonical_sha(decision), 'evidence_sha256': evidence['fingerprint']}
        self.write(self.folder + '/STATUS_REVIEW.json', review)
        cross = deepcopy(self.cross)
        cross['verdicts'][0]['input_files'][0]['sha256'] = self.digest(self.decision_path)
        cross['verdicts'][0]['input_files'][1]['sha256'] = self.digest(self.folder + '/EVIDENCE.json')
        cross['verdicts'][0]['evidence_canonical_fingerprint'] = evidence['fingerprint']
        self.write(self.cross_path, cross)
        item = self.item()
        self.assertEqual(item['evidence']['canonical_binding'], 'stale_or_mismatched')
        self.assertTrue(all(r['version_binding'] == 'stale_or_mismatched' for r in item['reviews']))
        self.assertTrue(all(r['dependency_state'] == 'reconciliation_required' for r in item['reviews']))
        self.assertEqual(item['adoption']['state'], 'current_status_present_version_reconciliation_required')
        self.assertTrue(any(p['state'] == 'invalid_evidence_binding' for p in item['reconciliation_tasks']))

    def test_existing_clause_questions_keep_scope_and_pointer_without_new_legal_gaps(self):
        obligation = {'scope_id': self.iid + '#sec4', 'clause_sha256': 'a'*64,
            'state': 'requires_clause_specific_research',
            'questions': ['Distinguish the due date and demonstrated performance.'],
            'own_term_evidence_ids': ['TERM:deadline'], 'later_actor_evidence_ids': ['ACT:ending']}
        self.dossiers[self.iid]['lifecycle_obligations'] = [obligation]
        brief = prior.brief(self.collect(), self.iid)
        self.assertEqual(brief['remaining_delta']['existing_lifecycle_questions'],
            [{**obligation, 'dossier_pointer': '/lifecycle_obligations/0'}])
        self.assertEqual(brief['remaining_delta']['new_legal_gaps_invented'], [])

    def write_hold(self):
        self.historical_path = 'research/session/lean/LEAN_REVIEW.json'
        self.hold_path = 'research/session/lean/HELD_PROPOSALS.json'
        self.historical = {'schema': 'sinclair-lean-review/v1', 'verdicts': [
            {'instrument_id': self.iid, 'verdict': 'uphold', 'q2': {'note': 'Only names parent.'}}]}
        self.write(self.historical_path, self.historical)
        self.hold = {'schema': 'eo-pending-adoption-procedural-hold/v1',
            'disposition': 'held_out_of_pending_adoption', 'label': 'Procedural hold, not a new verdict.',
            'reason': 'Inconsistent parent-ending treatment requires resolution.',
            'review_file': self.historical_path, 'review_file_sha256': self.digest(self.historical_path),
            'ruling_references': [{'cited_path': self.ruling_path, 'verified_blob_sha': 'historical-git-blob'}],
            'proposals': [{'instrument_id': self.iid, 'current_disposition': 'held_out_of_pending_adoption',
                'hold_reason': 'Ending names parent only.', 'original_review_pointer': '/verdicts/0',
                'original_review_verdict': 'uphold', 'original_review_source_file': self.source,
                'original_review_locus': 'Parent section 4', 'original_review_defects': ['Indirect naming']}]}
        self.write(self.hold_path, self.hold)

    def test_parent_ending_hold_preserves_pinned_history_without_approval(self):
        self.write_hold()
        context = self.collect();hold = context['orders'][self.iid]['status_holds'][0]
        self.assertEqual(hold['state'], 'held_out_of_pending_adoption')
        self.assertEqual(hold['historical_review']['binding'], 'exact')
        self.assertEqual(hold['historical_review']['record'], self.historical['verdicts'][0])
        self.assertEqual(hold['historical_review']['producer_version_binding'], 'not_established_by_procedural_hold')
        self.assertFalse(hold['automatic_approval']);self.assertFalse(hold['full_lifecycle_approved'])
        brief = prior.brief(context, self.iid)
        self.assertIn('Ending names parent only.', json.dumps(brief['status_holds']))
        self.assertEqual(brief['status_holds'][0]['historical_review']['pointer'], '/verdicts/0')

    def test_changed_missing_or_wrong_instrument_hold_review_stays_unresolved(self):
        self.write_hold()
        changed = deepcopy(self.historical);changed['verdicts'][0]['instrument_id'] = 'EO:other'
        self.write(self.historical_path, changed)
        hold = self.collect()['orders'][self.iid]['status_holds'][0]
        self.assertEqual(hold['historical_review']['binding'], 'reconciliation_required')
        self.assertEqual(hold['historical_review']['file']['state'], 'changed')
        self.assertIsNone(hold['historical_review']['record'])
        (self.repo/self.historical_path).unlink()
        hold = self.collect()['orders'][self.iid]['status_holds'][0]
        self.assertEqual(hold['historical_review']['binding'], 'reconciliation_required')
        self.assertEqual(hold['historical_review']['file']['state'], 'missing')
        self.assertEqual(hold['state'], 'held_out_of_pending_adoption')

    def test_saved_collector_context_does_not_discover_itself_as_status_research(self):
        context = self.collect()
        self.write('research/replay/VALIDATED_CONTEXT.json', context)
        self.assertEqual(self.collect(), context)


if __name__ == '__main__':
    unittest.main()
