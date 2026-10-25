"""One-case manual Stage19 completion using existing exact reference helpers.

The ordinary assembler has no manual later-source-search input. This script keeps
its emitted decision and frozen dossier, copies exact existing references through
the existing helper, and records the only manual claim supplement separately.
It does not replace or weaken any gate: overlay-check and actual checker run next.
"""
from copy import deepcopy
from pathlib import Path
import json, sys, hashlib
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'jobs/claim-kit'))
from assemble import _reference, _records, derive_inventory, canonical_sha
from status_overlay import check_working_claim
B=Path(__file__).resolve().parent
bundle=Path(sys.argv[1]).resolve()
def read(p):return json.loads(p.read_text())
def put(name,obj):
 p=bundle/name
 if p.exists():raise RuntimeError('refusing overwrite '+str(p))
 p.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
 return hashlib.sha256(p.read_bytes()).hexdigest()
d=read(bundle/'DOSSIER.json');s=read(bundle/'LIFECYCLE_DECISION.confirmed.json')
assert s['approved'] is True and s['dossier_sha256']==d['fingerprint']
assert d['instrument_id']=='EO:10014' and d['whole_order_status']=='no'
clauses,evidence,errors=derive_inventory(d,s['inventory_overrides']);assert not errors,errors
evidence={**_records(d),**evidence};selected=s['clauses'];assert len(selected)==len(clauses)==1
c=clauses[0];cd=selected[0]
assert c['scope_id']==cd['scope_id']
end={'date':cd['effective_date'],'actor':evidence[cd['end_id']]['actor_id'],'mechanism':evidence[cd['end_id']]['verb'],'source':_reference(cd['end_id'],evidence,errors)}
claim={'schema':'eo-lifecycle-claim/v1','instrument_id':'EO:10014','whole_order_status':'no','original_representation':_reference(d['original_source_id'],evidence,errors),'operative_clauses':[{'scope_id':c['scope_id'],'original_operative_text':c['text'],'original_source':_reference(c['id'],evidence,errors),'state_at_cutoff':'terminated','later_events':[],'first_end':end,'judgment_reason':cd['reason']}],'whole_order_end':deepcopy(end),'savings_residuals':{'state':s['savings']['state'],'reason':s['savings']['reason'],'source':_reference(s['savings']['source_id'],evidence,errors)},'later_source_search':[],'research_rationale':s['research_rationale'],'unresolved_material_gaps':deepcopy(s['unresolved_material_gaps']),'claim_kit':{'dossier_sha256':d['fingerprint'],'agent':s['agent'],'producer_approved':True,'original_pages_confirmed':True,'inventory_overrides':deepcopy(s['inventory_overrides']),'status_overlay':deepcopy(d['status_overlay'])}}
assert not errors, errors
before=put('CLAIM.before_manual_search.json',claim)
searches=read(B/'MANUAL_SEARCH_ENTRIES.v1.json');claim['later_source_search']=searches
# Source fields and adjudicative conclusions are identical before and after this
# supplement. The search entries are producer-written, not forged machine IDs.
final=bundle/'CLAIMS.working.v1.jsonl'
assert not final.exists()
final.write_text(json.dumps(claim,ensure_ascii=False,sort_keys=True)+'\n')
check_errors=check_working_claim(ROOT,claim,read(bundle/'PROMOTION_PROPOSAL.json'),read(bundle/'STATUS_DECISION.json'),read(bundle/'STATUS_REVIEW.json'),read(bundle/'EVIDENCE.json'))
receipt={'schema':'eo-manual-claim-supplement/v1','instrument_id':'EO:10014','reason':'Existing assembler accepts only frozen machine-search IDs; dossier has none. Existing Stage19 manual completion preserves exact dossier reference helpers and supplements only actual producer search entries. No source, event, status, source grade, approval or gate was invented.','before_path':str((bundle/'CLAIM.before_manual_search.json').relative_to(ROOT)),'before_file_sha256':before,'after_path':str(final.relative_to(ROOT)),'after_file_sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'after_claim_sha256':canonical_sha(claim),'changed_fields':['later_source_search'],'search_input':str((B/'MANUAL_SEARCH_ENTRIES.v1.json').relative_to(ROOT)),'search_input_sha256':hashlib.sha256((B/'MANUAL_SEARCH_ENTRIES.v1.json').read_bytes()).hexdigest(),'overlay_check_errors':check_errors,'independent_review_required_on_final_hash':True,'owner_adoption':False}
put('MANUAL_SUPPLEMENT_RECEIPT.json',receipt)
print(json.dumps(receipt,indent=2))
if check_errors:raise SystemExit(1)
