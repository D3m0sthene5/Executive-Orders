from pathlib import Path
import copy, csv, hashlib, json, re, sys
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path.cwd()
OUT = ROOT / 'research/readiness/reviews/astra-2026-10-18/producer/EO_9932'
START = '2026-10-19T01:39:34Z'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return Path(p).read_text(encoding='utf-8')
def save(name, data):
    p = OUT / name
    if p.exists(): raise RuntimeError('Frozen output exists: '+str(p))
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
def between(t, a, b):
    i=t.index(a); return t[i:t.index(b,i)].rstrip()
fixpath='jobs/official-fixity/output/MATCHED_BY_SHA256.json'
fix=json.loads(read(fixpath))
texts={}
def source(n, page=None, quotes=None):
    p=Path(f'jobs/fr-originals/data/full_run/texts/EO_{n}.txt')
    t=texts.setdefault(n,read(p))
    s=re.search(r'downloaded file: ([0-9a-f]+)',t)[1]
    u=re.search(r'^Source: (.+)$',t,re.M)[1]
    assert fix[s]['result']=='match' and fix[s]['url']==u
    d={'url':u,'sha256':s,'page_or_item':page or re.search(r'^Location: (.+)$',t,re.M)[1],
       'text_path':p.as_posix(),'text_sha256':sha(p),'read_method':'held official text extract; no page image verification claimed',
       'official_fixity_record':fixpath,'official_fixity_result':'match'}
    if quotes is not None:
        assert all(q in t for q in quotes)
        d['quoted_parts']=quotes
    return d

original=source(9932,'13 FR 1099, PDF page 1; complete EO9932 paragraphs 1-7, excluding contents furniture')
actor=source(12292)
t=texts[9932]; a=texts[12292]
activation={'effective_date':'1947-09-01','source':source(9932,'13 FR 1099, PDF page 1, paragraph 7',[between(t,'7. This order','H arry')])}
revocation={'effective_date':'1981-02-15','actor':'EO:12292 sections 10(d) and 11',
 'mechanism':'Express formal revocation effective as of February 15, 1981; termination by that date, without an unsupported finding that it was the first cessation.',
 'source':source(12292,'46 FR 13968, PDF page 12, sections 10(d), 11 and signature',[
 'Sec. 10. The following are hereby revoked:', '(d) Executive Order No. 9932 of February 27,1948;',
 'Sec. 11. This Order shall be effective as of February 15,1981.', 'THE WHITE HOUSE, \nF eb ru a ry  23, 1981.'])}
source(12107); am=texts[12107]
amendment={'effective_date':'1979-01-01','actor':'EO:12107 sections 2-101(b) and 2-404',
 'mechanism':'Substitution of Office of Personnel Management for Civil Service Commission in EO9932. This changes the implementing office; it does not expressly end the substantive rule or State-concurrence proviso.',
 'source':source(12107,'44 FR 1056-1057 and 1064, PDF pages 322-323 and 330, sections 2-101, 2-101(b), 2-404',[
 between(am,'2-101.','(a) Executive orders'),
 between(am,'(b) Other Executive orders','9961'),
 between(am,'2-404.','T he  W h ite')])}
draftpath='jobs/case-bundles/output/drafts/09/EO_9932.json'
claim=copy.deepcopy(json.loads(read(draftpath))['claim'])
scopes=[f'EO:9932#para{i}' for i in range(1,7)]
ends=['2. Any','3. Whenever','4. The','5. A person','6. The','7. This']
starts=['1 . Any','2. Any','3. Whenever','4. The','5. A person','6. The']
for i,c in enumerate(claim['operative_clauses']):
    c['original_operative_text']=between(t,starts[i],ends[i])
    c['original_source']=source(9932,f'13 FR 1099, PDF page 1, paragraph {i+1}')
    c['activation']=copy.deepcopy(activation)
    c['state_at_cutoff']='terminated'
    c['first_end']=None; c['current_predicate']=None
    c['later_events']=([copy.deepcopy(amendment)] if i==5 else [])+[copy.deepcopy(revocation)]
    c['first_end_gap']='The actual history and continuity of the incorporated Foreign Service categories and reinstatement rights are unresolved; the known formal revocation is not presumed to be the earliest ending.'
claim['original_representation']=original
claim['formal_revocation']=revocation
claim['later_source_search']=[]
claim['whole_order_end']=None; claim['savings_residuals']=None
claim['inventory_reason']='Six numbered substantive provisions. Paragraph 2 includes both status acquisition and reinstatement; paragraph 4 includes both notice and return arrangements; paragraph 6 includes both implementing authority and State-concurrence protection. Paragraph 7 supplies common activation, not a seventh continuing command. Titles, signature and contents are excluded.'
gap1={'scope_ids':scopes,'type':'incorporated_statutory_categories_and_reinstatement_history_unread',
 'specific_authority':'Foreign Service Act of 1946 sections 522(2) and 528, including the Reserve/Staff categories and reinstatement rights incorporated in EO9932.',
 'concrete_transition':'EO12292 sections 5, 7(b) and 8(d) replace the related 1946 Act section 528 reference with 1980 Act section 310 (22 U.S.C. 3950). Actual statutory amendments, repeal, effective dates and transition/savings are not held in the inspected source-retention outputs.',
 'source':source(12292,'46 FR 13967-13968, PDF pages 11-12, preamble and sections 5, 7(b), 8(d)',[
 between(a,'By the authority','Section 1,'),between(a,'Sec. 5.','Sec. 6.'),
 between(a,'(b) Section 1-401','Sec. 8.'),between(a,'(d) Section l-602(b)','(e) Section 1-603')]),
 'needed':'Read actual operative sections and material amendments, the 1980 replacement/repeal/effective and savings provisions, and determine their effect on each original command and accrued rights. No earlier cessation is inferred from the gap.',
 'impact':'All first_end values, whole_order_end and savings_residuals remain null. Final adequate-search closure is withheld.'}
gap2={'scope_ids':scopes[:2], 'type':'status_route_and_appointment_transition_effect_unresolved',
 'specific_authority':'EO9932 paragraphs 1-2 incorporate Civil Service Rule III and eligibility tied to the appointment held at original Foreign Service assignment. EO10577 replaces the earlier Civil Service Rules and changes appointment systems; the actual 1950 conversion regulation also changes indefinite appointment categories.',
 'needed':'Resolve the effect of those actual changes on pending versus already-acquired status, including implementing rules, without assuming that a changed appointment label or a closed appointment cohort proves exhaustion of all original duties.',
 'source':source(10577,'19 FR 7525-7526, PDF pages 5-6, sections 201, 301 and 401',[
 between(read('jobs/fr-originals/data/full_run/texts/EO_10577.txt'),'S ec. 301.','P art IV'),
 between(read('jobs/fr-originals/data/full_run/texts/EO_10577.txt'),'S ec. 401.','D wight')]),
 'impact':'No first-end date for the status-acquisition routes is assigned. The exact 1955 transition date is not used as an EO9932 end.'}
claim['unresolved_material_gaps']=[gap1,gap2]
claim['research_rationale']='Partial candidate. The complete original establishes six continuing substantive rules, expressly effective as of September 1, 1947, although signed February 27, 1948. Individual four-year appointment eligibility, two-month notice, thirty-day reinstatement and waiver conditions do not set a whole-order calendar sunset. EO12107 expressly substitutes OPM for CSC effective January 1, 1979. EO12292 expressly revokes EO9932 effective February 15, 1981, rather than its February 23 signature date. That establishes termination by the cutoff but does not establish first cessation. The revoker identifies a concrete statutory transition from the incorporated 1946 reinstatement regime to 1980 Act section 310; actual statutory history and continuity are unread. Earlier actual Civil Service Rule III and appointment-system changes also require resolution for the status routes. Named-function searches additionally found narrower overseas-program reinstatement limitations; they are recorded as bounded leads and do not establish a global ending. Accrued competitive status and individual reinstatement rights are not declared invalid. Final search and savings closure are withheld, and provisional no status is unchanged.'
save('claim.json',claim)

# The exact bounded scope is enumerated rather than described as a repository-wide search.
search_started=datetime.now(timezone.utc).isoformat()
root_specs=[('jobs/fr-originals/data/full_run/texts','*.txt'),('jobs/source-ladder/output/texts','*.txt'),('jobs/opus-media-match/output/text','*.txt'),('jobs/ofr-codification-1989/output/texts','*.txt'),('jobs/astra-source-retention/output/pages','*/selected-pages.txt')]
patterns=[r'\b9932\b',r'foreign\s+service\s+(?:reserve|staff)',r'(?:competitive\s+status|reinstatement|reemployment).{0,250}foreign\s+service',r'foreign\s+service.{0,250}(?:competitive\s+status|reinstatement|reemployment)',r'(?:section\s+522|section\s+528|civil\s+service\s+rule\s+III)',r'civil\s+service\s+commission.{0,180}(?:abolish|transfer|succeed)',r'war.?service\s+indefinite',r'temporary\s+indefinite',r'Foreign\s+Service.{0,180}section\s+310',r'Foreign\s+Service\s+Act\s+of\s+(?:1946|1980)',r'Office\s+of\s+Personnel\s+Management.{0,180}(?:reinstatement|Foreign\s+Service)']
rx=[re.compile(q,re.I) for q in patterns]
manifest=[]; hits=[]; root_counts=[]
for root,glob in root_specs:
    files=sorted(Path(root).glob(glob)); root_counts.append({'root':root,'glob':glob,'recursive':False,'files_selected':len(files),'exclusions':[]})
    for p in files:
        b=p.read_bytes(); raw=b.decode('utf-8'); norm=re.sub(r'\s+',' ',re.sub(r'[\u00ad-]\s*\n','',raw))
        rec={'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'lfs_pointer':b.startswith(b'version https://git-lfs.github.com/spec/v1')};manifest.append(rec)
        for qi,r in enumerate(rx):
            mm=list(r.finditer(norm))
            if mm:hits.append({'path':p.as_posix(),'sha256':rec['sha256'],'query_index':qi,'hit_count':len(mm),'normalized_contexts':[norm[max(0,m.start()-160):min(len(norm),m.end()+240)] for m in mm]})
for name,rows in [('search-file-manifest.jsonl',manifest),('search-hits.jsonl',hits)]:
    p=OUT/name
    if p.exists():raise RuntimeError('exists')
    p.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows),encoding='utf-8',newline='\n')
machine=[json.loads(l) for l in read('jobs/readiness-tracker/output/MACHINE_LATER_SEARCH.jsonl').splitlines() if json.loads(l).get('instrument_id')=='EO:9932']
edges=[r for r in csv.DictReader(Path('jobs/later-events/output/EDGES.csv').open(encoding='utf-8-sig',newline='')) if r['target_id']=='EO:9932']
mentions=[r for r in csv.DictReader(Path('jobs/current-law/output/MENTIONS.csv').open(encoding='utf-8-sig',newline='')) if r['instrument_id']=='EO:9932']
ecfr=[r for r in csv.DictReader(Path('jobs/current-law/output/ECFR_SEARCH_HITS.csv').open(encoding='utf-8-sig',newline='')) if 'EO:9932' in r.values() or '9932' in r.values()]
retention_rows=[json.loads(l) for l in read('jobs/astra-source-retention/output/SOURCES.jsonl').splitlines()]
related=[
 (9830,'Civil Service Rule III and immediately surrounding provisions, extracted character range 26000-31005 and Rule IV context only; complete EO not claimed read','The original Rule III identifies multiple status routes; historical eligibility is not identical to a single terminal cohort.'),
 (10577,'Complete actual EO through signature, across the two reads of the full extract; neighboring agriculture material excluded','New rules expressly revoke EO9830 Part II and listed other orders, not EO9932. Appointment conversions and altered status routes require assessment, not an automatic global end.'),
 (10217,'Complete EO10217 and complete neighboring CSC amendment to section 2.115(a)','EO10217 itself amends EO10157. The actual neighboring regulation converts several appointment categories from December 1, 1950; it is not an EO10217 revocation of EO9932.'),
 (9970,'Complete neighboring CSC Part 25 section 25.225 War transfer regulation at 13 FR 3335, PDF page 3; unrelated EO9970 is not relied upon','This is an actual CSC pay-regulation definition incorporating EO9932 employment, not an EO9970 lifecycle act or a later revival.'),
 (10822,'Complete actual EO across beginning and ending reads, PDF pages 1-3; page furniture excluded','Section 1(z-2) adds a thirty-month restriction for persons henceforth appointed under Mutual Security Act section 527(c), subject to agency agreement. It is program-specific; overlap with EO9932 statutory categories remains unresolved.'),
 (11219,'Complete actual EO, PDF pages 5-6','Separate appointment route for qualified current/former Foreign Service personnel. No express EO9932 repeal; actual 1981 amendments to this route are also read in EO12292.'),
 (11579,'Complete actual EO, PDF pages 5-6','OPIC functions and a separate reinstatement-regulation delegation. Its transfer/savings terms preserve applicable actions and do not expressly terminate EO9932.'),
 (10893,'Every raw 528/reinstat match with 700 characters before and 750 after; no complete-current-task read claimed','The retrieved 528 occurrence concerns the Mutual Security Act, not Foreign Service Act section 528; statutory names must not be conflated.'),
 (10973,'Every raw 528/reinstat match with 700 characters before and 750 after; relevant section 603(b) context only','Foreign-aid thirty-month reinstatement limitation; actual scope and agency-agreement exception recorded, no global end inferred.'),
 (11034,'Every raw 528/reinstat match with 700 characters before and 750 after; complete relevant section 5(c) and adjoining paragraphs','Cultural exchange personnel have section 528 benefits with a thirty-month/agency-agreement rule; this is the concrete antecedent of EO12292 section 5.'),
 (11041,'Every raw 528/reinstat match with 700 characters before and 750 after; complete relevant section 301 and adjoining context','Peace Corps program-specific thirty-month limit.'),
 (11603,'Every raw 528/reinstat match with 700 characters before and 750 after; complete relevant section 301 across PDF pages 12-13','Peace Corps program-specific thirty-month limit, not proof of EO9932-wide cessation.'),
 (12137,'Every raw 528/reinstat match with 700 characters before and 750 after; complete section 1-401 on PDF page 11','Actual antecedent to EO12292 section 7(b), tying Peace Corps benefits to 1946 section 528.'),
 (12163,'Every raw 528/reinstat match with 700 characters before and 750 after; section 1-602(b) and adjoining context','Actual antecedent to EO12292 section 8(d); retains agency-agreement exception to program-specific thirty-month limitation.'),
 (12188,'Header and named-function search contexts only; no full EO read claimed','Commercial-service extension lead remains contextual; no cessation conclusion relies on it.')]
read_records=[]
for n,scope,reason in [(9932,'Complete EO9932 including all seven numbered paragraphs and signature','Original inventory and express activation'),(12107,'Complete actual EO, PDF pages 321-330; sections 2-101/2-404 and savings reread','Direct succession amendment, not revocation'),(12292,'Complete actual EO, PDF pages 11-12','Formal revocation, actual effective date, statutory transition')]+related:
    s=source(n); cache=Path('jobs/fr-originals/data/full_run/blobs')/s['sha256'][:2]/(s['sha256']+'.pdf')
    retained=Path('jobs/astra-source-retention/output/pdf')/(s['sha256']+'.pdf')
    read_records.append({'instrument_id':f'EO:{n}','source':s,'read_scope':scope,'reason':reason,'official_fixity':fix[s['sha256']],
     'historical_pdf_cache_path':cache.as_posix(),'historical_pdf_cache_exists':cache.exists(),
     'retained_pdf_path':retained.as_posix() if retained.exists() else None,
     'retained_pdf_sha256':sha(retained) if retained.exists() else None,'page_image_read':False})
workpaper={'instrument_id':'EO:9932','search_started_utc':search_started,'search_finished_utc':datetime.now(timezone.utc).isoformat(),
 'roots':root_counts,'queries':patterns,'normalization':'UTF-8 decoding; remove soft-hyphen or hyphen followed by whitespace/newline; collapse whitespace; case-insensitive regex. Full selected files searched, including neighboring text and headers. No date filter or deduplication.',
 'file_manifest':'search-file-manifest.jsonl','file_manifest_sha256':sha(OUT/'search-file-manifest.jsonl'),'hit_file':'search-hits.jsonl','hit_file_sha256':sha(OUT/'search-hits.jsonl'),'selected_file_count':len(manifest),
 'query_file_hits':len(hits),'scope_limit':'Only the five explicitly selected roots/globs were searched by this producer. This is not a search of all jobs, all repo files, all historical statutes, or underlying U.S. Code/eCFR bulk corpora. Search matches are discovery contexts, not a claim that every matched document was read in full.',
 'machine_later_search_record':machine,'machine_scopes_not_reexecuted':json.loads(read('jobs/claim-kit/output/dossiers/EO_9932.json'))['machine_searches'],
 'machine_scope_assessment':'Machine catalog/saved-text/current-law searches are retained as leads only, not final closure. The dossier reports zero USC hits but actual MENTIONS.csv has one historic printed EO12292 note; the discrepancy is recorded, not silently accepted.',
 'earlier_edges':edges,'edge_resolution':'All four rows resolve to two actual actors, read in full. EO12107 target appears expressly in section 2-101(b) despite machine missing-provision flag; effective January 1, 1979. EO12292 operative revocation is section 10(d), not machine section 9 label; effective February 15, 1981, not signature February 23.',
 'current_law_mentions':mentions,'current_ecfr_exact_hits':ecfr,'current_law_resolution':'The sole USC mention is a printed historic revocation, not a present predicate. No numeric eCFR hit in the inspected output. Underlying bulk sources not newly searched or certified adequate.',
 'related_source_read_granularity':read_records,
 'unclosed_leads':'Foreign Service Act amendments/1980 transition; Rule III and implementing-regulation effects on pending status; intersection of program-specific thirty-month limits with EO9932 covered categories. Numeric and named searches do not alone close these issues.',
 'out_of_scope_hit_policy':'Earlier orders are background; individual appointments/transfers, salary/retirement provisions and unrelated section numbers are not automatically target lifecycle events. Same-source duplicates do not add legal evidence. Actual EO/neighboring regulation identity was checked for material hits.'}
save('bounded-search-workpaper.json',workpaper)

checks=[]
def walk(o,where='claim',src=None):
    if isinstance(o,dict):
        own=o if 'url' in o and 'text_path' in o else src
        if 'original_operative_text' in o:
            s=o['original_source'];q=o['original_operative_text'];checks.append({'field':where+'.original_operative_text','text_path':s['text_path'],'exact_substring':q in read(s['text_path'])})
        if 'quoted_parts' in o:
            for j,q in enumerate(o['quoted_parts']):checks.append({'field':where+f'.quoted_parts[{j}]','text_path':o['text_path'],'exact_substring':q in read(o['text_path'])})
        for k,v in o.items():walk(v,where+'.'+k,own)
    elif isinstance(o,list):
        for j,v in enumerate(o):walk(v,where+f'[{j}]',src)
walk(claim)
assert all(x['exact_substring'] for x in checks)
sys.path.insert(0,str(Path('research/stage19/code').resolve()))
from claim_gate import claim_sha, validate_claim
gate=validate_claim(claim)
finished=datetime.now(timezone.utc)
elapsed=(finished-datetime.fromisoformat(START.replace('Z','+00:00'))).total_seconds()
audit={'instrument_id':'EO:9932','producer_role':'AI producer','candidate_verdict':'partial_pending_independent_review','started_utc':START,'finished_utc':finished.isoformat(),'elapsed_wall_seconds':elapsed,'actual_model_usage':None,'actual_token_usage':None,
 'read_granularity':read_records,'inventory_reason':claim['inventory_reason'],
 'chronology_reasoning':[claim['research_rationale'],'1950 appointment conversions and EO10577 rules replacement are actual earlier leads, not assumed exhaustion of every original assignment/status case.','The 1959 and later overseas-program limits have express population qualifications and agency-agreement exceptions; no global date is inferred from an individual duration limit.'],
 'savings_reasoning':'Original paragraph 6 protects already assigned personnel against later rule changes absent State concurrence. Original accrued competitive status and reinstatement outcomes are distinct from an ongoing rule. EO12107 section 2-202 has personnel-action savings, but EO9932 was amended, not revoked there; this provision is not treated as perpetual survival after EO12292. EO12292 contains no express target-specific savings; actual statutory transition remains unread. Therefore savings_residuals stays null.',
 'earlier_edges':edges,'source_retention_inventory_checked':{'path':'jobs/astra-source-retention/output/SOURCES.jsonl','sha256':sha(Path('jobs/astra-source-retention/output/SOURCES.jsonl')),'rows_observed':len(retention_rows),'relevant_missing_actual_statutes':['STATUTE-60-Pg999','STATUTE-94-Pg2071'],'inventory_only_no_unrelated_full_read':True},
 'search_provenance_file':'bounded-search-workpaper.json','gaps':claim['unresolved_material_gaps'],'exact_quote_count':len(checks),'exact_quote_checks':checks,
 'no_external_fetch':True,'no_canonical_publication':True,'no_protected_writes':True,'page_image_verification_claimed':False}
save('source-read-audit.json',audit)
requests=[]
for url,purpose in [
 ('https://www.govinfo.gov/content/pkg/STATUTE-60/pdf/STATUTE-60-Pg999.pdf','Complete Foreign Service Act of 1946, especially sections 522(2), 528, statutory categories, effective and savings terms; identify material amendments for original status/reinstatement regime.'),
 ('https://www.govinfo.gov/metadata/pkg/STATUTE-60/premis.xml','Official fixity metadata for the 1946 Act source.'),
 ('https://www.govinfo.gov/content/pkg/STATUTE-94/pdf/STATUTE-94-Pg2071.pdf','Complete Foreign Service Act of 1980, particularly section 310, appointment-category replacement, repeal, effective, transition and savings terms affecting EO9932.'),
 ('https://www.govinfo.gov/metadata/pkg/STATUTE-94/premis.xml','Official fixity metadata for the 1980 Act source.'),
 ('https://www.govinfo.gov/content/pkg/USCODE-1976-title22/pdf/USCODE-1976-title22.pdf','Historical title 22 text and source/amendment notes for Foreign Service Act 1946 sections 522(2) and 528 / 22 U.S.C. 922 and 928; identify actual intervening acts for follow-up, not substitute notes for primary enactments.'),
 ('https://www.govinfo.gov/metadata/pkg/USCODE-1976-title22/premis.xml','Official fixity metadata for historical title 22.')]: requests.append({'instrument_id':'EO:9932','url':url,'purpose':purpose,'status':'proposed_only_not_fetched','queue_by':'coordinator','existing_queue_may_already_cover':True})
(OUT/'proposed-source-requests.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in requests),encoding='utf-8',newline='\n')
validation={'instrument_id':'EO:9932','candidate_verdict':'partial','canonical_claim_sha256':claim_sha(claim),'raw_claim_sha256':sha(OUT/'claim.json'),'source_read_audit_sha256':sha(OUT/'source-read-audit.json'),'bounded_search_workpaper_sha256':sha(OUT/'bounded-search-workpaper.json'),'structural_gate_errors':gate,'gate_errors_expected_for_partial':True,'exact_quote_count':len(checks),'all_exact_quotes_passed':True,'actual_claim_checker_run':False,'elapsed_wall_seconds':elapsed,'actual_model_usage':None,'actual_token_usage':None}
save('validation.json',validation)
(OUT/'AUDIT.md').write_text('EO9932 partial candidate, pending independent review.\n\nSix substantive rules; common activation 1947-09-01. EO12107 substitution effective 1979-01-01; formal EO12292 revocation effective 1981-02-15. First ends, whole-order end and savings remain null for actual statutory/status-route gaps.\n\nSee source-read-audit.json for exact reading scope and custody; bounded-search-workpaper.json plus the complete search-file-manifest.jsonl for reproducible bounded search. Machine scopes are explicitly separate. No page images, canonical publication, protected writes, human certification or external fetching are claimed.\n\nCanonical candidate SHA256: '+validation['canonical_claim_sha256']+'\nRaw candidate SHA256: '+validation['raw_claim_sha256']+'\nActual elapsed wall seconds: '+str(elapsed)+'; actual model/token usage unavailable (null).\n',encoding='utf-8',newline='\n')
print(json.dumps(validation,indent=2))
print('ROOT_COUNTS',json.dumps(root_counts))
