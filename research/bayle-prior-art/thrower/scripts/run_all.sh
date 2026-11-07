#!/usr/bin/env bash
# Rebuild every Thrower deliverable.
# usage: run_all.sh ARCHIVE_DIR WORKTREE REF PROJECT_CACHE_DIR
#   ARCHIVE_DIR  unpacked Harvard Dataverse ZIP (doi:10.7910/DVN/LZGQOH), read only
#   WORKTREE REF the git checkout and ref that hold the project files (files are read with `git show REF:path`)
#   PROJECT_CACHE_DIR  empty folder outside the repository for the copied project files
set -euo pipefail
ARCHIVE="$1"; WT="$2"; REF="$3"; CACHE="$4"
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
PY="${PY:-py -I}"
$PY "$HERE/test_thrower_lib.py"
$PY "$HERE/fetch_project_inputs.py" "$WT" "$REF" "$CACHE" "$ROOT/PROJECT_INPUTS.json"
$PY "$HERE/build_thrower_table.py" "$ARCHIVE" "$ROOT"
$PY "$HERE/coverage.py" "$ARCHIVE" "$CACHE" "$ROOT"
$PY "$HERE/crosscheck.py" "$ARCHIVE" "$CACHE" "$ROOT"
$PY "$HERE/inherited.py" "$ARCHIVE" "$CACHE" "$ROOT"
$PY "$HERE/strata.py" "$ARCHIVE" "$CACHE" "$ROOT"
$PY "$HERE/draw_sample.py" "$ARCHIVE" "$CACHE" "$ROOT"
$PY "$HERE/finalize_manifest.py" "$ROOT"
