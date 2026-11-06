# Producer report u104 (dorotheus)
Start 2026-11-06T10:11:53Z; end 2026-11-06T10:13:24Z

## Outcomes
- EO:4533 blocked: ORIGINAL is a ProQuest replica scan (acceptable_as_original=false, no page check); no ending/CURRENT record. Reading: operative no (self-executing opening completed), unrevoked.
- EO:4624 blocked: replica-scan original only; also each township revoked by EO 5506 (1930-12-08), EO 5943 (1932-10-29), EO 7175 (1935-09-06, effective on resurvey plat filing); missing the plat-filing date(s) and an acceptable original.
- EO:4975 blocked: replica-scan original only; superseded by EO 5945 (1932-11-03, quoted in held text), but status proposal impossible without an acceptable original.
- EO:4928, EO:5187: dispatch-blocked, rows left as prepared (unresolved); assessment rows from views only.
STATUS_DECISION.json files left blank for all.

## Time
Reading views and checking EO 7175 text; no clause inventories built (precheck rule).

## Batch-check
5 members, 0 claims, blocked 3, unresolved 2, actionable failures 0. Geddes: 0 flags, 0 coverage gaps; no resolutions needed.

## Other
Beyond views: read EO_7175 texts, the empty-status-history ruling (head), decisions.csv. Did not read the other rulings in full. Tool defects: none.

## Assessment supplement
Ran cruden.py number for EO:4533, 4624, 4975, 4928, 5187 (outputs in /tmp/claude-0/dorotheus-wave/work/u104/); read held later instruments EO 5506, 5943, 7175, 5945. Rewrote all five ASSESSMENT.jsonl rows: 4533 no (spent one-time land order); 4624 unknown (50N/51N revocation awaits plat filing; 48N/49N revoked); 4975 no (superseded by EO 5945, 1932-11-03); 4928 and 5187 unknown (no later instrument held). decisions.csv, clauses.csv, STATUS_DECISION.json and applied-v1 untouched.
