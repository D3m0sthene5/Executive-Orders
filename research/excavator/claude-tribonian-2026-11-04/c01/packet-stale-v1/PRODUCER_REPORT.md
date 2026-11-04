# Producer report, batch c01 (Tribonian correction run)

Start UTC: 2026-11-04T12:05:25Z
End UTC: 2026-11-04T12:31:49Z

## Outcome: STOPPED at apply; no claims assembled

`python3 jobs/claim-kit/kit.py apply <packet> --write <packet>/applied-v1` refused with
`claim-kit: changed prior research; prepare a new version` (exit 2). The brief says to stop and report this
rather than work around it, so I did not run batch-check, did not create any applied-vN, did not run Geddes,
and did not run `prepare`. No applied directory exists. Submitted: 0. Blocked (not assembled): 15.

I did not add or change any research file outside the packet. The prior-research fingerprint is checked against
research about these orders written outside the packet folder after preparation; other producers (c02, c03) were
running in sibling batch folders at the same time, which may be the cause, but I could not confirm that without
opening other folders. The coordinator should check that and re-prepare or re-run apply.

## Work done and ready (sheets are filled, not yet applied)

decisions.csv and clauses.csv in the packet hold complete corrected sheets for all 15 orders (15 decision rows,
164 clause rows, one new scope per enacting-words block and per numbered section; the Prior Actions section is split
in two where it has a precedence sentence and a revocation sentence). All 15 rows are `submit`, agent `claude`.
RATIONALES.json is unchanged (`{}`). The generator is /tmp/claude-0/tribonian-work/c01/gen.py with wording in
/tmp/claude-0/tribonian-work/c01/data.py; the blank originals are saved in /tmp/claude-0/tribonian-work/c01/orig/.

Per-order outcome if applied: every order is a terminated whole order (status no), all scopes ended 1969-10-28 by
express revocation in EO 11490 Sec. 3015 (items: 10346 item 4, 10997 item 5, 10998 item 6, 11000 item 8, 11001 item 9,
11002 item 10, 11003 item 11, 11004 item 12, 11088 item 15, 11090 item 17, 11091 item 18, 11092 item 19, 11093 item 20,
11094 item 21, 11095 item 22). The one-time revocation sentences of earlier emergency preparedness orders (in 10997,
10998, 11000, 11001, 11002, 11003, 11004, 11091, 11094 and 11095) end on each order's signing date as executed on issuance.

Defects from the brief, checked against held sources and fixed in the sheets:
- Savings reason (all 15): the span of the end source runs from "SECTION 501. Functions." through Sec. 3015 (Parts 5
  to 30), not Secs. 3011 to 3015; the Sec. 3014 quotation now reproduces the APP wording "Except as provided by
  Section 3015" instead of the Federal Register print wording.
- EO 11003 sec5, EO 11004 sec7, EO 11091 sec6, EO 11094 sec10, EO 11088 sec7, EO 11090 sec8, EO 11093 sec11: reasons
  rewritten to describe what each section actually says (guidance, redelegation, precedence), none assigns functions.
- EO 11092 sec7: the held text has no sentence reserving the authority to the President; the reason now says so.
- EO 11092 sec9: described as the non-derogation, continuance and precedence section.
- EO 10346: later events now include EO 10438, EO 10773, EO 10782 and EO 11051 on the scopes they touch; EO 10529
  only cites Section 3 and is not an event. EO 10773's held file ends at the first Federal Register page
  ("Continued on p. 5063"), so only its Secs. 3 and 4 are relied on; its date (1958-07-01) rests on EO 10782's text.
- EO 11090: the Federal Register print of EO 11490 (OCR) does not show its number, so the claim rests on the
  transcription alone and says so.
- Working-text confirmations: only the APP mirrors cited (EO 11490; EO 11051 for EO 10346) are confirmed, after the APP
  page-record check (MIRROR_DOCUMENTS.jsonl rows: heading, date and text sha256 agree with the held texts).

## What took the time (one line per order)
All orders: reading the full order text and checking each section description against the held bytes dominated; the
Sec. 3014/3015 wording and end-source span were shared work. EO 10346: tracing four later instruments (10438, 10773,
10782, 11051) and the signing date of EO 10773. EO 11092: the sec7/sec9 corrections. EO 11094 and 11095: long
multi-agency sections. EO 11090: the missing Federal Register print hit. Others: routine.

## Batch-check counts
Not run (apply refused).

## Geddes flags and resolutions
Not run (no applied directory).

## Full-packet files opened beyond the views
LOOKUPS.md (grep for page-check lines only), decisions.csv and clauses.csv (my own sheets), CORRECTION_BRIEF.json,
the prior a02 applied-v2 CLAIMS.proposed.jsonl, the a02 review files were not opened.

## Tool defects
None found, other than the `changed prior research` refusal described above.
