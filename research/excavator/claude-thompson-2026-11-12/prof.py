import sys, time, collections, json
from pathlib import Path
repo = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(repo / 'jobs/claim-kit'))
import build
t = time.monotonic()
corpus = build.load_corpus(repo)
print('load_corpus %.1fs' % (time.monotonic() - t), flush=True)
universe = corpus['universe']
acting_rows = [r for r in corpus.get('acting_texts', []) if r.get('instrument_id') not in universe]
pairs = {(p['target_id'], p['actor_id'], p.get('parent_id')): p for p in corpus['pairs'] if p.get('target_id') in universe}
non = sorted([k for k in pairs if k[1] not in universe], key=lambda k: (k[1], k[0], str(k[2])))
print('pairs', len(pairs), 'non-census actor pairs', len(non), 'acting rows', len(acting_rows), flush=True)
t = time.monotonic()
sel, ref = build.select_acting_texts(repo, acting_rows, {a for _, a, _ in non})
print('select_acting_texts %.1fs selected %d refused %d' % (time.monotonic() - t, len(sel), len(ref)), flush=True)
slow = []; by_actor = collections.defaultdict(float); n = 0; t0 = time.monotonic()
budget = float(sys.argv[2]) if len(sys.argv) > 2 else 600
for target, actor, parent in non:
    ar = sel.get(actor)
    if ar is None: continue
    t = time.monotonic()
    build.target_mentions(target, ar['text'], None, actor.startswith('FRDOC:'))
    dt = time.monotonic() - t; n += 1
    by_actor[actor] += dt
    if dt > 1: slow.append((round(dt, 1), target, actor, len(ar['text'])))
    if time.monotonic() - t0 > budget:
        print('budget hit after', n, 'pairs'); break
print('timed %d pairs in %.1fs' % (n, time.monotonic() - t0))
print('slowest actors', sorted(((round(v, 1), a, len(sel[a]['text'])) for a, v in by_actor.items()), reverse=True)[:12])
print('slow calls', sorted(slow, reverse=True)[:12])
