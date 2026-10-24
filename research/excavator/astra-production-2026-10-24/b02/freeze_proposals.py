"""Freeze this producer's explicit partial research; no inference/publication."""
import copy
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'jobs/claim-kit'))
import assemble

def canon(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(name, value):
    (BASE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def pin(path):
    path = ROOT / path
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)}

def ref(base, start, end):
    result = copy.deepcopy(base)
    text = (ROOT / result['text_path']).read_text(encoding='utf-8')
    result.update(char_start=start, char_end=end, quote=text[start:end])
    assert hashlib.sha256(text.encode()).hexdigest() == result['text_sha256']
    return result

prior_path = ROOT / 'research/readiness/claims/astra-source-first-2026-10-24.jsonl'
prior = {c['instrument_id']: c for c in map(json.loads, prior_path.read_text().splitlines())}
stat_path = Path('jobs/source-ladder/output/texts/queue_EO_11829_Public_Law93-531_Dec22_1974_88_Stat1712_especially_sections1_a_1_c_2_3_a_6174902fc1.txt')
stat = (ROOT / stat_path).read_text(encoding='utf-8')
stat_base = {
    'url': 'https://www.govinfo.gov/content/pkg/STATUTE-88/pdf/STATUTE-88-Pg1712.pdf',
    'sha256': '3b49dbad0980b7e745d8d4360a340aa073859b4580b0c3243142a5ecfafb3fd1',
    'text_path': stat_path.as_posix(), 'text_sha256': sha(ROOT / stat_path),
    'page_or_item': 'Public Law 93-531, 88 Stat 1712-1714, sections 1-4; PDF pages 1-3; controlling page images inspected',
}
stat_refs = {}
for key, a, b in [
    ('statutory_cessation', 'The dnties of the Mediator', '\n(b) The proceedings'),
    ('statutory_committee', '(2) To facilitate', '\n(d) The Secretary'),
    ('negotiation_and_submission', 'SEC. 3. (a)', '\nHearing. (b)'),
    ('separate_relocation_commission', 'SEC. 12. (a)', '\nSEC. 13. (a)'),
]:
    start, end = stat.index(a), stat.index(b, stat.index(a))
    stat_refs[key] = ref(stat_base, start, end)
stat_refs['separate_relocation_commission']['page_or_item'] = 'P.L.93-531 section12, 88 Stat1716-1717, PDF pages5-6; held text read; page images not newly inspected'

common = (
    'Recovered prior statutory reasoning is now made explicit and pinned: P.L.93-531 section1(a) ends the Mediator duties '
    'on entry of a full agreement into the supplemental Healing records under section3, or submission of a report to the '
    'District Court after negotiation default or partial agreement under section4. The actual occurrence, not the 180-day '
    'negotiation schedule or 90-day report deadline, is incorporated by EO11829 section4. Section12 establishes a separate '
    'Relocation Commission; its independent relocation work and presidential-determination sunset do not continue this '
    'Committee. The owner strike-and-insert ruling preserves section2(a) as amended, with both texts recorded, rather than '
    'ending it on April17,1975. The board-report-deadline ruling is not applied to erase this express conditional sunset. '
    'EO12379 section11, fully read on both official pages, directly revokes EO11829 as amended on August17,1982, with no '
    'express deferred commencement or target savings. It does not independently prove first cessation or completed notice/transfer. '
    'The misbound EO11022/11256 acquisition wrappers quote the same1982 source and create no earlier acting instrument. '
    'A new public discovery lead identifies December12,1975 report submission in GAO CED-81-139 p3 and Congressional Record '
    'June17,1977 p19634; this proposal retains it as unverified acquisition/application work, not an asserted first-end date.'
)

claims = []
inventory_proof = []
for iid in ['EO:11829', 'EO:11853']:
    c = copy.deepcopy(prior[iid])
    old_sha = assemble.canonical_sha(c)
    if iid == 'EO:11829':
        source = c['original_representation']
        original = (ROOT / source['text_path']).read_text()
        units = [
            ('sec1',1167,1616,'Establishment and membership of the Committee; actual statutory completion may end the Committee before1982. The HEW succession lead is relevant only if the Committee remained active in1980; no seat change is inferred here.'),
            ('sec2a',1616,2086,'Information function continues as amended by EO11853. Its section2(a) rewrite is a later event under the October21 ruling; before-and-after texts are recorded. The same statutory Mediator completion controls its potential earlier end.'),
            ('sec2b',2086,2404,'Chairman meetings and liaison facilitate timely information; section3(a) is a schedule reference and does not establish actual performance or the Committee termination date.'),
            ('sec3',2404,2568,'Interior support serves this Committee. The separate statutory Relocation Commission and its Interior support do not extend this EO command.'),
            ('sec4-termination',2568,2731,'Express event-based Committee dissolution upon completion of Mediator duties as defined by P.L.93-531 section1(a); notice is subsequently required and is not the dissolution condition.'),
            ('sec4-notice',2731,2802,'Independent command to advise the Chairman when the Mediator duties have ceased. Statutory submission and Committee dissolution do not establish actual notice; its first end remains separate and unresolved.'),
            ('sec4-records',2802,2916,'Independent transfer command limited to records the Committee maintained. Whether records existed, were transferred, and any resulting accrued custodial effect remain concrete unresolved inquiries; no speculative universe of records laws is imposed.'),
        ]
        # Exact boundaries use source phrases, avoiding any guessed split.
        units[5] = (units[5][0], original.index('The Mediator shall advise'), original.index('Any records which'), units[5][3])
        units[4] = (units[4][0],2568,units[5][1],units[4][3])
        units[6] = (units[6][0],units[5][2],2916,units[6][3])
        rev = copy.deepcopy(c['operative_clauses'][0]['later_events'][0])
        amendment = copy.deepcopy(c['operative_clauses'][1]['later_events'][0])
        amendment['mechanism'] = 'Section2(a) continues amended under the October21 owner ruling; full before-and-after text recorded; this event is not a first cessation.'
        amendment['before_text'] = original[1616:2086]
        amendment['after_text'] = (ROOT / amendment['source']['text_path']).read_text()[1300:1822]
        c['operative_clauses'] = []
        overrides = []
        for name,start,end,reason in units:
            scope = iid+'#'+name
            overrides.append({'scope_id':scope,'source_id':'ORIGINAL:'+iid,'char_start':start,'char_end':end,'reason':'Source-read complete inventory: distinct information, liaison, support, conditional dissolution, notice and records commands; exact original bytes.'})
            clause = {'scope_id':scope,'original_operative_text':original[start:end],'original_source':ref(source,start,end),
                      'state_at_cutoff':'terminated','first_end':None,'later_events':([copy.deepcopy(amendment)] if name=='sec2a' else [])+[copy.deepcopy(rev)],
                      'judgment_reason':reason+' Terminated here means prospective authority under the EO is removed by its complete formal revocation; it does not assert actual prior execution, first cessation, or the disappearance of accrued/independent effects.'}
            c['operative_clauses'].append(clause)
        dossier = json.loads((ROOT / 'jobs/claim-kit/output/dossiers/EO_11829.json').read_text())
        derived,evidence,errors = assemble.derive_inventory(dossier,overrides)
        assert not errors, errors
        assert [x['text'] for x in derived] == [x['original_operative_text'] for x in c['operative_clauses']]
        inventory_proof = {'instrument_id':iid,'dossier_fingerprint':dossier['fingerprint'],'errors':errors,'derived_scopes':[x['scope_id'] for x in derived],'inventory_overrides':overrides}
        c['unresolved_material_gaps'] = [
            'Retain and independently verify GAO CED-81-139 p3 and/or the Congressional Record June17,1977 p19634 actual report-submission account (candidate1975-12-12), then adjudicate its P.L.93-531 section1(a)/EO11829 section4 application. No first_end is yet asserted from public discovery output.',
            'Resolve separately section4 notice to the Chairman and transfer of any Committee records: occurrence/performance dates and specific accrued custodial effects remain unproved. The Committee dissolution date cannot settle these distinct commands or whole_order_end.',
            'Complete bounded intervening/savings/counterevidence review through2026-10-14; if actual Committee activity extended to1980, resolve the concrete HEW succession roster lead. No blanket1982 first-end or complete negative-search claim is made.',
        ]
    else:
        overrides = c['research_provenance']['inventory_overrides']
        c['operative_clauses'][0]['judgment_reason'] = (
            'Complete EO11853 is solely a replacement of EO11829 section2(a), with no independent notice, records or relocation command. '
            'It remains part of the parent as amended under the owner ruling and retains the parent section4 statutory completion condition. '
            'The parent separate notice/records work is context, not an additional command of EO11853. The new December12,1975 report-submission '
            'lead could resolve this narrower first-end question after exact source review; until then first_end stays null. '
            'The unqualified EO12379 parent-as-amended revocation supports terminated prospective authority but does not prove the first date.'
        )
        c['unresolved_material_gaps'] = [
            'Retain and independently verify the exact1975-12-12 Mediator report-submission evidence and adjudicate the parent section4/P.L.93-531 section1(a) trigger for the amended section2(a). No first_end or whole_order_end is yet asserted from the discovery lead.',
            'Complete bounded intervening-event and savings/counterevidence review for this dependent amendment through2026-10-14. Parent notice/records commands are not imported as independent commands of EO11853; EO12379 does not directly name EO11853.',
        ]
    c['original_representation'] = ref(c['original_representation'], 0, len((ROOT / c['original_representation']['text_path']).read_text()))
    c['research_rationale'] = common + '\nMember scope: ' + ('Seven exact original units restore distinct notice and records lifecycles from qualified Oct18 analysis; all first ends remain unresolved.' if iid=='EO:11829' else 'One complete amending instrument; statutory actual completion is a narrower remaining question than parent wind-down.')
    c['research_sources'] = list(copy.deepcopy(stat_refs).values())
    c['savings_residuals'] = {'state':None,'source':copy.deepcopy(c['operative_clauses'][-1]['original_source']),'reason':
        'EO12379 has no express target savings clause. P.L.93-531 separately preserves property/litigation arrangements and creates the Relocation Commission; those independent statutory functions are not evidence that this Committee continued. '+
        ('Section4 records-transfer and accrued custodial effects remain the concrete unresolved residual; notice performance remains distinct.' if iid=='EO:11829' else 'EO11853 itself adds only the dependent information clause and no separate records/notice/relocation duty. Complete bounded savings analysis remains unapproved.')}
    c['research_provenance'] = {
        'producer':'astra-production-b02','producer_model_family':'OpenAI','revision':'b02-v2',
        'publication_status':'partial_research_proposed_for_independent_review',
        'canonical_prior_claim_sha256':old_sha,'canonical_prior_file':prior_path.relative_to(ROOT).as_posix(),
        'input_commit':'b2944bab','inventory_overrides':overrides,'official_pages_inspected':True,
        'analysis_path':(BASE/'RESEARCH.md').relative_to(ROOT).as_posix(),
        'restored_prior_vs_new':'Statutory trigger analysis and seven-unit inventory restored/reconciled; exact date discovery1975-12-12 is new, remains unverified pending retained source review.',
        'cutoff':'2026-10-14','human_certification':0,
    }
    claims.append(c)

out = BASE/'PROPOSED_CLAIMS.v2.jsonl'
assert not out.exists(), 'Never overwrite a frozen proposal'
out.write_text(''.join(canon(c)+'\n' for c in claims),encoding='utf-8')
write('SOURCE_EVIDENCE.json',{'statutory_sources':stat_refs,'materialization':pin((BASE/'MATERIALIZATION.json').relative_to(ROOT)),'page_review_scope':{'EO11829':[11],'EO11853':[9],'EO12379':[9,10],'PL93-531':[1,2,3]},'statute_full_text_read':True,'new_discovery_qualified_only':True})
write('INVENTORY_PROOF.json',inventory_proof)
gate=assemble._gate(ROOT)
results=[]
for c in claims:
    errors=gate.validate_claim(c,expected_status=c['whole_order_status'])
    strict=assemble.check_claim(c,ROOT)
    results.append({'instrument_id':c['instrument_id'],'claim_sha256':assemble.canonical_sha(c),'publication_kind':'partial_research','expected_gate_errors':errors,'strict_errors':strict,'non_gate_errors':[e for e in strict if e not in errors]})
write('PRODUCER_GATES.json',results)
write('SELECTED_VERSIONS.json',{'selected_at_utc':datetime.now(timezone.utc).isoformat(),'agent':'astra-production-b02','producer_model_family':'OpenAI','claims':[dict(r,claim={**pin(out.relative_to(ROOT)),'line':i+1}) for i,r in enumerate(results)],'human_certification':0})
manifest={'schema':'eo-claim-kit-completion/v1','agent':'astra-production-b02','producer_model_family':'OpenAI','independence_requirement':'same_family_separate_context',
 'publication':{'mode':'replacement_proposal','path':(BASE/'reviewed-proposal/CLAIMS.proposed.jsonl').relative_to(ROOT).as_posix()},
 'members':[{'instrument_id':c['instrument_id'],'outcome':'submit','claim_sha256':assemble.canonical_sha(c),'claim':{**pin(out.relative_to(ROOT)),'line':i+1},'publication_kind':'partial_research'} for i,c in enumerate(claims)],
 'controls':[], 'receipts':[pin((BASE/n).relative_to(ROOT)) for n in ['RESEARCH.md','SOURCE_EVIDENCE.json','INVENTORY_PROOF.json','PRODUCER_GATES.json','SELECTED_VERSIONS.json','MATERIALIZATION.json','FETCH_REQUESTS.jsonl','RETENTION_REQUESTS.json']]}
write('COMPLETION.producer.json',manifest)
print(json.dumps(results,indent=2))
