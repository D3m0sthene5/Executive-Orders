"""Run the scan-inventory tests, then the inventory. See README.md."""
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).parent
if subprocess.run([sys.executable, "-m", "unittest", "-v", "test_inventory"], cwd=here).returncode:
    sys.exit("Tests failed; inventory not run.")
sys.path.insert(0, str(here))
import inventory  # noqa: E402

inventory.main()
