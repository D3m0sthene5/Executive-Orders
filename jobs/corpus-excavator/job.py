"""Bounded offline planner; network execution belongs to source-ladder."""
import os
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
if subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(HERE),'-p','test_*.py']).returncode:
    raise SystemExit('Excavator tests failed')
from excavator import build
build(Path(os.environ.get('REPO_ROOT',HERE.parents[1])),Path(os.environ.get('OUTPUT_DIR',HERE/'output')))
