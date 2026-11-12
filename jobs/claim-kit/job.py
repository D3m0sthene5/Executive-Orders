"""Runner entry: tests then full corpus. All writes go to OUTPUT_DIR/cache."""
import os
from pathlib import Path
import subprocess
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
repo=Path(os.environ.get('REPO_ROOT',HERE.parents[1])).resolve()
subprocess.run([sys.executable,'-m','unittest','discover','-s',str(HERE),'-p','test_*.py'],cwd=repo,check=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
from build import build
from population import validate_inputs, validate_derived
population=validate_inputs(repo)
out=Path(os.environ.get('OUTPUT_DIR',HERE/'output'))
# Bounded build (2026-11-12): a regex defect once kept build() at full CPU with no output for 4 h 20 min until the
# runner's 350-minute wall, so the whole station published nothing. A build past its limit (default 90 minutes,
# 6x its usual 15) now fails here with a named reason, and the station's other jobs still run and publish.
import threading,time
limit=float(os.environ.get('CLAIM_KIT_BUILD_LIMIT_SECONDS','5400'))
def _limit():
    print(f'claim-kit: build exceeded {limit/60:.0f} minutes; stopping (see the last progress line above; '
          'set CLAIM_KIT_BUILD_LIMIT_SECONDS only for a known longer build)',flush=True)
    os._exit(3)
timer=threading.Timer(limit,_limit);timer.daemon=True;timer.start()
build(repo,out,os.environ.get('JOB_CACHE_DIR'))
timer.cancel()
# A previous generation must not block regeneration in pre-build tests. Once
# built, reject missing/duplicate/wrong-status dossiers and stale draft coverage.
coverage=validate_derived(population,drafts=repo/'jobs/claim-drafts/output',dossiers=out)
from build import dump
dump(out/'POPULATION_VALIDATION.json',{
    **{key:value for key,value in population.items() if key!='statuses'},
    'derived':coverage,
})
