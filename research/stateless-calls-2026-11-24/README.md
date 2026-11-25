# Stateless calls: the paired-replay gauge (2026-11-24)

## Finding

On Papinian (`research/excavator/claude-papinian-2026-11-10`) the agent workers made about 60-110 calls each at about
170-214k tokens of context per call, about 2.3M tokens per worker. That cost $0.64 per attempted order and $4.71 per
filed claim at list price. The evidence one order needs is about 16.5k tokens (median) for a producer and about 9.7k for
a reviewer, so most of the spend re-reads context. Making every model stage one request with no tools projects a 2.4x
saving with Sonnet producers and 5-8x with Haiku 5.5 producers. The Maudslay conveyor now has that mode (`conveyor.py run
--stateless`, described in `jobs/maudslay-conveyor/README.md`, section "Stateless mode and the gauge"). The projection is
not a measurement: this gauge measures it.

## What the gauge does

`jobs/maudslay-conveyor/gauge_stateless.py` replays Papinian's own work through stateless workers, under $25 at the
list prices in `jobs/necker-costs/PRICES.json`, and compares each result with what the agents did.

1. **Producers.** 60 orders (a seeded draw of 30 that Papinian filed and 30 that it did not, from the `y*`, `c01` and
   `r01b` packets) go through a stateless Sonnet producer and a stateless Haiku 5.5 producer. Each answer is written as a
   sheet with the prepared column sets and checked; its outcome (submit or not), status (`operative_force_at_cutoff`,
   `claimed_status`) and end dates are compared with the agent producer's final sheet.
2. **Reviewers.** 40 already-reviewed genuine claims (20 the agent arms filed, 20 they did not; from
   `reviews/BLIND_REVIEW_{A,B}.jsonl` and the applied `CLAIMS.proposed.jsonl`) plus the planted controls go through two
   stateless Opus arms, arm B straight after arm A so it reads A's cached prefix. The controls are regenerated exactly as
   `tools/review_prep.py` planted them (seed `'papinian-controls:' + batch`, every end date moved back three years). The
   regenerated planted hashes equal the `planted_claim_sha256` values in each batch's `COMPLETION.json`, and both agent
   arms rejected each. 16 of Papinian's 18 controls can be regenerated from this checkout (`y01`-`y14`, `c01`,
   `r01b`); the other two belong to batches that left no reviewable packet. A control is caught only if both arms
   rejected its exact planted hash and named a date in their defects (the conveyor's rule, `C.caught`). The both-uphold
   rule is unchanged: a claim files only if both arms upheld it. The reveal pass is not replayed.

The run is a replay, not a chained pipeline: reviewers see Papinian's claims, not the stateless producers' claims.

## Stop rule (computed and printed by the gauge)

`KEEP_AGENT_ROUTE` if any of these holds:

- any planted control is missed by either arm;
- the stateless-vs-agent verdict disagreement exceeds the agent arms' own 7 of 85 (8.2%). The verdict is the both-uphold
  decision (file, block or split) on the 40 genuine claims, stateless pair against agent pair, so 4 or more disagreements
  of 40 trips it;
- the measured list-price cost exceeds $2.50 per filed claim, computed for Sonnet producers as
  `(producer cost per order + submit rate x (reviewer-pair cost x (1 + 1/15 for the reveal pass))) / (submit rate x upheld rate)`,
  with the filed and not-filed strata reweighted to the Papinian corpus (63 filed of 377 attempted orders). Haiku's figure
  is reported beside it;
- the run is incomplete (the dollar cap stopped it, or a request failed), because no GO can be concluded from a partial run.

Otherwise `GO_STATELESS`, with `haiku_matches_sonnet` true when Haiku's outcome agreement with the agent and its end-date
agreement are each within one order of 60 of Sonnet's or better.

## Owner commands

```text
python -I jobs/maudslay-conveyor/gauge_stateless.py --dry-run --scratch C:/Users/danie/maudslay-scratch/stateless-gauge
python -I jobs/maudslay-conveyor/gauge_stateless.py --scratch C:/Users/danie/maudslay-scratch/stateless-gauge --cap-usd 25
```

`claude -p` must be logged in on that PC. The first command renders everything and prints the token estimates and the
forecast without calling a model. The second writes `GAUGE_RESULTS.json` and `GAUGE_REPORT.md` into this folder: per-arm
control catches, stateless-vs-agent agreement, list-price cost per stage and per filed claim, and the cache evidence (the
second and later processes with the same prefix should show a first-call `cache_read` of about the prefix size).

`GAUGE_RESULTS.json` and `GAUGE_REPORT.md` do not exist until the owner runs the gauge.
