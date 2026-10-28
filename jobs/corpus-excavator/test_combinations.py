import hashlib
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE));sys.path.insert(0,str(ROOT/'jobs/readiness-tracker'))
from test_tracker import TrackerTest
from combinations import replay,validate_predictions


class Combinations(TrackerTest):
    def setUp(self):
        super().setUp()
        p=self.root/'jobs/readiness-tracker/tracker.py';p.parent.mkdir(parents=True)
        shutil.copyfile(ROOT/'jobs/readiness-tracker/tracker.py',p)
        for relative in ('jobs/claim-kit/working_text.py', 'jobs/claim-kit/factual_events.py',
                         'jobs/norton/model.py'):
            target=self.root/relative;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/relative,target)

    def test_copied_tracker_imports_without_cached_policy_modules(self):
        path=self.root/'jobs/readiness-tracker/tracker.py'
        code=('import importlib.util,sys; '
              's=importlib.util.spec_from_file_location("isolated_tracker",sys.argv[1]); '
              'm=importlib.util.module_from_spec(s); s.loader.exec_module(m)')
        subprocess.run([sys.executable,'-I','-c',code,str(path)],check=True,
                       capture_output=True,text=True)

    def test_pairs_use_production_logic_and_preserve_missing_claim(self):
        a={'key':'text','origin':'owner-seeded','assumption':'Assume original held; planning only.',
           'closures':{'EO:1':['original_text']}}
        b={'key':'shared','origin':'owner-seeded','assumption':'Assume shared source retrieved; planning only.',
           'closures':{'EO:1':['shared_sources']}}
        before,replays=replay(self.root,[a,b]);self.assertEqual(len(replays),3)
        both=replays[-1]['changes'][0]
        self.assertIn('ending_or_current_basis',both['residual_open_steps'])
        self.assertFalse(both['conditional_machine_ready'])
        self.assertTrue(replays[-1]['planning_only'])
        after,_=replay(self.root,[a]);self.assertEqual(before,after)
        self.assertFalse((self.root/'research/readiness/EXHAUSTED.jsonl').exists())

    def test_status_and_unknown_identity_closures_refused(self):
        for iid,steps in [('EO:1',['provisional_status']),('EO:999',['original_text'])]:
            with self.assertRaises(ValueError):replay(self.root,[{'key':'bad','origin':'owner-seeded','assumption':'planning only','closures':{iid:steps}}])

    def test_validator_exposes_wrong_residual_prediction(self):
        actual=[{'instrument_id':'x','step_original_text':'done','step_ending_or_current_basis':'open'}]
        self.assertTrue(validate_predictions([{'instrument_id':'x','residual_open_steps':['ending_or_current_basis']}],actual)[0]['residual_match'])
        self.assertFalse(validate_predictions([{'instrument_id':'x','residual_open_steps':[]}],actual)[0]['residual_match'])


if __name__=='__main__':unittest.main()
