"""Byte/version and no-write audit of a completed research checkpoint; no new legal review."""
from pathlib import Path
import json,hashlib,subprocess,datetime,re,csv,zipfile
repo=Path(__file__).resolve().parents[5]
r=repo/'research/excavator/machiavelli-modern-undecided-20261105/continuation-20261105'
cache={}
def sha(path):
 p=Path(path)
 if p not in cache:cache[p]=hashlib.sha256(p.read_bytes()).hexdigest()
 return cache[p]
def load(path):return json.loads(Path(path).read_bytes())
errors=[]
def verify(path,digest,label):
 p=repo/path
 ok=p.is_file() and sha(p)==digest
 if not ok:errors.append({'label':label,'path':path,'expected_sha256':digest,'actual_sha256':sha(p) if p.is_file() else None})
 return ok
# Restrict discovery to this campaign's retained source index and explicit repository paths
# in its JSON/text, not a global corpus/cache scan.
paths=set()
for p in r.parent.rglob('*'):
 if p.is_file() and not any(s.startswith('.') for s in p.relative_to(r.parent).parts) and 'cache' not in p.parts and 'native-prior-baseline' not in p.parts and 'empty-prior' not in p.parts:
  paths.add(p)
texts=[]
for p in list(paths):
 if p.suffix in {'.json','.jsonl','.md'} and p.stat().st_size<2000000:
  try:texts.append(p.read_text())
  except UnicodeDecodeError:pass
for text in texts:
 for q in re.findall(r'(?:research|jobs)/[^\s"<>`]+',text):
  q=q.rstrip(',;:)\\')
  p=repo/q
  if len(q)<800 and p.is_file():paths.add(p)
bysha={}
for p in paths:
 # PNG targets and download caches are checked by their exact manifests below.
 if p.suffix in {'.png','.zip','.bin'}:continue
 bysha.setdefault(sha(p),[]).append(p.relative_to(repo).as_posix())
latest={}
for folder in ['review-b01','review-b02a','review-b02b','review-b01-dtv-v4']:
 for p in (r/folder).glob('EO_*/REVIEW.json'):latest[load(p)['instrument_id']]=p
rows=[];source_seen={};source_missing=[]
for iid,p in sorted(latest.items()):
 d=load(p);v=d.get('producer_version',d.get('reviewed_version',{}));checks=[]
 if v.get('path'):checks.append(('native',v['path'],v['sha256']))
 for key in ['native','analysis','source_manifest','freeze','status']:
  if v.get(key+'_path'):checks.append((key,v[key+'_path'],v[key+'_sha256']))
 for label,path,digest in checks:verify(path,digest,iid+':'+label)
 associated=d.get('associated_reviewed_content_sha256',{})
 for label,h in associated.items():
  if h not in bysha:errors.append({'label':iid+':'+label,'unavailable_exact_hash':h})
 # Verify all hashes of examined source representations against exact held repository bytes.
 ss=d.get('sources_independently_inspected',d.get('source_examination',d.get('source_inspections',[])))
 for s in ss:
  for k in ['raw_sha256','text_sha256','retained_extraction_sha256']:
   h=s.get(k)
   if h:
    source_seen[h]=source_seen.get(h,0)+1
    if h not in bysha:source_missing.append({'instrument_id':iid,'hash_role':k,'sha256':h})
 complete=d.get('exact_scientific_completeness',{}).get('complete',False)
 if 'full_whole_lifecycle_complete' in d:complete=d['full_whole_lifecycle_complete']
 if d.get('whole_lifecycle_completeness'):complete=False
 fam=d.get('independence',d.get('reviewer',{}))
 if isinstance(fam,dict):different=fam.get('different_family',fam.get('different_family_certification',False))
 else:different=False
 assert different is False
 native=load(repo/(v.get('native_path') or v.get('path')))
 assert native.get('approved') is False
 rows.append({'instrument_id':iid,'review_path':p.relative_to(repo).as_posix(),'review_sha256':sha(p),'version_bindings':checks,'associated_exact_hashes_present':all(h in bysha for h in associated.values()),'scientific_complete_in_reviewed_scope':complete,'different_family_acceptance':different,'native_approved':False})
# Exact three-version supplement resolves previously qualified old text occurrences.
resolution=load(r/'review-b02a/SOURCE_VERSION_RESOLUTION.json')
for s in resolution['sources']:
 verify(s['claimed_public_text_path'],s['exact_text_sha256'],'B02a exact source version')
 assert s['raw_sha256'] in bysha
resolved={s['exact_text_sha256'] for s in resolution['sources']}
source_missing=[x for x in source_missing if x['sha256'] not in resolved]
if source_missing:errors.extend({'label':'source hash unavailable',**x} for x in source_missing)
historical_status=load(r.parent/'CASE_DISPOSITIONS.json')
status_no=0;status_hold=0;status_bindings=0;native_bundles=0
for iid,x in historical_status.items():
 decision=load(repo/x['decision_path'])
 # Native status contracts bind the canonical parsed decision object, while
 # the public review receipt is pinned by exact raw bytes.
 decision_hash=hashlib.sha256(json.dumps(decision,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
 if decision_hash!=x['decision_sha256']:errors.append({'label':'historical canonical status decision '+iid,'expected_sha256':x['decision_sha256'],'actual_sha256':decision_hash})
 review=load(repo/x['review_path']);assert review['decision_sha256']==decision_hash
 verify(x['review_path'],x['review_sha256'],'historical exact status review '+iid);status_bindings+=2
 if x['status_recommendation']=='no':status_no+=1
 else:status_hold+=1
 assert not x['status_adopted'] and not x['different_family_requirement_satisfied']
 if x.get('native_status_proposal'):native_bundles+=1
assert (status_no,status_hold,native_bundles)==(18,2,18)
assignment=load(r/'ASSIGNMENTS.json');dispatch=[]
for x in assignment['assignments']:
 if x.get('dispatch_receipt'):
  verify(x['dispatch_receipt'],x['dispatch_receipt_sha256'],'historical dispatch '+x['group'])
  dispatch.append({'group':x['group'],'path':x['dispatch_receipt'],'sha256':x['dispatch_receipt_sha256'],'instrument_count':len(x['instrument_ids'])})
parts=load(r/'LARGE_SOURCE_PARTS.json');large=[]
for s in parts['sources']:
 verify(s['target'],s['sha256'],'large source target')
 h=hashlib.sha256();n=0
 for part in s['parts']:
  verify(part['path'],part['sha256'],'exact source part');b=(repo/part['path']).read_bytes();assert len(b)==part['bytes'];h.update(b);n+=len(b)
 assert n==s['bytes'] and h.hexdigest()==s['sha256']
 large.append({'target':s['target'],'sha256':s['sha256'],'bytes':n,'parts':len(s['parts']),'exact':True})
images=load(r/'IMAGE_BUNDLES.json');unique=set();targets=0
for b in images['bundles']:
 verify(b['path'],b['sha256'],'image bundle');assert (repo/b['path']).stat().st_size==b['bytes']
 with zipfile.ZipFile(repo/b['path']) as z:
  for f in b['files']:
   v=z.read(f['member']);assert len(v)==f['bytes'] and hashlib.sha256(v).hexdigest()==f['sha256'];unique.add(f['sha256'])
   for p in f['targets']:verify(p,f['sha256'],'page image target');targets+=1
replay=load(r/'ASSET_MATERIALIZATION_REPLAY.transport-v2.json')
assert len(replay['sources'])==5 and replay['images']['bundles_checked']==48 and replay['images']['already_exact']+replay['images']['restored']==719
# Check materialized canonical bytes against baseline Git metadata without lazy-fetching
# historical object bodies. Missing sparse paths are explicitly not called unchanged bytes.
base={}
for line in subprocess.check_output(['git','ls-tree','-rz','HEAD'],cwd=repo).split(b'\0'):
 if line:
  a,p=line.decode().split('\t');base[p]=a.split()[2]
def blobsha(p):
 b=p.read_bytes();return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
canonical=[p for p in base if p.startswith('research/readiness/claims/') or p.startswith('research/readiness/reviews/') or p in ['research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv','jobs/readiness-tracker/output/READINESS_BY_ORDER.csv','jobs/readiness-tracker/output/TRACKER.md']]
present=[p for p in canonical if (repo/p).is_file()]
changed=[p for p in present if blobsha(repo/p)!=base[p]]
new=[]
for folder in ['research/readiness/claims','research/readiness/reviews']:
 for p in (repo/folder).glob('*'):
  if p.is_file() and p.relative_to(repo).as_posix() not in base:new.append(p.relative_to(repo).as_posix())
assert not changed and not new
status=repo/'research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv'
statusrows=list(csv.DictReader(status.open()))
assert len(statusrows)==4291
stats={x.get('instrument_id'):x.get('provisional_substantive_status') for x in statusrows}
assert not (set(latest)&set(stats))
expected_support={'EO:12965','EO:12980','EO:13053','EO:13081','EO:13102','EO:13108','EO:13114','EO:13255'}
assert {x['instrument_id'] for x in rows if x['scientific_complete_in_reviewed_scope']}==expected_support
assert len(rows)==20
report={'schema':'eo-continuation-checkpoint-validation/v1','generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Read-only exact-version, retained-byte and no-canonical-write audit. No new legal review or scientific admission.','baseline_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),'latest_public_reviews':rows,'counts':{'public_latest_reviews':20,'supported_in_scoped_scientific_review':8,'partial_whole_lifecycle_incomplete':12,'same_family_NO_status_recommendations':18,'status_NULL_HOLD':2,'different_family_acceptances':0,'adopted_statuses':0,'canonical_whole_lifecycle_claims':0,'new_review_ready_dossiers':0,'human_certifications':0},'reviewed_source_hashes':{'unique':len(source_seen),'representation_occurrences':sum(source_seen.values()),'unavailable':source_missing,'verification':'Each available hash maps to exact current retained repository bytes. Byte verification does not independently repeat prior semantic/source examination.'},'B01_public_version_closure':{'path':str((r/'review-source-closure/MANIFEST.json').relative_to(repo)),'sha256':sha(r/'review-source-closure/MANIFEST.json'),'objects':3,'qualification':'Three amendments associated proposed_analysis_json hash resolves to an88byte non-substantive context notice, not a separate legal analysis. Two government parent extraction versions are explicit exact bytes; unchanged reviews and native proposals remain pinned.'},'exact_source_version_supplement':{'path':str((r/'review-b02a/SOURCE_VERSION_RESOLUTION.json').relative_to(repo)),'sha256':sha(r/'review-b02a/SOURCE_VERSION_RESOLUTION.json'),'previously_unavailable_occurrences_resolved':28,'exact_versions':3},'large_source_materialization':large,'image_materialization':{'bundles_checked':len(images['bundles']),'unique_unchanged_png_payloads':len(unique),'exact_target_paths':targets,'replay_path':str((r/'ASSET_MATERIALIZATION_REPLAY.transport-v2.json').relative_to(repo)),'replay_sha256':sha(r/'ASSET_MATERIALIZATION_REPLAY.transport-v2.json'),'network_requests':0},'canonical_guard':{'baseline_tracked_paths_in_scope':len(canonical),'materialized_paths_exact':len(present),'sparse_absent_not_revalidated':len(canonical)-len(present),'changed_materialized_paths':changed,'new_claim_or_review_paths':new,'authoritative_status_rows':len(statusrows),'assigned_twenty_still_unset':True},'historical_status_guard':{'canonical_decision_and_exact_review_hash_bindings':status_bindings,'hash_rule':'Status decision hashes follow native canonical JSON contract; review receipt hashes pin raw bytes. Lifecycle proposal/source hashes pin raw bytes.','NO_recommendations':status_no,'NULL_HOLD':status_hold,'experimental_native_bundles':native_bundles,'new_adoptions':0},'historical_research_dispatch_receipts':dispatch,'native_validation_scope':'Historical 20 fresh-at-dispatch research eligibility receipts and 18 experimental status bundles remain their frozen historical evidence; this audit does not renew fingerprints, certify native filing or equate research approval with source/schema/adoption acceptance.','Bentham':{'plan_read_at_main':'6fe45a9cce168cf05e82c91e4b0d51a58de70eff','wave_predates_rule':True,'batch_attempted':20,'submitted_native_claims':0,'filed_native_claims':0,'actual_usd':None,'gate_command_exit':1,'gate_reason':'Actual completed research action is absent from ranked production plan. No unrelated stratum/cost substituted; no valid gate verdict or retroactive compliance claimed.','usage_command_exit':0,'usage_transcripts_found':0,'token_counts':None,'usage_reason':'Existing CLI only discovers Claude Code transcripts; none available on this machine for this OpenAI-hosted wave. Empty telemetry is unavailable, not zero cost.','next_production':'Stopped. No new production wave. Future work reads current owner-ranked plan and obtains real cost/yield measurements.'},'NORTON':'Optional factual registry route, not universal ordinary claim-kit source admission. Existing optional pilot covers12 instruments and new proposals would cover17; expansion needs separately reviewed implementation change. Ordinary proposed SOURCE_SUPPLEMENT route remains subject to exact source review, eligibility, producer reaffirmation and whole-case review. No wet-paper authentication prerequisite introduced.','errors':errors,'all_byte_version_checks_pass':not errors}
(r/'VALIDATION.final.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'reviews':len(rows),'supported':len(expected_support),'source_hashes':len(source_seen),'source_hashes_unavailable':len(source_missing),'large_sources':len(large),'image_bundles':len(images['bundles']),'image_targets':targets,'canonical_present_exact':len(present),'canonical_missing_sparse':len(canonical)-len(present),'errors':errors},indent=2))
