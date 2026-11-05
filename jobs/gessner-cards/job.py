"""Run the card view's tests, then build it. See README.md."""

import subprocess
import sys
import pathlib

here = pathlib.Path(__file__).parent
tests = subprocess.run([sys.executable, "-m", "unittest", "-v", "test_build_cards"], cwd=here)
if tests.returncode:
    sys.exit("Tests failed; card view not built.")

sys.path.insert(0, str(here))
import build_cards  # noqa: E402

build_cards.main()
