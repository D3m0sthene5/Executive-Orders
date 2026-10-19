# Type rules review, round 3 (independent AI agent; not human certification)

Reviewed 2026-10-19T17:02:32Z. 22 rules; TR-STOCK-DRIVEWAY withdrawn. Approved 21, approved with required changes 1, rejected 0, changed after review 0. Certified whole-lifecycle count unchanged at 0.

| Rule | Decision | Basis | Quote exact | Text hash | sha256 (first 12) |
|---|---|---|---|---|---|
| TR-ALIEN-PROPERTY-SALE | approve_pattern_lead_only | carried from round 2 | True | True | cdb05f4c8281 |
| TR-BIRD-REFUGE | approve_pattern_lead_only | carried from round 2 | True | True | 2f3979ca7188 |
| TR-CANAL-ZONE | approve_pattern_lead_only | round-3 review | True | True | 13d7930c7b1e |
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
| TR-OWN-TERMS-EXPIRY | approve_pattern_lead_only | round-3 review | True | True | e56fd6f50876 |
| TR-PHILIPPINES | approve_pattern_lead_only | carried from round 2 | True | True | 93b87c55f3a1 |
| TR-POWER-SITE | approve_pattern_lead_only | round-3 review | True | True | 7a5a92b5c180 |
| TR-PROPERTY-TRANSFER | approve_with_required_changes | round-3 review | True | True | 3510dd4a3134 |
| TR-RETIREMENT-EXEMPTION | approve_pattern_lead_only | carried from round 2 | True | True | e0168a290024 |
| TR-TAX-RETURN-INSPECTION | approve_pattern_lead_only | carried from round 2 | True | True | 9a56293122d4 |
| TR-WATER-RESERVE | approve_pattern_lead_only | carried from round 1 | True | True | 85083f86d4f4 |
| TR-WWI-EMERGENCY | approve_pattern_lead_only | round-3 review | True | True | cb259b6f16c8 |

## Required changes

TR-PROPERTY-TRANSFER:
- Add the outlier required in round 2 (not added): a stated transfer date qualified by 'or as promptly thereafter as practicable' (as in the exemplar), or a partial transfer at an official's discretion (the exemplar's 'exceptions and reservations ... in the discretion of the Secretary of State'), is not a delivery date; the delivery or accession record is the end, otherwise a stated gap. Without it, effective_date_basis ('a stated effective date in the order ... over the signature date') would read July 1, 1903 as the exemplar's own end date.
- Make the transfer-date sentence a second quoted_parts entry (round 2 asked for a second part; it is now joined to the first with a blank line in one part and one span), and end it at the sentence's end: '... conveniently practicable to the Department of State and the Library of Congress.' The current quote stops mid-sentence after 'conveniently practicable'. Record two spans.
- Add to required_evidence: the delivery or accession record (agency or Library of Congress report) or an explicit gap.

## Recommended (not blocking)

- TR-POWER-SITE: use s.24's 'reserved or classified as power sites'; add that s.24's reach for a given reserve must be shown from the order and FPC/FERC records; name FERC.
- TR-OWN-TERMS-EXPIRY: state the revoked/replaced case directly; start the quote at 'the effective date of Section 18' and drop the signature block.
- TR-WWI-EMERGENCY: give exact proclamation dates (Germany Nov. 14, 1921; Hungary Dec. 20, 1921, both checked; Austria Nov. 17, 1921, verify); state the Overman Act's end precisely.
- TR-CANAL-ZONE: add that the 21st Amendment did not itself end federal law in the Canal Zone.
