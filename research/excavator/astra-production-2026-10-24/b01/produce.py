"""Explicit bounded partial supplement; strict kit cannot emit incomplete claims.
No network, canonical-claim, status, hold or codebook write. Exact source quotes.
"""
from pathlib import Path
import copy,json,hashlib,datetime,sys,csv
R=Path(__file__).resolve().parents[4]; B=Path(__file__).resolve().parent
# parents: b01 / run / excavator / research / repository
assert (R/'AGENTS.md').exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,j):p.write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n')
def txt(p):return p.read_text()
def between(t,a,z):
 s=t.index(a);e=t.index(z,s);return t[s:e]
def ref(path,url,raw,locator,parts):
 p=R/path;t=txt(p)
 for q in parts:assert q in t,(path,q[:100])
 return {'url':url,'sha256':raw,'page_or_item':locator,'text_path':path,'text_sha256':sha(p),'quoted_parts':parts,'read_method':'Held exact source text read by b01 producer; specific visual checks separately pinned in SOURCE_AUDIT.json.'}
def fr(n,parts,locator):
 p=f'jobs/fr-originals/data/full_run/texts/EO_{n}.txt';t=txt(R/p);lines=t.splitlines()
 return ref(p,lines[1].split('Source: ',1)[1],lines[2].split(': ',1)[1],locator,parts)
new=[]
for l in (B/'acquisition/output/SOURCES.jsonl').read_text().splitlines():
 j=json.loads(l)
 if j['sha256'] in ['958927407bf09446e5e678a91dd91b633d8bec4a4519900c422532e48d0bbf94','78ed0072ef4c3dbf17a8eaf492d3afc07dd19d34c43044f8dab1d571ae761dee']:new.append(j)
def page(raw,n,newsource=False):
 if newsource:
  j=next(x for x in new if x['sha256']==raw); p=B/'acquisition/output'/Path(j['text_path']).parent/f'page-{n}.txt'
 else:p=R/'jobs/astra-source-retention/output/pages'/raw/f'page-{n}.txt'
 return str(p.relative_to(R)),txt(p)
def stat(raw,n,url,loc,selector,newsource=False):
 p,t=page(raw,n,newsource); return ref(p,url,raw,loc,selector(t))
can=R/'research/readiness/claims/astra-source-first-2026-10-24.jsonl'
c=next(json.loads(l) for l in can.read_text().splitlines() if json.loads(l)['instrument_id']=='EO:11022')
c=copy.deepcopy(c)
original=txt(R/'jobs/fr-originals/data/full_run/texts/EO_11022.txt')
x67=txt(R/'jobs/fr-originals/data/full_run/texts/EO_11376.txt');x79=txt(R/'jobs/fr-originals/data/full_run/texts/EO_12106.txt');x82=txt(R/'jobs/fr-originals/data/full_run/texts/EO_12379.txt')
before=between(original,'(b) The Council shall','(c) The Chairman').rstrip()
after67=between(x67,'“(b)  The Council','T h e W h ite H ouse').strip()
after79=between(x79,'“ (b) The Council','FEDERAL REGISTER, VOL. 44').strip()
# Existing four full operative sections retained exactly, covering ten substantive units.
# Plain additions below are producer hypotheses; no date inferred for remaining first ends.
member=c['operative_clauses'][0]
for e in member['later_events']:
 if e['actor']=='EO:11376':
  e['before_text']=before;e['after_text']=after67
  e['before_text_source']=fr(11022,[before],'27 FR4659, PDF5, original section1(b)')
  e['mechanism']='Section1(b) restated; under the October21 owner ruling the clause continues amended. Full-section rewrite changes the roster; exact written before/after text recorded for human review.'
 if e['actor']=='EO:12106':
  e['before_text']=after67;e['after_text']=after79
  e['before_text_source']=fr(11376,[after67],'32 FR14545, PDF5, replacement section1(b)')
  e['before_text_qualification']='Before text is the last express EO restatement. Since 1975-01-04 its OEO reference legally means CSA under P.L.93-644 section9(a), new EOA section601(d)(2), recorded separately.'
  e['mechanism']='Section1-103 restates section1(b), effective1979-01-01 by section1-106. The roster continues amended: OPM replaces CSC, EEOC is added, and CSA reflects the1975 statutory substitution. Full-section substance changed; no first cessation inferred.'
raw88='78ed0072ef4c3dbf17a8eaf492d3afc07dd19d34c43044f8dab1d571ae761dee';url88='https://www.govinfo.gov/content/pkg/STATUTE-88/pdf/STATUTE-88-Pg2291.pdf'
s88a=stat(raw88,20,url88,'88 Stat2310, PDF20, P.L.93-644 section9(a), new EOA section601',lambda t:[t[t.index('SEC. 9. (a)'):]],True)
s88b=stat(raw88,21,url88,'88 Stat2311, PDF21, new EOA section601(d)(1)-(4)',lambda t:[between(t,'"(d) (1)','" (e) (1)')],True)
e75={'effective_date':'1975-01-04','actor':'P.L.93-644 section9(a), EOA section601(d)(2)','mechanism':'The statute makes CSA successor to OEO in all respects and for all purposes, and expressly deems all executive-order references to OEO or its Director to mean CSA or its Director from enactment. This carries forward the OEO seat inserted by EO11376; it adds no separate council mission and does not terminate the parent clause.','source':s88b,'supporting_sources':[{'source':s88a}],'before_text':'Director of the Office of Economic Opportunity','after_text':'Director of the Community Services Administration','text_kind':'Statutory reference substitution, not a newly quoted restatement of the full EO clause.'}
raw96='cea5509545c9944ce10a384a19d76e78abf6bbec0c66c2eff53880e09d06732d';url96='https://www.govinfo.gov/content/pkg/STATUTE-93/pdf/STATUTE-93-Pg668.pdf'
s96=stat(raw96,28,url96,'93 Stat695, PDF28, P.L.96-88 section509(a)-(b)',lambda t:[between(t,'REDESIGNATION','COORDINATION OF PROGRAMS')])
x80=txt(R/'jobs/fr-originals/data/full_run/texts/EO_12212.txt')
s80=fr(12212,[between(x80,'1-101.','1-102.').strip()],'45 FR29557, PDF11, EO12212 section1-101')
e80={'effective_date':'1980-05-04','actor':'P.L.96-88 section509; EO12212 section1-101','mechanism':'HEW and its Secretary are redesignated HHS. Section509(b) carries official-paper references forward except transferred Education functions. The general Council on Aging chair is not an education-function transfer identified in section301. This is continuity of the chair, not an end of the council or an additional agency seat.','source':s96,'supporting_sources':[{'source':s80}],'before_text':'Secretary of Health, Education, and Welfare','after_text':'Secretary of Health and Human Services','text_kind':'Statutory reference substitution.'}
raw97='aacf815d01c9c3d797d7c516d9ccddd1f723dc1a44e47f8899ba742d988e2127';url97='https://www.govinfo.gov/content/pkg/STATUTE-95/pdf/STATUTE-95-Pg357.pdf'
s97=stat(raw97,163,url97,'95 Stat519, PDF163, P.L.97-35 sections682(e),683(a)-(c)',lambda t:[between(t,'(e) Upon the enactment','TITLE VII')])
e81={'effective_date':'1981-10-01','actor':'P.L.97-35 section683(a)','mechanism':'Repeals the Economic Opportunity Act except titlesVIII andX, with section682(e) directing disposition of CSA affairs and section683(c)(3) preserving proceedings. New EOA section601 establishing CSA was in titleVI. The disappeared CSA office is a material council-membership issue; the statute does not name EO11022 or abolish its whole council. No automatic substitution of the new HHS Office of Community Services Director, or clause-wide first end, is asserted.','source':s97,'supporting_sources':[{'source':s88a}]}
member['later_events'].extend([e75,e80,e81]);member['later_events'].sort(key=lambda e:e['effective_date'])
raw79='958927407bf09446e5e678a91dd91b633d8bec4a4519900c422532e48d0bbf94';url79='https://www.govinfo.gov/content/pkg/STATUTE-79/pdf/STATUTE-79-Pg667.pdf'
s79a=stat(raw79,3,url79,'79 Stat669, PDF3, P.L.89-174 section5(a)-(b)',lambda t:[between(t,'SEC. 5. (a)','(c) The President')],True)
s79b=stat(raw79,5,url79,'79 Stat671, PDF5, P.L.89-174 sections9(c),11(a)-(b) and approval',lambda t:[between(t,'(c) Except','SEPARABILITY'),t[t.index('EFFECTIVE DATE AND'):]],True)
rawfa='d46eb8e8384da8352c9619cf2c5df1c534e0b20dd36b68317c76bf5b612718d8';urlfa='https://www.govinfo.gov/content/pkg/STATUTE-86/pdf/STATUTE-86-Pg770.pdf'
sfa=stat(rawfa,1,urlfa,'86 Stat770, PDF1, FACA section3(2) (OCR heading8; earlier PR58 visual check identifies3)',lambda t:[t[t.index('(2) The term "advisory committee"'):]])
sfa14=stat(rawfa,7,urlfa,'86 Stat776, PDF7, FACA sections14-15; adjacent92-464 not part of FACA',lambda t:[between(t,'SEC. 14.','Approved October 6, 1972.')+'Approved October 6, 1972.'])
s96s=stat(raw96,24,url96,'93 Stat691, PDF24, P.L.96-88 section505(a)',lambda t:[between(t,'SEC. 505. (a)','(b)(1)')])
context=[{'issue':'HHFA/HUD succession before1967 express roster rewrite','finding':'Section5(a) transfers all HHFA functions/powers/duties to HUD Secretary; section9(c) preserves existing actions and addresses references in another Federal law, and lapses prior offices. This is material continuity/office-history evidence, not a named revocation of EO11022. Section11(a) supplies a60-day default effective rule from1965-09-09 with possible earlier presidential action. Exact effective-date/adaptation of this EO seat remains qualified pending the bounded earlier-order check; no1965 first end or falsely complete roster chronology is asserted.','source':s79b,'supporting_sources':[{'source':s79a}]},{'issue':'FACA potential earlier sunset','finding':'Section3(2) excludes a committee wholly composed of full-time federal officers/employees. The original,1967,and1979 rosters and section1(c) temporary members are federal department/agency heads. Thus FACA section14 does not itself supply an earlier two-year sunset for this Council. This is separate applicability analysis of the prior EO11782 statutory sources, not group approval.','source':sfa,'supporting_sources':[{'source':sfa14}]},{'issue':'HEW/HHS savings','finding':'Section509 preserves chair-office continuity; section505(a) saves instruments for transferred functions subject to later lawful modification/revocation. It does not preserve this Council against EO12379. Section301 education transfers were read separately; no general aging-council transfer appears in the inspected provisions.','source':s96,'supporting_sources':[{'source':s96s}]},{'issue':'EO12106 versus EO12107 source association','finding':'Both full orders read; EO12106 section1-103 is the express target amendment. EO12107 section2-101 applies general OPM redesignations to responsibility-related orders and its numbered list does not name11022. Actual PDF323 reads10982 rather than OCR19982; no11022 entry occurs between it and11103. Its general clause cannot replace the explicit same-day EO12106 roster or redirect the amendment to12107. Prior rejection is retained.','source':fr(12107,[between(txt(R/'jobs/fr-originals/data/full_run/texts/EO_12107.txt'),'2-101.','(a) Executive orders relating')],'44 FR1056, PDF322, section2-101')}]
c['counterevidence_review']=context
c['savings_residuals']={'state':None,'reason':'No express internal savings in the complete EO12379, but whole-case residual classification remains open. Original section4 executed abolition/supersession must be separated from ongoing Council duties and cannot be treated as revival of the1959 body. Statutory continuity/savings in P.L.89-174 sections7/9, P.L.93-644 new601(d), P.L.96-88 section505 and P.L.97-35 sections682(e)/683(c)(3) are identified rather than silently ignored. They address transferred functions, actions, liabilities or proceedings and do not alone establish an independent surviving Council command.','source':None,'supporting_sources':[{'source':s79b},{'source':s88b},{'source':s96s},{'source':s97}]}
c['unresolved_material_gaps']=['Complete exact HHFA-to-HUD effective-date and EO-seat treatment before the1967 restatement; section11 default rule and possible earlier presidential action are now held rather than assumed.','Resolve clause-specific first cessation and residual treatment of the self-executing1962 section4 predecessor abolition/supersession separately from continuing sections1-3. Retain the1981 CSA office-termination/member-seat issue; no whole-parent end is inferred from an unnamed statute.','Complete the remaining bounded intervening-event/current-law and savings review through2026-10-14, including distinguishing the separately established statutory Federal Council on Aging from the President\'s Council; no machine search or exhaustion claim is accepted.']
c['later_source_search']=[];c['whole_order_end']=None
c['research_rationale']='This is a materially expanded partial replacement proposal for Astra ownership review, not a complete lifecycle or human certification. It retains the four complete original operative sections previously checked in PR56, including all ten substantive units and the independent section4 predecessor abolition. The full originals of EO11022,11376,12106,12107,12212 and12379 were read in this fresh context;11022,11376,the relevant12106 page,the disputed12107 list and both12379 pages were visually checked. Exact written before/after rosters accompany the1967/1979 amendments, which continue the parent clause under theOctober21 owner ruling. New held P.L.93-644 establishes OEO-to-CSA reference continuity from1975-01-04. Separately read prior retained P.L.96-88/EO12212 supports HEW-to-HHS continuity from1980-05-04. Held P.L.97-35 supplies the material1981 CSA repeal/transition question, not a blanket parent ending. Newly acquired P.L.89-174 supplies HHFA/HUD transfer and savings text while its precise seat/effective-date application remains qualified. FACA wholly-federal exclusion is separately tested against this roster. EO12379 section12 is an express1982 revocation event; first ends, final savings classification and complete counterevidence remain unfilled. October18 partial review and PR56 corrected-v3 are attributed prior research; obsolete amendment-as-first-end language and the rejected12107 inference are not reused.'
for x in c['operative_clauses']:
 x['first_end']=None
 x['judgment_reason']='Terminated at cutoff is supported by the expressly named1982 revocation. The first effective end remains unresolved and is not supplied by a membership rewrite, a general office-transfer statute, or mere administrative inactivity. '+('This full section includes establishment, composition and temporary-member duties; expanded statutory events apply specifically to section1(b), not wholesale to1(a) or1(c).' if x['scope_id'].endswith('sec1') else 'The original text and distinct commands are retained without omission.')
c['research_provenance']={'producer':'Astra /root/research_reconciliation','publication_status':'partial_replacement_proposal_only','current_canonical_path':str(can.relative_to(R)),'current_canonical_file_sha256':sha(can),'base_current_claim_sha256':hashlib.sha256(json.dumps(next(json.loads(l) for l in can.read_text().splitlines() if json.loads(l)['instrument_id']=='EO:11022'),sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest(),'prior_context_packet':'research/excavator/astra-production-2026-10-24/b01/packet-v2/PACKET.json','assembler_limit':'ordinary strict assembler emits no incomplete claims and has no evidence IDs for newly acquired statutory pages; ordinary prepare/view/apply retained separately, partial supplement uses supported Stage19 schema and exact source references.','prior_unchanged_bytes_retained':True,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'tokens':None,'cached_tokens':None,'model_cost':None}
sys.path.insert(0,str(R/'research/stage19/code'));import claim_gate
p=B/'CLAIMS.partial.proposed-v1.jsonl';p.write_text(json.dumps(c,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n')
dump(B/'PROPOSAL-v1.json',{'instrument_id':'EO:11022','claim_path':str(p.relative_to(R)),'claim_file_sha256':sha(p),'claim_sha256':claim_gate.claim_sha(c),'expected_gate_errors':claim_gate.validate_claim(c,expected_status='no'),'review_scope':'partial_research','source_count':len(new),'producer_completed_utc':c['research_provenance']['completed_utc']})
print(json.dumps(json.loads((B/'PROPOSAL-v1.json').read_text()),indent=2))
