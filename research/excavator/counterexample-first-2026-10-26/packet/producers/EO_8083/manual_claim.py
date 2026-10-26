from pathlib import Path
import json,csv,hashlib,copy,sys
P=Path(__file__).resolve().parent;ROOT=P.parents[5];PK=P.parent.parent
M=json.loads((P/'MEMBER_CONTEXT.json').read_text());D=M['dossier'];rat=json.loads((P/'RATIONALES.json').read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
def exact(source,a,b):
 r=copy.deepcopy(source);r.pop('evidence_id',None);r.pop('evidence_id_encoding',None)
 t=(ROOT/r['text_path']).read_text();assert sha((ROOT/r['text_path']).read_bytes())==r['text_sha256'];r.update(quote=t[a:b],char_start=a,char_end=b);return r
src=D['evidence']['ORIGINAL:EO:8083']['source'];act=D['evidence']['ACT:EO:8083>EO:9830']['source']
original=exact(src,794,2692);ending=exact(act,90277,91001);globaldate=exact(act,2164,2220)
end={'date':'1947-05-01','actor':'EO:9830','mechanism':'revocation','source':ending,'sources':[globaldate]}
avail={}
for fn in PK.glob('SOURCE_AVAILABILITY.v*.json'):
 for r in json.loads(fn.read_text()):avail[r['url']]=r
retbase=ROOT/'jobs/astra-source-retention/output'
def newref(url,start,end,page):
 r=avail[url];t=(retbase/r['text_path']).read_text();a=t.index(start);b=t.index(end,a)+len(end)
 return {'url':url,'sha256':r['sha256'],'text_path':str((retbase/r['text_path']).relative_to(ROOT)),'text_sha256':r['text_sha256'],'page_or_item':page,'char_start':a,'char_end':b,'quote':t[a:b]}
acturl='https://www.govinfo.gov/content/pkg/STATUTE-56/pdf/STATUTE-56-Pg13-2.pdf'
acttext=(retbase/avail[acturl]['text_path']).read_text()
# Exact OCR spelling and line breaks come from the native retained text, never hand-edited quotations.
a=acttext.index('Sec. 3.') if 'Sec. 3.' in acttext else acttext.index('Sec . 3.')
b=acttext.index('“(c)',a) if '“(c)' in acttext[a:] else a+3500
statcoverage={'url':acturl,'sha256':avail[acturl]['sha256'],'text_path':str((retbase/avail[acturl]['text_path']).relative_to(ROOT)),'text_sha256':avail[acturl]['text_sha256'],'page_or_item':'56 Stat. 15, §3; PDF page 3','quote':acttext[a:b],'char_start':a,'char_end':b}
a=acttext.index('Sec. 10.') if 'Sec. 10.' in acttext else acttext.index('Sec . 10.');b=acttext.index('Approved, January 24, 1942.',a)+len('Approved, January 24, 1942.')
statsaving={**statcoverage,'page_or_item':'56 Stat. 17, §§10–11; PDF page 5','quote':acttext[a:b],'char_start':a,'char_end':b}
s9154='https://www.govinfo.gov/content/pkg/FR-1942-05-05/pdf/FR-1942-05-05.pdf';r=avail[s9154];t=(retbase/r['text_path']).read_text();a=t.index('3. This order shall be effective');b=t.index('F ranklin D Roosevelt',a)
saving={'url':s9154,'sha256':r['sha256'],'text_path':str((retbase/r['text_path']).relative_to(ROOT)),'text_sha256':r['text_sha256'],'page_or_item':'7 FR 3277, §3; PDF page 3','quote':t[a:b],'char_start':a,'char_end':b}
def oldref(iid,start,end,page):
 t=(ROOT/f'jobs/fr-originals/data/full_run/texts/EO_{iid}.txt').read_text();lines=t.splitlines();url=next(x[8:] for x in lines if x.startswith('Source: '));sh=next(x[34:] for x in lines if x.startswith('SHA-256 of the downloaded file: '))
 sh=lines[2].split(': ',1)[1];a=t.index(start);b=t.index(end,a)+len(end)
 return {'url':url,'sha256':sh,'text_path':f'jobs/fr-originals/data/full_run/texts/EO_{iid}.txt','text_sha256':sha(t.encode()),'page_or_item':page,'quote':t[a:b],'char_start':a,'char_end':b}
war=oldref('9063','1. The United States Civil Service','months thereafter.','7 FR 1075, §§1–2; PDF page 1')
postwar=oldref('9691','9. Executive Orders Nos. 9063','agency.','11 FR 1383, §9; PDF page 3')
searches=[copy.deepcopy(x['entry']) for x in D['machine_searches']]
searches.append({'repository':'Producer independent web searches (two search engines), OFR 1939 disposition entry and exact held source texts','query_or_scope':'Exact Executive Order 8083 / 8083 Civil Service retirement with revoked, amended, superseded, rights, 1942 and 1947; queries excluding 9830; 9830 May 1 1947 postponement; historical Rule II 3(d), EO 9063 and 9691 wartime transition. Read actual 1942 Act §§3,10,11, original EO9154 §§1–3, EO9063 §§1–2 and EO9691 full text; no earlier named ending or revival found. USC search is only through 2026-10-09 and number searches cannot negate unnamed statutory coverage changes, which are separately disclosed. Materialized local original text search for8083 found8083/9830 only; not a claim to absent-file coverage.','checked_on':'2026-10-26','legal_cutoff':'2026-10-14'})
clauses=[]
for c in csv.DictReader((P/'clauses.csv').open()):
 a=int(c['inventory_char_start']);b=int(c['inventory_char_end']);ref=exact(src,a,b)
 item={'scope_id':c['scope_id'],'original_operative_text':ref['quote'],'original_source':ref,'state_at_cutoff':'terminated','first_end':copy.deepcopy(end),'later_events':[],'judgment_reason':c['reason']}
 if c['scope_id'].endswith('retirement-extension'):
  item['later_events']=[{'effective_date':'1942-01-24','actor':'Act of January 24, 1942, ch.16, Public Law411','mechanism':'statutory_coverage_revision_disclosed_earlier_candidate','source':statcoverage,'sources':[statsaving],'note':'Functional replacement candidate. The Act does not name8083; formal end follows owner unnamed-instruments ruling.'},{'effective_date':'1942-01-24','actor':'EO:9154','mechanism':'retirement_exclusions_with_acquired_rights_saving','source':saving,'note':'Explicit retroactive date in§3, with acquired rights before May1,1942 issuance protected; no whole-order8083revocation.'}]
 clauses.append(item)
claim={'schema':'eo-lifecycle-claim/v1','instrument_id':'EO:8083','whole_order_status':'no','original_representation':original,'operative_clauses':clauses,'whole_order_end':copy.deepcopy(end),'savings_residuals':{'state':'transferred_or_accrued','reason':rat['8083_savings'],'source':saving,'sources':[statsaving,postwar,exact(act,(ROOT/act['text_path']).read_text().index('§ 1.1 Positions'),(ROOT/act['text_path']).read_text().index('RULE n —'))]},'later_source_search':searches,'research_rationale':rat['8083_main']+' Earlier end examination: '+rat['8083_earlier']+' Source qualification: GAO B11861 quoted the older1938Rule with a retirement exclusion removed by8083; that non-naming quotation is not treated as an amendment. No claim of actual pensionpayment or present8083authority.','unresolved_material_gaps':[],'sources':[war,postwar],'manual_provenance':{'schema':'eo-ordinary-stage19-manual/v1','agent':'codex-counterexample-EO8083','producer_approved':True,'original_pages_confirmed':True,'dossier_fingerprint':D['fingerprint'],'packet_fingerprint':M['packet_fingerprint'],'source_availability_files':['SOURCE_AVAILABILITY.v1.json','SOURCE_AVAILABILITY.v2.json','SOURCE_AVAILABILITY.v3.json'],'reason':'Ordinary manual Stage19 route supplements retained primary sources and actual producer searches absent from frozen packet evidence IDs. No fake IDs or claim_kit binding; original dossier unchanged.'}}
for x in [original,ending,globaldate,statcoverage,statsaving,saving,war,postwar]:assert (ROOT/x['text_path']).read_text()[x['char_start']:x['char_end']]==x['quote']
sys.path.insert(0,str(ROOT/'research/stage19/code'));import claim_gate
errors=claim_gate.validate_claim(claim,expected_status='no');assert not errors,errors
(P/'MANUAL_CLAIM.v2.json').write_text(json.dumps(claim,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
(P/'MANUAL_CLAIMS.v2.jsonl').write_text(json.dumps(claim,ensure_ascii=False,sort_keys=True)+'\n')
receipt={'schema':'eo-manual-claim-supplement/v1','instrument_id':'EO:8083','claim_path':str((P/'MANUAL_CLAIM.v2.json').relative_to(ROOT)),'claim_file_sha256':sha((P/'MANUAL_CLAIM.v2.json').read_bytes()),'claim_sha256':claim_gate.claim_sha(claim),'packet_fingerprint':M['packet_fingerprint'],'dossier_fingerprint':D['fingerprint'],'manual_changed_scopes':['corrected complete three-clause inventory','exact actor target and effective-date references','1942 statutory coverage revision and savings','EO9154 retroactive exclusions and acquired retirement rights','EO9063 and9691 wartime transition','actual bounded producer searches'],'strict_text_spans_checked':True,'stage19_gate_errors':errors,'actual_claim_checker':'coordinator runs native checker next','independent_review_required_on_final_hash':True,'owner_adoption':False}
(P/'SUPPLEMENT_RECEIPT.v2.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
