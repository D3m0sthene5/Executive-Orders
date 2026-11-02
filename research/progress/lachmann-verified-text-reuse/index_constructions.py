"""Count genuine provider-index construction across identical native batch routes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,default=HERE/'validation/cache-constructions.json')
DEST=parser.parse_args().output
archive=HERE/'prior-source'
manifest_raw=(archive/'MANIFEST.json').read_bytes()
manifest=json.loads(manifest_raw)
patch=archive/manifest['patch']
assert hashlib.sha256(patch.read_bytes()).hexdigest()==manifest['patch_sha256']

def restore_prior(code):
    # Only this published base git object is needed; the local prior commit id
    # in the manifest is a historical label, never an input to git show.
    for rel,digest in manifest['base_files'].items():
        raw=subprocess.check_output(['git','show',manifest['base_commit']+':'+rel],cwd=ROOT)
        assert hashlib.sha256(raw).hexdigest()==digest,rel
        q=code/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(raw)
    subprocess.run(['git','apply','--check',str(patch)],cwd=code,check=True)
    subprocess.run(['git','apply',str(patch)],cwd=code,check=True)
    actual={p.relative_to(code).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in manifest['folders'] for p in (code/folder).glob('*.py')}
    assert actual==manifest['prior_files'],'restored prior Python closure mismatch'

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
  if generation=='prior':
   restore_prior(code)
  else:
   for folder in manifest['folders']:
    for p in (ROOT/folder).glob('*.py'):
     rel=p.relative_to(ROOT).as_posix()
     q=code/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
  r=subprocess.run([sys.executable,'-B','-c',script,str(code)],capture_output=True,text=True)
  assert r.returncode==0,r.stderr
  results[generation]=json.loads(r.stdout.splitlines()[-1])
assert results['repaired']['total_index_constructions']==1,results
results['prior_commit_reference_only']=manifest['prior_commit_reference_only']
results['prior_source_restore']={'base_commit':manifest['base_commit'],
 'manifest_sha256':hashlib.sha256(manifest_raw).hexdigest(),
 'patch_sha256':manifest['patch_sha256'],'prior_python_files_verified':len(manifest['prior_files']),
 'requires_prior_git_object':False}
results['implementation_sha256']={n:hashlib.sha256((ROOT/'jobs/claim-kit'/n).read_bytes()).hexdigest()
 for n in ['working_text.py','fragment_cache.py','build.py','batch.py','inputs.py']}
DEST.parent.mkdir(parents=True,exist_ok=True)
DEST.write_text(json.dumps(results,sort_keys=True,indent=2)+'\n')
print(DEST.read_text())
