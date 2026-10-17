#!/usr/bin/env python3
"""Reproducible Stage16 canonical research DB. No migration mutates input files.

Uses Stage11 as immutable historical ledger, Stage12 de-dup/date projection, Stage13
NARA date evidence, Stage14 source graph, Stage15 repaired importer principle.
All editorial and OCR leads remain unadjudicated; no legal conclusion is promoted
from metadata alone. V3 assessments are kept separate from legacy v2 decisions.
"""
import sys,os,csv,json,sqlite3,hashlib,datetime,collections,re,math
from pathlib import Path
ROOT=Path(os.environ.get('STAGE16_RELEASE_ROOT',str(Path(__file__).resolve().parents[1])))
INPUT=Path(os.environ.get('STAGE16_INPUT_ROOT','/mnt/data/stage16_work/inputs'))
S11=INPUT/'RECONCILED_STATUS_LEDGER_STAGE11_PROVISIONAL.jsonl'
S12=INPUT/'EO_STAGE12_INDEPENDENT_AUDIT_2026-10-16/DATA/STAGE12_NORMALIZED_NONDESTRUCTIVE_15010.jsonl'
S13=INPUT/'EO_STAGE13_FOUNDATIONAL_VALIDATION_2026-10-16/CENSUS/NARA_UNNUMBERED_EDITORIAL_DATES_18.csv'
LORD=INPUT/'EO_STAGE13_FOUNDATIONAL_VALIDATION_2026-10-16/CENSUS/LORD_GEOMETRY_DATE_LEADS.jsonl'
S14=INPUT/'EO_STAGE14_LEVERAGE_ENGINE_2026-10-16/DATA/EO_SOURCE_DEPENDENCY_GRAPH.sqlite'
S15=INPUT/'EO_STAGE15_METHOD_FOUNDATION_2026-10-16/AUDIT/CHRONOLOGY_AND_COMPLETENESS_GATED_RELATION_FEED.csv'
S15KEY=INPUT/'EO_STAGE15_METHOD_FOUNDATION_2026-10-16/AUDIT/EO_STAGE15_SCHEMA_AND_RISK_SIDECAR.sqlite'
SAMPLE=INPUT/'EO_STAGE15_METHOD_FOUNDATION_2026-10-16/STATISTICS/STRATIFIED_POPULATION_SAMPLE_120_BLIND.csv'
PDF=Path(os.environ.get('STAGE16_LORD_PDF','/mnt/data/public-gdc-43013029-43013029.pdf'))
sys.path.insert(0,str(ROOT/'CODE'))
from policy import Review,authorize_status,authorize_first_cause,DecisionRejected,V3,CUTOFF
EXPECTED_SHA={ 'stage11':'c0308e008cd719cd153ca667271c93267d5d855bf3eb26d48076e41938fc7729', 'stage14':'41310b46f97712b28fcb7fd00e5ab5d38770c225fa57f5c10e5c9836738af55b', 'lord':'0553dd2318903af8fd4cdbb56140cd035f3bac52ec5420148307206940ab69e1'}
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for x in iter(lambda:f.read(1024*1024),b''):h.update(x)
 return h.hexdigest()
def dump(p,d):p.write_text(json.dumps(d,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
def jsonls(p):return (json.loads(s) for s in open(p,encoding='utf-8') if s.strip())
def make_schema(c):
 c.executescript('''
 PRAGMA foreign_keys=ON;
 CREATE TABLE build_metadata(key TEXT PRIMARY KEY,value TEXT);
 CREATE TABLE original_stage11_rows (record_id TEXT PRIMARY KEY, original_sha TEXT NOT NULL,raw_json TEXT NOT NULL);
 CREATE TABLE instruments (id TEXT PRIMARY KEY, canonical_group TEXT NOT NULL, issuance_date TEXT, historical_date_grade TEXT, include_proxy INT NOT NULL CHECK(include_proxy IN(0,1)), source_population_class TEXT NOT NULL, signer_claim TEXT, signer_capacity TEXT, delegated_authority TEXT, signature_authenticated INT NOT NULL DEFAULT 0 CHECK(signature_authenticated IN(0,1)),document_authenticated INT NOT NULL DEFAULT 0 CHECK(document_authenticated IN(0,1)), original_legacy_status TEXT, original_any_effect TEXT, original_review TEXT);
 CREATE TABLE bibliographic_entries (entry_id TEXT PRIMARY KEY,group_id TEXT,raw_population_class TEXT,raw_included_validated INT, raw_duplicate_of TEXT, raw_date TEXT, source_ids_json TEXT NOT NULL, original_record_sha TEXT NOT NULL, FOREIGN KEY(entry_id) REFERENCES original_stage11_rows(record_id));
 CREATE TABLE source_documents (source_id TEXT PRIMARY KEY,subject TEXT,source_url TEXT,original_date TEXT,reference TEXT,source_kind TEXT,acquisition_status TEXT,content_sha TEXT,source_note TEXT);
 CREATE TABLE source_observations (obs_id INT PRIMARY KEY,source_kind TEXT,related_id TEXT,source_sha TEXT,source_url TEXT,valid_asof TEXT,category TEXT,disposition TEXT,amendments TEXT,notes TEXT);
 CREATE TABLE candidate_relationships (candidate_key TEXT PRIMARY KEY,actor TEXT,predecessor TEXT,relation TEXT,source_url TEXT,provenance_type TEXT,source_obs_id INT,source_sha TEXT,eligible_for_research INT NOT NULL,quarantine_reason TEXT, legal_scope_verified INT NOT NULL DEFAULT 0,decision_promotion_allowed INT NOT NULL DEFAULT 0);
 CREATE INDEX rel_actor ON candidate_relationships(actor,eligible_for_research);
 CREATE INDEX rel_predecessor ON candidate_relationships(predecessor,eligible_for_research);
 CREATE TABLE lord_date_markers (marker_id TEXT PRIMARY KEY,pdf_page INT,month INT,day INT,year_heuristic INT,year_review_status TEXT,original_month TEXT,x REAL,y REAL,source_sha TEXT,document_authenticated INT NOT NULL DEFAULT 0);
 CREATE TABLE lord_source_excerpts (marker_id TEXT PRIMARY KEY,extracted_context TEXT,excerpt_sha TEXT,source_page INT,extraction_grade TEXT,FOREIGN KEY(marker_id) REFERENCES lord_date_markers(marker_id));
 CREATE TABLE source_date_references (instrument_id TEXT PRIMARY KEY,reference_date TEXT,source_url TEXT,source_sha TEXT,provenance_grade TEXT,identity_collision_resolved INT NOT NULL DEFAULT 0);
 CREATE TABLE lord_nara_date_matches (marker_id TEXT,unnumbered_instrument_id TEXT,proposed_date TEXT,identity_match_grade TEXT,PRIMARY KEY(marker_id,unnumbered_instrument_id));
 CREATE TABLE legal_inference_policy (version TEXT PRIMARY KEY,primary_estimand TEXT,secondary_estimand TEXT,attribution_rule TEXT,status TEXT);
 CREATE TABLE legal_episode (episode_id TEXT PRIMARY KEY,instrument_id TEXT,provision TEXT,state TEXT,valid_from TEXT,valid_to_exclusive TEXT,conditional_end_text TEXT,cessation_mechanism TEXT,first_cessation_proven INT,source_id TEXT,evidence_grade TEXT,remaining_gap TEXT,FOREIGN KEY(instrument_id) REFERENCES instruments(id));
 CREATE TABLE legal_event (event_id TEXT PRIMARY KEY,actor_instrument TEXT,affected_instrument TEXT,effective_date TEXT,date_granularity TEXT,event_kind TEXT,scope TEXT,source_id TEXT,first_cessation_claim TEXT,legal_review_state TEXT);
 CREATE TABLE v3_effect_assessments (id TEXT PRIMARY KEY,normative_status TEXT NOT NULL CHECK(normative_status IN ('yes','no','indeterminate')),enduring_consequence TEXT NOT NULL,formal_disposition TEXT NOT NULL,successor_policy_continuity TEXT NOT NULL,review_grade TEXT NOT NULL,original_source_id TEXT,decision_rationale TEXT NOT NULL,retains_legacy_status INT NOT NULL DEFAULT 1);
 CREATE TABLE source_evaluation (source_id TEXT PRIMARY KEY,url_discovered INT,representation_read INT,local_original_bytes INT,document_signature_authenticated INT,relationship_identified INT,legal_scope_checked INT,current_status_independently_verified INT);
 CREATE TABLE legal_readiness (id TEXT PRIMARY KEY,legacy_status TEXT,episode_count INT,episode_coverage_state TEXT,methodological_risk_flags_json TEXT,independent_human_review INT DEFAULT 0, v3_certified INT DEFAULT 0);
 CREATE TABLE census_methodology (estimand TEXT PRIMARY KEY,estimated_size INT,complete INT,description TEXT);
 CREATE TABLE probability_sample (id TEXT PRIMARY KEY,era TEXT,source_class TEXT,frame_stratum_size INT,n_drawn INT,inclusion_prob REAL,design_weight REAL,review_state TEXT NOT NULL CHECK(review_state IN ('UNREVIEWED','REVIEWED')),independent_verdict TEXT,blinded_source_reviewer TEXT); 
 CREATE TABLE mutation_audit (seq INTEGER PRIMARY KEY AUTOINCREMENT,record_id TEXT,field TEXT,original_value TEXT,new_value TEXT,reason TEXT,evidence_ref TEXT,action_class TEXT);
 -- A v3 whole-order YES/NO cannot be silently inserted without a reviewed
 -- original text and explicit source-scope inspection. This is separate from the
 -- stricter independent certification gate in policy.py.
 CREATE TRIGGER require_source_for_v3_determinate_before_insert BEFORE INSERT ON v3_effect_assessments
 WHEN NEW.normative_status IN ('yes','no') AND (
  NEW.original_source_id IS NULL OR NEW.review_grade NOT IN ('source_reviewed_not_independently_certified','independently_certified') OR
  NOT EXISTS (SELECT 1 FROM source_evaluation ev WHERE ev.source_id=NEW.original_source_id AND ev.representation_read=1 AND ev.legal_scope_checked=1)
 ) BEGIN SELECT RAISE(ABORT,'Cannot store determinate v3 status without source-linked scope inspection'); END;
 CREATE TRIGGER require_source_for_v3_determinate_before_update BEFORE UPDATE OF normative_status,original_source_id,review_grade ON v3_effect_assessments
 WHEN NEW.normative_status IN ('yes','no') AND (
  NEW.original_source_id IS NULL OR NEW.review_grade NOT IN ('source_reviewed_not_independently_certified','independently_certified') OR
  NOT EXISTS (SELECT 1 FROM source_evaluation ev WHERE ev.source_id=NEW.original_source_id AND ev.representation_read=1 AND ev.legal_scope_checked=1)
 ) BEGIN SELECT RAISE(ABORT,'Cannot promote v3 assessment without source-linked scope inspection'); END;
 CREATE TRIGGER prevent_unverified_relationship_promotion BEFORE UPDATE OF decision_promotion_allowed ON candidate_relationships
 WHEN NEW.decision_promotion_allowed=1 AND (NEW.legal_scope_verified!=1 OR NEW.eligible_for_research!=1)
 BEGIN SELECT RAISE(ABORT,'Cannot promote candidate relationship without verified scope and nonquarantine'); END;
 CREATE TRIGGER prevent_unreviewed_sample_outcome BEFORE UPDATE OF independent_verdict ON probability_sample
 WHEN NEW.independent_verdict IS NOT NULL AND (NEW.review_state!='REVIEWED' OR NEW.blinded_source_reviewer IS NULL OR NEW.blinded_source_reviewer='')
 BEGIN SELECT RAISE(ABORT,'A probability-sample verdict requires an identified independent reviewer'); END;
 CREATE TRIGGER prevent_unsupported_first_cause BEFORE INSERT ON legal_event
 WHEN NEW.first_cessation_claim='PROVEN_WHOLE_ORDER_FIRST_CESSATION' AND NEW.legal_review_state!='independently_adjudicated_whole_scope'
 BEGIN SELECT RAISE(ABORT,'A later event or source graph edge cannot by itself establish first cessation'); END;
 ''')

def insert_episode(c,id,prov,state,begin,end,conditional,cause,proven,src,grade,gap):
 key=id+'#'+prov
 assert state in {'never_operative','operative','partially_operative','dormant','terminated','revived','indeterminate'}
 c.execute('INSERT INTO legal_episode VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(key,id,prov,state,begin,end,conditional,cause,int(proven),src,grade,gap))

def main():
 files={'stage11':S11,'stage12':S12,'stage13':S13,'stage14':S14,'stage15':S15,'lord_date_markers':LORD,'lord':PDF,'probability_sample':SAMPLE}
 assert all(p.exists() for p in files.values()),[(k,str(v),v.exists()) for k,v in files.items()]
 hashes={k:sha(p) for k,p in files.items()}
 for k in EXPECTED_SHA: assert hashes[k]==EXPECTED_SHA[k],(k,hashes[k])
 out=ROOT/'DATA/AFTERLIFE_STAGE16_CANONICAL.sqlite'
 if out.exists():out.unlink()
 c=sqlite3.connect(str(out));c.execute('PRAGMA journal_mode=DELETE');make_schema(c)
 old={r['instrument_id']:r for r in jsonls(S11)}; projection={r['instrument_id']:r for r in jsonls(S12)}
 assert len(old)==15010 and len(projection)==15010
 graph=sqlite3.connect(f'file:{S14}?mode=ro',uri=True);graph.row_factory=sqlite3.Row
 g_orders={r['id']:dict(r) for r in graph.execute('SELECT * FROM orders')}
 assert len(g_orders)==15010
 for id,r in old.items():
  raw=json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))
  h=hashlib.sha256(raw.encode()).hexdigest()
  p=projection[id]; g=g_orders[id]
  canon=g['canonical_group'] or id
  c.execute('INSERT INTO original_stage11_rows VALUES(?,?,?)',(id,h,raw))
  c.execute('INSERT INTO bibliographic_entries VALUES(?,?,?,?,?,?,?,?)',(id,canon,r['population_class'],int(bool(r['included_validated'])),canon if (r['included_validated'] and not g['include_unique']) else None,r.get('signing_date'),json.dumps(r.get('source_ids',[])),h))
  srcdate=p.get('signing_date_audit_projection') or r.get('signing_date')
  dgrade='stage12_crosschecked' if p.get('date_source_url') else ('legacy_inherited' if srcdate else 'missing')
  c.execute('INSERT INTO instruments(id,canonical_group,issuance_date,historical_date_grade,include_proxy,source_population_class,original_legacy_status,original_any_effect,original_review) VALUES(?,?,?,?,?,?,?,?,?)',(id,canon,srcdate,dgrade,int(bool(g['include_unique'])),r['population_class'],r['substantive_effect'],r['any_operative_EO_effect'],r['review_status']))
  if r['included_validated'] and g['include_unique']:
   old_episode_count=len(r.get('operative_episodes') or [])
   c.execute('INSERT INTO legal_readiness(id,legacy_status,episode_count,episode_coverage_state,methodological_risk_flags_json) VALUES(?,?,?,?,?)',(id,r['substantive_effect'],old_episode_count,'legacy_episode_record_present_not_yet_v3_verified' if old_episode_count else 'no_structured_legacy_episode',json.dumps(r.get('effect_tags') or [])))
  if p.get('signing_date_audit_projection') and p['signing_date_audit_projection']!=r.get('signing_date'):
   c.execute('INSERT INTO mutation_audit(record_id,field,original_value,new_value,reason,evidence_ref,action_class) VALUES(?,?,?,?,?,?,?)',(id,'analysis_issuance_date',str(r.get('signing_date')),p['signing_date_audit_projection'],'Stage12 documentary-date projection',str(p.get('date_source_url')),'non_destructive_identity_projection'))
  if r['included_validated'] and not g['include_unique']:
   c.execute('INSERT INTO mutation_audit(record_id,field,original_value,new_value,reason,evidence_ref,action_class) VALUES(?,?,?,?,?,?,?)',(id,'analytical_proxy_membership','included','duplicate_alias','Case-folded canonical documentary identity', 'EO:7933A / EO:7933a','non_destructive_deduplication'))
 assert c.execute('SELECT SUM(include_proxy) FROM instruments').fetchone()[0]==14972

 # Explicit US Supreme Court attribution, but NOT forged autograph verification.
 for ident,attribution,capacity,authority in [
  ('EO:3016C','Frank L. Polk (court-attributed)','delegated presidential power','Wilson delegation December 3 1918 (Trading with the Enemy Act)'),
  ('EO:3016K','Frank L. Polk (court-attributed)','delegated presidential power','Wilson delegation December 3 1918 (Trading with the Enemy Act)'),
  ('EO:3016N','unverified','undetermined','cannot infer from Chemical Foundation holding')]:
  c.execute('UPDATE instruments SET signer_claim=?,signer_capacity=?,delegated_authority=? WHERE id=?',(attribution,capacity,authority,ident))

 curated=json.loads((ROOT/'SOURCES/CURATED_OFFICIAL_EVENTS.json').read_text());
 for s in curated['sources']:
  acq='uploaded_PDF_original_scan' if s.get('original_bytes_locally_acquired') else 'text_viewed_via_source_tool_no_local_original_bytes'
  sh=hashes['lord'] if s['source_id']=='LORD1943' else None
  c.execute('INSERT INTO source_documents VALUES(?,?,?,?,?,?,?,?,?)',(s['source_id'],s.get('subject'),s['url'],s.get('signing_date'),s['citation'],'full_scan' if s['source_id']=='LORD1943' else 'published_text_or_transcription',acq,sh,s['provenance']))
  c.execute('INSERT INTO source_evaluation VALUES(?,?,?,?,?,?,?,?)',(s['source_id'],1,1,1 if sh else 0,0,0,0,0))
 c.execute("UPDATE source_evaluation SET relationship_identified=1 WHERE source_id IN ('APP_EO6955A','NARA_EO3461','NARA_EO12220','NARA_EO12553')")

 for r in graph.execute('SELECT * FROM observations'):
  c.execute('INSERT INTO source_observations VALUES(?,?,?,?,?,?,?,?,?,?)',(r['obs_id'],r['source_kind'],r['instrument_id'],r['source_sha256'],r['source_url'],r['asof'],r['category'],r['disposition'],r['amendments'],r['notes']))
 assert c.execute('SELECT count(*) FROM source_observations').fetchone()[0]==11164

 # SOURCE-FIRST importer repair is performed live from the same preserved source rows.
 # Import the base candidates with their original status, then detect missing NARA successors.
 for r in graph.execute('SELECT * FROM relationships'):
  quar=bool(r['quarantined'])
  if r['actor']=='EO:13257' and r['predecessor']=='EO:13333':quar=True
  c.execute('INSERT INTO candidate_relationships VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(f'S14:{r["edge_id"]}',r['actor'],r['predecessor'],r['relation'],r['source_url'],'original_stage14',None,None,int(not quar),r['quarantine_reason'] if r['quarantined'] else ('chronology_precedes_predecessor' if quar else None),0,0))
 existing={(r['actor'],r['predecessor']) for r in graph.execute('SELECT actor,predecessor FROM relationships')}
 recovered=[]
 for r in graph.execute("SELECT * FROM observations WHERE source_kind='NARA_CODIFICATION_1989'"):
  try:successors=json.loads(r['notes'] or '{}').get('successor_candidates') or []
  except (TypeError,ValueError):continue
  for actor in successors:
   if (actor,r['instrument_id']) in existing:continue
   a=g_orders.get(actor); b=g_orders.get(r['instrument_id'])
   if not a or not b:why='actor_or_target_unresolved'
   elif re.fullmatch(r'\d{4}-\d{2}-\d{2}',a.get('signing_date') or '') and re.fullmatch(r'\d{4}-\d{2}-\d{2}',b.get('signing_date') or '') and a['signing_date']<b['signing_date']:why='backward_in_time'
   else:why=None
   key=f'NARA_OBS:{r["obs_id"]}:{actor}'
   c.execute('INSERT INTO candidate_relationships VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(key,actor,r['instrument_id'],r['category'],r['source_url'],'NARA_1989_source_row_discovered',r['obs_id'],r['source_sha256'],int(why is None),why,0,0))
   recovered.append((actor,r['instrument_id'],why))
 assert len(recovered)==513 and sum(why is None for a,p,why in recovered)==512
 good=c.execute('SELECT count(*) FROM candidate_relationships WHERE eligible_for_research=1').fetchone()[0]
 assert good==7086,good
 # Future imports call the same function/build logic; evidence edges never promote determinate law.
 with open(S15,newline='') as f:
  expected={(r['edge_id'],r['actor'],r['predecessor']) for r in csv.DictReader(f)}
 actual=set(c.execute('SELECT candidate_key,actor,predecessor FROM candidate_relationships WHERE eligible_for_research=1'))
 assert actual==expected,(len(actual),len(expected),len(actual.symmetric_difference(expected)))

 # Register scan-extracted historical date markers, and permit DATE-ONLY potential joins.
 for i,r in enumerate(jsonls(LORD),1):
  marker=f'LORD1943-P{r["pdf_page"]:03d}-X{r["pdf_word_x"]:06.1f}-Y{r["pdf_word_y"]:06.1f}'
  c.execute('INSERT INTO lord_date_markers VALUES(?,?,?,?,?,?,?,?,?,?,0)',(marker,r['pdf_page'],r['month'],r['day'],r.get('year_token_heuristic_unverified'),'UNVERIFIED_YEAR_AND_DOCUMENT_IDENTITY',r['raw_month'],r['pdf_word_x'],r['pdf_word_y'],hashes['lord']))
 assert c.execute('SELECT count(*) FROM lord_date_markers').fetchone()[0]==1023
 # EXCAVATOR: use the PDF's existing text layer and positional date cues to
 # make candidate context packets once for all ~1k leads; never assert an EO
 # exists from the context alone, and preserve the original scanned page.
 import fitz
 scan=fitz.open(str(PDF));by_page=collections.defaultdict(list)
 for marker_id,page_no,xx,yy in c.execute('SELECT marker_id,pdf_page,x,y FROM lord_date_markers ORDER BY pdf_page,y'):
  by_page[page_no].append((marker_id,xx,yy))
 extracted=0
 for page_no,anchors in sorted(by_page.items()):
  page=scan[page_no-1]
  for j,(marker_id,xx,yy) in enumerate(anchors):
   next_y=anchors[j+1][2] if j+1<len(anchors) else page.rect.height-65
   # The source month/date occupies the left column. Body text is typically
   # >90 PDF units right of that anchor; same-page next marker bounds it.
   crop=fitz.Rect(min(xx+90,page.rect.width-5),max(0,yy-8),page.rect.width-25,min(page.rect.height,max(yy+45,next_y-8)))
   raw=page.get_text(sort=True,clip=crop).strip()
   cleaned=re.sub(r'[ \t]+',' ',raw)
   cleaned=re.sub(r'\n{3,}','\n\n',cleaned)[:3000]
   grade='SOURCE_OCR_CONTEXT_NOT_AUTHENTICATED' if len(cleaned)>=18 else 'SOURCE_TEXT_LAYER_UNREADABLE'
   extracted+=int(grade=='SOURCE_OCR_CONTEXT_NOT_AUTHENTICATED')
   c.execute('INSERT INTO lord_source_excerpts VALUES(?,?,?,?,?)',(marker_id,cleaned,hashlib.sha256(cleaned.encode()).hexdigest(),page_no,grade))
 scan.close()
 assert extracted>=900,(extracted,'unexpected degraded source extraction')
 csv_path=ROOT/'REPORTS/LORD_SOURCE_EXCERPTS_FOR_REVIEW.csv'
 with open(csv_path,'w',newline='',encoding='utf-8') as f:
  w=csv.writer(f);w.writerow(['marker_id','pdf_page','month','day','UNVERIFIED_year_heuristic','ocr_excerpt','extraction_grade','document_authenticated'])
  for row in c.execute('SELECT m.marker_id,m.pdf_page,m.month,m.day,m.year_heuristic,e.extracted_context,e.extraction_grade,m.document_authenticated FROM lord_date_markers m JOIN lord_source_excerpts e USING(marker_id) ORDER BY m.pdf_page,m.y'):
   w.writerow(row)
 with open(S13,newline='') as f:
  for r in csv.DictReader(f):
   c.execute('INSERT INTO source_date_references VALUES(?,?,?,?,?,0)',(r['instrument_id'],r['reference_date'],r['source_url'],r['original_html_sha256'],'1989 editorial date source, not authenticated signature'))
   c.execute("UPDATE instruments SET issuance_date=?,historical_date_grade='NARA1989_editorial_date_not_signature_authenticated' WHERE id=? AND (issuance_date IS NULL OR issuance_date='' OR issuance_date='unknown')",(r['reference_date'],r['instrument_id']))
 for lm in c.execute('SELECT marker_id,month,day,year_heuristic FROM lord_date_markers WHERE day IS NOT NULL').fetchall():
  mid,mo,day,y=lm
  if not y:continue
  try:iso=datetime.date(y,mo,day).isoformat()
  except ValueError:continue
  for ident, in c.execute('SELECT instrument_id FROM source_date_references WHERE reference_date=?',(iso,)).fetchall():
   c.execute('INSERT INTO lord_nara_date_matches VALUES(?,?,?,?)',(mid,ident,iso,'DATE_ONLY_HYPOTHESIS_NOT_IDENTITY_PROOF'))

 # v3.0.0: source command, enduring consequences, formal status, policy continuity separate.
 c.execute('INSERT INTO legal_inference_policy VALUES(?,?,?,?,?)',(V3,'Currently applicable EO-sourced commands, permissions and constitutive statuses, assessed provision by provision; completed pure dispositions are spent as commands','Enduring legal consequences, revocation effects, transferred property interests, accrued/saved rights, and inherited host text recorded independently','Source EO -> current host amendment lineage requires present host and intervening history; independent re-enactment does not continue original authority; pure repeal effect goes to enduring-consequence axis','CURRENT_FOR_NEW_SOURCED_RESEARCH; legacy v2.0.0 remains archived unchanged'))
 c.execute('INSERT INTO census_methodology VALUES(?,?,?,?)',('working_identified_document_proxies',14972,0,'De-duplicated working bibliography; includes historical unnumbered editorial rows, cannot establish physical-document identity or complete historical issued universe'))
 c.execute('INSERT INTO census_methodology VALUES(?,?,?,?)',('authenticated_presidential_documents',None,0,'Exact number not established. No global original-signature authentication survey yet.'))
 c.execute('INSERT INTO census_methodology VALUES(?,?,?,?)',('all_historically_issued_executive_orders',None,0,'Open historical universe including unnumbered, unpublished, and delegated instruments. Cannot use 14,972 as exact national issued count.'))

 # FIRST COMPLETE RECONSTRUCTION FAMILY: Three original-text-verifiable, finite federal closures.
 closures=curated['family_review'];n_closed=0
 for item in closures:
  ident=item['id'];src='OFFICIAL_'+ident.replace(':','')
  days=item['days'];date_signed=next(x['signing_date'] for x in curated['sources'] if x['source_id']==src)
  for day in days:
   exclusive=(datetime.date.fromisoformat(day)+datetime.timedelta(days=1)).isoformat()
   insert_episode(c,ident,f'1_CLOSURE_{day}','terminated',day,exclusive,None,'original_term',1,src,'published_official_operative_text','Only closure scope; other independent residual duties analyzed separately')
   insert_episode(c,ident,f'2_ESSENTIAL_EXCEPTION_{day}','terminated',day,exclusive,None,'original_term',1,src,'published_official_operative_text','Only emergency exception tied to the named closure date')
   c.execute('INSERT INTO legal_event VALUES(?,?,?,?,?,?,?,?,?,?)',(ident+'#DAY_CLOSURE_END_'+day,ident,ident,exclusive,'day','original_dated_command_exhausted',f'EO sections 1-2 for {day}',src,'PROVEN_FOR_SECTIONS_1_AND_2_NOT_WHOLE_ORDER','first_pass_full_text_scope_review'))
   n_closed+=1
  insert_episode(c,ident,'3_PAY_AND_LEAVE_CROSS_REFERENCE','indeterminate',date_signed,None,'Potential accrued pay and leave effects of specified dates','unknown',0,src,'official_text_scope_qualified','Post-date payroll, leave, and retrospective claim application not established; any-effect remains indeterminate')
  insert_episode(c,ident,'4_OPM_IMPLEMENTATION','indeterminate',date_signed,None,'Actions needed to implement dated closure','unknown',0,src,'official_text_scope_qualified','Potential postdated administrative correction not conclusively closed')
  insert_episode(c,ident,'5_GENERAL_PROVISIONS','terminated',date_signed,(datetime.date.fromisoformat(days[-1])+datetime.timedelta(days=1)).isoformat(),None,'original_term',0,src,'official_text_scope_qualified','Non-creation of private rights does not itself settle accrued statutory pay entitlements')
  # Whole-order NO must be HELD where a potentially substantive original clause
  # (pay/leave or continuing implementation authority) has not been closed.
  proposal=Review(document_verified=True,whole_original_scope_verified=True,later_events_checked=False,saved_rights_checked=False,host_amendment_checked=True,residual_checked=False,unresolved_material_scope=True,original_evidence_ref=src,independent_review=False)
  grade=authorize_status('indeterminate',proposal,certified=False)
  c.execute('INSERT INTO v3_effect_assessments VALUES(?,?,?,?,?,?,?,?,1)',(ident,'indeterminate','unresolved_accrued_pay_leave_possible','not_supposedly_revoked','unknown','held_first_pass_original_source',src,'Sections 1-2 exhausted on identified dates. Whole-order substantive NO withheld: section 3 pay/leave rights and section 4 OPM implementation authority remain inadequately traced. The any-effect axis is likewise unresolved.'))
  c.execute('UPDATE source_evaluation SET legal_scope_checked=1 WHERE source_id=?',(src,))

 # Completed revocation modeled separately from resulting legal-state consequences.
 insert_episode(c,'EO:8885','CUSTOMS_PORT_REVOCATION','terminated','1941-09-15',None,'Effective at close of business Sept. 15, 1941','performance_complete',0,'FEDREG_EO8885','contemporaneous_official_FR_original_text','Original act is a completed disposition. Continuing source-attributable consequences in 2026 not independently traced.')
 c.execute('INSERT INTO legal_event VALUES(?,?,?,?,?,?,?,?,?,?)',('EO:8885#PORT_REVOCATION', 'EO:8885','EO:7632','1941-09-15','close_of_business','partial_revocation','Peskan, Montana port entry only','FEDREG_EO8885','NOT_A_PREDECESSOR_WHOLE_SCOPE_CESSATION','first_pass_original_source_checked'))
 c.execute("UPDATE source_evaluation SET legal_scope_checked=1 WHERE source_id='FEDREG_EO8885'")
 c.execute('INSERT INTO v3_effect_assessments VALUES(?,?,?,?,?,?,?,?,1)',('EO:8885','no','historical_revocation_legal_consequence_present_as_of_1941_current_2026_uncertain','executed_repeal','unknown','source_reviewed_not_independently_certified','FEDREG_EO8885','Only completed revocation and stated future effective date in original FR text; direct operative command spent, 2026 successor chain not proved.'))

 # Historical amended deadline: NEVER assign 1935-02-01 first end after a superseding amendment.
 insert_episode(c,'EO:6877','ORIGINAL_WOOL_ADMINISTRATION_WINDOW','operative','1934-10-16','1935-02-01',None,'later_amendment_condition',0,'APP_EO6877','hosted_original_transcription','1935-02-01 was original limit, not proved final cessation; superseding amendment changed it')
 insert_episode(c,'EO:6877','AMENDED_WOOL_ADMINISTRATION_WINDOW','indeterminate','1935-02-01',None,'30 days after report submitted to the President','unknown',0,'APP_EO6955A','hosted_original_transcription','Actual report date or independently verified program endpoint not found; no first cessation date promoted')
 insert_episode(c,'EO:6955A','MODIFY_EO6877_EXPIRATION','terminated','1935-02-01',None,'Change to host term executed','performance_complete',0,'APP_EO6955A','hosted_original_transcription','Host-incorporated norm life not known; do not treat this completed amender as proof host still active')
 c.execute('INSERT INTO legal_event VALUES(?,?,?,?,?,?,?,?,?,?)',('EO:6955A#AMEND6877','EO:6955A','EO:6877','1935-02-01','day','amendment','Original Feb 1 horizon replaced by 30 days after report submitted; no report date established','APP_EO6955A','NOT_A_FIRST_CESSATION; CHANGED_CONDITION','first_pass_transcription_only'))
 # Scope limited other event chains from independent old original documents.
 c.execute('INSERT INTO legal_event VALUES(?,?,?,?,?,?,?,?,?,?)',('EO:3461#2596','EO:3461','EO:2596','1921-05-16','day','revocation_with_savings','Wartime civil-service exception revoked; incumbent exceptions saved','NARA_EO3461','UNKNOWN_WHETHER_FIRST_AND_WHETHER_INCORPORATED_EFFECT_SURVIVES','first_pass_secondary_source'))
 c.execute('INSERT INTO legal_event VALUES(?,?,?,?,?,?,?,?,?,?)',('EO:3461#2602','EO:3461','EO:2602','1921-05-16','day','revocation_with_savings','Wartime civil-service eligibility rule revoked; existing employees retained in excepted status at agency discretion','NARA_EO3461','UNKNOWN_WHETHER_FIRST_AND_RIGHTS_ATTRIBUTION','first_pass_secondary_source'))
 c.execute('INSERT INTO legal_event VALUES(?,?,?,?,?,?,?,?,?,?)',('EO:12220#10746','EO:12220','EO:10746','1980-06-27','day','formal_revocation_after_partial_supersession','Text expressly says predecessor previously superseded at least in part','NARA_EO12220','LATER_BOUND_ONLY_EARLIER_PARTIAL_CESSATION_UNDATED','official_source_scoped'))
 c.execute('INSERT INTO v3_effect_assessments VALUES(?,?,?,?,?,?,?,?,1)',('EO:13286','indeterminate','host_amendment_effect_supported_in_v2;_v3_source_vs_host_attribution_requires_review','amended_in_part','host_rule_continues','not_reaudited_under_v3','NARA_EO12220','Legacy v2 YES retained, but whether an amender has independent continuing command in v3 cannot be decided from surviving host text alone.'))

 # SOURCE-CENTERED MASS FAMILY: EO 12553. Separate formal revocation from causal first ending.
 # In Stage14, 388 distinct referrals exist but two are quarantined. Its independent
 # full cached text vs government editorial comparison established exactly 386.
 direct_386=sorted({r['predecessor'] for r in graph.execute("SELECT predecessor FROM relationships WHERE actor='EO:12553' AND relation='express_revocation_claim' AND quarantined=0")})
 assert len(direct_386)==386, ('EA12553 effective crosswalk',len(direct_386))
 cached=graph.execute("SELECT sha256 FROM cache_representations WHERE subject_id_hint='EO:12553' AND archive_member LIKE '%rv_app_eo12553.txt'").fetchone()
 assert cached and cached['sha256']=='f4c31bbb6aa48f56699c75fa8f7de9717765a45e286a752217ae5da654a0ff64'
 c.execute('INSERT INTO source_documents VALUES(?,?,?,?,?,?,?,?,?)',('EO12553_CACHED_FULL_TEXT','EO:12553','https://www.presidency.ucsb.edu/documents/executive-order-12553-revocation-various-executive-orders','1986-02-25','Full EO12553 cached schedule crosschecked against 1989 NARA revocation listings','hosted_transcription_cache','cached_locally_extracted_text_not_original_pdf',cached['sha256'],'386 unique named revocation targets; original original image not independently acquired'))
 c.execute('INSERT INTO source_evaluation VALUES(?,?,?,?,?,?,?,?)',('EO12553_CACHED_FULL_TEXT',1,1,0,0,1,1,0))
 # Independent cross-document contradiction: two 1989 editorial rows named
 # EO12553 as their revoker but are absent from the separately enumerated 386
 # entries in its actual revocation schedule. Hold BOTH; don't invent a match.
 other_editorial=c.execute("SELECT candidate_key,predecessor FROM candidate_relationships WHERE actor='EO:12553' AND provenance_type='NARA_1989_source_row_discovered' AND eligible_for_research=1").fetchall()
 primary_set=set(direct_386)
 discordant=[(key,predecessor) for key,predecessor in other_editorial if predecessor not in primary_set]
 assert set(x[1] for x in discordant)=={'EO:11920','EO:12395'},discordant
 for key,predecessor in discordant:
  c.execute("UPDATE candidate_relationships SET eligible_for_research=0,quarantine_reason='PRIMARY_SCHEDULE_NARA_1989_CONFLICT_EO12553_UNRESOLVED' WHERE candidate_key=?",(key,))
  c.execute('INSERT INTO mutation_audit(record_id,field,original_value,new_value,reason,evidence_ref,action_class) VALUES(?,?,?,?,?,?,?)',(predecessor,'relation_EO12553_candidate_eligibility','stage15_usable','quarantined_source_conflict','Current NARA editorial reference absent from cached original 386-name revocation schedule','EO12553_CACHED_FULL_TEXT plus NARA 1989 source observation', 'source_priority_conflict_not_legal_disposition'))
 for target in direct_386:
  c.execute('INSERT INTO legal_event VALUES(?,?,?,?,?,?,?,?,?,?)',(f'EO:12553#REVOKE#{target}','EO:12553',target,'1986-02-25','day','formal_revocation_with_amendments','Named predecessor expressly revoked with any amendments thereto; historical rights and prior first ending unreviewed','EO12553_CACHED_FULL_TEXT','FORMAL_REVOCATION_ONLY_FIRST_CESSATION_NOT_KNOWN','source_schedule_text_and_NARA_identity_crosschecked_no_predecessor_whole_scope_review'))
 # EO 3461's saved-incumbent revocation family: source graph recovery is consumed
 # for historical event candidates, but source name matching alone cannot prove
 # 45 separate whole-order terminations or first dates.
 e3461=sorted({r[0] for r in c.execute("SELECT predecessor FROM candidate_relationships WHERE actor='EO:3461' AND eligible_for_research=1") if r[0] != 'EO:3461'})
 # Any existing base relations not enumerated explicitly by 3461's original revocation
 # list are not silently promoted. Use the recovered 45 NARA successor candidates.
 e3461_recovered=sorted({r[0] for r in c.execute("SELECT predecessor FROM candidate_relationships WHERE actor='EO:3461' AND provenance_type='NARA_1989_source_row_discovered' AND eligible_for_research=1")})
 assert len(e3461_recovered)==45,(len(e3461_recovered),e3461_recovered[:4])
 for target in e3461_recovered:
  if target in ('EO:2596','EO:2602'):continue # already separately written scoped events
  c.execute('INSERT INTO legal_event VALUES(?,?,?,?,?,?,?,?,?,?)',(f'EO:3461#SOURCE_REVOKES#{target}','EO:3461',target,'1921-05-16','day','revocation_subject_to_incumbent_savings','Historical civil-service exception named in EO3461 family; source text subject to existing-appointee saving clause','NARA_EO3461','FIRST_CAUSE_UNPROVEN_AND_SURVIVING_STATUS_UNCHECKED','archival_editorial_successor_crosscheck_original_named_list_held'))

 # Stage15 valid probability sample permanently registered IN the analysis database.
 # No survival estimate may be issued from unreviewed sampled observations.
 with open(SAMPLE,newline='') as f:
  for r in csv.DictReader(f):
   assert r['release_status']=='UNREVIEWED' and r['answer_key_held_separately']=='YES'
   c.execute('INSERT INTO probability_sample VALUES(?,?,?,?,?,?,?,?,NULL,NULL)',(r['id'],r['era'],r['source_class'],int(r['stratum_N']),int(r['stratum_sample_n']),float(r['inclusion_probability']),float(r['design_weight']),'UNREVIEWED'))
 assert c.execute('SELECT count(*) FROM probability_sample').fetchone()[0]==120
 assert abs(c.execute('SELECT sum(design_weight) FROM probability_sample').fetchone()[0]-14972)<0.01

 # Stage16 source-based status conclusions NOT magically full independent double-reviewed truth.
 # Guard machine promotions and make enforceable evidence tests programmatic.
 for id, in c.execute('SELECT id FROM v3_effect_assessments').fetchall():
  c.execute("UPDATE legal_readiness SET episode_coverage_state= 'stage16_source_scoped_reconstruction_with_open_residuals' WHERE id=?",(id,))

 for name,val in [('codebook_version',V3),('cutoff',CUTOFF),('source_stage11_sha256',hashes['stage11']),('source_stage14_sha256',hashes['stage14']),('source_pdf_sha256',hashes['lord']),('pipeline_status','SOURCE_SENSITIVE_RESEARCH_RELEASE_NOT_A_NATIONAL_CENSUS')]:
  c.execute('INSERT INTO build_metadata VALUES(?,?)',(name,str(val)))
 c.commit()

 # Metrics computed from DB, never editorial spreadsheet claims.
 q=lambda query:c.execute(query).fetchone()[0]
 counts=dict(original_rows=q('SELECT count(*) FROM original_stage11_rows'),working_unique_proxies=q('SELECT sum(include_proxy) FROM instruments'),stage11_determinate=q("SELECT count(*) FROM instruments WHERE include_proxy=1 AND original_legacy_status IN('yes','no')"),stage11_yes=q("SELECT count(*) FROM instruments WHERE include_proxy=1 AND original_legacy_status='yes'"),stage11_no=q("SELECT count(*) FROM instruments WHERE include_proxy=1 AND original_legacy_status='no'"),stage11_unknown=q("SELECT count(*) FROM instruments WHERE include_proxy=1 AND original_legacy_status='indeterminate'"),source_observations=q('SELECT count(*) FROM source_observations'),usable_candidate_relations=q('SELECT count(*) FROM candidate_relationships WHERE eligible_for_research=1'),excluded_candidate_relations=q('SELECT count(*) FROM candidate_relationships WHERE eligible_for_research=0'),recovered_candidate_relations=q("SELECT count(*) FROM candidate_relationships WHERE provenance_type='NARA_1989_source_row_discovered' AND eligible_for_research=1"),lord_unnumbered_date_leads_not_orders=q('SELECT count(*) FROM lord_date_markers'),lord_candidate_context_excerpts=q("SELECT count(*) FROM lord_source_excerpts WHERE extraction_grade='SOURCE_OCR_CONTEXT_NOT_AUTHENTICATED'"),lord_to_NARA_date_only_hypotheses=q('SELECT count(*) FROM lord_nara_date_matches'),recovered_archival_unnumbered_dates=q('SELECT count(*) FROM source_date_references'),curated_provision_episodes=q('SELECT count(*) FROM legal_episode'),curated_legal_events=q('SELECT count(*) FROM legal_event'),EO12553_named_formal_revocations=q("SELECT count(*) FROM legal_event WHERE actor_instrument='EO:12553'"),EO3461_named_revocation_events=q("SELECT count(*) FROM legal_event WHERE actor_instrument='EO:3461'"),source_reviewed_v3_whole_order_scope_no=q("SELECT count(*) FROM v3_effect_assessments WHERE normative_status='no'"),source_reviewed_v3_held=q("SELECT count(*) FROM v3_effect_assessments WHERE normative_status='indeterminate'"),uncertified_source_reviewed_v3=q("SELECT count(*) FROM v3_effect_assessments WHERE review_grade='source_reviewed_not_independently_certified'"),independent_human_verified_v3=q('SELECT count(*) FROM legal_readiness WHERE v3_certified=1'),probability_sample_n=q('SELECT count(*) FROM probability_sample'),probability_sample_completed_n=q("SELECT count(*) FROM probability_sample WHERE review_state='REVIEWED'"),classified_no_without_structured_stage11_episode=q("SELECT count(*) FROM legal_readiness WHERE legacy_status='no' AND episode_count=0"),determinate_without_structured_stage11_episode=q("SELECT count(*) FROM legal_readiness WHERE legacy_status IN('yes','no') AND episode_count=0"),historically_issued_exact_total_known=False)
 assert (counts['stage11_yes'],counts['stage11_no'],counts['stage11_unknown'])==(193,2322,12457)
 assert counts['determinate_without_structured_stage11_episode']==1868
 assert counts['recovered_candidate_relations']==510
 assert counts['usable_candidate_relations']==7084 and counts['excluded_candidate_relations']==121
 assert counts['source_reviewed_v3_whole_order_scope_no']==1
 assert counts['source_reviewed_v3_held']==4
 assert counts['curated_provision_episodes']>=20
 assert counts['lord_to_NARA_date_only_hypotheses']>=0

 # Snapshot legal and counting reach of the source graph and manuscript uncertainty.
 stats={'input_hashes':hashes,'metrics':counts,'legal_effect_framework':{'primary': 'operative_norms_or_constitutive_status', 'secondary':'enduring_consequences', 'legacy_codebook':'2.0.0_frozen', 'new_codebook':V3},'illustrative_family':{'official_full_text_first_pass_closure_orders':[x['id'] for x in closures],'closure_days_reconstructed':n_closed,'whole_order_first_cessation_dates_added':0,'why_zero':'Future payroll/leave and OPM implementation may produce residual operation; provision expiration dates are distinct from proven full-order first cessation'},'provenance':'New online source texts independently inspected via web, not locally byte-downloaded or human peer-reviewed; all statuses described as source-reviewed first pass.'}
 dump(ROOT/'REPORTS/VERIFIED_BUILD_METRICS.json',stats)
 rows=[]
 for beg,end in [(1789,1861),(1862,1906),(1907,1936),(1937,1989),(1990,2026)]:
  x=c.execute("SELECT original_legacy_status,count(*) FROM instruments WHERE include_proxy=1 AND CAST(substr(issuance_date,1,4) AS INTEGER) BETWEEN ? AND ? GROUP BY original_legacy_status",(beg,end)).fetchall();a=dict(x);rows.append(dict(period=f'{beg}-{end}',yes=a.get('yes',0),no=a.get('no',0),unknown=a.get('indeterminate',0),total=sum(a.values())))
 x=c.execute("SELECT original_legacy_status,count(*) FROM instruments WHERE include_proxy=1 AND (issuance_date IS NULL OR issuance_date='' OR issuance_date='unknown') GROUP BY original_legacy_status").fetchall();a=dict(x);rows.append(dict(period='UNDATED',yes=a.get('yes',0),no=a.get('no',0),unknown=a.get('indeterminate',0),total=sum(a.values())))
 with open(ROOT/'REPORTS/PROGRESS_BY_ERA.csv','w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
 
 c.close();graph.close()
 print(json.dumps({'status':'PASS','output':str(out),'counts':counts,'era_rows':rows},indent=2))
if __name__=='__main__':main()
