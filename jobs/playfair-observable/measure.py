"""Measure a built Observable Framework dist/: file count, bytes, gzip bytes, largest files. Standard library only."""
import gzip
import json
import os
import pathlib
import sys

dist = pathlib.Path(sys.argv[1])
files = []
for p in sorted(dist.rglob("*")):
    if p.is_file():
        raw = p.read_bytes()
        files.append({"path": p.relative_to(dist).as_posix(), "bytes": len(raw),
                      "gzip_bytes": len(gzip.compress(raw, 6))})
total = sum(f["bytes"] for f in files)
total_gz = sum(f["gzip_bytes"] for f in files)
by_ext = {}
for f in files:
    ext = os.path.splitext(f["path"])[1] or "(none)"
    d = by_ext.setdefault(ext, {"files": 0, "bytes": 0})
    d["files"] += 1
    d["bytes"] += f["bytes"]
out = {
    "file_count": len(files),
    "total_bytes": total,
    "total_gzip_bytes": total_gz,
    "by_extension": by_ext,
    "largest_files": sorted(files, key=lambda f: -f["bytes"])[:10],
}
json.dump(out, sys.stdout, indent=2)
