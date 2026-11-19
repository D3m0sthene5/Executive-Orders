# Kiaer tier probe, 2026-11-18: stopped at the plan review (four rejections)

**The probe did not run.** Codex reviewed the two launch plans against Augur's checks and rejected both four
times. The owner's rule was to stop after a second rejection; the owner then directed a third and a fourth review.
The third rejected on three narrower grounds and the fourth on one. Stage 0 and the full run were not started, no owner exception
was recorded, and no claim, status, census row, codebook or tracker file changed.

## What was done

| Step | Result |
| --- | --- |
| Tools | `Relay-kiaer.zip` extracted (`SOURCE.txt`). Branch `claude/kiaer-probe-2026-11-18` from main `18d93ad17d`. |
| Preflight | `claude`, `codex`, `node` and `npm` are not on PATH on this PC. Relay was pointed at the CLI binaries bundled with the two desktop apps: Claude Code 2.1.326 (owner signed in during the session) and codex-cli 0.167.0-alpha.3.2 (ChatGPT login). `bridge doctor`: both signed in. |
| Tests | 33 of 33 Relay tests passed in the zip; 62 of 62 now; selftest exit 0 (`CHANGES.md`). |
| Census (no tokens) | 15,002 numbered orders: T0 70, T1 2,245, T2 9,144, T3 1,940, T4 348, T5 1,255, T6 0. 2,938 undecided orders carry a finding-aid rule lead. 1,816 unnumbered identities. Machine estimate from committed job outputs (`CENSUS.json`); not corrected by any sample. |
| Draw (no tokens) | Seed 20261118, frame `40636c0c08be8c2ade0f46b25ec3967a2538b415bd09ca0fbcfb80fd4c51d884`; 11 cells, 235 orders at most, 29 in stage 0. |
| Smoke tests | Both PASS on EO 9703 (cell C04), producer, review and repair, every turn measured (`SMOKE.json`). First, on the zip's code: 167,712 units. Second, on the changed code: 186,931 units; the slowest turn took 112 seconds of the 900 allowed; the producer turn cost 0.93 dollars of its 2-dollar ceiling. At these costs about 32 to 35 orders fit in 6M units and 53 to 59 in 10M. |
| Augur | Both plans are refused only on the grounds the owner had accepted: not in Bentham's plan, the stage-1 configuration ramp, and the review binding (`review/AUGUR_receipt_stage*.json`). All matched lessons answered. |
| Review 1 (Codex, config default gpt-6-astra, high effort) | Reject, both plans (`review/CODEX_REVIEW_1.json`). Four real defects; fixed. |
| Review 2 (all code supplied) | Reject, both plans (`review/CODEX_REVIEW_2.json`). Seven grounds; the run stopped and was reported. |
| Fixes after review 2 (owner: "fix and re-review") | All seven grounds (`CHANGES.md`, round 2). |
| Review 3 | Reject, both plans (`review/CODEX_REVIEW_3.json`). It found the seven grounds met except part of ground 4, and three remaining grounds: `reconcile --units nan` passed validation and erased a charge; empty or partial usage from a provider counted as measured; four plan statements were stronger than the code. It again found no path for a model turn to write to the repository, file a claim or change a status. |
| Fixes after review 3 | The three grounds were fixed and tested (`CHANGES.md`, round 3). |
| Review 4 (owner: "Fourth review") | Reject, both plans (`review/CODEX_REVIEW_4.json`). It found the reconcile fix and the wording met, and every other check passed, with one ground left: the Codex adapter ignored a usage event whose usage field was missing, null or not an object, so a turn with such an event after a valid one was still counted as measured. No write path found. |
| Fix after review 4 | That ground is fixed and tested (`CHANGES.md`, round 4), and checked against the four real Codex event streams on file, which still read as measured. **This fix and the current plans (`review/WAVE_stage*.current-unreviewed.json`) have not been reviewed.** |

## Cost

| Item | Units | Raw tokens |
| --- | ---: | ---: |
| Smoke test 1 (3 turns) | 167,712 | 318,823 |
| Codex plan review 1 | 36,811 | 76,333 |
| Codex plan review 2 | 113,326 | 204,452 |
| Smoke test 2 (3 turns) | 186,931 | 335,404 |
| Codex plan review 3 | 140,029 | 366,917 |
| Codex plan review 4 | 138,460 | 357,764 |
| **Total** | **783,269** | **1,659,693** |

Units are 0.1 x cache reads + other input + 4 x output. The coordinating Claude session's own usage is not in
this table.

## What the numbers support

Nothing about tier moves: no sample ran. The census gives the machine tier shares only. The two measured orders
suggest the 10M-unit budget buys about 53 to 59 orders, a quarter of the 235 the draw allows, so the cells would be
shrunk to about 3 to 5 orders each. The third review also notes that the owner's stage-0 condition "fewer than 40
orders fit" could then stop the full run even when the code's own projection fits.

## To resume

The data folder holds the census, draw, plans and review records. From inside a Claude desktop session it is
`%LOCALAPPDATA%\Relay\kiaer-2026-11-18`; on disk that is
`C:\Users\danie\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Local\Relay\kiaer-2026-11-18`.
`python -m kiaer stage0` refuses to start until `WAVE_stage0.json` carries an approving review bound to its hash
(now `2244eae8b5d77973f94c6f3f54eea0b12ed35c912be2e725b07c0da1e5f8465e`; stage 1:
`4d36c76de394fdaefe49d7065a6a3495d336e252b7ebcd7956a64e1d69cac57a`). The owner's decision is Kean ask
`A-20261118-kiaer-fourth-rejection`.
