"""Freeze source-read supplemental ordinary Stage19 claim; retain normal batch output."""
from pathlib import Path
from copy import deepcopy
import json,hashlib,re,sys,csv,datetime
B=Path(__file__).resolve().parent;R=B.parents[3];sys.path.insert(0,str(R/'jobs/claim-kit'));import assemble
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(R).as_posix()
def save(n,v):(B/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ref(path,rawsha,url,loc,a,z):
 t=path.read_text();return {'url':url,'sha256':rawsha,'text_path':rel(path),'text_sha256':sha(path),'page_or_item':loc,'char_start':a,'char_end':z,'quote':t[a:z]}
def excerpt(path,rawsha,url,loc,a,z):
 t=path.read_text();start=t.index(a);end=t.index(z,start) if z else len(t);return ref(path,rawsha,url,loc,start,end)
basepath=B/'packet-v4/applied-v1/CLAIMS.proposed.jsonl';base=json.loads(basepath.read_text());c=deepcopy(base)
# Normal batch metadata is retained as an immutable source artifact, not claimed for an enriched object.
kit=c.pop('claim_kit');c.pop('working_text',None)
orig=R/'jobs/fr-originals/data/full_run/texts/EO_13975.txt';t=orig.read_text();rawsha='283590a8c941fa5a597f046cbb0153b07705b73845e62ac7502fe1f3cb69c4bb';url='https://www.govinfo.gov/content/pkg/FR-2021-01-21/pdf/2021-01469.pdf'
# Remove only extractor wrapper and printer/page furniture; compare surviving substantive bytes below.
start=t.index('Executive Order 13975 of');end=t.index('THE WHITE HOUSE,');body=t[start:end]
a=body.index('VerDate');z=body.index('relative importance of price is',a)
removed=body[a:z];clean=body[:a]+body[z:]
cleanpath=B/'source-review/EO_13975_page_checked_text.txt';cleanpath.write_text(clean)
assert clean.replace(removed,'')==clean
sourcebase=ref(cleanpath,rawsha,url,'86 FR6547-6548; complete official original pages1-2 inspected; page furniture excluded from exact derivative text',0,len(clean))
c['original_representation']=ref(cleanpath,rawsha,url,'86 FR6547-6548, official PDF pages1-2 completely inspected; quotation is title and first policy unit; full source held',0,clean.index('Sec. 2. Definitions.'))
ends=['Sec. 2. Definitions.','Sec. 3. Purpose.','(b) Executive Order 13881','Sec. 4. Encouraged Rules.','(b) An amendment or amendments','Sec. 5. General Provisions.','(b) This order shall','(c) This order is not',None]
starts=['Section 1. Policy.','Sec. 2. Definitions.','Sec. 3. Purpose.','(b) Executive Order 13881','Sec. 4. Encouraged Rules.','(b) An amendment or amendments','Sec. 5. General Provisions.','(b) This order shall','(c) This order is not']
for cl,a,z in zip(c['operative_clauses'],starts,ends):
 rr=excerpt(cleanpath,rawsha,url,'EO13975 '+cl['scope_id'].split('#')[1]+';86FR6547-6548; original page images inspected',a,z)
 cl['original_source']=rr;cl['original_operative_text']=rr['quote']
 # Keep the original exact official revocation quote; metadata evidence id harmless on ordinary route.
 c['savings_residuals']['source']=deepcopy(c['operative_clauses'][6]['original_source'])
# Source refs use the supported checker container and exact per-page spans.
refs=[]
records=[]
for v in ['source-v1','source-v2','source-v3']:
 for l in (B/v/'SOURCES.jsonl').read_text().splitlines():
  r=json.loads(l);r['_output']=v;records.append(r)
def rec(citation):return next(r for r in records if r['citation']==citation)
f=rec('86 FR 6180, 2021-00710, FAR Case 2019-016 final rule');fp=B/f['_output']/f['text_path']
fr=excerpt(fp,f['sha256'],f['url'],'86 FR6180 right column, final rule Case2019-016; PDF page1 inspected','[FAC 2021–04; FAR Case 2019–016; Docket','FOR FURTHER INFORMATION CONTACT :')
refs.append(fr)
f2=rec('86 FR 8308, C1-2021-00710, correction to FAR Case 2019-016 final rule');f2p=B/f2['_output']/f2['text_path']
f2r=excerpt(f2p,f2['sha256'],f2['url'],'86 FR8308 left column; PDF page1 inspected','[FAC 2021–04; FAR Case 2019–016; Docket','BILLING CODE 1301–00–P')
refs.append(f2r)
for title,n in [('USPS SPP June 20 2020',238),('USPS SPP September 1 2021',236)]:
 r=rec(title);p=B/'source-review'/f"{r['sha256']}.txt";tx=p.read_text();a=tx.index('2-36 Evaluate Foreign and Domestic Proposals',tx.index('\f')+1)
 # Skip table-of-contents occurrence by requiring body signature.
 a=tx.index('2-36 Evaluate Foreign and Domestic Proposals\n')
 z=tx.index('\f',a)
 refs.append(ref(p,r['sha256'],r['url'],title+f',printed p200;physical PDF page{n} inspected;full extraction held (ladder original extraction only first40 pages)',a,z))
actor=R/'jobs/fr-originals/data/full_run/texts/EO_14005.txt';act=actor.read_text();actsha='46ff80e74c11f548be46d0212a849be30620c6d6ed9e6a0ca5052955dbf19a5b';acturl='https://www.govinfo.gov/content/pkg/FR-2021-01-28/pdf/2021-02038.pdf'
refs.append(excerpt(actor,actsha,acturl,'EO14005 sections14-16(b),86FR7478,PDF page4 inspected','Sec. 14. Revocation','VerDate Sep<11>2014 17:21 Jan 27, 2021 Jkt 253001 PO 00000 Frm 00004'))
refs.append(excerpt(actor,actsha,acturl,'EO14005 section16(c) and signature,86FR7479,PDF page5 inspected','(c) This order is not intended','[FR Doc. 2021–02038'))
c['source_refs']=refs
for cl in c['operative_clauses']:
 if '#sec4' in cl['scope_id']:
  cl['later_events']=[{'effective_date':'2021-01-19','actor':'DoD, GSA and NASA / FAR Council','mechanism':'FAR Case2019-016 final rule published January19,2021 implementing EO13881; relevant issuance trigger for recommended consideration period, not amendment or cessation of EO13975. Original effective date January21 corrected by86FR8308 to January19; solicitation applicability February22,2021 is distinct.','source':deepcopy(fr),'sources':[deepcopy(f2r)]}]
c['research_rationale']+=' This final ordinary Stage19 object supplements the successful normal kit assembly with the FAR chronology and exact USPS counterevidence references. The normal batch source wrappers are preserved separately; this object cites the same inspected raw PDF using a clean, explicitly documented derivative text to exclude printer/extractor furniture. No claims of actual USPS consideration or adoption are made.'
c['later_source_search'].append({'repository':'Bounded producer review of held official EO texts, USPS SPP editions/newsletters and public discovery','query_or_scope':'Exact patterns (?:Order|Ord.)\\s+13975 and14005 in held jobs/fr-originals/output/texts/EO_*.txt; all other13975 mentions in target/new actor only.14005 references in14057/14104 are contextual, not target revival;14248 page14005 is numeric false positive. Read USPS2020/2021 SPP p200 and Jan/Feb2021 newsletters; web queries saved in WEB_SEARCH_20261025_1/2.json found no official actual-consideration record. Coverage excludes private USPS deliberations and does not prove nonperformance. Inherited USC search ends2026-10-09; inherited ecfr is2026-10-14; OFR held corpus search2026-10-19. No continuing legal predicate or automatic revival is inferred.','checked_on':'2026-10-25'})
c['research_provenance']={'producer':'codex-continuous-prior','producer_model_family':'OpenAI GPT','revision':'b01-candidate-v1','normal_packet':rel(B/'packet-v4/PACKET.json'),'normal_packet_sha256':sha(B/'packet-v4/PACKET.json'),'assembled_base':rel(basepath),'assembled_base_file_sha256':sha(basepath),'assembled_base_claim_sha256':assemble.canonical_sha(base),'inventory_overrides':kit['inventory_overrides'],'page_review_manifest':rel(B/'SOURCE_MANIFEST.json'),'substantive_analysis':rel(B/'RESEARCH.md'),'prior_status_context':rel(B/'packet-v4/PACKET.json')+'#/prior_research/orders/EO:13975','status_scope':'Existing adopted provisional NO retained; prior status review not lifecycle approval','human_certifications':0,'supplement_route':'Ordinary Stage19 exact-source enrichment; successful normal apply retained. No dossier mutation or new evidence engine.'}
path=B/'PROPOSED_CLAIM.v1.jsonl';serialized=json.dumps(c,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n'
if path.exists(): assert path.read_text()==serialized,'Frozen candidate changed'
else:path.write_text(serialized)
errors=assemble.check_claim(c,R);save('PRODUCER_GATES.v1.json',{'instrument_id':'EO:13975','claim_sha256':assemble.canonical_sha(c),'stage19_and_exact_source_errors':errors,'independent_review':False})
assert not errors,errors
manifest=[]
for r in records:
 raw=B/'source-cache'/r['cache_path'];tx=B/r['_output']/r['text_path']
 assert sha(raw)==r['sha256'] # ladder extracted_text_sha256 pins body, not wrapper file
 manifest.append({'citation':r['citation'],'url':r['url'],'raw':{'path':rel(raw),'sha256':sha(raw)},'ladder_receipt':{'path':rel(B/r['_output']/'SOURCES.jsonl'),'sha256':sha(B/r['_output']/'SOURCES.jsonl')},'extraction':{'path':rel(tx),'sha256':sha(tx)},'scope':r['page_or_item']})
save('SOURCE_MANIFEST.json',{'sources':manifest,'derived_texts':[{'path':rel(p),'sha256':sha(p)} for p in (B/'source-review').glob('*.txt')],'images_inspected':[{'path':rel(p),'sha256':sha(p)} for p in (B/'source-review/render').glob('*.png')],'official_pages_inspected':{'EO13975':[1,2],'EO14005':[4,5],'FAR2019-016':[1],'FARcorrection':[1],'SPP2020':[238],'SPP2021':[236]},'full_text_read':['EO13975','EO14005','EO13881'],'SPP_scope':'Complete source downloaded; full local text searched; p200 operative paragraphs inspected; not all746/760 pages read'})
save('SUPPLEMENT_AUDIT.v1.json',{'base':{'path':rel(basepath),'sha256':sha(basepath),'claim_sha256':assemble.canonical_sha(base)},'candidate':{'path':rel(path),'sha256':sha(path),'claim_sha256':assemble.canonical_sha(c)},'changes':['Remove claim_kit metadata because external-source enrichment is ordinary Stage19, not unchanged dossier assertion','Replace original representation/clauses with same PDF content on explicit page-checked derivative; keep9scopes,states,first_end dates and substantive inventory unchanged','Add FAR chronology to bothsection4subjects; exact corrected effective date; no end inferred','Add supported source_refs for FAR correction,SPP p200 andactor14-16','Append bounded search/disclosures and detailed provenance'],'removed_page_furniture':removed,'raw_original_sha256_unchanged':True,'no_new_adjudicated_status':True,'changed_claim_requires_full_independent_review':True})
print(json.dumps({'candidate':rel(path),'claim_sha256':assemble.canonical_sha(c),'strict_errors':errors},indent=2))
