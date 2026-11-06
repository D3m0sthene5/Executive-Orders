"""Run the NARA census tests, then the census. See README.md."""

import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).parent
tests = subprocess.run([sys.executable, "-m", "unittest", "-v", "test_census"], cwd=here)
if tests.returncode:
    sys.exit("Tests failed; census not run.")
sys.path.insert(0, str(here))
import census  # noqa: E402

census.main()
