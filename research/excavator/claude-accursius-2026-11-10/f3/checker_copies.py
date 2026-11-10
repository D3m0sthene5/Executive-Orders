"""Finding 5: how many held copies claim-checker's index gives the release-point ZIP sha256.

  python -I checker_copies.py BRANCH_WORKTREE NAME=SOURCES.jsonl [NAME=SOURCES.jsonl ...]
Builds claim-checker's own index (sources.load_job_sources) from each current-law SOURCES.jsonl alone, in a
temporary repo with the extract files copied beside it, and prints the copies under the ZIP sha256 and url.
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

branch = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(branch / "jobs/claim-checker"))
import sources as S  # noqa: E402

ZIP_SHA = "c6122974e951003437ece5a998aa7c0b2cdc0f5703dfc78d6135e1fc9e729142"
ZIP_URL = "https://uscode.house.gov/download/releasepoints/us/pl/119/121/xml_uscAll@119-121.zip"
notes = branch / "jobs/current-law/output/usc-notes"
report = {}
for arg in sys.argv[2:]:
    name, manifest = arg.split("=", 1)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "jobs/current-law/output"
        out.mkdir(parents=True)
        shutil.copyfile(manifest, out / "SOURCES.jsonl")
        if notes.is_dir():
            shutil.copytree(notes, out / "usc-notes")
        index = S.HeldIndex() if hasattr(S, "HeldIndex") else None
        if index is None:
            index = next(v for v in vars(S).values() if isinstance(v, type) and hasattr(v, "lookup_sha"))()
        S.load_job_sources(index, Path(tmp))
        by_sha = index.lookup_sha(ZIP_SHA)
        report[name] = {"copies_under_zip_sha256": len(by_sha),
                        "copies_with_text_under_zip_sha256": sum(1 for c in by_sha if c.text_path),
                        "copies_under_zip_url": len(index.lookup_url(ZIP_URL)),
                        "distinct_sha256_in_index": len(index.by_sha)}
print(json.dumps(report, indent=1))
