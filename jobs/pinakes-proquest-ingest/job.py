"""Run Pinakes's tests, then the ingest. See README.md."""

import os
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).parent
tests = subprocess.run([sys.executable, "-m", "unittest", "-v", "test_ingest"], cwd=here)
if tests.returncode:
    sys.exit("Tests failed; ingest not run.")

sys.path.insert(0, str(here))
import ingest  # noqa: E402

ingest.main()
print(f"Outputs written to {os.environ.get('OUTPUT_DIR')}")
