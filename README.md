# Executive Orders

**Agents start here:** read [`HANDOFF/`](HANDOFF/README.md) for the latest notes between Claude, Astra and Codex, and add your own before you stop. Run scripts that are too big for a chat's container through the [shared runner in `jobs/`](jobs/README.md).

**Current dashboard:** [Research progress and recent work](research/progress/README.md) · [Generated counts, receipt freshness, and source generations](jobs/daily-digest/output/DASHBOARD.md).

**Working progress measure:** the [readiness tracker](jobs/readiness-tracker/output/TRACKER.md) counts orders that are ready for human review (every machine research step done or searched to the end) and lists the single actions that unblock the most orders. Human verification is counted separately.

**Research archive entry point:** [MIGRATION_STATUS.md](MIGRATION_STATUS.md) records the verified publication state and recovery steps. See [PROGRESS.md](PROGRESS.md) and the [moving progress tracker](research/progress/README.md) for research status, remaining effort, and planning windows; the [artifact index](research/ARTIFACT_INDEX.json) for provenance and SHA-256; and the [release guide](research/releases/README.md) for restoration.

This repository holds the consolidated inputs, versioned public research releases, workpapers, and reproducibility tools for **The Afterlife of Executive Orders**. The research remains provisional and contains no independently human-certified legal findings.

**Human-certified whole-lifecycle progress:** the published certification register remains **0 / 14,972**. Machine research readiness, filed claims, and adopted provisional statuses are reported separately in the current dashboard. The earlier 22.435212% was the October 17 provisional-label inventory. A complete case must account for the original operative scope, whether and when it first ended, the actor and legal mechanism, surviving effects or a continuing predicate, counterevidence and independent review. See the [moving tracker](research/progress/README.md) and [Stage 19 excavators](research/stage19/README.md).

The original ZIP is **2,966,329,767 bytes**, above GitHub's per-file limit. Its two byte-exact parts are stored with Git LFS:

| File | Bytes | SHA-256 |
|---|---:|---|
| `EO_STAGE17_CONSOLIDATED_INPUTS_2026-10-16.zip.part01` | 1,500,000,000 | `42dc6f48c13550647896a708ed0bc5be27acc271c81509cc361588137b2fcef8` |
| `EO_STAGE17_CONSOLIDATED_INPUTS_2026-10-16.zip.part02` | 1,466,329,767 | `7f587b22e38c029f749bdca5d2c9381710c850775128421d8ece525364ca13a1` |

To restore the original ZIP after cloning with Git LFS installed:

```sh
git lfs pull
python restore_archive.py
```

The restore script verifies the complete ZIP's SHA-256: `52edb4d40d07fb713514968684f1adeb7cd65a52b9f89c9216fd44c590fc8775`.

The ZIP contains the named Stage 16 and Opus Stage 11 checkpoint releases, the provisional Stage 17 bridge, unique prior source packages, all ten Stage 2 source volumes, the verified Stage 3 archive, and the Clifford Lord scan. Read its `README.md` and `manifest.json` after extraction for provenance and exact file hashes.

**Later source-recovery update:** Stage 20 recovered the separate Opus original-media companion and verified its 496 listed PDF/image members against the manifest. See the [integrity record](research/stage20/output/OPUS_ORIGINAL_MEDIA_INTEGRITY.json). Case-specific document attribution and legal source review remain separate obligations.

## Stage 17 — integrated scientific research (October 17, 2026)

Research source code, pinned primary-source transcripts, case-specific temporal findings, the offline human-review docket, reproducible counters and the next machine-readable historical research queue are under [`research/stage17/`](research/stage17/README.md).

The earlier ~2.97GB consolidated archive remains under Git LFS, unchanged. The Stage 12–17 public releases and compressed Stage 17 canonical SQLite are published as hash-indexed binary parts under [`research/releases/`](research/releases/README.md). The Stage 12, 13, and 15 public archives omit sealed blind-review answers. The later Stage 20 recovery of the Opus original-image companion is recorded in the integrity link above.

As of the Stage 17 canonical checkpoint: 14,972 working bibliographic identities, 3,055 legacy-v2 provisional present-status findings (20.404756% of the working bibliography), 13 new scoped provision expirations, five early unnumbered printed catalogue leads **not** added to the census, and **zero** human-certified conclusions. The separately published [complete Opus Stage 11 archive](releases/opus_stage11_complete/README.md) includes 304 further additive decisions beyond those already in Stage 17: a reconciled provisional 3,359/14,972, or 22.435212%, pending a new canonical rebuild. National all-history enumeration and whole-order first cessation remain largely unresolved. These quantities must not be interpreted as survival rates.

## Stage 18 — direct-source and early-history pilot

[Stage 18](research/stage18/README.md) preserves official printed pages for all 14 Stage 17 pilot orders, crosswalks 13 scoped clauses and 26 transitions to those pages, corrects two source-reading/date errors, locates primary historical representations for all five initial 1789–90 catalogue leads, and traces EO 1's provisional court to a July 28, 1866 statutory transfer as construed by the Supreme Court. It is an additive AI research layer: no new early identity or EO 1 assessment is added to the 14,972 denominator or 3,359 reconciled YES/NO numerator, and no human certification is claimed. See the [moving tracker](research/progress/README.md) for the remaining effort and planning windows.

## Stage 19 — batch causal and early-source excavators

[Stage 19](research/stage19/README.md) records the required 10-by-10 idea funnel, generates a blocker-coded queue for every reconciled decided case and source-linked packets for stratified human review, and maps multiple archival search routes from Lord chronology leads. Candidate searches and worksheet exports never change the EO census or lifecycle numerator automatically.

