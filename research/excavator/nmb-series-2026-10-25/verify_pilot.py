"""Recheck the bounded pilot through existing native consumers; no network/build."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'jobs/source-ladder'))
import record_series

plan = json.loads((HERE/'SERIES_PLAN.v2.json').read_text())
result = record_series.propose(ROOT,plan)
assert {(r['instrument_id'],r['board']) for r in result['proposals']} == {
    ('EO:10029','67'),('EO:10117','83'),('EO:10130','86')}
assert not result['unresolved'] and len(result['omitted_cases']) == 3

sys.path.insert(0,str(ROOT/'jobs/norton'))
import norton
data = norton.load_registry(ROOT)
assert len({a['instrument_id'] for a in data['applications']}) == 12
questions = [norton.clean(q) for q in data['questions']]
answers,applications,rejected = norton.compile_reviews(ROOT,data,questions)
new = [a for a in applications if a.get('producer') == 'codex-nmb-series-20261025']
assert len(new) == 3
assert not [r for r in rejected if r.get('record',{}).get('producer') == 'codex-nmb-series-20261025']

sys.path.insert(0,str(ROOT/'jobs/claim-kit'))
import factual_events
events = []
for application in new:
    answer = answers[application['answer_id']]
    question = next(q for q in questions if q['question_key'] == application['question_key'])
    evidence = [norton.clean(r) for r in data['evidence'] if r['id'] in answer['evidence_ids']]
    review = next(norton.clean(r) for r in data['reviews'] if r['record_kind'] == 'application'
                  and r['record_id'] == application['id'])
    output,errors = factual_events.reviewed_events(ROOT,application['instrument_id'],{
        'application':application,'question':question,'reviewed_answer':answer,
        'reviewed_evidence':evidence,'application_review':review,'legal_effect':'unresolved'})
    assert not errors and len(output) == 1
    assert output[0]['legal_effect'] == 'unresolved'
    events.extend(output)
print(json.dumps({'routes':len(result['proposals']),'explicit_omissions':len(result['omitted_cases']),
                  'reviewed_events':len(events),'whole_histories_added':0,'network_requests':0}))
