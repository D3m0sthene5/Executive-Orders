"""Smoke test for the shared runner: reports the machine and reads a folder
listed in needs.txt."""

import json
import os
import pathlib
import platform
import shutil

out = pathlib.Path(os.environ["OUTPUT_DIR"])
repo = pathlib.Path(os.environ["REPO_ROOT"])

stage19 = repo / "research" / "stage19"
disk = shutil.disk_usage(repo)
report = {
    "python": platform.python_version(),
    "machine": platform.platform(),
    "cpus": os.cpu_count(),
    "free_disk_gb": round(disk.free / 1e9, 1),
    "stage19_files_visible": sorted(p.name for p in stage19.iterdir()) if stage19.is_dir() else None,
}
print(json.dumps(report, indent=2))
(out / "machine.json").write_text(json.dumps(report, indent=2) + "\n")
