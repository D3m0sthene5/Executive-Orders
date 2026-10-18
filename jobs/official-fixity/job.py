"""Run the tests, then check every govinfo file the project holds against GPO's SHA-256."""

import csv
import io
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
tests = subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_fixity"], cwd=HERE)
if tests.returncode:
    sys.exit("Tests failed; fixity check not run.")
sys.path.insert(0, str(HERE))
import fixity  # noqa: E402

repo = pathlib.Path(os.environ.get("REPO_ROOT", ".")).resolve()
out = pathlib.Path(os.environ["OUTPUT_DIR"])
# Earlier results are carried forward (read-only from the last commit), so each run
# only checks files that are new or whose recorded hash changed.
prior = []
got = subprocess.run(["git", "show", "HEAD:jobs/official-fixity/output/FIXITY.csv"], cwd=repo,
                     capture_output=True)
if got.returncode == 0:
    prior = list(csv.DictReader(io.StringIO(got.stdout.decode("utf-8"))))
limit = int(os.environ["JOB_LIMIT"]) if os.environ.get("JOB_LIMIT") else None
workers = int(os.environ.get("JOB_WORKERS") or 6)
sys.stdout.reconfigure(line_buffering=True)
s = fixity.run(repo, out, prior_rows=prior, workers=workers, limit=limit)
print(f"{s['files']} govinfo files: {s['results']}; {s['orders_with_a_gpo_matched_file']} orders have a file "
      f"byte-identical to GPO's published SHA-256. Checked {s['checked_this_run']} this run "
      f"({s['premis_bytes_read_this_run'] / 1e6:.1f} MB of PREMIS read) in {s['seconds']} s.")
print("Custody evidence only; nothing here changes a status or count.")
