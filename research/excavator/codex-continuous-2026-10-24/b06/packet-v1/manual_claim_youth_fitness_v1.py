"""Existing b02/b05 exact-reference manual search supplement; no core changes.
Run only after exact status review, reconfirmed lifecycle and preserved real assembler rejection.
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
d=read(bundle/'DOSSIER.json');s=read(bundle/'LIFECYCLE_DECISION.confirmed-v1.json');n=int(d['instrument_id'].split(':')[1]);chain=read(B/'AMENDMENT_CHAIN.v1.json')
assert n in (10673,10772) and d['whole_order_status']=='no'
assert s['approved']is True and s['dossier_sha256']==d['fingerprint']
evidence=_records(d);clauses,extra,errors=derive_inventory(d,s['inventory_overrides']);evidence.update(extra)
assert not errors and len(clauses)==len(s['clauses'])==({10673:7,10772:3}[n]),errors
selected={x['scope_id']:x for x in s['clauses']}
c={'schema':'eo-lifecycle-claim/v1','instrument_id':d['instrument_id'],'whole_order_status':'no','original_representation':_reference(d['original_source_id'],evidence,errors),'operative_clauses':[],'whole_order_end':None,'savings_residuals':{'state':s['savings']['state'],'reason':s['savings']['reason'],'source':_reference(s['savings']['source_id'],evidence,errors)},'later_source_search':[],'research_rationale':s['research_rationale'],'unresolved_material_gaps':deepcopy(s['unresolved_material_gaps']),'claim_kit':{'dossier_sha256':d['fingerprint'],'agent':s['agent'],'producer_approved':True,'original_pages_confirmed':True,'inventory_overrides':deepcopy(s['inventory_overrides']),'status_overlay':deepcopy(d['status_overlay'])}}
for cl in clauses:
 cd=selected[cl['scope_id']];assert cd['effective_date_confirmed']is True and cd['mechanism']=='revoke'
 end={'date':cd['effective_date'],'actor':evidence[cd['end_id']]['actor_id'],'mechanism':cd['mechanism'],'source':_reference(cd['end_id'],evidence,errors)}
 later=[]
 for event in cd['later_events']:
  assert event['effective_date_confirmed']is True
  ref=_reference(event['id'],evidence,errors);actor=evidence[event['id']]['actor_id'];ch=next(x for x in chain if x['actor']==actor and cl['scope_id']in x['affected_scopes'])
  ev={'effective_date':event['effective_date'],'actor':actor,'mechanism':event['mechanism'],'source':ref,'human_review_note':ch['change']+' No first cessation is inferred. Exact OCR quotations retained and compared with previously inspected official page images.'}
  if n==10673:
   beforeid='ORIGINAL:EO:10673' if ch['before']['instrument_id']=='EO:10673' else 'ACTOR_TEXT:'+ch['before']['instrument_id']
   ev.update(text_before=ch['before']['quote'],text_after=ch['after']['quote'],sources=[_reference(beforeid,evidence,errors),deepcopy(ref)])
   if cl['scope_id'].endswith('sec3'):
    ev['context_qualification']='These are the successive sec1 membership texts defining the departments reached by sec3. The words ofsec3 themselves remain unchanged: '+cl['text']
  else:
   ev.update(text_before=cl['text'],text_after=cl['text'],sources=[_reference(cl['id'],evidence,errors),deepcopy(ref)],context_qualification='The target designation wording is unchanged. The parent membership amendment changes the Council chairman from Interior Secretary to HEW Secretary; the full10931 source supplies that contextual fact. This is not a direct amendment or revocation of10772.')
  later.append(ev)
 c['operative_clauses'].append({'scope_id':cl['scope_id'],'original_operative_text':cl['text'],'original_source':_reference(cl['id'],evidence,errors),'state_at_cutoff':cd['state'],'first_end':end,'later_events':later,'judgment_reason':cd['reason']})
c['whole_order_end']=deepcopy(max((x['first_end']for x in c['operative_clauses']),key=lambda x:x['date']))
assert not errors,errors
before=put('CLAIM.before_manual_search.v1.json',c)
c['later_source_search']=read(B/'MANUAL_SEARCH_ENTRIES.v1.json')[str(n)]
final=bundle/'CLAIMS.working.v1.jsonl';assert not final.exists();final.write_text(json.dumps(c,ensure_ascii=False,sort_keys=True)+'\n')
errs=check_working_claim(R,c,read(bundle/'PROMOTION_PROPOSAL.json'),read(bundle/'STATUS_DECISION.json'),read(bundle/'STATUS_REVIEW.json'),read(bundle/'EVIDENCE.json'))
receipt={'schema':'eo-manual-claim-supplement/v1','instrument_id':d['instrument_id'],'reason':'Frozen undecided dossier has no machine-search IDs. Existing b02/b05 supported manual Stage19 route adds only actual bounded search records after preserving the ordinary assembler missing-search rejection. All exact evidence, complete inventory, status overlay label and ownerfalse preserved; no dossier/source/evidence/approval gates weakened.','route_precedent':'research/excavator/codex-continuous-2026-10-24/b05/packet-v1/manual_claim_youth_fitness_v1.py','before_path':str((bundle/'CLAIM.before_manual_search.v1.json').relative_to(R)),'before_sha256':before,'after_path':str(final.relative_to(R)),'after_file_sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'after_claim_sha256':canonical_sha(c),'changed_fields':['later_source_search'],'enrichment':'Exact before/after source text from AMENDMENT_CHAIN.v1.json accompanies explicit preserved legal judgments; ACTOR_TEXT11074 uses producer-confirmed revoke mechanism. Unneeded stale derivative-working-text disclosures from auto sheet are not used as original evidence; all actual references are held official originals.','search_input':str((B/'MANUAL_SEARCH_ENTRIES.v1.json').relative_to(R)),'search_input_sha256':hashlib.sha256((B/'MANUAL_SEARCH_ENTRIES.v1.json').read_bytes()).hexdigest(),'overlay_check_errors':errs,'owner_adoption':False,'independent_whole_lifecycle_review_required':True}
put('MANUAL_SUPPLEMENT_RECEIPT.v1.json',receipt);print(json.dumps(receipt,indent=2));assert not errs,errs
