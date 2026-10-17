#!/usr/bin/env python3
"""Stage14 planner: choose operations that unlock multiple subsequent legal reviews.
Uses source acquisition availability; ranks work TYPES, not direct EO conclusions.
Does not infer first cessation from formal revocation; that is a potential bound only.
"""
import csv,collections,json,pathlib,sqlite3,sys
base=pathlib.Path(sys.argv[1]);db=sqlite3.connect(base/'DATA/EO_SOURCE_DEPENDENCY_GRAPH.sqlite')
q=list(csv.DictReader(open(base/'QUEUES/REUSABLE_CONTROLLING_SOURCE_QUEUE.csv',encoding='utf8')))
fet={}
for r in csv.DictReader(open(base/'QUEUES/OFFICIAL_DIRECT_DOCUMENT_FETCH_MANIFEST.csv',encoding='utf8')):
 fet.setdefault(r['instrument_id'],[]).append(r)
flags=dict(db.execute("SELECT id,signing_date FROM orders"))
rows=[]
for r in q:
 k=r['actor'];n_unknown=int(r['distinct_unknown']);n_causal=int(r['status_NO_missing_first_cause']);cached=list(db.execute('SELECT source_grade,checksum_verdict,source_url FROM cache_representations WHERE subject_id_hint=?',(k,)))
 likely=sum(x[0]=='POSSIBLE_ORDER_TEXT_CACHED_UNAUTHENTICATED' for x in cached)
 strong=sum(x[0]=='POSSIBLE_ORDER_TEXT_CACHED_UNAUTHENTICATED' and x[1]=='MATCHES_DECLARED_TEXT_SHA256' for x in cached)
 direct=fet.get(k,[])
 risk=r['risk_flags']; p=float(r['priority_score'])
 if likely:
  action='AUTHENTICATE_REUSE_EXISTING_CACHED_TEXT_AND_TEST_SCOPE'
  source_class='CACHED_SOURCE_HINT'
 elif direct:
  action='FETCH_ORIGINAL_FROM_KNOWN_OFFICIAL_DIRECT_URL_ONCE'
  source_class='OFFICIAL_DIRECT_METADATA_URL_NOT_FETCHED'
 else:
  action='RESOLVE_PRIMARY_DOCUMENT_LOCATION_AND_CACHE_ONCE'
  source_class='PRIMARY_DOCUMENT_NOT_LOCATED_IN_RECOVERED_CACHE'
 if risk:
  action='EXCEPTION_OR_DISAGREEMENT_GATE_FIRST__'+action
 # Avoid overpromising: candidate potential refs; causal refs not a first-cause count.
 note='Causal refs only latest-known bounds; check earlier original terms/events' if n_causal else ''
 rows.append(dict(actor=k,priority_score=p,unknown_status_research_dependents=n_unknown,known_NO_first_cause_unknown_bound_leads=n_causal,cached_source_representations=len(cached),plausible_cached_actor_originals=likely,cached_actor_text_checksum_attested=strong,official_direct_document_url_count=len(direct),source_availability=source_class,next_enabling_action=action,known_scope_risk=risk,astropus_assigned=r['assigned'],notes=note))
rows.sort(key=lambda x:(-x['priority_score'], -x['unknown_status_research_dependents']))
with open(base/'QUEUES/EXECUTION_ACTIONS_DEPENDENCY_FIRST.csv','w',newline='',encoding='utf8') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
# Hand off top actor tasks across owners, preserving exceptional legal scope.
for owner in ['ASTRA','OPUS']:
 subset=[r for r in rows if f'{owner}:' in r['astropus_assigned']]
 with open(base/f'QUEUES/{owner}_SHARED_SOURCE_FIRST.csv','w',newline='',encoding='utf8') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(subset)
summary={'actor_tasks':len(rows),'cached_actor_source_hints':sum(r['plausible_cached_actor_originals']>0 for r in rows),'official_direct_actor_urls_others':sum(not r['plausible_cached_actor_originals'] and r['official_direct_document_url_count']>0 for r in rows),'remaining_primary_actor_discovery':sum(not r['plausible_cached_actor_originals'] and not r['official_direct_document_url_count'] for r in rows),'exception_gated_actor_tasks':sum(bool(r['known_scope_risk']) for r in rows),'top_12':[{'actor':r['actor'],'unknown':r['unknown_status_research_dependents'],'no_cause_upper_bound_refs':r['known_NO_first_cause_unknown_bound_leads'],'next':r['next_enabling_action']} for r in rows[:12]],'warning':'All reach counts are research leads and can overlap. Formal revocation does not establish first cessation. Cannot classify without originals/whole footprint/savings/revivals.'}
(base/'REPORTS/DEPENDENCY_PLANNER_RESULTS.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='top_12'},indent=2))
