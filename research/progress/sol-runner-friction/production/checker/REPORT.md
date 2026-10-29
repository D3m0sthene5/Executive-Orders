# Checker production read-closure audit

**Result:** the previous declarations omitted live checker providers and import dependencies. `inputs.txt` now includes checker/policy implementation files and dynamic provider patterns for job outputs/data, research records, and releases. `needs.txt` names the research and release roots required by those providers. This is a safe declaration repair for the known provider families; it does **not** certify a narrow materialization scope.

## Why the checker needs these paths

`checker.py` reads the census universe, decided-status table, Stage 21 crosswalk, Stage 14 fetch manifest, claim JSONL files, claim gate, and readiness tracker's step map. Its signing-date helper also scans every `jobs/*/output/*.csv` for `instrument_id` and `signing_date` columns.

`sources.py` discovers every `jobs/*/output/SOURCES.jsonl`, every `jobs/*/data/PROVENANCE.json`, the Stage 21 custody/acquisition records, Stage 20 statute/media indexes, Stage 18 source manifest, Opus manifest/index/text pack, official-fixity match map, and Pinakes replica fragments. `SOURCES.jsonl` records select `text_path` values dynamically; those paths can point anywhere under any job's output directory. Other-job download caches are runtime cache roots and do not belong to a committed-input declaration.

The import closure includes `working_text.py` and `factual_events.py`; the latter imports `jobs/norton/model.py`. The factual policy reads the five factual registry kinds and validates their referenced source paths and bytes. The project claim gate is imported from `research/stage19/code/claim_gate.py`; its error-to-step map is imported from `jobs/readiness-tracker/tracker.py`. The optional `--fetch` branch imports `fetch_ladder.py` and its three local modules (`embedded_cites.py`, `report_dates.py`, `request_contract.py`).

`working_text.Index` scans both `jobs/*/output/FRAGMENTS*.jsonl` and nested `jobs/*/data/**/FRAGMENTS*.jsonl`; each fragment may select a text body. Source-book custody is discovered recursively from every job's `data/PROVENANCE.json`, then per-order text is read from that producer's `output/FRAGMENTS.jsonl`. The source-book loader accepts any safe `releases/...` PDF named by provenance, not just the currently used `releases/source_books/` directory. The mirror adapter reads the literal `jobs/app-executive-orders/output/MIRROR_DOCUMENTS.jsonl` for archive capture pointers. No checker or imported checker-policy code reads `DOCUMENTS.jsonl`; custody records come from `SOURCES.jsonl` and the separate mirror provider.

## Closure boundary

The declarations intentionally retain provider breadth: all job output and data subtrees, all research, and all releases. Narrower fixed lists would miss dynamic text bodies, future provider files, or provenance-selected release members. The checker code also permits some repo-root-relative native paths: Stage 20/21 local paths, Pinakes replica `data.file`, and Norton factual `raw_path`/`text_path`. These are not confined to `research/`, `jobs/`, or `releases/` by the current implementation. Therefore no exact narrow certificate is safe from declarations alone. Full closure would require a full-repository input pattern, or a future code change that restricts those path fields, or an exact run-specific scan of every active record and referenced file. This worker did not change implementation or build the corpus.

The existing `needs.txt` convention lists `research` and `releases` as provider roots; jobs are always checked out by the runner. The broad `jobs/*/output/**` and `jobs/*/data/**` input patterns are the exact declared breadth required by provider discovery and dynamic body pointers.

## Bounded evidence

`runtime_fixture.py` constructs an isolated temporary repository and exercises five dynamic reads: nested `SOURCES.jsonl.text_path`, discovered FRAGMENTS text, a nested non-`source_books` LFS path selected by provenance, the fixed mirror capture provider, and repository-root-relative Norton raw/text paths. All five probes passed. The fixture does not claim full-corpus coverage.

The existing checker and ProQuest-input suites passed **50 tests** (`test_checker`, `test_proquest_inputs`), including cross-job output text paths, source-book LFS pointer/hash handling, Pinakes replica custody/path refusal, Opus index/text-pack behavior, mirror archive re-fetch, and exact cited ProQuest blob restoration. These are bounded mocked/local tests, not a production corpus build or certification.

## Cost and limits

Worker model: `gpt-6-luna`. Reliable start/finish timestamps and exclusive elapsed duration were not captured; `EVIDENCE.json` leaves them unavailable. Token and cash telemetry were unavailable. No full corpus build, network source acquisition, legal adjudication, output publication, branch/index operation, or implementation change occurred.
