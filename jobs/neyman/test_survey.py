import copy
import importlib.util
import json
from pathlib import Path
import random
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from survey import PHASES,TOKEN_CATEGORIES,OUTCOMES,sample,report,validate_observations,check_pins,frame
ROOT=Path(__file__).resolve().parents[2]


def rows():
    return [dict(instrument_id=f'EO:{g}-{h}-{i}',macro=str(g),stratum=f'{g}-{h}',era='undated',provisional_status='unknown',original_text='open')
            for g in range(2) for h in range(3) for i in range(h+1)]


def observation(iid,**changes):
    o={'instrument_id':iid,'manifest_sha256':'a'*64,'outcome':'blocked_prerequisite','right_censored':False,
       'completion_effort_seconds':None,'shared_event_ids':['shared'],'correlation_keys':[],
       'phases':{p:{'active_seconds':None,'machine_seconds':1,'access_wait_seconds':None,
                    'tokens':dict.fromkeys(TOKEN_CATEGORIES)} for p in PHASES}}
    o.update(changes);return o


class Sampling(unittest.TestCase):
    def test_fixed_seed_order_invariant_and_positive_probabilities(self):
        a,_=sample(rows(),1727,4);b,_=sample(list(reversed(rows())),1727,4)
        self.assertEqual(a,b);self.assertEqual(len({r['instrument_id'] for r in a}),4)
        self.assertEqual({r['macro'] for r in a},{'0','1'})
        self.assertTrue(all(0<r['inclusion_probability']<=1 for r in a))

    def test_probabilities_match_randomization_and_unbiased_weighted_population(self):
        pop=rows();seen={r['instrument_id']:0 for r in pop};totals=[]
        for seed in range(4000):
            chosen,_=sample(pop,seed,4);totals.append(sum(r['weight'] for r in chosen))
            for r in chosen:seen[r['instrument_id']]+=1
        for r in pop:
            p=2/3/(int(r['stratum'][-1])+1)
            self.assertLess(abs(seen[r['instrument_id']]/4000-p),0.03)
        self.assertLess(abs(sum(totals)/len(totals)-len(pop)),0.15)

    def test_limits_and_missing_macro_coverage_refused(self):
        for n in (0,1,25):
            with self.assertRaises(ValueError):sample(rows(),1727,n)

    def test_unconsumed_review_media_does_not_change_frame_but_audit_evidence_does(self):
        from survey import pins
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);t=r/'jobs/readiness-tracker/tracker.py';t.parent.mkdir(parents=True)
            t.write_text('P={}\nJ={}\n')
            baseline=pins(r)
            media=r/'research/readiness/reviews/unconsumed/page.png';media.parent.mkdir(parents=True);media.write_bytes(b'image')
            self.assertEqual(pins(r),baseline)
            hold=r/'research/readiness/SOURCE_AUDIT_HOLDS.jsonl'
            hold.write_text(json.dumps({'review_path':media.relative_to(r).as_posix()})+'\n')
            self.assertEqual(pins(r)[media.relative_to(r).as_posix()],__import__('hashlib').sha256(b'image').hexdigest())

    def test_stale_membership_and_hash_refused(self):
        with patch('survey.pins',return_value={'old':'a','new':'b'}):
            with self.assertRaisesRegex(ValueError,'stale'):check_pins(ROOT,{'old':'a'})
        with patch('survey.pins',return_value={'old':'b'}):
            with self.assertRaisesRegex(ValueError,'stale'):check_pins(ROOT,{'old':'a'})

    @unittest.skipUnless((ROOT/'jobs/claim-kit/output/FAMILIES.json').exists(),'requires actual repository outputs')
    def test_actual_frame_coverage_and_difficult_unknowns(self):
        population,counts=frame(ROOT);chosen,_=sample(population,1727)
        self.assertEqual(len(population)+counts['ready_for_human_review'],counts['orders_total'])
        self.assertEqual(len({r['instrument_id'] for r in population}),len(population))
        self.assertTrue(any(r['original_text']=='open' and r['provisional_status']=='unknown' for r in chosen))
        self.assertEqual(len(chosen),24)


class Accounting(unittest.TestCase):
    def setUp(self):
        self.m={'sample':[dict(instrument_id=i,stratum=i,macro='a',macro_cells=8) for i in ('x','y')],
                'manifest_sha256':'a'*64,'frame_population':100}
        self.obs=[observation('x'),observation('y')]
        self.shared=[{'event_id':'shared','machine_seconds':10,'active_seconds':None,'downstream_uses':['x','y']}]

    def test_shared_cost_once_and_correlated_cases(self):
        r=report(self.m,self.obs,self.shared)
        self.assertEqual(r['observed_machine_seconds_lower_bound'],24)
        self.assertEqual(r['correlation_components'],[2])
        self.assertEqual(r['active_phase_coverage'],0)
        self.assertIsNone(r['completion_total_seconds']);self.assertIsNone(r['api_token_valuation_usd'])
        self.assertIsNone(r['actual_cash_expenditure_usd'])

    def test_blocked_and_censored_in_denominator_missing_tokens_stay_null(self):
        self.obs[1].update(outcome='censored_limit',right_censored=True)
        r=report(self.m,self.obs,self.shared)
        self.assertEqual(r['attempts'],2);self.assertEqual(r['outcomes']['censored_limit'],1)
        self.assertTrue(all(v==0 for v in r['token_category_coverage'].values()))
        self.assertEqual(self.obs[0]['phases']['review']['tokens']['output'],None)

    def test_missing_case_duplicate_cost_and_forged_completion_refused(self):
        with self.assertRaisesRegex(ValueError,'nonresponse'):validate_observations(self.m,self.obs[:1],self.shared)
        with self.assertRaisesRegex(ValueError,'duplicate shared'):validate_observations(self.m,self.obs,self.shared*2)
        self.obs[0]['completion_effort_seconds']=0
        with self.assertRaisesRegex(ValueError,'incomplete'):validate_observations(self.m,self.obs,self.shared)

    def test_stale_observation_and_lost_censoring(self):
        self.obs[0]['manifest_sha256']='b'*64
        with self.assertRaisesRegex(ValueError,'stale'):validate_observations(self.m,self.obs,self.shared)
        self.obs[0]['manifest_sha256']='a'*64;self.obs[0]['outcome']='censored_limit'
        with self.assertRaisesRegex(ValueError,'censoring'):validate_observations(self.m,self.obs,self.shared)

    def test_shared_instrument_links_independent_of_cost_receipts(self):
        for o in self.obs:o['correlation_keys']=['instrument:EO:42']
        self.shared[0]['downstream_uses']=['x'];self.obs[1]['shared_event_ids']=[]
        self.assertEqual(report(self.m,self.obs,self.shared)['correlation_components'],[2])


if __name__=='__main__':unittest.main()

class Deadline(unittest.TestCase):
    def test_real_subprocess_deadline_retains_incomplete_observation(self):
        from pilot import run
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'jobs/neyman').mkdir(parents=True)
            (root/'jobs/neyman/attempt.py').write_text('import time\ntime.sleep(60)\n')
            kit=root/'jobs/claim-kit/output';kit.mkdir(parents=True)
            (kit/'INDEX.json').write_text('[]');(kit/'STATUS_LEADS.jsonl').write_text('{"instrument_id":"x"}\n')
            ladder=root/'jobs/source-ladder/output';ladder.mkdir(parents=True)
            (ladder/'RESULTS.csv').write_text('result,why,instrument_ids\n')
            m={'input_hashes':{},'manifest_sha256':'a'*64,'frame_population':1,'attempt_limit_seconds':0.05,
               'sample':[{'instrument_id':'x','families':['unknown'],'open_steps':['original_text'],'blockers':['MISSING'],
                          'stratum':'a','macro':'a','macro_cells':1}]}
            with patch('pilot.check_pins'):
                obs,r=run(root,m,root/'output',{'source_read_limit_bytes':1024})
            self.assertEqual(len(obs),1);self.assertEqual(obs[0]['outcome'],'censored_limit')
            self.assertTrue(obs[0]['right_censored']);self.assertIsNone(obs[0]['completion_effort_seconds'])
            self.assertGreater(obs[0]['attempt_wall_seconds'],0.04)
            self.assertEqual(r['attempts'],1)
