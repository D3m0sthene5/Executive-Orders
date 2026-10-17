"""Reproduce original 1943-ID cohort mismatch against frozen Stage11 ledger."""
import csv,json,sys,pathlib,hashlib
csvp,ledgerp,outdir=sys.argv[1:4];out=pathlib.Path(outdir);out.mkdir(parents=True,exist_ok=True)
with open(csvp,encoding='utf-8-sig',newline='') as f:
 cr=list(csv.DictReader(f))
ids={r['canonical_id'] for r in cr if r['in_original_1943_queue'].lower() in ('1','true','yes')}
with open(ledgerp,encoding='utf8') as f:
 lr=(json.loads(x) for x in f if x.strip()); flagged={r['instrument_id'] for r in lr if r.get('original_1943_cohort') is True}
extra=sorted(flagged-ids);missing=sorted(ids-flagged)
assert len(cr)==1943 and len(ids)==1943 and len(flagged)==1950 and len(extra)==7 and not missing
result={'source_csv_sha256':hashlib.sha256(pathlib.Path(csvp).read_bytes()).hexdigest(),'frozen_stage11_sha256':hashlib.sha256(pathlib.Path(ledgerp).read_bytes()).hexdigest(),'source_csv_records':len(cr),'source_ids':len(ids),'stage11_flagged_ids':len(flagged),'false_positive_flags':extra,'missing_orig_ids':missing,'corrected_membership_count':len(ids),'legal_status_change':False,'correction_status':'DIRECTLY_VERIFIED_WITH_SOURCE_CSV_AND_STAGE11'}
(out/'ORIGINAL_1943_FLAG_ERROR_VERIFIED.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
