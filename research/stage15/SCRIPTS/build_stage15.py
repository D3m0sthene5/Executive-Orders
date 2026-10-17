#!/usr/bin/env python3
"""Construct issue-oriented, no-status-promotion audit overlay from Stage 11 + Stage 14.
Never write upstream source bytes. The release is a diagnostic, not a legal adjudicator.
"""
import os,json,csv,sqlite3,re,hashlib,random,math,collections,datetime,sys
from pathlib import Path
BASE=Path(os.environ.get('EO_STAGE15_OUTPUT_DIR','/mnt/data/EO_STAGE15_METHOD_FOUNDATION_2026-10-16'))
SRC=Path(os.environ.get('EO_STAGE15_INPUT_ROOT','/mnt/data/eo_stage15_workspace'))
LEDGER=Path(os.environ.get('EO_STAGE11_LEDGER',str(SRC/'STAGE11/RECONCILED_STATUS_LEDGER_STAGE11_PROVISIONAL.jsonl')))
GRAPH=Path(os.environ.get('EO_STAGE14_GRAPH',str(SRC/'EO_STAGE14_LEVERAGE_ENGINE_2026-10-16/DATA/EO_SOURCE_DEPENDENCY_GRAPH.sqlite')))
LORD=Path(os.environ.get('EO_STAGE14_LORD_LEADS',str(SRC/'EO_STAGE14_LEVERAGE_ENGINE_2026-10-16/LORD/LORD_CHRONOLOGICAL_REVIEW_LEADS.csv')))
AUD13=SRC/'EO_STAGE13_FOUNDATIONAL_VALIDATION_2026-10-16/AUDIT/INDEPENDENT_BLIND_FIRST_EIGHT.jsonl'
assert LEDGER.is_file() and GRAPH.is_file() and LORD.is_file()
CUTOFF='2026-10-14';SEED=20261016
rows=[json.loads(l) for l in LEDGER.open() if l.strip()]; rmap={r['instrument_id']:r for r in rows};assert len(rows)==15010
conn=sqlite3.connect(GRAPH);conn.row_factory=sqlite3.Row
orderrows={r['id']:dict(r) for r in conn.execute('select * from orders')};assert len(orderrows)==15010
included=[r for r in rows if r['included_validated'] is True]
unique=[r for r in included if orderrows[r['instrument_id']]['include_unique']==1];assert len(unique)==14972

def write_csv(path,records,fields=None):
 path=BASE/path;path.parent.mkdir(parents=True,exist_ok=True)
 records=list(records);fields=fields or (list(records[0]) if records else [])
 with path.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fields,extrasaction='ignore');w.writeheader();w.writerows(records)
def write_json(path,data):
 p=BASE/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2,ensure_ascii=False,sort_keys=True)+'\n')
def iso(s):return isinstance(s,str) and bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}',s))
def year_group(y):
 if y is None:return 'Unknown date'
 if y<1862:return '1789–1861'
 if y<1907:return '1862–1906'
 if y<1937:return '1907–1936'
 if y<1990:return '1937–1989'
 return '1990–2026'

# Clean population layers: avoid treating source rows, signed documents, or 'all issued' as equivalent.
legacy_counts=collections.Counter(r['population_class'] for r in included)
units=[]
for r in unique:
 i=r['instrument_id'];o=orderrows[i];units.append({'id':i,'bibliographic_class':r['population_class'],'included_in_bibliography':1,'deduplicated_document_proxy':1,'document_authentication':'unadjudicated','presidential_signer_verification':'unadjudicated','signer_capacity':'unadjudicated','presidential_delegation':'unadjudicated','original_document_hash':None,'date_source_type':'stage13_projected_source_or_signing','date_effective':o['year'],'year_group':year_group(o['year']),'substantive_status_inherited':r['substantive_effect']})
write_csv('CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv',units)
fr=list(conn.execute("select instrument_id from observations where source_kind='FEDERAL_REGISTER_BULK'"))
frids=[r[0] for r in fr]
write_json('CENSUS/PUBLISHED_FR_ONLY_SOURCE_FRAME.json',{'raw_FR_bulk_source_rows':len(frids),'unique_source_row_identity_labels':len(set(frids)),'working_unique_document_proxies_matched':sum(orderrows[x]['include_unique'] for x in set(frids)),'source_year_span':'1937-2026 October collection','limitations':['This covers the captured Federal Register export, not all issued presidential EOs under 44 USC 1505.','Internal-only and never-published order texts remain possible.','The label-level proxy count can be smaller than source rows because of duplicates and suffix normalization.']})
write_json('CENSUS/POPULATION_ESTIMANDS.json',{
 'cutoff':CUTOFF,'estimands':[
 {'name':'bibliographic_identities','value':14973,'truth_claim':'project-admitted source identities only, not proven physical presidential documents','is_national_universe':False},
 {'name':'deduplicated_document_proxies','value':14972,'truth_claim':'analytical proxy after one EO7933A suffix-case duplicate; physical distinctness still open','is_national_universe':False},
 {'name':'original_physically_authenticated_presidential_instruments','value':None,'truth_claim':'not yet census-verified; cannot compute total','is_national_universe':False},
 {'name':'all_actual_presidential_executive_orders_1789_through_cutoff','value':None,'truth_claim':'unknown; early unnumbered historical universe not exhaustively identifiable','is_national_universe':False}
 ],'classes_included':dict(legacy_counts),'excluded_unverified_unnumbered_references':'>1500 Lord bibliography entries according to its own preface; specific number of distinct accepted new physical instruments not yet known','post_1937_publication_limitation':'44 USC 1505 exempts internal-only and nongeneral instruments from mandatory FR publication','source_barrier':'No estimate of all actual orders can be obtained by adding numbered labels or source-row appearances','original_populations_retained':{'stage11_all_rows':len(rows),'stage11_included':len(included)}})
# Authorship source-aware attribution: court confirms Polk-issued transactions, does not replace signatures.
auth=[
 dict(id='EO:3016C',signing_date='1919-02-26',signer_attribution='Frank L. Polk',source_basis='U.S. v. Chemical Foundation, 272 U.S. 1 (1926), opinion describes Polk order Feb. 26, 1919',presidential_authority='delegated TWEA section 12 via President Wilson order 1918-12-03',instrument_identity='retrospective numbered-index matching by date and subject',proof_of_signed_original='NOT_YET_AUTHENTICATED',membership_action='HOLD_PRESIDENT_SIGNED_SUBFRAME; KEEP_NUMBERED_BIBLIOGRAPHY',evidence_url='https://supreme.justia.com/cases/federal/us/272/1/'),
 dict(id='EO:3016K',signing_date='1919-04-05',signer_attribution='Frank L. Polk',source_basis='U.S. v. Chemical Foundation, 272 U.S. 1 (1926), opinion describes Polk order Apr. 5, 1919',presidential_authority='delegated TWEA section 12 via President Wilson order 1918-12-03',instrument_identity='retrospective numbered-index matching by date and subject',proof_of_signed_original='NOT_YET_AUTHENTICATED',membership_action='HOLD_PRESIDENT_SIGNED_SUBFRAME; KEEP_NUMBERED_BIBLIOGRAPHY',evidence_url='https://supreme.justia.com/cases/federal/us/272/1/'),
 dict(id='EO:3016N',signing_date='1919-04-18',signer_attribution='UNKNOWN_UNTIL_ACTUAL_INSTRUMENT',source_basis='numbered index names sale to Ludwig Vogelstein, but the Chemical Foundation opinion does NOT identify this order',presidential_authority='UNKNOWN; candidate delegated authority only',instrument_identity='retrospective numbered-index; signature not inspected',proof_of_signed_original='NOT_YET_AUTHENTICATED',membership_action='HOLD_SIGNER_AND_AUTHORITY; KEEP_NUMBERED_BIBLIOGRAPHY',evidence_url='')]
write_csv('CENSUS/3016_C_K_N_AUTHORSHIP_AUDIT.csv',auth)
# Source catalog leads are not EO identities. Keep reliability flags at page granularity.
leads=list(csv.DictReader(LORD.open())); pg=collections.Counter(int(x['pdf_page']) for x in leads)
write_json('CENSUS/LORD_ACQUISITION_QA.json',{'historical_volume':'List and Index of Presidential Executive Orders (Unnumbered Series), 1789-1941 (1943)','source_file_sha256':leads[0]['source_pdf_sha256'],'automated_month_line_markers':len(leads),'pages_with_at_least_one_marker':len(pg),'page_min':min(pg),'page_max':max(pg),'date_column_leads_without_document_confirmation':len(leads),'rule':'zero accepted additions to validated orders until individual source-to-instrument matching and authorship; marker count is not actual number of EOs','warning':'multiple orders per row, OCR loss, undated source references and early presidential endorsements make source-line identity indeterminate'})
write_csv('CENSUS/LORD_PAGE_GEOGRAPHY_QUEUE.csv', [{'pdf_page':p,'date_markers':pg[p],'recheck_priority':(0 if pg[p]>=4 else (1 if pg[p]>=1 else 2)),'page_review_state':'UNREVIEWED','source':'1943 Lord scanned volume'} for p in range(23,249)])
# Relationship chronology: an earlier EO cannot be the actor that amends/revokes a later EO.
edges=[dict(r) for r in conn.execute('select edge_id,actor,predecessor,relation,asof,source_url,quarantined,quarantine_reason,statement from relationships')]
chronology=[];unclear=[]
for e in edges:
 a=orderrows.get(e['actor']);b=orderrows.get(e['predecessor'])
 ad=a['signing_date'] if a else None;bd=b['signing_date'] if b else None
 if iso(ad) and iso(bd) and ad<bd and e['relation'] in ('amendment','express_revocation_claim','express_supersession_claim','express_rescission_claim'):
  chronology.append({'edge_id':e['edge_id'],'actor':e['actor'],'actor_date':ad,'predecessor':e['predecessor'],'predecessor_date':bd,'relation':e['relation'],'upstream_quarantined':e['quarantined'],'stage15_action':'SUPPRESS_FROM_ANALYTIC_GRAPH','source_url':e['source_url'],'claim_excerpt':(e['statement'] or '')[:260]})
write_csv('AUDIT/RELATIONSHIP_CHRONOLOGY_VIOLATIONS.csv',chronology)
leak=[x for x in chronology if x['upstream_quarantined']==0]
# All risk labels are lead-generation only, never adverse status determinations.
expected_risks=[
 ('R01_AUTHORITY_VS_FOOTPRINT','Program/authority termination may leave independent legal clauses','NIRA/industrial codes or wartime suspensions'),
 ('R02_FORMAL_EVENT_VS_FIRST_CAUSE','Later revocation supplies at most an upper bound unless all operative scopes are historically traced','known NO and source revocation bound'),
 ('R03_AMENDMENT_HOST_ATTRIBUTION','Order may amend a continuing host; amendment footprint must be independently reconstructed','amender reference or amending title'),
 ('R04_UNEXERCISED_PERMISSION','Grant, sale or appointment may not be proved exercised/exhausted','permissions and sales with no episode breakdown'),
 ('R05_PROGRAM_DISAPPEARANCE','Abolition of program or office may leave saved rights or independent legal consequences','civil service, retirement, land status, board family'),
 ('R06_COMPLETED_TASK_NOT_WHOLE_END','Finished temporary task does not necessarily extinguish every clause or ancillary right','boards/committee/inspection/closing with no episode breakdown'),
 ('R07_EDITORIAL_SILENCE','Index/codification omissions or dated annotations cannot prove modern legal cessation','historical compiler-reliant NO or incomplete provenance')]
write_csv('LEGAL/SEVEN_SHARED_FAILURE_MODES.csv',[{'rule_id':x[0],'hazard':x[1],'screen_basis':x[2],'automated_decision':'REVIEW_LEAD_ONLY','status_override_allowed':'NEVER'} for x in expected_risks])
risk_flags=[];rct=collections.Counter();sampled_examples={}
for r in unique:
 if r['substantive_effect']!='no':continue
 i=r['instrument_id']; title=(r.get('title') or '').lower();episodes=r.get('operative_episodes') or []
 me=r.get('cessation_mechanism');first=r.get('first_cessation_date');last=str(r.get('last_effect_end_date',''));gr=r.get('evidence_grade') or ''
 detected=[]
 if re.search(r'\bn\.?[ir]a\b|industrial recovery|fair competition|war[- ]?time|war work|workday|national recovery',title):detected.append('R01_AUTHORITY_VS_FOOTPRINT')
 if (me=='unknown' and ('not_later_than' in last or 'no later than' in last)) or ('firstcause_unknown' in str(me)):detected.append('R02_FORMAL_EVENT_VS_FIRST_CAUSE')
 if re.search(r'\bamend(?:ing|ed|ment)?\b|\bmodif(?:y|ying|ication)\b|\bsupplement\b',title):detected.append('R03_AMENDMENT_HOST_ATTRIBUTION')
 if (not episodes) and re.search(r'\bauthoriz(?:ed|ing|ation|e)\b|\bappoint(?:ment|ed|ing|s)?\b|\bsal(?:e|es)\b|\btransfer\b|\bcertif(?:y|ication)\b|\bpermission\b',title):detected.append('R04_UNEXERCISED_PERMISSION')
 if re.search(r'civil service|retirement|reserv(?:ation|e)|committee|board|commission|bureau|department',title):detected.append('R05_PROGRAM_DISAPPEARANCE')
 if (not episodes) and re.search(r'\bboard\b|\bcommittee\b|\binspection\b|\bclos(?:ing|ed|ure)\b|\bholiday\b|\bcommission\b',title):detected.append('R06_COMPLETED_TASK_NOT_WHOLE_END')
 if 'historical_index' in r['population_class'] and not episodes:detected.append('R07_EDITORIAL_SILENCE')
 if not episodes:detected.append('X01_WHOLE_ORDER_SCOPE_RECONSTRUCTION_ABSENT')
 if me=='unknown':detected.append('X02_FIRST_CAUSE_MECHANISM_UNRESEARCHED')
 if first=='unknown':detected.append('X03_FIRST_CAUSE_DATE_UNRESEARCHED')
 for d in detected:
  risk_flags.append({'instrument_id':i,'risk_rule':d,'source':'deterministic triage using frozen metadata; NOT adjudication','status':'SCREEN_FOR_INDEPENDENT_REVIEW'});rct[d]+=1
write_csv('LEGAL/CONSERVATIVE_RISK_SCREEN_NO_ORDERS.csv',risk_flags)
write_json('LEGAL/RISK_SCREEN_COUNTS.json',dict(rct))
# Explicit deterministic failure tests to guide large source-based batches.
valid_eo={'EO:14371','EO:6877','EO:13286','EO:12553','EO:2596','EO:2602','EO:3016C','EO:3016K','EO:3016N'}
example_provisions=[
 {'id':'EO:12553#REVOCATION_SCHEDULE','parent':'EO:12553','clause_type':'completed_disposition','ever_operative':'yes','currently_normative':'no_under_TC07','lasting_consequence':'yes_subject_to_current_attribution','trigger':'immediate_effect','first_cessation':'unknown_or_completed_action','source_ref':'1986-02-25 order text; 386 references enumerated, not proof all predecessor scope ended','purpose':'TC07 vs enduring effect'},
 {'id':'EO:2596#1917_WAIVER','parent':'EO:2596','clause_type':'exception_to_EO9','ever_operative':'yes_via_1917_command','currently_normative':'no_candidate_not_reaudited','lasting_consequence':'unknown','trigger':'wartime_appointment_precondition','first_cessation':'UNKNOWN; 1921 revocation and 1968 insofar-as cancellation distinct','source_ref':'EO2596 1917; EO3461 1921; EO11408 1968','purpose':'first-cause, partial scope and savings'},
 {'id':'EO:2602#ELIGIBLE_LIST','parent':'EO:2602','clause_type':'appointment_permission_and_rights','ever_operative':'yes_as_authorizing_rule','currently_normative':'no_candidate_not_reaudited','lasting_consequence':'historical appointments and rights require separate legal source investigation','trigger':'adoption_of_state_eligibility_list','first_cessation':'UNKNOWN; investigate EO3461 1921 and saved incumbent eligibility','source_ref':'EO2602 April1917; EO3461 1921','purpose':'saved rights vs extinguished permissions'},
 {'id':'EO:6877#WOOL_BOARD','parent':'EO:6877','clause_type':'time_limited_rule_amended','ever_operative':'yes_reported','currently_normative':'no_current_baseline','lasting_consequence':'unknown','trigger':'1934_issuance','first_cessation':'unknown; original 1935-02-01 end extended by EO6955-A','source_ref':'EO6877; EO6955-A','purpose':'amended expiration changes causal coding'},
 {'id':'EO:13286#SECTION22','parent':'EO:13286','clause_type':'host_amendment','ever_operative':'yes','currently_normative':'yes_supported_by_stage13_postkey_research','lasting_consequence':'yes','trigger':'2003_issuance','first_cessation':'still_active_as_of_cutoff','source_ref':'EO12978 + 31 CFR 536.312 as of 2026-10-14','purpose':'TC09 attribution'},
 {'id':'EO:14371#OFFICE_CLOSING','parent':'EO:14371','clause_type':'dated_performance','ever_operative':'yes','currently_normative':'no_current_baseline','lasting_consequence':'unknown_rights','trigger':'2025-12-24_and_2025-12-26','first_cessation':'2025-12-27 for only two office closure obligations; residual unclosed','source_ref':'EO14371 signed 2025-12-18','purpose':'original finite mandate vs residual'}]
write_csv('LEGAL/SEEDED_OPERATIVE_EPISODE_EXAMPLES.csv',example_provisions)
write_json('LEGAL/OPERATIONAL_STATE_CODEBOOK_DRAFT.json',{
 'release_status':'RESEARCH_PROJECTION_ONLY; frozen codebook 2.0.0 remains controlling; no historical status promotion',
 'document_identity':{'signer':'president|delegate|other|unknown','capacity':'direct_presidential|express_order|delegated_power|editorial_source|unknown','physical_manuscript':'authenticated|secondary_only|unknown'},
 'ever_operative_states':['not_researched','entered_substantive_operation','conditional_never_activated','hortatory_only','invalid_at_inception_established','unknown'],
 'present_normative_effect':['yes','no','indeterminate'],
 'enduring_legal_consequence':['confirmed_current_legal_relation','only_historical_result','historical_influence_without_current_attribution','unknown'],
 'attribution':['direct_continuing_source_EO','amended_host_with_traceable_current_norm','later_reauthorizing_independent_source','later_saving_clause_independent_right','historical_dispositive_consequence','unknown'],
 'temporal_state':['not_yet_effective','operative','dormant_revivable','terminated','revived','never_activated','indeterminate'],
 'first_cause_type':['under_original_terms','later_amendment_imposed_condition','later_presidential','legislative','regulatory','judicial','completion_of_task','never_activated','unresolved'],
 'historical_evidence_dates':['exact','not_later_than','not_earlier_than','interval','date_unknown'],
 'fields_required_for_any_final_causal_claim':['signed_identity','original_full_operative_footprint_or_exact_adjudicated_substitute','effective_date','operative_scope','actor_and_beneficiary','later_events_in_time_order','saved_rights','revisions_and_revivals','first_date_evidence','decision_rationale_and_external_source'],
 'rule':'A whole-order YES can contain multiple terminated episodes; a whole-order NO can have zero, one, or many preceding operative episodes; never infer first cause from last formal revocation.'})

# Mechanism and chronology progress: exact dates vs nonscalar bounding statements.
cause_rows=[]
for r in included:
 if r['substantive_effect']!='no':continue
 date=r.get('first_cessation_date','unknown');mech=r.get('cessation_mechanism','unknown')
 datekind='date_unknown' if date=='unknown' else ('exact_candidate_not_source_certified' if iso(date) else 'other_or_bound_not_exact')
 if mech=='unknown':mk='unresearched_or_unresolved'
 elif 'firstcause_unknown' in str(mech) or 'firstcause_unknown' in str(mech).replace('_',''):mk='known_late_endpoint_only'
 else:mk='populated_not_necessarily_first_cause'
 cause_rows.append({'id':r['instrument_id'],'mechanism_field_status':mk,'first_cessation_date_field':str(date),'first_date_kind':datekind,'last_effect_end_date_raw':str(r.get('last_effect_end_date'))[:140],'cleanup_after_cessation_raw':str(r.get('cleanup_after_cessation'))[:140],'episodes_n':len(r.get('operative_episodes') or [])})
write_csv('CAUSAL/NO_ORDERS_EVIDENCE_COMPLETENESS.csv',cause_rows)
classified=collections.Counter(r['substantive_effect'] for r in included);unique_class=collections.Counter(r['substantive_effect'] for r in unique)
mech_n=sum(x['mechanism_field_status']!='unresearched_or_unresolved' for x in cause_rows)
date_n=sum(x['first_date_kind']!='date_unknown' for x in cause_rows)
exact_n=sum(x['first_date_kind']=='exact_candidate_not_source_certified' for x in cause_rows)
joint_n=sum(x['first_date_kind']!='date_unknown' and x['mechanism_field_status']!='unresearched_or_unresolved' for x in cause_rows)
missing_episodes=sum(not r.get('operative_episodes') for r in unique if r['substantive_effect'] in ('yes','no'))
progress={'cutoff':CUTOFF,'source_data_stage':'frozen stage11 with stage14 identity de-dup and historical date projection','stage11_ledger_rows':len(rows),'stage11_included':len(included),'working_unique_proxy_n':len(unique),'substantive_status_count_stage11':dict(classified),'substantive_status_count_unique':dict(unique_class),'whole_order_status_determinate':unique_class['yes']+unique_class['no'],'whole_order_status_coverage_pct':100*(unique_class['yes']+unique_class['no'])/len(unique),'substantive_NO_count':len(cause_rows),'NO_mechanism_field_populated':mech_n,'NO_first_date_field_populated':date_n,'NO_first_date_exact_format_candidates_only':exact_n,'NO_both_fields_populated':joint_n,'NO_mechanism_populated_pct_of_NO':100*mech_n/len(cause_rows),'NO_mechanism_populated_pct_of_working_bibliography':100*mech_n/len(unique),'ever_operative_verified_population_fraction':None,'source_authenticated_full_causal_episodes_fraction':None,'determinate_order_no_recorded_episodes_count':missing_episodes,'uncertainty':'Populated date or mechanism is not necessarily an independently proven first legal cessation. Percentages are research metadata, not scholarly causal result.'}
write_json('CAUSAL/INDEPENDENT_PROGRESS_METRICS.json',progress)
# Separate representative sampling from accepted-decision error tests.
# Stage14 BLIND_60 audits only determinate cases; new sample draws from full working inventory, including UNKNOWN.
# Stratify by period x bibliographic source class; allocate samples proportional to sqrt size (rare class oversampled), weights N/n.
groups=collections.defaultdict(list)
for r in unique:
 o=orderrows[r['instrument_id']];st=(year_group(o['year']),r['population_class']);groups[st].append(r)
rng=random.Random(SEED)
# Sample 120 stratified (size permitting) with guaranteed >0 per non-empty stratum, then distribute by sqrt size.
N=120;alloc={st:1 for st in groups}
while sum(alloc.values())<N:
 # Proportional shortfall to sqrt(Nstratum); stable ties by key
 scores=[((len(groups[st])**.5)/alloc[st],str(st),st) for st in groups if alloc[st]<len(groups[st])]
 if not scores:break
 scores.sort(reverse=True);alloc[scores[0][2]]+=1
sample=[]
for st in sorted(groups):
 arr=sorted(groups[st],key=lambda z:z['instrument_id']);k=alloc[st]
 for r in rng.sample(arr,k):
  i=r['instrument_id'];sample.append({'id':i,'era':st[0],'source_class':st[1],'stratum_N':len(arr),'stratum_sample_n':k,'inclusion_probability':round(k/len(arr),10),'design_weight':round(len(arr)/k,8),'source_original_required':'YES','blind_review_id':'PREVALENCE-' + str(len(sample)+1).zfill(3),'release_status':'UNREVIEWED','answer_key_held_separately':'YES'})
write_csv('STATISTICS/STRATIFIED_POPULATION_SAMPLE_120_BLIND.csv',sample)
# Separate answer key: sealed in distinct subdirectory (no status in blind file).
write_csv('STATISTICS/SEALED_POPULATION_SAMPLE_BASELINE_120.csv',[{'id':x['id'],'stage11_status':rmap[x['id']]['substantive_effect'],'year_from_stage14':orderrows[x['id']]['year'],'evidence_grade':rmap[x['id']]['evidence_grade']} for x in sample])
framecounts=collections.Counter((r['year_group'],r['bibliographic_class']) for r in units)
write_csv('STATISTICS/SAMPLING_STRATA_WEIGHTS.csv',[{'era':st[0],'source_class':st[1],'frame_N':len(g),'sample_n':alloc[st],'selection_probability':alloc[st]/len(g),'weight':len(g)/alloc[st]} for st,g in sorted(groups.items())])
# Causation design controls (no premature Kaplan-Meier fit to targeted YES/NO convenience samples).
(BASE/'STATISTICS/SURVIVAL_ANALYSIS_PROTOCOL.md').write_text('''# Inference design: duration and competing risks\n\n**Frozen research cutoff:** 2026-10-14. No national survival estimate is licensed by the current convenience-classified statuses.\n\n## Population\n\nUse a clearly bounded, document-reconciled era (prefer contemporaneously numbered published EOs), then draw a stratified probability sample of **all** documents, including currently UNKNOWN; see the 120-case draw and design weights. Pre-1937 unnumbered coverage must be reported as observed lower-bound bibliographies, not a universal denominator. Consider unpublished orders under 44 USC §1505.\n\n## Time origin and endpoint\n\nDistinguish signing, first legal effectiveness, amendment, first cessation, last cessation, dormancy, revival, and formal revocation. Study order and provision/episode as distinct estimands. A nonoperative or never-activated clause does not contribute a traditional event-at-risk interval. A currently operative or unresolved clause with proved prior onset and no proved termination is administratively right-censored at cutoff; a clause with unproven origin or effect cannot be casually called censored.\n\n## Survival estimators\n\nUse issuance cohort and date at risk. Treat expirations in original terms, later-imposed terms, affirmative executive termination, statute, regulation, judicial intervention, and other termination as competing first causes where supported; use cumulative-incidence functions rather than equating 1-Kaplan-Meier with competing event risks. Record time-varying amendments, statutory transitions, revivals/multistate models and left truncation where documents enter the observable archive later than issuance. Avoid unweighted estimates from selected statuses. Stratified weights and error/nonresponse sensitivity must be included. Do not classify the date of a late housekeeping revocation as first cessation.\n\n## Publication gate\n\nNo estimates until: identity sampling frame audited; all sample originals and amendments sourced; provision-level episodes reconstructed; competing event type and date adjudicated; missingness and source failure quantified; weighted uncertainty intervals calculated.\n''')
# Temporal cleanup and source graph guard: identify reversals already quarantined and escaped.
write_json('AUDIT/RESEARCH_GRAPH_RELEASE_GATES.json',{'total_relationship_edges':len(edges),'upstream_quarantined':sum(x['quarantined'] for x in edges),'chronologically_backward_edges_all':len(chronology),'chronologically_backward_edges_NOT_upstream_quarantined':len(leak),'escaped_edges':[x for x in leak], 'required_gate':'Reject any actor-to-predecessor ending/amendment edge where both instrument dates are known and actor precedes predecessor; do not infer causality from publication or editorial-asof dates. For amendment metadata marked Amended by, reverse actor from index-row subject to later amender and re-authenticate original relationship.','publication_scope_warning':'1889/1989 NARA editorial source-as-of is not individual event date.'})

# SQLite sidecar normalized research fields + risk flags. Keeps immutable main graph unchanged.
side=BASE/'AUDIT/EO_STAGE15_SCHEMA_AND_RISK_SIDECAR.sqlite'
if side.exists():side.unlink()
db=sqlite3.connect(side)
db.executescript('''CREATE TABLE base_identity (id TEXT PRIMARY KEY, source_class TEXT, era TEXT, bibliographic_included INT, proxy_unique INT, physical_document_authenticated INT, signer TEXT, signer_capacity TEXT, delegated_authority TEXT, original_hash TEXT, inherited_status TEXT);
CREATE TABLE review_risk(id TEXT,rule_id TEXT,review_state TEXT,PRIMARY KEY(id,rule_id));
CREATE TABLE operative_episode (episode_id TEXT PRIMARY KEY,instrument_id TEXT,clause_kind TEXT,ever_operative TEXT,effective_start TEXT,current_normative TEXT,lasting_legal_consequence TEXT,attribution TEXT,first_cause TEXT,source_description TEXT,FOREIGN KEY(instrument_id) REFERENCES base_identity(id));
CREATE TABLE directed_event_guard(edge_id INTEGER PRIMARY KEY,actor TEXT,predecessor TEXT,source_relation TEXT,source_url TEXT,chronology_violation INT,upstream_quarantined INT,stage15_suppress INT);
CREATE TABLE authorship_special(id TEXT PRIMARY KEY,signer_attribution TEXT,authority TEXT,original_signature_state TEXT,source_url TEXT);
CREATE TABLE research_requirements(requirement_id TEXT PRIMARY KEY,criterion TEXT,status TEXT,evidence_file TEXT,still_needed TEXT);
''')
db.executemany('insert into base_identity values(?,?,?,?,?,?,?,?,?,?,?)',[(u['id'],u['bibliographic_class'],u['year_group'],1,1,None,None,None,None,None,u['substantive_status_inherited']) for u in units]);
db.executemany('insert into review_risk values(?,?,?)',[(r['instrument_id'],r['risk_rule'],r['status']) for r in risk_flags]);
db.executemany('insert into operative_episode values(?,?,?,?,?,?,?,?,?,?)',[(x['id'],x['parent'],x['clause_type'],x['ever_operative'],x['trigger'],x['currently_normative'],x['lasting_consequence'],None,x['first_cessation'],x['source_ref']) for x in example_provisions]);
db.executemany('insert into directed_event_guard values(?,?,?,?,?,?,?,?)',[(e['edge_id'],e['actor'],e['predecessor'],e['relation'],e['source_url'],int(any(x['edge_id']==e['edge_id'] for x in chronology)),e['quarantined'],int(e['quarantined'] or any(x['edge_id']==e['edge_id'] for x in chronology))) for e in edges]);
db.executemany('insert into authorship_special values(?,?,?,?,?)',[(x['id'],x['signer_attribution'],x['presidential_authority'],x['proof_of_signed_original'],x['evidence_url']) for x in auth]);
db.commit();db.close()
# Outcome matrix verbatim scope: each textual critique converted into acceptance criteria.
issues=[
('1.1','All 1789-2026 EO total distinct from bibliographic IDs','PARTIAL','CENSUS/POPULATION_ESTIMANDS.json','A complete count is unknowable without additional historical manuscripts; retain unknown full universe'),
('1.2','Only 19 documented unnumbered source rows cannot stand in for historically unnumbered EOs','PARTIAL','CENSUS/LORD_ACQUISITION_QA.json','Resolve >1500 source entries into signed documents using originals; current 1023 markers not complete'),
('1.3','44 USC §1505 excludes internal-only orders from mandatory publication','IMPLEMENTED_AS_SCOPE_GUARD','CENSUS/POPULATION_ESTIMANDS.json','Ascertain unpublished pre/post1937 records before any full-count claim'),
('1.4','Keep numbered identities, physical instruments, all actually issued orders as different totals','IMPLEMENTED_AS_DATA_MODEL','CENSUS/POPULATION_ESTIMANDS.json','Physical and all-issued totals remain unknown'),
('1.5','Resolve duplicate/suffix/group identity and partial cross-source coverage','PARTIAL','CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv','Authenticate 3016-family and Lord dates; crosswalk per-administration with APP'),
('2.1','EO3016C delegated author attribution','PARTIAL','CENSUS/3016_C_K_N_AUTHORSHIP_AUDIT.csv','Physically inspect the signed document; opinion supports Polk issuance'),
('2.2','EO3016K delegated author attribution was missing','PARTIAL','CENSUS/3016_C_K_N_AUTHORSHIP_AUDIT.csv','Physically inspect indexed EO 3016-K original; opinion supports Polk issuance'),
('2.3','EO3016N signature and delegated authority must not be guessed from other Polk orders','OPEN_HOLD','CENSUS/3016_C_K_N_AUTHORSHIP_AUDIT.csv','Find EO3016N original/signature; distinct Vogelstein transaction'),
('2.4','Track actual signer, delegated power, Presidential signature vs numbered membership','IMPLEMENTED_AS_DATA_MODEL','AUDIT/EO_STAGE15_SCHEMA_AND_RISK_SIDECAR.sqlite','Population-wide field backfill awaits originals'),
('3.1','TC07 spent repeals vs TC09 operative amendments vs TC06 durable status inconsistencies','PARTIAL','LEGAL/OPERATIONAL_STATE_CODEBOOK_DRAFT.json','Independent doctrinal audit and broad outcome sensitivity before final rule'),
('3.2','Present commands/constitutive statuses separate from enduring legal consequences','IMPLEMENTED_AS_DATA_MODEL','LEGAL/OPERATIONAL_STATE_CODEBOOK_DRAFT.json','Do not recode current statuses until attribution rule adopted'),
('3.3','Repeal A, amending B, land C all may change legal regime indefinitely','PARTIAL','LEGAL/SEEDED_OPERATIVE_EPISODE_EXAMPLES.csv','Test land reservation and final property transfer in blind doctrinal panel'),
('3.4','Property transfers and saved rights need stable attribution convention','OPEN_HOLD','LEGAL/OPERATIONAL_STATE_CODEBOOK_DRAFT.json','Legal expert review and property instrument primary-source tracing'),
('3.5','Count both current normative effects and legal consequences under credible theories','PARTIAL','LEGAL/OPERATIONAL_STATE_CODEBOOK_DRAFT.json','Re-adjudicate representative original and host text sample; compute whole-inventory ranges'),
('5.1','Order must have ever become operative (including never operative cases)','IMPLEMENTED_AS_DATA_MODEL','LEGAL/OPERATIONAL_STATE_CODEBOOK_DRAFT.json','Populate per instrument on primary evidence before causal tallies'),
('5.2','Hortatory, conditional-untriggered, and invalid ab initio need separate states','IMPLEMENTED_AS_DATA_MODEL','LEGAL/OPERATIONAL_STATE_CODEBOOK_DRAFT.json','Do not equate judicial invalidity with no historical effect'),
('5.3','Track actual effective date, fulfillment, dormant authority, revival','IMPLEMENTED_AS_DATA_MODEL','LEGAL/OPERATIONAL_STATE_CODEBOOK_DRAFT.json','Episode data still sparse and evidentiary'),
('5.4','Whole-order YES can contain expired provisions; first cessation not only in NO','PARTIAL','LEGAL/SEEDED_OPERATIVE_EPISODE_EXAMPLES.csv','Generate all provision timelines for YES as well as NO after originals recovered'),
('5.5','Provision/operative episode-level history required beneath headline','PARTIAL','AUDIT/EO_STAGE15_SCHEMA_AND_RISK_SIDECAR.sqlite','Existing determined record lacks episode details in majority of cases'),
('6.1','Status coverage 2515 / 14973 vs cause progress not same metric','IMPLEMENTED_AS_REPORTING','CAUSAL/INDEPENDENT_PROGRESS_METRICS.json','Do not treat status coverage as historical answer'),
('6.2','2216 / 2322 mechanism unknown; 2223 / 2322 first dates unknown','IMPLEMENTED_AS_REPORTING','CAUSAL/INDEPENDENT_PROGRESS_METRICS.json','Populate independently supported exact cause, not merely later bounds'),
('6.3','Later revocation not original first cessation; classify chronology','PARTIAL','AUDIT/RESEARCH_GRAPH_RELEASE_GATES.json','Resolve causal histories for 2322 NO and expired provisions of active orders'),
('6.4','Issuance cohorts, delayed observation, censoring, revival, competing risks','IMPLEMENTED_AS_DESIGN','STATISTICS/SURVIVAL_ANALYSIS_PROTOCOL.md','Complete rigorous sample before fitting survival model'),
('6.5','Representative population sample independent of selective determinate review','IMPLEMENTED_AS_SAMPLING_FRAME','STATISTICS/STRATIFIED_POPULATION_SAMPLE_120_BLIND.csv','Independently audit sampled identity/document/status; no estimates yet'),
('7.1','Authority termination versus disappearance of all effects (NIRA/war)','IMPLEMENTED_AS_SCREEN','LEGAL/CONSERVATIVE_RISK_SCREEN_NO_ORDERS.csv','Adjudicate all clauses before concluding any flagged order has no effect'),
('7.2','Subsequent revocation vs first cessation (3461/12553/retirement)','IMPLEMENTED_AS_SCREEN','LEGAL/CONSERVATIVE_RISK_SCREEN_NO_ORDERS.csv','Build earlier event timeline including cause proof'),
('7.3','Wrong source attribution for amendments/repealers/savings','IMPLEMENTED_AS_SCREEN','LEGAL/CONSERVATIVE_RISK_SCREEN_NO_ORDERS.csv','Map exact host version and saving law'),
('7.4','Assume granted permission exercised (appointments/sales)','IMPLEMENTED_AS_SCREEN','LEGAL/CONSERVATIVE_RISK_SCREEN_NO_ORDERS.csv','Acquire administrative completion or alternative extinguishment'),
('7.5','Program disappears but incumbent/land/institution rights survive','IMPLEMENTED_AS_SCREEN','LEGAL/CONSERVATIVE_RISK_SCREEN_NO_ORDERS.csv','Adjudicate property/beneficiary/savings chains'),
('7.6','Completed task does not end every clause and residual','IMPLEMENTED_AS_SCREEN','LEGAL/CONSERVATIVE_RISK_SCREEN_NO_ORDERS.csv','Review all original sections including residual duties'),
('7.7','Editorial/archival silence cannot prove 2026 cessation','IMPLEMENTED_AS_SCREEN','LEGAL/CONSERVATIVE_RISK_SCREEN_NO_ORDERS.csv','Acquire actual original and successor sources; screening not answer'),
('7.8','Shared-source correlated model reviews must not masquerade as independent truth','PARTIAL','STATISTICS/STRATIFIED_POPULATION_SAMPLE_120_BLIND.csv','Carry out two-level human/independent source-blind review of actual cases'),
('EXTRA.1','Stage14 reverse-date relationship survived quarantine','IMPLEMENTED_AS_GRAPH_GUARD','AUDIT/RELATIONSHIP_CHRONOLOGY_VIOLATIONS.csv','Confirm corrected direction in source, do not auto-reverse when source metadata ambiguous'),
('EXTRA.2','Original 1943 cohort false positives','VERIFIED_IN_STAGE13','../EO_STAGE13_FOUNDATIONAL_VALIDATION_2026-10-16/AUDIT/ORIGINAL_1943_FLAG_ERROR_VERIFIED.json','Original record kept; corrected in prior overlay'),
('EXTRA.3','513 Stage14 omission of already-known National Archives successor references','IMPLEMENTED_AS_GRAPH_GUARD','AUDIT/RECOVERED_MISSING_NARA_SUCCESSOR_CANDIDATES.csv','512 chronology-compatible references restored as research candidates only; primary documents and scope still unreviewed'),
('EXTRA.4','Regenerate complete research dependency priorities after relationship recovery','IMPLEMENTED_AS_GRAPH_GUARD','AUDIT/REBUILT_HIGH_LEVERAGE_ENDING_SOURCE_QUEUE.csv','Prove shared source once before legal expansion; do not count candidates as determinations')]
write_csv('AUDIT/COMPLETE_ISSUE_CLOSURE_MATRIX.csv',[{'issue_id':a,'verbatim_problem_or_precise_acceptance_test':b,'status':c,'evidence_artifact':d,'remaining_required_to_close':e} for a,b,c,d,e in issues]);
# status breakdown
status_ct=collections.Counter(x[2] for x in issues)
summary={'requirements_n':len(issues),'status_by_type':dict(status_ct),'stage14_relationship_chronology_escape_n':len(leak),'chronology_example':leak[0] if leak else None,'source_unverified_lord_leads':len(leads),'risk_screen_diagnostic_only':dict(rct),'det_no_with_no_episode':missing_episodes,'all_stage11_legal_labels_immutable':True,'scope':'Only audit framework and source-grounded selected cases; NOT complete historical census, legal validity audit or first-cause research'}
write_json('REPORTS/EXECUTION_SUMMARY.json',summary)
# Link issue matrix into sqlite
sdb=sqlite3.connect(side);sdb.executemany('insert into research_requirements values(?,?,?,?,?)',issues);sdb.commit();sdb.close()
print(json.dumps({'summary':summary,'progress':progress,'sample_n':len(sample)},indent=2)[:6500])
