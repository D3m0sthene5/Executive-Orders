# Producer report: dorotheus, packet u203 (undecided route)

Start 2026-11-06T10:16:30Z; end 2026-11-06T10:28:03Z.

Final applied directory: `applied-v2` (applied-v1 kept; v2 fixed a blank savings_reason column and replaced mirror/override end ids with official-text ids).

## Outcomes
- EO:11218 submit (awaiting_status_review). STATUS NO. Superseded by EO 11278 section 106 (1966-05-04); one clause.
- EO:10994 submit (awaiting_status_review). STATUS NO. Superseded by EO 11480 section 6(a) (1969-09-09). Registered inventory was wrong (omitted sections 1(a), 2, 3(a), 5(a), 6(a)); replaced by 9 clauses; section 6(a) 10640-supersession and 6(b) transfer dated 1962-02-14 as one-time acts.
- EO:10901 submit (awaiting_status_review). STATUS NO. Section 1 ended by EO 11652 sections 14-15 (effective 1972-06-01); section 2 (memoranda revoked) one-time act 1961-01-09. Inventory corrected (section 2 was missing).
- EO:10539 blocked; STATUS_DECISION filled NO (EO 11051 section 604, 1962-09-27). Missing: dates of organization/liquidation of the Federal Facilities Corporation, date fixed under section 7, expiry of the Rubber Act and Abaca Production Act functions; inventory incomplete. EO 11051 revokes only "to the extent ... not heretofore made or become inapplicable".
- EO:10745 blocked, status blank. No ending instrument; own-terms dates are deadlines for one permission; missing last-conversion records or instrument removing Part II of EO 10577.
- EO:10763 blocked, status blank. EO 11890 replaced paragraphs 2 and 3; paragraph 4 unchanged; no CURRENT record. Missing attributed text of 22 U.S.C. 287 note / EO 10422 as in force.

## Time
10539: reading the long FR page and the EO 11051/10773 texts; 10745: tracing section 203 of EO 10577; 10763: EO 11890/12107 comparison; 10901: later amendments' dates; 10994: inventory rebuild; 11218: straightforward.

## Checks
batch-check (applied-v2): 6 members, 0 claims checked (awaiting_status_review is expected), 0 actionable failures. Status decision validator (`_decision_errors`) returned [] for 11218, 10994, 10901, 10539. I also ran `assemble.assemble` on the three sheets in scratch with the status set to no: no errors except the expected dossier-fingerprint mismatch.
Geddes: 0 flags, 0 coverage gaps; GEDDES_RESOLUTIONS.json empty.

## Files opened beyond views
EVIDENCE.json/DOSSIER.json of my own undecided folders (bounded scripts), packet decisions/clauses CSVs, held order texts under jobs/ (EO 11278, 11480, 11018, 11051, 10773, 11652, 10985, 11097, 11382, 11890, 12107, 10577), jobs/status-history histories, cruden search and `number` (scratch output for 10745, 10763, 10539).

## Judgment calls to flag
- One-time clauses (10994 6(a) second sentence and 6(b); 10901 section 2) use the ORIGINAL record as end source and the order's signing date as the performance date; reviewers should test this.
- 10994 section 6(c) is dated at the 1969 supersession; the unexpired-term limb lapsed earlier at undated points.

## Tool defects
apply reports claims_checked 0 for awaiting members, so lifecycle sheets are only checked later; I used a scratch call to assemble.assemble to pre-check.
