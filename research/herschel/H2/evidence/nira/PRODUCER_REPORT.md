# Producer report: H2-w12 (nira packet)

Start UTC: 2026-11-05T23:52:12Z (first run; killed by OOM after reading, nothing written). Resumed run wrote sheets and ran apply/batch-check. End UTC: see final line.

## Outcomes
- EO:6249 (Lace Manufacturing Industry code approval): submit, NO. Both clauses (approval; Lace Industry Committee condition) are code-dependent; first end 1935-06-14, S.J. Res. 113 section 2. No own-terms or earlier end found in held texts; amendments to the code are later events, not ends. Savings: accrued (NIRA section 5).
- EO:6606E (amendment of the Electrotyping and Stereotyping code approval): submit, NO. Machine inventory (one fragment, chars 2542-3877) corrected to two clauses: the substituted condition/amendment (1333-3784) and the published statement (3912-5071). Both end 1935-06-14 by S.J. Res. 113. Savings: accrued.
- Submitted 2, blocked 0. Schechter recorded as validity characterization only.

## What took the time
- EO:6249: reading text and checking the lead/(1) inventory; short.
- EO:6606E: finding that the machine inventory was wrong and computing exact replacement spans.
- Apply about 100 s; batch-check about 6 min.

## Batch-check
applied-v1: 2 claims checked, strict pass 2, fail 0; actual checker all checks passed 2; no actionable failures.

## Geddes
0 flags (GEDDES_LINT.json written by batch-check); no resolutions needed.

## Full-packet files opened beyond views
No views existed. Opened READ.md (sections for both orders and shared texts), decisions.csv, clauses.csv, SOURCE_SUPPLEMENT.json, PREPARE.json. LOOKUPS.md was absent from the packet; I ran cruden.py searches for each order's name/number instead.

## Tool defects
- Packet had no views/ and no LOOKUPS.md.
- kit.py apply wrote applied-v1 (SUMMARY, claims, AUDIT all complete) but then logged "No such file: research/herschel/ATLAS/PROJECTION.json" (a post-step reading a folder I may not open); the outputs were complete and batch-check accepted them.
- An OOM kill ended the first run.
- Leftover waiting loops of mine may still be running; a pkill was denied.
2026-11-06T00:21:24Z
