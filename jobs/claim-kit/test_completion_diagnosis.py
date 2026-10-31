"""Explicit native completion → existing NEYMAN; diagnostics cannot change gates."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

import batch
import completion as C
import kit
import test_completion as fixtures

HERE=Path(__file__).resolve().parents[2]


class DiagnosticCompletionTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.CompletionTests('test_exact_producer_bytes_and_all_consumed_receipts_preserved')
        self.f.setUp();self.addCleanup(self.f.doCleanups);self.f.setup_completion()
        self.repo=self.f.repo
        target=self.repo/'jobs/neyman';target.mkdir(parents=True)
        for name in ('after_completion.py','production_receipts.py','diagnose.py','survey.py'):
            shutil.copyfile(HERE/'jobs/neyman'/name,target/name)
        # A recorded earlier failed invocation; current successful receipt is
        # appended only after native completion writes it.
        failed=self.repo/'research/earlier/TALLY.json'
        batch.dump(failed,{'schema':C.SCHEMA,'outcomes':[{'instrument_id':'EO:1','outcome':'exception','error':'retained failed try'}],
            'started_utc':'2026-10-29T09:00:00Z','finished_utc':'2026-10-29T09:00:01Z','wall_seconds':1})
        self.history=self.repo/'research/earlier/HISTORY.json'
        batch.dump(self.history,{'invocations':[self.f.ref(failed),self.f.ref(failed)]})
        self.attempt=self.repo/'research/earlier/ATTEMPT.json'
        batch.dump(self.attempt,{'schema':'neyman.research-attempt/1','attempt_id':'blocked2','instrument_id':'EO:2',
            'assessor':'fixture','question':'Which evidence remains missing?','outcome':'blocked',
            'started_utc':'2026-10-29T09:00:00Z','finished_utc':'2026-10-29T09:00:01Z',
            'basis':[self.f.ref(failed)]})
        self.options={'history':self.history.relative_to(self.repo).as_posix(),'base_commit':'a'*40,
            'write':'research/neyman/production-diagnostics/fixture',
            'research_attempt':[self.attempt.relative_to(self.repo).as_posix()]}

    def invoke(self,options):
        batch.dump(self.f.manifest_path,self.f.manifest)
        tracker={'canonical_outputs_modified':False,'selected':{'EO:1':{'after':{
            'instrument_id':'EO:1','ready_for_human_review':'yes','blockers':''}}}}
        args=['--repo',str(self.repo),'complete',str(self.f.manifest_path),'--write',str(self.f.dest)]
        for key,value in options.items():
            for item in value if isinstance(value,list) else [value]:
                args += ['--diagnostic-'+key.replace('_','-'),str(item)]
        with patch.object(C,'run_checker',side_effect=self.f.checker),patch.object(C,'run_tracker',return_value=tracker),redirect_stdout(io.StringIO()) as out:
            code=kit.main(args)
        return code,json.loads(out.getvalue())

    def test_native_cli_appends_current_retains_failures_and_blocked_member(self):
        code,result=self.invoke(self.options)
        self.assertEqual(code,0)
        self.assertEqual(result['diagnostic']['status'],'succeeded',result['diagnostic'])
        tally=json.loads((self.f.dest/'TALLY.json').read_text())
        self.assertNotIn('diagnostic',tally)
        data=json.loads((self.repo/self.options['write']/'diagnosis/DIAGNOSIS.json').read_text())
        self.assertEqual(len(data['attempts']),2)
        self.assertEqual(len(data['duplicate_receipt_aliases']),1)
        self.assertEqual({r['instrument_id'] for r in data['observations']},{'EO:1','EO:2'})
        self.assertIsNone(data['effort']['complete_session_cost'])
        self.assertEqual(tally['eligible'],['EO:1'])
        self.assertEqual(tally['claims_published'],0)
        receipt=json.loads((self.f.dest/'DIAGNOSTIC.json').read_text())
        self.assertTrue(receipt['scientific_completion_unchanged'])

    def test_missing_history_refuses_diagnosis_preserves_scientific_completion(self):
        options=dict(self.options,history='research/missing.json')
        code,result=self.invoke(options)
        self.assertEqual(code,0)
        self.assertEqual(result['diagnostic']['status'],'refused')
        self.assertEqual(result['eligible'],['EO:1'])
        self.assertEqual(result['exceptions'],0)
        self.assertTrue((self.f.dest/'DIAGNOSTIC.json').is_file())

    def test_omitted_unfinished_attempt_refuses_without_affecting_completion(self):
        options=dict(self.options,research_attempt=[])
        code,result=self.invoke(options)
        self.assertEqual(code,0)
        self.assertEqual(result['diagnostic']['status'],'refused')
        self.assertIn('refusing to drop: EO:2',result['diagnostic']['stdout'])
        self.assertEqual(result['eligible'],['EO:1'])

    def test_incomplete_diagnostic_options_are_separate_refusal(self):
        code,result=self.invoke({'history':self.options['history']})
        self.assertEqual(code,0)
        self.assertEqual(result['diagnostic']['status'],'refused')
        self.assertIn('base_commit required',result['diagnostic']['error'])

    def test_diagnostic_derivatives_do_not_change_prior_context(self):
        import prior_research
        _,ds=batch.load_packet(self.f.folder,self.repo)
        before=prior_research.collect(self.repo,ds,exclude=self.f.folder)
        self.invoke(self.options)
        after=prior_research.collect(self.repo,ds,exclude=self.f.folder)
        self.assertEqual(before,after)
        # A genuine relevant review elsewhere still changes context.
        batch.dump(self.repo/'research/other/REVIEW.json',dict(self.f.review,reasons=['Relevant source review']))
        self.assertNotEqual(after,prior_research.collect(self.repo,ds,exclude=self.f.folder))


if __name__=='__main__':unittest.main()
