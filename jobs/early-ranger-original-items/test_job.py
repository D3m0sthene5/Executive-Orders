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

    def row(self,id_):
        return {'catalog_item_url':'https://www.loc.gov/item/'+id_+'/',
                'title_as_indexed':'James Madison order','date_as_indexed':'1814-08-13',
                'triage_lane_NOT_identification':'priority_presidential_period_directive_wording',
                'review_priority_NOT_probability':'20'}
    def test_variable_plan_deduplicates_and_retains_page_followups(self):
        plan=self.mod.build_plan([self.row('new'),self.row('new'),self.row('mjm022917')])
        ids=[self.mod.item_id(r['catalog_item_url']) for r in plan]
        self.assertEqual(len(ids),5)
        self.assertEqual(ids[:3],['mjm017456','maj012871','mtjbib012509'])
        with self.assertRaisesRegex(ValueError,'official LOC'):
            self.mod.build_plan([{**self.row('x'),'catalog_item_url':'https://other.test/item/x/'}])
    def test_request_budget_preserves_deferred_leads(self):
        self.mod.SEEDS=self.csv('seeds.csv',[self.row('item'+str(i)) for i in range(25)])
        self.mod.LORD=self.csv('lord.csv',[],['candidate_id'])
        def fetch(id_):return b'{"item":{}}',{'item':{}},'https://www.loc.gov/item/'+id_+'/'
        with patch.object(self.mod,'fetch_item',side_effect=fetch) as mocked,patch.object(self.mod.time,'sleep'):
            self.mod.main()
        self.assertEqual(mocked.call_count,22)
        report=(self.mod.OUT/'ORIGINAL_SOURCE_REVIEW.md').read_text()
        self.assertIn('Planned 29',report)
        self.assertIn('attempted 22',report)
        packets=[json.loads(x) for x in (self.mod.OUT/'PRIMARY_ITEM_METADATA.jsonl').read_text().splitlines()]
        self.assertEqual(len(packets),29)
        self.assertEqual(sum(x['status']=='deferred_after_item_budget' for x in packets),7)
        self.assertTrue(all(x['legal_EO_inclusion']=='unknown' for x in packets))

if __name__=="__main__":unittest.main()
