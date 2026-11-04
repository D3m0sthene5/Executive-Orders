# Kean brief: read this first

Generated from `jobs/kean/register/` by `python3 -I jobs/kean/kean.py brief`; do not edit by hand. Named for
Thomas Kean, chair of the 9/11 Commission, which found that agencies held the pieces but did not share them.

- **Start:** read this page and only the newest entry of each `HANDOFF/notes-*.md`. Before proposing any tool,
  pilot or speed-up, run `python3 -I jobs/kean/kean.py search <words>`.
- **Stop:** record results (`add-finding`), questions for the owner (`add-ask`; cite the id in your notes) and
  owner decisions you received (`add-decision`, `wire`). Routine progress stays in your notes. See `jobs/kean/README.md`.

## Waiting for the owner (0)

Nothing.

## Standing owner requirements

- **Evidence decides; agents work out legal distinctions themselves** (D-20261028-evidence-decides): Record what the evidence establishes, with the best supported date or interval, and separate an exhausted command from surviving consequences. A claim of 'happened within this interval' needs evidence that it happened; otherwise the order stays open on that question. A later general rule ends a command only if something shows it extinguished that command. Disclosure keeps a gap visible but never fills it. Do not ask the owner to choose method answers to unlock rows: apply these distinctions to the supported cases and report the exceptions.
- **Coordinate by model tier** (D-20261029-tiered-delegation): Unless a task is small, the strongest available model plans, keeps legal judgment, control adjudication and integration, and delegates bounded tasks with exact inputs and deliverables to cheaper models; deterministic work goes to scripts. Skip delegation when briefing and checking cost about as much as the task. Review rules are unchanged; record each worker's model, tokens and time.

## Owner decisions not yet carried out by the tools (2)

- **D-20261031-jacquard** (partly wired): For X1 spent and swept classes, a pre-defined lot's provisional NO statuses may be adopted from a random sample with planted errors, zero misses allowed, 59 orders (95% upper bound 5%) or every order in small classes; flagged outliers go to individual review; adoption by owner-merged PR; statuses p… PR119 merged 888 individual NOs (4,291 total); no sampled lot passed. PR125 pins reconciled.
- **D-20261104-delegated-answers** (partly wired): Owner told Claude on 2026-11-03 to answer all open asks reasonably. Archival requests: yes, owner sends. Risk-tiered review: paired trial only. June 1932 EO 5853-5879: admit as compiled-source-only working identities. Class-notes PDF: remove from tree. Keys: NARA and Brave yes, SerpAPI held. Standi… Class-notes PDF removal and the EO 6471A/7016 re-review are done in the Tribonian PR; census admission, Valla change, ruleset and owner-only actions are not yet done.
- Not yet checked against the tools: D-20261021-eo-10449, D-20261021-report-deadline, D-20261021-strike-and-insert, D-20261021-unnamed-instruments, D-20261021-until-dates.

<!-- kean:drift -->
<!-- /kean:drift -->
## Newest results (6 of 115; `search` finds the rest)

- 2026-11-04 F-20261104-4 **worked**: Integrate PRs 131-137 and run the combined jobs. Lesson: Any change to jobs/valla or the runner scripts needs an audited certificate update in the same PR; separately, add .job-cache/ and jobs/_attempts/ handling to the fallback capture (runner tests alrea…
- 2026-11-04 F-20261104-3 **analysis**: Prepare correction packets (c01-c03) while other batches' completions were still being written. Lesson: Serialize: finish every completion that can mention a correction's ids before preparing the correction packet; check overlap by substring (an id like EO:1209 also matches EO:12090).
- 2026-11-04 F-20261104-2 **partly worked**: Re-complete reviewed claims that failed completion as custody_record_only after Cotton/astra retention later… Lesson: Custody must be settled before review and completion: run PR132 dispatch-check (custody preflight) before assigning a batch. Stranded claims need a new prepare for exactly those ids, the reviewed row…
- 2026-11-04 F-20261104-1 **failed**: Lind paired trial: 85 claims (a03, c01-c03) each reviewed by two fresh Opus blind reviewers launched together… Lesson: Do not wire receipts into the review prompt as a default; review cost is reading and legal judgment, and reviewers fold mechanical checks into the scripts they already write to read claims. Producers…
- 2026-11-02 F-20261102-population-contract-repair **worked**: Reproduce failed refresh and reconcile claim-kit contract to already-owner-merged PR119 rows Lesson: Carry accepted adoption into the independent population contract; do not infer authorization from mutable progress CSVs
- 2026-11-02 F-20261102-mountweazel-notes **worked**: Preserve optional source notes on blinded reviewer cards Lesson: Normalize optional presentation keys without erasing evidence or changing canonical/control payloads

Register: 19 owner decisions, 13 answered questions, 115 results; 16 older reports not yet summarized (`jobs/kean/register/legacy_reports.txt`).
