# Transcription working-text implementation report

Frozen for parent integration; no commits, pushes, canonical legal-claim/status edits, acquisition, or full claim-kit build performed by this agent.

## Implemented scope

- Shared `jobs/claim-kit/working_text.py` validates existing order-specific original-representation fragments. Exact grade, `acceptable_as_original:false`, instrument identity, raw-source hash, declared text hash, held text, full representation span and exact quotations survive preparation and assembly. Explicit identity/completeness and any page review remain required. Mandatory owner note and replacement/recheck obligations remain attached.
- Inputs, dossier preparation, blank decision sheets, assembler, batch decisions, checker and tracker consume the same policy. Tracker revalidates policy independently of old checker receipts and separately reports transcription-dependent ready claims and acquisition/quote debt. Official-copy arrival reopens replacement/recheck; exact independently declared official representation may share a PDF hash without being mislabeled derivative.
- Narrow Pinakes custody adapter reads its existing `FRAGMENTS.data.file` association (this producer has no SOURCES.jsonl). Only actual present PDF bytes enter ordinary rehash verification. Missing PDF or LFS pointer stays custody-only; grade/authentication/page/identity/completeness are never approved by the adapter.
- Factual-event checker/tracker integration uses report-bridge agent's `factual_events.claim_errors` and current registry/source bytes. Dependency inputs and triggers include helper, NORTON model and factual registry. Added working_text.py/population.py/factual_events.py compiler dependencies.
- Batch apply pins working-text policy, factual policy, NORTON model and lifecycle-obligation helper; enforces stored batch codec hash and existing assembler/preflight/excavator pins. Missing or changed pins require a new reviewed packet.
- Actual ProQuest preparation exposed a prior collector mutation: page debt appended `_needs_page_check` to the declared derivative grade. Fixed narrowly: false representations preserve exact grade while retaining separate `requires_page_check:true`; official-original behavior unchanged.

## Validation

Focused final runs passed: assembler 50 tests; checker 37; input discovery 27; batch 14; tracker 28; factual-event bridge 15. Tests include missing disclosure/identity/completeness/page review, wrong identity/grade, missing or tampered text/source bytes, exact quotation/full-span failure, fragment declared hash absent, official replacement, unchanged ending/current-law/custody gates, path aliases, uppercase/whitespace hash spelling, archival `local_file_sha256` aliases, nested sources/source_refs, valid listed derivative, same-PDF exact official representation, stale checker receipt, unsafe replica file path, missing raw PDF, source hash mismatch, and each packet dependency pin.

Actual patched tracker replay: `/tmp/eo-transcription-tracker-output`, log `/tmp/eo-transcription-tracker.log`. Compared with parent pristine-main replay `/tmp/eo-baseline-tracker-output`: all pre-existing summary keys and all per-step decided counts unchanged. 14,972 identities, 3,403 decided, 280 ready; 280 original-supported, zero transcription-dependent ready. Existing canonical claims did not invoke this new provisional route. Isolated rule effect: zero newly ready; no broad fragment-row credit.

## Actual three-case preparation sample

Artifacts: `transcription-sample/RESULT.json`, each EO_23/EO_249/EO_254 dossier and unapproved DECISIONS.json; reproducer `replay_transcription.py` and log `/tmp/eo-transcription-sample.log`.

Sample uses existing decided, text-step-open ProQuest records and actual held PDF/text bytes. EO23: 2,084 chars, 2 pages, quality 0.734. EO249: 7,304 chars, 1 page, quality 0.744. EO254: 685 chars, 1 page, quality 0.31 (retained weak-text control). All three exact PDF/text hash pairs verify. Baseline collector dropped source grade/false flag and appended a synthetic page-warning suffix; patched collector preserves declared `archival_replica_scan_pending_codebook`, false flag and page debt. Each produces one machine clause lead and the required standing note. Each remains blocked on blank identity/completeness/page confirmations, unapproved, with zero legal reviews and zero ready gain. No source/page/legal review was simulated to improve the result.

Local collector-only timings are recorded in RESULT.json; they are not end-to-end throughput or campaign cost claims. Source materialization, setup failures, engineering/reviewer repair and independent legal review costs remain outside this microtimer and must stay in parent campaign accounting. Token spend was not available to this agent.

## Limits / follow-up

Supported working-text declarations are existing FRAGMENTS original_representation rows with explicit grade and false flag. Ungraded Richardson/provenance-only records fail closed; no invented grade was assigned. APP mirrors without retained raw bytes still fail custody. ProQuest raw PDFs must be present when checker runs; current generic checker needs list does not automatically fetch entire large ProQuest directories. The narrow adapter safely reports absent ones as custody-only. Parent should retain this limitation or arrange bounded cited-PDF materialization, never broad custody credit.

Engineering validation is not independent whole-case legal review. No denominator/version repairs, canonical legal replacements, independent legal approval, or production readiness gains are claimed here. Parent owns shared ledgers/publication and final integrated checks.
