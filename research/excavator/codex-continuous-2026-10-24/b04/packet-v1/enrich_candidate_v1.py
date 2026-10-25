"""Add source-read continuity evidence using the existing ordinary Stage19 format."""
from pathlib import Path
import json,re,hashlib,sys,copy
B=Path(__file__).resolve().parent;R=B.parents[4];sys.path.insert(0,str(R/'jobs/claim-kit'));import assemble
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(R).as_posix()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def source(n,start,end=None):
 p=R/f'jobs/fr-originals/data/full_run/texts/EO_{n}.txt';t=p.read_text();a=t.index(start);z=t.index(end,a) if end else len(t)
 return {'url':re.search(r'^Source: (.+)',t,re.M).group(1),'sha256':re.search(r'downloaded file: (\w+)',t).group(1),'text_path':rel(p),'text_sha256':sha(p),'page_or_item':re.search(r'^Location: (.+?) \(confidence',t,re.M).group(1)+'; complete instrument page images inspected','char_start':a,'char_end':z,'quote':t[a:z]}
basepath=B/'applied-v1/CLAIMS.proposed.jsonl';base=json.loads(basepath.read_text());c=copy.deepcopy(base);kit=c.pop('claim_kit')
# Preserve the exact two assembled original clause spans and source grade.
# Narrow original metadata to the EO rather than unrelated neighboring page content.
c['original_representation']=source(10704,'EXECUTIVE ORDER 10704','TITLE 10— ATOMIC ENERGY')
end=source(10931,'S e c. 2.','J o h n F . K e n n e d y')
end['signing_date']='1961-03-29'
parent=source(10673,'EXECUTIVE ORDER 10673','RULES AND REGULATIONS')
section4=source(10772,'EXECUTIVE ORDER 10772','TITLE 6— AGRICULTURAL CREDIT')
successor=source(11074,'Executive Order 11074',None)
c['source_refs']=[parent,section4,successor]
# Exact before/after quotations with source pointers for each of the two scopes.
changes={
 '1':[(source(10704,'1. The President','2. Section'),source(10740,'L The President','2. Section')), (source(10740,'L The President','2. Section'),source(10785,'1. The President','2. Section'))],
 '2':[(source(10704,'2. Section','D wight'),source(10740,'2. Section','D w ight')), (source(10740,'2. Section','D w ight'),source(10785,'2. Section','D w ig h t'))]
}
for cl in c['operative_clauses']:
 cl['first_end']['source']=copy.deepcopy(end)
 for event,(before,after) in zip(cl['later_events'],changes[cl['scope_id'].split('#')[1]]):
  event['text_before']=before['quote'];event['text_after']=after['quote'];event['sources']=[before,after]
  event['source']=copy.deepcopy(after)
  event['human_review_note']='The membership/chair substance changed; the clause continues amended under the owner strike-and-insert ruling. Text is exact held OCR checked against official images.'
c['whole_order_end']['source']=copy.deepcopy(end)
c['savings_residuals']['source']=copy.deepcopy(end)
c['savings_residuals']['sources']=[parent,successor]
c['later_source_search'].append({'repository':'Qualified prior Sinclair status/D6 research plus bounded producer reconciliation of held family sources and public official discovery','query_or_scope':'Reused the carried historical search and correction, without repeating the same held full-run 10704 search. Inspected 31 exact target_id rows for EO10704/10673/10931 in held EDGES.csv; read complete official EO10673,10704,10740,10772,10785,10931,11074. New source work resolves original inventory, before/after membership, parent duties, successor continuity and no restoration. NARA1957 disposition and1989 codification entry checked online as corroborative editorial context; supplemental official-domain query for10704 revocation/restoration found no additional responsive legal text, not an exhaustive absence finding. USC inherited release ends2026-10-09; CFR point-in-time and OFR search scope reach2026-10-14. Earlier interpretation rejected under owner ruling, not an inference from catalog labels. All bounds/paths and exact prior versions remain in RESEARCH.v1.md, FAMILY_EDGES.v1.json and PACKET.json.','checked_on':'2026-10-25'})
c['research_rationale']+=' The exact before-and-after quotations for both scopes are included in later_events with source references. The completed normal batch assembly is preserved unchanged; this ordinary Stage19 enrichment adds explicit source support for parent/successor continuity and narrows the original/revocation quotations to the relevant instrument provisions. The absent historical APP alternatives are not relied on: matching pinned official FR representations and their newly retrieved exact raw bytes supply the current evidence.'
c['research_provenance']={'producer':'codex-continuous-prior-b04','producer_model_family':'OpenAI','actual_model_version':'not exposed by runtime','revision':'b04-v1','normal_packet':rel(B/'PACKET.json'),'normal_packet_sha256':sha(B/'PACKET.json'),'assembled_base':rel(basepath),'assembled_base_sha256':sha(basepath),'assembled_base_claim_sha256':assemble.canonical_sha(base),'page_review_manifest':rel(B/'SOURCE_MANIFEST.v2.json'),'substantive_analysis':rel(B/'RESEARCH.v1.md'),'prior_research_pointer':rel(B/'PACKET.json')+'#/prior_research/orders/EO:10704','independence_requirement':'same_family_separate_context','status_scope':'Existing adopted provisional NO unchanged; historical cross-family status review remains limited and does not approve this lifecycle.','supplement_route':'Existing ordinary Stage19 exact-source enrichment after successful normal kit apply. No dossier edits, new status authority or assembler bypass.','human_certifications':0}
p=B/'PROPOSED_CLAIM.v1.jsonl';serialized=json.dumps(c,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n'
if p.exists():assert p.read_text()==serialized,'Immutable candidate changed'
else:p.write_text(serialized)
errors=assemble.check_claim(c,R)
save(B/'PRODUCER_GATES.v1.json',{'instrument_id':'EO:10704','claim_sha256':assemble.canonical_sha(c),'stage19_and_exact_source_errors':errors,'independent_review':False})
save(B/'SUPPLEMENT_AUDIT.v1.json',{'normal_assembly':{'path':rel(basepath),'sha256':sha(basepath),'claim_sha256':assemble.canonical_sha(base)},'candidate':{'path':rel(p),'sha256':sha(p),'claim_sha256':assemble.canonical_sha(c)},'changes':['Remove claim_kit label because this enriched object is an ordinary Stage19 claim; unchanged normal assembly retained.','Retain exact two original clauses, states, amendments and first-end dates; narrow original/revocation source spans.','Add exact before/after text and sources to both membership events for both scopes.','Add complete source_refs10673/10772/11074 and savings sources to disclose institutional/independent continuity.','Append bounded search/reconciliation and provenance.'],'changed_claim_requires_independent_whole_case_review':True,'source_read_model_family':'OpenAI','core_code_changed':False})
print(json.dumps({'claim_sha256':assemble.canonical_sha(c),'errors':errors},indent=2));assert not errors,errors
