"""Job 3: draft clause inventories. Runs the unit tests first, then the build.

GitHub:  runs automatically from jobs/clause-drafts/ (see README.md).
PC:      REPO_ROOT=. OUTPUT_DIR=<dir> python jobs/clause-drafts/job.py
Options: JOB_LIMIT=<n> (process at most n orders), JOB_IDS=EO:9066,EO:12944,
         JOB_CACHE_DIR=<dir>, CLAUSE_INPUT_JOBS=fr-originals,source-ladder,
         CLAUSE_ALLOW_PARTIAL_INPUTS=1 (build even if the Opus zip or universe is missing)
"""

import os
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).resolve().parent
os.environ.setdefault("REPO_ROOT", str(here.parent.parent))
if "OUTPUT_DIR" not in os.environ:
    sys.exit("Set OUTPUT_DIR to the folder where results should be written.")

tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(here), "-p", "test_*.py", "-v"], cwd=here)
if tests.returncode:
    sys.exit("Unit tests failed; the clause drafts were not built.")

sys.path.insert(0, str(here))
import build  # noqa: E402

build.main()
