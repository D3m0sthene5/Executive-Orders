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

## Supported production usage bridge

The same CLI also accepts one supported Claude JSONL transcript export (the
`type`, `timestamp`, `message` records read by Geddes):

```sh
python3 -I jobs/hamilton-token-audit/profile.py /private/worker.output \
  --label RUN --production-metadata /private/METADATA.json --out /isolated/new-run
```

The profile now retains sanitized `usage_records` at call scope. Exact duplicate
events count once; a revised event with the same UUID can supply final usage.
Stable agent/message identity reconciles stream and final snapshots. Conflicting
final counts, decreasing final counters, missing message identities, invalid token
counts, contradictory cache totals and model conflicts refuse normalization.
Final completion without final output counts does not certify streamed output.
Fresh Anthropic input, cache reads, cache creation and output are nonoverlapping;
TTL cache-write details are a breakdown of the aggregate. Reasoning, when actually
reported, stays a subset of output. Absence of reasoning counts stays unknown.

`METADATA.json` has `session_id` and an `agents` object keyed by the existing agent
identity (`main` for a single Geddes-format transcript). Each agent requires
`worker_id`, `role`, `phase`, `actual_model`, unique downstream `instrument_ids`,
timezone-aware `started_utc`/`finished_utc`, `coverage` (`partial` or
`complete_interval`) and `measurement_method`. Phases use NEYMAN's existing
preparation/acquisition/production/review/correction/coordination/integration
vocabulary. Use explicit observed worker occupation; transcript gaps never supply
active labor. Retain distinct worker exports and metadata where a log has no
supported agent identity; do not guess roles or memberships from filenames.

With this metadata, the CLI additionally writes `PRODUCTION_EFFORT.json` in the
existing `neyman.production-effort/1` format. Stable session/agent/message usage
IDs keep shared calls once. The caller interval repeats on call events and the
existing consumer unions it per worker; it must not be summed across calls.
Session totals and session cash charges stay separate and are not re-exported as
calls. Membership describes shared use; no per-order allocation is inferred.
The receipt is create-only, so a second export to that path refuses overwrite.

Pass that file to the existing standalone `after_completion.py --effort PATH`
or ordinary `kit.py complete --diagnostic-effort PATH` route documented in
`jobs/neyman/AFTER_COMPLETION.md`. The ordinary diagnostic still requires its
explicit pinned history, base, destination and unfinished-attempt receipts.
Hamilton's `job.py` continues to run tests and reconcile historical aggregate
profiles only: the runner has no raw transcripts or caller intervals, so it
cannot fabricate a production receipt or dispatch collection automatically.

The profile's `collector` records measured offline load/normalization/hash elapsed
seconds and input byte counts/digests; it excludes output serialization. No model
calls occur. The observation window and possible-call denominator remain partial
or unknown, and neither API valuation nor cash is invented. Published worker CSV
totals cannot reconstruct missing per-call usage or correct first-stream captures.
All observed usage timestamps must fall inside the caller's declared interval.
Absolute pricing additionally requires a valid ISO calendar date and one known
observed model for the supplied single rate schedule. Mixed/unknown models refuse
that valuation; callers can profile their separately observed model scopes.
Keep full profiles private: existing context diagnostics can contain file paths
and tool labels. The production receipt omits transcript text, tools and source
paths, but caller-supplied identifiers/measurement descriptions must still be
reviewed for public release. No publication occurs in this CLI.
