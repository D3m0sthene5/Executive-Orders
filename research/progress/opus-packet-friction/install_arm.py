"""Install a code arm into an isolated replay tree without touching shared inodes.

`base` leaves the tree's own code. `fix` applies the branch diff (BASE_REF..WORKTREE, limited to
jobs/claim-kit and jobs/valla, tests and outputs excluded) onto the tree's files: each target is
unlinked and rewritten, then `git apply` patches it in place. Refuses to touch any claim-kit compiler
fingerprint file, so compiled outputs stay valid for undecided preparation.

Usage: python3 install_arm.py TREE fix [--only completion.py ...] [--base-ref origin/main] [--branch DIR]
"""
import argparse
import json
from pathlib import Path
import subprocess

COMPILER = {'segment.py', 'act_overrides.py', 'assemble.py', 'build.py', 'current_evidence.py', 'excavate.py',
            'factual_events.py', 'inputs.py', 'lifecycle_obligations.py', 'population.py', 'working_text.py'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('tree'); ap.add_argument('arm', choices=('base', 'fix'))
    ap.add_argument('--only', nargs='*'); ap.add_argument('--base-ref', default='origin/main')
    ap.add_argument('--branch', default=str(Path(__file__).resolve().parents[3]))
    a = ap.parse_args()
    tree = Path(a.tree).resolve(); branch = Path(a.branch)
    if a.arm == 'base':
        print(json.dumps({'arm': 'base', 'files': []})); return
    names = subprocess.run(['git', 'diff', '--name-only', a.base_ref, '--', 'jobs/claim-kit/*.py', 'jobs/valla/*.py'],
                           cwd=branch, check=True, capture_output=True, text=True).stdout.split()
    untracked = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard', '--', 'jobs/claim-kit/*.py', 'jobs/valla/*.py'],
                               cwd=branch, check=True, capture_output=True, text=True).stdout.split()
    files = sorted(n for n in set(names) | set(untracked) if not Path(n).name.startswith('test_'))
    if a.only:
        files = [f for f in files if Path(f).name in a.only]
    bad = [f for f in files if Path(f).name in COMPILER]
    if bad:
        raise SystemExit('refusing compiler fingerprint files: ' + ', '.join(bad))
    installed = []
    for rel in files:
        target = tree / rel
        if rel in untracked:
            raw = (branch / rel).read_bytes()
        else:
            raw = target.read_bytes() if target.exists() else b''
        if target.exists():
            target.unlink()
        target.write_bytes(raw)
        if rel not in untracked:
            patch = subprocess.run(['git', 'diff', a.base_ref, '--', rel], cwd=branch, check=True, capture_output=True).stdout
            subprocess.run(['git', 'apply', '--unidiff-zero', '-'], cwd=tree, input=patch, check=True)
        installed.append(rel)
    print(json.dumps({'arm': 'fix', 'base_ref': a.base_ref, 'files': installed}))


if __name__ == '__main__':
    main()
