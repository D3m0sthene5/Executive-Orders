"""Output-only sampling frame refresh; the frozen pilot is a separate consumer."""
import os
from pathlib import Path
import subprocess
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from survey import make_manifest,lines,write
root=Path(os.environ.get('REPO_ROOT',HERE.parents[1])).resolve()
out=Path(os.environ.get('OUTPUT_DIR',HERE/'output'))
subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(HERE),'-p','test_*.py'],check=True)
import json
rows,manifest=make_manifest(root,json.loads((HERE/'config.json').read_text()))
lines(out/'FRAME.jsonl',rows);write(out/'MANIFEST.json',manifest)
from collections import Counter
counts=Counter(r['stratum'] for r in rows)
write(out/'STRATA.json',[{'stratum':key,'population':n,'dimensions':next({k:r[k] for k in ('era','provisional_status','original_text','basis_evidence','families')} for r in rows if r['stratum']==key)} for key,n in sorted(counts.items())])
(out/'FRAME.md').write_text(f"# NEYMAN frame\n\n{len(rows):,} known unfinished orders; {len(counts):,} actual joint cells; {len(manifest['sample'])} prospective attempts.\n\nNo product of marginal probabilities. Historical census recovery is excluded and remains incompletely bounded. Sampling does not replace exhaustive research.\n")
print('NEYMAN frame',len(rows),'cells',len(counts),'attempts',len(manifest['sample']))
