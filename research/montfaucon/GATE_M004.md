# Bentham checkpoint after m004

The accepted 50-order m004 batch has 42 validated passes, 8 failures and
zero uncertainty. Both blind readers caught all three controls. Four
disagreements about plausible OCR substitutions received a fresh blind
third-reader adjudication; all four passed under the explicit OCR-noise
allowance, with each printed and held difference retained in the record.

The required native `bentham.py gate --action
acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK --batches
research/montfaucon/BATCHES.jsonl` still exits “not a ranked production
action” because the PLAN row has zero orders and no measured rate. It rejects
the action before reading the ledger. `BATCHES.json` mirrors the JSONL ledger
for the direct parser, which accepts JSON arrays or CSV.

The saved direct `gate.py --window 1` receipt uses a declared uniform
Beta(1,1) prior, $0.38/attempt plan proxy and next-best 0.1547238618
dossiers/USD. It says **CONTINUE**, posterior mean 0.8269, probability of
beating the next action 1.0. This is conditional planning, not measured
cost. Actual USD and model-level tokens are unavailable; `spent_usd: 0`
reflects unknown `usd: null` in the parser, not measured spend.
