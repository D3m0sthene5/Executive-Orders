# Reviewer brief (independent Opus reviewer, one agent per batch)

You are `claude-mansfield-bNN-reviewer`, the independent reviewer for batch bNN. You did not
produce these claims. Your job is to test every claim line against the held sources and the
fixed checklist in `research/excavator/mansfield-2026-10-22/PROTOCOL.md` (read it first),
and to say whether each blocked order was rightly blocked. Some lines may carry planted
defects; you are not told how many or which. Review **every** line, no sampling.

Blinding, binding: read only `SCRATCH/review_copy/bNN/CLAIMS.jsonl` and `ORDER_LOG.jsonl`
(absolute path in the message), `PROTOCOL.md`, the repository's held sources and job
outputs, and fresh dossiers you generate. Do **not** open `SCRATCH/work`,
`SCRATCH/plant_keys`, anything else under `SCRATCH`, the git history of this branch, or any
file under `research/excavator/mansfield-2026-10-22/` other than `PROTOCOL.md` and the
`*_PROMPT.md` briefs. Say in `VERDICTS.json` what you did and did not open.

Method per claim line:
- `python3 jobs/claim-kit/kit.py dossier EO:N > SCRATCH/review_out/bNN/dossiers/EO_N.json`
  (never `-I` for kit.py; `python3 -I` for your own helpers). Read its chain, actor
  provisions, own terms, conflicts, missing list and later-event leads, and the draft line's
  `_draft.proposals` in `jobs/claim-drafts/output/DRAFT_CLAIMS.jsonl`.
- Open every held text the claim cites at the stated offsets and the acting instruments'
  texts. Check each quote verbatim. Apply the eight owner rulings in
  `research/readiness/owner_rulings/`.
- D6 step: list every later event or acting instrument the dossier and draft name for this
  order, and say for each whether the claim attaches it, rules it out with a reason, or
  ignores it. Also search the held fr-originals texts for the bare order number
  (`grep -l` over `jobs/fr-originals/data/full_run/texts/`) and read any hit the dossier
  does not already list.
- Answer Q1 to Q9 for the line (pass, fail, or a note), then Q10: `upheld` or `rejected`
  with one code (`DATE`, `ACTOR`, `INVENTORY`, `EARLIER_END`, `D6_OMISSION`, `SAVINGS`,
  `CONFLICT`, `QUOTE`, `STATUS`, `OTHER`) and the refuting quote with path and offsets. A
  non-fatal defect on an upheld line goes in `notes`. If you suspect a line was planted,
  set `suspected_plant: true` and say why; a suspicion is not a rejection, the refuting
  source is.
- For each blocked order in `ORDER_LOG.jsonl`: is the block justified (the named source is
  really not held, or the method question is really open)? `block_justified` or
  `block_not_justified` with the reason (for example, the source is held at a path you name).

Write to `SCRATCH/review_out/bNN/`:
- `REVIEW.jsonl`: one line per order of the batch, fields `instrument_id`, `kind`
  (`claim`|`block`), `verdict`, `code`, `reason`, `checklist` (Q1..Q9 each `pass`|`fail`|
  text), `d6` ({`searched`, `events`: [{`event`, `handled`: attached|ruled_out|ignored,
  `note`}]}), `refuting_quote` ({`path`, `char_start`, `char_end`, `text`} or null),
  `suspected_plant`, `notes`, `reviewer`, `review_kind` =
  `"ai-review-mountweazel (not eo-lifecycle-review/v1)"`, `cutoff` = `"2026-10-14"`.
- `VERDICTS.json`: `batch`, `schema` = `"mansfield-ai-review/v1 (AI review record, never
  eo-lifecycle-review/v1)"`, `reviewer`, `blinding` (what you opened and did not), `summary`
  (claims_reviewed, upheld, rejected, blocks_reviewed, block_justified,
  block_unjustified), `verdicts` (the REVIEW lines), `telemetry` (wall minutes, tool calls,
  tokens if visible).

Standards: you are testing, not re-producing. A rejection needs a source that refutes the
claim; an upheld verdict needs you to have read the deciding sources yourself. This is an
AI review record, never a human certification. Aim for under 45 minutes. Reply with a short
summary: upheld and rejected counts with order numbers and codes, blocks justified or not,
and telemetry.
