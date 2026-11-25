# Producer report: packet u02 (undecided route), producer baldus

Start 2026-11-25T15:38:27Z; end 2026-11-25T15:49Z (approximate; last command 15:48:27Z).
Final applied directory: research/excavator/claude-baldus-2026-11-25/u02/packet/applied-v1

## Outcomes (assigned members)
- EO:11125: blocked. Revoked by EO 11222 Sec. 703(b), effective on the date the Civil Service Commission issued regulations under Sec. 701(a); that date is not held (missing: first issuance of 5 CFR part 735 in 1965; held 2005 notice FR Doc. 05-15927 gives only subpart D effective Oct 1, 1965). STATUS_DECISION filled: no (basis ACT:EO:11125>EO:11222@e2d683ee7c095685).
- EO:11874: submit, YES (awaiting_status_review). One clause operative; current basis CURRENT:EO:11874#0 (U.S. Code note under 42 U.S.C. 2996k, release 119-121 through 2026-10-09). STATUS_DECISION filled: yes.
- EO:12952: submit, NO (awaiting_status_review). Amendment of EO 12950's list, spent on signing 1995-02-24; basis OWN_TEXT:EO:12952#685; savings transferred to the parent's list.
- EO:13230: blocked. Superseded by EO 13555 Sec. 4(a) (2010-10-19) but first ends of the Commission/Initiative/reporting clauses (Sec. 8: 30 days after final report unless extended) not established; missing the final-report submission date or extension. STATUS_DECISION filled: no (basis ACT:EO:13230>EO:13555).
- EO:13593: submit, NO (awaiting_status_review). Self-executing amendments of the Manual for Courts-Martial effective 2012-01-12; basis OWN_TEXT:EO:13593#1126.
- EO:13624: submit, YES (awaiting_status_review). 18 clauses operative; basis CURRENT:EO:13624#0 (note under 42 U.S.C. 6341). Clause Sec. 2(a) (goal for the end of 2020) treated as operative because the date is a goal target, not a stated end; a reviewer may disagree.
- EO:7036: blocked. ORIGINAL:EO:7036 is a machine-read government printed copy (acceptable_as_original false, no working-text basis) and no ACT/ACTOR_TEXT ending record; STATUS_DECISION left blank; assessment row written from the text (trust-period extension ended during 1945 by own terms).
- Dispatch-blocked (assessment rows only, decisions rows left as prepared): EO:1739, 2541, 4474, 5194, 6258, 6409, 6629, 9461A. Note: the view text for EO:6409 appears to be EO 6408's text.

## What took the time
11125: tracing the conditional effective date of the EO 11222 revocation and looking for the Commission regulation date. 11874: current-law note and empty-catalog flag. 12952: parent EO 12950 and own-text amender route. 13230: 29-clause inventory, Commission end-date search. 13593: amender own-text route. 13624: 18 clause rows and the 2020 goal date. 7036: working-text read and cruden number search (scratch file under /home/claude/baldus-scr/work/u02/).

## Checks
apply: 4 awaiting_status_review, 3 blocked, 8 unresolved (dispatch-blocked rows as prepared), 0 rejected. batch-check: 15 members, 0 claims checked (undecided members assemble no claim at apply), 0 actionable failures. Because apply does not assemble undecided members, I ran assemble() and batch.check_claim() in scratch on a copy of each submitted dossier with the proposed status set in memory (never written): all four (11874, 12952, 13593, 13624) assembled with no errors and no gate errors. status_overlay._decision_errors returns [] for all six filled STATUS_DECISION.json files.

## Geddes
GEDDES_LINT.json: 0 claims checked, 0 flags, 0 coverage gaps. No resolutions file needed.

## Files opened beyond the views
Per-order undecided/EO_N/EVIDENCE.json and DOSSIER.json (read only, own packet), LOOKUPS.md, decisions.csv, clauses.csv. Not opened: PACKET.json, READ.md, LOOKUPS.details.json. Repository sources opened: held order texts for EO 11222, 12950, 13555, the FR notices fr-05-15927, fr-05-6383 (grep), fr-2026-00153, and current-law notes for EO 11874 and 13624; cruden searches for EO 11222, 12950 and the Commission name; cruden number search for EO:7036.

## Tool defects and notes
- apply/batch-check give no validation of submitted sheets for undecided members (no claim is assembled); only the scratch simulation above did.
- The clause inventory for EO 13624 and EO 13230 carries machine labels such as sec2-i-dup2 that stand for paragraph (d)(i) etc.; spans are correct, labels are not, so I did not rewrite the inventory.
- ASSESSMENT.jsonl: first_cause is left empty for the two YES orders (no ending occurred).
