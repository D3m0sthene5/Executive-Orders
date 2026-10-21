# Hamilton: token usage, measurement coverage, and cautious attribution

Hamilton is the existing offline profiler of saved agent-session transcripts. Raw transcripts stay outside the repository. It does not infer an invoice, a full-session capture, or a verified saving from a partial transcript.

```sh
python3 -I jobs/hamilton-token-audit/profile.py PAGES_DIR --label NAME --out OUT_DIR
python3 -I jobs/hamilton-token-audit/profile.py PAGES_DIR --cost-usd 10 --session-totals TOTALS.json --label NAME --out OUT_DIR
```

Input pages retain the existing `{"ccr":{"data":[...]}}` format. Optional `TOTALS.json` contains **independently reported full-session** token counts under `input`, `read`, `write5m`, `write1h`, and `output`. All categories must be known before the session token value can calibrate the observed window. A flag claiming all pages were downloaded is insufficient because initial streaming records can understate output. Captured token categories are never expanded to fill a missing window.

## What the output means

- `tokens` contains the sum actually observed in usage records. `coverage` gives missing-field counts and the independent session total/fraction where available. `session_tokens` stays null for unobserved totals. Initial streaming output is a lower bound until final usage is available. Later final records update the same call, rather than adding another call.
- Cache writes preserve 5-minute and 1-hour categories. An aggregate write count without its TTL stays in `cache_write_unclassified_tokens`; the profiler does not assume the cheaper TTL. Rebuild diagnostics price the actual observed mix.
- `session_token_value_usd` is reported API token valuation. `cash_charge_usd` is a separate optional observed invoice charge; it defaults to null. Local-session cost and unobserved output are not free.
- `observed_window_token_value_usd` is available only when all independently reported session token categories allow calibration. The calibration retains the original audit's explicit relative-price assumptions. `priced_observed_tokens_usd` is an optional separate subtotal using a supplied dated price schedule, with unknown/partial usage still disclosed.
- Context attribution uses characters/4 and the first observed call's context as a setup proxy. These are estimates. Cause rows partition the observed priced usage, while cache rebuilds, large-context polls, and agent views overlap those rows and one another. **Do not add the diagnostic views together.** A partial transcript's setup proxy may include earlier history.

Use `--pricing PRICING.json` for a schedule with `source`, `as_of`, and `usd_per_million_tokens` for all five categories. No current absolute price is silently assumed. `--cash-charge-usd` records an observed invoice amount. `--effort EFFORT.json` annotates production, build, coordination, monitoring, review, rework, and integration costs already included in session totals. Missing phases remain null; do not add phase annotations to the same totals again. Junto accounts for complete experiment expense and requires explicit complete-cost declarations and receipt references before pilot savings receive credit.

## Existing Junto adapter

`jobs/junto/finders/hamilton.py` uses the same usage parser. Its version 2 refuses to price a session solely from a complete-pages flag and no longer borrows a rate from another session. `session_index.json` may provide canonical `token_totals`, or the unambiguous aggregate fields `input_tokens`, `cache_read_tokens`, `cache_write_5m_tokens`, `cache_write_1h_tokens`, and `output_tokens`. Unpriced sessions remain visible in the `.check.json` sidecar. Candidates remain estimates with overlapping effects, never verified savings.

## Runner and preserved history

The job runs the focused regression suite and writes `COVERAGE_RECONCILIATION.json` only to `OUTPUT_DIR`. It hashes the five preserved first-audit profiles and reports which lack enough category totals to validate their old scaling. It does not pretend to rerun unavailable private transcripts. The original report and profiles remain in `research/production/hamilton-2026-10-20/`.

The source review for this repair found no published sensor-array implementation on main or the dependency branch. Hamilton remains the existing collector; no duplicate telemetry service was built and Tycho was not assumed to be that array.

Tests: `python3 -I jobs/hamilton-token-audit/test_profile.py`.
