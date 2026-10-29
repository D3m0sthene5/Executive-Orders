"""fr-pages runner entry: offline tests first, then fetch the wanted Federal Register pages. See README.md."""
import json
import os
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).resolve().parent
tests = subprocess.run([sys.executable, "-m", "unittest", "-v", "test_frpages", "test_land_handoff"], cwd=here)
if tests.returncode:
    sys.exit("Unit tests failed; fr-pages did not run.")

sys.path.insert(0, str(here))
import frpages  # noqa: E402

root = os.environ.get("REPO_ROOT") or str(here.parent.parent)
out = os.environ.get("OUTPUT_DIR") or str(here / "output")
cache = os.environ.get("JOB_CACHE_DIR") or os.path.join(os.path.dirname(out), "fr-pages-cache")
os.makedirs(out, exist_ok=True)
summary = frpages.run(root, str(here), out, cache, os.environ.get("JOB_PRIOR_OUTPUT_DIR") or "")
print(json.dumps({k: summary[k] for k in ("wanted_lines", "distinct_pages", "pages_held", "carried_forward",
                                          "committed_pdfs", "failures", "requests", "bytes_downloaded")}, indent=2))
if summary["distinct_pages"] and not summary["pages_held"]:
    sys.exit("No wanted page could be fetched or carried forward.")
