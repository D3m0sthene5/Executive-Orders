"""Run Linnaeus's tests, then the classifier. See README.md."""
import os
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).resolve().parent
if subprocess.run([sys.executable, "-I", str(here / "test_linnaeus.py")], cwd=str(here)).returncode:
    sys.exit("test_linnaeus.py failed; job not run")
repo = pathlib.Path(os.environ["REPO_ROOT"])
sys.path.insert(0, str(here))
import linnaeus  # noqa: E402

s = linnaeus.main(["--root", str(repo), "--out", os.environ["OUTPUT_DIR"]])
if s["no_lead"] == 0:
    sys.exit("no undecided order without a lead: inputs missing?")
