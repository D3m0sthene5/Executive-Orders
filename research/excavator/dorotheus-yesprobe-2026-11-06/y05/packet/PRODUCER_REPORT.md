# Producer report: y05 (dorotheus)
Start 2026-11-06T10:23:38Z; end 2026-11-06T10:35:09Z. Final applied dir: applied-v4 (v1-v3 superseded: v1 unknown evidence ids for new scopes; v2 passed but 14085 FR source custody_record_only; v3 APP mirror for 14085 rejected by working-text checks).

## Outcomes
- EO:14131: **submit**, status yes. 13 clauses, all operative, original_plus_bounded_search through 2026-10-14. No later events held. Batch-check and actual checker pass.
- EO:13830: **blocked**. Full yes analysis was prepared (inventory corrected: added promulgating paragraph and Sec. 8(e), re-cut Secs. 5(a), 5(d)(iv)), but EO 14085 (87 FR 60541; https://www.govinfo.gov/content/pkg/FR-2022-10-06/pdf/2022-21911.pdf, sha256 4b5a964ac6f2...) which amends the lead and Secs. 1, 2, 3, 4(a), 4(c), 5(a), 6(a) is held only as custody_record_only; the APP mirror fails working-text checks (official copy available, page confirmation). Missing: held bytes of that FR PDF.
- EO:13848, 14024, 14373: dispatch-blocked (custody_record_only originals); assessment rows only.

## Time
13830: inventory correction and 14085 source attempts. 14131: simple amendment order, little time.

## Batch-check (applied-v4)
5 members; 1 claim checked, strict pass 1, fail 0; actual checker 1/1 passed; blocked 1, unresolved 3, assembled 1.

## Geddes
0 defect flags; 2 coverage gaps (EO 13286 as earlier parent context, EO:14131 Secs. 1-2) resolved as disputed in applied-v4/GEDDES_RESOLUTIONS.json.

## Beyond views
LOOKUPS.details.json (bounded, to check hits; no hit detail present), decisions.csv/clauses.csv, jobs/fr-originals texts for EO 13830, 14131, 14085 (read by range); cruden.py searches. No other packets opened.

## Defects
Mechanical-task pointer for 10 U.S.C. notes has no located text slice, so current-law hits were unreadable. Overridden inventory scopes get no CLAUSES:* evidence id, so new scopes need ORIGINAL:EO:13830 as basis. actor-texts/EO_13286.json named by the view is absent from the packet.
