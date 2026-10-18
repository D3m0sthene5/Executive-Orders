"""Run the tests, then estimate how many 1789-1899 executive orders the project's lists have not found,
from the overlap between the lists. See README.md. Population-level estimates only; nothing is admitted
to the census or changed."""

import os
import pathlib
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
if subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_complete"], cwd=HERE).returncode:
    sys.exit("Tests failed; nothing built.")
sys.path.insert(0, str(HERE))
import complete  # noqa: E402

summary = complete.run(os.environ.get("REPO_ROOT", "."), HERE, os.environ["OUTPUT_DIR"])
complete.print_summary(summary)
