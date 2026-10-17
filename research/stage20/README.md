# Stage 20 — conversion excavator and verified full Opus recovery (2026-10-17)

The Stage 19 0/14,972 independently human-reviewed whole-lifecycle headline is **unchanged**. All 3,359 provisional YES/NO labels remain preserved and the 844 accepted Opus AI research cases are incorporated into a reproducible, evidence-preserving conversion index. AI reviewer reasoning, a claimed complete footprint, a cited legal authority or a date string **cannot** increment the headline.

## Current verified artifacts

| Artifact | State |
|---|---|
| [CONVERSION_INDEX.csv](output/CONVERSION_INDEX.csv) | 3,359 legacy classification records with source-readiness flags, triage lane and next research task |
| [OPUS_NOTE_LEADS.jsonl](output/OPUS_NOTE_LEADS.jsonl) | All **844** accepted Opus AI reviewer narratives, including **836** upstream footprint-complete claims and **323** cases with unclassified ISO date mentions |
| [OPUS_FULL_844.jsonl](output/OPUS_FULL_844.jsonl) | Full-archive structured material extracted after source ZIP SHA-256 verification, retained as research leads |
| [SHARED_SOURCE_REFERENCE_QUEUE.csv](output/SHARED_SOURCE_REFERENCE_QUEUE.csv) | **98** repeated legal-reference clusters enabling shared official-source acquisition, without propagating legal conclusions |
| [CONVERSION_WORKBENCH.html](output/CONVERSION_WORKBENCH.html) | Offline searchable AI reviewer-note research interface and uncertified researcher-proposal export |
| [SHARED_SOURCE_WORKBENCH.html](output/SHARED_SOURCE_WORKBENCH.html) | Source-once/per-order review interface across 98 clusters, 352 linked research tasks and 236 distinct cases; no legal-effect claims accepted |
| [SHARED_SOURCE_CASE_REVIEW_QUEUE.csv](output/SHARED_SOURCE_CASE_REVIEW_QUEUE.csv) | Flat task ledger assigning one separate source-and-clause legal inquiry per case–citation pair |
| [CAUSAL_CUE_SUMMARY.json](output/CAUSAL_CUE_SUMMARY.json) | Case-specific date-context research hints and explicit warnings about shared-batch image ambiguity |
| [OPUS_ORIGINAL_MEDIA_INTEGRITY.json](output/OPUS_ORIGINAL_MEDIA_INTEGRITY.json) | **496 of 496** media members match the Opus manifest's member sizes and SHA-256 checksums; 0 unmatched members |
| [OPUS_ORIGINAL_MEDIA_MEMBER_MAP.csv](output/OPUS_ORIGINAL_MEDIA_MEMBER_MAP.csv) | Manifest paths with source byte hashes and **provisional** evidence-folder case-association hints |
| [ARCHIVAL_COVERAGE_GRID.csv](output/ARCHIVAL_COVERAGE_GRID.csv) | 73 year-cells across 1789–1861 including 61 additional systematic years |
| [ARCHIVAL_SURVEY_ROUTES_1789_1861.csv](output/ARCHIVAL_SURVEY_ROUTES_1789_1861.csv) | 438 **planned, not searched** archival routes (six per year) |

The complete Opus ZIP (207,604,486 bytes, SHA-256 `1fbbd45e9a8846a955cbdcaa5bba2b0f138c10c80049c5bb6063197f6ac62d47`) and original-image companion (358,846,280 bytes, SHA-256 `5ece42b87164b3d8422e53fba554a28b5f644362cea920b72c7996a8e0b88e9a`) are preserved through Git LFS under [releases/opus_stage11_complete](../../releases/opus_stage11_complete/). Full-member verification is reported in Stage 20 and is reproducible by the [recovery workflow](../../.github/workflows/stage20-opus-recovery.yml); GitHub Actions run [39051699089](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39051699089) concluded successfully.

## Rebuilds and scientific gate

In a working Git checkout with complete LFS payloads, run:

```sh
python research/stage20/code/extract_full_opus.py releases/opus_stage11_complete/OPUS_STAGE11_FINITE_STATUS_DELTA_COMPLETE.zip research/stage20/output/OPUS_FULL_844.jsonl
python research/stage20/code/verify_opus_media.py releases/opus_stage11_complete/OPUS_STAGE11_FINITE_STATUS_DELTA_COMPLETE.zip releases/opus_stage11_complete/OPUS_STAGE11_EVIDENCE_ORIGINALS.zip research/stage20/output
node research/stage20/code/build_conversion_bridge.mjs --full-opus research/stage20/output/OPUS_FULL_844.jsonl --check
node research/stage20/code/extend_early_ranger.mjs --check
python research/stage19/code/test_excavators.py
```

The default Node build (without `--full-opus`) only builds the 304-case baseline and **does not match the published full-844 output**. Pass `--full-opus` when checking or regenerating this published version. The converter compares each of the three frozen source CSV's **actual Git blob SHA-1** against a pinned value and halts on any input drift. The Opus extractor preserves human-readable reviewer prose while retaining structured originals when the upstream notes are arrays or dictionaries.

To create one countable legal-lifecycle dossier, the project still needs a verified original text and complete operative-clause inventory; a source-backed first effective cessation of every relevant clause for a NO (or a continuing operative predicate as of 2026-10-14 for a YES); intervening events; savings, accrued rights, and adverse sources; and an **independent human reviewer** checking and approving the frozen claim under [Stage 19's gate](../stage19/CLAIM_SCHEMA.md). The workbench exports `eo-conversion-research-proposal/v1`, which cannot pass certification. The current **independently reviewed whole-lifecycle count remains 0**, and reaching 25% of the 14,972-item *working* bibliography requires 3,743 qualifying dossiers, subject to historical census revision.

See [Stage20 production report](STAGE20_REPORT.md), [early ranger protocol](EARLY_RANGER_EXTENSION.md), and [moving progress tracker](../progress/README.md).
