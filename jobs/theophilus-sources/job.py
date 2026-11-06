"""Theophilus: fetch the official sources behind the YES orders' current legal basis.
Runs the offline tests first, then the job. See README.md. Environment: OUTPUT_DIR, REPO_ROOT,
JOB_WORKERS (default 4), JOB_CACHE_DIR."""
import os, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
r = subprocess.run([sys.executable, "-I", str(HERE / "test_job.py")], cwd=str(HERE))
if r.returncode:
    sys.exit("tests failed; job not run")
sys.path.insert(0, str(HERE))
import theophilus  # noqa: E402

out = pathlib.Path(os.environ["OUTPUT_DIR"])
repo = pathlib.Path(os.environ["REPO_ROOT"])
workers = int(os.environ.get("JOB_WORKERS") or 4)
cache = pathlib.Path(os.environ.get("JOB_CACHE_DIR") or (out.parent / "theophilus-sources-cache")).resolve()
prev = pathlib.Path(os.environ.get("JOB_DIR", str(HERE))) / "output" / "SOURCES.jsonl"
prev_copy = None
if prev.is_file():
    prev_copy = out.parent / "theophilus-previous-SOURCES.jsonl"
    prev_copy.write_bytes(prev.read_bytes())
s = theophilus.run_job(repo, out, cache, workers, previous_path=prev_copy)
if s["notices"]["fetched"] == 0 and sum(s["sections_fetched"].values()) == 0:
    sys.exit("nothing fetched")
