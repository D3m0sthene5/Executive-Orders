"""Run Clark's tests, then Clark. See README.md."""

import os
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).parent
tests = subprocess.run([sys.executable, "-m", "unittest", "-v", "test_clark"], cwd=here)
if tests.returncode:
    sys.exit("Tests failed; Clark not run.")

sys.path.insert(0, str(here))
import clark  # noqa: E402

clark.main()
print(f"Outputs written to {os.environ.get('OUTPUT_DIR')}")
