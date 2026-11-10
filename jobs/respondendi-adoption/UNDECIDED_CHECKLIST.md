# Undecided-route producer and reviewer checklist

Give this page to every producer and both blind arms on the status-overlay (undecided) route, beside the route
prompt. Each item is a defect that cost an order in the Papinian (90 orders) or Haloander (30 orders) undecided
probes; the diagnosis is in `research/excavator/claude-respondendi-2026-11-10/REPORT.md`. Nothing here changes a kit
rule; where a kit rule blocks the order, say so in the blocker and still give the best-supported reading.

## Before you block, look where held evidence actually is

1. **U.S. Code notes.** Search `jobs/current-law/output/USC_EO_NOTES.jsonl` and `MENTIONS.csv` for the order's number
   (forms `Ex. Ord. No. N`, `E.O. N`, `Executive Order N`). A note that prints the order with no ending statement is
   current-status evidence; a note that says "revoked by" or "superseded by" is an ending lead. Never write "no held
   U.S. Code note names it" without that search (EO 12576, 10195 were rejected for it).
2. **Section texts.** `jobs/theophilus-sources/output/texts/` holds U.S. Code and CFR section texts (for example
   `cfr-t8-316.20.txt`, the IOIA list). Their `instrument_ids` in SOURCES.jsonl list orders that the section cites;
   they are not the identity of the text.
3. **Federal Register citers and later orders.** `jobs/selden-fr-citers/output/texts/`, `jobs/selden-fr-acting/`,
   `jobs/selden-statutes/`, `jobs/fr-originals/data/full_run/texts/EO_N.txt` for every later order the history or a
   cruden run names. Run `cruden.py number EO:N` and read each citer.
4. **The OFR 2025 disposition table** (held as a source-ladder queue text named for EO 14304, captured 2026-10-12)
   covers every 2025 order.
5. **Amendment-only orders.** An order that only amends a parent ends with the parent "as amended"
   (D-20261021-strike-and-insert; Pothier point P2): read the parent's own end and every later instrument acting on
   the parent. Record the text before and after.
6. **Large expressly revoked orders.** A named, dated, whole-order revocation settles the status even when
   clause-level first ends are unknown. A bound is not a block for the status: file the status and, if the lifecycle
   cannot be finished, publish the claim as `partial_research` with its exact open gaps.

## Inventory and citations (most lifecycle rejections)

7. Read the order's held text in full and check that every operative command is in a clause, including a section's
   lead-in sentence before its numbered items. OCR headings are often letter-spaced (`S e c . 2 .`) and the machine
   segmenter misses them; Carter-era decimal sections (`1-101`) are also missed.
8. Check every Federal Register page you cite against the printed page in the held text (a GovInfo PDF that bundles
   two orders reports the first order's page: EO 13294 is at 68 FR 15919, not 15917).
9. A later event's quote must be the operative section, not the heading or preamble.
10. Never state a count ("19 clauses") that the listed clauses do not match.

## Status-only filing

11. If the status is established and only clause-level gaps remain, fill STATUS_DECISION.json anyway and submit the
    claim as `partial_research` with the exact gaps in `unresolved_material_gaps`. Under the Respondendi standing
    rule (once the owner approves it) the status can be adopted while the lifecycle stays open for decided-order
    production. Do not leave a validated status decision unreviewed.

## For both blind arms

12. Review in the scope the manifest gives (`whole_case` or `partial_research`). In `partial_research` scope, uphold
    only if the status, the whole-order end and its source are right and the listed gaps are exactly the gaps.
13. A held text file is not a usable source if the checker grades it `custody_record_only`; check the unusable-source
    list before relying on it.
