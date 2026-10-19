import os
from pathlib import Path
import subprocess
import sys
HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
from history import build
from history import dump
out=Path(os.environ.get('OUTPUT_DIR',HERE/'output'))
try:
    subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(HERE),'-p','test_*.py'],check=True)
    build(Path(os.environ.get('REPO_ROOT',HERE.parents[1])),out)
except Exception as exc:
    dump(out/'FAILED.json',{'error':type(exc).__name__+': '+str(exc),'stale_outputs_must_not_be_used':True})
    raise
