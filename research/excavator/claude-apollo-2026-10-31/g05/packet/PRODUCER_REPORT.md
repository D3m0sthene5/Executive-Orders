# Producer report, g05 (agent: claude)

Start UTC: 2026-10-31T22:14:24Z. Report written: 2026-11-01T03:31Z. End UTC: 2026-11-01T03:34Z.

## Outcome
- applied-v1: 19 assembled, 2 blocked, 3 rejected. The three rejections (EO 10371, 10372, 10509) came from report-date later events that cited the held board report text as a working-text source; the checker required a recheck against an official copy of the order. I removed those later events; the report date stays in each clause reason as a spent fact.
- applied-v2 (final): 22 assembled proposals, 2 blocked.
- Submitted (22): 10371, 10372, 10406, 10415, 10509, 10511, 10542, 10543, 10570, 10576, 10605, 10615, 10630, 10634, 10681, 10691, 10693, 10710, 10723, 10738, 10739, 10749.
- Blocked (2): EO 10381 (the revocation by EO 11012 section 3 depends on the effective date of initial regulations, which no held source states). EO 10718 (no held evidence record for the current-law predicate, and the dossier clause inventory includes neighbouring Reorganization Plan sections instead of sections 1 to 3 of the order).

## Batch-check on applied-v2
Packet members 24; claims checked 22; strict claim pass 22, fail 0; blocked 2. The actual claim checker passed the gate for all 22 and all mechanical checks for 21. One actionable failure remains: EO 10570, three quote_verbatim failures (original representation quote, clause quote, original-source quote). The dossier original for EO 10570 is the pdfplumber recheck text (EO_10570.recheck.txt, hash matches, quotes match its bytes exactly), but the checker looks up the same PDF hash in the clause-drafts source record, whose saved text is an earlier OCR span of the same page, and the quotes do not appear in it. This is a mismatch between two held OCR readings of one PDF, not a quoting error. I did not block the order because the claim passes the structural gate and the quoted text matches the registered dossier evidence; the coordinator should decide whether to block 10570 or reconcile the two texts.

## Ends used
Thirteen emergency-board orders and 10543: express revocation by EO 12553, 1986-02-25 (no effective-date wording; signing date). 10542 and 10710 as in their rationales. 10634: EO 12148 section 5-106, effective 1979-07-15. 10605, 10681, 10739: EO 11157 section 502, 1964-06-22. 10738: EO 10906 superseded, 1961-01-18. 10415: continues until the parent order ends. Report deadlines and standstills are recorded as spent facts, not ends.

## Time spent
Most time went to the kit apply step (about 105 seconds of work, but long waits while other producers' kit processes ran), to locating exact revocation rows in the OCR of EO 12553 (numbers column OCR'd apart from subjects), and to the two blocked orders.

## Tool defects
- Apply and batch-check were slow under concurrent load from other producers.
- The working-text policy forces a recheck error for any later-event source whose instrument id has an official copy, so a report-date later event cannot be submitted from a held board report.
- Checker and dossier use different held OCR texts for EO 10570 (see above).
- Dossier inventory for EO 10718 spans the wrong text sections.
