# Pullman: emergency-board packets, prepared for the report-deadline ruling (2026-10-20)

The name comes from the 1894 Pullman strike, which led Congress to create federal railway labor boards. This folder holds pre-staged packets for the EO 12553 board orders whose first end depends on the owner's pending report-deadline ruling. Building them used no agents. **The ruling is not decided here.** No claim was written, no status changed, and the certified count stays 0. Nothing is committed.

`PACKETS.jsonl` has one line per order, 98 lines in all:
- **89 lines** are the Rastell batch 03-08 EO 12553 targets that were held out of R12553C. Each of them has an EO 12553 ACT record that the reviewer upheld with claims_enabled yes. EO 10376 (Post Office) is excluded.
- **9 lines** are extras: EO 9770, 9923, 9936, 10615, 10723, 10878, 11050, 11445 and 11543. Each is an emergency board with an upheld EO 12553 ACT record, but the reviewer marked claims_enabled no because the board's report may be an earlier end. That is the same ruling question.

Each line holds:
- the report-deadline clause, quoted verbatim with its text path and offsets, the text sha256 and the source PDF sha256. Every slice was re-checked against the file.
- the RLA standstill clause.
- a deadline computed from the clause, for information only.
- amendment and extension leads from the dossier chain.
- the held report, if any: its path and both sha256 values, the extracted report date with its page, line and surrounding page text, and the cover, transmittal and signature candidates with their flags.
- the EO 12553 ACT record id.
- the alternative first-end dates: A (on report), B (report + 30 days) and C (EO 12553, 1986-02-25).
- what is still missing.

## Readiness on the ruling (89 core / 9 extra)

| Class | Core | Extra | Meaning |
|---|---|---|---|
| staged_complete | 63 | 1 | Deadline clause, report date and ACT record are all held. Runnable under any ruling. |
| report_date_needs_reviewer | 6 | 0 | **EO 10045:** the "Signed ... 4th day of April 1949" line differs from the NMB index (04-06). **EO 10109 and EO 10874:** the year is misread in the OCR text. **EO 10811, 11040 and 11042:** the only dates are standalone date lines. |
| needs_page_check | 2 | 0 | EO 10286 and EO 10509; see below. |
| special_no_board_constituted | 1 | 0 | EO 10449. |
| awaiting_report_source | 17 | 8 | **Core 17:** 7 lines are still retry_later from the Lamm III run (EO 10029, 10106, 10117, 10130, 10283, 10542, 10576). 10 more are retry_later now. 9 of the 17 are LMRA sec. 206 boards of inquiry, which have no NMB report, so they need another route such as the Public Papers. **Extra 8:** no FETCH_QUEUE line exists. |

Under each possible ruling:
- **Ruling C:** all 89 core orders can run on the ACT record alone. EO 10449 runs only if the ruling also covers a board that was never set up.
- **Ruling A or B:** 63 core orders can run now. 8 more need a reviewer or a page check, and 17 need a report source first.

Two more facts bear on the ruling:
- 52 of the 70 core report dates fall after the creating order's own 30-day or stated deadline. The extension letters or orders behind them are mostly not held. So a reading of "the board ends at its deadline" would need extension sources for most orders.
- EO 10933 says that "the thirty-day period following the report ... shall be deemed to be included in the extension of time provided by this Order".

## Special orders

- **EO 10286 (PEB 96):** PDF pages 1-3 have no text layer, and no OCR or image text of them is held. Pages 4-8 give the creation date (September 6, 1951) and the chairman's appointment (September 7, 1951), but no transmittal date. No date is visible, so the order is marked **needs_page_check**. The NMB index closing date, 10/3/1951, is an index entry, not proof of the report date.
- **EO 10449 (PEB 104):** the NMB record says "No members appointed" and "Parties reached agreement on April 26, 1953 ... no emergency board was set up". The board was never constituted, so there is no report and no report date.
- **EO 10509 (PEB 105):**
  - The transmittal line's OCR text reads "WASHINGTON, D. C., February 27,1964."
  - The front page reads "FEBRUARY 17, 1954".
  - Page 4 says the report time was extended to "February 17, 1954".
  - "1964" is an OCR error for 1954. Whether the day is 17 or 27 needs a page check of PDF page 2. The packet uses 1954-02-17 as the lead.

## The ruling question for the owner

A Presidential Emergency Board order says the board "shall report ... within thirty days" and that no change may be made "for thirty days after the board has made its report". The order itself has no other end, and EO 12553 later revoked it expressly on 1986-02-25. When does the order first stop operating?

- **(A)** On the date the board made its report: the board's task is done.
- **(B)** When the RLA sec. 10 standstill ends, 30 days after the report. This is not applicable to LMRA boards of inquiry.
- **(C)** Only on express revocation by EO 12553 (the 1986-02-25 on_signing reading). Under C the report and the standstill are spent facts, not ends.

A or B would also need three sub-rulings:
- which date counts as "made its report": the transmittal letter, the cover date or the date received;
- what ends a board that was never constituted (EO 10449);
- whether a missed or extended deadline matters.

The packets already hold the A, B and C dates for each order.
