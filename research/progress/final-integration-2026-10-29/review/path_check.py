from pathlib import Path
import ast,hashlib,json,subprocess
repo=Path('/workspace/scratch/21fe24d0bcf0/integration');pin='cb69b0b29839cf5677cb709cdf72189d41e575ca';base=Path('/workspace/scratch/21fe24d0bcf0/review/followon-support')
def blob(path):return subprocess.check_output(['git','show',pin+':'+path],cwd=repo)
def entry(path):return subprocess.check_output(['git','ls-tree',pin,'--',path],cwd=repo,text=True).strip()
def sha(raw):return hashlib.sha256(raw).hexdigest()
harness='research/progress/final-integration-2026-10-29/validate_native.py';s=blob(harness).decode();tree=ast.parse(s);t=next(n for n in tree.body if isinstance(n,ast.Try));assigns=t.body[:3];scope={'ROOT':repo}
exec(compile(ast.Module(body=assigns,type_ignores=[]),harness,'exec'),scope)
packet,manifest,dest=(scope[k] for k in ('packet','manifest','dest'))
cr='research/progress/corpus-evidence-retrieval';source='research/excavator/claude-nira-sweep-2026-10-29/cruden.py'
paths=[harness,'jobs/claim-kit/kit.py',manifest,packet+'/PACKET.json',source,source.replace('cruden.py','cruden_cache.py'),cr+'/profile/profile_cruden.py',cr+'/challenge/BASELINE_CRUDEN.py',cr+'/native/r1-input/PACKET.json',cr+'/native/r1-input/ORIGIN.json','jobs/claim-kit/batch.py','jobs/domesday-register/output/REGISTER.csv','jobs/x1-class-engine/data/WPA_NUMBERED_ENTRIES.csv','jobs/app-executive-orders/output/MIRROR_DOCUMENTS.jsonl','jobs/app-executive-orders/output/DOCUMENTS.jsonl']
paths += [cr+'/challenge/'+name for name in ['fixture_challenge.py','staleness_challenge.py','deep_challenge.py','final_contract_challenge.py']]
checks={'root_resolves_to_repository':(repo/harness).resolve().parents[3]==repo,'wrong_previous_manifest_is_absent':not entry('research/excavator/opus-native-rehearsal-2026-10-29/r1/completion/COMPLETION.json'),'correct_manifest_under_packet':manifest==packet+'/completion/COMPLETION.json','rehearsal_output_absent_from_tree':not entry(dest.relative_to(repo).as_posix())}
source_pins={p:{'git_tree_entry':entry(p)} for p in paths};checks['all19_harness_inputs_tracked_regular_blobs']=len(paths)==19 and all(v['git_tree_entry'].startswith(('100644 blob','100755 blob')) for v in source_pins.values())
for p in [manifest,packet+'/PACKET.json',cr+'/native/r1-input/PACKET.json',cr+'/native/r1-input/ORIGIN.json',harness]:source_pins[p]['sha256']=sha(blob(p))
inputs_path=packet+'/adoption-dryrun-d13766a/INPUTS.json';inputs=json.loads(blob(inputs_path));expected=inputs['preserved_receipts'][manifest];checks['manifest_sha_matches_retained_adoption_receipt']=sha(blob(manifest))==expected
origin=json.loads(blob(cr+'/native/r1-input/ORIGIN.json'));checks['native_packet_exact_copy_of_retained_packet']=sha(blob(packet+'/PACKET.json'))==sha(blob(cr+'/native/r1-input/PACKET.json'))==origin['sha256']
manifest_doc=json.loads(blob(manifest));refs={}
def walk(obj):
 if isinstance(obj,dict):
  if isinstance(obj.get('path'),str) and isinstance(obj.get('sha256'),str):refs[obj['path']]=obj['sha256']
  for v in obj.values():walk(v)
 elif isinstance(obj,list):
  for v in obj:walk(v)
walk(manifest_doc)
reference_checks={p:{'expected':digest,'actual':sha(blob(p))} for p,digest in refs.items()};checks['all_manifest_pinned_references_match']=all(v['expected']==v['actual'] for v in reference_checks.values())
claimpath=packet+'/applied-v1/CLAIMS.proposed.jsonl';checks['expected_five_claim_sha_matches_retained_artifact']=sha(blob(claimpath))=='9ddb845bd75f877ba86c5742e9e4e799f6af1871d5b76d7c223792419a2fd897'
checks['dry_run_has_no_publish_argument']=not any(isinstance(n,ast.Constant) and n.value=='--publish' for n in ast.walk(tree))
report={'commit':pin,'checks':checks,'all_checks_pass':all(checks.values()),'source_pins':source_pins,'manifest_expected_sha256':expected,'retained_manifest_receipt':inputs_path,'manifest_reference_checks':reference_checks,'scope':'Read-only Git tree and bounded blob checks; no native execution or refresh of historical pins.'}
(base/'path-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':checks,'all_checks_pass':all(checks.values()),'manifest_sha256':expected,'reference_count':len(reference_checks)}))
