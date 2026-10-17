#!/usr/bin/env python3
"""Produce an authenticated-URL acquisition manifest from archived OFR records.
This extracts literal URLs only. Do not synthesize or trust the malformed old
body_html_url stubs that omit document numbers. Does not perform downloads.

Usage: python build_official_source_manifest.py <cached_stage10_zip> <stage14_db> <outdir>
"""
import collections,csv,hashlib,json,pathlib,re,sqlite3,sys,zipfile
from urllib.parse import urlparse
z=zipfile.ZipFile(sys.argv[1]);db=sqlite3.connect(sys.argv[2]);out=pathlib.Path(sys.argv[3]);out.mkdir(parents=True,exist_ok=True)
raw=[]
for i in range(1,8):
 path=f'EO_IMPORT_WORK/RAW_OFFICIAL_SOURCES/fedreg_bulk_{i:02d}.json'
 raw.extend(json.loads(z.read(path))['results'])
ids={r[0]:r for r in db.execute('SELECT id,substantive,include_unique,year,canonical_group FROM orders')}
blind=set(r[0] for r in db.execute("SELECT instrument_id FROM audit_sample WHERE kind='BLIND_60'"))
queued=set(r[0] for r in db.execute('SELECT instrument_id FROM queues'))
referenced=set(r[0] for r in db.execute('SELECT DISTINCT predecessor FROM relationships WHERE quarantined=0'))
rows=[];issues=[]
for r in raw:
 n=str(r.get('executive_order_number') or '').strip().replace(' ','')
 raw_source_label='EO:'+n
 # Historical source labels 7677-A versus ledger 7677A are aliases, not missing acts.
 normalized=re.sub(r'^EO:(\d+)-([A-Za-z])$', lambda m:'EO:'+m.group(1)+m.group(2).upper(), raw_source_label)
 if re.fullmatch(r'EO:\d+[A-Za-z]',normalized):normalized=normalized[:-1]+normalized[-1].upper()
 k=normalized
 if k in ids and ids[k][2] is not None and ids[k][2]==0 and ids[k][4] in ids:
  k=ids[k][4] # One known 7933A versus 7933a documentary duplicate; select analytic survivor.
 if k not in ids:

  issues.append({'eo_id':k,'reason':'FEDERAL_REGISTER_RAW_ID_NOT_IN_STAGED_LEDGER','signing_date':r.get('signing_date')});continue
 urls=[(f,r.get(f)) for f in ['html_url','pdf_url','full_text_xml_url'] if r.get(f)]
 for f,u in urls:
  parsed=urlparse(u)
  if parsed.scheme!='https' or parsed.hostname not in {'www.federalregister.gov','www.govinfo.gov'}:
   issues.append({'eo_id':k,'reason':'UNAPPROVED_OR_INVALID_URL','value':u});continue
  if '/documents/' not in parsed.path and '/content/pkg/' not in parsed.path:
   issues.append({'eo_id':k,'reason':'UNRECOGNIZED_EXPLICIT_LINK','value':u});continue
  state=ids[k][1];prio=(4 if k in blind else 0)+(3 if state=='indeterminate' else 0)+(2 if k in queued else 0)+(1 if k in referenced else 0)
  rows.append({'instrument_id':k,'source_label':raw_source_label,'url':u,'field':f,'source_kind':'FROZEN_OFFICIAL_FR_API_EXPORT','signing_date':r.get('signing_date'),'publication_date':r.get('publication_date'),'citation':r.get('citation'),'stage11_substantive_status':state,'priority_score':prio,'blind_sample_member':k in blind,'in_stage11_priority_queue':k in queued,'url_provenance':'LITERAL_URL_IN_CACHED_2026_OFR_METADATA','local_download_verified':False})
# Distinct provenance links; one order may have multiple official URL formats.
byurl={}
for r in rows:
 if r['url'] not in byurl or r['priority_score']>byurl[r['url']]['priority_score']:byurl[r['url']]=r
rows=sorted(byurl.values(),key=lambda r:(-r['priority_score'],r['instrument_id'],r['field']))
fields=['instrument_id','source_label','url','field','source_kind','signing_date','publication_date','citation','stage11_substantive_status','priority_score','blind_sample_member','in_stage11_priority_queue','url_provenance','local_download_verified']
with open(out/'OFFICIAL_DIRECT_DOCUMENT_FETCH_MANIFEST.csv','w',encoding='utf8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
with open(out/'OFFICIAL_EXPORT_JOIN_EXCEPTION_LOG.jsonl','w') as f:
 for r in issues:f.write(json.dumps(r)+'\n')
metric={'federal_register_raw_records':len(raw),'explicit_direct_document_urls':len(rows),'unique_orders_with_explicit_direct_document_urls':len({r['instrument_id'] for r in rows}),'unknown_orders_with_direct_urls':len({r['instrument_id'] for r in rows if r['stage11_substantive_status']=='indeterminate'}),'priority_queue_orders_with_direct_urls':len({r['instrument_id'] for r in rows if r['in_stage11_priority_queue']}),'blind_review_orders_with_direct_urls':len({r['instrument_id'] for r in rows if r['blind_sample_member']}),'by_format':dict(collections.Counter(r['field'] for r in rows)),'raw_unmatched_or_invalid_rows':len(issues),'downloaded_by_this_script':0,'warning':'URLs are provenance for fetching full original representations; availability/authenticity and content not yet verified. Older malformed body_html_url fields intentionally excluded.'}
(out/'OFFICIAL_FETCH_MANIFEST_METRICS.json').write_text(json.dumps(metric,indent=2)+'\n');print(json.dumps(metric,indent=2))
