# Jacquard L1 correction (D-20261110-ulpian-jacquard-l1-correction)

The owner decided on 2026-11-10 (`research/readiness/owner_rulings/2026-11-10-ulpian-outer-bound.md`, part 3) that the
42 Jacquard L1 provisional NO statuses dated on or after 1904-05-03 are read again. They were adopted in PR 119 on the
L1 card's premise that "anyone the federal service could employ in 1917 or earlier was at least 14 years old", which
the owner declined the same day (D-20261110-ulpian-no-floor). A row is kept when its own held text quotes a fact that
places the beneficiary's birth no later than 1904-05-02 (Ulpian RULE.md v2 section 2); otherwise it returns to
undecided. Takes effect only when the owner merges this pull request. Certified stays 0.

## Result

| | Orders |
|---|---:|
| Read | 42 |
| **Kept** (both arms; quote verified verbatim, birth bound on or before 1904-05-02) | **9** |
| **Returned to undecided** | **33** (25 no dated fact, 4 fact too late, 4 fact about another person) |
| Arms agreeing | 42 of 42 (no coordinator decision needed) |
| Planted controls caught by both arms | 3 of 3 |

Kept: EO 1388, 1391, 1807, 1844, 1906, 1918, 2272, 2529, 2648. Their NO stays, now on the quoted fact in
`DECISIONS.csv` (latest possible death 2019-2026), not on the 14-year premise.

The provisional status ledger goes from 4,307 to 4,274 decided orders on merge.

## Method

- `build_packet.py`: the 42 rows plus three planted controls (a fact about a husband, a fact dated 1906, and a genuine
  1893 appointment), shuffled under neutral item ids with a fixed seed. The control key was kept outside the worktree
  until both arms had finished.
- Two independent blind arms, each given only `INSTRUCTIONS.md` and `PACKET.jsonl`: arm A Claude Sonnet 5.5 (95,853
  tokens, 40 s), arm B Claude Fable 5.2 (100,437 tokens, 91 s). Same model family, different models; the coordinator
  (Opus 5.5) built the packet and read every KEEP quote and RETURN reason.
- `adjudicate.py`:
  - A KEEP counts only if its quote is verbatim in the text and its birth date is on or before 1904-05-02.
  - Both arms agreeing decides a row; any disagreement needs a coordinator record in `COORDINATOR.jsonl`. There
    were none.
  - With `--apply` it writes the correction:
    - the returned rows' lines leave `research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv`;
    - `PROPOSED_STATUS_ROWS.r1.csv` is the wave-1 rows file without them;
    - the Jacquard wave-1 entry of `jobs/claim-kit/population_contract.json` gets count 141, the new rows pin, and
      pins of the old rows file, the owner ruling and `CORRECTION.json`;
    - then `jobs/claim-kit/population.py` validates the population.
  - This follows the reversal pattern of Respondendi's `reverse`; `population.py` is unchanged.

## Files

`PACKET.jsonl`, `CONTROL_KEY.json`, `INSTRUCTIONS.md`, `ARM_A.jsonl`, `ARM_B.jsonl`, `DECISIONS.csv` (one row per order:
both arms, final, quote, birth bound, reason, text path and SHA-256), `ADJUDICATION.json` (counts, controls, pinned
inputs), `CORRECTION.json` (the record the contract pins), `PROPOSED_STATUS_ROWS.r1.csv`.

## Not covered here

- **Wave 2 (L1R) also rested on the same card.** 582 L1R statuses were adopted in PR 119 under the same L1 card; 527
  are dated on or after 1904-05-03 and 26 have no exact date. The 3 undated wave-1 L1 rows (EO 940, 1596, 1604) are
  in the same position. The decision named only the 42, so these are a separate owner ask:
  A-20261110-ulpian-l1r-correction.
- The returned orders are not decided "yes": they are undecided again, and Pothier/Ulpian tier 2 lists their required
  ages for any later reading.
