"""Run Selden FR citers' tests, then the job. See README.md."""
import os
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).resolve().parent
for t in ("test_citers.py", str(here.parent / "selden-common" / "test_selden_common.py")):
    r = subprocess.run([sys.executable, "-I", str(here / t) if not t.startswith("/") else t], cwd=str(here))
    if r.returncode:
        sys.exit(f"{t} failed; job not run")
sys.path.insert(0, str(here))
import citers  # noqa: E402

out = pathlib.Path(os.environ["OUTPUT_DIR"])
repo = pathlib.Path(os.environ["REPO_ROOT"])
cache = pathlib.Path(os.environ.get("JOB_CACHE_DIR") or (out.parent / "selden-fr-citers-cache")).resolve()
s = citers.main(repo, out, cache)
if s["targets_searched_this_run"] == 0 and s["targets_searched_total"] < s["targets_total"]:
    sys.exit("no target searched")
