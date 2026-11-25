# Producer report: Lind stage 0, packet p1 (undecided route)

Start 2026-11-12T20:57:04Z. End 2026-11-12T21:08:30Z. Final applied directory: `applied-v1`.

## Outcome per order
- EO:12701 submit (status no): amends EO 12334 sec. 1, spent on issue 1990-02-14; parent revoked by EO 12863 sec. 3.3 (1993-09-13). Basis OWN_TEXT plus PARENT_END.
- EO:11943 submit (status no): typo correction of EO 11941 Schedule 3, spent on issue 1976-10-25; parent superseded by EO 12010 sec. 4 (1977-09-28). The U.S. Code note to 5 U.S.C. 5332, the OFR catalog and the 1989 codification all list the same supersession and are reconciled.
- EO:9447 submit (status no): five clauses (A1(b), A2(b), A3(b), B1, B6 of EO 9356) by inventory override; the three fiscal-year-1945 rows end 1945-06-30 by own terms, B1 and B6 end 1946-07-01 by EO 9744B supersession (signing date 1946-06-29 disclosed as the alternative reading).
- EO:9739 blocked, status decision filled (no): revoked by EO 9834 sec. 3 effective as of 1946-11-01 with a saving for returns ordered before that date and incomplete; end of the saved applicability not shown by any held source.
- EO:14274 blocked: no ending or CURRENT record in the dossier; status proposal cannot be made. Sheet left blank.
- EO:13650 blocked: no ending record; only CURRENT record prints the text; about fifty clauses, performance of the dated tasks not held.
- EO:7841 blocked: no ending or CURRENT record; Alaska Railroad Transfer Act (45 U.S.C. 1201 et seq.) and any public land order not held.
- EO:8678 blocked: no ending or CURRENT record; later land transfers not held. The 1951 Federal Register naval-reservation table lists the order but its "revoked by EO 10264" remark belongs to the American Samoa row.
- EO:9481 blocked: no ending or CURRENT record; Secretary of the Interior's determination and return of the mines not held.
- EO:1957 blocked: original held only as ProQuest replica (acceptable_as_original false). Held EO 2048 (1914-09-15, compilation OCR text) revokes the withdrawal.
- EO:4193 blocked: original held only as ProQuest replica; no ending or CURRENT record.
- EO:4475, EO:4621, EO:4658, EO:4788: dispatch-blocked (mandatory sources not held); rows left as prepared, assessment from the views only.

## What took the time
- 12701: read parent and ending order text (short). 11943: found the 5 U.S.C. 5332 note and reconciled it. 9447: inventory split with offsets, checked EO 9465, 9525, 9583 and 9642 texts for B1/B6 touches, effective-date reading of EO 9744B. 9739: read EO 9834 sec. 3-4. 13650, 14274, 7841, 8678, 9481: reading evidence lists and held-text searches before blocking. 1957: found EO 2048.

## Batch-check counts
Apply: 3 awaiting_status_review, 8 blocked, 4 unresolved (dispatch-blocked). Batch-check: 15 members, 0 claims checked (undecided members are not assembled by apply, so the actual claim checker had nothing to run), no actionable failures. Because of that, the three submitted sheets were checked with a scratch replica of apply (scratch folder `work/p1/pre.py`) that assembles each against an experimental dossier and runs the claim checker: no errors. Each filled STATUS_DECISION.json (12701, 11943, 9447, 9739) passes `status_overlay._decision_errors` with no errors.

## Geddes
0 flags (GEDDES_LINT.json in applied-v1); no resolutions file needed.

## Files opened beyond views
LOOKUPS.details.json (structure and one member only); EVIDENCE.json of the undecided folders (history observations, evidence texts); decisions.csv and clauses.csv (edited). Held texts read: fr-originals EO_12863, EO_12010, EO_9525, EO_9642, EO_9744B, EO_9465, EO_9583, EO_9834, EO_10264, EO_7841, EO_14274, EO_13650; app-executive-orders EO 7841 text; tischendorf EO_2048; theophilus usc-t5-s5332; cruden-fr-concordance FR-1951-10-06 page.

## Tool and process notes
- Brief says undecided sheets are validated by batch-check; in this kit version apply does not assemble undecided members, so no claim reaches the actual checker.
- The first written sheet for 12701 overwrote the prefilled working_text; reconstructed from the values printed in the same session.
- EO 1957's ProQuest replica carries a working-text basis in the validator code (F6), which could allow a status proposal; the coordinator precheck and brief say to block, so it was blocked.
- cruden.py number writes about 10 MB per call; only match counts were read.
