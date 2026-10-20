#!/usr/bin/env python3
"""Read-only ledger validation and a fresh scoreboard in the runner output dir."""
import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import junto

output = Path(os.environ["OUTPUT_DIR"])
subprocess.run([sys.executable, "-I", str(Path(__file__).with_name("test_junto.py"))], check=True)
args = ["--output", str(output)]
result = junto.main(args + ["check"])
if result:
    raise SystemExit(result)
raise SystemExit(junto.main(args + ["score"]))
