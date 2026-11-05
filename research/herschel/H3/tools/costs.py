"""Filter sessions.py output to H3 agents and price it with jobs/bentham/measure.py's table (coordinator tool).
usage: python3 -I costs.py SESSIONS_OUT_DIR"""
import csv, json, sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, '/home/claude/executive-orders/jobs/bentham')
from measure import usd, PRICE_TABLE
H = Path('/home/claude/executive-orders/research/herschel/H3')
src = Path(sys.argv[1])
rows = [r for r in csv.DictReader(open(src / 'AGENT_USAGE.csv')) if r['phase'] != 'not_H3']
(H / 'telemetry').mkdir(exist_ok=True)
with open(H / 'telemetry/AGENT_USAGE.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
trace = [json.loads(l) for l in open(H / 'TRACE.jsonl')]
sid2w = {}
S = Path('/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H3')
for p in (S / 'run').glob('*.json'):
    try: sid2w.setdefault(json.load(open(p))['session_id'], p.stem.replace('-reveal', ''))
    except Exception: pass
I = lambda v: int(v or 0)
by_step = defaultdict(lambda: {'agents': 0, 'usd': 0.0, 'fresh_input': 0, 'cache_read': 0, 'cache_write': 0, 'output': 0, 'wall_seconds': 0.0})
per_worker = {}
for r in rows:
    fam = 'opus' if 'opus' in r['model'] else 'sonnet'
    t = {'fresh_input': I(r['fresh_input']), 'cache_read': I(r['cache_read']), 'output': I(r['output']),
         'cache_write': I(r['cache_write_5m']) + I(r['cache_write_1h']) + I(r['cache_write_unclassified'])}
    u = usd(fam, t)
    b = by_step[r['phase']]; b['agents'] += 1; b['usd'] += u; b['wall_seconds'] += float(r['wall_seconds'] or 0)
    for k in t: b[k] += t[k]
    w = sid2w.get(r['session_id'], 'H3-coordinator' if r['phase'] == 'coordination' else r['agent_id'])
    per_worker[w] = {'phase': r['phase'], 'model': r['model'], 'usd': round(u, 4), 'tokens': t, 'wall_seconds': float(r['wall_seconds'] or 0)}
orders_by_step = defaultdict(set)
for t in trace:
    orders_by_step[t['step']] |= set(t['orders'])
out = {'schema': 'herschel-h3-costs/v1', 'price_table': PRICE_TABLE, 'pricing': 'jobs/bentham/measure.py usd(); cache_write = 5m + 1h + unclassified writes',
       'since': '2026-11-05T23:24:00Z', 'by_step': {}, 'per_worker': per_worker}
for s, b in by_step.items():
    n = len(orders_by_step.get(s, ())) or None
    b = dict(b); b['usd'] = round(b['usd'], 4); b['orders_worked'] = n
    b['usd_per_order'] = round(b['usd'] / n, 4) if n else None
    b['tokens_per_order'] = {k: round(b[k] / n) for k in ('fresh_input', 'cache_read', 'cache_write', 'output')} if n else None
    out['by_step'][s] = b
out['total_usd'] = round(sum(b['usd'] for b in by_step.values()), 4)
json.dump(out, open(H / 'telemetry/COSTS.json', 'w'), indent=1)
print(json.dumps({s: (b['usd'], b['orders_worked'], b['usd_per_order']) for s, b in out['by_step'].items()}, indent=0), out['total_usd'])
