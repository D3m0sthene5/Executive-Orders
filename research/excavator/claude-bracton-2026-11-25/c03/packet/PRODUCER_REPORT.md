# Producer report, packet c03 (route: correction)

Start 2026-11-25T09:07:33Z; end 2026-11-25T09:12:51Z. Final applied directory: applied-v1.

## Outcomes
- EO:10415 blocked. Only a bound is held: formally revoked by EO 12553 (1986-02-25), a cleanup revocation without its own reason as a first end. Missing: text of EO 9949 (parent one-person order, not held) and any held source on whether the employee's service ended by 1953-12-31, whether a right vested, or whether EO 10804 (1959) reached him.
- EO:10440 blocked. Sec. 1 clauses end 1955-01-23 (EO 10577 sec. 301, effective under sec. 401; the 10463 and 9973 amendments are later events under the strike-and-insert ruling). Sec. 2 ("until the Commission has taken action") has no established completion date: the Commission's Part 6 document of 1953-04-14 (18 FR 2069) is held only through PDF page 3, before the schedule listings, and its only packet evidence id (ACTOR_TEXT:EO:10445) would record the wrong actor. Missing: held bytes of that Part 6 document or another source dating completion.
- EO:10449 blocked. Board never constituted; parties agreed 1953-04-26 per NMB PEB-104, which is custody_record_only. Bound: EO 12553 (1986-02-25).
- EO:10509, EO:10511, EO:10630, EO:10635 blocked. Own-terms end is thirty days after the board's report; the report dates rest on NMB PEB-105, -106, -112, -113 PDFs (custody_record_only). Bound: EO 12553 (1986-02-25).
- EO:10494, EO:10622 dispatch-blocked (custody_record_only mandatory sources); decisions left as prepared (unresolved); assessment rows written from the views.

## Time
10415: confirmed the parent EO 9949 is not held and read EO 10804 sec. 2. 10440: read the order text, EO 10577 sec. 301/401, and the 10445 page with the Commission document; longest. Boards: confirmed from source-ladder records that the report PDFs are custody-only.

## Batch-check
Submitted 0, blocked 7, unresolved 2 (dispatch-blocked). Claims checked 0; actionable failures 0.

## Geddes
Lint ran in batch-check: 0 flags, 0 coverage gaps. No GEDDES_RESOLUTIONS.json needed.

## Files opened beyond the views
research/stage19 and rulings as instructed; LOOKUPS.md (read once, truncated lines); jobs/claim-kit/batch.py and assemble.py (field requirements); jobs/source-ladder/output/SOURCES.jsonl (custody status of the NMB PDFs); order texts jobs/fr-originals/.../EO_10415, EO_10440, EO_10445, EO_10577, EO_10804; cruden.py searches (EO 9949 number, reclassification phrases). No PACKET.json, READ.md or LOOKUPS.details.json.

## Tool defects
None blocking. The decisions.csv working_text rows for 10440 list APP mirror texts for EO 10577 as unconfirmed; unused because blocked.
