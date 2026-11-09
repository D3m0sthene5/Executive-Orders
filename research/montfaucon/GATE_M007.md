# Bentham checkpoint after m007

The accepted 50-order batch has 0 validated passes, 49 failures on wrong cited
pages and 1 blocked target with no immutable held original text. Both blind
readers caught all three planted controls; no production output was
quarantined. The cited PDF's SHA-256 was verified. The lead lane stopped after
this batch because its machine locators were wrong and its held text absent.

The required native `bentham.py gate --action
acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK --batches
research/montfaucon/BATCHES.jsonl` refuses the action before reading the ledger:
the PLAN row has zero orders and no measured rate. The saved direct `gate.py
--window 1` receipt declares a uniform Beta(1,1) prior, $0.38 per attempt
planning proxy and 0.1547238618 dossiers/USD next-best rate. It says **STOP**:
posterior mean 0.01923, probability of beating the next action 0.04549, below
0.2. Actual model tokens and USD are unavailable. `spent_usd: 0` is the
parser's treatment of `usd: null`, not measured spend.
