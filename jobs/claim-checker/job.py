"""Run tests, restore a bounded batch of effective claims' cited scans, then check claims.

No external-source acquisition unless --fetch is supplied. A partial Git clone
may fetch the exact committed ProQuest blobs; no whole-folder checkout or LFS
pull is performed. See proquest_inputs.py and its materialization receipt.
"""

import json
import os
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).resolve().parent
tests = subprocess.run([sys.executable, "-m", "unittest", "-v", "test_checker", "test_proquest_inputs"], cwd=here,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
if tests.returncode:
    sys.exit("Unit tests failed; the claim checker was not run.")

os.environ.setdefault("REPO_ROOT", str(here.parent.parent))
sys.path.insert(0, str(here))
import proquest_inputs  # noqa: E402
import checker  # noqa: E402

materialized = proquest_inputs.materialize(os.environ["REPO_ROOT"], os.environ.get("OUTPUT_DIR", here / "output"))
print(json.dumps({"proquest_materialization": materialized["receipts"],
                  "errors": materialized["errors"],
                  "artifacts_attempted": materialized["artifacts_attempted"],
                  "bytes_read": materialized["bytes_read"],
                  "selection_sha256": materialized["selection_sha256"],
                  "next_cursor": materialized["next_cursor"],
                  "deferred": [a for a in materialized["artifacts"]
                               if a["state"].startswith("deferred_")]}))
# A deferred tail remains explicit in the retained receipt. Resume only through
# a separately bounded helper call with this exact cursor and unchanged inputs.
checker.main(sys.argv[1:])
