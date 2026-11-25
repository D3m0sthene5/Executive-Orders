# Producer report, m02 packet-v2-sup (baldus)

Start UTC 2026-11-25T19:12:15Z. End UTC 2026-11-25T19:48:15Z. Final applied directory: research/excavator/claude-baldus2-2026-11-25/m02/packet-v2-sup/applied-v1.

## Outcomes
Submitted (5): EO 10165, 10509, 10511, 10862, 10888. Blocked (3): EO 10449, 10635, 10875.
Each submitted order has two clauses (inventory corrected under owner rule D-20261108-board-rule): the board clause ends by completion of its task on the report date; the no-change clause ends by its own terms 30 days later (inclusive; exclusive reading stated). EO 12553 (1986-02-25) is a later event and the formal disposition, not the first end.
- EO 10165: report and letter dated 1950-11-02 (clean letter date, span through the submission sentence); board 1950-11-02, no-change 1950-12-02.
- EO 10509: cover 1954-02-17 (cover rule D-20261125-board-cover-date). Text-layer letter reads "February 27,1964"; the held PDF page image reads February 17, 1954. Board 1954-02-17, no-change 1954-03-19. Extension passage cited as a source note (no approval date printed).
- EO 10511: cover 1954-05-15; text-layer letter "May 15, 195~."; page image reads May 15, 1954. No-change 1954-06-14. Extension source note.
- EO 10862: cover 1960-07-15; text-layer letter year misread as 1980; page image reads July 15, 1960. No-change 1960-08-14. Extension source note.
- EO 10888: cover 1960-12-10; text-layer letter "Decembe~ 10,1960."; page image reads December 10, 1960. No-change 1961-01-09. Extension source note.
Blocked:
- EO 10449: no board constituted (NMB Board 104 sheet: no members, parties agreed 1953-04-26); no report, so own terms give no end, and no held source states the agreement's legal effect on the no-change sentence.
- EO 10635: the Federal Register printing interrupts the no-change sentence with the contents page, so no contiguous original span exists; needs page images of 20 FR 6485 and the continuation. Report letter dated 1955-10-26 (page image).
- EO 10875: the no-change sentence in the held 25 FR 3567 text is OCR-damaged; needs a legible original text (page image or the report's appendix registered as a held source). Report dated 1960-06-08; President approved an extension 1960-05-20.

## What took the time
All: the first pass found the report evidence not citable; the second route (source_supplement declarations, spans, extension passages, image checks) took most effort. 10509/10511/10862/10888: page-image checks of garbled letter dates. 10635/10875: clause splitting failed, decided as blocks. 10449: reading the NMB sheet.

## Batch-check
claims_checked 5, strict_claim_pass 5, fail 0, actionable_failures none; actual checker all 5 passed; blocked 3.

## Geddes
Flags 0 (coverage_gaps 5); no resolutions file needed. Lint: applied-v1/GEDDES_LINT.json.

## Full-packet files opened beyond views
PACKET.json and PACKET-v2 via batch.load_packet (evidence ids, clauses); HELD_SOURCES.json, HELD_SUPPLEMENT.json, LOOKUPS.md. Also jobs/olney-board-route (README, olney.py as a library for split_clause and as a format reference), research/excavator/claude-haloander-2026-11-07/tools/prompts/board_rule.txt, and the 2026-11-08 owner ruling.

## Tool defects
source_supplement.py refused a declaration file outside the repo until the coordinator moved it into the batch folder (research/excavator/claude-baldus2-2026-11-25/m02/DECL.json). The first apply on the original packet reported "changed prior research" (superseded by packet-v2).
