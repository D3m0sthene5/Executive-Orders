"""Resume the old-code run; after one call exceeds LIMIT seconds, record every remaining pair of that actor text as
old_timeout (the old code cannot finish that text in practice) and restart at the next actor."""
import sys, json, pickle, time, subprocess
from pathlib import Path
D = Path(__file__).parent; REPO = Path(sys.argv[1]).resolve(); LIMIT = float(sys.argv[2]); PKL, RES = sys.argv[3], sys.argv[4]
W = pickle.load(open(D / PKL, 'rb'))['work']; f = D / RES
child = D / ('compare.py' if PKL == 'pairs.pkl' else 'compare_census.py')
def count(): return sum(1 for _ in open(f)) if f.exists() else 0
start = count()
while start < len(W):
    p = subprocess.Popen([sys.executable, '-I', str(child), str(REPO), str(LIMIT), 'child', 'old', str(start)])
    last, t = count(), time.monotonic()
    while p.poll() is None:
        time.sleep(1); c = count()
        if c != last: last, t = c, time.monotonic()
        elif time.monotonic() - t > LIMIT + (90 if c == start else 0): p.kill(); p.wait(); break
    done = count()
    if done >= len(W): break
    actor = W[done][1]; j = done
    with open(f, 'a') as fh:
        while j < len(W) and W[j][1] == actor:
            fh.write(json.dumps([j, 'old_timeout', LIMIT]) + '\n'); j += 1
    if PKL != 'pairs.pkl':
        with open(D / 'skip_census.txt', 'a') as sk: sk.write(actor + '\n')
    print('old timeout on', actor, 'pairs', done, '-', j - 1, flush=True)
    start = j
print('old finished', flush=True)
