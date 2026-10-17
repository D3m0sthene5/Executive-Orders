#!/usr/bin/env bash
# Commit jobs/<name>/output/ for the jobs that ran and push to the same branch.
# If someone pushed in the meantime, rebase onto their work and try again.
set -euo pipefail

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

paths=()
for name in $JOBS; do
  [ -d "jobs/$name/output" ] && paths+=("jobs/$name/output")
done
[ ${#paths[@]} -eq 0 ] && { echo "No results to commit."; exit 0; }

git add -A -- "${paths[@]}"
if git diff --cached --quiet; then
  echo "Results are unchanged; nothing to commit."
  exit 0
fi

git commit -q -m "Results of job(s): $JOBS" -m "Run: $RUN_URL"

for attempt in 1 2 3 4 5; do
  if git push -q origin "HEAD:$BRANCH"; then
    echo "Results pushed to $BRANCH."
    exit 0
  fi
  echo "Push rejected (attempt $attempt); taking the newer commits and retrying."
  git fetch -q origin "$BRANCH"
  git rebase -q "origin/$BRANCH"
  sleep $((attempt * 5))
done

echo "::error::Could not push results after 5 attempts."
exit 1
