from pathlib import Path
import json,sys,subprocess,time,hashlib,os
B=Path(__file__).resolve().parent;R=B.parents[4];os.chdir(R);receipts=[]
def rel(p):return str(p.relative_to(R))
def put(p,v):assert not p.exists();p.write_text(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
def run(args,log):
 t=time.monotonic();r=subprocess.run(args,capture_output=True,text=True);assert not log.exists();log.write_text(r.stdout+r.stderr);receipts.append({'command':args,'log':rel(log),'exit_code':r.returncode,'machine_elapsed_seconds':time.monotonic()-t});return r
for n in [10673,10772]:
 u=B/f'undecided/EO_{n}';bundle=B/f'overlay/EO_{n}/proposal-v1';review=B/f'review/STATUS_REVIEW.EO_{n}.v1.json';assert review.exists()
 args=['python','jobs/claim-kit/kit.py','--output','tmp/continuous-compiled','overlay-propose','--evidence',rel(u/'EVIDENCE.json'),'--decision',rel(u/'STATUS_DECISION.json'),'--review',rel(review),'--lifecycle-sheet',rel(B/f'applied-v1/decisions/EO_{n}.source-grounded-v1.json'),'--write',rel(bundle)]
 r=run(args,B/f'OVERLAY_PROPOSE.EO_{n}.v1.log');assert r.returncode==0,(n,r.stdout,r.stderr)
 source=json.loads((bundle/'LIFECYCLE_SOURCE_DECISION.json').read_text());working=json.loads((bundle/'LIFECYCLE_DECISION.json').read_text());changed=[k for k in source.keys()|working.keys()if source.get(k)!=working.get(k)];assert set(changed)<=set(['approved','dossier_sha256']),changed
 assert source['clauses']==working['clauses']and source['inventory_overrides']==working['inventory_overrides']
 working['approved']=True;put(bundle/'LIFECYCLE_DECISION.confirmed-v1.json',working)
 r=run(['python','jobs/claim-kit/kit.py','--output','tmp/continuous-compiled','overlay-assemble',rel(bundle),'--sheet',rel(bundle/'LIFECYCLE_DECISION.confirmed-v1.json'),'--write',rel(bundle/'ordinary-assembly-v1')],bundle/'OVERLAY_ASSEMBLE.v1.log')
 result=json.loads(r.stdout);assert result['errors']==['bounded_later_search'],result
 r=run(['python',rel(B/'manual_claim_youth_fitness_v1.py'),rel(bundle)],bundle/'MANUAL_SUPPLEMENT.v1.log');assert r.returncode==0,(n,r.stdout,r.stderr)
 r=run(['python','jobs/claim-kit/kit.py','--output','tmp/continuous-compiled','overlay-check',rel(bundle),rel(bundle/'CLAIMS.working.v1.jsonl')],bundle/'OVERLAY_CHECK.v1.log');assert r.returncode==0,(n,r.stdout,r.stderr)
pair=B/'CLAIMS.working.pair-v1.jsonl';assert not pair.exists();pair.write_text(''.join((B/f'overlay/EO_{n}/proposal-v1/CLAIMS.working.v1.jsonl').read_text()for n in [10673,10772]))
put(B/'ASSEMBLY_TELEMETRY.v1.json',receipts)
print(json.dumps({'pair_path':rel(pair),'pair_file_sha256':hashlib.sha256(pair.read_bytes()).hexdigest(),'calls':receipts},indent=2))
