"""Run Larrey's tests, then triage every order from the committed claim-kit outputs. See README.md."""

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

sys.exit(larrey.main(["triage", "--no-pools", "--out", os.environ["OUTPUT_DIR"]]))
