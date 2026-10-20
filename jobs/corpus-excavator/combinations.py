"""Small planning-only closure combinations, replayed through production tracker.

Never invent receipts or write into canonical evidence. A closure is a conditional
step assumption, not a source, exhaustion record, status or admission decision.
"""
import importlib.util
import itertools
from pathlib import Path


def load_tracker(root):
    spec = importlib.util.spec_from_file_location('neyman_actual_tracker', Path(root)/'jobs/readiness-tracker/tracker.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def replay(root, proposals, max_size=2):
    if not 1 <= max_size <= 2 or not 1 <= len(proposals) <= 4:
        raise ValueError('bounded to four prerequisites, singles and pairs')
    tracker = load_tracker(root)
    before, problems = tracker.build(str(root))
    ids = {r['instrument_id'] for r in before}
    keys = [p['key'] for p in proposals]
    if len(set(keys)) != len(keys):
        raise ValueError('duplicate closure key')
    for p in proposals:
        if not p.get('origin') or not p.get('assumption'):
            raise ValueError('closure needs origin and explicit assumption')
        for iid, steps in p['closures'].items():
            if iid not in ids or not steps or not set(steps) <= set(tracker.STEP_NAMES)-{'provisional_status'}:
                raise ValueError('unknown identity/step or attempted status closure')
    output = []
    for size in range(1, max_size+1):
        for combo in itertools.combinations(proposals, size):
            closures = {}
            for p in combo:
                for iid, steps in p['closures'].items():
                    closures.setdefault(iid, set()).update(steps)
            after, more = tracker.build(str(root), planning_closures=closures)
            old = {r['instrument_id']: r for r in before}
            changes = []
            for row in after:
                b = old[row['instrument_id']]
                if row['provisional_status'] != b['provisional_status']:
                    raise ValueError('planning replay changed a provisional status')
                if row['instrument_id'] in closures:
                    changes.append({'instrument_id': row['instrument_id'],
                                    'assumed_steps': sorted(closures[row['instrument_id']]),
                                    'residual_open_steps': [s for s in tracker.STEP_NAMES if row['step_'+s]=='open'],
                                    'residual_blockers': row['blockers'].split('|') if row['blockers'] else [],
                                    'conditional_machine_ready': row['ready_for_human_review']=='yes',
                                    'before_machine_ready': b['ready_for_human_review']=='yes'})
            output.append({'planning_only': True, 'assumptions_are_not_evidence': True,
                           'prerequisites': [p['key'] for p in combo], 'assumptions': [p['assumption'] for p in combo],
                           'changes': changes, 'production_problems': sorted(set(problems+more)),
                           'canonical_changes': 0, 'human_certifications': 0})
    return before, output


def validate_predictions(predicted, observed):
    """Compare frozen predictions to later actual tracker rows, never inferred success."""
    actual = {r['instrument_id']: r for r in observed}
    result = []
    for p in predicted:
        r = actual[p['instrument_id']]
        opens = sorted(k[5:] for k,v in r.items() if k.startswith('step_') and v=='open')
        result.append({'instrument_id': p['instrument_id'],
                       'residual_match': sorted(p['residual_open_steps'])==opens,
                       'predicted': sorted(p['residual_open_steps']), 'observed': opens})
    return result


def historical_batches(root, batches):
    """Replay actual frozen accepted batch proposals on current held metadata.

    This is a retrospective software regression, not an ex ante legal forecast or
    a restored historical universe. Record baseline drift instead of hiding it.
    """
    import glob
    import json
    import tempfile
    root=Path(root).resolve();results=[]
    for rel in batches:
        folder=root/rel
        changes=json.loads((folder/'CHANGES.json').read_text())
        targets={c['instrument_id'] for c in changes}
        prior={}
        for p in sorted(glob.glob(str(root/'research/readiness/claims/*.jsonl'))):
            for line in Path(p).read_text().splitlines():
                if line.strip():
                    c=json.loads(line);prior[c['instrument_id']]=c
        before_claims=[c for iid,c in prior.items() if iid not in targets]
        proposals={}
        for line in (folder/'COMBINED.proposed-only.jsonl').read_text().splitlines():
            if line.strip():
                c=json.loads(line)
                if c['instrument_id'] in targets:proposals[c['instrument_id']]=c
        t=load_tracker(root)
        with tempfile.TemporaryDirectory(prefix='neyman-historical-') as tmp:
            p=Path(tmp)/'claims.jsonl'
            p.write_text(''.join(json.dumps(c)+'\n' for c in before_claims))
            t.P['claims']=str(p)
            before,_=t.build(str(root))
            # The named production bundle assumes only the step changes present in
            # the frozen accepted batch. No claim is invented by the planning arm.
            assumptions={c['instrument_id']:[k[5:] for k,v in c['before'].items()
                          if k.startswith('step_') and v=='open' and c['after'].get(k)=='done'] for c in changes}
            predicted,_=t.build(str(root),planning_closures=assumptions)
            p.write_text(''.join(json.dumps(c)+'\n' for c in before_claims+list(proposals.values())))
            checker=json.loads((root/t.J['checker']).read_text())
            overlay=json.loads((folder/'CHECKER.proposed-only.json').read_text())
            for iid in targets:checker['by_instrument'][iid]=overlay['by_instrument'][iid]
            cp=Path(tmp)/'checker.json';cp.write_text(json.dumps(checker));t.J['checker']=str(cp)
            after,_=t.build(str(root))
        preds=[{'instrument_id':r['instrument_id'],'residual_open_steps':[k[5:] for k,v in r.items() if k.startswith('step_') and v=='open']} for r in predicted if r['instrument_id'] in targets]
        base={r['instrument_id']:r for r in before}
        results.append({'batch':rel,'prospective':False,'restored_historical_universe':False,
                        'scope':'Actual historical accepted proposals replayed with current production tracker and held metadata.',
                        'unique_order_ids':sorted(targets),'comparisons':validate_predictions(preds,after),
                        'baseline_open_step_drift':{c['instrument_id']: sorted(k[5:] for k,v in base[c['instrument_id']].items() if k.startswith('step_') and v=='open') != sorted(k[5:] for k,v in c['before'].items() if k.startswith('step_') and v=='open') for c in changes},
                        'source_hashes':{name:__import__('hashlib').sha256((folder/name).read_bytes()).hexdigest() for name in ('CHANGES.json','COMBINED.proposed-only.jsonl','CHECKER.proposed-only.json')},
                        'canonical_changes':0})
    return results
