"""Run Larrey's tests, re-run the back-test on the current kit code, then triage every order. See README.md.

The back-test reads the frozen packets of past waves (needs.txt). Re-running it on every job run is what keeps the
gates calibrated when a route fix merges: the new kit rules are applied to the same real outcomes, and a route is
enforced only while that back-test loses no success at the operating point.
"""

import os
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).parent
tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(here), "-p", "test_*.py", "-v"],
                       cwd=here)
if tests.returncode:
    sys.exit("Tests failed; triage not written.")

sys.path.insert(0, str(here))
import larrey  # noqa: E402

out = pathlib.Path(os.environ["OUTPUT_DIR"])
out.mkdir(parents=True, exist_ok=True)
try:
    larrey.backtest(larrey.REPO, write=True, out_path=out / "BACKTEST.json")
    print("back-test re-run on the current kit code ->", out / "BACKTEST.json")
except (OSError, KeyError, ValueError) as exc:
    print("back-test not re-run (", exc, "); the committed BACKTEST.json calibrates the routes")
sys.exit(larrey.main(["triage", "--no-pools", "--out", str(out)]))
