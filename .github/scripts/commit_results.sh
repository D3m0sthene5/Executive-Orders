#!/usr/bin/env bash
# Commit jobs/<name>/output/ for the jobs that ran and push to the same branch.
# Reconcile unrelated branch updates, but never publish results for stale inputs.
#
# Arsenale (arsenale.py publish) does the work: on the latest branch tip it keeps
# only the jobs whose declared inputs still match (result_freshness.py check,
# rechecked until the published set is fresh as a whole), commits them in one
# "Results of job(s): ..." commit, and retries a rejected push up to 5 times,
# re-fetching and re-checking each time. Refused jobs are recorded in
# oversized/runner-freshness/ARSENALE.json and the step exits 3.
set -euo pipefail
exec python .github/scripts/arsenale.py publish
