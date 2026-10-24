"""Exact reviewed versions, control judgments, holds, bytes, and replay routing."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import batch
import completion as C
import test_batch as B


class CompletionTests(B.BatchTests):
    def setup_completion(self):
        self.folder = self.packet(('EO:1',))
        self.fill(self.folder)
        batch.apply(self.repo, self.folder, self.folder / 'applied')
        self.claim = json.loads((self.folder / 'applied/CLAIMS.proposed.jsonl').read_bytes())
        # Deliberately noncanonical spaces and CRLF: preserving producer bytes
        # is distinct from comparing Stage19's semantic claim hash.
        self.producer = self.folder / 'PRODUCER.jsonl'
        self.producer.write_bytes((json.dumps(self.claim, ensure_ascii=False, separators=(', ', ': ')) + '\r\n').encode())
        self.review = {'instrument_id': 'EO:1', 'claim_sha256': C.claim_sha(self.claim),
                       'reviewer': 'reviewer', 'model_family': 'OpenAI', 'independent': True,
                       'separate_context': True, 'review_kind': 'independent_ai_source_review',
                       'scope': 'whole_case', 'verdict': 'upheld'}
        self.review_path = self.folder / 'REVIEW.json'
        batch.dump(self.review_path, self.review)
        self.manifest = {'schema': C.SCHEMA, 'agent': 'producer', 'producer_model_family': 'OpenAI',
                         'independence_requirement': 'same_family_separate_context', 'controls': [],
                         'members': [{'instrument_id': 'EO:1', 'claim_sha256': C.claim_sha(self.claim),
                                      'outcome': 'submit', 'claim': self.ref(self.producer, line=1),
                                      'publication_kind': 'whole_case', 'review': self.ref(self.review_path),
                                      'packet': self.ref(self.folder / 'PACKET.json')}],
                         'publication': {'mode': 'own_claims', 'path': 'research/readiness/claims/producer-2026-10-24.jsonl'}}
        self.manifest_path = self.folder / 'COMPLETION.json'
        self.dest = self.folder / 'complete'

    def ref(self, path, **selector):
        return {'path': path.relative_to(self.repo).as_posix(), 'sha256': batch.file_sha(path), **selector}

    def checker(self, repo, claims, dest):
        dest.mkdir()
        rows = [{'instrument_id': c['instrument_id'], 'claim_sha256': C.claim_sha(c),
                 'mechanical_result': 'pass', 'all_checks_passed': True, 'gate_errors': []}
                for c in map(json.loads, claims.read_bytes().splitlines())]
        doc = {'claims': rows, 'by_instrument': {c['instrument_id']: c for c in rows}}
        batch.dump(dest / 'PER_CLAIM.json', doc)
        return doc

    def run_completion(self, publish=False):
        batch.dump(self.manifest_path, self.manifest)
        with patch.object(C, 'run_checker', side_effect=self.checker), patch.object(C, 'run_tracker', return_value={'actual_fixture': True}):
            return C.complete(self.repo, self.manifest_path, self.dest, publish)

    def add_control(self, caught=True, after=True):
        planted = deepcopy(self.claim)
        planted['research_rationale'] += ' Seeded defect for this fixture.'
        plant_path = self.folder / 'PLANT.jsonl'
        plant_path.write_bytes((json.dumps(planted) + '\n').encode())
        plant_review = dict(self.review, claim_sha256=C.claim_sha(planted), verdict='rejected',
                            rationale='No keyword matching can establish whether this names the defect.')
        review_path = self.folder / 'PLANT_REVIEW.json'
        batch.dump(review_path, plant_review)
        adjudication = {'instrument_id': 'EO:1', 'planted_claim_sha256': C.claim_sha(planted),
                        'review': self.ref(review_path), 'adjudicator': 'semantic-reviewer',
                        'caught': caught, 'scoring': 'strict', 'rationale': 'Explicit semantic adjudication.'}
        adjudication_path = self.folder / 'CONTROL_ADJUDICATION.json'
        batch.dump(adjudication_path, adjudication)
        self.manifest['controls'] = [{'instrument_id': 'EO:1', 'planted_claim_sha256': C.claim_sha(planted),
                                     'claim': self.ref(plant_path, line=1), 'review': self.ref(review_path),
                                     'adjudication': self.ref(adjudication_path)}]
        if after:
            path = self.folder / 'AFTER_REVEAL.json'
            batch.dump(path, dict(self.review, verdict='upheld_after_reveal'))
            self.manifest['members'][0]['after_reveal_review'] = self.ref(path)

    def test_exact_producer_bytes_and_all_consumed_receipts_preserved(self):
        self.setup_completion()
        result = self.run_completion(publish=True)
        self.assertEqual(result['eligible'], ['EO:1'])
        target = self.repo / self.manifest['publication']['path']
        self.assertEqual(target.read_bytes(), self.producer.read_bytes())
        self.assertEqual((self.dest / 'CLAIMS.publishable.jsonl').read_bytes(), self.producer.read_bytes())
        saved = self.dest / 'receipts' / self.review_path.relative_to(self.repo)
        self.assertEqual(saved.read_bytes(), self.review_path.read_bytes())
        self.assertEqual(result['independent_human_certifications'], 0)
        self.assertIsNone(result['model_tokens'])
        with self.assertRaisesRegex(ValueError, 'fresh research'):
            C.complete(self.repo, self.manifest_path, self.dest)

    def test_stale_exact_review_is_exception_and_no_publication(self):
        self.setup_completion()
        batch.dump(self.review_path, dict(self.review, claim_sha256='0' * 64))
        self.manifest['members'][0]['review'] = self.ref(self.review_path)
        result = self.run_completion(publish=True)
        self.assertEqual(result['eligible'], [])
        self.assertIn('selected exact', result['outcomes'][0]['error'])
        self.assertFalse((self.repo / self.manifest['publication']['path']).exists())

    def test_changed_file_does_not_silently_select_a_new_version(self):
        self.setup_completion()
        self.producer.write_bytes(self.producer.read_bytes() + self.producer.read_bytes())
        result = self.run_completion()
        self.assertIn('changed input', result['outcomes'][0]['error'])
        self.assertEqual(result['eligible'], [])

    def test_conflicting_selected_versions_are_refused(self):
        self.setup_completion()
        self.manifest['members'].append(dict(self.manifest['members'][0], claim_sha256='0' * 64))
        with self.assertRaisesRegex(ValueError, 'conflicting or duplicate'):
            self.run_completion()

    def test_exact_hold_blocks_but_a_different_held_version_does_not(self):
        self.setup_completion()
        path = self.repo / 'research/readiness/SOURCE_AUDIT_HOLDS.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        hold = {'schema': 'eo-source-audit-hold/v1', 'state': 'unresolved', 'instrument_id': 'EO:1',
                'claim_sha256': C.claim_sha(self.claim), 'reason': 'Exact source audit conflict',
                'review_path': self.review_path.relative_to(self.repo).as_posix(),
                'review_sha256': batch.file_sha(self.review_path)}
        path.write_text(json.dumps(hold) + '\n')
        # Avoid refreshing the packet: holds are independently checked first.
        result = self.run_completion()
        self.assertIn('exact version has unresolved', result['outcomes'][0]['error'])
        hold['claim_sha256'] = '0' * 64
        path.write_text(json.dumps(hold) + '\n')
        self.assertNotIn(('EO:1', C.claim_sha(self.claim)), C.held_versions(C.Inputs(self.repo)))
        self.assertEqual(path.read_text(), json.dumps(hold) + '\n')

    def test_control_adjudication_not_reason_keywords_and_after_reveal_exact(self):
        self.setup_completion()
        self.add_control()
        result = self.run_completion()
        self.assertEqual(result['plants_caught'], 1)
        self.assertEqual(result['eligible'], ['EO:1'])
        self.assertTrue(result['outcomes'][0]['after_reveal'])

    def test_control_false_stops_batch_even_with_upheld_after_reveal(self):
        self.setup_completion()
        self.add_control(caught=False)
        result = self.run_completion(publish=True)
        self.assertEqual(result['eligible'], [])
        self.assertEqual(result['plants_caught'], 0)
        self.assertFalse((self.repo / self.manifest['publication']['path']).exists())

    def test_missing_adjudication_and_missing_after_reveal_fail_closed(self):
        self.setup_completion()
        self.add_control(after=False)
        result = self.run_completion()
        self.assertEqual(result['eligible'], [])
        self.assertIn('after_reveal_review', result['outcomes'][0]['error'])
        self.dest = self.folder / 'complete2'
        self.manifest['controls'][0].pop('adjudication')
        result = self.run_completion()
        self.assertEqual(result['eligible'], [])
        self.assertEqual(result['plants_caught'], 0)

    def test_planted_exact_claim_never_filed(self):
        self.setup_completion()
        self.add_control()
        control = self.manifest['controls'][0]
        self.manifest['members'][0].update(claim=control['claim'], claim_sha256=control['planted_claim_sha256'])
        result = self.run_completion()
        self.assertIn('planted version cannot be filed', result['outcomes'][0]['error'])

    def test_cross_family_requirement_and_reviewer_identity(self):
        self.setup_completion()
        self.manifest['independence_requirement'] = 'different_family'
        result = self.run_completion()
        self.assertIn('different model family', result['outcomes'][0]['error'])
        self.dest = self.folder / 'complete2'
        self.manifest['independence_requirement'] = 'same_family_separate_context'
        batch.dump(self.review_path, dict(self.review, reviewer='producer'))
        self.manifest['members'][0]['review'] = self.ref(self.review_path)
        result = self.run_completion()
        self.assertIn('independent source review', result['outcomes'][0]['error'])

    def test_partial_keeps_full_gate_errors_and_does_not_repair_claim(self):
        self.setup_completion()
        self.claim.pop('claim_kit')
        self.claim['operative_clauses'][0]['first_end'] = None
        self.claim['whole_order_end'] = None
        self.claim['unresolved_material_gaps'] = ['Exact first cessation unresolved.']
        self.producer.write_bytes((json.dumps(self.claim) + '\n').encode())
        errors = C._gate(self.repo).validate_claim(self.claim)
        batch.dump(self.review_path, dict(self.review, claim_sha256=C.claim_sha(self.claim),
                                         scope='partial_research', expected_gate_errors=errors))
        self.manifest['members'][0].update(claim=self.ref(self.producer, line=1), claim_sha256=C.claim_sha(self.claim),
                                           publication_kind='partial_research', review=self.ref(self.review_path))
        result = self.run_completion()
        self.assertEqual(result['eligible'], ['EO:1'])
        self.assertEqual(result['outcomes'][0]['gate_errors'], errors)
        self.assertEqual((self.dest / 'CLAIMS.publishable.jsonl').read_bytes(), self.producer.read_bytes())

    def test_checker_failure_preserves_proposal_and_exception(self):
        self.setup_completion()
        batch.dump(self.manifest_path, self.manifest)
        with patch.object(C, 'run_checker', side_effect=ValueError('actual checker failed')), patch.object(C, 'run_tracker'):
            result = C.complete(self.repo, self.manifest_path, self.dest)
        self.assertEqual(result['eligible'], [])
        self.assertEqual((self.dest / 'CLAIMS.selected.jsonl').read_bytes(), self.producer.read_bytes())
        self.assertTrue((self.dest / 'EXCEPTIONS.json').exists())

    def test_changed_receipt_during_checker_cannot_publish(self):
        self.setup_completion()
        batch.dump(self.manifest_path, self.manifest)
        def changed(repo, claims, dest):
            result = self.checker(repo, claims, dest)
            self.review_path.write_text('{}')
            return result
        with patch.object(C, 'run_checker', side_effect=changed), patch.object(C, 'run_tracker', return_value={}):
            result = C.complete(self.repo, self.manifest_path, self.dest, True)
        self.assertEqual(result['eligible'], [])
        saved = self.dest / 'receipts' / self.review_path.relative_to(self.repo)
        self.assertEqual(json.loads(saved.read_bytes()), self.review)


# Reuse the corpus fixture and packet helpers, not their tests.
for base in (B.BatchTests, B.T.BuildIntegrationTests):
    for name in vars(base):
        if name.startswith('test_') and name not in CompletionTests.__dict__:
            setattr(CompletionTests, name, None)
del base

if __name__ == '__main__':
    unittest.main()
