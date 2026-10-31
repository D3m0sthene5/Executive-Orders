"""Bounded R3 replay through existing case builder, worksheet contract and consumers.

No acquisition, admission, canonical output overwrite, status, or certification.
Run from repository root: python3 research/progress/r3-ranger-roundtrip/replay.py
"""
import copy, hashlib, importlib.util, json, os, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BASE=Path(__file__).resolve().parent
REL=BASE.relative_to(ROOT)
def load(path):return json.loads((ROOT/path).read_text())
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n")
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
wb=module('r3_replay_workbench',Path('jobs/early-ranger-workbench/job.py'))
reg=module('r3_replay_census',Path('jobs/census-candidates/job.py'))
old='jobs/early-ranger-workbench/output/EARLY_SOURCE_REVIEW_WORKBENCH.html'
custodies=[str(REL/'research-polk/FACSIMILE_CUSTODY.json'),str(REL/'independent-source-review/FACSIMILE_CUSTODY.json')]
cases=wb.build_cases(ROOT,old,True,custodies)
producers={}
producer_paths=[REL/'research-madison/FINDINGS.json',REL/'research-jefferson/FINDINGS.json',REL/'research-polk/FINDINGS.json']
for p in producer_paths:
    d=load(p)
    for id_,note in d.get('items',d).items():
        if id_.startswith(('mjm','mtjbib','mss')):producers[id_]=(p,note)
independent_path=REL/'independent-source-review/FINDINGS.json'
independent=load(independent_path)
review_by={}
for f in independent['findings']:
    for id_ in [f['item']]+([f['related_item']] if f.get('related_item') else []):review_by[id_]=f
# These are attributed proposals, not automatic historical inclusion rules.
judgments={
'mjm017450':('recommend_exclusion','Exclude this Wanted checklist as the asserted standalone military-instruction text. It requests prior instructions; it does not contain those underlying orders. Whether the request itself was an issued administrative directive remains open.'),
'mjm018302':('hold','Prepared/revised Navy instructions: establish final adopted wording, presidential approval/transmission, uncertain manuscript date and historical naval-order inclusion before admission.'),
'mtjbib011110':('hold','Printed presidential naval instructions form has unfilled signature/addressee fields. Establish executed/issued representation and historical military-order treatment; retain affirmative By command evidence.'),
'mtjbib012509':('hold','Strong signed presidential expedition instruction: June20 dateline/signature is visible, while ante-June20 editorial description concerns drafting. Resolve draft/final transmission and historical expedition/military/letter-class inclusion and census crosswalk before admission.'),
'mtjbib016595':('hold','Seven-image revised Wilkinson/convention bundle includes alternate articles and envelope addressed to the President. Determine contributor/hand, final version, issued boundaries and historical class; never combine alternatives as simultaneous commands.'),
'mss365090092':('hold','Reclassify inspected bundle as rough drafts of a House message about withholding older Slidell instructions. Do not treat the short catalog title or Jan12 1848 record date as a new instruction to Slidell; reconcile message identity separately.'),
'mjm017456':('recommend_inclusion','Recommend an administrative presidential-instruction candidate: signed Aug13 1814 departmental reporting rules. Exact copy-witness comparison supports one research issuance cluster, without a second issuance demonstrated. Census/Lord crosswalk, final-version/issuance and formal inclusion adjudication remain required.'),
'mjm022917':('possible_duplicate','Actual pages begin Copy and reproduce the heading, ten rules, exception, reporting duty and close of mjm017456. Link as documentary witnesses of the same instruction in research; preserve distinct document/version IDs. No second issuance demonstrated; no candidate-row or census merge authorized.')}
notes={}
fields=['issuer_capacity','date_verified','original_page_matches_text','operative_clause_inventory','historical_inclusion_proposal','possible_first_cause','residuals_and_contrary_evidence','unresolved_gaps']
for id_,(disposition,reason) in judgments.items():
    path,source=producers[id_]
    note={k:(v if isinstance(v,str) else json.dumps(v,ensure_ascii=False,indent=2)) for k in fields if (v:=source.get(k)) is not None}
    note['reviewer']='R3 coordinator (OpenAI); producer gpt-6-luna; independent source examiner gpt-6-astra (configured models)'
    note['producer_proposal']=copy.deepcopy(source.get('proposal',source.get('structured_proposal')))
    examined=review_by[id_]
    note['issuer_capacity']=examined['issuer_capacity']
    note['date_verified']=examined['chronology']
    note['original_page_matches_text']=examined['identity']+'\n'+json.dumps(examined['source_pins'],ensure_ascii=False,indent=2)
    note['operative_clause_inventory']=json.dumps(examined['operative_inventory'],ensure_ascii=False,indent=2)
    note['residuals_and_contrary_evidence']=json.dumps(examined['limits'],ensure_ascii=False,indent=2)
    note['unresolved_gaps']=json.dumps(examined['limits'],ensure_ascii=False,indent=2)
    note['producer_artifact']={'path':str(path),'sha256':sha(path)}
    note['independent_source_examination']={'path':str(independent_path),'sha256':sha(independent_path),'finding':review_by.get(id_), 'scope':'same-family independent AI source examination; no human or admission certification'}
    note['coordinator_adjudication']=reason
    # Update current worksheet prose; producer's original exact artifact remains pinned above.
    note['historical_inclusion_proposal']=reason
    if id_ in ('mjm017456','mjm022917'):
        note['original_page_matches_text']='New independent examination of all 3 mjm017456 and 8 mjm022917 images finds corrected draft / explicitly labelled Copy documentary witnesses. Read 017456 in 03→01 left/right→02 order; 022917 in 08→01–05, then blank06/docket07. Word-for-word diplomatic equality is not asserted.'
        note['date_verified']='Aug13 1814 occurs on both image sequences. Identity linkage rests on copied substantive sequence and Copy label, as well as dates.'
        note['unresolved_gaps']='Preserve copy/draft variants; establish final sent/retained-copy role, crosswalk existing census/Lord and adjudicate historical inclusion. No later lifecycle ending research performed.'
    if id_=='mjm018302':
        note['date_verified']='Catalog Oct19 1816; later manuscript annotation ca October19 1816; independent reading finds nearby date 1815 or16 uncertain. Producer Oct16 reading remains in pinned producer artifact. Exact preparation/transmission date is held.'
    note['proposal']={'disposition':disposition,'reason':reason,'attribution':'AI_research','adoption_requirements':'Independent scientific/census inclusion adjudication and existing authorization; never supplied by source-version validation.'}
    notes[id_]=note
write(BASE/'case-packets/COORDINATOR_NOTES.json',notes)
doc=wb.rt.export_worksheet(cases,notes)
write(BASE/'case-packets/WORKSHEET.v2.json',doc)
records=wb.rt.validate_worksheet(doc,cases)
assert len(records)==8 and all(r['validation']=='unchanged_source' for r in records)
write(BASE/'case-packets/EXPORT_VALIDATION.json',records)
# Exercise actual generated HTML callbacks through the independent test harness.
tests=module('r3_replay_tests',Path('jobs/early-ranger-workbench/test_roundtrip.py'))
page=wb.make_html(cases,{'github_source_prefix':wb.GITHUB_RAW})
ui=subprocess.run(['node','-e',tests.NODE_RUN],input=json.dumps({'html':page,'raw':json.dumps(doc)}),text=True,capture_output=True,check=True)
observed=json.loads(ui.stdout)
write(BASE/'case-packets/UI_EXPORTED_WORKSHEET.v2.json',observed['exported'])
write(BASE/'case-packets/UI_RECEIPT.json',{'harness':'actual generated HTML script, minimal DOM in Node VM; no layout/image-decoding test','alerts':observed['alerts'],'ui_export_sha256':hashlib.sha256(json.dumps(observed['exported'],ensure_ascii=False,indent=2).encode()).hexdigest(),'exported_items':sorted(observed['exported']['per_case'])})
assert all(r['validation']=='unchanged_source' for r in wb.rt.validate_worksheet(observed['exported'],cases))
for c in cases:
    if c['id'] not in notes:continue
    compact=copy.deepcopy(c)
    for image in compact['master_JPEG_pages_stored']+compact.get('retained_facsimiles',[]):image.pop('display_data_uri',None)
    write(BASE/'case-packets'/f'{c["id"]}.json',{'case':compact,'worksheet_entry':doc['per_case'][c['id']]})
# Existing workbench CLI validates imports and restores them in the existing UI.
env={**os.environ,'REPO_ROOT':str(ROOT),'OUTPUT_DIR':str(BASE/'workbench'),'RANGER_SOURCE_REF':'88cef0253ed735b2a6e612770f25f9148641ce93'}
args=[sys.executable,str(ROOT/'jobs/early-ranger-workbench/job.py'),'--retained-workbench',old,'--include-retained-facsimiles','--import-worksheet',str(BASE/'case-packets/UI_EXPORTED_WORKSHEET.v2.json')]
for c in custodies:args+=['--facsimile-custody',c]
result=subprocess.run(args,cwd=ROOT,env=env,text=True,capture_output=True,check=True)
(BASE/'workbench/BUILD.log').write_text(result.stdout+result.stderr)
# Existing census job CLI, isolated OUTPUT_DIR only.
env['OUTPUT_DIR']=str(BASE/'census')
args=[sys.executable,str(ROOT/'jobs/census-candidates/job.py'),'--research-worksheet',str(BASE/'case-packets/UI_EXPORTED_WORKSHEET.v2.json'),'--retained-workbench',old,'--include-retained-facsimiles']
for c in custodies:args+=['--facsimile-custody',c]
result=subprocess.run(args,cwd=ROOT,env=env,text=True,capture_output=True,check=True)
(BASE/'census/BUILD.log').write_text(result.stdout+result.stderr)
items=[json.loads(line) for line in (BASE/'census/ITEM_CANDIDATES.jsonl').read_text().splitlines()]
assert len(items)==67 and sum(len(x.get('research_proposals',[])) for x in items)==8
assert all(x['census_membership']=='NOT_ADMITTED' and x['legal_inclusion']=='HOLD' and x['human_certified'] is False for x in items)
write(BASE/'REPLAY_RECEIPT.json',{'schema':'r3-native-roundtrip-replay/v1','LOC_candidates':len(items),'selected_items':sorted(notes),'source_bound_AI_proposals':8,'admitted':0,'human_certified':0,'input_code_sha256':{str(p):sha(p) for p in [Path('jobs/early-ranger-workbench/job.py'),Path('jobs/early-ranger-workbench/roundtrip.py'),Path('jobs/early-ranger-workbench/roundtrip.js'),Path('jobs/census-candidates/job.py')]},'source_custodies':{p:sha(p) for p in custodies},'worksheet_sha256':sha(REL/'case-packets/WORKSHEET.v2.json'),'UI_exported_worksheet_sha256':sha(REL/'case-packets/UI_EXPORTED_WORKSHEET.v2.json'),'final_candidate_output_sha256':sha(REL/'census/ITEM_CANDIDATES.jsonl'),'limits':'Native isolated tool replay and source-bound research only. No canonical adoption, readiness/lifecycle/status or census gain; no exhaustive historical census claim.'})
print('R3 replay passed: 8 source-bound proposals alongside 67 NOT_ADMITTED/HOLD candidates; no certifications.')
