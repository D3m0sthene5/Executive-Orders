# Dated measurement integration

The display reads `observability.json` at the same static origin as its other assets. Root's deterministic roll-up owns that file. A failed read, malformed generation or older `generated_at` retains the current measurement snapshot and shows an unavailable-refresh notice. Tracker counts continue to refresh independently from a single main commit. There is no cost extrapolation from newly refreshed tracker counts.

`observability-core.test.js` contains a small complete contract fixture. The version-1 contract requires:

- `schema_version`, ISO `generated_at`, and full `source_pin`;
- a baseline with full `source_pin`, `finished_utc`, nonnegative `orders_total`, `ready`, `unfinished`, `human_certified`, `first_missing` and `open_anywhere` counts;
- source references `{id,path,ref}` using relative repository paths and full commit refs;
- exactly five gap records with IDs `phase_role`, `repetition`, `blockers_retries`, `ready_conversion`, `time`, each carrying `title`, `recovered`, `prospective`, `unavailable`, and joined `source_ids`;
- campaigns with `id`, `label`, `window`, `scope`, `coverage`, `outcomes`, `source_ids`, `workers`, `tokens`, `api_equivalent_usd`, `actual_cash_usd`;
- role records with `campaign_id`, `role`, reported worker `model`, `workers`, `tokens`, `coverage`;
- a nonempty plain-text `boundaries` list.

The four token keys are `fresh_input`, `cache_read`, `cache_creation`, `output`. All measurements must be nonnegative numbers or explicit `null` when unavailable; token/worker counts must be safe integers. Unknown dollars cannot silently become zero. Reported worker models can be modal transcript models, not complete per-token model attribution. Role rows are nonoverlapping recorded subsets of their campaign, never costs to add again to the campaign totals. If historical role membership overlaps, normalize that evidence separately before publishing role rows.

Validation reconciles ready/unfinished totals and the unique partition, bounds overlapping counts, requires first-text and final-gate counts to match their respective partition counts, validates provenance joins, and refuses role totals exceeding campaign totals. It does not independently establish the scientific truth of supplied source records: the reproducible roll-up and its audit remain required.

The measurement view escapes all dynamic text and constructs links only to this repository at full commit pins. It accepts no HTML, arbitrary URLs, event handlers or remote measurement fetch paths from the artifact. The existing historical examples remain dated inside a disclosure. These changes do not alter first-missing/overlap semantics, scientific records, review gates, queues or active production.

Validation: `node --test research/progress/control-center/observability-core.test.js` (10 tests); JavaScript syntax checks; `python3 research/progress/control-center/verify-flow.py` reproduces the existing partition and overlap totals. Independent review identified an older-generation downgrade and impossible text overlap; both now have rejection tests. The bundled real artifact validates and renders in a VM integration test with unchanged first/overlap counts; all campaign primary source IDs render as pinned links. Root owns hosted/browser and final integration verification.

Implementation agent: actual model `gpt-6.1-sol`. Complete occupied wall time, worker-active time, tokens, tool usage and cash are unavailable. Test-run durations are machine-test durations only and do not estimate implementation labor or savings. No scientific case was produced, no production job dispatched, and no savings claim is made.
