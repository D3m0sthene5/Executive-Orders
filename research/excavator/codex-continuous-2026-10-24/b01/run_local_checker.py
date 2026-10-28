"""Call unchanged actual checker API with existing explicit HeldCopy input parameter.
Registers only hash-checked receipts under this research-owned directory for this run.
Does not change global jobs outputs, source registries, checker policy or canonical claims.
"""
from pathlib import Path
import json,hashlib,sys,csv,os,time,datetime
B=Path(__file__).resolve().parent;R=B.parents[3];sys.path.insert(0,str(R/'jobs/claim-checker'));import checker,sources
os.environ['CLAIM_CHECKER_VERIFY_DOWNLOADS']='0';out=B/'checker-v2-local';out.mkdir(exist_ok=True)
start=time.monotonic();index=sources.build_index(R,R/'jobs/claim-checker',[],exclude_jobs=('claim-checker',));pins=[]
for name in ['source-v1','source-v2','source-v3']:
 for line in (B/name/'SOURCES.jsonl').read_text().splitlines():
  r=json.loads(line);raw=B/'source-cache'/r['cache_path'];text=B/name/r['text_path'];assert hashlib.sha256(raw.read_bytes()).hexdigest()==r['sha256']
  if r['citation'].startswith('USPS SPP'):text=B/'source-review'/f"{r['sha256']}.txt"
  index.add(sources.HeldCopy(str((B/name/'SOURCES.jsonl').relative_to(R)),r['sha256'],r['url'],r['bytes'],raw,text,(),r['page_or_item'],r['instrument_ids'],'source-ladder receipt; exact raw hash verified',custody='repo_file'))
  pins.append({'receipt':str((B/name/'SOURCES.jsonl').relative_to(R)),'sha256':r['sha256'],'raw_path':str(raw.relative_to(R)),'text_path':str(text.relative_to(R)),'text_sha256':hashlib.sha256(text.read_bytes()).hexdigest()})
ctx=checker.Context(R,R/'jobs/claim-checker',out/'cache',index=index);p=B/'PROPOSED_CLAIM.v2.jsonl';c=json.loads(p.read_text());rows,errors,status=checker.check_claim(c,ctx)
s=checker.summarise_claim(str(p.relative_to(R))+':1',str(p.relative_to(R)),1,c,rows,errors,status,ctx)
(out/'PER_CLAIM.json').write_text(json.dumps(s,indent=2)+'\n');(out/'CHECKS.json').write_text(json.dumps(rows,indent=2)+'\n');(out/'INPUTS.json').write_text(json.dumps({'checker_sha256':hashlib.sha256((R/'jobs/claim-checker/checker.py').read_bytes()).hexdigest(),'sources_sha256':hashlib.sha256((R/'jobs/claim-checker/sources.py').read_bytes()).hexdigest(),'claim_file_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'claim_sha256':ctx.gate.claim_sha(c),'explicit_index_input_records':pins,'network_downloads':0,'machine_elapsed_seconds':time.monotonic()-start,'note':'Existing actual checker API with explicit HeldIndex; root standard retention job is still required for ordinary remote consumer discovery.'},indent=2)+'\n')
print(json.dumps({k:s[k] for k in ['claim_sha256','mechanical_result','gate_passed','all_checks_passed','failures','unverified']},indent=2))
