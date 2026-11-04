# Landing and live acceptance

## Ownership

This branch owns the permanent reporting adapter, reporting trigger, Mission tab,
and offline regressions. Concurrent PR 142 owns the one-time Tribonian readiness
reconciliation, its native outputs, and its current publication session. The
changed file lists were disjoint when checked on November 4. Do not overwrite its
outputs, cancel its workflows, or restart its recount to test this UI repair.

Merge order is flexible. Capcom's existing command-line interface is preserved.
If main advances, replay this branch normally, resolve append-only Kean records by
keeping both additions, regenerate `HANDOFF/KEAN.md`, and rerun affected checks.
Edit only `HANDOFF/notes-astra.md` for this task.

## Concrete activation

1. Land the reviewed implementation after the actual PR checks pass. The new
   workflow's own path causes an initial bounded reporting run on a normal main
   push. If a merge method suppresses push events or readiness has not been
   refreshed, use **Refresh published progress** → **Run workflow** on main once;
   do not dispatch the broader downstream job graph merely to refresh the rocket.
2. Inspect the workflow's actual result and the published
   `jobs/daily-digest/output/MISSION_REFRESH.json`. A ready receipt must agree with
   `MISSION.json`, the native checker/tracker generation, and consumed readiness
   tree. A pending receipt is an explicit refusal, not a successful recount.
3. Publish the updated `research/progress/control-center` assets to the **existing**
   Site through its normal authorized publishing path, preserving the current
   published data and observability work. The frontend changes are `app.js`,
   `index.html`, `mission.js`, and `mission.css`. No private source cache is needed.
4. Open the existing Site at
   `https://executive-orders-production-atlas.d3mosth3n3s.chatgpt.site/#mission`.
   Verify the displayed tracker date, weighted position, ready count, distinct
   certification count, source links, flight log, and manual refresh. The browser
   checks public main on opening and every five minutes while visible.
5. Verify the pending/retained behavior using an ordinary new canonical filing or
   an engineering fixture; do not manufacture scientific claims to animate the
   display. A successfully validated newer generation replaces the retained flight.

## Expected behavior

The rocket moves when verified completed work changes its underlying model.
Administrative/code-only commits and additional elapsed time need not move it.
Relevant canonical readiness, census, and reconciled-status pushes automatically
start a bounded reporting run. Completion of the main **Run jobs** workflow also
requests reporting, including after an overall failure that may have published
independent successful outputs. Multiple triggers may coalesce into one recount of
the latest complete state. This can repeat reporting after a run that already
included it, but never expands the selected job graph or calls a model. Other custom
workflows and external output publishers retain their own scheduled/manual routes.

The former Claude artifact remains a dated upload until its own publisher changes
it. Pointing the everyday bookmark at the Site's Mission view removes that manual
upload dependency. Pushing a repair branch is not evidence that the Site has already
been redeployed; retain the deployment revision and actual live acceptance result.
