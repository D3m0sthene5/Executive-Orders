### Sinclair re-freeze (2026-10-20)

I reviewed the re-frozen proposals for batches 01-05 against the held source texts, including the D6 step. 26 of the 29 are now valid proposals; the other 3 can't be proposed until their decision files are corrected. All are NO hypotheses with `owner_acceptance.accepted: false`.

**The decisions are unchanged.** For each of the 29, I set the evidence pin back to its old value, re-hashed the decision, and got the same `decision_sha256` that the earlier accepted review recorded. So the only change in the decision file is the evidence pin, and every blank review sheet matches its current decision.

**Every decision is still upheld.** I re-read each order's history, its held original and the held text of each ending instrument, and searched the held corpus for later instruments that name the order. I accepted all 26 that can be proposed. None of them changed decision. Four are "accept, with defect"; in each the NO status still stands:
- **EO 9593:** EO 9603 orders the property returned "as soon as practicable". It gives no end date and amends rather than revokes.
- **EO 7980:** the cited end-date record comes from the American Presidency Project transcription. The official Federal Register text has the same wording.
- **EO 8051:** the cited record is the conditional "cease on termination of the 1935 agreement" clause. The order actually stops operating because its only command covers January to June 1939.
- **EO 11261:** the savings clause in EO 12163 (sec. 1-904) is read as subordinate to its express revocation of EO 10973. The reading is noted as an open point.

**Valid proposals per batch** (re-reviewed = upheld in the first run; written = proposals now in `<NN>/PROPOSALS.jsonl`):

| Batch | Re-reviewed | Written | Held back |
|---|---|---|---|
| 01 | 4 | 4 | 0 |
| 02 | 6 | 3 (EO 12785, 13371, 7980) | 3 |
| 03 | 4 | 4 | 0 |
| 04 | 7 | 7 | 0 |
| 05 | 8 | 8 | 0 |
| **01-05** | **29** | **26** | **3** |
| 06 (written earlier) | – | 6 | – |

**The 3 held-back orders (batch 02: EO 11209, 13555, 9294):** on substance I would uphold all three. Their own records hold, and nothing later revives them:
- EO 11386 sec. 9(b) revokes EO 11209.
- EO 13935 sec. 4(a) supersedes EO 13555.
- EO 9625 revokes EO 9294.

`overlay-propose` still rejects them with `all_history_observations_must_be_reviewed`, because `observations_reviewed` lists extra supporting `API:` ids. Fixing that is a producer edit to the decision. That changes its hash, so each would then need a new blank sheet and a quick sign-off. I left their sheets blank.

**Adoption batch for the owner:** Bowditch 15 + Sinclair 32 (26 here + 6 from batch 06) = **47** NO proposals. It becomes 50 if the 3 batch-02 orders are fixed and signed off. The 6 orders whose reviews were lost to the planted defects are still waiting for re-review.

**Guardrails:** I did not write `DECIDED_CASE_COMPLETENESS_RECONCILED.csv`, `_staging/` is gone, and the certified count stays 0. I recorded no Llull outcome, because no forecast was registered for this re-review. I committed nothing.

**Files:**
- Proposals: `research/excavator/sinclair-2026-10-20/{01..05}/PROPOSALS.jsonl`, with the full proposal folders under `research/excavator/sinclair-2026-10-20/<NN>/overlay/EO_N/proposal-v1/`.
- Filled review sheets (reviewer `claude-sinclair-refreeze-reviewer`): `/tmp/claude-0/-home-user-Executive-Orders/dc388148-b92d-5956-9825-90ce34a3dac7/scratchpad/sinclair/refreeze/<NN>/EO_N/STATUS_REVIEW.json`

SUMMARY: All 29 re-frozen decisions are byte-identical to the reviewed versions apart from the evidence pin. My independent review upheld all of them, with 4 minor defects that leave the status standing and no changed decisions. 26 are written as proposals (01:4, 02:3, 03:4, 04:7, 05:8). EO 11209, 13555 and 9294 need a producer fix first. Owner adoption batch: Bowditch 15 + Sinclair 32 = 47 NO hypotheses.
