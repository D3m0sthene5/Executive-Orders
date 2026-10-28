import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from fetch_ladder import html_to_text
from record_series import propose


class SeriesIdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def put(self, name, text):
        p = self.root/name
        p.write_text(text)
        return {'path':name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

    def plan(self, duplicate=False):
        narrative = ('Case A-1, Emergency Board No. 67. Northwest Airlines and Machinists\n'
                     'Executive order of the President dated January 19, 1949, resulted in appointment.\n'
                     'The report was dated March 10, 1949.\n')
        raw = '<html><body><pre>National Mediation Board\nFor the Fiscal Year Ended June 30, 1949\n'+narrative
        raw += (narrative if duplicate else '')+'Case A-2, Emergency Board No. 68. Other Carrier\nNo case body</pre></body></html>'
        rawref = self.put('annual.html',raw)
        textref = self.put('annual.txt',html_to_text(raw))
        index = self.put('index.html','<table><tr><td>67</td><td>Northwest Airlines</td><td>A10</td><td>IAM</td><td>Machinists</td><td>1/24/1949</td><td>3/10/1949</td><td><a href="https://nmb.gov/PEB-067.pdf">report</a></td></tr></table>')
        original = self.put('original.txt','EXECUTIVE ORDER 10029\nNorthwest Airlines and Ma-\nchinists. M arch 19, 1949. January 19, 1949.')
        return {'schema':'nmb-series-plan/v1','requested_by':'test','index':index,
            'sources':[{'raw':rawref,'text':textref,'fiscal_year':1949}],
            'questions':[{'instrument_id':'EO:10029','order_date':'1949-01-19',
                'identity_source':original,'identity_span':[0,len((self.root/'original.txt').read_text())],
                'identity_terms':['northwest','machinists']}]}

    def test_later_appointment_is_not_assumed_to_be_eo_date(self):
        result = propose(self.root,self.plan())
        self.assertEqual(len(result['proposals']),1)
        self.assertEqual(result['proposals'][0]['index_date'],'1/24/1949')
        self.assertEqual(result['proposals'][0]['order_date'],'1949-01-19')
        self.assertEqual(result['factual_answers'],0)
        self.assertFalse(result['legal_findings'])

    def test_same_date_different_entity_does_not_join(self):
        p = self.plan()
        p['questions'][0]['identity_terms']=['other','carrier']
        with self.assertRaisesRegex(ValueError,'grounded'):
            propose(self.root,p)

    def test_ambiguous_narrative_is_not_selected(self):
        r = propose(self.root,self.plan(duplicate=True))
        self.assertFalse(r['proposals'])
        self.assertEqual(r['unresolved'][0]['matching_cases'],2)

    def test_report_date_cannot_replace_eo_reference(self):
        p = self.plan()
        p['questions'][0]['order_date']='1949-03-10'
        with self.assertRaisesRegex(ValueError,'original span'):
            propose(self.root,p)

    def test_changed_raw_source_and_edition_are_refused(self):
        p = self.plan()
        (self.root/'annual.html').write_text('different')
        with self.assertRaisesRegex(ValueError,'changed'):
            propose(self.root,p)
        p = self.plan()
        p['sources'][0]['fiscal_year']=1950
        with self.assertRaisesRegex(ValueError,'edition'):
            propose(self.root,p)

    def test_changed_extract_is_refused_even_with_new_text_hash(self):
        p = self.plan()
        p['sources'][0]['text']=self.put('annual.txt','invented matching narrative')
        with self.assertRaisesRegex(ValueError,'unchanged ladder extraction'):
            propose(self.root,p)

    def test_path_escape_and_missing_identity_date_are_refused(self):
        p = self.plan()
        p['index']['path']='../index.html'
        with self.assertRaisesRegex(ValueError,'unsafe'):
            propose(self.root,p)
        p = self.plan()
        p['questions'][0]['order_date']='1949-01-24'
        with self.assertRaisesRegex(ValueError,'original span'):
            propose(self.root,p)

    def test_alias_substring_cannot_match_a_different_word(self):
        p = self.plan()
        p['questions'][0]['identity_terms']=['north','machinists']
        with self.assertRaisesRegex(ValueError,'grounded'):
            propose(self.root,p)

    def test_instrument_number_cannot_be_rebound_to_other_original(self):
        p = self.plan()
        p['questions'][0]['instrument_id']='EO:99999'
        with self.assertRaisesRegex(ValueError,'exact instrument identity'):
            propose(self.root,p)


if __name__ == '__main__':
    unittest.main()
