# Producer report: dorotheus, yesprobe y01

Start 2026-11-06T10:19:52Z; end 2026-11-06T10:36Z (batch-check of applied-v4 finished 10:35:40Z).
Final applied directory: `applied-v4` (applied-v1 had a bad end_id for EO 10057 paragraph 3; applied-v2 assembled four claims but EO 9242A failed on a custody-only later-event source; applied-v3 had one Geddes flag).

## Outcomes
- EO:10104 submit (YES). Original plus bounded search; no later instrument, no own-terms end; ten operative scopes.
- EO:10057 submit (YES). Paragraphs 1 and 2 operative (36 U.S.C. 2111(b)(1)(A) recites the transfer as amended by EO 10087); paragraph 3 terminated by its own use windows (first end 1949-06-30, re-set by EO 10087, second window closed 1950-06-30).
- EO:10153 submit (YES). Inventory corrected to four section clauses. Section 1 operative as amended by EO 10649 (effective 1956-01-01) and EO 12683; section 2 terminated by EO 12683 deletion 1989-07-21; section 3 operative; section 4 spent 1950-09-01. Limit: 37 U.S.C. 204(b) not held; the Code and eCFR searches have 0 hits on this order.
- EO:9242A blocked. The dossier inventory (scopes 6 and 7) is another order's text; a corrected one-clause inventory assembled and passed the strict gate, but the only later-event source (EO 14085, 87 FR 60541, PDF sha256 4b5a964ac6f2641123bc30a9d67607264e2ebd577a285452a67f27ac99dc5bc6) is custody_record_only, which the checker flags (source_held:custody_record_only). Missing: held bytes of that PDF.
- EO:10111 blocked. The packet inventory is EO 10110's text (same Federal Register page 15 FR 909); the true order approves the CIA seal. Missing: a held current-law source that the approved seal remains official (50 U.S.C. 3507 text or equivalent) and a corrected inventory.
- EO:7993 blocked. PLO 2711 (1962-06-20, 27 FR 5987) revoked it in part (jobs/shepard-citations/output/PLO_TABLE.csv); its text is not held, and no current source shows what lands the refuge reservation covers. Missing: PLO 2711 text and a current refuge source.

## What took the time
- 10104: mostly reading the prior proposal in READ.md (an unavoidable large grep hit) and writing ten clause reasons.
- 10057: deciding paragraph 1 (performed transfer) and paragraph 3 (two windows, one amended after the first closed).
- 10153: inventory correction and tracing the two amendments and the deletion.
- 9242A: finding the wrong inventory, building a correction, then the custody-only block.
- 10111: finding the wrong order's text.
- 7993: finding PLO 2711.

## batch-check (applied-v4)
packet 6; claims checked 3; strict pass 3, fail 0; actual checker all checks passed 3; blocked 3; actionable failures 0; independent human certifications 0.

## Geddes
applied-v3: 1 flag (EO:10153 later_instrument_named_without_event_source), fixed in applied-v4 (0 flags). Two coverage gaps (EO:10057 literal name search) noted in GEDDES_RESOLUTIONS.json.

## Files opened beyond views
READ.md (a grep that printed a large prior-research line, about 15 KB, for EO 10104), LOOKUPS.details.json (one search), applied-v1/v2/v3 outputs. Repository sources: held order texts under jobs/fr-originals, jobs/app-executive-orders, jobs/theophilus-sources/output/texts/usc-t36-s2111.txt and cfr-t36-902.51.txt, jobs/shepard-citations/output/PLO_TABLE.csv, jobs/status-history/output/events/4c.jsonl (one line). Scratch: /tmp/claude-0/dorotheus-wave/work/y01/ (gen.py, v.py).

## Tool defects and notes
- Dossier inventories for EO 9242A and EO 10111 are taken from a neighbouring order on the same printed page (order boundary extraction error).
- A CLAUSES evidence id has no actor, so it cannot serve as end_id for an own-terms end (clause_N_first_end); ORIGINAL ids work.
- For operative orders ASSESSMENT first_cause is set to "unresolved" because no listed cause applies.
- original_pages_confirmed left false: I read the Federal Register text layers, not page images (requires_page_check is false for these records).
