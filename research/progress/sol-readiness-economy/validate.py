"""Bounded offline tests; writes only Session A validation artifacts."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
CHILD = r'''
import contextlib, json, resource, socket, sys, time, unittest
from pathlib import Path
socket.create_connection=lambda *a,**k: (_ for _ in ()).throw(AssertionError('network forbidden'))
class NoNetwork(socket.socket):
 def connect(self,*a,**k): raise AssertionError('network forbidden')
socket.socket=NoNetwork
started=time.monotonic()
log=Path(sys.argv[2]); log.parent.mkdir(parents=True,exist_ok=True)
with log.open('w') as f,contextlib.redirect_stdout(f),contextlib.redirect_stderr(f):
 suite=unittest.defaultTestLoader.discover(sys.argv[1],pattern='test_*.py')
 result=unittest.TextTestRunner(stream=f,verbosity=2).run(suite)
r=resource.getrusage(resource.RUSAGE_SELF)
info={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
 'skipped':len(result.skipped),'skip_reasons':[reason for _,reason in result.skipped],
 'wall_seconds':time.monotonic()-started,'cpu_user_seconds':r.ru_utime,
 'cpu_system_seconds':r.ru_stime,'peak_rss_kib_process':r.ru_maxrss,
 'success':result.wasSuccessful(),'network_forbidden':True}
Path(sys.argv[3]).write_text(json.dumps(info,indent=2)+'\n')
print(json.dumps(info))
sys.exit(0 if result.wasSuccessful() else 1)
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite',choices=['claim-kit','claim-checker'],required=True)
    parser.add_argument('--label',required=True)
    args=parser.parse_args()
    if not args.label.replace('-','').isalnum():
        parser.error('alphanumeric label with optional hyphens required')
    dest=ROOT/'research/progress/sol-readiness-economy/validation'
    log=dest/(args.suite+'-'+args.label+'.log')
    receipt=dest/(args.suite+'-'+args.label+'.json')
    if log.exists() or receipt.exists():
        parser.error('fresh validation label required')
    return subprocess.run([sys.executable,'-c',CHILD,'jobs/'+args.suite,str(log),str(receipt)],cwd=ROOT).returncode


if __name__=='__main__':
    raise SystemExit(main())
