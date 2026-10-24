"""Produce exact b02 v3 research assertions and completion input, no publication."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[4]
B=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'jobs/claim-kit'))
import assemble

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p): return p.relative_to(ROOT).as_posix()
def pin(p): return {'path':rel(p),'sha256':sha(p)}
def save(n,v): (B/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def exact(base,a,z):
 r=deepcopy(base); t=(ROOT/r['text_path']).read_bytes().decode();r.update(char_start=a,char_end=z,quote=t[a:z]);return r
for name in ['COMPLETION.producer','SELECTED_VERSIONS','PRODUCER_GATES','SOURCE_EVIDENCE']:
 src=B/(name+'.json'); dst=B/(name+'.v2.json')
 if not dst.exists(): shutil.copyfile(src,dst)
if not (B/'RESEARCH.v2.md').exists(): shutil.copyfile(B/'RESEARCH.md',B/'RESEARCH.v2.md')
claims=[json.loads(x) for x in (B/'PROPOSED_CLAIMS.v2.jsonl').read_text().splitlines()]
record=json.loads((B/'acquisition-v1/SOURCES.jsonl').read_text())
tp=B/'acquisition-v1'/record['text_path']; text=tp.read_bytes().decode()
a=text.index('Despite this effort');z=text.index(' On April 18, 1979,',a)
gao={'url':record['url'],'sha256':record['sha256'],'local_path':rel(B/'acquisition-v1'/record['cache_path']),'text_path':rel(tp),'text_sha256':sha(tp),'page_or_item':'GAO CED-81-139, B-203827, July 2, 1981, printed page 3 / PDF page 3; full ten-page report read and page 3 image inspected','char_start':a,'char_end':z,'quote':text[a:z]}
assert sha(ROOT/gao['local_path'])==gao['sha256']
parent_source=claims[0]['original_representation']
parent_condition=exact(parent_source,2568,2731)
stat=deepcopy(claims[0]['research_sources'][0])
end={'date':'1975-12-12','actor':'EO:11829 section 4, incorporating Public Law 93-531 section 1(a)','mechanism':'Express conditional termination upon cessation of the statutory Mediator duties: after no settlement, the Mediator submitted his recommendations for judicial partition to the District Court on December 12, 1975. GAO supplies the occurrence; the cited original section 4 and statutory section 1(a) supply legal effect. Neither the April 17, 1975 amendment, a negotiation/report deadline, the April 18, 1979 partition judgment, nor the August 17, 1982 formal revocation is substituted for this first end.','source':deepcopy(gao),'legal_sources':[deepcopy(parent_condition),deepcopy(stat)]}
for c in claims:
 iid=c['instrument_id']
 c['research_sources'] += [deepcopy(parent_condition),deepcopy(gao)]
 c['research_rationale']=c['research_rationale'].split('A new public discovery lead')[0] + ('New retained factual evidence: the complete GAO CED-81-139 report, p3, states that no settlement was reached and that the Mediator submitted his judicial-partition recommendations to the District Court on December12,1975. The first statement excludes the alternative full-agreement route on this official account; the second establishes the express statutory submission occurrence. The December12 date therefore ends the Committee and its dependent functional authority under EO11829 section4, as amended by EO11853. The report is a retrospective official factual source, not a legal instrument; the legal effect follows from separately pinned original and statutory texts. It does not show that the Mediator notified the Chairman or that any Committee records were transferred. The later1979 judicial partition and independent relocation program are distinct. This material date advancement is newly found and retained; the statutory construction and seven-unit inventory are restored prior research, not new discoveries. ')
 c['research_provenance'].update(revision='b02-v3',restored_prior_vs_new='Restored and reconciled qualified Oct18 seven-unit inventory and PR56 statutory trigger reasoning. New retained GAO occurrence establishes December12,1975 submission and no negotiated settlement; clause application newly advanced. Notice/records performance and bounded counterevidence completion remain open.')
 c['research_provenance']['source_custody_receipt']=rel(B/'acquisition-v1/SOURCES.jsonl')
 if iid=='EO:11829':
  reasons=[
   'The Committee and its membership offices terminate when the Mediator duties cease under the incorporated statutory condition. The retained GAO account supplies December12,1975 as that occurrence. The HEW succession lead in1980 therefore cannot change the roster of a Committee already terminated in1975.',
   'The information function continues through the April17,1975 amendment; exact before-and-after text is preserved in its later event. It ends with the Committee on the statutory report-submission occurrence, December12,1975.',
   'Meetings and liaison serve timely development of the Committee information. They end with the Committee on December12,1975. The negotiation time-limit reference is not itself the termination event.',
   'Interior administrative and staff support serves this Committee and ends with it on December12,1975. The separate statutory Relocation Commission and its Interior support are not continuation of this command.',
   'The express dissolution condition occurred on December12,1975: GAO says no settlement was reached and the Mediator submitted his recommendations to the District Court. Statutory section1(a) makes submission after failed negotiations the cessation event. Notice to the Chairman is required separately; it is not the dissolution condition.',
  ]
  for cl,reason in zip(c['operative_clauses'][:5],reasons):
   cl['first_end']=deepcopy(end);cl['judgment_reason']=reason
  for cl in c['operative_clauses'][5:]:
   cl['judgment_reason'] += ' The newly verified December12,1975 submission establishes cessation of Mediator duties and activation of the wind-down context, but does not establish this command was performed or its first end.'
  c['whole_order_end']=None
  c['unresolved_material_gaps']=[
   'Resolve separately section4 notice to the Chairman and transfer of any Committee records: performance dates, whether records were maintained, and any concrete accrued custodial effects remain unproved. December12,1975 dissolution is not proof of those distinct acts; their first_end and whole_order_end stay null.',
   'Complete bounded intervening and later-event/savings/counterevidence review through2026-10-14 for the independent wind-down commands and the asserted functional first ends. Existing Oct18 named-scope search and current kit screens are qualified retained research, not a new complete archive or statutory-history search. The1980 HEW succession lead is no longer material to a Committee shown ended in1975.'
  ]
  c['research_rationale']+='Member scope: five Committee-related first ends now have an exact occurrence and legal link. Separate notice and records first ends, residual effects and whole-order end remain unproved.'
 else:
  c['operative_clauses'][0]['first_end']=deepcopy(end)
  c['operative_clauses'][0]['judgment_reason']='The complete amending instrument only replaces parent section2(a), with no independent notice, records or relocation command. Under the owner amendment ruling the information function continues amended until the parent section4 statutory cessation on December12,1975. GAO establishes no settlement and actual report submission; the parent original and statute supply the legal link. Parent wind-down commands are not imported as commands of this amendment. EO12379 later revokes the parent as amended and does not directly name EO11853.'
  c['whole_order_end']=deepcopy(end)
  c['whole_order_end']['mechanism']+=' EO11853 has one complete dependent information amendment and no separate operative command, so this is also its whole-order end, subject to the explicitly unfinished counterevidence review.'
  c['unresolved_material_gaps']=['Complete bounded intervening-event and savings/counterevidence review for the dependent amendment through2026-10-14. The retained GAO occurrence and original/statutory legal link support December12,1975 first and whole-order end; partial filing does not certify complete search or savings closure. Parent notice/records commands are not imported as independent commands of EO11853.']
  c['research_rationale']+='Member scope: the sole dependent information amendment has December12,1975 as its first and whole-order end; complete bounded counterevidence and savings review remain unapproved.'
  c['savings_residuals']['reason']+=' The GAO report distinguishes independent relocation activity after the Mediator submission; it creates no surviving command in EO11853. No separate parent wind-down obligation is assigned to this amendment.'

# A fresh factual discovery is now a retained source; keep the prior draft intact.
research=(B/'RESEARCH.v2.md').read_text()
research=research.replace('The seven-unit inventory can retain this precise state standard while leaving all unsupported dates null.','The seven-unit inventory retains this precise state standard; the new v3 evidence below supports dates for the five Committee functions while notice and records remain separately unresolved.')
research=research.replace('Its actual outcome and machine/network cost are retained under `acquisition-v1/`; snippets alone do not become a certified occurrence or an exact claim first-end.','It completed successfully: one exact PDF retained, ten pages extracted, two HTTP requests, 879,729 downloaded bytes, 424.11209376700026 seconds measured job wall time. Raw SHA-256 is `2ff7480200648a0fb6525a90d888296a73434f7f13cded9fe733457bc55a426d`. All ten pages were read; report cover and page3 images were visually inspected. The submission date is clear in the actual page. `acquisition-v1/SOURCES.jsonl`, `RESULTS.json`, and `SUMMARY.json` preserve acquisition and extraction custody. The unretained Congressional Record and court-summary discoveries remain corroborating leads only and are not claim evidence.')
research=research.replace('The legal application, if independently accepted after custody and source review, would end the Committee\'s information functions at the section1(a) occurrence; it would not prove completion of the separate notice/records commands or end the separate Relocation Commission. EO11853 contains no independent notice or records command, so its first-end question is narrower than EO11829\'s whole-order end.',"The v3 proposed legal application is now explicit. GAO says no settlement was reached, so its account excludes the alternative full-agreement trigger. It says the Federal mediator submitted his recommendations for judicial partition to the District Court on December12,1975. P.L.93-531 §1(a) makes that report submission the cessation event after failed negotiations, and EO11829 §4 incorporates that event. Thus the Committee establishment/membership, information function as amended, meetings/liaison, Interior support and dissolution command end on December12,1975. April18,1979 judicial partition is later and is not the trigger. GAO is a retrospective official factual account (its report methodology includes legislation, regulations, project files and interviews); it does not purport to be the legal termination instrument. The source combination, rather than GAO alone, supports the inference.\n\nGAO does not establish the Chairman was advised or any Committee records were transferred. Those commands keep separate null first ends, and EO11829 whole-order end remains null. EO11853 contains only the dependent information amendment and no independent notice/records/relocation commands, so its sole first end and whole-order end are proposed as December12,1975. Its overall publication scope still remains partial because bounded counterevidence and savings review have not been completed. EO12379 is retained as a later formal cleanup event; its date is not the first end. The1980 HEW succession lead no longer changes the functional roster of a Committee ended in1975. Independent review must assess both the factual source and this clause-specific application.")
research=research.replace('Remaining questions are specific occurrence proof and its precise clause application, the independent notice/records performance and residuals, and bounded intervening/later-event review.','The specific occurrence is now retained and asserted with the original/statutory legal link. Remaining questions are independent notice/records performance and residuals, and bounded intervening/later-event review; the exact v3 application still requires independent review.')
(B/'RESEARCH.md').write_text(research)
out=B/'PROPOSED_CLAIMS.v3.jsonl';assert not out.exists()
out.write_text(''.join(json.dumps(c,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for c in claims))
evidence=json.loads((B/'SOURCE_EVIDENCE.v2.json').read_text())
evidence.update(new_discovery_qualified_only=False,new_occurrence_source=gao,parent_condition_source=parent_condition,full_gao_report_read=True,gao_page_images_inspected=[1,3],unretained_leads_not_used=['Congressional Record June17,1977 p19634','626 F2d113 court account'],source_custody=pin(B/'acquisition-v1/SOURCES.jsonl'))
save('SOURCE_EVIDENCE.json',evidence)
gate=assemble._gate(ROOT);results=[]
for c in claims:
 errors=gate.validate_claim(c,expected_status=c['whole_order_status']);strict=assemble.check_claim(c,ROOT)
 results.append({'instrument_id':c['instrument_id'],'claim_sha256':assemble.canonical_sha(c),'publication_kind':'partial_research','expected_gate_errors':errors,'strict_errors':strict,'non_gate_errors':[x for x in strict if x not in errors]})
assert all(not r['non_gate_errors'] for r in results),results
save('PRODUCER_GATES.json',results)
save('SELECTED_VERSIONS.json',{'selected_at_utc':datetime.now(timezone.utc).isoformat(),'agent':'astra-production-b02','producer_model_family':'OpenAI','claims':[dict(r,claim={**pin(out),'line':i+1}) for i,r in enumerate(results)],'human_certification':0})
save('PRODUCER_TELEMETRY.json',{'producer':'astra-production-b02','producer_model_family':'OpenAI','session_start_utc':None,'first_recorded_utc':'2026-10-24T16:39:07Z','producer_freeze_utc':datetime.now(timezone.utc).isoformat(),'session_elapsed_seconds':None,'session_start_note':'No exact timestamp was captured at agent task receipt; first_recorded_utc is not falsely reported as the start.','ordinary_prepare_seconds':7.3368,'acquisition':json.loads((B/'acquisition-v1/SUMMARY.json').read_text()),'git_held_materialization_bytes':154478135,'git_held_materialization_downloads':0,'model_input_tokens':None,'model_output_tokens':None,'cached_tokens':None,'model_dollars':None,'active_labor_seconds':None,'token_or_cash_savings_claimed':False,'attempts':[{'command':'kit.py prepare EO:11829 EO:11853 --agent astra-production-b02 --replacement-proposal --write b02/packet-v1','outcome':'success','receipt':rel(B/'packet-v1/PREPARE.json')},{'command':'kit.py view packet-v1 --order EO:11829; kit.py view packet-v1 --order EO:11853','outcome':'success','artifacts':[rel(B/'EO11829-view.txt'),rel(B/'EO11853-view.txt')]},{'command':'kit.py apply packet-v1 --write b02/applied-v1','outcome':'rejected','reason':'Output directory must be under packet.'},{'command':'kit.py apply packet-v1 --write packet-v1/applied-v1','outcome':'rejected','reason':'Changed Valla review context; prepare a new version.'},{'command':'assemble.derive_inventory on explicit seven-unit inventory','outcome':'success','receipt':rel(B/'INVENTORY_PROOF.json')},{'command':'Existing request_contract enqueue + bounded existing retention job','outcome':'success','receipt':rel(B/'acquisition-v1/SUMMARY.json')}],'intermediate_versions_preserved':['PROPOSED_CLAIMS.v1.jsonl','PROPOSED_CLAIMS.v2.jsonl'],'partial_draft_method':'Explicit ordinary lifecycle claim; existing assembler validated exact inventory and strict source spans; no claim_kit metadata or successful apply falsely asserted.','control_access':False,'subagents_spawned':0,'human_certification':0})
receipts=['RESEARCH.md','SOURCE_EVIDENCE.json','INVENTORY_PROOF.json','PRODUCER_GATES.json','SELECTED_VERSIONS.json','PRODUCER_TELEMETRY.json','MATERIALIZATION.json','FETCH_REQUESTS.jsonl','RETENTION_REQUESTS.json','acquisition-v1/SUMMARY.json','acquisition-v1/RESULTS.json','acquisition-v1/SOURCES.jsonl','packet-v1/PREPARE.json','packet-v1/PACKET.json','packet-v1/decisions.csv','packet-v1/RATIONALES.json']
manifest={'schema':'eo-claim-kit-completion/v1','agent':'astra-production-b02','producer_model_family':'OpenAI','independence_requirement':'same_family_separate_context','publication':{'mode':'replacement_proposal','path':rel(B/'reviewed-proposal/CLAIMS.proposed.jsonl')},'members':[{'instrument_id':c['instrument_id'],'outcome':'submit','claim_sha256':assemble.canonical_sha(c),'claim':{**pin(out),'line':i+1},'publication_kind':'partial_research'} for i,c in enumerate(claims)],'controls':[],'receipts':[pin(B/n) for n in receipts]}
save('COMPLETION.producer.json',manifest)
print(json.dumps({'claim_file':pin(out),'results':results,'completion':pin(B/'COMPLETION.producer.json')},indent=2))
