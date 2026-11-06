# Producer report: y03 yes-probe (dorotheus)

Start 2026-11-06T10:21:21Z; end: see last line.

## Outcomes
- EO:11600 submit (YES). One-paragraph seal approval; no own-terms end, no later instrument held, searches (usc, ecfr, ofr_catalog) no hits; original_plus_bounded_search route.
- EO:11961 submit (YES). Inventory corrected to sections 1-4 (dossier merged sec 3 into sec 2). Later events EO 12013 (eff. 1977-10-09), EO 12318 (eff. 1981-08-23), EO 12518 (1985-06-03) are amendments (strike-and-insert ruling); clauses continue. Official FR texts of all three held.
- EO:12028 blocked: no held source of performance/dates for one-time Sec. 1, 6, 7 commands; inventory wrong (Sec. 6 missing); partial transfer by EO 12134 of printing under Sec. 3(b)(5).
- EO:12046 blocked: 26-clause inventory with duplicate scopes, heading unresolved, many one-time Reorg Plan provisions, partial revocation by EO 12472; EO 13470/13764 contexts not read.
- EO:12146 blocked: Sec. 1-701(a) report deadline (1980-07-18) is not an end and performance is not shown; initial membership terms; inventory covers only fragments.
- EO:12163 blocked: 90 clauses, 198 later events, boundary conflict, unlocated provisions (EO 12356/12530/12884), acting identity absent.

## Time
11600: short single-clause order. 11961: inventory correction and tracing three amendments. 12028/12046/12146/12163: reading views and deciding the block; 12046 and 12163 views were very large (read only summaries).

## batch-check
applied-v1: 6 members; 2 assembled and 2/2 strict pass, actual checker 2/2 all checks passed; 4 blocked; actionable failures none.

## Geddes
0 flags, 0 coverage gaps (applied-v1/GEDDES_LINT.json). No resolutions needed.

## Files opened beyond views
Held texts jobs/fr-originals/data/full_run/texts/EO_{11961,12013,12318,12518,12028,12146(via view),12608,13286,11600}.txt (partial reads), LOOKUPS.md (head), LOOKUPS.details.json (keys only), PACKET.json via batch.load_packet (dossiers pickled in scratch). cruden.py searches for 11600 and Reorganization Plan No. 1 of 1977.

## Tool defects
None blocking. Note: ASSESSMENT first_cause left empty for operative orders (no enumerated value fits).
2026-11-06T10:29:47Z

## Attempt 2 (EO:12046, EO:12163)
Start 2026-11-06T10:35:18Z; end 2026-11-06T10:51Z. Final applied directory: applied-v7 (applied-v2 to v6 are earlier trial applies, kept, never overwritten; applied-v1 is attempt 1).

- EO:12046 submit (YES). Read the held official Federal Register text in full (43 FR 13349, signed March 27, effective March 26, 1978). Inventory corrected from 26 overlapping machine scopes to 25 paragraph-aligned scopes (offsets in the registered file). Sections 1-1 and 6-2 are self-executing and ended by performance on the order's own effective date (1978-03-26, per 6-304); 2-414, 4-102, 4-103, 4-202, 4-302, 5-3 and 6-101 ended by EO 12472 section 4(b)(1), effective on Federal Register publication, 1984-04-05 (section 5), not the signing date; 5-3 also carries EO 12148's amendment (effective 1979-07-15); 2-411 amended by EO 12472 (continues); 4-201 is recorded as continuing with EO 12472's supersession of the 1963 Memorandum disclosed as a later event, because no source shows it extinguished the transfer. Remaining sections operative, predicate through 2026-10-14 (47 U.S.C. 901(b)(6), 47 CFR 213.0, Code notes). EO 13470 and EO 13764 contexts read: neither (nor 12829, 13355, 13381, 13467, 13516, 13549, 13587, 13691) contains the number 12046; they are machine noise. EO 13618 (2012) revokes EO 12472 but does not name 12046; disclosed in the rationale, not a later event. Judgement call: sections 6-102 to 6-104 (transition commands) have no held performance source and no end, so they are recorded operative per the evidence ruling.
- EO:12163 blocked (precise gap). Boundary resolved: the order proper ends at 1-905 and the signature of September 29, 1979; the text after it in the dossier is EO 12164. EO 12356 does not cite 12163; EO 12530 sec. 6 only delegates subject to it; EO 12884 carves its delegations out of 1-102(a). The block is the first end of the IDCA-related provisions: the Code note to 22 U.S.C. 2381 says Pub. L. 105-277 div. G subdiv. A title XIV sec. 1422(a)(2) (Oct. 21, 1998) repealed 1-101 to 1-103, 1-401 to 1-403, 1-801(a) and other IDCA provisions without a date, and EO 13118 (effective April 1, 1999) rewrote Part 1-1 and revoked Part 1-4; the first end lies in an interval that held sources do not close. Missing source: text and effective date of secs. 1401 and 1422(a)(2); also FAA 122(e) and 640B statutory histories for the Development Loan and Coordination Committees (1-505, 1-506). Bound recorded in ASSESSMENT.jsonl.

Time: 12046 — reading the order, finding the revoking text and the checker's end-evidence rules (CLAUSES ids of corrected scopes are not accepted as end sources; ORIGINAL id used for the self-executing ends). 12163 — reading the order and later orders' contexts, then finding the Code note that shows the statutory repeal.

batch-check (applied-v7): 6 members, 3 assembled, strict 3/3, actual checker 3/3 all checks passed, 3 blocked, actionable failures none.
Geddes (applied-v7): 1 flag (event_precedes_order, EO:12046 s1-1, retroactive effective date 1978-03-26 vs signing 1978-03-27) disputed in applied-v7/GEDDES_RESOLUTIONS.json with the 6-304 reason; 2 coverage notes (own_order_body_unverified, citing_own_body_unverified) are not defects. Earlier flags (49 FR citation of the revoking order; EO 12472 named without a later event) were fixed in applied-v6/v7 by rewording.
Files opened beyond views: held texts jobs/fr-originals/data/full_run/texts/EO_{12046,12163,12148,12472}.txt and output/texts/EO_{13618,13118,12292,12321,12365,12423,12458,12530,12560,12608,12639,12680,12695,12738,12884,13030,13091,13346,13361,13656}.txt (citation contexts); jobs/theophilus-sources/output/texts/{usc-t47-s901,usc-t47-s701,cfr-t47-213.0,usc-t22-s2381}.txt; jobs/ofr-codification-1989/output/texts/EO_12046.txt (grep); PACKET.json via batch.load_packet (pickled in scratch); LOOKUPS.md lines 53-110.
Tool defects: kit.py apply refuses output outside the packet, so trial applies leave extra applied-vN folders. Edited only decisions.csv, clauses.csv (EO:12046 rows replaced; others untouched), ASSESSMENT.jsonl, PRODUCER_REPORT.md. RATIONALES.json untouched.
2026-11-06T10:51:00Z
