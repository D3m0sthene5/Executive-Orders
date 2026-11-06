"""Run Tischendorf's tests, then the search. See README.md."""

import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).parent
tests = subprocess.run([sys.executable, "-m", "unittest", "-v", "test_tischendorf"], cwd=here)
if tests.returncode:
    sys.exit("Tests failed; Tischendorf not run.")

sys.path.insert(0, str(here))
import tischendorf  # noqa: E402

tischendorf.main()
