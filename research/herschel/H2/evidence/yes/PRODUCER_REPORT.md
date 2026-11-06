# PRODUCER_REPORT H2-w05
Start 2026-11-05T23:36:57Z; end 2026-11-05T23:39:26Z

## Outcomes (all 6 blocked, 0 submitted)
- EO:11298, EO:12598, EO:10863, EO:12137: YES orders; no held, citable current-law text through 2026-10-14 (USC note / CFR leads are pointers without source sha256 or text slice). EO:12137 also has possible omitted commands in its inventory and unread later orders (12245, 12292, 12399, 13724).
- EO:7724 (Bitter Lake refuge), EO:8854 (Sitka reservation): no held current-status source (no public land order or current-law text; PLO:326, PLO:1707, PLO:6458, PL 98-63, PROC:2965 absent from census). EO:8854 also needs page review of the original boundary.

## Time per order
All orders: one view read, decision from the missing-source evidence; no deep research since the gap was the same.

## batch-check
6 members, 0 claims checked, 0 strict pass/fail, 6 blocked, no actionable failures. Geddes: 0 flags (GEDDES_LINT.json in applied-v1); no resolutions needed.

## Full-packet files opened beyond views
LOOKUPS.md, decisions.csv, clauses.csv, DISPATCH_CHECK.json (head only).

## Tool defects
First batch-check failed with "No such file ... research/herschel/H5/packets/d1/packet/clause_inventory_NOTES/clause_inventory.outcomes.json" (another packet's path, seemingly a race on a shared file); the rerun passed unchanged. I did not open that folder.

---
# Pass 2 (coordinator correction)
Start 2026-11-05T23:40:31Z; end 2026-11-06T00:21Z. Final applied directory: applied-v4 (v2: first_end original_confirmed missing; v3: sec6 end source fix; v4 passes). The session was OOM-killed once during batch-check; it was rerun to completion.

## Outcomes: 3 submitted, 3 blocked
- EO:11298 submitted (single clause operative on original + bounded searches; number search finds only own page/1989 entry).
- EO:12598 submitted (sec1-5 operative; sec6 supersession of EO 12576 recorded as spent 1987-06-17, signing date, no separate effective date).
- EO:10863 submitted (one clause covering secs 1-2 operative; EO 10864 text overlap on the same page explains the second held file).
- EO:7724 blocked: Public Land Order 326 (1946-08-30, 11 FR 10298), recorded as revoking the order in part, held only as a catalogue note.
- EO:8854 blocked: Proclamation 2965 (1952-02-25, partial revocation), PL 98-63 and PLO 6458 (1983, amendments), PLO 1707 (1958) held only as catalogue notes; a 2003 index mentions a PLO 6458 extension without text.
- EO:12137 blocked: Pub. L. 97-113 (made Peace Corps independent of ACTION; per 1989 editorial note only) and the later statute ending ACTION are not held, so sec 1-101 and ACTION-dependent clauses cannot be decided; dossier inventory (9 clauses, dups) covers ~1/5 of the order and needs an override. Found held: EO 12399 sec 4(k) revokes sec 1-2 (1982-12-31); EO 12292 amends 1-111, 1-401; EO 13724 adds 1-113, deletes 1-301(e); EO 12245 amends 1-202.

## Time: mostly reading EO 12137 and its later orders, and the land orders' status-history events; apply ~40 s each; batch-check ~15+ min.
## batch-check (applied-v4): 6 members, 3 claims checked, 3 strict pass, 0 fail, actual checker 3/3 passed, 0 actionable failures.
## Geddes: 0 flags, 4 coverage gaps on EO:11298 and EO:12598 (own_order_body_unverified, citing_own_body_unverified: order_heading_unresolved, the dossier boundary note); not defects, no resolutions file needed.
## Extra files opened: status-history event files, OFR 1989 codification text and later orders for 12137 (repository sources). Tool defect: batch-check intermittently fails on another packet's clause_inventory_NOTES path; rerun passes.
