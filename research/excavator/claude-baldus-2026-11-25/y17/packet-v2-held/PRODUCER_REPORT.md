# Producer report, packet y17 (packet-v2-held), baldus

Start 2026-11-25T17:05:20Z (first attempt in y17/packet stopped at 17:18Z on "changed Valla review context"; resumed in packet-v2-held 17:21Z). End 2026-11-25T17:32:05Z.

## Outcome per order
Final applied directory: research/excavator/claude-baldus-2026-11-25/y17/packet-v2-held/applied-v8. Submitted 8 (all YES), blocked 1.

- EO:13857 submit YES. Dossier inventory was a truncated preamble slice; corrected to five clauses by override (preamble, section 1(a), 2(a), 2(b), 2(c)). Basis: Venezuela emergency continued by notice of 2026-02-18; OFAC action 2026-08-07 applies EO 13850 as amended by EO 13857.
- EO:13863 submit YES (6 clauses). Notice 2026-07-13; OFAC designation 2026-10-01 under EO 13581 as amended.
- EO:13876 submit YES (28 clauses). EO 12957 notice 2026-03-02; EO 14382 does not revoke or amend. Conflict lines were notice recitals about EO 13846 revoking EOs 13716 and 13628.
- EO:13882 submit YES (25 clauses). Mali notice 2026-07-21; the 2020-02-07 conflict is the OFAC regulations rule.
- EO:13883 BLOCKED. Missing: National Emergencies Act continuation notices for the EO 12938 weapons-of-mass-destruction emergency (annual since 2019, incl. the notice due before 2025-11-14). Rechecked against SOURCE_SUPPLEMENT.json: it adds the order's own FR page and the text of 22 U.S.C. 2797 and 5605, but no continuation notice. Sections 2 and 5 depend on the emergency. The dossier inventory is also only the heading line.
- EO:13886 submit YES (19 clauses). Lead (termination of the EO 12947 emergency and revocation of EO 12947) terminated by performance on 2019-09-10; 18 clauses operative (OFAC designations 2026-10-02 under EO 13224 as amended; notice 2026-09-11). The September 2019 continuation notice for EO 13224 is not held; disclosed in the claim.
- EO:13894 submit YES. Inventory corrected to 25 exact-span clauses (the dossier omitted the preamble declaration of emergency). Terminated: section 1(a)(i)(B)-(D) and section 8(f), struck by EO 14142 on 2025-01-15. Section 1(a), 1(a)(i)(A), 1(a)(i)(E)-(F), 2(a) and the lead are operative with later events (EO 14142, EO 14312, 2025-06-30). Notice 2026-09-30.
- EO:13902 submit YES. Inventory corrected to 23 exact-span clauses (dossier spans cut sentences and its boundary was unverified). EO 12957 notice 2026-03-02; OFAC sector determination 2026-10-01 (91 FR 64758).
- EO:13915 submit YES. Sections 1-3 operative; section 4 (revocation of EO 13244) terminated by performance 2020-04-14. The Vacancies Reform Act text is not held; disclosed.

## Method notes
- Federal Register continuation notices and OFAC notices (FRDOC records) cannot be a clause's current_predicate source: the assembler treats them as working-text-grade and rejects them. Every operative clause therefore cites the order's own held original as current_basis_id, with the notices, OFAC actions and bounded-search coverage described in current_legal_basis and the rationale. The supplement-added notices were used only in prose, never as the sole basis.
- The original text is a machine-extracted text layer; original_pages_confirmed rests on identity checks of heading, date and FR Doc. number, not on page images.
- No EO 14294 hit ends any order; it concerns regulatory criminal penalties.

## What took the time
All orders: reading continuation notices and later orders. EO 13894 (amendments by EO 14142 and 14312, override inventory) and EO 13902 (override inventory) took the most; EO 13882 and 13876 were mostly clause blurbs.

## Checks
batch-check: 9 members, 8 claims checked, strict pass 8, fail 0; actual claim checker 8/8 passed (mechanical pass 8, gate 8). Geddes lint: 0 defect flags, 11 coverage gaps (advisory), GEDDES_LINT.json written; GEDDES_RESOLUTIONS.json is empty because no flag exists.

## Full-packet files opened beyond the views
LOOKUPS.md (old packet), PACKET.json, LOOKUPS.details.json, HELD_SOURCES.json and HELD_SUPPLEMENT.json (old packet, in scripts); SOURCE_SUPPLEMENT.json and views (new packet).

## Tool defects
- First apply in y17/packet failed on "changed Valla review context" (resolved by the coordinator's re-prepare).
- LOOKUPS number-citation list truncated at 40 for EO 13857; remainder checked by direct search.
- No ledger change is proposed: every submitted order was in force on 2026-10-14 on held evidence.
