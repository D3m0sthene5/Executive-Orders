# Llull: checks a research plan before money is spent on it

Named for Ramon Llull's *Ars Magna* (c. 1305), paper wheels that cross every term with every
other term and list the questions to ask. Design: `research/plans/LLULL_DESIGN.md`.
Standard library only; always run with `python3 -I`.

**Hard rule (as in Junto).** Llull earns trust only from measured outcomes. A base rate must be a
measured number with a source path, or `forecast` refuses it. Llull never changes the
evidence/legal codebook, claim statuses, tiers, or the certified count (0). AI statuses stay
hypotheses. It reads committed outputs and writes only under `jobs/llull/`.

```
python3 -I jobs/llull/llull.py [--pools FILE] census --pool Y2|CRAIG|... [--requires a,b,c] [--record] | --list
python3 -I jobs/llull/llull.py forecast  --plan-id ID --planner agent:model --quantity Q \
          (--p10 --p50 --p90 | --event TEXT --prob P) --reference-class KEY [--pool P | --census-id D-..] \
          [--unlock-p90 N] [--run-dir DIR] [--accept-flag REASON] [--deviation TEXT]
python3 -I jobs/llull/llull.py outcome   --forecast L-.. --measured N --source REPO/PATH
python3 -I jobs/llull/llull.py score                       # output/CALIBRATION.json
python3 -I jobs/llull/llull.py premortem PLAN.(json|md) [--pool P]   # at most 12 questions
python3 -I jobs/llull/llull.py rank      --actions FILE    # output/RANK.json
python3 -I jobs/llull/llull.py baserate  --outcome O-.. --key QUANTITY.name --population POOL --pool-desc TEXT [--num N --den D]
python3 -I jobs/llull/llull.py selfscore [--rule-commit C]   # output/SELFSCORE.json
python3 -I jobs/llull/llull.py check [--mark]
python3 -I jobs/llull/test_llull.py
```

Exit codes: 0 ok, 2 refused, 3 flagged (not registered), 4 check failed. `--ledger DIR` points at
another ledger (used by the tests).

## Parts

| Part | Command | What it does |
|---|---|---|
| BRIER | `forecast`, `outcome`, `score` | Registers an 80% interval or a probability **before** a run, resolves it from a committed file, scores Brier, normalized interval score, coverage, optimism (median log of measured/p50), and skill against the outside view, per planner `agent:model`. A planner is "unproven" until 5 resolved forecasts. |
| Domesday | `census` | Zero-agent, per-item count of orders that hold **every** required input. Strict ceiling = all gates held; leads ceiling = leads count too. Prints the product of marginals and flags `ASSUMED_INDEPENDENCE` when it is 1.5x or more above the joint count. |
| Wheel | `premortem` | Plan step x 10 failure modes (`failure_modes.json`). Each mode has a mechanical check; a question is emitted only when the check **fires** on that step or **cannot run** (needs a census, `reference_class`, `producer_model`/`reviewer_model`, `access_checked`, `approval`), and every question shows the plan-specific evidence. Checks that ran and passed are counted, not asked, so a clean plan gets 0 questions. In prose plans a paragraph line belongs to the step (heading, list item) above it, and a stated upheld/accepted/ready rate (`>= 50%`, `p50 0.15`) above the census strict share fires `UNMEASURED_PREREQUISITE`; a fetch or by-hand word negated just before it (`never fetch`) is not asked about. Order: `auto_fail` (structured plan only: number above the census ceiling, `requires_unmeasured`, unregistered gate, proxy unit), then by how many of the 12 past misses the mode caused. At most 2 per mode and 12 in all. |
| Raiffa | `rank` | Ranks actions by (expected ready orders + EVSI) / cost, with a Beta prior from a measured base rate and an exact beta-binomial preposterior. An action with no measured cost or conversion is listed UNRANKED. A zero-agent check that measures a missing input runs first. The census share is applied **only when the action's pool differs from the population the base rate was measured on** (`population` in `base_rates.json`): a rate measured on random Y2 draws already contains Y2's gate failures, so on Y2 the share is 1.0 (first use found a 55x undercount from applying it twice). On a different pool the rate moves by the ratio of strict shares (action pool / population), capped at 1: a pool that holds its prerequisites less often is discounted, a richer sub-pool (e.g. Y2LEAD) keeps the measured rate instead of being cut 10x, and a population with strict share 0 leaves the action UNRANKED. With no recorded population the action pool's own share applies. `RANK.json` shows each action's share and basis. |
| Juvenal (part) | `selfscore` | Of the resolved misses, the share Llull flagged in advance (`CEILING_EXCEEDED` at registration), counting only forecasts whose `registered_commit` resolves to a strict descendant of the rule's commit (hashes are resolved first, so a forecast registered at the rule commit is in-sample) and not marked `not_preregistered`. A miss is a measured value outside [p10, p90], or a binary event expected at p >= 0.5 that did not happen. "unproven" until 5 out-of-sample misses; 0 today. The full Juvenal (precision of premortem questions) is not built. |

## Refusals and flags (proved in `test_llull.py`)

- `forecast` refuses a `--reference-class` that is not in `ledger/base_rates.json` with a numeric
  value and a source (`new:<key>` plus `--reason` is allowed, but the interval must then be at least
  [0.1 x p50, 2 x p50], and the measured median miss ratio 0.036 is printed beside the p50).
  `check` fails on an unmeasured seeded row.
- A class with fewer than 3 studies needs the same wide interval. Most seeded classes have n = 1.
- p50 more than 2x from the measured outside view needs `--deviation`.
- p90 above the census ceiling (a count for `ready_orders_gained` / `accepted_items` / `items_reached`,
  a share for rate quantities) prints `CEILING_EXCEEDED` and exits 3 without writing. `--accept-flag`
  registers it flagged. `--unlock-p90` adds the p90 of a registered step that creates the missing input.
- Proxy units (tokens, payload, bytes, packets, certificates, agent-hours) are refused.
- `--run-dir` refuses if the directory already holds committed files. `check` verifies from git history
  that the forecast line was committed strictly before the run directory's first commit. A forecast that
  cannot be proven first (run committed together with or before it, or its outcome source first committed
  in the same commit) is reported `not_preregistered`: `check` still passes, `check --mark` appends it to
  `ledger/registration.jsonl`, and `score` leaves it out of calibration (`not_preregistered_excluded`).
  The forecast lines themselves are never edited.
- `baserate --outcome O-..` makes a base-rate row whose `source` is the outcome id (same quantity, a rate
  in [0, 1], `--num/--den` equal to the measured value, a known `--population`). `check` fails the row if
  its value differs from the outcome.
- `outcome` needs a repository-relative existing source file, one outcome per forecast, and warns
  `ceiling_violated` when the measurement exceeds the census cap (a gate missed a route).

## Seeds

- `ledger/postmortems.json`: the 23-plan pass-1 mining (history, **not registered**, so it feeds base
  rates but not calibration).
- `ledger/base_rates.json`: 19 rows copied only from measured values in the postmortems, each with
  `source`, `postmortem_id` and `evidence` (verbatim quotes that `check` finds in the cited files, whitespace
  ignored; the 0.036 fallback is instead recomputed from `postmortems.json`). Examples: Y2 upheld 3/50 = 0.06, Y1 accepted 15/50, X1 eligible 52/8,014,
  Opus refetch 17/472, HathiTrust 0/1,712, median measured/forecast over 9 unfavourable misses = 0.036.
- `failure_modes.json`: the 10 modes with past miss counts (8, 5, 3, 2, 2, 2, 1, 1, 0, 0 over 12 misses).
  Derived from the same 23 plans, so a score on them is in-sample; only future plans earn trust.
- `ledger/censuses.jsonl`: the three shipped pools. D-1 to D-3 (gates rev 1, commit 46f91fdac) are superseded by
  D-4 to D-6 (gates rev 2, commit 15b4b4d85); `test_llull.py` re-runs the latest rev on inputs taken with `git show`
  at the recorded commit, so later data commits do not break it.
- `examples/`: a structured plan for `premortem` and a candidate-actions file for `rank`.

## Custom census pools (`ledger/pools.json`)

Y1, Y2 and X1 are built in and cannot be redefined. Other pools are declared in the pools file (`--pools FILE`,
default `ledger/pools.json`); no code runs, only these keys: `from` (all or another pool), `where` (tracker
column = value, `[values]` or `{"not": ...}`), `eo_gte`, `eo_lt`, `open_steps_max/min`, `ids_file`, `gate_states`,
`default_requires`. A recorded census stores the pool definition it used. Shipped: `CRAIG` (the 23 Craigellachie
last-step orders), `NEAR`, `NR`, `Y2NO`, `Y2YES`, `Y2LEAD` (lead-selected), `Y1END`, `X1S`, `X1T` (pre-1937 routes), `X1PILOT` (X1 with status and held text: the population the X1 pilot rates were measured on, 32 today);
gates `ending_held_if_no`, `ending_or_current_lead2`, `ending_step_done` were added for them.

## Census pools (gates rev 2, commit 15b4b4d85)

| Pool | Definition | Required inputs | Pool | Strict | Leads |
|---|---|---|---|---|---|
| Y1 | numeric EO >= 7532, no provisional status, not ready | `original_text_held`, `status_evidence_held` | 4,274 | 3,952 | 3,952 |
| Y2 | EO >= 7532, status yes/no, text held, not ready, no claim | `status_present`, `original_text_held`, `ending_or_current_held` | 2,060 | 38 (1.8%) | 363 (17.6%) |
| X1 | not numeric EO >= 7532 (pre-1937 and unnumbered) | `status_present`, `original_text_held` | 8,032 | 32 (0.4%) | 32 |

Y1 reproduces the funnel plan's 4,274 and 3,952; X1 reproduces the postmortem's "32 by EO<7532 today"
(the pilot's 52 of 8,014 counted by signing date at an earlier commit). Y2's pool was 2,063 at 46f91fdac
(the scratch `y2_predictor.py` count) and is 2,060 at 15b4b4d85.

**Gates rev 2 (adversarial review, 2026-10-20).** Rev 1 counted any whole-scope ACT verb (transfer, other) and
any TERM end date, including a single section's (`#sec4-b`), as an ending instrument: 67 strict. Rev 2 counts
only revoke/supersede/terminate/abolish ACTs with an effective date and whole-scope TERMs: 38 strict. 10 items per
pool were checked by hand against the raw files.

**The strict count is not a ceiling for rates.** Bowditch Y2 drew its 50 orders at random from this pool and
upheld 3 (6%), above the strict share (3.2% in rev 1, 1.8% in rev 2). None of the 3 upheld orders passed the gate
in either rev (one partial revocation without a date, one whole TERM with a stated but not computed end, one
amended), and 0 of the 50 pass it in rev 2. So the gate misses routes; `outcome` logs `ceiling_violated` in that
case. The strict share is a gate-held share, useful for the order of magnitude, and caps a share only when the
attempts are an unselected draw from the pool. `hit_rate` is not capped at all (it is conditional on the
finder's own selection). Widening the gate to catch these three would be fitting the test cases, so it is not done.
Either way the Y2 target of 50% upheld was far above both counts. No repository source holds a
CURRENT predicate yet, so `current_predicate_held` yields leads only (325 YES orders), never "held".
Also registered: `claim_draft_present`, `no_evidence_conflict`, `only_judgment_left` (claim-drafts).

## Not built yet

The `host_allows` network gate, the Juvenal score (`selfscore`), a Murphy decomposition below 10
binaries, and per-step `requires` evaluation inside `premortem` (it checks only that the gate exists).
