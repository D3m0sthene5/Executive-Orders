# Producer report: u202 (undecided route), producer dorotheus

Start 2026-11-06T10:16:31Z; end 2026-11-06T10:25Z (UTC). Final applied dir: `applied-v1`.

## Outcomes
- EO:10513 **submit** (awaiting_status_review, the expected state): single standing designation clause, expressly revoked by EO 13245 sec. 4 (signed 2001-12-18, FR original held). STATUS_DECISION filled: no.
- EO:10534 **blocked**: first end only bounded by EO 11382 sec. 16 (1967-11-28); missing a dated record of completion of the Seaway construction (EO 10771's proviso ends Defense supervision on completion). STATUS_DECISION filled: no (express revocation).
- EO:10438 **blocked**: sec. 2 (records/personnel transfer) has no held performance source; Reorganization Plan No. 3 of 1953 not held; bound 1962-09-27 (EO 11051 sec. 604, qualified). STATUS_DECISION filled: no.
- EO:9762 **blocked**: bound 1946-12-12 (EO 9809); performance on 1946-07-25 not shown for OES/Director transfers; no express revocation held. STATUS_DECISION filled: no.
- EO:9703 **blocked, no status**: only amended "to conform" (EO 10122, 10400, 11160); no ending or CURRENT record. Left blank.
- EO:9939 **blocked, no status**: Board continues until terminated by the President; no termination held; report deadline is not an end. Left blank.

## Time
10513: short, one revocation. 10534: tracing EO 10771 restatement and 11382. 10438: reading 11051 qualified revocation and 10461. 9762: reading 9809/9841 to decide performance vs consolidation. 9703: inventory is dozens of regulation sections, no ending. 9939: cruden number, no termination.

## Checks
apply: blocked 5, awaiting_status_review 1. batch-check: 6 members, 0 claims checked (no strict claim yet), actionable_failures [], Geddes flags 0 (GEDDES_RESOLUTIONS.json empty). Status decisions validated with status_overlay._decision_errors: no errors for the four filled.

## Other
Opened beyond views: EVIDENCE.json (history/evidence ids), RATIONALES.json/decisions.csv/clauses.csv, LOOKUPS.md; ran cruden number for 9703 and 9939 (scratch). Read held texts of EO 13245, 11382, 10771, 11051, 10461, 9809, 11160, 10122, 10400, 9970. Tool defects: base ACT id for EO:10534>EO:11382 carries unrelated text (sec. 2); used the @884108b312386666 variant. `python3 -I kit.py` fails on import (run without -I).
