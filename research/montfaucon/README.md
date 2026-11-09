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

`checks/m003-fr-modern-1941-1951.jsonl` adds 50 further public GovInfo
Federal Register checks: 36 pass, 14 fail. `REPORT_M003.md` lists each failed
span, including two prescribed manuals where the held excerpt stops well
before the publication's terminal page. Both blind readers caught all three
controls; their two completeness disagreements received a separate blind
adjudication. The sealed reviews are under `reviews/m003/`; `GATE_M003.*` and
`COST.md` preserve the third checkpoint and unknown actual cash cost.

`checks/m004-fr-modern-1951-1967.jsonl` adds 50 further public GovInfo
Federal Register checks: 42 pass, 8 fail. `REPORT_M004.md` names each wrong
or truncated span and four plausible OCR substitutions resolved by a fresh
blind third reader. Both controlled readers caught all three challenges.
Their sealed reviews, controls and adjudications are under `reviews/m004/`;
`GATE_M004.*` and `COST.md` preserve the fourth checkpoint and unknown
actual cash cost.

`checks/m005-fr-modern-1968-1988.jsonl` adds 50 public GovInfo Federal
Register checks: 35 pass, 10 fail, 5 unsure. `REPORT_M005.md` identifies the
truncated annexes and manuals, wrong printed pinpoint, and uncertified dense
tables. Both controlled readers caught all three challenges; their two
disagreements received independent blind adjudication. Sealed evidence is
under `reviews/m005/`. `GATE_M005.*` and `COST.md` preserve the fifth
checkpoint and unknown actual spend.

`checks/m006-fr-modern-1937-1994.jsonl` adds 50 public GovInfo Federal
Register checks: 26 pass, 18 fail, 6 unsure. `REPORT_M006.md` identifies
wrong issue and printed page citations, missing order spans and uncertified
tables. Both blind readers caught all three controls; two verdict disagreements
received a fresh third reading. Sealed evidence is under `reviews/m006/`;
`GATE_M006.*` and `COST.md` preserve the sixth checkpoint and unknown
actual spend.

`checks/m007-photius-free-panama.jsonl` records 50 public GPO Panama-volume
lead checks: 0 pass, 49 fail on wrong cited pages, 1 blocked for missing held
original text. Both blind readers caught three controls and agreed throughout.
Each negative outcome pins the inspected PDF, exact source fragment and page
image; none confers original-text credit. The sealed audit is under
`reviews/m007/`; `REPORT_M007.md`, `GATE_M007.*` and `COST.md` record the
source-locator stop and unknown actual cost.

`checks/m008-mixed-held-originals.jsonl` records 50 distinct held-original
targets in GovInfo Federal Register issues and government report volumes:
1 third-adjudicated pass, 16 fail, 33 unsure. Both blind readers caught all
three controls; their sealed observations and the third review are under
`reviews/m008/`. `REPORT_M008.md` names every exact cited scope and reason.
`GATE_M008.*` and `COST.md` record the low-yield source-family stop and
unknown actual cost. Only the one fully checked GovInfo printing yields an
official fragment; no result is a human or legal certification.

`checks/m009-held-1936-and-reports.jsonl` records 50 distinct held targets:
0 pass, 47 fail, 1 unsure and 2 blocked. Both blind readers caught all
three controls. They separately revisited EO:3083 source provenance and
agreed that the complete numbered circular is not proven to be an issued
original printing. The two blocked orders need the exact 1911 Isthmian
GPO scan, PDF pages 28–29. The 50-row `REPORT_M009.md`, sealed evidence
under `reviews/m009/`, `GATE_M009.*` and `COST.md` document each span,
the low-yield source diagnosis and unknown actual cost. No result yields
original-text credit or a human/legal certification.
