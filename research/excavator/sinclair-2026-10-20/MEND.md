# Sinclair mend (SINCM)

Date: 2026-10-20. Pool: 9 SINCLAIRS orders (jobs/llull/ledger/pool_ids/SINCM.txt).

**Attempt 1:** blocked. No packet was written, so nothing was reviewed or measured.

**Attempt 2 (mend-2):** the producer, planter (in scratch only), independent Opus review with the D6 step, and tally all ran.
- **Plants:** 2 of 2 caught. EO 9294 (revoking order changed from 9625 to 9652) and EO 11796 (ending order changed from 11798 to 11797) were both rejected on the planted point. The plant gate passed.
- **Review:** 6 accepted (EO 11209, 13555, 10704, 12573, 13975, 12604), 1 accepted with defect (EO 9762: sec. 204 of EO 9841 takes effect May 4, 1947, and the para. 12 clause of EO 9809 is not addressed). The 2 planted orders were rejected. On the genuine decisions, NO holds for all 9.
- **Proposals:** 0 written. `overlay-propose` refused all 8 candidates with `claim-kit: stale_compiled_generation`. The evidence was frozen at 13:51Z. Results commit 91116f879 (14:25Z) then changed the `OWN_TERMS` and `TEXT_REPRESENTATIONS` shards of the claim-kit output. The decision and review checks pass. EO 11796 was not a candidate, because the reviewer also flagged a D6 omission: the decision does not address EO 12002's 1977 revocation of EO 11798.
- **Next:** re-freeze the 8 candidates against the current generation. Then re-pin their decisions, get a quick independent sign-off, and propose. Fix the EO 11796 rationale on D6 first.
- **Llull:** L-20261020-59 = 1.0 (plant-catch share). L-20261020-60 = 0.0 (proposals per attempt). Source: `mend/OUTCOME.json`.
- **Guardrails:** nothing was adopted, the codebook is unchanged, nothing was written to `DECIDED_CASE_COMPLETENESS_RECONCILED.csv`, and the certified count stays 0. Owner adoption total stays 47.
