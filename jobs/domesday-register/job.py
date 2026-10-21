"""Run the register's tests, then build the register. See README.md."""

import os
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).parent
tests = subprocess.run([sys.executable, "-m", "unittest", "-v", "test_register"], cwd=here)
if tests.returncode:
    sys.exit("Tests failed; register not built.")

sys.path.insert(0, str(here))
import register  # noqa: E402

register.main()
print(f"Outputs written to {os.environ.get('OUTPUT_DIR')}")
