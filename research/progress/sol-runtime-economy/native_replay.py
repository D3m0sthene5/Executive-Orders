"""Compare the ordinary checker main on retained inputs; writes only --out.

Usage: python3 -I native_replay.py --repo REPO --out SCRATCH
The baseline module is extracted from the pinned commit, not from a PR.
No network, source acquisition, claim publication or packet review occurs.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

BASE = '2c85459cf38b08dc1eea6d7c84a74268fa45c28e'
CLAIMS = 'research/readiness/claims/claude-2026-11-04-tribonian-o27.jsonl'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def rchar():
    return int(dict(line.split(':', 1) for line in Path('/proc/self/io').read_text().splitlines())['rchar'])


def child(args):
    repo, dest = args.repo.resolve(), args.out.resolve()
    if args.memory_mb:
        resource.setrlimit(resource.RLIMIT_AS, (args.memory_mb * 2**20,) * 2)
    sys.path.insert(0, str(repo / 'jobs/claim-checker'))
    source = args.source.resolve()
    spec = importlib.util.spec_from_file_location('sources', source)
    module = importlib.util.module_from_spec(spec)
    sys.modules['sources'] = module
    spec.loader.exec_module(module)
    import checker
    calls = {}
    for name in ('build_index', 'load_job_sources'):
        original = getattr(module, name)
        def timed(*a, _name=name, _original=original, **kw):
            started = time.monotonic()
            try:
                return _original(*a, **kw)
            finally:
                row = calls.setdefault(_name, {'calls': 0, 'seconds': 0.0})
                row['calls'] += 1
                row['seconds'] += time.monotonic() - started
        setattr(module, name, timed)
    os.environ.update(REPO_ROOT=str(repo), OUTPUT_DIR=str(dest / 'checker'),
                      JOB_CACHE_DIR=str(dest / 'cache'), CLAIM_CHECKER_VERIFY_DOWNLOADS='0',
                      CLAIM_KIT_CACHE_DIR=str(dest / 'kit-cache'), JOB_LIMIT='',
                      PYTHONDONTWRITEBYTECODE='1')
    before_io, started = rchar(), time.monotonic()
    summary = checker.main(['--claims', str(args.claims or repo / CLAIMS)])
    result = {'seconds': time.monotonic() - started, 'rchar': rchar() - before_io,
              'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'phases': calls, 'source_sha256': sha(source),
              'claims_checked': summary['claims_checked'],
              'claims_all_checks_passed': summary['claims_all_checks_passed'],
              'claims_mechanical_fail': summary['claims_mechanical_fail'],
              'claims_mechanical_unverified': summary['claims_mechanical_unverified']}
    (dest / 'METRICS.json').write_text(json.dumps(result, indent=2) + '\n')


def main(args):
    repo, out = args.repo.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    baseline = out / 'baseline_sources.py'
    baseline.write_bytes(subprocess.check_output(['git', 'show', BASE + ':jobs/claim-checker/sources.py'], cwd=repo))
    files = sorted(repo.glob('jobs/*/output/SOURCES.jsonl'))
    inputs = files + [args.claims.resolve() if args.claims else repo / CLAIMS]
    for path in (repo / 'research/stage21/original_sources').glob('*'):
        if path.is_file():
            inputs.append(path)
    inputs += list(repo.glob('jobs/fr-originals/**/EO_13128.txt'))
    inputs += list(repo.glob('jobs/fr-originals/**/EO_13274.txt'))
    inputs += list(repo.glob('jobs/fr-originals/**/EO_13286.txt'))
    pins = {(str(p.relative_to(repo)) if p.is_relative_to(repo) else str(p)):
            {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(set(inputs))}
    result = {'base': BASE, 'repo': str(repo), 'source_files': len(files),
              'source_bytes': sum(p.stat().st_size for p in files), 'input_pins': pins,
              'normalizations': [], 'runs': []}
    # Alternating order; every subprocess has an empty application cache.
    arms = ('baseline', 'repaired') if args.single_pair else ('baseline', 'repaired', 'repaired', 'baseline')
    for n, arm in enumerate(arms):
        dest = out / f'{n}-{arm}'
        dest.mkdir()
        source = baseline if arm == 'baseline' else repo / 'jobs/claim-checker/sources.py'
        command = [sys.executable, '-I', str(Path(__file__).resolve()), '--child',
                   '--repo', str(repo), '--out', str(dest), '--source', str(source)]
        if args.memory_mb:
            command += ['--memory-mb', str(args.memory_mb)]
        if args.claims:
            command += ['--claims', str(args.claims.resolve())]
        with (dest / 'LOG.txt').open('w') as log:
            run = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        row = {'arm': arm, 'returncode': run.returncode}
        if (dest / 'METRICS.json').exists():
            row.update(json.loads((dest / 'METRICS.json').read_text()))
        result['runs'].append(row)
        print(json.dumps(row), flush=True)
    reference = out / '0-baseline/checker'
    comparisons = {}
    if reference.exists():
        for dest in sorted(out.glob('[123]-*/checker')):
            comparisons[str(dest.parent.name)] = {p.name: p.read_bytes() == (dest / p.name).read_bytes()
                                                    for p in reference.iterdir() if p.is_file() and (dest / p.name).is_file()}
    result['byte_comparisons'] = comparisons
    result['input_pins_unchanged'] = all(sha(repo / rel) == value['sha256'] for rel, value in pins.items())
    (out / 'RESULT.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--child', action='store_true')
    parser.add_argument('--memory-mb', type=int)
    parser.add_argument('--claims', type=Path)
    parser.add_argument('--single-pair', action='store_true')
    args = parser.parse_args()
    child(args) if args.child else main(args)
