# Producer report, packet a01 (Tribonian)

Start UTC 2026-11-04T04:48:13Z (first pass; full redo after the coordinator re-prepared the packet). End UTC 2026-11-04T11:07:35Z. Final applied directory: applied-v6. Earlier directories applied-v1 to applied-v5 are retained.

## Outcome
Submitted 6 (EO 8226, 8402, 8497, 8538, 9027, 9301). Blocked 27. No order is unresolved.

Submitted orders and why:
- EO 8226: superseded by EO 8384 sec. 21 (retroactive date handled); the flagged EVENT_BEFORE_SIGNING conflict is EO 7845, the order EO 8226 amends.
- EO 8402, 8538, 8497: exemption orders ending by their own stated terms (recorded inclusive, exclusive reading disclosed); later further-exemption orders are later events.
- EO 9301: revoked by EO 9607 (August 30, 1945).
- EO 9027: Schedule A amendment revoked by EO 9830 Part III, effective May 1, 1947.

Blocked, by cause:
1. End instrument not citable (view carries no ACT record for EO 9830): EO 8214, 8257, 8283, 8937, 9333, 9653, 9815, 9644, 9691. The end is located in the held EO 9830 text (Part III list, enacting clause "effective May 1, 1947:"); a source-excerpt declaration is needed. EO 9333 also has an own-terms question (duration of the war plus six months; Proclamation 2714 not held). EO 9644 and 9691 also have own-terms limits that may end clauses earlier (War Service Regulations period; transitional period) and EO 9691 has 16 rows.
2. Only an APP-based ACT record exists while the official FR copy is held (applied-v2 rejected the APP citation with working_text:official_copy_available_recheck_required; applied-v3 rejected the actor-text citation with clause_N_first_end): EO 8168, 8751, 9067, 9294, 10169, 10223, 10359, 10373, 10377, 10433, 10685. These were fully decided (ends and dates in the blocking note). Needs an ACT or source-excerpt record pointing at the official text.
3. Actual-checker custody failures on fully prepared claims: EO 8078 and 9405 (registered original is a recheck text that differs from the SOURCES.jsonl text the checker reads, so quotes fail quote_verbatim), EO 9052 (registered text contains the OCR string "Executive Order 84612", which fails order_exists).
4. Too large or dependent on unheld dates: EO 10161 (about 70 rows, many ended earlier), EO 10193 (EO 10461 takes effect when the first Director under Reorganization Plan 3 of 1953 enters office; date not held), EO 10200 (clause-level ends differ), EO 10483 (EO 10700 effective July 1, 1957 unless funds unavailable; appropriation record not held).

## What took the time (one line per order)
8078: inventory of four rows and the amendment-versus-performed reading; checker custody mismatch. 8168: EO 8854 revocation and later re-reservation. 8214, 8257, 8283, 8937: locating the EO 9830 row and the later amendments (8564, 8363, 9579). 8226: retroactive supersession date and the EO 7845 conflict. 8402, 8538, 8497: exemption chains and a surname misspelling in EO 9238. 8751: EO 8926 section 5. 9027, 9052, 9405: sched A quotes; 9052 and 9405 checker failures. 9067: the machine inventory covered EO 9066, replaced with six sections; reemployment-rights chain. 9294: duplicate-numbered rows and EO 9570 lead rejected. 9301: EO 9607. 9333: war-duration wording. 9644, 9691, 9815: War Service Regulations chain and EO 9830. 9653: 17-row inventory with repeated paragraph numbers. 10161: 70-row inventory. 10169, 10373, 10377, 10359, 10433: EO 10480 section 607, inventory corrections for 10377 and 10359. 10193, 10200: effective-date dependency and clause-level ends. 10223: EO 10281 section 404 versus EO 10480 relisting. 10483: EO 10700 section 7. 10685: partial revocation (10827) then supersession (10900), EO 12220 relisting.

## Batch-check (applied-v6)
Six claims checked: 3 all checks passed (8226, 8497, 9301), 3 pass with unverified (8402 and 8538: source_held custody_record_only, which the coordinator is retaining; 9027: quotation too short to verify), 0 mechanical failures, 6 gate passed. Earlier runs: applied-v1 failed 9052 and 9405; applied-v2 rejected 12 orders; applied-v3 rejected 11; applied-v5 had 3 mechanical failures (8078, 9052, 9405), all moved to blocked in v6.

## Geddes
Lint on applied-v6: 6 claims, 0 defect flags, 2 coverage gaps, both on EO 9301 (order heading unresolved). Recorded as disputed in GEDDES_RESOLUTIONS.json (coverage gaps, not defects). The first lint attempt crashed with "held corpus inventory commit changed during search" because other producers wrote to the corpus; a rerun succeeded.

## Full-packet files opened beyond the views
None of READ.md, LOOKUPS.details.json or PACKET.json were read directly; I loaded the packet through batch.load_packet (read-only) to read dossier conflicts, which the views omit (EO 8226, 10223, 10685), and read PACKET-cited held texts under jobs/fr-originals and jobs/app-executive-orders.

## Tool defects and gaps
- Views omit dossier conflicts; apply rejects with unresolved_conflicts until conflict_resolutions are filled.
- Registered recheck originals differ from the SOURCES.jsonl text used by the actual checker (8078, 9405).
- order_exists treats OCR numbers in whole-page texts as citations (9052: "84612").
- ACT end records that point at APP transcriptions fail when an official copy is held; actor-text records cannot serve as first-end sources, leaving no citable route for 11 fully decided orders.
- Geddes crashed once on a corpus commit change during a search.
- Four of my applies were slow (up to 25 minutes) because of machine load from other producers; applied-v4 was empty and abandoned.
