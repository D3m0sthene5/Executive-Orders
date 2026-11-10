# Producer report, y08 (label producer-y08)

Start 2026-11-10T04:22:38Z; end 2026-11-10T04:44:08Z. Final applied directory: applied-v3 (applied-v1 and v2 were earlier iterations; v2 had three assembly rejections, fixed in v3).

## Outcomes (4 submitted, 20 blocked, 1 dispatch-blocked)

Submitted (all four pass the actual checker, batch-check strict pass 4 of 4, Geddes flags 0, so no GEDDES_RESOLUTIONS needed):
- EO:10352 (one clause, 33 CFR 6.10-1 still carries the order's text; EO 11249, 13143, 13273, 14116 amend other sections only).
- EO:10978 (eight clauses operative by the original_plus_bounded_search route; all three machine searches returned zero hits, stated as absence of an ending, not a 2026 positive source).
- EO:12047 (sections 1, 2, 3, 5 operative with the 2026-10-02 State Department notice as current use; sections 4 and 6 terminated 1978-04-01 by own terms).
- EO:12403 (three clauses operative; section 2 continues as amended by EO 12567, 12647, 12766, 13118).

Blocked, with the exact missing source (full text in decisions.csv unresolved_material_gaps and ASSESSMENT.jsonl):
- EO:9242A: ORIGINAL span (chars 556-1143) is sections 6-7 of the preceding EO 9242, not EO 9242-A; overrides cannot enclose the real text. Needs a re-prepared dossier.
- EO:10122: inventory merges sections 4 and 5 into sec3; text of the statutes replacing the Career Compensation Act not held.
- EO:11190: EO 13286 (amends section 1) is registered only as an APP mirror; an official-copy actor record is not registered (checker error official_copy_available_recheck_required).
- EO:12028: no held source for the completion date of the section 5-7 transfers (OMB determinations); inventory needs overrides; EO 12134 partial end.
- EO:12289: current text of 22 U.S.C. 4066(c)(1) and 4048(a) and Pub. L. 102-54 s.13(h)(2) not held.
- EO:12170, 12957, 12959, 13551, 13599, 13664, 13685, 13692, 13882, 14064, 14098, 14114, 14312: National Emergencies Act continuation notices through 2026-10-14 are not citable evidence (listed as absent from the census).
- EO:13350: EO 13668 ended the EO 13303 prohibitions that section 3 modified (clause-level dated decisions needed), plus the NEA notices.
- EO:13959: EO 14032 (2021-06-03) replaced and superseded sections 1-5 and the Annex; not a revocation, so the order is still treated as in force as amended; per-clause before/after decisions and NEA notices missing.
- EO:12281: dispatch-blocked (custody_record_only sources); assessment row only.

No order was found not in force on 2026-10-14 (so no ledger-contradicting finding), except that EO 13959's sections 1-5 and Annex were superseded in 2021 and EO 13350 was partly affected by EO 13668; both are recorded in the assessment rows.

## What took the time (one line each)
- 10352: tracing four Part 6 amendments to confirm none touches section 6.10-1.
- 10978: confirming zero hits and finding the 2011 notice as the only currency evidence.
- 11190: reading 11382 and 13286; blocked after apply showed the mirror-only source.
- 12047: finding the 2026 State notice; own-terms end needed an actor-bearing source (ORIGINAL id).
- 12403: tracing EO 11269 list amendments; official ACTOR_TEXT ids needed instead of APP mirror ACT ids.
- 12028, 10122, 12289, 9242A: inventory and source checks leading to precise blocks.
- Emergency orders: confirmed from the missing lists that notices are not citable; wrote assessment rows from the held current-law outputs.

## Batch-check
applied-v3: claims_checked 4, strict pass 4, fail 0, actual checker all passed 4, actionable failures none, Geddes flags 0 (coverage gaps 8).

## Full-packet files opened beyond the views
LOOKUPS.md (grep and per-order bounded print); LOOKUPS.details.json (one structure probe); PACKET.json (grep for ACTOR_TEXT:EO:13286 only); view source_catalogue sections for 11190, 12403, 12047. Also repository sources: jobs/current-law/output (ORDERS_CURRENT_LAW.csv, MENTIONS.csv, EVENT_CANDIDATES.csv, USC_EO_NOTES.jsonl), jobs/later-events/output/EDGES.csv (grep), held order texts under jobs/fr-originals and jobs/theophilus-sources, jobs/selden-fr-citers texts, jobs/claim-kit and research/stage19 code (format and error lookups).

## Tool defects and notes
- kit.py apply refuses a --write path outside the packet (a first trial to scratch failed harmlessly).
- A terminated clause whose end source is a CLAUSES record fails (clause_N_first_end: actor missing); an ORIGINAL or ACT/TERM record works.
- An ACT record that is an APP mirror triggers official_copy_available_recheck_required even when an official FR copy exists unregistered; ACTOR_TEXT ids avoid it where they exist.
- Machine extraction of EO 9242-A and EO 12028 clause spans was wrong or incomplete (described above).
