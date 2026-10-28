# NEYMAN

## Optional real-production diagnosis

`production_receipts.py` and `diagnose.py` adapt **actual** research/completion
receipts. They complement the offline prerequisite pilot below. The historical
`neyman.observation/1` format, frame sampler, pilot and default `job.py` are unchanged.
This CLI performs no network calls, model dispatch, acquisition, canonical writes,
tracker rebuild, or ledger mutation.

```sh
python -B jobs/neyman/diagnose.py --repo . \
  --manifest research/neyman/production-diagnostics/2026-10-25-pr60/IMPORT.json \
  --out research/neyman/production-diagnostics/2026-10-25-pr60/replay-NEW
python -B -m unittest discover -s jobs/neyman -p 'test_*.py'
```

The output directory must be new. Inside the repository it must be a run beneath
`research/neyman/production-diagnostics/` or `jobs/neyman/output/diagnostics/`.
An external new scratch directory is also supported. Inputs are read through
repository-confined SHA-256 references; symlink escapes, stale pins, duplicate JSON
keys, nonfinite measurements and inconsistent target/version selections fail.
Output includes `DIAGNOSIS.json`, `OBSERVATIONS.jsonl`, and `REPORT.md`, with input
and implementation hashes. Reproducing a result requires its referenced metadata,
not downloading its original PDFs again. The runner does not automatically launch
this CLI on every frame refresh. Call it after ordinary bounded production or
from a separately scoped consumer with these exact inputs materialized.

The included PR60 manifest imports all nine final selections and all thirteen
completion attempts, including failures. It distinguishes an eligible reviewed
partial from a whole-case gate pass, and a complete isolated proposal from an
adopted status. Multi-order invocations and byte-identical copied receipts are
counted once. Occupied completion wall time is a union; summed machine durations
are a different quantity. Neither is producer/reviewer labor. Source checkpoints
carry author attribution, source requests and `no_route` results without implying
that a document does not exist or a search is exhausted. Referenced claim versions
must match before a checkpoint guides the selected case's diagnosis.

### Input contract

The `neyman.production-import/1` manifest has `base_commit`, `cohort_kind`, a pinned
`selection` list and `completion_receipts` and/or a pinned `completion_index`
(`COMPLETION_COSTS.json` with `invocations[].path/sha256`). Every referenced object
uses `{ "path": "repo/relative/file.json", "sha256": "64 hex characters" }`, with
an optional RFC6901 `pointer`. Selection rows use the existing PR60 fields:
`instrument_id`, `claim_sha256`, `completion`, and `publication_kind`. Native final
`TALLY.json`, `CLAIMS.selected.jsonl` and `TRACKER_REPLAY.json` are validated and
pinned. Include unsuccessful invocations explicitly; filesystem absence is not
evidence that an attempt never occurred. Only the supplied history is measured.

For unfinished work, select `{ "instrument_id": "EO:123" }` and supply a pinned
`research_attempts` record, schema `neyman.research-attempt/1`: `attempt_id`,
`instrument_id`, `assessor`, `question`, `started_utc`, `finished_utc`, `basis`
(pinned JSON references), and `outcome` (`blocked`, `censored`, `unfinished`, or
`stage_result`). Such a record establishes a reported attempt, never independent
approval or readiness. Censored and unsuccessful work stay in the cohort.
`prospective_probability` additionally requires the original frozen NEYMAN
`sample_manifest`; verify it with the existing sampler, retain unobserved members,
and do not extrapolate a convenience cohort or incomplete sample into total cost.

Optional adapters:

- `checkpoints`: pinned existing `eo-source-blocked-work/v1` records.
- `source_checks`: `{instrument_id, record: REF, raw?: REF, text?: REF,
  edition_year?: YEAR, span?: {start, end, quote}}`. Metadata identity/edition,
  bytes, hashes and exact spans are separate from source-content identity,
  complete inventory, authentication and legal adequacy. Missing bytes mean
  unavailable **in this checkout**. Reads are bounded to 32 MB per input.
- `questions`: pinned `neyman.discriminating-question/1` records with instrument,
  assessor, question, at least two distinct alternatives, `needed_observation`,
  `suggested_existing_route`, and pinned `basis`. These are attributed research
  recommendations. Reuse NORTON question references in the basis where available;
  no new question registry or source queue is created.
- `effort_receipts`: `neyman.production-effort/1` records with `events`. Each event
  has stable `event_id`, `phase` (existing NEYMAN phases), `kind` (`worker_elapsed`,
  `active`, `access_wait`, `machine`), `worker_id`, downstream `instrument_ids`,
  timezone-aware start/end, `measurement_method`, and `coverage` (`partial` or
  `complete_interval`). Optional tokens use existing NEYMAN categories and a
  stable `usage_id`. Duplicate shared events/usage count once; conflicts fail.
  Intervals union per worker/kind. Phase views can overlap and must not be summed.
  Token subtotals are observed lower bounds; reasoning may be included in output.
  Hamilton's observed usage can supply these records, but missing fields or
  totals cannot be reconstructed by this importer.
- `repair_probes`: instrument, pinned `before`/`after` native tallies, and pinned
  `before_dependencies`/`after_dependencies` hash maps (such as native INPUTS
  `/dependency_sha256`). Report eligibility transitions and changed dependencies.
  Multiple changes are inconclusive. Even one declared change leaves causal
  attribution unverified because supplied maps may omit other changes. This
  retrospective probe does not run a repair or establish hours saved.

No import earns Junto savings credit. The output is a diagnostic input to its
existing candidate/test workflow, not its sanitized legacy aggregate schema.
Do not pass it to the old finder as if it were `neyman.aggregate/1` or alter
Junto's cost/quality rules. A substantive cause needs attributed source analysis;
open tracker steps alone never establish the expensive bottleneck.

NEYMAN surveys the **known unfinished inventory** and supplies domain-specific saver hypotheses to the existing Junto system. It changes no codebook, admission, provisional status, claim, exhaustion record or human certification. Sampling guides the campaign and does not replace exhaustive research.

## Current-state integration

Implementation starts from main `ed19a06039278c10e5a3ebddccf19d2bd02ac3a2`. PR #40 (`claude/junto-1727`, inspected at `91116f879978902343dafa88490b9b19587b10da`) remains open/conflicted. Its Junto/Hamilton code is already on main; its substantial newer Llull work was inspected and was not imported wholesale. NEYMAN uses main's actual `llull.Data`, claim-kit dossiers/status leads, corpus-excavator's isolated replay, and `tracker.build`. No allocator, efficiency score, dashboard or general planner is added.

The authoritative source-of-truth inputs are per-order census and tracker rows, not the older funnel totals. `FRAME.jsonl` lists every unfinished identity once. `STRATA.json` counts actual intersections of era, provisional status, original-text state, ending/current-basis prerequisite evidence, and the full sorted set of relevant claim-kit families. Unknown dates/families/statuses are explicit. Llull's held ending **candidate** and current-law lead are mechanical preparation flags, not legal proof.

## Reproducible probability sample

`config.json` fixes seed 1727, a maximum of 24 attempts, a 30-second subprocess deadline for each attempt, and a one-MiB source-read bound. The dated manifest freezes outcomes, input SHA-256 values, selected identities, and exact selection probabilities **before** the pilot runs.

Era × status defines macro strata. Each macro receives a fixed number of sample cells. Detailed joint cells are selected by simple random sampling without replacement within each macro; one order is selected uniformly within each selected cell. For an order in cell h of macro g, inclusion probability is `(sampled cells in g / all cells in g) / population of h`. All nonempty cells have positive probability. This deliberately includes hard and unknown cases; weights must be retained. The tests check randomization frequencies and inverse-probability unbiasedness across 4,000 seeds. No product of marginal source/status probabilities is used.

A tiny sample does not measure all cells' costs. Historical convenience samples remain historical. The pilot's target estimand is the cost of an investigation **attempt**, including unsuccessful work; completion effort requires the still-missing continuation, review, correction and integration costs. Historical-census recovery outside these identities is separately unbounded and excluded from the weights.

## Effort and missingness

`OBSERVATIONS.jsonl` has preparation, acquisition, production, review, correction, coordination and integration phases, each with active agent seconds, access waiting, machine seconds, token categories and coverage. Null means unavailable, never zero. Reasoning tokens can be a subset of output tokens and are not added again. `SHARED_COSTS.jsonl` charges each shared preparation/acquisition event once and identifies every downstream use. Shared source/instrument identifiers join correlated cases even when cost telemetry is absent.

The shipped pilot performs an offline prerequisite investigation from held dossiers or undecided status leads. It checks packet fingerprints and available source text hashes, preserves missing inputs and access failures, and identifies remaining work. It cannot perform independent legal review. Its production-phase timing is a machine gap probe, not measured legal production. Deadline stops are right-censored; unsuccessful subprocesses remain observations. Missing review/agent/token telemetry prevents a defensible completion total, confidence interval or date. Reports give observed effort lower bounds and the explicit conditions/formula for future scenarios rather than a success-only extrapolation.

The current Junto configuration documents a $10 API-value round and 20% nominal exploration ($2); NEYMAN reads it, does not allocate it, and reports that no allocation to this finder or session-level billing telemetry is available. The job makes zero model API calls. API token valuation and actual cash expenditure are separate null fields. Implementation/coordinator effort outside the instrumented job is unmeasured.

## Planning-only tracker replay

`python -B jobs/corpus-excavator/measure.py --closures FILE.json --out DIR` accepts at most four named prerequisite bundles and examines singles/pairs through the **production** tracker. Each bundle lists per-order step assumptions, its origin and its explicit hypothetical premise. Status closures are forbidden. The optional `planning_closures` argument marks every resulting row `planning_only`; ordinary tracker builds are unchanged. Claims, claim-level gates and source-audit holds still control readiness. No synthetic evidence or exhaustion records are written.

The pilot checks frozen no-intervention residuals after its 24 attempts. It also replays two historical accepted batch proposals against current held metadata, reporting baseline drift, exact source hashes and residual matches. Both historical arms contain EO12720, so they are one correlated historical case. These are software consistency tests; the pilot does not acquire new evidence and cannot validate the causal effects of the hypothetical prerequisite closures.

## Junto and Llull

`jobs/junto/finders/neyman.py` is a thin registered finder with the existing `--data`, `--out`, `--run-id`, optional `--profiles` interface. It accepts only `NEYMAN_AGGREGATE.json` with a fixed whitelist schema. The consumer stages that sanitized file outside the repository as required by Junto. No raw transcripts are needed.

Three stable saver keys register shared acquisition/preparation reuse, paired prerequisite preparation, and blocked-work handoffs. These ideas came from the owner/prompt and are explicitly **owner-seeded**, not discoveries credited to NEYMAN. Each begins unverified and includes a unit, baseline, quality requirement, stopping rule and result location. A workload estimate is never a dollar saving.

New minimal interface: optional `junto.test-contract/1` on candidates, validated at ingestion, ledger checking and test submission. `add-test` rejects a unit that differs from the prospective contract. Legacy candidates remain compatible. Junto's missing-quality defect is fixed: missing/partial/negative/zero-denominator quality measurements cannot produce `saves`, including when old stored tests are recomputed. Actual nonnegative quality counts are required in both arms. The shipped pilot performs no efficiency comparison and credits zero savings.

Prospective forecasts use the existing Llull implementation. The dated pilot forecast is stored in an isolated Llull-format ledger under `research/neyman/pilot-20261020/llull/` to avoid rewriting PR #40's evolving shared ledger. Registration precedes committed pilot outputs; resolution/scoring also call Llull's own functions.

## Runner and reproduction

- `jobs/neyman`: tests, current frame and fresh prospective manifest, output-only.
- `jobs/neyman-pilot`: explicit frozen-manifest consumer, bounded attempts, replay validation, sanitized Junto run/check/score, output-only.
- Both declare `needs.txt`, `after.txt`, `triggers.txt`, and additional input globs. Committed outputs do not trigger consumers; run both explicitly when requested. Updating inventory after the dated pilot invalidates its frozen manifest; create a new prospective run instead of silently substituting new cases.

Local frame: `OUTPUT_DIR=/tmp/neyman-frame python -B jobs/neyman/job.py`.
Current pilot: `OUTPUT_DIR=/tmp/neyman-pilot python -B jobs/neyman-pilot/job.py` consumes the separately frozen `jobs/neyman/output/MANIFEST.json` from the preceding frame job and copies that manifest and its provenance into its own output before attempting any cases. Exact input checks still apply. This is a new bounded consistency run; it does not overwrite or pool the historical pilot.

Historical replay: set `NEYMAN_MANIFEST=research/neyman/pilot-20261020/MANIFEST.json` on its pinned historical checkout. Changed inputs remain an error; the dated manifest, selected cases, observations and pilot limits are preserved.
Tests: unittest discovery in `jobs/neyman`, `jobs/junto`, `jobs/readiness-tracker`, and `jobs/corpus-excavator`. Inspect both successful `output/STATUS.json` files and the final `INTEGRATION.json`; a passing script alone is not a published consumer result.
