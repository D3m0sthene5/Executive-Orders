# Producer report: packet u05 (undecided route), producer baldus

Start 2026-11-25T16:06:43Z. End 2026-11-25T16:22:30Z. Final applied directory: applied-v2 (applied-v1 kept; v2 differs only by the EO 13244 inventory correction).

## Outcome per order (assigned members)
- EO:13244 submit (status proposal no). Revoked in whole by EO 13915 section 4, 2020-04-14 (express revocation); section 4 (revocation of EO 11487) spent on issue 2001-12-18; EO 13261 (2002-03-19) is a later event on section 3(a). Inventory corrected from 14 to 11 clauses because two bare headings were too short for the checker to verify (joined to the text they introduce).
- EO:13374 submit (no). Three self-executing acts, spent on issue 2005-03-14 (own-text records); the 22 U.S.C. 3901 note is an amender listing, not a current predicate.
- EO:13646 submit (no). Council terminated by section 6, 2015-06-25 (inclusive; exclusive reading stated); no extension held. All 41 clauses end by own terms; the policy clause (section 1) is the clause a reviewer is most likely to question.
- EO:7759 submit (no). Self-executing revocation, approved 1937-12-01 (own-text record).
- EO:7946 submit (no). One-period quota, own terms end 1938-12-31 (inclusive). The status basis id is ACTOR_TEXT:EO:8051, which recites EO 7946's period but does not itself end it (the dossier holds no TERM record for this order); the ACT lead EO 7946>EO 8051 is EO 8051's self-termination sentence, not an end of EO 7946.
- EO:8774 submit (no). Own terms: quota year ending 1941-09-30 (TERM record).
- EO:8015 blocked. Frozen dossier holds no ending-type or CURRENT record and the clause inventory is the Federal Register contents page, not the order text. Missing: a current source for the Union Slough refuge reservation (or an OWN_TEXT record) and a corrected inventory. STATUS_DECISION left blank.
- EO:9669 blocked (lifecycle only). Status proposal no is filed (EO 9709 paragraph 6 supersedes it). First end unresolved: EO 9709 paragraph 5 makes it effective per location at agreed times (not held), and the Budget Director's fund determination under EO 9669 item (4) is not shown. Missing: the agreements or the determination.
- Dispatch-blocked members (1104, 1362, 14249, 1542, 2474, 3799, 4843, 5026, 5521, 590, 6540, 85): decisions rows left as prepared; assessment rows written from the views and held lookups only.

## What took the time
13646: 41 clause reasons and the extension search. 13244: ACT records and the inventory correction after the actual checker flagged short headings. 13374: confirming the three own-text records and the amender listing. 9669 and 8015: working out why a first end or status basis could not be fixed. 7759, 7946, 8774: short own-terms reads.

## Counts
apply applied-v2: awaiting_status_review 6, blocked 2, unresolved 12 (dispatch-blocked rows as prepared). batch-check: packet members 20, claims checked 0 (undecided members assemble no claim until a status is adopted), actionable failures 0. As a substitute check I assembled the six submitted members into working claims under their proposed status in scratch (the kit's own assemble and check_claim) and ran the actual claim checker (jobs/claim-checker/checker.py, offline) on them: 6 of 6 pass all checks; STATUS_DECISION validation (_decision_errors) returns no errors for the 8 filled files.

## Geddes
GEDDES_LINT.json in applied-v2: 0 flags, 0 coverage gaps (no claims in the audit set). No resolutions file needed.

## Files opened beyond the views
EVIDENCE.json for the 8 assigned members (read with scripts, printed in parts), LOOKUPS.md, decisions.csv, clauses.csv, RATIONALES.json. Not opened: PACKET.json, READ.md, LOOKUPS.details.json. Repository files read: jobs/claim-kit batch.py, assemble.py, status_overlay.py, own_text.py (grep), stage19 claim_gate.py, jobs/current-law MENTIONS.csv (grep), the 1989 table text held under jobs/peano-formulario, jobs/pothier/README.md (partial), and a cruden literal search and number lookup for EO 13646 (output in scratch /home/claude/baldus-scr/work/u05).

## Tool defects and notes
- Apply and batch-check do not exercise undecided members' sheets (no claim is assembled without a status), so errors in a sheet would first appear at overlay-assemble; I replicated that step in scratch.
- The gate requires an actor on a first-end source; a CLAUSES record has none, so own-terms ends without a TERM record (EO 7946) must cite the ORIGINAL record, whose quote is the whole held text file.
- The checker flags clause records under about 30 characters as too short to verify; heading-only clauses in a dossier inventory need joining.
- Scratch generators and test claims are under /home/claude/baldus-scr/work/u05.
