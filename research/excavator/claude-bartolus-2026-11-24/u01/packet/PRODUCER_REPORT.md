# Producer report: u01 (undecided route), producer bartolus

Start UTC 2026-11-25T00:55:52Z. End UTC 2026-11-25T01:13:20Z (apply and batch-check ran after the last sheet edit; final applied directory applied-v1).

## Result
Submitted 5 (all status no, held as awaiting_status_review): EO:12437, EO:11943, EO:12701, EO:11294, EO:9155. Blocked 16 assigned members. 9 dispatch-blocked members were left as prepared (outcome unresolved) with assessment rows only. ASSESSMENT.jsonl has 30 rows.

## Outcome per order and why
Submitted
- EO:12437: one-sentence self-executing revocation of EO 12217, spent on issue 1983-08-11 (OWN_TEXT basis). 42 U.S.C. 8373 note confirms the revocation.
- EO:11943: one-time typographical correction in Schedule 3 of EO 11941, spent on issue 1976-10-25. The Federal Register note "Superseded by: EO 12010" is reconciled: EO 12010 Sec. 4 supersedes only EO 11941 (parent consequence, savings source PARENT_END), 5 U.S.C. 5332 note agrees.
- EO:12701: strike-and-insert amendment of EO 12334 sec. 1, spent on issue 1990-02-14; EO 12863 Sec. 3.3 revokes the parent "as amended" and does not name EO 12701.
- EO:11294: four clauses. Secs. 1, 3, 4 spent on issue 1966-08-04 (end source ORIGINAL record; no OWN_TEXT exists for this mixed order); Sec. 3 also superseded by EO 11609 Sec. 11(5) (1971-07-22, immediate under its Sec. 12); Sec. 2 delegation to the Secretary of State ended 1986-07-01 by EO 12561 Sec. 3, which also re-delegates under the 1985 Act and revokes paragraph (o). Open point stated in the sheet: 5 U.S.C. 5702/5707 and Pub. L. 99-234 text is not held, so an earlier statutory lapse is not excluded by statute text.
- EO:9155: eleven clauses; items 1 to 6 (and 3(a) to 3(e)) superseded by EO 9252 item 8, effective immediately, signed 1942-10-09; item 7 (effective date July 1, 1942) performed 1942-07-01. Whole end 1942-10-09.

Blocked (exact missing source)
- EO:10755: no held source on termination of the permits and rights-of-way the transfer preserves; frozen whole-order span includes unrelated contents pages (non-contiguous 23 FR 1191/1193).
- EO:12340: EO 12473 (rescinds the 1969 Manual as amended by 12340, effective 1984-08-01) is held but is not an evidence record in the frozen dossier; no OWN_TEXT record.
- EO:12753: EO 12791 (supersedes 12753; first end 1992-03-09) is held only as requires_page_check Federal Register text and APP mirror; trial assembly failed the working-text check. Draft kept at /home/claude/bartolus-scr/work/u01/o_12753_submit_draft.py.txt.
- EO:13649, EO:14101: no held current predicate through 2026-10-14 (only a U.S. Code note printing the text); 29 and 35 clauses not individually dated.
- EO:14274: no CURRENT record; Sec. 2(c) performance not shown.
- EO:1538: original needs page check; surviving reserved lands after EOs 1598, 1621, 1782 not shown.
- EO:1956: original only a ProQuest replica. Reading: revoked by PLO 3542 (30 FR 2215, signed 1965-02-11, lands open 1965-03-19).
- EO:2898, EO:4145, EO:4193: original only a ProQuest replica; no held later instrument naming them (4145: fixed ten-year extension ran out by 1935 by own terms).
- EO:7841, EO:8678: land orders with no held later disposition; 8678 inventory is an unverified segmentation lead.
- EO:944: one-time waiver for three named employees; no held source shows its use or end.
- EO:9482: wartime mine possession; no held source on termination under item 5 or statute expiry.
- EO:9729: delegation ended with the Office of Defense Transportation (EO 10065, effective 1949-07-01) but ends of clauses 2 and 4 (War Shipping Administration, Civilian Production Administration) are not held.

Dispatch-blocked (assessment rows from views only): EO:12280, 13474, 4475, 4621, 4657, 4788, 4861, 4968, 8870.

## What took the time (one line each)
12437, 11943, 12701: reading the short text and reconciling the parent-end notes. 11294: clause-by-clause reading of EOs 11609, 12561 and the earlier-end question for Sec. 2. 9155: reading eleven items and the EO 9252 effective wording. 12753: drafting a full submission, then the working-text failure. 12340, 9729, 9482, 13649, 14101, 14274: triage of what is held, then precise blocks. The six ProQuest or compilation-only orders: one cruden search each.

## Checks
apply (applied-v1): blocked 16, unresolved 9, awaiting_status_review 5. batch-check: 30 members, 0 claims checked (undecided members produce no claim at apply), actionable_failures none. Scratch validation (work/u01/val.py) assembled each of the five submitted sheets as if its status were set: assemble passed with no errors and status decisions had no _decision_errors.

## Geddes
Lint run on applied-v1: 0 claims checked, 0 defect flags, 0 coverage gaps. No GEDDES_RESOLUTIONS.json needed.

## Full-packet files opened beyond the views
READ.md (first 6000 bytes only), LOOKUPS.details.json (the EO:12437 member entry only), own packet undecided/EO_N/EVIDENCE.json and STATUS_DECISION.json. No PACKET.json.

## Tool defects and notes
- apply never assembles undecided lifecycle sheets, so batch-check cannot test them; a scratch validator was needed.
- A CLAUSES evidence record has no actor_id, so it cannot be a first_end source; spent amendment clauses in mixed orders had to cite the ORIGINAL record (quote is the whole order).
- Later-order sources flagged requires_page_check fail the working-text check even when they are Federal Register texts.
- EO 11609 machine candidate date 1971-10-20 applies the 90-day delay to all of Sec. 11; Sec. 12 limits it to paragraphs (1) to (13) and (19) of section 1.
- The Federal Register note for EO 11294 reads EO 10960 where the held text of Sec. 4 reads EO 10970.
