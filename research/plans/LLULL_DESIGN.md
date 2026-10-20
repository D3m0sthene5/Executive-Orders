# Llull: a tool that checks plans before they run (design, 2026-10-20)

Named for Ramon Llull's *Ars Magna* (c. 1305): paper wheels that, when turned, cross every
term with every other term and list the questions to ask. Llull does that to a research plan.
It crosses each plan step with each failure mode we have already seen and asks the questions
the plan must answer before anyone spends money on it.

Its parts carry their own names:

| Part | Named for | Job | Section |
|---|---|---|---|
| **BRIER** | Glenn Brier's 1950 verification score | Forecast ledger: register before running, score after, calibrate per planner, keep the reference-class table | 2 |
| **Domesday** | The 1086 survey that counted what was actually held | Prerequisite census ("gate dry-run"): a zero-agent count of items that hold every required input; the forecast cannot exceed it | 3 |
| **Wheel** | Llull's combinatory wheels | Premortem generator: step x failure mode -> question, with a mechanical check where one exists | 4 |
| **Raiffa** | Raiffa and Schlaifer's preposterior analysis (1961) | Value-of-information ranking of next actions | 5 |
| **Juvenal** | "Who will guard the guards themselves?" | Llull's own score | 6 |

Status: design only. Nothing is built. The postmortem miner (pass 1) and the Y2 predictor
exist as scratch scripts and move into `jobs/llull/` when the job is built (section 8).

## 0. Why, and the hard rule

The measure is **orders ready for human review**: 135 of 14,972 today. The certified
whole-lifecycle count is 0 and stays 0. AI statuses are hypotheses. Llull never touches the
evidence/legal codebook, any claim status, any tier or the certified count. It reads committed
outputs and writes only to its own ledger.

Postmortem pass 1 mined 23 plans from the repository. 15 had a numeric forecast and a measured
outcome:

- 12 missed against the plan, 1 hit (Y1 status sweep, P18), and 2 overestimated cost (P14, P21).
- Among misses with a ratio, the median measured/forecast ratio is **0.036**: outcomes came in
  about 28 times below forecast.
- 10 of the 12 misses could have been predicted mechanically from repository data at plan
  time.

| Failure mode (count in the 12 misses; a plan can have several) | Examples |
|---|---|
| `UNMEASURED_PREREQUISITE` 8 | Sprint: 300 ready, got 1. Family rules: 0 of 571 passing. Opus refetch: up to 472, got +17. X1: 4,134 h, got 463 (52 of 8,014 orders eligible). Y2: at least 50% upheld, got 6%. |
| `SELECTION_BIAS` 5 | The Codification swarm's 2 min per claim and 11% rejection were reused on harder families. Brief A2 forecast 60-75% complete and got 2 of 19. |
| `COST_SHIFT` 3 | The packaged arm used 21.8% more input tokens. The 60% saving estimate had the wrong sign. |
| `INVENTED_RATE` 2 | Type-rule hit rate 0.85, measured 0.19. Extinction events 0.8, measured 0. |
| `PROXY_UNIT` 2 | Payload-token cuts counted as savings. |
| `ACCESS_ASSUMPTION` 2 | HathiTrust blocked by robots.txt: 0 of 1,712. |
| `ASSUMED_INDEPENDENCE` 1, `POLICY_COUNTED_UNAPPROVED` 1 | X1 series plan. |

**Hard rule (as in Junto).** Llull earns trust only from measured outcomes. A forecast is
scored only against a measured value in a committed file. A flag counts toward Llull's score
only if it was committed before the outcome existed. Llull never claims dollars "saved" by a
plan it advised against, because the counterfactual is not measured (section 6).

### What the literature contributes

- **Reference-class forecasting** (Kahneman and Lovallo; Flyvbjerg's "outside view"). Start
  from how similar past projects actually turned out, then adjust. The uplift is read from a
  percentile of the past distribution, and how the class is defined changes the answer.
  BRIER's reference-class table and its start-from-base-rate rule apply this (section 2.4).
- **Premortem** (Klein, *HBR* 2007). Assume the plan has already failed and list why.
  "Prospective hindsight" raised correct identification of reasons by about 30% (Mitchell,
  Russo and Pennington 1989; that figure is theirs, not Klein's). The premortem makes reasons
  more numerous and specific. It does not prove forecasts more accurate, so the Wheel is scored
  on recall (section 6), not assumed to work.
- **Brier score and the Murphy decomposition** (1973): BS = reliability - resolution +
  uncertainty. Reliability measures calibration, and the uncertainty term is the base rate's own
  score, which a planner must beat to add anything.
- **Interval score** (Winkler 1972; Gneiting and Raftery 2007): width plus (2/alpha) times the
  distance by which the outcome falls outside. It rewards narrow intervals that still contain
  the outcome.
- **Value of information** (Schlaifer and Raiffa; EVSI is bounded by 0 and by EVPI). Buy a probe
  only if what it could change is worth more than it costs.
- **Fermi decomposition** (Tetlock's superforecasting habits). Split a forecast into its known
  and unknown parts, and do not answer an easy question in place of a hard one. Here the known
  part is the Domesday ceiling and the unknown part is the conversion rate.

## 1. Layout

```
jobs/llull/
  README.md
  llull.py                  # driver: register, census, wheel, voi, resolve, score, selfscore, check
  config.json               # thresholds (sections 2-6)
  failure_modes.json        # the 10 categories, each with question and check templates (section 4)
  gates/gates.json          # gate registry: key -> deterministic predicate over committed files (section 3)
  gates/<gate>.py           # one small reader per gate, standard library only
  plans/<plan_id>.json      # a plan spec: pool, steps, required gates, forecasts (section 2.1)
  ledger/
    forecasts.jsonl         # registered forecasts, append-only
    censuses.jsonl          # Domesday results, append-only
    wheels.jsonl            # Wheel question sets and their answers, append-only
    outcomes.jsonl          # measured values that resolve forecasts, append-only
    postmortems.jsonl       # mined history (P01..P23 seeded from pass 1), append-only
  output/
    CALIBRATION.json        # per planner and per class: Brier, interval score, coverage, log ratio
    REFERENCE_CLASSES.json  # measured base rates later plans must start from (section 2.4)
    VOI.json                # ranked next actions (section 5)
    LLULL_SCORE.json        # Juvenal: recall and precision of flags (section 6)
    STATUS.json
```

Ledger conventions are the same as Junto's: append-only JSONL, `schema`/`rev`/`written_at`/
`written_by` (agent name), ids `L-<yyyymmdd>-<n>` (forecast), `D-` (census), `W-` (wheel),
`O-` (outcome). The privacy rules in Junto section 5 apply unchanged: aggregates and
repository-relative paths only, no transcript text, no secrets, no email addresses. Driver and
gates run with `python3 -I`, use the standard library only, and give the same result for the
same commit. A gate too heavy for the container runs as `jobs/llull-census/` with `needs.txt` in
Actions, and Llull reads its `output/STATUS.json` first.

## 2. BRIER: the forecast ledger

### 2.1 Plan spec

A plan registers before it runs: `jobs/llull/plans/<plan_id>.json`.

```json
{"schema": "llull.plan/1", "plan_id": "Y3-2026-10-21", "planner": {"agent": "claude", "model": "claude-opus-5-5"},
 "plan_doc": "research/plans/EXCAVATOR_FUNNEL_2026-10-20.md",
 "pool": {"source": "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv",
          "filter": {"eo_min": 7532, "provisional_status": ["no"], "ready_for_human_review": "no"}},
 "steps": [
   {"step": "draft_end_claim", "requires": ["original_text_held", "ending_instrument_held"], "unit": "accepted_claim"},
   {"step": "tracker_rerun",   "requires": ["claim_checker_pass"], "unit": "ready_order"}],
 "forecasts": [ ... section 2.2 ... ]}
```

`requires` names gate keys from `gates/gates.json`. A step whose input is not a registered gate
must say `"requires_unmeasured": ["<what>"]`. The Wheel turns each such entry into its first
question.

### 2.2 Forecast record (`ledger/forecasts.jsonl`)

| Field | Meaning |
|---|---|
| `forecast_id`, `rev`, `plan_id`, `planner` | `planner` = `{agent, model}` |
| `registered_at`, `registered_commit` | Commit that holds this line. It must precede every run artifact of the plan (section 2.3). |
| `quantity` | One of the outcome units in `config.json`: `ready_orders_gained`, `upheld_per_attempt`, `rejected_per_submitted`, `accepted_items`, `usd_per_ready_order`, `usd_total`, `minutes_per_accepted`, `items_reached`. Proxy units (payload tokens, bytes, packets, certificates, agent-hours not from `get_session`) are refused, which closes `PROXY_UNIT` at the door. |
| `kind` | `interval` (p10, p50, p90) or `binary` (event text plus probability) |
| `p10`, `p50`, `p90` | An 80% central interval. Required for `interval`. |
| `event`, `prob` | For `binary`, e.g. `"upheld_per_attempt >= 0.5"`, prob 0.2 |
| `reference_class` | Key in `REFERENCE_CLASSES.json`, or `"new:<key>"` with a reason |
| `outside_view` | The reference class value BRIER filled in at registration (section 2.4). It is stored so the plan can be scored against it. |
| `census_id` | The Domesday result this forecast is capped by (section 3), or `null` with a reason |
| `deviation` | If p50 departs from `outside_view` by more than 2x: one line on why, which the Wheel turns into a question |
| `resolution` | How it resolves: committed file path, column or field, filter, and the date by which it is read. Example: `{"file": "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv", "count": "ready_for_human_review=yes", "baseline": 135, "by": "2026-11-01"}` |

### 2.3 Registration rules (`llull.py register --plan FILE`)

1. **Before running.** `register` refuses a plan if any file under its declared run directories
   exists in a commit earlier than the forecast line. `check` re-verifies this from git history,
   so a forecast written after the fact fails. A plan may run before the line is pushed, but the
   commit order still proves which came first.
2. **Every steering number is a forecast.** A number the plan uses to decide whether to scale
   (an upheld rate, minutes per item, a saving share) must be a registered forecast with an
   interval. An unregistered number is an `INVENTED_RATE` flag.
3. **Capped by Domesday.** For `ready_orders_gained`, `accepted_items` and `items_reached`,
   `p90` must not exceed the census ceiling of the step that produces the item. If the plan
   includes a step that creates the missing input (e.g. fetching ending instruments), that step
   needs its own forecast, and the cap becomes `ceiling_now + p90(unlock step)`.
4. **Start from the outside view.** If the reference class exists, `p50` defaults to its
   measured median. A planner may move away from it but must fill `deviation`. If the class has
   fewer than 3 outcomes, the interval must be at least as wide as `[0.1 x, 2 x]` of the
   planner's p50.
5. **Amend, do not overwrite.** A forecast can be amended (new `rev`) only before the first run
   artifact. After that it is frozen and scored as registered.

### 2.4 Reference-class table (`output/REFERENCE_CLASSES.json`)

These are measured base rates, derived only from `outcomes.jsonl` and `postmortems.jsonl`.
Each row lists its pool, n and source files. Classes are kept narrow because a broad class hides
the spread (the swarm's per-batch rejection ran from 0% to 50%). Seed rows from pass 1:

| Class key | Pool | Measured | n | Source |
|---|---|---|---|---|
| `upheld_per_attempt.modern_claim_no_held_end` | EO >= 7532, claim needs TERM/ACT or CURRENT | 0.06 | 3/50 | Bowditch Y2 |
| `accepted_per_attempt.modern_status_sweep` | EO >= 7532, status-history/OFR held | 0.30 | 15/50 | Bowditch Y1 |
| `minutes_per_accepted.modern_status` | same | ~1.5 | 15 | Bowditch Y1 |
| `minutes_per_accepted.reviewer.modern_claim` | Y2 | ~15.4 (reviewer only) | 3 | Bowditch Y2 |
| `rejected_per_submitted.codification_easy` | Codification revocations | 0.107 overall (0-0.50 per batch) | 176 accepted | swarm 10-18 |
| `rejected_per_submitted.harder_families` | Sol, A2, X1, Y2 pilots | 0.167, 0.105 (2/19; built rows were first 2/9, a stop trigger), 0.17, 0.40 | 4 pilots | P07, P12, P17, P19 |
| `accepted_per_target.family_claims` | Sol brief | 0.24 | 12/50 | P08 |
| `complete_per_accepted.family_rule_targets` | A2 | 0.105 | 2/19 | P12 |
| `hit_rate.type_tribunal` | X1 | 0.19 | 3/16 | P17 |
| `hit_rate.extinction_event` | X1 | 0.0 | 0/4 | P17 |
| `eligible_share.pre1937_orders` | status + held text | 0.0065 | 52/8,014 | P17 |
| `cleared_per_queued.opus_refetch` | A1 | 0.036 | 17/472 | P13 |
| `items_per_planned.blocked_host` | HathiTrust | 0.0 | 0/1,712 | P11 |
| `measured_over_forecast.all_misses` | 12 unfavourable misses | median 0.036 | 10 with ratio | pass 1 |
| `usd_build.meta_tool` | Junto build | $10.18 vs $12-25 forecast | 1 | P21 |

A new plan in a class it has no data for starts from `measured_over_forecast.all_misses`. Its
raw p50 is shown next to `0.036 x p50`, and the planner must say which one it registers.

### 2.5 Scoring (`llull.py resolve`, `llull.py score`)

`resolve --forecast L-... --measured N --source PATH` appends an outcome line. The value must be
readable from the committed file named in `resolution`, and `check` re-reads it. Scores:

- **Binary:** Brier `(prob - outcome)^2`. The Murphy decomposition (reliability, resolution,
  uncertainty) is reported per planner once there are 10 or more resolved binaries, using
  5 bins.
- **Interval:** the interval score at alpha = 0.2,
  `(p90 - p10) + 10 * max(0, p10 - y) + 10 * max(0, y - p90)`, divided by `max(|y|, 1)` so it can
  be compared across units. Coverage (the share of outcomes inside [p10, p90]) is reported
  separately; it should be near 0.8.
- **Magnitude:** the log accuracy ratio `ln(y / p50)` (`y` is floored at 0.5 of the unit so zero
  outcomes still score). Its median per planner is that planner's **optimism bias**.
- **Skill against the outside view:** each forecast is also scored with `outside_view` as its p50
  and the reference interval. `skill = 1 - score_planner / score_outside_view`. A planner with
  skill <= 0 over 5 or more forecasts in a class has the class median imposed as its default
  p50 for that class, and `deviation` then requires a Domesday or probe result as support.
- **Per planner calibration** in `CALIBRATION.json`, keyed by `{agent, model}` and by class:
  n, Brier, interval score, coverage, median log ratio and skill. History from pass 1 is loaded
  as `postmortems.jsonl` rows with `registered: false`. Those rows feed the reference classes
  but are kept out of calibration, because they were not registered before the run.

## 3. Domesday: the prerequisite census (gate dry-run)

`python3 -I jobs/llull/llull.py census --plan jobs/llull/plans/<id>.json`

This is a deterministic script with no agent, no model and (by default) no network. It reads the
plan's pool and each step's `requires`, evaluates every gate per item from committed outputs,
and writes `censuses.jsonl` plus a short table:

```
pool 2,063 (EO>=7532, status yes/no, original text done, not ready, no claim)
gate                         alone   cumulative
original_text_held           2,063   2,063
ending_instrument_held (NO)     64      64 of 1,683 NO
current_predicate_held (YES)     0       0 of 380 YES   (325 have leads only)
CEILING (strict)                64   = 3.1% of pool    -> p90(upheld_per_attempt) <= 0.031 + unlock
CEILING (leads counted)        389   = 18.9% of pool
```

The rows above are the Y2 rerun on the current repository (scratch `y2_predictor.py`). Y2 forecast
at least 50% upheld, and even counting every lead the ceiling is 18.9%.

*Built (review, 2026-10-20):* gates rev 2 counts only ending verbs and whole-scope TERMs: 38 strict and 363 leads
of 2,060 at 15b4b4d85. Bowditch Y2's measured 6% is above the strict share, and none of its 3 upheld orders
passed the gate, so the strict count is a gate-held share, not a proven ceiling (`jobs/llull/README.md`).

Rules:

1. **Joint, not product.** The ceiling is the count of items that pass **every** gate, computed
   per item. Domesday also prints `alone` counts and the product of the marginal shares. When the
   product exceeds the joint count by 1.5x or more, fewer items hold every gate than independence predicts
   (the gates are negatively associated, so multiplying marginal rates overstates the pool), and the
   plan is flagged `ASSUMED_INDEPENDENCE`.
2. **Gate registry** (`gates/gates.json`). Each gate has a key, a reader script, the files it
   reads and what "held" means. Seed gates, each traced to a committed output:

| Gate | Held means | Reads |
|---|---|---|
| `status_present` | `provisional_status` in {yes, no} | `jobs/readiness-tracker/output/READINESS_BY_ORDER.csv` |
| `original_text_held` | `step_original_text = done` | same |
| `clause_inventory_done` | `step_clause_inventory = done` | same |
| `custody_verified` | cited source is not `custody_record_only` | `jobs/claim-checker/`, `jobs/official-fixity/` outputs |
| `ending_instrument_held` | whole-scope ACT with effective date, or TERM with computed end | `jobs/claim-kit/output/ACTING_PROVISIONS.jsonl`, `OWN_TERMS.jsonl` |
| `current_predicate_held` | a held CURRENT predicate, not a lead | `jobs/current-law/output/ORDERS_CURRENT_LAW.csv` (lead and held are separate gates) |
| `media_resolved` | every cited Opus media matched | `jobs/opus-media-match/` output |
| `host_success_rate` | prior source-ladder success for the URL's host >= threshold | `jobs/source-ladder/` output |
| `family_target_text_located` | located original target text | `jobs/family-rules/output/` certificate blockers |
| `host_allows` | **network gate**: one `robots.txt` request plus one viewer request per host | live; results cached in `censuses.jsonl` with the date |

   `host_allows` is the only network gate. It sends at most 2 requests per host and runs only
   with `--network`. It would have stopped HathiTrust (0 of 1,712) for the cost of one request.
3. **The cap.** `register` reads the latest census for the plan at the same commit. If the
   census is older than the last commit to a file a gate reads, it must be rerun.
4. **Ceiling violation.** If a resolved outcome exceeds its census ceiling, a gate is wrong (it
   missed a route) or the outcome is wrong. Domesday logs `ceiling_violated` and the gate is
   reviewed before its next use. This is the `UNCONSIDERED_ROUTE` signal (P14, where an archive
   route made the crawl cheaper than planned).
5. **Back-tested on history.** For the 10 mechanically predictable misses, the gate queries
   in `postmortems.json` (`predictable_mechanically.query`) become gate readers first, so the
   seed set already covers X1 (52 eligible), the sprint (0 clause inventories), family rules
   (19 of 571 with located text and custody), Opus refetch (host success) and HathiTrust.

## 4. The Wheel: premortem generator

`python3 -I jobs/llull/llull.py wheel --plan jobs/llull/plans/<id>.json`

Two rings: the plan's steps and the 10 failure modes in `failure_modes.json`. A third, smaller
ring holds the kind of number each step leans on (pool size, rate, cost, unit). Each cell
(step x mode, filtered by number kind) yields one question. Where a mechanical check exists, the
Wheel runs it and marks the cell `auto_pass`, `auto_fail` or `needs_answer`. The frame is Klein's:
*"It is two weeks later. This step returned 1/28 of its forecast. Why?"*

| Mode | Question the Wheel asks | Mechanical check |
|---|---|---|
| `UNMEASURED_PREREQUISITE` | Which inputs must each item hold for this step to succeed, and how many items hold all of them today? | Domesday: every `requires` is a registered gate, the census is current, and p90 <= ceiling. `requires_unmeasured` is `auto_fail`. |
| `SELECTION_BIAS` | Where was the rate this step uses measured, and is this pool the same class? | The forecast's `reference_class` pool filter vs the plan pool. A different class, or a rate source with per-batch spread over 3x, is `auto_fail`. |
| `COST_SHIFT` | Who pays after the producer: review, correction, contrary-source research? Is the saving net of them? | A `usd_*` or `minutes_*` forecast must cover producer and reviewer. A producer-only unit is `auto_fail`. The reviewer share from the class (e.g. ~30% in the swarm) is shown. |
| `INVENTED_RATE` | Which number here has no measured source? | Every steering number is a forecast with `reference_class` or `new:` and a reason (rule 2.3.2). |
| `PROXY_UNIT` | Does success count ready orders, accepted items or billed $? | `quantity` is in the allowed outcome units (2.2). |
| `ASSUMED_INDEPENDENCE` | Do the steps or sources gate each other? Is a "bound" guaranteed or a tendency? | Domesday joint vs product of marginals (rule 3.1). A forecast that calls itself a bound needs an independent review line. |
| `ACCESS_ASSUMPTION` | Has one request to each host succeeded this week? | `host_allows` gate, and `host_success_rate` from source-ladder. |
| `REVIEW_LENIENCY` | Is the pass rate from a reviewer of the same model family in a single pass? | Reviewer model vs producer model in the plan. Same family plus a single pass is `needs_answer` (Y1's caveat). |
| `UNCONSIDERED_ROUTE` | Is there a cheaper route: an archive mirror, an index, a script instead of agents? | CDX or Common Crawl index lookup for URL lists (`--network`), and whether a zero-agent job already produces the input. |
| `POLICY_COUNTED_UNAPPROVED` | Does the forecast count a rule change the owner has not approved? | The step names an owner decision. If no approval line is cited in `HANDOFF/`, the cell is `auto_fail`. |

Output: `wheels.jsonl` plus `research/plans/llull/<plan_id>_QUESTIONS.md`, at most 12 questions,
ordered by `auto_fail` first and then by the mode's base rate among past misses (8/12, 5/12, ...).
**Gate:** a plan with an open `auto_fail` cannot be marked ready to run until it is fixed
(e.g. the forecast is lowered to the ceiling) or the planner answers and accepts the flag. An
accepted flag stays on the record for Juvenal's precision count.

## 5. Raiffa: value-of-information ranking

`python3 -I jobs/llull/llull.py voi --actions jobs/llull/plans/<id>.json`

Candidate next actions come in three tiers: **zero-agent checks** (Domesday gates, a tracker
rerun, an index lookup), **agent probes** (a bounded pilot of 20 to 50 items, Bowditch-style),
and **production runs**. For each:

```
cost_usd      = Actions minutes (zero-agent) | reference class usd_per_attempt x n (probe, run)
E_ready       = ceiling x p(accepted | attempt) x p(ready | accepted)     # from the forecast and its class
EVSI_ready    = sum over probe outcomes o: P(o) x max_a E[ready | a, o]  -  max_a E[ready | a]
                (a in {scale, stop, redirect}; a two-or-three-action preposterior over the probe's 80% interval)
EVPI_ready    = E[max_a ready | truth] - max_a E[ready]   # upper bound on what any probe is worth
rank          = (E_ready + EVSI_ready) / cost_usd         # ready orders per $; information counted in ready orders
```

Rules:

1. **Zero-agent first.** A zero-agent check that can change any cap or class used by a pending
   decision is run before any agent action, whatever its rank. It costs about $0 and its EVSI is
   at least 0.
2. **No probe worth more than EVPI.** If `EVPI_ready x usd_per_ready_order < probe cost`, the
   probe is skipped and the decision is made on current information.
3. **Probes pre-register a scale rule.** A probe is a plan with forecasts. It scales only if the
   measured rate is inside the forecast's [p10, p90] or above it, as Bowditch did with Y2.
4. **Costs are measured costs.** `usd_per_ready_order` comes from `get_session` totals in
   `outcomes.jsonl` and is shown with its n. Verified Junto savings (and only those) lower a
   class's cost. Unverified savers are ignored.
5. **Output** `VOI.json`: action, tier, cost, E_ready, EVSI, EVPI, rank, the decision it informs.
   It is advice to the coordinator, as Junto's `allocate` is.

## 6. Juvenal: Llull's own score

Llull is a forecaster of misses, so it is scored like one.

- **Flag recall** = misses whose actual failure mode had an `auto_fail` or an unanswered
  `needs_answer` flag in a Wheel line committed before the run, divided by all misses. A miss is
  a resolved forecast with outcome below p10 (or above p90 for cost), or a binary event scored
  wrong with prob >= 0.7.
- **Flag precision** = flagged cells whose plan then missed for that mode, divided by all flagged
  cells. This stops "flag everything" from scoring well. The Wheel's 12-question cap and the
  `auto_pass` checks keep the count bounded.
- **Calibration lift** = mean interval score of planner-registered forecasts minus that of the
  Domesday-capped, outside-view forecast, on the same resolved plans. If it is positive, Llull's
  caps helped.
- **Ceiling hits** = resolved outcomes at or below their census ceiling, divided by all capped
  outcomes. Domesday's own claim is that the ceiling holds; a violation lowers this number and
  opens a gate review.

**Held-out history.** The 10 failure modes were derived from all 23 plans, so a score on them is
in-sample. Juvenal therefore reports two numbers:
(a) **temporal hold-out**: freeze `failure_modes.json` and the gates using only P01 to P12
(dated 2026-10-17 to 10-18), run the Wheel and Domesday on P13 to P23 as written, and count
recall and precision on their misses (P13, P17, P19 among them). Any mode that first appears in
the later plans counts as a miss Llull could not flag.
(b) **future plans**: every plan registered from the build date on. **Only (b) earns trust.**
(a) is reported once and labelled in-sample-derived.

`LLULL_SCORE.json` records n, recall, precision, calibration lift and ceiling hits, each with the
ids behind it. Until (b) has at least 5 resolved plans, Llull's flags are advice and its score
is "unproven", as an unscored Junto finder scores 0.

**Llull's cost.** Its own driver runs are logged with `get_session` cost, as Junto logs `F-junto`.
`STATUS.json` shows Llull's dollars spent beside its recall, so the meta-tool pays its way in the
open.

### Relation to Junto

| | Junto | Llull |
|---|---|---|
| Asks | Which **finders** produce token savers that verify? | Which **plans and forecasts** deserve trust before money is spent? |
| Unit scored | Verified $ saved / $ spent per finder | Brier and interval score per planner; Llull's own flag recall and precision |
| Evidence | Before-and-after `get_session` tests | Pre-registered forecasts resolved from committed outputs |
| Blind spots | Standing queries: waste no finder targets -> finder proposal | A miss whose mode no Wheel cell flagged -> new row in `failure_modes.json` (and a new gate if a check exists) |

They share the ledger conventions, privacy rules, the `check` discipline and the hard rule.
Junto's verified savings feed Raiffa's cost per ready order. A Junto test is a plan, so it is
registered in BRIER with its expected saving as an interval forecast. Hamilton's savers (P20)
then get calibration scores like everything else. Llull never credits itself with Junto's
savings, and Junto never counts Llull's avoided runs.

## 7. Open forecasts to register first

These forecasts have not been scored. Each is registered with an interval or a probability
before its resolving run:

1. **Census bounds (P15).** Undiscovered 1862-1899 orders 295-555, called "all lower bounds".
   Astra's review (`research/plans/ASTRA_REVIEW_CENSUS_ESTIMATORS_2026-10-18.md`) showed the bound
   is a tendency, not a guarantee. Register it as an interval, and add a binary: "the next
   discovery batch leaves the Chao1 estimate inside 295-555". It resolves from
   `jobs/census-completeness/` output.
2. **Hamilton savers (P20).** Revere about 40% off an X1-like session, Quiet 5-15%, Watchman most
   of the 15% waiting cost. Register each as an interval on `usd_per_unit`, resolved by its Junto
   test.
3. **CSC reports reach "most of" the 695 waivers.** Register "most" as a binary: share >= 0.5,
   with an explicit prob. A Domesday gate (waiver year x CSC annual-report year held in
   `jobs/csc-annual-reports/` output) gives the ceiling before any agent reads a report.

## 8. Build order (proposed, not started)

1. `llull.py check` plus an empty ledger. Load `postmortems.jsonl` from pass 1
   (`build_postmortems.py` and `postmortems.json` in scratch) as unregistered history.
2. Domesday with the seed gates, starting from `y2_predictor.py` and the 10 mechanical queries.
   Rerun it on X1, Y2, family rules and the sprint, and confirm it reproduces 52, 64, 19 and 0.
3. `register` and `score`, then derive `REFERENCE_CLASSES.json`. Register section 7's three
   forecasts.
4. The Wheel with the table in section 4. Run the temporal hold-out once and report it as
   in-sample-derived.
5. Raiffa last: it needs measured costs per class, and today most classes have only n = 1 to 4.

Commands (as planned; all `python3 -I jobs/llull/llull.py ...`):

```
register  --plan FILE                 validate, fill outside_view and cap, append forecasts
census    --plan FILE [--network]     Domesday gate dry-run; joint ceiling per step
wheel     --plan FILE                 premortem questions with mechanical checks -> QUESTIONS.md
voi       --actions FILE              rank next actions by (E_ready + EVSI) / $
resolve   --forecast L-.. --measured N --source PATH
score                                 CALIBRATION.json, REFERENCE_CLASSES.json
selfscore [--holdout-before 2026-10-19]  LLULL_SCORE.json
check                                 schemas, registration-before-run order, privacy, re-read outcomes
```

None of this changes the codebook, claim statuses, tiers or the certified whole-lifecycle count
(0).

## Sources

- Flyvbjerg et al., reference-class forecasting for the Edinburgh Tram Inquiry: https://arxiv.org/pdf/1805.12106 ; PMI, "Planning for the planning fallacy": https://www.pmi.org/learning/library/planning-fallacy-causes-solutions-project-expectations-6374 ; on how the class definition changes uplifts: https://www.projectmanagement.com/blog-post/79682/reference-class-forecasting-depends-on-how-you-define--similar-
- Klein, "Performing a Project Premortem", *HBR* 85(9), 2007; Mitchell, Russo and Pennington 1989 on prospective hindsight (attribution as summarised at https://archive.phf.org/resourcestools/Documents/Pre_Mortem_Analysis.pdf)
- Brier score and Murphy decomposition: https://www.wikipedia.com/wiki/Brier_score ; https://arxiv.org/pdf/1303.6182
- Interval score (Gneiting and Raftery 2007, Section 6.2): https://scores.readthedocs.io/en/2.0.0/tutorials/Quantile_Interval_And_Interval_Score.html ; https://doi.org/10.1198/016214506000001437
- Value of information / EVSI: https://en.wikipedia.org/wiki/Expected_value_of_sample_information
- Tetlock's forecasting habits (decomposition, triage): https://aiimpacts.org/evidence-on-good-forecasting-practices-from-the-good-judgment-project/ ; https://fs.blog/ten-commandments-for-superforecasters/
