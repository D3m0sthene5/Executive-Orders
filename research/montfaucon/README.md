# Montfaucon page-check wave

`checks/m001-*.jsonl` contains the first 50 independently reviewed official
printing locations. Records pin the immutable source fragment, held text,
rendered source pages, two distinct blind reviewer contexts, exact original
scan and each final verdict. The additional WPA page images and crosswalk
fields bind EO numbers to the GPO Indian Reservations 1912 book, which does
not print order numbers itself. The code consumer validates the original-page
images and source fragment pins; the WPA crosswalk image hashes are separate
auditable research evidence. No source record or codebook grade was edited.

`BATCHES.json`, `COST.md`, `CONTROL_INCIDENT.md`, and `GATE_M001.*` preserve
batch quality, resource limits and the stop/continue checkpoint. A pass here
only says the original printing was found complete in the cited source scope,
allowing noted OCR recognition noise. It does not certify a clean
transcription, human review, physical location, or legal status. The failed
rows name missing opening/closing pages and remain as negative outcomes.

The 193 Cujas Photius-stale identities are excluded from the worklist.
ProQuest restricted files were not read or modified.

`checks/m002-fr-modern-1937-1940.jsonl` adds 50 public GovInfo Federal
Register checks: 32 pass, 18 fail. `REPORT_M002.md` lists the failed spans,
the five blind adjudications, the contemporary GPO catalog identity crosswalk
for the unnumbered EO:7624 printing, and the sealed reviewer/control receipts
under `reviews/m002/`. `GATE_M002.*` and `COST.md` record the second 50-order
checkpoint and its unmeasured actual cost. The original source fragment and
held OCR files remain immutable.

`BATCHES.jsonl` is the append-only, one-row-per-50-order ledger requested for
this wave, with explicit pass/fail/unsure/control/cost cells. `BATCHES.json`
mirrors those counts for the current Bentham parser, which accepts a JSON
array or CSV but not JSONL. Its native wrapper also cannot gate the current
page-check action because the plan row has no measured rate; each direct gate
receipt declares its prior and planning cost proxy.
