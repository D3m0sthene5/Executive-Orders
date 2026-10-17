"""Later-events job: run the unit tests, then build the candidate graph. See README.md."""

import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).resolve().parent
tests = subprocess.run([sys.executable, "-m", "unittest", "-v", "test_later_events"], cwd=here)
if tests.returncode:
    sys.exit("Unit tests failed; the job did not run.")

sys.path.insert(0, str(here))
import later_events  # noqa: E402

sys.exit(later_events.main())
