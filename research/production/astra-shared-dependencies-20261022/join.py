"""Reconstruct exact custody dependencies from the retained PR55 checker receipt."""
import csv,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'jobs/claim-checker'))
import checker as C

def main():
 previous=ROOT/'jobs/leverage-campaign-check/output/claim-checker'
 active=json.loads((previous/'PER_CLAIM.json').read_text())['by_instrument']
 claims={k:c for k,f,n,c,e in C.read_claims(sorted((ROOT/'research/readiness/claims').glob('*.jsonl')),ROOT) if c}
 refs={k:{p:v for p,key,v,chain in C.walk(c) if isinstance(v,dict)} for k,c in claims.items()}
 groups={}
 for r in csv.DictReader((previous/'CLAIM_CHECKS.csv').open()):
  if r['check']!='source_held' or r['status']!='custody_record_only' or active.get(r['instrument_id'],{}).get('claim_key')!=r['claim_key']:continue
  ref=refs[r['claim_key']][r['field']]; sha=C.S.sha_hex(ref.get('sha256') or ref.get('local_file_sha256'))
  g=groups.setdefault(sha,dict(sha256=sha,urls=set(),orders=set(),obligations=[]))
  g['urls'].add(ref.get('url',''));g['orders'].add(r['instrument_id']);g['obligations'].append(dict(instrument_id=r['instrument_id'],claim_key=r['claim_key'],claim_sha256=active[r['instrument_id']]['claim_sha256'],step=r['step'],field=r['field']))
 tree=subprocess.check_output(['git','ls-tree','-r','--name-only','HEAD'],cwd=ROOT,text=True).splitlines()
 for sha,g in groups.items():
  g['urls']=sorted(g['urls']);g['orders']=sorted(g['orders']);g['tracked_hash_named_paths']=[p for p in tree if sha in p]
 selected=json.loads((HERE/'RECOVERED_SHARED_REQUESTS.json').read_text());shared={r['expected_sha256'] for r in selected}
 assert all(s in groups and len(groups[s]['orders'])>=2 for s in shared)
 # All repeated exact GovInfo PDF dependencies, not a hand-picked subset.
 eligible={s for s,g in groups.items() if len(g['orders'])>=2 and any(u.startswith('https://www.govinfo.gov/') and '.pdf' in u for u in g['urls'])}
 assert shared==eligible,(shared^eligible)
 cohort=set().union(*(set(groups[s]['orders']) for s in shared))
 all_objects={s for s,g in groups.items() if set(g['orders'])&cohort}
 lost=set(json.loads((ROOT/'research/production/astra-leverage-2026-10-22/TRACKER_OFFLINE_DELTA.json').read_text())['lost_ready'])
 demands=[]
 for s in sorted(all_objects, key=lambda s:(s not in shared,-len(groups[s]['orders']),s)):
  g=groups[s];urls=[u for u in g['urls'] if u.startswith('https://www.govinfo.gov/') and '.pdf' in u];assert len(urls)==1,(s,urls)
  matching=[r for r in selected if r['expected_sha256']==s]
  d=dict(matching[0]) if matching else dict(url=urls[0],instrument_ids=[next(i for i in g['orders'] if i in cohort)],expected_sha256=s,pages=[])
  held=[p for p in g['tracked_hash_named_paths'] if p.endswith(('.bin','.pdf'))]
  if held:d['retained_path']=held[0]
  demands.append(d)
 result=dict(input_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),checker_run=39885190210,unique_objects=len(groups),distinct_orders=len(set().union(*(set(g['orders']) for g in groups.values()))),references=sum(len(g['obligations']) for g in groups.values()),dependencies=list(groups.values()))
 (HERE/'DEPENDENCIES.json').write_text(json.dumps(result,indent=2)+'\n')
 chosen=dict(shared_objects=sorted(shared),orders=sorted(cohort),prior_ready=sorted(cohort&lost),prior_ready_outside=sorted(lost-cohort),all_required_objects=demands,shared_fields=sum(len(groups[s]['obligations']) for s in shared))
 (HERE/'SELECTED.json').write_text(json.dumps(chosen,indent=2)+'\n')
 batches=[demands[:len(shared)]]+[demands[i:i+30] for i in range(len(shared),len(demands),30)]
 for n,b in enumerate(batches,1):(HERE/f'batch-{n}.json').write_text(json.dumps(b,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k!='dependencies'}));print(dict(shared=len(shared),claims=len(cohort),fields=chosen['shared_fields'],required=len(demands),existing_imports=sum('retained_path' in d for d in demands),prior_ready=len(cohort&lost),outside=chosen['prior_ready_outside']))
if __name__=='__main__':main()
