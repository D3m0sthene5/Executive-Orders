"""Run Cruden's tests, then the job. See README.md."""
import os
import pathlib
import shutil
import subprocess
import sys

here = pathlib.Path(__file__).resolve().parent
for t in (here / "test_cruden.py", here.parent / "selden-common" / "test_selden_common.py"):
    if subprocess.run([sys.executable, "-I", str(t)], cwd=str(t.parent)).returncode:
        sys.exit(f"{t.name} failed; job not run")
if not shutil.which("pdftotext") and shutil.which("apt-get"):
    # poppler's pdftotext reads a 400-page issue about ten times faster than pypdf; pypdf is the fallback.
    subprocess.run("sudo -n apt-get update -qq && sudo -n DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "
                   "poppler-utils >/dev/null", shell=True)
print("pdftotext:", shutil.which("pdftotext") or "not available, using pypdf", flush=True)
sys.path.insert(0, str(here))
import cruden  # noqa: E402

out = pathlib.Path(os.environ["OUTPUT_DIR"])
repo = pathlib.Path(os.environ["REPO_ROOT"])
cache = pathlib.Path(os.environ.get("JOB_CACHE_DIR") or (out.parent / "cruden-cache")).resolve()
s = cruden.main(repo, out, cache)
if not s["controls"]["passed"]:
    print("controls did not pass: every fragment was written as cross_reference", flush=True)
if s["searches_made_this_run"] == 0 and s["fragments_carried_forward"] == 0 and s["units_attempted"] == 0:
    sys.exit("nothing searched, read or carried forward")
