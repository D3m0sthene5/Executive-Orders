"""Run Selden FR acting's tests, then the job. See README.md."""
import os
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).resolve().parent
for t in (here / "test_acting.py", here.parent / "selden-common" / "test_selden_common.py"):
    if subprocess.run([sys.executable, "-I", str(t)], cwd=str(t.parent)).returncode:
        sys.exit(f"{t.name} failed; job not run")
sys.path.insert(0, str(here))
import acting  # noqa: E402

out = pathlib.Path(os.environ["OUTPUT_DIR"])
repo = pathlib.Path(os.environ["REPO_ROOT"])
cache = pathlib.Path(os.environ.get("JOB_CACHE_DIR") or (out.parent / "selden-fr-acting-cache")).resolve()
s = acting.main(repo, out, cache)
if s["pages_held"] == 0:
    sys.exit("no page held")
