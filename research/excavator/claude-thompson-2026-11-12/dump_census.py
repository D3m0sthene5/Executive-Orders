"""Census actor pairs (actor in the census): the actor's best-ranked readable held text, as the build ranks it."""
import sys, pickle
from pathlib import Path
repo = Path(sys.argv[1]).resolve(); out = Path(sys.argv[2])
sys.path.insert(0, str(repo / 'jobs/claim-kit'))
import build
corpus = build.load_corpus(repo)
universe = corpus['universe']
registered = {tuple(k) for k in corpus.get('registered_working_texts', [])}
by = {}
for r in sorted(corpus['texts'], key=lambda r: (build.rank_text(r, registered), r['instrument_id'])):
    by.setdefault(r['instrument_id'], []).append(r)
pairs = sorted({(p['target_id'], p['actor_id']) for p in corpus['pairs'] if p.get('target_id') in universe and p.get('actor_id') in universe and p['target_id'] != p['actor_id']})
texts, work = {}, []
for t, a in pairs:
    if a not in texts:
        for r in by.get(a, []):
            try: texts[a] = build.safe_read(repo, r['text_path']); break
            except Exception: continue
    if a in texts: work.append((t, a, None, False))
pickle.dump({'work': work, 'texts': texts}, open(out, 'wb'))
print(len(pairs), 'census pairs;', len(work), 'with a held actor text;', len(texts), 'texts', sum(map(len, texts.values())) // 1_000_000, 'M chars')
