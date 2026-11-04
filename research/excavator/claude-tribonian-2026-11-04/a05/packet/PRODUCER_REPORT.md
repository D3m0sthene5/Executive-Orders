# Producer report a05 (Tribonian, agent claude)

Start UTC 2026-11-04T04:51:44Z. End UTC 2026-11-04T05:41:53Z.
Final applied directory: applied-v5 (applied-v1 to v4 and applied-test1 are superseded trial runs; v1 rejected EO 13017, v2 same, v3 and v4 left quote failures for EO 12521 and EO 12296).

## Outcome per order (18 submitted, 13 blocked)
Submitted, with ending instrument and date:
- 12462: own-terms end restated by EO 12617 section 4(b), 1988-09-30 (inclusive); later events 12497, 12533, 12579, 12617; EO 12692 recorded as later cleanup.
- 12584: EO 12610 revokes parent EO 12575 (section 3(g)), 1987-09-30.
- 12592, 12601, 12668: EO 12692 section 3, 1989-09-30 (12601 inventory corrected to add section 1(a); 12592 cites no 12609 because only a mirror text is held).
- 12686: EO 12774, 1991-09-30 (inventory corrected).
- 12792: EO 12869, 1993-09-30.
- 12864 and 12921: own-terms end by EO 12970, 1996-06-01 (12921 via parent 12864 section 4(b)); 12921 later event 13062.
- 12946, 12964, 12987: EO 13062, 1997-09-30 (12946 savings transferred_or_accrued; 12964 later events 12987, 13032).
- 12961, 13038: EO 13138, 1999-09-30 (13038 later events 13062, 13065, 13081, 13102).
- 13015: own-terms six months from 1996-08-22 (inclusive), 1997-02-22; later event 13062.
- 13075, 13090, 13168: EO 13225 section 3, 2001-09-30 (13090 later event 13136).

Blocked (precise gap in decisions.csv unresolved_material_gaps):
- 12296 and 12521: decided but the registered text is the OCR recheck, which the claim checker cannot match to the PDF text layer (quote_verbatim not_found). Need a checker-matchable text.
- 13017: checker rejects the section 5 two-year outer limit as a report deadline (report_deadline_is_not_end); no held source dates the final report or shows no extension.
- 12607: registered original is an ungraded recheck transcription; no page or complete-text confirmation held.
- 12696, 12891, 10647, 11157, 12291, 12759: inventory/heading unresolved or per-clause amendment map and amending texts not completed; needs confirmed texts named in each gap.
- 12934, 13088, 13121: Federal Register national-emergency notice chain (continuations and EO 13304 termination) not held.

## Time per order
Most time went to quote exactness and inventory spans: 12592 and 12961 (14 and 21 clauses), 12686 and 12601 (inventory corrections), 12462 and 12921/12864 (own-terms plus inclusive reading), 12296 (five continuance orders), 12946 (savings), 12521 (OCR text). Blocked large orders (10647, 11157, 12291, 12759, 12891) were blocked quickly for source gaps; the three sanctions orders were blocked on the missing notice chain.

## Batch-check (applied-v5)
Claims checked 18; all checks passed 16; mechanical pass 16; unverified 2 (12864 short quotes, 13038 custody-record-only later-event sources); mechanical fail 0; gate passed 18.

## Geddes (applied-v5/GEDDES_LINT.json)
25 defect flags (all later_instrument_named_without_event_source) on EO 12462 (8), 12964 (10), 13090 (7), plus 21 coverage gaps. All 25 are recorded as disputed in GEDDES_RESOLUTIONS.json: each actor appears only inside the exact quotation of the revoking order's item (or, for 12462, is a parse of the OCR-spaced number), and the amending orders are recorded as later events on the clauses they amend. Coverage gaps (heading unresolved, boundary conflict, unclassified mentions) are advisory.

## Full-packet files opened beyond views
decisions.csv and clauses.csv (and pristine copies of them), PACKET.json via load_packet; no READ.md or LOOKUPS.details.json.

## Tool defects
- Claim checker verifies quotes against the PDF text layer, not the registered OCR recheck text, so recheck-only sources (EO 12521, EO 12489 text) fail quote_verbatim.
- Checker rejects an own-terms outer-limit TERM evidence for report-relative termination clauses (EO 13017).
- Geddes parses OCR-spaced numbers (No. 1 2462) as actor EO:1.
- batch-check and Geddes each take several minutes; the kit with a background process needed polling.
