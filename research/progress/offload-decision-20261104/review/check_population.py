"""Independent accounting on retained original artifacts, no protected case-level output."""
import csv, hashlib, io, json
from collections import Counter
from pathlib import Path
p = Path(__file__).resolve().parents[2]
old = p / 'production-observability-20261104'
base = old / 'baseline'
main = '600ae3018f71025b3e53dc8538b8f92e6e159b76'
protected = 'cacfb8f4af6db949476bd7bec8220a464055c931'
j = lambda f: json.loads(f.read_bytes())
sha = lambda data: hashlib.sha256(data).hexdigest()
def check(f, git_blob, digest):
    data = f.read_bytes()
    assert hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest() == git_blob
    assert sha(data) == digest
    return data
def artifact(path, ref):
    spec, = [s for s in j(base/'SOURCES.json') if s['path'] == path and s['commit'] == ref]
    return json.loads(check(base/spec['local_path'], spec['sha'], spec['sha256']))
native = j(base/'BASELINE.json')['source']['readiness']
rows = list(csv.DictReader(io.StringIO(check(p/'control-center/orders.csv',native['git_blob'],native['sha256']).decode())))
ids = {r['instrument_id'] for r in rows}
assert len(rows) == len(ids)
unfinished = {r['instrument_id'] for r in rows if r['ready_for_human_review'] != 'yes'}
plan = artifact('research/excavator/claude-tribonian-2026-11-04/tools/batches.json',protected)
flat = [i for group in plan.values() for i in group]
held = set(flat)
assert len(held) == len(flat) and held <= unfinished
locks = set(artifact('research/readiness/CLAIM_KIT_LOCK.json', main)['orders'])
assert locks == set(artifact('research/readiness/CLAIM_KIT_LOCK.json', protected)['orders'])
left = unfinished - held - locks
out = j(old/'historical/OUTCOMES.json')
summary = {}
for key in ['completion_outcomes','genuine_review_versions','apollo_to_erasmus_retry_membership']:
    rr = out[key]; subset = [r for r in rr if r['instrument_id'] in left]
    versions = {(r['instrument_id'],r['claim_sha256']) for r in rr if r.get('claim_sha256')}
    summary[key] = {'rows':len(rr),'orders':len({r['instrument_id'] for r in rr}),'outside_both_rows':len(subset),'outside_both_orders':len({r['instrument_id'] for r in subset})}
    if key != 'apollo_to_erasmus_retry_membership':
        field = 'outcome' if key == 'completion_outcomes' else 'verdict'
        summary[key].update(version_pairs=len(versions),outside_both_disposition=dict(Counter(r[field] for r in subset)))
result = dict(schema='offload-independent-population/v1', readiness_sha256=native['sha256'], historical_outcomes_sha256=sha((old/'historical/OUTCOMES.json').read_bytes()), rows=len(rows), unfinished=len(unfinished), protected=len(held), protected_batches=len(plan), outside_plan=len(unfinished-held), reservations=len(locks), reserved_unfinished=len(unfinished&locks), reserved_in_plan=len(locks&held), outside_both=len(left), historical=summary)
assert (result['unfinished'],result['protected'],result['outside_both'])==(14188,1218,12963)
print(json.dumps(result,indent=2,sort_keys=True))
