# Producer report, batch g04

Start UTC: 2026-10-31T22:13:55Z
End UTC: 2026-11-01T03:37:19Z (wall time includes a usage-limit pause)
Final applied directory: applied-v3 (applied-v1 and applied-v2 kept, never overwritten)
Agent column: claude. All 24 orders remain provisional status "no"; nothing about them was written outside this packet.

## Counts

- Packet members 24: submitted 22 (assembled_proposal), blocked 2 (EO 10177, EO 10291), rejected 0 in applied-v3.
- applied-v1: 21 assembled, 2 blocked, 1 rejected (EO 10346, working-text policy). applied-v2: same, EO 10346 still rejected (a second working-text source). applied-v3: 22 assembled, 2 blocked.
- batch-check on applied-v3: claims_checked 22, strict_claim_pass 22, strict_claim_fail 0, actual claim checker gate passed 22, all checks passed 21, mechanical unverified 1 (EO 10346), network off, independent human certifications 0.

## Outcome per order and why

Eighteen board orders plus 10080 and 10103 end on 1986-02-25 by express revocation by number in the table of Executive Order 12553 (actor EO 12553; dated on signing because 12553 has no separate effective-date wording; disclosed). The Executive Order 12553 report-deadline rule was applied: a board's report date is not an end; only the express revocation ends it.

- 10080 submitted: ended by EO 12553. Savings: transferred_or_accrued.
- 10103 submitted: three clauses, ended by EO 12553. Amendments by EO 10804 (1959-02-12), EO 11138 (1964-01-07) and EO 11303 (1966-09-12) recorded as later events, not ends. Savings: transferred_or_accrued.
- 10106, 10112, 10114, 10117, 10130, 10138, 10139, 10140, 10147, 10165, 10203, 10283, 10285, 10314 submitted: one clause each, ended by EO 12553 on 1986-02-25; savings none_after_bounded_search. For 10138/10139 the cross-citations are co-printing on one Federal Register page, for 10285 the EO 10155 and 10287 leads are a recital and an index listing; none ends the order.
- 10120, 10142, 10319 submitted: same ending; the dossier locator missed the table row so the ACTOR_TEXT record for EO 12553 is the cited source. 10142, 10303 and 10319 inventories corrected by absolute spans (neighbouring Federal Register items had been counted as clauses).
- 10303 submitted: ended by EO 12553; inventory corrected.
- 10222 submitted: three clauses, ended 1994-06-03 by EO 12919 (express revocation by number; effective on signing, disclosed). U.S. Code note agrees. Savings: transferred_or_accrued.
- 10346 submitted: three sections (the dossier listed eight, mostly a lemon-marketing regulation printed on the same page; corrected by spans). Ended 1969-10-28 by section 3015 item (4) of EO 11490. EO 10438 (1953-03-13), EO 10773 (1958-07-01) and EO 11051 section 603(b) (1962-09-27) are later events (amendments). Ending source is the American Presidency Project transcription of EO 11490, a registered working text, with identity, completeness and page confirmations; the govinfo OCR of the same section (held as an unregistered lead) agrees on item (4). Mechanical checker reports the five first-end/savings/whole-end source checks as unverified (custody_record_only: the byte file behind the transcription is not held); the claim gate passed and the claim is effective_for_tracker. This is inherent to a transcription working text and needs the official page when it is retrieved.
- 10177 blocked: EO 11012 section 3 (1962-03-27) revokes it effective on the date the initial Bureau of the Budget and General Services Administration regulations become effective. Those regulations are not held, so no exact first-end date can be quoted. Missing source: the Bureau of the Budget and General Services Administration issuances implementing EO 11012.
- 10291 blocked: only lead is the OFR catalog note "Revoked by: Federal Aviation Agency regulations of April 10, 1963 (Airspace Docket No. 62-W-141) (28 FR 3483)". The rule at 28 FR 3483 is not held, so whether and when it revoked the reservation cannot be quoted. Missing source: Federal Register 1963-04-10 page 3483.

## What took the time (one line per order)

- 10080: tracing the 10080/10103 chain and the EO 12553 table row to a clean ACT record.
- 10103: three clauses and three amendments (10804, 11138, 11303) each needing held text to place as later events.
- 10106: routine board pattern; confirmed the table row and inventory.
- 10112: routine board pattern.
- 10114: routine board pattern.
- 10117: routine board pattern.
- 10120: locator missed the table row; switched to ACTOR_TEXT.
- 10130: routine board pattern.
- 10138: ruling out the 10139 cross-citation as co-printing, not an end.
- 10139: same page-adjacency check as 10138.
- 10140: routine board pattern.
- 10142: locator miss and polluted inventory corrected by spans.
- 10147: routine board pattern.
- 10165: routine board pattern.
- 10177: reading EO 11012 and searching for the Bureau of the Budget and General Services Administration regulations; not held, blocked.
- 10203: routine board pattern.
- 10222: separate end by EO 12919, the 1989 codification lead sha gap, three clauses.
- 10283: routine board pattern.
- 10285: resolving the EO 10155 and 10287 leads (recital and index listing).
- 10291: searching for the Federal Aviation Agency rule; not held, blocked.
- 10303: polluted inventory corrected, same lead check as 10285.
- 10314: routine board pattern.
- 10319: locator miss and polluted inventory corrected.
- 10346: most of the time: corrected eight-clause inventory to three, four missing leads (10438, 10529, 10773, 10782), ACT record pointing at the wrong provision, then two rejected applies on the working-text policy before a registered source and an official-text later event were found.

## Tool defects and observations

1. EO 10346 ACT record for pair 10346/EO 11490 (main record) points to section 501, not the revoking section 3015; the revoking provision is only in alternative records.
2. Working-text policy: the govinfo tail text (held_text_lead, jobs/family-rule-tail) is not registered in any FRAGMENTS file, so it cannot be used as a source even though it is the best text. The error messages (grade_and_false_flag_required, fragment_identity_or_grade_mismatch, membership mismatch, official_copy_available) do not say which cited source is at fault; the real cause of the second rejection was a later-event source (EO 11051 ACT record on an APP mirror) that became a dependent working-text source. Naming the offending source in the error would have saved two applies.
3. APP transcription ACT records have very long spans (about 102k characters for EO 11490), which become the quote for the end source.
4. Locator misses for 10120, 10142, 10319 (EO 12553 table row not located); dossier clause inventories polluted by neighbouring Federal Register items for 10303, 10319 and 10346 (and 10142).
5. Running apply twice at overlapping times (a retry after a slow first run) produced "File exists: applied-v1" for the second; the first output file stayed empty. No data harm.
6. No "changed Valla review context" refusal occurred.
