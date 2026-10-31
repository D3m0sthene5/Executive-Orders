import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import after_completion as bridge
from production_receipts import Reader, canonical


class CompletionHandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.repo=Path(self.tmp.name)
        self.folder='research/excavator/fixture/complete'
        self.history='research/excavator/fixture/COMPLETION_COSTS.json'
        self.dest='research/neyman/production-diagnostics/fixture'
        self.claim={'schema':'eo-lifecycle-claim/v1','instrument_id':'EO:1','fixture':True}
        self.row={'instrument_id':'EO:1','outcome':'eligible','claim_sha256':canonical(self.claim),
                  'publication_kind':'whole_case','source_review_upheld':True,'gate_errors':[]}
        self.receipt={'schema':'eo-claim-kit-completion/v1','outcomes':[self.row],
                      'started_utc':'2026-10-29T10:00:00Z','finished_utc':'2026-10-29T10:00:02Z','wall_seconds':2}
        self.write(self.folder+'/TALLY.json',self.receipt)
        self.write(self.folder+'/CLAIMS.selected.jsonl',self.claim)
        self.write(self.folder+'/TRACKER_REPLAY.json',{'canonical_outputs_modified':False,
             'selected':{'EO:1':{'after':{'instrument_id':'EO:1','ready_for_human_review':'yes','blockers':''}}}})
        self.update_history([self.folder+'/TALLY.json'])

    def write(self,path,value):
        p=self.repo/path; p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(value)+'\n'); return path

    def update_history(self,paths):
        reader=Reader(self.repo)
        self.write(self.history,{'invocations':[reader.ref(p) for p in paths]})

    def run_it(self,**kwargs):
        return bridge.build(self.repo,self.history,[self.folder],'a'*40,self.dest,**kwargs)

    def test_real_native_import_preserves_scope_and_unknown_cost(self):
        path,data=self.run_it()
        self.assertEqual(data['observations'][0]['reviewed_output'],'whole_case_proposal')
        self.assertIsNone(data['net_savings'])
        self.assertIsNone(json.loads((path.parent/'HANDOFF.json').read_text())['total_agent_hours'])
        self.assertEqual(data['observations'][0]['human_certifications_added'],0)

    def test_failed_attempts_and_duplicate_receipts_are_retained_once(self):
        failed=self.write('research/excavator/fixture/failed/TALLY.json',dict(self.receipt,
            outcomes=[{'instrument_id':'EO:1','outcome':'exception','error':'fixture failure'}],
            started_utc='2026-10-29T09:00:00Z',finished_utc='2026-10-29T09:00:01Z',wall_seconds=1))
        self.update_history([failed,self.folder+'/TALLY.json',self.folder+'/TALLY.json'])
        _,data=self.run_it()
        self.assertEqual(len(data['attempts']),2)
        self.assertEqual(len(data['duplicate_receipt_aliases']),1)
        self.assertEqual(data['attempts'][0]['outcomes'][0]['outcome'],'exception')

    def test_changed_history_pin_refused(self):
        self.write(self.folder+'/TALLY.json',dict(self.receipt,wall_seconds=3))
        with self.assertRaisesRegex(ValueError,'changed input'): self.run_it()

    def test_selected_claim_mismatch_refused(self):
        self.write(self.folder+'/CLAIMS.selected.jsonl',dict(self.claim,fixture=False))
        with self.assertRaisesRegex(ValueError,'selected claim bytes'): self.run_it()
        self.assertTrue((self.repo/self.dest/'REFUSED.json').is_file())

    def test_partial_output_never_becomes_whole(self):
        self.row.update(publication_kind='partial_research',gate_errors=['source_gap'])
        self.write(self.folder+'/TALLY.json',self.receipt); self.update_history([self.folder+'/TALLY.json'])
        _,data=self.run_it()
        self.assertEqual(data['observations'][0]['reviewed_output'],'partial_research')
        self.assertFalse(data['observations'][0]['whole_case_gate_pass'])

    def test_unfinished_members_not_silently_dropped(self):
        self.receipt['outcomes'].append({'instrument_id':'EO:2','outcome':'blocked'})
        self.write(self.folder+'/TALLY.json',self.receipt); self.update_history([self.folder+'/TALLY.json'])
        with self.assertRaisesRegex(ValueError,'refusing to drop: EO:2'): self.run_it()

    def test_explicit_unfinished_attempt_included(self):
        self.receipt['outcomes'].append({'instrument_id':'EO:2','outcome':'blocked'})
        self.write(self.folder+'/TALLY.json',self.receipt); self.update_history([self.folder+'/TALLY.json'])
        reader=Reader(self.repo)
        attempt=self.write('research/excavator/fixture/attempt.json',{'schema':'neyman.research-attempt/1',
            'attempt_id':'attempt2','instrument_id':'EO:2','assessor':'fixture','question':'Which source is missing?',
            'outcome':'blocked','started_utc':'2026-10-29T09:00:00Z','finished_utc':'2026-10-29T09:01:00Z',
            'basis':[reader.ref(self.folder+'/TALLY.json')]})
        _,data=self.run_it(research_attempts=[attempt])
        self.assertEqual(len(data['observations']),2)
        self.assertEqual(data['observations'][1]['reviewed_output'],'no_reviewed_result')

    def test_final_must_be_in_explicit_history(self):
        other=self.write('research/excavator/fixture/other.json',dict(self.receipt,wall_seconds=7))
        self.update_history([other])
        with self.assertRaisesRegex(ValueError,'absent from explicit history'): self.run_it()

    def test_fresh_destination_required(self):
        self.run_it()
        with self.assertRaisesRegex(ValueError,'fresh NEYMAN'): self.run_it()

    def test_cli_invokes_existing_diagnosis_on_pinned_manifest(self):
        diagnose=mock.Mock(); diagnose.main.return_value=0
        with mock.patch.dict('sys.modules',{'diagnose':diagnose}):
            result=bridge.main(['--repo',str(self.repo),'--history',self.history,'--final',self.folder,
                                '--base-commit','a'*40,'--write',self.dest])
        self.assertEqual(result,0)
        args=diagnose.main.call_args[0][0]
        self.assertEqual(args[args.index('--manifest')+1],self.dest+'/IMPORT.json')
        self.assertTrue(args[-1].endswith('/diagnosis'))

    def test_current_receipt_appended_without_rewriting_supplied_history(self):
        before=(self.repo/self.history).read_bytes()
        path,data=self.run_it(current=self.folder)
        self.assertEqual((self.repo/self.history).read_bytes(),before)
        self.assertEqual(len(data['attempts']),1)
        self.assertEqual(len(data['duplicate_receipt_aliases']),1)
        manifest=json.loads(path.read_text())
        self.assertEqual(manifest['supplied_history']['path'],self.history)
        self.assertTrue(manifest['completion_index']['path'].endswith('/COMPLETION_HISTORY.json'))

    def test_new_current_unfinished_member_still_cannot_disappear(self):
        other='research/excavator/fixture/current'
        self.write(other+'/TALLY.json',dict(self.receipt,outcomes=[{'instrument_id':'EO:2','outcome':'blocked'}]))
        with self.assertRaisesRegex(ValueError,'refusing to drop: EO:2'):
            self.run_it(current=other)

    def test_question_is_forwarded_to_existing_diagnosis(self):
        reader=Reader(self.repo)
        question=self.write('research/excavator/fixture/question.json',{
            'schema':'neyman.discriminating-question/1','instrument_id':'EO:1','assessor':'fixture',
            'question':'Is the dated report held?', 'needed_observation':'Exact dated report',
            'suggested_existing_route':'Existing source-ladder explicit plan',
            'alternatives':['The report is held','The report still requires acquisition'],
            'basis':[reader.ref(self.folder+'/TALLY.json')]})
        path,_=self.run_it(questions=[question])
        import diagnose
        reader=Reader(self.repo)
        data=diagnose.diagnose(reader,json.loads(path.read_text()))
        self.assertEqual(data['observations'][0]['next_questions'][0]['question'],'Is the dated report held?')


if __name__=='__main__': unittest.main()
