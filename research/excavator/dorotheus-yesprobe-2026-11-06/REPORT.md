# Dorotheus YES probe, 2026-11-06: a random 30 of the provisional-YES Federal Register orders

`DRAW.json` drew 30 orders at random (seed 20261106) from the 359-order stratum `production.claim_ready.yes.fr`. They ran through the ordinary decided claim-kit route in five era-grouped packets (`y01`–`y05`), using the ice core's tested tools with Sonnet producers.

Each packet with a submission was reviewed by two separate-context Sonnet blind reviewers. Each review set carried a date-shift control and one Mountweazel plant; a third reviewer was added where an arm missed a plant. A claim filed only if every arm that saw it upheld it. No order was replaced.

**filed_per_attempt = 7 / 30 = 0.233.** Counting only orders a producer worked, it is 7 / 25 = 0.28. The ice core measured 11 / 30 = 0.367 for this stratum.

## Outcomes

| Outcome | Orders |
|---|---|
| Filed (`research/readiness/claims/dorotheus-2026-11-06-yesprobe.jsonl`) | 7: EO 10057, 10104, 10153, 11219, 11600, 11961, 12046 |
| Already filed elsewhere (ready_existing) | 1: EO 10967, filed by the ice core yesterday; the draw's pool predates it |
| Existing incomplete claim of another owner | 1: EO 13540 (`astra-2026-10-17-p3originals.jsonl`); not prepared |
| Dispatch-blocked (custody record only) | 3: EO 13848, 14024, 14373 |
| Blocked by the producer | 17 |
| Upheld but not filed (batch control missed) | 1: EO 14131 |

Filing was a single `kit.py complete --publish` over all 28 prepared members, with 3 controls, all caught. It ran inside a publication packet prepared for exactly the seven filed orders, whose dossiers are byte-identical to the producing packets'. `REPORT.md` in the sample folder explains why. The result: 7 published, 0 exceptions, 0 certified.

## Blockers (exact sources in `../dorotheus-sample-2026-11-06/DISPOSITION.csv`)

| Cause | Orders |
|---|---|
| A later instrument held only as an APP or Common Crawl mirror, or held but not registered as a source | 7: EO 10694 (EO 13286), 10431 (EO 13709), 12382 (EO 12692), 11396 (registered text is an AEC rule, not the order), 11023, 12294 and 13551 (NEA continuation notices of 2025–2026 held as text but not registered), 13830 (EO 14085 custody only) |
| Source held only as a custody record | 5: EO 9242A (EO 14085 FR PDF), 10431, and the three dispatch blocks |
| One-time commands with no source showing performance | 4: EO 12028, 12146, 12748, 11311 |
| Ending statute or public land order not held | 2: EO 7993 (PLO 2711), 12163 (Pub. L. 105-277 §1422) |
| Current-law source not held / wrong text | 2: EO 10111, 12445 |
| Owner-routed | 1: EO 13540 |
| Batch control missed | 1: EO 14131 |

The cause groups come from coordinator keyword rules (`../dorotheus-sample-2026-11-06/CAUSES.json`). Two orders appear under two headings above because their blocker names both kinds of gap.

## Review and controls

| Batch | Arms | Date-shift control | Mountweazel plant | Filed |
|---|---|---|---|---|
| y01 | A, B, C | EO 10153: caught by A, B, C | D3: missed by A, caught by B, C | 3 |
| y02 | A, B, C | EO 11219: caught by A, B, C | D6: missed by A, B; caught by C | 1 |
| y03 | A, B | EO 12046: caught by A, B | D7: caught by A (lenient only) and B | 3 |
| y05 | A, B, C | EO 14131 signing-date shift: caught by B only | D5: caught by A, B, C | 0 |

A plant counts as missed when an arm did not reject it. Two packets yield the missing rows: y04 had no submission, so it had no review; and y05's control was missed by arms A and C, so under the rule fixed in advance that batch does not file.

**Bentham gate** (`bentham.py gate --action production.claim_ready.yes.fr --batches BATCHES.json`): **STOP**, because "planted control missed in batch y05; quality failure outranks economics". The posterior yield is 0.244 (80% interval 0.149–0.348), against a breakeven of 0.164.

## Cost

| Batch | Worker cost (CLI-reported, API-equivalent) |
|---|---:|
| y01 | $6.33 |
| y02 | $5.34 |
| y03 | $6.93 (includes attempt 2) |
| y04 | $2.32 |
| y05 | $3.82 |
| **Total** | **$24.74** |

The total is $3.53 per filed claim, against the ice core's $2.70. Cumulative context per attempted order is about 2.7M tokens, against a 150k target that was not met. The YES producers took 39–76 turns per packet.

## What would raise the yield

1. **Register the official Federal Register texts of later orders held only as mirrors**: EO 13286, 13709 and 12692. Also register the 2025–2026 National Emergencies Act continuation notices already held as text. Seven blocked orders cite exactly these.
2. **Retain the custody-only bytes** for EO 13848, 14024 and 14373, and the EO 14085 FR PDF (87 FR 60541).
3. **Re-review EO 14131 in a fresh batch whose control can be caught.** Every arm upheld it after reveal. The signing-date plant used for a claim with no ends or later events was missed by two of three arms.
