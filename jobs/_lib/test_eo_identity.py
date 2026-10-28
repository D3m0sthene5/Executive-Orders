"""Shared discovery readers preserve held CSC texts as transcription leads."""
import json
from pathlib import Path
import tempfile
import unittest

import eo_identity


class CscReaderTest(unittest.TestCase):
    def test_csc_text_is_loaded_without_promoting_custody(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / 'jobs/csc-annual-reports/output'
            (output / 'texts').mkdir(parents=True)
            (output / 'texts/EO_196.txt').write_text('Historical report transcription.')
            (output / 'FRAGMENTS.jsonl').write_text(json.dumps({
                'instrument_id': 'EO:196', 'kind': 'original_representation',
                'produced_by': 'csc-annual-reports', 'grade': 'compiled_transcription_lead',
                'acceptable_as_original': False,
                'data': {'text_path': 'texts/EO_196.txt', 'needs_page_check': True,
                         'page_or_item': '1903 CSR 74', 'url': 'https://www.govinfo.gov/example.pdf'},
            }) + '\n')
            fragment, = eo_identity.load_fragments(str(root))['EO:196']
            self.assertEqual(fragment['class'], 'transcription')
            self.assertEqual(fragment['produced_by'], 'csc-annual-reports')
            self.assertFalse(fragment['acceptable_as_original'])
            self.assertTrue(fragment['needs_page_check'])
            self.assertEqual(Path(fragment['text_path']).read_text(), 'Historical report transcription.')


class DateTest(unittest.TestCase):
    def test_wpa_numbered_list_refines_a_bare_year_only_when_years_agree(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            wpa = root / eo_identity.WPA_NUMBERED
            wpa.parent.mkdir(parents=True)
            wpa.write_text('id,number,suffix,year,month_day,text\n'
                           'EO:1547,1547,,1912,June 19,Eight-hour day suspended.\n'
                           'EO:2000,2000,,1915,Jan 4,Disagreeing year.\n')
            pq = root / 'jobs/pinakes-proquest-ingest/output'
            pq.mkdir(parents=True)
            (pq / 'FRAGMENTS.jsonl').write_text(''.join(json.dumps({
                'instrument_id': i, 'kind': 'original_representation', 'produced_by': 'pinakes-proquest-ingest',
                'grade': 'archival_replica_scan_pending_codebook', 'acceptable_as_original': False,
                'data': {'signing_date': y, 'needs_page_check': True}}) + '\n' for i, y in (('EO:1547', '1912'), ('EO:2000', '1914'))))
            dates = eo_identity.load_dates(str(root))
            self.assertEqual(dates['EO:1547']['date'], '1912-06-19')
            self.assertEqual(dates['EO:1547']['date_source'], 'wpa_numbered_list')
            self.assertEqual(dates['EO:2000']['date'][:4], '1914')  # a disagreeing year is not overwritten


if __name__ == '__main__':
    unittest.main()
