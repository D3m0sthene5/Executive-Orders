# Stateless gauge report

Verdict: **KEEP_AGENT_ROUTE**; haiku_matches_sonnet: **false**.

Reasons: stateless-vs-agent verdict disagreement 2/2 = 1.000 exceeds the agent arms' own 7/85 = 0.082; measured cost $4.30 per filed claim exceeds $2.50; the run is incomplete (dollar cap reached or calls failed), so no GO can be concluded

Spent $25.06 of the $25.00 cap at list price (jobs/necker-costs/PRICES.json). Run complete: False.

## Planted controls

Regenerated 16 of the 18 Papinian controls (review_prep.py seeding; the u* batches left no reviewable packet in the checkout). Stateless arm A caught 16/16, arm B 16/16, both 16/16 (agent arms caught both on 16).

## Review agreement

On 40 genuine reviewed claims the stateless pair disagreed with the agent pair on 2 of 2 compared (limit: the agent arms' own 7/85); arm A 3, arm B 2. In this sample the agent arms disagreed with each other on 13/40.

## Producers

| model | ran | valid sheets | outcome match | status match | end dates match | list-price USD |
|---|---:|---:|---:|---:|---:|---:|
| haiku | 55 | 55 | 20/55 | 17/55 | 2/2 | 1.07 |
| sonnet | 55 | 55 | 22/55 | 15/55 | 5/5 | 8.90 |

## Cost

List-price cost per stage: {"producer-haiku": 1.073805, "producer-sonnet": 8.897945, "review-A": 10.214076, "review-B": 4.872312}.

Cost per filed claim: {"haiku": 2.1484, "sonnet": 4.3037} (Papinian agent lane: $4.71). Formula: (producer usd per order + submit_rate x (reviewer pair usd x (1 + 1/15 reveal))) / (submit_rate x upheld_rate); strata reweighted to the Papinian corpus.

## Cache evidence

- prefix 0efcc8fb5eda (about 13193 tokens): 2 processes; 1 of 1 later processes read at least 80% of the prefix from cache on their first call.
- prefix 15aade16883a (about 11699 tokens): 2 processes; 1 of 1 later processes read at least 80% of the prefix from cache on their first call.
- prefix 1fd7386f7c0a (about 12091 tokens): 2 processes; 1 of 1 later processes read at least 80% of the prefix from cache on their first call.
- prefix 214d19e79099 (about 8688 tokens): 8 processes; 6 of 7 later processes read at least 80% of the prefix from cache on their first call.
- prefix 2e0e65b85a59 (about 10909 tokens): 2 processes; 1 of 1 later processes read at least 80% of the prefix from cache on their first call.
- prefix 34cedfdfc455 (about 13104 tokens): 2 processes; 1 of 1 later processes read at least 80% of the prefix from cache on their first call.

The run is a replay: reviewers see Papinian's claims, not the stateless producers' claims, and the cost per filed claim combines the two stages' measured costs with Papinian's corpus rates. Nothing here certifies anything.
