"""Old Federal Register document boundaries and exact opening-command retention."""
import unittest
from pathlib import Path
import excavate

class LegacyExtentTests(unittest.TestCase):
    def test_native_dossier_retains_legacy_warning(self):
        from build import package
        text = ('EXECUTIVE ORDER\nBy virtue of authority I hereby reserve target lands.\n'
                'FRANKLIN D ROOSEVELT\nTHE WHITE HOUSE\nMay 10, 1939.\n[No. 8123]\n[F. R. Doc. target]\n')
        record=excavate.segment('EO:8123',text,{})
        dossier=package('EO:8123',{'drafts':{},'statuses':{},'machine_searches':{}},
                        {'EO:8123':{'source':{},'text':text}},record,[],[],None,[])
        self.assertIn(record['notes'],dossier['missing'])
        self.assertTrue(any('completeness remain unverified' in note for note in dossier['missing']))

    def test_neighbor_signature_cannot_end_target_and_terms_stay_in_target(self):
        text = ('EXECUTIVE ORDER\nBy virtue of authority, I hereby establish a previous board.\n'
                'It shall report within thirty days.\nFRANKLIN D ROOSEVELT\nTHE WHITE HOUSE\n'
                'May 10, 1939.\n[No. 8119]\n[F. R. Doc. previous]\n'
                'EXECUTIVE ORDER\nBy virtue of authority, I hereby reserve the target lands.\n'
                'It is unlawful to hunt on the target lands.\nFRANKLIN D ROOSEVELT\nTHE WHITE HOUSE\n'
                'May 10, 1939.\n[No. 8123]\n[F. R. Doc. target]\n')
        result = excavate.segment('EO:8123', text, {})
        combined = ' '.join(c['text'] for c in result['clauses'])
        self.assertIn('target lands', combined)
        self.assertNotIn('previous board', combined)
        self.assertFalse(excavate.own_terms('EO:8123', text, {}, result['clauses']))
        for c in result['clauses']:
            self.assertEqual(text[c['char_start']:c['char_end']], c['text'])

    def test_internal_subdivision_reference_cannot_discard_opening_entitlement(self):
        text = ('EXECUTIVE ORDER\nBy virtue of authority it is hereby ordered as follows:\n'
                'The retirement provisions are extended to all Federal employees appointed under subdivision\n'
                '(d) of section 3 and to employees with classified status.\n'
                'Subdivision (d) is amended to permit appointments.\nFRANKLIN D ROOSEVELT\n'
                'THE WHITE HOUSE\nApril 10, 1939.\n[No. 8083]\n[F. R. Doc. target]\n')
        clauses = excavate.segment('EO:8083', text, {})['clauses']
        self.assertIn('retirement provisions are extended', ' '.join(c['text'] for c in clauses))
        self.assertLess(clauses[0]['char_start'],text.index('The retirement provisions'))

    def test_numbered_intervening_document_refuses_trailing_binding(self):
        for heading in ('EXECUTIVE ORDER 9000','EXECUTIVE ORDER No. 9000',
                        'E X E C U T I V E  O R D E R 9000','EXECUTIVE ORDER\n9000'):
            text = ('EXECUTIVE ORDER\nFirst document.\n'+heading+'\n'
                    'By virtue of authority I hereby establish a body.\nTHE WHITE HOUSE\n'
                    'May 10, 1939.\n[No. 8123]\n[F. R. Doc. target]\n')
            self.assertIsNone(excavate._trailing_extent('EO:8123', text),heading)

    def test_four_real_source_boundary_regressions(self):
        folder = Path(__file__).resolve().parents[2] / 'jobs/fr-originals/data/full_run/texts'
        if not all((folder / ('EO_'+n+'.txt')).is_file() for n in ('8083','8123','8126','8992')):
            self.skipTest('Actual frozen FR text files not hydrated')
        required = {'8083': ('retirement', 'superseded'), '8123': ('320.00','Lake Moraine'),
                    '8126': ('480.00','Little lake'), '8992': ('320 acres','6964')}
        rejected = {'8123':'Florence Lake', '8126':'Lake Oliver', '8992':'weather reports'}
        for n, words in required.items():
            text = (folder/('EO_'+n+'.txt')).read_bytes().decode('utf-8')
            result = excavate.segment('EO:'+n, text, {})
            combined = ' '.join(c['text'] for c in result['clauses'])
            flat = ' '.join(combined.lower().replace('\u00ad','').split())
            for word in words: self.assertIn(word.lower(),flat)
            if n in rejected:self.assertNotIn(rejected[n].lower(),flat)
            for c in result['clauses']:self.assertEqual(text[c['char_start']:c['char_end']],c['text'])
            self.assertIn('completeness remain unverified',result['notes'])

if __name__ == '__main__':unittest.main()
