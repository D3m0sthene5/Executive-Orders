#!/usr/bin/env python3
"""Bounded Windows-style fixture-path serialization probe; no runtime mutations."""
import argparse,hashlib,json,socket,sys,time
from pathlib import Path,PureWindowsPath
from unittest.mock import patch
sys.dont_write_bytecode=True
ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,default=Path('/workspace/scratch/4fcab884091a/eo-maitland'));ap.add_argument('--output',type=Path);a=ap.parse_args();repo=a.repo.resolve();folder=repo/'research/progress/maitland/engineering-review';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();prior_path=folder/'FINAL_REVIEW.json';portability_path=folder/'FIXTURE_PORTABILITY_REVIEW.json';combined_path=folder/'COMBINED_REVIEW.json';prior=json.loads(prior_path.read_text());portability=json.loads(portability_path.read_text());test='jobs/claim-kit/test_provision_history.py';before={p:sha(repo/p) for p in prior['hashes']};started=time.monotonic();checks=[]
for p,v in prior['hashes'].items():
    if p!=test:assert before[p]==v,p
source=(repo/test).read_bytes();old_expression=b'str(self.review_path.relative_to(self.repo))';new_expression=b'self.review_path.relative_to(self.repo).as_posix()';assert source.count(new_expression)==1;assert hashlib.sha256(source.replace(new_expression,old_expression,1)).hexdigest()==portability['superseded_pin']['new_sha256'];checks.append({'name':'sole_test_change_is_portable_review_file_path_serialization','passed':True})
sys.path.insert(0,str(repo/'jobs/claim-kit'))
import test_provision_history as T
import provision_history as H
class WindowsRelativePathProxy:
    def __init__(self,path):self.path=path
    def relative_to(self,other):return PureWindowsPath(self.path.relative_to(other).as_posix())
    def write_text(self,*args,**kwargs):return self.path.write_text(*args,**kwargs)
    def read_bytes(self):return self.path.read_bytes()

def probe(name,fn):
    try:
        with patch.object(socket,'socket',side_effect=AssertionError('network forbidden')),patch.object(socket,'create_connection',side_effect=AssertionError('network forbidden')):fn()
        checks.append({'name':name,'passed':True})
    except Exception as exc:checks.append({'name':name,'passed':False,'error':type(exc).__name__+': '+str(exc)})
def windows_serialization():
    t=T.ProvisionHistoryTests();t.setUp()
    try:
        real_review=t.review_path;t.review_path=WindowsRelativePathProxy(real_review);assert str(t.review_path.relative_to(t.repo))=='research\\review\\REVIEW.json';t.write();assert t.bundle['review_file']['path']=='research/review/REVIEW.json';assert t.bundle['review_file']['sha256']==sha(real_review);assert H.query(t.repo,t.bundle_path,t.pid,'2025-01-01')['text_version']['text']==t.bundle['provisions'][0]['norm_text']
        t.bundle['review_file']['path']=str(t.review_path.relative_to(t.repo));t.bundle_path.write_text(json.dumps(t.bundle),encoding='utf-8')
        try:H.load(t.repo,t.bundle_path)
        except ValueError as exc:assert 'independent_review_file_required' in str(exc)
        else:raise AssertionError('runtime portable-path guard unexpectedly weakened')
    finally:t.doCleanups()
probe('windows_relative_path_serializes_portably_and_old_backslash_path_refuses',windows_serialization)
def exact_bytes_preserved():
    t=T.ProvisionHistoryTests();t.setUp()
    try:
        t.write();p=t.bundle['provisions'][0];source=p['source'];raw=(t.repo/source['text_path']).read_bytes();assert raw==('HEADER\n'+p['norm_text']+'\nFOOTER').encode('utf-8');assert raw.decode('utf-8')[source['char_start']:source['char_end']]==source['quote'];assert source['text_sha256']==hashlib.sha256(raw).hexdigest();assert t.bundle['review_file']['path']=='research/review/REVIEW.json';H.load(t.repo,t.bundle_path)
    finally:t.doCleanups()
probe('prior_exact_lf_fixture_and_review_byte_hashes_remain_valid',exact_bytes_preserved)
after={p:sha(repo/p) for p in prior['hashes']};assert before==after,'reviewed pins changed during bounded replay';checks.append({'name':'all_other_prior_17_pins_unchanged','passed':True,'count':len(after)-1})
report={'schema':'eo-maitland-fixture-path-engineering-review/v1','reviewer':'dispatch_audit','verdict':'approve' if all(c['passed'] for c in checks) else 'repair_required','model_family':'OpenAI','model_id':'inherited exact identifier unavailable','model_tokens':None,'cash_cost':None,'scope':'Only portable fixture review-file path serialization; source and runtime guards unchanged.','reported_hosted_failure':{'provenance':'coordinator-provided failure context; not independently browsed','platform':'Windows','job_id':'126466523538','commit_prefix':'2a1df8ae','cause':'Native Path string used backslashes, violating the existing portable research/ review-file prefix.','prior_lf_fix':'Coordinator reports the earlier source-span error is gone; this is a later independent path guard.'},'superseded_pin':{'path':test,'intermediate_portability_sha256':portability['superseded_pin']['new_sha256'],'current_sha256':after[test],'scope':'Only test-file identity superseded. Existing runtime verdicts and historical execution evidence remain intact.'},'runtime_pin_sha256':{p:v for p,v in after.items() if p!=test},'prior_review_references':[{'path':str(p.relative_to(repo)),'sha256':sha(p),'status':'Preserved historical/intermediate receipt; only its test_provision_history.py pin is superseded by the current test-file pin.'} for p in (prior_path,combined_path,portability_path)],'checks':checks,'other_fixture_platform_inspection':{'files':['jobs/claim-kit/test_provision_history.py','jobs/claim-kit/test_provision_history_cli.py','jobs/claim-kit/test_reinstatement_handoff.py'],'findings':[],'observations':['The review-file path was the only new protocol repository-relative path serialized from native Path in these fixtures.','Other str(Path) uses supply local CLI or import paths and correctly retain native syntax.','Held-text protocol paths are literal forward-slash strings; witness bytes use explicit UTF8 and LF.','Review and bundle serializations use explicit UTF8; hashes are computed from actual emitted bytes. Remaining default-encoding JSON mutations use ASCII JSON output.']},'script_sha256':sha(Path(__file__)),'wall_seconds':round(time.monotonic()-started,6),'findings':[],'limits':['Linux probes simulate Windows relative-path string semantics with PureWindowsPath; no claim of executing these probes on Windows.','No broad or full suite was rerun; coordinator owns focused and hosted verification.','No runtime, production job, canonical output, source grade, blind/source-production artifact or GitHub state was changed or inspected.','The prior LF/CRLF review is retained as an intermediate review; its newline reasoning still applies, while this receipt supplies the final test-file pin.']}
out=a.output or folder/'FIXTURE_PATH_REVIEW.json';assert not out.exists(),'refusing overwrite of additive fixture-path review';out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'path':str(out),'sha256':sha(out),'verdict':report['verdict'],'checks':len(checks),'current_test_sha256':after[test],'script_sha256':report['script_sha256']}));sys.exit(report['verdict']!='approve')
