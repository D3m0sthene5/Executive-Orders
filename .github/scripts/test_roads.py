"""Run road tests with sockets forbidden; identical entry point on Windows/Linux."""
import os, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
for name in ('family-rules','case-bundles','daily-digest','_lib','claim-drafts','readiness-tracker','pinakes-proquest-ingest','csc-annual-reports','early-ranger-transcriptions','early-ranger-reparse','early-ranger-triage','early-ranger-original-items','early-ranger-full-pages','lewis-originals'):
    folder=root/'jobs'/name
    if not any(folder.glob('test_*.py')):continue
    code="""import socket, unittest, sys
socket.create_connection=lambda *a,**k: (_ for _ in ()).throw(AssertionError('network forbidden in tests'))
class NoNetworkSocket(socket.socket):
    def connect(self,*a,**k): raise AssertionError('network forbidden in tests')
socket.socket=NoNetworkSocket
suite=unittest.defaultTestLoader.discover(sys.argv[1],pattern='test_*.py')
sys.exit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
"""
    subprocess.run([sys.executable,'-c',code,str(folder)],cwd=root,check=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
subprocess.run([sys.executable,str(root/'.github/scripts/test_result_freshness.py')],cwd=root,check=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})


subprocess.run([sys.executable,str(root/'.github/scripts/test_pick_jobs.py')],cwd=root,check=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
subprocess.run([sys.executable,str(root/'.github/scripts/test_rattle_watch.py')],cwd=root,check=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
