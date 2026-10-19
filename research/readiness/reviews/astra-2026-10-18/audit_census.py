"""Read-only census review diagnostics; writes only beside this new review script."""
import collections
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('census_reviewed', ROOT / 'jobs/census-completeness/complete.py')
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)

def rows(name):
    with (ROOT / 'jobs/census-completeness/output' / name).open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))

mentions = rows('MENTIONS.csv')
by_id = {r['mention_id']: r for r in mentions}
cluster_rows = rows('CLUSTERS.csv')
checks = []
for cluster in cluster_rows:
    ms = [by_id[x] for x in cluster['members'].split('|')]
    repeated = {k:v for k,v in collections.Counter(m['source'] for m in ms).items() if v > 1}
    dates = sorted({m['date'] for m in ms if m['precision'] == 'day'})
    if repeated or len(dates) > 1:
        checks.append({'cluster_id':cluster['cluster_id'], 'members':cluster['members'],
                       'repeated_source_members':repeated, 'distinct_day_dates':dates})
matches = rows('MATCHES.csv')
month_cross = [m for m in matches if m['kind'] == 'blind_year_and_two_tokens'
               and by_id[m['a']]['precision'] == 'month'
               and by_id[m['a']]['date'][:7] != by_id[m['b']]['date'][:7]]
est = json.loads((ROOT / 'jobs/census-completeness/output/ESTIMATES.json').read_text())
numbers = {scenario:{era:{k:v[k] for k in ['clusters_observed','numbered_orders_excluded','mt_all_lists','chao1_all_lists']}
                    for era,v in eras.items()} for scenario,eras in est.items() if isinstance(eras,dict)}
synthetic = [C.mention('LORD','LORD:U:9999','1830-01','month','Pensacola barracks construction','fixture',seq=9999),
             C.mention('MR_A','A','1830-02-01','day','Pensacola barracks construction','fixture'),
             C.mention('MR_A','B','1830-03-01','day','Pensacola barracks construction','fixture')]
mt, _ = C.match_mentions(synthetic)
cs = C.clusters(synthetic,mt,{m['kind'] for m in mt})
files = ['complete.py','output/ESTIMATES.json','output/REPORT.md','output/MENTIONS.csv','output/MATCHES.csv','output/CLUSTERS.csv']
result = {
  'reviewer_role':'ai_review',
  'inputs':{f:hashlib.sha256((ROOT/'jobs/census-completeness'/f).read_bytes()).hexdigest() for f in files},
  'descriptive':{'mentions':len(mentions),'clusters_including_numbered':len(cluster_rows),
                 'clusters_with_repeated_source':sum(bool(x['repeated_source_members']) for x in checks),
                 'clusters_with_multiple_day_dates':sum(len(x['distinct_day_dates'])>1 for x in checks),
                 'month_precision_lord_cross_month_edges':len(month_cross)},
  'numbers':numbers,
  'counterexamples':{
      'month_precision_bridge':{'matches':mt,'clusters':cs},
      'finite_mt_root_outside_fixed_bracket':{'list_sizes':[1000,1000], 's_obs':1999, 'actual_return':C.mt_mle([1000,1000],1999), 'two_list_root':1000000},
      'chapman_lower_interval_below_observed_union':{'inputs':[100,100,90], 'observed_union':110, 'actual_return':C.chapman(100,100,90)},
      'boundary_nested_lists':{'inputs':[[7,1,1,1],7],'actual_return':C.mt_mle([7,1,1,1],7),'interpretation':'Null is not evidence of no undiscovered orders.'}},
  'cluster_flags':checks,
  'month_cross_edges':month_cross,
}
(OUT/'CENSUS_DIAGNOSTICS.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ['numbers','cluster_flags','month_cross_edges']},indent=2))
