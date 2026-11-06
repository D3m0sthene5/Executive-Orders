"""Prepare every H4 batch; drop members the kit refuses (recorded), retry. Coordinator tool, no legal judgment."""
import json, subprocess, re, sys, shutil, time
from pathlib import Path
R=Path('/home/claude/executive-orders'); S=Path('/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H4')
B=json.load(open(R/'research/herschel/H4/tools/batches.json'))
refused=json.load(open(S/'refused.json')) if (S/'refused.json').exists() else {}
for b in (sys.argv[1:] or B):
    ids=list(B[b]); dest=R/f'research/herschel/H4/packets/{b}/packet'
    while ids:
        if dest.exists(): shutil.rmtree(dest)
        t=time.time()
        p=subprocess.run(['python3','jobs/claim-kit/kit.py','prepare',*ids,'--agent','claude','--write',str(dest)],cwd=R,capture_output=True,text=True)
        out=p.stdout+p.stderr
        (S/f'prep-{b}.log').open('a').write(f'--- {time.strftime("%FT%TZ",time.gmtime())} rc={p.returncode} {time.time()-t:.1f}s ids={ids}\n'+out[-3000:])
        if (dest/'PACKET.json').exists(): break
        m=re.search(r'(no dated history located for|reservation belongs to [^:]+:|route existing claim[^:]*:|stale dossier|dossier does not match current INDEX:)\s*(EO:\S+)',out)
        if not m: print(b,'UNHANDLED',out[-500:]); break
        bad=m.group(2); refused[bad]=m.group(0); ids.remove(bad); print(b,'refused',m.group(0))
    print(b,'prepared',ids)
json.dump(refused,open(S/'refused.json','w'),indent=1,ensure_ascii=False)
