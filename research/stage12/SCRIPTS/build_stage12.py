#!/usr/bin/env python3
"""Conservative, reversible Stage 12 method audit overlay. No original ledger mutation.
Usage: python build_stage12.py STAGE11_LEDGER.jsonl LORD_UNNUMBERED_PDF.pdf OUTPUT_DIRECTORY
No network access required; deterministic sampling seed 20261016.
"""
from __future__ import annotations
import csv,hashlib,json,sys,re,collections,random,subprocess,pathlib,datetime,math
from html import escape

CUTOFF='2026-10-14'; SEED=20261016
DATE_CORRECTIONS={
 'EO:8969':('1941-12-11','https://tile.loc.gov/storage-services/service/ll/cfr/cf/r1/94/30/05/-T/3C/2/cfr1943005-T3C2/cfr1943005-T3C2.pdf','3 CFR 1943 table; contemporaneous; NARA 1941 page misprints year 1946'),
 'EO:10276':('1951-07-31','https://www.presidency.ucsb.edu/documents/executive-order-10276-administration-the-housing-and-rent-act-1947-amended-and-termination','President Harry S Truman original dateline, July 31 1951'),
 'EO:13174':('2000-10-27','https://www.govinfo.gov/content/pkg/CFR-2001-title3-vol1/pdf/CFR-2001-title3-vol1-eo13173.pdf','3 CFR 2001 page following EO13173: signed October 27 2000; modern NARA states Oct31, conflict flagged'),
 'EO:13333':('2004-03-16','https://www.archives.gov/federal-register/executive-orders/2004.html','Official NARA disposition entry EO13333, signed March 16 2004'),
}
# EO13174 NARA and printed 3 CFR dating conflict is flagged; initial projection uses official signed 3 CFR but requires verification.
DUPLICATE_ALIAS={'EO:7933A':'EO:7933a'} # canonical primary kept as modern record with supported NO status
SEVEN_FALSE_FLAGS={f'EO:UN:executive-orders-01:row:{n}' for n in (2,4,8,11,61,65,205)}
MONTHS={'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,'jul':7,'aug':8,'sep':9,'oct':10,'nov':11,'dec':12}
MRE=r'(jan(?:uary|e|\.)?|feb(?:ruary|e|s|\.)?|mar(?:ch|e|\.)?|apr(?:il|e|\.)?|may|jun(?:e|e|\.)?|jul(?:y|e|\.)?|aug(?:ust|e|\.)?|sep(?:tember|t|te)?\.?|oct(?:ober|s|e|\.)?|nov(?:ember|e|\.)?|dec(?:ember|e|\.)?)'
DATE_RE=re.compile(r'^\s*'+MRE+r'\s*(\d{1,2})(?:\b|\.)',re.I)
YEAR_RE=re.compile(r'^\s*((?:17|18|19)\d{2})\s*$')

def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for part in iter(lambda:f.read(1024*1024),b''):h.update(part)
 return h.hexdigest()

def write_json(path, obj):
 with open(path,'w',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2,sort_keys=True);f.write('\n')

def write_jsonl(path,rows):
 with open(path,'w',encoding='utf-8') as f:
  for r in rows:f.write(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n')

def write_csv(path,rows,fields):
 with open(path,'w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)

def parse_year(date):
 if not isinstance(date,str) or not re.match(r'^\d{4}-\d{2}-\d{2}$',date):return None
 try:return datetime.date.fromisoformat(date).year
 except:return None

def era(y):
 return ('1789-1861' if y<1862 else '1862-1906' if y<1907 else '1907-1936' if y<1937 else '1937-1989' if y<1990 else '1990-2026') if y else 'undated'

def cause_class(r):
 if r['substantive_effect']=='indeterminate':return 'present_status_not_determined'
 if r['substantive_effect']=='yes':return 'current_effect_proved_first_episode_cessations_unassessed'
 mech=r.get('cessation_mechanism','unknown'); first=r.get('first_cessation_date','unknown')
 if mech in ('unknown',None,''):
  return 'cause_not_populated'
 if any(k in str(mech) for k in ['firstcause_unknown','earlierfirstcause_unknown']):return 'latest_termination_known_first_cause_unproved'
 if first in ('unknown',None,''):
  return 'mechanism_proposal_no_first_date'
 if isinstance(first,str) and re.match(r'^\d{4}-\d{2}-\d{2}$',first):return 'mechanism_and_date_populated_not_externally_verified'
 return 'mechanism_with_nonexact_or_untyped_first_date'

def ingest_lord(pdf,out):
 """Harvest dated-line REFERENCES ONLY, not unique EOs. All chronological pages registered.
 The source OCR is visibly unreliable, so year assignments are tentative and do not change the EO denominator.
 """
 try:
  pages=subprocess.check_output(['pdftotext','-layout',str(pdf),'-'],timeout=75).decode('utf8','replace').split('\f')
 except Exception as ex: raise RuntimeError('Need pdftotext for one-pass source-text parsing') from ex
 registry=[];leads=[];active_year=1789;held_year=1789;pdf_hash=sha(pdf)
 # Page 23 (one-indexed) begins printed chronological list page 1. Page 248 ends list; index starts PDF page 251.
 for page_no in range(23,249):
  text=pages[page_no-1] if page_no-1<len(pages) else ''
  lines=text.splitlines();n=0;yrs=[];src_sha=hashlib.sha256(text.encode('utf8')).hexdigest()
  for line_no,line in enumerate(lines,1):
   ymatch=YEAR_RE.match(line)
   if ymatch:
    possible=int(ymatch.group(1)); indent=len(line)-len(line.lstrip())
    if 1789<=possible<=1941 and indent<=26 and active_year<=possible and possible-active_year<=35:
     active_year=possible;yrs.append(possible)
   m=DATE_RE.match(line)
   if not m:continue
   day=int(m.group(2)); mon=MONTHS.get(m.group(1)[:3].lower())
   if not (mon and 1<=day<=31):continue
   n+=1
   # OCR page wraps often scramble sentences; preserve first three normalized lines as *locator*, not full order text.
   snippet=' '.join(z.strip() for z in lines[line_no-1:line_no+2] if z.strip())
   leads.append({'source_lead_id':f'LORD-UN1943:p{page_no:03}:datelead:{n:02}',
      'source_sha256':pdf_hash,'page_1_based':page_no,'ocr_line_1_based':line_no,
      'year_provisional':None,'month_provisional':mon,'day_provisional':day,
      'date_label_provisional':None, 'year_hint_ocr_unverified':active_year,
      'year_basis':'OCR year carry-forward IS UNRELIABLE; year and complete date intentionally null pending page image audit',
      'raw_date_line':line.strip(), 'context_ocr':snippet[:520],
      'status':'SOURCE_ONLY_UNREVIEWED_NOT_EO_IDENTITY',
      'identity_deduplicated':False,'is_full_signed_text':False})
  registry.append({'page_1_based':page_no,'page_text_sha256':src_sha,'date_leads':n,
     'monotone_year_headings_detected':yrs,'ocr_text_chars':len(text),
     'unextracted_items_expected':'undated, split-column, OCR-corrupted and multiple same-day entries remain; NOT a page-order count'})
 write_jsonl(out/'DATA/LORD_1943_PAGE_REGISTER_226.jsonl',registry)
 write_jsonl(out/'DATA/LORD_1943_DATE_LEADS_SOURCE_ONLY.jsonl',leads)
 return len(leads),len(registry),collections.Counter(l['year_hint_ocr_unverified']//10*10 for l in leads)

def main(ledger,pdf,out):
 out.mkdir(parents=True,exist_ok=True)
 for d in ['DATA','QA','VISUALS','SOURCES']: (out/d).mkdir(exist_ok=True)
 raw=[json.loads(l) for l in open(ledger,encoding='utf8') if l.strip()]
 assert len(raw)==15010
 byid={r['instrument_id']:r for r in raw}; assert len(byid)==len(raw)
 v=[r for r in raw if r.get('included_validated') is True];assert len(v)==14973
 cnt=collections.Counter(r.get('substantive_effect') for r in v)
 assert cnt=={'yes':193,'no':2322,'indeterminate':12458},cnt
 for i,alias in DUPLICATE_ALIAS.items():
  assert i in byid and alias in byid
  assert byid[i]['signing_date']==byid[alias]['signing_date']
 for id, (d,*_) in DATE_CORRECTIONS.items():assert id in byid and (not byid[id]['signing_date'] or byid[id]['signing_date']!=d)
 normalized=[];changes=[]
 for r in raw:
  ident=r['instrument_id']; d=r.get('signing_date'); corrected=DATE_CORRECTIONS.get(ident)
  new_d=corrected[0] if corrected else d
  duplicate=ident in DUPLICATE_ALIAS
  proj={'instrument_id':ident,'canonical_document_group':DUPLICATE_ALIAS.get(ident,ident),
    'included_validated_original':bool(r.get('included_validated')),
    'included_unique_document_proxy':bool(r.get('included_validated')) and not duplicate,
    'population_class':r.get('population_class'), 'signing_date_original':d,
    'signing_date_audit_projection':new_d,'signing_date_conflict':ident=='EO:13174',
    'year_audit_projection':parse_year(new_d),'era_audit_projection':era(parse_year(new_d)),
    'substantive_effect_original':r.get('substantive_effect'),
    'any_operative_EO_effect_original':r.get('any_operative_EO_effect'),
    'legacy_original_1943_cohort':r.get('original_1943_cohort'),
    'cohort_provenance_overlay':bool(r.get('original_1943_cohort')) and ident not in SEVEN_FALSE_FLAGS,
    'date_source_url':corrected[1] if corrected else None,
    'date_source_note':corrected[2] if corrected else None,
    'cause_evidence_state':cause_class(r),
    'ever_became_operative':'NOT_YET_ADJUDICATED',
    'first_cessation_date_original':r.get('first_cessation_date'),
    'first_cessation_mechanism_original':r.get('cessation_mechanism'),
    'judicial_status_original_type':type(r.get('judicial_enforceability')).__name__,
    'future_legal_recheck_required':ident in {'EO:2596','EO:2602','EO:3016C','EO:3016K','EO:3016N'},
    'overlay_not_legal_adjudication':True}
  normalized.append(proj)
  if corrected:changes.append({'instrument_id':ident,'change_type':'date_metadata','before':d,'after':new_d,'source':corrected[1],'rationale':corrected[2],'confidence':'high except EO13174: original text vs NARA date conflict, revisit'})
  if duplicate:changes.append({'instrument_id':ident,'change_type':'alias_collapse','before':'distinct included source-row identity','after':'alias of '+DUPLICATE_ALIAS[ident],'source':'https://www.archives.gov/federal-register/executive-orders/1938.html','rationale':'Same order 7933-A under two alphabetic cases; substantive NO held by modern representative; no change to predecessor evidence','confidence':'high'})
  if ident in SEVEN_FALSE_FLAGS and r.get('original_1943_cohort'):
   changes.append({'instrument_id':ident,'change_type':'cohort_provenance','before':True,'after':False,'source':'EO_PROJECT_INDEPENDENT_ADVERSARIAL_AUDIT_DOSSIER_2026-10-16.md section 4.5','rationale':'Original queue mismatch reported in dossier; pending recheck against original CSV','confidence':'inherited from dossier, not independently reconstructed'})
 write_jsonl(out/'DATA/STAGE12_NORMALIZED_NONDESTRUCTIVE_15010.jsonl',normalized)
 write_jsonl(out/'QA/OVERLAY_CHANGE_LOG.jsonl',changes)
 unique=[x for x in normalized if x['included_unique_document_proxy']]
 assert len(unique)==14972
 assert collections.Counter(x['substantive_effect_original'] for x in unique)=={'yes':193,'no':2322,'indeterminate':12457}
 count_date=sum(x['year_audit_projection'] is not None for x in unique)
 assert count_date==14854,count_date
 counts=collections.defaultdict(lambda:collections.Counter())
 decade=collections.defaultdict(lambda:collections.Counter())
 for r in unique:
  y=r['year_audit_projection'];key=str((y//10)*10) if y else 'undated'
  decade[key][r['substantive_effect_original']]+=1
  decade[key]['total']+=1
  e=r['era_audit_projection'];counts[e][r['substantive_effect_original']]+=1;counts[e]['total']+=1
 era_rows=[]
 for e in ['1789-1861','1862-1906','1907-1936','1937-1989','1990-2026','undated']:
  c=counts[e];num=c['yes']+c['no'];era_rows.append({'era':e,'included':c['total'],'yes':c['yes'],'no':c['no'],'unknown':c['indeterminate'],'determinate':num,'coverage_pct':round(100*num/c['total'],4) if c['total'] else None})
 write_csv(out/'DATA/STATUS_BY_ERA_AUDITED.csv',era_rows,['era','included','yes','no','unknown','determinate','coverage_pct'])
 dec_rows=[]
 for k in sorted(decade,key=lambda x:9999 if x=='undated' else int(x)):
  c=decade[k];num=c['yes']+c['no'];dec_rows.append({'decade':k,'included':c['total'],'yes':c['yes'],'no':c['no'],'unknown':c['indeterminate'],'determinate':num,'coverage_pct':round(100*num/c['total'],4) if c['total'] else None})
 write_csv(out/'DATA/STATUS_BY_DECADE_AUDITED.csv',dec_rows,['decade','included','yes','no','unknown','determinate','coverage_pct'])
 year_counts=collections.Counter(r['year_audit_projection'] for r in unique)
 yrref=json.load(open(out/'SOURCES/OFR_ANNUAL_REFERENCE_1937_2026.json',encoding='utf8'))
 year_audit=[]
 for y,v0 in yrref['annual_counts'].items():
  y=int(y);n=year_counts[y]
  year_audit.append({'year':y,'ofr_website_published_count':v0,'ledger_unique_proxy_with_repaired_dates':n,
     'difference':n-v0,'comparison_is_equivalence_proof':False,'note':('1937 7700-A additional documented historic entry not in OFR annual table' if y==1937 and n!=v0 else '2009 OFR displayed annual total disagrees with ordinary numeric series; unresolved' if y==2009 and n!=v0 else '')})
 write_csv(out/'QA/ANNUAL_OFR_RECONCILIATION.csv',year_audit,['year','ofr_website_published_count','ledger_unique_proxy_with_repaired_dates','difference','comparison_is_equivalence_proof','note'])
 # Reproducible, explicitly nonrepresentative stratified probe of *determinate* legal statuses
 rng=random.Random(SEED)
 groups=collections.defaultdict(list)
 for r in unique:
  if r['substantive_effect_original'] in ('yes','no'):groups[(r['substantive_effect_original'],r['era_audit_projection'])].append(r)
 capacities={('yes','1862-1906'):1,('yes','1907-1936'):3,('yes','1937-1989'):7,('yes','1990-2026'):10,
             ('no','1862-1906'):4,('no','1907-1936'):12,('no','1937-1989'):19,('no','1990-2026'):5}
 selections=[]
 for key,pool in groups.items():
  k=min(capacities.get(key,0),len(pool)); selections.extend((r,key,len(pool),k) for r in rng.sample(sorted(pool,key=lambda x:x['instrument_id']),k))
 # Fill shortfalls to exactly 60 with random sampling per status, preserving diversity
 chosen={r['instrument_id'] for r,_,_,_ in selections}
 while len(selections)<60:
  pool=[r for r in unique if r['substantive_effect_original'] in ('yes','no') and r['instrument_id'] not in chosen]
  r=rng.choice(pool);key=(r['substantive_effect_original'],r['era_audit_projection']); selections.append((r,key,len(groups[key]),None));chosen.add(r['instrument_id'])
 assert len(selections)==60
 rng.shuffle(selections)
 blind=[];keyrows=[]
 for j,(r,key,orig_n,k) in enumerate(selections,1):
  blind.append({'blind_case_id':f'BLIND-{j:03d}','instrument_id':r['instrument_id'],
      'original_signing_date_audit_projection':r['signing_date_audit_projection'],
      'source_quality_class':'BLINDED_Reviewer_independently_retrieve_original',
      'instructions':'Retrieve original and later legal chain without opening project reasoning; test every operative provision and reach YES/NO/UNKNOWN; then compare with keyed ledger.'})
  keyrows.append({'blind_case_id':f'BLIND-{j:03d}','instrument_id':r['instrument_id'],'stage11_substantive':r['substantive_effect_original'],
      'original_evidence_grade':byid[r['instrument_id']].get('evidence_grade'), 'era_stratum':key[1],
      'status_stratum_n':len(groups[key]),'target_selected_n':sum(1 for x in selections if x[1]==key),
      'sampling_scheme':'disproportionately stratified challenge; use stratum weights for error inference'})
 write_csv(out/'QA/BLIND_PRESENT_STATUS_AUDIT_60.csv',blind,['blind_case_id','instrument_id','original_signing_date_audit_projection','source_quality_class','instructions'])
 write_jsonl(out/'QA/REVIEW_KEY_WITH_BASELINE_60.jsonl',keyrows)
 # Unnumbered volume first pass
 leads,pagect,lead_bydec=ingest_lord(pdf,out)
 # Source-census sampling *separate* from legal review: indexed historical rows and unnumbered refs must be audited as identity proxies.
 rng2=random.Random(SEED+1)
 byclass=collections.defaultdict(list)
 for r in unique: byclass[r['population_class']].append(r)
 allocations={'validated_historical_index':12,'validated_numbered':11,'documented_unnumbered':7}
 ids=[]
 for cls,n in allocations.items():ids.extend(rng2.sample(sorted(byclass[cls],key=lambda x:x['instrument_id']),n))
 assert len(ids)==30
 write_csv(out/'QA/IDENTITY_AUTHENTICATION_SAMPLE_30.csv',[
  {'instrument_id':r['instrument_id'],'population_class':r['population_class'],'signing_date':r['signing_date_audit_projection'],
   'audit_question':'One physical presidential instrument? Is signer/authority presidential? Distinct from reprints, aliases, index rows and corrections?'} for r in ids],
  ['instrument_id','population_class','signing_date','audit_question'])
 # Special target test IDs
 target_ids=['EO:7933A','EO:7933a','EO:7700A','EO:8969','EO:10276','EO:13174','EO:13333','EO:3461','EO:2596','EO:2602','EO:3016C','EO:3016K','EO:3016N','EO:12553','EO:11408','EO:12829','EO:13708','EO:12001']
 write_csv(out/'QA/ADVERSARIAL_TARGETED_CHAIN_PANEL.csv',[
  {'instrument_id':id,'stage11_substantive':byid[id]['substantive_effect'],
   'date_audit':next(z['signing_date_audit_projection'] for z in normalized if z['instrument_id']==id),
   'test_focus': 'EO membership and authorship' if id.startswith('EO:3016') else 'EO legal footprint, preexisting cessation, savings, amendments, current attribution'}
   for id in target_ids],['instrument_id','stage11_substantive','date_audit','test_focus'])
 # QA machine assertions about collisions, status, provenance; no one claims every classification correct.
 repaired_counts=collections.Counter(r['substantive_effect_original'] for r in unique)
 cause=collections.Counter(r['cause_evidence_state'] for r in unique if r['substantive_effect_original']=='no')
 summary={'release_date':'2026-10-16','cutoff':CUTOFF,'baseline_sha256':sha(ledger),'lord_pdf_sha256':sha(pdf),
  'original_ledger_rows':len(raw),'original_included':14973,'audited_unique_document_proxies':len(unique),
  'duplicate_source_aliases_preserved':DUPLICATE_ALIAS,
  'original_effect_totals':dict(cnt),'audited_proxy_effect_totals':dict(repaired_counts),
  'date_corrections':len(DATE_CORRECTIONS),'undated_post_overlay':len(unique)-count_date,
  'wrong_provenance_flag_overlay_cases_observed':len([x for x in changes if x['change_type']=='cohort_provenance']),
  'blind_case_count':len(blind),'identity_sample_count':len(ids),
  'pre1862_counted':counts['1789-1861']['total'],
  'unnumbered_source_pdf_pages_total':'418 rendered pages (PDF parsing may differ in OCR layer)',
  'unnumbered_list_pages_covered':pagect,
  'unnumbered_source_only_OCR_date_line_leads':leads,
  'unnumbered_leads_not_included_denominator':True,
  'first_cause_statuses_among_NO':dict(cause),
  'ofr_annual_mismatches_after_overlay':[r for r in year_audit if r['difference']!=0],
  'coverage_pct_audited_unique_proxy':round(100*(repaired_counts['yes']+repaired_counts['no'])/len(unique),6),
  'unproven':['full actual historic EO total','Lord leads distinctness','true status error rate','first-cause causal rates','legally coherent causal attribution'],
  'no_legal_status_changes':True}
 write_json(out/'QA/RELEASE_METRICS.json',summary)
 # standalone HTML and PNG charts
 make_visuals(out,dec_rows,era_rows,summary,lead_bydec)
 print(json.dumps({'unique_proxies':len(unique),'date_leads':leads,'undated':len(unique)-count_date,
    'coverage':summary['coverage_pct_audited_unique_proxy'],'mismatches':summary['ofr_annual_mismatches_after_overlay']},indent=2))

def make_visuals(out,decs,eras,summary,lord_counts):
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 x=[r for r in decs if r['decade']!='undated']
 labels=[int(r['decade']) for r in x]
 fig,ax=plt.subplots(figsize=(14,6.5))
 unknown=[r['unknown'] for r in x];no=[r['no'] for r in x];yes=[r['yes'] for r in x]
 # explicit requested colors for distinguishable factual categories
 ax.bar(labels,unknown,width=7.5,label='Not adjudicated (UNKNOWN)',color='#C9D0D9',align='center')
 ax.bar(labels,no,width=7.5,bottom=unknown,label='Adjudicated substantive NO',color='#C17A51',align='center')
 ax.bar(labels,yes,width=7.5,bottom=[a+b for a,b in zip(unknown,no)],label='Adjudicated substantive YES',color='#367EAA',align='center')
 ax.set(xlim=(1784,2035),xlabel='Signing decade (1862–2026; pre-1862 excluded from validated inventory)',ylabel='Included, date-resolved candidate identities',title='The Afterlife of Executive Orders | Frozen Stage 11 statuses, Stage 12 census/date overlay')
 ax.set_xticks(range(1790,2030,20));ax.grid(axis='y',alpha=.2);ax.legend(loc='upper left');fig.tight_layout();fig.savefig(out/'VISUALS/DECADE_COUNTS_STACKED.png',dpi=160);plt.close(fig)
 fig,ax=plt.subplots(figsize=(14,4.8))
 percent=[r['coverage_pct'] for r in x]
 ax.bar(labels,percent,width=7.5,color='#367EAA')
 ax.set(xlim=(1784,2035),ylim=(0,100),xlabel='Signing decade',ylabel='Share with determinate substantive status (%)',title='Percent reviewed by issuance decade — not a legal survival probability')
 ax.set_xticks(range(1790,2030,20));ax.grid(axis='y',alpha=.2);fig.tight_layout();fig.savefig(out/'VISUALS/DECADE_COVERAGE_PERCENT.png',dpi=160);plt.close(fig)
 # SVG interactive local self-contained and by-decade table; no external library
 W=1220;H=460; padL=63;padR=32;plotW=W-padL-padR;plotH=300
 maxv=max(r['included'] for r in x)
 bars=[];ticks=[]
 for i,r in enumerate(x):
  dec=int(r['decade']);xp=padL+(dec-1789)/ (2026-1789)*plotW
  bottom=H-94
  heights=[round(plotH*r[k]/maxv,2) for k in ('unknown','no','yes')]
  colors=['#bfc5cc','#bc7757','#367eaa'];cy=bottom
  for height,color,tag in zip(heights,colors,['UNKNOWN','NO','YES']):
   if height>0:
    cy-=height;bars.append(f'<rect class="bar" data-decade="{dec}" x="{xp:.1f}" y="{cy:.1f}" width="{plotW/26:.1f}" height="{height:.1f}" fill="{color}" title="{dec}s {tag}: {r[tag.lower() if tag!="UNKNOWN" else "unknown"]}"/>')
 for d in range(1790,2030,20):
  xp=padL+(d-1789)/(2026-1789)*plotW;ticks.append(f'<text x="{xp:.1f}" y="{H-58}" fill="#64748b" text-anchor="middle" font-size="12">{d}</text>')
 trs=''.join(f'<tr><td>{r["decade"]}s</td><td>{r["included"]:,}</td><td>{r["yes"]}</td><td>{r["no"]:,}</td><td>{r["unknown"]:,}</td><td>{r["coverage_pct"]:.1f}%</td></tr>' for r in decs)
 metricpct=summary['coverage_pct_audited_unique_proxy']
 html=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EO Research | Stage 12 Audit</title><style>body{{margin:0;font-family:system-ui,-apple-system,Segoe UI,sans-serif;background:#f6f8fb;color:#1c3043}}main{{max-width:1230px;margin:auto;padding:35px 25px}}h1{{font-size:30px;margin:0 0 10px}}h2{{font-size:21px;margin:30px 0 12px}}.muted{{color:#617287}}.pane{{background:white;border-radius:14px;box-shadow:0 2px 12px #15253810;padding:24px;margin:18px 0}}.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}.metric{{background:#f0f3f7;padding:18px;border-radius:10px}}.number{{font-size:28px;font-weight:750}}.mini{{font-size:12px;color:#6d788b}}.prog{{height:16px;background:#dbe1e7;border-radius:30px;overflow:hidden}}.fill{{width:{metricpct}%;height:100%;background:#367eaa}}table{{width:100%;border-collapse:collapse;font-size:14px}}td,th{{text-align:right;padding:10px;border-bottom:1px solid #ebeff4}}td:first-child,th:first-child{{text-align:left}}th{{color:#617287}}.legend span{{margin-right:20px}}.dot{{display:inline-block;height:11px;width:11px;border-radius:3px;margin-right:5px}}.btn{{border:1px solid #ccd4de;background:white;border-radius:8px;padding:7px 12px;cursor:pointer}}.bar:hover{{opacity:.75}}details{{margin-top:10px}}@media(max-width:700px){{.metrics{{grid-template-columns:repeat(2,1fr)}}main{{padding:12px}}.pane{{overflow:auto}}}}</style></head><body><main><h1>The Afterlife of Executive Orders</h1><p class="muted">Stage 12 independent census & methodology audit · Status cutoff 14 October 2026 · Base ledger kept immutable</p><section class="metrics"><div class="metric"><div class="mini">Stage 11 source identities</div><div class="number">14,973</div></div><div class="metric"><div class="mini">After confirmed duplicate overlay</div><div class="number">{summary['audited_unique_document_proxies']:,}</div></div><div class="metric"><div class="mini">Present substantive decisions</div><div class="number">2,515</div></div><div class="metric"><div class="mini">Independent Lord OCR dated-line leads</div><div class="number">{summary['unnumbered_source_only_OCR_date_line_leads']:,}</div></div></section><section class="pane"><h2>Present-status coverage</h2><div class="prog"><div class="fill"></div></div><p><b>{metricpct:.2f}%</b> of the deduplicated working bibliography is determinate. This measures research completion, not historical survival. Every Lord source lead remains outside the denominator until independently authenticated.</p><h2>Number of working-bibliography orders by issuance decade</h2><div class="legend"><span><i class="dot" style="background:#bfc5cc"></i>UNKNOWN</span><span><i class="dot" style="background:#bc7757"></i>NO</span><span><i class="dot" style="background:#367eaa"></i>YES</span></div><svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Stacked histogram 1789 to 2026 showing UNKNOWN NO YES for project bibliography; zero included prior to 1862">{''.join(bars)}{''.join(ticks)}<line x1="60" y1="366" x2="1205" y2="366" stroke="#7b8797"/><text x="68" y="53" font-size="13" fill="#617287">Number in ledger</text></svg><p class="muted">Blank 1789–1861 bars show a known census omission, not zero actual orders. Historical series are incomplete. Missing signing years remain undated; {summary['undated_post_overlay']} known records have no usable date after this release.</p><h2>Classification percentage by historical era</h2><table><thead><tr><th>Era</th><th>Identities</th><th>YES</th><th>NO</th><th>UNKNOWN</th><th>Done</th></tr></thead><tbody>{''.join(f'<tr><td>{a["era"]}</td><td>{a["included"]:,}</td><td>{a["yes"]}</td><td>{a["no"]:,}</td><td>{a["unknown"]:,}</td><td>{f"{a["coverage_pct"]:.2f}%" if a["coverage_pct"] is not None else "—"}</td></tr>' for a in eras)}</tbody></table></section><section class="pane"><h2>Decade-by-decade table</h2><table><thead><tr><th>Decade</th><th>Identity count</th><th>YES</th><th>NO</th><th>UNKNOWN</th><th>Done</th></tr></thead><tbody>{trs}</tbody></table></section><section class="pane"><h2>What changed in this release</h2><p>Collapsed one confirmed suffix-case duplicate in a reversible projection, corrected four source-backed signing dates (EO13174 retains a source-date discrepancy flag), and isolated seven inherited false legacy-cohort flags on a reviewable overlay. Generated 60 blind legal-review cases and 30 identity-authentication cases, plus a full 226-page source register for Lord's 1943 unnumbered volume. All 193/2322 legal yes/no determinations remain unmodified.</p><p><b>Not yet adjudicated:</b> unnumbered-source identities, representative legal error rate, causal histories, and the defensible all-history denominator.</p></section></main></body></html>'''
 (out/'VISUALS/EO_STAGE12_AUDIT_DASHBOARD.html').write_text(html,encoding='utf8')

if __name__=='__main__':
 if len(sys.argv)!=4:
  print('Usage: python build_stage12.py STAGE11_LEDGER LORD_UNNUMBERED_PDF OUTDIR');sys.exit(2)
 main(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),pathlib.Path(sys.argv[3]))
