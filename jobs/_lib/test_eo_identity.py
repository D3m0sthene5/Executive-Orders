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


if __name__ == '__main__':
    unittest.main()
