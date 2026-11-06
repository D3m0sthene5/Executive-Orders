"""Run the tests, then build Niebuhr's lead files. See README.md."""
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).parent
if subprocess.run([sys.executable, "-m", "unittest", "-v", "test_leads"], cwd=here).returncode:
    sys.exit("Tests failed; leads not built.")
sys.path.insert(0, str(here))
import leads  # noqa: E402

leads.main()
