"""Dump the non-census acting-text pairs and their texts (as the build selects them) for an old/new comparison."""
import sys, json, pickle
from pathlib import Path
repo = Path(sys.argv[1]).resolve(); out = Path(sys.argv[2])
sys.path.insert(0, str(repo / 'jobs/claim-kit'))
import build
corpus = build.load_corpus(repo)
universe = corpus['universe']
acting_rows = [r for r in corpus.get('acting_texts', []) if r.get('instrument_id') not in universe]
pairs = {(p['target_id'], p['actor_id'], p.get('parent_id')): p for p in corpus['pairs'] if p.get('target_id') in universe}
non = sorted([k for k in pairs if k[1] not in universe], key=lambda k: (k[1], k[0], str(k[2])))
sel, _ = build.select_acting_texts(repo, acting_rows, {a for _, a, _ in non})
dates = {}
u = universe if isinstance(universe, dict) else {}
work = []
for t, a, p in non:
    if a in sel:
        d = (u.get(t) or {}).get('signing_date') if isinstance(u.get(t), dict) else None
        work.append((t, a, d, a.startswith('FRDOC:')))
texts = {a: sel[a]['text'] for _, a, _, _ in work}
pickle.dump({'work': work, 'texts': texts, 'universe_type': type(universe).__name__}, open(out, 'wb'))
print(len(work), 'pairs', len(texts), 'texts', sum(len(t) for t in texts.values()) // 1_000_000, 'M chars', type(universe).__name__)
