from pathlib import Path
from copy import deepcopy
import json,hashlib,datetime,time,sys
P=Path(__file__).resolve().parent;ROOT=P.parents[5]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(name,obj):
 q=P/name
 if q.exists():raise RuntimeError('Version already exists: '+name)
 q.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
 return sha(q)
source_path='jobs/astra-source-retention/output/pages/5437e663677371c8db1016ea81a834f6cca735ff9fa988e08397fb99c73ccd36/576710d4f00ed5b6d8736f3619a041899ab56778d23013637a071b8e7c30674f/selected-pages.txt'
pdf_path='jobs/astra-source-retention/output/pdf/5437e663677371c8db1016ea81a834f6cca735ff9fa988e08397fb99c73ccd36.pdf'
rawsha='5437e663677371c8db1016ea81a834f6cca735ff9fa988e08397fb99c73ccd36'
assert sha(ROOT/pdf_path)==rawsha
text=(ROOT/source_path).read_text();tsha=sha(ROOT/source_path)
def ref(a,b,page):return {'url':'https://www.govinfo.gov/content/pkg/FR-1939-07-01/pdf/FR-1939-07-01.pdf','sha256':rawsha,'local_path':pdf_path,'text_path':source_path,'text_sha256':tsha,'char_start':a,'char_end':b,'quote':text[a:b],'page_or_item':page}
a=text.index('(f) Bureau of Biological Survey.');b=text.index('(g) Officers of Biological',a)
functions=ref(a,b,'Reorganization Plan No. II, section4(f),4 FR2732, PDFpage6, left-column bottom continued at center-column top')
a=text.index('[Public Resolution No. 20');b=text.index('Reorganization Plan No. 1',a)
joint=ref(a,b,'June7,1939 Joint Resolution,Public Resolution20,S.J.Res.138,4 FR2727,PDFpage1 left column; effectiveJuly1,1939 and section2 no-extension limitation')
a=text.index('Sec. 401. Transfer of Functions');b=text.index('Sec. 403. Transfer of Funds',a)
general=ref(a,b,'Reorganization Plan No. II,sections401–402,4 FR2733,PDFpage7 left column')
reason=('Reorganization Plan No. II section4(f) transfers the Bureau of Biological Survey and its functions from Agriculture to Interior, and transfers the Secretary of Agriculture functions relating to wildlife, game and migratory birds to the Secretary of the Interior. Section401 transfers related departmental-head administration and section402 transfers records/property/personnel for administering those continuing functions. The June7,1939 joint resolution makes Plan II effective July1,1939, notwithstanding the general Reorganization Act timing; section2 does not extend preexisting durations. This is a legal administrative succession, not proof of physical delivery of records or property. It does not revoke the refuge, change its320-acre boundary, or terminate its wildlife/entry prohibition. Under the owner unnamed-instrument rule, this earlier instrument does not name EO8123 and is expressly disclosed and rejected as cessation. The continuing scopes remain subject to the later whole revocation on1958-08-05.')
c=json.loads((P/'MANUAL_CLAIM.v1.json').read_text())
old=deepcopy(c)
for cl in c['operative_clauses']:
 if cl['scope_id'] in ('EO:8123#reservation','EO:8123#protection'):
  is_res=cl['scope_id'].endswith('#reservation')
  e={'effective_date':'1939-07-01','actor':'Reorganization Plan No. II of1939,section4(f),with sections401–402; effective date fixed by June7,1939 joint resolution','mechanism':'administrative-function transfer; scope continues under successor administration','source':deepcopy(functions),'sources':[deepcopy(joint),deepcopy(general)],'before':'Department of Agriculture administers refuge reservation through its wildlife functions' if is_res else 'Secretary of Agriculture exercises wildlife/entry regulatory functions','after':'Department of the Interior administers refuge reservation through transferred Biological Survey/wildlife functions' if is_res else 'Secretary of the Interior exercises transferred wildlife/entry regulatory functions','reason':reason}
  cl['later_events']=[e]+cl['later_events']
  cl['judgment_reason']+=' '+reason
c['research_rationale']+=' '+reason
c['counterevidence_checked'].append({'issue':'July1,1939 Agriculture-to-Interior administrative transfer considered as earlier cessation candidate','source':deepcopy(functions),'sources':[deepcopy(joint),deepcopy(general)],'resolution':reason})
c['meta']['version']='v2';c['meta']['supersedes_file_sha256']=sha(P/'MANUAL_CLAIM.v1.json');c['meta']['correction']='Material administration-transfer disclosure added to reservation/protection; original quotes, all1958-08-05first ends, name amendment, other sources and bounded searches retained. Exact corrected-version review required.'
file_sha=put('MANUAL_CLAIM.v2.json',c)
(P/'MANUAL_CLAIM.v2.jsonl').write_text(json.dumps(c,ensure_ascii=False,sort_keys=True)+'\n')
rows=[]
def walk(x,path=''):
 if isinstance(x,dict):
  if 'text_path' in x and 'quote' in x:
   q=ROOT/x['text_path'];t=q.read_text();ok=sha(q)==x['text_sha256'] and t[x['char_start']:x['char_end']]==x['quote'];rows.append({'field':path,'exact':ok,'text_path':x['text_path']})
  for k,v in x.items():walk(v,path+'.'+k)
 elif isinstance(x,list):
  for i,v in enumerate(x):walk(v,path+f'[{i}]')
walk(c);assert all(r['exact'] for r in rows)
sys.path.insert(0,str(ROOT/'research/stage19/code'));import claim_gate
errors=claim_gate.validate_claim(c,expected_status='no');assert not errors,errors
put('SOURCE_SPAN_AUDIT.v2.json',{'kind':'producer exact-byte/span self-check and existing Stage19 structural gate; not independent review or actual native claim-checker','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'references_checked':len(rows),'all_exact':True,'rows':rows,'stage19_errors':errors,'claim_canonical_sha256':claim_gate.claim_sha(c)})
put('SUPPLEMENT_RECEIPT.v2.json',{'schema':'eo-manual-claim-supplement/v1','instrument_id':'EO:8123','before_path':str((P/'MANUAL_CLAIM.v1.json').relative_to(ROOT)),'before_file_sha256':sha(P/'MANUAL_CLAIM.v1.json'),'after_path':str((P/'MANUAL_CLAIM.v2.json').relative_to(ROOT)),'after_file_sha256':file_sha,'after_claim_sha256':claim_gate.claim_sha(c),'after_jsonl_file_sha256':sha(P/'MANUAL_CLAIM.v2.jsonl'),'correction_request':'packet/review/pair2/CORRECTION_REQUEST.EO_8123.json','reason':'Initial whole-case review rejected omission of1939administration transfer. Producer read complete PlanII and June7jointresolution text and visually checkedPDFpages1,6,7; independently accepted correction from primary evidence. Prior rejection retained.','changed_fields':['operative_clauses[reservation].later_events','operative_clauses[protection].later_events','operative_clauses[reservation/protection].judgment_reason','research_rationale','counterevidence_checked','meta.version/correction/provenance'],'new_source_references':[functions,joint,general],'ending_date_unchanged':'1958-08-05','status_unchanged':'no','source_span_checks':len(rows),'stage19_errors':errors,'actual_native_claim_checker_run_by_producer':False,'independent_exact_corrected_hash_review_required':True,'owner_adoption':False})
analysis=(P/'ANALYSIS.md').read_text()
insert='''## Correction: administration transferred July 1, 1939

The initial whole-case review rejected v1 because it omitted a material administration transfer, while supporting the August 5, 1958 ending. This v2 corrects that omission from primary evidence; v1 and its rejection remain preserved.

I independently read the complete Reorganization Plan No. II in the July 1, 1939 Federal Register, printed pages 2731–2733 (PDF pages 5–7), including its general provisions. I also read the complete June 7, 1939 joint resolution at printed page 2727 (PDF page 1), and visually inspected PDF pages 1, 6 and 7 from the rehashed native issue SHA-256 `5437e663677371c8db1016ea81a834f6cca735ff9fa988e08397fb99c73ccd36`. The first broad text read was output-truncated; I then read the complete Plan II span separately. No missing section was inferred from a pointer.

Section 4(f) states that the Bureau of Biological Survey in Agriculture and its functions “are hereby transferred to the Department of the Interior” and provides for administration under Interior's Secretary. It separately transfers the Secretary of Agriculture's functions relating to “the conservation of wild life, game, and migratory birds” to the Secretary of the Interior. The paragraph continues across columns on printed page 2732; I inspected both portions. Section 401 transfers related departmental-head administrative functions; section 402 transfers records, property and personnel for administering the transferred functions.

The June 7 joint resolution expressly makes both reorganization plans effective **July 1, 1939**, notwithstanding the general Reorganization Act timing. Its section 2 says the plans/resolution do not extend an agency or function beyond when it otherwise would have terminated. EO 8123 contains no such original expiry. I therefore do not derive the effective date from the plan's May 9 transmission or presume actual delivery/receipt of records and property; the legal transfer operates on the date fixed by the joint resolution.

The before/after administration is explicit in both affected clause histories. For the reservation: Agriculture's refuge/wildlife administration passes to Interior through the transferred Biological Survey functions. For protection: wildlife and entry regulatory functions previously exercised by the Secretary of Agriculture pass to the Secretary of the Interior. The exact original EO quotations remain historical original text; later events describe the successor authority rather than silently rewriting the original.

This is an earlier administrative change, not refuge cessation. Neither section 4(f), the general transfer provisions nor the joint resolution names EO 8123 or revokes its reservation, 320-acre boundary or protective command. The owner rule for unnamed instruments requires disclosure rather than treating such an instrument as the ending; v2 expressly records and rejects this earlier cessation candidate. Transfer to a successor administrator also explains Interior's later role and creates no independent surviving EO 8123 command after PLO 1704. All three first-end dates remain August 5, 1958. The 1940 name amendment, 1950 operational contrary evidence and later-search findings are unchanged.

'''
analysis=analysis.replace('## Earlier amendment and operational contrary evidence',insert+'## Earlier amendment and operational contrary evidence')
analysis=analysis.replace('MANUAL_CLAIM.v1.json is the complete whole-case proposal. SUPPLEMENT_RECEIPT.json pins','MANUAL_CLAIM.v2.json (also provided as .jsonl) is the corrected complete whole-case proposal. SUPPLEMENT_RECEIPT.v2.json pins')
analysis=analysis.replace('No producer native apply/check/completion was run.','The producer ran the existing Stage 19 structural gate and exact reference hash/span self-check on v2; both passed. No producer native apply, actual claim-checker or completion was run. Independent corrected-hash review remains required.')
(P/'ANALYSIS.v2.md').write_text(analysis)
with (P/'JOURNAL.jsonl').open('a') as f:f.write(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'monotonic':time.monotonic(),'action':'required correctionv2 source review and implementation','sources':'NativeFR1939-07-01 PDFpages1,5–7text and images1,6,7; completePlanIIsection4f,401,402 andJune7jointresolution. Broad initialoutputtruncated; targetedfullPlanIIrereadcompleted.','result':'AddedJuly1,1939administrationtransfer toreservation/protection; explainednotcessation; retained1958-08-05end. Allquotedspans exact; Stage19pass; noactualnativechecker.','after_file_sha256':file_sha,'after_canonical_claim_sha256':claim_gate.claim_sha(c)})+'\n')
print(json.dumps({'file_sha256':file_sha,'canonical_sha256':claim_gate.claim_sha(c),'span_count':len(rows),'stage19_errors':errors}))
