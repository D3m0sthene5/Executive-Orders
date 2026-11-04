# k01 producer report

Start UTC 2026-11-04T04:45:18Z (first session; stopped for a packet refresh and resumed on the re-prepared packet). End UTC 2026-11-04T05:30:39Z.
Final applied directory: applied-v3 (applied-v1 had 6 rejected claims from my own sheet error, applied-v2 assembled cleanly but drew 3 Geddes flags; both kept).

## Outcome: 16 submitted, 6 blocked

All 18 provisional-NO orders that rest on EO 14148 (2025-01-20, 90 FR 8237, FR 2025-01-28) were checked against the held official text of EO 14148. Section 2 revokes each order by number with no effective date other than signing, so the first end is 2025-01-20, mechanism express whole-order revocation. Section 3(b) of EO 14148 is the savings source (state transferred_or_accrued; no specific surviving action identified from held sources). Official Federal Register text layers are held for every order and every cited later instrument. Search ids used: current-law:usc, current-law:ecfr, later-events:ofr_catalog (all marked complete). original_confirmed true; original_pages_confirmed false (no page images inspected). No held text reinstates any of these orders.

Submitted:
- 13988, 13992, 13993, 14003, 14004, 14010, 14012, 14013, 14021, 14037, 14075: ended 2025-01-20 by EO 14148. Same-day instruments (EO 14168 supersession of conflicting provisions, EO 14154 sec 4(a), EO 14159 sec 3(a), EO 14163, EO 14171 sec 6) are in source notes as concurrent non-earlier ends. EO 14183 sec 5(a) and EO 14029 are recitals, not ends.
- 13992 and 14096: dossier inventory was incomplete or whole-order; replaced by span overrides (13992: lead, sec 1 to 4(c); 14096: sections 1 to 11).
- Clauses that revoke or amend earlier instruments in the present tense are recorded as exhausted by performance on the order's own date (14003 sec 2, 3(b), 3(c), 3(d); 14004 sec 2; 13992 sec 2; 14013 sec 2, 2(b); 14082 sec 4; 14096 sec 7). The EO 14148 revocation is not their first end.
- 14045, 14050: Commission sec 3(f) two-year term. EO 14048 (2021-09-30) and EO 14109 (2023-09-29) continue the Commission to 2025-09-30, so no earlier own-terms end; both recorded as later events on sec 3(f). 5 USC 1013 is held but unneeded.
- 14052: EO 14082 sec 4(c) strike-and-insert amendment recorded as a later event on sec 3(d), 3(d)(xi), 3(d)(xii) (owner ruling 2021-10-21).
- 14082, 14096: EO 14173 (2025-01-21) revokes EO 12898, which these orders amend; it does not name them, so it is a disclosed non-end (unnamed-instruments ruling). EO 14126 is a policy recital.

Blocked (precise gap):
- 13995: Task Force sec 2(f) ends within 30 days of accomplishing its objectives or 2 years from 2021-01-21, whichever is first, unless extended. Missing: held record dating the Task Force report or disbandment and any extension.
- 14011: Task Force sec 5(e) ends 30 days after its final report. Missing: record dating the final report.
- 14023: Commission sec 5 ends 30 days after its report. Missing: record dating the report submission.
- 14027: CCSO sec 1(e) ends at the maximum period under 5 USC 3161(a)(1). Missing: text of 5 USC 3161 and a record of CCSO establishment or termination.
- 14074: sec 19(b) interim accreditation command ends when standards are developed. Missing: DOJ record dating the standards. (EO 14110 cites 14074 only as cross-reference.)
- 14110: interim clauses 4.2(b), 4.2(c)(iii), 10.1(a) have contingent own-terms ends; inventory also stops at character 116273 of 146939. Missing: Commerce, cyber determination and Chief AI Officer trigger records.

## What took the time (one line per order)
- 13988, 13993, 14010, 14012, 14021, 14037, 14075: straightforward 14148 revocation; chain and same-day instrument review.
- 13992: inventory correction (clauses stopped mid sec 2).
- 14003, 14004, 14013: separating self-executing revocation clauses from mixed command clauses; 14004 conflict codes.
- 14045, 14050: tracing continuation orders 14048 and 14109 for the sec 3(f) term.
- 14052: strike-and-insert later event on three clauses.
- 14082, 14096: self-executing amendment clauses, EO 14173 and EO 12898 savings, Geddes flags; 14096 inventory correction.
- 13995, 14011, 14023, 14027, 14074, 14110: reading own-terms ends and finding no held dating source; 14110 inventory gap.

## Batch-check (applied-v3)
packet_members 22; claims_checked 16; strict_claim_pass 16; strict_claim_fail 0; blocked 6. Actual checker: claims_gate_passed 16, claims_mechanical_pass 0, claims_mechanical_unverified 16, claims_mechanical_fail 0 (all unverified items are "custody_record_only" source holds, not failures). batch-check exit code 1 because of the unverified items.

## Geddes
applied-v2: 3 flags (unaddressed_citing_instrument: EO 14126 on 14082; EO 14173 on 14082 and 14096). Fixed in applied-v3 by naming them in the rationale and savings text. applied-v3: 16 claims, 0 flags, 0 coverage gaps. No GEDDES_RESOLUTIONS.json needed.

## Full-packet files opened beyond views
LOOKUPS.md (head, on first pass), original decisions.csv and clauses.csv (heads and field layout), PACKET.json via load_packet(check_sources=False). The first session's work was on the earlier packet; its notes are in ../DRAFT_NOTES.md.

## Tool defects and observations
- The packet's bounded name search missed bare-number citations (for example EO 14168 naming "14075 of June 15, 2022"); I ran a broad regex scan of held texts instead and found no reinstating instrument.
- Chain events for 14074 and 14110 ("transfer", "amend") are cross-references, not amendments.
- Exhausted-by-performance clauses need end_id set to the original-source evidence id; a clause-scope id fails the first_end gate (applied-v1 rejections).
- A first apply on the earlier packet was left in that packet before the refresh; sheets in the re-prepared packet were regenerated from a generator under /tmp/claude-0/tribonian-work/k01/.
