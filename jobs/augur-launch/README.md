# Augur: the launch gate for agent waves

Named for the Roman augurs, who took the auspices before every public undertaking and could halt it.

```bash
python -I jobs/augur-launch/augur.py sha WAVE.json      # the hash a reviewer signs
python -I jobs/augur-launch/augur.py check WAVE.json    # PASS (exit 0) or REFUSE (exit 2), with a forecast
```

The Savigny supervisor (`jobs/savigny-supervisor/`) runs this check itself at startup and will not start a refused
wave. Any other wave, Claude or Codex, should run it before it spends.

## Why it exists

On 2026-11-09/10 an overnight Codex wave spent about half the owner's weekly allowance for 12 filed claims (Kean
F-20261110-mommsen-unranked-pools, F-20261110-codex-token-split). The project was not missing the lessons:

| Already recorded before the launch | What the wave did |
|---|---|
| Carnot PROTOCOL: coordinators had taken more than half of past waves' cost | Very High coordinators re-sent 190k-447k contexts on about 3,000 calls (54% of tokens) |
| Kean F-20261109-gutenberg-carnot: run the next wave as the measured "lean coordination" arm | ran heavier coordination, unmeasured |
| Bentham: "pre-1937 strata have no measured yield yet" | five lanes on pre-1937 orders; 494 of 593 reserved orders in no Bentham action |
| Kean F-20261107-haloander-undecided-probe: 0 of 30 undecided below EO 7532 filed | a lane assigned to them anyway |
| Montfaucon stopped after 0 of 50 | quoted in the prompt; the pool's neighbors were assigned |

The coordinator cited most of these in the wave's own prompts. What failed was the structure:
1. **Lessons were pull-only.** Kean must be searched; nothing checked the plan against it when the decision was
   made.
2. **The author approved his own plan.** The project has independent review for claims, but had none for plans.
3. **The objective drifted** from "claims per unit of cost" to "use the allowance", and nothing guarded it.
4. **A never-run configuration went straight to five lanes.** Bentham's 30-order probe rule covered pools, not
   methods.
5. **No forecast, and feedback came late.** Results were self-reported, and the published count moved hours later.

The same pattern appears outside the project:
- **Pull lessons registers fail.** GAO-02-195 found 23% of NASA managers had ever contributed to the agency's
  lessons system, and NASA's Inspector General (IG-12-012, 2012) found it rarely used. The fix is to push lessons
  into the procedure at the decision point.
- **Novel launches get an outside review against a fixed checklist,** as in Google SRE's launch checklist and its
  production readiness reviews.
- **Unproven changes ramp up only on an outcome metric.** Flagger halts a canary and rolls it back on failed metric
  checks, not on activity.

## The checks (each refusal names its reason)

1. **Outcome objective.** `objective.metric` is one of `filed_dossiers_per_unit`, `ready_gain_per_unit`,
   `verified_claims_per_unit`. Objective text that names spend or activity as a goal ("use the allowance", "burn",
   "keep lanes busy") is refused. Spend is a limit, never an objective.
2. **Bentham only.** Every action is in `jobs/bentham/output/PLAN.json`. A measured action below 0.2 dossiers per
   API-equivalent dollar runs only as a probe. An unmeasured or unranked action runs on one lane with at most 30
   orders.
3. **Forecast.** Expected filed dossiers and expected dollars, from Bentham's measured rates, are written into the
   receipt. Compare them with what the run actually filed.
4. **Ramp by configuration.** The configuration is `orchestrator|coordinator family|producer family`. Stage 0 is one
   lane, 30 orders and 6M units. Stage 1 is up to 3 lanes, 300 orders and 40M units. Stage 2 is full scale. A
   configuration may launch only one stage above the highest stage it has passed in `CONFIGURATIONS.json`. A run
   is added there only from a Kean finding with measures, never from an estimate.
5. **Lessons pushed to the decision.** Every Kean finding with verdict failed, stopped_at_gate or partly_worked that
   matches the plan's actions, models or orchestrator must be answered in `acknowledged_findings` (finding id:
   how this plan handles it, 25 characters or more).
6. **Pre-mortem.** At least three entries, each a concrete failure and the guard against it.
7. **Independent review.** `review.plan_sha256` must equal the plan's hash (`augur.py sha`), the verdict must be
   `approve`, and the reviewer must be a different model family from the author, or the owner. Editing the plan
   after review voids the review.
8. **Limits.** Every supervisor limit is set, and the lanes, orders and budget fit the stage.

## Plan shape (`WAVE.json`)

```json
{"wave": "name", "author": "claude-opus-5-5", "stage": 0,
 "objective": {"metric": "filed_dossiers_per_unit"},
 "actions": [{"id": "production.claim_ready.yes.fr", "orders": 30, "lanes": 1}],
 "configuration": {"orchestrator": "maudslay-conveyor", "coordinator_model": "claude-opus-5-5", "producer_model": "gpt-6.1-sol"},
 "limits": {"chain_budget_units": 6000000, "spend_per_claim_units": 3000000, "no_claim_minutes": 40,
            "context_kill_tokens": 120000, "reviews_per_hour": 6, "coordinator_units_per_hour": 1000000},
 "premortem": [{"failure": "...", "guard": "..."}],
 "acknowledged_findings": {"F-...": "how this plan handles it"},
 "review": {"reviewer": "gpt-6.1-sol", "verdict": "approve", "plan_sha256": "..."}}
```

## Limits of this gate

- A reviewer receipt is a file. An author could write a fake one. The family rule and the hash binding make that a
  deliberate act, not an accident. For high-stakes waves, the owner signs.
- The lessons match is keyword-based. A finding filed without useful keywords will not be pushed, so file findings
  with the action ids, models and orchestrator they concern.
- The forecast is only as good as Bentham's measured rates, and it says when they rest on fewer than 30 attempts.

Tests: `test_augur.py`, including a replay of the 2026-11-09/10 plan, which Augur refuses for eight of the reasons
it failed. Runs in road CI.
