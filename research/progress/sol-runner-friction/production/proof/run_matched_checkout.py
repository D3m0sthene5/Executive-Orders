"""Matched pinned production checkout proof; no scientific job execution.

Run after the caller has materialized the old broad checkout and invoked
result_freshness.prepare('readiness-tracker') once to warm its required objects.
All measured clones have no remotes and share only already-local Git objects.
--local-projection instead proves exact real bodies only on the locally available
projection; it explicitly cannot establish complete production availability.
"""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

NAME = 'readiness-tracker'
SCRATCH = Path(os.environ.get('MATCHED_PROOF_SCRATCH', tempfile.gettempdir()))
ENV = {**os.environ, 'GIT_NO_LAZY_FETCH': '1', 'PYTHONDONTWRITEBYTECODE': '1',
       'GIT_CONFIG_NOSYSTEM': '1'}


def cmd(root, *args, data=None, env=None):
    p = subprocess.run(args, cwd=root, env=env or ENV, input=data,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode:
        raise RuntimeError(f'{args[:4]} returned {p.returncode}: {p.stderr[-2000:].decode(errors="replace")}')
    return p.stdout


def git(root, *args, **kwargs):
    return cmd(root, 'git', *args, **kwargs)


@contextmanager
def cwd(root):
    old = Path.cwd()
    os.chdir(root)
    try:
        yield
    finally:
        os.chdir(old)


def module(root, name):
    sys.path.insert(0, str(root / '.github/scripts'))
    # Fresh imports bind each module to the measured checkout's exact code.
    sys.modules.pop('result_freshness', None)
    spec = importlib.util.spec_from_file_location(name, root / '.github/scripts' / (name + '.py'))
    out = importlib.util.module_from_spec(spec)
    sys.modules[name] = out
    spec.loader.exec_module(out)
    return out


def entries(root, ref):
    out = {}
    for row in git(root, 'ls-tree', '-rz', ref).split(b'\0'):
        if row:
            h, p = row.split(b'\t', 1)
            mode, kind, oid = h.decode().split()
            if kind == 'blob':
                out[p.decode()] = {'mode': mode, 'oid': oid}
    return out


def inventory(root, ref):
    # --batch-all-objects enumerates only local objects; no size query on a
    # missing promised blob and no ls-tree -l is performed.
    local = {}
    for line in git(root, 'cat-file', '--batch-all-objects',
                    '--batch-check=%(objectname) %(objecttype) %(objectsize)').decode().splitlines():
        oid, kind, size = line.split()
        if kind == 'blob':
            local[oid] = int(size)
    tree = entries(root, ref)
    def tally(paths):
        have = [p for p in paths if tree[p]['oid'] in local]
        return {'path_count': len(paths), 'local_path_count': len(have),
                'local_blob_bytes': sum(local[tree[p]['oid']] for p in have),
                'missing_path_count': len(paths) - len(have),
                'missing_blob_bytes': None}
    report = {label: tally([p for p in tree if predicate(p)]) for label, predicate in {
        'all_tracked': lambda p: True, 'jobs': lambda p: p.startswith('jobs/'),
        'job_outputs': lambda p: p.startswith('jobs/') and '/output/' in p,
        'research': lambda p: p.startswith('research/')}.items()}
    report['size_semantics'] = 'Local uncompressed Git blob bytes by path; not transfer bytes. Missing object sizes unknown.'
    return tree, local, report


def isolated(source, target, ref):
    target.mkdir()
    git(target, 'init', '-q')
    objects = Path(git(source, 'rev-parse', '--git-path', 'objects').decode().strip())
    if not objects.is_absolute():
        objects = (source / objects).resolve()
    alt = target / '.git/objects/info/alternates'
    alt.write_text(str(objects) + '\n')
    git(target, 'config', 'user.name', 'Bounded checkout proof')
    git(target, 'config', 'user.email', 'proof@example.invalid')
    git(target, 'config', 'core.autocrlf', 'false')
    # Deliberately no remote or promisor config: any missing body fails closed.
    git(target, 'update-ref', 'HEAD', ref)


def disk(root):
    paths = {}
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d != '.git' and d != '__pycache__')
        for name in files:
            p = Path(base) / name
            rel = p.relative_to(root).as_posix()
            data = os.readlink(p).encode() if p.is_symlink() else p.read_bytes()
            paths[rel] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    return paths


def tally_disk(paths):
    return {'files': len(paths), 'bytes': sum(v['bytes'] for v in paths.values()),
            'job_output_files': sum('/output/' in p and p.startswith('jobs/') for p in paths),
            'job_output_bytes': sum(v['bytes'] for p, v in paths.items() if p.startswith('jobs/') and '/output/' in p)}


def bootstrap(root):
    workflow = (root / '.github/workflows/run-jobs.yml').read_text()
    block = workflow.split('sparse-checkout: |', 1)[1].split('\n\n', 1)[0]
    return '\n'.join(s.strip() for s in block.splitlines() if s.strip()) + '\n'


def tracked_equal(root, path, item):
    p = root / path
    if not p.exists() and not p.is_symlink():
        return False
    data = os.readlink(p).encode() if p.is_symlink() else p.read_bytes()
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == item.split(':')[1]


def mutations(root, temp):
    """Actual freshness working map sees edit/delete/staged-add/untracked changes."""
    f = module(root, 'result_freshness')
    with cwd(root):
        declared = f.scope(NAME)
        before = f.working(declared)
        candidates = [p for p in before if p.startswith(f'jobs/{NAME}/') and p.endswith('.md')]
        edited = candidates[0]
        p = root / edited
        original = p.read_bytes()
        p.write_bytes(original + b'\nproof edit\n')
        edit_seen = f.working(declared)[edited] != before[edited]
        p.unlink()
        delete_seen = edited not in f.working(declared)
        p.write_bytes(original)
        add = f'jobs/{NAME}/PROOF_ADDED.txt'
        (root / add).write_text('staged addition\n')
        git(root, 'add', add)
        staged_seen = add in f.working(declared)
        untracked = f'jobs/{NAME}/PROOF_UNTRACKED.txt'
        (root / untracked).write_text('untracked addition\n')
        untracked_seen = untracked in f.working(declared)
    result = {'edit': edit_seen, 'delete': delete_seen, 'staged_add': staged_seen, 'untracked_add': untracked_seen}
    if not all(result.values()):
        raise AssertionError(result)
    return result


def run(source, target, projection=False, fixture_failure=False, scope_label=None, native_probe=None):
    pinned = git(source, 'rev-parse', 'HEAD').decode().strip()
    tree, local, inv = inventory(source, pinned)
    report = {'schema': 1, 'selected_jobs': [NAME], 'production_pin': pinned,
              'inventory': inv, 'scope': scope_label or ('complete pinned production' if not projection else 'locally available exact-body projection'),
              'remote_transfer_bytes': None, 'model': 'gpt-6.1-sol',
              'model_tokens': None, 'model_cost_usd': None,
              'scientific_job_executed': False}
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    broad = [p for p, v in tree.items() if (p.startswith(('jobs/', '.github/', 'HANDOFF/')) or '/' not in p) and v['oid'] not in local]
    if broad and not projection:
        raise RuntimeError(f'Old broad checkout needs {len(broad)} missing local paths; no bodies fetched. First: {broad[:5]}')
    SCRATCH.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='matched-', dir=SCRATCH) as tmp:
        temp = Path(tmp)
        pool = source
        ref = pinned
        if projection:
            pool = temp / 'projection'
            isolated(source, pool, pinned)
            index = temp / 'projection-index'
            env = {**ENV, 'GIT_INDEX_FILE': str(index)}
            git(pool, 'read-tree', '--empty', env=env)
            rows = [f"{v['mode']} blob {v['oid']}\t{p}\0" for p, v in sorted(tree.items()) if v['oid'] in local]
            git(pool, 'update-index', '-z', '--index-info', data=''.join(rows).encode(), env=env)
            treeid = git(pool, 'write-tree', env=env).decode().strip()
            ref = git(pool, 'commit-tree', treeid, data=b'Exact available production body projection\n').decode().strip()
            report['projection_commit'] = ref
            report['omitted_missing_paths'] = sum(v['oid'] not in local for v in tree.values())
        before, after = temp / 'old', temp / 'repaired'
        isolated(pool, before, ref)
        isolated(pool, after, ref)
        # Read the workflow blob from local objects without a broad checkout.
        flow = git(pool, 'show', f'{ref}:.github/workflows/run-jobs.yml').decode()
        block = flow.split('sparse-checkout: |', 1)[1].split('\n\n', 1)[0]
        rules = '\n'.join(x.strip() for x in block.splitlines() if x.strip()) + '\n'
        start = time.perf_counter()
        git(before, 'sparse-checkout', 'init', '--cone')
        git(before, 'sparse-checkout', 'set', '.github', 'jobs', 'HANDOFF')
        git(before, 'checkout', '-f', '--detach', ref)
        f_old = module(before, 'result_freshness')
        with cwd(before):
            f_old.prepare(NAME)
            old_manifest = f_old.working(f_old.scope(NAME))
        old_seconds = time.perf_counter() - start
        old_disk = disk(before)
        start = time.perf_counter()
        git(after, 'sparse-checkout', 'init', '--no-cone')
        git(after, 'sparse-checkout', 'set', '--no-cone', '--stdin', data=rules.encode())
        git(after, 'checkout', '-f', '--detach', ref)
        m = module(after, 'materialize_job_inputs')
        with cwd(after):
            receipt = m.materialize([NAME])
            closure, _, _ = m.input_closure([NAME])
            f_new = module(after, 'result_freshness')
            new_manifest = f_new.working(f_new.scope(NAME))
        new_seconds = time.perf_counter() - start
        report['narrow_status'] = ('blocked_certificate_fallback' if receipt['compatibility_fallback_jobs'] else 'audited_narrow')
        hashes = {p: {'oid': v.split(':')[1], 'old_matches': tracked_equal(before, p, v),
                      'repaired_matches': tracked_equal(after, p, v)} for p, v in sorted(closure.items())}
        if not all(v['old_matches'] and v['repaired_matches'] for v in hashes.values()):
            raise AssertionError('Required closure bytes differ or are absent')
        if old_manifest != new_manifest:
            raise AssertionError('Freshness manifests differ')
        after_disk = disk(after)
        # Import the actual tracker + native sibling imports without main().
        for root in (before, after):
            cmd(root, sys.executable, '-B', '-c', "import sys;sys.path.insert(0,'jobs/readiness-tracker');import tracker;assert tracker.W and tracker.F")
        native_results = ({'old': native_probe(before), 'repaired': native_probe(after)} if native_probe else {})
        failure = {}
        if fixture_failure:
            prior = (after / f'jobs/{NAME}/output/PRIOR.txt').read_bytes()
            env = {**ENV, 'JOBS': NAME, 'GITHUB_RUN_ID': 'shape-fixture',
                   'GITHUB_RUN_ATTEMPT': '1', 'GITHUB_SHA': ref,
                   'GITHUB_REF_NAME': 'shape-fixture', 'TRIGGER': 'fixture'}
            attempted = subprocess.run([sys.executable, '-B', '.github/scripts/run_jobs.py'],
                cwd=after, env=env, capture_output=True)
            status = json.loads((after / f'jobs/{NAME}/output/STATUS.json').read_text())
            attempt = after / f'jobs/_attempts/{NAME}/shape-fixture-1'
            attempt_status = json.loads((attempt / 'STATUS.json').read_text())
            failure = {'runner_exit': attempted.returncode, 'prior_status': status['result'],
                'prior_bytes_equal': prior == (after / f'jobs/{NAME}/output/PRIOR.txt').read_bytes(),
                'attempt_status': attempt_status['result'],
                'candidate_retained': (attempt / 'CANDIDATE.txt').exists()}
            if failure != {'runner_exit': 1, 'prior_status': 'succeeded',
                'prior_bytes_equal': True, 'attempt_status': 'failed', 'candidate_retained': True}:
                raise AssertionError(failure)
        report.update({'native_consumer_probe': native_results, 'failure_after_prior_success': failure, 'comparison_pin': ref, 'same_required_bytes': True,
                       'freshness_manifest_equal': True,
                       'freshness_input_sha256': f_new.digest(new_manifest),
                       'required_file_hashes': hashes,
                       'old': {**tally_disk(old_disk), 'elapsed_seconds': old_seconds},
                       'repaired': {**tally_disk(after_disk), 'elapsed_seconds': new_seconds},
                       'materializer_receipt': receipt,
                       'actual_tracker_and_native_imports': 'passed in both matched worktrees',
                       'working_changes': mutations(after, temp),
                       'condition': 'same local object pool; no remotes; no job cache; autocrlf=false',
                       'limits': 'Local warm-object worktree materialization. No cold transfer, GitHub startup, model token/cost, legal review or scientific readiness saving measured.'})
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'required_file_hashes'}, indent=2))
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, default=Path.cwd())
    p.add_argument('--receipt', type=Path, required=True)
    p.add_argument('--local-projection', action='store_true')
    a = p.parse_args()
    a.receipt.parent.mkdir(parents=True, exist_ok=True)
    try:
        run(a.source.resolve(), a.receipt.resolve(), a.local_projection)
    except Exception as e:
        report = json.loads(a.receipt.read_text()) if a.receipt.exists() else {'schema': 1}
        report.update({'result': 'blocked', 'error': str(e), 'selected_jobs': [NAME],
            'scientific_job_executed': False,
            'limits': 'No successful production materialization claimed; missing objects were not fetched.'})
        a.receipt.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
        raise
