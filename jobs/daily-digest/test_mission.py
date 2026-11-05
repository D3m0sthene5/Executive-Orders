"""Native-generation binding and last-good retention regression gates."""
import copy, csv, hashlib, io, json
from pathlib import Path
import subprocess, tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import mission

REPO = Path(__file__).resolve().parents[2]
CAPCOM = mission.load_capcom(REPO)

class MissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(['git','init','-q',str(self.root)],check=True)
        self.put('seed',b'seed')
        self.put('research/readiness/rules.json',b'{"fixture": true}\n')
        subprocess.run(['git','-C',str(self.root),'add','seed','research/readiness'],check=True)
        subprocess.run(['git','-C',str(self.root),'-c','user.name=fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture'],check=True)
        self.commit=mission.git(self.root,'rev-parse','HEAD')
        self.checker=self.status('claim-checker','10:00','10:01')
        self.tracker=self.status('readiness-tracker','10:01','10:02')
        self.doc(mission.CHECKER+'STATUS.json',self.checker)
        self.doc(mission.CHECKER+'RUNNER_INPUTS.json',self.manifest('claim-checker',{'research/readiness/rules.json':'100644:'+mission.git(self.root,'hash-object','--no-filters','--','research/readiness/rules.json')}))
        self.doc(mission.CHECKER+'PER_CLAIM.json',{'claims':[]})
        self.doc(mission.CHECKER+'SUMMARY.json',{'claims_checked':0})
        inputs={mission.CHECKER+n:'100644:'+mission.git(self.root,'hash-object','--no-filters','--',mission.CHECKER+n)
                for n in ('STATUS.json','RUNNER_INPUTS.json','PER_CLAIM.json','SUMMARY.json')}
        inputs['research/readiness/rules.json']='100644:'+mission.git(self.root,'hash-object','--no-filters','--','research/readiness/rules.json')
        self.doc(mission.TRACKER+'STATUS.json',self.tracker)
        self.doc(mission.TRACKER+'RUNNER_INPUTS.json',self.manifest('readiness-tracker',inputs))
        self.steps=CAPCOM.brw.STEPS[1:]
        self.rows=[{'instrument_id':'EO:1','ready_for_human_review':'yes','provisional_status':'no','text_evidence_tier':'original_supported',**{'step_'+s:'done' for s in self.steps}},
                   {'instrument_id':'EO:2','ready_for_human_review':'no','provisional_status':'','text_evidence_tier':'missing',**{'step_'+s:'open' for s in self.steps}}]
        for row in self.rows:
            for step in ('shared_sources','opus_media'):row['step_'+step]='n/a'
        self.table(mission.TRACKER+'READINESS_BY_ORDER.csv',self.rows)
        self.summary={'orders_total':2,'ready_for_human_review':1,'orders_with_provisional_status':1,'ready_by_text_evidence_tier':{'original_supported':1},'input_problems':[]}
        self.doc(mission.TRACKER+'SUMMARY.json',self.summary)
        self.table('research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv',[{'id':'EO:1'},{'id':'EO:2'}])
        for name in ('MISSION_WEIGHTS.csv','APOLLO11_MILESTONES.csv'):self.put(mission.SOURCE+name,(REPO/mission.SOURCE/name).read_bytes())
        self.doc(mission.SOURCE+'REMAINING_WORK.json',{'not_yet_in_project':1314})
        self.doc('research/stage19/output/PROGRESS.json',{'independently_reviewed_whole_lifecycle_complete':0})
        self.old=CAPCOM.snapshot(self.rows,mission.FROZEN_WEIGHTS,1314,CAPCOM.first_step_hours(),CAPCOM.milestones(),'2026-10-30','a'*40,'2026-10-30T10:00:00Z')
        self.table(mission.SOURCE+'snapshots/2026-10-30/MISSION_LOG.csv',[self.old])
        self.capcom=SimpleNamespace(brw=CAPCOM.brw,weights=lambda:dict(mission.FROZEN_WEIGHTS),milestones=CAPCOM.milestones,first_step_hours=CAPCOM.first_step_hours,snapshot=CAPCOM.snapshot,history=lambda head:[self.old])
        self.dashboard={'freshness':{'claim_receipts':{'state':'claim_versions_match'},'discrepancies':[],'tracker_generation':self.tracker,'checker_generation':self.checker}}
    def put(self,name,raw):
        p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    def doc(self,name,value):self.put(name,(json.dumps(value,sort_keys=True)+'\n').encode())
    def table(self,name,rows):
        stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows);self.put(name,stream.getvalue().encode())
    def status(self,name,start,finish):
        return {'job':name,'result':'succeeded','exit_code':0,'commit_run':self.commit,'started_utc':'2026-11-04T'+start+':00Z','finished_utc':'2026-11-04T'+finish+':00Z','run_url':'https://example.invalid/run/1','oversized_files_moved_to_run_download':[]}
    def manifest(self,name,inputs):return {'schema':1,'job':name,'base_commit':self.commit,'run_url':'https://example.invalid/run/1','inputs':inputs,'inputs_sha256':mission.digest(inputs)}
    def build(self):return mission.build(self.root,self.dashboard,self.capcom)
    def test_same_run_uncommitted_generation_uses_existing_model(self):
        result=self.build();latest=result['latest']
        self.assertEqual(latest['ready_for_human_review'],1);self.assertEqual(latest['orders_goal'],1316)
        self.assertNotEqual(latest['progress'],1/2);self.assertEqual(latest['human_certified'],0)
        self.assertEqual(result['human_review']['published_whole_lifecycle_certifications'],0)
        self.assertEqual(result['history'][0],self.old);self.assertEqual(latest['committed_at'],self.tracker['finished_utc'])
        self.assertEqual(result['readiness_inputs'],{'path':'research/readiness','git_tree':mission.git(self.root,'rev-parse','HEAD:research/readiness')})
        self.assertEqual(result['sources']['tracker_status']['sha256'],hashlib.sha256((self.root/mission.TRACKER/'STATUS.json').read_bytes()).hexdigest())
    def test_mixed_checker_rejected_even_with_same_counts_and_dates(self):
        self.doc(mission.CHECKER+'PER_CLAIM.json',{'claims':[{'changed':True}]})
        with self.assertRaisesRegex(ValueError,'different checker generation'):self.build()
    def test_summary_disagreement_and_unknown_step_rejected(self):
        self.summary['ready_for_human_review']=2;self.doc(mission.TRACKER+'SUMMARY.json',self.summary)
        with self.assertRaisesRegex(ValueError,'summary readiness disagree'):self.build()
        self.summary['ready_for_human_review']=1;self.doc(mission.TRACKER+'SUMMARY.json',self.summary)
        self.rows[1]['step_original_text']='unknown';self.table(mission.TRACKER+'READINESS_BY_ORDER.csv',self.rows)
        with self.assertRaisesRegex(ValueError,'unknown or missing tracker step'):self.build()
    def test_bad_manifest_and_stale_claims_rejected(self):
        path=self.root/mission.TRACKER/'RUNNER_INPUTS.json';m=json.loads(path.read_text());m['inputs_sha256']='0'*64;self.doc(mission.TRACKER+'RUNNER_INPUTS.json',m)
        with self.assertRaisesRegex(ValueError,'provenance digest differs'):self.build()
        m['inputs_sha256']=mission.digest(m['inputs']);self.doc(mission.TRACKER+'RUNNER_INPUTS.json',m)
        self.dashboard['freshness']['claim_receipts']['state']='stale'
        with self.assertRaisesRegex(ValueError,'current records require'):self.build()
    def test_weights_and_retained_history_are_frozen(self):
        self.capcom.weights=lambda:{**mission.FROZEN_WEIGHTS,1:20}
        with self.assertRaisesRegex(ValueError,'weights changed'):self.build()
        self.capcom.weights=lambda:dict(mission.FROZEN_WEIGHTS);self.capcom.history=lambda head:[{**self.old,'progress':.9}]
        with self.assertRaisesRegex(ValueError,'historical Mission checkpoints changed'):self.build()
    def test_pending_retains_exact_bytes_then_valid_transition_replaces_them(self):
        prior,output=self.root/'prior',self.root/'output';prior.mkdir()
        for name in ('MISSION.json','MISSION_LOG.csv'):(prior/name).write_bytes(('retained '+name+'\n').encode())
        self.dashboard['freshness']['claim_receipts']['state']='stale'
        with patch.object(mission,'load_capcom',return_value=self.capcom):
            receipt=mission.refresh(self.root,output,self.dashboard,prior);self.assertEqual(receipt['state'],'pending')
            for name in ('MISSION.json','MISSION_LOG.csv'):self.assertEqual((output/name).read_bytes(),(prior/name).read_bytes())
            self.dashboard['freshness']['claim_receipts']['state']='claim_versions_match';receipt=mission.refresh(self.root,output,self.dashboard,prior)
        self.assertEqual(receipt['state'],'ready');self.assertEqual(receipt['readiness_inputs']['path'],'research/readiness');self.assertEqual(json.loads((output/'MISSION.json').read_text())['latest']['ready_for_human_review'],1)
    def test_first_refusal_is_explicitly_empty(self):
        output=self.root/'empty';receipt=mission.refresh(self.root,output,{})
        self.assertEqual(receipt['state'],'pending');self.assertFalse((output/'MISSION.json').exists());self.assertFalse((output/'MISSION_LOG.csv').exists())
    def test_new_committed_canonical_input_refuses_old_successful_generation(self):
        old_tree=self.build()['readiness_inputs']['git_tree']
        self.put('research/readiness/rules.json',b'{"fixture": false}\n')
        subprocess.run(['git','-C',str(self.root),'add','research/readiness'],check=True)
        subprocess.run(['git','-C',str(self.root),'-c','user.name=fixture','-c','user.email=fixture@example.invalid','commit','-qm','new canonical rule'],check=True)
        self.assertNotEqual(old_tree,mission.git(self.root,'rev-parse','HEAD:research/readiness'))
        # Old successful tracker/checker/status and matching claims alone must
        # not stamp the new rule tree as consumed.
        with self.assertRaisesRegex(ValueError,'did not consume the current canonical readiness tree'):self.build()
    def test_new_tracker_cannot_promote_checker_from_an_old_rule_tree(self):
        # Hold checker generation constant, but let a new tracker capture the
        # current rule tree and the unchanged exact checker outputs.
        self.put('research/readiness/rules.json',b'{"fixture": false}\n')
        subprocess.run(['git','-C',str(self.root),'add','research/readiness'],check=True)
        subprocess.run(['git','-C',str(self.root),'-c','user.name=fixture','-c','user.email=fixture@example.invalid','commit','-qm','new canonical rule'],check=True)
        manifest=json.loads((self.root/mission.TRACKER/'RUNNER_INPUTS.json').read_text())
        manifest['inputs']['research/readiness/rules.json']='100644:'+mission.git(self.root,'hash-object','--no-filters','--','research/readiness/rules.json')
        manifest['inputs_sha256']=mission.digest(manifest['inputs']);self.doc(mission.TRACKER+'RUNNER_INPUTS.json',manifest)
        with self.assertRaisesRegex(ValueError,'checker did not consume the current canonical readiness tree'):self.build()
    def test_dirty_canonical_inputs_cannot_be_stamped_as_committed(self):
        self.put('research/readiness/new-claim.jsonl',b'{}\n')
        with self.assertRaisesRegex(ValueError,'uncommitted changes'):self.build()
        (self.root/'research/readiness/new-claim.jsonl').unlink()
        self.put('research/readiness/rules.json',b'{"fixture": false}\n')
        with self.assertRaisesRegex(ValueError,'uncommitted changes'):self.build()
    def test_provisional_text_preserves_existing_arithmetic(self):
        # A zero-gap isolated calculation makes the retained distinction visible
        # despite Capcom's five-decimal progress rounding.
        def snapshot(rows):return CAPCOM.snapshot(rows,mission.FROZEN_WEIGHTS,0,CAPCOM.first_step_hours(),CAPCOM.milestones(),'2026-11-04',self.commit,self.tracker['finished_utc'])
        baseline=snapshot(self.rows)
        rows=copy.deepcopy(self.rows);rows[1]['step_original_text']='provisional';latest=snapshot(rows)
        self.assertEqual(latest['steps_done'],baseline['steps_done']);self.assertEqual(latest['steps_open'],baseline['steps_open']-1)
        self.assertGreater(latest['progress'],baseline['progress']);self.assertEqual(latest['ready_for_human_review'],baseline['ready_for_human_review'])

if __name__=='__main__':unittest.main()
