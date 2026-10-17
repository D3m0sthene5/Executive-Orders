#!/usr/bin/env python3
"""Build an explicitly provisional, non-destructive Stage16<->Opus checkpoint2 reconciliation.
This does not certify any of Opus's legal findings.
"""
import zipfile, hashlib, json, io, csv, os, shutil, sqlite3, collections, pathlib, sys
OPUS = pathlib.Path(sys.argv[1] if len(sys.argv)>1 else '/mnt/data/OPUS_STAGE11_CHECKPOINT2_SUMMARY.zip')
ASTRA = pathlib.Path(sys.argv[2] if len(sys.argv)>2 else '/mnt/data/EO_STAGE16_SCIENTIFIC_RECONSTRUCTION_2026-10-16(1).zip')
OUT = pathlib.Path(sys.argv[3] if len(sys.argv)>3 else '/mnt/data/EO_STAGE17_COORDINATOR_BRIDGE_2026-10-16')
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'REPORTS').mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
shafile=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
zo=zipfile.ZipFile(OPUS); za=zipfile.ZipFile(ASTRA)
get=lambda z,tail:next(n for n in z.namelist() if n.endswith('/'+tail))
raw_jsonlines=lambda t:[json.loads(x) for x in zo.read(get(zo,t)).splitlines() if x.strip()]
accepted=raw_jsonlines('STAGE11_ACCEPTED.jsonl')
statusrecords=raw_jsonlines('STAGE11_STATUS_RECORDS.jsonl')
held=raw_jsonlines('STAGE11_HELD_QUEUE.jsonl')
conflicts=raw_jsonlines('CONFLICT_LOG.jsonl')
unprocessed=raw_jsonlines('UNPROCESSED_WORKLIST.jsonl')
accounting=json.loads(zo.read(get(zo,'ACCOUNTING.json')))
assert len(accepted)==540 and len(set(x['instrument_id'] for x in accepted))==540
assert collections.Counter(x['final_substantive_effect'] for x in accepted)=={'yes':75,'no':465}
assert len(statusrecords)==747 and len(held)==531 and len(conflicts)==155 and len(unprocessed)==414
assert sha(za.read(get(za,'PINNED_INPUTS/RECONCILED_STATUS_LEDGER_STAGE11_PROVISIONAL.jsonl'))) == accounting['baseline_source'].split('sha256 ')[1]
assert sha(zo.read(get(zo,'RECONCILED_STATUS_LEDGER_STAGE11_OPUS_PATCHED.jsonl')))==accounting['patched_ledger_sha256']
origdb = OUT/'STAGE16_PLUS_OPUS_CHECKPOINT2_PROVISIONAL.sqlite'
with za.open(get(za,'DATA/AFTERLIFE_STAGE16_CANONICAL.sqlite')) as src,open(origdb,'wb') as dest:shutil.copyfileobj(src,dest)
original_stage16_db_sha=shafile(origdb)
conn=sqlite3.connect(str(origdb));conn.row_factory=sqlite3.Row
base_counts=dict(conn.execute('select original_legacy_status,count(*) from instruments where include_proxy=1 group by 1').fetchall())
assert base_counts=={'indeterminate':12457,'no':2322,'yes':193},base_counts
c=conn.cursor()
c.executescript('''
CREATE TABLE opus_checkpoint2_import (
 instrument_id TEXT PRIMARY KEY REFERENCES instruments(id),
 substantive_status TEXT NOT NULL CHECK (substantive_status IN ('yes','no')),
 any_effect_status TEXT NOT NULL CHECK (any_effect_status IN ('yes','no','indeterminate')),
 reviewer_verdict TEXT,
 origin_lane TEXT,
 shard TEXT,
 source_text_obtained INTEGER,
 source_grade TEXT,
 footprint_complete INTEGER,
 historical_first_cause_status TEXT NOT NULL DEFAULT 'UNKNOWN',
 evidence_directory_declared TEXT,
 review_directory_declared TEXT,
 evidence_originals_in_supplied_opus_zip INTEGER NOT NULL DEFAULT 0,
 human_certified INTEGER NOT NULL DEFAULT 0,
 import_review_grade TEXT NOT NULL DEFAULT 'AI_ACCEPTED_PROVISIONAL_MISSING_COMPANION_ORIGINALS',
 status_review_record_json TEXT NOT NULL
);
CREATE TABLE opus_checkpoint2_work_state (
 instrument_id TEXT PRIMARY KEY,
 decision_state TEXT,
 raw_record_json TEXT NOT NULL
);
CREATE TABLE opus_checkpoint2_held (
 instrument_id TEXT PRIMARY KEY,
 raw_record_json TEXT NOT NULL
);
CREATE TABLE opus_checkpoint2_unprocessed (
 instrument_id TEXT PRIMARY KEY,
 raw_record_json TEXT NOT NULL
);
CREATE TABLE opus_checkpoint2_conflicts (
 seq INTEGER PRIMARY KEY,
 instrument_id TEXT,
 raw_record_json TEXT NOT NULL
);
CREATE TABLE coordinator_import_metadata (
 key TEXT PRIMARY KEY, value TEXT NOT NULL
);
CREATE VIEW reconciled_legacy_checkpoint2_provisional AS
 SELECT i.id, i.canonical_group, i.issuance_date, i.include_proxy,
 i.original_legacy_status AS stage16_inherited_legacy_status,
 CASE WHEN o.instrument_id IS NOT NULL THEN o.substantive_status ELSE i.original_legacy_status END AS combined_legacy_provisional_status,
 i.original_any_effect AS stage16_inherited_any_effect,
 CASE WHEN o.instrument_id IS NOT NULL THEN o.any_effect_status ELSE i.original_any_effect END AS combined_any_effect_provisional_status,
 CASE WHEN o.instrument_id IS NOT NULL THEN o.import_review_grade ELSE 'STAGE16_INHERITED_STAGE11_PROVISIONAL' END AS origin_and_review_grade,
 COALESCE(o.human_certified, 0) AS human_verified_of_import,
 CASE WHEN o.instrument_id IS NOT NULL THEN 1 ELSE 0 END AS opus_checkpoint2_accepted_imported
 FROM instruments i LEFT JOIN opus_checkpoint2_import o ON i.id=o.instrument_id WHERE i.include_proxy=1;
CREATE TRIGGER block_opus_import_certification BEFORE UPDATE OF human_certified ON opus_checkpoint2_import
 WHEN NEW.human_certified=1
 BEGIN SELECT RAISE(ABORT, 'Use independent human review docket + supporting evidence; imported AI review is never itself human certification'); END;
''')
for r in statusrecords:
 c.execute('INSERT INTO opus_checkpoint2_work_state VALUES(?,?,?)', (r['instrument_id'],r['decision_state'],json.dumps(r,ensure_ascii=False,sort_keys=True)))
for r in held:
 c.execute('INSERT INTO opus_checkpoint2_held VALUES(?,?)',(r['instrument_id'],json.dumps(r,ensure_ascii=False,sort_keys=True)))
for r in unprocessed:
 c.execute('INSERT INTO opus_checkpoint2_unprocessed VALUES(?,?)',(r['instrument_id'],json.dumps(r,ensure_ascii=False,sort_keys=True)))
for i,r in enumerate(conflicts):
 c.execute('INSERT INTO opus_checkpoint2_conflicts VALUES(?,?,?)',(i+1,r.get('instrument_id'),json.dumps(r,ensure_ascii=False,sort_keys=True)))
by_status={r['instrument_id']:r for r in statusrecords}
blines=[]
for r in accepted:
 id=r['instrument_id'];s=by_status[id]
 rr=c.execute('SELECT include_proxy,original_legacy_status,issuance_date FROM instruments WHERE id=?',(id,)).fetchone()
 assert rr is not None and rr['include_proxy']==1 and rr['original_legacy_status']=='indeterminate',(id,rr)
 c.execute('INSERT INTO opus_checkpoint2_import(instrument_id,substantive_status,any_effect_status,reviewer_verdict,origin_lane,shard,source_text_obtained,source_grade,footprint_complete,historical_first_cause_status,evidence_directory_declared,review_directory_declared,status_review_record_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(
 id,r['final_substantive_effect'],r['final_any_operative_EO_effect'],r['review_verdict'],r['lane'],r['shard'],int(bool(s.get('text_obtained'))),str(s.get('text_source_grade')),int(bool(s.get('footprint_complete'))),str(s.get('historical_causes') or 'UNKNOWN'),str(s.get('evidence_dir') or ''),str(s.get('review_dir') or ''),json.dumps(s,ensure_ascii=False,sort_keys=True)))
 # Elevated QA cases include index-only source, no whole footprint, disagreement on other axis
 risk=[]
 if not s.get('text_obtained'):risk.append('ORIGINAL_TEXT_NOT_OBTAINED')
 if s.get('text_source_grade')=='index_only':risk.append('INDEX_ONLY_INFERENCE')
 if not s.get('footprint_complete'):risk.append('PARTIAL_FOOTPRINT_YES')
 if s.get('review_verdict')=='reject_to_indeterminate':risk.append('REVIEWER_AXIS_DISAGREEMENT')
 if id.startswith('EO:UN:'):risk.append('UNNUMBERED_IDENTITY_REVIEW_REQUIRED')
 if r['final_any_operative_EO_effect']=='indeterminate':risk.append('ANY_EFFECT_AXIS_UNRESOLVED')
 if r['lane']=='C_NARA_TEMPORARY':risk.append('ORIGINAL_EXPIRATION_CAUSATION_PRIORITY')
 blines.append({'instrument_id':id,'issuance_date':rr['issuance_date'],'opus_status':r['final_substantive_effect'],'opus_any_effect':r['final_any_operative_EO_effect'],'lane':r['lane'],'reviewer_verdict':r['review_verdict'],'source_grade':s['text_source_grade'],'text_obtained':int(bool(s.get('text_obtained'))),'footprint_complete':int(bool(s.get('footprint_complete'))),'first_cause_still_unknown':1,'originals_attached':0,'risk_flags':';'.join(risk)})
for k,v in {'opus_archive_sha256':shafile(OPUS),'astra_archive_sha256':shafile(ASTRA),'original_stage16_canonical_sqlite_sha256':original_stage16_db_sha,'opus_patched_ledger_sha256':accounting['patched_ledger_sha256'],'shared_immutable_stage11_input_sha256':accounting['baseline_source'].split('sha256 ')[1],'Opus_companion_originals_present':'false','human_certification_count':'0','origin':'COORDINATOR_PROVISIONAL_BRIDGE_DO_NOT_CERTIFY'}.items():
 c.execute('INSERT INTO coordinator_import_metadata VALUES(?,?)',(k,str(v)))
conn.commit()
combined=dict(c.execute('SELECT combined_legacy_provisional_status,count(*) FROM reconciled_legacy_checkpoint2_provisional GROUP BY 1').fetchall())
assert combined=={'indeterminate':11917,'yes':268,'no':2787},combined
assert c.execute('select count(*) from opus_checkpoint2_import').fetchone()[0]==540
assert c.execute('select count(*) from v3_effect_assessments').fetchone()[0]==5
assert c.execute('select count(*) from original_stage11_rows').fetchone()[0]==15010
assert c.execute('select count(*) from legal_episode').fetchone()[0]==21
assert c.execute('select count(*) from legal_event').fetchone()[0]==438
assert c.execute('select count(*) from opus_checkpoint2_import x join v3_effect_assessments v on x.instrument_id=v.id').fetchone()[0]==0
assert c.execute('select count(*) from opus_checkpoint2_import where human_certified=1').fetchone()[0]==0
assert c.execute('select count(*) from candidate_relationships where eligible_for_research=1').fetchone()[0]==7084
assert c.execute('select count(*) from opus_checkpoint2_held').fetchone()[0]==531
assert c.execute('select count(*) from opus_checkpoint2_conflicts').fetchone()[0]==155
assert c.execute('select count(*) from opus_checkpoint2_unprocessed').fetchone()[0]==414
assert c.execute('select count(*) from opus_checkpoint2_work_state').fetchone()[0]==747
# Fresh v3 research retained without promotion
c.execute('PRAGMA integrity_check');res=c.fetchone()[0];assert res=='ok',res
# Guard counterexample
try:
 c.execute("UPDATE opus_checkpoint2_import SET human_certified=1 WHERE instrument_id='EO:10262'")
 raise AssertionError('Unexpected human-certification transition succeeded')
except sqlite3.IntegrityError as e:
 assert 'Use independent human review' in str(e)
conn.rollback()
conn.close()
with open(OUT/'REPORTS'/'OPUS_ACCEPTED_540_RECONCILED.csv','w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(blines[0]));w.writeheader();w.writerows(sorted(blines,key=lambda x:x['instrument_id']))
meta={'baseline_codebook':'2.0.0 (frozen)','Stage16_codebook':'3.0.0-research (v3 parallel)','baseline_unique_working_proxies':14972,'stage16_inherited':base_counts,'opus_statuses_imported_as_provisional':540,'opus_added_yes':75,'opus_added_no':465,'status_after_non_destructive_import':combined,'provisional_determinate':combined['yes']+combined['no'],'provisional_coverage_pct':(combined['yes']+combined['no'])/14972*100,'new_v3_independently_certified':0,'new_whole_order_first_causes_stage16':0,'human_verified_opus':0,'stage16_v3_assessment_overlap_with_opus':0,'held_queue_not_promoted':531,'unprocessed_worklist_not_promoted':414,'opus_checkpoint2_conflicts_preserved':155,'opus_status_records':747,'missing_companion_evidence_and_originals':True,'bridge_certification':'STRUCTURAL_RECONCILIATION_ONLY','stage16_sqlite_sha_before_bridge':original_stage16_db_sha,'stage17_bridge_db_sha_after_merge':shafile(origdb),'opus_zip_sha':shafile(OPUS),'astra_zip_sha':shafile(ASTRA)}
(OUT/'REPORTS'/'RECONCILIATION.json').write_text(json.dumps(meta,indent=2)+'\n')
(OUT/'README_FIRST.md').write_text('''# Stage 17 coordinator bridge — PROVISIONAL, structurally reconciled\n\nThis bridge is an **overlay of Opus Stage 11 Checkpoint 2 AI-reviewed determinations onto Astra Stage 16's independent canonical research release**, not a human/legal certification and not a new source-verified case adjudication. It is intentionally NOT written back to the original Stage 16 SQLite database or any permanent Library file.\n\n## Verified structural merge\n\nBoth uploaded ZIPs share exactly the immutable Stage 11 ledger SHA `c0308e008cd719cd153ca667271c93267d5d855bf3eb26d48076e41938fc7729`. Stage 16's immutable source data, 15,010 original rows, canonical 14,972 working proxies, 21 episodes, 438 events, and separate v3 research statuses are preserved. All 540 Opus accepted decisions match currently included, previously UNKNOWN Stage 16 identities, with zero overlap with its five v3 assessments.\n\nThe resulting **provisional coverage** is 268 YES / 2,787 NO / 11,917 UNKNOWN = 3,055/14,972 = 20.404756%. Opus counted 3,055/14,973 = 20.403393% because it did not carry Astra's one-proxy deduplication. Neither is the fraction of the actual historical universe of issued executive orders or the percent of completed causal histories.\n\n## Critical evidence limitation\n\nOpus's SUMMARY ZIP contains review descriptions, 747 status records, 540 accepted status labels, 531 held records, 414 unprocessed worklist entries, and 155 conflict entries, but it contains **no referenced `evidence/` files and no companion original document images**. Its `REPORT.md` refers to an additional `OPUS_STAGE11_CHECKPOINT2_EVIDENCE_ORIGINALS.zip`, which was not among the two supplied ZIPs. The Opus AI-review agreement is inherited as provisional, not independently source-adjudicated. Reacquire referenced originals and independent extracts before accepting as v3 or human-certified.\n\nSpecial reviews worth retrieving early: EO:4872 (original missing, index-only whole-land inference); EO:UN:executive-orders-01:row:3 (1856 unnumbered identity original missing); EO:12446 (positive continuity despite incomplete full footprint; potentially defensible on identified surviving clause); EO:9616 (NO substantive, indeterminate any-effect because saved survivor rights). Those are qualification cases, not established errors.\n\nThe entire set of 540 has `historical_causes = UNKNOWN`; notably 155 NO cases come from Opus's temporary-order lane. They are high-priority *hypotheses* for natural-expiration history reconstruction, requiring checks for amendments, extensions, saving clauses, and earlier termination.\n\nStage16 quarantines two editorial EO12553 relationship claims (`EO:11920` and `EO:12395`) because they are absent from the cached original 386-target revocation schedule. Its retained formal-event graph is NOT proof of the first cessation of those orders.\n\n## What the bridge holds\n\n`STAGE16_PLUS_OPUS_CHECKPOINT2_PROVISIONAL.sqlite` retains Stage 16's tables, plus a reversible, separate `opus_checkpoint2_import` table; all 747 status work records, 531 held, 414 unprocessed, 155 conflicts; and the view `reconciled_legacy_checkpoint2_provisional`. A trigger prohibits promoting imported AI results as human-verified. Original Stage16 immutable tables and v3 statuses are untouched.\n\n`REPORTS/OPUS_ACCEPTED_540_RECONCILED.csv` is an import-level audit list with source quality and risks. `REPORTS/RECONCILIATION.json` contains reproducible counts and archive checksums. `build_stage17_bridge.py` regenerates the overlay from the two original ZIPs and validates all counts.\n\n## Intended next step\n\nUse this bridge as a lossless accelerator inside Astra's existing **chat** session. Reinspect all originals and review dependencies before any v3 status certification. Integrate human-review cases as source-anchored claims with permanent review records. Do not treat raw Opus accepted statuses, Stage16 event counts, or library scripts as independently proven legal histories. No other active AI research branch is assumed.\n''')
shutil.copyfile(__file__,OUT/'build_stage17_bridge.py')
print(json.dumps(meta,indent=2))
