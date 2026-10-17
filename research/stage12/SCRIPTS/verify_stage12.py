#!/usr/bin/env python3
"""Read-only verification of Stage12 outputs; optional baseline and source arguments."""
import sys,json,hashlib,collections,pathlib,csv
p=pathlib.Path(sys.argv[3] if len(sys.argv)>3 else pathlib.Path(__file__).resolve().parents[1])
def jsonl(x):return [json.loads(l) for l in open(p/x,encoding='utf8') if l.strip()]
def sha(f):
 h=hashlib.sha256()
 with open(f,'rb') as z:
  for b in iter(lambda:z.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
metrics=json.load(open(p/'QA/RELEASE_METRICS.json'))
assert metrics['original_ledger_rows']==15010
assert metrics['audited_unique_document_proxies']==14972
assert metrics['original_effect_totals']=={'yes':193,'no':2322,'indeterminate':12458}
assert metrics['audited_proxy_effect_totals']=={'yes':193,'no':2322,'indeterminate':12457}
assert metrics['undated_post_overlay']==118
assert metrics['unnumbered_source_only_OCR_date_line_leads']==717
assert metrics['unnumbered_leads_not_included_denominator']
assert metrics['no_legal_status_changes']
r=jsonl('DATA/STAGE12_NORMALIZED_NONDESTRUCTIVE_15010.jsonl');assert len(r)==15010
ids={x['instrument_id']:x for x in r};assert len(ids)==15010
u=[x for x in r if x['included_unique_document_proxy']];assert len(u)==14972
assert collections.Counter(x['substantive_effect_original'] for x in u)=={'yes':193,'no':2322,'indeterminate':12457}
assert ids['EO:7933A']['canonical_document_group']=='EO:7933a'
assert not ids['EO:7933A']['included_unique_document_proxy'] and ids['EO:7933a']['included_unique_document_proxy']
assert ids['EO:8969']['signing_date_audit_projection']=='1941-12-11'
assert ids['EO:10276']['signing_date_audit_projection']=='1951-07-31'
assert ids['EO:13174']['signing_date_audit_projection']=='2000-10-27' and ids['EO:13174']['signing_date_conflict']
assert ids['EO:13333']['signing_date_audit_projection']=='2004-03-16'
assert sum(not x['year_audit_projection'] for x in u)==118
for id in ['2','4','8','11','61','65','205']:
 key=f'EO:UN:executive-orders-01:row:{id}';assert not ids[key]['cohort_provenance_overlay']
leads=jsonl('DATA/LORD_1943_DATE_LEADS_SOURCE_ONLY.jsonl');assert len(leads)==717
assert len({x['source_lead_id'] for x in leads})==717
assert all(x['status']=='SOURCE_ONLY_UNREVIEWED_NOT_EO_IDENTITY' for x in leads)
assert all(x['date_label_provisional'] is None and x['year_provisional'] is None for x in leads)
assert len(jsonl('DATA/LORD_1943_PAGE_REGISTER_226.jsonl'))==226
with open(p/'QA/BLIND_PRESENT_STATUS_AUDIT_60.csv',newline='') as f:blind=list(csv.DictReader(f))
assert len(blind)==60 and len(set(x['instrument_id'] for x in blind))==60
assert all(set(x)=={'blind_case_id','instrument_id','original_signing_date_audit_projection','source_quality_class','instructions'} for x in blind)
with open(p/'QA/IDENTITY_AUTHENTICATION_SAMPLE_30.csv',newline='') as f:identity=list(csv.DictReader(f))
assert len(identity)==30 and len(set(x['instrument_id'] for x in identity))==30
with open(p/'QA/ANNUAL_OFR_RECONCILIATION.csv',newline='') as f:years=list(csv.DictReader(f))
assert len([x for x in years if x['difference']!='0'])==4
assert set(int(x['year']) for x in years if x['difference']!='0')=={1937,1941,1951,2009}
if len(sys.argv)>1:
 ledger=pathlib.Path(sys.argv[1]);assert sha(ledger)==metrics['baseline_sha256']
if len(sys.argv)>2:
 pdf=pathlib.Path(sys.argv[2]);assert sha(pdf)==metrics['lord_pdf_sha256']
print('PASS Stage12: 15,010 preserved original references, 14,972 unique proxies, 4 metadata dates, one proven alias collision, 717 quarantined OCR leads, 60 blind-status cases, 30 identity cases, no legal-status promotions')
