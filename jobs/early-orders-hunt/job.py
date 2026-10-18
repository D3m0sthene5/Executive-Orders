"""Run the tests, then hunt for the printed texts of the 18th- and 19th-century executive orders that Lord's
1943 list cites to Richardson, the War Department reservation books and the General Land Office reports.
See README.md. Leads only: nothing is admitted to the census or changed."""

import os
import pathlib
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
if subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_hunt"], cwd=HERE).returncode:
    sys.exit("Tests failed; nothing built.")
sys.path.insert(0, str(HERE))
import hunt  # noqa: E402

summary = hunt.run(os.environ.get("REPO_ROOT", "."), HERE, os.environ["OUTPUT_DIR"])
hunt.print_summary(summary)
