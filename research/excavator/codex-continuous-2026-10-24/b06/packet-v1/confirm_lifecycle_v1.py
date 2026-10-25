from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parent
put=lambda p,o:p.write_text(json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
receipts=[]
for n in [10673,10772]:
 p=B/f'applied-v1/decisions/EO_{n}.json';s=json.loads(p.read_text());s['research_rationale']+=' Full29-row search review rejects two10931→10673 false revocation attachments: actualsec2 revoked list is10704/10740/10785. Exact before/after source quotations and source references are preserved in AMENDMENT_CHAIN.v1.json, and all seven original10673 sections/three10772 commands in INVENTORY_CHECK.v1.json.'
 for c in s['clauses']:c['mechanism']='revoke'
 q=p.with_name(f'EO_{n}.source-grounded-v1.json');assert not q.exists();put(q,s)
 receipts.append({'instrument_id':f'EO:{n}','source_sheet':str(p),'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'confirmed_sheet':str(q),'confirmed_sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'changes':['clauses[*].mechanism explicitly revoke because exact ACTOR_TEXT11074 lacks machine verb','research_rationale appends completed counterevidence explanation'],'producer_reconfirmed':True,'source_reason':'Complete11074sec6 names10673 and10772 and hereby revokes them; no fabricated ACT registry entry.'})
put(B/'LIFECYCLE_RECONFIRMATION.v1.json',receipts)
print(json.dumps(receipts,indent=2))
