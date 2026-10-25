"""One-case Stage19 partial research record after preserved assembler refusal.

Uses existing immutable reference helpers and gates. This is not an assembler or
gate change. The absent first ending and unresolved gaps remain explicit.
"""
from pathlib import Path
from copy import deepcopy
import json, sys, hashlib
ROOT = Path.cwd()
sys.path.insert(0, str(ROOT/'jobs/claim-kit'))
from assemble import _reference, _records, canonical_sha, check_claim
from status_overlay import check_working_claim
P = ROOT/'research/excavator/codex-continuous-2026-10-24/b03/packet-v1'
B = P/'overlay/proposal-v2'
def read(p): return json.loads(p.read_text())
def put(p, o):
    assert not p.exists(), p
    p.write_text(json.dumps(o, ensure_ascii=False, indent=2)+'\n')
def pin(p): return {'path':str(p.relative_to(ROOT)), 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
d = read(B/'DOSSIER.json')
s = read(B/'LIFECYCLE_DECISION.confirmed.v1.json')
assert s['approved'] is True and s['dossier_sha256'] == d['fingerprint']
assert d['instrument_id'] == 'EO:10030' and d['whole_order_status'] == 'no'
assert len(d['clauses']) == len(s['clauses']) == 2
e = _records(d); errors = []
ending = {'date':'1969-10-01','actor':'EO:11485','mechanism':'supersession',
          'source':_reference('ACT:EO:10030>EO:11485',e,errors)}
items = []
for n, (c, cd) in enumerate(zip(d['clauses'], s['clauses'])):
    assert c['scope_id'] == cd['scope_id']
    item = {'scope_id':c['scope_id'], 'original_operative_text':c['text'],
            'original_source':_reference(c['id'],e,errors),
            'state_at_cutoff':'terminated', 'later_events':[],
            'judgment_reason':cd['reason']}
    if n == 0:
        event = deepcopy(ending); event['effective_date'] = event.pop('date')
        item['later_events'] = [event]
    else:
        item['first_end'] = deepcopy(ending)
    items.append(item)
claim = {'schema':'eo-lifecycle-claim/v1','instrument_id':'EO:10030',
         'whole_order_status':'no',
         'original_representation':_reference(d['original_source_id'],e,errors),
         'operative_clauses':items,'whole_order_end':deepcopy(ending),
         'savings_residuals':{'state':s['savings']['state'],'reason':s['savings']['reason'],
                             'source':_reference(s['savings']['source_id'],e,errors)},
         'later_source_search':read(P/'MANUAL_SEARCH_ENTRIES.v1.json'),
         'research_rationale':s['research_rationale'],
         'unresolved_material_gaps':deepcopy(s['unresolved_material_gaps']),
         'claim_kit':{'dossier_sha256':d['fingerprint'],'agent':s['agent'],
                      'producer_approved':True,'original_pages_confirmed':True,
                      'inventory_overrides':[], 'status_overlay':deepcopy(d['status_overlay'])}}
assert not errors, errors
out = B/'CLAIMS.partial.v1.jsonl'; assert not out.exists()
out.write_text(json.dumps(claim,ensure_ascii=False,sort_keys=True)+'\n')
checked = check_working_claim(ROOT, claim, read(B/'PROMOTION_PROPOSAL.json'),
                             read(B/'STATUS_DECISION.json'),read(B/'STATUS_REVIEW.json'),read(B/'EVIDENCE.json'))
assert sorted(checked) == sorted(['clause_0_first_end','unresolved_material_gaps']), checked
receipt = {'schema':'eo-manual-partial-claim/v1','instrument_id':'EO:10030',
           'claim':pin(out),'claim_sha256':canonical_sha(claim),
           'decision':pin(B/'LIFECYCLE_DECISION.confirmed.v1.json'),
           'assembler_refusal':pin(P/'OVERLAY_ASSEMBLE.v1.log'),
           'reason':'Existing assembler requires complete first endings and search IDs. Normal Stage19 partial record preserves absent paragraph1 first_end, unresolved gaps and exact frozen reference helpers. Producer-written bounded searches are explicit; no machine search IDs invented.',
           'strict_and_gate_errors':checked,'non_gate_strict_errors':[],
           'analysis':pin(P/'ANALYSIS.v3.json'),'source_manifest':pin(P/'SOURCE_MANIFEST.v3.json'),
           'independent_lifecycle_review_required':True,'owner_accepted':False,
           'canonical_status_adopted':False}
put(B/'MANUAL_PARTIAL_RECEIPT.v1.json',receipt)
print(json.dumps(receipt,indent=2))
