from pathlib import Path
from copy import deepcopy
import json,hashlib,sys
B=Path(__file__).resolve().parent;R=B.parents[3];sys.path.insert(0,str(R/'jobs/claim-kit'));import assemble
p=B/'PROPOSED_CLAIM.v1.jsonl';c=json.loads(p.read_text());old=deepcopy(c);base=json.loads((B/'packet-v4/applied-v1/CLAIMS.proposed.jsonl').read_text())
for k in ['original_source','original_operative_text']:c['operative_clauses'][4][k]=deepcopy(base['operative_clauses'][4][k])
c['operative_clauses'][4]['judgment_reason']+=' The source span includes printed-page and extractor furniture at the page break; that material carries no operative force. It is retained solely to preserve exact continuous quotation across the two inspected pages.'
c['research_provenance']['revision']='b01-candidate-v2'
c['research_provenance']['representation_correction']='4(a) exact original continuous span retained with visible page furniture, avoiding an unsupported seamless cross-page quote in the normal consumer; substantive words/dates unchanged.'
c['research_rationale']=c['research_rationale'].replace('this object cites the same inspected raw PDF using a clean, explicitly documented derivative text to exclude printer/extractor furniture.','this object cites the same inspected raw PDF using an explicitly documented derivative text; the cross-page section4(a) retains exact held page furniture for consumer quote continuity.')
q=B/'PROPOSED_CLAIM.v2.jsonl';assert not q.exists();q.write_text(json.dumps(c,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n')
e=assemble.check_claim(c,R);assert not e,e
(B/'PRODUCER_GATES.v2.json').write_text(json.dumps({'instrument_id':'EO:13975','claim_sha256':assemble.canonical_sha(c),'stage19_and_exact_source_errors':e,'independent_review':False},indent=2)+'\n')
(B/'REPRESENTATION_CORRECTION.v2.json').write_text(json.dumps({'prior':{'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'claim_sha256':assemble.canonical_sha(old)},'candidate':{'path':str(q.relative_to(R)),'sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'claim_sha256':assemble.canonical_sha(c)},'reason':'Actual checker on v1 found 4(a) cleaned cross-page quote discontinuous in held source; restore precise existing official extraction span, disclose page furniture; nine substantive units,states andend dates unchanged.','failed_receipt':'checker-v1/PER_CLAIM.json','new_sources':0},indent=2)+'\n')
print(assemble.canonical_sha(c))
