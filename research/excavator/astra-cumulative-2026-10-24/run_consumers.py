"""Replay the real tracker on identical inputs before/after two checked claims."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'jobs/readiness-tracker'))
import tracker as T

baseline=ROOT/'jobs/leverage-campaign-check/output/shared-source/claim-checker/PER_CLAIM.json'
prior=ROOT/'research/excavator/astra-source-first-2026-10-23/checker-v4/PER_CLAIM.json'
partial=ROOT/'research/excavator/astra-source-first-2026-10-23/CLAIMS.partial.corrected-v3.jsonl'
new_checks=[OUT/f'EO_{n}/checker/PER_CLAIM.json' for n in [11782,9452]]
new_claims=[OUT/f'EO_{n}/PROPOSED_CLAIMS.jsonl' for n in [11782,9452]]
pins={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [baseline,prior,partial,*new_checks,*new_claims]}
old=json.loads(baseline.read_text())
old['by_instrument'].update(json.loads(prior.read_text())['by_instrument'])
claims=[]
for p in sorted((ROOT/'research/readiness/claims').glob('*.jsonl')):
    for line in p.read_text().splitlines():
        if line.strip():
            c=json.loads(line)
            if c['instrument_id'] not in ('EO:11782','EO:9452'):claims.append(c)
claims.append(next(json.loads(l) for l in partial.read_text().splitlines() if json.loads(l)['instrument_id']=='EO:11782'))
after=copy.deepcopy(old)
for p in new_checks:after['by_instrument'].update(json.loads(p.read_text())['by_instrument'])
observations={}
with tempfile.TemporaryDirectory(prefix='cumulative-tracker-') as tmp:
    tmp=Path(tmp)
    for name,receipt,rows in [('before',old,claims),('after',after,claims+[json.loads(p.read_text()) for p in new_claims])]:
        cp=tmp/(name+'-checker.json');cp.write_text(json.dumps(receipt))
        qp=tmp/(name+'-claims.jsonl');qp.write_text(''.join(json.dumps(c)+'\n' for c in rows))
        T.J['checker']=str(cp)
        T.P['claims']=str(qp) if name=='before' else 'research/readiness/claims/*.jsonl'
        tick=time.monotonic();orders,problems=T.build(str(ROOT));elapsed=time.monotonic()-tick
        observations[name]={'machine_seconds':round(elapsed,3),'input_problems':problems,
                            'orders':{o['instrument_id']:o for o in orders if o['instrument_id'] in ('EO:11782','EO:9452')}}
result={'input_commit':'9ecddf9fe82a1989c6133610a77308ec74454184','legal_cutoff':'2026-10-14','pins':pins,
        'method':'Actual tracker.build twice on identical available inputs; exact prior checker receipts reused for unchanged claims, PR56 corrected-v3 receipt for before, two actually executed current checker results for after. After reads actual canonical research/readiness/claims/*.jsonl with its ordinary precedence. No planning_closures or hypothetical completed steps. Cohort comparison only; optional absent checkout inputs disclosed. Committed PR55 baseline had EO9452 at3/6; its local before1/6 reflects absent optional machine metadata, so the extra2 sparse steps are not credited as new research.',
        **observations,'tokens':None,'human_certifications':0,'status_changes':0}
(OUT/'TRACKER_COMPARISON.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:{iid:{f:o.get(f) for f in ['ready','ready_for_human_review','steps_done','steps_applicable','blockers']} for iid,o in v['orders'].items()} for k,v in observations.items()},indent=2))
