"""Run the actual custody checker on identical real refs and exact warm bytes."""
import collections,copy,json,shutil,sys,tempfile,time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'jobs/claim-checker'));import checker as C

def main():
 started=time.monotonic(); selected=json.loads((HERE/'SELECTED.json').read_text());hashes=set(selected['shared_objects'])
 groups=[g for g in json.loads((HERE/'DEPENDENCIES.json').read_text())['dependencies'] if g['sha256'] in hashes]
 obs=[o for g in groups for o in g['obligations']]
 claims={k:c for k,f,n,c,e in C.read_claims(sorted((ROOT/'research/readiness/claims').glob('*.jsonl')),ROOT) if c}
 refs={k:{p:v for p,key,v,chain in C.walk(c) if isinstance(v,dict)} for k,c in claims.items()}
 index=C.S.HeldIndex();C.S.load_job_sources(index,ROOT,exclude_jobs=('claim-checker',))
 before=copy.deepcopy(index)
 for mapping in (before.by_sha,before.by_url):
  for key,copies in mapping.items():mapping[key]=[c for c in copies if c.origin!='jobs/astra-source-retention/output/SOURCES.jsonl']
 assert all(before.lookup_sha(s) for s in hashes)
 C._VERIFY['left']=0
 result=dict(candidate_id='C-20261020-16',saver_key='neyman_shared_acquisition_once',objects=len(hashes),orders=len(selected['orders']),references=len(obs),comparison='Identical actual source fields and already-retrieved exact bytes; warm cache versus retained source catalogue',arms={},model_tokens=None,aggregate_agent_seconds=None,cash_usd=None,net_efficiency_verified=False)
 with tempfile.TemporaryDirectory() as tmp:
  cache=Path(tmp)
  for s in hashes:
   f=ROOT/'jobs/astra-source-retention/output/pdf'/f'{s}.pdf';assert C.S.file_sha256(f)==s
   dst=cache/'verified'/s[:2]/f'{s}.bin';dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dst)
  result['setup_seconds']=time.monotonic()-started
  for label,idx in [('before',before),('after',index)]:
   ctx=SimpleNamespace(index=idx,reader=C.S.TextReader(cache,packed=idx.packed_texts),gpo_matched={},cache_dir=cache)
   counts=collections.Counter();sizes=collections.Counter();read=Path.read_bytes;hashfn=C.S.file_sha256
   def read_bytes(path):
    data=read(path)
    if path.is_relative_to(cache/'verified') and path.stem in hashes:counts[path.stem]+=1;sizes[path.stem]+=len(data)
    return data
   def file_hash(path):
    if path.suffix=='.pdf' and path.stem in hashes:counts[path.stem]+=1;sizes[path.stem]+=path.stat().st_size
    return hashfn(path)
   rows=[];tick=time.monotonic()
   with patch.object(Path,'read_bytes',read_bytes),patch.object(C.S,'file_sha256',file_hash):
    for o in obs:C.check_source(refs[o['claim_key']][o['field']],o['field'],ctx,rows)
   assert len(rows)==len(obs) and all(r['result']=='pass' for r in rows)
   result['arms'][label]=dict(source_fields_passed=len(rows),raw_object_reads=sum(counts.values()),raw_bytes_read=sum(sizes.values()),reads_by_sha256=dict(counts),wall_seconds=time.monotonic()-tick,network_requests=0)
  assert result['arms']['after']['raw_object_reads']==len(hashes)
  result['repeated_raw_reads_eliminated']=result['arms']['before']['raw_object_reads']-result['arms']['after']['raw_object_reads']
  result['raw_bytes_read_avoided']=result['arms']['before']['raw_bytes_read']-result['arms']['after']['raw_bytes_read']
 result['wall_seconds_including_setup']=time.monotonic()-started
 result['limits']=['Custody-check I/O only, not total research/model/dollar efficiency.','Implementation, failed attempts, engineering review, integration and session recovery remain additional costs.','Warm-cache comparison establishes no avoided network requests; publication and recovery transfers are additional.']
 (HERE/'REUSE_MEASUREMENT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='arms'}));print({k:{f:v for f,v in a.items() if f!='reads_by_sha256'} for k,a in result['arms'].items()})
if __name__=='__main__':main()
