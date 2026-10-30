"""Reproduce pinned full-tree/scoped metadata parity; never read source bodies."""
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import time
import types

ROOT = Path(__file__).resolve().parents[4]
BASE = 'f9c6d806ad059dcad7875ab3708715f20ea386df'
sys.path.insert(0, str(ROOT / '.github/scripts'))
import result_freshness as repaired

old = types.ModuleType('baseline_freshness')
source = subprocess.check_output(['git', 'show', BASE + ':.github/scripts/result_freshness.py'], cwd=ROOT)
exec(compile(source, '<pinned baseline freshness>', 'exec'), old.__dict__)
# Read declarations from the same pinned tree in both implementations.
def pinned_lines(path):
    result = subprocess.run(['git', 'show', BASE + ':' + str(path)], cwd=ROOT, capture_output=True)
    if result.returncode:
        return []
    return [s for row in result.stdout.decode().splitlines() if (s := row.split('#', 1)[0].strip())]
old.lines = pinned_lines
rows = []
for name in ('example-hello', 'kean', 'fr-originals', 'claim-kit', 'daily-digest'):
    declared = old.scope(name)
    t = time.perf_counter()
    baseline = old.select(old.tree(BASE), declared)
    before = time.perf_counter() - t
    t = time.perf_counter()
    after = repaired.tree(BASE, declared)
    elapsed = time.perf_counter() - t
    assert baseline == after, name
    rows.append({'job': name, 'selected_files': len(after), 'identical_entries': True,
                 'inputs_sha256': repaired.digest(after), 'baseline_elapsed_seconds': before,
                 'scoped_elapsed_seconds': elapsed})
print(json.dumps({'baseline_commit': BASE, 'network_source_requests': 0,
                  'notice': 'Local Git metadata timing; not remote bytes or workflow startup.',
                  'results': rows}, indent=2))
