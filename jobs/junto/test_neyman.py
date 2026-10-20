import copy
import importlib.util
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import junto
from contracts import validate_contract
spec=importlib.util.spec_from_file_location('finder_neyman',Path(__file__).resolve().parent/'finders/neyman.py')
finder=importlib.util.module_from_spec(spec);spec.loader.exec_module(finder)


class QualityRegression(unittest.TestCase):
    def test_unknown_zero_partial_negative_quality_never_verifies(self):
        good={'usd':10,'units':2,'quality':{'accepted':2,'rejected':0}}
        for quality in ({},{'accepted':0,'rejected':0},{'accepted':2},{'accepted':3,'rejected':-1}):
            for arm in ('before','after'):
                t={'before':dict(good,usd=20),'after':copy.deepcopy(good)};t[arm]['quality']=quality
                self.assertNotEqual(junto.verdict_of(t),'saves')

    def test_measured_quality_pass_and_quality_drop(self):
        t={'before':{'usd':20,'units':2,'quality':{'accepted':2,'rejected':0}},
           'after':{'usd':10,'units':2,'quality':{'accepted':2,'rejected':0}}}
        self.assertEqual(junto.verdict_of(t),'saves')
        t['after']['quality']={'accepted':1,'rejected':1}
        self.assertEqual(junto.verdict_of(t),'quality_fell')

    def test_isolated_cli_can_load_sibling_contract_module(self):
        import subprocess
        p=subprocess.run([sys.executable,'-I',str(Path(junto.__file__)),'check'],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)

    def test_owner_origin_and_contract_immutable_unit(self):
        a={'schema':'neyman.aggregate/1','manifest_sha256':'a'*64,'frame_population':100,'attempts':24,
           'outcomes':{'blocked_prerequisite':24},'blocker_counts':{},'shared_events':1,'active_phase_coverage':0,
           'api_token_valuation_usd':None,'actual_cash_expenditure_usd':None}
        records=finder.candidates(a)
        self.assertTrue(all(c['origin']=='owner-seeded' and c['status']=='unverified' for c in records))
        self.assertEqual(len({c['saver_key'] for c in records}),3)
        records[0]['test_contract']['result_location']='/tmp/raw.txt'
        with self.assertRaises(ValueError):validate_contract(records[0])
        a['raw_transcript']='private'
        with self.assertRaises(ValueError):finder.candidates(a)


if __name__=='__main__':unittest.main()
