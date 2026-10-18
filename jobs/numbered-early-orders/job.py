"""Run the tests, then look for the printed texts of the undecided numbered orders 1-5075 in the books the
project holds and in the government book series listed in data/BOOKS.json. See README.md. Leads only:
nothing is admitted to the census or changed."""

import os
import pathlib
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
if subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_numbered"], cwd=HERE).returncode:
    sys.exit("Tests failed; nothing built.")
sys.path.insert(0, str(HERE))
import numbered  # noqa: E402

numbered.run(os.environ.get("REPO_ROOT", "."), HERE, os.environ["OUTPUT_DIR"])
