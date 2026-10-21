"""Run Lewis's tests, then Lewis. See README.md."""

import json
import os
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).parent
tests = subprocess.run([sys.executable, "-m", "unittest", "-v", "test_lewis"], cwd=here)
if not tests.returncode:
    tests = subprocess.run([sys.executable, "-m", "unittest", "-v", "test_eo_websearch"], cwd=here.parent / "_lib")
if tests.returncode:
    sys.exit("Tests failed; Lewis not run.")

sys.path.insert(0, str(here))
import lewis  # noqa: E402
import online  # noqa: E402

lewis.main()
print("Offline stage done; starting the web search stage")
web = online.run(os.environ.get("REPO_ROOT") or str(here.parent.parent), os.environ.get("OUTPUT_DIR") or str(here / "output"))
print(json.dumps({k: web[k] for k in ("advanced_this_run", "requests_used", "hits_total", "leads_page_confirmed", "engines")}, indent=2))
print(f"Outputs written to {os.environ.get('OUTPUT_DIR')}")
