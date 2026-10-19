"""Run the tests, then parse the APP footnotes. See README.md."""

import os
import pathlib
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
if subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_footnotes"], cwd=HERE).returncode:
    sys.exit("Tests failed; nothing parsed.")
sys.path.insert(0, str(HERE))
import footnotes  # noqa: E402

footnotes.main()
print(f"Outputs written to {os.environ.get('OUTPUT_DIR')}")
