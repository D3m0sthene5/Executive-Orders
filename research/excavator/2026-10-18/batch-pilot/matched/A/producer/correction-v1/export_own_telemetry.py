"""Numeric exports from precisely this producer's rollout; no unrelated log reads.

Rerun after this correction turn finishes to include its final response. The
initial-producer export is bounded by its completed turn and remains invariant.
No prompt, response content, tool argument, account data or rate limit is exported.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[7]
THREAD = '01a14f2d-148a-7391-973a-39f2f83f3bbc'
INITIAL_TURN = '01a14f2d-1521-71c0-9964-1908fb6edaca'
CORRECTION_TURN = '01a14f40-a265-7f80-b55f-88e3211fc6de'
KEYS = ('input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens','total_tokens')


def dump(name,value):
    (HERE/name).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n',encoding='utf-8')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    root = Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex')))
    # Filename matching only; no other log contents are opened.
    candidates = list((root/'sessions').rglob('*'+THREAD+'*.jsonl'))
    if len(candidates)!=1:raise ValueError('Exact own-thread log is not unique')
    path = candidates[0]
    rows = [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
    usage = [r for r in rows if r.get('type')=='token_usage_record']
    if not usage or any(r['payload'].get('thread_id')!=THREAD for r in usage):
        raise ValueError('Usage thread identity does not match this producer')
    restored = REPO/'research/excavator/2026-10-18/status-history-pilot/capture_telemetry.py'
    spec = importlib.util.spec_from_file_location('restored_capture_telemetry',restored)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.capture(path,HERE/'RUNTIME_SNAPSHOT.json',phase='2026-10-18T13:43:18.390Z')

    def counters(items):
        result = {k:sum(r['payload']['usage'].get(k,0) for r in items) for k in KEYS}
        result['uncached_input_tokens_derived'] = result['input_tokens']-result['cached_input_tokens']
        return result

    def phase(turn):
        events = [r for r in rows if r.get('type')=='event_msg' and r.get('payload',{}).get('turn_id')==turn]
        start = next(r['timestamp'] for r in events if r['payload'].get('type')=='task_started')
        complete = next((r['timestamp'] for r in events if r['payload'].get('type')=='task_complete'),None)
        uses = [r for r in usage if r['payload'].get('turn_id')==turn]
        end = complete or uses[-1]['timestamp']
        bounded = [r for r in rows if start<=r.get('timestamp','')<=end]
        responses = [r for r in bounded if r.get('type')=='response_item' and r.get('payload',{}).get('type') in ('reasoning','message','function_call','custom_tool_call')]
        first_response = responses[0]['timestamp']
        call_counts = dict(Counter(r['payload'].get('name','unknown') for r in bounded if r.get('type')=='response_item' and r.get('payload',{}).get('type') in ('function_call','custom_tool_call')))
        last = uses[-1]['payload']
        elapsed = (datetime.fromisoformat(end.replace('Z','+00:00'))-datetime.fromisoformat(first_response.replace('Z','+00:00'))).total_seconds()
        return {'schema':'matched-own-rollout-phase-telemetry/v1','thread_id':THREAD,'turn_id':turn,'task_start_utc':start,'first_response_record_utc':first_response,'last_usage_record_utc':uses[-1]['timestamp'],'submission_or_snapshot_end_utc':end,'phase_complete':complete is not None,'wall_seconds_first_response_through_submission_or_snapshot':elapsed,'per_response_usage_records':len(uses),'sum_observed_response_usage':counters(uses),'last_runtime_turn_cumulative_counter':{k:last.get('turn_token_usage',{}).get(k) for k in KEYS},'last_runtime_thread_cumulative_counter_for_reference_only':{k:last.get('thread_token_usage',{}).get(k) for k in KEYS},'outer_tool_calls_by_name':call_counts,'outer_tool_calls_total':sum(call_counts.values()),'source_log_filename':path.name,'source':'Restored capture_telemetry.py run on the exact CODEX_THREAD_ID-matching log; phase counters separately partitioned by immutable turn_id. No unrelated conversation log read.','limits':['Initial producer turn is complete and excludes correction input, tool calls and usage.','Correction phase is a snapshot until its task_complete event exists; rerun this script after completion for final correction costs.','Runtime usage counters are not an invoice. Input includes cached input; reasoning is already included in output and is not added twice.','Outer tool counts include wrappers and collaboration calls, not all nested calls.','Per-response usage sums are the phase metric; do not add runtime cumulative counters to them.','No active-labor timing, dollar cost or matched-arm saving is inferred.']}

    initial = phase(INITIAL_TURN)
    correction = phase(CORRECTION_TURN)
    dump('INITIAL_RUNTIME_TELEMETRY.json',initial)
    dump('CORRECTION_RUNTIME_TELEMETRY.json',correction)
    dump('MODEL_USAGE_ADDENDUM.json',{'schema':'matched-producer-telemetry-availability-addendum/v1','original_file_preserved':'../TELEMETRY.json','correction':'The initial TELEMETRY.json recorded token usage unavailable. Actual per-response input/cache/output/reasoning counters are available in the exact own-thread rollout and are now exported. The original unavailable statement is superseded by these numeric exports, while its wall/exposure measurements remain preserved.','initial_phase_export':'INITIAL_RUNTIME_TELEMETRY.json','correction_phase_export':'CORRECTION_RUNTIME_TELEMETRY.json','restored_capture_script':str(restored.relative_to(REPO)),'restored_capture_script_sha256':hashlib.sha256(restored.read_bytes()).hexdigest(),'no_unrelated_logs_read':True,'no_contents_exported':True})
    metrics = json.loads((HERE/'CORRECTION_METRICS.json').read_text(encoding='utf-8'))
    metrics.update(outer_tool_calls_at_runtime_snapshot=correction['outer_tool_calls_by_name'],runtime_snapshot_cutoff_utc=correction['submission_or_snapshot_end_utc'],wall_seconds_first_response_to_runtime_snapshot=correction['wall_seconds_first_response_through_submission_or_snapshot'],actual_usage_snapshot_file='CORRECTION_RUNTIME_TELEMETRY.json',claim_checker_invocations=2,claim_checker_initial_failure='Sandbox default TEMP denied fixture directory writes; preserved in claim-checker/INVOCATION.*',claim_checker_final_result={'claims_checked':1,'all_checks_passed':1,'mechanical_fail':0,'gate_passed':1,'exact_quotations':39,'source_references_gpo_published_hash_match':30,'unit_tests_passed':28,'output':'claim-checker/attempt-02'})
    dump('CORRECTION_METRICS.json',metrics)
    report = '''# Arm A correction v1

Only independently accepted EO12720 is retained as an exact proposed claim; its canonical SHA-256 is unchanged. All six frozen cases remain in the denominator: one retained proposal and five unable cases. Initial producer artifacts remain byte-for-byte preserved, including all failures and rejected claims, as verified in INITIAL_ARTIFACT_PRESERVATION.json.

EO12813 approval is withdrawn because December 31, 1992 is a not-later-than bound, not an affirmatively established exact first cessation. EO12734 and EO12817 approval is withdrawn because historical congressional-transmission/publication commands need distinct supported first ends; later 2004 revocation does not supply those dates. Their corrected inventories separate these commands and keep unknown exact dates blank. EO12696 and EO12722 remain unable on their independently upheld blockers.

The UNSCR1483 paragraphs 10, 16-17/23 and OFAC575.533 effective May23,2003 lead is an unresolved acquisition/legal-scope task for EO12817. Restoration of Resolution778 funds remains contemplated. The lead supplies no automatic 2003 whole ending and no inference that transfers, repayments or assets were exhausted.

All six corrected sheets were run through the existing assembler: one pass, five deliberate fail-closed results, zero unexpected assembly failures. EO12720 also passed the actual claim-checker: one claim, one gate/mechanical pass, 39 exact quotations and 30 GPO published-hash source matches. The first checker invocation failed in the sandbox default TEMP; that failure is preserved. Retry with TMP/TEMP/TMPDIR inside correction-v1 passed all 28 checker unit tests and the single-claim check. No fetch flag or network acquisition was used.

Precise shared research/acquisition tasks appear in ACQUISITION_TASKS.json. No canonical statuses/claims/census/reservations/HANDOFF files were written, and no human certification or publication is asserted.

The initial token-unavailability statement in the preserved ../TELEMETRY.json is corrected by MODEL_USAGE_ADDENDUM.json. INITIAL_RUNTIME_TELEMETRY.json contains complete actual initial-turn counters from first response through initial submission, excluding this correction. CORRECTION_RUNTIME_TELEMETRY.json contains separately partitioned correction counters through its recorded snapshot. RUNTIME_SNAPSHOT.json is the restored capture script's numeric-only exact own-rollout export. This script may be rerun after the correction final response to include that response and mark the correction phase complete. No unrelated logs or message contents were exported. Runtime counters do not establish dollars, active labor or savings.
'''
    (HERE/'REPORT.md').write_text(report,encoding='utf-8')
    print(json.dumps({'initial':{'usage':initial['sum_observed_response_usage'],'wrappers':initial['outer_tool_calls_by_name'],'wall_seconds':initial['wall_seconds_first_response_through_submission_or_snapshot'],'complete':initial['phase_complete']},'correction_snapshot':{'usage':correction['sum_observed_response_usage'],'wrappers':correction['outer_tool_calls_by_name'],'wall_seconds':correction['wall_seconds_first_response_through_submission_or_snapshot'],'complete':correction['phase_complete']}},indent=2))


if __name__=='__main__':
    main()
