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

## Mend III (re-freeze, re-pin and propose)

- **Re-freeze:** all 9 orders were re-frozen against the current compiled generation. For 8 of them only the evidence pin changed (`evidence_sha256`), and the evidence differs only in the corpus-wide `OWN_TERMS` and `TEXT_REPRESENTATIONS` manifest hashes. No observation ids changed. EO 9294 carries the genuine decision, which cites EO 9625, not the planted 9652 version. EO 11796's rationale now covers D6: EO 12002 sec. 7 revokes EO 11798 but does not revive EO 11796.
- **Sign-off:** an independent reviewer (`claude-sinclair-mend-reviewer`) accepted 7 orders: EO 11209, 13555, 9294, 10704, 12573, 13975 and 12604. It accepted 2 with a defect:
  - EO 9762: the earlier defects carry over.
  - EO 11796: the rationale says no FR original of EO 12002 is held, but one is held at `jobs/fr-originals/data/full_run/texts/EO_12002.txt`. That text matches the quotes, so the conclusion is unaffected.
- **Proposals:** 9 NO proposals were written to `<NN>/overlay/EO_<n>/proposal-v1/` and appended to each batch's `PROPOSALS.jsonl`. Each has `owner_acceptance.accepted: false`. There were no refusals. On the first attempt `overlay-propose` returned `overlay_bundle_exists`, because the inputs were sitting in the destination folder. I moved the inputs to a scratch staging folder and proposed again into `proposal-v1`. `FREEZE_TELEMETRY.json` was copied back into each bundle.
- **Owner adoption total:** 56 (Bowditch 15 + Sinclair 41).
- **Guardrails:** nothing was adopted, nothing was written to `DECIDED_CASE_COMPLETENESS_RECONCILED.csv`, the codebook is unchanged, and the certified count stays 0. Nothing was committed or pushed.
