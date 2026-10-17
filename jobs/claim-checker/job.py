"""Claim checker job: run the unit tests, then check every claim. See README.md.

GitHub runs this with no arguments (no downloads). On the PC (PowerShell):
    $env:REPO_ROOT='.'; $env:OUTPUT_DIR='<dir outside the repo>'; python jobs/claim-checker/job.py [--fetch]
or (Git Bash):
    REPO_ROOT=. OUTPUT_DIR=<dir> python jobs/claim-checker/job.py [--fetch]
"""

import os
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).resolve().parent
tests = subprocess.run([sys.executable, "-m", "unittest", "-v", "test_checker"], cwd=here,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
if tests.returncode:
    sys.exit("Unit tests failed; the claim checker was not run.")

os.environ.setdefault("REPO_ROOT", str(here.parent.parent))
sys.path.insert(0, str(here))
import checker  # noqa: E402

checker.main(sys.argv[1:])
