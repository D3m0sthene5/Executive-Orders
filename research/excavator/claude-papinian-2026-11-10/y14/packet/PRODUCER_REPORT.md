# Producer report y14 (papinian lane)

Start 2026-11-10T05:24:03Z. End 2026-11-10T05:56Z. Final applied directory: `applied-v3` (applied-v1 and applied-v2 were early trial applies; v1 assembled nothing because of a key bug in my generator, v2 assembled 2 claims and rejected EO 12883).

## Outcome per order (3 submitted, 19 blocked)

Submitted (YES, original_plus_bounded_search, all three claims passed the actual checker):
- EO:10488 submit. One-paragraph Treasury foreign-exchange order; 31 CFR 281.1 and part 281 authority (eCFR 2026-10-14) still cite it; no later instrument. Order refers to two appropriation-act sections only as limits; their current text is not held (stated in the claim).
- EO:12019 submit. Inventory corrected to five clauses (recital, sections 1-4); EO 13666 (held FR text) amends section 1; Code prints the order as amended at 10 U.S.C. ch. 57 note.
- EO:14085 submit. Inventory corrected to eight clauses; six amendments of earlier orders plus general provisions; Code prints each amended order as amended by EO 14085; the Code's editorial note that section 4(a) could not be executed (identical earlier amendment by EO 13286) is disclosed and the section 4 clause rests on paragraphs (b)-(d).

Blocked (exact missing source in each decisions.csv row and ASSESSMENT.jsonl):
- EO:10457 authority statute 35 U.S.C. 181 text not held (zero hits in all three searches; favors YES).
- EO:10950 Pub. L. 101-509 sec. 112(c) amendment (104 Stat. 1454) and Alaska Statehood Act sec. 6(b) selection-period text.
- EO:11203 EO 12107 amendment not located or citable in the packet.
- EO:11348 EO 14207 partial revocation (Federal Executive Institute provisions) and EO 12107/13111 provisions not located; 29 clauses unmapped.
- EO:11485 current text of 32 U.S.C. 110 and the D.C. Code provision not held (favors YES).
- EO:11582 5 U.S.C. 6103 amendment history needed to decide whether section 2(a)'s 1971 holiday list continues; sections 8 and 9 performed/dated.
- EO:12067 EO 12107 amendment not citable; Reorganization Plan No. 1 of 1978 not held.
- EO:12115 no held source for performance of the dated task clauses; the executed U.S.-Panama agreement not held.
- EO:12208 EO 13286 section 49 held only as APP mirror / clause-drafts copy.
- EO:12560 and EO:12738 no section-by-section map to parent orders (EO 13637 revoked EO 11958); mirror-only EO 12620/12738 texts; EO 12611 provision not located.
- EO:12883 original (58 FR 63281) is also registered by montfaucon FRAGMENTS_OFFICIAL as official_printing, acceptable_as_original false, no text_sha256, so apply rejects it as a working text; needs a page-image check or registered text with text_sha256. Substance favors YES.
- EO:12938, EO:13315, EO:13372, EO:13984 National Emergencies Act continuation notices not held (dossier lists them as absent from the census); amending orders not mapped to clauses. EO 13372 section 2 ended 2019-09-09 with EO 12947's revocation by EO 13886 (held), section 1 depends on the EO 13224 emergency.
- EO:13179 41 clauses not worked; EO 13699/13708/13811/13889/13899 provisions not located; EEOICPA text not held.
- EO:13265 section 6(b) two-year termination unless extended; extension orders after 2011 (EO 13316 ... 13585 and successors) not held.
- EO:8065 Public Land Order 1785 (24 FR 972, partial revocation 1959-02-03), EO 8319, EO 8479 and land descriptions not held.

No held evidence showed any assigned order was not in force on 2026-10-14; no order was blocked for that reason.

## What took the time (one line each)
10488 CFR hits and statute-reference reading; 12019 inventory correction and EO 13666 check; 14085 reading seven amending sections and the Code note on 4(a); 12883 original rejected by working-text policy after full drafting; 10457 and 11485 statute-text gap; 8065, 10950, 11203, 11348, 12067, 11582, 12115, 12208 each checked via current-law MENTIONS/EDGES and the order text to name the blocker; 12560, 12738, 12938, 13179, 13265, 13315, 13372, 13984 blocked after checking own-terms and later-event chains (13668, 13637, 13886 read).

## batch-check
applied-v3: packet members 22; outcomes assembled_proposal 3, blocked 19; claims checked 3, strict pass 3, fail 0; actual checker: all checks passed 3, mechanical fail 0, gate passed 3; actionable failures none; independent human certifications 0.

## Geddes
Lint on applied-v3: 0 defect flags; 7 coverage gaps (citing corpus incomplete 912 of 63,287 files; own-order body unverified for EO 12019; two unclassified mentions in EO 14085). GEDDES_RESOLUTIONS.json records them as advisory, no flag to resolve.

## Full-packet files opened beyond the views
LOOKUPS.md not opened. PACKET.json loaded once through batch.load_packet in a script (evidence ids and original spans only). Repository sources read: jobs/current-law/output MENTIONS.csv, EVENT_CANDIDATES.csv and USC_EO_NOTES.jsonl (by order); jobs/later-events/output/EDGES.csv (by order); held texts under jobs/fr-originals and jobs/app-executive-orders (EO 13666, 13415, 13668, 13637, 13106); jobs/claim-kit sources (assemble.py, batch.py, working_text.py) and one committed claim file (research/readiness/claims/claude-2026-11-05-icecore-yes.jsonl) as a format example.

## Tool defects / notes
- Apply reported nothing for the first run because my generator keyed rows by int; fixed (scratch only).
- The U.S. Code scan holds only executive-order notes, not statute text, so authority statutes cannot be checked from held bytes; this drove the 10457 and 11485 blocks.
- A first-run Geddes lint took about 6.5 minutes; its output file had trailing partial text from the tool and was rewritten as clean JSON.
