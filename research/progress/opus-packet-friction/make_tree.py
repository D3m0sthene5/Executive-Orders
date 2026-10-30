"""Isolated replay tree: hardlinked copy of the pristine main checkout, own git worktree index,
rewound to COMMIT by writing (never editing in place) the files that differ. Files are made read-only
so any in-place write fails loudly instead of altering the shared inode."""
import os, sys, subprocess, shutil, stat
from pathlib import Path
SRC = Path('/home/user/Executive-Orders')
dst = Path(sys.argv[1]); commit = sys.argv[2]
def git(*a, cwd=SRC, **k): return subprocess.run(['git', *a], cwd=cwd, check=True, capture_output=True, **k).stdout
head = git('rev-parse', 'HEAD').decode().strip()
assert not git('status', '--porcelain', '--untracked-files=no').strip(), 'pristine checkout must be clean'
git('worktree', 'add', '--no-checkout', '--detach', str(dst), commit)
for entry in SRC.iterdir():
    if entry.name == '.git': continue
    subprocess.run(['cp', '-al', str(entry), str(dst / entry.name)], check=True)
changed = 0
if git('rev-parse', commit + '^{commit}').decode().strip() != head:
    out = git('diff', '--name-status', '--no-renames', '-z', commit, head).split(b'\0')
    items = [x.decode() for x in out if x]
    for status, path in zip(items[0::2], items[1::2]):
        p = dst / path
        if p.exists() or p.is_symlink(): p.unlink()
        if status in ('M', 'D', 'T'):
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(git('show', f'{commit}:{path}'))
        changed += 1
git('reset', '-q', commit, cwd=dst)
n = 0
for root, dirs, files in os.walk(dst):
    if '.git' in dirs and Path(root) == dst: pass
    for f in files:
        fp = os.path.join(root, f)
        if not os.path.islink(fp):
            os.chmod(fp, os.stat(fp).st_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)); n += 1
print({'tree': str(dst), 'commit': commit, 'rewound_paths': changed, 'readonly_files': n})
