"""Export only usage counters/tool names from the caller's own rollout log.

Pass the exact CODEX_THREAD_ID-matching file; never scan other conversations.
No prompts, arguments, account data, rate limits or message contents are exported.
These are runtime counters, not an invoice or a measured baseline/pilot saving.
"""
import argparse
from collections import Counter
import datetime
import json
from pathlib import Path

KEYS=('input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens','total_tokens')

def capture(path,out,phase='2026-10-18T08:40:15Z'):
    rows=[json.loads(l) for l in path.read_text('utf-8').splitlines() if l.strip()]
    usage=[r for r in rows if r.get('type')=='token_usage_record']
    if not usage:raise ValueError('no per-response usage records')
    cutoff=usage[-1]['timestamp'];bounded=[r for r in rows if r.get('timestamp','')<=cutoff]
    def counters(items):
        totals={k:sum(r['payload']['usage'].get(k,0) for r in items) for k in KEYS}
        totals['uncached_input_tokens_derived']=totals['input_tokens']-totals['cached_input_tokens']
        return totals
    def calls(items):
        return dict(Counter(r['payload'].get('name','unknown') for r in items
          if r.get('type')=='response_item' and r.get('payload',{}).get('type') in ('function_call','custom_tool_call')))
    result={'schema':'eo-excavator-runtime-telemetry/v1','snapshot_cutoff_utc':cutoff,
        'coverage_start_utc':usage[0]['timestamp'],'phase_floor_start_utc':phase,
        'source':'Exact own-chat rollout JSONL selected using CODEX_THREAD_ID; no conversation contents exported.',
        'per_response_usage_records':len(usage),'sum_observed_response_usage':counters(usage),
        'last_runtime_thread_cumulative_counter':{k:usage[-1]['payload'].get('thread_token_usage',{}).get(k) for k in KEYS},
        'observed_usage_since_phase_floor':counters([r for r in usage if r['timestamp']>=phase]),
        'outer_tool_calls_by_name':calls(bounded),
        'outer_tool_calls_since_phase_floor':calls([r for r in bounded if r.get('timestamp','')>=phase]),
        'billed_dollars':None,'complete_active_labor_seconds':None,
        'limits':['Snapshot excludes subsequent responses and independent reviewer unless separately recorded.',
          'Input includes cached input; reasoning output is included in output and must not be added again.',
          'Outer tools count wrappers such as functions.exec; nested tool calls and retries are not fully counted.',
          'Do not sum last runtime cumulative counters with per-response sums. Counter aggregation may differ; both are exposed.',
          'These implementation/review costs do not measure savings versus equal-quality legal adjudication.']}
    out.write_bytes((json.dumps(result,sort_keys=True,indent=2)+'\n').encode())
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--log',type=Path,required=True)
    p.add_argument('--out',type=Path,default=Path(__file__).with_name('ROOT_RUNTIME_TELEMETRY.json'))
    a=p.parse_args();r=capture(a.log,a.out);print(json.dumps(r,sort_keys=True))
