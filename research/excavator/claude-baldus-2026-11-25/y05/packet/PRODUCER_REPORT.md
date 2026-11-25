# Producer report: baldus, packet y05

Start 2026-11-25T15:40:34Z. End 2026-11-25T15:56Z (final applied directory `applied-v1`).

## Outcomes
| Order | Outcome | Why |
|---|---|---|
| EO:11545 | submit (yes) | Four sections, all operative; sections 1 and 2 amended by EO 14085 section 6 (2022-10-03), recorded as later events with before and after wording; no end found. |
| EO:11582 | blocked | Section 7 ends "until changed by the Postal Service" and no held source shows whether or when it changed; the section 2(a) list entry "fourth Monday of October" was displaced by statute (5 U.S.C. 6103 text held only outside the packet catalogue; Pub. L. 94-97 not held); overlap of sections 3-6 with 5 U.S.C. 6103(b) unresolved; inventory lacks sections 1 and 5. |
| EO:11593 | submit (yes) | 17 clauses, all operative; deadlines (1973-07-01, 1972-01-01 and annually) are not ends; EO 13006 and EO 13022 recite the order and neither amends nor revokes it. Judgment call: section 2(b) (interim caution until inventories complete) is treated as continuing because no held source shows completion. |
| EO:11609 | blocked | About 50 delegations each rest on a statute whose current text is not held; EO 11429, 12107 and 12608 provisions not located; paragraphs (22)-(23) revoked by EO 12215; inventory has a duplicate scope and no section 7 clause. |
| EO:11633 | blocked (dispatch) | ORIGINAL and CLAUSES sec1-sec4 not held. Not researched. |
| EO:11755 | submit (yes) | Seven clauses: sections 1, 1(a)(1), 1(a)(2), 1(b), 2 and 4 operative (section 1 amended by EO 12608 section 23 and EO 12943); section 3 (supersession of EO 325A) terminated 1974-01-01 on its own terms. Judgment call: section 2 (revise procurement regulations) treated as a continuing duty by inference from later FAR rulemakings; no held source dates a first performance. 28 CFR 0.94-1 is custody_record_only, so cited as context, not as source. |
| EO:11846 | blocked (dispatch) | ORIGINAL and all CLAUSES records custody_record_only. Not researched. |
| EO:11851 | submit (yes) | Inventory corrected (the OCR fragment "301." merged into section 2); all clauses operative; authority 7 U.S.C. 1854 is current (text held outside the catalogue, context only). |
| EO:11884 | submit (yes) | Sections 1-4 and enacting clause operative on the bounded-search record only (zero hits in all three searches, no affirmative current-law source); section 5 (revokes EO 10016) terminated 1975-10-07 on its own terms. |

Submitted 5, blocked or unresolved 4 (2 producer blocks, 2 dispatch blocks). No order was found not in force on 2026-10-14. All assessment rows are in `ASSESSMENT.jsonl`; `first_cause` is "unresolved" for every row because no cessation was established for any order.

## What took the time
- 11545: reading EO 14085 section 6; the CURRENT-note quote defect (below).
- 11582: weighing section 7, section 2(a) and the 5 U.S.C. 6103 overlap; decided to block.
- 11593: 17 per-clause reasons; deadlines versus ends.
- 11609: deciding the 61-clause inventory was not supportable; blocked early.
- 11755: two amending orders, the section 3 end date, the section 2 judgment.
- 11851 and 11884: inventory correction (11851) and the self-executing revocation clause (11884).

## Checks
- apply: 5 assembled, 2 blocked, 2 unresolved (ran 25 s).
- batch-check: 5 claims checked, 5 strict pass, 0 fail; actual claim checker 5 of 5 all checks passed, 0 mechanically unverified; 0 actionable failures.
- Geddes lint: 0 defect flags, 5 coverage gaps (no flag needs a resolution; `GEDDES_RESOLUTIONS.json` not written). `GEDDES_LINT.json` is in `applied-v1`.

## Files opened beyond the views
LOOKUPS.md (prescribed). LOOKUPS.details.json structure only (key listing). Outside the packet, repository sources: `jobs/current-law/output/` (MENTIONS.csv, EVENT_CANDIDATES.csv, ORDERS_CURRENT_LAW.csv, usc-notes), `jobs/later-events/output/EDGES.csv`, `jobs/theophilus-sources/output/texts/` (5 U.S.C. 6103, 7 U.S.C. 1854, 5 CFR 610.201-.202, 19 CFR 12.6, 28 CFR 0.94-1), `jobs/fr-originals/data/full_run/texts/` (the orders and amending orders). No READ.md or PACKET.json was opened. `jobs/claim-kit/*.py` and `jobs/claim-checker/checker.py` were read for the field formats. Scratch scripts are in /home/claude/baldus-scr/work/y05/.

## Tool defects
1. The claim checker cannot quote-verify a CURRENT: record that is a U.S. Code note: it reads `USC_EO_NOTES.jsonl` as raw JSON lines, so the first-two-lines quote the assembler picks (with a newline) is "not_found" (observed: "first 8 of 33 words found"). Claims therefore use the held original clause as the current basis, which the brief allows.
2. A CURRENT: record from eCFR (28 CFR 0.94-1) is custody_record_only (no bytes held), which fails completion; it was not cited.
3. The assembler gives a clause record no actor, so a terminated clause cannot use its own CLAUSES id as `end_id`; `ORIGINAL:EO:N` was used (it carries the instrument id).
4. Dossier inventories have OCR-derived defects (11582, 11609, 11851); only 11851 was corrected.
