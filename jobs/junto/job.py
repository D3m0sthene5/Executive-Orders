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
subprocess.run([sys.executable, "-I", str(Path(__file__).with_name("test_evidence.py"))], check=True)
args = ["--output", str(output)]
result = junto.main(args + ["check"])
if result:
    raise SystemExit(result)
code = junto.main(args + ["score"])
if code:
    raise SystemExit(code)
# Rumford: measured cost at stake per saver, from committed wave usage (no session data needed).
import evidence  # noqa: E402
repo = Path(__file__).resolve().parents[2]
found = evidence.write(repo, output)
print("Rumford: " + "; ".join(f"{s['saver_key']} ${s['cost_at_stake_usd']:.2f}" for s in found["savers"]))
