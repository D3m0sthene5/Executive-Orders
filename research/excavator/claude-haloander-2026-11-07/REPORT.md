# Haloander wave, 2026-11-07: Bentham ranks 7-9 within a $75 budget

Named for Gregor Haloander, whose 1529 edition of the Digest was checked against the manuscripts. Most of this
wave's paid work was checking held transcriptions against newly held official GPO printings.

**Result: 25 lifecycle claims filed.** Ready went from 992 to 1,017 in the completion's tracker replay; the published
tracker moves once PR #222 is merged and the tracker reruns. The wave also produced 3 isolated status-overlay
proposals, which await the owner's adoption. No status, census or codebook changed. Human certified: **0**.

Measured cost was **$61.78** API-equivalent at Necker list prices, from `telemetry/AGENT_USAGE.csv`:

| Role | Model | Cost |
|---|---|---:|
| Coordinator | Opus | $44.45 |
| Producers (4) | Sonnet | $7.49 |
| Reviewers (5) | Opus | $9.84 |

## Before spending: the plan and the tracker had moved

The plan was rebuilt on main `b8223fd55`. The ranks were unchanged, but two strata had changed members (`evidence/strata-recomputed/`, `evidence/PLAN.recomputed.md`).

- **#8 recovery.custody_stranded, 48 orders.**
  - 13 were already ready.
  - 7 are the known Theophilus blocks.
  - 27 had working-text confirmations made stale by the Photius GPO printings.
  - 1 was EO 12323 (a later-event grade mismatch).
- **#9 production.one_step_away grew from 40 to 219 orders.**
  - 176 are Justinian R3 re-tags (`FIRST_END_UNRESOLVED`), 146 of them Presidential Emergency Board orders.
  - For those board orders, the source ladder already holds 79 board reports. 58 were never requested and 9 were requested but not found (`evidence/R3_BOARD_REPORTS.csv`).
  - The re-tagged claims belong to `justinian-2026-11-06-r3-retag`, which sorts after any `claude-2026-11-07` file. Any correction of them is therefore a replacement proposal that needs owner adoption.

**claim-kit had not rebuilt on main since 2026-11-06.** Its dossiers froze the Lachmann records from before Photius, so `prepare` refused every stale member. Two defects blocked the rebuild, and both are fixed:

- **PR #219:** `population_contract.json` pins `research/dorotheus/OWNER_RULINGS.md`, but claim-kit's `inputs.txt` did not declare it, so the runner never materialized it.
- **PR #221:** the R9 alias `EO:7933a -> EO:7933A` was not applied by claim-drafts or claim-kit's `inputs.py`. Both built 4,297 decided orders where the population check expects 4,298.

After that, publication was refused three times because reporting outputs advanced during the 25-minute run. claim-kit finally published on main at `938c1515a`.

## Rank 8 recovery: 28 orders, 25 filed (`h01/`)

- **Producer.** The rows two reviewers upheld on 2026-11-05 were carried in unchanged, with confirmations reset to false (`tools/carry.py`, `h01/packet/CARRY.json`). A Sonnet producer compared each APP transcription word by word with its Photius GPO printing, re-confirmed identity, completeness and pages, and rechecked the legal content.
- **Result.** 26 claims were submitted, and the actual checker passed all 26.
- **Producer blocks.**
  - EO 8907: APP "47 Stat. 382, 401" against GPO "404", inside the quoted span.
  - EO 12323: the source for the EO 12366 later event is held only as a custody record.
- **Review.** Two independent blind Opus arms reviewed the batch. Both caught both planted date-shift controls (EO 8412, EO 9010) and upheld the genuine versions after reveal.
- **Review rejection.** Arm B rejected EO 8538: a held FR note reads "Revoked by: EO 8905, September 22, 1941" and the claim does not address it. A claim files only if both arms uphold it, so EO 8538 was not filed.
- **Filing.** `kit.py complete --publish` ran with 0 exceptions and filed `research/readiness/claims/claude-2026-11-07-haloander-h01.jsonl`.
- **Gate.** PILOT (28 attempts, under 30). The probability that this action beats the next one was 1.00. The list is exhausted.

## Rank 7 probe: 30 undecided orders (`DRAW.json`, seed 20261107; `u01`-`u03`, `ux/`)

| Stage | Orders |
|---|---:|
| Drawn | 30 |
| Source-blocked at dispatch | 8 |
| Dispatchable | 22 |
| Held only a transcription or replica (refused by the undecided route; Dorotheus tool defect 1, still present) | 8 |
| Status proposals (all NO) | 7 |
| Accepted by the independent status reviewer (EO 8875 rejected: no held source shows an end) | 6 |
| Upheld by both blind lifecycle arms (planted control EO 10955 caught by both) | 4 |
| Refused by the actual checker | 2 |
| **Filed as isolated replacement proposals** | **3** |

- The two arms rejected EO 12200: its clause end dates conflict with its own reasons.
- The checker refused EO 10955 (its EO 10973 source is custody-record only) and EO 9446 (`order_exists:not_in_universe` in a quoted span).
- The 3 filed proposals are EO 12082, EO 7814 and EO 10733, in `ux/overlay/REPLACEMENT_PROPOSAL.jsonl`. Owner acceptance is false.

Canonical yield is **0 of 30**. Overlay yield is 3 of 30.

**Bentham cannot measure this stratum as built.** `measure.py` computes no `filed_per_attempt.undecided`, and `gate` refuses unranked actions. Every plan will keep listing this probe, whatever is measured.

Measured cost was $12.12 (workers only).

## Rank 9 one_step_away: no paid work

The budget left after ranks 7 and 8 (about $13) is smaller than one board pilot plus its coordination.

The zero-token unlock was done instead. 58 board-report fetch requests were validated and enqueued (`evidence/BOARD_REPORT_REQUESTS.jsonl`; the queue went from 1,120 to 1,178 lines). A legal rule for the board orders is drafted in `tools/prompts/board_rule.txt`:

- the board's command ends by completion of its task on the transmittal-letter date of its report;
- the order's own no-change sentence ends 30 days after that date (inclusive; the exclusive reading is the alternative);
- EO 12553 and EO 12379 stay as the formal disposition.

Corrections of these claims are replacement proposals for the owner, because Justinian owns the claims.

## Files

`BATCHES_recovery.json` and `BATCHES_probe.json` hold the gate inputs. `evidence/DISPOSITION.json` is not pooled (see `pool_basis`). `COORDINATOR_LOG.txt`, `telemetry/` and `tools/` hold the logs, usage and scripts. Completion receipts over 40 MB are stored as lossless `.gz` files, each with `TRACKER_CLAIMS.COMPRESSED.json` recording its SHA-256.
