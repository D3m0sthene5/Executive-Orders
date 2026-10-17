# Stage 17: scientific evidence and legal-history reconstruction

This directory contains the reproducible **Stage 17 research implementation** for *The Afterlife of Executive Orders*, cutoff 2026-10-14. The repository's existing Git LFS archive retains earlier inputs and their provenance; Stage 17 does not modify that archive.

## Work performed

- Transactionally rebuild Stage 16 and import the 540 Opus Checkpoint 2 accepted legacy determinations, preserving 531 held cases, 414 unprocessed, 155 conflicts and all 747 status-work records. Their findings remain **AI-reviewed and source-reinspection-pending**, not human certified.
- Preserve all original Stage 11 rows, all Stage 16 research episodes and events, and the two EO 12553 quarantine records.
- Add research on EO 10084 and its five amendments (EOs 10098, 10118, 10136, 10158, 10174), distinguishing four statutory regulatory groups and their distinct sunsets.
- Add source-reviewed temporal clauses on Puerto Rico acting-judge EOs 10035, 10097, 10188, 10310, 10517 and 10599, and ceremonial EOs 9896 and 11481. Individual prospective mandates expired, but durable consequences remain analytically distinct.
- Add five candidate 1789–1790 unnumbered catalogue references from visual inspection of Clifford Lord's scanned page 23. **Not counted** as authenticated unique original orders.
- Build a review docket for all 15,010 historical bibliographic rows: the CLI generates self-contained HTML for any identity. Reviewer choices export JSON, and the importer validates claim fingerprints/versions and imports transactionally. No human verification is inferred from the interface. Test-only round trip is performed on a disposable DB copy.

## Repository / archive boundaries

`EO_STAGE17_CONSOLIDATED_INPUTS_2026-10-16.zip.part01` and `.part02` are Git LFS pointers in ordinary file previews. `git lfs pull` obtains the actual byte parts. Existing `restore_archive.py` validates the 2.966 GB restored input archive. The Stage 17 build consumes two individual ZIPs inside that consolidated archive: Stage 16 and Opus Checkpoint 2. Its *separate Opus original-image companion remains absent* and cannot be described as verified.

## Rebuild (Python 3.11+, standard library)

After `git lfs pull` and `python restore_archive.py`, extract the consolidated archive. Locate the exact input files and run:

```
python research/stage17/code/prepare_legal_facts.py  # regenerate explicit source and legal-fact JSON
python research/stage17/code/build_stage17.py --stage16 /path/to/EO_STAGE16_SCIENTIFIC_RECONSTRUCTION_2026-10-16\(1\).zip --opus /path/to/OPUS_STAGE11_CHECKPOINT2_SUMMARY.zip --bridge-script research/stage17/code/build_stage17_bridge.py --out ./local_stage17_output
python research/stage17/code/review_docket.py dossier ./local_stage17_output/data/AFTERLIFE_STAGE17_CANONICAL.sqlite EO:10084 --html ./local_stage17_output/EO10084_REVIEW.html
```

`prepare_legal_facts.py` is included to show the originating case-specific legal operations; the committed JSON files are the pinned evidence ledger used by the deterministic builder. Source URLs, dates, transcription grades and absent originals are explicit. Do not increase human-certified statistics without submitted and imported human review JSON.

## Research confidence

The provisional v2 coverage is 268 YES / 2,787 NO / 11,917 UNKNOWN among 14,972 working proxies (20.404756%). It is not an estimate of all historical executive orders or the proportion still in effect. Human independently certified legal claims: **zero** on this release. The original first-cessation question remains mostly unanswered.

See `research/stage17/reports/STAGE17_REPORT.md`, `research/stage17/sources/verified_web_source_references.json` and `research/stage17/sources/adjudicated_legal_facts.json` for the bounded legal conclusions and citation limitations.

## Durable outputs and review

The 92 MB canonical SQLite is distributed in the **Stage 17 verified release ZIP** and the smaller compressed database pack, both available from [`research/releases/`](../releases/README.md) in GitHub. The source code, pinned evidence facts, executable claim importer, and QA results are versioned here; the earlier 2.966 GB consolidated source archive remains in LFS. Restore with `python research/releases/restore_releases.py --all --decompress --out restored_research`. The large original LFS payloads have a separate verification status in [`MIGRATION_STATUS.md`](../../MIGRATION_STATUS.md).

The reviewer may open a generated HTML dossier, select individual claims, record a rationale and choose **Export JSON**. The standard-library importer verifies the current claim fingerprint and inserts the review in one SQL transaction. Never distribute or import the test fixture as a human approval.
