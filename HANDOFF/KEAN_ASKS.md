# Questions waiting for the owner

Generated from `jobs/kean/register/asks.jsonl` by `python3 -I jobs/kean/kean.py brief`; do not edit by hand.
Answer with `kean.py answer --id ID --answer TEXT`.

## A-20261106-1 (2026-11-06, claude-selden)

Does a statute that abolishes an order's body, or ends the emergency its term depends on, without naming the order, date the order's end? Default: no.

*Why:* Blocks EO 11270, 11599, 12304 in the Selden proof; recurs among the 1,814.

Sources: `research/selden/REPORT.md`

## A-20261106-dagron-nyu (2026-11-06, Claude)

NYU Film 709/Hein: lift the 2026-10-19 no-microfilm rule for this collection, and approve staged images under research/dagron/acquired?

*Why:* The manifest routes 5,875 orders to the reels; the 2026-10-19 owner decision forbids planning around a reel set, and no job may count the images until wired.

Sources: `research/dagron/README.md`

## A-20261106-pothier (2026-11-06, Claude)

Adopt each Pothier family doctrine (yes/no each); rule on amending orders and PLO tables? research/pothier/REPORT.md

*Why:* 2,139 status leads; no status change.

Sources: `research/pothier/REPORT.md`

## A-20261107-cap-mirror (2026-11-06, claude-encyclopedie)

Is the Hugging Face common-pile mirror of Harvard's Caselaw Access Project (22.6 GiB, third-party repackaging) acceptable as a case-text source for court-ended orders, given static.case.law disallows robots?

*Why:* The free citator route needs bulk case text; CourtListener's public-domain S3 bulk is the alternative.

Sources: `research/encyclopedie-campaign/LOG.md`

## A-20261107-loc-hein (2026-11-06, claude-encyclopedie)

The Library of Congress's free CFR, Federal Register and U.S. Code scans are HeinOnline-origin with a stated no-bulk-download term. Allow targeted, throttled pulls of a few hundred items (for example the U.S. Code EO tables 1934-1988 and 3 CFR 1940-1995), or wait for LOC's reply to the drafted request?

*Why:* These are the only free route found for pre-1994 U.S. Code tables and pre-1996 Title 3; you asked to avoid Hein.

Sources: `research/encyclopedie-campaign/LOG.md`

## A-20261107-lowande-email (2026-11-06, claude-encyclopedie)

Send research/bayle-prior-art/lowande-poznansky/REQUEST_EMAIL.md (corrected after independent check) to Kenneth Lowande asking for the order-level dataset and the 20 missing revocations and 65 misattributions? Confirm the bracketed identity line and the offer of corrections.

*Why:* Their error cases are counts only in the SI; they become controls only once the primary bytes are held.

Sources: `research/encyclopedie-campaign/LOG.md`

## A-20261107-mountweazel-plants-leak (2026-11-06, claude-encyclopedie)

Mountweazel's whole-repository check fails because research/excavator/dorotheus-sample-2026-11-06/PLANTS.csv names seeded item MW-C720-01 (red in the Valla pilot check). Allow the check to accept revealed plant keys under research/excavator/*/PLANTS.csv after reveal, or move revealed keys under jobs/mountweazel/fixtures?

*Why:* The check blocks every PR's Valla pilot; the plants are already revealed, so it is a check-policy question, not a live leak.

Sources: `research/encyclopedie-campaign/LOG.md`

## A-20261107-ocr-reference-rule (2026-11-06, claude-encyclopedie)

OCR pilot: exact GPO-and-engine agreement leaves 1 of 43 reference passages. Choose: (a) enlarge your hand-transcribed set, (b) agreement within a CER threshold (0.5% gives 8, 1% gives 18), or (c) GPO, Surya and Claude agree after lenient folding?

*Why:* The 'invents nothing on clean passages' arm of the adoption test cannot run with 1 passage.

Sources: `research/encyclopedie-campaign/LOG.md`

## A-20261107-tracker-thesis-fix (2026-11-06, claude-encyclopedie)

Apply TRACKER_FIX.md (about 80 lines) so the tracker fills formal_revocation_after_earlier_cessation from filed claims (32 yes, 487 no)? It is count-sensitive, so it would go in a count-changing PR for you to merge.

*Why:* The thesis measure is blank for all 14,998 orders because tracker.py reads only v2 claims.

Sources: `research/encyclopedie-campaign/LOG.md`
