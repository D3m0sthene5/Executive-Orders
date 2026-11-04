"""Independent offline accounting. Frozen semantics only; no Valla freshness claim."""
import json, csv, hashlib
from pathlib import Path
from collections import Counter
p = Path(__file__).resolve().parents[1]
old = p.parent/'production-observability-20261104'
j = lambda f: json.loads(f.read_bytes())
canonical = lambda obj: json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
sha = lambda data: hashlib.sha256(data).hexdigest()
source = p/'experiment/inputs/erasmus-c1.jsonl'
packetfile = p/'paths/inputs/pr133/research/progress/maitland/valla-audit/correction-packet-v1/PACKET.json'
loaded = j(packetfile)
frozen = loaded['fingerprint']
assert frozen == sha(canonical({k:v for k,v in loaded.items() if k!='fingerprint'}))
ctx=loaded['valla_context']
ids = list(loaded['dossiers'])
claims = [json.loads(line) for line in source.read_bytes().splitlines()]
out = j(old/'historical/OUTCOMES.json')
native = {(r['instrument_id'],r['claim_sha256']) for r in out['completion_outcomes'] if r['campaign_id']=='erasmus' and r['batch']=='c1' and r['outcome']=='eligible' and r['exact_version_review_matched']}
exact_claims = {(r['instrument_id'],sha(canonical(r))) for r in claims}
assert exact_claims <= native
def source_objects(node):
    if isinstance(node,list):
        for v in node: yield from source_objects(v)
    elif isinstance(node,dict):
        if {'evidence_id','quote','text_sha256','char_start','char_end'} <= set(node): yield canonical(node)
        else:
            for v in node.values():yield from source_objects(v)
occurrences=[list(source_objects(r)) for r in claims]
total=sum(map(len,occurrences))
allrefs=set(o for refs in occurrences for o in refs)
member_distinct=sum(len(set(refs)) for refs in occurrences)
members=set(i for i,_ in exact_claims)
held = set(i for batch in j(next((old/'baseline/inputs').rglob('claude-tribonian*/tools/batches.json'))).values() for i in batch)
assert not (members | set(ids)) & held
byid={r['instrument_id']:r for r in csv.DictReader((p.parent/'control-center/orders.csv').open())}
rq=ctx['review_queue']; member=ids[0]
assert ids==['EO:13792']
assert all(r['instrument_id']==member for r in rq)
assert ctx['automatic_approvals'] == 0 and ctx['whole_case_review_required'] is True
claim=ctx['claims'][member]
native_projection=dict(notice=ctx['notice'],claim=claim,review_queue=rq)
branch_projection=dict(native_projection,refused_method_reviews=[r for r in ctx['refused_method_reviews'] if r['instrument_id']==member])
assert j(p/'paths/NATIVE_VALLA_PREVIEW.json')['native_member_projection'] == branch_projection
print(json.dumps(dict(
schema='offload-independent-frozen/v1',c1=dict(artifact_sha256=sha(source.read_bytes()), claims=len(claims), native_exact_eligible_versions=len(exact_claims&native),ready_snapshot=sum(byid[i]['ready_for_human_review']=='yes' for i in members), all_reference_occurrences=total, whole_distinct=len(allrefs), within_order_repetitions=total-member_distinct, additional_across_order_repetitions=member_distinct-len(allrefs), protected_overlap=0),
maitland=dict(packet_sha256=sha(packetfile.read_bytes()),self_fingerprint=frozen, main_order_projection_sha256=sha(canonical(native_projection)), main_order_projection_compact_bytes=len(canonical(native_projection)), pr135_order_projection_compact_bytes=len(canonical(branch_projection)), pr135_projection_sha256=sha(canonical(branch_projection)), member_ids=ids, invalidated_pointers=len(claim['invalidated_conclusion_pointers']), eligible_component_reviews=len(claim['component_reviews']),queue_states=dict(Counter(r['state'] for r in rq)), member_method_refusals=len([r for r in ctx['refused_method_reviews'] if r['instrument_id']==member]), whole_case_review_required=ctx['whole_case_review_required'], automatic_approvals=ctx['automatic_approvals'],protected_overlap=0,live_context_revalidated=False)),indent=2,sort_keys=True))
