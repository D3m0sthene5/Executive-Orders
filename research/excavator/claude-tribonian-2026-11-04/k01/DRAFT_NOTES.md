# k01 draft notes (producer, stopped before batch-check)

Start UTC 2026-11-04T04:45:18Z. Stopped on coordinator instruction. No claim filed.
Before the stop I had overwritten packet/decisions.csv and packet/clauses.csv with my sheets and run `kit.py apply` once (packet/applied-v1, result not inspected). Originals are saved in the producer scratchpad (k01w/decisions.orig.csv, clauses.orig.csv) and the generator is k01w/gen.py, so the work can be regenerated against a fresh packet.

## Common finding (all 18 EO 14148 orders)
EO 14148 of 2025-01-20 (90 FR 8237, FR 2025-01-28) sec 2 revokes the order by number. It states no later effective date, so the first end is 2025-01-20 (signing). Sec 3(b) (review and rescission of actions taken under listed orders) is the savings source: state transferred_or_accrued, no specific surviving action identified. Official FR texts (jobs/fr-originals/data/full_run/texts/EO_N.txt) are held for each order and for 14148. Evidence ids used: ACT:EO:N>EO:14148 (end), ACTOR_TEXT:EO:14148 (savings), search ids current-law:usc, current-law:ecfr, later-events:ofr_catalog (all complete). original_confirmed true, original_pages_confirmed false (text layer only, no page images inspected).
No held text restores any of these orders. The held OFR 2025 disposition listing (source-ladder EO_14315 capture) shows only 14003 "Reinstates EO 13957" (that is 14171 reinstating 13957, not 14003).

## Per order
Submit (revocation by 14148 sec 2 letter; later instruments to record as source notes):
- 13988 (d): EO 14168 same-day supersession of conflicting provisions only.
- 13992 (g): EO 14154 sec 4(a) same-day. Inventory incomplete (clauses stop mid sec 2). Correct with overrides: lead 723-859, sec1 861-1525, sec2 1527-2302, sec3 2304-3409, sec4 3411-3885, sec4-c 4156-4432. Sec 2 revokes EO 13771, 13777, 13875, 13891, 13892, 13893 in the present tense, so it was exhausted on 2021-01-20.
- 13993 (h): EO 14159 sec 3(a) same-day revocation.
- 14003 (o): EO 14171 sec 6 same-day revocation. EO 14029 only recites that 14003 revoked 13957. Pure self-executing revocation clauses (exhausted on 2021-01-22): sec2, sec3-b, sec3-c, sec3-d. Sec3 is mixed (also a withdrawal command) and ends 2025-01-20.
- 14004 (p): EO 14168 same-day. EO 14183 sec 5(a) of 2025-01-27 only recites the revocation. Conflict codes need resolution. Sec2 (revokes 2018 memo) exhausted on 2021-01-25.
- 14010 (u), 14012 (w): EO 14159 sec 3(a) same-day. Sec 6 of 14012 is mixed (revocation plus review command), so it ends 2025-01-20.
- 14013 (x): EO 14163 and EO 14154 same-day. Sec2 and sec2-b exhausted on 2021-02-04. Sec2-c (90-day report) is not exhausted.
- 14021 (cc): EO 14168 same-day.
- 14037 (kk): EO 14154 same-day.
- 14045 (mm) and 14050 (oo): Commission sec 3(f) says terminate 2 years from the order unless extended. EO 14048 (2021-09-30) continues the 14045 Commission to 2023-09-30 and EO 14109 (2023-09-29) continues both Commissions to 2025-09-30, so there is no earlier own-terms end. Record these as later events on sec3-f only. 5 USC 1013 is held (source-ladder opus-refetch uscode_5_1013). 14050 was extended before its 2023-10-19 date.
- 14052 (pp): EO 14082 sec 4(c) amends sec 3(d) (strike-and-insert). Later events on sec3-d, sec3-x-xi, sec3-x-xii, dated 2022-09-12.
- 14075 (ww): EO 14168 same-day.
- 14082 (xx): EO 14154 same-day. All of sec 4 (amendments to 14008, 12898 and 14052) is self-executing, exhausted 2022-09-12. EO 14096 only restates 12898 text, so it is not an end. 12898 is not listed in 14148 sec 2, which matters for savings.
- 14096 (eee): EO 14154 same-day. Inventory has one clause (whole), so correct to one clause per section 1-11 (starts 919, then each "Sec. N." heading, last ends before THE WHITE HOUSE). Sec 7 (amendments to EO 12898) is exhausted on 2023-04-21.

Blocked, with the missing source:
- 13995: Task Force sec 2(f) ends within 30 days of accomplishing its objectives or 2 years from 2021-01-21, whichever is first, unless extended. Need an official record dating the Task Force report or disbandment, and showing whether it was extended.
- 14011: Task Force sec 5(e) ends 30 days after its final report. Need a record dating the final report.
- 14023: Commission sec 5 ends 30 days after its report. Need a record dating the report submission.
- 14027: CCSO sec 1(e) ends at the maximum period under 5 USC 3161(a)(1). Need the text of 5 USC 3161 and a record of CCSO establishment or termination.
- 14074: sec 19(b) interim command ("pending the development of such standards") has a contingent own-terms end. Need a DOJ record dating the accreditation standards.
- 14110: three interim clauses (4.2(b), 4.2(c)(iii), 10.1(a)) with contingent own-terms ends. The inventory also stops at 116273 of 146939 and needs correction. Need Commerce, cyber and Chief AI Officer trigger records.

## Tool and packet observations
- The lookups' bounded name search missed bare-number citations (for example 14168 naming 14075 as "14075 of June 15, 2022"). A broad regex scan of held texts found no instrument that reinstates any order.
- The chain's "transfer" and "amend" events for 14110 and 14074 are cross-references, not amendments.
- Full-packet files opened beyond the views: PRODUCTION_ROUTE.md, BATCH.md, CLAIM_SCHEMA.md, the 6 rulings, the PRODUCER_BRIEF section, LOOKUPS.md (head), the original decisions.csv and clauses.csv (head), and PACKET.json via load_packet(check_sources=False).
