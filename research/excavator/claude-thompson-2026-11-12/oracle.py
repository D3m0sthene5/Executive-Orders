"""Independent check of the fixed citation-list pattern with GNU grep -E (a DFA engine that does not backtrack):
1. translate the OLD Python pattern to ERE; 2. validate grep against the old Python engine on windows from pairs
the old code finishes; 3. on windows from the 130 pairs the old code cannot finish, compare grep (old language)
with the fixed Python pattern. Each window is the 400 characters before a number hit, as target_mentions builds it."""
import sys, re, json, pickle, subprocess, random, collections
from pathlib import Path
D = Path(__file__).parent; REPO = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(REPO / 'jobs/claim-kit')); sys.path.insert(0, str(D / 'oldkit')); import build as old
assert 'oldkit' in old.__file__
import importlib.util
spec = importlib.util.spec_from_file_location('newb', REPO / 'jobs/claim-kit/build.py'); new = importlib.util.module_from_spec(spec); spec.loader.exec_module(new)
assert new._PRECEDES.pattern != old._PRECEDES.pattern
p = old._PRECEDES.pattern
ere = (p.replace('(?:', '(').replace(r'\x27', "'").replace(r'\d', '[0-9]').replace(r'\Z', '$')
         .replace(r'[ \t\n]', '[[:space:]]'))
assert '\\t' not in ere and '\\n' not in ere, ere
assert '(?' not in ere
def windows(pkl, res, want_timeout, cap=None, seed=1):
    data = pickle.load(open(D / pkl, 'rb')); W, T = data['work'], data['texts']
    old_res = {json.loads(l)[0]: json.loads(l)[1] for l in open(D / res)}
    idx = [i for i in range(len(W)) if (old_res.get(i) == 'old_timeout') == want_timeout]
    if cap: random.Random(seed).shuffle(idx); idx = idx[:cap]
    out = []
    for i in idx:
        t, a = W[i][0], W[i][1]
        m = re.fullmatch(r'EO:(\d+)([A-Za-z]?)', t)
        if not m: continue
        digits = m[1]; spaced = '|' + ' '.join(re.escape(ch) for ch in digits) if len(digits) >= 3 else ''
        number = '(?:' + re.escape(digits) + spaced + ')'
        text = T[a]
        for hit in re.finditer(r'(?<![\w.,/$§-])(?<!\d[ ])' + number + r'(?![ ]?\d|\w|[.,]\d)', text):
            s = hit.start(); a0 = max(0, s - 400)
            w = old._HYPHENATED.sub('', ('w' if a0 else '') + text[a0:s])
            out.append((t, a, ''.join('#' if ch.isspace() and ch not in ' \t\n' else ch for ch in w)))
    return out
def grep(ws):
    """(matched, start) per window from one grep -z -E -i -o -n run (leftmost match ends at $, so start = len - len(match))."""
    clean = [w.replace('\0', ' ') for w in ws]
    r = subprocess.run(['grep', '-z', '-E', '-i', '-o', '-n', ere], input='\0'.join(clean) + '\0', capture_output=True,
                       text=True, env={'LC_ALL': 'C.UTF-8'})
    if r.returncode not in (0, 1): raise RuntimeError(r.stderr)
    first = {}
    for rec in r.stdout.split('\0'):
        if not rec: continue
        n, _, m = rec.partition(':'); n = int(n) - 1
        first.setdefault(n, m)
    return [(True, len(clean[i]) - len(first[i])) if i in first else (False, None) for i in range(len(clean))]
def py(pat, w):
    m = pat.search(w); return (bool(m), m.start() if m else None)
# 1-2: validate grep against the old engine on finished pairs
val = windows('pairs.pkl', 'res_old.jsonl', False, cap=800) + windows('census_pairs.pkl', 'cres_old.jsonl', False, cap=1500)
g = grep([w for _, _, w in val]); c = collections.Counter(); bad = []
for (t, a, w), gr in zip(val, g):
    o = py(old._PRECEDES, w); c['agree' if o == gr else 'disagree'] += 1; c['old_match'] += o[0]
    if o != gr and len(bad) < 3: bad.append((t, a, o, gr, w[-120:]))
print('VALIDATION grep vs old Python on', len(val), 'windows from finished pairs:', dict(c)); [print('  ', b) for b in bad]
# 3: oracle on the timeout pairs
tw = windows('pairs.pkl', 'res_old.jsonl', True) + windows('census_pairs.pkl', 'cres_old.jsonl', True)
g = grep([w for _, _, w in tw]); c = collections.Counter(); bad = []
for (t, a, w), gr in zip(tw, g):
    n = py(new._PRECEDES, w); c['agree' if n == gr else 'disagree'] += 1; c['grep_match'] += gr[0]
    if n != gr and len(bad) < 5: bad.append((t, a, 'fixed', n, 'grep(old language)', gr, w[-160:]))
print('ORACLE fixed Python vs grep(old language) on', len(tw), 'windows from the 130 unfinishable pairs:', dict(c)); [print('  ', b) for b in bad]
