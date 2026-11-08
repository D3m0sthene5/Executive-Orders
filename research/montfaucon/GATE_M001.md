# Bentham checkpoint after m001

The native `bentham.py gate --action
acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK` exits with “not a ranked production
action” because the current `jobs/bentham/output/PLAN.json` entry has
`orders: 0` and no measured `rate`, despite listing the page-check action and
its $0.38 per-attempt planning proxy. The direct `jobs/bentham/gate.py` run is
saved in `GATE_M001.json`.

For 50 accepted attempts and 34 validated passes, the direct gate returns
**CONTINUE** under a uniform Beta(1,1) prior, the plan proxy $0.38/order and
the next ranked action's 0.1547 value/USD. This is a conditional planning
result. Actual batch spend and model-level token counts are unavailable; the
gate's `spent_usd: 0` is its treatment of an unknown cell, not a measured
cost. The three cheap-tier control misses occurred in quarantined attempts;
the lane was stopped, fixed, rechecked by stronger independent readers, and
only the accepted 50-order batch enters the yield gate. The incident and
remediation are in `CONTROL_INCIDENT.md`.
