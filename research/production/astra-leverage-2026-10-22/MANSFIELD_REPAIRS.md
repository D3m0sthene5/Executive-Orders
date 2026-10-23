# Mansfield evidence-preparation diagnostic, October 22, 2026

Six known failures were independently reproduced from the held text and current
main dossiers, pinned to `46a29e15d6ed4c252416b28e0ccc0590fcf6abc2`. The prior
failure descriptions come from PR54 head
`d8613babe75bbee5ac6b46d9e756835a8d61c5ab`; they remain historical producer/reviewer
records, not newly accepted conclusions. No Mansfield claim was adopted or
replaced. The legal cutoff remains October 14, 2026.

The existing `batch.preflight` now checks actual held text hashes and exact
spans, explicit identity mismatches, ambiguous neighboring documents, numbered
sections missing from inventory, possible truncation against another declared
representation of the same source, and ACT snippets that stop at a heading or
introductory formula. It explicitly distinguishes report-relative termination
from a reporting deadline. These are preparation warnings, not legal findings.
Raw-source custody still requires the actual claim checker.

A narrow segmentation repair recognizes whitespace between the section number
and punctuation. On EO12607's held recheck extraction, `Section 1 .` previously
caused section 1(a)'s establishment/member command to disappear. The replay now
retains it with exact original offsets. It does not repair the missing second
page or approve the resulting inventory.

| Order | Independently observed problem | Existing path and unresolved work |
|---|---|---|
| EO10915 | The dossier still reports EO11963/12148/12220 provisions unlocated. EO12220's held FR text contains section 1-501 revoking EO10900 “as amended”; the dossier's EO12220 snippet uses another representation/list. Other ACT snippets also stop before operative sections. | Correct the exact source/provision association, with independent review. Existing `act_overrides` only fills genuinely unlocated target/actor pairs and excludes pairs already located in another representation. Parent reach, distinct commands and the unnamed-instrument ruling remain substantive questions. No wholesale-parent-ending approval follows from correcting a quote. |
| EO11927 | The EO11976 ACT quote at characters 475–902 ends at the `Section 1.` label. Its operative section 2, starting at 1222, is outside that quote. The target inventory is one block containing separately amended items. | Correct the located provision through a reviewed preparation correction; the ordinary override path rejects an already-located pair. Split the inventory with the existing reviewed inventory-override interface and determine each item's lifecycle, including parent-ending scope. |
| EO12975 | EO13137's ACT quote at 610–1101 stops at the `Section 1.` label. Section 3(c), including the 1999→2001 date substitution, is later in the held text. Several aliases repeat the incomplete snippet. | Correct the exact provision association and review the renumbered clauses. Existing located-pair override refusal must be preserved. The first cessation of distinct duties, conditional extension history, and EO14096's later reference remain separate legal questions. |
| EO9333 | EO9830's held full text contains the target in its long revocation list, but the dossier has only the overflow actor pointer and no citable ACT. | This is a candidate for the existing independently reviewed `act_overrides` path after checking the exact selected text, governing revocation/effectiveness span and D6. The war-duration own term and complete inventory still require source-based legal review. |
| EO12607 | The selected `.recheck.txt` ends after section 2(d), then a page marker and filing line. Another declared extraction of the same PDF includes sections 3–4. Section 4(b) expressly terminates the Commission 30 days after submission of its final report. | Section-number spacing is repaired. A reviewed source-selection/inventory correction is still needed, using the held complete page. Actual report submission and the relative sunset require research. The deadline ruling does **not** establish the later cleanup revocation as first cessation. |
| EO8072 | The dossier's four clauses are the adjacent Federal Interdepartmental Safety Council order. The raw page contains multiple unnumbered order headings; metadata alone did not select the target's land-withdrawal text. PLO1068's held issue text expressly names EO8072 in its operative paragraph, but is absent from the dossier's citable evidence. | Correct the boundary/inventory with source-page review. PLO1068 needs the existing external-source/citation preparation route or a narrowly reviewed extension: `act_overrides` currently requires both actors in the EO census, so simply adding a PLO record there would fail. Savings, land scope and earlier events remain review obligations. |

`MANSFIELD_REPAIRS.json` records exact dossier hashes, before/after tasks,
held-text hashes and the isolated EO12607 segmentation replay. The six-case
diagnostic packet under `mansfield-preflight/` was actually prepared: six
members, 71 validated text files, exact lossless round trip and 50 disclosed
tasks. Its preparation receipt records 0.8136 machine seconds. The older screen
reported 37 tasks; more visible tasks are more accurate preparation, not
additional completed research. EO10032 and EO10056 are unaffected held-source
controls: no new evidence warning was added. Their legal obligations remain.

Validation: 12 focused evidence/preparation regressions and 12 existing batch
tests pass. The 29 existing excavator tests have 26 passes and three sparse
real-corpus skips; skipped cases are untested here. The focused tests include
missing bytes, wrong hash/identity, mismatched quotes, custody-only references,
neighboring orders, truncation, unchanged valid controls, source preservation,
report-relative sunsets and the section-spacing repair. Full held originals
and exact source snippets remain accessible in the diagnostic packet.

**Outcome:** one bounded segmentation defect repaired; six preparation failures
classified; zero complete dossiers, zero new ready orders and zero authenticated
originals. No substantive hold was removed. No new source was acquired. No
matched savings test was run and no global benefit is inferred. Model-token,
aggregate agent-time and cash telemetry are unavailable, represented as null.
The prior Mansfield missed D6 control and after-reveal reviews remain unchanged;
this diagnostic is not an independent retest authorizing its production method
to scale.

Reproduce the compact receipt with
`python research/production/astra-leverage-2026-10-22/replay_mansfield.py` against
the pinned baseline objects and materialized dossier sources. It writes only
the diagnostic receipt; it never modifies canonical outputs or claims.
