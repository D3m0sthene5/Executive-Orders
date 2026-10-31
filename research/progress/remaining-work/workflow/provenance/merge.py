"""Merge reader groups into WORKFLOW_NODES.json, apply coordinator overrides, verify Wikipedia titles."""
import json, re, sys, urllib.error, urllib.parse, urllib.request
from pathlib import Path
W = Path(__file__).resolve().parent  # the provenance folder; writes ../WORKFLOW_NODES.json
PIN = '88cef0253ed735b2a6e612770f25f9148641ce93'
nodes = []
for g in 'abcd':
    p = W / f'group_{g}.json'
    if p.exists():
        for n in json.load(open(p, encoding='utf-8')):
            n['_group'] = g; nodes.append(n)
ov = json.load(open(W / 'overrides.json', encoding='utf-8')) if (W / 'overrides.json').exists() else {}
aliases = ov.get('aliases', {})
drop = set(ov.get('drop', []))
# de-duplicate ids (first wins unless overridden)
seen, out = {}, []
for n in nodes:
    n['id'] = aliases.get(n['id'], n['id'])
    if n['id'] in drop: continue
    if n['id'] in seen:
        print('duplicate id', n['id'], 'groups', seen[n['id']]['_group'], n['_group'], file=sys.stderr); continue
    seen[n['id']] = n; out.append(n)
ids = set(seen)
DESCRIPTIVE = re.compile(r'^[a-z0-9]+(?:[-_][a-z0-9]+)+$')
for n in out:
    o = ov.get('nodes', {}).get(n['id'], {})
    ns = n.pop('namesake', {}) or {}
    text = (ns.get('text') or '').strip()
    low = text.lower()
    st = 'none' if (not text or low.startswith('undocumented') or low.startswith('none')) else 'documented'
    n['namesake_status'] = st
    n['namesake_text'] = text if st == 'documented' else ''
    n['namesake_evidence'] = ns.get('evidence', '') if st == 'documented' else ''
    n['_wiki_title'] = ns.get('wikipedia_title_unverified', '') if st == 'documented' else ''
    n['label'] = re.sub(r'\s*\([^()]*\)\s*$', '', n.get('name', '')).strip() or n.get('name', '')
    n.update({k: v for k, v in o.items() if k not in ('_wiki_title',)})
    if '_wiki_title' in o: n['_wiki_title'] = o['_wiki_title']
    n['feeds'] = [aliases.get(f, f) for f in n.get('feeds', [])]
    n['feeds'] = [f for f in n['feeds'] if f in ids and f != n['id']]
    n['source_pin'] = PIN
    n.setdefault('order', 70 if n.get('status_class') != 'current' else 50)
    n.pop('_group', None)
def _fix(src, fixes):
    if not src: return src
    toks = [t.strip() for t in str(src).split(';')]
    for k, t in enumerate(toks):
        for a, b in fixes:
            if t == a or t.startswith(a) and (len(t) == len(a) or t[len(a)] in ' :/(' or a.endswith('-') or a.endswith('/')):
                toks[k] = b + t[len(a):]; break
    return '; '.join(toks)
for n in out:
    fixes = ov.get('source_fixes', {}).get(n['id'], [])
    if fixes:
        for key in ('results', 'history'):
            for it in n.get(key, []): it['source'] = _fix(it.get('source', ''), fixes)
        for s in n.get('sources', []):
            if s.get('path'): s['path'] = _fix(s['path'], fixes)
        n['namesake_evidence'] = _fix(n.get('namesake_evidence', ''), fixes)
    for rep in ov.get('result_replace', {}).get(n['id'], []):
        new_res = []
        for it in n.get('results', []):
            new_res += rep['with'] if rep['match'] in it.get('text', '') else [it]
        n['results'] = new_res
for n in out:
    if n['id'] == 'later-events-status-history-current-law':
        n['jobs'] = [j for j in n.get('jobs', []) if 'ofr-codification' not in j]
# extra nodes
for n in ov.get('extra', []):
    n.setdefault('source_pin', PIN); n.setdefault('order', 50); out.append(n)
# verify Wikipedia titles in batches
titles = sorted({n['_wiki_title'] for n in out if n.get('_wiki_title')})
cache_p = W / 'wiki_cache.json'
canon = json.load(open(cache_p)) if cache_p.exists() else {}
todo = [t for t in titles if t not in canon]
for i in range(0, len(todo), 40):
    q = urllib.parse.urlencode({'action': 'query', 'titles': '|'.join(todo[i:i+40]), 'redirects': 1, 'format': 'json'})
    import time
    for wait in (0, 20, 60, 120, 240):
        time.sleep(wait)
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request('https://en.wikipedia.org/w/api.php?' + q, headers={'User-Agent': 'eo-workflow-check/1.0 (executive-orders dashboard; one batched lookup)'}), timeout=30))['query']
            break
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            print('rate limited; waiting', file=sys.stderr)
    else:
        sys.exit('Wikipedia kept rate-limiting; try later')
    norm = {x['from']: x['to'] for x in r.get('normalized', [])}
    red = {x['from']: x['to'] for x in r.get('redirects', [])}
    ok = {p['title'] for p in r['pages'].values() if 'missing' not in p and 'invalid' not in p}
    for t in todo[i:i+40]:
        f = red.get(norm.get(t, t), norm.get(t, t))
        canon[t] = f if f in ok else None
json.dump(canon, open(cache_p, 'w'), indent=1)
bad = []
for n in out:
    t = n.pop('_wiki_title', '')
    if t:
        c = canon.get(t)
        if c:
            n['wikipedia_url'] = 'https://en.wikipedia.org/wiki/' + urllib.parse.quote(c.replace(' ', '_'), safe="_(),'-.")
            if not n.get('namesake_short'): n['namesake_short'] = 'after ' + c
        else:
            bad.append((n['id'], t)); n['wikipedia_url'] = ''
    else:
        n.setdefault('wikipedia_url', '')
    if n.get('namesake_status') == 'inferred' and n.get('namesake_short', '').startswith('after '):
        n['namesake_short'] = 'probably after ' + n['namesake_short'][6:]
json.dump(out, open(W.parent / 'WORKFLOW_NODES.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(out), 'nodes;', 'unresolved wikipedia:', bad)
dang = sorted({f for n in nodes for f in n.get('feeds', []) if aliases.get(f, f) not in ids})
print('dangling feeds dropped:', dang)
