# Producer report u103 (undecided route)
Start 2026-11-06T10:11:50Z; end 2026-11-06T10:12:39Z. Final applied dir: applied-v1.

## Outcomes
- EO:4029 blocked: only ProQuest archival replica held (acceptable_as_original=false, page check required); no held later event. Best reading: 10-year trust extension ran to 1934 on its own terms (operative no). STATUS_DECISION left blank.
- EO:4310 blocked: only ProQuest replica held. Best reading: EO 5690 (1931-08-20, OFR compilation text) returned the lands to the Philippine government (revoked, no). STATUS_DECISION blank.
- EO:4433 blocked: only ProQuest replica held; no held ending or CURRENT record (temporary Utah withdrawal pending legislation; status unknown). STATUS_DECISION blank.
- EO:3987, EO:4011 dispatch-blocked (unresolved, rows left as prepared): ORIGINAL not held (custody_record_only / not_held). Assessment rows written from views only.

## Time
All three: precheck showed no acceptable original, so no clause inventory built; time was reading views only.

## batch-check
5 members; 0 claims; outcomes blocked 3, unresolved 2; no actionable failures. Geddes: 0 flags, 0 coverage gaps; no GEDDES_RESOLUTIONS needed.

Files opened beyond views: none (read EO_5690 OFR text for 4310). Tool defects: none.

## Assessment supplement
Ran cruden.py number for all five (outputs in /tmp/claude-0/dorotheus-wave/work/u103/). Hits: 3987 -> EO 8307 (express revocation 1939-12-19, now read: operative no, revoked); 4310 -> EO 5690 (release of same area); 4011, 4029, 4433 -> no later held instrument. Rows rewritten with command type: 3987 standing personnel rule (no), 4011 one-time waiver (no), 4029 one-time trust extension to 1934 (no), 4310 land reservation released (no), 4433 temporary land withdrawal (unknown). Only ASSESSMENT.jsonl changed.
