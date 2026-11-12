"""Old (origin/main) vs fixed target_mentions on the same real pairs. The old code runs in a child that is
killed when one call exceeds LIMIT seconds; that pair is recorded as old_timeout."""
import sys, json, pickle, time, subprocess, os
from pathlib import Path
D = Path(__file__).parent; REPO = Path(sys.argv[1]).resolve(); LIMIT = float(sys.argv[2])
if len(sys.argv) > 3 and sys.argv[3] == 'child':
    which, start = sys.argv[4], int(sys.argv[5])
    sys.path.insert(0, str(REPO / 'jobs/claim-kit'))
    if which == 'old': sys.path.insert(0, str(D / 'oldkit'))
    import build
    assert (which == 'old') == ('oldkit' in build.__file__), build.__file__
    data = pickle.load(open(D / 'census_pairs.pkl', 'rb'))
    out = open(D / f'cres_{which}.jsonl', 'a')
    sk = D / 'skip_census.txt'; skip = set(sk.read_text().split()) if sk.exists() else set()
    for i in range(start, len(data['work'])):
        t, a, dt, ag = data['work'][i]
        if a in skip:
            out.write(json.dumps([i, 'old_timeout', 0]) + '\n'); out.flush(); continue
        s = time.monotonic(); r = build.target_mentions(t, data['texts'][a], dt, ag)
        out.write(json.dumps([i, r, round(time.monotonic() - s, 4)]) + '\n'); out.flush()
    sys.exit(0)
n = len(pickle.load(open(D / 'census_pairs.pkl', 'rb'))['work'])
for which in ('new', 'old'):
    f = D / f'cres_{which}.jsonl'
    if f.exists(): f.unlink()
    start = 0
    while start < n:
        p = subprocess.Popen([sys.executable, '-I', __file__, str(REPO), str(LIMIT), 'child', which, str(start)])
        last_count, last_t = -1, time.monotonic()
        while p.poll() is None:
            time.sleep(1)
            c = sum(1 for _ in open(f)) if f.exists() else 0
            if c != last_count: last_count, last_t = c, time.monotonic()
            elif time.monotonic() - last_t > LIMIT + (90 if c == 0 or c == start else 0):
                p.kill(); p.wait(); break
        done = sum(1 for _ in open(f)) if f.exists() else 0
        if done >= n: break
        with open(f, 'a') as fh: fh.write(json.dumps([done, 'old_timeout', LIMIT]) + '\n')
        print(which, 'timeout at pair', done, flush=True)
        start = done + 1
    print(which, 'finished', flush=True)
