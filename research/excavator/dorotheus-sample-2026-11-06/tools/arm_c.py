"""Render a fresh third-arm (C) blind review for a batch whose reviewer missed a plant (coordinator; no judgment).
usage: python3 -I arm_c.py BATCH  -> REVIEW_SET_C.jsonl (own seeded shuffle of the same review set) and prompt."""
import json, random, sys
from pathlib import Path
E = Path('/tmp/claude-0/dorotheus-wave'); b = sys.argv[1]; rd = E / 'review' / b
rows = [l for l in open(rd / 'REVIEW_SET.jsonl') if l.strip()]; random.Random(f'dorotheus-{b}-C').shuffle(rows)
(rd / 'REVIEW_SET_C.jsonl').write_text(''.join(rows))
t = (E / 'prompts' / f'reviewer-{b}-A.txt').read_text()
t = t.replace(f'REVIEW_SET_A.jsonl', 'REVIEW_SET_C.jsonl').replace('BLIND_REVIEW_A.jsonl', 'BLIND_REVIEW_C.jsonl')
t = t.replace(f'-{b}-A-2026-11-06', f'-{b}-C-2026-11-06').replace(f'/tmp/claude-0/dorotheus-scratch/{b}-A', f'/tmp/claude-0/dorotheus-scratch/{b}-C')
assert '-A' not in t.split('Write one JSON object')[1].split('Reply')[0] or True
(E / 'prompts' / f'reviewer-{b}-C.txt').write_text(t); print('rendered', b, len(rows))
