# Producer report: dorotheus, packet u201 (undecided route)

Start 2026-11-06T10:14:17Z; end 2026-11-06T10:23Z.

## Outcomes
- EO:7628: sheet filled; apply reported `awaiting_status_review` (expected). Proposed status NO: superseded by EO 7719 (signed 1937-10-08), which includes the same 79.50-acre tract in the Ouachita National Forest. Inventory corrected: the registered clause extent (764-1178) was EO 7627's text; the real order is characters 1372-2273 of the original file. STATUS_DECISION.json filled and passes `_decision_errors` (no errors).
- EO:7687: blocked. No ending (ACT/TERM/ACTOR_TEXT) or CURRENT record; missing a held later instrument/statute text on the 1930 Act extension to Panama employees.
- EO:8120: blocked. No real ending or CURRENT record (its TERM records quote the order's own reservation clause); missing a revocation/public land order or refuge record.
- EO:9235: blocked. Only possible end is the own term (section 4, "so long as Title I of the First War Powers Act, 1941, remains in force"); missing the statute text and the later act ending Title I with its date. EO 9425 is a cross-reference only.
- EO:9316: blocked. No ending or CURRENT record; missing EO 8942 text and the instrument/statute ending the six-month report duty under 55 Stat. 742.
- EO:7700A: dispatch-blocked (ORIGINAL and CLAUSES custody_record_only); left unresolved; assessment row from the view alone.

## What took the time
7628: finding that the registered clause was 7627's text, and the interleaved FR columns around the EO 7719 sentence. 7687/8120/9316: confirming no ending/CURRENT record. 9235: checking whether Title I FWPA's end is held (it is not).

## Counts
apply: awaiting_status_review 1, blocked 4, unresolved 1. batch-check: claims_checked 0 (no submit-ready claims; 7628 awaits status review), actionable_failures [].

## Geddes
0 flags, 0 coverage gaps; GEDDES_RESOLUTIONS.json is empty.

## Files opened beyond views
undecided/EO_*/EVIDENCE.json and DOSSIER.json (read-only, for observations and evidence text); LOOKUPS.md; decisions.csv/clauses.csv. cruden number run once per assigned order (scratch /tmp/claude-0/dorotheus-wave/work/u201/). Repository sources: jobs/fr-originals texts for 7628, 7719, 9235, 9425; USC_EO_NOTES.jsonl grep. Other-batch examples read for sheet format: claude-erasmus r2 packet, claude-nira PRODUCER_BRIEF.

## Tool defects
None. Note: the FR text layer for EO 7719 interleaves neighbouring columns; quotes were limited to exact single-line fragments.

## Reconfirmation
EO:7628: reconfirmed (approved true, no other change); overlay-assemble and overlay-check passed (1 checked, 0 failures). Working dossier status no matches the analysis: terminated by EO 7719 on 1937-10-08.
