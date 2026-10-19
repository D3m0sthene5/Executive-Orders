"""Run the tests, then convert the APP records. See README.md."""

import os
import pathlib
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
if subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_convert"], cwd=HERE).returncode:
    sys.exit("Tests failed; nothing converted.")
sys.path.insert(0, str(HERE))
import convert  # noqa: E402

convert.main()
print(f"Outputs written to {os.environ.get('OUTPUT_DIR')}")
