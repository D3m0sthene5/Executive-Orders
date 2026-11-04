# Producer report, packet o23 (claude)

Start UTC: 2026-11-04T06:38:06Z. End UTC: 2026-11-04T11:13:35Z (the run was interrupted by a usage limit and resumed).
Final applied directory: applied-v3 (applied-v1 and v2 retained; v1/v2 included EO 13420, which the checker left unverified).

## Outcomes (3 submitted, 27 blocked)
- Submitted: EO 13421 and EO 13453 (one-day closing orders, every clause ended by its own date, 2007-01-02 and 2007-12-24, inclusive, exclusive reading disclosed; no later held order names either number), and EO 13561 (every clause ended by section 8 of EO 13594, signed 2011-12-19, "is superseded"; disclosed note that EO 13594 section 7 sets pay-period effective dates).
- Blocked, EO 13420: end by EO 13454 section 8 (2008-01-04) is textually supported, but the checker finds the official PDF bytes of 08-62 held nowhere (custody record only), so the source stays unverified; the APP mirror has no confirmation prepared.
- Blocked, 11 emergency boards (13409, 13417, 13429, 13452, 13586, 13654, 13663, 13670, 13679, 13700, 13711): the section 5 end depends on the actual report-submission date, which no held reviewed source gives (NMB table is an index only); the records-maintenance clause (section 4) outlives the Board and needs a current-source check that is not held.
- Blocked, 7 pay orders (13594, 13635, 13641, 13655, 13715, 13756, 13819): superseded only "as of the effective dates" in the later order's section 7, and pay-period start dates are not held.
- Blocked, 7 closing orders (13482, 13523, 13633, 13682, 13713, 13852, 13854): no held evidence ends the OPM implementation, general-provision and disclaimer clauses; EO 13523 also lacks a page/heading check.
- Blocked, EO 13811: per-clause first ends (until-date vs EO 13889 effective date, sections 3 and 4, 1(s) by EO 13872) not established.
Judgment note: the blocks on the closing orders and EO 13811 rest on a cautious reading of the evidence rule, not on a missing source; a reviewer may reasonably route them differently.

## What took the time
Reading the views and rulings, the one-time NMB and held-text searches (EO 13409 family), and apply/batch-check (about 3 minutes apply, a few minutes check). Per order effort was small for blocked orders.

## batch-check (applied-v3)
claims_checked 3, strict pass 3, fail 0; actual checker all checks passed 3, unverified 0, fail 0; actionable failures none.

## Geddes
Lint ran in batch-check: 0 flags, 0 coverage gaps (applied-v3/GEDDES_LINT.json). No resolutions file needed.

## Full-packet files opened beyond the views
None (no READ.md, LOOKUPS.details.json or PACKET.json read directly; PACKET dossiers loaded once through batch.load_packet to inspect evidence records for EO 13420).

## Tool defects
None found. The checker reports custody-only PDFs as unverified rather than failed.
