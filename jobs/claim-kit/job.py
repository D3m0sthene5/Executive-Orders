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
build(repo,Path(os.environ.get('OUTPUT_DIR',HERE/'output')),os.environ.get('JOB_CACHE_DIR'))
