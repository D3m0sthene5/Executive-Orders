#!/usr/bin/env python3
"""Reproduce whether an unrelated-scope control review receives completion credit."""
from pathlib import Path
import json
import sys

repo = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repo / 'jobs/claim-kit'))
sys.path.insert(0, str(repo / 'jobs/readiness-tracker'))
import batch
from test_completion import CompletionTests

case = CompletionTests(methodName='runTest')
case.setUp()
try:
    case.setup_completion()
    case.add_control(iid='EO:1')
    control = case.manifest['controls'][0]
    review_path = case.repo / control['review']['path']
    review = json.loads(review_path.read_bytes())
    review['scope'] = 'status_only_unrelated_scope'
    batch.dump(review_path, review)
    control['review'] = case.ref(review_path)
    adjudication_path = case.repo / control['adjudication']['path']
    adjudication = json.loads(adjudication_path.read_bytes())
    adjudication['review'] = control['review']
    batch.dump(adjudication_path, adjudication)
    control['adjudication'] = case.ref(adjudication_path)
    result = case.run_completion(publish=False)
    print(json.dumps({
        'fixture': 'jobs/claim-kit/test_completion.py::CompletionTests tiny repo',
        'selected_member_scope': case.manifest['members'][0]['publication_kind'],
        'control_review_scope': review['scope'],
        'control_review_verdict': review['verdict'],
        'plants_caught': result['plants_caught'],
        'eligible': result['eligible'],
        'control_outcome': result['controls'][0],
        'canonical_outputs_modified': False,
    }, indent=2))
finally:
    case.tearDown()
