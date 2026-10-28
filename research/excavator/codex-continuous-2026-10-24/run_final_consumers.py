#!/usr/bin/env python3
"""One aggregate replay of already completed selections; no filing or adoption."""
from pathlib import Path
import argparse, hashlib, json, sys, time
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'jobs/claim-kit'))
import completion as C
import batch

parser=argparse.ArgumentParser()
parser.add_argument('--completion', action='append', required=True)
parser.add_argument('--write', required=True)
args=parser.parse_args()
dest=batch.safe(ROOT,args.write);dest.mkdir(exist_ok=False,parents=True)
inputs=C.Inputs(ROOT);selected={};selections=[];started=time.monotonic()
for name in args.completion:
    folder=batch.safe(ROOT,name)
    tally=json.loads((folder/'TALLY.json').read_bytes())
    publication=json.loads((folder/'PUBLICATION.json').read_bytes())
    assert tally['exceptions']==0 and publication['written'] is True
    for leaf in ['TALLY.json','PUBLICATION.json','INPUTS.json','CLAIMS.publishable.jsonl']:
        inputs.pin((folder/leaf).relative_to(ROOT).as_posix())
    raw=(folder/'CLAIMS.publishable.jsonl').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==publication['sha256']
    for line in raw.splitlines(keepends=True):
        if not line.strip():continue
        claim=json.loads(line);iid=claim['instrument_id'];assert iid not in selected
        selected[iid]=(claim,line)
        selections.append({'instrument_id':iid,'completion':name,
                           'claim_sha256':batch.digest(batch.canon(claim).encode()),
                           'publication_kind':'partial_research' if claim.get('unresolved_material_gaps') else 'whole_case'})
claims=dest/'CLAIMS.exact-selected.jsonl';claims.write_bytes(b''.join(v[1] for v in selected.values()))
C.pin_checker_inputs(inputs,selected)
checker=C.run_checker(ROOT,claims,dest/'checker')
tracker=C.run_tracker(ROOT,selected,checker,dest,inputs)
inputs.unchanged();inputs.save(dest)
batch.dump(dest/'SELECTION.json',selections)
batch.dump(dest/'TRACKER_REPLAY.json',tracker)
batch.dump(dest/'RUN.json',{'scope':'Actual checker/tracker replay of exact already independently reviewed and completed selections; no new legal review, filing, status adoption or canonical output overwrite.',
    'wall_seconds':time.monotonic()-started,'selected':len(selected),
    'claims_filed':0,'human_certifications':0,'model_tokens':None})
print(json.dumps({iid:{k:row['after'].get(k) for k in ['steps_done','steps_applicable','ready_for_human_review','blockers']} for iid,row in tracker['selected'].items()},indent=2))
