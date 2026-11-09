# Bentham checkpoint after m009

The accepted 50-order batch has no authenticated original-text passes, 47
failures, one unsure and two blocked. Both blind readers rejected all three
planted controls. Their separate EO:3083 provenance follow-ups independently
changed the provisional pass to unsure. No output was quarantined.

The direct Federal Register witnesses mostly fail because the held OCR spans
the entire issue page or neighboring orders, not an isolated complete order.
The government-report volumes reprint or abstract orders without proof of the
official original; EO:3083's scanned circular lacks an issuing imprint. The
exact 1911 Isthmian GPO scan for EO:273 and EO:274 remains missing. The lane's
authentication yield is low because of source/held-text quality, not reviewer
control failure. The next worklist uses three grouped annual-report scans to
resolve the still-open low-grade leads with exact page-level fail/unsure or
blocked reasons. It does not treat those leads as original-printing passes.

The required native `bentham.py gate --action
acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK --batches
research/montfaucon/BATCHES.jsonl` refuses this action before reading the
ledger: the action is absent from the current ranked production plan. The
saved direct `gate.py --window 1` receipt declares a uniform Beta(1,1) prior,
$0.38 per attempt planning proxy and 0.1547238618 dossiers/USD next-best
rate. It says **STOP**: posterior mean 0.01923 and probability of beating
the next action 0.04549, below 0.2. This is a source-family diagnosis, not
the missed-control hard stop. Actual model tokens and USD are unavailable;
`spent_usd: 0` is the gate parser's treatment of `usd: null`, not measured
spend.
