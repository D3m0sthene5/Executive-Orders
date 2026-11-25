# Producer report, y21 packet-v2-held (baldus)

Start 2026-11-25T19:09:45Z. End 2026-11-25T19:18:30Z.

## Stopped at apply: "changed prior research"

`kit.py apply ... --write applied-v1` exited with "claim-kit: changed prior research; prepare a new version". I did not work around it. A read-only comparison (scratch script, nothing written to the repo) of `prior_research.collect` against the frozen packet shows one difference: an owner ruling file added after preparation, `research/readiness/owner_rulings/2026-11-25-adopt-upool1-9.md` (new input pin and a new `current_rulings` entry, state unqualified). No applied-vN directory exists, so batch-check and Geddes lint were not run (batch-check counts: none; Geddes flags: none). The packet needs a new prepare by the coordinator; decisions.csv, clauses.csv and ASSESSMENT.jsonl are ready for re-use, but decisions.csv carries the old dossier_sha256 values and will need them refreshed. Pre-edit copies of both sheets are in /home/claude/baldus-scr/work/y21/ (decisions.orig.csv, clauses.orig.csv); the fill script is fill.py there.

## Outcome per order (sheets as filled)

- EO:9158 submit, YES. One clause (whole order), operative, current basis CURRENT:EO:9158#0 (10 U.S.C. note, release point through 2026-10-09; disclosed gap to 2026-10-14). Later events: EO 9242-A (1942-09-11) and EO 14085 s.1 (2022-10-03), strike-and-insert with before/after. Catalog See note (Transfer Order 30, 13 FR 8163) reconciled as a cross-reference, not an ending.
- EO:9242A submit, YES, with inventory correction. The held 7 FR 7874 text opens with items 6 and 7 of the preceding EO 9242, so the draft inventory was another order's clauses; replaced by one clause at characters 1535-2383 of ORIGINAL:EO:9242A. Operative because its "in or with" wording survives EO 14085 (later event) in the current note. Reviewer note recorded that it is an amending clause.
- EO:9586 blocked. Page check required (requires_page_check true, location low); govinfo PDF bytes not held. Order is otherwise in force as the Presidential Medal of Freedom order (EO 10336, 11085 restating all sections, 11515 s.5).
- EO:9761 blocked. Missing: text and repeal or successor status of R.S. 1555 (5 U.S.C. 418); no CURRENT record.
- EO:9998 blocked. Missing: R.S. 1752 (22 U.S.C. 132) text and status; text and termination of Foreign Assistance Act of 1948 s.109(a), on which paragraph 3's proviso depends; no CURRENT record.

No order was found not in force on 2026-10-14. Assessment rows use first_cause "unresolved" for orders with no established cessation (the enumeration has no "none" value).

## Time per order

9158: reading 14085 and the current note, 5 minutes. 9242A: finding that the registered inventory belongs to a different order, 4 minutes. 9586: identifying the page-check block, 3 minutes. 9761 and 9998: statute-text search in held corpus, 3 minutes each.

## Full-packet files opened beyond the views

LOOKUPS.md, decisions.csv, clauses.csv, HELD_SOURCES.json (member list), SOURCE_SUPPLEMENT.json (head), LOOKUPS.details.json (key listing only), PACKET.json via batch.load_packet (dossier records for 9242A offsets and machine-search entries). No other packet folders were opened; the 9158 view's own prior_research section was read.

## Tool defects

Fingerprint check in `batch.load_packet` fails on any new owner ruling file, so a ruling added mid-wave invalidates an in-flight packet.
