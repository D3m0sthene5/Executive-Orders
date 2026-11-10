"""Run road tests with sockets forbidden; identical entry point on Windows/Linux."""
import os, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
for name in ('family-rules','case-bundles','daily-digest','_lib','claim-drafts','readiness-tracker','montfaucon-page-check','lachmann','pinakes-proquest-ingest','csc-annual-reports','early-ranger-transcriptions','early-ranger-reparse','early-ranger-triage','early-ranger-original-items','early-ranger-full-pages','lewis-originals','valla','early-ranger-workbench','census-candidates','claim-kit','neyman'):
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
# Pergamon's store tests talk to fake servers on 127.0.0.1 only; the socket guard above skips them, so run them here.
subprocess.run([sys.executable,str(root/'jobs/_lib/test_pergamon_store.py')],cwd=root,check=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
subprocess.run([sys.executable,str(root/'.github/scripts/test_result_freshness.py')],cwd=root,check=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
subprocess.run([sys.executable,str(root/'.github/scripts/test_materialize_job_inputs.py')],cwd=root,check=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
subprocess.run([sys.executable,str(root/'.github/scripts/test_valla_materialization.py')],cwd=root,check=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})


subprocess.run([sys.executable,str(root/'.github/scripts/test_pick_jobs.py')],cwd=root,check=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
subprocess.run([sys.executable,str(root/'.github/scripts/test_rattle_watch.py')],cwd=root,check=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
subprocess.run([sys.executable,str(root/'.github/scripts/test_ariadne.py')],cwd=root,check=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
subprocess.run([sys.executable,str(root/'.github/scripts/test_ockham_hook.py')],cwd=root,check=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
subprocess.run([sys.executable,str(root/'.github/scripts/test_input_attributes.py')],cwd=root,check=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})

subprocess.run([sys.executable,str(root/'.github/scripts/test_r1_r4_integration.py')],cwd=root,check=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})

subprocess.run([sys.executable,str(root/'.github/scripts/test_job_summary.py')],cwd=root,check=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})

subprocess.run([sys.executable,str(root/'.github/scripts/test_writer_queue.py')],cwd=root,check=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
subprocess.run([sys.executable,str(root/'.github/scripts/test_arsenale.py')],cwd=root,check=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
# Trigger policy (owner, 2026-11-09): no push starts Run jobs, no tag starts any workflow.
subprocess.run([sys.executable,str(root/'.github/scripts/test_workflow_triggers.py')],cwd=root,check=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})

