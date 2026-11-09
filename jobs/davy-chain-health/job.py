"""Runner entry for Davy: unit tests, then the chain health check. See davy.py."""
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).resolve().parent
tests = subprocess.run([sys.executable, "-m", "unittest", "-v", "test_davy"], cwd=here)
if tests.returncode:
    sys.exit("Davy's own tests failed; the health check was not run.")
sys.path.insert(0, str(here))
import davy  # noqa: E402

sys.exit(davy.main())
