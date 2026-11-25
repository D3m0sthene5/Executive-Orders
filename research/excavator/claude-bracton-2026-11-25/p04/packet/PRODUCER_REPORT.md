# Producer report, packet p04 (claude, 2026-11-25)

Start 2026-11-25T10:15:31Z; end 2026-11-25T10:36Z. Final applied directory: applied-v2.

## Outcomes
- EO:5825 submit (no). Revoked by EO 8189 (signed 1939-07-05), exact, no delayed effect; EOs of 1932-39 touching the Instructions/Consular Regulations read, none touches leave.
- EO:14006 submit (no). Revoked by EO 14148 sec. 2(q), 2025-01-20, exact; no deadline or performance event in the order. Stage 19 QUARANTINED_RELATIONSHIP_CONFLICT cannot be cleared by a claim (the tracker holds counterevidence open); disclosed in conflict_resolutions.
- Blocked (own-terms end undated, 30 days after a report whose submission date no held source gives): EO:12792 (sec. 3(e); report date 1993-01-20 per EO 12827), EO:12946 (sec. 4(a)), EO:13227 (sec. 4(e); report date 2002-07-01 per EO 13255). Filed bound dates for 12946 (1997-09-30) and 13227 (2003-09-30) are wrong; EO 13062 was signed 1997-09-29 and EO 13316 on 2003-09-17.
- Blocked (one-time/time-bound task clauses without dated performance; revocation is only a bound; Astra source-audit holds name the blanket premise): EO:13783, EO:13792 (held DOI report undated as to submission), EO:13807 (EO 13990 sec. 7(a)/(b), 2021-01-20), EO:13997 (EO 14148 sec. 2(k), 2025-01-20).
- Exact missing source per block is in decisions.csv unresolved_material_gaps and ASSESSMENT.jsonl.

## Time per order
12792/12946/13227: read order, confirmed no held report-date source (cruden name searches). 13783/13807/13997: classified task vs standing clauses (clause lists of 51/52/23). 13792: checked held DOI report for submission date. 14006: read order, USC note, conflict ids. 5825: traced 1932-39 Foreign Service orders.

## batch-check (applied-v2)
9 members; 2 claims checked, 2 strict pass, 0 fail; actual checker 2/2 all checks passed; 7 blocked; 0 actionable failures.

## Geddes
applied-v1: 2 flags on EO:5825 (attributed_quote_not_verbatim: a quote from EO 8189 attributed to EO 5825's body; heuristic). Fixed by removing the quotation in applied-v2; applied-v2 lint: 0 flags, 0 coverage gaps. GEDDES_RESOLUTIONS.json empty.

## Files opened beyond the views
research/excavator/claude-production-2026-10-28/PRODUCTION_ROUTE.md, CLAIM_SCHEMA.md, BATCH.md (two sections), the four owner rulings, NIRA PRODUCER_BRIEF section, LOOKUPS.md, decisions.csv/clauses.csv; views read only by key subsets. Repository sources: held texts for EO 12827, 13255, 12869, 13062, 13316, 8189, 14148, 13990, 5642, 6737, 6810, 7012, 7013, 7261, 7449, the DOI final report text, jobs/current-law MENTIONS.csv, readiness-tracker READINESS_BY_ORDER.csv, astra lambertini-review EO_13783 audit, stage19 CAUSAL_QUEUE.csv, jobs/claim-kit batch.py/assemble.py (code), jobs/readiness-tracker/tracker.py (grep). PACKET.json loaded via batch.load_packet in scratch scripts (check_sources=False). applied-v1 (rejected-assembly then 2 Geddes flags) was removed and recreated once for a missing savings_check; applied-v1 now holds the Geddes-flagged version.

## Tool defects / notes
- kit.py assembles v1 claims only; a bound-only end (v2 not_later_than) cannot be submitted through apply, hence the blocks.
- Machine searches report 0 hits for EO 5825 although EO 8189 names it (number format).
- Views are not slim (0.1-0.8 MB each).
