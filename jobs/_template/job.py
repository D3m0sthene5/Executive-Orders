"""Copy this folder to jobs/<name>/ and replace this script.

Write every result into OUTPUT_DIR. Print progress freely: it is saved to
output/log.txt. Exit with an error (raise or sys.exit(1)) if the job failed.
"""

import os
import pathlib

out = pathlib.Path(os.environ["OUTPUT_DIR"])
repo = pathlib.Path(os.environ["REPO_ROOT"])

(out / "result.txt").write_text("replace me\n")
