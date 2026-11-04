#!/usr/bin/env python3
"""Reusable exact-input mechanical baseline for o25 prerequisite routing."""
import json
import time
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

start = time.monotonic()
started_utc = datetime.now(timezone.utc).isoformat()
root = Path(__file__).resolve().parents[1]
preferred = root / 'inputs/o25-preflight-only.json'
fallback = root / 'inputs/o25-prerequisites.json'
source = preferred if preferred.is_file() else fallback
if not source.is_file():
    raise SystemExit('No authorized o25 preflight input found')
data = json.loads(source.read_text(encoding='utf-8'))
preflight = data['preflight']
output_members = []
groups = OrderedDict()
for iid, payload in preflight.items():
    matching = [task for task in payload.get('mechanical_tasks', [])
                if task.get('kind') == 'operative_current_law']
    output_members.append({
        'instrument_id': iid,
        'route': 'route_source_preparation' if matching else 'no_known_declared_prerequisite',
        'member_tasks': matching,
    })
    for task in matching:
        key = task.get('shared_key')
        group_key = (iid, task.get('kind'), key) if key == '{}' else (task.get('kind'), key)
        if group_key not in groups:
            groups[group_key] = {
                'kind': task.get('kind'),
                'shared_key': key,
                'grouped_by_shared_key': key != '{}',
                'affected_orders': [],
                'member_tasks': [],
            }
        group = groups[group_key]
        if iid not in group['affected_orders']:
            group['affected_orders'].append(iid)
        group['member_tasks'].append(task)
result = {
    'schema': 'arm-a-baseline-routing/v1',
    'input': str(source.relative_to(root)),
    'model': 'gpt-6-luna',
    'utc_started': started_utc,
    'members': output_members,
    'groups': list(groups.values()),
    'scope_note': 'Mechanical assignment-prerequisite routing only. This is not a source-feasibility or legal-readiness finding, does not approve dispatch, and is not completed dossier work. Groups are advisory task-key groups and establish neither shared source nor shared legal question.',
}
result['elapsed_seconds_monotonic'] = round(time.monotonic() - start, 6)
result['accounting'] = {
    'configured_model': 'gpt-6-luna',
    'provider_tokens': None,
    'cash_usage': None,
    'tool_interactions_total': 4,
    'shell_command_invocations_total': 4,
    'monotonic_elapsed_scope': 'Final reusable-script execution only; earlier bounded input inspection time was not instrumented.',
    'one_time_setup_and_inspection_cost': 'unmeasured',
    'repeat_execution_model_contexts': 0,
    'repeat_execution_note': 'Equivalent assignments can run this script without another model task.',
}
result['utc_completed'] = datetime.now(timezone.utc).isoformat()
out = Path(__file__).resolve().parent / 'result-v2.json'
out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'output': str(out), 'members': len(output_members), 'routes': {
    route: sum(m['route'] == route for m in output_members)
    for route in ('route_source_preparation', 'no_known_declared_prerequisite')},
    'matching_tasks': sum(len(m['member_tasks']) for m in output_members),
    'groups': len(groups),
    'elapsed_seconds_monotonic': result['elapsed_seconds_monotonic']}, indent=2))
