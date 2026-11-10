"""Run Pacioli's tests, then the reconciliation. See README.md."""
import os
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).resolve().parent
if subprocess.run([sys.executable, "-I", str(here / "test_pacioli.py")], cwd=str(here)).returncode:
    sys.exit("test_pacioli.py failed; job not run")
sys.path.insert(0, str(here))
import pacioli  # noqa: E402

s = pacioli.main(["--root", os.environ["REPO_ROOT"], "--out", os.environ["OUTPUT_DIR"]])
if s["agreed_pairs"] == 0:
    sys.exit("no agreed pair: inputs missing?")
