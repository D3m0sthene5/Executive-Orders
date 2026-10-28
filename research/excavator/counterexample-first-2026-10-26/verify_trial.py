"""Read-only verification of the fixed trial and its exact filed/source versions."""
from pathlib import Path
import hashlib,json,sys
RUN=Path(__file__).resolve().parent
ROOT=RUN.parents[2]
def load(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def safe(rel):
 p=(ROOT/rel).resolve()
 if not p.is_relative_to(ROOT):raise ValueError('unsafe path '+str(rel))
 return p
assert sha(RUN/'DESIGN.json')==(RUN/'DESIGN.sha256').read_text().split()[0]
expected={'EO:7975A','EO:8083','EO:8123','EO:8126','EO:8915','EO:8992'}
assert {r['instrument_id'] for r in load(RUN/'DESIGN.json')['members']}==expected
selected=[json.loads(x) for x in (RUN/'packet/PROPOSED_SELECTION.v3.jsonl').read_text().splitlines()]
filed={}
for p in (ROOT/'research/readiness/claims').glob('codex-counterexample-20261026*.jsonl'):
 for line in p.read_text().splitlines():
  c=json.loads(line);assert c['instrument_id'] not in filed;filed[c['instrument_id']]=c
assert len(filed)==5 and 'EO:8915' not in filed
assert {c['instrument_id']:canonical(c) for c in selected}=={i:canonical(c) for i,c in filed.items()}
sys.path.insert(0,str(ROOT/'research/stage19/code'));import claim_gate
for c in selected:assert not claim_gate.validate_claim(c,expected_status=c['whole_order_status'])
texts={};raws={};spans=0
for c in selected:
 def walk(v):
  global spans
  if isinstance(v,dict):
   if v.get('text_path') and v.get('text_sha256'):
    f=safe(v['text_path']);texts.setdefault(str(f),sha(f));assert texts[str(f)]==v['text_sha256']
    if 'quote' in v and isinstance(v.get('char_start'),int):
     assert f.read_text(encoding='utf-8')[v['char_start']:v['char_end']]==v['quote'];spans+=1
   if v.get('sha256') and (v.get('url') or v.get('local_path')):
    f=ROOT/'jobs/astra-source-retention/output/pdf'/(v['sha256']+'.pdf')
    if f.exists():raws.setdefault(str(f),sha(f));assert raws[str(f)]==v['sha256']
   for x in v.values():walk(x)
  elif isinstance(v,list):
   for x in v:walk(x)
 walk(c)
for x in load(RUN/'REMOTE_SOURCE_REQUESTS.json'):
 f=ROOT/'jobs/astra-source-retention/output/pdf'/(x['expected_sha256']+'.pdf');assert sha(f)==x['expected_sha256']
checker=load(RUN/'packet/selected-checker-v3/SUMMARY.json');assert checker['claims_all_checks_passed']==5 and checker['claims_mechanical_unverified']==0
for where,num in [('complete-publish-v2',4),('packet/continuation-7975a-v2/complete-publish-v1',1)]:
 d=load(RUN/where/'PUBLICATION.json');assert d['written'] and d['claims']==num and sha(safe(d['path']))==d['sha256']
combined=load(RUN/'packet/final-combined-tracker/TRACKER_REPLAY.json');assert combined['before']['ready_for_human_review']==277 and combined['after']['ready_for_human_review']==279
assert sorted(i for i,x in combined['selected'].items() if x['after']['ready_for_human_review']=='yes')==['EO:7975A','EO:8083']
for pair,label in [(1,'P8'),(2,'B9'),(3,'M2')]:
 p=RUN/f'packet/review/pair{pair}';seed=load(p/'SEED_RECEIPT.json');reviews=[json.loads(l) for l in (p/'BLIND_REVIEW.jsonl').read_text().splitlines()];x=next(x for x in reviews if x.get('label')==label);assert x['verdict']=='rejected' and x['claim_sha256']==seed['planted_claim_sha256']
print(json.dumps({'fixed_cases':6,'filed_reviewed_whole_case_proposals':5,'notice_blocked_cases':1,'native_checker_pass':5,'ready_in_isolated_combined_replay':2,'raw_pdf_versions':24,'exact_text_spans_rechecked':spans,'controls_caught':3,'human_certifications':0,'runtime_or_status_changes':0,'significant_hours_saving_established':False}))
