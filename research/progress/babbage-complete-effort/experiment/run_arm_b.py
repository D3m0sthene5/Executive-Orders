#!/usr/bin/env python3
"""Exact ordinary-dispatch classification slice; no native dispatch approval."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'jobs/claim-kit'))
import dispatch

def run(source, destination):
    started = time.monotonic()
    source = Path(source)
    raw = source.read_bytes()
    data = json.loads(raw)
    preflight = data['preflight']
    ids = list(preflight)
    blockers, requirements = dispatch._assignment_prerequisites(
        preflight, ids, require_task_kinds=['operative_current_law'])
    result = {
        'endpoint': 'known_assignment_prerequisite_routing_only',
        'input_sha256': hashlib.sha256(raw).hexdigest(),
        'members': [{'instrument_id': iid,
                     'route': 'route_source_preparation' if blockers[iid] else 'no_known_declared_prerequisite',
                     'tasks': [b['task'] for b in blockers[iid]]} for iid in ids],
        'groups': requirements['unresolved'],
        'notice': requirements['notice'],
        'native_dispatch_approved': False,
        'scientific_approval': False,
    }
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    metric = {'wall_seconds': time.monotonic()-started, 'model_tasks': 0,
              'model_calls': 0, 'provider_tokens': None, 'cash': None,
              'output_bytes': destination.stat().st_size,
              'dispatch_code_sha256': hashlib.sha256(Path(dispatch.__file__).read_bytes()).hexdigest(),
              'input_sha256': result['input_sha256'],
              'scope': 'Execution only; development, coordination and review recorded separately.'}
    destination.with_suffix('.cost.json').write_text(json.dumps(metric, indent=2)+'\n')
    print(json.dumps({'members': len(ids), 'routed': sum(bool(b) for b in blockers.values()),
                      'task_occurrences': sum(len(b) for b in blockers.values()),
                      'advisory_task_key_groups': len(result['groups']), **metric}))
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    run(args.source, args.destination)
