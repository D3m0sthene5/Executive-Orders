# Producer report, packet o18 (Tribonian, 2026-11-04)

Start UTC 2026-11-04T06:29:09Z (the run paused for a usage limit and resumed); end UTC 2026-11-04T11:12:28Z.
Final applied directory: applied-v1 (no later version needed).

## Outcomes (30 orders: 14 submitted, 16 blocked)

Submitted, all as provisional NO with first end from the order's own terms or performance on issuance:
- Serial retirement exemptions ending on the stated "until" date, inclusive with the exclusive reading stated: EO 11642 (1973-02-28, later event EO 11704), 11653 (1975-05-19), 11657 (1974-04-01), 11675 (1976-08-10), 11704 (1974-02-28), 11757 (1974-12-31), 11791 (1975-12-31). For 11757 and 11791 the dossier clause began at character 0 (registry header), so an inventory correction (new scope id `#order`) starts at the order heading.
- One-day orders: EO 11693 (1972-12-28), 11700 (1973-01-25), 11696 (three clauses, 1973-01-19).
- EO 11741: section 3 "shall continue through" 1976-12-31 ends all three sections.
- Revocations performed on signing (no effective-date wording): EO 11681 (1972-08-21), 11773 (1974-03-21), 11794 (1974-07-11; second sentence treated as a rule of construction, alternative disclosed).

Blocked (precise gap in decisions.csv):
- "until interment" flag orders 11620, 11626, 11665: no held source dates the interment.
- "during the Ninety-second/Ninety-third Congress" tax-inspection orders 11624, 11631, 11655, 11656, 11711, 11719, 11720, 11722: no held text fixes the end of either Congress (held-text search for January 3, 1973 and 1975 found nothing relevant).
- EO 11786: no stated end and no held record of when the Judiciary Committee access ended.
- EO 11666: window closed before signing; section 48(a)(7) and Treasury lists not held.
- EO 11688: the Council's end is not held.
- EO 11766: ending statute (PL 94-455 lead) and EO 11464 text not held.
- EO 11778: dossier inventory is neighbouring Cost of Living Council text; amendment-versus-parent-end question with EO 11812 unresolved.

## What took the time
One line each: all submitted orders were quick (short texts, clean views); the time went to the Congress and interment orders (searching held texts for end dates, none found), EO 11778 (corrupted inventory), EO 11794 (second sentence), and the usage-limit pause. Apply took about 2 minutes; batch-check several minutes.

## Batch-check
14 claims checked, 14 strict pass, 0 fail, actual checker 14/14 all checks passed, 0 actionable failures, 0 human certifications.

## Geddes
1 flag (EO 11794, attributed_stock_phrase_absent / non_derogation). Disputed in applied-v1/GEDDES_RESOLUTIONS.json: the held body does contain a saving-style sentence, worded differently from the linter's stock phrase.

## Full-packet files opened beyond the views
PACKET.json (via batch.load_packet, to resolve shared objects for machine-search hit counts), decisions.csv, clauses.csv, LOOKUPS.md. Other repository sources: held FR texts for the 30 orders, EO 12553, EO 11399, EO 11812, status-history records for EO 11642/11688/11766, an earlier Erasmus decisions row (sheet format), and filed claims for field format.

## Tool defects
None blocking. Note: Cruden number search for EO 12553 returns table numbers as separate lines, so a per-number regex scan of the held EO 12553 text was used to confirm none of the 30 orders is listed there.
