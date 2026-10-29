# Mansfield: judgment-only claims for modern orders (2026-10-22)

Production run on the "only judgment left" pool. Every claim here is an AI hypothesis for
human review. The human-certified whole-lifecycle count stays **0**. No status, codebook or
census changed.

## Pool and sample

`POOL.csv`: 743 orders (564 NO, 179 YES) from `TODO_BY_ORDER.csv` rows with
`only_judgment_left = yes`, `estimated_effort = small`, a provisional status, the text step
done and not ready in the tracker, and no claim on main. The brief estimated about 860;
74 of those already had claims and 43 have the text step open. Batches of 10 drawn with
seed 20261022 over the sorted NO ids (`BATCH_PLAN.json`). Three NO batches ran (b01-b03,
30 orders). The YES stratum was not attempted because the gate failed.

## Result against the gate

| Measure | Value | Gate |
|---|---|---|
| Orders attempted | 30 | |
| Claims submitted by producers | 14 | |
| Blocked by producers (all judged justified by the reviewer) | 16 | |
| Genuine claims reviewed blind (plants excluded) | 9 | |
| Genuine upheld / rejected | 9 / 0 | rejections 0% (limit 25%): **passes** |
| Upheld genuine per attempt, blind review only | **0.30** | at least 0.5: **fails** |
| Planted orders' genuine lines upheld after reveal | 5 | |
| Upheld per attempt counting after-reveal re-reviews | 0.47 | at least 0.5: **fails** |
| Plants placed / caught | 5 / 4 (0.8) | |
| Claims filed | **14** | |
| Mechanical failures on filed claims (gate + checker) | 0 | |

The gate failed on conversion, not on quality: every genuine claim the producers submitted
was upheld, but 16 of 30 orders could not be claimed at all. So the run stops after 30
attempts, as the brief requires, with the 14 upheld claims filed.

**Forecast (Llull L-20261022-1):** p50 0.45 (interval 0.045 to 0.9) for upheld per
attempt; measured 0.30 (outcome O-20261022-1), inside the interval and below p50. Plant
catch forecast L-20261022-2: p50 0.9; measured 0.8 (O-20261022-2). Llull notes the
measured 0.30 exceeds its strict prerequisite coverage share (0.27), so its gate again
missed a route.

## Why the pool did not convert

Of 16 blocks (all justified on review):

| Reason | Orders | Count |
|---|---|---|
| The ending text is held in the repository but the claim-kit dossier has no evidence span for the acting provision, so the kit cannot cite it (needs an `act_overrides` record with independent review, or a kit fix) | 10915, 11927, 12975, 9333, 12607 (dossier original text truncated), 8072 (dossier clauses are EO 8071's) | 6 |
| Emergency-board report date not held; the report-deadline ruling asks for it, and for 12414 and 12393 the order's own terms end on or after the report | 10319, 12370, 12414, 12393 | 4 |
| Ending Public Land Order text not held | 8173 (PLO 1660), 8505 (PLO 1649), 8915 (PLO 1070) | 3 |
| Statute that keeps the order in effect not held | 12810 (Pub. L. 103-160 sec. 1511) | 1 |
| Open method question for the owner | 11877 (parent revoked "as amended", independent sec. 2 command), 12921 (parent's fixed sunset vs later express revocation) | 2 |

So "only judgment left" as the draft job computes it is too generous for this pool: in a
third of the orders the deciding source is held but not wired into the dossier, and in
another third a source the owner's rulings now require (report dates, Public Land Orders)
is not held. Eight fetch lines were enqueued for the missing sources.

**Method questions raised for the owner** (recorded in the order logs, no claim rests on
them): does revoking a parent order "as amended" end an amending order that no instrument
names (10915, 11927, 11877)? Does a parent's fixed sunset set by an order that does not
name the amending order end it (12921)? Does a later citation of a revoked order (EO 14096
citing 12975) matter?

## Per batch

| Batch | Attempted | Submitted | Blocked | Genuine upheld / rejected | Plants caught | Filed (after reveal in italics) |
|---|---|---|---|---|---|---|
| b01 | 10 | 2 | 8 | 1 / 0 | 1 of 1 (D3) | 10390, *10926* |
| b02 | 10 | 5 | 5 | 3 / 0 | 1 of 2 (date swap caught; D6 omission missed, `noticed_but_accepted`) | 10622, 11005, 11310, *13032*, *10972* |
| b03 | 10 | 7 | 3 | 5 / 0 | 2 of 2 (D6, date swap) | 9922, 11040, 11078, 11135, 13997, *10312*, *5825* |

Filed files: `research/readiness/claims/claude-mansfield-b01-2026-10-22.jsonl` (2),
`-b02-` (5), `-b03-` (7). All 14 pass `claim_gate.validate_claim` and the claim checker
with 0 mechanical failures; 3 are `pass_with_unverified` because a cited source is held
only as a custody record (EO 10390: the APP transcription of EO 10480 as the end source,
although the official text is held and quoted; EO 10926 and EO 10622: emergency-board
reports).

## Planted controls

One scratch planter per batch, key sealed outside the repository, reviewer not told the
count. Blinding is instructed, not technical (same account). Details per batch in
`bNN/PLANTED_CONTROLS.md`.

- Caught (4): EO 10926 D3 cut quote (also fails `kit.py check`, so partly mechanical);
  EO 13032 date swap; EO 10312 D6 omission of EO 11051; EO 5825 date swap from the
  neighbouring order's effective-date sentence.
- Missed (1): EO 10972 D6 omission of the EO 11036 insertion. The reviewer noted the gap
  and upheld because the event changes no date or clause state. D6 omissions remain the
  weak spot (Mountweazel MW-C2 caught 1 of 3).

**After-reveal re-reviews.** The genuine line of each planted order was re-reviewed by the
same independent reviewer after the key was opened, against the full checklist with
`kit.py check`, quote verification and the D6 step repeated; all 5 were upheld and filed,
and are counted separately (`upheld_after_reveal`) so the blind rate (0.30) and the rate
with them (0.47) are both visible. This departs from the Y2LEAD precedent, which did not
file them; the owner can drop those 5 lines if he prefers the stricter rule.

## Cost and time

`COST.md` and `COST.json`. Estimated $55 of Opus 5.5 token value at list prices over 20
agent runs (about 108 agent-minutes), with an upper bound of $291 if nothing had been
cached. Per filed claim: about $3.90 estimated and 7.7 agent-minutes; per blind-upheld
claim about $6.10. Token counts are the harness's transcript sizes; the API's own
input/output/cache split was not visible, so the dollar figures are estimates.

## What was not verified

- No human read any claim. The certified count is 0.
- The reviewer's blinding is instructed only.
- Token costs are estimated from transcript sizes, not metered.
- Three filed claims cite a custody-record-only source (listed above).
- The readiness tracker has not run on these claims; the expected change is up to 14 more
  orders ready for human review (AI-upheld tier), fewer if the tracker's rules reject a
  custody-record-only source.

## Files

- `OUTCOME.json`, `BATCH_PLAN.json`, `POOL.csv`, `PROTOCOL.md`, the four `*_PROMPT.md`
  briefs, `USAGE.jsonl`, `COST.json`, `COST.md`.
- `b01/`, `b02/`, `b03/`: producer claims and logs, review records (`REVIEW.jsonl`,
  `VERDICTS.json`, `REVIEW_AFTER_REVEAL.jsonl`), checker outputs, `TALLY.json`,
  `PLANTED_CONTROLS.md`.
- Llull: forecasts L-20261022-1 and -2, census D-20261022-1, outcomes O-20261022-1 and -2.

SUMMARY: 30 judgment-only NO orders attempted; 14 claims filed (9 upheld blind, 5 upheld
after reveal), 0 genuine rejections, 16 justified blocks, 4 of 5 plants caught. Upheld per
attempt 0.30 blind (0.47 with re-reviews) against a 0.45 forecast and a 0.5 gate, so the
run stopped. The pool did not convert because held sources are not wired into the dossiers
and report dates and Public Land Orders are not held. Certified: 0.
