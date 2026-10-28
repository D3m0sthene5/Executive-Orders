#!/usr/bin/env python3
"""Runner entry for Cotton: offline tests, then fetch and re-hash the cited web sources into OUTPUT_DIR."""
import json
import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
tests = subprocess.run([sys.executable, "-I", str(HERE / "test_cotton.py")], capture_output=True, text=True)
print(tests.stderr[-2000:])
if tests.returncode:
    sys.exit("Cotton tests failed")
import cotton  # noqa: E402

summary = cotton.run(os.environ.get("REPO_ROOT", "."), os.environ.get("JOB_DIR", str(HERE)),
                     os.environ.get("OUTPUT_DIR", str(HERE / "output")))
print(json.dumps(summary, sort_keys=True))
