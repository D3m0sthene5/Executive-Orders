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

    def inputs(self,items):
        self.mod.SOURCE=self.csv('items.csv',items,['loc_item_https','catalog_date','title','response_sha256'])
        self.mod.GRID=self.csv('grid.csv',[{'year':str(y),'year_risk':'NO_INHERITED_LEADS_MEANS_UNKNOWN_NOT_ZERO'} for y in range(1789,1862)])
        self.mod.CURATED=self.csv('curated.csv',[],['candidate_id'])
    def test_variable_catalog_and_empty_curated_are_discovery_only(self):
        self.inputs([{'loc_item_https':'https://www.loc.gov/item/a/','catalog_date':'1814-08-13','title':'James Madison order','response_sha256':'a'*64}])
        self.mod.main()
        with (self.mod.OUT/'PRIORITIZED_PRESIDENTIAL_PERIOD_CANDIDATES.csv').open() as f:rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['eo_inclusion_judgment'],'unknown')
        self.assertIn('NOT_AUTHENTICATED',rows[0]['presidential_term_screen_ONLY'])
        self.inputs([]);self.mod.main()
        self.assertEqual(json.loads((self.mod.OUT/'TRIAGE_SUMMARY.json').read_text())['loc_item_candidates'],0)
    def test_missing_year_and_bad_source_hash_rejected(self):
        self.inputs([])
        self.mod.GRID=self.csv('grid.csv',[{'year':str(y),'year_risk':'unknown'} for y in range(1790,1862)])
        with self.assertRaisesRegex(ValueError,'each year'):self.mod.main()
        self.inputs([{'loc_item_https':'https://www.loc.gov/item/a/','catalog_date':'1814','title':'x','response_sha256':'bad'}])
        with self.assertRaisesRegex(ValueError,'source response hash'):self.mod.main()

if __name__=="__main__":unittest.main()
