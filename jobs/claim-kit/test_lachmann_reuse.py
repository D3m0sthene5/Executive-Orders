"""Exact standalone confirmation reuse and current-record refusals."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parent))
import working_text as W


class ReuseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        text_path = self.repo / 'jobs/source/output/order.txt'
        text_path.parent.mkdir(parents=True)
        text_path.write_text('Executive Order 7\nThe Board shall report.\n', encoding='utf-8')
        self.text_path = 'jobs/source/output/order.txt'
        sha = hashlib.sha256(text_path.read_bytes()).hexdigest()
        self.record = {'schema': W.CONFIRMATION_SCHEMA, 'method': 'machine',
                       'instrument_id': 'EO:7', 'grade': 'mirror_transcription',
                       'sha256': 'a' * 64, 'text_sha256': sha, 'text_path': self.text_path,
                       'acceptable_as_original': False, 'confirmed': True,
                       'identity_confirmed': True, 'complete_text_confirmed': True,
                       'requires_page_check': True, 'pages_confirmed': True}
        fragment = {'kind': 'original_representation', 'instrument_id': 'EO:7',
                    'data': {'grade': self.record['grade'], 'acceptable_as_original': False,
                             'sha256': self.record['sha256'], 'text_sha256': sha,
                             'text_path': self.text_path, 'requires_page_check': True}}
        (self.repo / 'jobs/source/output/FRAGMENTS.jsonl').write_text(json.dumps(fragment) + '\n')
        self.machine = self.repo / W.CONFIRMATION_PATHS[0]
        self.machine.parent.mkdir(parents=True)
        self.machine.write_text(json.dumps(self.record) + '\n')

    def test_exact_match_and_current_record(self):
        prior = W.matching_confirmation(self.record, self.repo)
        self.assertEqual(prior['record'], self.record)
        self.assertEqual(prior['source_path'], W.CONFIRMATION_PATHS[0])
        self.assertTrue(W.blank([self.record], prior)['confirmations'][0]['pages_confirmed'])
        dossier = {'instrument_id': 'EO:7', 'original_source_id': 'ORIGINAL:EO:7',
                   'evidence': {'ORIGINAL:EO:7': {'source': self.record}},
                   'working_text_confirmation': prior}
        W.require_current_confirmation(dossier, self.repo)
        agent = self.repo / W.CONFIRMATION_PATHS[1]
        agent.write_text(json.dumps(dict(self.record, method='agent', confirmed=False)) + '\n')
        self.assertIsNone(W.matching_confirmation(self.record, self.repo))
        with self.assertRaisesRegex(ValueError, 'changed or invalid'):
            W.require_current_confirmation(dossier, self.repo)

    def test_refusals_for_pages_grade_identity_and_bytes(self):
        index = W.Index(self.repo)
        self.assertEqual(W.confirmation_rejection(dict(self.record, pages_confirmed=False), index, self.repo),
                         'pages_not_confirmed_but_page_check_required')
        self.assertEqual(W.confirmation_rejection(dict(self.record, grade='compiled_transcription'), index, self.repo),
                         'pinned_fields_match_no_loaded_fragment')
        self.assertIsNone(W.matching_confirmation(dict(self.record, text_path='other'), self.repo))
        (self.repo / self.text_path).write_text('changed', encoding='utf-8')
        self.assertEqual(W.confirmation_rejection(self.record, index, self.repo),
                         'text_file_missing_or_hash_mismatch')

    def test_each_confirmation_gate_refuses_reuse(self):
        changes = [dict(schema='unknown'), dict(method='human'),
                   dict(acceptable_as_original=True), dict(grade='original'),
                   dict(confirmed=False), dict(identity_confirmed=False),
                   dict(complete_text_confirmed=False), dict(pages_confirmed=False),
                   dict(instrument_id='EO:8'), dict(sha256='b'*64),
                   dict(text_sha256='c'*64), dict(text_path='../outside.txt')]
        for change in changes:
            with self.subTest(change=change):
                self.machine.write_text(json.dumps(dict(self.record, **change))+'\n')
                self.assertIsNone(W.matching_confirmation(self.record, self.repo))

    def test_fragment_completeness_and_new_page_requirement_stale_prior(self):
        fragment_path = self.repo/'jobs/source/output/FRAGMENTS.jsonl'
        fragment = json.loads(fragment_path.read_text())
        prior = W.matching_confirmation(self.record, self.repo)
        dossier = {'original_source_id':'o', 'evidence':{'o':{'source':self.record}},
                   'working_text_confirmation':prior}
        fragment['data']['complete_text'] = False
        fragment_path.write_text(json.dumps(fragment)+'\n')
        self.assertIsNone(W.matching_confirmation(self.record, self.repo))
        with self.assertRaisesRegex(ValueError, 'changed or invalid'):
            W.require_current_confirmation(dossier, self.repo)
        fragment['data'].pop('complete_text')
        fragment['data']['url'] = 'https://example.gov/new-citation'
        fragment_path.write_text(json.dumps(fragment)+'\n')
        # A still-valid confirmation with changed source metadata needs a new dossier.
        self.assertIsNotNone(W.matching_confirmation(self.record, self.repo))
        with self.assertRaisesRegex(ValueError, 'changed or invalid'):
            W.require_current_confirmation(dossier, self.repo)

    def test_only_matching_source_inherits_and_policy_rechecks_without_dossier(self):
        prior = W.matching_confirmation(self.record, self.repo)
        other = dict(self.record, instrument_id='EO:8')
        disclosure = W.blank([self.record, other], prior)
        self.assertTrue(disclosure['confirmations'][0]['identity_confirmed'])
        self.assertFalse(disclosure['confirmations'][1]['identity_confirmed'])
        self.assertNotIn('prior_confirmation', disclosure['confirmations'][1])
        text = (self.repo/self.text_path).read_text()
        ref = dict(self.record, char_start=0, char_end=len(text), quote=text)
        claim = {'instrument_id':'EO:7', 'original_representation':ref,
                 'working_text':W.blank([ref], prior)}
        self.assertEqual(W.policy(claim, self.repo)[0], [])
        changed = deepcopy(claim)
        changed['working_text']['confirmations'][0]['pages_confirmed'] = False
        self.assertIn('working_text:prior_confirmation_changed', W.policy(changed,self.repo)[0])
        self.machine.write_text(json.dumps(dict(self.record, evidence={'revision':2}))+'\n')
        self.assertIn('working_text:prior_confirmation_stale', W.policy(claim,self.repo)[0])

    def test_negative_or_invalid_agent_overrides_and_last_record_semantics(self):
        agent = self.repo/W.CONFIRMATION_PATHS[1]
        for change in [dict(confirmed=False), dict(schema='unknown'), dict(method='unknown')]:
            agent.write_text(json.dumps(dict(self.record, **change))+'\n')
            self.assertIsNone(W.matching_confirmation(self.record, self.repo))
        agent.write_text(json.dumps(dict(self.record, confirmed=False))+'\n'+
                         json.dumps(dict(self.record, method='agent'))+'\n')
        self.assertEqual(W.matching_confirmation(self.record,self.repo)['record']['method'],'agent')

    def test_no_pages_needed_only_when_both_record_and_fragments_agree(self):
        self.record.update(requires_page_check=False,pages_confirmed=False)
        self.machine.write_text(json.dumps(self.record)+'\n')
        self.assertIsNone(W.matching_confirmation(self.record,self.repo))
        path=self.repo/'jobs/source/output/FRAGMENTS.jsonl'
        fragment=json.loads(path.read_text());fragment['data']['requires_page_check']=False
        path.write_text(json.dumps(fragment)+'\n')
        self.assertIsNotNone(W.matching_confirmation(self.record,self.repo))
        (self.repo/self.text_path).unlink()
        self.assertIsNone(W.matching_confirmation(self.record,self.repo))


if __name__ == '__main__':
    unittest.main()
