"""Combine numeric study receipts without reading conversation contents."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
KEYS=('input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens','uncached_input_tokens_derived')
def read(rel):return json.loads((HERE/rel).read_bytes())
def total(*rows):return {k:sum(r.get(k,0) for r in rows) for k in KEYS}
def calls(row):return sum(row.values())


def run():
    ap=read('matched/A/producer/correction-v1/INITIAL_RUNTIME_TELEMETRY.json')
    ac=read('matched/A/producer/correction-v1/CORRECTION_RUNTIME_TELEMETRY.json')
    ar=read('matched/A/review/REVIEW_METRICS.json')
    bp=read('matched/B/producer/correction-v1/TELEMETRY_ADDENDUM.json')
    br=read('matched/B/review/MEASUREMENT.json')
    bt=read('matched/B/review/TELEMETRY.json')
    phases={
      'A_producer':{'usage':ap['sum_observed_response_usage'],'calls':calls(ap['outer_tool_calls_by_name']),
                    'wall':ap['wall_seconds_first_response_through_submission_or_snapshot']},
      'A_reviewer':{'usage':ar['actual_own_rollout_usage'],'calls':calls(ar['outer_calls_through_usage_snapshot']),
                    'wall':ar['wall_elapsed_seconds_through_record']},
      'A_correction':{'usage':ac['sum_observed_response_usage'],'calls':calls(ac['outer_tool_calls_by_name']),
                    'wall':ac['wall_seconds_first_response_through_submission_or_snapshot']},
      'B_producer':{'usage':bp['initial_phase']['sum_observed_response_usage'],
                    'calls':calls(bp['initial_phase']['outer_tool_calls_by_name']),'wall':471.387},
      'B_reviewer':{'usage':bt['sum_observed_response_usage'],'calls':calls(br['observed_outer_calls']),
                    'wall':br['task_wall_seconds']},
      'B_correction':{'usage':bp['correction_phase']['sum_observed_response_usage'],
                    'calls':calls(bp['correction_phase']['outer_tool_calls_by_name']),'wall':bp['correction_wall_seconds']}}
    def arm(name,correction):
        rows=[phases[name+'_producer'],phases[name+'_reviewer']]
        if correction:rows.append(phases[name+'_correction'])
        return {'usage':total(*(r['usage'] for r in rows)),'outer_calls':sum(r['calls'] for r in rows),
            'sum_sequential_task_wall_seconds':round(sum(r['wall'] for r in rows),3),
            'members':6,'exact_proposals_upheld':1,'blocked_after_correction':5,
            'canonical_publications':0,'human_certifications':0}
    root=read('ROOT_RUNTIME_TELEMETRY.json');pre=read('preflight/TELEMETRY.json')
    packet=read('packet-review/TELEMETRY.json');overlay=read('overlay/TELEMETRY.json')
    runner=read('runner/RUNTIME_TELEMETRY.json')
    overhead={
      'coordinator_implementation_integration':root['observed_usage_since_phase_floor'],
      'fifty_preflight':{**pre['runtime_total_token_usage'],'uncached_input_tokens_derived':pre['uncached_input_tokens']},
      'independent_packet_completeness':{**packet['phase_runtime_token_delta'],'uncached_input_tokens_derived':packet['phase_uncached_input_tokens']},
      'overlay_engineering_and_tests':overlay['sum_observed_response_usage'],
      'runner_engineering_source_review_and_tests':runner['sum_observed_response_usage']}
    paired={'initial_producer_plus_reviewer':{'A':arm('A',False),'B':arm('B',False)},
            'including_observed_correction':{'A':arm('A',True),'B':arm('B',True)}}
    for value in paired.values():
        a,b=value['A'],value['B']
        value['B_minus_A_percent']={
          'input_tokens':round(100*(b['usage']['input_tokens']/a['usage']['input_tokens']-1),2),
          'uncached_input_tokens':round(100*(b['usage']['uncached_input_tokens_derived']/a['usage']['uncached_input_tokens_derived']-1),2),
          'output_tokens':round(100*(b['usage']['output_tokens']/a['usage']['output_tokens']-1),2),
          'outer_calls':round(100*(b['outer_calls']/a['outer_calls']-1),2),
          'sum_task_wall':round(100*(b['sum_sequential_task_wall_seconds']/a['sum_sequential_task_wall_seconds']-1),2)}
    result={'schema':'eo-matched-excavator-cost-comparison/v1','phases':phases,'paired':paired,
      'engineering_preflight_and_verification_usage_lower_bound':total(*overhead.values()),
      'overhead_components':overhead,
      'all_observed_task_usage_lower_bound':total(*overhead.values(),*(p['usage'] for p in phases.values())),
      'cost_verdict':'Producer effort decreased; total reviewed-workflow savings NOT demonstrated. No measured amortization break-even.',
      'billed_dollars':None,'complete_active_labor_seconds':None,
      'limits':['Six cases, one run per arm, four historical accepted replicas/two difficult controls; not a randomized population estimate.',
        'Both arms received the same full frozen evidence and legal standard. Review discovery varied: B additionally searched2003 primary sources; A already blocked affected claims for a separate valid reason.',
        'Runtime input includes cached input; reasoning output is included in output. Neither is a billing invoice.',
        'Correction snapshots include metadata/telemetry work but exclude later final responses. Every phase retains its actual cutoff.',
        'Engineering totals are observed lower bounds; preflight and packet-audit windows do not overlap, but leave an unmeasured finalization gap.',
        'Elapsed task times include tools/retries. Parallel engineering times are not added as a wall-clock duration.',
        'Representation bytes, requested source bytes and serialized tool characters are distinct proxies; exact model exposure is unavailable.']}
    (HERE/'COST_COMPARISON.json').write_bytes((json.dumps(result,sort_keys=True,indent=2)+'\n').encode())
    print(json.dumps({'paired':paired,'engineering_usage_lower_bound':result['engineering_preflight_and_verification_usage_lower_bound'],
                      'all_observed_usage_lower_bound':result['all_observed_task_usage_lower_bound']},indent=2))

if __name__=='__main__':run()
