# Jacquard L1R correction (D-20261110-ulpian-l1r-correction)

The owner answered A-20261110-ulpian-l1r-correction in the Ulpian session on 2026-11-10 with "Yes, read them"
(`research/readiness/owner_rulings/2026-11-10-ulpian-l1r-correction.md`).

**What was read.** Some provisional NO statuses adopted in PR 119 rested on the L1 card's "at least 14" premise, which
the owner declined in D-20261110-ulpian-no-floor. Every such status where that premise could matter is read again:
- 553 of the 582 wave-2 L1R statuses (527 dated on or after 1904-05-03, 26 with no exact date);
- the 3 undated wave-1 L1 rows (EO 940, 1596, 1604).

**The test.** A row is kept when its own held text quotes a fact that places the beneficiary's birth no later than
1904-05-02 (Ulpian RULE.md v2 section 2); otherwise it returns to undecided. The method is the one used for the 42
wave-1 rows (`research/ulpian/jacquard-l1-correction/`). The correction takes effect only when the owner merges this
pull request. Certified stays 0.

## Result

| | Orders |
|---|---:|
| Read | 556 (6 batches of at most 93, each with 3 planted controls) |
| **Kept** (quote verbatim, birth bound on or before 1904-05-02) | **70** (all wave 2) |
| **Returned to undecided** | **486** (483 wave 2, 3 wave 1) |
| Arms agreeing | 547 of 556 |
| Coordinator decisions (`COORDINATOR.jsonl`) | 13 (9 disagreements, plus 4 agreed returns given the uniform named-war reason) |
| Planted controls caught by both arms | 18 of 18 |

Reasons for the returns:

| Reason | Orders |
|---|---:|
| No dated fact | 391 |
| Fact too late | 47 |
| Fact about another person | 19 |
| Condition | 14 |
| Named war without a date (see below) | 8 |
| Not the order's own text | 3 |
| Second command | 2 |
| Several persons | 1 |
| Other | 1 |

The decided count goes from 4,274 to 3,788 on merge. The Jacquard wave-2 contract entry goes from 714 to 231 and the
wave-1 entry from 141 to 138, each with pins of its old rows file, the owner ruling and `CORRECTION.json`.

## Method

- **Packets.** `build_packets.py` shuffles the 556 rows with a fixed seed and splits them into six batches.
- **Controls.** Each batch gets three planted controls: a fact about another person, a fact dated too late, and a
  genuine pre-1904 fact.
  - Each control's base is an undecided one-person waiver from Ulpian tier 2 whose text contains no year before 1905,
    so the base text cannot already settle the question.
  - The control key stayed outside the worktree until every arm had finished.
- **Readers.** Two blind arms per batch read only `INSTRUCTIONS.md` and their packet: arm A was Claude Sonnet 5.5 and
  arm B Claude Fable 5.2. That is the same model family but different models.
- **Worker usage.**
  - Arm A: 718,682 tokens.
  - Arm B: 751,019 tokens.
  - Total: 1,469,701 tokens.
  - Batch 1 ran alone first; batches 2-6 ran after it checked out.
- **Adjudication** (`adjudicate.py`).
  - A KEEP counts only with a verbatim quote and a birth bound on or before 1904-05-02.
  - Both arms agreeing decides a row; the coordinator (Opus 5.5) recorded each disagreement in `COORDINATOR.jsonl`.
  - `--apply` removes the returned rows from the ledger and edits both contract entries in place.
  - It then validates the population with `jobs/claim-kit/population.py`; `population.py` itself is unchanged.
  - Tests that pass after the change: `jobs/claim-kit/test_population.py`, `test_status_continuity.py`,
    `jobs/case-bundles/test_build.py`, `jobs/clause-drafts/test_build.py`, `jobs/fr-originals/test_fr_originals.py`.

## Coordinator decisions

- **EO 478 (B1-14), KEEP.** "Employed almost continuously for seven years" ending no later than 1906: "almost"
  qualifies the continuity, not the years.
- **EO 189 (B1-74), KEEP.** The text dates the order September 4, 1902, so the named person was alive then.
- **EO 2611 (B2-45), KEEP.** 14 years' stated experience ending no later than 1917-05-07.
- **EO 2562 (B6-43), KEEP.** He is exempted from the diplomatic service's over-35 bar. EO 3499, in the approved lot,
  rests on the same bar.
- **EO 1848 (B2-23), RETURN.** "Known to the Secretary for 25 years" is not a fact kind in section 2.
- **Named-war rows, RETURN** (EO 437, 444, 453, 411, and 4 rows both arms returned):
  - Each text says the beneficiary served in the Civil War or the Spanish war, but states no date.
  - Such a person was certainly born before 1904, but the approved section 2 counts only facts whose date the text
    states ("only these").
  - So the 8 rows return uniformly, and ask A-20261110-ulpian-named-war asks whether named-war service should count.

## Files

| File | What it is |
|---|---|
| `PACKET_B1..B6.jsonl` | the six blind packets |
| `CONTROL_KEY.json` | which item is which order, and the planted controls |
| `INSTRUCTIONS.md` | what each arm was told |
| `ARM_A_B*.jsonl`, `ARM_B_B*.jsonl` | the two arms' answers |
| `COORDINATOR.jsonl` | the coordinator's decisions |
| `DECISIONS.csv` | one row per order: both arms, the final answer, quote, birth bound, reason, text path and SHA-256 |
| `ADJUDICATION.json` | counts, controls, pinned inputs |
| `CORRECTION.json` | the record the contract pins |
| `PROPOSED_STATUS_ROWS_W2.r1.csv`, `PROPOSED_STATUS_ROWS_W1.r2.csv` | the rows files without the returned rows |
