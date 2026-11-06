"""Later-events job: run the unit tests, then build the candidate graph. See README.md."""

import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).resolve().parent
tests = subprocess.run([sys.executable, "-m", "unittest", "-v", "test_later_events", "test_text_jobs"], cwd=here)
if tests.returncode:
    sys.exit("Unit tests failed; the job did not run.")

sys.path.insert(0, str(here))
import later_events  # noqa: E402
import os  # noqa: E402
from text_jobs import text_jobs  # noqa: E402

# Selden's acting-order texts are scanned with the default texts (see text_jobs.py).
os.environ["LATER_EVENTS_TEXT_JOBS"] = text_jobs(later_events.DEFAULT_TEXT_JOBS)
sys.exit(later_events.main())
