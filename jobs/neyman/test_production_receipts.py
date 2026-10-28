"""Adversarial accounting and evidence-boundary checks for the optional importer."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from production_receipts import Reader, canonical, source_check, union_seconds
from diagnose import diagnose, effort, main, repair_probe
from survey import OUTCOMES


class Production(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); self.reader = Reader(self.root)
        self.claims = [{'instrument_id': 'EO:1', 'schema': 'eo-lifecycle-claim/v1'},
                       {'instrument_id': 'EO:2', 'schema': 'eo-lifecycle-claim/v1'}]
        self.rows = [dict(instrument_id=c['instrument_id'], claim_sha256=canonical(c),
                         outcome='eligible', source_review_upheld=True,
                         publication_kind='whole_case', gate_errors=[]) for c in self.claims]
        self.native = dict(schema='eo-claim-kit-completion/v1', outcomes=self.rows,
                           started_utc='2026-10-25T12:00:00Z', finished_utc='2026-10-25T12:00:10Z', wall_seconds=10,
                           model_tokens=None, model_cost=None)
        self.put('run/TALLY.json', self.native)
        self.put('run/CLAIMS.selected.jsonl', self.claims, jsonl=True)
        self.replay = dict(canonical_outputs_modified=False, selected={
            c['instrument_id']: {'after': {'instrument_id': c['instrument_id'],
                'ready_for_human_review': 'no', 'blockers': 'NO_PROVISIONAL_STATUS'}} for c in self.claims})
        self.put('run/TRACKER_REPLAY.json', self.replay)
        self.selection = [dict(instrument_id=c['instrument_id'], claim_sha256=canonical(c),
                               completion='run', publication_kind='whole_case') for c in self.claims]
        self.manifest = dict(schema='neyman.production-import/1', cohort_kind='retrospective_convenience',
                             base_commit='a'*40, selection=self.put('selection.json', self.selection),
                             completion_receipts=[self.reader.ref('run/TALLY.json')])

    def put(self, name, data, jsonl=False):
        p = self.root/name; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(''.join(json.dumps(x)+'\n' for x in data) if jsonl else json.dumps(data))
        return self.reader.ref(name)

    def result(self):
        return diagnose(self.reader, self.manifest)

    def test_shared_multiorder_invocation_counted_once(self):
        s = self.result()['summary']
        self.assertEqual((s['observed_orders'], s['unique_completion_invocations']), (2, 1))
        self.assertEqual(s['completion_machine_seconds_total'], 10)
        self.assertEqual(s['diagnoses'], {'reviewed_proposal_awaits_status_adoption': 2})
        self.assertIsNone(s['total_agent_hours']); self.assertFalse(s['verified_savings'])

    def test_duplicate_copied_receipt_not_additional_attempt(self):
        ref = self.put('copy/TALLY.json', self.native)
        self.manifest['completion_receipts'].append(ref)
        r = self.result()
        self.assertEqual(len(r['duplicate_receipt_aliases']), 1)
        self.assertEqual(r['summary']['completion_machine_seconds_total'], 10)

    def test_failures_remain_in_costs(self):
        d = copy.deepcopy(self.native); d['outcomes'][0]['outcome'] = 'exception'
        d['started_utc'] = '2026-10-25T11:59:00Z'; d['finished_utc'] = '2026-10-25T11:59:20Z';d['wall_seconds'] = 20
        self.manifest['completion_receipts'].append(self.put('failed.json', d))
        r = self.result()['summary']
        self.assertEqual(r['failed_completion_invocations'], 1)
        self.assertEqual(r['completion_machine_seconds_total'], 30)

    def test_partial_eligible_is_not_whole_case(self):
        self.native['outcomes'][0].update(publication_kind='partial_research', gate_errors=['clause_0_first_end'])
        self.selection[0]['publication_kind'] = 'partial_research'
        self.manifest['selection'] = self.put('selection.json', self.selection)
        self.manifest['completion_receipts'] = [self.put('run/TALLY.json', self.native)]
        s = self.result()['summary']
        self.assertEqual(s['reviewed_whole_case_proposals'], 1)
        self.assertEqual(s['reviewed_partials'], 1)

    def test_whole_case_with_open_gates_refused(self):
        self.native['outcomes'][0]['gate_errors'] = ['missing_first_end']
        self.manifest['completion_receipts'] = [self.put('run/TALLY.json', self.native)]
        with self.assertRaisesRegex(ValueError, 'still has gate'): self.result()

    def test_changed_selected_claim_refused(self):
        self.claims[0]['new_assertion'] = True
        self.put('run/CLAIMS.selected.jsonl', self.claims, jsonl=True)
        with self.assertRaisesRegex(ValueError, 'selected claim bytes'): self.result()

    def test_changed_receipt_refused(self):
        self.put('run/TALLY.json', dict(self.native, wall_seconds=12))
        with self.assertRaisesRegex(ValueError, 'changed input'): self.result()

    def test_unselected_group_member_refused(self):
        self.manifest['selection'] = self.put('selection.json', self.selection[:1])
        with self.assertRaisesRegex(ValueError, 'unselected member'): self.result()

    def test_wrong_tracker_target_refused(self):
        self.replay['selected']['EO:1']['after']['instrument_id'] = 'EO:2'
        self.put('run/TRACKER_REPLAY.json', self.replay)
        with self.assertRaisesRegex(ValueError, 'tracker target'): self.result()

    def test_nonisolated_tracker_refused(self):
        self.replay['canonical_outputs_modified'] = True
        self.put('run/TRACKER_REPLAY.json', self.replay)
        with self.assertRaisesRegex(ValueError, 'isolated replay'): self.result()

    def test_missing_machine_measurement_not_zero(self):
        self.native['wall_seconds'] = None
        self.manifest['completion_receipts'] = [self.put('run/TALLY.json', self.native)]
        self.assertIsNone(self.result()['summary']['completion_machine_seconds_total'])

    def test_nonfinite_or_negative_measurements_refused(self):
        for value in (-1, True, float('nan'), float('inf')):
            self.manifest['completion_receipts'] = [self.put('run/TALLY.json', dict(self.native, wall_seconds=value))]
            with self.assertRaises(ValueError): self.result()

    def test_traversal_and_symlink_refused(self):
        with self.assertRaisesRegex(ValueError, 'escapes'): self.reader.path('../outside')
        (self.root/'link').symlink_to(self.root.parent)
        with self.assertRaisesRegex(ValueError, 'escapes'): self.reader.path('link/file')

    def test_duplicate_keys_refused(self):
        (self.root/'duplicate.json').write_text('{"a":1,"a":2}')
        with self.assertRaisesRegex(ValueError, 'duplicate JSON'): self.reader.value(self.reader.ref('duplicate.json'))

    def test_unknown_schema_refused(self):
        self.native['schema'] = 'another/v1'
        self.manifest['completion_receipts'] = [self.put('run/TALLY.json', self.native)]
        with self.assertRaisesRegex(ValueError, 'unsupported completion'): self.result()

    def test_censored_real_attempt_retained(self):
        self.manifest['selection'] = self.put('selection.json', [{'instrument_id': 'EO:3'}])
        self.manifest['completion_receipts'] = []
        ref = self.put('attempt.json', dict(schema='neyman.research-attempt/1', instrument_id='EO:3',
            attempt_id='producer-3', assessor='producer', question='Actual report delivery date?', outcome='censored',
            started_utc='2026-10-25T12:00:00Z', finished_utc='2026-10-25T12:10:00Z',
            basis=[self.put('evidence.json', {'unresolved': True})]))
        self.manifest['research_attempts'] = [ref]
        r = self.result()
        self.assertEqual(r['summary']['censored_orders'], 1)
        self.assertEqual(r['summary']['reviewed_whole_case_proposals'], 0)
        self.assertEqual(r['observations'][0]['diagnosis'], 'censored_research_attempt')

    def test_no_route_does_not_prove_missing_document_or_exhaustion(self):
        ref = self.put('cp.json', dict(schema='eo-source-blocked-work/v1', instrument_id='EO:1', state='source_blocked',
            reason='Actual event date not established', source_requests=[], source_results=[{'result':'no_route'}]))
        self.manifest['checkpoints'] = [ref]
        cp = self.result()['observations'][0]['source_checkpoints'][0]
        self.assertFalse(cp['exhaustion_established']);self.assertEqual(len(cp['no_route']), 1)

    def test_source_identity_span_and_adequacy_separate(self):
        (self.root/'text.txt').write_text('The event happened.')
        record = self.put('source.json', dict(instrument_id='EO:2', text_sha256=self.reader.ref('text.txt')['sha256']))
        r = source_check(self.reader, dict(instrument_id='EO:1', record=record, text=self.reader.ref('text.txt'),
                                         span={'start':0, 'end':3, 'quote':'The'}))
        self.assertIn('wrong_identity', r['states']); self.assertIn('span_exact', r['states'])
        self.assertEqual(r['proposition_adequacy'], 'requires_substantive_review')

    def test_effort_overlap_shared_cost_and_usage_dedup(self):
        def ev(key, start, end, worker='A'):
            return dict(event_id=key, phase='review', kind='worker_elapsed', worker_id=worker,
                        instrument_ids=['EO:1','EO:2'], started_utc=f'2026-10-25T12:00:{start:02d}Z',
                        finished_utc=f'2026-10-25T12:00:{end:02d}Z', coverage='partial', measurement_method='test clock intervals',
                        usage_id='usage-1', tokens={'output':20,'reasoning':5})
        events = [ev('a',0,10), ev('b',5,15), ev('c',0,10,'B')]
        ref = self.put('effort.json', {'schema':'neyman.production-effort/1','events':events})
        r = effort(self.reader, [ref, ref], {'EO:1','EO:2'})
        self.assertEqual(r['observed_seconds_by_kind']['worker_elapsed'], 25)
        self.assertEqual(r['observed_token_lower_bounds']['output'],20)
        self.assertEqual(r['observed_token_lower_bounds']['reasoning'],5)
        self.assertIsNone(r['observed_seconds_by_kind']['active'])

    def test_effort_conflicting_shared_event_refused(self):
        e = dict(event_id='a', phase='review', kind='active', worker_id='A', instrument_ids=['EO:1'],
                 started_utc='2026-10-25T12:00:00Z',finished_utc='2026-10-25T12:00:10Z',coverage='partial',measurement_method='test clock intervals')
        ref = self.put('effort.json', {'schema':'neyman.production-effort/1','events':[e,dict(e,phase='correction')]})
        with self.assertRaisesRegex(ValueError,'conflicting shared'):effort(self.reader,[ref],{'EO:1'})

    def test_repair_multiple_changes_cannot_be_single_change_success(self):
        before = copy.deepcopy(self.native)
        before.update(started_utc='2026-10-25T11:00:00Z',finished_utc='2026-10-25T11:00:10Z')
        before['outcomes'][0]['outcome'] = 'exception'
        spec = dict(instrument_id='EO:1', before=self.put('before.json',before),after=self.reader.ref('run/TALLY.json'),
                    before_dependencies=self.put('bd.json',{'a':'a'*64,'b':'b'*64}),
                    after_dependencies=self.put('ad.json',{'a':'c'*64,'b':'d'*64}))
        r = repair_probe(self.reader,spec)
        self.assertTrue(r['observed_transition']);self.assertEqual(r['result'],'inconclusive_multiple_changes')
        self.assertIsNone(r['hours_saved'])

    def test_output_refuses_existing_directory_and_protected_destination(self):
        ref = self.put('manifest.json',self.manifest)
        for dest in (self.root/'jobs/claim-kit/output/new', self.root/'already'):
            if dest.name=='already':dest.mkdir()
            self.assertEqual(main(['--repo',str(self.root),'--manifest',ref['path'],'--out',str(dest)]),2)
            self.assertFalse((dest/'DIAGNOSIS.json').exists())

    def test_cli_writes_only_new_diagnostic_directory(self):
        self.put('manifest.json',self.manifest)
        dest=self.root/'research/neyman/production-diagnostics/test/result'
        self.assertEqual(main(['--repo',str(self.root),'--manifest','manifest.json','--out',str(dest)]),0)
        self.assertEqual(set(p.name for p in dest.iterdir()),{'DIAGNOSIS.json','OBSERVATIONS.jsonl','REPORT.md'})
        self.assertEqual(self.reader.value(self.reader.ref('run/TALLY.json')),self.native)

    def test_probability_sample_keeps_nonresponse_explicit(self):
        sample=dict(sample=[{'instrument_id':i,'inclusion_probability':0.5} for i in ('EO:1','EO:2','EO:3')],
                    outcome_definitions=OUTCOMES)
        import hashlib
        sample['manifest_sha256']=hashlib.sha256(json.dumps(sample,sort_keys=True).encode()).hexdigest()
        self.manifest.update(cohort_kind='prospective_probability',sample_manifest=self.put('sample.json',sample))
        r=self.result()
        self.assertEqual(r['sample_unobserved'],['EO:3'])
        self.assertFalse(r['summary']['population_inference_supported'])

    def test_source_absent_bytes_is_local_coverage_gap(self):
        record=self.put('source.json',{'instrument_id':'EO:1','sha256':'a'*64})
        r=source_check(self.reader,dict(instrument_id='EO:1',record=record,raw={'path':'absent.pdf','sha256':'a'*64}))
        self.assertIn('raw_bytes_unavailable_in_checkout',r['states'])
        self.assertIsNone(self.reader.pins['absent.pdf'])

    def test_unknown_identity_is_not_wrong_identity(self):
        r=source_check(self.reader,dict(instrument_id='EO:1',record=self.put('s.json',{})))
        self.assertIn('identity_not_recorded',r['states']);self.assertNotIn('wrong_identity',r['states'])

    def test_timezone_and_reversed_intervals_refused(self):
        for start,end in [('2026-10-25T12:00:00','2026-10-25T12:00:10'),
                          ('2026-10-25T12:00:10Z','2026-10-25T12:00:00Z')]:
            self.manifest['completion_receipts']=[self.put('run/TALLY.json',dict(self.native,started_utc=start,finished_utc=end))]
            with self.assertRaises(ValueError):self.result()


class RealPR60(unittest.TestCase):
    @unittest.skipUnless((Path(__file__).resolve().parents[2]/'research/neyman/production-diagnostics/2026-10-25-pr60/IMPORT.json').is_file(),
                         'requires pinned PR60 research metadata')
    def test_native_cohort_and_shared_runtime(self):
        root=Path(__file__).resolve().parents[2];reader=Reader(root)
        path='research/neyman/production-diagnostics/2026-10-25-pr60/IMPORT.json'
        r=diagnose(reader,reader.value(reader.ref(path)));s=r['summary']
        self.assertEqual((s['observed_orders'],s['unique_completion_invocations'],s['failed_completion_invocations']),(9,13,3))
        self.assertEqual((s['reviewed_whole_case_proposals'],s['reviewed_partials'],s['ready_in_isolated_replay']),(8,1,2))
        self.assertAlmostEqual(s['completion_machine_seconds_total'],451.3040604580001)
        self.assertEqual(s['diagnoses']['reviewed_proposal_awaits_status_adoption'],6)
        self.assertEqual(s['diagnoses']['documented_unresolved_evidence_or_application'],1)
        self.assertEqual(r['repair_probes'][0]['result'],'inconclusive_multiple_changes')
        self.assertIsNone(s['net_hours_saved'])


if __name__ == '__main__':
    unittest.main()
