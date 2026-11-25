# Producer report y12 (baldus)

Start 2026-11-25T16:15:02Z. End 2026-11-25T16:44:00Z. Final applied dir: applied-v6.

## Outcomes
- Submitted (3): EO 13251, 13303, 13309. Blocked (6): EO 13118, 13219, 13265, 13268, 13312, 13315.
- Batch-check v6: 3 claims checked, 3 pass the actual checker and gate; 6 blocked.
- Geddes: 5 flags (13251 x1, 13303 x4), all answered as disputed in applied-v6/GEDDES_RESOLUTIONS.json; gate passes. 3 coverage gaps (citing corpus incomplete) not gated.

## Per order (what took the time)
- 13309: submitted; sec 5 ended 2005-09-30 by terms, EO 13446 reordered members; USC CURRENT record custody_record_only so ORIGINAL used as current basis.
- 13251: submitted; EO 13261 amended sec 3(b); four clauses under the checker's quote length were merged by inventory override (38 to 34).
- 13303: submitted; sec 1 ended by EO 13668 (2014), EO 13350/13364 changes, conflict_resolutions needed for PARTIAL_END_CANDIDATE_ON_YES_ORDER.
- 13265: blocked; EO 13545 text not citable (custody_record_only / APP mirror fails); also ACT record for EO 14045 points to the wrong span.
- 13219, 13315: blocked; National Emergencies Act continuation notices missing for 2014 and 2013-2020 respectively.
- 13268: blocked; emergency-dependent via EO 13224, no continuation notice held.
- 13312: blocked; partly revoked by EO 13324, clause-level sources not citable.
- 13118: blocked; no checkable current text of amended orders.

## Files opened beyond views
LOOKUPS.md, HELD_SUPPLEMENT.json, HELD_SOURCES.json, DISPATCH_CHECK.json, PREPARE.json, ADMISSION.json; held texts of EO 13446, 13261, 13324, 14294, 13668, 13364, 13350, 13545, 13824, 14327 and notices; claim-kit docs and owner rulings.

## Tool defects
- ACT record for EO 14045 holds the order's own working-group text, not an amendment of EO 13265.
- Duplicate ACT records with different @hash variants.
- Apply/batch-check logs are very long because of source-recovery task JSON.
- Inventory splits create sub-verifiable clauses (headings), needing manual merges.
