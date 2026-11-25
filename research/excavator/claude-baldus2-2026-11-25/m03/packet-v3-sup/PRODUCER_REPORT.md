# Producer report, packet m03/packet-v3-sup (agent baldus)

Start 2026-11-25T19:51:58Z (first attempt on packet-v2 stopped at a "changed prior research" refusal; continued here after re-preparation). End 2026-11-25T20:19Z.

## Outcome: 1 submitted, 6 blocked

- EO 10919: submitted (applied-v1). Two clauses: board clause ends by completion of task 1961-06-20 (cover date line "JUNE 20, 1961"; letter page image reads June 20, 1961; EO 10926 of 1961-03-18, which extended the report time to that date, recorded as a later event); no-change sentence ends by its own terms 1961-07-20 inclusive (exclusive 1961-07-19). Formal disposition EO 12553 (1986-02-25) is a later event on both clauses. The search account names EO 10926 and EO 12553 as the instruments the later-events search found.
- EO 10904, 11006, 11008, 11011, 11027, 11040: blocked. In each case the held report states a presidential extension of the board's report time, which must be recorded as a dated later event, and no approval date or instrument is held.
  - 10904: held p6, two stipulated extensions approved by the President, last to 1961-03-11; missing the approval date(s).
  - 11006: p7, two extensions, last to 1962-05-01; missing their dates.
  - 11008: PDF page 33 prints the NMB letter with an approval line reading "MAR. 30, 1962" (new limit 1962-05-03) but that page is outside the held text layer (pages 1-8), so no source record can be declared; missing held text of that page.
  - 11011: p9, extension to 1962-05-01 approved; missing the date.
  - 11027: p7, extension to 1962-08-31; missing the date.
  - 11040: pp5-6, several extensions, last to 1963-03-05; missing the dates. Also the cover prints "EXECUTIVE ORDER 11041" (typographical error; EO 11041 is the Peace Corps order); the letter names EO 11040.
  For all six the report date and own-terms end are established (see ASSESSMENT.jsonl and the table in packet-v2/PRODUCER_REPORT.md); only the extension record is missing.

## Checks
batch-check: 7 members, 1 claim checked, strict pass 1, fail 0, actual checker all checks passed 1, blocked 6, actionable failures none. Geddes lint: 0 flags, 1 coverage gap (no resolution needed; GEDDES_LINT.json in applied-v1). No GEDDES_RESOLUTIONS.json written because there are no flags.

## Page labels
The DECL source label for the report spans reads "PDF pages 1-8 (front matter; transmittal letter)"; the 10919 spans lie on PDF pages 1-2, inside that range. I did not write DECL2.json; if the reviewers want the narrower label ("PDF pages 1-2") the coordinator should re-prepare with a DECL2.

## What took the time
10919: confirming EO 10926 and the report scan. The six blocks: reading each report for extensions.

## Files opened beyond the views
As in packet-v2/PRODUCER_REPORT.md; additionally packet-v3-sup dossier evidence via load_packet(check_sources=False), and jobs/olney-board-route/olney.py helpers (savings scan, cleanup lookup).

## Tool defects
None new. Earlier: source_supplement refused packet-v2 because other waves changed prior-research pins.
