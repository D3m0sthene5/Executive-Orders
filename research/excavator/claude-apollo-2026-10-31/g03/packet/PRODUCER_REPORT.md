# Producer report, batch g03

Producer: claude (single context). Start 2026-10-31T22:13:55Z. End 2026-10-31T22:30:18Z (UTC).

Final applied directory: `research/excavator/claude-apollo-2026-10-31/g03/packet/applied-v2`. The earlier `applied-v1` is kept; it had one rejected member (EO 10010, see tool notes).

## Outcome per order

Submitted (20):

- Emergency-board orders ended by EO 12553 (signed 1986-02-25, effective on signing; lists each order by number; no saving clause; owner ruling 2026-10-21 report-deadline, option C: the thirty-day report deadline and the standstill are spent facts, not ends): EO 10010, 10029, 10050, 10051, 10056, 10067, 10071, 10078, 9918, 9923, 9929, 9936, 9940, 9948, 9991. Each is one clause, status no, first end 1986-02-25.
  - EO 9929: inventory corrected (the dossier clause began mid-order on the second page; the override spans the heading, recitals and board-creation sentence through the standstill sentence).
  - EO 10078, 9918, 9929, 9940, 9948, 9991 have no acting-provision record for EO 12553 in the packet, so the ending source cited is the full held text of EO 12553. Orders 9918, 9923, 9929, 9936 and 9940 are on the first table page, where the text layer separates the number column from the subject column; I matched number to subject by position and say so in the claim.
  - EO 10010: EO 10015 (amendment) is described in prose, not as a later event, because the only record of it in the dossier cites an APP transcription while an official copy is held, and the working-text policy rejected that in applied-v1.
  - No actual report date or standstill expiry is recorded as a later event for any board order: the packet holds no reviewed factual-event record for them (AGENT_PROTOCOL: unreviewed report candidates supply no citable factual event).
- EO 10015: three clauses (lead-in, add six carriers to List A, rename two List B organizations); all end 1986-02-25 by EO 12553, which lists it and also revokes amendments and EO 10010.
- EO 9949: one-person modification of EO 9721 paragraph 3(a) (Paul D. Miles); first end 1986-02-25 by EO 12553 (names it by number). EO 10415 (1952-12-02, strike-and-insert) recorded as a later event with before and after wording. Whether Miles transferred is not established; the claim says so and does not rely on exhaustion.
- EO 9787: first end 1947-09-23 by EO 9894 (discontinuance of the San Clemente Island Naval Defensive Sea Area; signing date, publication 1947-09-25 stated as the alternative). Ending source is the full held text of EO 9894 (no acting record in the packet).
- EO 9799: first end 1981-02-15 by EO 12292 section 10(b), effective as of that date under section 11 (signed 1981-02-23, alternative stated). The Foreign Service Act of 1980 (held, source-ladder) took effect the same day but section 2401(a) kept orders in force until revoked, so the revocation, not the repeal, is the end. The EO 9452 acting record in the dossier is a labeling artifact of the issue that prints EO 12292. The prior Astra gap about the 1980 Act is addressed.
- EO 9982: inventory corrected (the dossier clause was only the tail "1949." plus the effective-date sentence). First end 1948-10-22 by EO 10011 paragraph 3(b), earlier than the own-terms end of June 30, 1949 (inclusive; exclusive reading 1949-07-01), which is a source note. Savings: regulations continued by the proviso and powers re-delegated.

Blocked (4):

- EO 9815: EO 9830 (revoked EO 9691, effective 1947-05-01) is only an actor-context overflow, not a citable evidence record; no source shows that revoking the amended parent extinguished this amending order; the Schedule A trigger date (promulgation 1947-02-24 versus effective 1947-05-01) is untied.
- EO 9933 and EO 10069: EO 11012 section 3 revokes them only effective on the date the initial Bureau of the Budget and General Services regulations take effect; no held source gives that date. EO 10196 (and 10274, 10507) restates parts of EO 9805; clause-level supersession is not established.
- EO 9997: the producer-registered text is Proclamation 2814 plus a correction notice, not the order (the order text sits in the file registered for EO 9996); plus the same EO 11012 date gap.

## What took the time (one line per order)

- Boards (15 orders): one shared check of the EO 12553 table (the first page needs column alignment by position), then per-order reading of the clause span; EO 9929 needed an inventory fix.
- EO 10010: a rejected apply (working-text policy) and removal of the EO 10015 later event.
- EO 10015: reading the three-clause inventory against the EO 12553 row.
- EO 9949: reading EO 10415 and deciding how to treat the unproven transfer.
- EO 9787: locating EO 9894 (actor text only) and checking that the own-term records come from neighboring orders.
- EO 9799: reading the Foreign Service Act of 1980 sections 2205, 2401 and 2403 to test the repeal against the revocation date.
- EO 9815: confirming that EO 9830 has no citable record and reading its effective date.
- EO 9933, 9997, 10069: reading EO 9805 amendments, EO 10196 and EO 11012 section 3; finding the wrong registered page for EO 9997.
- EO 9982: finding the truncated inventory span and the 10011 date.

## Batch-check (applied-v2)

Members 24; claims checked 20; strict pass 20, strict fail 0; actual claim-checker: 20 checked, 20 all-checks-passed, 20 mechanical pass, 0 unverified, 0 fail, 20 gate passed; blocked 4; actionable failures none; independent human certifications 0. (applied-v1: 19 assembled, 1 rejected, 4 blocked; its batch-check failed only for EO 10010.)

## Tool notes

- No tool defect that stopped work. `apply` did not raise "changed Valla review context".
- Source supplements were not usable for the fr-originals: the declaration needs a local copy of the PDF, which the repository does not hold for them, so six board orders and EO 9787 cite the full held text of the revoking order as the ending quote (33,227 characters for EO 12553).
- The decisions sheets were generated by a script kept outside the packet; the final CSVs in the packet are the submitted input.
