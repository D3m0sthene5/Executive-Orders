# Producer report: baldus y07

Start UTC 2026-11-25T15:51:06Z. End UTC 2026-11-25T16:08Z. Final applied directory: applied-v3.

## Outcomes
- EO:12105 submit (YES). Seven clauses: delegation, three content requirements and the 1-202 savings sentence operative with EO 12107 (effective 1979-01-01) as an amendment; 1-201 (revocation of EO 11881) terminated by performance 1978-12-19. 1-202 is recorded operative only because no held source shows the preserved pre-1978 regulations were all modified or superseded (limit stated in the claim).
- EO:12139 submit (YES). 1-101, 1-102 and 1-103 with its subsections operative as amended by EO 13383 and EO 13475; 1-104 and 1-105 (amendments of EO 12036) terminated by performance 1979-05-23. Inventory corrected (subsections (a) and (b) merged, 23 and 25 characters, below the checker's quotation minimum). EO 12333 (revokes EO 12036) is disclosed in the reasoning but not cited because its page check is not completed and the checker rejects it as a later-event source.
- EO:12208 submit (YES). Inventory corrected to ten clauses (merged the (e) citation fragment into 1-101(a), trimmed 1-103(c) before the page break, added 1-104). 1-101(b), 1-102(a), 1-102(b) terminated 2003-03-01 (EO 13286 section 49, effective by section 92); EO 12608 section 15 recorded as an amendment of 1-102(a); the rest operative as amended and renumbered.
- EO:12115 blocked. Missing: held source for Neutrality Treaty entry into force, the Panama Canal Act abolition of the Governor of the Canal Zone, the Corozal cemetery agreement, and performance of the disinterment/reinterment/transport commands (the April 1, 1982 date is a request deadline, not an end).
- EO:12125 blocked. EO 13124 (held at jobs/fr-originals/output/texts/EO_13124.txt) amends the Rule 3.1(b) text the order added, but it and the later 5 CFR 3.1 history (65 FR 41868; EO 14410) are not citable evidence in the packet. A source supplement is needed.
- EO:12137 blocked. Dated parts: 1-2 Advisory Council revoked effective 1982-12-31 (EO 12399 section 4(k), section 6); 1-301(e) deleted by EO 13724. The other 36 clauses depend on ACTION and one-time transfers with no held text on their later status.
- EO:12154 blocked. Fifteen amending orders held, but no Executive Schedule text as of 2026-10-14 to decide each of the 14 position placements.
- EO:12107 blocked. 86 clauses, unresolved dossier conflict (2018-06-15 partial revocation, no actor or text held), no consolidated current text.
- EO:12163 blocked. 120 clauses, about twenty amending orders, partial revocations (EO 12292 section 8(a), EO 12608 section 30, EO 13118 Part 1-4), no consolidated current text or statutes.

No held evidence showed an order not in force on 2026-10-14, so no ledger-contradicting blocks.

## What took the time (one line each)
- 12105: finding that EO 12107 section 2-101(b) is the amendment and settling 1-202 and 1-201 states; CURRENT USC record failed custody (bytes not held), so the original was used as the current basis.
- 12139: EO 12333 failed the working-text source check; reworked 1-104/1-105 as performance; short-quote inventory merge.
- 12208: inventory correction offsets; tracing EO 13286 section 49 and effective date section 92 (no citable record of section 92, so the date is stated from the held FR text in the reasoning).
- 12115: reading the order and confirming no held source on treaty entry into force or performance.
- 12125: finding EO 13124 and 5 CFR 3.1 history not citable.
- 12137, 12154, 12107, 12163: sizing the clause counts and amendment chains; triaged to blocks with exact missing sources.

## Runs
- applied-v1: 12139 rejected (EO 12333 as first-end source fails working-text check); 12105 and 12208 failed selected-source custody because CURRENT USC records are custody_record_only.
- applied-v2: all three assembled; batch-check showed 12139 quote_verbatim too_short_to_verify on 1-103(a) and (b).
- applied-v3 (final): apply assembled 3, blocked 6; batch-check strict_claim_pass 3, strict_claim_fail 0; actual checker claims_all_checks_passed 3 of 3, mechanical pass 3, unverified 0, fail 0, gate passed 3; actionable_failures none.

## Geddes
GEDDES_LINT.json in applied-v3 (written by batch-check): 0 flags on 3 claims, 9 coverage gaps (listed in the file). No GEDDES_RESOLUTIONS.json needed.

## Full-packet files opened beyond the views
PACKET.json (loaded once through batch.load_packet to read evidence records and clause spans, not printed), LOOKUPS.md (read in full), decisions.csv and clauses.csv (edited). READ.md and LOOKUPS.details.json not opened beyond a key listing.

## Tool defects and notes
- The USC zip-derived CURRENT: records are custody_record_only (zip bytes not held), so every YES claim that uses them fails selected-source custody; the original-plus-bounded-search route was used instead.
- The dossier's own working_text template lists mirror and held-text-lead sources for later events; none was used, so working_text was left blank.
- The packet citable evidence omits EO 13124 (12125) although its text is held; a claim cannot cite it without a supplement.
- ASSESSMENT first_cause has no value for orders still in force; "unresolved" was used with formal_revocation_after_earlier_cessation "no".
