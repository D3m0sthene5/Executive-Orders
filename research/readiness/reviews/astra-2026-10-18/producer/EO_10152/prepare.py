"""Materialize the coordinator's source-read partial claim; no network or job output writes."""
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[6]
HERE = Path(__file__).parent
sys.path.insert(0, str(ROOT / 'research/stage19/code'))
from claim_gate import claim_sha

def dump(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8', newline='\n')

texts = {}
fixity = json.loads((ROOT / 'jobs/official-fixity/output/MATCHED_BY_SHA256.json').read_text(encoding='utf-8'))
refs = {}
for n in [10152,10618,10681,10739,10892,11120,11157]:
    p = ROOT / f'jobs/fr-originals/data/full_run/texts/EO_{n}.txt'
    s = p.read_text(encoding='utf-8')
    texts[n] = s
    sha = re.search(r'downloaded file: ([a-f0-9]{64})', s)[1]
    assert fixity[sha]['result'] == 'match'
    refs[n] = {'url':re.search(r'Source: (\S+)',s)[1], 'sha256':sha,
        'text_path':p.relative_to(ROOT).as_posix(), 'text_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
        'page_or_item':re.search(r'Location: ([^\n]+)',s)[1],
        'official_fixity_record':'jobs/official-fixity/output/MATCHED_BY_SHA256.json',
        'official_fixity_result':'match',
        'read_method':'Held official PDF text extract; no original-page image inspection asserted for this candidate.'}

def source(n, quote=None, location=None):
    d = copy.deepcopy(refs[n])
    if quote is not None:
        assert quote in texts[n]
        d['quoted_parts'] = [quote]
    if location: d['page_or_item'] = location
    return d

def between(n, a, b):
    s = texts[n]; start=s.index(a);return s[start:s.index(b,start)].rstrip()

draft = next(json.loads(l)['claim'] for l in (ROOT/'jobs/claim-drafts/output/DRAFT_CLAIMS.jsonl').open(encoding='utf-8') if json.loads(l)['instrument_id']=='EO:10152')
claim = copy.deepcopy(draft)
s = texts[10152]
activation = between(10152, 'Sec. 13. This order', 'H arry  S. T ruman')
claim['original_representation'] = source(10152, activation)
claim['original_representation']['acceptable_as_original'] = True
claim['operative_clauses'] = []

def clause(label, a, b, context=None, continuation=None):
    q=between(10152,a,b)
    c={'scope_id':f'EO:10152#{label}', 'original_operative_text':q,
       'original_source':source(10152), 'state_at_cutoff':None, 'first_end':None,
       'current_predicate':None, 'later_events':[],
       'activation':{'general_date':'1950-09-01','exception_date':'1949-10-01',
          'reason':'Section13 applies the earlier date only to so much of the order as necessary to authorize incentive pay under sections9 and10; it is not a sunset.',
          'source':source(10152,activation)},
       'first_end_gap':'Earlier statutory displacement, amendment continuity and saved accrued-pay effects remain unresolved; no formal-revocation date substituted for earliest actual cessation.'}
    if context: c['interpretive_context']={'source':source(10152,context)}
    if continuation: c['original_text_continuations']=[{'source':source(10152,continuation)}]
    claim['operative_clauses'].append(c)

# Definitions and general assignment. Section3(a)'s second half follows unrelated page furniture;
# keep two exact source spans within one legal clause, never silently join text into a quote.
clause('sec1a','(a) The terms defined','(b) The term “aerial flight”')
clause('sec1b','(b) The term “aerial flight”','(c) The term “aviation accident”')
clause('sec1c','(c) The term “aviation accident”','S ec. 2.')
clause('sec2','S ec. 2.','S ec. 3.')
clause('sec3a','S ec. 3.','(Continued on next page)',continuation=between(10152,'member or as a non-crew member','(b) Determinations'))
clause('sec3b','(b) Determinations','Sec. 4.')
sec4context=between(10152,'Sec. 4.','(a) Minimum flight requirements')
sec4acontext=between(10152,'(a) Minimum flight requirements','=== PDF page 3')
sec4bcontext=between(10152,'(b) Minimum flight requirements','(1) During one calendar month: 2')
for prefix,first,end,ct in [('sec4a','(1) During one calendar month: 4','(b) Minimum flight requirements',sec4acontext),('sec4b','(1) During one calendar month: 2','S ec. 5.',sec4bcontext)]:
    start=s.index(first); stop=s.index(end,start);block=s[start:stop]
    matches=list(re.finditer(r'(?m)^\([1-6]\)',block))
    for i,m in enumerate(matches):
        q=block[m.start():matches[i+1].start() if i+1<len(matches) else len(block)].rstrip()
        c={'scope_id':f'EO:10152#{prefix}{i+1}','original_operative_text':q,'original_source':source(10152),
           'state_at_cutoff':None,'first_end':None,'current_predicate':None,'later_events':[],
           'interpretive_context':{'sources':[source(10152,sec4context),source(10152,ct)]},
           'activation':{'source':source(10152,activation)},
           'first_end_gap':'Statutory and later regulatory continuity remains unresolved.'}
        claim['operative_clauses'].append(c)
clause('sec5','S ec. 5.','S ec. 6.')
clause('sec6','S ec. 6.','S ec. 7.')
for number, start, end in [(7,'S ec. 7.','S ec. 8.'),(8,'S ec. 8.','S ec. 9.'),(9,'S ec. 9.','Sec. 10.')]:
    a=s.index(start);b=s.index(end,a);block=s[a:b]
    matches=list(re.finditer(r'(?m)^\([a-d]\)',block))
    # Sections7/8 start (a) on the heading line; references such as204(a) are not labels.
    if number in [7,8]: matches=[re.search(r'\(a\)',block)]+matches
    intro=block[:matches[0].start()].rstrip()
    for i,m in enumerate(matches):
        q=block[m.start():matches[i+1].start() if i+1<len(matches) else len(block)].rstrip()
        c={'scope_id':f'EO:10152#sec{number}{m.group()[1]}','original_operative_text':q,'original_source':source(10152),
           'state_at_cutoff':None,'first_end':None,'current_predicate':None,'later_events':[],
           'activation':{'source':source(10152,activation)},
           'first_end_gap':'Read earlier amendments establish changes but do not alone resolve every retained command, statutory continuity or saved-pay effect.'}
        if intro: c['interpretive_context']={'source':source(10152,intro)}
        claim['operative_clauses'].append(c)
clause('sec10','Sec. 10.','S ec. it .')
clause('sec11','S ec. it .','=== PDF page 4')
clause('sec12','S ec. 12.','Sec. 13.')

events=[]
for n,start,end,date,reason in [
 (10618,'1. Subsection (b)','CO N TEN TS','1955-07-01','Original section9(b) replaced effective first day of month after June28,1955. Added9(e)-(g) separately effective April1,1955; they are not original1950 clauses.'),
 (10681,'By virtue of the authority','D w ig h t',None,'Added4(c) mixed active/inactive reserve flight rule; actual text has no separate effective-date clause. OCR corruption in the added operational tail remains a page-check gap.'),
 (10739,'1. Section 9','D wight','1957-09-01','Adds9(h), does not delete original9(a)-(d); actual express retrospective date, not signing date.'),
 (10892,'Section 1. Section 6','Dwight','1960-07-12','Replaces section6 while retaining original submarine/builders-trials text and adding submersible/training entitlements. Replacement does not automatically end every retained command.'),
 (11120,'Section 1. Executive Order','S ec . 2.', '1963-10-01','Changes6,8(a),9,10; adds12 and renumbers original12/13. Section9(c)/(d) expressly struck; substantive first-end/statutory priority still not certified.'),
 (11157,'S ec. 502. The following','L yndon','1964-06-22','Express present-tense revocation. Actual retained PDF page14 image confirms June22,1964 signature despite corrupt text-layer1961^. No deferred effective clause in the read order. This formal event is not asserted to be the earliest cessation.')]:
    q=between(n,start,end)
    e={'actor':f'EO:{n}','effective_date':date,'analysis':reason,'source':source(n,q)}
    if n==11120: e['effective_date_instrument']={'source':source(n,between(n,'Sec. 4. The amendments','J ohn'))}
    if n==10618: e['added_duties_activation']={'source':source(n,between(n,'Subsections (e), (f),  and (g)','Dwight'))}
    if n==11157:
        img=ROOT/'research/readiness/reviews/astra-2026-10-18/page-evidence/EO11157-14.png'
        e['page_image_verification']={'path':img.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(img.read_bytes()).hexdigest(),'finding':'Rendered page14 actually viewed; signature date is June22,1964; section502(b) lists EO10152.'}
    events.append(e)

claim['reviewed_later_events']=events
claim['whole_order_end']=None;claim['savings_residuals']=None;claim['later_source_search']=[]
claim['unresolved_material_gaps']=[
 {'gap':'Read actual Career Compensation Act1949 sections102/204/501(d), subsequent Title37 recodification and concrete1963 statutory amendments/effective/savings history. The original, EO11120 and EO11157 change statutory referents; continuity and accrued-pay effects cannot be decided from recital alone.','impact':'All first_end values, whole_order_end and savings_residuals remain null.'},
 {'gap':'Review remaining named/subject hits and current-law historical mentions. NAMED_SEARCH records actual located files and does not pretend each hit was read or resolved.','impact':'No final bounded later-source search or no-savings conclusion asserted.'},
 {'gap':'EO10681 operative added-tail OCR needs the queued official image before exact added-rule scope conclusions. EO11157 signature-year ambiguity was resolved by viewing retained PDF page14, but that does not close earlier cessation or savings.','impact':'Formal revocation is dated June22,1964; original clause states and first ends remain null pending substantive continuity review.'}]
claim['clause_inventory_reason']='Thirty-three substantive legal units cover original sections1-12. Section3(a) uses a separately cited continuation to avoid joining page furniture into the quote. Section4 common conditions and subsection lead-ins are quoted as interpretive context, not counted as independent commands. Section13 is the common activation rule. Headers, contents, signatures and neighboring EO10153 are excluded. Section11 OCR label it is retained verbatim; its position and complete command identify the intervening section. This is the official printing, not a signed original.'
claim['research_rationale']='Partial source-read reconstruction. Start from DRAFT_CLAIMS claim object; replace every APP original/inventory reference with held official FR spans and verified GPO fixity. Read the complete original and the relevant full earlier amending EOs10618,10681,10739,10892,11120, and EO11157 revocation/general terms. Separate original commands from added later duties, retained wording from actual cessation, and retroactive effective dates from signatures. No first-end or saved-entitlement conclusion is inferred from formal cleanup. Provisional no status is unchanged; clause states remain null pending material continuity/search work. No independent human review or full-readiness finding.'
assert len(claim['operative_clauses'])==33,len(claim['operative_clauses'])
assert len({c['scope_id'] for c in claim['operative_clauses']})==33
for c in claim['operative_clauses']: assert c['original_operative_text'] in s
dump('claim.json',claim)
dump('SOURCE_AUDIT.json',{'reviewer_role':'ai_review','kind':'producer source audit','sources':refs,'fixity_file_sha256':hashlib.sha256((ROOT/'jobs/official-fixity/output/MATCHED_BY_SHA256.json').read_bytes()).hexdigest(),'exact_original_units':33,'read_11157_scope':'Previously full text read; current dossier reread header, sections501/502 and closing signature/filing. No fresh complete-image read claimed.','model_usage':None})
dump('TELEMETRY.json',{'author_context':'root producer','finalized_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'measured_finalization_window_start_utc':'2026-10-19T01:41:03Z','full_producer_wall_seconds':None,'reason':'Earlier source reading began before measured finalization window; do not substitute this window for full producer cost.','model_usage':None,'claim_sha256':claim_sha(claim),'claim_file_sha256':hashlib.sha256((HERE/'claim.json').read_bytes()).hexdigest()})
print(json.dumps({'clauses':33,'claim_sha256':claim_sha(claim),'raw':hashlib.sha256((HERE/'claim.json').read_bytes()).hexdigest()}))
