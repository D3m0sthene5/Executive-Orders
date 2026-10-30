#!/usr/bin/env python3
"""Bound an ordinary default packet validation attempt; preserve refusal/timeout."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

ap = argparse.ArgumentParser()
ap.add_argument('repo', type=Path)
ap.add_argument('packet', type=Path)
ap.add_argument('out', type=Path)
ap.add_argument('--timeout', type=float, default=30)
a = ap.parse_args()
repo, packet = a.repo.resolve(), a.packet.resolve()
code = '''import json,sys
from pathlib import Path
repo,packet=map(Path,sys.argv[1:])
sys.path.insert(0,str(repo/'jobs/claim-kit'))
import batch
try:
 p,d=batch.load_packet(packet,repo)
 print(json.dumps({'accepted':True,'members':sorted(d)}))
except Exception as e:
 print(json.dumps({'accepted':False,'exception':type(e).__name__,'error':str(e)}))
 sys.exit(2)
'''
t = time.perf_counter()
try:
    p = subprocess.run([sys.executable,'-I','-c',code,str(repo),str(packet)],capture_output=True,text=True,timeout=a.timeout)
    result = {'completed':True,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
except subprocess.TimeoutExpired as e:
    result = {'completed':False,'outcome':'timeout','timeout_seconds':a.timeout,
              'stdout':(e.stdout or b'').decode() if isinstance(e.stdout,bytes) else e.stdout,
              'stderr':(e.stderr or b'').decode() if isinstance(e.stderr,bytes) else e.stderr}
result.update({'packet':str(packet.relative_to(repo)),'wall_seconds':time.perf_counter()-t,
               'notice':'Ordinary default load_packet gate; no validation disabled. A timeout is not a refusal or acceptance.'})
a.out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
