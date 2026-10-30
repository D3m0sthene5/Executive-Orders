"""Reconstruct the canonical-claims and NRA research state seen by a saved completion run (from its INPUTS.json)."""
import json, os, shutil, stat, sys, hashlib
from pathlib import Path
MAIN = Path('/home/user/Executive-Orders'); NRA = 'research/excavator/claude-nira-sweep-2026-10-29'
tree = Path(sys.argv[1]); complete_dir = sys.argv[2]   # e.g. t6/packet/supp/complete-v1
def put(rel, raw):
    p = tree / rel
    if p.exists(): p.unlink()
    p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(raw); os.chmod(p, 0o444)
sha = lambda b: hashlib.sha256(b).hexdigest()
copied = 0
for root, dirs, files in os.walk(MAIN / NRA):
    dirs[:] = [d for d in dirs if not d.startswith('complete-v')]
    for f in files:
        src = Path(root) / f; rel = src.relative_to(MAIN).as_posix(); put(rel, src.read_bytes()); copied += 1
inputs = json.loads((MAIN / NRA / complete_dir / 'INPUTS.json').read_bytes())
want = inputs['file_sets']['research/readiness/claims/*.jsonl']
have = sorted(p.relative_to(tree).as_posix() for p in (tree / 'research/readiness/claims').glob('*.jsonl'))
for rel in set(have) - set(want): (tree / rel).unlink()
for rel in set(want) - set(have): put(rel, (MAIN / rel).read_bytes())
bad = {rel: 'missing' if not (tree / rel).exists() else 'differs' for rel, s in inputs['dependency_sha256'].items()
       if not (tree / rel).exists() or sha((tree / rel).read_bytes()) != s}
print(json.dumps({'copied_nra_files': copied, 'claims_files': len(want), 'pin_mismatches': bad}, indent=1))
