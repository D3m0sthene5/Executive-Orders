# clause_inventory (H5-w13)
Start 2026-11-05T23:57:25Z; end 2026-11-05T23:59:30Z (H5-w13 re-verification)

EO:2489: blocked:official page image/record for ProQuest 1916-EO-2489 (needed for original_pages_confirmed and working-text pages_confirmed; none held, Cruden page check "none found")
Time: reading the two short texts; no validator run.
EO:4220: blocked:official page image/record for ProQuest 1925-EO-4220 (same reason)
Time: working out that the draft's two scopes were one OCR-split clause.

Inventory itself is done and confirmed (inventory_confirmed=true); identity and complete_text booleans set true for the ProQuest source of each order; pages_confirmed and original_confirmed/original_pages_confirmed left false.

Clause scopes:
- EO:2489#whole (0-370, unchanged): reserves NE1/4 Sec. 21, T. 28 S., R. 8 W., N.M.P.M., New Mexico, 160 acres, for military purposes. Signed Woodrow Wilson, 21 Nov 1916. Single sentence, no term stated.
- EO:4220#whole (override, ORIGINAL:EO:4220, 273-6790): temporarily withdraws, in aid of classification contemplated by the acts of 4 Mar 1925 (Public Nos. 613 and 616), the public lands in the listed Oregon Willamette Meridian townships/sections that are not part of any national forest, subject to valid claims and existing withdrawals. No stated term in the held text; the draft #lead/#4 split was an OCR artifact and both old rows were replaced (the sheet row has blank clause_id). The report_deadline wording feature came from the old lead scope; check the text for any report/deadline before treating it as an ending. The evidence span starts mid-sentence ("tions therein expressed"), after the preamble, so the preamble cannot be quoted.
- OCR date in the scan reads "May 8, 1926"; register and the 1925 acts say 8 May 1925. Do not quote the date from the scan.
Not run: kit.py view/apply validation of the override (slow); the next worker should run it.

Re-verified texts by direct read. Corrected EO:4220 override end from 6895 to 6790: 6895 ran past the signature (CALVIN COOLIDGE at 6799) and number; 6790 is end of the last township entry. Start 273 = "tions therein expressed". Still not run: kit.py view/apply validation. Page check missing for both (no page image/record held), so original_pages_confirmed stays false; blockers as above.
