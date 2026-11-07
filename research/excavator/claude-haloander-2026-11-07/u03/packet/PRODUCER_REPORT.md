# Producer report, u03 (undecided route)

Start 2026-11-07T21:16:46Z; end 2026-11-07T21:26:22Z.

## Outcomes
- EO:10733 submit (status no): EO 10925 sec. 403 revokes it, effective 30 days after 1961-03-06 = 1961-04-05.
- EO:9446 submit (no): EO 9975 para. 5 supersedes, 1948-07-07.
- EO:7814 submit (no): self-executing partial revocation performed 1938-02-15; dossier clause (chars 0-2585) was the neighbouring proclamation, so inventory corrected to chars 2990-3475; EO 8861 (1941-08-20) revoked the parent, kept as later event/bound.
- EO:8875 submit (no): SPAB clauses end 1942-01-16 (EO 9024), OPM clauses and para. 9 end 1942-01-24 (EO 9040); paras 8, 10, 11 self-executing 1941-08-28. Odd scope EO:8875#1941 is the rest of para. 1.
- EO:12214 blocked: no CURRENT: record, no record ending it; missing hash-pinned 50 U.S.C. 4603 note / 15 CFR 730 slice at 2026-10-14 and ECRA 2018 repeal text.
- EO:14238 blocked: no CURRENT:/ending record; missing a hash-pinned 2026 later-event/current-law record.
- EO:14348 blocked: same (TERM records are discretionary designation termination only).
- EO:2588 blocked: only Wikisource transcription held; official original missing.
- EO:341A blocked: Wikisource description of War Dept GO 145, not the order text.
- EO:5495 dispatch-blocked: row left as prepared (unresolved); custody_record_only original.
STATUS_DECISION.json filled for the four submitted members; all pass status_overlay._decision_errors (checked directly). Apply reports awaiting_status_review for them.

## Time notes
10733/9446: short; 7814: inventory correction; 8875: 12 clauses, reading 9024/9040; 12214/14238/14348/2588/341A: cruden number runs and held-text reading for assessment rows.

## Checks
apply: blocked 5, awaiting_status_review 4, unresolved 1. batch-check: 0 claims checked (undecided members assemble no claim), 0 actionable failures. Geddes: 0 flags, 0 coverage gaps; GEDDES_RESOLUTIONS.json empty.
Final applied dir: applied-v1.

## Beyond views
Opened packet undecided/EO_N/EVIDENCE.json for all members (evidence text, history observations); decisions.csv, clauses.csv, LOOKUPS.md. cruden.py number/search runs for 2588, 341A, 12214, 14238, 14348 and regex searches for 10733, 7814, 9446.

## Defects / caveats
Quotes are whitespace-normalised against held text (checked in code), not byte-for-byte across line breaks; soft-hyphen passages avoided. Undecided apply does not run assemble, so clause fields are not mechanically gated here.
