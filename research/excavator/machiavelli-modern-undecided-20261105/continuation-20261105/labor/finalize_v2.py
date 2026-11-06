import json, pathlib, hashlib, re, fitz, datetime
R=pathlib.Path('.'); B=R/'research/excavator/machiavelli-modern-undecided-20261105/continuation-20261105/labor'
def H(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
S=json.loads((B/'SOURCE_FINDINGS.v2.json').read_text());S['schema']='eo-continuation-source-findings/v3';S['supersedes']='SOURCE_FINDINGS.v2.json';S['scope']='Producer source examination only. Custody pins do not authenticate sources or approve lifecycle conclusions.'
M=json.loads((B.parent/'SOURCE_MAP_001.json').read_text())['sources']; byurl={x['url']:x for x in M}
seen={'CADC2019':[6,20],'OPM20191004':[1],'OPM20210305':[1,2,3,5,11],'FLRA20230327':[1,3],'OPMCBA20181120':[1],'OPMCBA20200109':[1,2],'OPMFY2019':[1,3,4],'OPMRULE2020':[1],'OPMRULE2022':[1,16],'OPMFY2025':[1],'NTIAPET2020':[1,3,4]}
needles={'CADC2019':['We hold that the district court lacked','Order at 2-3','we vacate the district court’s judgment'], 'OPM20191004':['On October 3, 2019','hereby rescinded','originally issued on July 5'], 'OPM20210305':['All U.S. Office','All materials issued by the LRG','under its own statutory','Agency actions to implement any other requirements','July 13, 2020','December 17,'], 'FLRA20230327':['will be automatically extended','October 3, 2019','We remand the matter'], 'OPMCBA20181120':['sections of EO 13836','complete and attach two forms'], 'OPMCBA20200109':['announcing the release','supersedes and replaces','OPM is uploading'], 'OPMFY2019':['October 2020','preventing publication'], 'OPMRULE2020':['DATES: Effective','These revised','OPM anticipates proposing'], 'OPMRULE2022':['DATES: Effective','OPM discontinued'], 'OPMFY2025':['January 30, 2026','Federal Service Labor-Management Relations Statute'], 'NTIAPET2020':['July 27, 2020','Pursuant to section 1.401','(i) the interaction','(ii) the conditions','(A) deceptive','(B) taken after','(iii) any another'], 'DOJ20200923':['Today, on behalf','The legislation also executes'], 'WH20200923':['we’re here today','sent to Congress']}
missing=[]
for s in S['sources']:
 sid=s['source_id'];m=byurl.get(s.get('url'))
 if m and m.get('text_path'):
  s['text_path']=m['text_path'];s['text_sha256']=H(m['text_path'])
 if sid=='MEMO2019':
  d=fitz.open(s['local_path']); t=''.join(f'=== PDF page {i+1} ===\n'+p.get_text()+'\n' for i,p in enumerate(d));p=B/'v2/texts/MEMO2019.txt';p.write_text(t);s.update(text_path=str(p),text_sha256=H(p),pdf_page_count=len(d));needles[sid]=['Agencies shall adhere','amend Executive Orders','August 25, 2018']
 if s.get('local_path'):
  assert H(s['local_path'])==s['sha256'],sid
 if s.get('held_text_path'):
  assert H(s['held_text_path'])==s['text_sha256'],sid
  s['text_path']=s['held_text_path'];needles[sid]=['Sec. 3. Revocation','(b) Executive Order 13837','(c) Executive Order 13839'] if sid=='EO14003' else ['Section 1. Revocation','Sec. 2. Implementation.']
 if s.get('text_path'):
  t=pathlib.Path(s['text_path']).read_text(); assert H(s['text_path'])==s['text_sha256']
  ex=[]
  for n in needles.get(sid,[]):
   i=t.lower().find(n.lower())
   if i<0:missing.append([sid,n]);continue
   # retain literal source span, bounded to paragraph / 500 chars
   j=t.find('\n\n',i);j=min(i+500,len(t)) if j<0 else min(j,i+500)
   a=max(i,t.rfind('\n',0,i)+1);q=t[a:j]
   pages=re.findall(r'=== PDF page (\d+) ===',t[:a]);ex.append({'quote':q,'char_start':a,'char_end':j,'pdf_page':int(pages[-1]) if pages else None,'text_sha256':s['text_sha256'],'raw_sha256':s['sha256']})
  s['excerpts']=ex
 if sid in seen:s['image_inspected_pdf_pages']=seen[sid]
 s.pop('inspected_page_images_pending',None)
 if sid=='FLRA20230327':s['finding']='Primary adjudication, retained PDF and selected page images examined. Continued CBA protected against conflicting agency-wide rule under 5 USC 7116(a)(7); remanded March 27, 2023. Footnote 8 cites mandate Doc1809309 filed October3 2019. Concrete residual dispute after EO revocation; no cutoff-wide extinction of all CBA effects proved.'
 if sid=='NTIAPET2020':s.update(page_or_item='PDF p1 dated cover; pp3–4 (printed1–2) exact EO connection and required content',finding='Petition expressly requests every subject in EO13925 section2(b)(i)–(iii): interaction of (c)(1)/(c)(2); deceptive/pretextual/inconsistent moderation; notice, explanation and meaningful opportunity to be heard; other appropriate disclosure rules. These content specifications are performed by the July27 filing, subject to separately retained receiving-agency confirmation. FCC need not grant the petition for filing task performance.')
 if sid=='OPM20191004':s['finding']+=' Actual mandate document was subsequently browsed at a university mirror (see MANDATE_MIRROR); native raw retention remains pending, no judicial raw hash asserted here.'
S['unmatched_excerpt_needles']=missing
for s in S['sources']:
 if s['source_id']=='EO14029':s['finding']='Section1 unnumbered list says the following Presidential actions are revoked, including13925. No section1(a) exists. Signing-date command extinction proposed May14 2021; publicationMay19. Section2 separately requires consideration of rule/policy rollback and appropriate entity abolition, consistent with law. This supersedes the earlier draft citation/quotation.'
S['corrections_to_prior_versions']=['EO14029 revokes EO13925 in section1, not section1(a); wording is the following Presidential actions are revoked. Prior hereby wording was inaccurate for this actor. Immediate revocation analysis rests on present-tense operative text with no deferred date.']
write(B/'SOURCE_FINDINGS.v3.json',S)
# Update the sidecar with source-pinned legal analysis; preserve all earlier versions.
for eo in [13836,13837,13839,13925]:
 P=B/f'EO_{eo}'; a=json.loads((P/'LIFECYCLE_ANALYSIS.json').read_text());d=json.loads((P/'LIFECYCLE_PROPOSAL.json').read_text())
 a['schema']='eo-continuation-lifecycle-analysis/v2';a['supersedes']='LIFECYCLE_ANALYSIS.json';a['source_findings']={'path':'../SOURCE_FINDINGS.v3.json','sha256':H(B/'SOURCE_FINDINGS.v3.json')};a['first_cessation_policy']='A temporary injunction is a suspension episode, not permanent legal extinction. Exact first suspension date remains August24–25 2018 pending Dkt57; July16 appellate decision is distinct from October3 mandate. A one-off task can be exhausted by actual performance before formal revocation; composite scopes retain separate component dates.'
 a['review_scope']='Producer proposal; approved=false. Native frozen evidence has not been supplemented or assembled. No independent or human approval.'
 a['residual_effects_through_cutoff']='No automatic revival inferred from EO14148 revoking EO14003/14029. Existing CBA terms, statutory authorities, regulatory proceedings and litigation require their own legal bases and endpoints. Evidence establishes particular surviving consequences after revocation, not an exhaustive cutoff-wide residual-effects inventory.'
 a['source_ids']=[x['source_id'] for x in S['sources'] if (eo==13925 and x['source_id'] in ['NTIAPET2020','FCC20200727','DOJ20200923','WH20200923','EO14029']) or (eo!=13925 and x['source_id'] not in ['NTIAPET2020','FCC20200727','DOJ20200923','WH20200923','EO14029'])]
 if eo==13925:
  a['formal_extinction']['reason']='Section1 says the following Presidential actions are revoked, expressly naming EO13925, without deferred effectiveness. Signing-date command extinction May14 is a proposed legal judgment; publicationMay19 remains distinct. No subsection1(a) exists.'
  a['actor_implementation_savings']='EO14029 section2 directs OMB/agencies promptly to consider rescinding implementing orders, rules, guidelines and policies as appropriate and consistent with law, including APA; entities shall be abolished as appropriate and consistent with law. This does not itself erase every rule or statutory proceeding. No EO-specific unconditional residual-extinction date is proved.'
  for c in d['clauses']:c['reason']=c['reason'].replace('section 1(a)','section 1')
  d['savings']['reason']+=' EO14029 section2 separately directs appropriate, legally consistent implementation rollback and entity abolition; it does not establish automatic rescission of all implementing regulations.'
  content={'sec2-i':'Interaction of section230(c)(1) and (c)(2).','sec2-i-ii':'Good-faith conditions including pretext and procedural safeguards.','sec2-c':'Machine fragment is subsection2(b)(ii)(A)/(B): deceptive/pretextual/inconsistent terms and notice/explanation/hearing.','sec2-c-iii':'Other appropriate rules; petition expressly proposes disclosure requirements.'}
  for c in a['scope_analysis']:
   key=c['scope_id'].split('#')[1]
   if key in content:
    c['reason']=content[key]+' Held petition PDF p4 expressly requests this topic, with EO connection on p3. The filing/content task was exhausted July27 2020; this does not require FCC adoption and does not end the separate agency application instruction.'
    c['component_performance_date']='2020-07-27';c['source_ids']=['NTIAPET2020','FCC20200727'];c['first_end_supported_exact_date']='2020-07-27';c['native_exact_field_deferred_reason']='New factual source evidence lacks a frozen, independently reviewed ending ID; source integration required before native assembly.'
    for n in d['clauses']:
     if n['scope_id']==c['scope_id']:n['reason']='EO14029 formally revoked remaining EO authority May14 2021. '+c['reason']+' Exact earlier factual ending is recorded in analysis, pending frozen evidence integration.'
  a['remaining_gaps']=[x for x in a['remaining_gaps'] if not x.startswith('Check the held NTIA')]
  a['remaining_gaps'].insert(0,'Native retention of FCC same-day filing confirmation is pending; exact NTIA content is now examined on held PDF pp3–4. Integrate newly acquired evidence into a new packet before assembly.')
  a['performance_events'][0]['petition_content_verified_pdf_pages']=[3,4]
 else:
  a['retained_primary_source_results']={'court_decision':'July16 2019 vacatur for lack of jurisdiction, CADC2019 pp2/6/20. This is not a merits ruling approving every provision.','operative_restoration':'OPM20191004 p1 expressly witnesses October3 mandate; October4 guidance withdrawal/reinstatement is a separate agency action.','court_order_date_conflict':'CADC2019 p6 cites Order at2–3 datedAugust24 2018 Dkt57; October11 memorandum describes injunctionAugust25. Actual Dkt57 remains required for exact first suspension.','implementation_revocation':'OPM20210305 pp1–5 rescinds guidance, ends implementation and directs legally constrained CBA unwinding; EO revocation occurredJanuary22.','residual_example':'FLRA20230327 pp1/3 demonstrates continued CBA effects and a remanded dispute after revocation.'}
  if eo==13836:a['actual_performance_bounds']=[{'task':'Section8 public CBA database release','date':'2020-01-09','source':'OPMCBA20200109 pp1–2','limit':'Release completed; uploading continued. No proof continuing publication duty exhausted.'},{'task':'Section3 model CBA language','document_date':'2020-07-13','source':'OPM20210305 attachment item14, PDFp10','limit':'Agency-distributed item identified; full contents, initial performance date and all required subcomponents not proved.'},{'task':'Section3 report to President','document_date':'2020-12-17','source':'OPM20210305 attachment item18, PDFp11','limit':'Item exists and was distributed to agencies. Does not itself prove required submission throughOMB, presidentialreceipt, or firstmeetingdate.'}]
  if eo==13837:a['actual_performance_bounds']=[{'task':'First governmentwide annual report and analysis','document_month':'2020-10','source':'OPMFY2019 cover, printedpp2–3/PDFpp3–4','limit':'Actual analysis and report established; June30 deadline expressly missed; documentmonth does not establish exact publication day. Recurring duty not exhausted.'}]
  if eo==13839:a['actual_performance_bounds']=[{'task':'OPM rulemaking, partial implementation','publication':'2020-10-16','effective':'2020-11-16','source':'OPMRULE2020 p1','limit':'Rule anticipates additional revisions; no whole section7(a) exhaustion.'},{'task':'Partial regulatory rescission','publication':'2022-11-10','effective':'2022-12-12','source':'OPMRULE2022 pp1/16','limit':'Separate regulatory residue after EO revocation. Data collection discontinued; source sayssection5 though originaldutysection6.'}]
 d['source_notes']=['Original/page confirmations carried from frozen producer-b; not a new original-authentication attestation.','New retained primary source examination, exact raw/text hashes, literal source excerpts and page references are in ../SOURCE_FINDINGS.v3.json, sha256 '+H(B/'SOURCE_FINDINGS.v3.json')+'.','New factual evidence is not an admitted ending ID in the frozen packet. Component performance dates and intervals are carried in LIFECYCLE_ANALYSIS.v2.json without inventing registry evidence.','approved=false. No assembly, canonical filing, adoption or readiness change.']
 d['research_rationale']=d['research_rationale'].replace('LIFECYCLE_ANALYSIS.json','LIFECYCLE_ANALYSIS.v2.json')+' The new source review verifies NTIA petition content and binds judicial/OPM findings to actual retained raw bytes and local text spans.'
 d['unresolved_material_gaps']=a['remaining_gaps'];d['approved']=False
 write(P/'LIFECYCLE_ANALYSIS.v2.json',a);write(P/'LIFECYCLE_PROPOSAL.v2.json',d)
print('source excerpts',sum(len(x.get('excerpts',[])) for x in S['sources']),'unmatched',missing)
