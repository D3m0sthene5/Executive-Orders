# Stage 20 — conversion excavator (2026-10-17)

This release resumes the interrupted Codex lifecycle work. It preserves the original 3,359 provisional classifications and uses the 304 accessible complete-Opus addition narratives to make them actionable without equating a provisional classification with a verified legal history.

## Reusable work produced

- `output/CONVERSION_INDEX.csv`: **3,359** labeled cases indexed with source and scope flags, triage lanes, expected next research steps, and status provenance.
- `output/OPUS_NOTE_LEADS.jsonl`: **304** full, verbatim Opus reviewer narratives and explicitly outstanding inferential issues. **297** assert footprint completeness (AI claims only); **110** mention at least one ISO-formatted date (cause/date meaning not established).
- `output/SHARED_SOURCE_REFERENCE_QUEUE.csv`: **32** multi-case citation clusters, such as statutes, EO amendments, and codified regulations. A shared citation is an acquisition opportunity, never proof of shared termination.
- `output/CONVERSION_WORKBENCH.html`: offline research interface, linked verbatim review narratives, date/citation leads, and research-proposal-only export. It cannot generate qualifying independent human review records.
- `code/build_conversion_bridge.mjs`: deterministic Node 18+ standard-library builder for both partial 304 and full 844 extracted Opus datasets.

The full complete-Opus archive has **844** accepted AI decisions (212 YES / 632 NO). The **540** overlapping Stage 17 records require extracting their complete Opus reviewer narratives. The research ZIP is at `releases/opus_stage11_complete/OPUS_STAGE11_FINITE_STATUS_DELTA_COMPLETE.zip` in Git LFS. A separate **358,846,280-byte media companion** was uploaded to the repository on 2026-10-17 at commit `e41abf0`. Both LFS pointers are visible; their full contents still require retrieval, hash checks and source-to-case reconciliation. The media companion has expected SHA-256 `5ece42b87164b3d8422e53fba554a28b5f644362cea920b72c7996a8e0b88e9a`.

## How to reproduce

From the repository root:

```sh
node research/stage20/code/build_conversion_bridge.mjs
node research/stage20/code/build_conversion_bridge.mjs --check
```

The `--check` mode regenerates in memory and compares five output files byte-for-byte. For the complete 844 records, first restore the verified ZIP through `git lfs pull` and run `python research/stage20/code/extract_full_opus.py FULL_OPUS_ZIP /tmp/opus844.jsonl`, then pass `--full-opus /tmp/opus844.jsonl` to the Node builder. The complete version rechecks the 304 overlapping statuses and reviewer notes before publishing any recovered full notes. Neither extractor imports statuses into the canonical SQLite or claims that the separate media ZIP has been audited.

## Scientific meaning

Every date in the conversion index is an unclassified mention. Every cited EO, CFR section, statute and review keyword is an unverified acquisition lead. Stage 19's `eo-lifecycle-claim/v1` gate still requires authentic original, full operative clause inventory, dated events or current predicates, earlier-cessation search, savings, and independent human review bound to the frozen claim. A Stage 20 `eo-conversion-research-proposal/v1` is structurally ineligible for lifecycle certification. The headline count therefore remains **0 / 14,972**, with 3,359 / 14,972 (22.435212%) retained as provisional YES/NO progress, not lost.
