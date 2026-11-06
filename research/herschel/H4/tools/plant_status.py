"""Plant one blind control among a batch's producer status decisions (coordinator tool; no legal judgment).
usage: plant_status.py BATCH PACKETDIR
Copies every STATUS_DECISION.producer.json that recommends yes/no into scratch status-review/BATCH/EO_N.decision.json;
for one seeded pick, the copy has its recommended status flipped (yes<->no) and every proposed_intervals date moved
back three years (rationale unchanged, so the planted sheet contradicts its own sources). Key in scratch status-keys/."""
import hashlib, json, random, sys
from pathlib import Path
S=Path('/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H4')
def shift(d):
    if not isinstance(d,str) or len(d)<10 or not d[:4].isdigit(): return d
    md=d[4:10]; md='-02-28' if md=='-02-29' else md
    return f"{int(d[:4])-3:04d}{md}{d[10:]}"
def walk(o):
    if isinstance(o,dict): return {k:(shift(v) if 'date' in k or k in ('start','end','from','to') else walk(v)) for k,v in o.items()}
    if isinstance(o,list): return [walk(v) for v in o]
    return o
b,pk=sys.argv[1],Path(sys.argv[2])
out=S/'status-review'/b; out.mkdir(parents=True,exist_ok=True)
decs={}
for p in sorted(pk.glob('undecided/*/STATUS_DECISION.producer.json')):
    d=json.loads(p.read_text())
    if d.get('recommended_provisional_status') in ('yes','no'): decs[p.parent.name]=(p,d)
if not decs: print(json.dumps({'batch':b,'decisions':0})); sys.exit(0)
pick=random.Random(hashlib.sha256(('herschel-H4-status-controls:'+b).encode()).hexdigest()).choice(sorted(decs))
key=[]
for n,(p,d) in decs.items():
    raw=p.read_bytes()
    if n==pick:
        q=dict(d); q['recommended_provisional_status']={'yes':'no','no':'yes'}[d['recommended_provisional_status']]
        q['proposed_intervals']=walk(d.get('proposed_intervals',[]))
        raw2=(json.dumps(q,ensure_ascii=False,indent=2)+'\n').encode()
        (out/f'{n}.decision.json').write_bytes(raw2); (S/'status-keys').mkdir(exist_ok=True); (S/'status-keys'/f'{b}-{n}.genuine.json').write_bytes(raw)
        key.append({'order':d['instrument_id'],'planted_sha256':hashlib.sha256(raw2).hexdigest(),'genuine_sha256':hashlib.sha256(raw).hexdigest(),'defect':'status flipped and interval dates moved back three years'})
    else: (out/f'{n}.decision.json').write_bytes(raw)
(S/'status-keys').mkdir(exist_ok=True); (S/'status-keys'/f'{b}.json').write_text(json.dumps({'batch':b,'controls':key},indent=1))
print(json.dumps({'batch':b,'decisions':len(decs),'controls':[k['order'] for k in key]}))
