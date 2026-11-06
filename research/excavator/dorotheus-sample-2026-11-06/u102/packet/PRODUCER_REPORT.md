# Producer report u102 (dorotheus)
Start 2026-11-06T10:11:51Z; end 2026-11-06T10:13:13Z. Final applied dir: applied-v2 (applied-v1 was a failed first apply before decisions.csv was filled; left untouched).

## Outcomes (0 submitted, 5 blocked, 1 unresolved)
- EO:1513 blocked: only a replica scan transcription held, not acceptable_as_original, no CURRENT/ending record. Missing: official original and a later land order or revocation.
- EO:1522 blocked: original acceptable, but no ending (the TERM records are only the "valid existing rights" saving) and no CURRENT record. Missing: later public land order/BLM record or current-law text on the withdrawal of N1/2 NE1/4 sec. 29 T8S R21E.
- EO:2021 unresolved (dispatch-blocked): ORIGINAL:EO:2021 and CLAUSES:EO:2021#whole not held.
- EO:2412 blocked: only a replica scan held, no ending or CURRENT record.
- EO:2978 blocked: replica scan only. EO 3067 (March 1919, OCR) recites it is in lieu of EO 2978 and revokes it; its day is illegible and no official original of either is held.
- EO:3923 blocked: replica scan only; no ending or performance source.
STATUS_DECISION.json files left blank for all.

## Time
All orders were decided from views, no extended search, since the precheck showed no acceptable path.

## batch-check
6 members, 0 claims, blocked 5, unresolved 1, 0 actionable failures.

## Geddes
0 flags; GEDDES_LINT.json written by batch-check; no resolutions needed.

## Files opened beyond views
LOOKUPS.md, decisions.csv, clauses.csv, RATIONALES.json (head), IR1912 p53 text, APP EO_1522 text (head), EO_3067.txt (grep).

## Tool defects
None.

## Assessment supplement
Read the working text of EO:1513, 2021, 2412, 2978 and 3923 and the held IR1912 text for EO:1522. Ran cruden number for all six into /tmp/claude-0/dorotheus-wave/work/u102/EO_N.json. Only EO:3067 (naming EO:2978) is a held later instrument; the other hits are Wikisource navigation pages. ASSESSMENT.jsonl basis fields were rewritten with the kind of command. EO:2978 is "no"; the other five stay "unknown" because no held source shows an end or continuation. decisions.csv, clauses.csv, STATUS_DECISION.json and applied-v* are unchanged.
