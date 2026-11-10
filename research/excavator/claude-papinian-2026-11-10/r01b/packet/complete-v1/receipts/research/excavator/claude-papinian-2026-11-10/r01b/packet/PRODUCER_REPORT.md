# Producer report r01b (papinian)
Start 2026-11-10T03:23:46Z; end 2026-11-10T03:42:13Z. Final applied: applied-v3 (v1, v2 superseded).

## Outcomes
- EO:13900, EO:13965: submitted (status no). All 9 clauses end 12-24 of the closure year by own terms; OFR "See: EO 11582" is a cross-reference, not an end; four FR notices citing "EO 13900" miscite EO 13990.
- EO:8341, EO:8613, EO:8639: blocked by a tool limit. Legal reading complete (own-terms ends 1940-02-08; 1940-12-24 and 1940-12-18; 1941-01-15). The only usable ending source is the whole-file ORIGINAL record, whose quote carries neighbouring-document OCR numbers (Executive Order 83231, 85721, 74581) that fail the checker's order_exists test (seen in applied-v1); the CLAUSES record is rejected as an ending source by the gate (no actor, applied-v2).
- EO:10570: blocked. Needs committed bytes of NMB PEB-107 report (sha256 841bb65f...); text lead dates report 1954-11-20 (end about 1954-12-20); EO 12553 (1986) is the formal revocation.
- EO:14012: blocked. Dated one-time tasks (3(b),3(c),4(b),5(a),5(b),5(d)) have no held performance source; EO 14148 sec 2(w) 2025-01-20 is only a not-later-than bound; v1 cannot record it; inventory also needs correction (55 scopes with -dup2 duplicates).

## Time
10570: reading text and report lead. 14012: reading 12k-char text and EO 14148. 8341/8613/8639/13900/13965: drafting, then checker debugging (three apply/batch-check rounds).

## batch-check (v3)
7 members; 2 claims checked, 2 strict pass, 0 fail; actual checker 2/2 pass; blocked 5.
## Geddes
0 flags, 2 coverage gaps (GEDDES_LINT.json in applied-v3); no resolutions needed.
## Files opened beyond views
Original texts under jobs/fr-originals, EO_14148, EO_11582, PEB-107 text lead, jobs/later-events EDGES.csv, four selden-fr-citers texts, DISPATCH_CHECK.json, READ.md (head and grep, once). PACKET.json loaded via batch.load_packet.
## Tool defects
Checker order_exists scans OCR noise in whole-file ORIGINAL quotes; ORIGINAL span is whole file for pre-1994 orders. cruden search regex run was very slow (about 15 min).
