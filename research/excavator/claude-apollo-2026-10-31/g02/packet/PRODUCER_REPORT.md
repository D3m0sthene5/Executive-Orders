# Producer report, batch g02 (Claude, subagent)

Start UTC: 2026-10-31T22:13:16Z. End UTC: 2026-11-01T03:38:40Z (the run was paused for a usage-limit reset; active work was roughly two hours).

Final packet: `packet/supp` (source supplement written inside the packet, as the production route requires). Final applied directory: `packet/supp/applied-v3`. Earlier versions are kept unchanged: `applied-v1` (two rejections: working-text confirmations), `applied-v2` (7 assembled; actual checker failed 9052 and 9405 on custody).
The sheets in the root `packet/decisions.csv` and `clauses.csv` were left blank; every decision is in `packet/supp/decisions.csv` and `clauses.csv`, because the supplement changes the dossier fingerprints.

Counts: 24 orders; 5 submitted, 19 blocked, 0 unresolved. batch-check (applied-v3): 5 claims checked, strict pass 5, fail 0, actual-checker mechanical pass 4, unverified 1 (EO 8937, see below). The command exit code is 1 only because of that one unverified item.

## Outcome per order

Submitted (all provisional NO; status not changed):

- EO 8714 (Treasury succession). First end 1955-01-13: EO 10586 says EO 8714 "is hereby revoked" (20 FR 361, held). The dossier's EO 10588 revocation records are a false positive from the shared Federal Register page extract (EO 10588 creates the Veterans' Pensions commission and does not mention EO 8714). Date is the signing date (no effective wording); printing on 1955-01-15 is the disclosed alternative. Savings: EO 10586 re-designates independently.
- EO 9200 (Schedule A, Subdivision II, para. 3). First end 1947-05-01: EO 9830 Part III revokes No. 9200; enacting clause orders the whole order "effective May 1, 1947:". The dossier had no ACT record, so the naming and the enacting clause are held excerpts from the retained official Federal Register PDF (SUPPLEMENT:FR9830P3, FR9830ENACT). Alternative reading (signing date 1947-02-24) disclosed. Savings: EO 9830 re-lists the Foreign Service Buildings Office entry only.
- EO 8937 (armed-forces eligibility). First end 1947-05-01 by the same EO 9830 route. Later event: EO 9579 restates the proviso (forty days to 90 days plus hospitalization), effective as of 1944-12-08; before-and-after text recorded. Savings: EO 9830 Rule II section 2.1(b). Unverified item: EO 9579 is held only as an APP mirror transcription (custody record only, expected for mirrors); page check done (heading, date and text hash agree), standing note carried.
- EO 9538 (probational certification). First end 1946-06-04: EO 9733 paragraph 3 "This order supersedes Executive Order No. 9538 of April 13, 1945" (official Federal Register text). EO 9830's 1947-05-01 revocation is recorded as a later event on an already superseded order. EO 9598 "does not supersede or modify" EO 9538 and is disclosed as a recital, not an end. The ninety-day wording is an applicant deadline, not an end.
- EO 9702 (Alton emergency board). First end 1986-02-25 by express revocation in EO 12553 (official Federal Register text lists 9702), per the owner's report-deadline ruling (option C). The report date and standstill end are not held; the 1946-04-07 report deadline and the 1946-05-07 latest standstill expiry (if the board reported on time) are disclosed as unestablished. An APP-based excerpt was rejected by the checker policy (official copy available) and is not used.

Blocked:

- 15 land orders (8658, 8776, 8786, 8864, 8865, 8874, 8883, 8915, 8932, 9026, 9053, 9081, 9130, 9143, 9173): the only end lead is an OFR note naming a Public Land Order, and none of those PLO pages is held (jobs/fr-pages holds none; the PLO numbers and Federal Register citations are listed in each row's gaps for the WANTED list). Eight of them (8865, 8874, 8915, 8932, 9026, 9053, 9081, 9143) were also amended by EO 9526, which adds a jurisdiction sunset tied to the end of the emergency declared by Proclamation 2487 while keeping the lands withdrawn; the terminating proclamation is not held in this packet. EO 8915 also carries an earlier independent review that left the Secretary-notice question open.
- EO 9333: own-terms "For the duration of the war and six months thereafter" versus EO 9830's revocation (1947-05-01); no held source fixes when the war ended for this clause, so the first end cannot be ordered.
- EO 9644: section 2 depends on the period of the War Service Regulations under EO 9063; EO 9691 (1946-02-04) revoked EO 9063 with a thirty-day transition, so the section 2 end falls on an undated day in early 1946; sections 1(a) and (b) overlap EO 9691 section 8 without being named.
- EO 9052 and EO 9405: claims assembled in applied-v2 (EO 9830 revocation, 1947-05-01) but the actual checker failed them on original-text custody. For 9052, the dossier's fixed original quote contains the OCR string "Executive Order 84612", read as a nonexistent order number. For 9405, the dossier's original is a reading-order rebuild (`EO_9405.recheck.txt`) the checker cannot verify. Both were blocked in applied-v3 with the exact fix named; the v2 sheets can be resubmitted unchanged once a checker-readable original is registered.

## What took the time (one line per order)

- 8714: reading the page extract to discard the false EO 10588 record.
- 9200, 8937: building the EO 9830 supplement (APP text omits two list entries, so the official retained PDF text was used) and quote verification.
- 9052, 9405: confirming no later Schedule A amendment (normalised search of held texts; EO 9653 headings) and then the checker custody failures.
- 9538: tracing EO 9733 versus EO 9598 and replacing an incomplete APP excerpt with the official text.
- 9702: weighing the report-deadline ruling and swapping APP for the official text after a policy rejection.
- 9333, 9644: working out the own-terms dates and finding no held source to fix them.
- Land orders: reading each order and confirming no PLO text is held (about one pass for all 15).

## Tool defects and observations

- The dossier ACT records for EO 9052 and EO 9405 depend on the fixed original span; a sheet cannot correct an original-text custody failure.
- The supplement route requires the raw file hash at `local_path`; fr-originals PDFs are not held, so only sources retained by jobs/astra-source-retention (here the 9830 PDF) work for official text.
- The APP transcription of EO 9830 omits Part III entries No. 458 and No. 8214; APP text of EO 9733 omits part of paragraphs 1 and 2. Both are unsafe as complete texts.
- The working-text gate rejects an APP excerpt when an official copy is held ("official_copy_available_recheck_required").
- ACT records for EO 9598 and EO 10588 are false positives from neighbouring text on shared Federal Register pages.
- batch-check exits 1 for the single unverified custody-record item even with zero failures.
