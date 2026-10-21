"""Paired actual-tracker replay with additive, frozen acquisition receipts.

Never writes upstream output, claims or legal state. A mechanical ready delta
is reported separately from independent source/legal review.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import time

from excavator import ROOT, write_json, write_lines, canonical, STEPS, CENSUS


def compare(before, after):
    b={r['instrument_id']:r for r in before};a={r['instrument_id']:r for r in after}
    if set(a)!=set(b):raise ValueError('identity universe changed')
    changes=[]
    for iid in sorted(a):
        if a[iid]['provisional_status']!=b[iid]['provisional_status']:
            raise ValueError('provisional status changed')
        for step in STEPS:
            key='step_'+step
            if a[iid][key]!=b[iid][key]:
                if a[iid][key]!='done' or b[iid][key]!='open':raise ValueError('unexpected step regression or applicability change')
                changes.append({'instrument_id':iid,'step':step,'before':'open','after':'done',
                                'remaining_open_steps':[s for s in STEPS if a[iid]['step_'+s]=='open'],
                                'remaining_blockers':a[iid]['blockers']})
    return {'steps_completed':len(changes),'orders_with_a_step_completed':len({r['instrument_id'] for r in changes}),
            'steps_by_kind':dict(Counter(r['step'] for r in changes)),
            'mechanically_new_ready':[i for i in a if a[i]['ready_for_human_review']=='yes' and b[i]['ready_for_human_review']!='yes'],
            'independently_human_certified_added':0,'changes':changes}


def run(root, receipts, out, baseline_receipts=None):
    root=root.resolve();receipts=receipts.resolve();out=out.resolve()
    rel=receipts.relative_to(root).as_posix()
    if not out.is_relative_to(root/'research/excavator'):
        raise ValueError('measurement output must be under research/excavator')
    spec=importlib.util.spec_from_file_location('excavator_actual_tracker',root/'jobs/readiness-tracker/tracker.py')
    tracker=importlib.util.module_from_spec(spec);spec.loader.exec_module(tracker)
    baseline_rel=None
    if baseline_receipts is not None:
        # A frozen catalogue before this acquisition permits replay after the
        # canonical source output has advanced. It changes no file on disk.
        baseline_receipts=baseline_receipts.resolve()
        baseline_rel=baseline_receipts.relative_to(root).as_posix()
        tracker.J['ladder_sources']=[baseline_rel]
    start=time.monotonic()
    before,pb=tracker.build(str(root));bs=tracker.summarise(before,pb)
    tracker.J['ladder_sources']=list(tracker.J['ladder_sources'])+[rel]
    after,pa=tracker.build(str(root));ass=tracker.summarise(after,pa)
    delta=compare(before,after)
    hashes={}
    for p in [root/CENSUS,root/'research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv',
              root/'jobs/claim-checker/output/PER_CLAIM.json',root/'jobs/readiness-tracker/tracker.py',receipts,
              *([baseline_receipts] if baseline_receipts is not None else []),
              *sorted((root/'research/readiness/claims').glob('*.jsonl'))]:
        hashes[p.relative_to(root).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    delta.update(input_hashes=hashes,measurement_seconds=round(time.monotonic()-start,4),
                 baseline_receipts=baseline_rel,added_receipts=rel,
                 legal_cutoff='2026-10-14',audited_correctly_new_ready=None,
                 caution='Mechanical readiness is an existing tracker result; independent source/legal audit is separate.')
    write_json(out/'SUMMARY.json',delta);write_json(out/'BEFORE.json',bs);write_json(out/'AFTER.json',ass)
    write_lines(out/'STEP_CHANGES.jsonl',delta['changes'])
    print(canonical({k:v for k,v in delta.items() if k not in ('input_hashes','changes')}))
    return delta


def run_combinations(root, proposals, out):
    from combinations import replay
    before, results = replay(Path(root), proposals)
    write_json(Path(out)/'COMBINATIONS.json', {'planning_only': True, 'canonical_changes': 0, 'combinations': results})
    return before, results


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,default=ROOT)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--receipts',type=Path);g.add_argument('--closures',type=Path);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--baseline-receipts',type=Path,help='frozen prior ladder catalogue; default is current canonical output')
    a=p.parse_args()
    if a.closures:run_combinations(a.repo,json.loads(a.closures.read_text()),a.out)
    else:run(a.repo,a.receipts,a.out,a.baseline_receipts)
