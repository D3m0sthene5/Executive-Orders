"""Refresh Polya from the exact inputs consumed in this runner invocation."""
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import polya

if __name__ == '__main__':
    root = os.environ.get('REPO_ROOT', str(Path(__file__).resolve().parents[2]))
    out = os.environ['OUTPUT_DIR']
    for command in ['compare', 'export']:
        result = polya.main(['--repo', root, '--output', out, command])
        if result: raise SystemExit(result)
