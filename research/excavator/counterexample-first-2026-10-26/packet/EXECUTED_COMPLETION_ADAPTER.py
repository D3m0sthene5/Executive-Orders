import pathlib,json,hashlib
root=pathlib.Path('/workspace/scratch/c478176c789b/eo-neyman');r=root/'research/excavator/counterexample-first-2026-10-26';p=r/'packet';sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest();canon=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def ref(path,line=None):
 x={'path':str(path.relative_to(root)),'sha256':sha(path)}
 if line:x['line']=line
 return x
reviews={'EO:7975A':(1,'BLIND_REVIEW.jsonl',2,'AFTER_REVEAL.jsonl',1),'EO:8083':(1,'BLIND_REVIEW.jsonl',3,'AFTER_REVEAL.jsonl',2),'EO:8123':(2,'CORRECTED_REVIEW.jsonl',1,'AFTER_REVEAL.v2.jsonl',2),'EO:8126':(2,'CORRECTED_REVIEW.EO_8126.jsonl',1,'AFTER_REVEAL.v2.jsonl',3),'EO:8992':(3,'BLIND_REVIEW.jsonl',1,'AFTER_REVEAL.jsonl',1)}
cp=p/'PROPOSED_SELECTION.v3.jsonl';claims=[json.loads(l) for l in cp.read_text().splitlines()];members=[]
for n,c in enumerate(claims,1):
 i=c['instrument_id'];pair,rf,rl,af,al=reviews[i];rd=p/'review'/f'pair{pair}';rv=json.loads((rd/rf).read_text().splitlines()[rl-1]);av=json.loads((rd/af).read_text().splitlines()[al-1]);assert rv['claim_sha256']==canon(c)==av['claim_sha256'] and rv['verdict']=='upheld' and av['verdict']=='upheld_after_reveal'
 m={'instrument_id':i,'outcome':'submit','claim_sha256':canon(c),'claim':ref(cp,n),'publication_kind':'whole_case','review':ref(rd/rf,rl),'after_reveal_review':ref(rd/af,al)}
 if c.get('claim_kit'):m['packet']=ref(p/'PACKET.json')
 members.append(m)
members.append({'instrument_id':'EO:8915','outcome':'blocked','reason':'Primary original preserves actual earlier Interior-notice/return condition; no occurrence/closing record fixes first jurisdiction cessation. Independent source review upholds bounded findings, leaves exact whole lifecycle incomplete. Not an encoding blocker.'})
controls=[]
for pair,label in [(1,'P8'),(2,'B9'),(3,'M2')]:
 rd=p/'review'/f'pair{pair}';seedp=rd/'SEED_RECEIPT.json';seed=json.load(open(seedp));bp=rd/'BLIND_REVIEW.jsonl';rs=[json.loads(l) for l in bp.read_text().splitlines()];line=next(n for n,x in enumerate(rs,1) if x.get('label')==label);row=rs[line-1];assert row['claim_sha256']==seed['planted_claim_sha256'] and row['verdict']=='rejected';ap=rd/'CONTROL_ADJUDICATION.json';ad=json.load(open(ap));caught=ad.get('caught') is True or ad.get('strict_pass') is True or ad.get('strict_semantic_caught') is True;assert caught
 normalized={'instrument_id':seed['instrument_id'],'planted_claim_sha256':seed['planted_claim_sha256'],'review':ref(bp,line),'adjudicator':ad.get('adjudicator') or ad['reviewer'],'caught':True,'scoring':'strict','rationale':ad.get('rationale') or ad.get('blind_detection') or ad['semantic_detection'],'source_adjudication':ref(ap),'normalization':'Mechanical field adapter of explicit independent strict semantic adjudication; no new judgment or control content.'};np=rd/'COMPLETION_CONTROL_ADJUDICATION.json';np.write_text(json.dumps(normalized,indent=2)+'\n');controls.append({'instrument_id':seed['instrument_id'],'planted_claim_sha256':seed['planted_claim_sha256'],'seed':ref(seedp),'review':ref(bp,line),'adjudication':ref(np)})
receipts=[ref(r/'DESIGN.json'),ref(p/'DERIVATIVE_REGISTRATION.json'),ref(p/'selected-checker-v3/SUMMARY.json')]
manifest={'schema':'eo-claim-kit-completion/v1','agent':'codex-counterexample-20261026','producer_model_family':'OpenAI','independence_requirement':'same_family_separate_context','publication':{'mode':'own_claims','path':'research/readiness/claims/codex-counterexample-20261026-whole.jsonl'},'members':members,'controls':controls,'receipts':receipts};(r/'COMPLETION.json').write_text(json.dumps(manifest,indent=2)+'\n');print('members',len(members),'submit',len(claims),'controls',len(controls))
