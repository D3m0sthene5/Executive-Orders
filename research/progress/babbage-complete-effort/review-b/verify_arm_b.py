#!/usr/bin/env python3
"""Independent contract reconstruction plus bounded adversarial native probes."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time
import types

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
EXP = HERE.parent / 'experiment'
sys.path.insert(0, str(ROOT / 'jobs/claim-kit'))
import dispatch
import batch
import test_dispatch

started = time.monotonic()
raw = (EXP/'inputs/o25-preflight-only.json').read_bytes()
source = json.loads(raw)
actual = json.loads((EXP/'arm-b/o25-result.json').read_bytes())
snapshot = source['source']
object_name = snapshot['ref'] + ':' + snapshot['path']
assert subprocess.check_output(['git','rev-parse',object_name],cwd=ROOT,text=True).strip() == snapshot['git_blob']
retained_packet = json.loads(subprocess.check_output(['git','show',object_name],cwd=ROOT))
assert retained_packet['preflight'] == source['preflight']
assert retained_packet['fingerprint'] == source['packet_fingerprint']
members, groups = [], []
# Do not call the production classifier to derive the expected result.
for iid, item in source['preflight'].items():
    tasks = [t for t in item['mechanical_tasks'] if t.get('kind') == 'operative_current_law']
    members.append({'instrument_id': iid,
                    'route': 'route_source_preparation' if tasks else 'no_known_declared_prerequisite',
                    'tasks': tasks})
    for task in tasks:
        group = next((g for g in groups if g['kind'] == task['kind'] and
                      g['shared_key'] == task['shared_key'] and
                      (task['shared_key'] != '{}' or g['affected_orders'] == [iid])), None)
        if group is None:
            group = {'kind': task['kind'], 'shared_key': task['shared_key'],
                     'grouped_by_shared_key': task['shared_key'] != '{}',
                     'affected_orders': [], 'member_tasks': []}
            groups.append(group)
        if iid not in group['affected_orders']:
            group['affected_orders'].append(iid)
        group['member_tasks'].append(task)
assert actual['members'] == members
assert actual['groups'] == groups
assert actual['input_sha256'] == hashlib.sha256(raw).hexdigest()
assert actual['endpoint'] == 'known_assignment_prerequisite_routing_only'
assert actual['scientific_approval'] is actual['native_dispatch_approved'] is False
assert len(members) == 30 and sum(len(m['tasks']) for m in members) == 355
assert len(groups) == 231
assert all(len(g['affected_orders']) == 1 for g in groups if g['shared_key'] == '{}')
checks = []
def refused(label, fn):
    try:
        fn()
    except ValueError as exc:
        checks.append({'probe': label, 'result': 'refused', 'reason': str(exc)})
    else:
        raise AssertionError(label + ' unexpectedly accepted')

task = {'kind': 'operative_current_law', 'shared_key': '{}', 'instrument_id': 'EO:1', 'reason': 'missing'}
pf = {'EO:1': {'mechanical_tasks': [task, task]}, 'EO:2': {'mechanical_tasks': [{**task, 'instrument_id': 'EO:2'}]}, 'EO:3': {'mechanical_tasks': []}}
helper = dispatch._assignment_prerequisites
for bad in (['unknown'], ['operative_current_law']*2, 'operative_current_law', {}, [None], 0):
    refused('bad scope '+repr(bad), lambda bad=bad: helper(pf, list(pf), bad))
for ids in ([], ['EO:1','EO:1'], ['EO:999'], ['EO:1',None]):
    refused('bad subset '+repr(ids), lambda ids=ids: helper(pf, ids, ['operative_current_law']))
for key in ('shared_key', 'reason', 'instrument_id'):
    damaged = copy.deepcopy(pf)
    damaged['EO:1']['mechanical_tasks'][0].pop(key)
    refused('missing '+key, lambda damaged=damaged: helper(damaged,list(damaged),['operative_current_law']))
damaged = copy.deepcopy(pf); damaged['EO:1']['mechanical_tasks'] = None
refused('missing task list', lambda: helper(damaged,list(damaged),['operative_current_law']))
blockers, p = helper(pf, list(pf), ['operative_current_law'])
assert len(blockers['EO:1']) == 2 and len(p['unresolved']) == 2
assert p['unresolved'][0]['member_tasks'] == [task, task]
assert p['unresolved'][0]['affected_orders'] == ['EO:1']
assert helper(pf,['EO:3'],['operative_current_law'])[1]['unresolved'] == []
assert all(not b for b in helper(pf,list(pf))[0].values())
checks.append({'probe': 'literal empty key / duplicates / subset / default', 'result': 'passed'})

# Native fixture and actual CLI; previous implementation is executed in memory.
fixture = test_dispatch.DispatchTests(methodName='test_explicit_current_predicate_scope_blocks_known_tasks_only')
fixture.setUp()
try:
    fixture.current_gaps(ids=('EO:1',))
    folder = fixture.packet()
    old_source = subprocess.check_output(['git','show','HEAD:jobs/claim-kit/dispatch.py'],cwd=ROOT,text=True)
    old = types.ModuleType('review_b_previous_dispatch')
    old.__file__ = dispatch.__file__
    exec(compile(old_source, '<HEAD dispatch>', 'exec'), old.__dict__)
    before = old.check(fixture.repo,folder)
    after = dispatch.check(fixture.repo,folder)
    before.pop('wall_seconds'); after.pop('wall_seconds')
    assert before == after, 'default behavior changed'
    checks.append({'probe': 'default full native report equals HEAD except wall_seconds', 'result': 'passed'})
    demos = []
    for extra, expected in (([],0), (['--require-task-kind','operative_current_law'],1),
                            (['--order','EO:2','--require-task-kind','operative_current_law'],0),
                            (['--order','EO:999','--require-task-kind','operative_current_law'],2),
                            (['--order','EO:2','--order','EO:2','--require-task-kind','operative_current_law'],2),
                            (['--require-task-kind','operative_current_law']*2,2)):
        code, output = fixture.cli('dispatch-check',folder,*extra)
        assert code == expected, (extra,code,output)
        demos.append({'arguments': extra, 'exit_code': code, 'stdout': json.loads(output) if output.strip() else None})
    (HERE/'cli-demonstrations.json').write_text(json.dumps(demos,indent=2)+'\n')
    checks.append({'probe': 'six native CLI demonstrations', 'result': 'passed'})
finally:
    fixture.doCleanups()

summary = {'members': len(members), 'routed': sum(m['route']=='route_source_preparation' for m in members),
           'task_occurrences': sum(len(m['tasks']) for m in members), 'groups': len(groups),
           'empty_key_member_groups': sum(g['shared_key']=='{}' for g in groups),
           'ambiguous_slice_task_occurrences': sum('No uniquely located' in t.get('reason','') for m in members for t in m['tasks']),
           'exact_snapshot_preflight_and_fingerprint_equal': True,
           'all_exact_member_and_group_payloads_equal': True,
           'probes': checks, 'wall_seconds': time.monotonic()-started}
(HERE/'independent-verification.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
