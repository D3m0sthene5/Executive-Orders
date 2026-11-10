"""Papinian: list-price dollars of one Agent-tool worker transcript (coordinator tool; arithmetic only).
usage: python -I cost.py LABEL ROLE TRANSCRIPT.jsonl [--log COSTS.log]
Takes the last usage object per message id (as jobs/bentham/sessions.py does), prices each call by its model with
jobs/necker-costs/PRICES.json (1-hour and 5-minute cache writes separately), and appends one line to COSTS.log:
    LABEL agent-tool ROLE MODEL cost USD calls N in N cache_read N cache_write N out N
The `claude -p` cost line format of worker.py is not available (the headless CLI is not logged in on this PC)."""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
PRICES = json.loads((REPO / 'jobs/necker-costs/PRICES.json').read_text(encoding='utf-8'))['models']


def rate(model):
    for m in PRICES:
        if re.match(m['match'], model or ''):
            return m
    return None


def main(label, role, path, *rest):
    last, models = {}, {}
    for line in open(path, encoding='utf-8'):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        msg = e.get('message') if isinstance(e, dict) else None
        if isinstance(msg, dict) and isinstance(msg.get('usage'), dict) and msg.get('id'):
            last[msg['id']] = msg['usage']
            models[msg['id']] = msg.get('model')
    tot = dict(inp=0, cr=0, cw=0, out=0)
    usd = 0.0
    for mid, u in last.items():
        m = rate(models[mid])
        cc = u.get('cache_creation') or {}
        w1, w5 = cc.get('ephemeral_1h_input_tokens', 0) or 0, cc.get('ephemeral_5m_input_tokens', 0) or 0
        wu = max((u.get('cache_creation_input_tokens') or 0) - w1 - w5, 0)
        tot['inp'] += u.get('input_tokens') or 0
        tot['cr'] += u.get('cache_read_input_tokens') or 0
        tot['cw'] += w1 + w5 + wu
        tot['out'] += u.get('output_tokens') or 0
        if m:
            usd += ((u.get('input_tokens') or 0) * m['input'] + (u.get('cache_read_input_tokens') or 0) * m['cache_read']
                    + w1 * m['cache_write_1h'] + (w5 + wu) * m['cache_write_5m'] + (u.get('output_tokens') or 0) * m['output']) / 1e6
    model = sorted({v for v in models.values() if v}) or ['unknown']
    line = (f"{label} agent-tool {role} {'+'.join(model)} cost {usd:.4f} calls {len(last)} in {tot['inp']} "
            f"cache_read {tot['cr']} cache_write {tot['cw']} out {tot['out']}")
    print(line)
    if '--log' in rest:
        with open(rest[rest.index('--log') + 1], 'a', encoding='utf-8') as fh:
            fh.write(line + '\n')


if __name__ == '__main__':
    main(*sys.argv[1:])
