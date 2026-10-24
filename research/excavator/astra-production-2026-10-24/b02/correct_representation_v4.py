"""Correct consumer source association/quoted wrappers only; preserve v3 judgments."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import time
ROOT=Path(__file__).resolve().parents[4];B=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'jobs/claim-kit'));import assemble
started=datetime.now(timezone.utc).isoformat();clock=time.monotonic()
def canon(v): return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p): return p.relative_to(ROOT).as_posix()
def pin(p): return {'path':rel(p),'sha256':sha(p)}
def save(n,v): (B/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ref_span(r,a,z):
 v=deepcopy(r);t=(ROOT/v['text_path']).read_bytes().decode();v.update(char_start=a,char_end=z,quote=t[a:z]);return v
oldpath=B/'PROPOSED_CLAIMS.v3.jsonl';newpath=B/'PROPOSED_CLAIMS.v4.jsonl'
assert not newpath.exists(),'Do not overwrite a frozen claim version'
old=[json.loads(x) for x in oldpath.read_text().splitlines()];new=deepcopy(old);audits=[]
page_marker=re.compile(r'(?m)^=== PDF page \d+ of \d+ ===\r?\n')
for c,original in zip(new,old):
 changes=[];s=c['original_representation'];t=(ROOT/s['text_path']).read_bytes().decode()
 start=page_marker.search(t).end()
 assert s['quote']==t and s['char_start']==0
 c['original_representation']=ref_span(s,start,len(t))
 changes.append({'path':'original_representation','operation':'Remove synthetic extraction metadata prefix from quotation; retain complete official page body, source URL, hash, full text path and page location.','old_char_start':0,'new_char_start':start,'char_end':len(t),'removed_prefix':t[:start]})
 refs=c.pop('research_sources');expanded=[]
 for i,r in enumerate(refs):
  q=r['quote'];matches=list(page_marker.finditer(q))
  if not matches:
   expanded.append(r);continue
  last=0;parts=[]
  for m in matches:
   if m.start()>last: parts.append(ref_span(r,r['char_start']+last,r['char_start']+m.start()))
   last=m.end()
  if last<len(q):parts.append(ref_span(r,r['char_start']+last,r['char_end']))
  assert ''.join(p['quote'] for p in parts)==page_marker.sub('',q)
  expanded.extend(parts)
  changes.append({'path':f'research_sources[{i}]','operation':'Split into supported source_refs with exact per-page spans; exclude only generated PDF-page separator. All substantive text and provenance retained.','removed_separators':[m.group(0) for m in matches],'old_span':[r['char_start'],r['char_end']],'new_spans':[[p['char_start'],p['char_end']] for p in parts]})
 c['source_refs']=expanded
 changes.append({'path':'research_sources','operation':'Rename to checker-supported source_refs; same references, with recorded generated-separator splits only.'})
 for i,cl in enumerate(c['operative_clauses']):
  end=cl.get('first_end')
  if end and 'legal_sources'in end:
   end['sources']=end.pop('legal_sources')
   changes.append({'path':f'operative_clauses[{i}].first_end.legal_sources','operation':'Rename to checker-supported sources; exact reference objects unchanged.'})
 if c.get('whole_order_end') and 'legal_sources'in c['whole_order_end']:
  c['whole_order_end']['sources']=c['whole_order_end'].pop('legal_sources')
  changes.append({'path':'whole_order_end.legal_sources','operation':'Rename to checker-supported sources; exact reference objects unchanged.'})
 c['research_provenance']['revision']='b02-v4-representation-correction'
 c['research_provenance']['representation_correction_audit']=rel(B/'REPRESENTATION_CORRECTION.v4.json')
 # Reverse only the enumerated representation changes and prove every other key unchanged.
 reverse=deepcopy(c)
 reverse['original_representation']=deepcopy(original['original_representation'])
 reverse.pop('source_refs');reverse['research_sources']=deepcopy(original['research_sources'])
 for cl in reverse['operative_clauses']:
  if isinstance(cl.get('first_end'),dict) and 'sources'in cl['first_end']:
   cl['first_end']['legal_sources']=cl['first_end'].pop('sources')
 if reverse.get('whole_order_end') and 'sources'in reverse['whole_order_end']:
  reverse['whole_order_end']['legal_sources']=reverse['whole_order_end'].pop('sources')
 reverse['research_provenance']['revision']=original['research_provenance']['revision']
 reverse['research_provenance'].pop('representation_correction_audit')
 assert reverse==original,'Unapproved semantic or other change'
 # Every revised/direct reference quote still maps to exact, hash-verified stored text.
 refs_to_check=[c['original_representation']]+c['source_refs']
 for cl in c['operative_clauses']:
  if cl.get('first_end'): refs_to_check+=cl['first_end']['sources']
 if c.get('whole_order_end'):refs_to_check+=c['whole_order_end']['sources']
 for r in refs_to_check:
  raw=(ROOT/r['text_path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['text_sha256'];assert raw.decode()[r['char_start']:r['char_end']]==r['quote']
 audits.append({'instrument_id':c['instrument_id'],'prior_claim_sha256':assemble.canonical_sha(original),'new_claim_sha256':assemble.canonical_sha(c),'changes':changes,'all_other_keys_exactly_unchanged':True,'substantive_statutory_text_exactly_preserved_after_removing_generated_separators':True,'checked_exact_reference_spans':len(refs_to_check),'legal_judgments_dates_gaps_and_operative_inventory_unchanged':True})
newpath.write_text(''.join(canon(c)+'\n' for c in new))
save('REPRESENTATION_CORRECTION.v4.json',{'schema':'eo-producer-representation-correction/v1','prior_claim_file':pin(oldpath),'new_claim_file':pin(newpath),'reason':'Actual complete-v1 failed closed: unsupported legal_sources/research_sources containers caused wrong-source fallback; whole original_representation quotation included generated extraction metadata. Generated PDF page separators also excluded from split statutory quotations. No checker or source policy changed.','actual_failure':pin(B/'review/complete-v1/EXCEPTIONS.json'),'actual_failure_csv':pin(B/'review/complete-v1/checker/CLAIM_CHECKS.csv'),'supported_container_definition':pin(ROOT/'jobs/claim-checker/checker.py'),'claims':audits,'semantic_difference':False,'original_full_source_availability_unchanged':True,'full_checker_repeated':False,'new_research_or_fetch':False})
gate=assemble._gate(ROOT);results=[]
for c in new:
 errors=gate.validate_claim(c,expected_status=c['whole_order_status']);strict=assemble.check_claim(c,ROOT)
 results.append({'instrument_id':c['instrument_id'],'claim_sha256':assemble.canonical_sha(c),'publication_kind':'partial_research','expected_gate_errors':errors,'strict_errors':strict,'non_gate_errors':[e for e in strict if e not in errors]})
assert all(not r['non_gate_errors'] for r in results),results
save('PRODUCER_GATES.v4.json',results)
save('SELECTED_VERSIONS.v4.json',{'selected_at_utc':datetime.now(timezone.utc).isoformat(),'agent':'astra-production-b02','producer_model_family':'OpenAI','claims':[dict(r,claim={**pin(newpath),'line':i+1}) for i,r in enumerate(results)],'human_certification':0})
save('CORRECTION_TELEMETRY.v4.json',{'script_started_utc':started,'script_completed_utc':datetime.now(timezone.utc).isoformat(),'script_wall_seconds':time.monotonic()-clock,'interactive_correction_start_utc':None,'interactive_checkpoint_utc':'2026-10-24T17:11:03Z','model_tokens':None,'cached_tokens':None,'model_dollars':None,'fetches':0,'full_checker_runs':0,'strict_gate_runs':1,'human_certification':0})
manifest=json.loads((B/'COMPLETION.producer.json').read_text())
for i,(m,c) in enumerate(zip(manifest['members'],new)):
 m.update(claim_sha256=assemble.canonical_sha(c),claim={**pin(newpath),'line':i+1})
for rec in manifest['receipts']:
 if rec['path'].endswith('/PRODUCER_GATES.json'): rec.update(pin(B/'PRODUCER_GATES.v4.json'))
 elif rec['path'].endswith('/SELECTED_VERSIONS.json'): rec.update(pin(B/'SELECTED_VERSIONS.v4.json'))
 else: assert sha(ROOT/rec['path'])==rec['sha256'], 'Prior receipt changed'
manifest['receipts'] += [pin(B/n) for n in ['REPRESENTATION_CORRECTION.v4.json','CORRECTION_TELEMETRY.v4.json']]
save('COMPLETION.producer.v4.json',manifest)
print(json.dumps({'claims':pin(newpath),'results':results,'completion':pin(B/'COMPLETION.producer.v4.json'),'correction_audit':pin(B/'REPRESENTATION_CORRECTION.v4.json')},indent=2))
