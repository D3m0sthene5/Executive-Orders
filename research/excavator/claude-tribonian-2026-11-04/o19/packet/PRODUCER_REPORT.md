# Producer report, packet o19 (Tribonian, 2026-11-04)

Start UTC 2026-11-04T06:29:09Z. End UTC 2026-11-04T11:57:01Z (includes a usage-limit pause).
Final applied directory: applied-v3. Submitted 21, blocked 9.

## Outcomes
Submitted (21): EO 11796 (revoked in full by EO 11798, 1974-08-14), 11827 (superseded by EO 11948 effective 1976-12-31; item 2(4) rescinded by EO 11915 1976-05-10; section 4 own-terms 1975-01-05), 11824, 11826, 11847, 11869, 11909, 11924, 11928, 11942, 12000, 12006, 12011, 12016, 12031, 12037, 12056, 12077 (one-person retirement exemptions, each ended by its own until-date, inclusive with exclusive reading stated; later further-exemption orders recorded as later events), 11891 and 11923 (single-day commands), 12110 (inventory corrected to five clauses; superseded by EO 12258 effective 1980-12-31; sections 1-103 to 1-105 exhausted 1978-12-31).
Blocked (9): 11806 and 11820 (actual termination / congressional session record not held), 11856 (replacement of Civil Service Rule IX and current CFR not held), 11859 and 11900 (94th Congress end date not held), 11883 and 12010 (pay-period start dates for the supersession not held), 11996 and 12120 (interment dates not held).

## What took the time (one line each)
Retirement exemptions: reading texts and later-chain orders; the 13 with FR-original text needed a first-end source from the order's own held TERM record. 11796: read 11798, 11810, 11940, 11978 to resolve the full/partial conflict. 11827: 14 establishing-order searches plus 11915 and 11948. 12110: inventory correction. Blocked orders: confirming the missing source was truly not held.

## Batch-check
apply v1: 8 assembled, 13 rejected (unknown namier search id on non-namier orders, end ids pointing at CLAUSES rather than ORIGINAL or an own-text TERM from a lead text); v2 and v3 21 assembled. batch-check on v3: 21 of 21 strict pass, actual claim-checker 21 passed, 0 failures.

## Geddes
8 flags (EO 11796: 2, EO 11827: 6), all unaddressed_citing_instrument for orders revoking other instruments (EO 11533 or committees' establishing orders). All disputed in applied-v3/GEDDES_RESOLUTIONS.json. 41 coverage gaps, not resolved.

## Full-packet files opened beyond the views
PACKET.json via load_packet (check_sources=False), LOOKUPS.md, clauses.csv and decisions.csv; kit.py view for EO 11824 only. No READ.md or LOOKUPS.details.json. Other repository files read: held order texts (FR originals for 11798, 11810, 11940, 11978, 11915, 11948, 11941, 12087, 12258), Cruden searches, a prior namier batch's sheets as a format example (no research content reused).

## Tool defects
Cruden search output is large; no defects in apply or batch-check. A prior-batch worked example was used only for the sheet format.
