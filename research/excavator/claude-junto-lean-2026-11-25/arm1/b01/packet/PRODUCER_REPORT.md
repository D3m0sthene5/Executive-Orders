# Producer report: arm1 b01 (agent junto-arm1)

Start 2026-11-25T08:55:12Z. End 2026-11-25T09:10:01Z. Final applied directory: `applied-v3` (applied-v1 failed selected-source custody because `CURRENT:` records are custody_record_only; applied-v2 passed but its wording on search coverage was tightened in v3).

## Outcomes

| Order | Outcome | Reason / exact missing source |
|---|---|---|
| EO:11177 | blocked | Original is requires_page_check (29 FR 13097-13098); PDF bytes not held (not in jobs/fr-pages/output/captures), no montfaucon pass, so original_pages_confirmed cannot be set truthfully. Also no held source on the Columbia River Treaty's status on 2026-10-14 (no CURRENT: record; the only U.S. Code hit is the EO 12038 text). EO 12038 section 3(b) (effective 1977-10-01 by its section 6) amends sections 101, 103 and 201; no revocation found. |
| EO:11203 | submit (yes) | 13 clauses all operative. EO 12107 section 2-101 (effective 1979-01-01 under section 2-404) recorded as an amendment on 1(3), 1(4) and 5. Basis: own held text plus the three bounded searches. |
| EO:11515 | blocked | Held evidence shows it was not in force on 2026-10-14: sections 1 to 5 terminate bodies, revoke orders and amend EO 11382 and EO 9586 by their own terms on signing, 1970-03-13; section 6 winding up has no continuing evidence. Do not file a YES claim; the ledger YES looks wrong and needs a separate owner route (a NO claim would need held sources for the revocations of EO 10898, 10986, 11117, 11152 and the EO 9586 amendment). |
| EO:11589 | blocked | Section 1(b) and section 2 rest on the Federal Civil Defense Act of 1950, which the U.S. Code extract says was repealed by Pub. L. 103-337 section 3412(a); that statute text (date, scope) is not held. Section 1(a) (5 U.S.C. 3376) looks in force; EO 12107 amended it (OPM for CSC); EO 12148 section 4-103(b) excludes the 1(b) function from its delegation but has no located provision. |
| EO:11845 | blocked | Original is requires_page_check (40 FR 13299); page images not held. Substance otherwise supportable (2 U.S.C. 685(b), (d), (e) held; EO 12608 section 25 technical amendment). |
| EO:11932 | blocked | Section 3(a) (regulations within 60 days) was performed by 22 CFR part 9a (42 FR 46516, Sept. 16, 1977), but that text is not an evidence record in the packet, so a terminated clause cannot be assembled without a source supplement; effect of EO 11652's revocation on sections 1 and 2 is not shown by a held later-event source; section 3(b) OCR is scrambled. |
| EO:12043 | blocked | Sections 3 and 4 amended Civil Service Rule IX (5 CFR 9.6(c), 9.20(f)); no held source shows Rule IX's later fate (EO 12107 text has no Rule IX provision). Sections 1 and 2 persist as 5 CFR 6.1(c) and 6.6 but those CFR texts are not evidence records and no CURRENT: record exists. |
| EO:12235 | submit (yes) | 4 clauses operative. No later instrument found. Basis: own held text plus the three bounded searches. The authority text for 15 U.S.C. 717z, 3361-3363 is not held; the claim says so and does not rely on it. |

Submitted 2, blocked 6. One order (EO:11515) is blocked because held evidence shows it was not in force at the cutoff.

## What took the time (one line each)

- 11177: reading EO 12038 amendment records, then finding the page-check and treaty gaps.
- 11203: reading EO 12107 section 2-101 and 2-404 and the CURRENT note, building 13 clause reasons.
- 11515: read text; each section is self-executing, so a block rather than research.
- 11589: tracing 42 U.S.C. 5195 notes to the Pub. L. 103-337 repeal and EO 12148 4-103(b).
- 11845: confirming 2 U.S.C. 685 and EO 12608 section 25, then the page-check gap.
- 11932: reading 22 CFR part 9a and the EO 11652 dependency.
- 12043: searching for Rule IX / 5 CFR part 9 sources (none held).
- 12235: confirming 15 U.S.C. 3364(d) and the lack of later instruments.

## Batch-check (applied-v3)

claims_checked 2; strict_claim_pass 2; strict_claim_fail 0; actual claim checker all checks passed 2; actionable_failures none; outcomes: 2 assembled, 6 blocked. applied-v1 selected-source check failed (13 and 4 clause predicates citing `CURRENT:` records that are custody_record_only); fixed in v2 by citing the held original as the current basis, with the U.S. Code note kept as a lead.

## Geddes

defect_flags 0; coverage gaps 4 (citing corpus incomplete: 52,269 of 66,744 tracked files verified; EO:12235 own_order_body_unverified / order_heading_unresolved). No flags, so GEDDES_RESOLUTIONS.json has no entries. The claims state that absence of a citation is not shown corpus-wide.

## Full-packet files opened beyond the views

None of READ.md, PACKET.json (used only through batch.load_packet in a scratch script to dump dossiers to /home/claude/junto-scr/work/arm1/b01/dossiers), LOOKUPS.details.json (one grep). decisions.csv, clauses.csv, ADMISSION.json, DISPATCH_CHECK.json (head only) and LOOKUPS.md were read.

## Tool defects and notes

- kit.py apply printed a dispatch-check style custody blocker block to the console even on exit 0; the information is in SELECTED_SOURCE_CHECK.json.
- `first_cause` for in-force orders in ASSESSMENT.jsonl is "unresolved" (no first end found); the schema offers no "none" value.
- The 11203 later-event source for EO 12107 is the whole 27,006-character actor text (no ACT provision located), so the claim is about 146 KB.
