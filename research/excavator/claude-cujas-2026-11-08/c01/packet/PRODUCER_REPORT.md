# Cujas c01 producer report

Start UTC: 2026-11-08T17:20:16Z   End UTC: 2026-11-08T17:25:00Z (approx.)

## Status: INCOMPLETE — actual claim checker could not run (tool/environment defect)
`kit.py apply` succeeded (applied-v1: 25 assembled_proposal, 91 source hashes checked). `kit.py batch-check` exited 2:
checker.py raised FileNotFoundError for research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv. The git index lists the file
(mode 100644) but it is absent from the working tree (git status shows nothing, so probably skip-worktree/sparse). Restoring it needs a
git-state change or a write outside my allowed paths, both forbidden, so I stopped. See applied-v1/CHECKER.log.
No claim has a checker result: 0 all_checks_passed, 0 failed, 25 unchecked. Geddes lint was not run (it follows a passing checker).
No order is blocked on its merits; none can be called submitted until the checker runs on applied-v1 (or on a fixed copy of the same decisions).

## Working-text comparison (all 25 members, plus the cited ending/later-event instruments)
Method: word-level difflib on normalised text of every held APP transcription (and its clause-draft copy) against the Photius GPO printing
(jobs/photius-gpo-volumes/output/texts/EO_<n>.txt, including printings of cited orders 7936, 7978, 8139, 8543, 8555, 8804, 8805, 8827, 8844, 8896, 8904, 8919, 8967, 8995, 9238),
plus the APP page record (DOCUMENTS/MIRROR_DOCUMENTS row with same sha256: heading number, date and text_sha256 agree for every text) and
PAGE_CHECKS.csv rows where present (all pass; number, dateline, signatory match).
Result: AGREEMENT for all. Differences are OCR noise (split words, page stamps, garbled year digits, truncated/dropped signature lines on some printings; the page check shows the signature on 7978 and 8844) and three transcription-side variants, none material:
- EO:8452: APP "sec. 715a" vs printing "section 715a" (U.S.C. parenthetical).
- EO:8525: APP "see. 715a" (typo) vs printing "sec. 715a".
- EO:9238 (cited by EO:8256 and EO:8497): APP operative sentence reads "Maurice C. Latte"; printing reads "Latta". The existing clause text already notes the APP spelling "Latte".
Change made: in decisions.csv, identity_confirmed, complete_text_confirmed and pages_confirmed set true on every mirror_transcription entry of each member's working_text (own order, clause-draft copy, cited other orders); approved=true. official_printing entries left unconfirmed (comparator only; PAGE_CHECKS rows are missing for many). pages_confirmed follows the APP page-record rule; I also compared each text with the official printing. Standing note untouched.

## Legal recheck
For all 25 orders the "ending <date>" in the operative sentence equals the clause effective_date (recital dates differ only where the text recites an earlier exemption, e.g. 8047, 8392, 8422, 8525). All are own-terms expiries of one-person time-limited exemptions. Later further-exemption orders (8543, 8497, 8904, 9238, 8525, 8827, 8844, 8555, 8805, 8896, 8804, 8967, 8995, 8919) are recorded as later events and do not alter the stated periods. No errors found; no rows changed beyond approval and confirmations. Note: EO:8047/8049/8050 clause rows have an empty mechanism field (left as reviewed); the checker should say whether that matters.

## Outcomes
All 25 remain `submit`; checker verification outstanding.

## Batch-check counts
Not available (checker crashed before loading claims).

## Geddes flags
Not run.

## Tool defects
Missing research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv in the working tree blocks claim-checker and therefore batch-check.
