# Apollo rejected-claim inventory

Deterministic inventory only. This package indexes the 40 genuine rejected claim versions from the Apollo run; it does not edit or retry claims, decide legal questions, source the six completion drops, or publish findings.

## Rebuild and contents

Run from the repository root:

```sh
python3 research/excavator/claude-geddes-2026-11-01/inventory/build_inventory.py
```

`MANIFEST.json` contains all 40 rows and their exact review defects, source JSONL path/line, source-file and record hashes, and prior claim path/line/file hash/record hash. The three `batch-*.jsonl` files are grouped without mixing tracks: n01 has all 6 NRA rows; g01 has 20 general rows; g02 has the remaining 14 general rows. The generator selects blind rejections excluding the planted claim hashes, then adds rejected genuine versions from `AFTER_REVEAL.jsonl`; this yields 35 blind genuine rejections plus five after-reveal genuine versions. It verifies the target count in the manifest. The five after-reveal EO versions are 6876, 8163, 10103, 10915 and 12095.

The result is 6 NRA and 34 general claims, matching the source report. EO 6471A and 7016 are excluded under open Kean ask A-20261031-1. The six completion drops are identified in the manifest for custody only: EO 12921, 12987 and 8937 have absent mirror/PDF custody; EO 8168, 10570 and 10346 have quote/checker OCR mismatches. No acquisition or sourcing was performed.

## Mismatches and blockers

- The report's headline arithmetic is reproducible: 300 reviewed proposals = 260 completion submissions + 40 rejected versions; 260 submissions = 254 filed + 6 mechanical drops.
- The blind review JSONL contains 55 rejected records because it includes 20 planted controls. Those 20 control-version records are not treated as 20 additional genuine rejected claims. Five genuine versions were instead rejected in after-reveal records, producing the exact 40-item retry inventory.
- The five after-reveal versions are source-recorded separately from the planted hashes; the inventory resolves their genuine claim bytes by exact record SHA-256 in the retained proposed-claims files.
- No unresolved review-to-claim hash or claim-file-pointer mismatch remains in the 40 rows; the generator found all exact claim records and verified their file and per-record hashes.
- Controls' key/seed material is not used to infer legal validity. Only completion's planted claim hashes are used to exclude seeded versions from the genuine inventory.

## Retry preparation and telemetry readiness

`kit.py prepare --help` now imports successfully with `jobs/norton/model.py` present. `kit.py prepare` is bounded to 1–50 distinct IDs, requires a new destination below `research/`, refuses conflicting owners/reservations, and validates each dossier fingerprint (and status against the compiled INDEX for ordinary decided dossiers). It pins preparation, assembler, preflight, policy, held-source, prior-research and relevant Valla context; undecided cases additionally freeze status-history and compiled-summary evidence. Source supplements require the parent packet and same-agent routing described in the packet. The current workspace has no `jobs/claim-kit/output/INDEX.json` or compiled dossier output, so a real prepare has not been attempted. Materialize and validate the retained compiled output and its complete preparation dependencies on the intended base; regenerate only if those retained outputs are stale. Then prepare each retry batch into a fresh destination while respecting locks and prior ownership. The required Sonnet/Opus execution route is also unavailable in this session. No prepare was run here.

Apollo's original packets and claim bytes are present, but they are not a substitute for a fresh prepare against the intended current repository pins.

Apollo's `tools/moon_telemetry.py` deterministically parses per-agent transcript JSONL files named `<agent-id>.output`, keyed from `COORDINATOR_LOG.txt`, and emits token/tool/time CSV and JSON summaries. The existing `TELEMETRY.csv` is present. The per-agent transcript files are not in the hydrated Apollo tree, so the extractor cannot independently regenerate or audit that CSV from this workspace. The CSV and report identify Claude Sonnet 5.5 producers and Claude Opus reviewers. This inventory used the configured gpt-6-luna agent for deterministic bookkeeping only, not as a producer or reviewer; this worker's tokens are unavailable, and no scientific judgment was performed. The start wall marker was unavailable, so elapsed time is null rather than reconstructed.
