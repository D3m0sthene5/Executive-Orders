# Producer a04 report (Tribonian fresh lot)

Start UTC 2026-11-04T04:48:12Z (first run, stopped on the coordinator's order, then resumed on the re-prepared packet). End UTC 2026-11-04T06:15Z. Final applied directory: applied-v3.

## Outcomes
Submitted 23, blocked 10.

Submitted, with the first end:
- EO 12319 family: 11578 and 11658 end 1981-10-01 (EO 12319 Sec. 5(a)); 11659 ends 1982-01-01 (Sec. 5(b)); membership-list amendments by EO 11882, 12038, 12148 (and EO 11737 for 11659) are later events. The Sec. 1 recital of EO 12319 names commissions, not orders, and is disclosed as an earlier candidate.
- EO 12379 family, end 1982-08-17: 11654, 12042, 12075, 12085, 12095, 12132, 12182, 12207, 12275, 12285. Report deadlines and 30-day standstills are not ends. 11654 Sec. 8 (supersession of EO 7397 and 10257) is recorded as an executed command ended at issue.
- 12202: own sunset as amended by EO 12240, 1981-09-30; EO 12379 and EO 12399 are later events.
- 12323: own date 1982-10-01 (report alternative disclosed). 12511: own date 1987-04-29 (report alternative disclosed).
- 12310 ends 1982-12-31 (EO 12399 Sec. 4(g)). 12468 ends 1985-09-30 (EO 12534 Sec. 3(o)).
- EO 12610 Sec. 3, end 1987-09-30: 12490, 12503, 12526, 12546, 12575.

Blocked, with the gap:
- 12100: no instrument names it; Public Law 96-14 is not a packet evidence record and no final-report date is held.
- 12192: Sec. 1-402 own end depends on an unstated effective date and an undated report; EO 12379 Sec. 13 is later than the outer bound.
- 12307, 12317, 12339, 12507, 12542, 12545, 12581 (amending orders) and 12325: the later revocation names the parent order, not the amender (owner ruling on unnamed instruments). 12325 also rests only on graded mirror records for its own date.

## What took the time
- One line per order: most time went to confirming the clause inventory and end sources. Inventory corrections (character-span overrides) were needed for 11578, 11654, 11658, 11659, 12075, 12192 (blocked), 12285, 12325 (blocked), 12511, 12542 (blocked).
- 11659: the stated-effective-date conflict. 12202: the competing 1982 actors against the 1981 own sunset. 12468: whole versus partial reading of EO 12534. 12575: undated report. 12100, 12192, 12325: researched and blocked.
- The rest were routine single-revocation orders.

## Batch-check
applied-v3: 33 members; 23 claims checked, 23 strict pass, 0 strict fail; blocked 10. Actual checker: 21 all-pass, 2 mechanical-unverified (12323 and 12546, quotes too short to verify), 0 fail, gate passed 23. applied-v1 was rejected (later-event ids used ACT ids not in the dossier and savings sources missing); fixed in v2. v3 was made after Geddes flagged 12095.

## Geddes
applied-v2: 1 defect flag (12095, held_board_report_unaddressed); fixed in v3. applied-v3: 0 defect flags, 24 coverage gaps (own_order_body_unverified / citing_own_body_unverified, reason order_heading_unresolved), advisory and not defects. See GEDDES_RESOLUTIONS.json. One Geddes run failed once with "held corpus inventory commit changed during search" and succeeded on retry.

## Full-packet files opened beyond the views
PACKET.json (via load_packet, in scratch pickle), LOOKUPS.md, decisions.csv, clauses.csv. READ.md and LOOKUPS.details.json were not opened.

## Other notes
- DRAFT_NOTES.md was written in a04/ outside the packet at the coordinator's stop order, before FILE DISCIPLINE existed.
- Tool defects: none beyond the transient Geddes error above. The checker date bug was not triggered.
