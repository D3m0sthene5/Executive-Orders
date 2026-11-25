# Producer report, packet y10 (agent baldus)

Start 2026-11-25T16:07:14Z. End 2026-11-25T16:26:53Z.

Final applied directory: applied-v3 (applied-v1 was superseded after a custody failure, applied-v2 after a 4-character inventory fragment; neither overwritten).

## Outcomes
- EO:12597 submit (YES). 21 units operative after one stated inventory correction (the 4-character fragment "801." merged into section 10). Current predicate is the held original clause text plus the bounded searches; the U.S. Code note found by the search is a custody_record_only lead and is not cited.
- EO:12600 submit (YES). 22 units operative; section 3(a)(i) terminated by its own 10-year age limit (end 1997-12-31, alternative reading 1997-12-30 disclosed; source is the whole held original because the packet has no smaller own-terms record).
- EO:12630 submit (YES). 44 units operative; 1988 deadlines in sections 1(c) and 5(c) are not ends and sit in clauses with continuing duties.
- EO:12657 submit (YES). 30 units operative; EO 13286 section 41 (effective 2003-03-01) recorded as a later event on every unit naming FEMA; section 6(a) to (c) carried as continuing on a disclosed limited basis (no held source dates performance).
- EO:12793 submit (YES). Sections 1 to 4 operative with EO 13286 section 31 and EO 14131 section 1 as later events (restatement notes for the reviewer); section 5 (supersession of EO 10879) terminated by performance 1992-03-20.
- EO:12748 blocked. Missing: official page-checked bytes of EO 12883 (58 FR 63281, 1993-12-01); the held fr-originals text is requires_page_check with low location confidence and the APP copy is custody_record_only. Decisions are retained in clauses.csv (sections 3 and 6 revoked by EO 13415 on 2006-12-01; sections 4, 5 and 8(a) performed 1991-02-03 and 1991-05-04; sections 1, 2, 7, 8(b), 9 continuing).
- EO:12608 blocked. 62-unit omnibus amendment and revocation order; missing held current text or status of each amended or revoked parent order and effective dates (only section 26, revoked by EO 13242 on 2001-12-18, is evidenced).
- EO:12656 blocked. 323 units; missing the official page/image check of 53 FR 47491 and a unit-by-unit mapping of EO 12977, 13074, 13228, 13286 sec. 42 and 13603 sec. 803(a) (revokes 401(3)-(4) on 2012-03-16) against the inventory.
- EO:12738 blocked. Amending order; missing held text of EO 12163 Part 1-1 and section 1-301 as of 2026-10-14 (EO 13118 restated Part 1-1 on 1999-03-31) to compare with the 19 units.

No order was found not in force on 2026-10-14; the ledger is unchanged. Evidence for the partial revocations is in ASSESSMENT.jsonl.

## What took the time (one line each)
- 12597: reading the order and deciding the Section 801 authority and EO 12356 cross-reference; inventory merge of the 801 fragment.
- 12600: age-limit end for section 3(a)(i) and finding an end source with an actor (only the whole original qualified).
- 12630: 44 definition and criteria units; checking EO 13061 and 13406 section citations.
- 12657: tracing the mislabeled EO 12977 chain entry to EO 13286 section 41; section 6 performance gap.
- 12793: reading EO 13286 sec. 31 and EO 14131 restatements; section 5 end date.
- 12748: reading prior blind reviews of an earlier claim (cited in the view), then the EO 12883 custody failure.
- 12608, 12656, 12738: inventory size and per-unit evidence, blocked quickly.

## batch-check (applied-v3)
packet members 9; claims checked 5; strict pass 5, fail 0; actual checker: 5 all checks passed, 0 unverified, 0 fail, gate passed 5; outcomes 5 assembled, 4 blocked.

## Geddes
GEDDES_LINT.json: 0 defect flags, 11 coverage gaps (not flags). GEDDES_RESOLUTIONS.json is empty (no flags).

## Full-packet files opened beyond the views
READ.md (first 3,000 bytes only), LOOKUPS.md (read), decisions.csv and clauses.csv (edited), PACKET.json (loaded once per script through batch.load_packet with check_sources=False; no direct reading). Repository sources read: held order texts under jobs/fr-originals, jobs/app-executive-orders and jobs/current-law/output (notes), ORDERS_CURRENT_LAW.csv and EVENT_CANDIDATES.csv rows for these orders, jobs/later-events/output/EDGES.csv rows for EO 12630, and an unattached prior blind review for EO 12748 that the view itself cites (research/excavator/claude-icecore-2026-11-05/evidence/yes/reviews).

## Tool defects and notes
- The packet chain and ACT records for EO 12657 and EO 12793 list EO 12977 as an amender; the quoted text is EO 13286 sec. 23/31/41 from a source-ladder queue file mislabeled with EO 12977's number. Not used.
- U.S. Code release-point CURRENT: records are custody_record_only (bytes not committed), so they fail selected-source custody; the first apply (applied-v1) showed this only in SELECTED_SOURCE_CHECK.json after reporting assembled proposals.
- A later-event source such as EO 12883 can fail the working-text check (requires_page_check, no exact official registration) with no clear message; the error is working_text_exact_grade_and_false_flag_required.
- Own-terms ends need an evidence record with an actor; CLAUSES records have none, so only ORIGINAL (whole text) or TERM records can serve.
- Python scratch scripts were run without -I because they import from the scratch folder; all repository scripts were run as instructed.
