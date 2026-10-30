#!/usr/bin/env python3
"""Reproduce readiness-tracker exhaustion behavior on its real tiny-repo fixture."""
from pathlib import Path
import json
import importlib.util
import subprocess
import sys
import tempfile

repo = Path(__file__).resolve().parents[4]
BASELINE = 'f9c6d806ad059dcad7875ab3708715f20ea386df'
sys.path.insert(0, str(repo / 'jobs/readiness-tracker'))
sys.path.insert(0, str(repo / 'jobs/claim-kit'))

# Load the frozen tracker blob explicitly: this probe must keep reproducing the
# baseline even if the working tree contains the coordinator's repair.
source = subprocess.run(['git', 'show', f'{BASELINE}:jobs/readiness-tracker/tracker.py'],
                        cwd=repo, check=True, capture_output=True).stdout
with tempfile.TemporaryDirectory(prefix='lifecycle-baseline-tracker-') as td:
    baseline_path = Path(td) / 'tracker.py'
    baseline_path.write_bytes(source)
    spec = importlib.util.spec_from_file_location('tracker', baseline_path)
    tracker = importlib.util.module_from_spec(spec)
    sys.modules['tracker'] = tracker
    spec.loader.exec_module(tracker)
from test_tracker import TrackerTest

import test_tracker
test_tracker.REAL_ROOT = repo

case = TrackerTest(methodName='runTest')
case.setUp()
try:
    empty_orders, empty_summary = case.run_tracker()
    iid = 'EO:4'
    records = [
        {'instrument_id': iid, 'step': step, 'searched': ['synthetic bounded probe'],
         'recorded_by': 'probe', 'recorded_on': '2026-10-30'}
        for step in tracker.STEP_NAMES
    ]
    exhausted_orders, exhausted_summary = case.run_tracker(exhausted=records)
    seven_orders, _ = case.run_tracker(exhausted=[r for r in records if r['step'] != 'provisional_status'])
    result = {
        'fixture': 'jobs/readiness-tracker/test_tracker.py::TrackerTest tiny repo',
        'baseline_no_claim_no_exhaustion': {
            'provisional_status': empty_orders[iid]['provisional_status'],
            'claim_present': empty_orders[iid]['claim_present'],
            'ready': empty_orders[iid]['ready_for_human_review'],
            'tier': empty_orders[iid]['ready_tier'],
            'blockers': empty_orders[iid]['blockers'],
        },
        'all_steps_except_provisional_status_exhausted_no_claim': {
            'ready': seven_orders[iid]['ready_for_human_review'],
            'tier': seven_orders[iid]['ready_tier'],
            'provisional_status_step': seven_orders[iid]['step_provisional_status'],
            'blockers': seven_orders[iid]['blockers'],
        },
        'all_STEP_NAMES_marked_exhausted_no_claim': {
            'exhaustion_steps': records and [r['step'] for r in records],
            'provisional_status': exhausted_orders[iid]['provisional_status'],
            'claim_present': exhausted_orders[iid]['claim_present'],
            'ready': exhausted_orders[iid]['ready_for_human_review'],
            'tier': exhausted_orders[iid]['ready_tier'],
            'exhausted_steps': exhausted_orders[iid]['exhausted_steps'],
            'blockers': exhausted_orders[iid]['blockers'],
            'summary_ready': exhausted_summary['ready_for_human_review'],
        },
        'step_names': tracker.STEP_NAMES,
        'canonical_outputs_modified': False,
    }
    print(json.dumps(result, indent=2))
finally:
    case.tearDown()
