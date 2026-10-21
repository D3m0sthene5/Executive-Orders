# Junto and Hamilton repair

Base inspected: `91116f879978902343dafa88490b9b19587b10da`, the refreshed head of PR #40. Main remained `ed19a06039278c10e5a3ebddccf19d2bd02ac3a2`. Code hashes, defect reproduction and local validation are in `VALIDATION.json`. GitHub execution is a separate integration check; these local results do not claim an executed remote commit.

## Concrete defects and corrections

The original `quality_ok` returned true when either arm lacked quality data. A synthetic measured comparison of $20/2 units against $10/2 units consequently returned `saves` without any quality observations. It now returns `cost_reduction_quality_unverified`, preserves the observation and expense, and produces no verified-savings line. Zero-sized quality samples behave the same way. Negative counts and nonfinite monetary values are rejected.

Junto now requires comparable workload descriptions, explicit units, aggregate receipt references, adequate quality coverage, and complete cost declarations for quality-checked pilot credit. Declared complete totals include production, build, coordination, monitoring, review, rework, integration and failed attempts. Both experimental arms and additional overhead enter the expense denominator; the old denominator counted only the extra test cost. Unknown expense remains null. Identical session-set receipts are deduplicated and conflicting or partially overlapping totals prevent a complete-cost claim. Reused treatment sessions cannot generate duplicate savings credit.

Pilot evidence is labelled as such. The record exposes sample sizes and Wilson rejection-rate intervals, leaves an unmeasured cost interval null, and sets `deployment_supported` to false. These mechanics do not establish causal attribution or broad deployment effectiveness.

The existing `propose` command still mines measured waste. `seed-candidate` accepts an explicitly attributed owner/agent idea, while `register-test` freezes a contract with sample hashes, baseline, outcomes, quality conditions, budget, stop rules and result paths. Supplied ideas receive no finder invention credit. Prospective status requires the exact frozen record in an earlier Git commit; preexisting results or missing evidence fails that condition. The realized sample manifest must match the contract. `test-gate` exits nonzero on registration, budget, unknown-cost, attempt-limit or quality-stop failures. Nonconforming measured outcomes remain recorded with costs and violations and receive no credit.

Hamilton previously assigned an entire supplied $100 session valuation to a synthetic partial capture containing only one call with 25 relative-price units. The repaired profiler leaves absolute attribution unknown unless complete independently reported session category totals support calibration. With a known 700-unit session total, that 25-unit window receives only its 25/700 share. The Junto adapter no longer trusts a complete-pages flag as proof of complete output or borrows another session's rate.

The profiler preserves input, read, 5-minute write, 1-hour write, and output observations; absent fields remain disclosed. Unclassified cache writes retain their count without an invented TTL. Final usage updates replace initial streaming counts for the same call. Five-minute rebuilds use the five-minute weight, and interleaved agents no longer consume one another's pending context. Actual cash charges, reported API token value, optional dated price schedules, and approximate cause attribution are separate fields. Rebuild, polling and agent diagnostics explicitly overlap the cause totals and must not be added together.

## Reconciliation and measurements

The append-only run ledger now includes the documented **$10.18 of reported Junto build API token value**, sourced to Claude's dated HANDOFF entry at the inspected base commit. The source describes about 50 minutes and 49 million cache reads; those remain approximate reported observations. No cash invoice or complete coordination/integration total is inferred.

Current derived result: **$10.18 known token-value expense, complete expense unknown, cash charge unknown, $0 verified savings**. The 13 historical candidates remain unverified. No adequately metered production comparison was available in this session, so no savings pilot was fabricated or charged against the exploration allowance.

Hamilton's runner hashes all five preserved historical profiles. Three contain legacy dollar scaling that needs independent complete-category totals before its coverage can be validated; two were already unpriced. None was silently rewritten. The private raw transcripts are unavailable here, so the additive reconciliation reports the gap rather than pretending to remeasure them.

The refreshed published branch inventory did not reveal a sensor-array implementation, and neither main nor the dependency branch contains one. The existing collector was repaired; Tycho was not assumed to be the missing array.

## Validation and remaining limits

Local validation passed **36 Junto tests and 12 Hamilton tests**, including real CLI tests with synthetic saved transcript pages, temporary Git registration histories, uncommitted/retrospective contracts, changed samples, budget violations, missing quality, failed-arm expense, overlapping credit, and unavailable category totals. Both new job entrypoints exited successfully and wrote to their designated `OUTPUT_DIR`. `git diff --check` passed for both tool trees.

The runner jobs perform no LLM calls: Junto validates the ledger and regenerates its scoreboard; Hamilton validates the profiler and generates the historical coverage addendum. The latter declares its research-input dependency and external trigger explicitly. Root integration must inspect the actual GitHub execution commit and runner `STATUS.json`.

Receipt references and complete-cost declarations are reviewable evidence claims, not independent invoice authentication. Registration compares Git evidence with a declared measurement start time; it does not cryptographically attest when an external experiment ran. Model token counters, cash billing and complete repair-session effort were unavailable, and no per-order token saving is claimed.
