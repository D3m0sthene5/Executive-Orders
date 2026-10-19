"""Runner entry point: see README.md. Writes everything to OUTPUT_DIR."""

import os
import pathlib
import sys

repo = pathlib.Path(os.environ.get("REPO_ROOT", "."))
job_dir = pathlib.Path(os.environ.get("JOB_DIR", pathlib.Path(__file__).parent))
out = pathlib.Path(os.environ["OUTPUT_DIR"])
sys.path.insert(0, str(repo / "jobs" / "_lib"))
sys.path.insert(0, str(job_dir))

from fetch_pool import FetchPool  # noqa: E402
import csc  # noqa: E402

import tempfile  # noqa: E402

# Never inside OUTPUT_DIR: everything there is committed.
cache = pathlib.Path(os.environ.get("JOB_CACHE_DIR") or tempfile.mkdtemp(prefix="csc-cache-"))
# Report PDFs are 50-300 MB page scans; three at a time keeps GovInfo load and runner memory modest.
pool = FetchPool(cache, workers=3, per_host=3, max_bytes=600_000_000, timeout=120,
                 user_agent="EO-Road-System/1.0 (Executive-Orders research; csc-annual-reports)")
limit = int(os.environ["CSC_MAX_REPORTS"]) if os.environ.get("CSC_MAX_REPORTS") else None
summary = csc.run(repo, job_dir, out, pool, max_reports=limit)
if summary["packages_fetched_ok"] == 0:
    sys.exit("no report could be fetched")
