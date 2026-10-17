#!/usr/bin/env python3
import csv,json,os,hashlib,sqlite3,sys,unittest,collections
from pathlib import Path
root=Path(sys.argv[1] if len(sys.argv)>1 else '/mnt/data/EO_STAGE15_METHOD_FOUNDATION_2026-10-16')
def getcsv(p):return list(csv.DictReader((root/p).open(encoding='utf-8')))
def getj(p):return json.load((root/p).open(encoding='utf-8'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for ch in iter(lambda:f.read(2097152),b''):h.update(ch)
 return h.hexdigest()
source=Path(os.environ.get('EO_STAGE11_LEDGER','/mnt/data/eo_stage15_workspace/STAGE11/RECONCILED_STATUS_LEDGER_STAGE11_PROVISIONAL.jsonl'))
old_graph=Path(os.environ.get('EO_STAGE14_GRAPH','/mnt/data/eo_stage15_workspace/EO_STAGE14_LEVERAGE_ENGINE_2026-10-16/DATA/EO_SOURCE_DEPENDENCY_GRAPH.sqlite'))
checks=[]
def expect(flag,message):
 checks.append({'check':message,'pass':bool(flag)});
 if not flag:print('FAILED',message)
issues=getcsv('AUDIT/COMPLETE_ISSUE_CLOSURE_MATRIX.csv');expected_n=36
expect(len(issues)==expected_n,'36 issue-specific acceptance tests enumerated and explicitly classified')
expect(len(set(i['issue_id'] for i in issues))==expected_n,'issue IDs unique')
expect(sum(1 for x in issues if x['issue_id'].startswith('7.'))==8,'seven source-root mechanisms + correlation gate mapped')
expect(all((root/i['evidence_artifact']).exists() for i in issues if not i['evidence_artifact'].startswith('../')),'every referenced locally produced issue evidence artifact present')
a=getj('CENSUS/POPULATION_ESTIMANDS.json');expect([x['value'] for x in a['estimands']]==[14973,14972,None,None],'historical census cannot be mislabeled complete')
au=getcsv('CENSUS/3016_C_K_N_AUTHORSHIP_AUDIT.csv');expect(len(au)==3 and [x['id'] for x in au]==['EO:3016C','EO:3016K','EO:3016N'],'three Polk family identities separate')
expect(au[2]['signer_attribution']=='UNKNOWN_UNTIL_ACTUAL_INSTRUMENT','3016N signature not inferred from unrelated case')
fr=getj('CENSUS/PUBLISHED_FR_ONLY_SOURCE_FRAME.json');expect(fr['raw_FR_bulk_source_rows']==6938 and fr['working_unique_document_proxies_matched']==6937,'FR publication proxy caveat respected')
progress=getj('CAUSAL/INDEPENDENT_PROGRESS_METRICS.json');expect((progress['working_unique_proxy_n'],progress['whole_order_status_determinate'],progress['NO_mechanism_field_populated'],progress['NO_first_date_field_populated'],progress['NO_first_date_exact_format_candidates_only'],progress['determinate_order_no_recorded_episodes_count'])==(14972,2515,106,99,68,1868),'no inflated historical causation progress')
sample=getcsv('STATISTICS/STRATIFIED_POPULATION_SAMPLE_120_BLIND.csv');key=getcsv('STATISTICS/SEALED_POPULATION_SAMPLE_BASELINE_120.csv')
expect(len(sample)==len(set(x['id'] for x in sample))==120,'120 distinct population probability sample cases')
expect(len(key)==120 and {x['id'] for x in sample}=={x['id'] for x in key},'sealed answer key covers sample')
expect(not any(x in sample[0] for x in ('stage11_status','substantive_effect','any_operative_EO_effect','headline_category')),'no baseline answer leakage into blind sample')
expect(all(abs(float(x['stratum_N'])/float(x['stratum_sample_n'])-float(x['design_weight']))<0.00001 for x in sample),'sampling weight matches stratum N/n')
expect(sum(len([x for x in sample if x['era']==s['era'] and x['source_class']==s['source_class']]) for s in getcsv('STATISTICS/SAMPLING_STRATA_WEIGHTS.csv'))==120,'stratum allocation reconciles')
edge=getj('AUDIT/RECOVERED_NARA_SUCCESSOR_AUDIT_METRICS.json');expect((edge['stage14_missed_NARA_successor_references'],edge['recovered_candidate_edges_pass_chronology'],edge['stage15_usable_candidate_ending_or_amendment_edges'])==(513,512,7086),'previously omitted official editorial links restored as candidates')
rev=getcsv('AUDIT/RELATIONSHIP_CHRONOLOGY_VIOLATIONS.csv');expect(len([x for x in rev if x['upstream_quarantined']=='0'])==1,'escaped backward amendment quarantined')
recovered=getcsv('AUDIT/RECOVERED_MISSING_NARA_SUCCESSOR_CANDIDATES.csv');expect(len(recovered)==513 and len([x for x in recovered if x['acceptance_class']=='QUARANTINE_REVERSE_CHRONOLOGY'])==1,'recovered NARA leads pass temporal gating except one')
feed=getcsv('AUDIT/CHRONOLOGY_AND_COMPLETENESS_GATED_RELATION_FEED.csv');expect(len(feed)==7086,'gated relationship feed complete')
expect(all(x['legal_promotion']=='DISALLOWED' for x in getcsv('AUDIT/REBUILT_HIGH_LEVERAGE_ENDING_SOURCE_QUEUE.csv')),'no legal finding auto-promoted from candidate edges')
expect(all(x['causal_promotion_allowed']=='NO' for x in recovered),'recovered links do not auto-promote first causes')
risk=getcsv('LEGAL/SEVEN_SHARED_FAILURE_MODES.csv');expect(len(risk)==7 and all(x['status_override_allowed']=='NEVER' for x in risk),'seven shared-error screens, no override of baseline legal status')
db=sqlite3.connect(root/'AUDIT/EO_STAGE15_SCHEMA_AND_RISK_SIDECAR.sqlite')
expect(db.execute('select count(*) from base_identity').fetchone()[0]==14972,'sidecar preserves unique bibliography')
expect(db.execute('select count(*) from research_requirements').fetchone()[0]==36,'sidecar tracks audit requirements')
expect(db.execute('select count(*) from operative_episode').fetchone()[0]==6,'six clearly preliminary clause examples, not supposed full reconstruction')
expect(db.execute('select count(*) from directed_event_guard where stage15_suppress=1').fetchone()[0]==118,'original 117 + new 1 invalid edge suppressed')
expect(db.execute("select count(*) from authorship_special where original_signature_state='NOT_YET_AUTHENTICATED'").fetchone()[0]==3,'physical authorship remains unverified')
if source.is_file():expect(sha(source)=='c0308e008cd719cd153ca667271c93267d5d855bf3eb26d48076e41938fc7729','Stage 11 ledger has exact original SHA256')
if old_graph.is_file():expect(sha(old_graph)=='41310b46f97712b28fcb7fd00e5ab5d38770c225fa57f5c10e5c9836738af55b','Stage14 source graph has exact original SHA256')
res={'result':'PASS' if all(c['pass'] for c in checks) else 'FAIL','checks_n':len(checks),'checks':checks,'limit':'Machine QA does not independently adjudicate the 2515 legal statuses, historical completeness, or causal truth.'}
(root/'REPORTS/STAGE15_VERIFICATION.json').write_text(json.dumps(res,indent=2)+'\n')
print(res['result'],res['checks_n'],'checks')
if res['result']!='PASS':sys.exit(1)
