"""Run Dagron's tests, then build every collection manifest. See README.md."""
import os
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).parent
tests = subprocess.run([sys.executable, "-m", "unittest", "-v", "test_dagron"], cwd=here)
if tests.returncode:
    sys.exit("Tests failed; manifests not built.")
sys.path.insert(0, str(here))
import dagron  # noqa: E402

dagron.main([os.environ.get("REPO_ROOT", "."), os.environ.get("OUTPUT_DIR", str(here / "output"))])
