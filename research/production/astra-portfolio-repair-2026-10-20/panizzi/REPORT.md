# Panizzi repair and bounded source acquisition

Recorded October 20, 2026 against base commit `91116f879978902343dafa88490b9b19587b10da`.
This report describes local work and the installed source catalog. It does not certify a new GitHub Actions run, integrated readiness, a legal conclusion, or human review.

## Result

The repaired canonical catalog at `jobs/source-ladder/output/` contains **364 usable source receipts: 361 retained prior receipts and three newly acquired primary documents**. Nineteen prior receipts fail the retrieval checks for their requests and are quarantined, with the original receipts and exact held text preserved. No quarantined receipt appears as `found` in the usable catalog. All 364 usable receipts pass a second carry-forward validation.

The original queue's **17 rejected rows** were reproduced. Fifteen requests can be corrected unambiguously. Two compound requests retain a usable original-source task and a visibly unresolved ending-source task. The repair does not infer an ending instrument from the original order. Exactly three new requests were validated and appended for the authorized primary-source probe; the preceding queue bytes were preserved unchanged.

Source-ladder now has **173 passing tests**, compared with 148 at the base. The final catalog refresh used **zero HTTP requests, zero range requests, and zero downloaded bytes**; it reused the bounded live acquisition's cache. These are retrieval results, not 364 completed EO lifecycles.

## Reproduced defects and changes

`BEFORE.json` pins the original queue and records the old behavior. Its test reproductions load the original source-ladder code from the base commit rather than merely describing what was suspected.

The old parser rejected legacy `current_basis`, `original_page_check`, and compound steps, and missed two exact original-source requests stored in a note. A new shared `request_contract.py` validates before append and again before execution, records original objects and canonical JSON fingerprints, and assigns stable request/task identities independent of queue position. Existing valid acquisition IDs remain compatible with the prior catalog. Corrections are emitted as audit records rather than edits to historical queue rows.

| Original rows | Count | Reconciliation |
| --- | ---: | --- |
| 306, 444–449, 451, 453, 455 | 10 | `current_basis` becomes `ending_or_current_basis`. |
| 452, 519 | 2 | `original_page_check` becomes an original-text acquisition task; the page-review obligation remains explicit. |
| 457, 470 | 2 | Recover only the exact same order's original-text citation explicitly named in the note; retain the declared step. |
| 434 | 1 | Split the original EO 9132-A and the expressly identified EO 9427-A into distinct acquisition tasks. |
| 515, 523 | 2 | Preserve original-source work; keep the unidentified ending source unresolved, without copying the original URL into a second supposed ending task. |

The original 17 objects and line numbers are regression fixtures in `jobs/source-ladder/fixtures/legacy_requests.jsonl`. `QUEUE_CORRECTIONS.jsonl` retains their complete reconciliation. The installed `QUEUE_AUDIT.jsonl` covers the current 551 rows, including the three authorized additions. The resulting acquisition universe is 1,454 tasks: 590 from the queue, 90 shared-source tasks, and 774 Opus refetch tasks. These are task counts, with embedded citations included, not a count of unique orders or remaining legal judgments.

Carried receipts previously bypassed checks offline; report-date receipts also had a blanket exemption. A wrong expected file hash could still return `found`. Unselected invalid receipts could remain `found` after a bounded run. Those paths are repaired. Every prior receipt is checked before carry, including receipts outside the selected plan. The checks cover explicit document identity contradictions, citation identifiers, source and extracted-text hashes, changed request fingerprints, metadata and finding-aid URLs, existing partial-extraction/content checks, explicit historical edition, and precise required dates where the source identifies them.

Passing these checks establishes that no implemented retrieval defect was detected. It does not authenticate the transcription or establish which version was legally in force. Annual editions are not treated as proof of the law on an exact day. Evidence tiers distinguish document text, report records, finding aids, metadata and custody-only material.

Report matching previously found the named commission somewhere in a large extracted range and an unrelated occurrence of “report” elsewhere. The new screen requires the report word and the named body in local context. It also avoids matching “reporters.” Three held records demonstrate the defect:

- EO 12502: a commission appointment record with an unrelated “reporters” occurrence.
- EO 12526: an update on the Packard Commission's work, with unrelated reports elsewhere in the range.
- EO 12607: a deadline amendment near an unrelated Belgian tax-convention report.

The old and new decisions, document hashes and held-text hashes are in `BEFORE.json`. The local-context screen is deliberately a retrieval heuristic. It does not establish delivery, first cessation, or the legal significance of a report. Relevant but insufficient material remains preserved for review.

## Prior evidence and failure history

Of the 380 prior found receipts, 361 pass the repaired checks and 19 fail for their requests: 11 partial statute extracts, five listing/finding-aid records, and the three report-context mismatches above. The first 16 had already carried defect annotations in the old catalog; the repair prevents them from continuing to appear usable merely because they were outside the current selection.

`REJECTED_PRIOR_SOURCES.jsonl` stores each original source record, its reason, source hash, and preserved-text hash/path. Each record says `usable_for_request: false`; rejection does not mean the document could never support a different question. All 380 original text byte sequences were compared with their retained or quarantined copies and were unchanged.

Bounded runs also retain cumulative, deduplicated failure and attempt history. The installed output preserves 152 earlier failure records and 125 earlier attempt records. Sixteen older failures outside the immediately preceding selection would otherwise disappear from the next history file. The scheduler now reads this retained history when distinguishing previously tried work. Cache reuse, retry behavior, request and byte budgets, and the distinction between a retryable failure and an exhaustion proposal remain intact.

The original GitHub `STATUS.json`, `RUNNER_INPUTS.json`, source/results files, attempt history and logs are preserved unchanged under `prior-output-receipts/`. The current catalog's provenance is `jobs/source-ladder/output/LOCAL_REFRESH.json`, also copied to `CANONICAL_REFRESH.json`. It pins the original receipts, current Python sources, queue and resulting files. A later GitHub run must provide its own runner metadata.

## Three real primary-source acquisitions

The authorized requests are in `PRIMARY_REQUESTS.jsonl`; `ENQUEUE_RECEIPT.json` records the append and the unchanged original queue prefix. `live-probe/PRIMARY_FILES.json` gives exact file and text paths. The PDF/HTML bytes are retained under `live-probe/files/`, not just represented by links.

| Source | Outcome and evidence tier | Downloaded bytes | SHA-256 |
| --- | --- | ---: | --- |
| [DOI final monuments review report](https://www.doi.gov/sites/default/files/uploads/revised_final_report.pdf) | Found; document text, all 20 PDF pages | 499,001 | `c4f219cfceab84f567b7a87a97d8db8aab2a75257d97ee88229067573c9179b3` |
| [DOI congressional testimony](https://www.doi.gov/node/26508) | Found; document text | 64,763 | `5960e47c7c1e1dce79cf2ac8d55f26a9042e150f66a04443e7990678af82fc19` |
| [OMB Memorandum M-18-25](https://trumpwhitehouse.archives.gov/wp-content/uploads/2018/09/M-18-25.pdf) | Found; document text, all six PDF pages | 553,906 | `f4744e1e2ad041f51e4c58daf07acaa123f316e20ab3e7094c2df439e992a28a` |

The testimony is dated January 30, 2018 and states that the Secretary submitted both interim and final reports to the President. It does not provide an exact submission date. The final report's page 2 discusses an August 24, 2017 reporting deadline; the deadline alone does not establish actual performance on that date. M-18-25 is dated September 26, 2018 and describes issuance of the accountability system as well as continuing quarterly reviews and scorecards. Review must distinguish those completed and continuing acts. These observations are source pointers for the separate Lambertini review; this job does not resolve a whole-order first-cessation question.

The supplied-URL-only probe allowed three ladder requests per pass, no retries, a 30-second timeout, and a 50 MB download ceiling. A preflight integration-test failure made no HTTP requests and is preserved in `live-probe-attempt1.log`; the test's inherited environment was corrected. The first acquisition pass found the DOI files and stopped at the three-request ceiling before the OMB file. Its receipts and budget stop remain in `live-probe-attempt2/`. The next bounded pass reused both DOI files from cache and obtained the OMB document.

Across the two acquisition passes the recorded totals are five ladder HTTP requests, seven pool network calls, zero range requests and **1,117,670 downloaded document bytes**. The two existing request counters differ because the pool also counts its own robots requests; they should not be presented as the same measurement. Job execution time was 3.6 and 2.8 seconds respectively, excluding agent work. The second pass's three `new_sources_found` entries are new to that isolated pass; across the probe there are three distinct newly acquired documents, not five.

The deterministic jobs make no model calls, so their model-token count is zero. Build, investigation, coordination and review tokens, local-session cash charges and total elapsed human/agent effort are unavailable. No total cost saving is claimed from these runs.

## Validation and handoff

- Source-ladder: 173 tests passed, including the actual 17 requests, expected-hash rejection, historical edition/date checks, compound-task cache reuse, invalid in-memory requests with zero network, report-context errors, quarantine byte preservation and successive-run history retention. See `TESTS.log`.
- Compatibility checks: fr-originals passed 37 tests; corpus-excavator passed eight during this repair.
- A real four-item offline probe revalidated all 380 held receipts before the live acquisition. Its earlier sparse-input counts are explicitly local in `LOCAL_SUMMARY.json`; they are not the final queue universe.
- The canonical refresh selected only the three authorized cached requests, retained the 361 passing prior receipts, quarantined all 19 failures, and made no network requests. A second revalidation accepted all 364 usable receipts.
- `git diff --check` passed for the changed source-ladder code and report artifacts.

Consumers should use `request_contract.enqueue_requests(queue_path, requests)` for validated append-only source requests. Invalid or unresolved batches raise before any write. The corresponding CLI is `python jobs/source-ladder/request_contract.py validate --input requests.jsonl`, followed by `enqueue --input requests.jsonl --queue research/readiness/FETCH_QUEUE.jsonl` for a valid batch. Execution performs the same essential request checks before fetching.

The root integration task must run the checker/tracker and the designated offline consumers against this catalog, reconcile any readiness decrease, and obtain the separate AI/human review evidence required by the campaign. This repair supplies no new canonical legal claim and does not change authoritative admission decisions.
