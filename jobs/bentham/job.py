"""Run Bentham's tests, then build the plan. See README.md."""

import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).parent
tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(here), "-p", "test_*.py", "-v"],
                       cwd=here)
if tests.returncode:
    sys.exit("Tests failed; plan not built.")

sys.path.insert(0, str(here))
import bentham  # noqa: E402

bentham.main(["plan"])
