# Bentham: where the next agent tokens go

Named for Jeremy Bentham's felicific calculus (1789), which weighs an act's certainty, its nearness in time and its
fecundity (the further goods it makes likely) against its cost. Bentham joins tools the project already had but
never connected, so they run without anyone feeding them:

| Part | Existing tool it feeds from | What it does here |
|---|---|---|
| `measure.py` | wave dispositions; Hamilton telemetry | Filed dossiers per attempted order, by status and era; API-equivalent cost per attempted order, per reviewed claim and for coordination |
| `candidates.py` | readiness tracker, `SHARED_UNLOCKS.csv`, Polya | Every action available now: production strata, recoveries, source acquisitions with the orders each unblocks, zero-agent steps |
| `bentham.py plan` | Llull's rule that only measured rates may be used | Ranks actions by (expected dossiers now + discounted dossiers unlocked later) per dollar; writes `output/PLAN.md` |
| `gate.py` / `bentham.py gate` | Llull's Beta-binomial method | During a wave, after each batch: CONTINUE, PILOT or STOP |
| `sessions.py` / `bentham.py usage` | Hamilton's profiler | Finds this machine's Claude Code transcripts and writes sanitized per-agent token usage, so the next plan is measured on the newest wave |

## The score

For each action: expected dossiers now (orders x measured filed-per-attempt for its stratum), plus fecundity (orders
it moves into a draftable stratum x that stratum's measured yield, discounted with a 60-day half-life), divided by
its cost in API-equivalent dollars (measured tokens priced at Anthropic API list prices). Machine jobs and zero-agent
steps cost no model tokens and are listed first. The plan is recomputed at 30- and 180-day half-lives and says
whether the actions inside the budget change.

Bentham refuses to guess. A stratum whose yield rests on fewer than 30 measured attempts is listed as unranked with
the cost of a 30-order probe, which the gate then runs and measures. A cost that has not been measured leaves the
action unranked.

**Larrey triage (2026-11-10).** For an action Larrey triages (`jobs/larrey-triage`), `orders` is the number of members
its zero-token check admits; the plan shows "admitted of members". Yield per admitted order is the measured rate
times Larrey's back-test `yield_lift` (its rate among admitted orders over its rate among all attempted), and cost
per attempt is the measured cost times `cost_lift` (review stays while producers go), both capped by the action's
own members/admitted ratio. These are projections, noted in the plan, until a gated wave measures the rate (a rate
row marked `"gated": true` turns them off). An action whose route Larrey does not enforce is unchanged.

## During a wave

After each batch, append `{batch, attempted, submitted, filed, controls_missed, usd}` to a JSON or CSV file and run
`python3 -I jobs/bentham/bentham.py gate --action ID --batches FILE`. The gate judges the last two batches (on the
2026-11-04 replay a pooled gate never reacted, while a two-batch window stopped the wave at o23, where 9 of 60 orders
filed). It stops on any planted-control miss, pilots below 30 attempts, and stops when the probability that this
wave still beats the next-ranked action per dollar falls below 0.2.

## Percent of a week

Anthropic does not publish what a week of a plan buys. Measure it once: note the weekly figure in Settings > Usage
before and after a run, then
`python3 -I jobs/bentham/bentham.py calibrate --run-usd COST --percent-used DELTA --run NAME --by WHO`, with COST from
`bentham.py usage`. `data/ALLOWANCE.json` then lets every plan line show its share of a week.

## Limits

- Yields come from one wave so far (2026-11-04: 492 of 1,041 production orders filed; 53 of 83 corrections). Every
  attempted production order was a Federal Register-era order, so pre-1937 strata have no measured yield yet.
- Costs are API-equivalent at list prices, not invoices; the coordinator's tokens are a lower bound.
- **Prices (Gutenberg, 2026-11-09):** every dollar comes from `jobs/necker-costs/PRICES.json` through `pricing.py`
  (per exact model, 5-minute and 1-hour cache writes apart, fast mode and Haiku 5.5 long prompts per call). The old
  private table (Opus 5 / Sonnet 4.x rates) ran 1.3x-1.9x high per session and 1.94x on the Tribonian wave
  ($673 -> $346). Pass each worker's `claude -p` result or the wave's cost log to
  `bentham.py usage --reported-costs FILE`: the run cross-checks every reported session within max(1 cent, 1%), exits
  3 on a disagreement (outputs still written), and labels those sessions `worker` instead of `coordinator`.
- Fecundity counts an order only when one action alone clears what stands between it and a draftable stratum.
- Nothing here changes a status, claim, codebook grade or count, or dispatches anything by itself. Certified: 0.

Runs daily (`DAILY`), after the tracker, Polya, Neyman and Llull, and whenever a wave publishes new dispositions or
telemetry (`triggers.txt`). Tests in `test_*.py` run first. Design contract: `CONTRACT.md`.
