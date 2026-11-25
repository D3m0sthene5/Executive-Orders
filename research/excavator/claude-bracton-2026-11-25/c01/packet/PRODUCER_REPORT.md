# Producer report: c01 (route: correction)

Start 2026-11-25T09:07:33Z; end 2026-11-25T09:16:42Z. Final applied directory: `applied-v4` (applied-v1 and v3 assembled the EO:10029 proposal and failed the selected-source custody check; v2 is the earlier all-blocked version).

## Outcome per order

All nine members are blocked or unresolved; no claim was submitted. Each blocked order is `blocked` in decisions.csv with the gap in `unresolved_material_gaps`.

- EO:10010, 10032, 10038, 10048, 10050, 10056, 10067: blocked. The open step is the first end. Each order's last-running command is the standstill that runs until thirty days after the board made its report to the President, so the first end needs the report date from a source whose bytes are held. The only held texts that date the reports are the National Mediation Board report PDFs (PEB-066, 068, 070, 072, 073, 075, 076; hashes in each decisions.csv row). Their text is held but their bytes are not, so they are custody_record_only and cannot be an ending source. Executive Order 12553 (1986-02-25) lists every one of these orders by number and gives only a not-later-than bound; under the owner ruling of 2026-10-28 point 3 it is not a first end without its own reason. Missing: retained bytes of the named PEB report, or a reviewed factual-event record dating the board's report or transmittal. EO:10010 also has EO 10015 (1948-11-05, amends the attached lists only), recorded as a later event in the earlier claim and not an end. EO:10048 additionally has a bad prepared inventory (four clauses, three of them Civil Service Commission rule text and contents pages printed on the same Federal Register page); a submission would need a one-clause inventory correction.
- EO:10029: blocked at the last step. It is the only member with a reviewed factual event (the board's transmittal letter dated 1949-03-10), which supports an own-terms end on 1949-04-09 (thirty days after the letter). I drafted and assembled that claim (applied-v1 shows `assembled_proposal`), but apply's selected-source check returned `not_held` for the later-event source: the retained PEB-067-Report.pdf (sha256 afc5c581e901d6a22180aebbd1dcba9cf853d1b4301b339fc05a647b158bbee9) lives under `jobs/astra-source-retention/output/`, and that directory is not present in this working tree. Missing: that PDF (and selected-pages text) materialised with custody registered. A second limit: the held sources date the letter, not its receipt at the White House; the draft counts the report as made when submitted and says so. The draft sheet is left in the EO:10029 rows of decisions.csv and clauses.csv for reuse (its outcome is `blocked`).
- EO:10051: dispatch-blocked (CLAUSES:EO:10051#whole and ORIGINAL:EO:10051 custody_record_only); row left as prepared (`unresolved`); assessment row written from the view and the held NMB report text lead.

## What took the time (one line each)

- 10010: confirmed the report date is held only as a lead and that EO 10015 is an amendment of the lists.
- 10029: found the one reviewed factual event; drafted the claim; the custody check blocked it.
- 10032, 10038, 10050, 10056, 10067: confirmed the same custody gap; no other held source dates the report (corpus search for the board and carrier names found no non-NMB report text).
- 10048: found the mis-split inventory.
- 10051: assessment row only.

## batch-check (applied-v4)

9 packet members; 0 claims checked; 0 strict pass, 0 strict fail; outcomes blocked 8, unresolved 1; 0 actionable failures; 0 independent human certifications.

## Geddes

Lint run on applied-v4: 0 flags, 0 coverage gaps. GEDDES_RESOLUTIONS.json holds an empty resolutions list.

## Files opened beyond the views

- jobs/claim-kit/BATCH.md (two sections), assemble.py, factual_events.py and AGENT_PROTOCOL.md (bounded reads) to see how a factual event is cited and why a custody failure blocks.
- PACKET.json, loaded once in a script, only for EO:10029's factual-event objects (text, review and question), and for the machine-search entry of EO:10029.
- jobs/source-ladder/output/SOURCES.jsonl (report-date leads and hashes), jobs/fr-originals/data/full_run/texts/EO_12553.txt (table entries for each order, no saving clause), jobs/fr-originals/data/full_run/texts/EO_10029.txt (head and tail), research/readiness/claims/claude-2026-10-31-apollo-g03.jsonl (the prior EO:10029 claim).
- A corpus search with cruden.py for the board and carrier names (output in /home/claude/bracton-scr/work/c01/cruden1.txt).
- No LOOKUPS.details.json, READ.md or other packet folders.

## Tool defects and notes

- `kit.py view` was not used. The task text says the NMB report PDFs are not held; the dispatch check did not flag the EO:10029 factual-event source because it only checks the original and inventory ids, so that blocker appears only at apply time.
- The held NMB text for EO:10038 (PEB-070) shows a title-page date of September 19, 1949 against an appointment of February 15, 1949, which is an unusually long interval for a thirty-day board; it was not investigated because the order is blocked.
