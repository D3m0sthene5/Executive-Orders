"""Embed the dated, editorial tier assessment into Apollo's existing page.

Run from any directory. Does not produce scientific counts or change dataset feeds.
Requires every workflow node to be accounted for exactly once; human gates stay unranked.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAGE = HERE.parent / 'dashboard' / 'index.html'
START = '/* eo-tier-assessment */'
END = '/* /eo-tier-assessment */'


def main():
    data = json.loads((HERE / 'JOB_TIERS.json').read_text())
    nodes = json.loads((HERE.parent / 'workflow' / 'WORKFLOW_NODES.json').read_text())
    ids = [r['id'] for r in data['ratings']]
    assert len(ids) == len(set(ids)), 'duplicate tier id'
    assert {n['id'] for n in nodes} <= set(ids), 'workflow node missing a tier disposition'
    for r in data['ratings']:
        assert r['tier'] in ['S', 'A', 'B', 'C', 'D', 'F', 'U']
        assert r['reason'].strip()
        assert r['id'] in {n['id'] for n in nodes} or r.get('record'), 'extra assessment lacks evidence record'
    for n in nodes:
        if n['kind'] in ['gate', 'proposal']:
            assert next(r for r in data['ratings'] if r['id'] == n['id'])['tier'] == 'U'
    s = PAGE.read_text()
    assert s.count(START) == s.count(END) == 1, 'missing or duplicate assessment markers'
    a, rest = s.split(START)
    _, b = rest.split(END)
    encoded = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    PAGE.write_text(a + START + encoded + END + b)
    print(f"Embedded {len(ids)} assessments; {len(nodes)} workflow records covered")


if __name__ == '__main__':
    main()
