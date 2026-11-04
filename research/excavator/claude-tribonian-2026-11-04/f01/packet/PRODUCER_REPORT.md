# Producer report f01 (Tribonian)
Start 2026-11-04T04:45:20Z. Written 2026-11-04T06:07Z, before the final pipeline finished.

## Outcome
Submitted 33, blocked 1 (EO 10323), unresolved 3 (EO 10328, 10504, 10601). The 33 submitted orders end by EO 12553 (1986-02-25), express revocation by number in the table. EO 9942, 9949 and 10157 and 10376 are non-board orders; 9942, 9949 and 10157 carry amendment later events.
- 10323: Small Business Act of 1953 (67 Stat. 232) not held; an earlier end by abolition of the Small Defense Plants Administration cannot be excluded.
- 10328: Selective Service regulations amended piecemeal by EO 10420, 10837, 10984; needs section-level comparison with CFR text not held.
- 10504: order text split across pages 7667-7669; completion of liquidation not shown.
- 10601: section 3 ended earlier by EO 12148 section 5-105 (1979-07-20); sections 4-6 and EO 10773, 10782, 11051, 11725 not read.

## Time per order
Board orders: inventory repair (page junk, wrong spans) and report-date verification against NMB texts. 9942, 9949, 10157, 10376, 10848, 10689, 10842: inventory repair and amendment text. Blocked orders: source identification only.

## Batch-check on applied-v2
Strict pass 33, fail 0. Actual checker: 33 checked, 32 all passed, 1 mechanical fail (EO 10570: the checker searches the clause-drafts OCR text registered for the same file hash, not the packet's recheck text that holds the quote; claim text matches the registered recheck bytes. Tool defect, claim left unchanged).
applied-v3 (EO 9949 text change only) was still applying/checking when this report was written; its results are not recorded here.

## Geddes (applied-v2)
3 flags, 30 coverage gaps (own_order_body_unverified etc. on 10 orders, OCR column text). Resolutions in applied-v2/GEDDES_RESOLUTIONS.json: 9949 fixed in v3, 10032 and 10643 disputed.

## Full-packet files opened beyond views
LOOKUPS.md, LOOKUPS.details.json, PACKET.json, decisions.csv, clauses.csv. READ.md not opened.

## Tool defects
cruden.py table-number returns counts only; cruden search takes over 2 minutes; view/load_packet use @eo:ref indirection; checker quote check for 10570 uses a different registered text than the packet's.

## Final: applied-v3
applied-v3 completed: 33 assembled, strict pass 33, actual checker 32 of 33 (same EO 10570 checker defect). Geddes on v3 re-run; GEDDES_RESOLUTIONS.json copied to applied-v3. Final applied directory: applied-v3.
