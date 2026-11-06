"""Job 8: draft claims per order. Runs the unit tests first, then the merge. See README.md.

GitHub:  runs from jobs/claim-drafts/ when this folder changes (or by hand: Actions -> Run jobs).
PC:      REPO_ROOT=. OUTPUT_DIR=<dir outside the repo> python jobs/claim-drafts/job.py
Options: JOB_LIMIT=<n>, CLAIM_DRAFTS_IDS=EO:12944,EO:9066, CLAIM_DRAFTS_SCOPE=decided|all (default here: all),
         CLAIM_DRAFTS_INPUTS="<folder>;<job>=<folder>", CLAIM_DRAFTS_CHECKER=0, JOB_CACHE_DIR=<dir>
"""

import os
import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True
here = pathlib.Path(__file__).resolve().parent
os.environ.setdefault("REPO_ROOT", str(here.parent.parent))
# Draft undecided orders too (2026-11-05). The claim kit's undecided route (status overlay) takes each order's
# machine later-source searches from its draft; with decided-only drafts all 10,681 undecided orders reached
# overlay-assemble with none and failed bounded_later_search (Herschel survey, research/herschel/REPORT.md).
os.environ.setdefault("CLAIM_DRAFTS_SCOPE", "all")
if not os.environ.get("OUTPUT_DIR"):
    sys.exit("Set OUTPUT_DIR to the folder where results should be written (outside research/).")

env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}
tests = subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_drafts"], cwd=here, env=env)
if tests.returncode:
    sys.exit("Unit tests failed; no drafts were written.")

sys.path.insert(0, str(here))
import drafts  # noqa: E402

drafts.main()
