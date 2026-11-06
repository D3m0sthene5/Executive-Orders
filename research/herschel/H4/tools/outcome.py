"""outcome.py WORKER STEP 'EO:n=outcome' ... -> records the coordinator's per-order outcome for one worker (scratch)."""
import json, sys
from pathlib import Path
S=Path('/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H4'); p=S/'outcomes.json'
O=json.loads(p.read_text()) if p.exists() else {}
w,step=sys.argv[1],sys.argv[2]; e=O.setdefault(w,{'step':step,'outcomes':{}}); e['step']=step
for a in sys.argv[3:]:
    k,v=a.split('=',1); e['outcomes'][k]=v
p.write_text(json.dumps(O,indent=1,ensure_ascii=False)); print(w,step,len(e['outcomes']))
