# Independent matched-packet completeness audit

**Verdict: PASS for the pinned six-case evidence packet and readable view.** No material evidence omission was found in this cohort. This is a packet-completeness result; no legal decisions, producer-arm outputs, decision CSVs, applied records or producer rationales were read.

The audited inputs are the same six frozen A/dossiers files, B/PACKET.json, B/READ.md, B/PREPARE.json, the held text files named by the packet and relevant codec source. Initial copies and input pins are preserved under `initial/` and `INITIAL_PINS.json`. `FINAL_REVIEW.json` contains all detailed results and source hashes. The auditor imports no production codec or assembler module.

## Exact reconstruction and source checks

An independent recursive interpreter expands source dictionaries, text spans and repeated objects, with singleton-tag checks, bounds checks and cycle detection. All **six reconstructed JSON dossiers equal the frozen A inputs**, and every canonical dossier fingerprint matches. The packet envelope fingerprint and original input file hashes also match.

The audit independently verified **33 held text-file hashes**, **23 shared block bodies and all declared aliases/ranges**, **35 source catalogue dictionaries**, and **140 shared objects** through expansion. Every readable block preserves its exact Unicode body, parent text hash, absolute character bounds and path metadata. A source heading inside a code fence is treated as source content rather than a dossier section.

The baseline files total **650,064 physical bytes**. Their normalized pretty JSON is **650,060 bytes**, matching PREPARE.json: four files contain one additional trailing LF each. Reconstruction is exact for dossier values, fingerprints and source-text Unicode; the codec does not preserve those four outer JSON formatting bytes. This distinction is explicit rather than calling physical file bytes identical.

## Independent readable-material coverage

The audit parses READ.md's catalogue, fenced source bodies, evidence index and per-order sections, then checks each against the frozen A inputs. Coverage includes:

- **146 evidence records and their accessible exact text**, including all **6 original records** and **16 full actor-context records**.
- All **43 clause inventory entries**, which are verified to duplicate complete records in the readable evidence index, including source, text and span metadata.
- All **26 evidence records with exception or savings fields**, preserving those fields exactly.
- Complete own-term IDs, actor contexts/provisions, chains, current-law leads, machine searches and coverage warnings, gate errors, conflicts, draft material gaps, missing lists and notices.
- Source identity, page/location and provenance flags, effective-wording metadata, readable shared tasks and codec warnings.

The renderer excludes `provision_text` and `alternative_provisions` containers from index metadata. This requires actual verification: for this six-case cohort, all **50 nonempty provision_text values exactly equal retained text**, and all **37 alternative records are independently indexed with their complete fields**. Therefore those exclusions drop no unique evidence here. This audit would fail a nonredundant omitted provision or alternative; it is not a general claim that the renderer can always discard those fields.

No actual actor-overflow entries occur in these six frozen dossiers. Their absence was checked. The audit verifies that any present overflow pointer is printed, but this sample does not demonstrate readable overflow handling across the full fifty; the root's separate extension must retain that limit. The lossless PACKET provides all six complete input structures beside the readable view.

A usability limitation remains: evidence rows give source hashes and absolute character bounds without direct per-row links to shared text block anchors. The audit independently resolved those addresses, so this is a navigation cost rather than an observed evidence omission. No change to packet/legal content is required by this finding.

## Sizes and interpretation

| Artifact | UTF-8 bytes | Reduction against normalized baseline |
|---|---:|---:|
| Six normalized dossier JSON files | 650,060 | — |
| Lossless PACKET.json | 376,608 | 42.07% |
| Readable READ.md | 263,944 | 59.40% |
| PACKET plus READ | 640,552 | 1.46% |

These are different representations, not additive savings. If an agent reads both complete packet files, combined bytes are the relevant payload figure. Actual tool/model cache behavior, subsequent source reads, legal reasoning, failures and review determine research cost separately. This audit measures no net token, dollar or legal-review savings.

The older 684,097 → 349,648 prototype has unknown member identities. No exact numerical reproduction or cohort comparability is claimed for it.

## Code pins, negative controls and retained failures

PACKET.json pins codec SHA-256 `5d2fca1e26657ca648571e339cee71a8a2d5a66783f9bd0f38e96b5989eceee2`. The coordinator preserved this exact packet-era source under versions/PACKET_ERA_BATCH.py; the auditor copied and verified it at `initial/PACKET_ERA_BATCH.py`. Current batch.py had already changed to SHA `9d15949b70cdf74ba429a85e49ad8fc69b39547699897c9c29ba825554010318`; both identities are recorded. No current-code hash was silently substituted for packet preparation. The assembler pin also matches the observed file.

Four deliberately damaged controls all produce **FAIL_REQUIRES_CORRECTION_AND_REREVIEW**: removed source body, removed exception metadata, removed current-law leads, and a removed original record with the packet envelope fingerprint recomputed. This shows that exact-envelope checking alone is not the basis of the positive verdict. Control files, reviews and mutation code remain under `negative-controls/`; `NEGATIVE_CONTROLS.json` records all four detections. These are auditor controls and were never supplied to an arm.

Initial exploratory console output hit a Windows Unicode display error; no packet files changed. The first negative-control harness wrote CRLF while the pinned READ uses LF, so it produced broad formatting-related failures before the expected specific check. The failed control inputs/review are preserved as `initial-control-newline-failure*`; the harness was corrected to write exact UTF-8 bytes and all four targeted controls reran successfully. These preparation failures are separate from the unchanged packet's zero-failure audit.

The first telemetry-export command contained a stray patch marker and failed before execution; its corrected rerun produced TELEMETRY.json. No verdict or evidence file was changed by that failed command. The own-rollout tool trace retains these failed attempts.

The initial successful audit took **0.066 seconds**; the final pin-verified audit took **0.063 seconds**. Full agent preparation and own-rollout runtime usage are separately recorded in `TELEMETRY.json` with explicit phase boundaries and cutoff. Those times are script wall times, not complete agent labor.

Reproduce from the repository root:

```powershell
python research/excavator/2026-10-18/batch-pilot/packet-review/audit_packet.py --prefix REPRODUCED_REVIEW
python research/excavator/2026-10-18/batch-pilot/packet-review/run_negative_controls.py
```

The immutable initial READ and PACKET remain available for replay. No producer was sent a legal outcome hint. Nothing was published, and no sources, frozen dossiers, claims, statuses or reservations were changed by this audit.
