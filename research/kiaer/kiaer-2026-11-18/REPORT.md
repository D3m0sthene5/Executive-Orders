# Kiaer tier probe, 2026-11-18: stopped at the plan review (three rejections)

**The probe did not run.** Codex reviewed the two launch plans against Augur's checks and rejected both three
times. The owner's rule was to stop after a second rejection; the owner then directed "fix and re-review", and the
third review rejected again on three narrower grounds. Stage 0 and the full run were not started, no owner exception
was recorded, and no claim, status, census row, codebook or tracker file changed.

## What was done

| Step | Result |
| --- | --- |
| Tools | `Relay-kiaer.zip` extracted (`SOURCE.txt`). Branch `claude/kiaer-probe-2026-11-18` from main `18d93ad17d`. |
| Preflight | `claude`, `codex`, `node` and `npm` are not on PATH on this PC. Relay was pointed at the CLI binaries bundled with the two desktop apps: Claude Code 2.1.326 (owner signed in during the session) and codex-cli 0.167.0-alpha.3.2 (ChatGPT login). `bridge doctor`: both signed in. |
| Tests | 33 of 33 Relay tests passed in the zip; 58 of 58 now; selftest exit 0 (`CHANGES.md`). |
| Census (no tokens) | 15,002 numbered orders: T0 70, T1 2,245, T2 9,144, T3 1,940, T4 348, T5 1,255, T6 0. 2,938 undecided orders carry a finding-aid rule lead. 1,816 unnumbered identities. Machine estimate from committed job outputs (`CENSUS.json`); not corrected by any sample. |
| Draw (no tokens) | Seed 20261118, frame `40636c0c08be8c2ade0f46b25ec3967a2538b415bd09ca0fbcfb80fd4c51d884`; 11 cells, 235 orders at most, 29 in stage 0. |
| Smoke tests | Both PASS on EO 9703 (cell C04), producer, review and repair, every turn measured (`SMOKE.json`). First, on the zip's code: 167,712 units. Second, on the changed code: 186,931 units; the slowest turn took 112 seconds of the 900 allowed; the producer turn cost 0.93 dollars of its 2-dollar ceiling. At these costs about 32 to 35 orders fit in 6M units and 53 to 59 in 10M. |
| Augur | Both plans are refused only on the grounds the owner had accepted: not in Bentham's plan, the stage-1 configuration ramp, and the review binding (`review/AUGUR_receipt_stage*.json`). All seven matched lessons answered. |
| Review 1 (Codex, config default gpt-6-astra, high effort) | Reject, both plans (`review/CODEX_REVIEW_1.json`). Four real defects; fixed. |
| Review 2 (all code supplied) | Reject, both plans (`review/CODEX_REVIEW_2.json`). Seven grounds; the run stopped and was reported. |
| Fixes after review 2 (owner: "fix and re-review") | All seven grounds (`CHANGES.md`, round 2). |
| Review 3 | Reject, both plans (`review/CODEX_REVIEW_3.json`). It found the seven grounds met except part of ground 4, and three remaining grounds: `reconcile --units nan` passed validation and erased a charge; empty or partial usage from a provider counted as measured; four plan statements were stronger than the code. It again found no path for a model turn to write to the repository, file a claim or change a status. |
| Fixes after review 3 | The three grounds are fixed and tested (`CHANGES.md`, round 3). **These fixes and the current plans (`review/WAVE_stage*.current-unreviewed.json`) have not been reviewed.** |

## Cost

| Item | Units | Raw tokens |
| --- | ---: | ---: |
| Smoke test 1 (3 turns) | 167,712 | 318,823 |
| Codex plan review 1 | 36,811 | 76,333 |
| Codex plan review 2 | 113,326 | 204,452 |
| Smoke test 2 (3 turns) | 186,931 | 335,404 |
| Codex plan review 3 | 140,029 | 366,917 |
| **Total** | **644,809** | **1,301,929** |

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
(now `cd4519959b2f54a58510198196f2bf2ca9f2a2cfadc1942b0e438b2702c31a80`; stage 1:
`51588be2136bb099da087c0a9a8850b7e0456ed651e5a6c3208f4a8af1f3c79c`). The owner's decision is Kean ask
`A-20261118-kiaer-third-rejection`.
