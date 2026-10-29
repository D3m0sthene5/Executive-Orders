# Matched checkout proof, limits preserved

The nominated production selection is exactly `JOBS=readiness-tracker`. The old and repaired arms always use the same pinned tree, selected job, empty job cache, available object pool, and LF checkout configuration. Neither arm executes the scientific job. The actual tracker and its native `working_text`, `factual_events`, and NORTON model import closure are imported in both worktrees without calling `tracker.main()`.

`run_matched_checkout.py` compares the historical cone checkout of `.github`, `jobs`, and `HANDOFF`, followed by freshness preparation, with the actual current workflow bootstrap followed by the actual materializer. It checks every required file against its pinned Git blob ID and requires equal complete freshness input maps. Required files have identical bytes in both arms. It also exercises tracked edits/deletions, staged additions, and untracked additions in an isolated worktree. The measured worktrees have no remotes, and all Git objects come from the same warm local alternate object pool. The script writes its requested receipt; all checkout operations and working-change probes run in isolated repositories, leaving the source index and branch untouched.

## Actual existing outputs, bounded local result

`LOCAL_PROJECTION_INITIAL.json` pins production source `bc65c165a2d192a6949f16b5ebf5ab5e545d61f5` and a separate projection commit containing only bodies already present locally. Missing production files are omitted, never replaced with invented payloads. This is a real Git materialization comparison of actual existing code, data, and output bytes on that projection; it is not complete production availability.

| Arm | Materialized files | Worktree bytes | Existing job output bytes | Local elapsed |
|---|---:|---:|---:|---:|
| Historical broad checkout + prepare | 14,923 | 318,427,714 | 109,047,683 | 1.912 s |
| Current bootstrap + compatibility materializer | 14,923 | 318,427,714 | 109,047,683 | 3.029 s |

All 14,887 required files match their Git blob IDs in both arms, and freshness maps are exactly equal. The actual pinned native imports pass in both. All four working-change cases pass. The current production selection is unaudited and retains compatibility fallback. **This matched sample establishes no byte or elapsed-time saving.** It preserves the negative result instead of manufacturing a narrow certificate.

At that production pin the metadata lists 97,182 tracked paths; 14,938 have locally available bodies. The 72,553 job output paths include 6,768 locally available paths totaling 109,047,683 uncompressed Git blob bytes counted by path, and 65,785 missing paths. The metadata inventory uses `cat-file --batch-all-objects` and plain `ls-tree`; it never requests sizes of missing blobs. Missing object sizes and cold transfer bytes are unknown. There is no extrapolation from local availability to the repository's full size.

`LOCAL_COMPLETE_BLOCKED.json` preserves a failed complete-production preflight: the historical broad arm requires 65,787 unavailable paths including root files. No missing bodies were fetched. A subsequent complete production run needs the old checkout's required bodies prewarmed by its caller. No full multi-gigabyte transfer was performed merely to measure this result.

## Bounded production-shape fixture

`run_production_shape_fixture.py` uses actual runner/helper/freshness code and actual tracker/native sibling modules with small synthetic records in the real production path shapes. It covers provider `FRAGMENTS.jsonl` nested `data` references to `text_path`, `raw_path`, and `review_path`; `SOURCES.jsonl` references to held bytes and capture custody; claim `source_refs`; `after.txt` predecessor generations; and the selected job's previous successful output. The 48 required pinned blobs and complete freshness maps match between arms. A 2 MiB unrelated output is omitted by the synthetic certificate. This certificate is created only inside the disposable fixture and grants no production eligibility.

The actual runner executes a deliberately failing fixture `job.py`, retains its candidate attempt with failed status, and leaves the prior successful output/status byte intact. In both matched arms the real tracker working-text Index discovers one exact nested fragment; working-text policy opens the expected text body and returns only the mandatory `working_text:disclosure_required` hold. Native NORTON `source_span(require_bytes=True)` opens both text and raw bodies and passes identity/hash/quote checks. Audit events distinguish indexing, policy reads, and source-span reads from the final expected-body assertion. This is fixture consumption, never a reviewed legal claim. The receipt distinguishes the fixture payloads from the exact copied native code hashes. The fixture's byte reduction is solely a mechanism result. `PRODUCTION_SHAPE_FIXTURE_INITIAL_BYTE_ONLY.json` retains the initial receipt exactly; `FIXTURE_CORRECTION.json` qualifies its malformed top-level fragment fields as byte-availability evidence only and pins the corrected receipt. The initial import-only check established no provider semantic read; the corrected nested record and native trace establish the bounded reads described above.

## Read-only production history

`WORKFLOW_HISTORY.json` records the inspected recent runner history and bounded log excerpts from completed run `40908344773`, pinned `73d99f666573ee10f5b1ff2ada60f7d9331c3952`, job `123569160194`. That run selected 25 jobs, including claim-checker and readiness-tracker. Historical checker elapsed time was 963.8 seconds and tracker ran with tests. Those observations justify a real production selection shape; they are not an old/new matched checkout comparison and cannot be attributed to this repair.

## Reproduce

From the repository root, using a directory outside tracked reports for scratch:

```sh
MATCHED_PROOF_SCRATCH=/tmp/runner-proof python3 -B research/progress/sol-runner-friction/production/proof/run_matched_checkout.py --source . --receipt /tmp/MATCHED_PRODUCTION.json --local-projection
MATCHED_PROOF_SCRATCH=/tmp/runner-proof python3 -B research/progress/sol-runner-friction/production/proof/run_production_shape_fixture.py
```

For complete pinned production, omit `--local-projection` after separately prewarming the source's historical cone checkout and calling `result_freshness.prepare('readiness-tracker')`. Keep that untimed acquisition separate from the measured comparison; the script itself cannot fetch missing objects. A reported compatibility fallback remains a blocked narrow rollout, even if all parity checks pass.

No scientific output, legal conclusion, readiness count, source grade, review gate, or adoption was changed. Model: actual `gpt-6.1-sol`; model tokens, cache tokens, billing, and active labor telemetry are unavailable. Local wall clocks are single warm-object observations, not production startup, network-transfer, or total research-cost measurements.
