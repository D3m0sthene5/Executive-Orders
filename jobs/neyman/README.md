# NEYMAN

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
