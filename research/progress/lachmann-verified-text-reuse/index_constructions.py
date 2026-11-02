"""Count genuine provider-index construction across identical native batch routes."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[3]
PRIOR='47fa75a34a8a330d2e07bdd50909b7ce715f2aa9'
DEST=Path(__file__).parent/'validation/cache-constructions.json'
if DEST.exists():raise SystemExit('refusing overwrite '+str(DEST))
script=r'''
import json,os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
root=Path(sys.argv[1]);sys.path.insert(0,str(root/'jobs/claim-kit'))
import test_build as F,batch,fragment_cache as FC,working_text as W
f=F.BuildIntegrationTests('test_whole_population_including_yes_no_undecided_and_missing');f.setUp()
try:
 c=f.confirmed_derivative();f.run_build()
 with tempfile.TemporaryDirectory() as cache,patch.dict(os.environ,{'CLAIM_KIT_CACHE_DIR':cache,'CLAIM_KIT_INDEX_CACHE':'1'}):
  FC._SHARED.clear();counts=[];original=W.Index.__init__
  def count(instance,*args,**kwargs):counts.append(str(args[0]));original(instance,*args,**kwargs)
  with patch.object(W.Index,'__init__',count):
   for n in range(2):
    p=f.repo/('research/count/packet'+str(n));batch.prepare(f.repo,f.out,p,['EO:2'],'producer')
    batch.load_packet(p,f.repo)
    result=batch.apply(f.repo,p,p/'applied');assert result['counts']=={'unresolved':1}
    batch.check(f.repo,p,p/'applied',actual=False)
   first=len(counts)
   # Direct assembly and dossier checking are also exercised with an accepted
   # synthetic fixture, separate from unresolved demonstration members.
   import test_batch
   t=test_batch.BatchTests('test_changed_source_or_packet_rejected')
   t.repo,t.out=f.repo,f.out
   t.fill(p,'EO:2');batch.apply(f.repo,p,p/'submitted')
   batch.check(f.repo,p,p/'submitted',actual=False)
   second=len(counts)-first
  print(json.dumps({'blank_batches':2,'submitted_synthetic_batches':1,
                   'blank_route_index_constructions':first,'submit_and_check_additional_constructions':second,
                   'total_index_constructions':len(counts),'canonical_claims_published':0,
                   'scope':'isolated synthetic construction multiplicity; no corpus runtime or saving inferred'}))
finally:f.doCleanups()
'''
results={}
with tempfile.TemporaryDirectory(prefix='lachmann-index-proof-') as tmp:
 for generation in ['prior','repaired']:
  code=Path(tmp)/generation
  for folder in ['jobs/claim-kit','jobs/clause-drafts','jobs/norton','jobs/status-history','research/stage19/code']:
   for p in (ROOT/folder).glob('*.py'):
    rel=p.relative_to(ROOT).as_posix()
    raw=subprocess.check_output(['git','show',PRIOR+':'+rel],cwd=ROOT) if generation=='prior' else p.read_bytes()
    q=code/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(raw)
  r=subprocess.run([sys.executable,'-B','-c',script,str(code)],capture_output=True,text=True)
  assert r.returncode==0,r.stderr
  results[generation]=json.loads(r.stdout.splitlines()[-1])
assert results['repaired']['total_index_constructions']==1,results
results['prior_commit']=PRIOR
results['implementation_sha256']={n:hashlib.sha256((ROOT/'jobs/claim-kit'/n).read_bytes()).hexdigest()
 for n in ['working_text.py','fragment_cache.py','build.py','batch.py','inputs.py']}
DEST.write_text(json.dumps(results,sort_keys=True,indent=2)+'\n')
print(DEST.read_text())
