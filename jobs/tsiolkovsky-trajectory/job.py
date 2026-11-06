"""Tsiolkovsky runner entry: tests first, then the trajectory from main's history. See README.md."""
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
test = subprocess.run([sys.executable, "-m", "unittest", "-v", "test_trajectory"], cwd=HERE)
if test.returncode:
    sys.exit("tsiolkovsky: tests failed; trajectory not rebuilt")
sys.path.insert(0, str(HERE))
import trajectory  # noqa: E402

trajectory.build(os.environ.get("REPO_ROOT", str(HERE.parents[1])), os.environ.get("OUTPUT_DIR", str(HERE / "output")),
                 os.environ.get("JOB_PRIOR_OUTPUT_DIR") or str(HERE / "output"))
