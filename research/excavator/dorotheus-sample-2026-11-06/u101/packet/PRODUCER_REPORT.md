# Producer report u101 (dorotheus, undecided route)
Start 2026-11-06T10:11:52Z; end 2026-11-06T10:12:54Z (wall time cut short because all members blocked at the source check).

## Outcomes (all 6 blocked; STATUS_DECISION.json left blank for each)
Common reason: the only held original is not acceptable_as_original (page check required), so the status proposal cannot be made.
- EO:1027: ProQuest replica (archival_replica_scan_pending_codebook). Missing: official printed copy and any ending/CURRENT: record (none held).
- EO:1439: ProQuest replica. Missing: official original and an ending; EO 8380 (1940) only renames the reservation and recites this order.
- EO:575: Wikisource transcription. Missing: official original and any ending/CURRENT: record.
- EO:645: Wikisource transcription. Same.
- EO:703: ProQuest replica. Missing: official original and an ending naming this order (EO 7503's hits cite a different Hawaii order No. 703 of 1936).
- EO:809: Wikisource transcription. Same as 575.

## Time
Each order: reading the view's source grade and acceptable_as_original; no clause inventory built, per instructions.

## Checks
apply: blocked 6. batch-check: 0 claims, 0 failures, outcomes blocked 6. Geddes: 0 flags, 0 coverage gaps; no resolutions needed.
Final applied dir: applied-v1. ASSESSMENT.jsonl written (6 rows; readings mostly "unknown", as no ending or current record is held).

## Files opened beyond views
decisions.csv, clauses.csv (head), one STATUS_DECISION.json, DISPATCH_CHECK.json (head). No PACKET.json/READ.md.
I did not read the owner rulings or the other reference documents because no order reached a substantive decision. Only PRODUCTION_ROUTE.md and part of BATCH.md were read.

## Tool defects
None.

## Assessment supplement
Ran cruden.py number for all six (outputs in /tmp/claude-0/dorotheus-wave/work/u101/EO_N.json) and read each working text. Only later instrument naming one of these orders: EO 8380 (1940), which renames and enlarges the Cold Springs refuge and recites EO 1439 without revoking it. EO 7502/7503 hits for 703 cite a different 1936 Hawaii order. Operative force stays "unknown" for all six, since no held source reaches 2026-10-14; formal validity is "unrevoked" for 1027, 1439 and "unknown" otherwise. Rows rewritten with command kind (one-time, standing, body, land) in each basis. decisions.csv, clauses.csv, STATUS_DECISION.json and applied-v1 unchanged.
