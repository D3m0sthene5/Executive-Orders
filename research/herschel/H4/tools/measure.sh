#!/bin/bash
# usage: measure.sh OUTDIR -> sessions.py over H4's finished worker transcripts plus a snapshot of the H4 coordinator
# transcript, isolated in a private HOME so live transcripts of other coordinators cannot break the parse.
S=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H4
SRC=/root/.claude/projects/-tmp-claude-0--home-claude-1b28d9a2-1935-5c00-acfa-76feacb7b775-scratchpad-herschel-H4-run
CO=/root/.claude/projects/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/subagents/agent-a54c0a5a4df81ae07.jsonl
OUT=$1; H=$S/tele-home; rm -rf $H; mkdir -p $H/.claude/projects/h4-run $H/.claude/projects/h4-coord
python3 -I - "$S" <<'PY'
import json,glob,os,sys
S=sys.argv[1]; W=json.load(open(S+'/workers.json')); m={'default':'coordinator'}
step={'status_producer':'provisional_status','original_text':'original_text','producer':'lifecycle','producer_overlay':'lifecycle','status_reviewer':'review_status','reviewer':'review_lifecycle'}
done=[]
for f in sorted(glob.glob(S+'/run/*.json')):
    try: d=json.load(open(f))
    except Exception: continue
    w=os.path.basename(f)[:-5]; sid=d.get('session_id')
    base='-'.join(w.split('-')[:2])
    if sid: m['session:'+sid]=step.get(W.get(base,{}).get('template'),'other'); done.append(sid)
json.dump(m,open(S+'/phase_map.json','w'),indent=1); open(S+'/done_sids.txt','w').write('\n'.join(sorted(set(done))))
PY
for sid in $(cat $S/done_sids.txt); do cp $SRC/$sid.jsonl $H/.claude/projects/h4-run/ 2>/dev/null; done
python3 -I - "$CO" "$H/.claude/projects/h4-coord/h4-coordinator.jsonl" <<'PY'
import sys
lines=open(sys.argv[1],encoding='utf-8').read().splitlines()
ok=[]
import json
for l in lines:
    try: json.loads(l); ok.append(l)
    except Exception: pass
open(sys.argv[2],'w',encoding='utf-8').write('\n'.join(ok)+'\n')
PY
cd /home/claude/executive-orders
HOME=$H python3 -I jobs/bentham/sessions.py --wave herschel-H4 --phase-map $S/phase_map.json --since 2026-11-05T23:24:00Z --out $OUT 2>&1 | tail -3
