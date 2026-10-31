"""Read-only matched native Valla runner proof. No result publication or adoption.

Prewarm the exact old broad input availability once, then use the same local Git
object pool, source commit, worktree path, prior outputs and empty job caches for
both arms. Construction cost is separate. No projection of missing bodies.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ENV = {**os.environ, 'GIT_LFS_SKIP_SMUDGE': '1', 'GIT_NO_LAZY_FETCH': '1',
       'PYTHONDONTWRITEBYTECODE': '1', 'RATTLE_HEARTBEAT_SECONDS': '1'}
OLD_ROOTS = ['jobs', 'research/readiness', 'research/stage19', 'research/stage15/LEGAL',
             'research/valla', 'research/excavator', 'research/production']


def run(root, args, data=None, env=None):
    p = subprocess.run(args, cwd=root, env=env or ENV, input=data, capture_output=True)
    if p.returncode:
        raise RuntimeError(f'{args[:4]} exit {p.returncode}: {p.stderr[-4000:].decode(errors="replace")}')
    return p.stdout


def git(root, *args, **kwargs):
    return run(root, ['git', *args], **kwargs)


def net():
    try:
        return sum(int(row.split(':', 1)[1].split()[i])
                   for row in Path('/proc/net/dev').read_text().splitlines()[2:]
                   if row.split(':', 1)[0].strip() != 'lo' for i in (0, 8))
    except (OSError, ValueError):
        return None


def digest(data):
    return hashlib.sha256(data).hexdigest()


def disk(root):
    count = total = 0
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__')]
        for name in files:
            p = Path(base) / name
            count += 1
            total += len(os.readlink(p).encode()) if p.is_symlink() else p.stat().st_size
    return {'path_count': count, 'bytes': total}


def modules(root, metadata):
    sys.path.insert(0, str(root / '.github/scripts'))
    for name in ('result_freshness', 'materialize_job_inputs'):
        sys.modules.pop(name, None)
    import result_freshness as f
    import materialize_job_inputs as m
    for mod in (f, m):
        original = mod.git
        def wrapped(*args, _original=original, _module=mod.__name__, **kwargs):
            started = time.perf_counter()
            raw = _original(*args, **kwargs)
            metadata.append({'module': _module, 'argv': args, 'stdout_bytes': len(raw),
                             'seconds': time.perf_counter() - started})
            return raw
        mod.git = wrapped
    return f, m


def isolated(source, root, pin):
    root.mkdir()
    git(root, 'init', '-q')
    objects = Path(git(source, 'rev-parse', '--git-path', 'objects').decode().strip())
    if not objects.is_absolute():
        objects = (source / objects).resolve()
    (root / '.git/objects/info/alternates').write_text(str(objects) + '\n')
    git(root, 'config', 'core.autocrlf', 'false')
    git(root, 'update-ref', 'HEAD', pin)
    git(root, 'sparse-checkout', 'init', '--no-cone')
    # Exact workflow bootstrap, with root entrypoints and old generations omitted.
    workflow = git(source, 'show', pin + ':.github/workflows/run-jobs.yml').decode()
    rules = workflow.split('sparse-checkout: |', 1)[1].split('\n\n', 1)[0]
    rules = '\n'.join(s.strip() for s in rules.splitlines() if s.strip()) + '\n'
    git(root, 'sparse-checkout', 'set', '--no-cone', '--stdin', data=rules.encode())
    git(root, 'checkout', '-f', '--detach', pin)


def main():
    source = Path.cwd().resolve()
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    pin = git(source, 'rev-parse', 'HEAD').decode().strip()
    report = {'source_pin': pin, 'selection': ['valla'], 'cache_conditions':
              'shared fully warmed local Git objects; empty job/download caches per arm; OS page-cache state uncontrolled',
              'remote_transfer_bytes': None, 'scientific_adoption': False, 'arms': {}}
    begin = time.perf_counter()
    before_net = net()
    # This is the OLD supported broad checkout, not a full corpus rebuild.
    # Acquiring retained bodies is construction, charged outside both arms.
    run(source, ['git', 'sparse-checkout', 'add', '--stdin'],
        data=('\n'.join('/' + p + '/**' for p in OLD_ROOTS) + '\n').encode(),
        env={**ENV, 'GIT_NO_LAZY_FETCH': '0'})
    after_net = net()
    report['construction'] = {'seconds': time.perf_counter() - begin,
                              'host_network_bytes_delta': None if before_net is None or after_net is None else after_net - before_net,
                              'network_semantics': 'host-interface sent+received; not Git pack bytes or avoidable transfer'}
    # Same absolute path prevents missing-file diagnostics from differing by arm.
    with tempfile.TemporaryDirectory(prefix='r1-production-') as temporary:
        work = Path(temporary) / 'work'
        for arm in ('full', 'selective'):
            print('Starting ' + arm, flush=True)
            arm_out = out / arm
            arm_out.mkdir()
            start_net = net()
            start = time.perf_counter()
            isolated(source, work, pin)
            os.chdir(work)
            metadata = []
            f, m = modules(work, metadata)
            if arm == 'full':
                git(work, 'sparse-checkout', 'add', '--stdin',
                    data=('\n'.join('/' + p + '/**' for p in OLD_ROOTS) + '\n').encode())
                checkout_receipt = {'mode': 'historical broad availability'}
            else:
                checkout_receipt = m.materialize(['valla'])
                if checkout_receipt['compatibility_fallback_jobs']:
                    raise AssertionError(checkout_receipt)
            f.prepare('valla')
            relevant = f.working(f.scope('valla'))
            previous = {p.relative_to(work).as_posix(): digest(p.read_bytes())
                        for p in (work / 'jobs/valla/output').rglob('*') if p.is_file()}
            startup_seconds = time.perf_counter() - start
            footprint = disk(work)
            startup_metadata = list(metadata)
            metadata_seconds = sum(x['seconds'] for x in startup_metadata)
            native_start = time.perf_counter()
            result = subprocess.run([sys.executable, '.github/scripts/run_jobs.py'], cwd=work,
                                    env={**ENV, 'JOBS': 'valla', 'GITHUB_RUN_ID': 'r1-production-comparison',
                                         'GITHUB_RUN_ATTEMPT': '1', 'RUN_URL': 'r1-matched-read-only'},
                                    capture_output=True)
            (arm_out / 'runner.log').write_bytes(result.stdout + result.stderr)
            if result.returncode:
                raise RuntimeError(f'{arm} native runner failed; inspect runner.log')
            native_seconds = time.perf_counter() - native_start
            native = work / 'jobs/valla/output'
            hashes = {}
            for name in ('INDEX.json', 'SUMMARY.json', 'RUNNER_INPUTS.json'):
                raw = (native / name).read_bytes()
                hashes[name] = digest(raw)
                shutil.copyfile(native / name, arm_out / name)
            doc = json.loads((native / 'INDEX.json').read_bytes())
            if doc['package_scan']['unmaterialized_packages']:
                raise AssertionError(doc['package_scan'])
            # Actual guard, no commit-results publisher. Broad and selective
            # candidates must both pass before declaring equality.
            if f.check('HEAD', ['valla'], arm_out / 'FRESHNESS.json'):
                raise AssertionError('Native generation rejected by existing freshness guard')
            end_net = net()
            report['arms'][arm] = {'startup_seconds': startup_seconds, 'native_seconds': native_seconds,
                                   'materialized': footprint, 'checkout_receipt': checkout_receipt,
                                   'metadata_calls_in_startup': len(startup_metadata),
                                   'metadata_stdout_bytes': sum(x['stdout_bytes'] for x in startup_metadata),
                                   'metadata_seconds': metadata_seconds,
                                   'host_network_bytes_delta': None if start_net is None or end_net is None else end_net - start_net,
                                   'remote_transfer_bytes': 0, 'remote_semantics': 'no remote configured; shared existing objects',
                                   'relevant_inputs_sha256': f.digest(relevant), 'relevant_input_count': len(relevant),
                                   'prior_output_sha256': digest(json.dumps(previous, sort_keys=True).encode()),
                                   'output_sha256': hashes, 'package_scan': doc['package_scan']}
            (arm_out / 'METADATA.json').write_text(json.dumps(metadata, indent=2) + '\n')
            (out / 'COMPARISON.json').write_text(json.dumps(report, indent=2) + '\n')
            os.chdir(source)
            shutil.rmtree(work)
    a, b = report['arms']['full'], report['arms']['selective']
    for key in ('relevant_inputs_sha256', 'relevant_input_count', 'prior_output_sha256', 'output_sha256'):
        if a[key] != b[key]:
            raise AssertionError(f'Matched comparison differs: {key}')
    report['equality'] = 'exact native INDEX/SUMMARY/RUNNER_INPUTS bytes, relevant input map and prior generation'
    report['total_seconds_including_construction_and_verification'] = time.perf_counter() - begin
    (out / 'COMPARISON.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
