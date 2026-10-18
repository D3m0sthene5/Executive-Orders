"""Read-only actual tracker replay; isolated inputs never become publication.

Includes an intentionally unreviewed initial-proposal arm to demonstrate the
mechanical/legal distinction. The independently accepted arm contains EO12720.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]


def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes((json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())


def main():
    start=time.perf_counter()
    output=HERE/'tracker-replay-v2'
    output.mkdir(exist_ok=True)
    spec=importlib.util.spec_from_file_location('batch_actual_tracker',ROOT/'jobs/readiness-tracker/tracker.py')
    t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
    protected=[ROOT/t.P['universe'],ROOT/t.P['decided'],ROOT/t.J['checker'],
        ROOT/'research/readiness/SOURCE_AUDIT_HOLDS.jsonl',
        *sorted((ROOT/'research/readiness/claims').glob('*.jsonl'))]
    def hashes():return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    beforehash=hashes()
    before,p=t.build(str(ROOT));baseline=t.summarise(before,p)
    dump(output/'BASELINE.json',baseline)
    old={r['instrument_id']:r for r in before}
    canonical=''.join(p.read_text('utf-8').rstrip()+'\n' for p in sorted((ROOT/'research/readiness/claims').glob('*.jsonl')))
    checker=json.loads((ROOT/t.J['checker']).read_bytes())
    initial=HERE/'matched/A/producer/assembled-proposals.jsonl'
    proposals=[json.loads(s) for s in initial.read_text('utf-8').splitlines() if s.strip()]
    verified=json.loads((HERE/'matched/A/initial-actual-checker/PER_CLAIM.json').read_bytes())
    bproposals=[json.loads(s) for s in (HERE/'matched/B/applied/CLAIMS.proposed.jsonl').read_text('utf-8').splitlines() if s.strip()]
    bverified=json.loads((HERE/'matched/B/applied/actual-checker/PER_CLAIM.json').read_bytes())
    experiments={}
    for name,selected,checked in [('A_UNREVIEWED_INITIAL',proposals,verified),
            ('A_INDEPENDENTLY_ACCEPTED',[c for c in proposals if c['instrument_id']=='EO:12720'],verified),
            ('B_UNREVIEWED_INITIAL',bproposals,bverified),
            ('B_INDEPENDENTLY_ACCEPTED',[c for c in bproposals if c['instrument_id']=='EO:12720'],bverified)]:
        folder=output/name;folder.mkdir(exist_ok=True)
        claims=folder/'COMBINED.proposed-only.jsonl'
        claims.write_bytes((canonical+''.join(json.dumps(c,ensure_ascii=False,sort_keys=True)+'\n' for c in selected)).encode())
        merged={**checker,'by_instrument':dict(checker['by_instrument'])}
        for c in selected:merged['by_instrument'][c['instrument_id']]=checked['by_instrument'][c['instrument_id']]
        cp=folder/'CHECKER.proposed-only.json';dump(cp,merged)
        t.P['claims']=claims.relative_to(ROOT).as_posix();t.J['checker']=cp.relative_to(ROOT).as_posix()
        after,problems=t.build(str(ROOT));summary=t.summarise(after,problems)
        dump(folder/'SUMMARY.json',summary)
        by={r['instrument_id']:r for r in after}
        changes=[{'instrument_id':i,'before':old[i],'after':by[i]} for i in old if old[i]!=by[i]]
        dump(folder/'CHANGES.json',changes)
        experiments[name]={'selected_proposals':len(selected),'ready':summary['ready_for_human_review'],
            'ready_delta':summary['ready_for_human_review']-baseline['ready_for_human_review'],
            'newly_mechanically_ready':[i for i in old if old[i]['ready_for_human_review']!='yes' and by[i]['ready_for_human_review']=='yes'],
            'source_audit_hold_9789':by['EO:9789'],
            'scope':'isolated counterfactual inputs to actual tracker; never canonical writes'}
    assert hashes()==beforehash,'authoritative inputs changed'
    result={'schema':'eo-batch-actual-tracker-replay/v1','baseline_ready':baseline['ready_for_human_review'],
        'experiments':experiments,'canonical_ready_delta':0,'human_certifications_added':0,
        'authoritative_input_hashes_unchanged':True,'input_hashes':beforehash,
        'wall_seconds':round(time.perf_counter()-start,4),
        'limits':['Unreviewed initial proposals include independently rejected legal conclusions and MUST NOT be published.',
                  'Accepted EO12720 is an owner-routed replica of an upstream Sol proposal; it is not an additional independent discovery.',
                  'A mechanically ready proposal remains subject to owner acceptance and human review.']}
    dump(output/'RESULTS.json',result)
    print(json.dumps({k:result[k] for k in ('baseline_ready','canonical_ready_delta','human_certifications_added','authoritative_input_hashes_unchanged','wall_seconds')}))
    print(json.dumps({k:{x:v[x] for x in ('selected_proposals','ready_delta','newly_mechanically_ready') if x in v} for k,v in experiments.items()}))

if __name__=='__main__':main()
