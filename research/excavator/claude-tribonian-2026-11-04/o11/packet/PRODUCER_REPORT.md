# Producer report, packet o11 (Tribonian)

Start UTC 2026-11-04T06:07:11Z. End UTC 2026-11-04T06:42Z.

## Outcomes (30 orders: 14 submitted, 16 blocked)

Submitted (applied-v1, status no, all clauses terminated, whole_order_end equals the latest clause end):
- Revocations performed on signing: EO 9622 (1945-09-20, revokes EO 9103), EO 9625 (1945-09-21, revokes EO 9294; inventory corrected to chars 781-1145 because the machine clause stopped at "it is ordered that"), EO 9667 (1945-12-28, EO 9074), EO 9859 (1947-05-31, EO 9196), EO 9883 (1947-08-11, EO 9172), EO 9906 (1947-11-18, EO 7165).
- Own-terms ends: EO 9810 (1946-12-24 half-day excusal; publication clause 1946-12-14), EO 9907 (1947-12-24; publication 1947-12-04), EO 9849 (six months from 1947-05-09, recorded 1947-11-09), EO 9889 (until 1952-07-25, inclusive with exclusive reading stated), EO 9928 (until 1948-06-30, inclusive), EO 9627 (sixty days from 1945-09-24, recorded 1945-11-23).
- Successor appointment: EO 9618 (ended no later than 1947-10-25 by EO 9901, which appoints a successor vice Arnold; resignation date unheld, disclosed) and EO 9901 (ended no later than 1953-07-07 by EO 10468, same pattern; resignation date unheld, disclosed).

Blocked (precise gap named in unresolved_material_gaps in decisions.csv): EO 9610 (Second War Powers Act Title II expiry not held), 9611 (guidance clause of paragraph 3 undated; page check), 9616A (war or emergency termination not tied to a held dated source), 9626, 9661 and 9736 (no held record of the Director's termination of possession), 9679, 9690, 9714 (later amendments EO 9792, 9840, 9867, 9886 not read for effect), 9740, 9764, 9811 (later trust-extension orders and statute not held), 9812, 9814 (submission date of final recommendations not held), 9915 (Joint Resolution of 1947-12-30 not held), 9917.

## What took the time
- Batch of 14 submissions: reading clause text and surrounding Federal Register page layout (most time: separating adjacent orders printed on the same page, e.g. EO 9622, 9667, 9928).
- 9618/9901: tracing the successor chain and the unheld resignation dates.
- Blocked orders: short checks of the view, then a precise missing-source statement per order.
- Apply 26 s; batch-check about 25 min (busy machine).

## Batch-check counts
Packet members 30; claims checked 14; strict pass 14, fail 0; actual claim-checker 14 all-checks-passed, mechanical fail 0, gate passed 14; blocked 16; independent human certifications 0.

## Geddes
GEDDES_LINT.json written by batch-check in applied-v1: 0 defect flags, 5 coverage gaps. No GEDDES_RESOLUTIONS.json needed (no flags).

## Full-packet files opened beyond the views
PACKET.json (via batch.load_packet, once, for evidence text and clause spans), decisions.csv and clauses.csv (edited), LOOKUPS.md (read in full). READ.md and LOOKUPS.details.json were not opened. Repository sources opened: the held fr-originals texts of the 30 orders and of EO 9387, EO 9901, EO 10468, EO 10018 (excerpts), the 1964 U.S. Code front-matter text (grep only).

## Tool defects
None blocking. batch-check's wall time exceeded the 120 s foreground limit and had to run in the background. Scratch scripts are under /tmp/claude-0/tribonian-work/o11/.
