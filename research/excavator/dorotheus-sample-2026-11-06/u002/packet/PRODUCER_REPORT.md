# Producer report, u002 (dorotheus)
Start 2026-11-06T10:11:50Z; end 2026-11-06T10:13:40Z.

## Outcomes
- EO:454 blocked: only a ProQuest replica is held (not acceptable as original, page check pending); no ending or CURRENT record. Missing: official original page image and a source for the later disposition of the Kingfisher Government Acre.
- EO:527 blocked: original acceptable, but no held source ends the whole order (EO 725 only modifies it); no CURRENT record; later statute or order abolishing the Commission organization not held; whole-order boundary unverified.
- EO:538 blocked: held Wikisource page carries only a State Department description, not the order text; EO 5110 (1929), named in the page note, is not held.
- EO:541 blocked: only a Wikisource transcription held; no ending or CURRENT record; no source showing the Harvey transfer.
- EO:UNN:LORD1944:p1:1863-03-10: dispatch-blocked (mandatory source not held); assessment row only; outcome left unresolved.

STATUS_DECISION.json files left blank for all, as the brief requires for blocks.

## Time
Reading the views and held texts (527 and 725) took most of the time; apply and batch-check ran in seconds.

## Batch-check
5 members, 0 claims checked, 4 blocked, 1 unresolved, 0 actionable failures. Geddes: 0 flags, 0 coverage gaps; no resolutions needed. Final applied dir: applied-v1.

## Files opened beyond views
jobs/isthmian-canal-1911/output/texts/EO_725.txt; jobs/wikisource-texts/output/texts/EO_538.txt and EO_541.txt (heads); cruden.py searches. I did not read the prescribed rulings, PRODUCTION_ROUTE.md, CLAIM_SCHEMA.md or BATCH.md sections, because every order blocked on a missing source.

## Tool defects
None.

## Assessment supplement
Ran cruden.py number for EO:454, 527, 538, 541 (outputs in /tmp/claude-0/dorotheus-wave/work/u002/). Found no held later instrument that revokes any of them. Hits were only Wikisource neighbour links, EO 725 (modifies 527), EO 496 (amended by 538), and unrelated Public Land Order and Bureau Order 538/541 citations. Rows rewritten with the command type for each order: 454 one-time land transfer, unknown; 527 standing body rules modified by EO 725, unknown; 538 standing fee rule, "no" on the Wikisource note alone (EO 5110 not held); 541 one-time personnel authorization, unknown. The LORD1944 row is unchanged (no text held). decisions.csv, clauses.csv, STATUS_DECISION.json and applied-v1 were not touched.
