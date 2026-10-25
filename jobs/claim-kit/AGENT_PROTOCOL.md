# Claim kit protocol (any AI or person)

The kit is an offline machine dossier builder. Every output is a lead. No source,
segmentation, candidate date, family grouping or search result establishes legal status.
Start at the committed `output/SUMMARY.json` and `STATUS.json`: check the input commit
and read warnings. Never reuse a decision against a changed dossier fingerprint.

For bounded production batches, prefer the executable `prepare` / `view` /
`apply` / `batch-check` / `complete` path in [BATCH.md](BATCH.md). It shares exact source text,
retains blocked members, supports inventory corrections and saves full audits.
Undecided identities enter the same assignment with a full dossier and status
unset, using the existing experimental-overlay path for a reviewed proposal;
owner acceptance remains separate. The legacy individual
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
   own `research/readiness/claims/NAME-DATE.jsonl`. Use `kit.py complete` with the
   exact reviewed selection and recorded control adjudication to prepare filing;
   explicit `--publish` creates only its authorized new file. See
   [COMPLETION.md](COMPLETION.md). Missing or conflicting versions are exceptions.
   Same-actor single-clause CSV sheets are conveniences: approve each row and remove
   outliers. They confer no group approval.
7. Record the checker/tracker before and after, accept/reject outcomes, actual
   tool calls, available model-usage telemetry and wall time in your own HANDOFF
   note. Use `kit.py status`; use `kit.py release --agent NAME EO:NUMBER` to free
   unused work. Never edit statuses, census identities, ledger, codebook, other
   agents' claims/notes or human reviews.

Commands accept global `--repo` and `--output` before the subcommand. Only `build`
(the runner's `job.py`) writes machine outputs. The assembler does not fetch sources.

For undecided orders, ordinary `prepare` freezes the existing full `base_dossier`
with status unset, plus a blank status decision. Investigate the whole lifecycle
from that evidence in one bounded producer assignment. Maintain the analysis as
the status and lifecycle outputs are assembled; `apply` retains a populated
lifecycle sheet as `awaiting_status_review` without issuing an unset-status claim.
After exact independent status review, `overlay-propose --lifecycle-sheet PATH`
carries that sheet forward, rebinds its status/fingerprint and resets producer
approval for explicit reconfirmation. Status review approves only its stated
scope. The same independent reviewer may retain its source examination for a
separate lifecycle verdict, subject to all applicable independence and control
requirements. Owner adoption remains a separate gate.

Read the carried `prior_research` findings, qualifications, rejected theories,
source pins and remaining questions before repeating an investigation. Missing
or changed historical evidence requires reconciliation; no old status verdict
approves a lifecycle. Keep each bounded assignment's evolving analysis and review
inside its packet directory; preserve immutable earlier versions. Fresh contexts
belong between bounded assignments, not automatically between these two outputs.
The `history`, `status-sheet` and `overlay-prepare` commands remain available for
targeted work. History fragments are machine leads only; see
`jobs/status-history/README.md`.

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

NORTON `FACT:` evidence is available only after separate source-based factual and
clause-application review against the exact held bytes. Select it explicitly in
`later_events`; its reviewed date, entity, event kind and clause scope cannot be
changed. It is not an original, ending, current predicate or savings source.
The assembler and checker revalidate the current registry, both reviews and the
source bytes. A dated transmittal letter is not automatically proof of receipt,
delivery, standstill expiration or legal cessation. Unreviewed or custody-only
report candidates remain visible context and supply no citable factual event.

VALLA adds exact reasoning review leads and explicitly reviewed preparation
components to batch packets. Read the pinned `valla_context` and the readable
review section. A wording match is never a confirmed error or legal equivalence.
An independently examined dependency identifies only the specified conclusions
for revalidation. Component attestations cover only their stated scope and method;
an overall upheld review or silence approves no field. Reusing a quotation does
not confirm its source identity, complete inventory or ending theory. Changed
review dependencies require a new packet version. Every correction still needs
all member-specific checks, independent whole-case review, and owner acceptance
for replacement proposals. See `jobs/valla/README.md`.


## Provisional working texts under the October 21 owner ruling

The immutable original-authentication rule is unchanged. The assembler may use an
explicitly graded `acceptable_as_original: false` representation as a provisional
working text. Its source reference preserves the fragment's exact `grade`, order
identity, source hash, text path/hash and exact quoted span. Current supported
records are order-specific `original_representation` rows in existing
`jobs/*/output/FRAGMENTS*.jsonl` or `jobs/*/data/**/FRAGMENTS*.jsonl`; ungraded or
unmapped provenance stays blocked rather than acquiring an invented grade.

`blank_sheet` supplies a `working_text` disclosure and blank confirmations for
these sources. Independently inspect the source before setting each source's
`identity_confirmed` and `complete_text_confirmed` to true, plus `pages_confirmed`
when its fragment calls for a page check. This confirms the held representation,
not original authentication. A confirmed original is still required on the
original-supported route. The batch CSV carries the same `working_text` JSON.
The assembler retains only confirmations for sources actually cited by the claim.

Every dependent claim must preserve this exact standing note:
"original not yet held; replace and re-check quotes when an official copy is retrieved."
The checker retains its existing byte-custody requirements for every reference,
including ending instruments and current-law predicates. A custody record alone
still cannot pass. A new available official copy reopens a dependent claim for
replacement/recheck; rebuilding a dossier also invalidates old sheet fingerprints.
The tracker separately reports transcription-dependent ready dossiers and the
original-replacement/quotation-recheck obligations that remain. The rule does not
make uncited fragment rows ready, resolve legal questions, or certify a history.
