# Producer report, packet c10 (route: correction)

Start 2026-11-25T09:11:21Z; end 2026-11-25T09:17Z (see handback).

Final applied directory: applied-v1 (0 submitted, 9 not submitted: 7 blocked, 2 unresolved). batch-check: 0 claims checked, Geddes 0 flags, 0 coverage gaps.

## Outcomes
- EO:12964 blocked. Missing: Commission final report submission date (sec. 4 ends it 30 days later); no held source dates it. Bound: ended no later than EO 13062 (signed 1997-09-29, effective 1997-09-30), whose recital says the committees "have terminated and whose work is completed". A bound, not a first end (owner ruling 2026-10-28).
- EO:13032 blocked. Amendment of the 12964 report date; its end follows the parent's unresolved end. Same missing source.
- EO:13038 blocked. Missing: final report date (sec. 4). Bound: EO 13138 (1999-09-30).
- EO:13075 blocked. Missing: Special Oversight Board final report date (sec. 3(b)). Bound: EO 13225 (signed 2001-09-28, effective 2001-09-30).
- EO:13090 blocked. Missing: final report date (sec. 3(d), 60 days). Bound: EO 13225.
- EO:13168 blocked. Missing: final report date (sec. 6). The own-terms outer limit (2 years, 2002-09-22) is later than the EO 13225 revocation, so it gives no bound.
- EO:13210 blocked. Missing: final report date (sec. 6). Bound: EO 13316 (signed 2003-09-17, effective 2003-09-30); its recital is disjunctive ("terminated or whose work is completed").
- EO:13101, EO:13148 unresolved (work not finished, no missing source identified). Expected first end: EO 13423 sec. 11(a)(i) and (iv), 2007-01-24. Still to do: rebuild the 91 and 105 row clause sheets from the filed claims' inventory_overrides with per-clause reasons; read the current-law leads (13101: 48 CFR 2823.404-70, 48 CFR 552.238-78, 41 CFR 102-76.55; 13148: 33 CFR 148.737, 28 CFR part 61 App. E, 42 U.S.C. 4321 note, EO 13693 amendment of EO 13327); confirm an adequate registered EO 13423 text.

## Why not v1 intervals
apply builds v1 claims with an exact end only. The evidence supports an interval for the commission orders (terminated before the revocation), but the sheet cannot express one, so these are blocked with the bound in ASSESSMENT.jsonl.

## Time
Most time went to reading the views and the 13101/13148 inventory structure; the other seven turned on one missing report date each.

## Files opened beyond views
packet decisions.csv and clauses.csv; held texts EO_13138, EO_13225, EO_13316, EO_13423, EO_13148 by grep; research/readiness/claims files for precedent (parsed in a script).

## Coordinator note
After 09:25Z files arrived (selden-fr-citers etc.), grep of jobs/selden-fr-citers/output/texts and selden-fr-acting for the commission names found no report-date source. No block rested on a missing directory.

## Tool defects
None. Two context-heavy outputs (clause-override dump) came from printing a whole claim_kit field.

## Pass 2, 2026-11-25 (EO:13101 and EO:13148, at the coordinator's request)
Final applied directory: applied-v3. applied-v2 was rejected by apply (original_confirmed was false) and is kept unchanged. applied-v1 is the first pass.
- EO:13101 submitted (85-scope corrected inventory from the filed claim's overrides). EO:13148 submitted (94 scopes). Both claim status no; first end for every clause is EO 13423 sec. 11(a)(i) / (iv), 2007-01-24, except sec. 901 of each order (revocation of other orders), which is recorded as performed on signing (1998-09-14 and 2000-04-21) with the surviving consequence under savings (transferred_or_accrued). The sec. 901 performance reading is a judgment a reviewer may contest.
- Current-law conflict NO_ORDER_CITED_IN_CURRENT_LAW resolved from the held snippets and the 42 U.S.C. 4321 note, which records EO 13148 as revoked by EO 13423. The regulation texts themselves are held only as snippets.
- EO 13423 end source is the Federal Register text (jobs/fr-originals/data/full_run/texts/EO_13423.txt); no working-text disclosure needed.
- batch-check: 2 claims checked, 2 pass, 0 failures; Geddes 0 flags, 2 coverage gaps (citing_corpus_incomplete), recorded in applied-v3/GEDDES_RESOLUTIONS.json as disputed (coverage note, not a defect).
- Other seven orders remain blocked as in pass 1.
