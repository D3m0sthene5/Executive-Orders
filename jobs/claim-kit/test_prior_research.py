"""Cumulative preparation never promotes or silently discards previous research."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

import batch
import lifecycle_obligations as lifecycle
import prior_research as prior


class PriorResearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.source = {'url': 'https://example.test/order', 'sha256': 'a'*64,
            'text_path': 'held.txt', 'text_sha256': prior.sha(b'The Council shall advise.')}
        (self.repo/'held.txt').write_text('The Council shall advise.')
        self.claim = {'schema': 'eo-lifecycle-claim/v1', 'instrument_id': 'EO:11782',
            'research_rationale': 'Bounded partial research.', 'whole_order_status': 'no',
            'whole_order_end': None, 'savings_residuals': None,
            'unresolved_material_gaps': ['Actual earlier end still requires review.'],
            'operative_clauses': [{'scope_id': 'EO:11782#council',
                'original_operative_text': 'The Council shall advise.', 'original_source': self.source,
                'state_at_cutoff': 'terminated', 'first_end': None, 'current_predicate': None, 'later_events': []}]}
        self.dossier = {'schema': 'eo-claim-kit-dossier/v1', 'instrument_id': 'EO:11782',
            'whole_order_status': 'no', 'clauses': [], 'evidence': {}, 'missing': ['read source']}
        self.dossier['fingerprint'] = batch.canonical_sha(self.dossier)
        self.dossiers = {'EO:11782': self.dossier}

    def write(self, path, value):
        p = self.repo/path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(value)+'\n')
        return p

    def review(self, claim_path, verdict='uphold_partial', **fields):
        p = self.repo/claim_path
        return {'artifact_type': 'independent_ai_claim_review', 'instrument_id': 'EO:11782',
            'reviewer_role': 'ai_review', 'claim_path': claim_path,
            'claim_sha256': prior.canonical_sha(json.loads(p.read_text())),
            'claim_file_sha256': prior.sha(p.read_bytes()), 'verdict': verdict,
            'verdict_scope': 'Only the specified partial inventory and event; no first-end approval.', **fields}

    def collect(self):
        return prior.collect(self.repo, self.dossiers)

    def test_11782_noncanonical_selected_review_and_prior_rejection_survive(self):
        old = 'research/readiness/reviews/session/producer/EO_11782/v3/claim.json'
        new = old.replace('/v3/', '/v4/')
        self.write(old, self.claim)
        self.write('research/readiness/reviews/session/reviewer/v3/REVIEW.json', self.review(old, 'reject', reasons=['Incorrect search scope.']))
        corrected = deepcopy(self.claim);corrected['research_rationale'] = 'Corrected bounded source inventory.'
        self.write(new, corrected)
        self.write('research/readiness/reviews/session/reviewer/v4/REVIEW.json', self.review(new, 'uphold', candidate_version='v4'))
        self.write('research/readiness/reviews/session/BATCH_SELECTION.json', {'EO:11782': {'version': 'v4', 'reason': 'Exact reviewed correction.'}})
        x = self.collect();order = x['orders']['EO:11782']
        self.assertEqual(len(order['versions']), 2)
        self.assertEqual({r['verdict'] for v in order['versions'] for r in v['reviews']}, {'reject','uphold'})
        self.assertTrue(all(r['version_binding']=='exact' for v in order['versions'] for r in v['reviews']))
        self.assertEqual(order['selection_and_checkpoint_records'][0]['record']['version'], 'v4')
        self.assertEqual(x['automatic_approvals'], 0)
        self.assertIsNone(order['current_canonical_claim_sha256'])

    def test_stale_review_and_changed_source_cannot_be_reused(self):
        path = 'research/session/claim.json';self.write(path, self.claim)
        review = self.review(path);self.write('research/session/REVIEW.json', review)
        changed = deepcopy(self.claim);changed['operative_clauses'][0]['first_end'] = {'date': '1982-08-17'}
        self.write(path, changed)
        version = self.collect()['orders']['EO:11782']['versions'][0]
        self.assertEqual(version['reviews'][0]['version_binding'], 'stale_or_mismatched')
        (self.repo/'held.txt').write_text('Different text')
        version = self.collect()['orders']['EO:11782']['versions'][0]
        self.assertEqual(next(iter(version['sources'].values()))['held_text']['state'], 'changed')

    def test_conflicting_versions_remain_unresolved_and_scope_is_not_assumed(self):
        for date in ('1980-01-01', '1982-08-17'):
            claim = deepcopy(self.claim);claim['operative_clauses'][0]['first_end'] = {'date': date}
            self.write('research/session/'+date+'/claim.json', claim)
        order = self.collect()['orders']['EO:11782']
        self.assertEqual(order['conflicting_versions'][0]['fields'], ['first_end'])
        self.assertEqual(order['conflicting_versions'][0]['resolution'], 'unresolved_by_preparation')
        self.assertEqual(order['versions'][0]['scopes'][0]['alignment'], 'scope_or_source_reconciliation_required')

    def test_no_prior_history_and_unfinished_other_producer_checkpoint(self):
        self.assertEqual(self.collect()['orders']['EO:11782']['state'], 'no_prior_research_located')
        self.write('research/another/producer/IN_PROGRESS.json', {'instrument_id': 'EO:11782',
            'actual_reads': ['Two provisions read.'], 'claim_created': False, 'next': ['Check scope.']})
        order = self.collect()['orders']['EO:11782']
        self.assertEqual(order['unfinished_work'][0]['record']['next'], ['Check scope.'])
        self.assertEqual(order['versions'], [])

    def test_current_valid_partial_review_retains_qualified_scope_and_only_existing_gaps(self):
        path = 'research/readiness/claims/producer.jsonl';self.write(path, self.claim)
        self.write('research/independent/REVIEW.json', {'schema': 'eo-partial-source-ai-review/v1',
            'reviewer': 'other', 'review_kind': 'separate AI source review', 'claim_file': path,
            'claim_file_sha256': prior.sha((self.repo/path).read_bytes()), 'scope': 'Partial only.',
            'claims': [{'instrument_id': 'EO:11782', 'claim_sha256': prior.canonical_sha(self.claim),
                'verdict': 'approve_exact_partial_claim', 'full_lifecycle_approved': False}]})
        order = self.collect()['orders']['EO:11782'];version = order['versions'][0]
        self.assertTrue(version['current_canonical'])
        self.assertEqual(version['reviews'][0]['version_binding'], 'exact')
        self.assertFalse(version['reviews'][0]['full_lifecycle_approved'])
        self.assertEqual(version['scopes'][0]['different_current_fields'], [])
        self.assertEqual(order['remaining_delta']['current_reported_gaps'], self.claim['unresolved_material_gaps'])
        self.assertEqual(order['remaining_delta']['new_legal_gaps_invented'], [])

    def test_frozen_planted_control_excluded_but_real_blind_candidate_retained(self):
        control = self.write('research/review/blind/C.json', self.claim)
        real = deepcopy(self.claim);real['research_rationale'] = 'Actual proposed research.'
        candidate = self.write('research/review/blind/A.json', real)
        self.write('research/review/blind/FREEZE.json', {'candidates': {
            'C': prior.sha(control.read_bytes()), 'A': prior.sha(candidate.read_bytes())}})
        self.write('research/review/CONTROL_REVEAL.json', {'controls': {'C': 'Planted omission.'},
            'real_candidates': {'A': 'Actual claim'}})
        result = self.collect()
        self.assertEqual(len(result['orders']['EO:11782']['versions']), 1)
        self.assertEqual(result['orders']['EO:11782']['versions'][0]['research_rationale'], 'Actual proposed research.')
        self.assertEqual(result['excluded_control_records'][0]['binding'], 'exact')

    def test_existing_source_block_checkpoint_and_default_cli_resume_without_feedback(self):
        import contextlib
        import io
        old = {'schema': 'eo-source-blocked-work/v1', 'instrument_id': 'EO:11782',
            'state': 'source_blocked', 'reason': 'Actual report not established.',
            'source_requests': [{'citation': 'actual report'}], 'result_paths': ['research/attempt.json']}
        self.write('research/previous/CHECKPOINT.json', old)
        found = self.collect()['orders']['EO:11782']['unfinished_work'][0]
        self.assertEqual(found['record']['reason'], old['reason'])
        dossier_path = self.write('dossier.json', self.dossier)
        requests_path = self.write('requests.json', [{'citation': 'actual report'}])
        checkpoint_path = self.repo/'research/new/CHECKPOINT.json'
        common = ['--repo', str(self.repo), '--dossier', str(dossier_path),
            '--requests', str(requests_path), '--routes-sha256', 'a'*64]
        with contextlib.redirect_stdout(io.StringIO()):
            lifecycle.main(['checkpoint', *common, '--reason', 'Missing report', '--result',
                'research/attempt.json', '--out', str(checkpoint_path)])
            result_path = self.repo/'research/new/RESUME.json'
            lifecycle.main(['resume', *common, '--checkpoint', str(checkpoint_path), '--out', str(result_path)])
        self.assertEqual(json.loads(result_path.read_text())['action'], 'defer_unchanged_source_block')

    def test_default_packet_and_resume_fingerprints_reject_changed_prior_work(self):
        self.write('research/session/claim.json', self.claim)
        out = self.repo/'compiled';self.write('compiled/dossiers/EO_11782.json', self.dossier)
        self.write('compiled/INDEX.json', [{'instrument_id': 'EO:11782',
            'status': self.dossier['whole_order_status'], 'fingerprint': self.dossier['fingerprint']}])
        dest = self.repo/'research/packet'
        batch.prepare(self.repo,out,dest,['EO:11782'],'test')
        packet, _ = batch.load_packet(dest,self.repo)
        self.assertIn('Prior research', (dest/'READ.md').read_text())
        self.assertEqual(batch.rows(dest/'decisions.csv')[0]['approved'], 'false')
        old = self.collect()
        check = lifecycle.blocked_checkpoint(self.dossier,[{'id':'source'}],'a'*64,'not held',['attempt'],prior_research=old)
        self.assertEqual(lifecycle.resume_decision(check,self.dossier,[{'id':'source'}],'a'*64,prior_research=old)['action'], 'defer_unchanged_source_block')
        self.write('research/session/IN_PROGRESS.json', {'instrument_id': 'EO:11782', 'actual_reads': ['New source read.']})
        with self.assertRaisesRegex(ValueError, 'changed prior research'):
            batch.load_packet(dest,self.repo)
        self.assertEqual(lifecycle.resume_decision(check,self.dossier,[{'id':'source'}],'a'*64,prior_research=self.collect())['action'], 'reopen')


if __name__ == '__main__':
    unittest.main()
