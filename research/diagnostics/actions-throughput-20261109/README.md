# Where the runner time went, 2026-11-06 to 2026-11-09

Measured 2026-11-09 by Claude for the owner, who asked why the weekend's bottleneck was waiting on
GitHub rather than research. Kean F-20261109-actions-throughput (the measurement) and
D-20261109-no-push-runs (the owner's decision and its wiring).

## Method

- `runs.py` lists every workflow run created 2026-11-06T00:00Z to 2026-11-09T23:59Z through the
  Actions API, in 6-hour windows (one query returns at most 1,000 runs): 2,885 runs.
- `steps.py` fetches job and step timings for an even sample of 410 completed runs (260 Run jobs,
  80 Refresh published progress, 40 Road tests, 30 Kean checks).
- Failure reasons come from `gh run view --log-failed` on a random sample of 10 publish failures.
- Main's first-parent commits and the readiness counts come from `git log` on `main`.

## Results

| | |
|---|---|
| Runner time, all workflows | about 1,090 hours (sum of run wall times) |
| Run jobs | 748 runs, 392 succeeded; started by 474 pushes, 257 dispatches, 17 schedules |
| Run jobs minutes in successful runs (sample) | 18% |
| Run jobs minutes in runs refused at publish as stale | 33% (87 of 260 runs) |
| Run jobs minutes in checkout and input materialization | 28% |
| Run jobs queue wait for a runner | about 12 minutes per run |
| Refresh published progress | 39 of 313 succeeded |
| Legacy Stage 20/21 workflows, Geddes, Neyman | about 79 runs each, all started by `pergamon-*` tag pushes |
| Main first-parent commits | 345, of which 191 (55%) were bot result commits |
| Tracked tree at main | 194,561 files, 17.5 GB |
| Ready for human review | 1,384 (Fri 08:38 UTC) to 1,179 (Mon); statuses 4,291 to 4,301; human-certified 0 |

Nine of ten sampled publish failures read "Runner results rejected as stale": the run finished, but
main had moved while it ran. Every push-started run and every result commit moved main for the
others.

## Changes made (owner decision D-20261109-no-push-runs)

- Run jobs starts only on its schedule or by hand; `only=true` runs exactly the named jobs, as a
  push used to. The sweep now reads every commit after the previous sweep's input commit, found in
  the run history, so a late sweep or a commit dated before its push is still seen; the daily run is
  a sweep too.
- Every push trigger names literal branches, so tag pushes start nothing.
- The Stage 20/21, Tribonian and R1 workflows run only by hand.
- No workflow listens to tag events (`create`, `delete`, `release`, `registry_package`); only
  `run-jobs.yml` may pick jobs or be named Run jobs; an automatically started workflow may start no
  other workflow run except re-queueing itself, and `arsenale.py requeue` refuses any other target.
- A sweep counts as covering its range once its plan succeeded and, if it finished, its publish ran;
  a sweep still running counts, so its range is not swept twice. History is read up to 300 runs.
- `.github/scripts/workflow_triggers.py` checks all of this and fails closed on trigger syntax it
  cannot read (inline forms, anchors, tabs, Unicode line separators, column-0 continuations). Its
  adversarial tests run in the road tests. An independent review found nine ways past the first
  version; each now has a test. Mutation testing: all 34 deliberate breakages of the checker, the
  picker's sweep rules and the re-queue rule made the tests fail.

Remaining known limits: a finished sweep whose publish could not push after its retries
(`push-failed`) still counts, so its range is not retried; a force-push to main or an unreadable run
history falls back to the 3h20m window, with a warning.

## Not changed

- Job outputs are still committed to main, which is the remaining source of stale refusals.
- Main has no branch protection, so a red check does not stop a merge or a direct push.
