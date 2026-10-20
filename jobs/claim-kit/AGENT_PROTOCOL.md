# Claim kit protocol (any AI or person)

The kit is an offline machine dossier builder. Every output is a lead. No source,
segmentation, candidate date, family grouping or search result establishes legal status.
Start at the committed `output/SUMMARY.json` and `STATUS.json`: check the input commit
and read warnings. Never reuse a decision against a changed dossier fingerprint.

For bounded production batches, prefer the executable `prepare` / `view` /
`apply` / `batch-check` path in [BATCH.md](BATCH.md). It shares exact source text,
retains blocked members, supports inventory corrections and saves full audits.
Undecided identities use its independently reviewed experimental-overlay path;
owner acceptance remains separate from a working proposal. The legacy individual
JSON commands below remain supported.

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

For undecided orders, start with `kit.py history EO:NUMBER`, then `--full` to read
the exact held fields and page chunks. `kit.py status-sheet EO:NUMBER --agent NAME
--write PATH` creates a blank, history-pinned status-research decision. Review the
typed snapshot/capture/candidate dates, partial scope and every conflict; request
missing originals via FETCH_QUEUE. This sheet has no publication command and does
not bypass provisional adjudication. Once that adjudication is recorded through
the established process, resume the dossier/sheet/assemble/check steps above.
History fragments are machine leads only. See `jobs/status-history/README.md`.
For OCR inventory corrections, add `inventory_overrides` to the decision sheet:
`[{"scope_id":"EO:123#corrected-1","source_id":"ORIGINAL:EO:123","char_start":100,"char_end":250,"reason":"Explain the corrected operative boundary."}]`.
Use the dossier's exact `original_source_id`; offsets are absolute Unicode character
offsets in its held text file, enclosed within that original evidence span. Supply
every corrected clause, with unique scopes and disjoint nonempty spans; no free quote
or source fields are accepted. Replace the sheet's `clauses` with decisions for exactly
those scopes, omitting `clause_id` so assembly derives it. Keep the original dossier
fingerprint and explicitly confirm the complete inventory. Assembly copies exact text
and source provenance, pins the override list in claim metadata, and reconstructs it
when checking. `assemble.derive_inventory(dossier, overrides)` returns
`(clauses, derived_evidence_by_id, errors)` without editing the dossier or deciding law.
Sheets retain raw dossier IDs. Assembled source provenance stores each ID as unpadded
base64url UTF-8 under `evidence_id`, marked `evidence_id_encoding: base64url-utf8`;
the checker decodes it solely for exact dossier lookup. Legal citations, quotes,
actors and producer rationale remain unchanged.

For a pair whose dossier says `target provision not located: EO:X` while the acting text is
held, an agent may record the provision in `research/readiness/act_overrides/*.jsonl` (one ACT
record per line, fields as in `excavate.py` plus `provision_sha256`, `target_naming.sha256`,
`target_text_sha256` and a `review` object with `verdict: "upheld"`, `independent: true`, a
`reviewer` different from the `producer`, `review_kind`, `d6_searched`, `d6_found` and
`source_file`). `source_file` names the reviewer's committed `REVIEW.jsonl` under `research/`;
its line for the record id must say `upheld` with the same reviewer, review kind and D6 fields,
and the sibling `UPHELD_ACT_RECORDS.jsonl` must hold the reviewed record with every ACT field
equal. `act_overrides.py` re-slices every quoted span from the held actor text and requires and
checks the sha256 values. It refuses any record whose hash or span does not match or is missing,
that has an unknown field, that has no independent upheld review with a D6 step, that differs
from what the reviewer upheld, that is marked seeded, planted or example (or carries `EXAMPLE ONLY`
text anywhere), that says `located: false`, whose review ledger sits outside `research/` or inside
the override folder, whose pair the scanner already located, or that shares its pair or id with
another line (every such line is refused). Refusals are listed in `output/ACT_OVERRIDES_REPORT.json`;
with no override lines no report is written and the build output is unchanged.
An accepted record enters `ACTING_PROVISIONS` as `ACT:<target>><actor>` with provenance
`agent_located`; it is an AI-review hypothesis, never a certification, and never a status.

A source marked `requires_page_check` also requires explicit
`original_pages_confirmed: true` after the official pages/images were inspected;
confirming an extracted OCR text alone does not satisfy that flag.
