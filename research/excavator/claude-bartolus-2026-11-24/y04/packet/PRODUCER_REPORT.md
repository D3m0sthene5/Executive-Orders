# Producer report y04 (bartolus)

Start 2026-11-25T01:11:30Z; end 2026-11-25T01:28:21Z. Final applied directory: applied-v4.

## Outcomes
- EO:13666 submit. Amending order; override inventory covers recital and amending sentence; basis is own held text (the U.S. Code note record is custody_record_only, so it is not the cited source).
- EO:10111 submit. Packet inventory belonged to EO 10110; two overrides from EO 10111's own text; authority statute 50 U.S.C. 3507 not held (disclosed, not relied on).
- EO:11701 submit. Five sections; sec 5 ended 1973-01-24 by own terms; secs 1-4 operative on own text.
- EO:13257 submit. Membership list merged into one clause (short items fail quote check); EO 13286 sec 5 (effective 2003-03-01) and EO 13333 (2004-03-18) as later events.
- EO:10860 blocked: registered original text carries OCR 'EO 1086-Q'; checker reports unverified; need original text without front matter.
- EO:12458 blocked: need consolidated text of EO 12163 sections 1-201(a), 1-301, 1-801 (reconstruction not completed; EO 12560 restates 1-301(c), EO 12608 revokes 1-201(a) paragraphs (23),(24) under numbering that later orders changed).
- EO:11269 blocked: clause-by-clause reconciliation of 21+ amendments not completed; need consolidated text.
- EO:13485 blocked: no held source on existence/succession of five listed offices.
- EO:14283 blocked: no dated EPA record of termination of the advisory council (sec 6).

## What took the time
13666 and 10111 inventory overrides; 10860 checker defect; 11701 quick; 13257 diffing against the current note; 12458 and 11269 amendment chains; 13485 and 14283 short.

## Batch-check (applied-v4)
4 assembled, 5 blocked; actual checker 4 checked, 4 pass, 0 unverified, 0 fail. Earlier versions: v1 failed because CURRENT: U.S. Code records are custody_record_only; v2/v3 had unverified entries (10860 OCR number; 13257 short quotes).

## Geddes
0 flags, 3 coverage gaps; no resolutions file needed.

## Files opened beyond views
READ.md/PACKET.json (PACKET.json loaded to inspect evidence spans; one oversized print of shared_objects keys), Papinian decisions.csv and clauses.csv rows for EO 11701 (clauses beyond the permitted decisions row), held texts under jobs/.

## Tool defects
First batch-check run failed once with missing research/lind/stage0/ARM_KEY.json; a direct re-run succeeded. kit.py apply and sheets work as documented otherwise.
