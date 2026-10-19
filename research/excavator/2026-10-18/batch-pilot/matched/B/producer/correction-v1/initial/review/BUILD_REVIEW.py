"""Bounded independent arm-B review receipts; never writes producer/canonical data."""
from pathlib import Path
import csv
import datetime as dt
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
B = HERE.parent
ROOT = B.parents[5]
THREAD = '01a14f35-14b4-7fc2-a7ac-4ef571e4278d'
START = '2026-10-18T13:30:41.315Z'

def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()

def pin(path):
    p = ROOT / path
    return {'path': path, 'sha256': sha_bytes(p.read_bytes()), 'bytes': p.stat().st_size}

def dump(name, obj):
    (HERE / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)+'\n', encoding='utf-8')

def readable(text):
    """Space compressed legal citations in narrative fields; never alter pins/IDs."""
    protected=[]
    def protect(m):
        protected.append(m.group(0)); return f'ZZPROTECTEDTOKEN{len(protected)-1}ZZ'
    text=re.sub(r'https?://\S+|[0-9a-f]{64}',protect,text)
    text=re.sub(r'(?<=[,;])(?=\S)',' ',text)
    text=re.sub(r'(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])',' ',text)
    text=re.sub(r'(\b(?:EO|UNSCR|USC|CFR|FR)) (?=\d)',r'\1 ',text)
    text=re.sub(r'(?<=[a-z])(?=[A-Z])',' ',text)
    text=re.sub(r'(?<=[a-z])\.(?=\d)', '. ', text)
    text=re.sub(r'(?<=\))(?=[A-Za-z])', ' ', text)
    for n,old in enumerate(protected):
        text=text.replace(f'ZZPROTECTEDTOKEN {n} ZZ',old)
    return text

p = json.loads((B/'PACKET.json').read_text(encoding='utf-8'))
refs = {'shared_references': 0, 'source_references': 0, 'text_spans': 0}
ref_errors = []

def decode(v):
    if isinstance(v, list):
        return [decode(x) for x in v]
    if isinstance(v, dict):
        if '@eo:ref' in v:
            refs['shared_references'] += 1
            return decode(p['shared_objects'][v['@eo:ref']])
        if '@eo:source' in v:
            refs['source_references'] += 1
            return p['sources'][v['@eo:source']]
        if '@eo:span' in v:
            refs['text_spans'] += 1
            tid, a, z = v['@eo:span']
            text = p['text_blocks'][tid]['text']
            if not 0 <= a <= z <= len(text):
                ref_errors.append({'text_block':tid,'start':a,'end':z,'block_length':len(text)})
            # Encoded spans are relative to the text block, not the held-file base.
            return text[a:z]
        return {k:decode(x) for k,x in v.items()}
    return v

ds = {k:decode(v) for k,v in p['dossiers'].items()}
decisions = list(csv.DictReader((B/'decisions.csv').open(encoding='utf-8',newline='')))
clauses = list(csv.DictReader((B/'clauses.csv').open(encoding='utf-8',newline='')))
audit = {x['instrument_id']:x for x in json.loads((B/'applied/AUDIT.json').read_text(encoding='utf-8'))}
claims = {}
for line_no, line in enumerate((B/'applied/CLAIMS.proposed.jsonl').read_text(encoding='utf-8').splitlines(),1):
    c = json.loads(line)
    claims[c['instrument_id']] = {'claim':c,'line':line_no,'line_sha256':sha_bytes(line.encode('utf-8'))}

file_checks = []
for path, expected in p['held_text_file_pins'].items():
    got = pin(path)
    got['expected_sha256'] = expected
    got['match'] = got['sha256'] == expected
    file_checks.append(got)

block_checks = []
for tid, block in p['text_blocks'].items():
    path = block['paths'][0]
    text = (ROOT/path).read_text(encoding='utf-8')
    a, z = block['char_start'], block['char_end']
    block_checks.append({'block_id':tid,'path':path,'start':a,'end':z,
                         'match_held_slice':text[a:z] == block['text'],
                         'chars':len(block['text'])})

inventory_checks = []
for x in clauses:
    did=x['instrument_id']; ev=ds[did]['evidence'][x['inventory_source_id']]
    a,z=int(x['inventory_char_start']),int(x['inventory_char_end'])
    text=ev['text']; valid=0 <= a < z <= len(text)
    inventory_checks.append({'instrument_id':did,'scope_id':x['scope_id'],
        'source_id':x['inventory_source_id'],'source':ev['source'],
        'start':a,'end':z,'valid_original_span':valid,
        'selected_text_sha256':sha_bytes(text[a:z].encode('utf-8'))})

claim_quote_checks=[]
for did, x in claims.items():
    for c in x['claim']['operative_clauses']:
        s=c['original_source'];text=(ROOT/s['text_path']).read_text(encoding='utf-8')
        claim_quote_checks.append({'instrument_id':did,'scope_id':c['scope_id'],
            'exact':text[s['char_start']:s['char_end']] == c['original_operative_text']})

source_reading=[]
for n in [12696,12720,12722,12734,12813,12817,12756,12783,12869,12771,12743,12724,13303,13350,12815]:
    path=f'jobs/fr-originals/data/full_run/texts/EO_{n}.txt'
    info=pin(path)
    info['instrument_id']=f'EO:{n}'
    info['exposure']='complete target-specific operative text read directly from held file'
    if n==12815:
        info['exposure']='complete EO12815 on PDF page11 read; retained neighbouring tax material on pages13-15 was identified as unrelated and was not substantively reviewed'
    if n==13350:
        info['exposure']='complete operative text on PDF pages1-3 read; annex OCR/graphic placeholders retained, annex images4-13 not substantively reviewed for unrelated person lists'
    if n==12696:
        info['exposure']='alternate two-page OCR read in full; it is not the selected truncated ORIGINAL evidence and has not received official page-image verification'
    source_reading.append(info)
source_reading.append({**pin('jobs/fr-originals/data/full_run/texts/EO_12696.recheck.txt'),
    'instrument_id':'EO:12696','exposure':'selected original read in full; stops after3(c) and page12 filing marker'})

external_sources=[
 {'source_id':'EXT:UN:1483:2003','url':'https://press.un.org/en/2003/sc7765.doc.htm',
  'location':'official UN reproduction of Resolution1483(2003), paragraphs10,16(c)(iii),17,18,19,23',
  'access':'target operative provisions returned by web search; direct open/find failed; official PDF retrieval also failed',
  'original_file_sha256':None,
  'finding':'The2003 change expressly reaches resolution778 prohibitions, while restoration of funds originally provided under778 is specifically contemplated. It is contrary-evidence/repayment analysis to resolve, not proof of an automatic whole-order first end.'},
 {'source_id':'EXT:OFAC:03-16216','url':'https://www.govinfo.gov/content/pkg/FR-2003-06-27/pdf/03-16216.pdf',
  'location':'68FR38188-38190;31CFR575.533(a),(b)(1),(c);PDFpages1-3',
  'access':'complete relevant rule text read via official PDF web extraction',
  'original_file_sha256':None,
  'finding':'License has explicit2003-05-23 effectiveness and preserves existing blocked property and requirements; it does not establish that EO12817 transfer/repayment commands ceased.'},
 {'source_id':'EXT:USC:2808:1994','url':'https://uscode.house.gov/view.xhtml?edition=1994&req=granuleid%3AUSC-1994-title10-chapter169-subchapter1&saved=%7CZ3JhbnVsZWlkOlVTQy0xOTk0LXRpdGxlMTAtc2VjdGlvbjI4MDE%3D%7C%7C%7C0%7Cfalse%7C1994',
  'location':'10USC2808(a)-(c),1994edition,including historical source credit',
  'access':'complete relevant section returned by official OLRC search result',
  'original_file_sha256':None,
  'finding':'Construction authority is conditioned on the relevant emergency and terminates at its end. This supports the construction limb; it does not execute congressional transmission/publication.'},
 {'source_id':'EXT:UN:S2003640','url':'https://digitallibrary.un.org/nanna/record/496868/files/S_2003_640-EN.pdf?registerDownload=1&version=1&withMetadata=0&withWatermark=0',
  'location':'S/2003/640,paragraph14',
  'access':'paragraph returned by official UN search result; complete report not reviewed',
  'original_file_sha256':None,
  'finding':'Restoration of778funds was described as under way; no completion date is proved.'}
]

initial_notes={
 'EO:12720': {'outcome':'accepted_ai_proposal','basis':'Fixed Council sunset on1993-01-16 from EO12783, followed by EO12869 formal revocation on1993-09-30; nine corrected clauses cover the original. Accrued travel rights are separated. No independent publication/transmittal command occurs in this original.'},
 'EO:12734': {'outcome':'accepted_ai_proposal','basis':'Initial provisional review accepted the continuing construction invocation ending with EO13350 on2004-07-30, while treating immediate effect/transmittal/publication as ancillary. This acceptance is preserved but superseded by the stricter separate-command review.'},
 'EO:12817': {'outcome':'rejected_requires_correction','basis':'All clauses receive2004-07-30 first-end without resolving the2003 change involving UNSCR1483/OFAC575.533 and the separate repayment limb. No replacement date is established.'},
 'EO:12813': {'outcome':'blocked_decision_upheld','basis':'Not-later-than is a limit, not proof of the actual first cessation. EO12815 changes only the date, has no express effective provision, and was issued on the old limit. No actual closeout record is held.'},
 'EO:12696': {'outcome':'blocked_decision_upheld','basis':'Selected original is truncated after3(c); alternate OCR retains3(d),4(a),4(b). The fixed-term lead survives in the packet but cannot repair selected original/inventory coverage. Page verification/new pinned dossier is necessary.'},
 'EO:12722': {'outcome':'blocked_decision_upheld','basis':'EO12724 inconsistency revocation/savings, EO13303 selected-property exception, EO13350 continuing blocking, and current-law pointer gaps prevent a complete clause lifecycle. No single2004date is substituted for all earlier transitions.'}
}

facts={
 'EO:12720':{
  'inventory':'Sections1(a)-(b),2(a)-(b),3(a)-(e),including separate FACA delegation in3(d),are covered by9 exact disjoint original spans. The page-header gap is not operative text.',
  'earlier_end':'Original two-year Council sunset was replaced by the fixed1993-01-16 command in EO12783. EO12869 recognizes that amendment and later revokes the entire order effective1993-09-30. The report/appropriation condition leads do not prove an earlier termination.',
  'partial_scope':'EO12783 changes3(e),not the whole order text; Council-dependent appointments/advice/information/support/FACA duties end with that institution. Later formal revocation remains separately recorded.',
  'effective_dates':'1993-01-16 is the explicit fixed termination date,not EO12783 signing as a proxy. EO12869section6 expressly supplies1993-09-30.',
  'independent_commands':'No separate transmission/publication command in this original.3(b)travel entitlements for completed Council service may accrue; other duties expressly depend on the Council and supply no separate program after sunset.',
  'savings':'Possible accrued travel rights retained as residuals without assuming any unpaid claim. EO12783/EO12869 do not preserve a prospective Council program.',
  'contrary_and_cutoff':'Held common sources checked; no contrary operative lead found for this Council. OFR catalog/saved-text search and49-title eCFR search are bounded. USC119-121ends2026-10-09 and is not complete2026-10-14coverage.'},
 'EO:12734':{
  'inventory':'The whole source span707:1753 includes construction invocation and a separate final paragraph directing immediate effect,transmission to Congress,and Federal Register publication. A single blanket first_end does not distinguish these commands.',
  'earlier_end':'The continuing construction limb depends on the EO12722 emergency; EO12771 expressly leaves that emergency unaffected. EO12722/12724 predate this order and cannot be its later cessation. No earlier end of the construction limb is established by the held chain.',
  'partial_scope':'EO13303selected property and EO12817transfer commands do not terminate construction. EO13350expressly names EO12734in revocation; no new-emergency transfer of this construction delegation is stated.',
  'effective_dates':'EO13350section10explicitly gives2004-07-30at00:01EDT. That date supports express revocation and construction authority cessation,not execution of the1990publication/transmission directions.',
  'independent_commands':'Reject blanket2004first_end for immediate-effect/publication/transmission text. The original announces immediate effectiveness; its Federal Register issue establishes publication on1990-11-19. Actual transmission-to-Congress fact/date is absent. Split or otherwise explicitly model the implementation commands and their earlier execution/unknown status.',
  'savings':'EO13350section1retains accrued rights/duties,pending actions/pre-effective-date proceedings and penalties. Its property-blocking continuation names12722/12724,not prospective construction under12734.',
  'contrary_and_cutoff':'Historical10USC2808(c)confirms emergency-end condition; no independent post-emergency construction authority identified. This does not close the separate implementation-command gap. Bounded searches are not universal legal completeness.'},
 'EO:12817':{
  'inventory':'Eight exact source sections cover Treasury authority/direction,conditional financial-institution transfers,FRBNY receiving/holding/investment/transfers,acquittance/nonliability/pre-transfer rights,definition,implementation/redelegation,noncreation of rights,and immediate-effect/transmission/publication. Section8needs subcommand treatment.',
  'earlier_end':'No actual transfer,repayment,exhaustion or administrative completion date is proved. UNSCR1483(2003)and OFAC575.533are a material unclosed earlier-change inquiry for sections1-3; para17of1483also contemplates restoration of778funds,so no automatic2003whole-order end follows.',
  'partial_scope':'Separate incoming blocked petroleum proceeds,outgoing transfers to UN,UN repayments,and FRBNYholding/investment must be mapped to the2003changes and any Treasury directives. Already-blocked property is expressly retained under575.533(b)(1). No new2003first-end date is asserted.',
  'effective_dates':'EO13350section10expressly establishes2004-07-30at00:01EDT revocation. OFAC575.533(c)expressly gives2003-05-23for its license. Neither signing date nor UN-program deadline is treated as proof of actual implementation or completion.',
  'independent_commands':'Section8receives2004-07-30first_end but separately commands immediate effect,transmission,and publication. The original Federal Register issue establishes1992-10-23publication; actual congressional transmission is not proved. Correct section8representation rather than imposing the revocation date on all subcommands.',
  'savings':'Section4acquittance,good-faith nonliability,and pre-transfer rights/debts/claims have accrued consequences. EO13350section1also preserves accrued effects; ongoing blocking continuation names12722/12724. This does not by itself establish continuing prospective12817transfer authority or an earlier completion.',
  'contrary_and_cutoff':'Additional primary2003sources were read; they require target-specific resolution,not inference from family membership. Complete supplemental source-byte hashes are absent,so new legal propositions are not incorporated into a producer claim by this review.'},
 'EO:12813':{
  'inventory':'Corrected8spans retain1,2,3(a)-(d),4(a)-(b); the packet machine whole-title segmentation is insufficient but was corrected in the explicit blocked sheet.',
  'earlier_end':'Original4(b)not-later-than1992-09-30and EO12815replacement1992-12-31are outside limits. EO12869section4(b)later revokes already-terminated/completed committees; it supplies no unique actual first cessation date.',
  'partial_scope':'EO12815changes4(b)only. Reporting progress to Deputy Secretary is a function and not an automatic report-completion sunset. No actual closeout source is held.',
  'effective_dates':'No express timing clause in EO12815; it was issued on old deadline. Signing alone is not used as effectiveness. EO12869section6explicitly gives1993-09-30formal revocation.',
  'independent_commands':'Advising,reporting,funding,services,temporary procurement and FACA delegation separately considered. No independent publication/transmission command in this original. Actual report/termination events remain unproved.',
  'savings':'Travel/reimbursable services/procurement can accrue; no prospective Commission program saved by EO12869. This does not solve first cessation.',
  'contrary_and_cutoff':'Packet has no closeout record. Bounded later/current-law searches do not manufacture one. Existing2producer gaps remain actionable.'},
 'EO:12696':{
  'inventory':'Selected original/recheck3511characters stops after3(c)and filing marker. Alternate OCR has3(d)information duty,4(a)FACA delegation,4(b)sunset; the selected11clause inventory cannot reach them.',
  'earlier_end':'Alternate original24-month sunset and EO12756continuance until1993-11-13must be considered before EO12869revocation1993-09-30. Reporting whenever requested has no fixed deadline. No earlier actual closeout is established.',
  'partial_scope':'EO12756section2changes membership30to35;section1continues Council. It does not erase information/FACA/sunset provisions omitted from selected original.',
  'effective_dates':'EO12869section6explicitly supplies1993-09-30;no own-term1991sunset may be used without the extension. Correct original-source/page evidence must precede final dates for every clause.',
  'independent_commands':'Advisory/public-information/reporting/compensation/travel/staffing duties read in selected and alternate texts.4(a)retains President congressional-reporting exception;no actual report cessation inferred.3(d),4(a),4(b)must be added to inventory after source repair.',
  'savings':'Travel under3(b)can have accrued effects;no prospective saving in EO12869for this Council. Residual closure awaits complete source.',
  'contrary_and_cutoff':'The packet retains the alternate4(b)term excerpt despite no codec warnings;this is evidence of the gap,not complete original coverage. Official1989PDFretrieval failed due size;block remains.'},
 'EO:12722':{
  'inventory':'Explicit13spans include emergency declaration,blocking,transaction-intro,prohibitions2(a)-(h),definition,3immediate effect,and4Treasury/redelegation/all-agency/transmission/publication. Every scope remains undecided in blocked sheet.',
  'earlier_end':'EO12724section6partial inconsistency revocation/savings precedes2004;EO12771does not terminate Iraq emergency;EO13303section2selects property;EO12817transfers do not prove all property transferred or authority exhausted.',
  'partial_scope':'Map each prohibition/delegation to EO12724inconsistency and EO13303selected-property reach. Add OFAC575.5332003license and its retained blocking to gap work. EO12743is reserve/personnel invocation,furtherance rather than a located transition of12722.',
  'effective_dates':'EO12724says immediate;EO13303has no express effective-date clause;no signing shortcut used. EO13350section10gives2004-07-30at00:01EDT. OFAC575.533gives its own2003-05-23date.',
  'independent_commands':'Emergency,delegations,all-agency measures,prohibitions,immediate effect,transmission/publication each require appropriate histories. No blanket revoked2004first_end is approved;actual transmission fact is absent.',
  'savings':'EO12724section6continues administrative acts;EO13303section2(b)saves specified actions;EO13350section1continues remaining blocked-property prohibitions and accrued consequences. Full31CFR576.201and50USC1701IraqSanctionsnote slices/currency remain unclosed.',
  'contrary_and_cutoff':'NO_ORDER_CITED_IN_CURRENT_LAW conflict is unresolved. Current-law references are pointers/snippets,not held exact complete attributable law. USC119-121does not reach2026-10-14;existing4gaps retained plus separate-command and2003license inquiry.'}
}

amended_outcomes={k:v['outcome'] for k,v in initial_notes.items()}
amended_outcomes['EO:12734']='rejected_requires_correction'
gaps={
 'EO:12720':[],
 'EO:12734':[
  {'id':'B-REVIEW-12734-INDEPENDENT-IMPLEMENTATION','scope_ids':['EO:12734#whole'],
   'correction':'Separate/model immediate-effect,congressional-transmittal,and Federal Register publication commands from construction authority. Preserve2004revocation for construction where supported;record earlier proven publication and acquire/pin actual congressional transmission or retain a precise gap. Do not assign all commands2004first cessation.'}],
 'EO:12817':[
  {'id':'B-REVIEW-12817-2003-SCOPE','scope_ids':['EO:12817#sec1','EO:12817#sec2','EO:12817#sec3','EO:12817#sec6'],
   'correction':'Acquire/pin UNSCR1483paras10,16(c)(iii),17,23and OFAC575.533/68FR38188-38190;map incoming petroleum proceeds,UNtransfers,UNrepayments,FRBNYholding/investment,and relevant Treasury directives to the2003changes. Distinguish continuing authority,partial cessation,and accrued/transfer effects. Do not substitute a2003whole-order date without legal/factual support.'},
  {'id':'B-REVIEW-12817-SECTION8-IMPLEMENTATION','scope_ids':['EO:12817#sec8'],
   'correction':'Split/model section8(a)immediate effect and8(b)transmission/publication. Pin1992-10-23publication from original issue;obtain actual congressional transmission evidence or retain gap. No blanket2004-07-30first cessation for these implementation commands.'}],
 'EO:12813':[{'id':'B-REVIEW-AID-FIRST-STOP','correction':'Retain and complete B-TASK-AID-FIRST-STOP and B-TASK-AID-EXTENSION-EFFECT;do not convert not-later-than into actual date.'}],
 'EO:12696':[{'id':'B-REVIEW-12696-COMPLETE-ORIGINAL','correction':'Retain B-TASK-12696-COMPLETE-ORIGINAL;verify official54FR47507-47508pages11-12,rebuild selected original,add3(d),4(a),4(b),repin dossier,and re-evaluate member-specific history.'}],
 'EO:12722':[{'id':'B-REVIEW-12722-RETAIN-BLOCK','correction':'Retain all4producer gaps. Include2003OFAC575.533and separate implementation commands in later clause histories;resolve exact current-law text,currency,and actual transfer facts without blanket2004closure.'}]
}

base={
 'schema':'eo-independent-ai-review/v1','arm':'B','reviewer_thread_id':THREAD,
 'actual_model':'gpt-6.1-sol','actual_reasoning_effort':'xhigh','task_start_utc':START,
 'legal_cutoff':'2026-10-14','packet_fingerprint':p['fingerprint'],
 'packet_file_pin':pin(str((B/'PACKET.json').relative_to(ROOT)).replace('\\','/')),
 'scope':'Six armBmembers only; no armA/prior Solreview/producer-outcome/coordinator-answer inspection. Packet embedded ownership/preflight metadata was visible but not used as legal authority.',
 'human_certifications':0,'canonical_claims_changed':0,'statuses_changed':0,'census_changed':0,
 'producer_files_changed':0,'queue_changed':0,'handoff_changed':0,
 'limits':['AIreview only; no independent human approval.',
           'Bbounded-search reports are accepted only within their stated coverage,not a universal absence proof.',
           'Runtime counters are not billed dollars or complete active-labor measurements.',
           'External web sources lack newly acquired source-byte hashes; they identify actionable contrary-evidence gaps and do not silently amend producer claims.']}

def record(did,outcome):
    d=next(x for x in decisions if x['instrument_id']==did)
    out={'instrument_id':did,'producer_outcome':d['outcome'],'review_outcome':outcome,
        'decision_csv_row_1based':decisions.index(d)+2,
        'decision_csv_file_pin':pin(str((B/'decisions.csv').relative_to(ROOT)).replace('\\','/')),
        'decision_row_sha256':sha_bytes(json.dumps(d,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')),
        'dossier_fingerprint':d['dossier_sha256'],'producer_remaining_gaps':json.loads(d['unresolved_material_gaps']),
        'inventory_scopes':[x['scope_id'] for x in clauses if x['instrument_id']==did]}
    if did in claims:
        x=claims[did]
        out['claim_pin']={'path':str((B/'applied/CLAIMS.proposed.jsonl').relative_to(ROOT)).replace('\\','/'),
                          'line':x['line'],'line_sha256':x['line_sha256'],
                          'audit_claim_sha256':audit[did]['claim_sha256']}
        out['decision_json_pin']=pin(str((B/f"applied/decisions/{did.replace(':','_')}.json").relative_to(ROOT)).replace('\\','/'))
    else:
        out['decision_json_pin']=None
    return out

initial={**base,'stage':'initial_provisional','note':'First communicated provisional assessment. Preserved unchanged; later amended review applies exact independent implementation-command cessation to12734and12817.',
 'counts':{'members':6,'accepted_ai_proposals':2,'rejected_proposals':1,'blocked_decisions_upheld':3,'human_ready':0},
 'records':[{**record(k,v['outcome']),'initial_basis':v['basis']} for k,v in initial_notes.items()]}
if not (HERE/'REVIEW_INITIAL.json').exists():
    dump('REVIEW_INITIAL.json',initial)
amended={**base,'stage':'amended_final','prior_review':'REVIEW_INITIAL.json',
 'amendment_reason':'Coordinator explicitly required exact first_end assessment for independent notice/transmittal/publication commands. Initial ancillary-command treatment was insufficient; no producer amendment is fabricated.',
 'counts':{'members':6,'accepted_ai_proposals':1,'rejected_proposals':2,'blocked_decisions_upheld':3,'human_ready':0,
           'initial_rejections_preserved':1,'additional_rejections_on_amendment':1,'producer_corrections_reviewed':0},
 'records':[{**record(k,amended_outcomes[k]),'checks':facts[k],'actionable_gaps':gaps[k]} for k in initial_notes]}
for member in amended['records']:
    member['checks']={k:readable(v) for k,v in member['checks'].items()}
    for gap in member['actionable_gaps']:
        gap['correction']=readable(gap['correction'])
amended['amendment_reason']=readable(amended['amendment_reason'])
dump('REVIEW_AMENDED.json',amended)
dump('SOURCE_PINS.json',{'schema':'eo-review-source-pins/v1','arm':'B',
 'packet_source_catalogue':p['sources'],'held_file_pin_checks':file_checks,
 'direct_source_reads':source_reading,'supplemental_web_sources':external_sources,
 'official_pdf_verified':{**pin('research/stage21/original_sources/EO_13350.pdf'),
   'visually_inspected_pdf_pages_1based':[1,3],
   'relevant_text_pages_read_1based':[1,2,3]},
 'inventory_source_spans':inventory_checks,'claim_quotation_checks':claim_quote_checks})
dump('PACKET_AUDIT.json',{'schema':'eo-review-packet-audit/v1','arm':'B',
 'packet_file_bytes':(B/'PACKET.json').stat().st_size,'read_file_bytes':(B/'READ.md').stat().st_size,
 'packet_members':list(p['dossiers']),'text_blocks':len(p['text_blocks']),
 'unique_retained_text_block_chars':sum(len(x['text']) for x in p['text_blocks'].values()),
 'sources':len(p['sources']),'shared_objects':len(p['shared_objects']),
 'reference_resolution_counts':refs,'reference_errors':ref_errors,
 'text_block_held_slice_checks':block_checks,'held_file_pin_count':len(file_checks),
 'held_file_pin_mismatches':sum(not x['match'] for x in file_checks),
 'invalid_inventory_spans':sum(not x['valid_original_span'] for x in inventory_checks),
 'claim_quote_mismatches':sum(not x['exact'] for x in claim_quote_checks),
 'explicit_overflow_codec_warnings':p['codec_issues'],
 'retained_evidence_findings':[
  'READexplicit overflow/codec warnings are empty. Every encoded reference/span resolves and every retained block matches its held source slice.',
  'This is representational completeness,not legal-source completeness:EO12696selected original is truncated;the alternate sunset excerpt is retained but does not restore3(d)/4(a).',
  'EO12813machine whole-title clause is incomplete as an inventory;producer explicit8spans correct it while retaining blocked outcome.',
  'EO12720machine3(c)/(d)merge and EO12817empty8heading/1-2merge are corrected in explicit spans,not erased from packet.',
  'EO12815retains neighbouring tax material;it is not missing contrary EOevidence.',
  'EO13350annex graphic placeholders are retained;target revocation/savings/timing are in operativepages1-3.',
  'Current-law pointers/currency gaps and unlocated12743target provision remain visible,not promoted to legal determinations.'],
 'exposure_limits':'Files were read programmatically for pins;model exposure consisted of bounded displays of all six originals,all relevant actor operative texts,all unique rationales,decision/clauses/audits,and packet metadata. Serialized file bytes are not model token counts.'})

failures=[
 {'stage':'exporter availability','failure':'Assigned exporter initially absent;root restored sparse checkout before capture.','resolution':'Exact requested exporter used after restoration.'},
 {'stage':'initial metadata display','failure':'PowerShell depth serialization emitted89618tokens and tool truncation.','resolution':'Replaced with bounded Python key/source/rationale reads;truncation not treated as absence.'},
 {'stage':'packet read','failure':'Python defaultcp1252failed decodingUTF8packet.','resolution':'ExplicitUTF8read set.'},
 {'stage':'EO12815display','failure':'Stdoutcp1252failed onU+2666in retained neighbouring material.','resolution':'UTF8stdout and complete target page11read;irrelevant retained overflow identified.'},
 {'stage':'claim schema','failure':'Reviewer queried nonexistentclauseskey and receivedKeyError.','resolution':'Correctoperative_clauseskeyused;all18submittedclausequoteschecked.'},
 {'stage':'temporary reviewer decoder','failure':'Reviewer initially subtracted held-filebasefrom block-relative spans,emptying alternate12696term text.','resolution':'Corrected to block-relative[a:z];allencodedspansvalidated;no packet defect inferred.'},
 {'stage':'remote source access','failure':'Official1989PDFtoo large;official1990constructionPDFunavailable;multipleUN/OLRCdirectopens,PDFs,andfindsfailed.','resolution':'Held originals remain authoritative inputs;local13350PDFpages1/3visuallychecked;successfulofficialsearchreproductions/ruleusedwithaccesslimitations.','details':[
  'govinfoFR1990-11-19PDFinaccessible;FR1989-11-15PDF44.8MBtoo large',
  'digitallibraryUN495555and150970directrecordopensinternalerror',
  'docs.un.org1483anddigitallibrary1483PDF403;1483PDF?ln=eninternalerror',
  'govinfo03-16383candidatePDFunavailable;correct03-16216subsequentlyread',
  'govinfoUSCODE1994sec2808PDFunavailable;OLRChistoricalsectionsearchresultread',
  'remote13350page1screenshotcachemiss;localPDFreplacedvisualcheck',
  'directOLRC1994sectionandUNSC7765opensinternalerror',
  '575.215findnomatch;UN778PDF,unmovic1483PDF,andUNrepertoirePDFinternalerror',
  'UNdocumentaccessAPIredirectedtounusableerrorpage;UNmandateopenmiss;threeUNpressfindsnomatch',
  'finalbroadUNsearchoutputtruncated;target2003provisionshadalreadybeenreturnedintheprecedingboundedsearch']},
 {'stage':'initial legal review','failure':'Initial12734acceptancetreatedtransmittal/publicationasancillarywithoutseparatefirst_end.','resolution':'Initialrecordpreserved;amendedreviewrejectsblanketfirst-endassignment.'}
]
dump('FAILURES.json',{'schema':'eo-review-failure-log/v1','failure_categories':len(failures),
 'failures':failures,'all_six_cases_retained_in_outcomes':True,
 'initial_legal_rejections_retained':['EO:12817'],
 'additional_amended_rejections':['EO:12734'],
 'producer_failure_log_pin':pin(str((B/'producer/FAILURES.json').relative_to(ROOT)).replace('\\','/')),
 'producer_failure_log':json.loads((B/'producer/FAILURES.json').read_text(encoding='utf-8'))})

md='''# Independent AI review — matched arm B

Final amended outcome: **1 accepted proposal, 2 rejected proposals, 3 upheld blocked decisions, 6 total. No human certification.**

| Order | Producer | Amended review |
|---|---|---|
| EO12720 | submit | Accepted AI proposal |
| EO12734 | submit | Rejected: separate immediate-effect/transmission/publication history |
| EO12817 | submit | Rejected: 2003 scope/repayment inquiry and section8 implementation history |
| EO12813 | blocked | Block upheld: actual first cessation and extension effectiveness |
| EO12696 | blocked | Block upheld: truncated selected original/inventory |
| EO12722 | blocked | Block upheld: partial changes, savings/current-law/cutoff and actual events |

The initial provisional review accepted EO12734. REVIEW_INITIAL.json preserves that assessment and the initial EO12817 rejection. REVIEW_AMENDED.json applies the stricter command-specific first-cessation check requested by the coordinator and adds the EO12734 rejection. No producer correction has been silently applied or reviewed. All failures and all six cases remain in the totals.

EO12720 has an express fixed Council termination on January16,1993 under EO12783. EO12869 separately revokes the order effective September30,1993. The nine source spans retain the original commands and possible accrued travel rights. Neither an appropriation qualifier nor a report deadline supplies an earlier end.

EO13350's revocation and savings are confirmed in the held official PDF (source SHA98cbb450439692d42e626eebd8af565e19ad5227945b2ea74c242274335277a9), with pages1 and3 visually inspected. Section10 explicitly gives July30,2004 at12:01a.m.EDT. That supports revocation of EO12734/12817, but does not prove that their older implementation commands first ceased then. EO12734's publication appears in the November19,1990 issue; EO12817's publication appears in the October23,1992 issue. Actual congressional-transmission evidence is absent. Those commands must be separately modeled or precisely left unresolved.

EO12817 also needs a source-based reconciliation of its transfer/holding/repayment limbs with UNSCR1483(2003) paragraphs10,16(c)(iii),17,23 and OFAC31CFR575.533. The UN text both changes earlier sanctions and contemplates restoration of778funds. The OFAC rule is explicitly effective May23,2003 and retains already-blocked property and existing requirements. These sources do not establish an automatic2003whole-order end, completed transfer, or exhaustion. [UN primary reproduction](https://press.un.org/en/2003/sc7765.doc.htm), [OFAC rule,68FR38188–38190](https://www.govinfo.gov/content/pkg/FR-2003-06-27/pdf/03-16216.pdf).

The packet's33held-file pins,23retained text blocks and18submitted original-clause quotations were checked. The absence of codec/overflow warnings does not cure EO12696's truncated selected original. Missing/current-law pointer records and retained overflow remain visible. Full USC119-121currency reaches October9,2026,not the October14cutoff; bounded searches do not prove universal absence.

Exact claim lines and hashes, decision pins, per-member tests and actionable gaps are in REVIEW_AMENDED.json. SOURCE_PINS.json and PACKET_AUDIT.json retain evidence checks. FAILURES.json preserves operational failures, the initial verdict limitation, and current Bproducer failures. TELEMETRY.json is the requested numeric export from this reviewer's exact own rollout; MEASUREMENT.json records task wall time and model identity. Dollar cost and complete active labor are unavailable.
'''
(HERE/'REPORT.md').write_text(readable(md),encoding='utf-8')
print(json.dumps({'written_under':str(HERE),'amended_counts':amended['counts'],
 'ref_errors':len(ref_errors),'held_pin_mismatches':sum(not x['match'] for x in file_checks),
 'block_slice_mismatches':sum(not x['match_held_slice'] for x in block_checks),
 'quote_mismatches':sum(not x['exact'] for x in claim_quote_checks)},sort_keys=True))
