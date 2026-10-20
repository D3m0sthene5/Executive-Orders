"""GitHub Actions entry point: runs `lambertini build` into OUTPUT_DIR (see README.md)."""
import os
import sys
import json
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lambertini  # noqa: E402

lambertini.main(["--repo", os.environ.get("REPO_ROOT", lambertini.DEFAULT_REPO),
                 "--output", os.environ["OUTPUT_DIR"], "build"])
import progress
result = progress.reconcile(os.environ.get("REPO_ROOT", lambertini.DEFAULT_REPO))
(Path(os.environ["OUTPUT_DIR"]) / "RESEARCH_PROGRESS.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n")
