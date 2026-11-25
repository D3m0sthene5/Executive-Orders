# Producer report, baldus2 m01 (packet-v2-sup2)

Start UTC: 2026-11-25T19:12:14Z
End UTC: 2026-11-25T19:49:02Z

## Outcome: 8 submitted, 0 blocked
Each order is one clause ended by its own no-change term (thirty days after the board's report), inclusive reading, exclusive reading stated; EO 12553 (1986-02-25) recorded as later formal disposition after the earlier cessation.
- EO:10010 end 1949-01-16 (report letter 1948-12-17; EO 10015 recorded as a later non-ending amendment).
- EO:10029 end 1949-04-09 (letter 1949-03-10).
- EO:10038 end 1949-10-19 (letter 1949-09-19).
- EO:10048 end 1949-05-29 (letter 1949-04-29); inventory corrected from four scopes (which swept in a Civil Service Commission notice) to one scope, chars 617-2201.
- EO:10130 end 1950-08-05 (letter 1950-07-06; letter misprints the order as 10138, report body names EO 10130).
- EO:10138 and EO:10139 end 1950-09-10 (one joint report, letter 1950-08-11).
- EO:10147 end 1950-10-13 (letter 1950-09-13).
Letter dates for 10010, 10038, 10048, 10138 and 10147 were checked on rendered page images (clean); the text layer garbles years or omits the line. End source for every order is a SUPPLEMENT excerpt of the held NMB report (cover and letter); for 10029 and 10130 the reviewed factual events are also cited as later events.

## Process notes
- First supplement packet (packet-v2-sup, DECL.json) was unusable: the assembler needs an end record with an actor, and I had set the actor label to the report. I re-prepared as packet-v2-sup2 with DECL2.json (actor = the order; two added excerpts for 10029 and 10130). packet-v2-sup holds an applied-v1 of all rejected claims; ignore it.
- source_supplement refused a DECL outside the repo; the coordinator moved it to m01/DECL.json.

## batch-check
8 claims checked, 8 strict pass, 0 fail; actual checker 8 all-checks-passed, 8 gate-passed, 0 mechanical fail or unverified. Geddes: 0 flags, 9 coverage gaps (no resolutions needed). GEDDES_LINT.json is in applied-v1.

## What took the time
10010: standstill reading and EO 10015. 10029/10130: factual-event routing. 10038: extension records. 10048: inventory correction. 10138/10139: confirming one joint report. 10147: letter date only in image. The actor-field rejection cost one re-prepare.

## Files opened beyond views
owner ruling 2026-11-08-haloander-decisions.md and the board_rule.txt it cites; PACKET.json via load_packet; report PDFs and source-ladder texts directly; packet-v2-sup2 evidence via load_packet.

## Tool defects
apply fails on prior-research drift from other waves; assembler needs an actor-bearing end record, and clause/override records carry none, so every own-terms end needs a SUPPLEMENT with actor label.
