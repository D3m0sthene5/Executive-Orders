import ast, contextlib, hashlib, importlib.util, io, json, os, subprocess, tempfile
from pathlib import Path
from unittest.mock import patch
SRC=Path(os.environ.get('PHASE2_REVIEW_SOURCE', Path(__file__).resolve().parents[5]))
spec=importlib.util.spec_from_file_location('phase2_picker',SRC/'.github/scripts/pick_jobs.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
results=[]
def check(name,actual,expected):
 assert actual==expected,(name,actual,expected)
 results.append({'case':name,'result':'PASS'})
def gitblob(ref,path):
 return subprocess.run(['git','show',ref+':'+path],cwd=SRC,check=True,capture_output=True).stdout
old=Path.cwd()
with tempfile.TemporaryDirectory(prefix='adversarial-',dir=os.environ.get('PHASE2_REVIEW_SCRATCH')) as scratch:
 os.chdir(scratch)
 try:
  for ref in ('bc65c165','71b06f9f'):
   for rel,known in p.CLAIM_KIT_COMPILER_SHA256.items():
    raw=gitblob(ref,rel);check(ref+' pin '+rel,hashlib.sha256(raw).hexdigest() in known,True)
    dst=Path(rel);dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw)
   for rel in sorted(p.CLAIM_KIT_RUNTIME_ONLY):
    check(ref+' suppress '+rel,p.claim_kit_runtime_only([rel]),True)
    check(ref+' picker suppress '+rel,p.for_changes([rel],triggers=False,runtime_push=True),[])
    check(ref+' default rebuild '+rel,p.for_changes([rel],triggers=False),['claim-kit'])
   for rel in p.CLAIM_KIT_COMPILER_SHA256:
    dst=Path(rel);raw=dst.read_bytes();dst.write_bytes(raw+b'\n# unknown compiler version\n')
    check(ref+' unknown '+rel,p.claim_kit_runtime_only(['jobs/claim-kit/batch.py']),False)
    check(ref+' unknown rebuild '+rel,p.for_changes(['jobs/claim-kit/batch.py'],triggers=False,runtime_push=True),['claim-kit'])
    dst.write_bytes(raw)
   runtime=['jobs/claim-kit/batch.py']
   for extra in list(p.CLAIM_KIT_COMPILER_SHA256)+['jobs/claim-kit/needs.txt','jobs/claim-kit/inputs.txt','jobs/claim-kit/triggers.txt','jobs/claim-kit/after.txt','jobs/claim-kit/data/new.json','jobs/claim-kit/new_module.py','jobs/claim-kit/test_new.py','research/new.json','jobs/other/output/new.json']:
    check(ref+' mixed rebuild '+extra,p.for_changes(runtime+[extra],triggers=False,runtime_push=True),['claim-kit'])
   for event in ('push','schedule','workflow_dispatch'):
    env={'EVENT':event,'AFTER':'head','GITHUB_OUTPUT':str(Path(scratch)/'outputs'),'INPUT_JOB':'claim-kit','SCHEDULE':'47 */3 * * *'}
    Path('outputs').write_text('')
    with patch.dict(os.environ,env),patch.object(p,'changed_files',return_value=runtime),patch.object(p,'recent_changes',return_value=runtime),contextlib.redirect_stdout(io.StringIO()): p.main()
    out=dict(line.split('=',1) for line in Path('outputs').read_text().splitlines())
    check(ref+' main '+event,out,{'jobs':'','runtime_tests':'claim-kit'} if event=='push' else {'jobs':'claim-kit'})
  # Closure: all local static imports of every pinned implementation in both variants.
  modules={x.stem:x.relative_to(SRC).as_posix() for x in (SRC/'jobs/claim-kit').glob('*.py')}
  for ref in ('bc65c165','71b06f9f'):
   for rel in p.CLAIM_KIT_COMPILER_SHA256:
    tree=ast.parse(gitblob(ref,rel))
    for node in ast.walk(tree):
     names=[]
     if isinstance(node,ast.Import):names=[x.name for x in node.names]
     elif isinstance(node,ast.ImportFrom):names=[node.module or '']
     for name in names:
      if name in modules:check(ref+' closure '+rel+' -> '+name,modules[name] in p.CLAIM_KIT_COMPILER_SHA256,True)
  check('empty change rebuild',p.claim_kit_runtime_only([]),False)
 finally:os.chdir(old)
receipt={'model':'gpt-6.1-sol','tokens':None,'billing':None,'assertions_passed':len(results),'cases':results,'scope':'Isolated copies of actual 15 implementation pin closures at baseline and Opus, no source worktree/index/sparse modifications. No full claim-kit suite or production job executed.'}
Path(__file__).with_name('ADVERSARIAL.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='cases'}))
