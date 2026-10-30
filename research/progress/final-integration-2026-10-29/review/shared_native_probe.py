from pathlib import Path
import ast,hashlib,json,shutil,subprocess,tempfile,textwrap
repo=Path('/workspace/scratch/21fe24d0bcf0/integration');pin='8bd150ec3066973e4b12c03c421c87e9d2bf6035';base=Path('/workspace/scratch/21fe24d0bcf0/review/followon-support')
def blob(p):return subprocess.check_output(['git','show',pin+':'+p],cwd=repo)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
rel='research/progress/final-integration-2026-10-29/validate_native.py';raw=blob(rel);s=raw.decode();section=textwrap.dedent(s[s.index('    shared_dest ='):s.index('    cruden =')]);manifest='research/excavator/shared-research-production/completion-v2/COMPLETION.json';doc=json.loads(blob(manifest));refs={}
def walk(x):
 if isinstance(x,dict):
  if isinstance(x.get('path'),str) and isinstance(x.get('sha256'),str):refs[x['path']]=x['sha256']
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
walk(doc);checks={};reference_results={p:{'expected':v,'actual':digest(blob(p))} for p,v in refs.items()};checks['all_manifest_references_match']=all(v['expected']==v['actual'] for v in reference_results.values())
retained='research/excavator/shared-research-production/new-v1/packet/supp/completed-v3';receipt=json.loads(blob(retained+'/INPUTS.json'));checks['manifest_matches_retained_receipt']=receipt['preserved_receipts'][manifest]==digest(blob(manifest));claimraw=blob(retained+'/CLAIMS.publishable.jsonl');checks['retained_two_claim_digest_matches_harness']=digest(claimraw)=='fe5c3fafc4dacbe86e867450d457b94b043182b9f16bf72bd7c15be83e986a6a';checks['manifest_exists']=bool(blob(manifest));checks['no_publish_argument']=not any(isinstance(n,ast.Constant) and n.value=='--publish' for n in ast.walk(ast.parse(s)));checks['new_output_absent_from_tree']=not subprocess.check_output(['git','ls-tree',pin,'--','research/integration-shared-rehearsal'],cwd=repo)
variants=[('reject_traceback',1,'Traceback (most recent call last):',None,False),('reject_missing_tally',1,'ordinary result',None,False),('reject_nonnative_refusal',2,'changed input',None,False),('reject_unrelated_error',2,'claim-kit: missing path',None,False),('preserve_native_stale_refusal',2,'claim-kit: stale input',None,True),('reject_published_tally',0,'result',{'claims_published':1,'eligible':['x','y']},False),('accept_exact_dryrun_receipts',0,'result',{'claims_published':0,'eligible':['EO:6847A','EO:6925A']},True),('retain_exception_dryrun',1,'result',{'claims_published':0,'eligible':[],'exceptions':1},True)]
for name,rc,log,tally,expected in variants:
 with tempfile.TemporaryDirectory() as td:
  root=Path(td);out=root/'out';out.mkdir();dest=root/'old';dest.mkdir();(dest/'TALLY.json').write_text('{"claims_published":0}')
  calls=[]
  def run(label,args,**kwargs):
   calls.append((label,args,kwargs));(out/(label+'.log')).write_text(log)
   folder=root/'research/integration-shared-rehearsal';folder.mkdir(parents=True)
   if tally is not None:
    (folder/'TALLY.json').write_text(json.dumps(tally));(folder/'CLAIMS.publishable.jsonl').write_bytes(claimraw)
    (folder/'checker').mkdir();(folder/'checker/SUMMARY.json').write_text('{"fixture":true}')
   return {'label':label,'returncode':rc}
  scope={'ROOT':root,'OUT':out,'dest':dest,'run':run,'json':json,'sha':sha,'shutil':shutil}
  try:exec(compile(section,rel,'exec'),scope);accepted=True
  except (AssertionError,OSError,ValueError,KeyError):accepted=False
  checks[name]=accepted==expected
  if accepted:
   checks[name+'_no_publish_call']='--publish' not in calls[0][1]
   if tally is not None:
    checks[name+'_copies_exact_receipts']=sha(root/'research/integration-shared-rehearsal/TALLY.json')==sha(out/'shared-receipts/TALLY.json') and sha(out/'shared-receipts/CLAIMS.publishable.jsonl')==digest(claimraw)
    checks[name+'_match_flag']=scope['shared']['matches_retained_two']==(len(tally['eligible'])==2)
report={'commit':pin,'source_sha256':digest(raw),'manifest':manifest,'manifest_sha256':digest(blob(manifest)),'retained_receipt':retained+'/INPUTS.json','checks':checks,'all_checks_pass':all(checks.values()),'manifest_reference_checks':reference_results,'scope':'Exact added harness block exercised with temporary synthetic command outcomes; read-only pinned Git references checked. No native corpus execution, canonical publication or scientific review.'}
(base/'shared-native-probe.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':checks,'all_checks_pass':all(checks.values()),'manifest_references':len(reference_results),'manifest_sha256':report['manifest_sha256']}))
