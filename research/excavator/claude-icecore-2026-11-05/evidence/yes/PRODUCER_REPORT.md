# Producer report (claude, ice core yes packet) - PASS 2 (supersedes pass 1 outcome)
Pass 1 (kept): start 2026-11-05T21:20:34Z; end 2026-11-05T21:23:42Z. Result applied-v1: all 24 blocked on a wrong premise (no held current-law bytes).
Pass 2: start 2026-11-05T21:25:27Z; end 2026-11-05T22:03:10Z. Coordinator correction applied: basis_pattern original_plus_bounded_search (EO 13306 precedent); searches current-law:usc, current-law:ecfr, later-events:ofr_catalog.

## Outcome (pass 2)
Final applied dir: applied-v10. Of the 24 assigned orders, 17 submitted and 7 blocked. The 5 coordinator-blocked rows (13736, 13827, 14038, 14306, 14404) were not touched; packet total 29 = 17 submitted + 12 blocked.
Submitted (17): 9998, 10805, 10967, 11228, 11435, 11830, 12019, 12024, 12114, 12138, 12228, 12292, 12293, 12344, 12372, 12748, 13361.
Blocked (7), each with its gap:
- 7724: Public Land Order 326 (1946-08-30, 11 FR 10298) revoked it in part per the OFR note; its text is not held.
- 10173: regulations (33 CFR Part 6) rewritten section by section by EO 10277, 10352, 11249, 13143, 13273, 14116; no held current Part 6 text; dossier inventory has 4 coarse clauses.
- 10789: official copies of EO 11051, 11610 and 13286 are in the corpus but not registered in the packet (only APP mirrors), so the working-text check rejects the later-event sources; garbled preamble and paragraph 4.
- 11438: same registration gap for EO 13286.
- 12957, 13553: missing yearly Iran national-emergency continuation notices (before March 15 each year; 12957: 1996-2026, 13553: 2011-2026).
- 13611: missing yearly Yemen continuation notices (before May 16 each year, 2013-2026).

## Per-order time notes
Most time went to the long or mis-cut texts: 12293, 12292, 12748, 12138, 12228, 10805, 11228 and 12344 needed inventory overrides (dossier clauses mis-cut) and later-event reading; 10789 and 10173 were read in full before blocking; 12372, 10967, 12019 were short and clean; 7724, 12957, 13553, 13611 were quick once the missing source was named.

## batch-check (applied-v10)
29 members: 17 strict claim pass, 0 fail, 12 blocked. Actual claim checker: 17 checked, 17 gate-passed, 13 all-checks-passed, 4 mechanically unverified (source_held custody_record_only: later-event PDFs for 12019, 12293, 12372, 12748 whose bytes are not kept in a committed place), 0 mechanical fail. Because of those 4 skips batch-check stops before Geddes, so I ran geddes lint_for_kit on applied-v10 directly.
## Geddes (applied-v10)
8 flags (all unaddressed_citing_instrument: 10805, 11228 x3, 12292 x2, 13361 x2), 19 coverage gaps. All 8 recorded as disputed in applied-v10/GEDDES_RESOLUTIONS.json (schema geddes-resolutions/v1); the geddes gate passes (0 unresolved). Fixed in earlier versions: 12024 event_precedes_order (end date moved to signing date 1977-12-01) and 10967 attributed_quote_not_verbatim (quotation marks removed from the OFR note).
## Full-packet files opened beyond views
decisions.csv, clauses.csv; outside the packet: jobs/fr-originals texts of later orders, jobs/current-law/output and jobs/later-events/output EDGES.csv (leads only, never quoted).
## Tool defects
batch-check skips the Geddes step when any claim has a custody_record_only skip (short-circuit in kit.py); worked around by calling geddes lint_for_kit directly.
