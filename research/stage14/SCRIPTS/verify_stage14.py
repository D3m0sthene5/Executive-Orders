#!/usr/bin/env python3
"""Fail closed on Stage14 structural, source, legal-label and blind-audit invariants."""
import collections,csv,hashlib,json,pathlib,sqlite3,sys,zipfile
p=pathlib.Path(sys.argv[1]);db=sqlite3.connect(p/'DATA/EO_SOURCE_DEPENDENCY_GRAPH.sqlite')
assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
assert db.execute('SELECT COUNT(*) FROM orders').fetchone()[0]==15010
assert db.execute('SELECT SUM(included_validated),SUM(include_unique) FROM orders').fetchone()==(14973,14972)
assert dict(db.execute('SELECT substantive,COUNT(*) FROM orders WHERE included_validated=1 GROUP BY 1'))=={'yes':193,'no':2322,'indeterminate':12458}
assert db.execute('SELECT COUNT(*) FROM observations').fetchone()[0]==11164
assert db.execute('SELECT COUNT(*) FROM relationships WHERE quarantined=0').fetchone()[0]==6575
assert db.execute('SELECT COUNT(*) FROM relationships WHERE quarantined=1').fetchone()[0]==117
assert db.execute('SELECT COUNT(*) FROM queues').fetchone()[0]==2841
assert db.execute('SELECT COUNT(*) FROM sources').fetchone()[0]==25
assert db.execute('SELECT COUNT(*) FROM observations WHERE source_sha256 NOT IN (SELECT key FROM sources)').fetchone()[0]==0
assert db.execute("SELECT COUNT(*) FROM problem_flags WHERE code='CROSS_SOURCE_ACTOR_DISAGREEMENT'").fetchone()[0]==15
assert db.execute('SELECT COUNT(*) FROM audit_sample').fetchone()[0]==60
assert db.execute('SELECT COUNT(*) FROM cache_representations').fetchone()[0]==1051
assert db.execute('SELECT COUNT(*) FROM cache_blobs').fetchone()[0]==966
assert db.execute("SELECT COUNT(*) FROM cache_representations WHERE checksum_verdict='CONFLICTING_DECLARED_TEXT_SHA256'").fetchone()[0]==0
assert db.execute('SELECT COUNT(*) FROM cache_fts').fetchone()[0]==966
assert db.execute('SELECT COUNT(*) FROM orders WHERE substantive=\'no\' AND cause_mechanism=\'unknown\' AND included_validated=1').fetchone()[0]==2216
# Unique document proxy counts are from Stage13 sidecar; no original Stage11 records mutated.
for id in ['EO:7933A','EO:7933a']:
 assert db.execute('SELECT COUNT(*) FROM orders WHERE id=?',(id,)).fetchone()[0]==1
assert db.execute("SELECT include_unique FROM orders WHERE id='EO:7933A'").fetchone()[0]==0
assert db.execute("SELECT include_unique FROM orders WHERE id='EO:7933a'").fetchone()[0]==1
raw_metrics=json.loads((p/'REPORTS/ENGINE_METRICS.json').read_text())
assert raw_metrics['frozen_baseline']['new_status_promotions']==0
link=json.loads((p/'QUEUES/OFFICIAL_FETCH_MANIFEST_METRICS.json').read_text())
assert link['explicit_direct_document_urls']==4331
assert link['raw_unmatched_or_invalid_rows']==0
assert link['downloaded_by_this_script']==0
assert not (p/'SOURCES/OFFICIAL_PRIMARY_CACHE/EO_12900_641a2ac375c6.html').exists()
assert len(list(csv.DictReader((p/'QUEUES/OFFICIAL_DIRECT_DOCUMENT_FETCH_MANIFEST.csv').open())))==4331
no_source_notes=list((p/'QUEUES/OFFICIAL_EXPORT_JOIN_EXCEPTION_LOG.jsonl').open())
assert len(no_source_notes)==0
with open(p/'QUEUES/EXECUTION_ACTIONS_DEPENDENCY_FIRST.csv',newline='') as f:
 actorrows=list(csv.DictReader(f))
assert len(actorrows)==1029
assert actorrows[0]['actor']=='EO:12553'
assert actorrows[0]['plausible_cached_actor_originals']!='0'
assert actorrows[1]['actor']=='EO:11408'
assert actorrows[1]['known_scope_risk']
ld=list((p/'LORD/LORD_CHRONOLOGICAL_REVIEW_LEADS.jsonl').open())
assert len(ld)==1023
assert all(json.loads(v)['date_status']=='NOT_AUTHENTICATED' for v in ld)
assert all(json.loads(v)['identity_class']=='UNRESOLVED_BIBLIOGRAPHIC_APPEARANCE' for v in ld)
assert len(list(csv.DictReader((p/'LORD/PAGE_REVIEW_PRIORITIES.csv').open())))==226
blindfiles=list((p/'WORKPACKS/BLIND_60').glob('*.json'))
assert len(blindfiles)==60
for q in blindfiles:
 v=json.loads(q.read_text());raw=q.read_text()
 assert 'baseline_substantive' not in raw and 'baseline_any_effect' not in raw and 'baseline_evidence_grade' not in raw
 assert v['classification_allowed_without_source_review'] is False
mass=json.loads((p/'REPORTS/EO12553_INDEPENDENT_SCHEDULE_CROSSWALK.json').read_text())
assert mass['distinct_text_schedule_entries']==386 and mass['distinct_unquarantined_government_actor_targets']==386 and mass['cross_source_exact_match']
# Source original bytes not altered; build/read is deterministic, no upstream mutation.
metrics={'verification':'PASS','verified_database':str(p/'DATA/EO_SOURCE_DEPENDENCY_GRAPH.sqlite'),'frozen_bibliography':14973,'working_unique_proxies':14972,'accepted_status_changes':0,'government_observations':11164,'source_edges_usable_as_leads':6575,'quarantined_edges':117,'cache_blobs':966,'official_links_manifested':4331,'lord_candidates_held':1023,'blind_packets':60,'mass_schedule_identity_reconciled':386,'important_note':'No legal status determination, causation finding, historical order authentication or primary-source retrieval implied.'}
(p/'REPORTS/STAGE14_VERIFICATION.json').write_text(json.dumps(metrics,indent=2)+'\n')
print(json.dumps(metrics,indent=2))
