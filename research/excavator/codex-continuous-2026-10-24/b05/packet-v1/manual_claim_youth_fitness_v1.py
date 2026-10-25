"""Reuse b02's exact-reference manual Stage19 search supplement for this pair.

Requires a real reviewed overlay bundle and producer-reconfirmed lifecycle sheet.
Preserves the failed ordinary overlay-assemble output, all dossier/source pins,
existing working-status label, ownerfalse, and all subsequent gates.
"""
from copy import deepcopy
from pathlib import Path
import json,sys,hashlib
B=Path(__file__).resolve().parent;R=B.parents[4];sys.path.insert(0,str(R/'jobs/claim-kit'))
from assemble import _reference,_records,derive_inventory,canonical_sha
from status_overlay import check_working_claim
bundle=Path(sys.argv[1]).resolve();read=lambda p:json.loads(p.read_text())
def put(name,obj):
 p=bundle/name
 if p.exists():raise RuntimeError('refusing overwrite '+str(p))
 p.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n');return hashlib.sha256(p.read_bytes()).hexdigest()
d=read(bundle/'DOSSIER.json');s=read(bundle/'LIFECYCLE_DECISION.confirmed-v1.json');n=int(d['instrument_id'].split(':')[1])
assert n in (10740,10785) and d['whole_order_status']=='no'
assert s['approved'] is True and s['dossier_sha256']==d['fingerprint']
evidence=_records(d);errors=[]
if s['inventory_overrides']:
 clauses,extra,errors=derive_inventory(d,s['inventory_overrides']);evidence.update(extra)
else:clauses=d['clauses']
assert not errors and len(clauses)==len(s['clauses'])==2,errors
selected={x['scope_id']:x for x in s['clauses']}
c={'schema':'eo-lifecycle-claim/v1','instrument_id':d['instrument_id'],'whole_order_status':'no','original_representation':_reference(d['original_source_id'],evidence,errors),'operative_clauses':[],'whole_order_end':None,'savings_residuals':{'state':s['savings']['state'],'reason':s['savings']['reason'],'source':_reference(s['savings']['source_id'],evidence,errors)},'later_source_search':[],'research_rationale':s['research_rationale'],'unresolved_material_gaps':deepcopy(s['unresolved_material_gaps']),'claim_kit':{'dossier_sha256':d['fingerprint'],'agent':s['agent'],'producer_approved':True,'original_pages_confirmed':True,'inventory_overrides':deepcopy(s['inventory_overrides']),'status_overlay':deepcopy(d['status_overlay'])}}
for cl in clauses:
 cd=selected[cl['scope_id']];assert cd['effective_date_confirmed'] is True
 end={'date':cd['effective_date'],'actor':evidence[cd['end_id']]['actor_id'],'mechanism':evidence[cd['end_id']]['verb'],'source':_reference(cd['end_id'],evidence,errors)}
 later=[]
 for event in cd['later_events']:
  assert event['effective_date_confirmed'] is True
  ref=_reference(event['id'],evidence,errors)
  ev={'effective_date':event['effective_date'],'actor':evidence[event['id']]['actor_id'],'mechanism':event['mechanism'],'source':ref}
  # Both whole original and whole actor are existing exact dossier references.
  # Quote the corresponding operative before/after text while retaining their source.
  old=cl['text'];actor=ref['quote'];idx=cl['scope_id'].split('#')[1]
  if idx=='1':a=actor.index('1. The President');z=actor.index('2. Section',a)
  else:a=actor.index('2. Section');z=actor.index('D w ig h t',a)
  ev.update(text_before=old,text_after=actor[a:z],sources=[_reference(cl['id'],evidence,errors),deepcopy(ref)],human_review_note='Substantive membership change; continuation amended under owner strike-and-insert ruling, not first cessation. Exact OCR text retained and checked against official page images.')
  later.append(ev)
 c['operative_clauses'].append({'scope_id':cl['scope_id'],'original_operative_text':cl['text'],'original_source':_reference(cl['id'],evidence,errors),'state_at_cutoff':cd['state'],'first_end':end,'later_events':later,'judgment_reason':cd['reason']})
c['whole_order_end']=deepcopy(max((x['first_end']for x in c['operative_clauses']),key=lambda x:x['date']))
assert not errors,errors
before=put('CLAIM.before_manual_search.v1.json',c)
searches=read(B/'MANUAL_SEARCH_ENTRIES.v1.json');c['later_source_search']=searches[str(n)]
final=bundle/'CLAIMS.working.v1.jsonl';assert not final.exists();final.write_text(json.dumps(c,ensure_ascii=False,sort_keys=True)+'\n')
errs=check_working_claim(R,c,read(bundle/'PROMOTION_PROPOSAL.json'),read(bundle/'STATUS_DECISION.json'),read(bundle/'STATUS_REVIEW.json'),read(bundle/'EVIDENCE.json'))
receipt={'schema':'eo-manual-claim-supplement/v1','instrument_id':d['instrument_id'],'reason':'Existing undecided frozen dossier has no machine-search IDs. Reuse the b02 manual exact-reference Stage19 route, supplementing only actual producer search records after preserving the missing-search assembler rejection. Original inventory, judgments, sources and reviewed working-status label retained; no source/evidence/approval gate weakened.','route_precedent':'research/excavator/codex-continuous-2026-10-24/b02/manual_claim_eo10014.py','before_path':str((bundle/'CLAIM.before_manual_search.v1.json').relative_to(R)),'before_sha256':before,'after_path':str(final.relative_to(R)),'after_file_sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'after_claim_sha256':canonical_sha(c),'changed_fields':['later_source_search'],'search_input':str((B/'MANUAL_SEARCH_ENTRIES.v1.json').relative_to(R)),'search_input_sha256':hashlib.sha256((B/'MANUAL_SEARCH_ENTRIES.v1.json').read_bytes()).hexdigest(),'overlay_check_errors':errs,'owner_adoption':False,'independent_whole_lifecycle_review_required':True}
put('MANUAL_SUPPLEMENT_RECEIPT.v1.json',receipt);print(json.dumps(receipt,indent=2));assert not errs,errs
