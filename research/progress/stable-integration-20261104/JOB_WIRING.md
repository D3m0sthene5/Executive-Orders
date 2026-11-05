# Job wiring classification

The current picker enumerates 70 runnable jobs and orders all 70 without a
dependency cycle. Twenty-two have no noncomment incoming after/triggers entry
and no DAILY marker. This is a list of scheduling roots, not 22 orphan jobs:
own-folder source/data pushes select runnable roots, and the existing manual
interface also selects them. Sweeps/manual runs then include declared consumers;
pushes deliberately stay limited to directly edited jobs.

| Role | Jobs | Evidence and intended interface |
| --- | --- | --- |
| Source producer or deterministic converter | app-footnote-leads, app-transcriptions, current-law, fr-originals, indian-reservations-1912, isthmian-canal-1911, numbered-early-orders, ofr-compilations, opus-media-match, richardson-volumes | Each job's README describes its output/command. Acquisition or fixed historical extraction need not recur daily. Existing after declarations or generic input readers consume the outputs. |
| Bounded acquisition or repair | astra-source-retention, family-rule-sources, family-rule-tail, poggio-archive-backfill | Exact requests, two named source instruments, a specific truncated source, or a fixed archive-only backfill. Broad recurrence would change the request scope. |
| One-off or bounded diagnostic | capcom-finalization, early-ranger-year-reconcile, leverage-campaign-check, library-survey | Explicit historical reconciliation, isolated verifier or extraction experiment. Retain their receipts and reproduce on demand. |
| Explicit operator protocol | geddes, jacquard, junto | Geddes consumes an applied packet; Jacquard needs frozen sampling/review steps; Junto checks/scores its ledger and accepts explicitly evidenced experiments. These are valid CLI interfaces. |
| Runner smoke | example-hello | The picker names it explicitly when runner files change. |

There are nine after references from Clark, Namier and Shepard to three existing
source-provider directories without job.py/job.sh: app-executive-orders,
wikisource-texts and hathi-gpo-orders. Their READMEs describe explicit acquisition
commands and retained outputs. Wikisource explicitly forbids scheduled invocation;
Hathi explicitly omits a generic entrypoint because output clearing would destroy
its accumulated corpus. The picker never starts these as nonexistent jobs. Their
existing retained fragments remain ordinary inputs; creating automatic acquisition
would require a separate supported design.

Some valid connections use generic readers rather than an after edge. For
example, APP footnote leads write lead-only EDGES.csv and claim-kit inputs.py
discovers every job's output/EDGES.csv. Geddes is called directly by ordinary
kit.py batch-check. Merely counting incoming/outgoing scheduling edges would
misclassify these paths.

The demonstrated disconnected consumer was Lachmann: producers did not select
it, and its first successful result could be deleted by a repeat pass after the
tracker made the text provisional. The bounded repair and native evidence are
in `lachmann/IMPLEMENTATION.md`. It now freshly reassesses machine-provisional
members and has five valid producer edges, with no upstream acquisition fanout.

`JOB_WIRING_CLASSIFICATION.json` records all 22 root classifications, exact
declared downstream consumers, the nine nonrunnable references and inspected
provider documentation. This is static wiring inspection plus scoped native
tests. It does not establish that every historical output/source is current,
that every optional tool has a suitable live production input, or that every
scientific workflow has been run and certified. No further orphan defect was
established in this bounded classification, so no additional automatic work was
introduced.
