"""Recovers omitted *candidate* successor references from already-cached 1989 NARA editorial rows.
Corrects a discovery graph omission without asserting revocation of whole operative footprint,
first cessation, or a 2026 YES/NO. Never patches the immutable Stage14 source database.
"""
import sqlite3,json,csv,re,collections,os
from pathlib import Path
SRC=Path(os.environ.get('EO_STAGE14_GRAPH','/mnt/data/eo_stage15_workspace/EO_STAGE14_LEVERAGE_ENGINE_2026-10-16/DATA/EO_SOURCE_DEPENDENCY_GRAPH.sqlite'))
ROOT=Path(os.environ.get('EO_STAGE15_OUTPUT_DIR','/mnt/data/EO_STAGE15_METHOD_FOUNDATION_2026-10-16'))
conn=sqlite3.connect(SRC);conn.row_factory=sqlite3.Row
O={r['id']:dict(r) for r in conn.execute('select id,signing_date,substantive,cause_mechanism,included_validated from orders')}
existing={(r['actor'],r['predecessor']) for r in conn.execute('select actor,predecessor from relationships')}
recovered=[]
for r in conn.execute("select obs_id,instrument_id,category,disposition,notes,source_sha256,source_url,asof from observations where source_kind='NARA_CODIFICATION_1989'"):
 try: successors=json.loads(r['notes'] or '{}').get('successor_candidates') or []
 except ValueError:continue
 for actor in successors:
  if (actor,r['instrument_id']) in existing:continue
  a=O.get(actor);b=O.get(r['instrument_id']);
  if not a or not b:classification='UNRESOLVED_MISSING_CATALOG_ID'
  elif re.fullmatch(r'\d{4}-\d{2}-\d{2}',a.get('signing_date') or '') and re.fullmatch(r'\d{4}-\d{2}-\d{2}',b.get('signing_date') or '') and a['signing_date']<b['signing_date']:classification='QUARANTINE_REVERSE_CHRONOLOGY'
  else:classification='CANDIDATE_PREDECESSOR_RELATION_ONLY'
  recovered.append({'source_obs_id':r['obs_id'],'actor':actor,'candidate_predecessor':r['instrument_id'],'actor_date':a['signing_date'] if a else '', 'predecessor_date':b['signing_date'] if b else '', 'source_category':r['category'],'editorial_disposition':r['disposition'],'source_pdf_or_html_sha256':r['source_sha256'],'source_url':r['source_url'],'editorial_source_asof_not_event_date':r['asof'],'acceptance_class':classification,'target_stage11_substantive':b['substantive'] if b else 'not_in_ledger','causal_promotion_allowed':'NO','whole_order_NO_promotion_allowed':'NO'})
path=ROOT/'AUDIT/RECOVERED_MISSING_NARA_SUCCESSOR_CANDIDATES.csv';path.parent.mkdir(parents=True,exist_ok=True)
with path.open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,recovered[0].keys());w.writeheader();w.writerows(recovered)
assert len(recovered)==513, len(recovered)
usable=[x for x in recovered if x['acceptance_class']=='CANDIDATE_PREDECESSOR_RELATION_ONLY']
assert len(usable)==512
# combine already valid Stage14 edges with new NARA candidacy evidence; record source origin distinction.
side=sqlite3.connect(ROOT/'AUDIT/EO_STAGE15_SCHEMA_AND_RISK_SIDECAR.sqlite')
suppressed={x[0] for x in side.execute('select edge_id from directed_event_guard where stage15_suppress=1')}
outpath=ROOT/'AUDIT/CHRONOLOGY_AND_COMPLETENESS_GATED_RELATION_FEED.csv';present=[]
for r in conn.execute('select edge_id,actor,predecessor,relation,source_url,asof from relationships'):
 if r['edge_id'] in suppressed:continue
 present.append({'edge_id':f'S14:{r["edge_id"]}','actor':r['actor'],'predecessor':r['predecessor'],'relation':r['relation'],'source_url':r['source_url'],'evidence_status':'STAGE14_CANDIDATE_EDGE'} )
for r in usable:
 present.append({'edge_id':f'NARA_OBS:{r["source_obs_id"]}:{r["actor"]}', 'actor':r['actor'],'predecessor':r['candidate_predecessor'],'relation':r['source_category'],'source_url':r['source_url'],'evidence_status':'STAGE15_RECOVERED_NARA_EDITORIAL_LEAD'})
assert len(present)==6574+512
with outpath.open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,present[0].keys());w.writeheader();w.writerows(present)
# recompute uncertainty impact against legal statuses without double counting
ct=collections.Counter(x['acceptance_class'] for x in recovered)
candidates_by_actor=collections.defaultdict(list)
for r in present:
 if any(x in r['relation'] for x in ['revoc','revok','supersed','terminat','rescind','nullif','ending']):
  candidates_by_actor[r['actor']].append(r['predecessor'])
q=[]
for actor,targets in candidates_by_actor.items():
 ids=sorted(set(targets));uk=[i for i in ids if i in O and O[i]['substantive']=='indeterminate'];nc=[i for i in ids if i in O and O[i]['substantive']=='no' and O[i]['cause_mechanism']=='unknown'];
 if not uk and not nc:continue
 q.append({'candidate_ending_source':actor,'unknown_status_predecessors':len(uk),'NO_first_cause_unknown_predecessors':len(nc),'unique_linked_predecessors':len(ids),'approx_leverage_score':round(len(uk)+0.12*len(nc),2),'next_gate':'AUTHENTICATE_ACTOR_ORIGINAL__CHECK_CLAUSE_SCOPE_AND_SAVINGS__NO_AUTOMATED_NO','legal_promotion':'DISALLOWED'})
q.sort(key=lambda x:(-x['approx_leverage_score'],x['candidate_ending_source']))
with (ROOT/'AUDIT/REBUILT_HIGH_LEVERAGE_ENDING_SOURCE_QUEUE.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,q[0].keys());w.writeheader();w.writerows(q)
impact={'stage14_original_edges':6692,'stage14_existing_nonquarantined_edge_count':6575,'stage14_reverse_edge_newly_quarantined':1,'stage15_valid_existing_candidate_edges':6574,'stage14_missed_NARA_successor_references':len(recovered),'recovered_candidate_edges_pass_chronology':len(usable),'recovered_reverse_date_quarantine':len(recovered)-len(usable),'stage15_usable_candidate_ending_or_amendment_edges':len(present),'recovered_leads_touch_unique_unknown_records':len(set(x['candidate_predecessor'] for x in usable if x['target_stage11_substantive']=='indeterminate')),'recovered_leads_touch_unique_NO_records':len(set(x['candidate_predecessor'] for x in usable if x['target_stage11_substantive']=='no')),'major_missing_clusters':collections.Counter(x['actor'] for x in usable).most_common(12),'new_high_leverage_queue_actor_count':len(q),'safe_for_mass_status_decision':False}
(ROOT/'AUDIT/RECOVERED_NARA_SUCCESSOR_AUDIT_METRICS.json').write_text(json.dumps(impact,indent=2)+'\n')
print(json.dumps(impact,indent=2))
