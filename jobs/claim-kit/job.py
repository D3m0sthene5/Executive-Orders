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
build(repo,out,os.environ.get('JOB_CACHE_DIR'))
# A previous generation must not block regeneration in pre-build tests. Once
# built, reject missing/duplicate/wrong-status dossiers and stale draft coverage.
coverage=validate_derived(population,drafts=repo/'jobs/claim-drafts/output',dossiers=out)
from build import dump
dump(out/'POPULATION_VALIDATION.json',{
    **{key:value for key,value in population.items() if key!='statuses'},
    'derived':coverage,
})
