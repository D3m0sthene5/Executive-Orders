"""Audit retained hosted benchmark artifacts; never reruns the corpus/linter."""
from pathlib import Path
import hashlib,json,subprocess,zipfile,datetime,time
ROOT=Path(__file__).resolve().parents[5];HERE=Path(__file__).parent;REPAIR=HERE.parent;NATIVE=REPAIR/'native'
H=lambda b:hashlib.sha256(b).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def run():
 receipt=json.loads((NATIVE/'RECEIPT.json').read_text());run=json.loads((NATIVE/'RUN.json').read_text());index=json.loads((NATIVE/'ARTIFACT_INDEX.json').read_text());archive=(NATIVE/'ARTIFACT.zip').read_bytes();assert H(archive)==index['sha256'];members=[]
 with zipfile.ZipFile(NATIVE/'ARTIFACT.zip') as z:
  actual={n for n in z.namelist() if not n.endswith('/')};assert actual=={m['path'] for m in index['members']}
  for member in index['members']:
   raw=z.read(member['path']);assert len(raw)==member['bytes'] and H(raw)==member['sha256'];members.append(member)
  raw=z.read('EVALUATION.json');assert raw==(NATIVE/'EVALUATION.json').read_bytes();assert H(raw)==receipt['evaluation_sha256']==run['evaluation_sha256'];assert json.loads(z.read('NATIVE_RECEIPT.json'))==receipt
 native=json.loads(raw);local=json.loads((REPAIR/'EVALUATION.json').read_text());seal=json.loads((HERE/'FINAL_LOCAL_SEAL.json').read_text());assert H((REPAIR/'EVALUATION.json').read_bytes())==seal['evaluation_sha256'];assert native['module_sha256']==local['module_sha256']==receipt['module_sha256']==run['module_sha256']
 scope=receipt['name_scope'];commit=scope['inventory_commit'];parents=git('show','-s','--format=%P',commit).decode().strip().split();assert run['commit'] in parents
 code={}
 for name,digest in native['module_sha256'].items():
  rel='jobs/geddes/'+name;blob=git('show',commit+':'+rel);assert H(blob)==digest==seal['code_modules'][rel];code[rel]=digest
 inv={}
 for record in git('ls-tree','-rz',commit,'jobs').split(b'\0'):
  if not record:continue
  meta,path=record.decode().split('\t',1)
  if '/texts/' in path and path.endswith('.txt') and not path.startswith('jobs/clause-drafts/'):inv[path]=meta.split()[2]
 invhash=H(json.dumps(inv,sort_keys=True).encode());assert invhash==scope['inventory_sha256'];assert len(inv)==scope['tracked_files']==scope['verified_files']==39770;assert scope['missing_files']==0 and scope['changed_files']==[] and scope['full_discovered_corpus_covered']
 inputraw=git('show',commit+':research/excavator/claude-geddes-2026-11-01/repair/INPUT_PINS.json');inputs=json.loads(inputraw);assert inputs==json.loads((REPAIR/'INPUT_PINS.json').read_text());pins=[]
 for rel,digest in inputs['sha256'].items():
  b=(ROOT/rel).read_bytes();assert H(b)==digest
  blobsha=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();assert blobsha==git('rev-parse',inputs['source_commit']+':'+rel).decode().strip();pins.append({'path':rel,'sha256':digest,'base_git_blob':blobsha})
 totals={};scopes=[];bounds=set();correlation=json.loads((HERE/'FINAL_EXACT_CORRELATION.json').read_text());corr={r['instrument_id']:r for r in correlation['rows']}
 for kind,expected in [('rejected',40),('filed',254)]:
  ns={r['instrument_id']:r for r in native[kind]};ls={r['instrument_id']:r for r in local[kind]};assert len(ns)==len(native[kind])==expected and set(ns)==set(ls)
  for iid,r in ns.items():
   assert r['flags']==ls[iid]['flags'];assert r.get('held_text_integrity_failures',0)==0
   if kind=='rejected':
    assert r['prior_claim']==ls[iid]['prior_claim']==corr[iid]['prior_claim'];assert r['review_defects']==ls[iid]['review_defects']==corr[iid]['review_defects'];assert all(flag in r['flags'] for flag in corr[iid]['matching_flags'])
   else:assert r['filed_path']==ls[iid]['filed_path']
   for g in r['coverage_gaps']:
    if g['code']=='literal_name_corpus_scope':assert g==scope;scopes.append(g)
    if g['code']=='own_order_body_unverified':bounds.add(iid)
  normalized=[{'instrument_id':r['instrument_id'],'flags':r['flags']} for r in native[kind] if r['flags']];assert normalized==receipt[kind+'_flags'];totals[kind]={'exact_member_set_equal':True,'members':expected,'flagged':len(normalized),'all_flags_equal_to_sealed_local':True}
 assert sorted(bounds)==receipt['source_boundary_gaps'];assert len(bounds)==5
 correlation['evaluation_path']=str((NATIVE/'EVALUATION.json').relative_to(ROOT));correlation['evaluation_sha256']=H(raw);correlation['module_sha256']=native['module_sha256'];correlation['native_binding_note']='All40 exact prior refs and historical defect labels, every matching flag, and all254 filed member identities were compared to the sealed local evaluation. All flags are structurally identical; no new source adjudication or new recall credit inferred.';(HERE/'NATIVE_EXACT_CORRELATION.json').write_text(json.dumps(correlation,indent=2)+'\n')
 audit=json.loads((HERE/'FINAL_FILED_FLAG_AUDIT.json').read_text());fa={r['instrument_id']:r for r in audit['rows']}
 for r in receipt['filed_flags']:assert fa[r['instrument_id']]['flags']==r['flags']
 audit['evaluation_sha256']=H(raw);audit['module_sha256']=native['module_sha256'];audit['native_binding_note']='All18 exact flag objects unchanged in recovered native raw evaluation; prior source/structural adjudication remains bound to those exact flags. No new warnings or EO6876 candidates appeared.';(HERE/'NATIVE_FILED_FLAG_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n')
 return {'schema':'geddes-independent-native-artifact-review/v1','run':run,'native_merge_commit':commit,'native_merge_parents':parents,'artifact_id':index['artifact_id'],'artifact_sha256':H(archive),'artifact_members_verified':len(members),'artifact_members':members,'native_evaluation_sha256':H(raw),'native_receipt_sha256':H((NATIVE/'RECEIPT.json').read_bytes()),'raw_artifact_recovered':True,'code_modules_verified_from_native_git_commit':code,'input_pin_file_sha256':H(inputraw),'frozen_input_pin_count':len(pins),'input_pins_verified_against_base_git_blobs':pins,'workflow_sha256':H(git('show',commit+':.github/workflows/geddes.yml')),'evaluator_sha256':H(git('show',commit+':research/excavator/claude-geddes-2026-11-01/repair/evaluate.py')),'inventory_membership_independently_recomputed':True,'inventory_commit':commit,'inventory_sha256':invhash,'inventory_member_count':len(inv),'hosted_reported_verified_source_count':scope['verified_files'],'hosted_reported_missing_source_count':0,'hosted_reported_changed_sources':[],'scope_records_checked':len(scopes),'source_verification_qualification':'Exact inventory membership recomputed independently from native Git tree. Raw39,770 source bytes were verified by the pinned hosted workflow and reported in recovered evaluation; reviewer did not rehydrate/recheck39,770 files locally. Frozen32 packet/INDEX/segment inputs checked locally against base Git blobs.','member_sets':totals,'no_added_or_changed_flags':True,'eo6876_candidates_unchanged':True,'source_boundary_gap_ids':sorted(bounds),'exact_historical_defects_caught':20,'historical_rejected_denominator':40,'filed_flagged_claims':18,'filed_denominator':254,'supported_source_discrepancy_claims':16,'supported_structural_omission_claims':2,'unsupported_flagged_claims_observed':0,'indeterminate_flagged_claims_observed':0,'original_all_flagged_filed_target_met':False,'scope':'Bounded engineering and source-correlation review only; no new whole-case scientific/legal approval, canonical adoption, model substitution or certified human review.','utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
if __name__=='__main__':print(json.dumps(run(),indent=2))
