"""render.py WORKER TEMPLATE BATCH [extra KEY=VAL...] -> scratch prompts/WORKER.txt and registry entry (coordinator tool)."""
import json, sys
from pathlib import Path
R=Path('/home/claude/executive-orders'); H=R/'research/herschel/H4'; S=Path('/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H4')
w,tpl,b=sys.argv[1:4]; extra=dict(a.split('=',1) for a in sys.argv[4:])
B=json.load(open(H/'tools/batches.json')); ids=extra.pop('IDS').split(',') if 'IDS' in extra else B[b]
pk=f'{H}/packets/{b}/packet'
t=(H/'tools/prompts'/(tpl+'.txt')).read_text()
rep={'WORKER':w,'PACKETPATH':pk,'<PACKET>':pk,'PACKETDIR':extra.pop('PACKETDIR',pk),'ASSIGNEDLIST':', '.join(ids),'BATCH':b,
     'OUTFILE':f'{H}/original_text/{b}.jsonl','REPLNOTE':extra.pop('REPLNOTE','')}
rep.update(extra)
t=t.replace('BATCH.md','\x00DOC\x00')
for k,v in rep.items(): t=t.replace(k,v)
t=t.replace('\x00DOC\x00','BATCH.md')
(S/'prompts').mkdir(exist_ok=True); (S/'prompts'/f'{w}.txt').write_text(t)
reg=S/'workers.json'; W=json.loads(reg.read_text()) if reg.exists() else {}
W[w]={'template':tpl,'batch':b,'orders':ids}; reg.write_text(json.dumps(W,indent=1,ensure_ascii=False))
print(w,tpl,b,len(ids),len(t.split()))
