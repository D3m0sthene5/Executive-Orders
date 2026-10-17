#!/usr/bin/env python3
"""Reproducible explicit case-specific transcriptions/decisions from cited publicly inspectable sources."""
import json,hashlib,pathlib
root=pathlib.Path(__file__).resolve().parent.parent; sources=[];f={'provisions':[],'transitions':[],'assessments':[],'catalogue':[]}
policy='3.0.0-research-stage17'
def source(num,url,subject=None,issuer='Institutional source hosting presidential text',date=None,grade='WEB_HOSTED_TRANSCRIPT_INDEPENDENTLY_VIEWED_ORIGINAL_BYTES_ABSENT',note='',excerpt='',local=0,content_sha=None):
 sources.append(dict(source_id=num,subject_id=subject,issuer=issuer,source_url=url,document_date=date,document_type='presidential executive order text or archival scan',transcript_grade=grade,local_original_bytes=local,stored_representation_sha=content_sha,source_excerpt=excerpt,acquisition_limit=note or 'Exact source URL examined online; local official scan not included in this release. Retain URL and verify against image for human approval.'))

def provision(eo,scope,src,text,orig,end,start=None,gap='No original signed scan retained; later amendments and accrued rights require reinspection.',grade='COMPLETE_SINGLE_PROVISION_HOSTED_TEXT_AI_REINSPECTED'):
 id='P17-'+eo.replace(':','_')+'-'+scope.replace(' ','_').replace('/','_').replace('(','').replace(')','').replace(',','').replace('.','')
 f['provisions'].append(dict(provision_id=id,instrument_id=eo,source_id=src,scope=scope,norm_text=text,valid_start=start,original_sunset=orig,known_sunset_end_exclusive=end,expected_2026_normative='expired_under_text_as_written',evidence_grade=grade,remaining_gap=gap));return id

def transition(pid,when,kind,actor,src,old,new,infer='INTERMEDIATE_EXTENSION',grade='EXACT_TEXT_SOURCE_SCOPED_AI_VERIFIED',note='No locally retained signed document; no claim about saved rights or policy continuity.'):
 f['transitions'].append(dict(transition_id='T17-'+str(len(f['transitions'])+1).zfill(3),affected_provision_id=pid,actor_id=actor,event_date=when,kind=kind,old_rule=old,new_rule=new,source_id=src,first_cause_inference=infer,causation_grade=grade,source_review_limit=note))

def assessment(id,status,source_ids,rationale,gaps,grade='INDEPENDENT_AI_SOURCE_INSPECTION_NOT_HUMAN_CERTIFIED'):
 f['assessments'].append(dict(assessment_id='A17-'+id.replace(':','_'),instrument_id=id,normative_status=status,enduring_consequences='possible_past_acts_preserved_not_current_authority',formal_disposition='not_yet_wholly_adjudicated',policy_continuity='unknown_or_independent',codebook_version=policy,review_grade=grade,reviewer_role='AI_SOURCE_REINSPECTION',rationale=rationale,source_ids_json=json.dumps(source_ids),remaining_gaps=gaps,human_certified=0))

# Actual original-order texts and later amendments at Harry S. Truman Presidential Library (NARA-administered).
for eo,date,excerpt in [
 ('10084','1949-10-12','shall cease to be effective on January 31, 1950'),
 ('10098','1950-01-25','shall cease to be effective on March 31, 1950'),
 ('10118','1950-03-27','shall continue in effect until June 30, 1950'),
 ('10136','1950-06-30','until August 31, 1950; section 302 until September 30, 1950'),
 ('10158','1950-08-31','sections 206 and 302 until October 31, 1950'),
 ('10174','1950-10-23','section 302 until January 31, 1951')]:
 source('TRUMAN-'+eo,f'https://www.trumanlibrary.gov/library/executive-orders/{eo}/executive-order-{eo}',subject='EO:'+eo,issuer='Harry S. Truman Presidential Library, National Archives and Records Administration',date=date,excerpt=excerpt)

host='EO:10084';section_groups=[
 ('other-1949-regulations','Titles II III and V except later explicitly saved authorities','1950-04-01'),
 ('sections-201e-204-501d','Career Compensation Act sections 201(e), 204, 501(d)','1950-09-01'),
 ('section-206','Career Compensation Act section 206','1950-11-01'),
 ('section-302','Career Compensation Act section 302','1951-02-01')]
for name,scope,end in section_groups:
 pid=provision(host,name,'TRUMAN-10084','Presidential adoption of pre-existing pay regulations under Titles II, III, V with subsequent scope-dependent expiration amendments','1950-02-01',end,'1949-10-01',gap='Scope mapping to every adopted regulation and saved individual benefit must be verified; post-1950 survival under independent statute may be outside original EO attribution.',grade='ORIGINAL_DIRECTIVE_PLUS_FIVE_AMENDING_TEXTS_AI_REINSPECTED')
 transition(pid,'1950-01-25','host_sunset_extension','EO:10098','TRUMAN-10098','1950-01-31','1950-03-31')
 if name!='other-1949-regulations':
  transition(pid,'1950-03-27','statutory_section_extension','EO:10118','TRUMAN-10118','1950-03-31','1950-06-30')
  if name=='sections-201e-204-501d':
   transition(pid,'1950-07-01','statutory_section_extension','EO:10136','TRUMAN-10136','1950-06-30','1950-08-31')
  elif name=='section-206':
   transition(pid,'1950-07-01','statutory_section_extension','EO:10136','TRUMAN-10136','1950-06-30','1950-08-31')
   transition(pid,'1950-09-01','statutory_section_extension','EO:10158','TRUMAN-10158','1950-08-31','1950-10-31')
  else:
   transition(pid,'1950-07-01','statutory_section_extension','EO:10136','TRUMAN-10136','1950-06-30','1950-09-30')
   transition(pid,'1950-09-01','statutory_section_extension','EO:10158','TRUMAN-10158','1950-09-30','1950-10-31')
   transition(pid,'1950-11-01','statutory_section_extension','EO:10174','TRUMAN-10174','1950-10-31','1951-01-31')
 transition(pid,end,'original_operative_authorization_sunset',host,'TRUMAN-10174' if name=='section-302' else ('TRUMAN-10158' if name=='section-206' else ('TRUMAN-10136' if name=='sections-201e-204-501d' else 'TRUMAN-10098')),'continued authority','prospective EO10084 authority ended at this date','FIRST_NORMATIVE_SUNSET','TEXTUAL_END_AFTER_DOCUMENTED_HOST_AMENDMENTS',note='This is first termination of this SCOPED regulatory group as an EO10084 authority, not first end of all parent policy or accrued claims.')
assessment(host,'indeterminate',['TRUMAN-'+x for x in ['10084','10098','10118','10136','10158','10174']],
 'Four scoped portions of EO10084 have documentary sunsets between March 1950 and January 1951, after FIVE amendments. No assertion of whole-order NO without verifying complete adopted-regulation scope and saved consequences.',
 'Original regulations incorporated from older executive and departmental rules not individually mapped to every applicable statutory provision.')
for eo in ['10098','10118','10136','10158','10174']:
 assessment('EO:'+eo,'indeterminate',['TRUMAN-'+eo,'TRUMAN-10174'],
 'Amending language and amended host sunset are documented; attribution of a spent amender versus surviving host text is TC07/TC09 definition-sensitive. The host regulated period ended by early 1951 on current amendment crosswalk.',
 'No independent original scan retained; original amender may have secondary provisions absent from excerpt and amendments must be reconstructed under alternative attribution rules.')

judge=[
 ('10035','1949-02-10','1949','1950-01-01','GOVINFO-FR10035','https://www.govinfo.gov/content/pkg/FR-1949-02-11/pdf/FR-1949-02-11.pdf','Luis Negron-Fernandez'),
 ('10097','1950-01-24','1950','1951-01-01','FRSCAN-10097','https://archives.federalregister.gov/issue_slice/1950/1/27/461-464.pdf','A. Cecil Snyder'),
 ('10188','1950-12-06','1951','1952-01-01','APP-10188','https://www.presidency.ucsb.edu/documents/executive-order-10188-designating-the-honorable-luis-negron-fernandez-acting-judge-the','Luis Negron-Fernandez'),
 ('10310','1951-12-10','1952','1953-01-01','APP-10310','https://www.presidency.ucsb.edu/documents/executive-order-10310-designating-the-honorable-cecil-snyder-act-under-certain','A. Cecil Snyder'),
 ('10517','1954-02-10','1954','1955-01-01','APP-10517','https://www.presidency.ucsb.edu/documents/executive-order-10517-designating-the-honorable-cecil-snyder-act-under-certain','A. Cecil Snyder'),
 ('10599',None,'1955','1956-01-01','GOVINFO-FR10599','https://www.govinfo.gov/content/pkg/FR-1955-03-16/pdf/FR-1955-03-16.pdf','A. Cecil Snyder')]
for eo,issued,year,end,sid,url,who in judge:
 grade='OFFICIAL_FR_DIGITAL_IMAGE_ONLINE_VIEWED_NO_LOCAL_BYTES' if sid.startswith(('GOVINFO','FRSCAN')) else 'UNIVERSITY_EDITORIAL_TRANSCRIPTION_CROSSCHECK_WITH_NARA_DATE'
 note='Text from official contemporaneous Federal Register issue inspected via web; original binary not copied to local release.' if sid.startswith(('GOVINFO','FRSCAN')) else 'University-hosted text; original contemporary Federal Register scan needs acquisition.'
 if eo=='10599':note+=' Source-date CONFLICT: NARA 1955 disposition says March 15, APP transcription says March 14; retain both pending image/date authentication.'
 source(sid,url,subject='EO:'+eo,issuer='Office of the Federal Register / GovInfo' if sid.startswith(('GOVINFO','FRSCAN')) else 'American Presidency Project (UCSB)',date=issued,grade=grade,note=note,excerpt='acting Judge ... during the year '+year)
 pid=provision('EO:'+eo,'annual_acting_judge_authorization',sid,'Conditional permission for '+who+' to act as federal district judge in Puerto Rico, expressly confined to calendar year '+year,end,end,'{}-01-01'.format(year),gap='No locally retained original scan; contemporaneous exercise and any saved validity of judicial acts require separate reconstruction.',grade='SINGLE_CLAUSE_COMPLETE_VIEWED_TEXT_WITH_OFFICIAL_DATE_CHECK')
 transition(pid,end,'express_calendar_year_sunset','EO:'+eo,sid,'permission operative within '+year,'permission prospective operation ends at start of following year','FIRST_NORMATIVE_SUNSET','AI_SCOPED_PROSPECTIVE_PERMISSION_EXPIRATION','This does not assert a particular exercise of judicial power or expiration of validity of judgments rendered.')
 assessment('EO:'+eo,'no',[sid],
 'Only original prospective grant allows '+who+' to act conditionally during year '+year+'; on its stated terms the permission ended on '+end+'. This concludes prospective normative operation, not collateral validity of judgments.',
 'No original signed PDF locally retained; no documented continuing residual command. Bounded historical disposition check, not exhaustive proof of all downstream legal consequences.')

for eo,date,dates,url in [
 ('9896','1947-10-02',['1947-10-10','1947-10-26'],'https://www.presidency.ucsb.edu/documents/executive-order-9896-display-the-flag-the-united-states-half-mast-honor-the-return-world'),
 ('11481','1969-09-10',['1969-09-11'],'https://www.presidency.ucsb.edu/documents/executive-order-11481-the-honorable-everett-mckinley-dirksen')]:
 sid='APP-'+eo;source(sid,url,subject='EO:'+eo,issuer='American Presidency Project (UCSB)',date=date,excerpt='explicit time-limited federal flag half-staff display',note='Full published transcription independently viewed; original signed binary not copied. Dates are explicit in order.')
 for day in dates:
  from datetime import date as dt,timedelta
  end=(dt.fromisoformat(day)+timedelta(days=1)).isoformat()
  pid=provision('EO:'+eo,'flag_halfstaff_'+day,sid,'Display national flag at half staff at specified government sites on '+day,day,end,day,gap='No distinct claim that private parties acquired any surviving right.',grade='SOURCE_TRANSCRIPTION_SCOPED_EXACT_DATE')
  transition(pid,end,'calendar_day_expiry','EO:'+eo,sid,'day-specific flag display duty','event no longer prospectively applicable','FIRST_NORMATIVE_SUNSET','DATED_CEREMONIAL_CLAUSE_TEXT_REINSPECTED')
 assessment('EO:'+eo,'no',[sid],'All original operative flag display dates had passed. No separate present authority identified.','Original scan not acquired; historic ceremony performance distinct from current normative effect.')

# The Clifford Lord source is a physically locally retained user-supplied scan, and page 23 is independently visually verified.
source('LORD1943_SCAN','https://www.loc.gov/item/43013029/',issuer='Clifford L. Lord, Historical Records Survey (1943); user-provided LOC digitization',grade='USER_PROVIDED_ORIGINAL_SCANNED_PRINTED_INDEX_PDF_SHA_VERIFIED',note='Original PDF image available as separate project Library source and Git LFS consolidated archive. Catalogue does NOT authenticate corresponding signed original instrument.',excerpt='Chronological entries 1789 and 1790 on scanned page 23.',local=1,content_sha='0553dd2318903af8fd4cdbb56140cd035f3bac52ec5420148307206940ab69e1')
for idx,date,title,note in [
 ('01','1789-06-08','Department heads asked for clear account of affairs','X Sparks 11; X Richardson Appendix 80. Form is presidential request to department heads; underlying signed paper unlocated.'),
 ('02','1789-10-06','Northwest Territory governor instructions regarding Wabash and Illinois Indians','American State Papers Indian Affairs I:96; X Richardson Appendix 81. Written original needs inspection.'),
 ('03','1789-10-13','Regulations for payment of Revolutionary War veterans pensions','Signed by Henry Knox, Secretary of War according to Lord; presidential authorization and signer/capacity need authentication.'),
 ('04','1790-08-28','Treasury Secretary authorized to borrow fourteen million dollars','Annals 2 Congress 1 session 1247; X Richardson Appendix 84. Cabinet correspondence/original order unknown.'),
 ('05','1790-08-28','Directions to Treasury Secretary for arranging government loan','Annals 2 Congress 1 session 1249; X Richardson Appendix 84. Same-day overlap with preceding authorizing note; cannot presume distinct original instrument.')]:
 f['catalogue'].append(dict(catalogue_key='LORD1943-P023-'+idx,source_id='LORD1943_SCAN',date_guess=date,title_excerpt=title,source_page=23,source_row_note=note,signer_status='UNVERIFIED_OR_DELEGATED_SIGNER',document_authenticated=0,candidate_state='UNNUMBERED_CATALOGUE_CANDIDATE_NOT_COUNTED',matched_existing_instrument=None,scope_note='No current stage16 instrument match established; 1789 and 1790 previously omitted from heuristic 1,023 date markers.'))

# Critical local-source absence is explicit; source list includes scan references not byte ownership claims.
(root/'sources'/'verified_web_source_references.json').write_text(json.dumps(sources,indent=2,ensure_ascii=False)+'\n')
(root/'sources'/'adjudicated_legal_facts.json').write_text(json.dumps(f,indent=2,ensure_ascii=False)+'\n')
print('sources',len(sources),'provisions',len(f['provisions']),'transitions',len(f['transitions']),'assessments',len(f['assessments']),'catalogue',len(f['catalogue']))
