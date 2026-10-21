"""Run Lewis's tests, then Lewis. See README.md."""

import os
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).parent
tests = subprocess.run([sys.executable, "-m", "unittest", "-v", "test_lewis"], cwd=here)
if tests.returncode:
    sys.exit("Tests failed; Lewis not run.")

sys.path.insert(0, str(here))
import lewis  # noqa: E402

lewis.main()
print(f"Outputs written to {os.environ.get('OUTPUT_DIR')}")
