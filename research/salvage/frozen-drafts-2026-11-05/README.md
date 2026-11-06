# Salvage of three frozen draft runs (2026-11-05)

Three agent runs stopped responding with their pull requests still open as drafts: Codex's Machiavelli continuation (PR 151), Astra's unfinished-docket source trial (PR 146) and Sol's Babbage complete-effort comparison (PR 141). On the owner's instruction (2026-11-05, 20:52 ET) their useful material was extracted into main and the pull requests were closed. Nothing here changes a status, claim, source grade, census row or ready or certified count. Certified: 0.

## Where the material went

Research folders keep their own paths, because their reports and receipts cite those paths and no job reads `research/excavator/` or `research/progress/` automatically:

- `research/excavator/machiavelli-modern-undecided-20261105/` (Codex): 20 modern undecided orders researched end to end. Eight carry scoped, supported lifecycle proposals: EO 12965, 12980, 13053 and 13114 (ended June 30, 1999, inclusive), EO 13108 (September 30, 1999), EO 13255 (July 31, 2002), EO 13081 and 13102 (January 17, 1999). Twelve are partial. Three planted-error probes were caught by fresh reviewers. The folder also holds its retained source parts and page images; run its offline materializer before using those sources at their original paths.
- `research/excavator/astra-unfinished-docket-20261104/` and `research/excavator/archive-wave-20261104/` (Astra): archival intake, docket crosswalk and evaluation for unfinished archival texts.
- `research/progress/babbage-complete-effort/` (Sol): a negative result. A deterministic prerequisite route and the baseline script preserved the same 30 members, 355 tasks and 231 advisory groups, so the route saved nothing measurable.
- `research/progress/stable-integration-20261104/PR141_*` and `PR146_*`: the drafts' integration receipts.

Everything a job could pick up is archived under this folder instead, so it changes nothing until someone promotes it through the normal channel:

| Folder | What it holds | How to promote it |
|---|---|---|
| `codex-machiavelli/retained-sources/`, `astra-docket/retained-sources/` | Source PDFs and page texts the runs downloaded through the retention job, with each run's `SOURCES.jsonl`, `RESULTS.json` and `SUMMARY.json` | Append the matching rows from `FETCH_QUEUE_ADDITIONS.jsonl` to `research/readiness/FETCH_QUEUE.jsonl`, then import each file through `jobs/astra-source-retention` with `retained_path` and `expected_sha256` (at most 30 per run). This is the quickest win here: hash-only sources were a top blocker in the Herschel survey. |
| `*/FETCH_QUEUE_ADDITIONS.jsonl` | Queue rows the runs added (133 Codex, 43 Astra) | As above. |
| `astra-docket/job-data/` | Page-reviewed texts, fragments and agent confirmations for the ProQuest, Hathi, CSC, Canal Zone and Lachmann jobs | Move into `jobs/<job>/data/` only after a page review. This can change ready counts, so the owner merges it. |
| `astra-docket/CODE_CHANGES.patch` | Unreviewed changes to `lachmann`, `isthmian-canal-1911` and the readiness tracker | `git apply` on a branch, run the tests, and review. The tracker change alters counting. |
| `astra-docket/REQUESTS.json` | The run's last retention request manifest | Reference for the import above. |
| `sol-babbage/CODE_CHANGES.patch` | An opt-in prerequisite flag for claim-kit dispatch | Apply only with a measured saving; the run found none. |
| `codex-machiavelli/notes-codex.md` | Codex's last handoff entries | Read for context. |
| `MANIFEST.json` | Every file each run changed and where it went | |

## What was left behind

Generated job outputs and briefs (rebuilt on main), Codex's claim-kit reservations for its 20 orders (released, since the run is gone), and the drafts' copies of files that main has since replaced. The branches remain on GitHub with their full history.

## Unfinished work worth continuing

- Codex: different-family review of the eight supported proposals, owner adoption of their statuses, then fresh preparation, review and completion through the claim kit. 3,871 eligible Campaign B orders remain unassigned.
- Astra: independent review of the archival intake and the job-data page checks, then promotion as above.
- Sol: the planned follow-on was to deliver full United States Code note text, not pointers, to 13 remaining orders; it was never built.
