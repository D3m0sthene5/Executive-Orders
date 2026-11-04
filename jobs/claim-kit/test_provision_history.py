"""Synthetic research histories: exact reviews never imply canonical certification."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import provision_history as H


class ProvisionHistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.bundle_path = self.repo / 'research/history.json'
        self.review_path = self.repo / 'research/review/REVIEW.json'
        self.review_path.parent.mkdir(parents=True)
        self.bundle = {'schema': H.SCHEMA, 'producer': 'producer', 'provisions': [], 'transitions': []}
        self.review_scopes = {}
        self.add_provision('P17-EO_1-duty', 'The board shall use red ink.', '2020-01-01')

    def source(self, rid, quote):
        path = 'research/texts/' + rid.replace(':', '_') + '.txt'
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        # Keep exact LF witness text so character offsets are stable on every platform.
        target.write_bytes(('HEADER\n' + quote + '\nFOOTER').encode('utf-8'))
        return {'text_path': path, 'text_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                'char_start': 7, 'char_end': 7 + len(quote), 'quote': quote}

    def add_provision(self, pid, text, start, scopes=('text', 'legal_effect'), **fields):
        p = {'provision_id': pid, 'instrument_id': 'EO:1', 'scope': 'section 1', 'norm_text': text,
             'valid_start': start, 'known_sunset_end_exclusive': None, 'source_id': 'S:' + pid,
             'source': self.source(pid, text), 'date_basis': 'explicit effective clause', **fields}
        self.bundle['provisions'].append(p)
        self.review_scopes[pid] = scopes
        return p

    def add(self, tid, kind, date, scopes=('text', 'legal_effect'), **fields):
        quote = fields.pop('quote', 'The source expressly orders ' + kind + '. Blue ink. Green ink.')
        t = {'transition_id': tid, 'affected_provision_id': self.bundle['provisions'][0]['provision_id'],
             'actor_id': 'EO:2', 'event_date': date, 'effective_date': date, 'kind': kind,
             'source_id': 'S:' + tid, 'date_basis': 'explicit effective clause',
             'source': self.source(tid, quote), **fields}
        self.bundle['transitions'].append(t)
        self.review_scopes[tid] = scopes
        return t

    @property
    def pid(self):
        return self.bundle['provisions'][0]['provision_id']

    def write(self):
        reviews = []
        for r in self.bundle['provisions'] + self.bundle['transitions']:
            rid = r.get('provision_id', r.get('transition_id'))
            for scope in self.review_scopes[rid]:
                reviews.append({'record_id': rid, 'record_sha256': H.canonical_sha(r), 'scope': scope,
                                'review_scope': r.get('affected_provision_id', rid), 'verdict': 'upheld',
                                'reviewer': 'independent-reviewer', 'independent': True})
        self.review_path.write_text(json.dumps({'schema': H.REVIEW_SCHEMA, 'reviews': reviews}), encoding='utf-8')
        self.bundle['review_file'] = {'path': self.review_path.relative_to(self.repo).as_posix(),
                                     'sha256': hashlib.sha256(self.review_path.read_bytes()).hexdigest()}
        self.bundle_path.write_text(json.dumps(self.bundle), encoding='utf-8')

    def query(self, on='2025-01-01', pid=None):
        self.write()
        return H.dated_query(self.repo, self.bundle_path, on, pid or self.pid)['queries'][0]

    def amend(self, tid='T-amend', date='2021-01-01', **fields):
        return self.add(tid, 'amend', date, from_version_id=self.pid + '::v0', old_rule='red',
                        new_rule='blue', expected_new_text='The board shall use blue ink.', **fields)

    def test_amendments_and_reinstatement_restore_exact_version_with_gap(self):
        self.amend()
        self.add('T-revoke', 'revoke', '2022-01-01')
        self.add('T-reinstate', 'reinstate', '2024-01-01', restore_version_id='T-amend')
        self.assertEqual(self.query('2020-06-01')['text_version']['text'], 'The board shall use red ink.')
        self.assertEqual(self.query('2021-06-01')['text_version']['text'], 'The board shall use blue ink.')
        gap = self.query('2023-01-01')
        self.assertEqual(gap['operative_state'], 'revoked')
        self.assertIsNone(gap['operative_episode'])
        revived = self.query()
        self.assertEqual(revived['operative_episode']['start'], '2024-01-01')
        self.assertEqual(revived['text_version']['version_id'], 'T-amend')
        self.assertEqual(revived['prior_episodes'][0]['end_exclusive'], '2022-01-01')
        self.assertIn('record:T-amend', revived['dependencies'])
        self.assertFalse(revived['human_certified'])
        self.assertFalse(revived['completeness_guaranteed'])

    def test_crlf_witness_requires_exact_unnormalized_span(self):
        record = self.bundle['provisions'][0]
        source = record['source']
        target = self.repo / source['text_path']
        raw = ('HEADER\r\n' + record['norm_text'] + '\r\nFOOTER').encode('utf-8')
        target.write_bytes(raw)
        source['text_sha256'] = hashlib.sha256(raw).hexdigest()
        with self.assertRaisesRegex(ValueError, 'source_span_mismatch'):
            self.query()
        source['char_start'] = 8
        source['char_end'] = 8 + len(record['norm_text'])
        self.assertEqual(self.query()['text_version']['text'], record['norm_text'])

    def test_reinstatement_never_renews_expired_clock(self):
        self.bundle['provisions'][0]['known_sunset_end_exclusive'] = '2020-07-01'
        self.add('T-revoke', 'revoke', '2021-01-01')
        self.add('T-restore', 'reinstate', '2024-01-01', restore_version_id=self.pid + '::v0')
        q = self.query()
        self.assertEqual(q['operative_state'], 'expired')
        self.assertIsNone(q['operative_episode'])
        self.assertEqual(q['known_sunset_end_exclusive'], '2020-07-01')

    def test_amendment_after_expiry_does_not_reestablish(self):
        self.bundle['provisions'][0]['known_sunset_end_exclusive'] = '2020-07-01'
        self.amend(known_sunset_end_exclusive='2030-01-01')
        self.assertEqual(self.query()['operative_state'], 'expired')

    def test_renumber_transfer_preserve_identity_and_text(self):
        self.add('T-renumber', 'renumber', '2021-01-01', new_label='section 5')
        self.add('T-transfer', 'transfer', '2022-01-01', transfer_to='Secretary of State')
        q = self.query()
        self.assertEqual(q['provision_id'], self.pid)
        self.assertEqual(q['label'], 'section 5')
        self.assertEqual(q['executor'], 'Secretary of State')
        self.assertEqual(q['text_version']['version_id'], self.pid + '::v0')

    def test_text_review_never_supplies_legal_effect_or_effective_date(self):
        self.add('T-revoke', 'revoke', '2022-01-01', scopes=('text',), effective_date=None,
                 date_basis='signing_date', unresolved_questions=['Scope of saved rights unknown.'])
        q = self.query()
        self.assertEqual(q['operative_state'], 'unknown')
        self.assertIn('Scope of saved rights unknown.', q['unresolved_questions'])
        self.assertIsNone(q['operative_episode'])
        self.assertFalse(q['transition_details'][0]['retroactive_effect'])

    def test_legal_effect_review_alone_does_not_approve_text(self):
        self.add('T-revoke', 'revoke', '2022-01-01', scopes=('legal_effect',))
        self.assertEqual(self.query()['operative_state'], 'unknown')

    def test_missing_initial_coverage_and_scope_are_local(self):
        p = self.bundle['provisions'][0]
        p['valid_start'] = None
        p['remaining_gap'] = 'Only section 1 has been examined.'
        self.review_scopes[self.pid] = ('text',)
        self.add_provision('P-other', 'Another command.', '2020-01-01')
        q = self.query()
        self.assertEqual(q['operative_state'], 'unknown')
        self.assertIn('Only section 1 has been examined.', q['unresolved_questions'])
        self.assertEqual(self.query(pid='P-other')['operative_state'], 'operative')

    def test_conflicting_same_day_refused_but_reviewed_sequence_allowed(self):
        self.add('T-revoke', 'revoke', '2022-01-01')
        self.add('T-restore', 'reinstate', '2022-01-01', restore_version_id=self.pid + '::v0')
        with self.assertRaisesRegex(ValueError, 'conflicting_same_time'):
            self.query()
        self.bundle['transitions'][0]['sequence'] = 1
        self.bundle['transitions'][1]['sequence'] = 2
        self.assertEqual(self.query()['operative_episode']['start'], '2022-01-01')

    def test_retroactive_supersession_discloses_later_signature(self):
        self.add('T-super', 'supersede', '1961-11-03', effective_date='1961-09-30',
                 signing_date='1961-11-03', publication_date='1961-11-07')
        self.bundle['provisions'][0]['valid_start'] = '1960-01-01'
        q = self.query('1961-10-01')
        self.assertEqual(q['operative_state'], 'superseded')
        self.assertTrue(q['transition_details'][0]['retroactive_effect'])
        self.assertTrue(any('knowable' in x for x in q['unresolved_questions']))

    def test_source_span_and_source_byte_tampering_refused(self):
        self.write()
        p = self.bundle['provisions'][0]
        (self.repo / p['source']['text_path']).write_text('tampered', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'stale_source'):
            H.dated_query(self.repo, self.bundle_path, '2025-01-01')
        self.bundle['provisions'][0]['source'] = self.source(self.pid, p['norm_text'])
        self.bundle['provisions'][0]['source']['char_start'] += 1
        with self.assertRaisesRegex(ValueError, 'source_span_mismatch'):
            self.query()

    def test_changed_review_file_or_record_refused(self):
        self.write()
        self.review_path.write_text(self.review_path.read_text() + '\n')
        with self.assertRaisesRegex(ValueError, 'changed_review_file'):
            H.load(self.repo, self.bundle_path)
        self.write()
        data = json.loads(self.bundle_path.read_text())
        data['provisions'][0]['scope'] = 'different scope'
        self.bundle_path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'stale_or_wrong_scope_review'):
            H.load(self.repo, self.bundle_path)

    def test_duplicate_unknown_operation_and_nonprior_version_refused(self):
        self.amend()
        self.bundle['transitions'].append(deepcopy(self.bundle['transitions'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate_record'):
            self.query()
        self.bundle['transitions'].pop()
        self.bundle['transitions'][0]['kind'] = 'guess_effect'
        with self.assertRaisesRegex(ValueError, 'unknown_operation'):
            self.query()
        self.bundle['transitions'][0]['kind'] = 'amend'
        self.bundle['transitions'][0]['from_version_id'] = 'T-amend'
        with self.assertRaisesRegex(ValueError, 'cyclic_or_nonprior'):
            self.query()

    def test_ambiguous_substitution_and_wrong_expected_text_refused(self):
        self.bundle['provisions'][0]['norm_text'] = 'red red'
        self.bundle['provisions'][0]['source'] = self.source(self.pid, 'red red')
        t = self.amend()
        with self.assertRaisesRegex(ValueError, 'ambiguous_or_missing_old_rule'):
            self.query()
        self.bundle['provisions'][0]['norm_text'] = 'red'
        self.bundle['provisions'][0]['source'] = self.source(self.pid, 'red')
        with self.assertRaisesRegex(ValueError, 'expected_new_text_mismatch'):
            self.query()

    def test_revalidation_is_exact_and_restored_version_keeps_ancestry(self):
        self.amend()
        self.add('T-revoke', 'revoke', '2022-01-01')
        self.add('T-restore', 'reinstate', '2024-01-01', restore_version_id='T-amend')
        self.add_provision('P-unrelated', 'A separate command.', '2020-01-01')
        self.write()
        results = H.dated_query(self.repo, self.bundle_path, '2025-01-01')
        changed = {'record:T-amend': 'changed', 'source:unexamined': None}
        report = H.revalidation_report(results, changed)
        self.assertEqual(report['affected_provisions'], ['provision:' + self.pid])
        self.assertEqual(report['affected_queries'], ['query:' + self.pid + '@2025-01-01'])
        self.assertEqual(report['unexamined_changes'], ['source:unexamined'])
        unchanged = {'record:T-amend': H.canonical_sha(self.bundle['transitions'][0])}
        self.assertEqual(H.revalidation_report(results, unchanged)['affected_queries'], [])


    def test_unreviewed_expiry_cannot_determine_reinstatement_effect(self):
        self.bundle['provisions'][0]['known_sunset_end_exclusive'] = '2020-07-01'
        self.review_scopes[self.pid] = ('text',)
        self.add('T-restore', 'reinstate', '2024-01-01', restore_version_id=self.pid + '::v0')
        q = self.query()
        self.assertEqual(q['operative_state'], 'unknown')
        self.assertFalse(q['expiry_reviewed'])
        self.assertTrue(any('clock' in x for x in q['unresolved_questions']))

    def test_legal_effect_review_requires_explicit_timing(self):
        self.add('T-revoke', 'revoke', '2022-01-01', effective_date=None)
        self.assertEqual(self.query()['operative_state'], 'unknown')

    def test_auxiliary_source_and_raw_byte_pins_are_checked(self):
        t = self.add('T-revoke', 'revoke', '2022-01-01')
        t['effective_date_source'] = self.source('date-clause', 'Effective January 1, 2022.')
        self.write()
        (self.repo / t['effective_date_source']['text_path']).write_text('wrong')
        with self.assertRaisesRegex(ValueError, 'stale_source'):
            H.load(self.repo, self.bundle_path)
        t.pop('effective_date_source')
        raw = self.repo / 'research/held.pdf'
        raw.write_bytes(b'held raw source, no authentication inferred')
        t['source'].update(raw_path='research/held.pdf', raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest())
        self.write()
        raw.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'stale_raw_source'):
            H.load(self.repo, self.bundle_path)

    def test_missing_text_review_marks_textual_coverage_incomplete(self):
        self.add('T-unreviewed', 'revoke', '2022-01-01', scopes=())
        q = self.query()
        self.assertFalse(q['textual_coverage_complete'])
        self.assertEqual(q['operative_state'], 'unknown')


    def test_reviewed_transition_before_establishment_refused(self):
        self.bundle['provisions'][0]['valid_start'] = '2022-01-01'
        self.add('T-early', 'revoke', '2021-01-01')
        with self.assertRaisesRegex(ValueError, 'transition_precedes_reviewed_establishment'):
            self.query()

    def test_new_unreviewed_transition_changes_only_its_provision_membership(self):
        self.add_provision('P-unrelated', 'An independent command.', '2020-01-01')
        self.write()
        old = H.dated_query(self.repo, self.bundle_path, '2025-01-01')
        ledger_bytes = self.review_path.read_bytes()
        self.add('T-new', 'revoke', '2022-01-01', scopes=())
        self.write()
        self.assertEqual(self.review_path.read_bytes(), ledger_bytes)
        new_pins = H.membership_fingerprints(self.repo, self.bundle_path)
        report = H.revalidation_report(old, new_pins)
        self.assertEqual(report['affected_provisions'], ['provision:' + self.pid])
        self.assertEqual(report['affected_queries'], ['query:' + self.pid + '@2025-01-01'])
        self.assertEqual(H.query(self.repo, self.bundle_path, self.pid, '2025-01-01')['operative_state'], 'unknown')


    def test_initial_pre_document_text_is_held_evidence_not_dated_text(self):
        p = self.bundle['provisions'][0]
        p['signing_date'] = '2020-01-01'
        q = self.query('1900-01-01')
        self.assertEqual(q['initial_text_date_state'], 'not_yet_documented')
        self.assertIsNone(q['text_version'])
        self.assertEqual(q['held_text_version']['version_id'], self.pid + '::v0')
        self.assertEqual(q['operative_state'], 'not_yet_established')

    def test_unknown_document_date_does_not_date_text_by_normative_start(self):
        p = self.bundle['provisions'][0]
        p['valid_start'] = None
        self.review_scopes[self.pid] = ('text',)
        q = self.query('1900-01-01')
        self.assertEqual(q['initial_text_date_state'], 'unknown')
        self.assertIsNone(q['text_version'])
        self.assertIsNotNone(q['held_text_version'])
        p['valid_start'] = '2020-01-01'
        self.assertIsNone(self.query('1900-01-01')['text_version'])

    def test_initial_retrospective_effect_is_not_public_availability(self):
        p = self.bundle['provisions'][0]
        p['valid_start'] = '2020-01-01'
        p['signing_date'] = '2020-02-01'
        q = self.query('2020-01-15')
        self.assertEqual(q['initial_text_date_state'], 'reviewed_retrospective_reconstruction')
        self.assertIsNotNone(q['text_version'])
        self.assertEqual(q['operative_state'], 'operative')
        p['publication_date'] = 'not-a-date'
        with self.assertRaisesRegex(ValueError, 'invalid_date'):
            self.query()

    def test_inverted_reviewed_initial_sunset_refused(self):
        self.bundle['provisions'][0]['known_sunset_end_exclusive'] = '2019-12-01'
        self.add('T-revoke', 'revoke', '2021-01-01')
        with self.assertRaisesRegex(ValueError, 'sunset_precedes_reviewed_establishment'):
            self.query()

    def test_expired_revival_followed_by_later_event_never_creates_episode(self):
        self.bundle['provisions'][0]['known_sunset_end_exclusive'] = '2020-06-01'
        self.add('T-revoke', 'revoke', '2021-01-01')
        self.add('T-restore', 'reinstate', '2024-01-01', restore_version_id=self.pid + '::v0')
        self.add('T-renumber', 'renumber', '2024-06-01', new_label='section 5')
        q = self.query()
        self.assertEqual(q['operative_state'], 'expired')
        self.assertIsNone(q['operative_episode'])
        self.assertTrue(all(e['start'] < e['end_exclusive'] for e in q['prior_episodes']))
        self.assertEqual(len(q['prior_episodes']), 1)

    def test_cutoff_blocks_future_state_extrapolation(self):
        self.bundle['legal_cutoff'] = '2024-12-31'
        self.bundle['coverage_notice'] = 'Selected scopes only.'
        q = self.query()
        self.assertEqual(q['operative_state'], 'unknown')
        self.assertIsNone(q['operative_episode'])
        self.assertTrue(q['outside_legal_cutoff'])
        self.assertEqual(q['coverage_notice'], 'Selected scopes only.')
        self.assertIn('supplied reviewed transitions', q['operative_state_scope'])



    def test_typed_text_date_is_validated_and_event_date_is_not_documentary(self):
        p = self.bundle['provisions'][0]
        self.review_scopes[self.pid] = ('text',)
        p['valid_start'] = None
        p['event_date'] = '1900-01-01'
        self.assertIsNone(self.query('2021-01-01')['text_version'])
        p['text_date'] = '2020-01-01'
        self.assertIsNotNone(self.query('2021-01-01')['text_version'])
        p['text_date'] = 'bad-date'
        with self.assertRaisesRegex(ValueError, 'invalid_date'):
            self.query()

    def test_changed_cutoff_with_identical_review_ledger_invalidates_queries(self):
        self.write()
        old = H.dated_query(self.repo, self.bundle_path, '2025-01-01')
        old_ledger = self.review_path.read_bytes()
        self.bundle['legal_cutoff'] = '2024-12-31'
        self.write()
        self.assertEqual(old_ledger, self.review_path.read_bytes())
        current = H.membership_fingerprints(self.repo, self.bundle_path)
        report = H.revalidation_report(old, current)
        self.assertEqual(report['affected_queries'], ['query:' + self.pid + '@2025-01-01'])
        self.assertEqual(H.query(self.repo, self.bundle_path, self.pid, '2025-01-01')['operative_state'], 'unknown')

    def test_independent_review_and_scopes_cannot_be_forged(self):
        self.write()
        ledger = json.loads(self.review_path.read_text())
        ledger['reviews'][0]['reviewer'] = 'producer'
        self.review_path.write_text(json.dumps(ledger))
        self.bundle['review_file']['sha256'] = hashlib.sha256(self.review_path.read_bytes()).hexdigest()
        self.bundle_path.write_text(json.dumps(self.bundle))
        with self.assertRaisesRegex(ValueError, 'independent_upheld_review_required'):
            H.load(self.repo, self.bundle_path)


if __name__ == '__main__':
    unittest.main()
