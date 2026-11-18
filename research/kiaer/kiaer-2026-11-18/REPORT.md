# Kiaer tier probe, 2026-11-18: stopped at the plan review

**The probe did not run.** Codex reviewed the two launch plans against Augur's checks and rejected both, twice.
The owner's rule for this probe is to stop after a second rejection. Stage 0 and the full run were not started, no
owner exception was recorded, and no claim, status, census row, codebook or tracker file changed.

## What was done

| Step | Result |
| --- | --- |
| Tools | `Relay-kiaer.zip` extracted (`SOURCE.txt`). Branch `claude/kiaer-probe-2026-11-18` from main `18d93ad17d`. |
| Preflight | `claude`, `codex`, `node` and `npm` are not on PATH on this PC. Relay was pointed at the CLI binaries bundled with the two desktop apps: Claude Code 2.1.326 (owner signed in during the session) and codex-cli 0.167.0-alpha.3.2 (ChatGPT login). `bridge doctor`: both signed in. |
| Tests | 33 of 33 Relay tests passed; selftest exit 0. After the fixes in `CHANGES.md`: 38 of 38; selftest exit 0. |
| Census (no tokens) | 15,002 numbered orders: T0 70, T1 2,245, T2 9,144, T3 1,940, T4 348, T5 1,255, T6 0. 2,938 undecided orders carry a finding-aid rule lead. 1,816 unnumbered identities. Machine estimate from committed job outputs (`CENSUS.json`); not corrected by any sample. |
| Draw (no tokens) | Seed 20261118, frame `40636c0c08be8c2ade0f46b25ec3967a2538b415bd09ca0fbcfb80fd4c51d884`; 11 cells, 235 orders at most, 29 in stage 0. |
| Smoke test | PASS. EO 9703 (cell C04) through producer, review and repair. 167,712 units, 318,823 raw tokens, every turn measured, none estimated (`SMOKE.json`). At that cost about 35 orders fit in 6M units and about 59 in 10M; one order, costs vary. |
| Augur | Both plans refused only on the grounds the owner had accepted: not in Bentham's plan, the stage-1 configuration ramp, and the review binding (`review/AUGUR_receipt_stage*.json`). All six matched lessons answered. |
| Review 1 (Codex, gpt-6-astra, high effort) | Reject, both plans (`review/CODEX_REVIEW_1.json`). It saw only `run.py` and `__main__.py`. Real defects found: stage 0 raised its own ceiling; nothing bound a run to the reviewed plan; the full-run condition was not enforced; an empty audit comparison counted as agreement. |
| Fixes | `CHANGES.md`, `CHANGES.diff`. |
| Review 2 (same reviewer, all code supplied) | Reject, both plans (`review/CODEX_REVIEW_2.json`). Seven remaining grounds, listed at the end of `CHANGES.md`. It found no path for a model turn to write to the repository, file a claim or change a status. |

## Cost

| Item | Units | Raw tokens |
| --- | ---: | ---: |
| Smoke test (3 turns) | 167,712 | 318,823 |
| Codex plan review 1 | 36,811 | 76,333 |
| Codex plan review 2 | 113,326 | 204,452 |
| **Total** | **317,849** | **599,608** |

Units are 0.1 x cache reads + other input + 4 x output. The coordinating Claude session's own usage is not in
this table.

## What the numbers support

Nothing about tier moves: no sample ran. The census gives the machine tier shares only. The one measured order
suggests the 10M-unit budget buys about 59 orders, a quarter of the 235 the draw allows, so the cells would have
been shrunk to about 3 to 5 orders each.

## To resume

The data folder holds the census, draw, plans and review records. From inside a Claude desktop session it is
`%LOCALAPPDATA%\Relay\kiaer-2026-11-18`; on disk that is
`C:\Users\danie\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Local\Relay\kiaer-2026-11-18`.
`python -m kiaer stage0` now refuses to start until `WAVE_stage0.json` carries an approving review bound to its
hash. The owner's decision is Kean ask `A-20261118-kiaer-review-rejected`.
