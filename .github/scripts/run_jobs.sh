#!/usr/bin/env bash
# Run each job named in $JOBS and write its results to jobs/<name>/output/.
# Every job runs even if an earlier one fails; the step fails at the end if
# any job did. Files over 95 MB are moved to oversized/<name>/ (git cannot
# hold them) and kept as a download on the workflow run.
set -uo pipefail

REPO_ROOT="$(pwd)"
LIMIT=$((95 * 1024 * 1024))
failed=0

for name in $JOBS; do
  dir="$REPO_ROOT/jobs/$name"
  out="$dir/output"
  echo "::group::Job $name"
  rm -rf "$out"
  mkdir -p "$out"
  started="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  if [ -f "$dir/needs.txt" ]; then
    # Folders of the repo this job reads, one per line; # starts a comment.
    mapfile -t needs < <(sed -e 's/#.*//' -e 's/[[:space:]]*$//' "$dir/needs.txt" | grep -v '^$' || true)
    if [ ${#needs[@]} -gt 0 ]; then
      echo "Downloading folders this job needs: ${needs[*]}"
      git sparse-checkout add "${needs[@]}"
    fi
  fi

  if [ -f "$dir/requirements.txt" ]; then
    pip install --quiet -r "$dir/requirements.txt" 2>&1 | tee "$out/install-log.txt"
  fi

  if [ -f "$dir/job.sh" ]; then
    cmd=(bash "$dir/job.sh")
  else
    cmd=(python "$dir/job.py")
  fi

  JOB_NAME="$name" JOB_DIR="$dir" OUTPUT_DIR="$out" REPO_ROOT="$REPO_ROOT" \
    "${cmd[@]}" 2>&1 | tee "$out/log.txt"
  code=${PIPESTATUS[0]}
  finished="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  [ "$code" -ne 0 ] && failed=1

  # Move anything git cannot store.
  moved=()
  while IFS= read -r -d '' f; do
    rel="${f#"$out"/}"
    mkdir -p "$REPO_ROOT/oversized/$name/$(dirname "$rel")"
    mv "$f" "$REPO_ROOT/oversized/$name/$rel"
    moved+=("$rel")
  done < <(find "$out" -type f -size +"${LIMIT}c" -print0)

  MOVED="$(printf '%s\n' "${moved[@]+"${moved[@]}"}")" \
  NAME="$name" CODE="$code" STARTED="$started" FINISHED="$finished" OUT="$out" \
  python - <<'EOF'
import json, os, platform, subprocess
moved = [m for m in os.environ["MOVED"].splitlines() if m]
status = {
    "job": os.environ["NAME"],
    "result": "succeeded" if os.environ["CODE"] == "0" else "failed",
    "exit_code": int(os.environ["CODE"]),
    "started_utc": os.environ["STARTED"],
    "finished_utc": os.environ["FINISHED"],
    "commit_run": os.environ.get("GITHUB_SHA"),
    "branch": os.environ.get("GITHUB_REF_NAME"),
    "trigger": os.environ.get("TRIGGER"),
    "run_url": f"{os.environ.get('GITHUB_SERVER_URL')}/{os.environ.get('GITHUB_REPOSITORY')}/actions/runs/{os.environ.get('GITHUB_RUN_ID')}",
    "machine": f"GitHub Actions {platform.platform()}, Python {platform.python_version()}",
    "oversized_files_moved_to_run_download": moved,
}
with open(os.path.join(os.environ["OUT"], "STATUS.json"), "w") as fh:
    json.dump(status, fh, indent=2)
    fh.write("\n")
print(json.dumps(status, indent=2))
EOF
  echo "::endgroup::"
  if [ "$code" -ne 0 ]; then
    echo "::error::Job $name failed with exit code $code. See jobs/$name/output/log.txt."
  fi
done

exit "$failed"
