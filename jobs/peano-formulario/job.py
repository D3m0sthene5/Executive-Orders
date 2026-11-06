"""Formulario runner entry: tests first, then build the lemma library. See README.md."""
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
test = subprocess.run([sys.executable, "-m", "unittest", "-v", "test_formulario"], cwd=HERE)
if test.returncode:
    sys.exit("formulario: tests failed; library not rebuilt")
sys.path.insert(0, str(HERE))
import formulario  # noqa: E402

formulario.main(["build", os.environ.get("REPO_ROOT", str(HERE.parents[1])),
                 os.environ.get("OUTPUT_DIR", str(HERE / "output"))])
