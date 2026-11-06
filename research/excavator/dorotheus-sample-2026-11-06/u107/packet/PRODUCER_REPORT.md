# Producer report u107 (dorotheus)
Start 2026-11-06T10:13:17Z; end 2026-11-06T10:14:14Z (clock as recorded by the sandbox).

## Outcomes
- EO:7081 blocked: original is the APP mirror transcription (node 375216, sha256 60f4029a...c4b9), acceptable_as_original=False, page check outstanding; dossier holds no ACT:/TERM:/ACTOR_TEXT: or CURRENT: record. STATUS_DECISION left blank. Best reading: executed one-time revocation of EO 6497 (1935-06-20); no continuing force.
- EO:7164 blocked: original is a machine-read djvu copy (sha256 10b7e443...6cc9), acceptable_as_original=False; held ACT: records are only amendments EO 7319 and EO 7433 (not ends); no held source for the end of the ERA 1935 student-aid authority; no CURRENT: record. STATUS_DECISION left blank.
- EO:6920B, 7032, 7114: dispatch-blocked (outcome left `unresolved` as prepared); assessment rows from views only. Missing: official originals (custody_record_only).

Time: all five were decided by the precheck (no acceptable original), so no per-order research was needed; most time went into reading views.

## batch-check
5 members; 0 claims; outcomes unresolved 3, blocked 2; actionable failures 0.
## Geddes
0 flags, 0 coverage gaps; no resolutions needed.
## Beyond views
Opened undecided/EO_7164 and EO_7032 DOSSIER.json (evidence keys only) and EO_7081 STATUS_DECISION.json. No tool defects.

## Assessment supplement
Ran cruden number for all five orders (outputs in /tmp/claude-0/dorotheus-wave/work/u107/) and read held texts plus EO 7319 and 7433. Rewrote ASSESSMENT.jsonl rows: 6920B no (one-time dismissal); 7081 no (one-time revocation); 7032, 7114, 7164 stay unknown (land withdrawal, permissive land modification, standing regulation with no held ending). decisions.csv, clauses.csv, STATUS_DECISION.json and applied-v1 untouched.
