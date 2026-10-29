from pathlib import Path
import subprocess,tempfile,json
with tempfile.TemporaryDirectory(prefix='claim-kit-sparse-') as name:
 root=Path(name)
 def git(*args,input=None):
  return subprocess.run(['git',*args],cwd=root,input=input,text=True,capture_output=True,check=True)
 git('init','--template=')
 files={'.github/workflows/run-jobs.yml':'runner','HANDOFF/test.md':'notes','jobs/claim-kit/build.py':'compiler','jobs/claim-kit/output/dossiers/a.json':'old output','jobs/other/output/old.json':'other output','research/stage19/code/claim_gate.py':'gate','research/stage19/code/nested/a.py':'nested gate','research/plans/claim_kit_contract/fixtures/a.json':'fixture','research/unrelated/private.json':'outside'}
 for path,value in files.items():
  dest=root/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(value)
 git('add','.')
 git('-c','user.name=fixture','-c','user.email=fixture@example.invalid','commit','-m','fixture')
 git('sparse-checkout','set','--no-cone','--stdin',input='/*\n!/*/\n/.github/**\n/HANDOFF/**\n/jobs/**\n!/jobs/*/output/**\n')
 assert not (root/'research/stage19/code/claim_gate.py').exists()
 assert not (root/'research/plans/claim_kit_contract/fixtures/a.json').exists()
 git('sparse-checkout','add','/research/stage19/code/**','/research/plans/claim_kit_contract/**')
 actual=sorted(path for path in files if (root/path).is_file())
 expected=sorted(path for path in files if '/output/' not in path and path!='research/unrelated/private.json')
 assert actual==expected,(actual,expected)
 print(json.dumps({'result':'passed','bootstrap_fixture_roots_absent':True,'required_descendants_restored':True,'outputs_restored':[],'unrelated_research_restored':False,'files':actual},indent=2))
