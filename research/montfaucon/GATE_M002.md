# Bentham checkpoint after m002

The accepted 50-order m002 batch has 32 validated passes and 18 validated
failures. Both readers caught all three controls; five verdict disagreements
received independent third-reader adjudications. EO:7624's initial uncertainty
was resolved by two independent supplemental reviews of a contemporary GPO
Monthly Catalog entry that binds its number to the exact Federal Register
issue and page. Thus 50 attempts, 50 submissions and 32 filings enter this
checkpoint.

The native `bentham.py gate --action
acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK` still exits “not a ranked production
action”: its current `PLAN.json` row has zero orders and no measured rate.
The attempted native command named the requested `BATCHES.jsonl` ledger;
the wrapper rejects the action before opening that file. The JSONL ledger is
mirrored in `BATCHES.json` because the direct parser accepts JSON arrays or
CSV, not JSONL.
The saved `GATE_M002.json` is the direct `gate.py --window 1` result using a
declared uniform Beta(1,1) prior, $0.38/attempt planning proxy and the plan's
next-best 0.1547238618 dossiers/USD. It returns **CONTINUE**, posterior mean
0.6346 and probability of beating the next action 1.0. This is conditional
on the proxy. Actual USD and model-level tokens are unavailable;
`spent_usd: 0` is the parser's treatment of unknown `usd: null`, not measured
spend. See `COST.md`.
