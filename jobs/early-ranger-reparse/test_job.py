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

    def source(self,n=24,results=None):
        raw=json.dumps({'results':results or []}).encode()
        digest=hashlib.sha256(raw).hexdigest()
        self.mod.CACHE=self.root/'responses';self.mod.CACHE.mkdir(exist_ok=True)
        (self.mod.CACHE/(digest+'.json.gz')).write_bytes(gzip.compress(raw))
        self.mod.ATTEMPTS=self.root/'attempts.jsonl'
        self.mod.ATTEMPTS.write_text(''.join(json.dumps({'provider':'loc','status':'json_response_preserved_NOT_authenticated','request_id':f'q{i}','response_sha256':digest})+'\n' for i in range(n)))
        return digest
    def test_variable_successes_and_empty_catalog_keep_schema(self):
        self.source()
        self.mod.main()
        summary=json.loads((self.mod.OUT/'REPARSE_SUMMARY.json').read_text())
        self.assertEqual(summary['existing_loc_json_responses_reused'],24)
        self.assertEqual(summary['unique_canonical_LOC_item_or_resource_links'],0)
        with (self.mod.OUT/'LOC_MANUSCRIPT_CANDIDATES.csv').open() as f:
            self.assertEqual(csv.DictReader(f).fieldnames,self.mod.FIELDS)
    def test_hash_mismatch_and_duplicate_request_rejected(self):
        digest=self.source(1)
        (self.mod.CACHE/(digest+'.json.gz')).write_bytes(gzip.compress(b'{}'))
        with self.assertRaisesRegex(ValueError,'hash mismatch'):self.mod.main()
        self.source(1)
        text=self.mod.ATTEMPTS.read_text();self.mod.ATTEMPTS.write_text(text+text)
        with self.assertRaisesRegex(ValueError,'duplicate scout'):self.mod.main()
    def test_no_success_is_not_an_empty_catalog(self):
        self.source(0)
        with self.assertRaisesRegex(ValueError,'No preserved LOC'):self.mod.main()
    def test_decompression_bound(self):
        digest=self.source(1)
        (self.mod.CACHE/(digest+'.json.gz')).write_bytes(gzip.compress(b'x'*(self.mod.MAX_RESPONSE_BYTES+1)))
        with self.assertRaisesRegex(ValueError,'decompressed response too large'):self.mod.main()

if __name__=="__main__":unittest.main()
