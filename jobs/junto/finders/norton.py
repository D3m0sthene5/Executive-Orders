"""NORTON finder adapter: measured intersections, never invented dollar savings."""
import argparse
import hashlib
import json
from pathlib import Path
import time

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--data',required=True);p.add_argument('--out',required=True)
    p.add_argument('--run-id',required=True);p.add_argument('--profiles')
    a=p.parse_args();start=time.monotonic()
    raw=(Path(a.data)/'NORTON_CENSUS.json').read_bytes();c=json.loads(raw)
    candidates=[]
    count=c['counts']['exact_reusable_questions']
    if count:
        candidates.append({'title':'NORTON: pool exact shared factual obligations',
            'saver_key':'norton_shared_factual_obligations','origin':'owner_seeded',
            'targets':['repeated_factual_research'], 'status':'unverified',
            'evidence':[{'path':'jobs/norton/output/CENSUS.json','sha256':hashlib.sha256(raw).hexdigest(),
                         'exact_questions':count,'clause_applications':c['counts']['applications_of_reusable_questions'],
                         'reviewed_answers':c['counts']['reviewed_answers']}],
            'estimate':{'basis':'Observed intersections only; dollars and savings unmeasured.', 'usd_per_session':None},
            'usd_basis':'unmeasured',
            'proposed_test':'Fresh matched family clusters through independent factual review, per-clause applicability and integration; include source holds and all arm costs. No cross-arm source or answer sharing.'})
    out=Path(a.out);out.write_text(''.join(json.dumps(c,sort_keys=True)+'\n' for c in candidates))
    Path(str(out)+'.run.json').write_text(json.dumps({'data_digest':hashlib.sha256(raw).hexdigest(),
        'inputs':{'census_sha256':hashlib.sha256(raw).hexdigest()},'wall_seconds':time.monotonic()-start}))

if __name__=='__main__':main()
