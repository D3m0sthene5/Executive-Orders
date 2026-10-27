from pathlib import Path
import sys,json,hashlib,time,datetime
repo=Path('.').resolve();sys.path.insert(0,str(repo/'jobs/claim-kit'));import completion
r=repo/'research/excavator/production-cost-trace-2026-10-26';dest=r/'packet-b2-correction-v9/combined-four-replay-v1';dest.mkdir()
start=time.monotonic();selected={}
for name in ['codex-production-cost-trace-20261026-b1.jsonl','codex-production-cost-trace-20261026-b2.jsonl']:
 for raw in (repo/'research/readiness/claims'/name).read_bytes().splitlines(keepends=True):
  j=json.loads(raw);selected[j['instrument_id']]=(j,raw)
assert len(selected)==4
checker={'by_instrument':{},'claims':[]}
for path in [r/'recovery/complete-b1-v1/checker/PER_CLAIM.json',r/'packet-b2-correction-v9/complete-v1/checker/PER_CLAIM.json']:
 data=json.loads(path.read_bytes());checker['by_instrument'].update(data['by_instrument']);checker['claims'].extend(data['claims'])
result=completion.run_tracker(repo,selected,checker,dest)
result.update(schema='eo-four-case-actual-tracker-replay/v1',wall_seconds=time.monotonic()-start,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),selected_claim_hashes={iid:completion.claim_sha(j) for iid,(j,raw) in selected.items()},note='Actual tracker with four exact filed claims and their actual checker receipts substituted together. Isolated replay, no canonical output generation or human certification.')
(dest/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'seconds':result['wall_seconds'],'before':result['before'].get('ready_for_human_review'),'after':result['after'].get('ready_for_human_review'),'selected':{k:v['after'].get('ready_for_human_review') for k,v in result['selected'].items()}}))
