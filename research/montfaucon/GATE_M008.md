# Bentham checkpoint after m008

The accepted 50-order batch has one validated pass, 16 failures and 33 unsure.
Both blind readers caught all three planted controls. A fresh blind third
resolved the sole disagreement, EO:7520, as pass after complete image/held
text comparison. No reader output was quarantined.

The mixed government-report lane has low authentication yield: reprints often
omit the EO number, presidential signature or complete original wording, and
several cited Federal Register pages have wrong or incomplete spans. The lane
stopped and the next batch will favor directly cited 1936 Federal Register
issues and GPO original-printing volumes with immutable held text.

The required native `bentham.py gate --action
acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK --batches
research/montfaucon/BATCHES.jsonl` refuses this action before reading the
ledger: the PLAN row has zero orders and no measured rate. The saved direct
`gate.py --window 1` receipt declares a uniform Beta(1,1) prior, $0.38 per
attempt planning proxy and 0.1547238618 dossiers/USD next-best rate. It says
**STOP**: posterior mean 0.03846 and probability of beating the next action
0.19041, below 0.2. This is a source-family diagnosis, not a missed-control
hard stop. Actual model tokens and USD are unavailable. `spent_usd: 0` is a
parser artifact from `usd: null`, not measured spend.
