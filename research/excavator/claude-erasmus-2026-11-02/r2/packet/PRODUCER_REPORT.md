# Producer report: Erasmus r2 (producer: claude)

- Start: 2026-11-02T03:51:30Z
- End: 2026-11-02T04:10:00Z (approximately; the last command ran at 04:09:28Z)
- Final applied directory: `applied-v2`. `applied-v1` was rejected by apply for five orders and is kept as it was.
- Result: 9 submitted (assembled proposals) and 3 blocked. batch-check: 9 claims checked, 9 strict passes, 0 fails, 0 actionable failures; the actual claim checker passed and gated all 9; Geddes found 0 flags and 0 coverage gaps (`applied-v2/GEDDES_LINT.json`). Nothing needed resolving, so no `GEDDES_RESOLUTIONS.json` was written.
- Sheets: `decisions.csv` and `clauses.csv` in this packet. One-order views: `views/EO_N.json`.

## Outcome per order

| Order | Outcome | First end / reason |
|---|---|---|
| EO 8129 | blocked | Public Land Order 1704, the instrument that revokes this order, has no evidence record in this packet. The dossier's missing list says: Acting identity absent from census: PLO:1704. Proclamation No. 2416 (1940), which renamed the refuge, is not in the dossier either. The claim cannot cite its end, and it cannot record the renaming as the later event the review requires. |
| EO 8163 | blocked | Same gap as EO 8129: neither Public Land Order 1704 nor Proclamation No. 2416 is in the dossier. |
| EO 9538 | submit | Ends 1946-06-04: Executive Order 9733, paragraph 3, supersedes it by number, date and title. Later event: Executive Order 9830, Part III, revokes it effective 1947-05-01. |
| EO 9949 | blocked | This order's dossier has no evidence record for Executive Order 10804 (1959), which revoked the parent order, Executive Order 9721, with savings. No held source shows whether Miles's modified reemployment right vested or lapsed (by Executive Order 10415 his service had to end on or before 1953-12-31). |
| EO 10103 | submit | Ends 1986-02-25: Executive Order 12553 revokes it without exception. The 1959 Executive Order 10804 revocation is corrected to read as a general revocation with two savings, and it is recorded as a later event on every clause. |
| EO 10138 | submit | Ends 1986-02-25 (Executive Order 12553). The board's report, dated 1950-08-11, is disclosed as the date the order became functionally spent. |
| EO 10139 | submit | Ends 1986-02-25 (Executive Order 12553). The board's joint report, dated 1950-08-11, is disclosed the same way. |
| EO 10222 | submit | Ends 1994-06-03: Executive Order 12919, section 904(a)(2). Reorganization Plan No. 1 of 1958 and Executive Order 10952 are disclosed as unnamed earlier candidates. |
| EO 10283 | submit | Ends 1986-02-25 (Executive Order 12553). No held source records the President terminating the Board. |
| EO 10285 | submit | Ends 1986-02-25 (Executive Order 12553). The report, dated 1951-09-19, is disclosed. |
| EO 10303 | submit | Ends 1986-02-25 (Executive Order 12553). The inventory is corrected to one whole-order clause. The report, dated 1952-01-25, is disclosed. |
| EO 10314 | submit | Ends 1986-02-25 (Executive Order 12553). The report, dated 1952-02-16, is disclosed. |

Status is unchanged for every order. The certified count is 0.

## What took the time (one line per order)

- EO 8129 and EO 8163: confirming that the dossier held neither Public Land Order 1704 nor Proclamation No. 2416, and checking Proclamation No. 2416 in `jobs/fr-originals/output/texts/EO_8494.txt` and the earlier supplement's declarations.
- EO 9538: checking the issue date, April 17, 1945, against the govinfo file name, and reading Executive Order 9733 paragraphs 1–3 and the enacting clause and Part III of Executive Order 9830.
- EO 9949: reading Executive Orders 10415 and 10804 and finding that this order's dossier has no record for Executive Order 10804.
- EO 10103: reading section 2 of Executive Order 10804 to place its qualifier, then Executive Orders 11138 and 11303, the date of Executive Order 11303 and the 22 U.S.C. 288 note.
- EO 10138 and EO 10139: rewriting each order's own text and checking the board's held report.
- EO 10222: reading section 904 of Executive Order 12919 and the 1989 Codification note, and checking whether Executive Order 10952 and the 1958 plan are held.
- EO 10283: the clause that keeps the Board in existence until the President terminates it.
- EO 10285, EO 10303 and EO 10314: confirming which of the four operative elements each order contains, and checking the report dates.
- All orders: a script that checks every quotation in the sheets against the held source bytes, allowing only whitespace differences. 0 mismatches.

## Brief defects: confirmed, fixed, disputed or unresolved

- **EO 8129 and EO 8163** (Proclamation No. 2416 omitted). Confirmed: `EO_8494.txt` (sha256 87e6c363…) lists the old and new refuge names. Under the strike-and-insert ruling the renaming is an amendment of the naming sentence, so it is a later event and not an end. The defect could not be fixed in this packet because neither the proclamation nor Public Land Order 1704 has an evidence record. Both orders are blocked. A source supplement adding Public Land Order 1704, Proclamation No. 2416 and Reorganization Plan No. II would reopen them, and the earlier 1958-08-05 end would then probably stand.
- **EO 9538** (issue date given as April 27). Confirmed and fixed. The claim now gives the Federal Register of April 17, 1945 (file FR-1945-04-17), filed April 14, 1945, and says the OCR masthead is garbled. Recheck: I removed an unsupported note about search coverage and replaced a quotation that crossed a soft hyphen in the held text with a paraphrase.
- **EO 9949** (Executive Order 10804 omitted; whether anything survived). Both points confirmed. The order cannot be supported from this dossier, so it is blocked with the precise gap.
- **EO 10103** (Executive Order 10804 qualifier misread). Confirmed and fixed. The qualifier "insofar as it affects" is singular and attaches to Executive Order 10774. Executive Order 10103 was revoked generally, subject to two savings. The end stays at 1986: the savings kept the order "in effect" for the saved classes, and Executive Orders 11138 and 11303 applied it in 1964 and 1966. Recheck: the savings source changed from the order's own clause 2 to Executive Order 10804. The 22 U.S.C. 288 note claim was confirmed in the current-law MENTIONS output.
- **EO 10138 and EO 10139** (15 FR 4333 page error). Confirmed and fixed: both orders are on 15 FR 4241, in the Federal Register of July 4, 1950. Recheck: I removed a stray template fragment and the "railroad" description of a dock-company dispute, and the EO 12553 subject is now quoted exactly. I added the held report date under the owner's ruling on report deadlines.
- **EO 10222** (premise "end shown in 1986 or earlier"). Confirmed and fixed: the coverage text no longer relies on that premise. Recheck: the paths of the held texts behind the unnamed candidates are disclosed, and the text of the 1958 plan is stated to be unheld.
- **EO 10283** ("a labor dispute"). Confirmed and fixed: the claim now says "certain labor disputes" and names the employers and unions. The EO 12553 row is paraphrased because the held text layer reads "affeoting".
- **EO 10285** (status-quo sentence attributed). Confirmed and fixed. The order's four operative elements are listed, and no such sentence is described.
- **EO 10303** ("airline" subject; status-quo sentence). Both confirmed and fixed. The inventory override to one whole-order clause is kept.
- **EO 10314** (non-derogation sentence attributed). Confirmed and fixed. The claim lists creation with the bar on interested members, the report, the Defense Production Act sentence, and the sentence on unchanged conditions.

None of the brief defects was disputed.

## Geddes

The lint was run by batch-check and again on its own over `applied-v2`. It found 0 defect flags and 0 coverage gaps across 9 claims, so no resolutions were needed.

## Tool defects and notes

- apply on `applied-v1` rejected source notes that cited the National Mediation Board report texts (source-ladder files) registered as TERM evidence. The errors were `working_text_exact_grade_and_false_flag_required`, `working_text_fragment_identity_or_grade_mismatch` and `official_copy_available_recheck_required`. These report texts can be cited only as working texts with confirmations, so I removed the notes and disclosed the report dates, with their held paths, in the reasoning text. A disclosed "functionally spent" date (owner ruling of 2026-10-21) cannot currently be pinned to a non-order report through `source_notes`.
- For each board report, the pinned TERM span stops just before the date line on the title page, so the date itself lies outside the pinned bytes.
- In the dossiers for EO 8129 and EO 8163, the `machine_searches` entries have no `search_id`.
- Geddes did not crash.

## Full-packet files opened beyond the views

- `PACKET.json`, decoded once through `batch.load_packet` (a dump in the scratchpad), to list each dossier's evidence ids, its machine-search ids and coverage notes, its current-law leads and its TERM spans. The view shows the source catalogue only for the original, clause and TERM records; it does not list ACT or ACTOR_TEXT ids, and it does not show machine-search ids or coverage. This was the main gap.
- `decisions.csv` and `clauses.csv`, which hold the pre-filled `working_text`.
- `LOOKUPS.md`, read as the brief instructed.
- Outside the packet, read-only: the earlier claim sheets in the Apollo g01–g04 packets and the g01 source declarations, `jobs/later-events/output/EDGES.csv` (for the OFR disposition-note hits behind the machine-hit counts, which the view gives only as numbers), and `jobs/current-law/output/MENTIONS.csv` (for the U.S. Code notes).
