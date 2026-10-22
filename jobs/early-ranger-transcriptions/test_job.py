import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


class TranscriptionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        with patch.dict(os.environ, {'REPO_ROOT': str(Path(__file__).resolve().parents[2]),
                                     'OUTPUT_DIR': str(self.root / 'out'),
                                     'JOB_CACHE_DIR': str(self.root / 'cache')}):
            spec = importlib.util.spec_from_file_location('loc_transcription_job', Path(__file__).with_name('job.py'))
            self.mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.mod)
        self.addCleanup(self.tmp.cleanup)

    def row(self, n, item=None):
        return {'catalog_item_id': item or f'item{n}', 'url': 'https://www.loc.gov/item/example/',
                'source_metadata_sha256': 'a' * 64, 'official_item_title': 'Example',
                'media_resource_candidates': [{'link_role_as_metadata': 'fulltext_file',
                    'url': f'https://tile.loc.gov/storage-services/test/{n}.xml'}]}

    def test_changed_metadata_count_deduplication_and_bound(self):
        rows = [self.row(n) for n in range(11)]
        self.assertEqual(len(self.mod.build_plan(rows + rows)), 11)
        self.assertEqual(self.mod.build_plan([]), [])
        with self.assertRaisesRegex(ValueError, 'bounded maximum'):
            self.mod.build_plan([self.row(n) for n in range(51)])

    def test_untrusted_url_stops_before_fetch(self):
        for url in ('http://tile.loc.gov/storage-services/a.xml',
                    'https://other.test/storage-services/a.xml',
                    'https://tile.loc.gov/elsewhere/a.xml'):
            row = self.row(1)
            row['media_resource_candidates'][0]['url'] = url
            with self.assertRaisesRegex(ValueError, 'Unsafe XML'):
                self.mod.build_plan([row])

    def test_two_resources_for_one_item_keep_distinct_bytes(self):
        rows = [self.row(n, 'sameitem') for n in range(2)]
        source = self.root / 'seeds.jsonl'
        source.write_text(''.join(json.dumps(r) + '\n' for r in rows))
        self.mod.SEEDS = source
        class Pool:
            def prefetch(self, urls):
                self.urls = urls
            def fetch(self, url):
                return {'final_url': url, 'body': ('<p>Unreviewed official transcription text: ' + url + '</p>').encode()}
        self.mod.POOL = Pool()
        self.mod.main()
        inventory = [json.loads(s) for s in (self.mod.OUT / 'TRANSCRIPTION_INVENTORY.jsonl').read_text().splitlines()]
        self.assertEqual(len({r['xml_path'] for r in inventory}), 2)
        self.assertEqual(len({r['transcript_path'] for r in inventory}), 2)
        self.assertTrue(all(not r['legal_directive_verified'] for r in inventory))
        self.assertTrue(all((self.mod.OUT / r['xml_path']).is_file() for r in inventory))


if __name__ == '__main__':
    unittest.main()
