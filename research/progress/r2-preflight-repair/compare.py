"""Replay pinned original/inventory projections and source-bound omission controls."""
import copy, hashlib, json, subprocess, sys, types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = '88cef0253ed735b2a6e612770f25f9148641ce93'
sys.path.insert(0, str(ROOT/'jobs/claim-kit'))
import evidence_preflight as patched

def baseline():
    code = subprocess.run(['git','show',BASE+':jobs/claim-kit/evidence_preflight.py'],
                          cwd=ROOT, check=True, capture_output=True, timeout=30).stdout
    module = types.ModuleType('r2_baseline_preflight')
    exec(compile(code, '<pinned-main-evidence_preflight>', 'exec'), module.__dict__)
    return module, hashlib.sha256(code).hexdigest()

def run(module, dossier):
    before = copy.deepcopy(dossier)
    result = module.inspect(dossier, ROOT)
    assert dossier == before
    return result

def main():
    old, old_sha = baseline()
    freeze = json.loads((HERE/'FREEZE.json').read_text())
    results = []
    for c in freeze['cases']:
        file = ROOT/c['frozen_dossier']
        assert hashlib.sha256(file.read_bytes()).hexdigest() == c['frozen_sha256']
        d = json.loads(file.read_text())
        results.append({'instrument_id': d['instrument_id'], 'variant': 'frozen',
                        'baseline': run(old,d), 'patched': run(patched,d)})
        if d['instrument_id'] not in ('EO:7952','EO:8123','EO:13613'):
            continue
        body = d['evidence'][d['original_source_id']]['text']
        if d['instrument_id'] == 'EO:7952':
            a = body.index('T his order sh all')
            b = body.index('F ranklin', a)
        elif d['instrument_id'] == 'EO:8123':
            a = body.index('It is unlawful', 5000)
            b = body.index('This reservation', a)
        else:
            a = body.index('Sec. 2.')
            b = body.index('Sec. 3.')
        a, b = patched._clause_locator()._trim(body,a,b)
        ranges = []
        for clause in d['clauses']:
            ca, cb = clause['char_start'], clause['char_end']
            for ga, gb in ((ca,min(cb,a)), (max(ca,b),cb)):
                if ga < gb:
                    ranges.append({'char_start':ga,'char_end':gb,'text':body[ga:gb]})
        control = dict(d, clauses=ranges)
        results.append({'instrument_id':d['instrument_id'], 'variant':'disclosed_omission_control',
                        'omitted':{'char_start':a,'char_end':b,'text':body[a:b]},
                        'baseline':run(old,control), 'patched':run(patched,control)})
    out = {'base':BASE,'baseline_code_sha256':old_sha,
           'patched_code_sha256':hashlib.sha256((ROOT/'jobs/claim-kit/evidence_preflight.py').read_bytes()).hexdigest(),
           'notice':'Controls deliberately remove held-source spans; they are not current production defects.',
           'results':results}
    (HERE/'COMPARISON.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
    print([(r['instrument_id'],r['variant'],[t['kind'] for t in r['patched']['tasks']]) for r in results])

if __name__=='__main__':
    main()
