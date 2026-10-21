"""Offline review-lead compiler. Never writes canonical claims or reviews."""
import os
from pathlib import Path
import valla

repo = Path(os.environ.get('REPO_ROOT', valla.REPO)).resolve()
out = Path(os.environ.get('OUTPUT_DIR', Path(__file__).parent / 'output'))
doc = valla.build(repo)
valla.dump(out / 'INDEX.json', doc)
valla.dump(out / 'SUMMARY.json', doc['summary'])
print(valla.canon(doc['summary']))
