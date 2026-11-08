# Bentham checkpoint after m003

The accepted 50-order m003 batch has 36 validated passes, 14 validated
failures and no uncertainty. Both blind readers caught all three controls.
Two disagreements about whether prescribed manuals belong to complete-order
scope received fresh blind third-reader adjudication: EO:10020 and EO:10214
both fail because the held texts end partway through their manuals.

The required native `bentham.py gate --action
acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK --batches
research/montfaucon/BATCHES.jsonl` again exits “not a ranked production
action”: the PLAN row has zero orders and no measured rate. It rejects the
action before opening the JSONL ledger. `BATCHES.json` mirrors that ledger for
the direct parser, which accepts JSON arrays or CSV.

The saved direct `gate.py --window 1` result uses a declared uniform Beta(1,1)
prior, $0.38/attempt plan proxy and next-best 0.1547238618 dossiers/USD.
It says **CONTINUE**: posterior mean 0.7115, probability of beating the
next action 1.0. This is conditional planning, not measured cost. Actual
USD and model-level tokens remain unavailable; `spent_usd: 0` is the parser's
treatment of unknown `usd: null`, not measured spend. See `COST.md`.
