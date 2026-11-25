# Producer report: baldus, y04 (route YES, provisional)

Start 2026-11-25T15:37:59Z; end 2026-11-25T15:50:07Z (of which apply and batch-check took under 2 minutes).
Final applied directory: `applied-v2` (applied-v1 failed selected-source custody: the U.S. Code release-point zip is custody_record_only, so I switched the current basis to the held original text).

## Outcome per order

| Order | Outcome | Why |
|---|---|---|
| EO 11298 | submit (yes) | One clause; 10 U.S.C. 1035(b) held and unchanged in substance; 1989 codification editorial note (DOD Instruction 1348.15, terminal date 1973-03-28) tested and explained; the earlier review rejection on that note is addressed. |
| EO 11311 | blocked | Clause 1 (TSUS entries from 1967-01-01) needs the statute replacing the TSUS with the HTSUS and HTSUS 9817.00.40 text; clause 2 (USIA designation) needs 22 U.S.C. 6531, 6532, 6551 text (only a cross-reference in the 19 U.S.C. 2051 note is held). |
| EO 11348 | blocked | EO 14207 section 2(b) revokes unnamed "applicable provisions" of EO 11348 (Federal Executive Institute); no held source says which clauses. Inventory also has two non-clause fragments (sec202-a-dup2, sec402-6). |
| EO 11438 | submit (yes) | Inventory corrected to four section clauses (absolute spans 861-1527, 1527-2479, 2479-2729, 2729-3552); later events EO 12107 (effective 1979-01-01, CSC to OPM, section 4) and EO 13286 section 63 (effective 2003-03-01). |
| EO 11446 | submit (yes) | One clause; later event EO 13286 section 62 (effective 2003-03-01). |
| EO 11471 | blocked | 28 CFR 0.49(b) (2025) gives Justice the Central Authority functions section 1 gave State; the dated modifying instrument (section 3 allows modification) and 0.49 amendment history are not held. Operative force unknown. |
| EO 11485 | submit (yes) | Sections 1-4 operative on the established original-plus-bounded-search route; section 5 (supersedes EO 10030) terminated 1969-10-01 by performance (signing date; publication date is the stated alternative). |
| EO 11491 | blocked | 22 sections / 40 clauses against 5 U.S.C. chapter 71 (effective 1979-01-11); only 7101, 7103, 7135 held. Held evidence does not show the order in force clause by clause on 2026-10-14. Ledger YES not supported by held evidence; the ledger is unchanged. |
| EO 11521 | blocked | Section 1(a) GS-5 / Vietnam-era / 14-year terms conflict with current 5 CFR 307.102-307.103 (GS-11, covered veterans); no dated source shows which instrument displaced each of 21 clauses. |

Submitted 4, blocked 5.

## What took the time (one line each)
- 11298: finding and answering the 1973 editorial note, the reason an earlier claim was rejected.
- 11311: tracing item 1 (TSUS) and item 2 (USIA) to find the missing statutes.
- 11348: reading EO 12107 and EO 14207 and failing to map "applicable provisions" to clauses.
- 11438: correcting the merged inventory and the mislabelled EO 12977 actor.
- 11446: same mislabelled EO 12977 entry; EO 13286 effective date.
- 11471: reading 28 CFR 0.49 against section 1.
- 11485: deciding section 5 as performed and the report-duty term leads.
- 11491: confirming the held statute coverage was too thin.
- 11521: comparing the order with current part 307.

## Checks
- batch-check (applied-v2): 4 claims checked, 4 strict pass, 0 fail; actual checker 4 of 4 all checks passed; actionable failures none.
- Geddes: 0 defect flags; 8 coverage gaps (own_order_body_unverified, citing_corpus_incomplete, citing_own_body_unverified); `GEDDES_RESOLUTIONS.json` holds an empty resolutions list.

## Full-packet files opened beyond the views
- LOOKUPS.md (read in full), clauses.csv and decisions.csv (edited), PACKET.json (loaded in scripts to read evidence records, conflicts and shared objects for 11298, 11438, 11446, 11485), LOOKUPS.details.json (keys only). No READ.md.

## Tool and packet defects
- The packet's chain and prefilled working_text list EO 12977 (1995) as an actor for EO 11438 and EO 11446. The cited queue file is a copy of EO 13286 pages, and the held EO 12977 text does not contain either number. I did not treat it as a later event.
- The CURRENT: records built from the U.S. Code release-point zip are custody_record_only, so they fail selected-source custody; current-law notes cannot be a current basis until the zip bytes are held.
- The held extracts of the 5 U.S.C. 4103 (EO 11348) and 5 U.S.C. 7101 (EO 11491) notes contain only the heading and preamble.
- The ASSESSMENT first_cause field has no value for orders with no cessation; I left it blank for those.
