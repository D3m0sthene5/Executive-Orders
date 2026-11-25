# Producer report, packet c08 (route: correction)

Start 2026-11-25T09:15:38Z; end 2026-11-25T09:29Z (UTC).

Final applied directory: applied-v3 (applied-v1 had one rejected member: the first end of EO 12076 clause 1-202 cited a clause record that carries no actor; applied-v2 passed batch-check with one Geddes flag on EO 12121; both kept, not overwritten).

## Outcomes
- EO:12076 submit. Whole order revoked "as amended" by EO 12154 section 1-202 (1979-09-04, read as on signing). Amendments by EO 12099, 12111 and 12119 are later events (strike-and-insert ruling). Clause 1-202 (revokes EO 11861) ends by performance on issuance, 1978-08-18. Quarantined Stage 19 relationship (EO 12060) answered in conflict_resolutions; the tracker blocker QUARANTINED_RELATIONSHIP_CONFLICT comes from the causal queue file and may persist after filing.
- EO:12121 submit. Sole command amends EO 12083 section 1-102; EO 12379 section 20 revokes EO 12083 "as amended" (1982-08-17). Exact end given with the reason it extinguishes the amendment (EO 12083 has no sunset; the amendment operates only inside it). Earlier-end tests recorded. This replaces the prior not_later_than bound; a reviewer may disagree that the cleanup revocation is the first end, and the claim states the alternative reading.
- EO:11941 blocked. Missing: dated source for the 1977 executive/congressional/judicial salary increase (held 28 U.S.C. 172 note says only "1977"; Schedule 7 may have been displaced before EO 12010 superseded the order on 1977-09-28) and a source tying it to section 3; also the effective date of the EO 12010 section 4 supersession versus the new-rate dates.
- EO:11971 blocked. Missing: dated record of submission of the Committee's report (and any section 3(b) extension). EO 12110 (effective 1978-12-31) is formal disposition and only a bound.
- EO:11973 blocked. Missing: dated record of transmittal of the final report (due 1978-04-01).
- EO:11998 blocked. Missing: dated record of submission of the Commission's report (due 1978-03-15).
- EO:11876, EO:12085, EO:12095: not assigned (board route); rows untouched; assessment rows written as "unresolved".

## What took the time
- 11941: separating the express supersession from the possible earlier 1977 salary displacement; clause inventory includes schedule-footnote pseudo-clauses.
- 11971/11973/11998: confirming no held source dates the reports (searched held texts by committee name).
- 12076: 35 clauses; amendment events; Geddes and quarantine reading.
- 12121: deciding whether a cleanup revocation is the first end for an order with no sunset.

## Checks
apply (v3): 2 assembled, 4 blocked, 3 unresolved. batch-check: 2 claims checked, strict pass 2, fail 0; actual checker 2/2 passed; actionable failures none.
Geddes (v3): 0 flags, 4 coverage gaps (own order body unverified / citing corpus incomplete: 1401 held files missing or changed); GEDDES_RESOLUTIONS.json has no entries.

## Files opened beyond the views
LOOKUPS.md (assigned reading); decisions.csv, clauses.csv; PACKET.json via batch.load_packet (evidence spans, conflicts, searches); held order texts in jobs/fr-originals, jobs/app-executive-orders, jobs/current-law/output/usc-notes, jobs/theophilus-sources; research/stage19/output/REVIEW_PACKETS.jsonl (quarantine lead). No READ.md, no LOOKUPS.details.json, no other packet folders.

## Tool defects
- Views are 55-420 KB; printing a view in full overflows context (first call consumed about 50k tokens).
- The assembler rejects a CLAUSES evidence id as first_end source with only "clause_N_first_end" (no actor); ORIGINAL id works.
