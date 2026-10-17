"""Append independent NARA historical bibliographic reference dates without changing EO legal statuses.
Run: python build_source_date_overlay.py STAGE12_OVERLAY_JSONL STAGE10_IMPORT_ZIP OUTPUT_DIR
All 18 dates describe NARA source-row labels, NOT authenticated original signatures.
"""
import zipfile,json,sys,pathlib,csv,collections,hashlib,datetime,re
p_in,p_zip,p_out=sys.argv[1:4];out=pathlib.Path(p_out);out.mkdir(parents=True,exist_ok=True)
key='EO_IMPORT_WORK/FULL_RESULTS/UNNUMBERED_SOURCE_ROW_MATCHES.jsonl'
with zipfile.ZipFile(p_zip) as z: imported=[json.loads(x) for x in z.read(key).decode().splitlines() if x.strip()]
assert len(imported)==18
months={'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'June':6,'July':7,'Aug':8,'Sept':9,'Oct':10,'Nov':11,'Dec':12}
def parse(s):
 q=re.match(r'^([A-Za-z]+)\.?\s+(\d{1,2}),\s+(\d{4})$',s)
 assert q,s
 return datetime.date(int(q[3]),months[q[1]],int(q[2])).isoformat()
refs={i['instrument_id']:i for i in imported}
assert len(refs)==18
normalized=[];audit=[];seen=set()
with open(p_in,encoding='utf8') as f:
 for line in f:
  r=json.loads(line);ident=r['instrument_id'];
  r['nara_1989_bibliographic_reference_date']=None
  r['nara_1989_date_reference_url']=None
  r['nara_1989_reference_authentication']='NOT_APPLICABLE'
  r['nara_1989_date_not_original_signature_verified']=False
  if ident in refs:
   row=refs[ident];dt=parse(row['identity_date_only_original_label']);seen.add(ident)
   r['nara_1989_bibliographic_reference_date']=dt
   r['nara_1989_date_reference_url']=row['source_url']
   r['nara_1989_reference_authentication']='OFFICIAL_EDITORIAL_LABEL_NOT_ORIGINAL_SIGNATURE'
   r['nara_1989_date_not_original_signature_verified']=True
   assert r['signing_date_audit_projection'] is None,(ident,r['signing_date_audit_projection'])
   audit.append(dict(instrument_id=ident,reference_date=dt,raw_label=row['identity_date_only_original_label'],year=int(dt[:4]),signing_date_original=r['signing_date_original'],signing_date_stage12_projection=r['signing_date_audit_projection'],editorial_as_of=row['editorial_as_of'],editorial_category=row['editorial_category'],source_kind=row['source_kind'],source_url=row['source_url'],original_html_sha256=row['raw_source_sha256'],signature_authentication='NOT_REVIEWED',unique_document_authentication='NOT_REVIEWED',included_unique_document_proxy=r['included_unique_document_proxy']))
  normalized.append(r)
assert seen==set(refs),(seen.symmetric_difference(refs))
audit.sort(key=lambda x:(x['reference_date'],x['instrument_id']))
# Possible 1914 row collisions require review of physical originals.
bydate=collections.defaultdict(list)
for x in audit:bydate[x['reference_date']].append(x['instrument_id'])
collisions={k:v for k,v in bydate.items() if len(v)>1}
assert collisions=={'1914-08-08':['EO:UN:executive-orders-01:row:12','EO:UN:executive-orders-01:row:71']},collisions
csvpath=out/'NARA_UNNUMBERED_EDITORIAL_DATES_18.csv'
with csvpath.open('w',newline='',encoding='utf8') as f:
 w=csv.DictWriter(f,fieldnames=list(audit[0]));w.writeheader();w.writerows(audit)
with (out/'STAGE13_DATE_REFERENCE_OVERLAY_15010.jsonl').open('w') as f:
 for r in normalized:f.write(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n')
unique=[r for r in normalized if r['included_unique_document_proxy']]
assert len(unique)==14972
assert sum(r['substantive_effect_original']!='indeterminate' for r in unique)==2515
originallydated=sum(bool(r['signing_date_audit_projection']) for r in unique)
sourceonly=sum(bool(r['nara_1989_bibliographic_reference_date']) and not r['signing_date_audit_projection'] for r in unique)
assert sourceonly==18 and originallydated==14854,(sourceonly,originallydated)
assert sum(not r['signing_date_audit_projection'] and not r['nara_1989_bibliographic_reference_date'] for r in unique)==100
agg=collections.defaultdict(lambda:collections.Counter())
for r in unique:
 dt=r['signing_date_audit_projection'];other=r['nara_1989_bibliographic_reference_date'];year=int((dt or other)[:4]) if dt or other else None
 label=f'{(year//10)*10}s' if year else 'UNKNOWN_DATE';kind='stage12_signed_date_projection' if dt else 'NARA_1989_EDITORIAL_DATE_REFERENCE_ONLY' if other else 'no_date'
 agg[label][(kind,r['substantive_effect_original'])]+=1
allkinds=['stage12_signed_date_projection','NARA_1989_EDITORIAL_DATE_REFERENCE_ONLY']
states=['yes','no','indeterminate']
rows=[]
for label in sorted([x for x in agg if x!='UNKNOWN_DATE'],key=lambda s:int(s[:-1]))+['UNKNOWN_DATE']:
 rr={'decade':label}
 for typ in allkinds:
  for st in states:rr[typ+'_'+st]=agg[label][(typ,st)]
 rr['total']=sum(agg[label].values());rr['determined']=sum(v for (t,st),v in agg[label].items() if st!='indeterminate');rr['coverage_percent']=round(100*rr['determined']/rr['total'],3) if rr['total'] else 0
 rows.append(rr)
with (out/'STATUS_BY_DECADE_WITH_NARA_DATE_REFERENCE.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
summary=dict(stage11_ledger_rows=len(normalized),deduped_stage12_candidate_population=len(unique),substantive_determinate=sum(r['substantive_effect_original']!='indeterminate' for r in unique),coverage_percent=100*2515/14972,stage12_original_date_projection_count=originallydated,NARA_new_editorial_date_reference_count=sourceonly,remaining_no_date_after_reference_overlay=100,historical_pre1862_editorial_date_refs=sum(x['year']<1862 for x in audit),potential_same_date_distinct_document_collisions=collisions,nara_rows_source_zip_sha256=hashlib.sha256(pathlib.Path(p_zip).read_bytes()).hexdigest(),all_date_references_are_provisional=True,claim_full_historical_census=False)
(out/'DATE_REFERENCE_OVERLAY_METRICS.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
