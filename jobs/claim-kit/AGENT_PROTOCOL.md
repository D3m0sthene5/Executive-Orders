# Claim kit protocol (any AI or person)

The kit is an offline machine dossier builder. Every output is a lead. No source,
segmentation, candidate date, family grouping or search result establishes legal status.
Start at the committed `output/SUMMARY.json` and `STATUS.json`: check the input commit
and read warnings. Never reuse a decision against a changed dossier fingerprint.

1. Pull the assigned branch and read `HANDOFF/README.md`, your current assignment,
   `jobs/claim-drafts/AGENT_GUIDE.md` and `research/stage19/CLAIM_SCHEMA.md`.
   `python jobs/claim-kit/kit.py next --agent NAME --n 20` reserves disjoint work in
   `research/readiness/CLAIM_KIT_LOCK.json`, ranked by remaining family unlocks.
   Reservations serialize processes in one shared checkout. Commit/pull reservations
   before dividing work across independent clones; a local lock cannot coordinate
   uncommunicating branches. Never steal another agent's reservation.
2. `kit.py dossier EO:NUMBER` prints one dossier. Read its original and clause spans,
   actor provisions, own terms, earlier chain, exceptions, savings, current-law leads,
   conflicts, searches and explicit missing list. A source pointer is not a source
   read. Request absent material via `research/readiness/FETCH_QUEUE.jsonl`.
3. `kit.py sheet EO:NUMBER --agent NAME` writes a blank decision to
   `research/readiness/decisions/NAME-DATE/`. Confirm the complete original and
   inventory. For every clause choose its state and evidence IDs; expressly confirm
   the effective date and explain why earlier ends, partial amendments and savings
   do or do not control. A report deadline is never an end. Review schedules and
   retained independent commands. For YES, establish the current legal predicate
   through 2026-10-14; a citation or 1989 snapshot cannot establish it.
4. Resolve every conflict before accepting any machine search. Select adequate
   search IDs after reading their scope and coverage warnings. State savings and
   reasons, rationale and remaining material gaps. Set `approved` only after your
   own source review. This is producer approval, never an independent human review.
5. `kit.py assemble <sheet files or directories> --write /tmp/NAME-claims.jsonl`
   copies sources/quotes and runs Stage 19 plus exact-span/hash checks. A failed
   sheet is reported and the batch is not emitted. `kit.py check <claims>` repeats
   the pre-gates. Run the actual claim-checker for custody, identity and date checks.
6. A separate reviewer reads the sources, tests earlier endings, and writes an
   **AI review record** under your pilot research folder (never an
   `eo-lifecycle-review/v1` human review). Commit only accepted claim lines to your
   own `research/readiness/claims/NAME-DATE.jsonl`; no automatic publication exists.
   Same-actor single-clause CSV sheets are conveniences: approve each row and remove
   outliers. They confer no group approval.
7. Record the checker/tracker before and after, accept/reject outcomes, actual
   tool calls, available model-usage telemetry and wall time in your own HANDOFF
   note. Use `kit.py status`; use `kit.py release --agent NAME EO:NUMBER` to free
   unused work. Never edit statuses, census identities, ledger, codebook, other
   agents' claims/notes or human reviews.

Commands accept global `--repo` and `--output` before the subcommand. Only `build`
(the runner's `job.py`) writes machine outputs. The assembler does not fetch sources.
