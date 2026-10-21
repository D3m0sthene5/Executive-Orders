#!/usr/bin/env bash
# Commit jobs/<name>/output/ for the jobs that ran and push to the same branch.
# Reconcile unrelated branch updates, but never publish results for stale inputs.
set -euo pipefail

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

ALL_JOBS="$JOBS"
if [ -f oversized/runner-freshness/ATTEMPTS.json ]; then
  JOBS="$(python - <<'PY'
import json
from pathlib import Path
print(' '.join(r['job'] for r in json.loads(Path('oversized/runner-freshness/ATTEMPTS.json').read_text()) if r['publish_output']))
PY
)"
fi

# Fetch/check even before the first push: fast-forward ancestry alone does not
# prove that the branch still contains the code and inputs this run consumed.
check_freshness() {
  git fetch -q origin "$BRANCH"
  [ -z "$JOBS" ] && return 0
  python .github/scripts/result_freshness.py check "origin/$BRANCH" \
    oversized/runner-freshness/publication-check.json $JOBS
}

paths=()
for name in $JOBS; do
  [ -d "jobs/$name/output" ] && paths+=("jobs/$name/output")
done
for name in $ALL_JOBS; do
  [ -d "jobs/_attempts/$name" ] && paths+=("jobs/_attempts/$name")
done
if [[ " $JOBS " == *" daily-digest "* ]] && [ -f jobs/daily-digest/output/DIGEST.md ]; then
  python - <<'PYDIGEST'
from pathlib import Path
p=Path('jobs/daily-digest/output/DIGEST.md')
if len(p.read_text(encoding='utf-8').splitlines()) >= 150:
    raise SystemExit('Digest exceeds 149 lines')
Path('HANDOFF/DIGEST.md').write_bytes(p.read_bytes())
PYDIGEST
  paths+=("HANDOFF/DIGEST.md")
fi
[ ${#paths[@]} -eq 0 ] && { echo "No results to commit."; exit 0; }

git add -A -- "${paths[@]}"
if git diff --cached --quiet; then
  echo "Results are unchanged; nothing to commit."
  exit 0
fi
# On the daily run, skip the commit when only the run record (times, log)
# changed, so an unchanged tracker does not add a commit every day.
if [ "${EVENT:-}" = "schedule" ] && ! git diff --cached --name-only | grep -qvE '/output/(STATUS\.json|log\.txt|install-log\.txt|RUNNER_INPUTS\.json)$'; then
  echo "Only the run record changed; nothing new to commit."
  exit 0
fi

check_freshness

git commit -q -m "Results of job(s): $JOBS" -m "Run: $RUN_URL"

# Keep a copy of the results, so a clash with another run's results can be
# resolved by re-applying only after this run's input/output versions pass.
saved="$(mktemp -d)"
for p in "${paths[@]}"; do mkdir -p "$saved/$(dirname "$p")"; cp -a "$p" "$saved/$p"; done

for attempt in 1 2 3 4 5; do
  if git push -q origin "HEAD:$BRANCH"; then
    echo "Results pushed to $BRANCH."
    exit 0
  fi
  echo "Push rejected (attempt $attempt); taking the newer commits and retrying."
  check_freshness
  if ! git rebase -q "origin/$BRANCH"; then
    echo "Another run changed the same results; re-applying this run's results on top."
    git rebase --abort
    git reset -q --hard "origin/$BRANCH"
    for p in "${paths[@]}"; do rm -rf "./${p:?}"; mkdir -p "$(dirname "$p")"; cp -a "$saved/$p" "$p"; done
    git add -A -- "${paths[@]}"
    git diff --cached --quiet || git commit -q -m "Results of job(s): $JOBS" -m "Run: $RUN_URL"
  fi
  sleep $((attempt * 5))
done

echo "::error::Could not push results after 5 attempts."
exit 1
