#!/usr/bin/env python3
"""EO Stage 14: non-destructive, reproducible source-first research compiler.

Only builds research dependencies/packets; never changes substantive legal status.
Uses sealed Stage 11 ledger, Stage 13 projected identities and the official Stage 10
cached source importer. No assertions that references are whole-scope legal endings.

Examples:
 python eo_leverage_engine.py build --stage11 ...zip --stage13 ...jsonl --importer ...zip --stage12 ... --output ...
 python eo_leverage_engine.py show --database ...sqlite --id EO:3461
 python eo_leverage_engine.py cluster --database ...sqlite --actor EO:12553
 python eo_leverage_engine.py search --database ...sqlite --query 'homeland security'
 python eo_leverage_engine.py packet --database ...sqlite --actor EO:12553 --output ./packet.json
"""
import argparse,collections,csv,datetime,hashlib,json,math,pathlib,re,sqlite3,sys,zipfile

VER='EO-LEVERAGE-ENGINE-1.0.0'
NOW='2026-10-16'
CUTOFF='2026-10-14'
KNOWN_SCOPE_BLOCKERS={
 'EO:11408':'EXPRESS_PARTIAL_SCOPE: revokes listed amendments to EO9 only insofar as specified; do not infer whole order NO',
 'EO:9521':'CONDITIONAL_REGULATORY_REPLACEMENT: test matching agency regulations and dates',
 'EO:3461':'SAVINGS_OF_INCUMBENT_ELIGIBILITY: requires predecessor original and saved-right attribution',
 'EO:12553':'SCOPE_AND_CROSS_SOURCE_DISAGREEMENT: compare primary revocation schedule and NARA/FR, inspect residual rights',
 'EO:9805':'SAVED_PENDING_TRANSFERS: verify each incomplete transfer',
 'EO:6179-A':'PERSON_SPECIFIC_CANCELLATION: do not conflate cancelled appointment with underlying authority',
 'EO:12220':'PREVIOUS_PARTIAL_SUPERSESSION: later formal revocation not first cessation for all scopes',
}
ENDING={'express_revocation_claim','rescission','supersession','nullification','termination','revocation','express_supersession_claim','express_rescission_claim'}
def sha(b):return hashlib.sha256(b).hexdigest()
def lines(data):
 for line in data.splitlines():
  if line.strip():yield json.loads(line)
def dumpjson(path,obj):
 pathlib.Path(path).parent.mkdir(parents=True,exist_ok=True)
 pathlib.Path(path).write_text(json.dumps(obj,indent=2,ensure_ascii=False,sort_keys=True)+'\n',encoding='utf8')
def dumpcsv(path,rows,keys):
 pathlib.Path(path).parent.mkdir(parents=True,exist_ok=True)
 with open(path,'w',encoding='utf8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');w.writeheader();w.writerows(rows)
def lim(s,n=550):return str(s or '')[:n]
def normalized_id(s):
 if not s:return s
 s=str(s).strip()
 if re.fullmatch(r'EO:\d+[A-Za-z]',s):return s[:-1]+s[-1].upper()
 return s

def load_build(args):
 out=pathlib.Path(args.output);out.mkdir(parents=True,exist_ok=True)
 db=out/'DATA/EO_SOURCE_DEPENDENCY_GRAPH.sqlite';db.parent.mkdir(parents=True,exist_ok=True)
 if db.exists():db.unlink()
 c=sqlite3.connect(db);c.execute('PRAGMA journal_mode=OFF');c.execute('PRAGMA synchronous=OFF');
 c.executescript('''
 CREATE TABLE orders(id TEXT PRIMARY KEY,canonical_group TEXT,include_unique INT,included_validated INT,population_class TEXT,title TEXT,year INT,signing_date TEXT,substantive TEXT,any_effect TEXT,cause_mechanism TEXT,first_cause_date TEXT,evidence_grade TEXT,review_status TEXT,source_ids TEXT,provenance_shard TEXT);
 CREATE TABLE sources(key TEXT PRIMARY KEY,filename TEXT,sha256 TEXT,kind TEXT,valid_asof TEXT,canonical_url TEXT);
 CREATE TABLE observations(obs_id INTEGER PRIMARY KEY,source_kind TEXT,instrument_id TEXT,raw_label TEXT,source_sha256 TEXT,source_url TEXT,asof TEXT,category TEXT,disposition TEXT,amendments TEXT,notes TEXT,table_index INT,table_row INT);
 CREATE TABLE relationships(edge_id INTEGER PRIMARY KEY,actor TEXT,predecessor TEXT,relation TEXT,statement TEXT,source_url TEXT,asof TEXT,evidence_level TEXT,quarantined INT DEFAULT 0,quarantine_reason TEXT);
 CREATE TABLE queues(instrument_id TEXT PRIMARY KEY,owner TEXT,track TEXT,priority INTEGER,original_source TEXT);
 CREATE TABLE problem_flags(instrument_id TEXT,code TEXT,detail TEXT,source TEXT);
 CREATE TABLE audit_sample(instrument_id TEXT,kind TEXT,ordinal INTEGER,PRIMARY KEY(instrument_id,kind));
 CREATE INDEX idx_edges_actor ON relationships(actor); CREATE INDEX idx_edges_pred ON relationships(predecessor);
 CREATE INDEX idx_obs_order ON observations(instrument_id); CREATE INDEX idx_obs_source ON observations(source_sha256);
 CREATE INDEX idx_orders_status ON orders(substantive); CREATE INDEX idx_queues_track ON queues(track);
 CREATE VIRTUAL TABLE search_index USING fts5(id UNINDEXED,text,kind UNINDEXED,tokenize='unicode61');
 ''')
 raw11=pathlib.Path(args.stage11).read_bytes();z11=zipfile.ZipFile(args.stage11)
 raw13=pathlib.Path(args.stage13).read_bytes();r13={r['instrument_id']:r for r in lines(raw13)}
 R=list(lines(z11.read('RECONCILED_STATUS_LEDGER_STAGE11_PROVISIONAL.jsonl')))
 assert len(R)==15010 and len(r13)==15010
 assert all(r['instrument_id'] in r13 for r in R)
 s11=collections.Counter(); src_ledger=[]
 for r in R:
  k=r['instrument_id'];d=r13[k];ss=r.get('substantive_effect');
  if r.get('included_validated'):s11[ss]+=1
  inc=bool(d.get('included_unique_document_proxy'))
  title=lim(r.get('title'),1500);year=d.get('year_audit_projection');
  srcids=json.dumps(r.get('source_ids',[]),ensure_ascii=False)
  src_ledger.append((k,d.get('canonical_document_group'),int(inc),int(bool(r.get('included_validated'))),r.get('population_class'),title,year,d.get('signing_date_audit_projection'),ss,r.get('any_operative_EO_effect'),str(r.get('cessation_mechanism') or 'unknown'),str(r.get('first_cessation_date') or 'unknown'),r.get('evidence_grade'),r.get('review_status'),srcids,r.get('provenance_shard')))
 c.executemany('INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',src_ledger)
 c.executemany('INSERT INTO search_index(id,text,kind) VALUES (?,?,?)',[(r[0],r[5],'title') for r in src_ledger if r[5]])
 assert s11=={'yes':193,'no':2322,'indeterminate':12458},s11
 zimp=zipfile.ZipFile(args.importer);prefix='EO_IMPORT_WORK/'
 cache={};registries=[]
 for n in zimp.namelist():
  if n.startswith(prefix+'RAW_OFFICIAL_SOURCES/') and (n.endswith('.html') or ('fedreg_bulk_' in n and n.endswith('.json'))):
   b=zimp.read(n);s=sha(b)
   typ='NARA_CODIFICATION_1989' if 'nara_numeric' in n else 'FEDERAL_REGISTER_BULK'
   # Official URL comes from source archive manifest, not reconstructed beyond known stable NARA table names.
   u=('https://www.archives.gov/federal-register/codification/executive-orders-'+str(int(n.rsplit('_',1)[1].split('.')[0]))+'.html') if typ=='NARA_CODIFICATION_1989' else 'https://www.federalregister.gov/api/v1/documents.json'
   cache[s]=n;registries.append((s,n,s,typ,'1989-01-20' if typ.startswith('NARA') else None,u))
 c.executemany('INSERT INTO sources VALUES (?,?,?,?,?,?)',registries)
 ob=list(lines(zimp.read(prefix+'FULL_RESULTS/EDITORIAL_SOURCE_OBSERVATIONS.jsonl')))
 for r in ob:
  c.execute('INSERT INTO observations(source_kind,instrument_id,raw_label,source_sha256,source_url,asof,category,disposition,amendments,notes,table_index,table_row) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(
   r.get('source_kind'),r.get('instrument_id'),r.get('raw_identifier'),r.get('raw_source_sha256'),r.get('source_url'),r.get('editorial_as_of'),r.get('editorial_category'),r.get('disposition_text'),r.get('amendments'),json.dumps({'successor_candidates':r.get('successor_candidates',[]),'amendment_reference_candidates':r.get('amendment_reference_candidates',[])},ensure_ascii=False),r.get('table_index'),r.get('table_row_index')))
  txt=' '.join([str(r.get(k) or '') for k in ('disposition_text','amendments')]);
  if txt.strip():c.execute('INSERT INTO search_index(id,text,kind) VALUES(?,?,?)',(r.get('instrument_id'),lim(txt,3000),'editorial'))
 er=list(lines(zimp.read(prefix+'FULL_RESULTS/OUTGOING_ACTOR_RELATIONSHIPS.jsonl')))
 qset=set()
 for q in lines(zimp.read(prefix+'FULL_RESULTS/ACTOR_RELATION_QUARANTINE.jsonl')):
  qset.add((q.get('actor'),q.get('target_id'),q.get('relation')))
 conflicts=list(lines(zimp.read(prefix+'FULL_RESULTS/CROSS_SOURCE_ACTOR_DISAGREEMENTS.jsonl')))
 conflict_actors=set(v.get('actor') for v in conflicts)
 suspect_subjects=list(lines(zimp.read(prefix+'FULL_RESULTS/SUBJECT_SUCCESSOR_CLAIM_QUARANTINE.jsonl')))
 for r in er:
  key=(r.get('actor'),r.get('predecessor'),r.get('relation')); blocked=key in qset
  c.execute('INSERT INTO relationships(actor,predecessor,relation,statement,source_url,asof,evidence_level,quarantined,quarantine_reason) VALUES(?,?,?,?,?,?,?,?,?)',(
    r.get('actor'),r.get('predecessor'),r.get('relation'),r.get('statement'),r.get('editorial_source'),r.get('editorial_as_of'),r.get('evidence_level'),int(blocked), 'source parser quarantine' if blocked else None))
 # Preserve 117 rejected extraction hypotheses as explicit quarantined graph rows.
 # They are excluded from relationship inference and benefit calculations.
 for r in lines(zimp.read(prefix+'FULL_RESULTS/ACTOR_RELATION_QUARANTINE.jsonl')):
  key=(r.get('actor'),r.get('target_id'),r.get('relation'))
  if key in qset and any(x.get('actor')==key[0] and x.get('predecessor')==key[1] and x.get('relation')==key[2] for x in er):continue
  c.execute('INSERT INTO relationships(actor,predecessor,relation,statement,source_url,asof,evidence_level,quarantined,quarantine_reason) VALUES(?,?,?,?,?,?,?,?,?)',(
    r.get('actor'),r.get('target_id'),r.get('relation'),r.get('actor_statement'),None,'1989-01-20','QUARANTINED_PARSER_LEAD',1,r.get('error')))
 for r in conflicts:
  c.execute('INSERT INTO problem_flags VALUES(?,?,?,?)',(r.get('actor'),'CROSS_SOURCE_ACTOR_DISAGREEMENT',json.dumps(r,sort_keys=True), 'importer_cross_source'))
 for a,desc in KNOWN_SCOPE_BLOCKERS.items():
  c.execute('INSERT INTO problem_flags VALUES(?,?,?,?)',(a,'KNOWN_SCOPE_OR_ATTRIBUTION_RISK',desc,'stage13_dossier'))
 for r in suspect_subjects:
  c.execute('INSERT INTO problem_flags VALUES(?,?,?,?)',(r.get('subject'),'SOURCE_DISAGREEMENT',json.dumps(r),'stage10_importer'))
 # If normalized collision, use only analytic group for counts; original documentary IDs remain addressable.
 for r in R:
  k=r['instrument_id'];d=r13[k]
  if d.get('canonical_document_group')!=k:
   c.execute('INSERT INTO problem_flags VALUES(?,?,?,?)',(k,'DOCUMENT_ID_COLLISION','canonical group='+str(d.get('canonical_document_group')),'stage13_overlay'))
 for name in ['WORKLISTS/STAGE11_RECONCILED_PRIORITY_2841.jsonl','WORKLISTS/ASTRA_STAGE11_REVERSE_ENDINGS_1696.jsonl','WORKLISTS/OPUS_STAGE11_FINITE_CONTINUITY_1145.jsonl']:
  records=list(lines(z11.read(name)))
  if '2841' in name: allqueue=records
  else: pass
 # Discover field names from stage 11 manifest - never invent assignments.
 task_owner={}
 for owner,name in [('ASTRA','WORKLISTS/ASTRA_STAGE11_REVERSE_ENDINGS_1696.jsonl'),('OPUS','WORKLISTS/OPUS_STAGE11_FINITE_CONTINUITY_1145.jsonl')]:
  for r in lines(z11.read(name)):
   k=r.get('instrument_id') or r.get('id')
   if k:task_owner[k]=owner
 for i,r in enumerate(allqueue):
  k=r.get('instrument_id') or r.get('id')
  if not k:raise ValueError('No instrument_id in source queue')
  track=r.get('research_track') or r.get('track') or ''
  c.execute('INSERT INTO queues VALUES(?,?,?,?,?)',(k,task_owner.get(k,'UNASSIGNED'),track,i+1,'Stage11 frozen queue'))
 # Import baseline blind review IDs ONLY. Private answer key omitted entirely.
 import csv as _csv
 with open(args.stage12_sample,encoding='utf8',newline='') as f:
  sr=list(_csv.DictReader(f))
 for i,r in enumerate(sr):
  k=r.get('instrument_id') or r.get('id') or r.get('canonical_id')
  if not k:raise ValueError('Blind audit CSV requires instrument_id')
  c.execute('INSERT INTO audit_sample VALUES(?,?,?)',(k,'BLIND_60',i+1))
 c.commit()
 # Task statistics are dependency counts (not probabilistic classifications), favor source reuse.
 causal_unknown={r['instrument_id'] for r in R if r.get('included_validated') and r.get('substantive_effect')=='no' and r.get('cessation_mechanism')=='unknown'}
 remain_unk={r['instrument_id'] for r in R if r.get('included_validated') and r.get('substantive_effect')=='indeterminate'}
 currentQ=set(k for (k,) in c.execute('SELECT instrument_id FROM queues'))
 group=collections.defaultdict(lambda:{'unknown':set(),'cause':set(),'all':set(),'sources':set(),'rel':collections.Counter()})
 for actor,pred,rel,url,quar in c.execute('SELECT actor,predecessor,relation,source_url,quarantined FROM relationships'):
  if quar:continue
  if rel not in ENDING and not ('revok' in rel or 'supersed' in rel or 'rescind' in rel or 'terminat' in rel or 'nullif' in rel):continue
  k=group[actor]; k['all'].add(pred); k['rel'][rel]+=1; k['sources'].add(url)
  if pred in remain_unk:k['unknown'].add(pred)
  if pred in causal_unknown:k['cause'].add(pred)
 # Distinct readiness measures: source link, known exception, conflict, queue owner.
 actorrows=[];cause_targets=set();unk_targets=set()
 for actor,g in group.items():
  U=g['unknown'];N=g['cause'];qcur=U&currentQ
  if not (U or N):continue
  risk=[]
  if actor in KNOWN_SCOPE_BLOCKERS:risk.append(KNOWN_SCOPE_BLOCKERS[actor])
  if actor in conflict_actors:risk.append('CROSS_SOURCE_ACTOR_DISAGREEMENT')
  if not U and not N:continue
  source_edges=len(g['all'])
  # Actor scientific dependency priority: reusable historical cause and present status,
  # then potential shared-root contamination; penalty for known scope limitations.
  # Formal endings offer useful latest-date bounds, but almost never prove FIRST cause.
  reach=len(U)+0.04*len(N)
  score=round(reach*math.log2(1+source_edges)*(1 if not risk else 0.68),2)
  label='EXCEPTION_FIRST_PROTOCOL' if risk else 'CONTROLLING_SOURCE_FIRST'
  owner=collections.Counter(task_owner.get(x,'UNASSIGNED') for x in qcur)
  actorrows.append(dict(actor=actor,priority_score=score,distinct_unknown=len(U),stage11_queue_unknown=len(qcur),status_NO_missing_first_cause=len(N),distinct_predecessor_refs=len(g['all']),risk_flags=' | '.join(risk),source_count=len(g['sources']),work_type=label,unknown_ids=';'.join(sorted(U)),no_cause_ids=';'.join(sorted(N)),assigned=';'.join('%s:%s'%(k,v) for k,v in sorted(owner.items()))))
  cause_targets|=N;unk_targets|=U
 actorrows.sort(key=lambda x:(-x['priority_score'],-x['distinct_unknown'],x['actor']))
 keyfields=list(actorrows[0]) if actorrows else []
 dumpcsv(out/'QUEUES/REUSABLE_CONTROLLING_SOURCE_QUEUE.csv',actorrows,keyfields)
 # Accepted NO review group = correlated-source risk, do not treat independent records as independent errors.
 buckets=collections.defaultdict(list)
 for r in R:
  if not r.get('included_validated') or r.get('substantive_effect')!='no':continue
  cohort=(r.get('evidence_grade') or 'UNSPECIFIED',r.get('review_status') or 'UNSPECIFIED')
  buckets[cohort].append(r['instrument_id'])
 risks=[]
 for (grade,review),ids in buckets.items():
  # share provenance/reviewer style, but do not assert same legal rule without actual decision audit.
  risk_score=round(len(ids) * (1.4 if ('reported' in grade or 'reported' in review) else 1),2)
  risks.append(dict(evidence_grade=grade,review_status=review,accepted_no_count=len(ids),audit_exposure_score=risk_score,ids=';'.join(sorted(ids))))
 risks.sort(key=lambda x:-x['audit_exposure_score'])
 dumpcsv(out/'QUEUES/CORRELATED_REVIEW_EXPOSURE.csv',risks,list(risks[0]))
 # Source reuse summary: unique unknowns across all actors != sum per actor.
 known_origins=collections.Counter(r['source_kind'] for r in ob)
 source_usage=collections.Counter(r.get('raw_source_sha256') for r in ob)
 candidates=sorted(source_usage.items(),key=lambda x:-x[1])
 srcrows=[]
 for digest,count in candidates:
  related={r['instrument_id'] for r in ob if r.get('raw_source_sha256')==digest}
  srcrows.append(dict(source_sha256=digest,records=count,distinct_order_ids=len(related),unknown_order_ids=len(related&remain_unk),known_no_cause_ids=len(related&causal_unknown),file_in_frozen_cache=(digest in cache),filename=cache.get(digest,'')))
 dumpcsv(out/'QUEUES/CACHED_SOURCE_REUSE.csv',srcrows,list(srcrows[0]))
 # High priority is "build/fetch reusable source", not "label N orders NO".
 tasks=[
  {'rank':1,'task':'Maintain canonical source & dependency search index','type':'FOUNDATION','enables':'All EO lookup, duplicate-proofed source retrieval, actor group packets and reasoned status checks','built_in_this_release':True,'evidence':'15,010 ledger rows / official 11,164 metadata rows / 6,575 candidate actor relationships'},
  {'rank':2,'task':'Full Lord chronological-source extraction & signed-document crosswalk','type':'FOUNDATION','enables':'Close pre-1937 all-history numerator/denominator blindness; recover >1500 historical bibliography leads without individual web searches','built_in_this_release':'SOURCE_REGISTER_AND_ENTRY_REVIEW_QUEUE_ONLY','evidence':'1943 historical volume; Stage13 1,023 unverified date markers'},
  {'rank':3,'task':'Test source-family end inference once before mass application','type':'VALIDATION_GATE','enables':'Quarantine unsafe shared legal rules before they contaminate hundreds of results','built_in_this_release':'SHARED_SOURCE_QUARANTINE_AND_CLUSTER_EXPANSION','evidence':'15 government-source cross disagreements; 117 relation quarantine; explicit partial/savings cases'},
  {'rank':4,'task':'Acquire primary original texts and late statutory/agency changes as a shared cache','type':'FOUNDATION','enables':'Original footprint and negative 2026 continuity search across all affected candidate decisions','built_in_this_release':'DEDUPE_SOURCE_ACTIONS_AND_PACKET_GENERATOR','evidence':'Cached archive is editorial and metadata, not complete originals'},
  {'rank':5,'task':'Complete genuinely blind stratified status audits as family gates','type':'VALIDATION_GATE','enables':'Estimate error by source/review class and choose legal codebook; do not run hundreds of status cases under unvalidated family heuristics','built_in_this_release':'BLIND_SAFE_RESEARCH_PACKET_GENERATOR','evidence':'Stage13 first eight reviewed; 52 remaining'},
  {'rank':6,'task':'Provision-level first-cause event intervals for YES and NO','type':'CAUSAL_FOUNDATION','enables':'Competing-risk survival study and housekeeping-revocation estimate','built_in_this_release':'DISCOVERY_QUEUE_ONLY','evidence':'2,216/2,322 accepted substantive NO missing cessation mechanism'},
  {'rank':7,'task':'Mass classify remaining unknown orders','type':'DOWNSTREAM','enables':'Final completeness after validating upstream graph and legal rules','built_in_this_release':False,'evidence':'Keep Stage11 queue, no automated legal-status promotions'}]
 dumpjson(out/'PROTOCOLS/LEVERAGE_FIRST_TASK_DAG.json',tasks)
 # Packet generation for top 12 actor clusters; no model claims; source metadata only.
 packs=out/'WORKPACKS';packs.mkdir(exist_ok=True)
 for i,row in enumerate(actorrows[:12],1):
  p=actor_packet(c,row['actor'],max_targets=75)
  dumpjson(packs/('%02d_%s.json'%(i,row['actor'].replace(':','_'))),p)
 # Prepare genuinely blind research briefs for all Stage12 sample IDs; no baseline statuses.
 blind_dir=packs/'BLIND_60';blind_dir.mkdir(exist_ok=True)
 for k,kind,i in c.execute("SELECT instrument_id,kind,ordinal FROM audit_sample ORDER BY ordinal"):
  dumpjson(blind_dir/(f'{i:02d}_'+k.replace(':','_')+'.json'),single_packet(c,k,blind=True))
 metrics={
  'version':VER,'built_on':NOW,'historical_cutoff':CUTOFF,
  'source_sha256':{'stage11_packet_zip':sha(raw11),'stage13_overlay_jsonl':sha(raw13),'stage10_importer_zip':sha(pathlib.Path(args.importer).read_bytes())},
  'frozen_baseline':{'ledger_rows':len(R),'bibliographic_included':sum(x.get('included_validated') for x in R),'unique_working_proxies':sum(x.get('included_unique_document_proxy',False) for x in r13.values()),'substantive_decided':s11['yes']+s11['no'],'substantive_yes':s11['yes'],'substantive_no':s11['no'],'substantive_unknown':s11['indeterminate'],'new_status_promotions':0},
  'source_system':{'official_metadata_observations':len(ob),'candidate_actor_edges':len(er),'cross_source_actor_conflicts':len(conflicts),'actor_relation_quarantine_cases':len(qset),'frozen_raw_source_files':len(cache),'official_metadata_source_mix':dict(known_origins),'priority_unknown_stage11':len(allqueue),'stage11_ownership_counts':dict(collections.Counter(task_owner.values()))},
  'leverage_measured':{'actor_ending_clusters_with_unresolved_beneficiaries':len(actorrows),'unique_unknown_orders_mentioned_by_actor_ending_leads':len(unk_targets),'unique_NO_orders_with_unknown_cause_mentioned_by_actor_ending_leads':len(cause_targets),'source_files_with_known_caches':sum(bool(x['file_in_frozen_cache']) for x in srcrows),'actor_source_packets_generated':min(12,len(actorrows)),'blind_safe_individual_packets_generated':len(sr),'highest_fanout_actor':actorrows[0]['actor'] if actorrows else None},
  'epistemic_caveat':'All relationship data are candidate references; graph traversal cannot prove current legal status or first cessation date; a formal ending only gives a potential upper bound. Actor original text may be missing.',
  'files':{'db':str(db.relative_to(out)),'actor_queue':'QUEUES/REUSABLE_CONTROLLING_SOURCE_QUEUE.csv','cached_sources':'QUEUES/CACHED_SOURCE_REUSE.csv','blind_packets':'WORKPACKS/BLIND_60/'}}
 dumpjson(out/'REPORTS/ENGINE_METRICS.json',metrics)
 c.commit();c.close()
 return metrics

def cache_hits(c,key,excerpt_chars=0,limit=8):
    # Cached filename hints are never proof of EO authorship or whole-original scope.
    try:
        rs=list(c.execute("""SELECT cr.sha256,cr.source_url,cr.source_grade,cr.checksum_verdict,cr.archive_member,substr(cb.extracted_text,1,?) FROM cache_representations cr JOIN cache_blobs cb ON cb.sha256=cr.sha256 WHERE cr.subject_id_hint=? ORDER BY CASE cr.source_grade WHEN 'POSSIBLE_ORDER_TEXT_CACHED_UNAUTHENTICATED' THEN 0 WHEN 'POSSIBLE_GOVINFO_PUBLICATION_TEXT_UNAUTHENTICATED' THEN 1 ELSE 2 END, cr.checksum_verdict DESC LIMIT ?""",(excerpt_chars,key,limit)))
    except sqlite3.OperationalError:return []
    return [{'sha256':r[0],'source_url':r[1],'grade':r[2],'checksum':r[3],'member_path':r[4],**({'text_excerpt':r[5]} if excerpt_chars else {})} for r in rs]

def single_packet(c,key,blind=False):
 # Blind reviewers receive primary metadata and sources, but no accepted status or grades.
 order=c.execute('SELECT id,title,signing_date,canonical_group,population_class,substantive,any_effect,evidence_grade FROM orders WHERE id=?',(key,)).fetchone()
 if not order:return {'error':'ID not in dataset','id':key}
 cols=['id','title','date_provisional','canonical_group','population_class']
 d=dict(zip(cols,order[:5]))
 if not blind:d.update(baseline_substantive=order[5],baseline_any_effect=order[6],baseline_evidence_grade=order[7])
 obs=[{'kind':r[0],'source_url':r[1],'source_sha256':r[2],'editorial_asof':r[3],'historical_category':r[4],'disposition_excerpt':lim(r[5],580),'amendments_excerpt':lim(r[6],480)}
      for r in c.execute('SELECT source_kind,source_url,source_sha256,asof,category,disposition,amendments FROM observations WHERE instrument_id=? LIMIT 20',(key,))]
 edges=[{'actor':r[0],'relation':r[1],'statement':lim(r[2],260),'source_url':r[3],'quarantined':bool(r[4])} for r in c.execute('SELECT actor,relation,statement,source_url,quarantined FROM relationships WHERE predecessor=? ORDER BY quarantined ASC LIMIT 32',(key,))]
 output={'subject':d,'official_editorial_observations':obs,'later_actor_relation_leads':edges,'reusable_cached_source_hints':cache_hits(c,key,excerpt_chars=1400),'evidence_scope':'Official archived editorial metadata only; full original instrument and current-law continuity NOT established by this packet','classification_allowed_without_source_review':False}
 if blind:output['blind_review_rules']=['Retrieve original instrument independently before viewing any prior case review','Resolve all operative clauses, saved rights, incorporation and scope','Search bounded later events to cutoff 2026-10-14','Freeze and hash review BEFORE opening baseline answer key','No search results or editorial note alone proves a NO']
 return output

def actor_packet(c,actor,max_targets=75):
 rows=list(c.execute('''SELECT DISTINCT predecessor,relation,quarantined,source_url,statement FROM relationships WHERE actor=? ORDER BY predecessor,relation LIMIT 1000''',(actor,)))
 subj=[r[0] for r in rows if not r[2]]
 relevant=list(dict.fromkeys(subj))
 o=c.execute('SELECT title,signing_date FROM orders WHERE id=?',(actor,)).fetchone()
 flags=[dict(code=r[0],detail=lim(r[1],1000)) for r in c.execute('SELECT code,detail FROM problem_flags WHERE instrument_id=?',(actor,))]
 statuses=dict(c.execute('SELECT id,substantive FROM orders WHERE id IN ('+','.join('?'*len(relevant))+')',relevant)) if relevant else {}
 origin_count=collections.Counter(statuses.values())
 if max_targets:relevant=relevant[:max_targets]
 return {'actor':actor,'actor_title':o[0] if o else None,'actor_date':o[1] if o else None,'unique_listed_predecessor_count':len(set(subj)),'known_status_mix_of_listed':dict(origin_count),'risk_flags':flags,'cached_actor_source_hints':cache_hits(c,actor,excerpt_chars=3500),'predecessor_refs':[{'id':k,'status_unknown':statuses.get(k)=='indeterminate','reference_claims':[{'relation':r[1],'source_url':r[3],'statement':lim(r[4],280),'quarantined':bool(r[2])} for r in rows if r[0]==k][:5]} for k in relevant],
  'required_facts_before_batch_decision':['Authentic complete ACTOR text and all savings/conditions','Complete original text of every predecessor, or specific justified whole-scope exception','Effective date versus signature/publication','Actor action covers entire original operative footprint','Prior cessation of each provision before actor, and later revivals','Residual duties/rights/host amendments','Independent legal review and counterevidence search'],
  'no_automatic_status_inferences':True}

def cmd_read(args):
 c=sqlite3.connect(args.database)
 if args.command=='show':print(json.dumps(single_packet(c,args.id),indent=2,ensure_ascii=False))
 elif args.command=='cluster':print(json.dumps(actor_packet(c,args.actor,max_targets=args.max_targets),indent=2,ensure_ascii=False))
 elif args.command=='packet':
  obj=actor_packet(c,args.actor,max_targets=args.max_targets) if args.actor else single_packet(c,args.id,blind=args.blind)
  dumpjson(args.output,obj);print(args.output)
 elif args.command=='search':
  rows=list(c.execute('''SELECT id,kind,snippet(search_index,1,'[',']','...',13) FROM search_index WHERE search_index MATCH ? LIMIT ?''',(args.query,args.limit)))
  print(json.dumps([{'id':r[0],'kind':r[1],'match':r[2]} for r in rows],indent=2,ensure_ascii=False))
 elif args.command=='search-cache':
  rows=list(c.execute("SELECT sha256,snippet(cache_fts,1,'[',']','...',18) FROM cache_fts WHERE cache_fts MATCH ? LIMIT ?",(args.query,args.limit)))
  print(json.dumps([{'sha256':r[0],'cached_text_excerpt':r[1]} for r in rows],indent=2,ensure_ascii=False))
 elif args.command=='source':
  print(json.dumps({'id':args.id,'cached_local_representations':cache_hits(c,args.id,excerpt_chars=args.max_chars,limit=10)},indent=2,ensure_ascii=False))
 c.close()

def main():
 a=argparse.ArgumentParser(description=__doc__);sub=a.add_subparsers(dest='command',required=True)
 b=sub.add_parser('build');b.add_argument('--stage11',required=True);b.add_argument('--stage13',required=True);b.add_argument('--importer',required=True);b.add_argument('--stage12-sample',required=True);b.add_argument('--output',required=True)
 for command in ['show','cluster','search','search-cache','source','packet']:
  p=sub.add_parser(command);p.add_argument('--database',required=True)
  if command in ['show','source','packet']:p.add_argument('--id')
  if command in ['cluster','packet']:p.add_argument('--actor');p.add_argument('--max-targets',type=int,default=75)
  if command in ['search','search-cache']:p.add_argument('--query',required=True);p.add_argument('--limit',type=int,default=20)
  if command=='source':p.add_argument('--max-chars',type=int,default=16000)
  if command=='packet':p.add_argument('--output',required=True);p.add_argument('--blind',action='store_true')
 args=a.parse_args()
 if args.command=='build':print(json.dumps(load_build(args),indent=2))
 else:cmd_read(args)
if __name__=='__main__':main()
