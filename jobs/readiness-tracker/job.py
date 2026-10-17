"""Run the readiness tracker's tests, then the tracker. See README.md."""

import os
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).parent
tests = subprocess.run([sys.executable, "-m", "unittest", "-v", "test_tracker"], cwd=here)
if tests.returncode:
    sys.exit("Tests failed; tracker not run.")

sys.path.insert(0, str(here))
import tracker  # noqa: E402

tracker.main()
print(f"Outputs written to {os.environ.get('OUTPUT_DIR')}")
