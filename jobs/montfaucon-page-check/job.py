import json
import os
from pathlib import Path
from page_check import assemble

root = Path(os.environ.get('REPO_ROOT', '.')).resolve()
out = Path(os.environ['OUTPUT_DIR'])
out.mkdir(parents=True, exist_ok=True)
outcomes = []
lanes, rejected = assemble(root, outcomes)
for lane, rows in lanes.items():
    (out / ('FRAGMENTS_' + lane.upper() + '.jsonl')).write_text(
        ''.join(json.dumps(row, sort_keys=True) + '\n' for row in rows), encoding='utf-8')
(out / 'REJECTIONS.json').write_text(json.dumps(rejected, indent=2) + '\n', encoding='utf-8')
(out / 'OUTCOMES.json').write_text(json.dumps(outcomes, indent=2) + '\n', encoding='utf-8')
print({lane: len(rows) for lane, rows in lanes.items()}, 'rejected:', len(rejected))
