"""Preparation failures must be visible before legal production is assigned."""
from copy import deepcopy
import hashlib
from pathlib import Path
import tempfile
import unittest

import evidence_preflight as preflight
from excavate import segment


class EvidencePreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.d = {'instrument_id': 'EO:2', 'original_source_id': 'ORIGINAL:EO:2',
                  'evidence': {}, 'clauses': [], 'actor_provisions': []}

    def source(self, name, text, raw_sha='a' * 64):
        (self.repo / name).write_text(text, encoding='utf-8')
        return {'text_path': name, 'text_sha256': hashlib.sha256(text.encode()).hexdigest(),
                'sha256': raw_sha, 'url': 'https://example.gov/' + name}

    def original(self, text):
        source = self.source('original.txt', text)
        item = {'text': text, 'char_start': 0, 'char_end': len(text), 'source': source, 'actor_id': 'EO:2'}
        self.d['evidence']['ORIGINAL:EO:2'] = item
        self.d['clauses'] = [dict(item, scope_id='EO:2#whole')]
        return item

    def kinds(self):
        return {t['kind'] for t in preflight.inspect(self.d, self.repo)['tasks']}

    def test_valid_single_order_is_unaffected_and_no_authentication_is_claimed(self):
        self.original('Instrument: EO:2\nExecutive Order 2 of January 1, 2000\nSection 1. There is established a board.\n')
        result = preflight.inspect(self.d, self.repo)
        self.assertEqual(result['tasks'], [])
        self.assertEqual(result['custody_validation'], 'required_from_actual_claim_checker')

    def test_missing_bytes_and_wrong_hash_are_distinct_failures(self):
        original = self.original('I establish a board.')
        (self.repo / 'original.txt').unlink()
        self.assertIn('held_text_unavailable', self.kinds())
        (self.repo / 'original.txt').write_text('Changed bytes.')
        self.assertIn('held_text_fixity', self.kinds())
        original['source'].pop('text_sha256')
        self.assertIn('held_text_fixity', self.kinds())

    def test_custody_only_pointer_and_mismatched_quote_do_not_look_ready(self):
        original = self.original('I establish a board.')
        original['text'] = 'A different quote.'
        self.assertIn('citable_span', self.kinds())
        original['source'].pop('text_path')
        self.assertIn('citable_text_pointer', self.kinds())

    def test_unsafe_source_is_not_read(self):
        original = self.original('I establish a board.')
        original['source']['text_path'] = '../outside.txt'
        self.assertIn('held_text_unavailable', self.kinds())

    def test_explicit_wrong_order_is_flagged(self):
        self.original('Instrument: EO:1\nExecutive Order 1\nSection 1. Establish a board.')
        self.assertIn('original_identity', self.kinds())

    def test_neighboring_old_order_inventory_requires_boundary_review(self):
        self.original('Instrument: EO:2\nEXECUTIVE ORDER\n1. Council established.\n[No. 1]\nEXECUTIVE ORDER\nSection 1. Land withdrawn.\n[No. 2]')
        self.assertIn('original_boundary', self.kinds())
        self.original('Instrument: EO:2\nEXECUTIVE ORDER\nSection 1. Land withdrawn.\n[No. 2]')
        self.assertNotIn('original_boundary', self.kinds())

    def test_numbered_neighbor_sections_do_not_create_false_inventory_gaps(self):
        text = ('Instrument: EO:2\nExecutive Order 2 of January 1, 2000\nSection 1. Board.\n'
                'THE WHITE HOUSE\nExecutive Order 3 of January 1, 2000\nSection 1. Other board.\nSec. 2. Other duty.')
        self.original(text)
        self.d['clauses'][0]['char_end'] = text.index('THE WHITE HOUSE')
        self.assertNotIn('inventory_section_coverage', self.kinds())

    def test_uncovered_numbered_section_is_flagged(self):
        text = 'Section 1 . The board is established.\n(b) Its chairman is appointed.'
        self.original(text)
        self.d['clauses'][0]['char_start'] = text.index('(b)')
        self.assertIn('inventory_section_coverage', self.kinds())

    def test_spaced_section_number_keeps_operative_first_subsection(self):
        # EO12607's selected extraction prints "Section 1 .". The previous
        # heading rule started at (b), losing the establishment/member command.
        text = ('Executive Order 2 of January 1, 2000\n'
                'Section 1 . Establishment. (a) There is established a board.\n'
                '(b) The President shall designate a Chairman.\nSec. 2. The board shall report.\nTHE WHITE HOUSE')
        result = segment('EO:2', text, {})
        self.assertEqual(result['clauses'][0]['scope_id'], 'EO:2#sec1')
        self.assertIn('There is established a board.', result['clauses'][0]['text'])
        for clause in result['clauses']:
            self.assertEqual(text[clause['char_start']:clause['char_end']], clause['text'])
        clean = segment('EO:2', text.replace('1 .', '1.'), {})
        self.assertEqual([c['scope_id'] for c in clean['clauses']], [c['scope_id'] for c in result['clauses']])

    def test_same_source_alternate_exposes_truncation_without_selecting_it(self):
        self.original('Instrument: EO:2\nSection 1. Board.\nSec. 2. Duty.')
        text = 'Instrument: EO:2\nSection 1. Board.\nSec. 2. Duty.\nS ec. 3. Support.\nSec. 4. Sunset.'
        self.d['evidence']['TERM:EO:2'] = {'text': text, 'char_start': 0, 'char_end': len(text),
                                             'source': self.source('alternate.txt', text), 'actor_id': 'EO:2'}
        before = deepcopy(self.d)
        result = preflight.inspect(self.d, self.repo)
        task = next(t for t in result['tasks'] if t['kind'] == 'alternate_text_section_coverage')
        self.assertEqual(task['additional_sections'], ['3', '4'])
        self.assertEqual(self.d, before)
        # A different raw source is not evidence of omitted pages in this copy.
        self.d['evidence']['TERM:EO:2']['source']['sha256'] = 'b' * 64
        self.assertNotIn('alternate_text_section_coverage', self.kinds())

    def test_header_only_actor_quote_including_section_label_is_not_operating_text(self):
        self.original('I establish a board.')
        text = 'Executive Order 3\nAmending Executive Order 2\nSection 1. Executive Order 2 is revoked.'
        end = text.index('Section 1.') + len('Section 1.')
        self.d['evidence']['ACT:EO:2>EO:3'] = {'text': text[:end], 'char_start': 0,
            'char_end': end, 'source': self.source('actor.txt', text), 'actor_id': 'EO:3'}
        self.d['actor_provisions'] = ['ACT:EO:2>EO:3']
        self.assertIn('acting_provision_scope', self.kinds())
        self.d['evidence']['ACT:EO:2>EO:3'].update(text=text[text.index('Section 1.'):],
            char_start=text.index('Section 1.'), char_end=len(text))
        self.assertNotIn('acting_provision_scope', self.kinds())

    def test_report_relative_sunset_remains_a_substantive_event_question(self):
        self.original('The Commission shall terminate 30 days after submitting its final report to the President.')
        self.assertIn('conditional_report_sunset', self.kinds())
        self.original('The Commission shall report within thirty days.')
        self.assertNotIn('conditional_report_sunset', self.kinds())


if __name__ == '__main__':
    unittest.main()
