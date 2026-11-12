import json, pickle, collections, sys
from pathlib import Path
D = Path(__file__).parent
data = pickle.load(open(D / 'census_pairs.pkl', 'rb')); W = data['work']; T = data['texts']
def load(f):
    r = {}
    for l in open(D / f):
        i, v, s = json.loads(l); r[i] = (v, s)
    return r
new, old = load('cres_new.jsonl'), load('cres_old.jsonl')
c = collections.Counter(); ex = []; old_t = 0.0; new_t = 0.0; slow_old = []
for i, (t, a, dt, ag) in enumerate(W):
    nv, ns = new[i]; ov, os_ = old.get(i, ('missing', 0))
    new_t += ns
    if ov == 'old_timeout': c['old_timeout'] += 1; slow_old.append((t, a)); continue
    if ov == 'missing': c['old_missing'] += 1; continue
    old_t += os_
    if os_ > 1: slow_old.append((t, a, round(os_, 1)))
    o = {tuple(x) for x in (ov or [])}; n = {tuple(x) for x in (nv or [])}
    if o == n: c['same'] += 1; continue
    lost, gained = o - n, n - o
    c['lost_spans_pairs' if lost else 'gained_only_pairs'] += 1
    c['lost_spans'] += len(lost); c['gained_spans'] += len(gained)
    if bool(o) != bool(n): c['named_changed_' + ('to_no' if o else 'to_yes')] += 1
    for s, e in sorted(lost)[:2]:
        ex.append((t, a, T[a][max(0, s - 160):e + 20].replace('\n', ' ')))
print(dict(c)); print('old seconds (finished calls) %.1f, new seconds %.1f' % (old_t, new_t))
print('old slow/timeouts', slow_old[:20])
for e in ex[:40]: print('LOST', e[0], e[1], '|', e[2])
