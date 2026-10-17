#!/usr/bin/env python3
"""Stage17 lossless source-backed merge + legal history; no automatic human certification.
Usage: python code/build_stage17.py --stage16 STAGE16.zip --opus OPUS.zip --bridge-script bridge.py --out ROOT
"""
from __future__ import annotations
import argparse,collections,csv,hashlib,json,os,sqlite3,subprocess,sys,pathlib,shutil,zipfile

EXPECTED_STAGE16_SHA='0a8f4c6f734cfb7c77382426eced747e5dea31175587d86497803afb35036f64'
EXPECTED_STAGE11_SHA='c0308e008cd719cd153ca667271c93267d5d855bf3eb26d48076e41938fc7729'
EXPECTED_OPUS_PATCH_SHA='087e85b9e99afb6a77bc44f1a17ed707dd1b932cd338cf561893a62af53a03f6'
VERSION='3.0.0-research-stage17'; CUTOFF='2026-10-14'
sha=lambda b:hashlib.sha256(b).hexdigest()
canon=lambda v:json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))

def build(stage16,opus,bridge_script,out):
 out=pathlib.Path(out);(out/'data').mkdir(parents=True,exist_ok=True);(out/'reports').mkdir(exist_ok=True)
 stage16=pathlib.Path(stage16);opus=pathlib.Path(opus)
 za=zipfile.ZipFile(stage16);zo=zipfile.ZipFile(opus)
 inner=lambda z,tail:next(x for x in z.namelist() if x.endswith('/'+tail))
 assert sha(za.read(inner(za,'DATA/AFTERLIFE_STAGE16_CANONICAL.sqlite')))==EXPECTED_STAGE16_SHA
 assert sha(za.read(inner(za,'PINNED_INPUTS/RECONCILED_STATUS_LEDGER_STAGE11_PROVISIONAL.jsonl')))==EXPECTED_STAGE11_SHA
 assert sha(zo.read(inner(zo,'RECONCILED_STATUS_LEDGER_STAGE11_OPUS_PATCHED.jsonl')))==EXPECTED_OPUS_PATCH_SHA
 accepted=[json.loads(x) for x in zo.read(inner(zo,'STAGE11_ACCEPTED.jsonl')).splitlines() if x.strip()]
 assert len(accepted)==540 and collections.Counter(x['final_substantive_effect'] for x in accepted)=={'no':465,'yes':75}
 bridgeout=out/'_bridge_tmp'; subprocess.run([sys.executable,str(bridge_script),str(opus),str(stage16),str(bridgeout)],check=True,stdout=subprocess.DEVNULL)
 bridgedb=bridgeout/'STAGE16_PLUS_OPUS_CHECKPOINT2_PROVISIONAL.sqlite'
 target=out/'data'/'AFTERLIFE_STAGE17_CANONICAL.sqlite';shutil.copyfile(bridgedb,target)
 conn=sqlite3.connect(str(target));conn.execute('PRAGMA foreign_keys=ON')
 schema='''
 CREATE TABLE IF NOT EXISTS stage17_source(
 source_id TEXT PRIMARY KEY,subject_id TEXT,issuer TEXT,source_url TEXT NOT NULL,
 document_date TEXT,document_type TEXT,transcript_grade TEXT,local_original_bytes INTEGER NOT NULL,
 stored_representation_sha TEXT,source_excerpt TEXT,acquisition_limit TEXT NOT NULL
 );
 CREATE TABLE IF NOT EXISTS stage17_provision(
 provision_id TEXT PRIMARY KEY,instrument_id TEXT NOT NULL REFERENCES instruments(id),
 source_id TEXT NOT NULL REFERENCES stage17_source(source_id),scope TEXT NOT NULL,
 norm_text TEXT NOT NULL,valid_start TEXT,original_sunset TEXT,
 known_sunset_end_exclusive TEXT,expected_2026_normative TEXT,
 evidence_grade TEXT NOT NULL,remaining_gap TEXT
 );
 CREATE TABLE IF NOT EXISTS stage17_transition(
 transition_id TEXT PRIMARY KEY,affected_provision_id TEXT NOT NULL REFERENCES stage17_provision(provision_id),
 actor_id TEXT,event_date TEXT NOT NULL,kind TEXT NOT NULL,old_rule TEXT,new_rule TEXT,
 source_id TEXT NOT NULL REFERENCES stage17_source(source_id),
 first_cause_inference TEXT NOT NULL CHECK(first_cause_inference IN ('NONE','FIRST_NORMATIVE_SUNSET','INTERMEDIATE_EXTENSION','BOUND_ONLY')),
 causation_grade TEXT NOT NULL,source_review_limit TEXT
 );
 CREATE TABLE IF NOT EXISTS stage17_assessment(
 assessment_id TEXT PRIMARY KEY,instrument_id TEXT NOT NULL REFERENCES instruments(id),
 normative_status TEXT NOT NULL CHECK(normative_status IN ('yes','no','indeterminate')),
 enduring_consequences TEXT NOT NULL,formal_disposition TEXT NOT NULL,policy_continuity TEXT NOT NULL,
 codebook_version TEXT NOT NULL,review_grade TEXT NOT NULL,reviewer_role TEXT NOT NULL,
 rationale TEXT NOT NULL,source_ids_json TEXT NOT NULL,remaining_gaps TEXT NOT NULL,
 human_certified INTEGER NOT NULL DEFAULT 0 CHECK(human_certified=0)
 );
 CREATE TABLE IF NOT EXISTS stage17_catalogue_candidate(
 catalogue_key TEXT PRIMARY KEY,source_id TEXT NOT NULL REFERENCES stage17_source(source_id),
 date_guess TEXT,title_excerpt TEXT,source_page INTEGER,source_row_note TEXT,
 signer_status TEXT NOT NULL,document_authenticated INT NOT NULL DEFAULT 0,
 candidate_state TEXT NOT NULL,matched_existing_instrument TEXT,scope_note TEXT
 );
 CREATE TABLE IF NOT EXISTS stage17_claim(
 claim_id TEXT PRIMARY KEY,instrument_id TEXT NOT NULL REFERENCES instruments(id),
 claim_kind TEXT NOT NULL,claim_scope TEXT NOT NULL,claim_payload TEXT NOT NULL,
 source_ids_json TEXT NOT NULL,policy_version TEXT NOT NULL,fingerprint TEXT NOT NULL
 );
 CREATE TABLE IF NOT EXISTS stage17_review(
 review_id TEXT PRIMARY KEY,claim_id TEXT NOT NULL REFERENCES stage17_claim(claim_id),
 claim_fingerprint TEXT NOT NULL,reviewer_name TEXT NOT NULL,reviewed_at TEXT NOT NULL,
 decision TEXT NOT NULL CHECK(decision IN ('uphold','revise','hold')),
 rationale TEXT NOT NULL,new_claim_text TEXT,
 source_gaps TEXT NOT NULL,review_scope TEXT NOT NULL,
 test_only INT NOT NULL DEFAULT 0,import_hash TEXT NOT NULL,created_state TEXT NOT NULL
 );
 CREATE VIEW IF NOT EXISTS stage17_current_reviews AS
 SELECT r.*,CASE WHEN r.claim_fingerprint=c.fingerprint THEN 1 ELSE 0 END AS still_current
 FROM stage17_review r JOIN stage17_claim c ON c.claim_id=r.claim_id;
 CREATE TRIGGER IF NOT EXISTS stage17_no_human_research_impersonation BEFORE UPDATE OF human_certified ON stage17_assessment
 BEGIN SELECT RAISE(ABORT,'Independent human review required; use stage17_review importer'); END;
 '''
 conn.executescript(schema)
 base=pathlib.Path(__file__).resolve().parent.parent
 sources=json.loads((base/'sources'/'verified_web_source_references.json').read_text())
 for s in sorted(sources,key=lambda x:x['source_id']):
  values=[s.get(k) for k in ('source_id','subject_id','issuer','source_url','document_date','document_type','transcript_grade','local_original_bytes','stored_representation_sha','source_excerpt','acquisition_limit')]
  conn.execute('INSERT INTO stage17_source VALUES (?,?,?,?,?,?,?,?,?,?,?)',values)
 facts=json.loads((base/'sources'/'adjudicated_legal_facts.json').read_text())
 for p in sorted(facts['provisions'],key=lambda x:x['provision_id']):
  conn.execute('INSERT INTO stage17_provision VALUES (?,?,?,?,?,?,?,?,?,?,?)',tuple(p.get(k) for k in ('provision_id','instrument_id','source_id','scope','norm_text','valid_start','original_sunset','known_sunset_end_exclusive','expected_2026_normative','evidence_grade','remaining_gap')))
 for t in sorted(facts['transitions'],key=lambda x:x['transition_id']):
  conn.execute('INSERT INTO stage17_transition VALUES (?,?,?,?,?,?,?,?,?,?,?)',tuple(t.get(k) for k in ('transition_id','affected_provision_id','actor_id','event_date','kind','old_rule','new_rule','source_id','first_cause_inference','causation_grade','source_review_limit')))
 for a in sorted(facts['assessments'],key=lambda x:x['assessment_id']):
  conn.execute('INSERT INTO stage17_assessment VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',tuple(a.get(k) for k in ('assessment_id','instrument_id','normative_status','enduring_consequences','formal_disposition','policy_continuity','codebook_version','review_grade','reviewer_role','rationale','source_ids_json','remaining_gaps','human_certified')))
 for e in sorted(facts['catalogue'],key=lambda x:x['catalogue_key']):
  conn.execute('INSERT INTO stage17_catalogue_candidate VALUES (?,?,?,?,?,?,?,?,?,?,?)',tuple(e.get(k) for k in ('catalogue_key','source_id','date_guess','title_excerpt','source_page','source_row_note','signer_status','document_authenticated','candidate_state','matched_existing_instrument','scope_note')))
 # Claims cover EVERY of the 15,010 raw catalogue/identity rows. No implied human certification.
 instruments=conn.execute('SELECT id,canonical_group,issuance_date,source_population_class,original_legacy_status,include_proxy FROM instruments ORDER BY id').fetchall()
 v3={x[0]:x[1:] for x in conn.execute('SELECT id,normative_status,review_grade FROM v3_effect_assessments')}
 newass={}
 for id,norm,grade,why in conn.execute('SELECT instrument_id,normative_status,review_grade,rationale FROM stage17_assessment'):newass.setdefault(id,[]).append({'normative':norm,'grade':grade,'rationale':why})
 events=collections.defaultdict(list)
 subject_sources=collections.defaultdict(list)
 source_fingerprints={}
 for sid,sub,url,grade,content_sha,excerpt in conn.execute('SELECT source_id,subject_id,source_url,transcript_grade,stored_representation_sha,source_excerpt FROM stage17_source'):
  if sub:subject_sources[sub].append(sid)
  source_fingerprints[sid]=sha(canon({'url':url,'grade':grade,'sha':content_sha,'excerpt':excerpt}).encode())
 for row in conn.execute('SELECT provision_id,instrument_id,scope,known_sunset_end_exclusive FROM stage17_provision'):
  events[row[1]].append({'provision_id':row[0],'scope':row[2],'known_sunset_exclusive':row[3]})
 for id,group,date,pop,legacy,include in instruments:
  orig={'instrument_id':id,'canonical_group':group,'issuance_date':date,'population_class':pop,'included_proxy':include}
  basemap={'identity':orig,'authenticity':{'source_quality':'unknown_unless_explicitly_proved','identifier':id},'2026_effect':{'legacy_v2':legacy,'stage16_v3':v3.get(id),'stage17':newass.get(id,[])},'first_cause':{'provision_details':events.get(id,[]),'first_cause_status':'unknown_except_specific_provisions'}}
  for kind,payload in basemap.items():
   cid=f'{id}::{kind}'; sourceids=sorted(subject_sources.get(id,[])); fingerprint=sha(canon({'claim_id':cid,'payload':payload,'source_versions':[(z,source_fingerprints[z]) for z in sourceids],'policy':VERSION}).encode())
   conn.execute('INSERT INTO stage17_claim VALUES(?,?,?,?,?,?,?,?)',(cid,id,kind,'whole_instrument',canon(payload),canon(sourceids),VERSION,fingerprint))
  for x in events.get(id,[]):
   payload=x;cid=f'{id}::provision::{x["provision_id"]}';fingerprint=sha(canon({'claim_id':cid,'payload':payload,'source_versions':[(z,source_fingerprints[z]) for z in sorted(subject_sources.get(id,[]))],'policy':VERSION}).encode())
   conn.execute('INSERT INTO stage17_claim VALUES(?,?,?,?,?,?,?,?)',(cid,id,'provision',x['provision_id'],canon(payload),'[]',VERSION,fingerprint))
 for aid,i,n,cons,formal,policy,code,grade,role,why,ids,gaps,human in conn.execute('SELECT * FROM stage17_assessment'):
  cid=f'{i}::assessment::{aid}';pay={'status':n,'consequences':cons,'formal':formal,'policy':policy,'rationale':why,'gaps':gaps}
  sf=sha(canon({'claim_id':cid,'payload':pay,'source_versions':[(z,source_fingerprints.get(z,z)) for z in json.loads(ids)],'policy':VERSION}).encode())
  conn.execute('INSERT INTO stage17_claim VALUES(?,?,?,?,?,?,?,?)',(cid,i,'independent_assessment',aid,canon(pay),ids,VERSION,sf))
 for eid,inst,actor,date,kind,scope,src,first,legal in conn.execute('SELECT event_id,affected_instrument,actor_instrument,effective_date,event_kind,scope,source_id,first_cessation_claim,legal_review_state FROM legal_event'):
  if not inst or not conn.execute('SELECT 1 FROM instruments WHERE id=?',(inst,)).fetchone():continue
  cid=f'{inst}::legacy_event::{eid}';pay={'event_id':eid,'actor':actor,'date':date,'kind':kind,'scope':scope,'source_id':src,'first_cause_claim':first,'review_state':legal}
  fp=sha(canon({'claim_id':cid,'payload':pay,'source_ids':[src],'policy':VERSION}).encode())
  conn.execute('INSERT INTO stage17_claim VALUES(?,?,?,?,?,?,?,?)',(cid,inst,'legal_event',eid,canon(pay),canon([src]),VERSION,fp))
 # Independently confirm Opus counts and protect specific exception cases.
 counts=dict(conn.execute('SELECT combined_legacy_provisional_status,count(*) FROM reconciled_legacy_checkpoint2_provisional GROUP BY 1').fetchall())
 assert counts=={'yes':268,'no':2787,'indeterminate':11917},counts
 assert conn.execute('SELECT count(*) FROM opus_checkpoint2_import').fetchone()[0]==540
 assert conn.execute('SELECT count(*) FROM instruments WHERE include_proxy=1').fetchone()[0]==14972
 assert conn.execute('SELECT count(*) FROM original_stage11_rows').fetchone()[0]==15010
 assert conn.execute('SELECT count(*) FROM opus_checkpoint2_conflicts').fetchone()[0]==155
 assert conn.execute('SELECT count(*) FROM opus_checkpoint2_held').fetchone()[0]==531
 for id in ['EO:11920','EO:12395']:
  assert conn.execute('SELECT count(*) FROM candidate_relationships WHERE predecessor=? AND eligible_for_research=0',(id,)).fetchone()[0]>=1,id
 assert conn.execute('SELECT count(*) FROM stage17_review').fetchone()[0]==0
 conn.commit();conn.execute('PRAGMA foreign_key_check');conn.execute('VACUUM');conn.close();shutil.rmtree(bridgeout)
 c=sqlite3.connect(target)
 metrics={
 'stage':'17','cutoff':CUTOFF,'include_proxy':14972,'original_rows':15010,
 'legacy_v2_yes':counts['yes'],'legacy_v2_no':counts['no'],'legacy_v2_indeterminate':counts['indeterminate'],
 'provisional_status_coverage_pct':round(100*(counts['yes']+counts['no'])/14972,6),
 'opus_accepted':540,'opus_held':531,'opus_conflicts':155,'opus_unprocessed':414,'opus_work_statuses':747,
 'stage16_episodes_preserved':c.execute('SELECT count(*) FROM legal_episode').fetchone()[0],
 'stage16_events_preserved':c.execute('SELECT count(*) FROM legal_event').fetchone()[0],
 'new_source_refs':c.execute('SELECT count(*) FROM stage17_source').fetchone()[0],
 'new_provision_histories':c.execute('SELECT count(*) FROM stage17_provision').fetchone()[0],
 'new_transitions':c.execute('SELECT count(*) FROM stage17_transition').fetchone()[0],
 'new_independent_ai_assessments':c.execute('SELECT count(*) FROM stage17_assessment').fetchone()[0],
 'new_census_candidates_unverified':c.execute('SELECT count(*) FROM stage17_catalogue_candidate').fetchone()[0],
 'reviewable_claims':c.execute('SELECT count(*) FROM stage17_claim').fetchone()[0],
 'human_reviewed_claims':c.execute('SELECT count(*) FROM stage17_review WHERE test_only=0').fetchone()[0],
 'database_sha256':sha(target.read_bytes()),
 'source_stage16_sha256':EXPECTED_STAGE16_SHA,'source_stage11_sha256':EXPECTED_STAGE11_SHA,'opus_patched_sha256':EXPECTED_OPUS_PATCH_SHA,
 'input_zip_sha256':{'stage16':sha(stage16.read_bytes()),'opus':sha(opus.read_bytes())},
 'independent_source_originals_unavailable':True,'data_release_grade':'AI_RESEARCH_NOT_HUMAN_CERTIFIED'
 }
 (out/'reports'/'METRICS_STAGE17.json').write_text(json.dumps(metrics,indent=2,sort_keys=True)+'\n')
 with (out/'reports'/'PER_ERA_PROGRESS.csv').open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['era','included','legacy_yes','legacy_no','legacy_unknown','independently_reviewed_stage17_assessments','human_reviews'])
  eras=[(1789,1861),(1862,1906),(1907,1936),(1937,1989),(1990,2026)]
  for lo,hi in eras:
   q='SELECT combined_legacy_provisional_status,count(*) FROM reconciled_legacy_checkpoint2_provisional WHERE CAST(substr(issuance_date,1,4) AS INT) BETWEEN ? AND ? GROUP BY 1'
   stat=dict(c.execute(q,(lo,hi)).fetchall()); w.writerow([f'{lo}-{hi}',sum(stat.values()),stat.get('yes',0),stat.get('no',0),stat.get('indeterminate',0),c.execute('SELECT count(*) FROM stage17_assessment a JOIN instruments i ON i.id=a.instrument_id WHERE CAST(substr(i.issuance_date,1,4) AS INT) BETWEEN ? AND ?',(lo,hi)).fetchone()[0],0])
  q='SELECT combined_legacy_provisional_status,count(*) FROM reconciled_legacy_checkpoint2_provisional WHERE issuance_date IS NULL OR issuance_date = "" GROUP BY 1';stat=dict(c.execute(q).fetchall());w.writerow(['undated',sum(stat.values()),stat.get('yes',0),stat.get('no',0),stat.get('indeterminate',0),0,0])
 c.close();print(json.dumps(metrics,indent=2))
 return metrics

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--stage16',required=True);ap.add_argument('--opus',required=True);ap.add_argument('--bridge-script',required=True);ap.add_argument('--out',required=True);a=ap.parse_args();build(a.stage16,a.opus,a.bridge_script,a.out)
