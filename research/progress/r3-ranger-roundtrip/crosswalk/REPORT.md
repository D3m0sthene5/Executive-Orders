# Early Ranger source availability crosswalk

Research cutoff context: repository's Stage 22 cutoff is 2026-10-14. This mechanical crosswalk was assembled on 2026-10-31 from the checked-out `sol/r3-ranger-roundtrip` tree at `88cef0253ed735b2a6e612770f25f9148641ce93`. It covers the six top-ranked directive-title rows in the early-ranger triage CSV and both Madison-to-Armstrong LOC records (`mjm017456`, `mjm022917`). It checks local paths, file bytes and existing recorded digests; it does not authenticate an author, decide historical inclusion, or add census instruments.

The machine-readable record is [CROSSWALK.json](CROSSWALK.json). It includes per-file byte counts and SHA-256, LOC source URLs, catalog metadata versions, current acquisition state, older workbench payload fields and source-run pins.

## What is available now

| LOC item | Local manuscript representation | Transcript currently in acquisition inventory | Transcript embedded in held workbench | Current item metadata output |
|---|---|---|---|---|
| `mjm017450` | 1 facsimile JPG | none | none | request failed (HTTP 429) |
| `mjm018302` | 2 facsimile JPGs | none | none | skipped after provider failures |
| `mtjbib011110` | 1 facsimile JPG | none | none | skipped after provider failures |
| `mtjbib012509` | 4 master-page JPGs plus 1 service PDF | none | yes, 15,600 UTF-8 bytes in HTML payload | request failed (HTTP 429) |
| `mtjbib016595` | 7 facsimile JPGs | none | none | skipped after provider failures |
| `mss365090092` | no locally stored page or derivative found | none | none | skipped after provider failures |
| `mjm017456` | 3 master-page JPGs plus 1 service PDF | none | yes, 6,954 UTF-8 bytes in HTML payload | request failed (HTTP 429) |
| `mjm022917` | no locally stored page or derivative found; workbench holds LOC URLs for eight master JPG resources | none | none | skipped after provider failures |

All retained facsimile/page files listed above hash-match their respective custody manifests. Per-image hashes and exact paths are in `CROSSWALK.json`. The Madison master images are `jobs/early-ranger-full-pages/output/mjm017456/page_01.jpg` through `page_03.jpg`; its separate service PDF is a small 12,361-byte derivative. The alternate Madison catalog record has potential image URLs in its old metadata payload but no downloaded image bytes locally.

The six priority leads are based on title/date triage only. LOC catalog payloads in the old HTML carry richer titles, creator labels and resource links than today's `PRIMARY_ITEM_METADATA.jsonl`; current rows have status/error fields only. The six records still have unknown inclusion in triage. The two Armstrong catalog records each carry the same title, date and creator in the older workbench payload but have different catalog IDs and resource sets. That is a duplicate/identity review lead, not a finding that they represent the same physical document or the same instrument.

## Transcript recovery and stale-output mismatch

The current transcription acquisition output is empty: `TRANSCRIPTION_INVENTORY.jsonl` has zero bytes, `derived_text/` is absent, and `TRANSCRIPTION_METRICS.json` records 0 XML links, 0 preserved transcripts and 0 words. Its `STATUS.json`, however, says the old run 39821342262 on 2026-10-22 succeeded. The current original-item metadata metrics likewise say zero retrieved responses, while its 21-row `PRIMARY_ITEM_METADATA.jsonl` has four HTTP 429 failures and 17 `skipped_after_provider_failures` rows. Those current outputs are not a complete copy of the earlier acquisition representation.

An older static `EARLY_SOURCE_REVIEW_WORKBENCH.html` remains locally readable and embeds all 21 item records; its payload metrics report nine nonempty transcripts and a `source_text_bytes` value of 58,553. Parsing confirms that this HTML contains the full LOC-derived transcript text for the scoped `mtjbib012509` and `mjm017456` items, even though neither has a current `derived_text/*.txt` file or inventory entry. The `source_text_bytes` metric is actually computed with Python `len(text)` and therefore counts Unicode code points, not UTF-8 bytes. The two embedded text values have SHA-256 hashes recorded in `CROSSWALK.json`; the underlying XML bytes are not present in the current source inventory, so these hashes pin only the extracted text inside the static HTML, not its source XML.

For the Madison August 13 candidate, Stage 22 records an older LOC XML digest `6592b275afad9cf7556462c8712fe7d3ae1c950b29fd7325c617b4f999583e6a` and path `jobs/early-ranger-transcriptions/output/derived_text/mjm017456.txt`; that file is absent now. Its transcript in the HTML is a retained derivative representation. Do not silently regenerate or present it as recovered raw XML. The Stage 22 candidate file separately marks original-page verification false and inclusion `hold_original_and_codebook_review`.

The workbench's `STATUS.json` ties it to run 39059618624 / build commit `4b3281a938621d0940de1693e96925a98f0db7ce`; the transcription status points to run 39821342262 / `20d4f4d4b6c4284fecd46e6671411a05388d9d9a`. Current tracked transcription output files hash to an empty inventory plus zero metrics, while the older HTML blob (`b85629888840d5a5135f9acc80bb9e2306abbe9d`) still carries text and earlier metadata. This is a version/provenance mismatch, not a legal-source conclusion.

## Census and historical inclusion boundary

Stage 22 says no additional historical orders have been admitted. `jobs/census-candidates/output/CENSUS_READINESS.md` reports zero candidates admitted and zero independent certifications, while separating 67 LOC item IDs from the existing 14,972 working EO population. The historical pilot says the manuscript and exact operative clause remain to be checked against the original pages, instrument identity and Lord representation, and frozen codebook 2.0.0; project procedure requires resolving identity/inclusion before the separate lifecycle research. The triage report likewise says titles and dates only order inspection and direct review must distinguish presidential instructions from papers, independent secretary action, nomination or later editorial copies. This crosswalk records availability and those documented holds; it makes no inclusion ruling and no instrument-count claim.

## Run and telemetry disclosure

Exact agent wall time was not instrumented. Model family is not exposed to this subtask, and token/cash telemetry is unavailable. Individual shell calls completed in under one second, which is machine-call latency and not total research labor. No network fetch or acquisition-file mutation was performed; no output image/transcript was rewritten.
