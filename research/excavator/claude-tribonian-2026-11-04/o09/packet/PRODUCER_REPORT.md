# Producer report, packet o09 (claude, 2026-11-04)

Start 2026-11-04T05:38:58Z. End: see last line.

Final applied directory: `applied-v2` (applied-v1 preserved; it differed only in that four Federal Register orders were submitted without a page image).

## Outcome
30 orders: 24 submitted, 6 blocked.

Submitted (23 retirement exemptions, each one clause, own fixed term, first end inclusive with exclusive alternative stated): EO 9015 (1943-06-30), 9016 (1943-01-31), 9030 (1943-02-28), 9031 (1943-04-30), 9032 (1943-01-31), 9033 (1943-01-31), 9034 (1943-02-28), 9037 (1943-04-30), 9043 (1943-01-31), 9044 (1943-01-31), 9045 (1943-01-31), 9056 (1943-03-31), 9062 (1943-02-28), 9077 (1943-02-28), 9100 (1943-07-31), 9118 (1943-04-30), 9131 (1943-04-30), 9144 (1943-04-30), 9174 (1943-06-30), 9199 (1943-08-31), 9201 (1943-07-31), 9202 (1943-09-30), 9208 (1943-09-30). The "further exempt" orders (9016, 9030, 9031, 9037, 9118) record the earlier grant as an earlier recited instrument, not a later event. EO 9062: lead EO 9378 read and rejected (amends EO 9063, does not name 9062). Also submitted: EO 9161 (revocation of EO 8975, performed 1942-05-13).

Blocked:
- EO 9120, 9147, 9204, 9260: FR page image not held (only the machine text layer of the official PDF); assembler requires original_confirmed. Analysis done and recorded in each rationale: 9120 self-executing revocation effective 1942-06-30 (ninetieth day); 9147 revocation performed 1942-04-25; 9204 all six clauses ended 1945-10-29 by EO 9649 terminating the Office; 9260 three clauses amended by EO 10600 (1955-03-15) and ended 2018-04-20 by EO 13830 sec. 8(c) supersession. Needed: govinfo FR PDF/page images.
- EO 9184: first end undecidable; EO 9279 and EO 9409 (restatements of the War Manpower Commission membership) are not citable from the packet; needs source supplement; EO 9617 does not name it.
- EO 9238: states no term or end date for the Forster/Latta exemptions; no held ending instrument.

YES orders: none (all provisional status no).

## What took the time
- Retirement orders: scripted from the held texts; name search over held texts was the long step.
- EO 9204, 9260, 9184: reading the later orders (9649, 10600, 13830, 9409, 9617, 9279).
- Apply 5 minutes (v1), batch-check about 3 minutes.

## Batch-check (applied-v2)
Exit 1. 30 members; 24 claims checked; strict pass 24, fail 0; 0 errors; 0 mechanical failures; actual checker 24 gate-passed, 24 unverified solely for source_held:custody_record_only (coordinator retaining those bytes) plus the recorded-verbatim date_valid note.

## Geddes
0 defect flags; 20 coverage gaps (18 "no other held order text names him" pronoun not resolved; 2 for EO 9161 whose APP text has no heading). All recorded as disputed in `applied-v2/GEDDES_RESOLUTIONS.json`.

## Full-packet files opened beyond views
PACKET.json (to find TERM evidence spans), decisions.csv and clauses.csv (edited). LOOKUPS.md head only. No READ.md.

## Tool defects
None blocking. The first apply attempt in the shell was killed once by my own pkill; nothing was written by it.
2026-11-04T06:23:33Z
