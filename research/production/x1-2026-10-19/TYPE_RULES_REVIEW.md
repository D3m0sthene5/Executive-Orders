# Type rules review, round 4 (independent AI agent; not human certification)

Reviewed 2026-10-19T17:04:01Z. 22 rules; TR-STOCK-DRIVEWAY withdrawn. Approved 22, approved with required changes 0, rejected 0, changed after review 0. Certified whole-lifecycle count unchanged at 0.

| Rule | Decision | Basis | Quote exact | Text hash | sha256 (first 12) |
|---|---|---|---|---|---|
| TR-ALIEN-PROPERTY-SALE | approve_pattern_lead_only | carried from round 2 | True | True | cdb05f4c8281 |
| TR-BIRD-REFUGE | approve_pattern_lead_only | carried from round 2 | True | True | 2f3979ca7188 |
| TR-CANAL-ZONE | approve_pattern_lead_only | carried from round 3 | True | True | 13d7930c7b1e |
| TR-CLOSING-MOURNING | approve_pattern_lead_only | carried from round 1 | True | True | c825b13728c4 |
| TR-CS-WAIVER | approve_pattern_lead_only | carried from round 2 | True | True | c64f4416a934 |
| TR-EIGHT-HOUR-SUSPENSION | approve_pattern_lead_only | carried from round 2 | True | True | fec45cfa7461 |
| TR-FUND-ALLOTMENT | approve_pattern_lead_only | carried from round 2 | True | True | 5da95f938c9a |
| TR-INDIAN-RESERVATION | approve_pattern_lead_only | carried from round 2 | True | True | b54edfc971a4 |
| TR-LAND-WITHDRAWAL | approve_pattern_lead_only | carried from round 2 | True | True | a4ac9bd6aff4 |
| TR-LIGHTHOUSE | approve_pattern_lead_only | carried from round 2 | True | True | 1639b681f7c6 |
| TR-MILITARY-RESERVATION | approve_pattern_lead_only | carried from round 2 | True | True | 27766fb580a0 |
| TR-MINERAL-WITHDRAWAL | approve_pattern_lead_only | carried from round 2 | True | True | f3ea8d79908d |
| TR-NATIONAL-FOREST | approve_pattern_lead_only | carried from round 2 | True | True | e17032017fe2 |
| TR-NRA-CODE | approve_pattern_lead_only | carried from round 2 | True | True | fc05b20b26a7 |
| TR-OWN-TERMS-EXPIRY | approve_pattern_lead_only | carried from round 3 | True | True | e56fd6f50876 |
| TR-PHILIPPINES | approve_pattern_lead_only | carried from round 2 | True | True | 93b87c55f3a1 |
| TR-POWER-SITE | approve_pattern_lead_only | carried from round 3 | True | True | 7a5a92b5c180 |
| TR-PROPERTY-TRANSFER | approve_pattern_lead_only | round-4 review | True | True | 9cfc109fd52d |
| TR-RETIREMENT-EXEMPTION | approve_pattern_lead_only | carried from round 2 | True | True | e0168a290024 |
| TR-TAX-RETURN-INSPECTION | approve_pattern_lead_only | carried from round 2 | True | True | 9a56293122d4 |
| TR-WATER-RESERVE | approve_pattern_lead_only | carried from round 1 | True | True | 85083f86d4f4 |
| TR-WWI-EMERGENCY | approve_pattern_lead_only | carried from round 3 | True | True | cb259b6f16c8 |

## TR-PROPERTY-TRANSFER (round 4)

All three round-3 required changes are made. (1) The qualified-date / discretionary-partial-transfer outlier is added to outlier_conditions, and effective_date_basis now says a date qualified by 'or as promptly thereafter as practicable', or a partial transfer at an official's discretion, is not a delivery date: the end is the delivery or accession record, otherwise a stated gap. (2) The transfer-date sentence is a separate second quoted_parts entry, running to '... the Department of State and the Library of Congress.'; two spans [554,1720] and [1722,1917]; each part is exact and unique in EO_206.txt at those spans, and quoted_clause equals part 1. (3) required_evidence adds the delivery or accession record (agency or receiving-institution record) with its date, or an explicit gap. Text file sha256 equals source.text_sha256. No new errors found; the generalized 'receiving-institution' wording is acceptable. Approval is of a research pattern lead only; the exemplar text is a mirror transcription, not an authenticated original.

## Required changes

None.

## Recommended (not blocking)

Round-3 recommendations for TR-POWER-SITE, TR-OWN-TERMS-EXPIRY, TR-WWI-EMERGENCY and TR-CANAL-ZONE remain open (see TYPE_RULES_REVIEW_R3.md); those files are unchanged and their approvals stand.
