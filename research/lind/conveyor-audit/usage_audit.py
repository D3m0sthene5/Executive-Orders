"""Deterministic usage accounting for one Claude Code transcript (no model calls).

Each API request is counted once: the CLI writes one assistant record per content block, all carrying the same
message id and identical usage, so records are deduplicated by message id. Per request, the prompt is
input_tokens (uncached) + cache_read_input_tokens + cache_creation_input_tokens; these are per-request token counts,
not running sums. Prices: jobs/necker-costs/PRICES.json (API list price; not a bill under a subscription).

usage:  python3 -I usage_audit.py TRANSCRIPT.jsonl START END [START END ...]   (ISO UTC, e.g. 2026-11-12T20:41)
        add --calls to print one line per request (time, prompt k-tokens, cost, tool description).
"""
import json, re, statistics, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PRICES = json.loads((REPO / 'jobs/necker-costs/PRICES.json').read_text())['models']


def price(model):
    for p in PRICES:
        if re.match(p['match'], model or ''):
            return p
    raise SystemExit('no price for ' + str(model))


def requests(path):
    seen = {}
    for line in open(path, encoding='utf-8'):
        try:
            d = json.loads(line)
        except ValueError:
            continue                       # a partly written last line of a live transcript
        if d.get('type') != 'assistant' or d.get('isSidechain'):
            continue
        m = d['message']
        r = seen.setdefault(m['id'], {'t': d['timestamp'], 'model': m.get('model'), 'u': m.get('usage') or {},
                                      'desc': []})
        for c in m.get('content') or []:
            if c.get('type') == 'tool_use':
                inp = c.get('input') or {}
                r['desc'].append(c['name'] + ': ' + str(inp.get('description') or inp.get('file_path') or
                                                        inp.get('pattern') or '')[:70])
    return sorted(seen.values(), key=lambda r: r['t'])


def cost(r):
    u, p = r['u'], price(r['model'])
    cc = u.get('cache_creation') or {}
    w5, w1 = cc.get('ephemeral_5m_input_tokens'), cc.get('ephemeral_1h_input_tokens')
    if w5 is None and w1 is None:
        w5, w1 = u.get('cache_creation_input_tokens', 0), 0
    parts = {'input': u.get('input_tokens', 0) * p['input'], 'cache_read': u.get('cache_read_input_tokens', 0) * p['cache_read'],
             'cache_write': w5 * p['cache_write_5m'] + w1 * p['cache_write_1h'], 'output': u.get('output_tokens', 0) * p['output']}
    return {k: v / 1e6 for k, v in parts.items()}


def window(reqs, a, b, show):
    rs = [r for r in reqs if a <= r['t'][:16] < b]
    if not rs:
        return print(a, b, 'no requests')
    tok = {k: sum(r['u'].get(k, 0) for r in rs) for k in
           ('input_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens', 'output_tokens')}
    prompt = [r['u'].get('input_tokens', 0) + r['u'].get('cache_read_input_tokens', 0) +
              r['u'].get('cache_creation_input_tokens', 0) for r in rs]
    cs = [cost(r) for r in rs]
    usd = {k: round(sum(c[k] for c in cs), 2) for k in cs[0]}
    print(json.dumps({'window': [a, b], 'requests': len(rs), 'tokens_summed': tok,
                      'prompt_per_request_k': {'mean': round(statistics.mean(prompt) / 1e3), 'median':
                                               round(statistics.median(prompt) / 1e3), 'min': round(min(prompt) / 1e3),
                                               'max': round(max(prompt) / 1e3)},
                      'uncached_share_of_prompt': round(tok['input_tokens'] / sum(prompt), 6),
                      'list_usd': usd, 'list_usd_total': round(sum(usd.values()), 2)}))
    if show:
        for r, c, n in zip(rs, cs, prompt):
            print(r['t'][11:19], f'{n/1e3:5.0f}k', f'${sum(c.values()):.3f}', ' | '.join(r['desc']) or '(text)')


if __name__ == '__main__':
    args = [x for x in sys.argv[1:] if x != '--calls']
    reqs = requests(args[0])
    for i in range(1, len(args), 2):
        window(reqs, args[i], args[i + 1], '--calls' in sys.argv)
