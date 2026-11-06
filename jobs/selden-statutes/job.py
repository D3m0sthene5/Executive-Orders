"""Run Selden statutes' tests, then the job. See README.md."""
import os
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).resolve().parent
for t in (here / "test_statutes.py", here.parent / "selden-common" / "test_selden_common.py"):
    if subprocess.run([sys.executable, "-I", str(t)], cwd=str(t.parent)).returncode:
        sys.exit(f"{t.name} failed; job not run")
sys.path.insert(0, str(here))
import statutes  # noqa: E402

out = pathlib.Path(os.environ["OUTPUT_DIR"])
repo = pathlib.Path(os.environ["REPO_ROOT"])
cache = pathlib.Path(os.environ.get("JOB_CACHE_DIR") or (out.parent / "selden-statutes-cache")).resolve()
s = statutes.main(repo, out, cache)
if s["held"] == 0:
    sys.exit("no statute held")
