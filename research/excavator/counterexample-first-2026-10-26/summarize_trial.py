"""Summarise the fixed trial's actual producer clocks; no savings forecast."""
from pathlib import Path
import json
from collections import defaultdict
RUN=Path(__file__).resolve().parent
members=json.loads((RUN/'DESIGN.json').read_bytes())['members']
rows=[];totals=defaultdict(float)
for m in members:
    end=json.loads((RUN/'packet/producers'/m['instrument_id'].replace(':','_')/'CLOCK_END.json').read_bytes())
    sec=end['elapsed_seconds']; totals[m['arm']]+=sec
    rows.append({**m,'initial_producer_worker_seconds':sec,'whole_case_upheld':m['instrument_id']!='EO:8915','source_review_correction_required':m['instrument_id']=='EO:8123'})
paired={a:sum(x['initial_producer_worker_seconds'] for x in rows if x['pair'] in (1,2) and x['arm']==a) for a in totals}
correction=json.loads((RUN/'packet/producers/EO_8123/CORRECTION_CLOCK_END.json').read_bytes())['elapsed_seconds']
result={'schema':'eo-counterexample-first-results/v1','members':rows,'initial_producer_seconds_by_arm':dict(totals),'fully_upheld_pairs':[1,2],'fully_upheld_pairs_initial_producer_seconds':paired,'fully_upheld_pairs_initial_difference_seconds':paired['ordinary']-paired['counterexample_first'],'fully_upheld_pairs_initial_difference_fraction':1-paired['counterexample_first']/paired['ordinary'],'treatment_substantive_producer_correction_seconds':correction,'all_three_pairs_both_histories_upheld':False,'prespecified_success_rule_met':False,'total_recurring_agent_hour_reduction':None,'total_token_reduction':None,'campaign_savings':None,'decision':'Do not deploy this sequencing instruction as a demonstrated accelerator or expand an associated tool. Retain useful research and optional technique.','limits':['Initial producer times are observed worker occupancy, not active labor or tokens.','Pair3 has a condition/occurrence difference and only one complete history, so its cheaper blocked attempt is not completion savings.','Two complete pairs differed by about18seconds before review, correction, sources and integration; this is not an end-to-end causal estimate.','Ordinary workers also examined contrary evidence before final drafting; explicit early-test records did not demonstrate a distinct removed operation.','Shared review/control/source and root effort cannot be reliably assigned to individual arms. Full total cost and causal savings remain unknown.','Small source-supported decided convenience sample, same model family, actual inventory mismatches, partial timing coverage, no population estimate.']}
(RUN/'TRIAL_RESULTS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'initial_seconds':dict(totals),'closed_pair_difference_seconds':result['fully_upheld_pairs_initial_difference_seconds'],'correction_seconds':correction,'target_met':False}))
