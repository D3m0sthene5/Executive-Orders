# Mansfield: judgment-only claims for modern orders (2026-10-22)

Named for Lord Mansfield, who cleared a clogged docket by deciding the cases that were
already ripe. Production only: no new tool, no efficiency experiment, no status, codebook
or census change. Everything filed here is an AI hypothesis; the human-certified
whole-lifecycle count stays 0.

## Pool

`POOL.csv`: rows of `jobs/claim-drafts/output/TODO_BY_ORDER.csv` with
`only_judgment_left = yes`, `estimated_effort = small`, a provisional status (YES/NO),
`step_original_text = done` and `ready_for_human_review = no` in
`jobs/readiness-tracker/output/READINESS_BY_ORDER.csv`, and no claim line for the order in
`research/readiness/claims/` on main (the sibling branches `claude/justinian-1` and
`claude/olney-1` named in the brief do not exist on origin, so main is the only claim set).
743 orders: 564 NO, 179 YES (the brief estimated about 860; 74 were already claimed and 43
have the text step open). `BATCH_PLAN.json` draws random batches of 10 with seed 20261022
(NO) and 20261023 (YES): `random.Random(seed).shuffle` over the sorted ids of each stratum,
then consecutive slices of 10. NO batches run first; YES batches only if the gate passes.

## Gate (after the first 30 attempts)

Continue only if upheld genuine claims per attempted order is at least 0.5 and rejected
genuine claims are at most 25% of genuine reviewed claims. Attempted = every order given to
a producer (submitted or blocked). Stop when the pool is exhausted, the gate fails, or the
agents' token value reaches $120 at list prices.

## Roles per batch bNN (each a separate agent; the coordinator only routes)

Paths: RUN = `research/excavator/mansfield-2026-10-22`, SCRATCH = the session scratchpad
folder `mansfield/` (outside the repository; given to each agent by absolute path).

1. **Producer** (Opus). Reads nothing under RUN but this file and `BATCH_PLAN.json`.
   For each order of the batch: `python3 jobs/claim-kit/kit.py dossier EO:N` (never `-I`),
   the order's draft line in `jobs/claim-drafts/output/DRAFT_CLAIMS.jsonl`, the held texts
   at the dossier's `text_path`s at the stated offsets, and the owner rulings in
   `research/readiness/owner_rulings/` (all eight). Decides every clause from the held
   sources, writes a decision sheet with `kit.py sheet EO:N --agent claude-mansfield-bNN-producer
   --write SCRATCH/work/bNN/sheets/`, then `kit.py assemble SCRATCH/work/bNN/sheets --write
   SCRATCH/work/bNN/CLAIMS.proposed.jsonl` and `kit.py check` on it. Quotes sources verbatim
   with path and offsets. A needed source that is not held makes the order **blocked**, with
   a request line in `SCRATCH/work/bNN/FETCH_REQUESTS.jsonl` validated by
   `python3 jobs/source-ladder/request_contract.py validate --input ...` (never enqueued by
   the producer). Never guesses, never changes `whole_order_status`, never runs `kit.py next`
   or `release`, never writes outside SCRATCH/work/bNN. Writes `ORDER_LOG.jsonl` (one line per
   order: `instrument_id, stratum, provisional_status, outcome submitted|blocked, block_reason,
   fetch_line, d6_searched, rulings_applied, notes, minutes_approx`) and
   `PRODUCER_TELEMETRY.json` (wall minutes, tool calls, tokens if known, submitted, blocked).
2. **Planter** (Mountweazel, scratch planter). Copies `CLAIMS.proposed.jsonl` and
   `ORDER_LOG.jsonl` to `SCRATCH/review_copy/bNN/CLAIMS.jsonl` and `ORDER_LOG.jsonl`, with one
   or two known defects inserted in one or two claim lines (types from `jobs/mountweazel/README.md`:
   D2, D3, D5, D6, D7, D8 or a date/actor swap carried consistently through the rationale).
   Every line is re-serialized the same way, and every file in the copy gets the same
   modification time, so no name, timestamp or formatting gives a plant away. The key goes
   to `SCRATCH/plant_keys/bNN.json` (order, field, genuine value, planted value, defect
   type, refuting quote). Nothing under RUN or the repository is touched.
3. **Reviewer** (independent Opus, held sources, D6 check). Reads only
   `SCRATCH/review_copy/bNN/`, this protocol, the repository's held sources and fresh
   `kit.py dossier` output. Must not open `SCRATCH/work`, `SCRATCH/plant_keys`, the git
   history of this branch, or any file under RUN except `PROTOCOL.md`. Some lines may carry
   planted defects; the reviewer is not told how many or which. Reviews **every claim line**
   against the fixed checklist below (no sampling) and every blocked order for whether the
   block is justified. Writes `REVIEW.jsonl` (one line per order) and `VERDICTS.json` to
   `SCRATCH/review_out/bNN/`.
4. **Tally** (after the review). Reads the key, the review and the producer's unplanted
   claims. Files only upheld genuine claim lines, copied byte-for-byte from the producer's
   `CLAIMS.proposed.jsonl`, to `research/readiness/claims/claude-mansfield-bNN-2026-10-22.jsonl`;
   runs `research/stage19/code/claim_gate.py` `validate_claim` and the claim checker
   (`CLAIM_CHECKER_CLAIMS=<file> REPO_ROOT=. OUTPUT_DIR=SCRATCH/checker/bNN python3
   jobs/claim-checker/job.py`) on that file; removes any line that fails the gate or has a
   mechanical `fail`; enqueues the producer's validated fetch lines with `request_contract.py
   enqueue`; copies the producer files, review files and `TALLY.json` into `RUN/bNN/`, and
   records the plants in `RUN/bNN/PLANTED_CONTROLS.md`. Rejected genuine claims, plants and
   blocked orders are recorded with reasons, never filed.

A planted order's genuine (unplanted) line is **not** filed on the blind review alone. After
the key is opened, the same independent reviewer may re-review the unplanted line against
the full checklist; a line upheld in that re-review is filed and counted separately
(`upheld_after_reveal`) so the report can show the count with and without it.

## Reviewer checklist (fixed; answer every item for every claim line)

- Q1 Original: the cited original is this order's complete official text at the stated
  page or item; the representation grade is labelled as the fragment records it
  (transcription ruling: `acceptable_as_original: false` stays false).
- Q2 Inventory: every operative clause of the held original is listed, boundaries are right,
  and each `original_operative_text` is verbatim at the stated offsets.
- Q3 Ending: for every clause marked `terminated`, the acting instrument's held text names
  this order (unnamed-instruments ruling: an instrument that does not name the target does
  not end it; such an event is a disclosed candidate only), the effective date is the one
  the acting text states (signing date only when nothing else is stated), and no earlier end
  is missed: own term, "until" date (inclusive, alternative noted), earlier amendment
  (strike-and-insert ruling: an amended clause continues), report deadline (never an end;
  "functionally spent" is a note), one-time command already performed (a later revocation
  does not prove first cessation of a performed command: say how the claim handles it).
- Q4 Whole order: for a NO order, `whole_order_end.date` equals the latest clause
  `first_end.date`, and the whole-order ending instrument is the one the claim cites.
- Q5 D6, later events: list every later event the fresh dossier (chain, ACT actor
  provisions, missing list, conflicts) and the draft proposals name for this order, and say
  for each whether the claim attaches it, rules it out with a reason, or ignores it. An
  ignored event that could change a date, an actor or a clause state is a rejection
  (`D6_OMISSION`).
- Q6 Savings: the `savings_residuals` state is supported by the ending instrument's and the
  order's held text (quote the savings sentence or say none was found where).
- Q7 Conflicts: every conflict the draft listed (for example `NO_ORDER_CITED_IN_CURRENT_LAW`)
  is resolved in the rationale with a reason that the held or cited text supports; no
  `CONFLICT` line remains while `later_source_search` is filled.
- Q8 Quotes and dates: every quote is verbatim in the held text it cites; every date, order
  number and actor in the rationale matches the sources.
- Q9 Status: `whole_order_status` equals the provisional status; the claim does not
  promote anything (no certification language, no `acceptable_as_original` promotion).
- Q10 Verdict: `upheld` or `rejected` with one code (`DATE`, `ACTOR`, `INVENTORY`,
  `EARLIER_END`, `D6_OMISSION`, `SAVINGS`, `CONFLICT`, `QUOTE`, `STATUS`, `OTHER`) and the
  refuting quote with its path. For a blocked order: `block_justified` or
  `block_not_justified` with the reason.

## Files

- `RUN/bNN/`: `CLAIMS.proposed.jsonl` (producer, unplanted), `ORDER_LOG.jsonl`,
  `PRODUCER_TELEMETRY.json`, `FETCH_REQUESTS.jsonl`, `REVIEW.jsonl`, `VERDICTS.json`,
  `TALLY.json`, `PLANTED_CONTROLS.md`.
- `research/readiness/claims/claude-mansfield-bNN-2026-10-22.jsonl`: filed upheld lines.
- `OUTCOME.json`, `REPORT.md`, `COST.md` at the run root, written by the coordinator.
- Llull: forecast registered before the first batch; outcome recorded after.
