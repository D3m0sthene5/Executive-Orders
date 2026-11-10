# Producer report, y05 (papinian, Claude Sonnet 5.5)

Start 2026-11-10T03:51:00Z, end 2026-11-10T04:13:16Z. Final applied directory: `applied-v2` (applied-v1 was a two-order pilot of the sheet format; it passed and is superseded).

## Outcomes (8 submitted, 17 blocked)

Submitted (YES, operative with the held original, later events attached, bounded searches read):
- EO:10552 submit. Delegation continues as amended by EO 12107 (2-101(b), effective 1979-01-01); 5 U.S.C. 6104 note and 5 CFR part 610 cite it.
- EO:10670 submit. No later instrument and no own-terms end; bounded searches have zero hits.
- EO:10718 submit. Inventory corrected to the order's 3 sections (dossier clauses came from Reorganization Plan No. 1 of 1957 on the same pages); 22 U.S.C. 4219 note and 22 CFR part 22 cite it.
- EO:10849 submit. Amended by EO 10942 (1961-05-19, design description); 14 CFR 1221.102 current.
- EO:11141 submit. 48 CFR 22.901 restates the policy.
- EO:11300 submit. 8 CFR 252.5 applies the designation; treaty status source not held (stated in the claim).
- EO:11701 submit. Inventory corrected (section 1 added; 5 sections); section 5 (supersedes EO 11598) terminated by the order's own date 1973-01-24; sections 1-4 operative per 20 CFR 654.8 and 48 CFR 22.1300.
- EO:11935 submit. Amended by EO 12107 (OPM for Commission, 1979-01-01); 5 CFR 7.3 reproduces the rule; EO 13197 renumbering and EO 13940 recital explained as not ends.

Blocked (exact missing source in each decisions.csv `unresolved_material_gaps` and ASSESSMENT.jsonl `blocker`):
- EO:7993 citable PLO 2710/2711 (partial revocation) and remaining-lands source.
- EO:10033, 10577, 11521, 11609, 12107, 12163, 12591, 13091, 11990: multi-clause orders (5 to 90 clauses) whose per-clause effect of the held amenders and a current predicate were not worked in this pass.
- EO:11926 EO 13286 citable only as APP mirror records (official FR text is overflow, not citable).
- EO:13570, 13661, 13871, 13884, 14088: National Emergencies Act continuation notices are leads absent from the census (not citable); some years missing.
- EO:14410 no performance source for the 7-day and 60-day steps.

No held evidence showed any assigned order was not in force on 2026-10-14; no ledger change is suggested.

## What took the time (one line each)
- 10552 reading EO 12107 section 2-101 and 2-404 for the amendment and effective date.
- 10670, 11141, 11300, 10849 short texts; time went to locating current CFR/USC text.
- 10718 inventory correction (neighbor Reorganization Plan on the same FR pages).
- 11701 inventory correction and the self-executing supersession clause.
- 11935 reconciling EO 13197 renumbering, EO 12107 and EO 13940.
- 11926 reading EO 13373, 14131 and 13286; blocked on citable source for 13286.
- Blocked multi-clause orders: triage of chain events and clause counts only.
- Sanctions orders: reading the dossier missing list for notices.

## batch-check (applied-v2)
8 claims checked, 8 strict pass, 0 fail, actual claim checker 8/8 passed, 0 actionable failures, 17 blocked, 0 independent certifications.

## Geddes
`applied-v2/GEDDES_LINT.json`: 0 defect flags, 10 coverage gaps (8 claims with coverage gaps, advisory). `GEDDES_RESOLUTIONS.json` is empty (no flags).

## Full-packet files opened beyond the views
`LOOKUPS.md` (condensed per order by script), `PACKET.json` via `batch.load_packet(check_sources=False)` for ORIGINAL span and evidence ids; decisions.csv and clauses.csv rows; no READ.md and no LOOKUPS.details.json content beyond a key listing. Repository texts opened: jobs/fr-originals EO_12107, EO_13373, EO_14131, EO_13197, EO_13286 (grep), EO_12608 (grep), EO_10850, EO_10854, EO_14410 (grep); jobs/theophilus-sources texts for 5 CFR 7.3, 14 CFR 1221.102, 48 CFR 22.901, 8 CFR 252.5, 20 CFR 654.8, 22 U.S.C. 4219; `cruden.py search "10552"` and `cruden.py number EO:13197` (the latter slow).

## Tool defects
- Shell `( time cmd ) > log &` produced empty logs in this environment; batch-check was run in the foreground instead.
- `cruden.py number` exceeded the 120 s default tool timeout.
- The dossier's PARTIAL_END_CANDIDATE conflicts for EO 13884 and EO 13871 list notice-date "revocations" with unidentified actors (these are NEA continuation notices, not revocations).
