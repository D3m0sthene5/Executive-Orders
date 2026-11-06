"""Run Mabillon held-printings tests, then the offline match. See README.md."""

import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).parent
tests = subprocess.run([sys.executable, "-m", "unittest", "-v", "test_held"], cwd=here)
if tests.returncode:
    sys.exit("Tests failed; held printings not run.")
sys.path.insert(0, str(here))
import held  # noqa: E402

held.main()
