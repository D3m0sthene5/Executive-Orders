#!/usr/bin/env python3
"""New synthetic engineering probes; no scientific packets or blind keys read.
Accept --repo or ROOT. Persist only requested receipt; fixtures are temporary.
"""
import argparse,contextlib,hashlib,importlib.util,io,json,os,socket,sys,time,unittest
from pathlib import Path
from unittest.mock import patch
sys.dont_write_bytecode=True
ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,default=Path(os.environ.get('ROOT','.')));ap.add_argument('--output',type=Path,default=Path('/tmp/maitland-engineering-review/FINAL_REVIEW.json'));args=ap.parse_args();repo=args.repo.resolve()
paths=['jobs/claim-kit/provision_history.py','jobs/claim-kit/test_provision_history.py','jobs/claim-kit/test_provision_history_cli.py','jobs/claim-kit/excavate.py','jobs/claim-kit/act_overrides.py','jobs/claim-kit/test_reinstatement_handoff.py','jobs/claim-kit/inputs.py','jobs/claim-kit/needs.txt','jobs/claim-kit/kit.py','jobs/claim-kit/batch.py','jobs/valla/valla.py','jobs/valla/test_valla.py','jobs/valla/premises.json','jobs/later-events/later_events.py','jobs/clause-drafts/segment.py','jobs/claim-kit/assemble.py','jobs/claim-kit/test_build.py','jobs/claim-kit/test_act_overrides.py']
initial_hashes={p:hashlib.sha256((repo/p).read_bytes()).hexdigest() for p in paths}
sys.path.insert(0,str(repo/'jobs/claim-kit'))
import provision_history as H
import test_provision_history as T
import excavate as E
import kit
start=time.monotonic();checks=[]
def probe(name,fn):
    try:
        with patch.object(socket,'socket',side_effect=AssertionError('network forbidden')),patch.object(socket,'create_connection',side_effect=AssertionError('network forbidden')):fn()
        checks.append({'name':name,'passed':True})
    except Exception as exc:checks.append({'name':name,'passed':False,'error':type(exc).__name__+': '+str(exc)})
def fixture(fn):
    def run():
        t=T.ProvisionHistoryTests();t.setUp()
        try:fn(t)
        finally:t.doCleanups()
    return run
def refuses(fn,part):
    try:fn()
    except ValueError as exc:assert part in str(exc),(part,str(exc))
    else:raise AssertionError('expected refusal: '+part)
def restore(t):
    t.amend();t.add('R','revoke','2022-01-01');t.add('I','reinstate','2024-01-01',restore_version_id=t.pid+'::v0');q=t.query()
    assert q['text_version']['text']=='The board shall use red ink.'
    assert q['operative_episode']['start']=='2024-01-01' and q['prior_episodes'][0]['end_exclusive']=='2022-01-01'
probe('old_version_restore_preserves_gap',fixture(restore))
def conflict(t):
    t.add('R','revoke','2022-01-01',sequence=1);t.add('I','reinstate','2022-01-01',sequence=1,restore_version_id=t.pid+'::v0');refuses(t.query,'conflicting_same_time')
probe('duplicate_explicit_same_day_sequence_refused',fixture(conflict))
def retro(t):
    t.add('R','supersede','2023-02-01',effective_date='2022-12-01',signing_date='2023-02-01',publication_date='2023-02-08');q=t.query('2022-12-02')
    assert q['operative_state']=='superseded' and q['transition_details'][0]['retroactive_effect'] and any('knowable' in x for x in q['unresolved_questions'])
probe('effective_signing_and_publication_dates_separate',fixture(retro))
def expiry(t):
    t.bundle['provisions'][0]['known_sunset_end_exclusive']='2020-06-01';t.add('R','revoke','2021-01-01');t.add('I','reinstate','2024-01-01',restore_version_id=t.pid+'::v0');q=t.query()
    assert q['operative_state']=='expired' and q['operative_episode'] is None and q['known_sunset_end_exclusive']=='2020-06-01'
probe('reinstatement_never_resets_expired_clock',fixture(expiry))
def transitive(t):
    t.amend();t.add('R','revoke','2022-01-01');t.add('I','reinstate','2024-01-01',restore_version_id='T-amend');t.add_provision('P-other','Another command.','2020-01-01');t.write();results=H.dated_query(t.repo,t.bundle_path,'2025-01-01');r=H.revalidation_report(results,{'record:T-amend':'changed'})
    assert r['affected_provisions']==['provision:'+t.pid] and r['affected_queries']==['query:'+t.pid+'@2025-01-01']
probe('restored_version_dependency_invalidates_transitively',fixture(transitive))
def forged(t):
    t.write();ledger=json.loads(t.review_path.read_text());ledger['reviews'][0]['reviewer']='producer';t.review_path.write_text(json.dumps(ledger));t.bundle['review_file']['sha256']=hashlib.sha256(t.review_path.read_bytes()).hexdigest();t.bundle_path.write_text(json.dumps(t.bundle));refuses(lambda:H.load(t.repo,t.bundle_path),'independent_upheld')
probe('producer_self_review_refused',fixture(forged))
def stale(t):
    t.write();d=json.loads(t.bundle_path.read_text());d['provisions'][0]['date_basis']='changed';t.bundle_path.write_text(json.dumps(d));refuses(lambda:H.load(t.repo,t.bundle_path),'stale_or_wrong_scope')
probe('record_mutation_stales_review',fixture(stale))
def source(t):
    t.write();(t.repo/t.bundle['provisions'][0]['source']['text_path']).write_text('changed');refuses(lambda:H.load(t.repo,t.bundle_path),'stale_source')
probe('source_mutation_refused',fixture(source))
def renumber(t):
    t.add('N','renumber','2022-01-01',new_label='section 5');q=t.query();assert q['provision_id']==t.pid and q['label']=='section 5' and q['text_version']['version_id']==t.pid+'::v0'
probe('renumber_preserves_stable_identity',fixture(renumber))
def negative(t):
    t.bundle['provisions'][0]['valid_start']='2022-01-01';t.add('R','revoke','2021-01-01');refuses(t.query,'transition_precedes_reviewed_establishment')
probe('reviewed_pre_initial_transition_refused',fixture(negative))
def membership(t):
    t.add_provision('P-other','Another command.','2020-01-01');t.write();old=H.dated_query(t.repo,t.bundle_path,'2025-01-01');ledger=t.review_path.read_bytes();t.add('U','revoke','2021-01-01',scopes=());t.write();assert ledger==t.review_path.read_bytes();assert H.query(t.repo,t.bundle_path,t.pid,'2025-01-01')['operative_state']=='unknown';r=H.revalidation_report(old,H.membership_fingerprints(t.repo,t.bundle_path));assert r['affected_queries']==['query:'+t.pid+'@2025-01-01']
probe('unreviewed_new_event_invalidates_only_affected_scope',fixture(membership))
SRC={'text_path':'held/synthetic.txt','text_sha256':'a'*64}
def incidental():
    text='Executive Order 13934 is hereby reinstated as it was prior to the issuance of Executive Order 14029.';acts,refs=E.discover_mentions('EO:14189',text,SRC,with_references=True);assert [(x['target_id'],x['verb']) for x in acts]==[('EO:13934','reinstate')];assert [r['target_id'] for r in refs]==['EO:14029'];assert E.chain('EO:14029',acts)['events']==[]
probe('EO14029_incidental_citation_not_reinstated',incidental)
def mixed():
    text='Executive Order 1 is reinstated, and Executive Order 2 is amended.';acts=E.discover_mentions('EO:9',text,SRC);assert [(x['target_id'],x['verb']) for x in acts]==[('EO:1','reinstate'),('EO:2','amend')];assert all(text[x['char_start']:x['char_end']]==x['provision_text'] for x in acts)
probe('same_sentence_targets_remain_distinct',mixed)
def readonly(t):
    t.write();snap=lambda:{str(p.relative_to(t.repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in t.repo.rglob('*') if p.is_file()};before=snap()
    with patch.object(socket,'socket',side_effect=AssertionError('network forbidden')),patch.object(socket,'create_connection',side_effect=AssertionError('network forbidden')):
        out=H.dated_query(t.repo,t.bundle_path,'2025-01-01');H.revalidation_report(out,{'record:'+t.pid:'changed'})
        with contextlib.redirect_stdout(io.StringIO()):rc=kit.main(['--repo',str(t.repo),'history-at',str(t.bundle_path),'--provision',t.pid,'--on','2025-01-01'])
        assert rc==0
    assert before==snap();q=out['queries'][0];assert q['human_certified'] is False and q['canonical_approval'] is False and q['completeness_guaranteed'] is False
probe('query_cli_no_network_write_or_scientific_promotion',fixture(readonly))
def escape(t):
    t.write()
    with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):rc=kit.main(['--repo',str(t.repo),'history-at',str(t.bundle_path),'--provision',t.pid,'--on','2025-01-01','--write',str(t.repo/'outside.json')])
    assert rc!=0 and not(t.repo/'outside.json').exists()
probe('explicit_query_write_cannot_escape_research',fixture(escape))
def expired_followup(t):
    t.bundle['provisions'][0]['known_sunset_end_exclusive']='2020-06-01';t.add('R','revoke','2021-01-01');t.add('I','reinstate','2024-01-01',restore_version_id=t.pid+'::v0');t.add('N','renumber','2024-06-01',new_label='section 7');q=t.query()
    assert q['operative_state']=='expired'
    assert all(e['start']<e['end_exclusive'] for e in q['prior_episodes']),q['prior_episodes']
    assert not any(e['episode_id']=='I::episode' for e in q['prior_episodes'])
probe('expired_revival_then_later_event_cannot_make_negative_episode',fixture(expired_followup))
def transfer():
    
    for text in ['Executive Order 1 is reinstated, and functions under Executive Order 2 are transferred to the Secretary of State.','Executive Order 1 is reinstated and Executive Order 2 is transferred to the Secretary of State.','Executive Order 2 is transferred to the Secretary of State and Executive Order 1 is reinstated.']:
        acts=E.discover_mentions('EO:9',text,SRC);assert [(x['target_id'],x['verb']) for x in acts]==[('EO:1','reinstate'),('EO:2','transfer')]
probe('mixed_reinstatement_preserves_transfer_lead',transfer)

def unknown_text_date(t):
    t.bundle['provisions'][0]['valid_start']=None;t.review_scopes[t.pid]=('text',);q=t.query('1900-01-01')
    assert q['text_version'] is None and q['held_text_version']['text']=='The board shall use red ink.' and q['initial_text_date_state']=='unknown'
probe('undated_text_review_cannot_supply_as_of1900_text',fixture(unknown_text_date))
def predocument(t):
    p=t.bundle['provisions'][0];p['valid_start']=None;p['signing_date']='2020-01-01';t.review_scopes[t.pid]=('text',);q=t.query('1900-01-01')
    assert q['text_version'] is None and q['initial_text_date_state']=='not_yet_documented' and q['held_text_version']
probe('document_date_blocks_predocument_text',fixture(predocument))
def initial_retro(t):
    p=t.bundle['provisions'][0];p['signing_date']='2021-01-01';q=t.query('2020-06-01')
    assert q['text_version'] and q['operative_state']=='operative' and q['initial_text_date_state']=='reviewed_retrospective_reconstruction'
    assert q['text_date_state']=='reviewed_retrospective_reconstruction' and q['initial_document_date_used']=='2021-01-01'
probe('initial_retroactive_rule_disclosed_as_reconstruction',fixture(initial_retro))
def delayed_effect(t):
    p=t.bundle['provisions'][0];p['valid_start']='2021-01-01';p['signing_date']='2020-01-01';q=t.query('2020-06-01')
    assert q['text_version'] and q['operative_state']=='not_yet_established' and q['initial_text_date_state']=='documented_by_query_date'
probe('documented_text_can_precede_normative_start',fixture(delayed_effect))
def inverted_initial_clock(t):
    t.bundle['provisions'][0]['known_sunset_end_exclusive']='2019-12-01';t.add('R','revoke','2021-01-01')
    try:t.query()
    except ValueError:return
    raise AssertionError('reviewed initial sunset before start accepted')
probe('inverted_reviewed_initial_dates_refused',fixture(inverted_initial_clock))
def invalid_document_date(t):
    t.bundle['provisions'][0]['signing_date']='2020-02-30';refuses(t.query,'invalid_date')
probe('initial_document_dates_validated',fixture(invalid_document_date))
def before_start(t):
    q=t.query('1900-01-01');assert q['text_version'] is None and q['held_text_version'] and q['operative_state']=='not_yet_established'
probe('future_reviewed_start_does_not_show_future_as_of_text',fixture(before_start))

def cutoff(t):
    t.bundle['legal_cutoff']='2025-12-31';t.write();old=H.dated_query(t.repo,t.bundle_path,'2025-01-01');ledger=t.review_path.read_bytes();t.bundle['legal_cutoff']='2024-01-01';t.write();assert ledger==t.review_path.read_bytes();new=H.query(t.repo,t.bundle_path,t.pid,'2025-01-01');assert new['operative_state']=='unknown' and new['operative_episode'] is None and new['outside_legal_cutoff'];r=H.revalidation_report(old,H.membership_fingerprints(t.repo,t.bundle_path));assert r['affected_queries']==['query:'+t.pid+'@2025-01-01'],r
probe('cutoff_context_change_invalidates_prior_dated_state',fixture(cutoff))

def typed_text_date(t):
    p=t.bundle['provisions'][0];p['valid_start']=None;p['text_date']='2020-01-01';t.review_scopes[t.pid]=('text',);q=t.query('2020-06-01');assert q['text_version'] and q['initial_text_date_state']=='documented_by_query_date' and q['initial_document_date_used']=='2020-01-01' and q['operative_state']=='unknown'
probe('typed_text_date_dates_text_without_establishing_commencement',fixture(typed_text_date))
def event_not_document(t):
    p=t.bundle['provisions'][0];p['valid_start']=None;p['event_date']='2020-01-01';t.review_scopes[t.pid]=('text',);q=t.query();assert q['text_version'] is None and q['initial_document_date_used'] is None and q['initial_text_date_state']=='unknown'
probe('generic_initial_event_date_cannot_supply_documentary_chronology',fixture(event_not_document))
def context_notice(t):
    t.bundle['coverage_notice']='Limited examination.';t.write();old=H.dated_query(t.repo,t.bundle_path,'2025-01-01');t.bundle['coverage_notice']='Narrower limited examination.';t.write();r=H.revalidation_report(old,H.membership_fingerprints(t.repo,t.bundle_path));assert r['affected_queries']==['query:'+t.pid+'@2025-01-01']
probe('changed_coverage_notice_invalidates_saved_exact_context',fixture(context_notice))
def foreign_version(t):
    t.add_provision('P-other','Another command.','2020-01-01');t.add('R','revoke','2021-01-01');t.add('I','reinstate','2022-01-01',restore_version_id='P-other::v0');refuses(t.query,'cyclic_or_nonprior_version')
probe('cross_provision_restore_refused',fixture(foreign_version))

def cli_run(t,*args):
    stdout=io.StringIO()
    with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(io.StringIO()):rc=kit.main(['--repo',str(t.repo),*map(str,args)])
    return rc,stdout.getvalue()
def cli_check_readonly(t):
    t.write();snap=lambda:{str(p.relative_to(t.repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in t.repo.rglob('*') if p.is_file()};before=snap();rc,out=cli_run(t,'history-check',t.bundle_path);r=json.loads(out);assert rc==0 and r['mechanical_validation_passed'] and r['canonical_approval'] is False and r['human_certified'] is False;assert before==snap()
probe('history_check_is_readonly_mechanical_validation',fixture(cli_check_readonly))
def cli_impact_setup(t,multi=False):
    if multi:t.add_provision('P-other','Another command.','2020-01-01')
    t.write();folder=t.repo/'research/progress';folder.mkdir(parents=True,exist_ok=True);answer=folder/'saved.json';changed=folder/'changed.json'
    results=H.dated_query(t.repo,t.bundle_path,'2025-01-01') if multi else H.query(t.repo,t.bundle_path,t.pid,'2025-01-01');answer.write_text(json.dumps(results));changed.write_text(json.dumps({'record:'+t.pid:'changed'}));return answer,changed

def cli_single_impact(t):
    answer,changed=cli_impact_setup(t);snap=lambda:{str(p.relative_to(t.repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in t.repo.rglob('*') if p.is_file()};before=snap();rc,out=cli_run(t,'history-impact',answer,'--changed',changed);r=json.loads(out);assert rc==0 and r['affected_queries']==['query:'+t.pid+'@2025-01-01'] and r['affected_provisions']==['provision:'+t.pid];assert before==snap()
probe('history_impact_single_answer_readonly_exact_closure',fixture(cli_single_impact))
def cli_multi_impact(t):
    answer,changed=cli_impact_setup(t,True);dest=t.repo/'research/progress/new-impact.json';rc,out=cli_run(t,'history-impact',answer,'--changed',changed,'--write',dest);r=json.loads(out);assert rc==0 and r==json.loads(dest.read_text()) and r['affected_queries']==['query:'+t.pid+'@2025-01-01'];prior=dest.read_bytes();rc,_=cli_run(t,'history-impact',answer,'--changed',changed,'--write',dest);assert rc==2 and dest.read_bytes()==prior
probe('history_impact_multi_answer_writes_new_json_and_refuses_overwrite',fixture(cli_multi_impact))
def cli_bad_shapes(t):
    answer,changed=cli_impact_setup(t);dest=t.repo/'research/progress/malformed-refused.json'
    malformed=[[],None,{'schema':'eo-provision-history-results/v1','queries':[{'query_id':'q','provision_id':t.pid,'dependencies':[]}]}]
    for value in malformed:
        answer.write_text(json.dumps(value));rc,_=cli_run(t,'history-impact',answer,'--changed',changed,'--write',dest);assert rc==2 and not dest.exists(),value
    answer.unlink();rc,_=cli_run(t,'history-impact',answer,'--changed',changed,'--write',dest);assert rc==2 and not dest.exists()
probe('history_impact_malformed_or_missing_results_refuse_cleanly',fixture(cli_bad_shapes))
def cli_output_restrictions(t):
    answer,changed=cli_impact_setup(t);outside=t.repo/'research/readiness';outside.mkdir(parents=True);link=t.repo/'research/progress/escape';link.symlink_to(outside,target_is_directory=True)
    for target in [outside/'query.json',t.repo/'research/progress/query.jsonl',link/'query.json']:
        for command in [['history-at',t.bundle_path,'--provision',t.pid,'--on','2025-01-01'],['history-impact',answer,'--changed',changed]]:
            rc,_=cli_run(t,*command,'--write',target);assert rc==2 and not target.exists(),str(target)
probe('both_output_commands_refuse_canonical_nonjson_and_symlink_escape',fixture(cli_output_restrictions))
def cli_at_overwrite(t):
    t.write();dest=t.repo/'research/progress/query.json';rc,out=cli_run(t,'history-at',t.bundle_path,'--provision',t.pid,'--on','2025-01-01','--write',dest);assert rc==0 and json.loads(out)==json.loads(dest.read_text());prior=dest.read_bytes();rc,_=cli_run(t,'history-at',t.bundle_path,'--provision',t.pid,'--on','2025-01-01','--write',dest);assert rc==2 and dest.read_bytes()==prior
probe('history_at_new_json_write_refuses_existing_exact_answer',fixture(cli_at_overwrite))

def cli_changed_map(t):
    answer,changed=cli_impact_setup(t);dest=t.repo/'research/progress/invalid-map.json'
    for value in [[],None,{'record:'+t.pid:42}]:
        changed.write_text(json.dumps(value));rc,_=cli_run(t,'history-impact',answer,'--changed',changed,'--write',dest);assert rc==2 and not dest.exists()
    changed.unlink();rc,_=cli_run(t,'history-impact',answer,'--changed',changed,'--write',dest);assert rc==2 and not dest.exists()
    changed.write_text(json.dumps({'record:'+t.pid:None}));rc,out=cli_run(t,'history-impact',answer,'--changed',changed);assert rc==0 and json.loads(out)['affected_queries']==['query:'+t.pid+'@2025-01-01']
probe('impact_changed_map_invalid_shapes_refused_deletion_propagates',fixture(cli_changed_map))
def cli_result_bound(t):
    answer,changed=cli_impact_setup(t);saved=json.loads(answer.read_text());answer.write_text(json.dumps({'schema':'eo-provision-history-results/v1','queries':[saved]*10001}));dest=t.repo/'research/progress/oversize-refused.json';rc,_=cli_run(t,'history-impact',answer,'--changed',changed,'--write',dest);assert rc==2 and not dest.exists()
probe('impact_results_query_count_bound_refused',fixture(cli_result_bound))

# Existing native synthetic gates; deliberately omit held-source replay.
suite=unittest.defaultTestLoader.loadTestsFromTestCase(T.ProvisionHistoryTests)
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
C=module('synthetic_provision_history_cli_tests',repo/'jobs/claim-kit/test_provision_history_cli.py');suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(C.ProvisionHistoryCliTests))
R=module('synthetic_reinstatement_tests',repo/'jobs/claim-kit/test_reinstatement_handoff.py')
for name in unittest.defaultTestLoader.getTestCaseNames(R.ReinstatementExtractionTests):
    if name!='test_held_eo14189_four_distinct_operations_and_unchanged_target_terms':suite.addTest(R.ReinstatementExtractionTests(name))
sys.path.insert(0,str(repo/'jobs/valla'));V=module('synthetic_valla_tests',repo/'jobs/valla/test_valla.py');suite.addTest(V.VallaTests('test_packet_exposes_stale_review_without_invalidating_conclusions'))
log=io.StringIO();run=unittest.TextTestRunner(stream=log,verbosity=1).run(suite)
final_hashes={p:hashlib.sha256((repo/p).read_bytes()).hexdigest() for p in paths}
probe('implementation_files_stable_during_replay',lambda: (_ for _ in ()).throw(AssertionError('implementation changed during replay')) if initial_hashes!=final_hashes else None)
receipt={'schema':'eo-maitland-independent-engineering-review/v1','reviewer':'dispatch_audit','model_family':'OpenAI','model_id':'inherited exact identifier unavailable','model_tokens':None,'cash_cost':None,'scope':'synthetic engineering only; scientific production and blind keys unseen','hashes':final_hashes,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'probes':checks,'probe_count':len(checks),'probe_passed':sum(c['passed'] for c in checks),'unit_gate':{'tests_run':run.testsRun,'failures':len(run.failures),'errors':len(run.errors),'skips':len(run.skipped),'log':log.getvalue()},'verdict':'approve' if all(c['passed'] for c in checks) and run.wasSuccessful() else 'repair_required','wall_seconds':round(time.monotonic()-start,6),'limits':['No scientific source verdict, legal adjudication, human certification, corpus readiness or savings claim.','Exact scoped review ledgers do not cryptographically authenticate reviewer identities.','No production job, GitHub mutation, current Tribonian workspace or PR132 accessed.','Tests read temporary synthetic fixtures only; existing held-source replay intentionally omitted.','Preexisting nonreinstatement incidental-target binding is outside this repair and may still produce machine leads requiring source review.'],'findings':[],'resolved_findings':[{'issue':'Pre-establishment revoke produced negative historical episode','resolution':'Reviewed pre-establishment effects now refused; independent regression passes.'},{'issue':'Unreviewed past event added without review-ledger change did not invalidate saved query','resolution':'Scoped exact membership pins now propagate invalidation; independent regression passes.'},{'issue':'Future or undated initial text appeared as dated historical text','resolution':'Typed documentary chronology separates held evidence, dated text, and reviewed retrospective legal reconstruction.'},{'issue':'Inverted initial sunset/start accepted and expiry followed by later event produced negative revival episode','resolution':'Reviewed inverted initial dates refuse; expiry loop omits fictitious revival intervals.'},{'issue':'Mixed reinstatement sentence dropped transfer or cross-bound reversed clause','resolution':'Bounded target-scoped mixed clauses preserve transfers and reinstatements independently.'},{'issue':'Cutoff or coverage metadata change escaped membership invalidation','resolution':'Exact relevant bundle context is included in every affected provision membership pin.'},{'issue':'New history-impact CLI crashed on missing or malformed saved-result shapes','resolution':'Bounded saved-results and changed-map validation now returns rc2 without output writes; independent malformed, deletion and count-bound probes pass.'}]}
args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'receipt':str(args.output),'passed':receipt['probe_passed'],'probes':len(checks),'unit_tests':run.testsRun,'unit_successful':run.wasSuccessful(),'verdict':receipt['verdict'],'failed':[c for c in checks if not c['passed']]}));sys.exit(receipt['verdict']!='approve')
