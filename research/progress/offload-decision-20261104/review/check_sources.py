"""Verify four pinned source-span specimens and the associated unfinished-row ceiling."""
import collections,csv,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
native=P/'population'
j=lambda p: json.loads(p.read_bytes())
canon=lambda v:json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
sha=lambda b:hashlib.sha256(b).hexdigest()
files=j(native/'SOURCE_HASHES.json')
cache=native/'.source-cache'
src=cache/'EO_12553.txt'
raw=src.read_bytes()
dig=sha(raw)
assert dig == '6361bdc557b6acaeae6e6908cded18f4f8fef9fde1a97cc11fb7c12c8cdea761'
hold={'EO:10622','EO:11040','EO:11078','EO:9922'}
def visit(x):
    if isinstance(x,list):
        for v in x: yield from visit(v)
    elif isinstance(x,dict):
        if x.get('text_path')=='jobs/fr-originals/data/full_run/texts/EO_12553.txt':
            yield x
        for v in x.values(): yield from visit(v)
ref_objects=[]; reads=0; spans=[]; selected=[]
for f in sorted(cache.glob('*.jsonl')):
    filehash=sha(f.read_bytes())
    assert any(r.get('sha256')==filehash for r in files)
    for line in f.read_bytes().splitlines():
        claim=json.loads(line)
        if claim['instrument_id'] not in hold: continue
        selected.append(claim['instrument_id'])
        for ref in visit(claim):
            reads+=1;assert ref['text_sha256']==dig
            a,b=ref['char_start'],ref['char_end']
            assert type(a) is int and type(b) is int and 0<=a<b<=len(raw.decode()) and ref['quote']==raw.decode()[a:b]
            spans.append((dig,a,b,ref['quote'])); ref_objects.append(canon(ref))
assert set(selected)==hold and len(selected)==4
obs=P.parent/'production-observability-20261104/baseline/inputs'
plan=set(i for grp in j(next(obs.rglob('claude-tribonian*/tools/batches.json'))).values() for i in grp)
locks=set(j(next(obs.rglob('600a*/research/readiness/CLAIM_KIT_LOCK.json')))['orders'])
rows={r['instrument_id']:r for r in csv.DictReader((P.parent/'control-center/orders.csv').open())}
available={i for i in rows if i not in plan|locks and rows[i]['ready_for_human_review']!='yes'}
claims_in_scope={i for i in available if rows[i]['claim_present']=='yes'}
assert hold<=claims_in_scope
pop=j(native/'POPULATION.json')
assert pop['opportunities']['claim_present']['remaining_membership_sha256']==sha(('\n'.join(sorted(claims_in_scope))+'\n').encode())
assert (reads,len(set(ref_objects)),len(set(spans)),len(claims_in_scope))==(14,4,2,114)
print(json.dumps(dict(target_sha256=dig, specimen_order_versions=len(selected), unfrozen_current_version_status='not established', full_reference_occurrences=reads, unique_full_objects=len(set(ref_objects)), unique_exact_spans=len(set(spans)), positive_width_and_quote_match=reads, remaining_claim_present_ids=len(claims_in_scope), remaining_identity_set_sha256=pop['opportunities']['claim_present']['remaining_membership_sha256'], additional_eligible_orders=None,raw_pdf_checked=False),sort_keys=True,indent=2))
