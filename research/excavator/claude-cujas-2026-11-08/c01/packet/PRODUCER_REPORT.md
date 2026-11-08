# Cujas c01 producer report

Start UTC: 2026-11-08T17:20:16Z   End UTC: 2026-11-08T17:25:00Z (approx.)

## Status: COMPLETE (after the coordinator restored the census file)
Final applied dir: packet/applied-v1. Submitted 25, blocked 0. End UTC: 2026-11-08T17:27:36Z
batch-check: packet_members 25, claims_checked 25, strict_claim_pass 25, fail 0, actual checker all_checks_passed 25, mechanical_fail 0, gate_passed 25, actionable_failures none, no custody_record_only sources.
Geddes lint (applied-v1/GEDDES_LINT.json): 0 defect flags, 25 coverage gaps (advisory); GEDDES_RESOLUTIONS.json holds an empty resolutions list since there are no flags.
(Earlier crash, now resolved: missing IDENTITY_LAYER_PROJECTION_14972.csv.)

## Working-text comparison (all 25 members, plus the cited ending/later-event instruments)
Method: word-level difflib on normalised text of every held APP transcription (and its clause-draft copy) against the Photius GPO printing
(jobs/photius-gpo-volumes/output/texts/EO_<n>.txt, including printings of cited orders 7936, 7978, 8139, 8543, 8555, 8804, 8805, 8827, 8844, 8896, 8904, 8919, 8967, 8995, 9238),
plus the APP page record (DOCUMENTS/MIRROR_DOCUMENTS row with same sha256: heading number, date and text_sha256 agree for every text) and
PAGE_CHECKS.csv rows where present (all pass; number, dateline, signatory match).
Result: AGREEMENT for all. Differences are OCR noise (split words, page stamps, garbled year digits, truncated/dropped signature lines on some printings; the page check shows the signature on 7978 and 8844) and three transcription-side variants, none material:
- EO:8452: APP reads "sec. 715a" (char offset 549) vs printing "section 715a" (OCR text offset 1138), in the U.S.C. parenthetical.
- EO:8525: APP reads "see. 715a" (typo, offset 535) vs printing "sec. 715a" (offset 1116).
- EO:9238 (APP "Latte" at offset 704 vs printing "Latta", near offset 698-720; cited by EO:8256 and EO:8497): APP operative sentence reads "Maurice C. Latte"; printing reads "Latta". The existing clause text already notes the APP spelling "Latte".
Change made: in decisions.csv, identity_confirmed, complete_text_confirmed and pages_confirmed set true on every mirror_transcription entry of each member's working_text (own order, clause-draft copy, cited other orders); approved=true. official_printing entries left unconfirmed (comparator only; PAGE_CHECKS rows are missing for many). pages_confirmed follows the APP page-record rule; I also compared each text with the official printing. Standing note untouched.

## Legal recheck
For all 25 orders the "ending <date>" in the operative sentence equals the clause effective_date (recital dates differ only where the text recites an earlier exemption, e.g. 8047, 8392, 8422, 8525). All are own-terms expiries of one-person time-limited exemptions. Later further-exemption orders (8543, 8497, 8904, 9238, 8525, 8827, 8844, 8555, 8805, 8896, 8804, 8967, 8995, 8919) are recorded as later events and do not alter the stated periods. No errors found; no rows changed beyond approval and confirmations. Note: EO:8047/8049/8050 clause rows have an empty mechanism field (left as reviewed); the checker should say whether that matters.

## Outcomes
All 25 submit, checker-verified.

## Batch-check counts
See Status.

## Geddes flags
See Status.

## Tool defects
Missing census file (first run only), since restored.
