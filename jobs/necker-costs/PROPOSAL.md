# Proposal: the smallest Bentham change that reads Necker's dollars

Bentham already has two places where dollars enter. This proposal edits neither; it is for the coordinator.

1. **Gate batch files** (`bentham.py gate --batches FILE`) take a `usd` column per batch. Necker's
   `output/telemetry/<wave>/gate_<wave>.csv` and `output/BATCH_COSTS.csv` already use the gate's column names
   (`batch, attempted, submitted, filed, controls_missed, usd`), and the gate ran on one unchanged. No change is needed.
   The gate only reports `usd` as money spent; its decision uses `cost_per_attempt` from `output/PLAN.json`.
2. **The plan's unit costs** (`MEASURED.json` `costs`, built by `measure.py`) are where dollars decide the ranking, and
   they use `PRICE_TABLE` (Sonnet 3/15/0.30/3.75, Opus 5/25/0.50/6.25, one cache-write rate). Necker prices the same
   token rows at about 0.47 (production), 0.57 (review) and 0.52 (coordination) of that. The smallest change is in
   `measure.py::usd` and `load_usage`:

```python
# measure.py: replace PRICE_TABLE by the per-model table Necker keeps
import json, re
_PRICES = json.loads((REPO / "jobs/necker-costs/PRICES.json").read_text())
_MODELS = [(re.compile(m["match"]), m) for m in _PRICES["models"]]

def usd(model, tokens):          # tokens keep the cache-write split
    for rx, m in _MODELS:
        if rx.search(model):
            return (tokens["fresh_input"] * m["input"] + tokens["output"] * m["output"]
                    + tokens["cache_read"] * m["cache_read"]
                    + tokens["cache_write_5m"] * m["cache_write_5m"]
                    + tokens["cache_write_1h"] * m["cache_write_1h"]) / 1e6
    raise MeasureError("no price for " + model)
```

   `load_usage` would keep `cache_write_5m` and `cache_write_1h` apart instead of summing them into `cache_write` (the
   CSV already has both columns), and `price_table` in `MEASURED.json` would cite `PRICES.json`, its URL and its
   retrieval date instead of "assumption". The window-token fields stay as they are.
3. Optional, no code in Bentham: `bentham.py usage` could also call `necker.py transcripts` so each wave's
   `AGENT_USAGE.csv` gets a `usd` column; for cloud waves the CSV already holds what `necker.py telemetry` needs.

Before adopting it, the owner should settle one fact the transcripts cannot: whether Opus workers in the cloud waves ran
with fast mode (Herschel's Opus workers cost the CLI 1.93 times the standard Opus 5.5 list price). If they did,
Necker's Opus dollars double and the production-to-review cost ratio moves.
