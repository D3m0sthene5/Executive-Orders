# Producer report y07 (papinian)

Start 2026-11-10T04:10:16Z; end 2026-11-10T04:43Z. Final applied directory: applied-v3 (applied-v1 and applied-v2 are superseded).

## Outcomes
Submitted (6): EO:8809, EO:11298, EO:11851, EO:12109, EO:12572, EO:13276, all YES with checked_through 2026-10-14.
Blocked (19): see ASSESSMENT.jsonl blocker column for the exact missing source of each.

| Order | Outcome | Why / missing source |
|---|---|---|
| 8809 | submit | one clause, restated by EO 9323 and EO 10444 and amended by EO 14085 s.2 (before/after recorded); OFR "See" Transfer Order 30 addressed |
| 11298 | submit | one clause; 10 U.S.C. 1035 note and statute held |
| 11851 | submit | inventory corrected to four clauses (machine merged s.2 into 1(b)); 7 U.S.C. 1854 and 19 CFR 12.6 held |
| 12109 | submit | inventory split: 1-101 operative, 1-102 ended 1979-01-01 by own terms (date from EO 12107 s.1-101) |
| 12572 | submit | one clause; 48 U.S.C. 1801 note prints it as current |
| 13276 | submit | 13 clauses (section 3 heading merged into 3(a)); EO 13286 s.1 amendment dated by its s.92 effective date 2003-03-01, not the signing date |
| 10173 | blocked | inventory defect (page text mixes a CAB regulation); six amending orders and current 33 CFR part 6 (amended by USCG-2020-0304) |
| 10694 | blocked | inventory defect (item 2 runs across a contents page); EO 13286 s.74 and EO 14085 s.3 clause-level text |
| 10830 | blocked | whether the 1959 seal approval survives "shall be modified" directions (EO 13545, 13824, 14327) |
| 10910 | blocked | EO 11287 / EO 10961 clause-level comparison not done |
| 10982 | blocked | ten clauses, EO 12107 and EO 12748 clause-level work not done |
| 11177 | blocked | page/image check required (29 FR 13097), bounded text |
| 11183 | blocked | ten clauses, five amendments, thirty continuation orders unlocated |
| 11899 | blocked | s.2 performance date (5 CFR part 352 issuance) not held |
| 11997 | blocked | s.5 savings sentence status; heading unresolved |
| 12268 | blocked | Hostage Relief Act ss.103-105 text not held |
| 12411 | blocked | inventory omits s.2; recodified authority statute text |
| 12994 | blocked | 34 clauses, six amendments, EO 14354 provision not located |
| 13219, 13382, 13438, 13611, 13667, 13835 | blocked | emergency-dependent: NEA continuation notices not held (13438: none after 2022 held; 13611: Proc. 11026 of May 5, 2026 not held) |
| 13461 | blocked | 18 office clauses need current HHS organization sources |

No order was found not in force on 2026-10-14 on held evidence; the 13438 and 13611 readings are "unknown".

## What took the time (one line each)
8809: reading three restating amendments and the OFR See note. 11298: confirming heading from page text. 11851: correcting inventory spans. 12109: splitting 1-101/1-102 and sourcing the OPM date. 12572: Covenant-derived term records ruled out. 13276: 13 clause rows and EO 13286 effective date. Blocks: triage from views, inventory/chain checks; no deep reading beyond the views.

## Batch-check (applied-v3)
6 claims checked; strict pass 6, fail 0; actual checker all checks passed 6, mechanical unverified 0; 19 blocked; actionable failures none.
applied-v1 passed but 13276 had an "unverified: too_short_to_verify" item (14-character heading clause); fixed in v2 by merging the heading into 3(a). v2 Geddes flagged EO 8809 (reported_empty_search_has_hit); fixed in v3.

## Geddes
v3: 0 flags, 8 coverage gaps (citing_corpus_incomplete, corpus-level). Resolution file: applied-v3/GEDDES_RESOLUTIONS.json.

## Files opened beyond the views
PACKET.json via batch.load_packet (dossier evidence ids, spans) in a script; LOOKUPS.md head only; jobs/current-law and jobs/later-events output CSVs (ORDERS_CURRENT_LAW, MENTIONS, EDGES, CATALOG_INDEX, COUNTEREVIDENCE_LEADS, USC_EO_NOTES); held statute/CFR texts under jobs/theophilus-sources and later-order texts under jobs/fr-originals and jobs/selden-fr-citers; EO_12107 text. No other packet folders opened.

## Tool defects
None blocking. Notes: `sleep` polling is blocked by the shell tool; the view caps hide current-law hit texts so I read jobs/current-law CSVs directly; first_cause has no value for in-force orders (left empty in ASSESSMENT.jsonl).
