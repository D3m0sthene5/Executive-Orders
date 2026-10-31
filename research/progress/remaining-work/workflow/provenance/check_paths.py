"""Check every repository link the Workflow tab will render against the pinned commit's tree.

Parses citations exactly as the page's srcLink() does (split on ';', first word of each part; http links and
commit shas handled separately) and resolves each path with `git cat-file -e <pin>:<path>`. Exit 1 on any
missing target. Usage: python3 check_paths.py [WORKFLOW_NODES.json]
"""
import json, re, subprocess, sys
from pathlib import Path

p = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / 'WORKFLOW_NODES.json'
nodes = json.load(open(p, encoding='utf-8'))
PATH = re.compile(r'^([A-Za-z0-9_.\-/]+?)(?::(\d+)(?:-(\d+))?)?$')


def citations(n):
    for k in ('results', 'history'):
        for it in n.get(k, []):
            yield it.get('source', '')
    for s in n.get('sources', []):
        yield s.get('url') or s.get('path', '')
    yield n.get('namesake_evidence', '')
    yield from n.get('jobs', [])


checked, bad, shas = set(), [], set()
for n in nodes:
    pin = n.get('source_pin') or 'HEAD'
    for c in citations(n):
        for part in [x.strip() for x in str(c or '').split(';') if x.strip()]:
            w = part.split()[0]
            if w.startswith('http'):
                continue
            if re.fullmatch(r'[0-9a-f]{7,40}', w):
                shas.add(w); continue
            m = PATH.match(w)
            if not m or ('/' not in m[1] and '.' not in m[1]):
                continue  # rendered as plain text, not a link
            key = (pin, m[1])
            if key in checked:
                continue
            checked.add(key)
            if subprocess.run(['git', 'cat-file', '-e', f'{pin}:{m[1]}'], capture_output=True).returncode:
                bad.append((n['id'], m[1]))
for s in sorted(shas):
    if subprocess.run(['git', 'cat-file', '-e', s], capture_output=True).returncode:
        bad.append(('commit', s))
print(json.dumps({'distinct_paths_checked': len(checked), 'commit_ids_checked': len(shas), 'missing': bad}, indent=1))
sys.exit(1 if bad else 0)
