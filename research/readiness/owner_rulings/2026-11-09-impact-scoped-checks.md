# Owner ruling, 2026-11-09: scope verification runs to what a change can affect

**Owner's words (session of 2026-11-09, PR superseding #185):** "that seems like a massive oversight. make sure kean
knows this needs a permanent fix for every future time this could come up. that only one fricking claim is even held
by mabillon and you run the whole thing"

## What happened

To measure a change to Mabillon held printings (which text files exist and their hashes) and to Lachmann (which
working text is confirmed), the session dispatched a full diagnostic chain that reruns `claim-checker` over all 1,828
claims and about 22,000 source references, about 50 minutes on a runner (3,021.6 s on 2026-11-09). Measured afterwards:

- **1 claim line** in the repository (`research/readiness/claims/claude-2026-10-28-spent-probe.jsonl:8`) cites any of
  the 45 source SHA-256s behind Mabillon's 2,015 fragments.
- The other effect, the staleness of working-text confirmations, is computed by the readiness tracker itself with the
  same function (`working_text.policy`, `tracker.py:558`), which takes about 30 seconds locally. It showed no changed
  field on any order.

## Ruling

The project needs a permanent, general fix, not one for Mabillon alone. Before any full rerun of an expensive
consumer (claim-checker first, then claim-kit, claim-drafts and others), determine which of its units (claims, orders,
dossiers) can be affected by what changed:

- a producer's fragments, texts or source hashes;
- Lachmann confirmations;
- rules or code.

Then rerun only those units, plus whatever the cheap whole-population step (the tracker) already recomputes. A
full rerun is used only when the change touches the consumer's own code or rules, or the affected set cannot be
determined. That case is stated, never assumed.

This applies to agent diagnostics and to scheduled runs. Soundness comes first: an impact selector that misses an
affected unit lets a stale result publish, which is worse than the wasted run. The selector therefore needs:

- a declared dependency map, checked against what the consumer actually reads (PR #242's read audit, Quo Warranto, is
  the existing base);
- planted controls: a change known to affect a given claim must select it;
- a periodic full run that reconciles against the selective results.

No status, census, codebook, claim or certified count (0) changes under this ruling.
