# Mountweazel and Llull repair

Base: `91116f879978902343dafa88490b9b19587b10da`. This is a code, measurement, and execution-control repair. No legal status or canonical lifecycle claim is changed here.

## Findings reproduced and repaired

The former Mountweazel D6 scorer awarded strict credit to a verdict that mentioned the same EO while identifying a cut quote in another clause. Strict credit now requires the material planted issue and the affected clause, and D6 also requires event identity. Manual adjudication carries its author, reason, source, locus and issue separately from the mechanical match. Missing plants are unscored; genuine flags stay unadjudicated unless explicitly resolved. New fixture keys record instructed blinding and do not claim technical isolation. Controlled tests cover first cessation, performance evidence, partial scope, savings, coherent but wrong premises and unrelated criticism. These screens do not establish legal truth.

Llull previously included unchecked registration in calibration. It now requires verifiable prospective registration, separates retrospective from unchecked records, identifies quantities from the same experiment, and consumes only the current valid outcome correction chain. The original forecasts are untouched. The current forecast must also match its first committed record, so a post-run revision cannot borrow its original registration date. Correction O-20261020-44 records the existing MW-C2 manual result **7/10**, with D6 **0/3**; the original 8/10 outcome remains. Base-rate revision 2 cites that correction and supersedes its original 0.8 record. This experiment remains excluded from prospective calibration because no run directory was declared.

The Lambertini III and Rastell R12553 probes each called a gate passed after inserting one of the three required plants. O-20261020-45 and O-20261020-46 append **untested**, `measured:null`; historical outcomes and actual continuation are preserved. No invented failed-trial number is substituted. The reusable `gates.py` checks the exact recorded counts, verifies pinned observation files before execution, and exits 5 without launching a continuation when the gate is failed, incomplete or malformed. Root integration connects this control to the production continuation path.

Coverage screens now describe observed prerequisite coverage as a **heuristic**, not a proven ceiling. New results do not mistake coverage exceedance for a legal impossibility. Historical labels remain readable.

## Current derived results

The refreshed outputs contain 55 forecasts, 41 measured current outcomes and **37 prospectively scorable quantities in 11 identifiable experiments**. Two retrospective and two unchecked measurements are excluded. Two corrected plant gates are untested. Multiple quantities are correlated within an experiment; 37 does not mean 37 independent trials. The selfscore remains **unproven**: its three observed misses span only two experiments. The output refresh validates source references and correction provenance and writes no ledger records.

## Validation and practical limits

- `python3 -I jobs/mountweazel/test_mountweazel.py`: 38 tests passed, including real repository fixture-leak checks.
- `python3 -I jobs/llull/test_llull.py`: 67 tests, 66 passed and 1 explicitly skipped historical census snapshot whose source blobs are unavailable locally.
- `python3 -I jobs/llull/test_gates.py`: 5 tests passed. A real subprocess sentinel ran only after the complete passing probe with matching evidence hash; incomplete or unpinned probes did not execute it.
- `OUTPUT_DIR=jobs/llull/output python3 -I jobs/llull/job.py`: succeeded with no ledger-check errors.

Earlier failures are preserved in the reproduction artifact or test history: the material-match bug, unchecked registration credit, missing historical source inputs, and the two false plant-gate passes. The two missing Craigellachie current outcome sources were restored before the final successful refresh. `VALIDATION.json` pins the corrected source artifacts and generated output hashes.

Token consumption, cost and productivity savings were not metered and remain unknown. The legal five-claim review is a separate evidence audit under `research/excavator/astra-portfolio-repair-2026-10-20/lambertini-review/`.
