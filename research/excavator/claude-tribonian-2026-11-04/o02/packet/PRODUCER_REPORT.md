# Producer report, o02 (Tribonian)

Start 2026-11-04T04:48:12Z. End: see the last line of this file.

## Outcomes (final applied dir: applied-v3)
- Submitted (23), all retirement exemptions that ended by their own stated period (end recorded inclusive, exclusive reading disclosed): 8011, 8019, 8024, 8025, 8032, 8041, 8046, 8047, 8048, 8049, 8050, 8058, 8060, 8070, 8073, 8074, 8075, 8094, 8096, 8097, 8105, 8106, 8132. Extension orders (8287, 8328, 8369, 8747, 8368, 8710, 8345, 8351, 8392, 8414, 8420) are later events, not ends. 8041 uses a ceiling reading (1940-02-29); 8094 rejects the 8293 disposition note in prose.
- Blocked (7): 8044 (no held end for section 3 or for section 1 outside EO 8743 coverage); 8051 (contingent end, termination of the 1935 Canada trade agreement, not dated by held sources); 8131 (House Resolution 26 and its expiry not held); 8139 (registered original is a live harvest); 8031 and 8069 (apply rejected: no registered evidence record with an acting instrument can carry the first-end quote; FR page image also not held); 8080 (held OCR line breaks fail the checker's verbatim-quote test).

## Time
Mostly spent on reading the 23 exemption texts and extension orders, building the 4 blocked-order analyses (8044, 8051, 8131), and two apply/batch-check cycles (about 1 minute each).

## Counts
apply-v1: 24 assembled, 2 rejected (8031, 8069), 4 blocked. v2 and v3 after blocking. batch-check on v3: 23 claims, strict pass 23, strict fail 0, actual checker mechanical fail 23, all for one cause: date_valid, matched_date "<Month D, YYYY>" inside the inherited Lachmann prior confirmation (working_text). I cannot edit it without invalidating the prior confirmation.

## Geddes
Lint on applied-v3: 23 claims, 0 defect flags, 0 coverage gaps; no resolutions file needed.

## Full-packet files opened beyond views
READ.md (parsed), decisions.csv, clauses.csv, plus held texts and EDGES.csv / MIRROR_DOCUMENTS.jsonl.

## Tool defects
Inherited Lachmann matched_date format fails the actual checker's date_valid check for every working-text claim. apply log is empty until completion.
2026-11-04T05:17:14Z
