# Erasmus source readiness: bounded recovery investigation

Read-only investigation at main `f07b023133640f288fd44c10c5176888c49f23e2`, 2026-11-02. No primary source was downloaded, queue appended, source grade changed, claim edited, or legal finding adopted. Root coordinates the four actor-source cases; this report verifies the two board-report routes and EO 12891 custody, and identifies all seven source/evidence cases.

## Result

**The existing retention and source-supplement interfaces can carry the board reports. No engineering change is established.** Current dossier board excerpts fail because `held_text_lead` is a generic lead classification excluded from the provisional order-working-text policy. Do not add that grade to `working_text.GRADES` or relabel these excerpts. Retain each exact report PDF, then declare explicit raw-PDF-backed excerpts through `source_supplement.py`; the original lead remains unchanged.

This route is conditional: none of the three required raw PDFs is tracked under its known hash at this HEAD, and their source-ladder cache paths are runner-relative custody metadata. The unchanged supplement requires real in-repository `local_path` bytes matching `sha256`, matching text bytes, exact spans and a fresh native packet. No supplemented packet or source-ready claim was created here.

## Seven cases

| Case | Erasmus blocker | Safe next action |
|---|---|---|
| EO 8129 | Packet lacks evidence IDs for Public Land Order 1704 and Proclamation 2416 | Root's separate actor-source inventory must verify held raw/text bytes and declare an exact source supplement; no inferred legal identity. Producer also identifies Reorganization Plan II context. |
| EO 8163 | Same missing PLO 1704 and Proclamation 2416 evidence | Same existing supplement route after exact source inventory, with the same Plan II context requirement. |
| EO 9949 | Packet lacks an evidence ID for EO 10804 | Same existing supplement route; a mention in reasoning is not citable event evidence. |
| EO 11026 | EO 11029 is not citable from the dossier | Same existing supplement route after custody and exact-span checks. |
| EO 11343 | NMB report text is held; raw PEB-170 PDF is missing from tracked custody | Retain exact version, inspect identity/transmittal pages, supplement, then conduct new research/review. |
| EO 12095 | NMB report text is held; raw PEB-189 PDF is missing from tracked custody | Same; explicitly reconcile internal Board 95-504 identity against NMB PEB-189 filename/index. |
| EO 12891 | EO 13062 evidence IDs and texts exist, but the selected official PDF is not held | Retain EO 13062 from its existing exact queue entry, inspect pages and resolve custody through ordinary native preparation/checking. |

EO 6204A is separately blocked by the missing Cotton Textile approval instrument; it is not one of these seven. The additional held later-order IDs in the Erasmus report are follow-up metadata cases, not seven newly completed claims.

## Exact source inventory

Full metadata and exact paths are in `BOARD_SOURCE_INVENTORY.json` and `EO13062_SOURCE.json`. PDF hashes below are the existing source receipts, **not newly rehashed PDF bytes**. All listed text hashes were independently recomputed against retained Git bytes.

| Source | Existing PDF SHA-256; receipt bytes | Rehashed text SHA-256 |
|---|---|---|
| PEB-170, EO 11343 | `5a7a3638cdd0d3d0614bcc0f37e5ddb86cab8e4c2c5f0fdae6e72565c2104a71`; 1,810,396 | `4c748d295c7367cfc179ce9be0aee2813e10f1280812143bc0b5b761d7d0400b` |
| PEB-189, EO 12095 | `060e9e9dbce19691f22a58039c2cfb0de7637147a6626d6f631760b09d6e0cd7`; 759,760 | `c1eac7592871985d1120f810e0d4f1a5359aeac807557b238acaf5e3b44b93fe` |
| EO 13062, 62 FR 51755 | `9d07849b94e259a259fb81828fe502bbe0860671d9dd962788b4bb0a42f42026`; 156,567 | FR text `356d0ec029b2cd64f68e65c4df65e745a1365202b3bd63cf15837be29b99dc1c`; ladder text `509f245181925cf614bed5e33def50c4890c05075cb8ad16bcbfed33e31faa35` |

Both board receipts are `evidence_tier=report_record`, not authentication or delivery findings. Existing selected text covers PDF pages 1–8. PEB-170 text names EO 11343 and carries a May 12, 1967 transmittal letter. PEB-189 cover names EO 12095 and Board 95-504, while NMB uses PEB-189; its February 9, 1979 transmittal OCR also contains a conflicting November 29 creation date against the November 2 cover/history. Inspect actual pages before resolving these representations. A dated transmittal letter does not itself establish actual presidential receipt or a computed standstill end; the Erasmus producer's June 11, 1967 endpoint is not adopted here.

## Queue and retention plan

The prior stalled plan's two exact JSON rows and two-item manifest are preserved unchanged as `FETCH_QUEUE_APPEND.jsonl` and `RETENTION_REQUESTS.json`.

- EO 11343 already has a report search at queue line 187, with no URLs. EO 12095 line 101 points to the NARA finding aid; the ladder receipt records its replacement by the NMB report. Other EO 12095 rows request statutes/code.
- Neither proposed board row is an exact existing JSON duplicate. Neither exact `(instrument_id, report URL)` pair exists. Both proposals concern an already-attempted report search, so they are bounded retention prerequisites, not discoveries or a second broad search.
- `astra-source-retention.validate_manifest` rejects the unchanged current queue: `Every instrument/URL pair must already be in FETCH_QUEUE`. It accepts that queue plus exactly these two rows. Validate/enqueue with the existing request-contract CLI once, preserving prior queue bytes. Its deduplication compares whole normalized JSON content hashes, not semantic source identity: changing prose can create a new row. Reuse the exact proposal on retries and recheck pairs before appending.
- EO 13062 already has the exact URL pair at line 65. Add no queue row. `RETENTION_REQUESTS.with-13062.json` supplies the two board requests plus this existing-pair request, expected hashes and bounded pages. It is an unexecuted plan, not custody evidence. Use the existing declared `RETENTION_MANIFEST` runner input; an accessible exact cached object can instead be imported with `retained_path` and expected hash.

## Why no grade-policy repair is needed

`fragment-hash-screen.json` enumerates all 24 tracked provider files matched by the existing working-text index patterns. Neither board PDF hash occurs as an `original_representation`; both EO 13062 official FR declarations do. The board dossier's grade comes from generic input fallback, so the shared source hash is not registered as a derivative order text.

`READ_ONLY_PROBES.json` records the bounded existing-policy probe: both old board references produce grade/registration/disclosure errors; equivalent raw-source forms produce zero **grade-policy** errors. This does not verify the unavailable raw bytes or establish source acceptance. `source_supplement.py` already checks raw/text hashes and exact spans, creates `SUPPLEMENT:<alias>` evidence IDs with `role=unreviewed_source_excerpt`, and binds lineage without changing inherited fields. An initial concern that the raw hash might be registered as a derivative was tested and disproved; no bypass is proposed.

After actual retention and source inspection, prepare a fresh native packet under current dependency/source pins, declare excerpts, verify supplement lineage, conduct substantive producer analysis, run apply/batch-check and independent review, and use ordinary completion only when all gates permit it. Historical packets may correctly reject current pins; do not renew fingerprints by hand. This investigation supplies no independent legal review, different-family review, certification, readiness increase or cost-saving result.

Prepared by delegated OpenAI-family Codex context; precise model tier, token/cash usage and complete active labor unavailable. No source/research workflow dispatched. Root owns shared Kean/HANDOFF integration.

## Authorized retention preparation follow-through

After the read-only investigation above, root authorized exactly the two board URL queue appends and a three-source default retention manifest. The original investigation and receipts remain unchanged as historical evidence.

- Appended exactly the preserved two board proposals through existing `request_contract.enqueue_requests`, after checking both exact pairs were absent. Every byte of the prior queue is preserved as a prefix; repeating the exact enqueue left the amended queue unchanged. EO 13062's existing pair was reused.
- Replaced `jobs/astra-source-retention/REQUESTS.json` with exact `RETENTION_REQUESTS.with-13062.json` bytes. Its three requests pin the existing PDF hashes and pages 1–8, 1–8 and 1–2 respectively. The previous 19-item default is preserved byte-for-byte as `PREVIOUS_DEFAULT_REQUESTS.json`.
- `QUEUE_DEFAULT_CHANGE.json` pins queue/default hashes, request-contract audits, prefix preservation and retry idempotency. `RETENTION_PREPARATION_TESTS.json` records nine passing checks, including seven expected refusals: excessive/zero pages, malformed expected hash, missing expected hash for a retained import, wrong held bytes for the expected board PDF hash, a missing retained object, and a missing exact queued pair. Existing `validate_manifest` accepts all three actual requests against the actual amended queue.
- The hash-refusal probe uses an existing text file solely as deliberately wrong PDF bytes. It creates no PDF or source acceptance. General network requests may omit an expected hash under the unchanged interface; these three requests explicitly pin theirs. No stricter policy is asserted or implemented.

No acquisition was run. Root will combine its actor-source requests into the existing default manifest and dispatch ordinary retention on integrated main. Subsequent custody, source examination, fresh preparation, independent review and scientific gates remain required. No source grade, source content, claim, status, readiness count, shared register or handoff was changed in this follow-through.

## Native five-source acquisition and independent custody audit

Run [41497558869](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/41497558869)
succeeded and published exact output commit `a3fbcbfe960c417e006a821b1a053a0bb3e482e7`.
All five requested PDFs matched their expected hashes and were retained: 47,090,803
bytes, seven HTTP requests, five completed extractions. The job reports 24.962
seconds of native work; setup/materialization/publication are additional costs.
`NATIVE_CUSTODY_REVIEW.json` independently rehashes the five actual Git PDFs,
20 page-text files, five selected-page text files and extraction directories.
Sources append 265 to 270 and attempts 343 to 348 with exact prior prefixes;
all prior retained artifact paths/object IDs remain, with zero deletions.
Requested targets remain separate from authenticated document identity.

No PNGs were produced: all 20 requested pages record an unavailable renderer,
and three page-text extractions are empty. This is retained PDF custody and
text extraction, not visual page review, authentication, delivery evidence,
source-grade promotion or a legal conclusion. Actual page examination, fresh
source supplements and ordinary independent scientific review remain necessary.
`SOURCE_INTEGRATION_REVIEW.json` also verifies unchanged native output bytes
while merging the current main coordination history. Earlier source-blocked
reports and request-preparation receipts remain historical; they are not erased.
