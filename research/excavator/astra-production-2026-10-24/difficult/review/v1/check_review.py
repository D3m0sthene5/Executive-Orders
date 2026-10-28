import csv, hashlib, json, sys, copy, datetime, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[6]
D=ROOT/'research/excavator/astra-production-2026-10-24/difficult'
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'jobs/claim-kit'))
from lifecycle_obligations import resume_decision,digest

def j(p): return json.loads(p.read_text())
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(name, passed, detail=None): checks.append({'check':name,'passed':bool(passed),'detail':detail})
for p,sha in [('REVIEW_ASSIGNMENT.md','1b380058e567cd5b8de8ad148a77058763c5729b808e306b8ae936eec16e690c'),('MANIFEST.json','9c2dc83244c0f36f46a72dbd714e5a45e7d7332d49ccfd9997a44351ec6fd8fd')]:check('assigned:'+p,h(D/p)==sha,h(D/p))
for label, rows in [('manifest',j(D/'MANIFEST.json')['files']),('inputs',j(D/'INPUT_PINS.json')['files'])]:
 for row in rows:
  p=ROOT/row['path'];check(label+':'+row['path'],p.exists() and h(p)==row['sha256'] and p.stat().st_size==row['bytes'],{'sha256':h(p) if p.exists() else None})
eo=j(D/'EO_4314_RESEARCH.json');c=j(D/'HISTORICAL_CANDIDATE.json')
for label,path,spans in [('4314',ROOT/eo['source']['text_path'],list(eo['exact_held_text_spans'].values())),('7937-corrected',ROOT/c['source']['extracted_text_path'],[c['source']['exact_predecessor_reference'],c['source']['complete_7937_print_span']]),('7937-first-ocr',ROOT/c['earlier_print_conflict']['text_path'],[c['earlier_print_conflict']['exact_held_ocr']])]:
 t=path.read_text()
 for idx,span in enumerate(spans):check(label+':span'+str(idx),t[span['char_start']:span['char_end']]==span['quote'] and hashlib.sha256(span['quote'].encode()).hexdigest()==span['quote_sha256'])
searches=[]
for row in c['bounded_prior_identity_search']:
 rows=list(csv.DictReader((ROOT/row['path']).open(newline='')))
 hits=[{'row':i+2,'value':r} for i,r in enumerate(rows) if '1838-02-16' in ' '.join(str(v) for v in r.values()) or 'west sister' in ' '.join(str(v) for v in r.values()).lower()]
 check('bounded-search:'+row['path'],len(rows)==row['rows_scanned'] and not hits,{'rows':len(rows),'hits':hits})
 searches.append({'path':row['path'],'rows':len(rows),'hits':hits})
clark=list(csv.DictReader((ROOT/c['clark_input']['path']).open(newline='')))
selected=[r for r in clark if r['date']=='1838-02-16']
check('clark-exact-three-rows',selected==c['clark_input']['rows'])
prior=j(D/'EO_4314_PRIOR_ATTEMPTS.json');receipt=j(D/'EO_4314_CURRENT_RECEIPTS.json')
historical=[json.loads(s) for s in (ROOT/'research/excavator/2026-10-18/acquisition/ATTEMPTS.jsonl').read_text().splitlines() if s.strip()]
check('historical-attempt-exact',prior==[r for r in historical if r.get('wanted_id')=='EO::4314'])
frag=j(D/'EO_4314_FRAGMENT.json')
allfrags=[json.loads(s) for s in (ROOT/'jobs/pinakes-proquest-ingest/output/FRAGMENTS.jsonl').read_text().splitlines() if s.strip()]
check('fragment-exact-importer-row',frag in allfrags)
check('receipt-exact-fragment-data',receipt==[frag['data']])
check('grade-preserved',frag['grade']==eo['source']['grade']=='archival_replica_scan_pending_codebook' and eo['source']['acceptable_as_original'] is False and frag['acceptable_as_original'] is False)
check('standing-disclosure',eo['standing_disclosure']=='original not yet held; replace and re-check quotes when an official copy is retrieved.')
route=j(D/'ROUTE_PINS.json')
check('route-map-digest',hashlib.sha256(json.dumps(route['files'],sort_keys=True).encode()).hexdigest()==route['sha256'])
for p,sha in route['files'].items(): check('route:'+p,h(ROOT/p)==sha)
old=j(D/'EO_4314_RECONSTRUCTED_PRIOR_CHECKPOINT.json');cur=j(D/'EO_4314_CURRENT_CHECKPOINT.json')
dossier=j(D/'EO_4314_PRIOR_DOSSIER.json');requests=j(D/'EO_4314_UNRESOLVED_REQUESTS.json');context=j(D/'EO_4314_PRIOR_RESEARCH_CONTEXT.json')
replays={}
for label,checkpoint,receipts,path in [('unchanged',old,prior,'EO_4314_UNCHANGED_ROUTE_RESUME.json'),('changed',old,prior+receipt,'EO_4314_CHANGED_RECEIPT_RESUME.json'),('current',cur,prior+receipt,'EO_4314_CURRENT_UNCHANGED_RESUME.json')]:
 result=resume_decision(checkpoint,dossier,requests,route['sha256'],receipts,context);replays[label]=result;check('resume:'+label,result==j(D/path))
mutated=copy.deepcopy(prior);mutated[0]['time_utc']='2026-10-24T16:47:07Z'
time_only=resume_decision(old,dossier,requests,route['sha256'],mutated,context)
replays['same_failure_time_utc_only']=time_only
# This is a contract probe, separate from exact packet replay.
contract_probe={'only_changed_field':'source_results[0].time_utc','before':prior[0]['time_utc'],'after':mutated[0]['time_utc'],'expected_action':'defer_unchanged_source_block','actual_action':time_only['action'],'passed':time_only['action']=='defer_unchanged_source_block','engine_path':'jobs/claim-kit/lifecycle_obligations.py','engine_sha256':h(ROOT/'jobs/claim-kit/lifecycle_obligations.py')}
result={'schema':'eo-independent-source-review-validation/v1','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'packet_checks':checks,'packet_checks_all_pass':all(r['passed'] for r in checks),'packet_check_count':len(checks),'bounded_searches':searches,'resume_replays':replays,'retry_timestamp_contract_probe':contract_probe,'mechanical_success_is_not_substantive_approval':True}
(OUT/'CHECKS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'packet_checks':len(checks),'failures':[r for r in checks if not r['passed']],'timestamp_contract_probe':contract_probe,'search_rows_total':sum(x['rows'] for x in searches)},indent=2))
