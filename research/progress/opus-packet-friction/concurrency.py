"""Run real `kit.py complete --publish` processes concurrently in isolated trees (engineering receipt).

PLAN.json: {"cases": [{"name": ..., "runs": [{"tree": ..., "manifest": ..., "dest": ..., "target": ...,
             "submitted": [ids] | null}], "cleanup": true}]}
`manifest` is an existing completion manifest inside `tree`. With `submitted`, a variant manifest is
written beside it keeping only those submitted members (others become blocked with a reason) and
publishing to `target`. Every run starts at the same moment; afterwards the case records each run's
outcome and, when `cleanup` is true, removes what it published so the next case starts from the same
canonical claims. Isolated replay trees only: this never touches a real checkout's canonical records.

Usage: python3 concurrency.py PLAN.json OUT.json
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent


def variant(run):
    tree = Path(run['tree']); manifest = tree / run['manifest']
    m = json.loads(manifest.read_bytes())
    if run.get('submitted') is not None:
        for member in m['members']:
            if member['outcome'] == 'submit' and member['instrument_id'] not in run['submitted']:
                iid = member['instrument_id']
                member.clear()
                member.update(instrument_id=iid, outcome='blocked',
                              reason='Left to another concurrent completion in this engineering receipt.')
    m['publication']['path'] = run['target']
    path = manifest.with_name('CONCURRENCY_' + run['name'] + '.json')
    path.write_text(json.dumps(m, indent=1, sort_keys=True) + '\n')
    return path


def main(plan_path, out_path):
    plan = json.loads(Path(plan_path).read_bytes()); results = []
    for c in plan['cases']:
        procs = []
        for i, run in enumerate(c['runs']):
            run = dict(run, name=f"{c['name']}-{i}")
            tree = Path(run['tree']); manifest = variant(run)
            dest = tree / run['dest']
            p = subprocess.Popen([sys.executable, '-B', str(HERE / 'io_run.py'), str(tree / 'jobs/claim-kit/kit.py'),
                                  '--repo', str(tree), 'complete', str(manifest), '--write', str(dest), '--publish'],
                                 cwd=tree, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            procs.append((p, run, tree, dest))
        started = time.monotonic(); runs = []
        for p, run, tree, dest in procs:
            out, err = p.communicate()
            stats = next((json.loads(l[7:]) for l in err.splitlines() if l.startswith('IO_RUN ')), {})
            tally = json.loads((dest / 'TALLY.json').read_bytes()) if (dest / 'TALLY.json').exists() else {}
            exc = json.loads((dest / 'EXCEPTIONS.json').read_bytes()) if (dest / 'EXCEPTIONS.json').exists() else None
            target = tree / run['target']
            runs.append({'tree': tree.name, 'manifest': run['manifest'], 'target': run['target'], 'returncode': p.returncode,
                         **stats, 'counts': tally.get('counts'), 'eligible': tally.get('eligible'),
                         'claims_published': tally.get('claims_published'), 'published_file_exists': target.exists(),
                         'published_sha256': __import__('hashlib').sha256(target.read_bytes()).hexdigest() if target.exists() else None,
                         'concurrent_disjoint_claim_files': tally.get('concurrent_disjoint_claim_files'),
                         'exceptions': exc, 'stderr_tail': err.strip().splitlines()[-2:] if p.returncode else []})
        results.append({'case': c['name'], 'wall_seconds': round(time.monotonic() - started, 1), 'runs': runs})
        print(c['name'], [(r['returncode'], r['claims_published'], r['published_file_exists']) for r in runs], flush=True)
        if c.get('cleanup', True):
            for _, run, tree, _ in procs:
                if (tree / run['target']).exists():
                    (tree / run['target']).unlink()
    Path(out_path).write_text(json.dumps({'plan': plan, 'results': results}, indent=1) + '\n')


if __name__ == '__main__':
    main(*sys.argv[1:3])
