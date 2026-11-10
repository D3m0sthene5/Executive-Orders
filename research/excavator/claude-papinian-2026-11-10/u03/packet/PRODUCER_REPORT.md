# Producer report, u03 (undecided, status-overlay route), producer-u03

Start 2026-11-10T07:41:58Z; end 2026-11-10T08:17:23Z (see last line for the final stamp). Final applied directory: `applied-v1`.

## Outcome

Six members submitted as lifecycle sheets with a status proposal (all `no`): EO:9245, EO:10472, EO:10679, EO:10816, EO:10938, EO:11962. Apply reports them as `awaiting_status_review`, the expected state for an undecided member. Twenty-three members blocked (EO:10350 and EO:13204 are blocked for the lifecycle claim but carry a validated `no` STATUS_DECISION.json). EO:10603 is dispatch-blocked and left as prepared (outcome `unresolved`); only its assessment row was written. ASSESSMENT.jsonl has 30 rows.

Because the undecided route assembles no claim in `apply`, I dry-ran the six sheets in scratch with the proposed status patched into a copy of each frozen dossier, assembled them with the kit's assembler and ran the actual claim checker on the result (not written under the packet): 6 of 6 claims passed all checks. The status decisions of the eight members that carry one pass `status_overlay._decision_errors` (no errors).

## Per order

Submitted (all `no`):
- EO:9245: express repeal by EO 9616 paragraph 1, signed 1945-09-14 (10 FR 11837, official text, full order held). Time: reading the 14-paragraph successor order for savings.
- EO:10472: express revocation by EO 11256 section 7, 1965-11-04. Inventory corrected (scan columns misordered: section 1 and the first part of section 2 were outside the machine span). EO 10937 (1961 restatement of section 1) is disclosed but not cited because its Federal Register copy is held only as a custody record. Time: rebuilding the inventory from displaced OCR columns.
- EO:10679: express supersession by EO 10996 section 8, 1962-02-16. Inventory corrected (paragraph 1 was a 12,448-character clause swallowing a page break and contents pages). Savings continuing_independent (EO 10996 section 7 keeps State agreements). Time: splitting the page-break clause.
- EO:10816: supersession of the parent EO 10501 as amended by EO 10816, EO 11652 sections 14 and 15, effective 1972-06-01. Inventory corrected (paragraph 1 omitted); EO 10964 rewrote section 4 (later event on clause 1). Time: checking each later amender of EO 10501 for the touched sections.
- EO:10938: express revocation by EO 11460 section 6, 1969-03-20. U.S. Code note at 50 U.S.C. 3023 agrees. Time: short.
- EO:11962: termination and revocation by EO 12007 section 5, 1977-08-22, before the own-terms sunset of 1978-12-31. Inventory corrected (section 1(a) omitted). U.S. Code note at 22 U.S.C. 3107 agrees. Time: short.

Blocked, with the exact missing source (full text in decisions.csv):
- EO:10350: status `no` is supported (EO 10773 section 7(4), effective 1958-07-01) but the lifecycle claim cannot be assembled: sections 7 to 10 of EO 10773 are held only as an APP transcription, while an official FR copy ends before them (23 FR 5063 needed); the working-text policy rejects the transcription.
- EO:13204: status `no` supported (EO 13495 section 7, effective immediately, 2009-01-30). Section 2 (move promptly to rescind) has no cited performance date, so its first end is only bounded by 2009-01-30.
- EO:8266: no ending record; appropriation text for the fiscal-year 1940 and 1941 funds or a revocation of EO 6746 needed.
- EO:8511, 9124, 9390: land and jurisdiction transfers; later disposition or current land record needed.
- EO:8627: unit-by-unit induction, relief or extension instruments needed.
- EO:8649: only a partial revocation by PLO 5534; full PLO land description versus the three tracts needed.
- EO:8695: no CURRENT record (19 CFR 101.3 table cites E.O. 8695 as a lead only).
- EO:9211: EO 9471 excepts the EO 9211 property functions; Second War Powers Act Title II expiry or disposition needed.
- EO:9554: EO 10065 only designates the ICC to liquidate; termination of possession needed.
- EO:10565: instrument superseding the 1951 Manual for Courts-Martial needed.
- EO:10603: dispatch-blocked (mandatory sources custody-only); not researched.
- EO:10624, 13116, 13647, 14051, 14191: possible `yes` but no CURRENT record in the dossier (U.S. Code notes are leads only).
- EO:10828, 13013, 14231: no ending or current record.
- EO:11315: EO 12748 revoked Rule 9 only, held only as a transcription while an official copy exists; other parts unchecked.
- EO:12379: no dossier record ends EO 12379 itself (its ending-type records are its actions on other orders).
- EO:13064: EO 13138 section 3(c) revokes amended parent provisions of EO 13010, not EO 13064 by number; EO 13010 not held; partial.

## Batch-check

`apply`: blocked 23, awaiting_status_review 6, unresolved 1 (EO:10603, left as prepared). `batch-check`: 30 members, 0 claims checked (undecided members assemble no claim), 0 actionable failures; actual claim checker had no claims. Geddes lint of applied-v1: 0 flags, 0 claims, 0 coverage gaps; no GEDDES_RESOLUTIONS.json needed.

## Files opened beyond the views

LOOKUPS.md (per-order sections by script), undecided/EO_N/EVIDENCE.json (by script, all members), decisions.csv and clauses.csv, PACKET.json (loaded once by script via batch.load_packet, and copied to scratch for a dry Geddes lint). Repository sources: held order texts under jobs/fr-originals, jobs/app-executive-orders, jobs/selden-fr-acting, jobs/mabillon-held-printings, jobs/current-law output (MENTIONS.csv, USC_EO_NOTES.jsonl, ORDERS_CURRENT_LAW.csv, FRAGMENTS.jsonl).

## Tool defects

1. The undecided route's `apply` assembles no claim, so `batch-check` exercises nothing for submitted members; I used a scratch dry run.
2. working_text policy rejects a transcription later-event source whenever any official copy is held, even a truncated one (EO 10350).
3. The Federal Register PDF for EO 10937 (FR 1961-05-05, 43 MB) is custody_record_only, so a later event citing it fails.
4. Several machine clause inventories are wrong (EO 10472, 10679, 10816, 11962 and others), and the dossier's actor contexts include ids that are the order's own actions (EO 12379).

End 2026-11-10T08:17:23Z.

## Overlay follow-up (coordinator request)

For EO 9245, 10472, 10679, 10938 and 11962 LIFECYCLE_DECISION.json was inspected against my analysis, left unchanged and set approved true. For EO 10816 I changed the sheet: EO 10964 (26 FR 8932, signed 1961-09-20) deleted paragraph (i) of section 4 of EO 10501 (the paragraph clause 1 added) and restated paragraphs (c) and (d) of section 8 in full (replacing clause 3's text), so clauses 1 and 3 now end on 1961-09-20 (end source ACTOR_TEXT:EO:10964, mechanism express_replacement_of_text) and the earlier-end, scope and rationale texts were corrected; clause 2 still ends 1972-06-01 by EO 11652, which remains the whole-order end. All six sheets were set approved true; overlay-assemble and overlay-check passed for all six (0 failures). No command is left running.
