"""Run this job's unit tests, then match the Opus Stage 11 media to orders. See README.md.

GitHub: started by job.sh (which first tries to install OCR tools).
PC:     REPO_ROOT=. OUTPUT_DIR=<folder> python jobs/opus-media-match/job.py
Optional env: JOB_LIMIT (read at most N media members, evenly spread),
JOB_CACHE_DIR (text/OCR cache; default <OUTPUT_DIR>/../opus-media-match-cache),
JOB_OCR=0 (never OCR), JOB_OCR_MAX_PAGES (default 2000).
"""

import json
import os
import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True  # leave no __pycache__ in the job folder
here = pathlib.Path(__file__).resolve().parent
tests = subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_media_match"], cwd=here)
if tests.returncode:
    sys.exit("Unit tests failed; the job did not run.")

sys.path.insert(0, str(here))
import media_match as mm  # noqa: E402

repo = pathlib.Path(os.environ.get("REPO_ROOT", ".")).resolve()
out = pathlib.Path(os.environ["OUTPUT_DIR"]).resolve()
out.mkdir(parents=True, exist_ok=True)
cache = pathlib.Path(os.environ.get("JOB_CACHE_DIR") or (out.parent / f"{mm.JOB_NAME}-cache")).resolve()
cache.mkdir(parents=True, exist_ok=True)
limit = None
if os.environ.get("JOB_LIMIT", "").strip():
    try:
        limit = int(os.environ["JOB_LIMIT"])
    except ValueError:
        sys.exit(f"JOB_LIMIT must be a whole number, not {os.environ['JOB_LIMIT']!r}.")
    if limit <= 0:
        sys.exit("JOB_LIMIT must be 1 or more (leave it unset to read every file).")
ocr_enabled = os.environ.get("JOB_OCR", "1") != "0"
ocr_max = int(os.environ.get("JOB_OCR_MAX_PAGES", "2000"))


def ensure_lfs(rel):
    """On GitHub the zips arrive as Git LFS pointer files; fetch the real bytes."""
    p = repo / rel
    if not p.exists():
        sys.exit(f"Missing input {rel}. Add its folder to needs.txt.")
    with open(p, "rb") as fh:
        head = fh.read(200)
    if head.startswith(b"version https://git-lfs"):
        print(f"Fetching Git LFS file {rel} ...", flush=True)
        subprocess.run(["git", "lfs", "install", "--local"], cwd=repo, check=False)
        subprocess.run(["git", "lfs", "pull", "--include", rel, "--exclude", ""], cwd=repo, check=True)
        with open(p, "rb") as fh:
            if fh.read(40).startswith(b"version https://git-lfs"):
                sys.exit(f"Could not fetch {rel} from Git LFS.")


for rel in (mm.MEDIA_ZIP, mm.COMPLETE_ZIP):
    ensure_lfs(rel)

summary = mm.run(repo, out, cache_dir=cache, limit=limit, ocr_enabled=ocr_enabled, ocr_max_pages=ocr_max,
                 progress=lambda s: print(s, flush=True))

a = summary["accepted_844"]
t = summary["text"]
print()
print("Summary")
print(f"- Read {summary['members_processed']} of {summary['members_in_zip']} media files "
      f"({summary['sha256_check']['matches_member_map']} matched the Stage 20 hash list, "
      f"{summary['sha256_check']['mismatch']} did not).")
print(f"- {t['members_with_some_text']} files gave text; {t['members_needing_ocr']} files "
      f"({t['pages_needing_ocr']} pages) still need OCR; OCR done on {t['pages_ocr_done']} pages.")
print(f"- File/order pairs: {json.dumps(summary['pairs_by_grade'])}; files with no match: {summary['unmatched_members']}.")
print(f"- Of the {a['orders']} accepted Opus orders: {a['with_unique_supported_member']} have at least one "
      f"unique_supported file ({a['with_all_cited_media_resolved']} with nothing else left open), "
      f"{a['ambiguous_only']} only ambiguous candidates, {a['no_member_signal']} none.")
print(f"  Of those with none: {a['no_member_signal_because_records_cite_no_media_at_all']} cite no PDF/image at all; "
      f"{a['no_member_signal_because_cited_originals_not_in_companion']} cite PDF/image URLs whose originals are not "
      f"in the companion (re-fetch); {a['no_member_signal_because_cited_files_not_packaged']} cite only files left "
      f"out as too large; {a['no_member_signal_other']} other.")
if t.get("ocr_failures_this_run"):
    print(f"- OCR failed on {t['ocr_failures_this_run']} pages this run (see SUMMARY.json text.ocr_failure_examples).")
print(f"- {summary['fragments_written']} original_representation candidate fragments written.")
if summary.get("note_on_limit"):
    print(f"- {summary['note_on_limit']}")
print("These are leads for human checking, not legal findings. Outputs:", out)
