from pathlib import Path
import json,hashlib,re,datetime
OUT=Path(__file__).parent;BASE=OUT.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
p=OUT/'SOURCE_FINDINGS.json';x=json.loads(p.read_text());native={r['url']:r for r in x['new_retained_source_checks']}
specs=[('2021-00710.pdf','dates','DATES: Effective: January 21, 2021.','FOR FURTHER INFORMATION',1),('2021-00710.pdf','filing','[FR Doc. 2021–00710 Filed','BILLING CODE',15),('2021-00710.pdf','original implementing formula','25.105 [Amended]','■ 8.',8),('2022-04173.pdf','retained EO13881 and revised ordinary content','■ 5. Amend section 25.101','■ 6.',11),('2022-04173.pdf','base factors, fallback and critical-items framework','25.106 Determining reasonableness','■ 10.',12),('2022-04173.pdf','construction alternate and higher-factor scope','25.201 Policy.','25.501 [Amended]',13),('2022-13373.pdf','agency preamble contrary shorthand','E.O. 13881 supersedes','DoD published',1),('2022-13373.pdf','actual agency conformity','DATES: Effective June 23, 2022.','II. Discussion',1),('2026-17828.pdf','actual current classification','DATES: The annual LSA list is effective','FOR FURTHER INFORMATION',1),('2026-17828.pdf','annual classification promulgation','Department of Labor (DOL)’s regulations','In addition,',1),('2026-17828.pdf','duration','DOL issues the LSA list','To ensure',1),('CFR-2025-title20-vol3-part654.pdf','operative EO10582 subpart','§ 654.11 Purpose','=== PDF page 4',3)]
spans=[]
for suffix,purpose,start,end,page in specs:
 row=next(r for u,r in native.items() if u.endswith(suffix))
 if not row['selected_texts']:continue
 tp=Path(row['selected_texts'][0]['text_path']);t=tp.read_text();a=t.find(start)
 if a<0:raise RuntimeError('missing substantive start '+start)
 b=t.find(end,a+len(start))
 if b<0:raise RuntimeError('missing substantive end '+end)
 q=t[a:b];spans.append({'url':row['url'],'raw_sha256':row['raw_sha256'],'text_path':str(tp),'text_sha256':sha(tp),'char_start':a,'char_end':b,'quote':q,'quote_sha256':hashlib.sha256(q.encode()).hexdigest(),'offset_units':'Unicode code points in exact text_path','pdf_page_of_start':page,'purpose':purpose})
x['substantive_native_spans']=spans
x['contrary_primary_source_application']={'url':native[next(u for u in native if u.endswith('2022-13373.pdf'))]['url'],'printed_page':37440,'preamble_shorthand':'E.O.13881 supersedes E.O.10582','resolution':'Agency explanatory preamble is broader shorthand than the controlling EO13881 §3 text. The EO expressly limits general supersession to inconsistency and singles out2(a)/2(c) for conditional revocation. Apply those scopes; preserve contrary shorthand as counterevidence, without treating it as an independent presidential whole-order revocation.'}
x['page_checks'] += [{'raw_sha256':'c28aecd46debf9ac5f0924126d13a4fb4083391818b46046b3b8a4e55d17284b','pdf_pages':[1,11,12],'check':'Visual effective date, retained EO13881 in operative amendment, 60/65/75 schedule,20/30 factors and55fallback. Operative Part25/52 amendments pp11–19 read; no claim of exhaustive regulatory-history coverage.'},{'raw_sha256':'f8579009fab6059700beeeaeb171ede6355099506cddb227501c2f45a6f49193','pdf_pages':[1],'check':'Full notice text and raw page read; actual annual classifications effective2026-10-01, term through following September30.'},{'raw_sha256':'72792ca43b35856d1b95534334175e38cd74ea791c09ba945491dcc68ee7691c','pdf_pages':[3],'check':'Full Part654 text read; raw printed325 confirms operative654.11–.13 and original-authority distinction.'}]
failures=[]
for rp in [BASE/'acquisition-v1/pdf-run-2/RESULTS.json',BASE/'acquisition-v2/pdf-run-1/RESULTS.json']:
 for r in json.loads(rp.read_text()):
  if r['url'] in x['native_binding']['not_retained']:failures.append({'url':r['url'],'results_path':str(rp),'results_sha256':sha(rp),'attempt':r['attempt']})
x['failed_native_requests']=failures
x['native_binding']['final_checkpoint']='SOURCE_MAP_003;15/18 requested objects retained;3 failed. No additional retrieval authorized in this producer freeze.'
save(p,x)
requests=json.loads((OUT/'SOURCE_REQUESTS.json').read_text())
for r in requests:
 f=next((f for f in failures if f['url']==r['url']),None)
 if f:r.update(status='native_attempt_failed_not_exhaustion',failure_results_path=f['results_path'],failure_reason=f['attempt']['error'])
save(OUT/'SOURCE_REQUESTS.json',requests)
for n in ['10582','13881']:
 for name in ['STATUS_PROPOSAL.json','LIFECYCLE_PROPOSAL.json']:
  p=OUT/f'EO_{n}'/name;y=json.loads(p.read_text())
  for key in ['material_gaps','unresolved_material_gaps']:
   if key in y:y[key]=['Retained new sources need explicit native supplement/registration into a refreshed dossier before native legal acceptance;15/18 frozen requests now held and independently rehashed.' if 'New regulatory/FY2027 source custody' in z else z for z in y[key]]
  if 'source_notes' in y:y['source_notes'].append('Final custody bound to SOURCE_MAP_003;15/18 requested PDFs held. Exact substantive spans in SOURCE_FINDINGS.json. Failed2026 editions/as-of retrieval/Proc3279 slice are not exhaustion.')
  if name=='STATUS_PROPOSAL.json':y['rationale']+=' Final native retention now binds the actual2021/2022 FAR rules, DFARS rule,2025 CFR and2026LSA notice. This closes source-custody gaps for those objects, without resolving the remaining report/performance, statutory-successor and cutoff-deviation questions.'
  save(p,y)
p=OUT/'RESEARCH.md';s=p.read_text();s=s.replace('SOURCE_MAP_002 binds ten of the eighteen frozen requested objects','SOURCE_MAP_003 binds fifteen of the eighteen frozen requested objects').replace('Source registration and further rule custody remain separate.','Source registration remains separate. The 2026 CFR editions and Proclamation3279 slice failed acquisition; those failures establish no exhaustion.')
s=s.replace('§3(d)national-security advice','§3(d) national-security advice').replace('substitutesOEPDirector','substitutes the OEP Director').replace('revokesEO','revokes EO').replace('as ofApril','as of April').replace('onMarch','on March')
s+='\nThe DFARS rule’s preamble at37440 uses the broad shorthand that EO13881 supersedes EO10582. The controlling EO13881§3 expressly confines general supersession to inconsistency and enumerates only2(a)/2(c) for conditional revocation. The preamble does not supply an additional presidential whole-order revocation. Its contrary shorthand remains recorded in SOURCE_FINDINGS.json.\n'
s=re.sub(r'\bEO(?=\d)','EO ',s);s=re.sub(r'\b(January|February|March|April|May|June|July|August|September|October|November|December)(?=\d)',r'\1 ',s);s=re.sub(r'(\d),20(\d\d)',r'\1, 20\2',s);s=s.replace('§3 expressly',' §3 expressly');p.write_text(s)
p=OUT/'TIMING.json';y=json.loads(p.read_text());y['checkpoint_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();y['freeze_version']='v2';save(p,y)
print('finalized v2 substantive findings and native proposals')
