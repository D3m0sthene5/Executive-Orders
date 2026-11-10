# Producer report u01b (papinian, undecided route)

Start 2026-11-10T06:30:46Z; end 2026-11-10T06:53:39Z. Final applied directory: applied-v1 (regenerated before batch-check; no earlier version was checked).

## Outcomes
Submitted lifecycle sheet and status proposal NO (awaiting_status_review): EO:11957 (EO 13241 Sec. 4, 2001-12-18), EO:12348 (EO 12512 Sec. 4, 1985-04-29), EO:11726 (EO 11775, 1974-03-26; inventory corrected to 19 clauses; EO 11748 partial supersession recorded as later event), EO:11728 (parent EO 11157 revoked by EO 13294, 2003-03-28), EO:11816 (parent EO 10973 revoked by EO 12163, effective 1979-10-01; EO 11959 restatement recorded), EO:9674 (EO 9744, effective 1946-06-30), EO:9680 (own terms, abolished as of 1946-06-30).
Status proposal NO filled, lifecycle blocked: EO:10771 (Sec. 1 ends on completion of construction, undated in held sources; EO 11382 Sec. 16 1967-11-28 is only a bound), EO:12072 (revoked by EO 14274; dossier original span omits sections 1-1..1-3 lead text so inventory cannot be corrected), EO:13024 (OPM final rule effective 2012-07-10 held only outside the dossier).
Blocked (STATUS_DECISION left blank): EO:7573, 7621, 7721, 7729, 8494, 8617, 9181, 9231, 9408, 9794, 11225, 13354, 13505, 14233, 14318, 14435; exact reasons are in decisions.csv (unresolved_material_gaps, first item) and ASSESSMENT.jsonl (blocker). No YES proposal is possible for this packet: every dossier has 0 CURRENT records.
Dispatch-blocked (rows as prepared, assessment from view only): EO:10917, 13411, 14223, 7778.

## What took the time
Most time went to reading end sources: 11816 (effective date 1-905 and restated sec 301), 11726 (inventory correction, partial supersession), 11728 (searching 14 amending orders for section 104), 12072 (inventory span), 13024 (finding the OPM rule date), 9408/9231/9181 (checking for held termination sources).

## Batch-check
apply: 30 members; 7 awaiting_status_review, 19 blocked, 4 unresolved (dispatch-blocked), 0 rejected. batch-check: 0 claims checked (undecided members assemble no claim), 0 actionable failures. Because apply never assembles undecided sheets, I assembled each of the 7 sheets in a scratch script against a copy of its dossier with whole_order_status set to no and run through assemble/check_claim: 0 errors; every STATUS_DECISION.json (10 filled) passes status_overlay._decision_errors with no errors; quotes in prose were verified against dossier texts.

## Geddes
GEDDES_LINT.json: 0 flags, 0 coverage gaps (no claims assembled). No GEDDES_RESOLUTIONS.json needed.

## Files opened beyond the views
Each member's undecided/EO_N/EVIDENCE.json (read with scripts), LOOKUPS.md, held texts under jobs/fr-originals (EO 9744, 9313, 9521, 11382, 11748, 11775, 11959, 12163, 13240, 13241, 13294, 13562, 14274 and others), jobs/selden-fr-citers/output/texts/fr-2012-11068.txt, jobs/theophilus-sources usc-t50-s3001.txt, and one cruden number run for EO:13354 (output 10 MB, not read in full). Not opened: READ.md, PACKET.json, LOOKUPS.details.json.

## Tool defects
1. kit apply never assembles undecided members, so no claim checker runs on them until overlay-assemble; I replicated that check in scratch.
2. A clause-record (CLAUSES: or OVERRIDE:) end source has no actor, so assemble reports clause_N_first_end; self-executing clauses must cite ORIGINAL: as the end source.
3. Inventory overrides must lie inside the dossier ORIGINAL span, so a bounded-envelope original (EO 12072) cannot be completed.
4. cruden.py search over the whole corpus exceeds 120 s.

## Overlay follow-up (coordinator request)
For EO 9674, 11726, 11728, 11816, 11957 and 12348 I inspected LIFECYCLE_DECISION.json against my sheets (clauses, end ids, dates, savings, no gaps), changed nothing except setting approved true, then ran overlay-assemble and overlay-check. All six assembled; overlay-check returned checked 1, failures [] for each. Correction to the report above: the corrected EO 11726 inventory has 18 clauses (not 19); the sheet itself is right. EO 9680 was rejected by the status reviewer and was not assembled.
