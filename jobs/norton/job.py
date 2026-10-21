"""Bounded offline NORTON compilation. All generated files stay under OUTPUT_DIR."""
import os
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from norton import build

if __name__ == '__main__':
    import subprocess
    subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(Path(__file__).parent),
                    '-p', 'test_*.py'], check=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    root = Path(os.environ.get('REPO_ROOT', Path(__file__).resolve().parents[2]))
    build(root, Path(os.environ.get('OUTPUT_DIR', Path(__file__).parent / 'output')))
