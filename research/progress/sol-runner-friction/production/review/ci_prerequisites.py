import ast, hashlib, json, os, shutil, subprocess, tempfile
from pathlib import Path
SRC=Path(os.environ.get('PHASE2_REVIEW_SOURCE', Path(__file__).resolve().parents[5]));OUT=Path(__file__).parent
base=['test_build.BuildIntegrationTests.test_cli_sheet_assemble_check_and_failed_batch','test_batch.BatchTests.test_lossless_roundtrip_shares_sources_and_full_text','test_batch.BatchTests.test_valla_context_attaches_without_approval_and_refuses_stale_claim','test_completion.CompletionTests.test_exact_producer_bytes_and_all_consumed_receipts_preserved','test_source_supplement.SourceSupplementTests.test_native_csv_apply_and_strict_gate','test_status_overlay.OverlayTests.test_reviewed_proposal_has_no_authority_and_experimental_full_dossier']
records=[]
for ref in ('bc65c165','71b06f9f'):
 with tempfile.TemporaryDirectory(prefix='ci-prerequisites-',dir=os.environ.get('PHASE2_REVIEW_SCRATCH')) as td:
  root=Path(td)
  paths=subprocess.run(['git','ls-tree','-r','--name-only',ref,'--','jobs/claim-kit','jobs/valla','jobs/status-history','jobs/norton/model.py','jobs/clause-drafts/segment.py','research/stage19/code/claim_gate.py','research/plans/claim_kit_contract/fixtures'],cwd=SRC,check=True,capture_output=True,text=True).stdout.splitlines()
  chosen=[p for p in paths if (p.startswith('jobs/claim-kit/') and p.count('/')==2 and p.endswith('.py')) or p in ['jobs/valla/valla.py','jobs/valla/premises.json','jobs/status-history/history.py','jobs/norton/model.py','jobs/clause-drafts/segment.py','research/stage19/code/claim_gate.py'] or (p.startswith('research/plans/claim_kit_contract/fixtures/') and p.endswith('.example.jsonl'))]
  pins={}
  for path in chosen:
   raw=subprocess.run(['git','show',ref+':'+path],cwd=SRC,check=True,capture_output=True).stdout
   dst=root/path;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw);pins[path]=hashlib.sha256(raw).hexdigest()
  tests=base+(['test_working_text_index'] if ref=='71b06f9f' else [])
  source="import socket,sys,unittest;sys.path.insert(0,'jobs/claim-kit');socket.create_connection=lambda *a,**k:(_ for _ in ()).throw(AssertionError('network forbidden'));socket.socket.connect=lambda *a,**k:(_ for _ in ()).throw(AssertionError('network forbidden'));suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromNames("+repr(tests)+"));result=unittest.TextTestRunner(verbosity=2).run(suite);sys.exit(not result.wasSuccessful())"
  r=subprocess.run(['python3','-B','-c',source],cwd=root,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True)
  records.append({'ref':ref,'returncode':r.returncode,'selected_tests':tests,'output':r.stdout+r.stderr,'copied_actual_blob_pins':pins,'scope':'Selected runtime prerequisite checks in exact copied code/fixtures. No production output directories, no source worktree/index edits, not full claim-kit suite.'})
  assert r.returncode==0,records[-1]['output']
(OUT/'CI_PREREQUISITES.json').write_text(json.dumps(records,indent=2)+'\n')
for r in records:print(r['ref'],r['output'][-300:])
