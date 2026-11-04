# Producer report, f02 (Tribonian)

Start: 2026-11-04T04:45:19Z (first session; stopped by the coordinator about 05:05Z for a stale packet). Resumed on the re-prepared packet at 2026-11-04T05:17:03Z. End: 2026-11-04T06:12Z.

Final applied directory: packet/applied-v4 (24 submitted claims, 13 blocked; same decisions as applied-v2 plus EO 10878 blocked in the sheet). applied-v1 (14 of 37 filled), applied-v2 (Geddes first run; EO 10878 submitted, then superseded) and applied-v3 (EO 10878 checker failure) are retained and are not final.

## Batch-check (applied-v4)
24 claims checked, 24 strict pass, 0 failures, actual checker 24 of 24 mechanical pass; 13 blocked. Geddes (rerun on v4 after a first v4 batch-check run crashed Geddes with 'held corpus inventory commit changed during search'): 7 flags (all attributed_stock_phrase_absent for the standstill, on EO 10875 and EO 11131) and 11 coverage gaps (EO 11321, 11324, 11443, 11663, 11694: order heading unresolved or boundary conflict). Flags are resolved as disputed in applied-v4/GEDDES_RESOLUTIONS.json: both orders do contain the section 10 standstill sentence, but the text layer is garbled (10875) or letter-spaced (11131), so the phrase matcher cannot find it. Coverage gaps are not flags and need no resolution.

## Outcomes
Submitted, terminated by EO 12553 on 1986-02-25 (express revocation by number; no saving clause; report date and standstill disclosed as functionally spent): 10872, 10875, 10888, 10919 (EO 10926 later event), 10923 (EO 10933 later event), 10953, 10965, 11101, 11115, 11131, 11343, 11745, 11852, 11663, 11694, 11324 and 11443 (inventory corrected), 11054 and 11321 (inventory corrected; LMRA boards), 11181, 11622, 11797, 11805.
Submitted, earlier end: 11452, terminated by EO 11541 sec 2(b) on 1970-07-01 (EO 11500 amendment and EO 12553 as later events; inventory corrected to 14 clauses).
Blocked: 10878 (the actual checker reads a different text file for the order's PDF, so every quotation fails; checker defect, claim otherwise ready), 11026 (EO 11029 earlier candidate needs a source supplement that producers may not prepare), 11108, 11574, 11237, 11761 (statute texts not held), 11386, 11434 (per-clause mapping against partial revocations not completed), 10976, 11387 (Proclamation 2914 and Pub. L. 94-412 not held), 11327 (EO 11366 exception), 11098, 11325 (Selective Service per-clause mapping workload). Precise gaps are in each row's unresolved_material_gaps.

## What took the time (one line each)
Board orders with report dates (10872-11115, 11343, 11663, 11694): checking the held NMB report front matter for dates and extensions. 10875 and 10878 and 11131: garbled or mis-registered text. 11324, 11443, 11054, 11321: wrong dossier inventories, replaced with overrides. 11452: building a 14-clause inventory and reading EO 11541 and EO 11500. 11181, 11622, 11797, 11805: reading the order and its USC lead. Blocked orders: identifying the missing source; no deep research was done on 11386, 11434, 11098, 11325.

## Notes
- Report dates come from held_text_lead NMB reports (not a citable grade) and are disclosed in reasons, not recorded as later events, except EO 10926 and EO 10933.
- Full-packet files opened beyond the views: packet/decisions.csv, clauses.csv (sheets), PACKET.json (dossier current_law_leads only), LOOKUPS.md, LOOKUPS.details.json (key listing). jobs/current-law/output MENTIONS, ORDERS_CURRENT_LAW and ECFR_SEARCH_HITS were read for the USC leads.
- Tool defects: (1) batch-check "date_valid ... matched_date" checker bug mentioned by the coordinator did not occur on the final run. (2) For EO 10878 the claim checker's text file (EO_10878.txt, which starts with a different document) differs from the dossier's registered original (EO_10878.recheck.txt), so quote_verbatim fails. (3) batch-check as a background job exited 144 (timeout) once and had to be rerun in the foreground.
- Side effects of the first session (SUPPLEMENT_DECLARATIONS.json, refresh/) were removed by the coordinator at re-prepare. Scratch files are under /tmp/claude-0/tribonian-work/f02/. DRAFT_NOTES.md sits outside the packet at the coordinator's request.
