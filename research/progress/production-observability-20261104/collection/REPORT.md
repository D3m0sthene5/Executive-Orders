# Supported usage normalization in the existing Hamilton consumer

Hamilton now accepts the supported Claude JSONL export already read by Geddes,
preserves revised stream/final records sharing an event UUID, and exports the
existing NEYMAN effort receipt with explicit caller metadata. This closes a
concrete ingestion gap without a telemetry service or scientific schema change.

Base inspected: `54db2cf5948d7c0cdd91c8f66a96349224aee6a1`. Read-only dependencies
were fetched at that exact SHA. Geddes, NEYMAN, Junto and Hamilton `job.py` remain
byte-identical to the fetched Git blobs. Changes are confined to Hamilton
`profile.py`, `test_profile.py`, `README.md`, `needs.txt`, and this collection folder.

## Supported contract and existing ordinary route

- Hamilton already provided cautious pricing, TTL categories and a Junto adapter.
  Its loader discarded updates sharing an event UUID before reconciliation; the
  correction deduplicates exact event bytes and then reconciles stable agent/call
  identities. Final output usage must actually be present to certify completion.
- Anthropic fresh input excludes cache reads and cache creation. Aggregate cache
  creation includes TTL details; the receipt exports the aggregate once. Missing
  TTL remains unknown. Reasoning is included in output and never added again.
- Conflicting final snapshots, missing identities, invalid counts, inconsistent
  cache totals, explicit pricing-model mismatches and incompatible late streams
  refuse normalization. Caller occupation must contain all observed call-usage
  timestamps. Unknown billing, possible-call denominator and active labor remain
  explicit. Stable shared membership does not allocate observed cost per order.
- NEYMAN's existing `diagnose.py` already deduplicates usage IDs and unions worker
  intervals. `after_completion.py --effort` and ordinary `kit.py complete
  --diagnostic-effort` already retain the receipt through explicit pinned inputs.
  No claim-kit/NEYMAN code was changed. Default Hamilton `job.py` still only runs
  regressions and reconciles historical profiles; it lacks raw logs and observed
  occupation intervals and therefore cannot automatically collect production.

## Verification and measured overhead

`python3 -I jobs/hamilton-token-audit/test_profile.py` passes **26 tests** (12
existing, 14 added), including the actual NEYMAN importer/diagnosis functions.
An independent engineer identified interval, aggregate-final, reasoning-final,
late-stream, price-model, dated-price and mixed-model refusal gaps; these were corrected and regression
cases retained. Independent final adjudication is recorded by the coordinator.

The direct CLI acceptance can be reproduced without network/model calls:

```sh
python3 -I research/progress/production-observability-20261104/collection/replay.py --out /tmp/NEW_UNUSED_DIRECTORY
```

`retained-cli-final-v2/REPLAY_RECEIPT.json` records exact implementation hashes,
commands, outputs, measured intervals and input digests. This **synthetic
engineering fixture** has an initial stream, a final update and an exact duplicate,
then imports the create-only effort receipt through unchanged native NEYMAN CLI.
Two blocked members share one usage record. Input 3/cache-read 5/cache-create
7/output 11/reasoning-subset 4 survives once; session totals are not added. The
60-second worker interval is fixture data, not measured production labor. Active
labor is unknown. No dossier becomes ready; cost per newly ready dossier is null
(undefined), not zero. It establishes integration, not historical token accuracy,
research productivity or savings.

The final engineering replay occupied `2026-11-04T09:47:21.240543+00:00` through
`2026-11-04T09:47:21.390534+00:00` (0.149997 seconds). Its Hamilton
load/normalize/hash portion took 0.001261 seconds for 1,112 bytes. These are one
small deterministic replay, not a representative collector performance estimate.
Output serialization is excluded from Hamilton's collector timer and included in
the enclosing replay. The observer made zero model API calls.

Earlier failed attempts remain in `retained-cli-replay/` (isolated Python prevented
NEYMAN sibling imports) and `retained-cli-replay-v2/FAILED_COMMANDS.json`
(absolute manifest rejected; native importer requires repository-relative input).
The harness now uses documented `python -B` for native NEYMAN and a relative
manifest. Successful intermediate v3 is retained separately from final source pins.

## What remains unavailable

No legitimately available raw historical provider-call export was supplied.
Published Geddes/Apollo/Erasmus CSV aggregates cannot recover stream/final
revisions, missing per-call categories, original message identity, cache TTL,
reasoning or coordinator costs. Geddes's existing first-usage summation and
600-second-gap active-time estimate were inspected, not retroactively corrected
or reused as observed labor. Existing historical values remain attributed to
their original method. Hamilton cannot discover a possible-call denominator,
invoice, plan usage, review costs or unrecorded attempts from those aggregates.

Full Hamilton profiles remain private because legacy context diagnostics can
contain paths/tool labels. The new receipt excludes transcript text and source
paths; caller identifiers/descriptions still require release review. Only synthetic
fixture profiles are retained here. No hidden controls/private transcripts are used.

Actual engineering model: **gpt-6.1-sol**. Whole-session start/end occupation,
active labor, model token counts and cash are unavailable to this worker; no
estimate fills them. Observable deterministic intervals and exact subprocess
commands are retained in replay receipts. Tools used: read-only GitHub file fetch,
local exec, local patches and parent/reviewer coordination. No commits, remote
workflows, Claude quota consumption, branch updates, reservations, assignments or
production writes occurred. The coordinator owns Kean registration and handoff.
