# Token-count and Bentham estimates against Necker's priced estimate

API-price estimates, not bills. Under a subscription none of these dollars is charged.

| Wave | Agents | Total tokens | Cache reads, share of tokens | Bentham USD | Necker USD | Necker / Bentham | Lumped USD | Lumped / Necker | Cache reads, share of Necker USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tribonian-2026-11-04 | 78 | 1,354,974,123 | 96.2% | 815.18 | 419.36 | 0.51 | 3,720.64 | 8.87 | 41.8% |
| claude-icecore-2026-11-05 | 7 | 98,946,980 | 97.2% | 59.25 | 32.92 | 0.56 | 297.57 | 9.04 | 43.0% |
| claude-theophilus-2026-11-05 | 11 | 109,086,406 | 97.7% | 73.46 | 41.70 | 0.57 | 397.09 | 9.52 | 45.5% |

Columns: `tokens_total` fresh input + output + cache read + cache write, summed (a size, not a price). `usd_bentham` Bentham measure.py table: Sonnet 3/15/0.30/3.75, Opus 5/25/0.50/6.25, both cache-write kinds at one rate. `usd_necker` per-model list price of the model in the row (PRICES.json), 5m and 1h writes apart. `usd_lumped` every input-side token (fresh, cache read, cache write) at the full input price, output at the output price, current rates: the estimate that lumps cache reads with full-price input.

