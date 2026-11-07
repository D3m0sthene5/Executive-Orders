"""Run Duodecim's offline tests, then the job. See README.md.

SMOKE: a file named SMOKE in this folder (or JOB_SMOKE=1) reads three editions only. Delete the file for the full run.
"""
import os
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).resolve().parent
if subprocess.run([sys.executable, "-I", str(here / "test_duodecim.py")], cwd=str(here)).returncode:
    sys.exit("test_duodecim.py failed; job not run")
sys.path.insert(0, str(here))
import duodecim  # noqa: E402

out = pathlib.Path(os.environ["OUTPUT_DIR"])
repo = pathlib.Path(os.environ["REPO_ROOT"])
cache = pathlib.Path(os.environ.get("JOB_CACHE_DIR") or (out.parent / "duodecim-tableiv-cache")).resolve()
duodecim.main(repo, out, cache)
