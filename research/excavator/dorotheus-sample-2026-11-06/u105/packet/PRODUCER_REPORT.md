# Producer report u105 (dorotheus)
Start 2026-11-06T10:13:16Z; end 2026-11-06T10:17:24Z.

## Outcomes
- EO:5700: submitted (awaiting_status_review, expected). Status NO: EO 11408 (signed 1968-04-25, 33 FR 6459) sec. 1-2 revokes EO 9 of 1873 and lists "5700, August 31, 1931". STATUS_DECISION filled (basis ACTOR_TEXT:EO:11408).
- EO:6002: blocked. No ACT/TERM/ACTOR_TEXT or CURRENT record held. Missing: text of Public Land Order 5658 (Mar. 5, 1979, 44 FR 14559), listed only in a BLM index as revoking EO 6002. STATUS_DECISION left blank.
- EO:5224, 5386, 6077: dispatch-blocked (original custody_record_only); decisions rows unchanged; assessment rows written from view. EO 6077 is revoked by EO 7327 (1936) effective on filing of a resurvey plat; filing date not held.

## Time
5700: working out whether EO 11408 reaches an amendatory order and checking for earlier ends. 6002: confirming no held ending (one grep of BLM index).

## Checks
apply: unresolved 3, awaiting_status_review 1, blocked 1. batch-check: 0 claims checked, 0 actionable failures. Geddes: 0 flags, no resolutions needed (applied-v1/GEDDES_LINT.json).

## Beyond views
EO_5700 DOSSIER/history json, jobs/status-history observation, EO_11408 texts, BLM index lines, decisions/clauses CSV and prior example sheet (claude-spent-probe) for field formats. No full PACKET.json/READ.md.

## Tool defects
None.

## Assessment supplement
Reran cruden number searches (scratch /tmp/claude-0/dorotheus-wave/work/u105/EO_{5224,5386,6077}.json). EO:5224: one-time personnel permission, no later instrument; force no. EO:5386: land modification of EO 4430, whose whole withdrawal EO 8861 (Aug. 20, 1941, APP mirror) revoked; force no, 5386 itself unrevoked. EO:6077: land withdrawal, revoked by EO 7327 effective on plat filing (date not held); force unknown. Only ASSESSMENT.jsonl changed.

## Reconfirmation
EO:5700: assembled and overlay-check passed (0 failures). The lifecycle sheet lacked a resolution for dossier conflict FULL_AND_PARTIAL_EVIDENCE_CONFLICT; I added one (EO 11408 reaches the whole of EO 5700 on either reading) in LIFECYCLE_DECISION.reconfirmed.json with approved true. That also cleared conflicts_with_later_source_search.
