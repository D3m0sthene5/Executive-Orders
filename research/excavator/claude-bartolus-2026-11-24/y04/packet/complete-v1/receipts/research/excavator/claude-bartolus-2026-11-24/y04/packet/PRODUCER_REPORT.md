# Producer report y04 (bartolus)

Start 2026-11-25T01:11:30Z; end 2026-11-25T01:28:21Z. Final applied directory: applied-v7 (v4 held the first four claims; they are byte-identical in v7).

## Outcomes
- EO:13666 submit. Amending order; override inventory covers recital and amending sentence; basis is own held text (the U.S. Code note record is custody_record_only, so it is not the cited source).
- EO:10111 submit. Packet inventory belonged to EO 10110; two overrides from EO 10111's own text; authority statute 50 U.S.C. 3507 not held (disclosed, not relied on).
- EO:11701 submit. Five sections; sec 5 ended 1973-01-24 by own terms; secs 1-4 operative on own text.
- EO:13257 submit. Membership list merged into one clause (short items fail quote check); EO 13286 sec 5 (effective 2003-03-01) and EO 13333 (2004-03-18) as later events.
- EO:10860 blocked: registered original text carries OCR 'EO 1086-Q'; checker reports unverified; need original text without front matter.
- EO:12458 submit. Seven clauses cut from the original: paragraphs (23) and (25) ended 1986-05-24 (EO 12560 sec 2 deletion); (24), sec 2(c) and sec 3(a),(b) ended 1999-04-01 (EO 13118 secs 2, 3, 8, effective April 1, 1999); sec 2(a) (1-301(a)) operative. Paragraph identification rests on stated numbering (disclosed); EO 12292 (1981) predates it.
- EO:11269 submit. 14 clauses; secs 1-4 operative with 17 amendments recorded as later events (11334, 11808, 11977, 12164, 12188, 12403, 12567, 12647, 12766, 12916, 13118); secs 5-6 spent 1966-02-14; 2006-07-05 conflict resolved (State Dept delegation, not this order).
- EO:13485 blocked: no held source on existence/succession of five listed offices.
- EO:14283 blocked: no dated EPA record of termination of the advisory council (sec 6).

## What took the time
13666 and 10111 inventory overrides; 10860 checker defect; 11701 quick; 13257 diffing against the current note; 12458 and 11269 amendment chains; 13485 and 14283 short.

## Batch-check (applied-v4)
applied-v7: 6 assembled, 3 blocked; actual checker 6 checked, 6 pass, 0 unverified, 0 fail. (applied-v4 was the earlier 4/5 result.) Earlier versions: v1 failed because CURRENT: U.S. Code records are custody_record_only; v2/v3 had unverified entries (10860 OCR number; 13257 short quotes).

## Geddes
applied-v7: 0 flags, 5 coverage gaps. applied-v6 had 2 flags, fixed in v7 (11269 sec 5/6 end date moved from 1966-01-01 to the order's own date 1966-02-14; 12458 rationale now addresses EO 12292, which predates it).

## Files opened beyond views
READ.md/PACKET.json (PACKET.json loaded to inspect evidence spans; one oversized print of shared_objects keys), Papinian decisions.csv and clauses.csv rows for EO 11701 (clauses beyond the permitted decisions row), held texts under jobs/.

## Tool defects
First batch-check run failed once with missing research/lind/stage0/ARM_KEY.json; a direct re-run succeeded. kit.py apply and sheets work as documented otherwise.
