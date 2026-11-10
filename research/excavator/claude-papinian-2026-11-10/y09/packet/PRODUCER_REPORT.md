# Producer report, y09 (producer-y09)

Start UTC 2026-11-10T04:22:38Z. End UTC: see last line of this file.

Final applied directory: `applied-v2`. Submitted 6 (EO 9158, 10979, 12353, 12478, 12561, 13830); blocked 19 (including dispatch-blocked EO 11633, not researched).

## Outcomes
- EO 9158 submit (YES): Air Medal, amended by EO 9242-A and EO 14085; 10 U.S.C. note prints it as amended.
- EO 10979 submit (YES): inventory corrected by overrides (lead, 2(a), 2(b), 7, 8). Sections 7 and 8 ended 1977-10-19 by EO 12014 (deleted with the Board); section 2 continues per the 5 U.S.C. 4504 note.
- EO 12353 submit (YES): inventory corrected to preamble and sections 1-9 (packet omitted 7, 8, 9); amended by EO 12404 and EO 13743. Conflict PARTIAL_END_CANDIDATE_ON_YES_ORDER (2007 FR rule E7-16986) resolved: it records EO 10927's revocation by this order.
- EO 12478 submit (YES): transfer to Secretary of State preserved by 18 U.S.C. 3056A(d) and Pub. L. 109-177 sec. 606(b).
- EO 12561 submit (YES): 5 U.S.C. 5702(a) still vests the power in the President or his designee; 3 U.S.C. 301 note prints EO 10621 sec. 1(h).
- EO 13830 submit (YES): inventory rebuilt to 11 section-level clauses (packet clauses did not match the text); amended by EO 14085 sec. 5.
- Blocked, National Emergencies Act continuation notices not held as evidence records: EO 13441, 13536, 13581, 13694, 13757, 13886, 13902, 14014, 14078. EO 13312: Clean Diamond Trade Act renewal text and EO 13194 emergency notices not held.
- Blocked, other: EO 10579 (27 clauses; current 40 U.S.C. ch. 6 / 41 CFR 102-34 not evidence); EO 11491 (116 clauses; Pub. L. 95-454 title VII savings text and clause comparison); EO 11589 (clause 1(b) rests on former 50 U.S.C. App. 2286(a)(4); repeal/restatement text not held; 1(a) current); EO 11932 (EO 11652 successors' savings text, 22 CFR 9a); EO 12171 (41 clauses, 18 amending orders); EO 12569 (compact acts of 2003 and Palau not held); EO 12597 (49 U.S.C. 41307 text, EO 12356 successors, inventory omits sections 2, 3(a), 11, 12); EO 12657 (NRC/FEMA regulation text, repealed civil-defense authorities); EO 11633 (dispatch-blocked: sec1, sec3, original not held).
- No order was found not in force on 2026-10-14; assessments in `ASSESSMENT.jsonl` (25 rows).

## Time per order
Most time went to reading text and amendments for the six submitted orders (EO 12353 and 13830 needed full inventory rebuilds with offsets); the NEA and large orders were triaged from dossier gap lists and chains in a few minutes each.

## Batch-check (applied-v2)
claims checked 6, strict pass 6, fail 0; actual claim checker all checks passed 6/6; blocked 19. (applied-v1 had EO 12353 rejected for an unresolved conflict; fixed in v2.)

## Geddes
1 flag: EO 13830, unaddressed_citing_instrument EO 10189 (amends EO 4601, which section 8(c) supersedes); recorded as disputed in `applied-v2/GEDDES_RESOLUTIONS.json`. 6 coverage gaps (citing corpus incomplete, 912 held texts changed or missing; EO 12353 heading unresolved) noted, not flags.

## Files opened beyond the views
PACKET.json loaded once in a script (evidence texts via batch.load_packet, check_sources=False); LOOKUPS.md head and greps; repository sources: jobs/later-events/output/EDGES.csv, jobs/current-law/output (ORDERS_CURRENT_LAW.csv, EVENT_CANDIDATES.csv, USC_EO_NOTES.jsonl), jobs/ofr-codification-1989/output/DISPOSITION_1989.csv, jobs/claim-drafts/output/CONFLICTS.csv and selden-fr-citers CITATIONS.csv (one grep each), jobs/theophilus-sources/output/texts (usc-t5-s3376, usc-t5-s5702, usc-t18-s3056A, usc-t40-s601, cfr-t5-part334 heads), fr-originals texts of EO 9242A, 14085, 12014, 11085, 12107, 12148, 12404, 13743.

## Tool defects
None blocking. The packet inventories for EO 12353, 13830, 12597 and 10979 did not match the order text (merged or duplicated clauses, missing sections), corrected by overrides where submitted. Views are large (50-700 KB) despite the slim label.

End UTC 2026-11-10T04:44:10Z
