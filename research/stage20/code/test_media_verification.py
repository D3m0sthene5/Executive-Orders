"""Tests for original-image manifest verification without extracting PDF bytes."""
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from verify_opus_media import PREFIX, verify

class Companion(unittest.TestCase):
    def test_hash_alignment_and_reject_mismatch(self):
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder)
            main,companion=folder/'main.zip',folder/'media.zip'
            document=b'FAKE PDF FIXTURE, NOT A LEGAL SOURCE'
            rel='evidence/shards/S11_SAMPLE/original/page.pdf'
            manifest={'files':[{'path':rel,'bytes':len(document),'sha256':hashlib.sha256(document).hexdigest()},
                {'path':'STAGE11_ACCEPTED.jsonl','bytes':2,'sha256':'fixture'}]}
            records=[{'instrument_id':'EO:TEST' if i==0 else f'EO:OTHER{i}', 'evidence_dir':'evidence/shards/S11_SAMPLE/' if i==0 else ''} for i in range(1155)]
            with zipfile.ZipFile(main,'w') as z:
                z.writestr(PREFIX+'MANIFEST.json',json.dumps(manifest))
                z.writestr(PREFIX+'STAGE11_ACCEPTED.jsonl','{}')
                z.writestr(PREFIX+'STAGE11_STATUS_RECORDS.jsonl','\n'.join(map(json.dumps,records)))
            with zipfile.ZipFile(companion,'w') as z:
                z.writestr('media/'+rel,document)
            result,items=verify(main,companion,expected_missing=1)
            self.assertEqual(result['media_members_bytewise_verified'],1)
            self.assertEqual(result['whole_lifecycle_dossiers_human_certified'],0)
            self.assertIn('EO:TEST',items[0]['candidate_case_ids_from_directory_only'])
            with zipfile.ZipFile(companion,'w') as z:
                z.writestr('media/'+rel,b'wrong bytes')
            with self.assertRaises(ValueError):
                verify(main,companion,expected_missing=1)

if __name__=='__main__':
    unittest.main()
