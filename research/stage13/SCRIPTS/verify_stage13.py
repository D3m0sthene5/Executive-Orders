"""Verify standalone Stage13 release against included frozen Stage12 ZIP and source CSV.
Usage: python SCRIPTS/verify_stage13.py ROOT
Optional external verification sources: original 1943 Lord PDF and Stage10 import ZIP with known SHA256.
"""
import sys,pathlib,zipfile,json,csv,hashlib,collections
root=pathlib.Path(sys.argv[1]);src=root/'SOURCES/STAGE12_FROZEN_BASELINE.zip';assert src.exists()
sha=lambda x:hashlib.sha256(pathlib.Path(x).read_bytes()).hexdigest()
assert sha(root/'SOURCES/EO_Original_1943_Status_Queue_2026-10-14.csv')=='a49f6fef67b36cad9a580fbda860d027e4acf8d86fbf65c05598774581f8cf3c'
assert sha(root/'AUDIT/INDEPENDENT_BLIND_FIRST_EIGHT.jsonl')=='d5ece5abbe4ab0b713921d498ef96a853971631a11ffa244809a32f4eab44234'
with zipfile.ZipFile(src) as z:
 initial=[x for x in z.namelist() if x.endswith('STAGE12_NORMALIZED_NONDESTRUCTIVE_15010.jsonl')];assert len(initial)==1
 baselines=[json.loads(x) for x in z.read(initial[0]).decode().splitlines() if x.strip()]
overlay=[json.loads(x) for x in (root/'CENSUS/STAGE13_DATE_REFERENCE_OVERLAY_15010.jsonl').read_text().splitlines() if x.strip()]
assert len(overlay)==len(baselines)==15010
added={'nara_1989_bibliographic_reference_date','nara_1989_date_reference_url','nara_1989_reference_authentication','nara_1989_date_not_original_signature_verified'}
for b,r in zip(baselines,overlay):
 assert b=={k:v for k,v in r.items() if k not in added},r.get('instrument_id')
 assert set(r)-set(b)==added
unique=[r for r in overlay if r['included_unique_document_proxy']]
assert len(unique)==14972
assert collections.Counter(r['substantive_effect_original'] for r in unique)=={'yes':193,'no':2322,'indeterminate':12457}
assert sum(bool(r['signing_date_audit_projection']) for r in unique)==14854
assert sum(bool(r['nara_1989_bibliographic_reference_date']) for r in unique)==18
assert sum(not r['nara_1989_bibliographic_reference_date'] and not r['signing_date_audit_projection'] for r in unique)==100
assert sum(bool(r['nara_1989_bibliographic_reference_date'] and r['nara_1989_bibliographic_reference_date']<'1862') for r in unique)==3
assert all(r['nara_1989_reference_authentication']=='OFFICIAL_EDITORIAL_LABEL_NOT_ORIGINAL_SIGNATURE' for r in unique if r['nara_1989_bibliographic_reference_date'])
cohort=json.loads((root/'AUDIT/ORIGINAL_1943_FLAG_ERROR_VERIFIED.json').read_text());assert cohort['source_csv_records']==1943 and cohort['stage11_flagged_ids']==1950 and len(cohort['false_positive_flags'])==7
lead=[json.loads(x) for x in (root/'CENSUS/LORD_GEOMETRY_DATE_LEADS.jsonl').open()];assert len(lead)==1023 and all(r['year_candidate'] is None and r['identification_status']=='DATE_MARKER_NOT_VERIFIED_ORDER' for r in lead)
blind=list(csv.DictReader((root/'AUDIT/POSTBLIND_COMPARISON_FIRST_EIGHT.csv').open()));assert len(blind)==8 and sum(r['comparison']=='AGREE' for r in blind)==7 and sum(r['comparison']=='BLIND_INDETERMINATE' for r in blind)==1
assert {r['id'] for r in csv.DictReader((root/'LEGAL/TC07_TC09_ALTERNATIVE_OUTCOME_PANEL.csv').open())} >= {'EO:8885','EO:12553','EO:13286','EO:13284'}
assert (root/'VISUALS/EO_STAGE13_RESEARCH_DASHBOARD.html').exists()
print('PASS — 15,010 frozen source rows preserved with ONLY 4 additive Stage13 NARA fields; statuses identical; 18 editorial dates, 100 still undated, 1023 unvalidated Lord text leads, 7 directly verified false cohort flags, 8 first-pass reviewed cases')
