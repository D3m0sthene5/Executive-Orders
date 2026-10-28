from pathlib import Path
import json,hashlib
root=Path('.');r=root/'research/excavator/production-cost-trace-2026-10-26';p=r/'packet-b2-correction-v9';rv=p/'review-final'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def ref(f,pointer=None):
 d={'path':str(f),'sha256':sha(f)}
 if pointer is not None:d['pointer']=pointer
 return d
def canonical(j):return hashlib.sha256(json.dumps(j,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def walk(j,pointer=''):
 if isinstance(j,dict):
  yield pointer,j
  for k,v in j.items():yield from walk(v,pointer+'/'+str(k).replace('~','~0').replace('/','~1'))
 elif isinstance(j,list):
  for n,v in enumerate(j):yield from walk(v,pointer+'/'+str(n))
def select(f,h,verdict):
 found=[pointer for pointer,j in walk(json.loads(f.read_bytes())) if j.get('claim_sha256')==h and j.get('verdict')==verdict]
 assert len(found)==1,(f,found)
 return ref(f,found[0]) if found[0] else ref(f)
claimsfile=p/'applied-v1/CLAIMS.proposed.jsonl';cs=[json.loads(x) for x in claimsfile.read_text().splitlines()];seedfile=p/'CONTROL_SEED.final.json';seed=json.loads(seedfile.read_bytes());blind=rv/'BLIND_REVIEW.json';members=[]
afterfiles=[]
for f in rv.glob('*.json'):
 if any(j.get('claim_sha256')==seed['genuine_claim_sha256'] and j.get('verdict')=='upheld_after_reveal' for _,j in walk(json.loads(f.read_bytes()))):afterfiles.append(f)
assert len(afterfiles)==1,afterfiles
for n,c in enumerate(cs,1):
 h=canonical(c);m={'instrument_id':c['instrument_id'],'outcome':'submit','claim_sha256':h,'claim':{**ref(claimsfile),'line':n},'publication_kind':'whole_case','review':select(blind,h,'upheld'),'packet':ref(p/'PACKET.json')}
 if c['instrument_id']==seed['instrument_id']:m['after_reveal_review']=select(afterfiles[0],h,'upheld_after_reveal')
 members.append(m)
adj=rv/'CONTROL_ADJUDICATION.json';j=json.loads(adj.read_bytes());assert j['planted_claim_sha256']==seed['planted_claim_sha256'] and j['caught'] is True and j['scoring']=='strict'
receipts=[p/'producers/batch2/PRODUCER_SEAL.corrected-v1.json',p/'producers/batch2/COMPLETION_RECEIPT.corrected-v1.json',p/'producers/batch2/COST.corrected-v1.json',rv/'BLIND_SEAL.json',r/'recovery2/CONTROL_PROCESS_FAILURE.json',r/'recovery2/review2/SOURCE_REVIEW.new.jsonl',r/'recovery2/review2/COST.new.json',r/'NATIVE_PREPARE_COMPARISON.json',r/'ENGINEERING_REVIEWS.json']
for name in ['SOURCE_EXAMINATION.md','SOURCE_BYTE_AUDIT.json','CARD_SOURCE_BYTE_AUDIT.json','RENDER_MANIFEST.json','COST.final.json','FINAL_SEAL.json']:
 f=rv/name
 if f.exists():receipts.append(f)
manifest={'schema':'eo-claim-kit-completion/v1','agent':'codex-production-cost-trace','producer_model_family':'OpenAI','independence_requirement':'same_family_separate_context','publication':{'mode':'own_claims','path':'research/readiness/claims/codex-production-cost-trace-20261026-b2.jsonl'},'members':members,'controls':[{'instrument_id':seed['instrument_id'],'planted_claim_sha256':seed['planted_claim_sha256'],'seed':ref(seedfile),'review':select(blind,seed['planted_claim_sha256'],'rejected'),'adjudication':ref(adj)}],'receipts':[ref(f) for f in receipts]}
f=p/'COMPLETION.json';f.write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'manifest':str(f),'sha256':sha(f),'after':str(afterfiles[0])}))
