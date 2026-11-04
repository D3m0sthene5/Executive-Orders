#!/usr/bin/env python3
"""Bounded LF/CRLF synthetic fixture review; runtime and prior receipts are read-only."""
import argparse,hashlib,io,json,socket,sys,time,unittest
from pathlib import Path
from unittest.mock import patch
sys.dont_write_bytecode=True
ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,default=Path('/workspace/scratch/4fcab884091a/eo-maitland'));ap.add_argument('--output',type=Path);args=ap.parse_args();repo=args.repo.resolve()
receipt_dir=repo/'research/progress/maitland/engineering-review';prior_path=receipt_dir/'FINAL_REVIEW.json';combined_path=receipt_dir/'COMBINED_REVIEW.json';prior=json.loads(prior_path.read_text());combined=json.loads(combined_path.read_text());changed_test='jobs/claim-kit/test_provision_history.py';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before={p:sha(repo/p) for p in prior['hashes']};checks=[];started=time.monotonic()
for path,digest in prior['hashes'].items():
    if path!=changed_test:assert before[path]==digest,path
sys.path.insert(0,str(repo/'jobs/claim-kit'))
import test_provision_history as T
import provision_history as H

def probe(name,fn):
    try:
        with patch.object(socket,'socket',side_effect=AssertionError('network forbidden')),patch.object(socket,'create_connection',side_effect=AssertionError('network forbidden')):fn()
        checks.append({'name':name,'passed':True})
    except Exception as exc:checks.append({'name':name,'passed':False,'error':type(exc).__name__+': '+str(exc)})

def stable_lf():
    t=T.ProvisionHistoryTests()
    try:
        with patch.object(Path,'write_text',side_effect=AssertionError('fixture source must not use platform newline translation')):t.setUp()
        source=t.bundle['provisions'][0]['source'];raw=(t.repo/source['text_path']).read_bytes();assert raw==b'HEADER\nThe board shall use red ink.\nFOOTER';assert source['char_start']==7 and raw.decode('utf-8')[source['char_start']:source['char_end']]==source['quote'];assert source['text_sha256']==hashlib.sha256(raw).hexdigest()
    finally:t.doCleanups()
probe('source_fixture_writes_explicit_lf_bytes_without_text_translation',stable_lf)

def exact_crlf_unicode():
    t=T.ProvisionHistoryTests();t.setUp()
    try:
        record=t.bundle['provisions'][0];record['norm_text']='The board shall use blå ink.';source=record['source'];source['quote']=record['norm_text'];raw=('HEADER\r\n'+record['norm_text']+'\r\nFOOTER').encode('utf-8');(t.repo/source['text_path']).write_bytes(raw);source['text_sha256']=hashlib.sha256(raw).hexdigest();source['char_start']=7;source['char_end']=7+len(record['norm_text']);t.write()
        try:H.load(t.repo,t.bundle_path)
        except ValueError as exc:assert 'source_span_mismatch' in str(exc)
        else:raise AssertionError('normalized LF offset incorrectly accepted for CRLF bytes')
        source['char_start']=8;source['char_end']=8+len(record['norm_text']);t.write();out=H.query(t.repo,t.bundle_path,t.pid,'2025-01-01');assert out['text_version']['text']==record['norm_text'];assert out['dependencies']['source:'+source['text_path']]==hashlib.sha256(raw).hexdigest();assert len(raw)>len(raw.decode('utf-8'));assert source['char_end']!=8+len(record['norm_text'].encode('utf-8'))
    finally:t.doCleanups()
probe('crlf_unicode_witness_refuses_wrong_character_offset_and_accepts_exact_one',exact_crlf_unicode)
stream=io.StringIO();native=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.TestSuite([T.ProvisionHistoryTests('test_crlf_witness_requires_exact_unnormalized_span')]))
after={p:sha(repo/p) for p in prior['hashes']};assert before==after,'reviewed files changed during bounded replay';checks.append({'name':'all_prior_runtime_pins_identical_only_test_file_pin_superseded','passed':True,'unchanged_prior_pins':len(before)-1})
report={'schema':'eo-maitland-fixture-portability-engineering-review/v1','reviewer':'dispatch_audit','verdict':'approve' if all(c['passed'] for c in checks) and native.wasSuccessful() else 'repair_required','model_family':'OpenAI','model_id':'inherited exact identifier unavailable','model_tokens':None,'cash_cost':None,'scope':'Only test_provision_history.py fixture newline portability; no runtime repair or scientific source verdict.','reported_hosted_failure':{'provenance':'coordinator-provided failure context; not independently browsed','platform':'Windows','job_id':'126464041905','commit_prefix':'a42b7997','cause':'write_text newline translation changed LF fixture prefix to CRLF while fixed character start remained7'},'superseded_pin':{'path':changed_test,'old_sha256':prior['hashes'][changed_test],'new_sha256':after[changed_test],'scope':'Test-file identity only; historical receipts remain intact.'},'runtime_pin_sha256':{p:v for p,v in after.items() if p!=changed_test},'prior_review_references':[{'path':str(prior_path.relative_to(repo)),'sha256':sha(prior_path),'status':'Only old test_provision_history.py pin superseded; runtime review unchanged.'},{'path':str(combined_path.relative_to(repo)),'sha256':sha(combined_path),'status':'Only old test fixture pin superseded; merged runtime compatibility verdict unchanged. Prior combined test executions used the earlier fixture.'}],'probes':checks,'native_regression':{'tests_run':native.testsRun,'failures':len(native.failures),'errors':len(native.errors),'skips':len(native.skipped),'log':stream.getvalue()},'script_sha256':sha(Path(__file__)),'wall_seconds':round(time.monotonic()-started,6),'findings':[],'limits':['Linux review with explicitly constructed LF/CRLF byte witnesses; no claim of executing this reviewer’s probes on Windows.','Only the new native CRLF regression was run; no full suite repeated. Coordinator owns full-suite and hosted reruns.','Exact raw-byte hashing and decoded Unicode character indexing remain intact; no line-ending normalization was added to runtime.','No blind/source-production artifacts, production jobs, canonical outputs, runtime files or GitHub state were accessed or changed by this bounded review.']}
out=args.output or receipt_dir/'FIXTURE_PORTABILITY_REVIEW.json';assert not out.exists(),'refusing overwrite of additive fixture review';out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'path':str(out),'sha256':sha(out),'verdict':report['verdict'],'probes':len(checks),'native_tests':native.testsRun,'new_test_sha256':after[changed_test]}));sys.exit(report['verdict']!='approve')
