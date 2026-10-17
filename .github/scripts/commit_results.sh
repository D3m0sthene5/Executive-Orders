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
# On the daily run, skip the commit when only the run record (times, log)
# changed, so an unchanged tracker does not add a commit every day.
if [ "${EVENT:-}" = "schedule" ] && ! git diff --cached --name-only | grep -qvE '/output/(STATUS\.json|log\.txt|install-log\.txt)$'; then
  echo "Only the run record changed; nothing new to commit."
  exit 0
fi

git commit -q -m "Results of job(s): $JOBS" -m "Run: $RUN_URL"

# Keep a copy of the results, so a clash with another run's results can be
# resolved by re-applying ours on top of the newest commit (newest results win).
saved="$(mktemp -d)"
for p in "${paths[@]}"; do mkdir -p "$saved/$p"; cp -a "$p/." "$saved/$p/"; done

for attempt in 1 2 3 4 5; do
  if git push -q origin "HEAD:$BRANCH"; then
    echo "Results pushed to $BRANCH."
    exit 0
  fi
  echo "Push rejected (attempt $attempt); taking the newer commits and retrying."
  git fetch -q origin "$BRANCH"
  if ! git rebase -q "origin/$BRANCH"; then
    echo "Another run changed the same results; re-applying this run's results on top."
    git rebase --abort
    git reset -q --hard "origin/$BRANCH"
    for p in "${paths[@]}"; do rm -rf "./${p:?}"; mkdir -p "$p"; cp -a "$saved/$p/." "$p/"; done
    git add -A -- "${paths[@]}"
    git diff --cached --quiet || git commit -q -m "Results of job(s): $JOBS" -m "Run: $RUN_URL"
  fi
  sleep $((attempt * 5))
done

echo "::error::Could not push results after 5 attempts."
exit 1
