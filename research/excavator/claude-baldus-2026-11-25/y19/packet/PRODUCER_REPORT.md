# Producer report, y19 (baldus)

Start UTC 2026-11-25T17:11:15Z. End UTC 2026-11-25T17:22:30Z.

## Outcome: stopped, no applied directory

`kit.py apply` (run once, with decisions.csv and clauses.csv filled) exited with "claim-kit: changed Valla review context; prepare a new version" before creating applied-v1. Per the brief I stopped and did not work around it. No claim was assembled, batch-check and Geddes lint were not run, nothing was submitted.

## Sheets as filled (not applied)
decisions.csv and clauses.csv hold the intended decisions (backups of the originals: /home/claude/baldus-scr/work/y19/decisions.orig.csv and clauses.orig.csv; generator: /home/claude/baldus-scr/work/y19/gen.py, rerunnable).
- Intended submit (YES, all clauses operative at 2026-10-14): EO:14064 (20 clauses), EO:14065 (37), EO:14066 (19), EO:14068 (inventory corrected to 16), EO:14071 (18), EO:14088 (18), EO:14114 (inventory corrected to 11), EO:14131 (13). Emergency-dependent orders cite the held NEA continuation notices through 2025-11-20 (14088) or 2026-01-20/02-18/03-24 (others).
- Blocked: EO:14144. Missing: held evidence of performance of dated commands (NIST/CISA/NSA/OMB deadlines Aug-Dec 2025) as amended by EO 14306, and a reviewed inventory against the amended text.
- No held evidence showed any of the nine orders not in force on 2026-10-14.

## Points to know on re-run
- EO 14064: section 1(b) transfer performance is not shown by any held source; carried as operative with disclosure (reviewer may prefer a block). The 2025-01-15 notice as held prints "beyond February 11, 2024" (apparent misprint); the 2026 notice governs the cutoff.
- EO 14068/14114: packet inventory was a single preamble "whole" clause; corrected via inventory overrides.
- EO 14131 current basis is the USC note record, edition current through 2026-10-09; checked_through set to 2026-10-14 (may be questioned by the checker).
- OFR note on EO 14068 prints EO 14114 as December 12, 2023; held order text is signed December 22, 2023.

## Time per order
Reading and scripting dominated; EO 14144 and the inventory corrections of 14068/14114 took longest.

## Batch-check / Geddes
Not run (apply refused). Full-packet files opened beyond views: PACKET.json (evidence records for EO:14064/14068/14071/14131), LOOKUPS.md, LOOKUPS.details.json (structure only), decisions.csv, clauses.csv. Tool defects: none beyond the apply refusal; repo-wide grep -r timed out once (stopped).
