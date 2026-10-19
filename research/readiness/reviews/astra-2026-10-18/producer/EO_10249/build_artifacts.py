from pathlib import Path
from datetime import datetime, timezone
import copy,csv,hashlib,json,re,sys
sys.stdout.reconfigure(encoding='utf-8')
OUT=Path(__file__).resolve().parent
START='2026-10-19T01:51:57Z'
def read(p):return Path(p).read_text(encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,d):
    with (OUT/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def between(t,a,b):
    i=t.index(a);return t[i:t.index(b,i)].rstrip()
FIX='jobs/official-fixity/output/MATCHED_BY_SHA256.json';fix=json.loads(read(FIX));texts={}
def source(n,page=None,quotes=None):
    p=Path(f'jobs/fr-originals/data/full_run/texts/EO_{n}.txt');t=texts.setdefault(n,read(p))
    h=re.search(r'downloaded file: ([0-9a-f]+)',t)[1];u=re.search(r'^Source: (.+)$',t,re.M)[1]
    assert fix[h]['result']=='match' and fix[h]['url']==u
    s={'url':u,'sha256':h,'page_or_item':page or re.search(r'^Location: (.+)$',t,re.M)[1],'text_path':p.as_posix(),'text_sha256':sha(p),'official_fixity_record':FIX,'official_fixity_result':'match','read_method':'held official extract; no page-image verification claimed'}
    if quotes is not None:
        assert all(q in t for q in quotes);s['quoted_parts']=quotes
    return s
original=source(10249,'16 FR 5309, PDF page 1; entire EO10249 extract read, with materially damaged section 4 opening; image absent from checked caches')
actor=source(12292);related=source(11264)
t=texts[10249];a=texts[12292];b=texts[11264]
claim=copy.deepcopy(json.loads(read('jobs/case-bundles/output/drafts/10/EO_10249.json'))['claim'])
original['quoted_parts']=[between(t,'By virtue','Sec. 2.')]
rev={'effective_date':'1981-02-15','actor':'EO:12292 sections 10(e) and 11','mechanism':'Express formal revocation effective as of February 15, 1981. Establishes termination by that date; earliest cessation remains unresolved.',
 'source':source(12292,'46 FR 13968, PDF page 12, sections 10(e), 11 and signature',[
 'Sec. 10. The following are hereby revoked:','(e) Executive Order No. 10249 of June 4,1951;',
 'Sec. 11. This Order shall be effective as of February 15,1981.','THE WHITE HOUSE, \nF eb ru a ry  23, 1981.'])}
activation={'effective_date':'1951-06-04','basis':'Signing date; no deferred, retroactive, conditional or otherwise separate activation clause appears in the complete held EO extract. This is not an express effective-date sentence.',
 'source':source(10249,'16 FR 5309, PDF page 1, signature',[between(t,'Harry S. T ruman','[F. R. Doc.')])}
cl=[]
for sec,stop in [(2,'Sec. 3.'),(3,'Sec. 4.'),(4,'Harry S. T ruman')]:
    cl.append({'scope_id':f'EO:10249#sec{sec}','original_operative_text':between(t,f'Sec. {sec}.',stop),'original_source':source(10249,f'16 FR 5309, PDF page 1, section {sec}'+('; opening words materially damaged in held OCR' if sec==4 else '')),
      'state_at_cutoff':'terminated','activation':copy.deepcopy(activation),'first_end':None,'current_predicate':None,'later_events':[copy.deepcopy(rev)],
      'first_end_gap':'Actual statutory continuity of the specifically implemented reporting regime in Foreign Service Act of 1946 section 311 and its 1980 transition remains unread.'})
cl[1]['included_subduties']=['Prepare and maintain comprehensive statement of useful types of foreign data, attending to relative importance.','Prepare and maintain standards for transmitting requests and assigning priorities.','Afford interested Federal departments and agencies consultation opportunity and consider advice when preparing or revising the statement and standards.']
cl[2]['text_completeness_gap']='The opening priority-direction sentence is materially garbled; raw held text is preserved, not silently reconstructed. The subsequent resource-management and agency-relative-priority language is legible.'
gap1={'scope_ids':['EO:10249#sec4'],'type':'material_original_text_damage','source':source(10249,'16 FR 5309, PDF page 1, opening of section 4',[between(t,'Sec. 4.','it may take')]),
 'needed':'Retain and read official FR-1951-06-06 PDF page 1; verify the complete section 4 imperative, its subject and object. Existing fixity identifies the source bytes but does not repair the missing text. No page-image reading is claimed.',
 'impact':'Exact scope and completeness of section 4 cannot be certified; inventory and whole-order closure remain partial.'}
gap2={'scope_ids':[c['scope_id'] for c in cl],'type':'specific_statutory_reporting_regime_history_unread',
 'specific_authority':'Foreign Service Act of 1946 section 311, 60 Stat. 1002, then 22 U.S.C. 846, expressly implemented by EO10249 reporting regulations.',
 'concrete_transition':'EO12292 says its amendments and revocations conform existing orders to changes resulting from the Foreign Service Act of 1980 and specifically revokes EO10249 in section 10(e). Actual section 311 history and the 1980 repeal/replacement/effective/continuity terms are not yet held in the inspected retention outputs. The exact replacement provision is not guessed.',
 'source':source(12292,'46 FR 13967-13968, PDF pages 11-12, preamble and section 10(e)',[between(a,'By the authority','Section 1,'),'(e) Executive Order No. 10249 of June 4,1951;']),
 'supporting_sources':[{'source':source(10249,'16 FR 5309, PDF page 1, statutory recital',[between(t,'By virtue','Section 1.')])}],
 'needed':'Read actual section 311 and material amendments, and the actual 1980 change, repeal, commencement and savings provisions. Determine whether the original reporting regulations continued, were displaced earlier or ended with the known formal revocation.',
 'impact':'All first_end values, whole_order_end and savings_residuals remain null, and final adequate-search closure is withheld. No earlier cessation is asserted from missing evidence.'}
claim.update(operative_clauses=cl,original_representation=original,later_source_search=[],whole_order_end=None,savings_residuals=None,formal_revocation=rev,unresolved_material_gaps=[gap1,gap2])
claim['inventory_reason']='Three substantive section units: section 2 data-obtaining duty; section 3 statement/standards/consultation duties; section 4 priority/resource/relative-priority directions. The preamble prescribes these regulations but is not an additional independent duty. Section 1 defines foreign data and qualifies every substantive unit; preserved with the original source. Section 3 lead-in and subdivisions are reunited because the machine draft severed the verb and combined (a)/(b). Full inventory certification is withheld pending the damaged section 4 opening.'
claim['research_rationale']='Partial candidate. The full held original extract was read through the signature. Sections 2-4 impose continuing data collection, maintenance/consultation and prioritization functions; maintaining the statement and standards is not completed by initial preparation. The definition in section 1 includes reports, statistics and publications. No own-term sunset, fixed deadline, automatic completion or termination event appears; resource and practicability limits qualify performance. Signature is June 4, 1951, with no separate activation clause. Section 4 opening is materially damaged in OCR and the original PDF is absent from checked local caches; it is not reconstructed from a nonofficial transcription. Full EO12292 establishes formal revocation effective February 15, 1981, not the February 23 signature date. It does not alone establish the first ending of regulations expressly implementing 1946 Act section 311. The 1980 Act transition and statutory continuity remain unread. Full EO11264 creates separate report-supply duties to personnel boards and limited savings; it does not expressly amend or revive EO10249 foreign-data collection. Bounded named/function searches and numeric leads are preserved with exact file manifests; no final search closure, savings disposition, human certification or canonical publication is asserted. Provisional no status is unchanged.'
save('claim.json',claim)

edges=[r for r in csv.DictReader(Path('jobs/later-events/output/EDGES.csv').open(encoding='utf-8-sig',newline='')) if r['target_id']=='EO:10249']
mentions=[r for r in csv.DictReader(Path('jobs/current-law/output/MENTIONS.csv').open(encoding='utf-8-sig',newline='')) if r['instrument_id']=='EO:10249']
ecfr=[r for r in csv.DictReader(Path('jobs/current-law/output/ECFR_SEARCH_HITS.csv').open(encoding='utf-8-sig',newline='')) if 'EO:10249' in r.values() or '10249' in r.values()]
machine=[json.loads(l) for l in read('jobs/readiness-tracker/output/MACHINE_LATER_SEARCH.jsonl').splitlines() if json.loads(l).get('instrument_id')=='EO:10249']
family=json.loads(read('jobs/family-rules/output/evidence/EO_12292/EO_10249.json'))
counter=[]
for r in family['counterexamples']:
    p=Path(r['text_path']);raw=read(p)
    counter.append({**r,'text_sha256':sha(p),'reading':'Target-number contexts checked; full underlying original/revoker separately read. No independent full read of every duplicate claimed.','resolution':'Duplicate original EO10249 text' if '10249' in p.name else 'Duplicate actual EO12292 revocation, not a later active predicate','actual_contexts':[raw[max(0,m.start()-180):min(len(raw),m.end()+260)] for m in re.finditer('10249',raw)]})
records=[]
for n,scope,reason in [(10249,'Entire held official extract including all sections and signature, excluding neighboring agriculture rules and contents; section 4 material OCR damage expressly preserved','Original and own-term assessment; no claimed image verification or exact section 4 reconstruction'),(12292,'Complete actual EO, PDF pages 11-12, all amendments/revocations and signature','Effective formal revocation and concrete Foreign Service Act transition lead'),(11264,'Complete actual EO through signature, PDF pages 5-7; blank page 8 and neighboring rules page 9 excluded','Distinct boards and their report-supply duty; complete savings terms read')]:
    s=source(n);cache=Path('jobs/fr-originals/data/full_run/blobs')/s['sha256'][:2]/(s['sha256']+'.pdf');ret=Path('jobs/astra-source-retention/output/pdf')/(s['sha256']+'.pdf')
    records.append({'instrument_id':f'EO:{n}','source':s,'read_scope':scope,'reason':reason,'official_fixity':fix[s['sha256']], 'checked_historical_cache':cache.as_posix(),'historical_cache_exists':cache.exists(),'checked_retention_cache':ret.as_posix(),'retention_cache_exists':ret.exists(),'retained_pdf_sha256':sha(ret) if ret.exists() else None,'page_image_read':False})
boardsource=source(11264,'31 FR 68-69, PDF pages 6-7, section 41(b), section 42 saving provisions',[
 between(b,'(b) Upon request of the Secretary','S ec,. 42.'),between(b,'S ec,. 42.','S e c. 43.')])
searchmeta=json.loads(read(OUT/'search-metadata.json'))
work={'instrument_id':'EO:10249','search':searchmeta,'search_file_manifest':'search-file-manifest.jsonl','search_file_manifest_sha256':sha(OUT/'search-file-manifest.jsonl'),'search_hits_file':'search-hits.jsonl','search_hits_sha256':sha(OUT/'search-hits.jsonl'),
 'all_hit_contexts_read':True,'hit_resolutions':[
 {'group':'EO10249 and copies','resolution':'Original actual order and its definition/recital; not later lifecycle action.'},
 {'group':'EO12292 and official copies','resolution':'Formal revocation, actual text and effective clause read in full.'},
 {'group':'EO11264','resolution':'Section 41(b) requires departments to furnish reports to personnel boards, a different direction, recipient and subject from EO10249 obtaining foreign data through the Foreign Service for agencies. Sections 42(a)-(c) save actions tied to functions affected by that board order, not a blanket continuation of EO10249. No EO10249 amendment or ending stated.','source':boardsource},
 {'group':'EO8189/8190/8191/8192,8305/8306/8307,8346,8356/8357/8358,8396 and ladder copy,9001A,9539,9880 ladder neighbor','resolution':'Pre-1951 background, neighboring Foreign Service regulations/organization, property/personnel reporting or non-Foreign-Service military usage. Contexts only, not a later cessation claim. Duplicate neighboring-source hits not attributed to each file-label actor.'},
 {'group':'EO12493 and codification copy; EO14251','resolution':'Later personnel assignments and reporting hierarchy / labor exclusions. Search contexts do not impose EO10249 data-obtaining functions or revive its regulations; no full source read claimed.'},
 {'group':'EO12661 and codification copy; EO12851','resolution':'Later specific defense/trade/arms reporting functions under separately named statutes, not EO10249 foreign-data requests; contexts only, no global statutory-history conclusion.'},
 {'group':'EO12910 FR document number 94-10249; EO13825 printed page 10249; EO9599 contents page numbers; EO10480 ladder neighboring FCC docket 10249','resolution':'Numeric false positives identified in actual contexts, not references to EO10249.'}],
 'earlier_edges':edges,'edge_resolution':'Two duplicate catalog edges; actual sole actor EO12292 section 10(e), with section 11 effective February 15, 1981. No earlier edge in inspected table. This is not evidence that no earlier statutory effect exists.',
 'current_law_mentions':mentions,'ecfr_exact_hits':ecfr,'current_law_resolution':'One historic printed EO12292 revocation note, not a current operative predicate. Dossier machine summary says zero USC hits, whereas actual MENTIONS.csv has one; discrepancy recorded. Underlying USC/eCFR corpora not rerun.',
 'machine_later_search_record':machine,'machine_search_scopes':json.loads(read('jobs/claim-kit/output/dossiers/EO_10249.json'))['machine_searches'],'machine_scope_judgment':'Retained leads, not adopted final adequate-search closure. Explicit bounded producer search is separate from these machine-reported catalog/bulk scopes.',
 'counterexample_resolutions':counter,'material_gaps':claim['unresolved_material_gaps'],'full_read_source_records':records}
save('bounded-search-workpaper.json',work)
checks=[]
def walk(o,where):
    if isinstance(o,dict):
        if 'original_operative_text' in o:
            checks.append({'field':where+'.original_operative_text','text_path':o['original_source']['text_path'],'exact_substring':o['original_operative_text'] in read(o['original_source']['text_path'])})
        if 'quoted_parts' in o:
            for i,q in enumerate(o['quoted_parts']):checks.append({'field':where+f'.quoted_parts[{i}]','text_path':o['text_path'],'exact_substring':q in read(o['text_path'])})
        for k,v in o.items():walk(v,where+'.'+k)
    elif isinstance(o,list):
        for i,v in enumerate(o):walk(v,where+f'[{i}]')
walk(claim,'claim');walk(work,'workpaper');assert all(x['exact_substring'] for x in checks)
retrows=[json.loads(l) for l in read('jobs/astra-source-retention/output/SOURCES.jsonl').splitlines()]
assert not [r for r in retrows if 'STATUTE-60-Pg999' in r['url'] or 'STATUTE-94-Pg2071' in r['url']], 'Source availability changed: read actual statutes before claiming absence'
finished=datetime.now(timezone.utc);elapsed=(finished-datetime.fromisoformat(START.replace('Z','+00:00'))).total_seconds()
audit={'instrument_id':'EO:10249','producer_role':'AI producer','candidate_verdict':'partial_pending_independent_review','started_utc':START,'finished_utc':finished.isoformat(),'elapsed_wall_seconds':elapsed,'actual_model_usage':None,'actual_token_usage':None,'source_read_granularity':records,
 'inventory_reason':claim['inventory_reason'],'own_terms':'No sunset, deadline, completion or trigger date. Section 3 requires maintenance and consultation on revisions, so initial preparation is not cessation. Section 4 resource/practicability qualifications are not termination dates. Exact section 4 opening requires the original page.',
 'activation_reason':activation,'chronology_reasoning':claim['research_rationale'],
 'savings_reasoning':'No target-specific savings clause appears in full EO10249 or full EO12292. Board-order EO11264 savings are bounded to its affected board functions and do not establish blanket EO10249 survival. Existing reports, completed data collection and agency work products are not invalidated merely because the original order ended. Actual statutory continuation and residual reporting obligations remain unresolved, so savings_residuals is null.',
 'search_provenance':'bounded-search-workpaper.json plus exact search-metadata.json, search-file-manifest.jsonl and search-hits.jsonl; no broader scope implied',
 'source_retention_inventory':{'path':'jobs/astra-source-retention/output/SOURCES.jsonl','sha256':sha('jobs/astra-source-retention/output/SOURCES.jsonl'),'rows_observed':len(retrows),'required_statutes_present':False,'source_acquisition_reported_running_not_read':True},
 'gaps':claim['unresolved_material_gaps'],'exact_quote_checks':checks,'exact_quote_count':len(checks),'no_external_fetch':True,'no_canonical_publication':True,'no_protected_writes':True,'page_images_read':False}
save('source-read-audit.json',audit)
requests=[]
for url,purpose in [
 ('https://www.govinfo.gov/content/pkg/FR-1951-06-06/pdf/FR-1951-06-06.pdf','Retain actual original bytes and page 1 (16 FR 5309); materially damaged section 4 opening requires image/text verification. Held MATCHED_BY_SHA256 already identifies expected SHA256 41cef3c20ae57f45f737f380884b13831fc2aef89b2f4e3e0779d0814113028c.'),
 ('https://www.govinfo.gov/metadata/pkg/FR-1951-06-06/premis.xml','Retain/reconfirm official fixity metadata for the material original-page request.'),
 ('https://www.govinfo.gov/content/pkg/STATUTE-60/pdf/STATUTE-60-Pg999.pdf','Actual Foreign Service Act 1946 section 311 (60 Stat. 1002), reporting regime and relevant effective/savings terms; already reported queued.'),
 ('https://www.govinfo.gov/metadata/pkg/STATUTE-60/premis.xml','Official fixity metadata for actual 1946 enactment.'),
 ('https://www.govinfo.gov/content/pkg/STATUTE-94/pdf/STATUTE-94-Pg2071.pdf','Actual Foreign Service Act 1980 changes to section 311 reporting regime, repeal/replacement, effective and continuity/savings terms; already reported queued.'),
 ('https://www.govinfo.gov/metadata/pkg/STATUTE-94/premis.xml','Official fixity metadata for actual 1980 enactment.'),
 ('https://www.govinfo.gov/content/pkg/USCODE-1976-title22/pdf/USCODE-1976-title22.pdf','Historical 22 U.S.C. 846 text and amendment/source notes to identify actual intervening enactments; not a substitute for reading the enactments.'),
 ('https://www.govinfo.gov/metadata/pkg/USCODE-1976-title22/premis.xml','Official fixity metadata for historical title 22.')]:requests.append({'instrument_id':'EO:10249','url':url,'purpose':purpose,'status':'proposed_only_not_fetched','queue_by':'coordinator','deduplicate_existing_queue':True})
(OUT/'proposed-source-requests.jsonl').open('x',encoding='utf-8',newline='\n').write(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in requests))
sys.path.insert(0,str(Path('research/stage19/code').resolve()))
from claim_gate import claim_sha,validate_claim
v={'instrument_id':'EO:10249','verdict':'partial','canonical_claim_sha256':claim_sha(claim),'raw_claim_sha256':sha(OUT/'claim.json'),'source_read_audit_sha256':sha(OUT/'source-read-audit.json'),'bounded_search_workpaper_sha256':sha(OUT/'bounded-search-workpaper.json'),'structural_gate_errors':validate_claim(claim),'expected_partial_errors':True,'exact_quote_count':len(checks),'all_exact_quotes_passed':True,'actual_claim_checker_run':False,'elapsed_wall_seconds':elapsed,'actual_model_usage':None,'actual_token_usage':None}
save('validation.json',v)
(OUT/'AUDIT.md').open('x',encoding='utf-8',newline='\n').write('EO10249 partial candidate, pending independent review.\n\nThree substantive section units preserve the full identified command structure; definition and recital are not independent duties. Exact section 4 wording requires the original page because held OCR is materially damaged. Actual 1946 section 311 / 1980 transition remains unread. Formal revocation is proven effective 1981-02-15, but first ends, whole-order end and savings remain null.\n\nBounded search covers the five precisely enumerated root/glob selections and hashes all 7,825 files. Machine scopes are separately identified and not adopted as final closure. See JSON workpaper and audit for source-read granularity.\n\nCanonical SHA256: '+v['canonical_claim_sha256']+'\nRaw SHA256: '+v['raw_claim_sha256']+'\nActual wall seconds: '+str(elapsed)+'; usage telemetry null.\n')
print(json.dumps(v,indent=2))
