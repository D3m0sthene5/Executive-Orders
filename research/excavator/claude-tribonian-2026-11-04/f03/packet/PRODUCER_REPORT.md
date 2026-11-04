# Producer report, packet f03 (Tribonian)

Start 2026-11-04T04:45:20Z. End 2026-11-04T06:04:55Z.

## Outcome
Final applied directory: packet/applied-v2 (applied-v1 kept; v2 only rewords the EO 12553 row description for the 11 emergency-board orders). Apply: 32 assembled proposals, 4 blocked, 0 rejected.
batch-check (v2): 36 members, 32 claims checked, strict pass 32, fail 0, actionable failures none; actual claim checker 32 of 32 all checks passed, mechanical fail 0, unverified 0.
Geddes: v1 lint gave 9 flags (attributed_row_wording_mismatch on 11876, 12370, 12373, 12384, 12385, 12386, 12393, 12405, 12414: the held table text prints numbers apart from subjects, so the word "railroad" was not in the row). Fixed in applied-v2; v2 lint gives 0 flags. Resolutions recorded in applied-v2/GEDDES_RESOLUTIONS.json. 58 coverage gaps remain (row_description_source_unresolved 29, own_order_body_unverified 14, citing_own_body_unverified 14, unclassified_instrument_mention 1 for EO 12038 in EO 12153 sec 1-103); these are not flags.

## Submitted (32)
Ended on EO 12553 (1986-02-25, express revocation by number in its table, read as effective on signing): 11876, 12370, 12373, 12384, 12385, 12386, 12393, 12405, 12414, 12480, 12481 (boards; report date and standstill recorded as spent facts under the report-deadline ruling, with no report date given because no report text is citable; the "board terminates on report" clauses in 12393, 12405, 12414, 12480, 12481 are treated as spent by disclosed analogy to the ruling), 11969, 12186, 12187, 12257, 12263, 12297, 12376, 12390 (sec 3 ratification ended on issuance 1982-10-25), 12392, 12397, 12440, 12442, 12447, 12449.
Mixed first ends: 12097 (inventory corrected to eight numbered sections; sec 1-302 ended 1981-05-05 by EO 12305, which names 12097; the rest on 12553), 12140 (inventory corrected; sunset sentence deleted by EO 12162 on 1979-09-28; rest on 12553), 12153 (inventory corrected; sec 1-102 deleted by EO 12186 on 1979-12-21; rest on 12553), 12457 (para (b) own sunset 1984-12-31), 12476 (sec 3 own sunset 1984-10-31).
Own-terms end: 12254 (1981-12-31, inclusive; exclusive reading 1981-12-30), 12327 (1982-10-01, inclusive).

## Blocked (4)
11896 (sec 6 contingent end undated), 12256 (expires when the Census issues 1981 estimates; no date held), 12357 (phase-out deadline of 1982-09-30 with no held evidence of performance), 12463 (extension to 1985-03-10; later EURATOM orders not located or read).

## What took the time
Reading the 36 order texts and the EO 12553 table, correcting three inventories, checking parent-order revocations (EO 12534, 12305), and an initial stale-packet stop. apply took 2m39s.

## Judgment calls for the reviewer
Report-relative "board terminates" clauses are treated as spent facts, not ends. Several unnamed instruments (EO 12534 revoking parent orders of 12397, 12440, 12442, 12447, 12449, 12457, 12476; EO 12287 for the oil orders) are disclosed as candidates only, in reasoning and not as later events. The EO 12370 board report (dated 1982-08-19, report time extended with presidential approval on 1982-07-26) sits in a held source-ladder text that is not citable evidence in the dossier.

## Full-packet files opened beyond the views
PACKET.json (via load_packet, to read evidence ids), LOOKUPS.md.

## Tool defects
First packet went stale on "changed prior research" after a new owner ruling file appeared; the coordinator re-prepared it.
