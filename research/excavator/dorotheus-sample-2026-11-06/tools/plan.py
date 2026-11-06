"""Dorotheus wave packet plan (coordinator tool, no legal judgment).
usage: python3 -I plan.py  -> writes /tmp/claude-0/dorotheus-wave/batches.json and tools/batches.json
Routes: ready -> ready_existing; owned by another agent -> nonresponse_dispatch (route_owner);
decided_not_ready (d*), YES probe (y*), undecided (u*): packets of <=6, sorted by era then number."""
import csv, json, re, sys
from pathlib import Path
REPO = Path('/home/user/Executive-Orders'); sys.path.insert(0, str(REPO / 'jobs/claim-kit'))
import batch
W = REPO / 'research/excavator/dorotheus-sample-2026-11-06'
S = list(csv.DictReader(open(W / 'SAMPLE.csv')))
D = json.load(open(REPO / 'research/excavator/dorotheus-yesprobe-2026-11-06/DRAW.json'))['draw']
own = batch.owners(REPO)
ERA = ['1862–1906', '1907–1936', '1937–1989', '1990–2026', 'Unknown date']
def num(i):
    m = re.match(r'EO:(\d+)', i); return (int(m.group(1)) if m else 10**9, i)
def chunk(ids, prefix):
    n = -(-len(ids) // 6); out = {}; a = 0
    for k in range(n):
        b = a + len(ids) // n + (1 if k < len(ids) % n else 0); out[f'{prefix}{k+1:02d}'] = ids[a:b]; a = b
    return out
pre = {}; groups = {'d': [], 'u': [], 'y': []}
for r in S:
    i = r['id']
    if r['group'] == 'ready': pre[i] = 'ready_existing'; continue
    if i in own: pre[i] = 'owned:' + own[i]['owner']; continue
    groups['d' if r['group'] == 'decided_not_ready' else 'u'].append((ERA.index(r['era']), num(i), i))
for i in D:
    if i in own: pre['Y|' + i] = 'owned:' + own[i]['owner']; continue
    groups['y'].append((0, num(i), i))
plan = {}
for p in 'duy':
    ids = [x[2] for x in sorted(groups[p])]
    if p == 'u':  # chunk within era so packets stay era-homogeneous
        for e in range(len(ERA)):
            sub = [x[2] for x in sorted(groups[p]) if x[0] == e]
            for k, v in chunk(sub, f'u{e}').items(): plan[k] = v
    else:
        plan.update(chunk(ids, p))
out = {'packets': plan, 'pre_routed': pre}
for f in (Path('/tmp/claude-0/dorotheus-wave/batches.json'), W / 'tools/batches.json'):
    f.write_text(json.dumps(out, indent=1) + '\n')
print({k: len(v) for k, v in plan.items()}, sum(map(len, plan.values())), pre)
