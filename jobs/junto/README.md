# Junto

Named for Benjamin Franklin's Junto (1727), the Philadelphia club that kept only the ideas that
worked in practice. Junto is a meta tool for token savings. Design: `research/plans/JUNTO_DESIGN.md`.

| Level | What it is | Here |
|---|---|---|
| Saver | A change that cuts tokens (Revere, Watchman, Spare setup, Quiet protocol) | not built by Junto |
| Finder | A script that reads audit data and proposes savers ("candidates") | `finders/hamilton.py`, `finders/friction.py` (Clausewitz), `finders/wasted_work.py` (Gallatin) |
| Junto | Runs finders, scores them, divides effort, proposes new finders | `junto.py` |

## The hard rule

A saving counts only after a small before-and-after test that measured it. Estimates and
"should save" figures never enter a score (an earlier plan claimed 4,134 hours; it measured 463).
Every finder output is forced to `status: unverified` on the way in. The only command that can
mark a candidate verified is `add-test`, and only with measured before and after values, comparable workloads, adequate quality observations, explicit receipt references, and complete cost coverage. A verified result is evidence for the observed pilot only; broad deployment remains unestablished.

## Commands

Run from the repo root with `python3 -I jobs/junto/junto.py [--ledger DIR] [--output DIR] <command>`.

```
run       --data DIR [--profiles DIR] [--finder NAME] [--usd-spent N] [--usd-basis B] [--force]
add-test  --saver-key K | --candidate C-... --unit-of-work U --test-cost-usd N
          --before-usd N --before-units N --after-usd N --after-units N
          --before-session S --after-session S [--before-accepted/--before-rejected/--after-accepted/--after-rejected N]
          [--matched-on TEXT] [--waste-before k=usd,... --waste-after k=usd,...]
score     verified USD / (USD spent + $2 prior), per finder -> output/SCOREBOARD.json
allocate  [--budget N] [--round N]   exploitation 80% by score, exploration 20% for new/unscored finders
propose   [--test T-id] [--dry-run]  blind-spot step: measured waste no finder predicted -> finder_proposals.jsonl
check     validate the ledger (schemas, privacy rules, every verified line tied to a measured test)
```

- `run` needs a `--data` directory outside the repo (raw `list_events` pages and `get_session` totals
  never get committed). It runs each registered finder with `-I`, assigns global ids, appends the
  candidates and one `runs.jsonl` line per finder. `--usd-spent` records measured API token valuation, split equally over the finders run. Cash charges and API valuation are separate bases. Omission remains unknown; pass an explicit measured zero only when justified. A duplicate attempt still logs its known or unknown cost.
  Running the same data and finder version twice is skipped unless `--force`.
- `add-test` computes the verdict itself from the two arms (per-unit cost, `after <= 0.9 x before`
  and no worse reject rate for `saves`; a gain below 10% is `inconclusive`; a second inconclusive
  result refutes). On `saves` it writes a `verified_savings.jsonl` line
  (`usd_saved = (before - after per unit) x after units`) and marks the candidates verified;
  `no_saving` and `quality_fell` mark them refuted. Both arms must name their measured session
  ids; an after-arm session already used by another test is refused, and `score` counts any one
  after-arm session at most once, so one measured saving can never be credited twice. Candidates of several finders with the same
  `saver_key` share one test: its cost and its credit are split equally. Totals must come from
  `get_session`, not from Hamilton's per-cause shares. Quality counts are required for verified pilot credit. Missing, zero-sample, or incomplete quality remains a cost observation with quality unverified.
- `score` ignores everything but `verified_savings.jsonl` lines whose test exists, is measured,
  recomputes to `saves` and whose `usd_saved` is within the measured delta. A finder with no
  verified saving scores exactly 0. Junto's own totals (verified over spent, plus `F-junto` overhead
  runs) are in the scoreboard so the tool is held to the same rule.
- `allocate` is advice, not spending. With no positive score the whole budget goes to exploration
  (up to 3 `exploring` finders, oldest first). A finder with 0 score after 2 resolved tests and $10
  spent is `dormant` and re-enters exploration every 5th round. State is derived, not stored.
- `propose` reads the optional `--waste-before/--waste-after` cause costs of a test. A cause is waste
  if it is 5% of the arm, $1 or more, or rose 20% (and at least $0.10). If no registered finder or
  candidate targets it, it becomes an open proposal and the test gets `unpredicted_waste`.
  Cause keys are lowercase slugs (`model_writes`); never put command text or `=` in a cause label.
  Every ledger write refuses any `NAME=value` text (Hamilton's rule against echoing commands
  that set variables) and any `targets` or `cause_key` that is not a slug.

## Files

```
junto.py  config.json  test_junto.py
finders/            hamilton.py friction.py wasted_work.py   (stdlib only; interface in design section 2)
ledger/             finders.json (registry, 3 finders)  runs.jsonl  candidates.jsonl  tests.jsonl
                    verified_savings.jsonl  finder_proposals.jsonl  contracts.jsonl   (append-only; highest rev wins)
output/             SCOREBOARD.json (derived, never hand-edited)
catalog/            finders and savers not yet built (status not_built), each with a design and cost estimate
```

The ledger starts with no candidates; the first `run` fills it. Privacy: no transcript text, commands,
secrets, emails, absolute paths or query-string URLs in any ledger field (`check` and every write
enforce this; a violation exits 3 and appends nothing, though the run's cost is still logged).

## Catalog (not built)

| Name | Historical name | What |
|---|---|---|
| `mason_dixon_resurvey` | Mason-Dixon Resurvey | replay a finished task more cheaply, compare bills |
| `tocqueville_comparison` | Tocqueville Comparison | compare sessions of the same task class |
| `washington_farewell` | Washington Farewell | an exit question for every agent |
| `thornton_patent_scan` | Thornton Patent Scan | scan platform features that cut cost |
| `wolcott_preflight` | Wolcott Pre-flight | estimate a task's cost before it starts |

Every catalog dollar figure is an unverified estimate.

## Tests

`python3 -I jobs/junto/test_junto.py` proves that an unverified candidate never contributes to a
score and that verified savings require a measured test record.


## Acceptance and accounting repair (2026-10-20)

`add-test` now records a cheaper run with missing quality as `cost_reduction_quality_unverified`. It preserves that attempt and its costs without a verified-savings line. Negative quality counts, nonfinite money, overlapping before/after sessions, and reused after sessions are refused. A measured zero is distinct from missing telemetry.

For quality-checked pilot credit, supply both accepted/rejected counts, `--matched-on`, `--before-measurement-ref`, `--after-measurement-ref`, and `--complete-costs`. The references identify aggregate measurement receipts; no private transcript text belongs in the ledger. The complete-cost declaration means both arm totals include production, build, coordination, monitoring, review, rework, integration, and failed attempts. Quality observations must cover at least the reported output units. Additional `--test-cost-usd` is expense **outside** the two arm totals; omit it when unknown. The tool retains the measurement gap and gives no credit in that case. It cannot independently verify an invoice or every statement in an externally produced receipt.

The scoreboard counts both experiment arms and additional overhead, including unsuccessful tests. It deduplicates identical session-set totals; conflicting or partially overlapping totals make coverage unknown. It presents known expense separately from total expense, and does not mix cash charges into API token valuation. The sourced build reconciliation records $10.18 of reported API token value and leaves unmeasured coordination/integration expense unknown. Thus a known subtotal can be $10.18 while complete total and cash charge remain null. Estimates and overlapping cause shares never enter the monetary score.

A pilot includes observed sample sizes, Wilson rejection-rate intervals, one cost comparison, and an explicit missing cost interval. A small sample with no observed rejection does not establish a zero population rejection rate. `deployment_supported` remains false. Retrospective pilots are labelled retrospective; prospective evidence needs the frozen contract below.

## Seeded candidates and frozen test contracts

`propose` continues to mine measured unpredicted waste. It is not a brainstorm importer. Use these separate commands for supplied ideas and prospective tests:

```sh
python3 -I jobs/junto/junto.py seed-candidate --file CANDIDATE.json
python3 -I jobs/junto/junto.py register-test --file CONTRACT.json
# Commit the contract before execution, then use its exact 40-character commit.
python3 -I jobs/junto/junto.py test-gate --contract PILOT_ID --registration-commit COMMIT
```

A seed needs `saver_key`, `title`, `targets` cause slugs, and `origin` with `kind` (`owner` or `agent`), `name`, and `reference`. It enters unverified, has no mining finder, and cannot credit a finder with inventing the supplied idea. Repeating the same origin and key is rejected. Existing finder-origin candidates and historical revisions remain unchanged.

A contract needs:

- `contract_id`, distinct existing `candidate_ids` for one saver key, and a `sample` of distinct `{id, sha256}` members;
- `baseline.measurement_ref`, `unit_of_work`, `matched_on`, and `outcome_definition`;
- `quality_condition` with `metric: rejection_rate`, `max_increase: 0`, and positive `min_reviewed`;
- finite nonnegative `budget_usd`; `stop_rules` with positive `max_attempts` and `stop_on_quality_drop: true`;
- nonempty repository-relative `result_paths`.

Contracts are immutable: a revision uses a new id and a `supersedes` reference. Registration is not prospective merely because its JSON says so. `add-test --contract ID --registration-commit COMMIT --measurement-started-at ISO_TIMESTAMP --sample-manifest SAMPLE.json` checks that the exact frozen record existed in that commit before the declared measurement start and that the result paths were absent then. The aggregate sample manifest must match every member id and hash in the frozen contract; it records what the experiment says it executed. Missing history, absent commit evidence, or preexisting results remains unverified. The receipt start time is a reported observation, not cryptographic proof of when research occurred.

Run production only after `test-gate` exits successfully (for example, chain the producer after the gate with your normal process runner). The gate exits nonzero on missing registration, exhausted attempts, a prior quality drop, unknown prior costs, or an exhausted budget. `add-test` separately reconciles candidate/workload/baseline/result identity, quality sample, and total budget. An over-budget or otherwise nonconforming result is retained with its costs and violations; it receives no verified credit. A test allowance is advisory and does not independently authorize spending.

The scheduled job reads the ledger, runs the regression suite, validates it, and writes only the derived scoreboard to `OUTPUT_DIR`. It never mines private transcripts, runs an experiment, or mutates the ledger. No measured production-token experiment was available in the repair session; verified savings remain zero.
