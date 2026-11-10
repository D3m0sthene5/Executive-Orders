# Producer report y06 (producer-y06, Papinian lane)

Start 2026-11-10T04:10:16Z; end 2026-11-10T04:32Z. Final applied directory: `applied-v3`.

## Outcomes (6 submitted, 19 blocked)

Submitted (all pass batch-check and the actual claim checker; Geddes 0 flags): EO:10870, EO:11302, EO:11545, EO:11629, EO:11904, EO:13736.

- EO:10870: single designation clause, operative; 51 U.S.C. 20306 text in release point 119-121 refers to the center.
- EO:11302: one whole-order clause, operative as amended by EO 11429 and EO 11609 (later events, ACTOR_TEXT official records); 38 CFR part 70 authority citations list the order.
- EO:11545: one whole-order clause, operative as amended by EO 14085 section 6 (before/after in the reason).
- EO:11629: two standing clauses (delegation, consultation duty), operative on original text plus bounded searches (no hits).
- EO:11904: four standing clauses, operative on original text plus bounded searches.
- EO:13736: succession order; sec 1/2/4 operative, sec 3(a)-(d) terminated by performance 2016-08-12. Inventory corrected (entries (d)+(e) merged: entry (d) alone was too short for the checker to verify a quote).

Blocked, with the exact missing source (also in decisions.csv unresolved_material_gaps and ASSESSMENT.jsonl):
- EO:10521: held text of EO 12608 showing its amendment (OFR note 'Amended by: EO 12608'; held text does not name 10521); corrected inventory; before/after for EO 10807.
- EO:11046: registered citable official-copy record of EO 13286 s.70 (only APP mirrors in the packet; first apply rejected with working_text:official_copy_available_recheck_required). Rest of the order was worked and is ready to resubmit once supplied.
- EO:11738: corrected inventory (sections 3-6 and 8 merged); attributed current-law text.
- EO:12294, 13059, 13268, 13304, 13687, 14066, 14071, 14140: emergency-dependent; National Emergencies Act continuation notices are acting identities absent from the census (not citable); provision records of cross-referenced orders not located. (13268 and 13304 also need a corrected inventory: terminated emergency vs surviving amendment.)
- EO:12341: held text lacks heading (order_heading_unresolved); inventory merges sections 1-3; EO 13286 only as APP mirror.
- EO:12500, 12639: current text or comparison of EO 12163 as amended (EO 13118 rewrote Part 1-1) not held.
- EO:12580: 78-clause inventory with four amending orders not worked clause by clause.
- EO:12793: whole-order boundary unverified; EO 14131 restates secs 1-2; EO 13286 only APP mirror.
- EO:13666: single exhausted amending command; held text of EO 12019 as current basis missing.
- EO:7680: Proclamation 2578 (partial supersession) and EO 9021 not held/citable.
- EO:8685: PLO 3032, PLO 4367, Pub. L. 100-696 and PLO 7045 (partial revocations) absent from census.

No held evidence showed an order was out of force on 2026-10-14; every assessed order is unrevoked on the held record (see ASSESSMENT.jsonl for the unknowns).

## What took the time (one line each)
EO:11904, 11629, 10870: short orders, quick. EO:11545, 11302: reading the amending orders for before/after text. EO:11046: three amendments and a sec. 5 savings clause, then rejected for the APP-only EO 13286 record. EO:13736: 21-clause inventory and the short-quote fix (inventory correction). Blocks: reading the view, OFR edge notes (jobs/later-events/output/EDGES.csv, read once for all 25) and the missing-lists.

## batch-check (applied-v3)
claims_checked 6, strict pass 6, fail 0; actual checker all_checks_passed 6, unverified 0, fail 0; blocked 19; actionable failures none. applied-v1 (11046 rejected) and applied-v2 (13736 short-quote unverified) are kept as history.

## Geddes
applied-v3/GEDDES_LINT.json: 0 flags, 6 coverage gaps. GEDDES_RESOLUTIONS.json records no resolutions needed.

## Full-packet files opened beyond the views
LOOKUPS.md (read once), PACKET.json (read in scripts for current_law_leads and the evidence ids of EO:11046), LOOKUPS.json/LOOKUPS.details.json (structure and one hit list), decisions.csv and clauses.csv. Repository sources opened: held order texts under jobs/fr-originals and jobs/app-executive-orders (EO 14085, 13286, 11429, 11609, 11382, 10807, 12608, 14131, 14382, 14384, 14329), jobs/theophilus-sources usc-t51-s20306.txt, jobs/later-events/output/EDGES.csv, jobs/claim-kit sources (assemble.py, batch.py, AGENT_PROTOCOL.md), one prior claim file (research/readiness/claims/claude-2026-11-04-tribonian-o27.jsonl) read for the shape of the current_predicate and first_end fields only.

## Tool defects and notes
- The view field own_original_text for EO 10521 contains the whole Federal Register issue page (contents, codification guide), not only the order text.
- batch-check exit 1 on a clause quote under about 20 characters (quote_verbatim:too_short_to_verify); fixed by inventory correction.
- kit.py apply rejects an APP-mirror later-event source when an official copy exists in the repo even if the packet has no citable official record for it.
