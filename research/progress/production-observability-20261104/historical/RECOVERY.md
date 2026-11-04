# Published historical production recovery

This recovery uses main `600ae3018f71025b3e53dc8538b8f92e6e159b76` and records the dashboard proposal pin `54db2cf5948d7c0cdd91c8f66a96349224aee6a1`. It neither resumes nor instruments the protected Opus run. The 149 public source files total 2,409,971 bytes; each has a Git blob identity and SHA256 in `SOURCE_MANIFEST.json`. Raw native files are excluded from publication. Outputs contain no planted-case markers or per-case reveal labels.

The useful recovered unit is a worker aggregate joined through its batch to exact reviewed claim versions and native completion receipts. Tokens remain at worker/batch scope. No cash, active labor, per-order allocation or comprehensive project bill is inferred.

| Recovered observation | Apollo, Oct 31 | Erasmus, Nov 2 |
|---|---:|---:|
| Published worker IDs | 38 | 20 |
| Published API-message count | 2,700 | 1,047 |
| Fresh-input tokens | 5,466 | 2,124 |
| Cache-read input tokens | 496,350,796 | 182,772,589 |
| Cache-creation input tokens, TTL unknown | 13,313,052 | 3,669,178 |
| Output tokens | 2,407,390 | 926,723 |
| Genuine reviewed versions | 300 | 58 |
| Genuine review rejections | 40 | 5 |
| Published completion runs | 19 | 8 |
| Completion attempted memberships | 444 | 64 |
| Submitted after review, at completion | 260 | 53 |
| Published claims | 254 | 52 |
| Mechanical completion rejections | 6 | 1 |
| Sum of deterministic completion wall seconds | 2,118.228 | 458.946 |

Apollo's 184 final blocked memberships include 144 producer blocks and 40 rejected reviews. Its producer-submitted 300 and completion-submitted 260 measure different boundaries. The published report's opening prose says 241 general orders, but its results table and native totals give 251 general plus 193 NRA = 444. Native receipts govern the derived counts.

Erasmus's 64 completion memberships include retries. Joining exact genuine reviews and native outcomes by instrument finds all 40 rejected Apollo members: 42 completion memberships, 32 eligible distinct members, nine blocked memberships and one mechanical rejection. The other 20 Erasmus publications correct already-filed Apollo versions. The report's claim of 32 recovered rejects plus 20 corrections is consistent with the joins. `OUTCOMES.json` retains version hashes and exact-match booleans; it does not publish which cases were controls.

Each eligible completion version matches a genuine upheld review of the exact claim SHA256. Each native publication reports written=true and agrees with the tally count. Publication file SHA256 values are retained as native claims, not re-attested by fetching all canonical claim bodies. Each tracker replay explicitly says canonical outputs were not modified.

All 254 Apollo selected versions and all 52 Erasmus selected versions transition from not ready to ready in their separate completion replays. Those are historical replay transitions. A correction can transition too because the replay's baseline is reconstructed and its checker context differs. These 52 Erasmus transitions therefore do not establish 52 newly created dossiers. Neither summing replays nor dividing incomplete worker tokens by them establishes complete cost per additional ready dossier. Current canonical readiness and causal campaign net change require separate baseline/final evidence.

Two report discrepancies remain explicit. Erasmus says 27 agents including resumptions; its roster and telemetry contain 20 unique worker IDs, with no resumption segmentation. Erasmus says 10 controls caught; this bounded source inventory contains nine published blind/reveal pairs, eight completed tally controls and one reviewed batch with no published completion. A tenth control is not manufactured. Aggregate completion counts have their narrower eight-run scope.

## What the instruments actually measure

`jobs/geddes/telemetry.py` labels the most frequent observed model per worker, rather than preserving call-by-call model mixtures. Historical rows identify Sonnet and Opus producers, Opus reviewers, and one builder of each label in Erasmus. Coordinators are excluded. Builder costs remain visible even though builders have no filing completion; the rejected uncompleted review batch likewise remains in the usage denominator.

The exporter deduplicates usage on the first message ID, turns missing token categories into zero, and counts tool-use blocks without deduplicating tool IDs. A later final usage update for the same message is ignored. Missing message IDs collapse together. Private transcripts are unavailable, so the historical figures cannot be corrected or certified as final provider usage. These are published transcript-derived aggregates with unknown omissions; a coverage fraction of all possible calls is unavailable.

Four deterministic synthetic assertions in `probe_contracts.py` establish the contract boundary. For one message with a streamed output count of 1 and final count of 9, Geddes retains 1 while Hamilton retains 9. Geddes counts the repeated tool ID twice, renders absent input as zero, and collapses two missing-ID fixture events into one API message. This proves parser behavior on the fixture; it does not quantify historical error.

`jobs/hamilton-token-audit/profile.py` version 2 already retains missing token categories, separates cache-write TTL when available, reconciles repeated observed usage fields, tracks final-output markers, and separates cash from API-equivalent valuation. Its repeated-context attribution remains an estimate using characters/4 and a first-call setup proxy. Diagnostic views overlap and must not be added to its cause total. It does not supply the missing historical transcripts or make estimated context attribution causal.

The CSV's `active_seconds` is a sum of consecutive event gaps no longer than 600 seconds. `RECOVERED.json` renames it `gap_filtered_event_seconds`. A transcript envelope spanning a quota pause is not model reasoning; omitted long gaps do not identify all waiting, and retained short gaps can also contain waiting. Neither this proxy nor deterministic completion wall time measures active worker labor or exclusive compute. Sums across overlapping workers are not occupied campaign wall time.

## Five views and the remaining boundary

| View | Recovered | Still unavailable |
|---|---|---|
| Tokens and money by phase/role | Worker/batch/role and modal-model tokens; builder and failed-work coverage | All coordinator usage, separate phases, cache TTL, billing/cash, dated applicable prices, final-usage completeness |
| Repeated evidence/context | Aggregate cache reads and Read tool counts | Per-load source/page digests, resets, context membership, avoidable repetition, marginal cost of repetition |
| Late blockers/retries | Exact genuine version reviews, final outcomes, all 40 Apollo-reject retry memberships | First blocker detection/cost, all abandoned attempts, missing rejected canonical hashes in completion |
| Cost per additional ready dossier | Exact batch→version→review→completion linkage and separate historical replay transitions | Full campaign cost, causal net ready denominator, observed per-order tokens or dollars |
| Waiting/compute/worker time | First/last event envelopes, gap-filtered event proxy, deterministic completion wall time | Active labor, exclusive compute, queue waits, exact quota pause intervals from CSV, overlap-resolved critical path |

## Useful next changes

First repair Geddes's usage contract by reusing Hamilton's missingness and repeated-usage rules: require stable call identity, reconcile partial/final snapshots, retain finality and model mixtures, deduplicate tools by stable ID, expose missing category counts and preserve cache-write TTL. Do not silently rewrite historical totals from aggregates. An unknown-ID record should remain an explicit coverage exception.

Then link ordinary worker aggregate IDs to exact native completion versions and publication receipts at batch scope, including rejected, blocked and builder-only batches. This recovery validates that existing receipts support the join. Collect provider categories, actual model, role and a small phase counter prospectively; retain coordinator overhead. Do not require raw transcripts or control identities in the public roll-up.

The data supports inspecting small repair-batch overhead, but does not establish that batching or slimming a packet lowers complete cost. Resubmission, case mix, shared analyses and missing coordination costs confound that comparison. A bounded prospective ordinary-work measurement with complete roles and real outcome versions would resolve more than pricing these incomplete historical totals.

## Reproduction and publication boundary

Run `python3 -I research/progress/production-observability-20261104/historical/recover.py --source-cache /path/to/exact-public-sources`, then run `python3 research/progress/production-observability-20261104/historical/probe_contracts.py --source-cache /path/to/exact-public-sources`. The cache preserves repository-relative source paths listed in `SOURCE_MANIFEST.json`. Materialize missing files through a supported GitHub exact-ref file read, preserving bytes. Git blob and SHA256 checks reject transport changes. Without a cache the script reads already available local Git objects with lazy fetching disabled; missing evidence fails explicitly. No network operation or scientific mutation occurs in the recovery script.

The publication allowlist is `.gitignore`, `recover.py`, `probe_contracts.py`, `SOURCE_MANIFEST.json`, `RECOVERED.json`, `OUTCOMES.json`, `CONTRACT_PROBES.json`, `RECOVERY.md`, `COSTS.json`, `VALIDATION.json`, and `KEAN_FINDING.json`. The `inputs/` and `.source-cache/` directories are ignored and must remain untracked. They contain native source evidence and are not public deliverables. Root owns registration and integration; no commit, main update, protected-run change, production workflow, quota use or assignment was made here.
