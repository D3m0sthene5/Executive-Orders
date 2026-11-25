# Producer report, packet y15 (producer baldus)

Start 2026-11-25T16:50:24Z. End 2026-11-25T17:11Z. Final applied directory: `applied-v8` (applied-v1 to v7 were earlier drafts; v8 is the only one that passed everything).

## Outcome per order

| Order | Outcome | Reason |
|---|---|---|
| EO:13664 | submit (yes) | South Sudan blocking order. Twelve annual notices 2015 to 2026 attached; last (91 FR 15513, March 24, 2026) continues the emergency beyond April 3, 2026. No own-terms end, no later instrument ends or amends it. |
| EO:13667 | submit (yes) | Central African Republic blocking order. Twelve notices 2015 to 2026; last (91 FR 25069, May 4, 2026). The held print refers to an Annex but contains none; disclosed in clause sec1-i and the rationale. |
| EO:13687 | submit (yes) | North Korea expansion order. Twelve notices on the EO 13466 emergency, each naming this order; last 91 FR 38231 (June 22, 2026). Inventory corrected: the frozen opening clause was only "I hereby order:"; widened to the preamble that expands the emergency's scope. |
| EO:13694 | submit (yes) | Cyber emergency order. Eleven notices 2016 to 2026 (last 91 FR 15511). Four amendments recorded as later events with before/after substance (EO 13757 eff. 2016-12-29 on sec 1(a) and sec 10; EO 13984 on sec 9; EO 14144 and EO 14306 on sec 1(a)). Conflict PARTIAL_END_CANDIDATE_ON_YES_ORDER resolved: the three listed "ends" are an OFAC general-license supersession and two notices saying EO 14148 revoked EO 14110. |
| EO:13722 | submit (yes) | North Korea blocking order. Eleven notices 2016 to 2026 on the EO 13466 emergency; last 91 FR 38231. Opening clause widened (frozen text too short to quote-check). |
| EO:13620 | blocked | Missing source: citable NEA continuation notices of 2017 to 2026 (FR Docs 2017-07238 to 2026-07069). Held on disk and declared in HELD_SUPPLEMENT.json, but the packet was not sealed with `--held-supplement`, so only 2013 to 2016 are citable. |
| EO:13671 | blocked | Missing source: the October 2014 DRC continuation notice (beyond October 27, 2014), the first renewal after signing; not held anywhere in the repository. Held notices start October 2015. |
| EO:13685 | blocked | Missing source: citable March 2018, 2019, 2020, 2021 Ukraine continuation notices (FR Docs 2018-04626, 2019-04120, 2020-04192, 2021-04759); on disk and in HELD_SUPPLEMENT.json but unsealed. |
| EO:13658 | blocked | Partial supersession by EO 14026 (as of 2022-01-30) and its 2025 revocation by EO 14236 (not in packet evidence); performance of the one-time commands (DOL rule 79 FR 60634, FAR rule) not held; no held presidential text on revival. Evidence shows the order was in force on 2026-10-14 for a residual class of contracts (DOL notice FR Doc. 2026-20646), so it is not a not-in-force case. |

No member was found not in force on 2026-10-14. All CURRENT records for 31 CFR and 22 U.S.C. are custody_record_only (eCFR bulk and U.S. Code zip bytes not held), so no claim cites them; every submitted clause cites the held Federal Register print as its current basis plus the held notice chain as later events.

## What took the time (one line each)

- EO:13664: first end-to-end test of the format; discovered CURRENT CFR records fail source custody and switched the basis to the held original.
- EO:13667: reading a 30-clause inventory and the missing Annex.
- EO:13687: inventory correction for the opening clause (all 23 clauses need override rows).
- EO:13694: tracing four amendments and writing before/after substance; resolving the machine "partial end" conflict.
- EO:13722: 36 clauses; opening clause widening after the checker could not verify a 15-character quote.
- EO:13620, 13671, 13685: finding that the notice chain is not citable (view vs PACKET.json vs HELD_SUPPLEMENT.json).
- EO:13658: reading EO 14026 and the two 2026 DOL notices, then deciding the clause partition cannot be sourced.

## batch-check (applied-v8)

packet_members 9; claims_checked 5; strict_claim_pass 5, fail 0; outcomes blocked 4, assembled_proposal 5; actual claim checker: claims_all_checks_passed 5, mechanical pass 5, unverified 0, fail 0, gate passed 5; actionable_failures none.

## Geddes

`applied-v8/GEDDES_LINT.json`: defect_flags 0; coverage gaps 5 (one per submitted claim, code `citing_corpus_incomplete`, an advisory about the lookup corpus). `GEDDES_RESOLUTIONS.json` written with an empty resolutions list because there are no flags.

## Full-packet files opened beyond the views

LOOKUPS.md (first 41 KB, printed once); PACKET.json and HELD_SUPPLEMENT.json via scripts (evidence ids, citable notices, conflicts); LOOKUPS.details.json via script (sentence scan of the held texts citing each of EO 13664, 13667, 13687, 13722); DISPATCH_CHECK.json, PREPARE.json, ADMISSION.json (headers only). Outside the packet: jobs/later-events/output/EDGES.csv (catalog edges), held notice texts under jobs/selden-fr-citers/output/texts/, EO 13757, 13984, 14144, 14306, 14026, 13848 and 14294 print texts, the DOL notices FR Docs 2026-02466 and 2026-20646, jobs/claim-kit sources (batch.py, assemble.py, README.md) to learn the field format.

## Tool defects and notes

- The view's citable-evidence list is capped at 40 records; EO 13694 and EO 13658 showed truncated lists, so notices had to be read from PACKET.json.
- CURRENT records from eCFR bulk and the U.S. Code zip are custody_record_only and fail the selected-source check, so the brief's "held CURRENT: record" route is unavailable for these orders.
- A correction of any clause's inventory requires override rows for every clause of that order (batch.py), which is why EO 13687 and EO 13722 carry 23 and 36 override rows.
- `first_cause` in ASSESSMENT.jsonl is left empty for in-force orders because none of the enumerated values describes an order with no cessation; blocked orders with a real unresolved cause are not applicable either.
- The packet's DISPATCH_CHECK marked all nine dispatchable; the unsealed HELD_SUPPLEMENT is what makes three orders unciteable.
