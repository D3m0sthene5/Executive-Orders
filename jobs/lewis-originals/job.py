"""Run Lewis's tests, routes, existing acquisition-state join, then web search."""

import json
import os
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).parent
tests = subprocess.run([sys.executable, "-m", "unittest", "-v", "test_lewis", "test_handoff"], cwd=here)
if not tests.returncode:
    tests = subprocess.run([sys.executable, "-m", "unittest", "-v", "test_eo_websearch"], cwd=here.parent / "_lib")
if tests.returncode:
    sys.exit("Tests failed; Lewis not run.")

sys.path.insert(0, str(here))
import lewis  # noqa: E402
import handoff  # noqa: E402
import online  # noqa: E402

repo = os.environ.get("REPO_ROOT") or str(here.parent.parent)
out = os.environ.get("OUTPUT_DIR") or str(here / "output")
lewis.main()
print(json.dumps({"acquisition_handoff": handoff.refresh(repo, out, lewis.write_report)}, sort_keys=True))
print("Offline stage done; starting the web search stage")
web = online.run(repo, out)
print(json.dumps({k: web[k] for k in ("advanced_this_run", "requests_used", "hits_total", "leads_page_confirmed", "engines")}, indent=2))
print(f"Outputs written to {out}")
