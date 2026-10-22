import csv, gzip, hashlib, importlib.util, json, os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

class RangerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        with patch.dict(os.environ, {'REPO_ROOT':str(Path(__file__).resolve().parents[2]),
             'OUTPUT_DIR':str(self.root/'out'), 'JOB_CACHE_DIR':str(self.root/'cache')}):
            spec=importlib.util.spec_from_file_location('ranger_job',Path(__file__).with_name('job.py'))
            self.mod=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.mod)
    def csv(self,name,rows,fields=None):
        path=self.root/name
        with path.open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=fields or list(rows[0]))
            writer.writeheader();writer.writerows(rows)
        return path

    def inputs(self,count=2):
        rows=[{'catalog_item_id':id_,'url':'https://www.loc.gov/item/'+id_+'/',
               'status':'official_item_JSON_retrieved','source_metadata_sha256':'a'*64,
               'media_resource_candidates':[{'url':f'https://tile.loc.gov/storage-services/master/{id_}/{n}.jpg'} for n in range(count)]}
              for id_ in self.mod.IDS]
        self.mod.INPUT=self.root/'input.jsonl'
        self.mod.INPUT.write_text(''.join(json.dumps(x)+'\n' for x in rows))
        return rows
    def test_changed_page_count_recorded_without_authentication(self):
        self.inputs()
        class Pool:
            def prefetch(self,urls):self.urls=urls
            def fetch(self,url):return {'final_url':url,'body':b'\xff\xd8\xffpage\xff\xd9'}
        self.mod.POOL=Pool();self.mod.main()
        summary=json.loads((self.mod.OUT/'PAGE_IMAGE_METRICS.json').read_text())
        self.assertEqual(summary['original_scan_JPEGs_acquired'],6)
        self.assertTrue(summary['page_count_changes_require_review'])
        self.assertFalse(summary['original_clause_authentication_done'])
        with (self.mod.OUT/'PAGE_IMAGE_CUSTODY.csv').open() as f:
            fields=csv.DictReader(f).fieldnames
            self.assertEqual(fields.count('error'),1)
    def test_invalid_source_and_budget_stop_before_prefetch(self):
        from unittest.mock import Mock
        for count in (0,25):
            self.inputs(count);self.mod.POOL=Mock()
            with self.assertRaisesRegex(ValueError,'master page manifest'):self.mod.main()
            self.mod.POOL.prefetch.assert_not_called()
        rows=self.inputs()
        rows[0]['media_resource_candidates'][0]['url']='https://evil.test/storage-services/master/a.jpg'
        self.mod.INPUT.write_text(''.join(json.dumps(x)+'\n' for x in rows))
        with self.assertRaisesRegex(ValueError,'Unapproved'):self.mod.main()
        self.mod.POOL.prefetch.assert_not_called()
    def test_failed_metadata_does_not_become_empty_success(self):
        rows=self.inputs();rows[0]['status']='metadata_request_failed'
        self.mod.INPUT.write_text(''.join(json.dumps(x)+'\n' for x in rows))
        with self.assertRaisesRegex(ValueError,'metadata unavailable'):self.mod.main()

if __name__=="__main__":unittest.main()
