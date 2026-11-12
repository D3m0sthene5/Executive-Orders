import sys, json, pickle, time, collections
from pathlib import Path
D = Path(__file__).parent; REPO = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(REPO / 'jobs/claim-kit')); sys.path.insert(0, str(D / 'v2kit')); import build
assert 'v2kit' in build.__file__
for pkl, oldf, newf in (('pairs.pkl', 'res_old.jsonl', 'res_new.jsonl'), ('census_pairs.pkl', 'cres_old.jsonl', 'cres_new.jsonl')):
    data = pickle.load(open(D / pkl, 'rb')); W, T = data['work'], data['texts']
    old = {json.loads(l)[0]: json.loads(l)[1] for l in open(D / oldf)}
    c = collections.Counter(); tot = 0; worst = (0, None); diffs = []; v2res = {}
    for i, (t, a, dt, ag) in enumerate(W):
        s = time.monotonic(); r = build.target_mentions(t, T[a], dt, ag); e = time.monotonic() - s
        tot += e; worst = max(worst, (e, (t, a))); v2res[i] = r
        o = old.get(i)
        if o == 'old_timeout': c['old_timeout'] += 1; continue
        if {tuple(x) for x in (o or [])} == {tuple(x) for x in (r or [])}: c['same_as_old'] += 1
        else: c['differs_from_old'] += 1; diffs.append((t, a, o, r))
    json.dump({str(k): v for k, v in v2res.items()}, open(D / ('v2_' + pkl.replace('.pkl', '.json')), 'w'))
    print(pkl, dict(c), 'v2 total %.1fs, slowest %.3fs %s' % (tot, worst[0], worst[1]))
    for d in diffs[:10]: print('  DIFF', d[0], d[1], 'old', d[2], 'v2', d[3])
