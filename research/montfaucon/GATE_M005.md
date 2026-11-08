# Bentham checkpoint after m005

The accepted 50-order batch has 35 validated passes, 10 failures and
5 unsure. Both blind readers caught all three controls. The two verdict
disagreements received a fresh blind third reading, one unsure and one fail.

The required native `bentham.py gate --action
acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK --batches
research/montfaucon/BATCHES.jsonl` still exits “not a ranked production
action” because the PLAN row has zero orders and no measured rate. It rejects
the action before reading the ledger. `BATCHES.json` mirrors the JSONL ledger
for the direct parser, which accepts JSON arrays or CSV.

The saved direct `gate.py --window 1` receipt declares a uniform Beta(1,1)
prior, $0.38/attempt plan proxy and next-best 0.1547238618 dossiers/USD.
It says **CONTINUE**: posterior mean 0.6923 and probability of beating the
next action 1.0. This is conditional planning, not measured cost. Actual
USD and model-level tokens remain unavailable; `spent_usd: 0` is the parser's
treatment of unknown `usd: null`, not measured spend.
