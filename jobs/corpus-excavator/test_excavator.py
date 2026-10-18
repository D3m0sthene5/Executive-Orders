import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent))
from excavator import opportunity, rank_actions, era, source_type, discover, canonical
from plan import select_plan, queue_fingerprint, retain_unselected
from fetch_ladder import Wanted


class PlannerTests(unittest.TestCase):
    def row(self, *opens, blockers='OPUS_MEDIA_REFETCH_NEEDED'):
        from excavator import STEPS
        return dict({'step_'+s:('open' if s in opens else 'done') for s in STEPS},blockers=blockers)

    def test_ready_source_before_large_lead_queue(self):
        rows={'EO:1':self.row('opus_media'),'EO:2':self.row('opus_media','ending_or_current_basis')}
        a=opportunity(Wanted('opus-refetch:a',['EO:1'],step='opus_media'),rows,set())
        b=opportunity(Wanted('opus-refetch:b',['EO:2'],step='opus_media'),rows,set())
        self.assertEqual(rank_actions([b,a])[0]['wanted_id'],'opus-refetch:a')
        self.assertEqual(b['remaining_step_tasks'],1)
        self.assertEqual(a['ready_lower_bound'],0)

    def test_conflict_is_not_removed_by_download(self):
        rows={'EO:1':self.row('opus_media',blockers='OPUS_MEDIA_REFETCH_NEEDED|QUARANTINED_RELATIONSHIP_CONFLICT')}
        a=opportunity(Wanted('opus-refetch:a',['EO:1'],step='opus_media'),rows,set())
        self.assertEqual(a['near_ready_order_ids'],[])

    def test_current_receipt_is_not_a_new_step(self):
        rows={'EO:1':self.row('opus_media')}
        self.assertEqual(opportunity(Wanted('opus-refetch:a',['EO:1'],step='opus_media'),rows,{'opus-refetch:a'})['potential_step_completions'],0)

    def test_stale_plan_and_ambiguous_id_fail_closed(self):
        items=[Wanted('x',['EO:1'],urls=['https://example.test/old'])]
        p={'schema':'eo-source-plan/v1','queue_fingerprint':queue_fingerprint(items),'wanted_ids':['x'],'max_requests':5}
        self.assertEqual(select_plan(items,p),items)
        items[0].urls=['https://example.test/new']
        with self.assertRaises(ValueError):select_plan(items,p)
        items=[Wanted('x',[]),Wanted('x',[])]
        p['queue_fingerprint']=queue_fingerprint(items)
        with self.assertRaises(ValueError):select_plan(items,p)

    def test_budget_cannot_be_unbounded(self):
        items=[Wanted('x',[])]
        p={'schema':'eo-source-plan/v1','queue_fingerprint':queue_fingerprint(items),'wanted_ids':['x'],'max_requests':0}
        with self.assertRaises(ValueError):select_plan(items,p)

    def test_incremental_pass_retains_exact_prior_bytes(self):
        class Prior:
            label='frozen prior'
            def csv_rows(self,name):return [{'wanted_id':'old','result':'found'}]
        source={'wanted_id':'old','sha256':'a'*64,'retrieved_utc':'2000-01-01T00:00:00Z'}
        with tempfile.TemporaryDirectory() as t:
            sources,results=retain_unselected(Prior(),{'old':(source,b'raw\r\nbytes\x0c')},{'new'},Path(t))
            self.assertEqual((Path(t)/sources[0]['text_path']).read_bytes(),b'raw\r\nbytes\x0c')
            self.assertEqual(sources[0]['retrieved_utc'],source['retrieved_utc'])
            self.assertEqual(results[0]['attempts'],0)

    def test_historical_witness_never_date_merges(self):
        class Fake:
            def csv(self,path):return [{'key':'eo:42A','seq':'1','pairing_confidence':'high'},
                {'key':'date:1814-08-13','seq':'2','in_census':'no','pairing_confidence':'low'}]
            def lines(self,path):return []
        rows=discover(Fake(),{'EO:41':{},'EO:43':{},'EO:UN:existing-same-date':{}})
        self.assertEqual({r['kind'] for r in rows},{'numbered_editorial_witness','unnumbered_editorial_witness','numbered_series_gap'})
        self.assertTrue(any(r['candidate_id']=='EO:42A' for r in rows))

    def test_year_only_is_not_an_effective_date(self):
        self.assertEqual(era({'date_effective':'1900'}),'1862-1906')
        self.assertEqual(era({}),'undated')
        self.assertEqual(source_type({'url':'https://www.presidency.ucsb.edu/x'}),'derivative_or_mirror')


if __name__=='__main__':unittest.main()
