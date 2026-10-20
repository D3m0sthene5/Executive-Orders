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
mark a candidate verified is `add-test`, and only with measured before and after values.

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
  candidates and one `runs.jsonl` line per finder. `--usd-spent` is what the run cost (the change in
  the running session's `get_session` cost, plus any Actions minutes), split equally over the finders
  run (kept to 4 decimals; a skipped rerun still logs its cost); leave it out only for a pure script with no model in the loop (recorded as `local_script`).
  Running the same data and finder version twice is skipped unless `--force`.
- `add-test` computes the verdict itself from the two arms (per-unit cost, `after <= 0.9 x before`
  and no worse reject rate for `saves`; a gain below 10% is `inconclusive`; a second inconclusive
  result refutes). On `saves` it writes a `verified_savings.jsonl` line
  (`usd_saved = (before - after per unit) x after units`) and marks the candidates verified;
  `no_saving` and `quality_fell` mark them refuted. Both arms must name their measured session
  ids; an after-arm session already used by another test is refused, and `score` counts any one
  after-arm session at most once, so one measured saving can never be credited twice. Candidates of several finders with the same
  `saver_key` share one test: its cost and its credit are split equally. Totals must come from
  `get_session`, not from Hamilton's per-cause shares. Quality counts are optional but you should
  give them: without them "no worse quality" is not proven.
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
                    verified_savings.jsonl  finder_proposals.jsonl   (append-only; highest rev wins)
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

Valla is an owner-seeded domain hypothesis registered as `F-valla`. Its finder
reads `valla_rework_salvage.json` from an external data directory and proposes a
matched total-cost correction experiment. Preparation timings alone leave it
unverified; `add-test` still requires actual measured session totals. No pricing,
scoring or review rule changes were made for Valla.
