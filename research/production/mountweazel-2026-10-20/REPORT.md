# Mountweazel: first reviewer calibration (2026-10-20)

**Design.** Mountweazel builds a practice batch that mixes real claims with "plants": copies of real claims, each carrying one documented defect, drawn from the real rejection types (D1–D13). Reviewers see an unmarked copy of each plant in `scratchpad/mountweazel/<batch>/batch/`. The sealed answer key (mode 0600, hash-sealed) sits beside it. Marked copies live only in `jobs/mountweazel/fixtures/`, carrying `SEEDED: true`, a `SEEDED:` id prefix and a `SEEDED-` schema, and the claim checker rejects them. `score` reports catch rate per defect type and pooled. A "strict" catch must name the specific changed value, actor or clause; a "lenient" catch is any reject. It also reports the false-alarm rate as lower and upper bounds, with Wilson and Clopper-Pearson 95% intervals. `check` scans the whole repo for leaks.

**Trial MW-C1** (20 items, 6 plants; reviewer from the same model family as the producer, reading the batch only):

| Defect type | Plants | Caught (strict) | 95% interval |
|---|---|---|---|
| D4 partial end applied to another clause | 1 | 1 (MW-C1-04) | 0.03–1.0 |
| D5 missed earlier end | 2 | 2 (07, 15) | 0.16–1.0 |
| D3 quote cut before the verb | 1 | 0 (09) | 0–0.98 |
| D6 later event removed | 1 | 0 (16) | 0–0.98 |
| D9 coverage count inflated | 1 | 0 (01) | 0–0.98 |
| **Pooled** | 6 | **3/6** | Wilson 0.19–0.81, Clopper-Pearson 0.12–0.88 |

- **Plants with no seeding artifact:** 0/3 caught (Wilson 0–0.56).
- **False alarms:** 0/14 real items flagged (Wilson 0–0.22).
- **Noticed but accepted:** on MW-C1-09 the reviewer named the missing "revoked" but accepted it as OCR truncation. One real item has a similar naturally cut quote.
- **Relabel:** I scored MW-C1-07 as D5 rather than its keyed D2. The clause is an annual report, so it was never a one-time duty.

**Adversarial review: what I found and fixed**
- **Seeding artifact (major):** the tool rewrote every mention of the old date and actor in the rationale. That changed sentences about other clauses, so the packet contradicted itself. All 3 caught plants had this contradiction, and the reviewer used it as supporting evidence. New plants are now skipped when the old end is shared with another clause or event.
- **Wrong D2 classification:** "annual report" was treated as a one-time duty. Recurring duties are now excluded.
- **D9 not checkable in the packet:** the check that the true count still appears elsewhere was matching "49 Stat.". It now needs the same count and unit.
  - That leaves D9 with 0 plantable bases, and D2 also has 0.
  - What remains: D3 51, D6 36, D7 11, D5 7, D8 5, D4 1.
- **Strict scoring credited bare field names** like `first_end`. It now needs a specific value, actor, clause path or the cut-off word.
- **`check` false positives (the 24 problems):** a D3 plant's quote is a prefix of the real EO 12076 text. `check` now only searches for plant text that does not appear in the real item.
- **`check` coverage:** it now scans the whole repo, not just `output/` and `data/` folders. It also catches an unmarked exact copy of a plant, which it missed before.
- **Added to `score`:** `--relabel`, `--tells`, `--production k/n`, a noticed-but-accepted list, and `verdict` accepted as an alias for `decision`.
- **Stats:** the interval maths is correct, and I added tests for it.
- **Still open:**
  - The key sits beside the batch, so blinding relies on the reviewer's instructions.
  - Plants differ from claims already in the repo, so a reviewer with repo access could find them by comparison.

**What this means for Bowditch Y1's 0/15 and past reviews.** 0/15 flags means the true flag rate is at most 0.22. With a catch rate of 0.5, the defect rate is at most 0.44. At the catch rate's lower bound, or using artifact-free plants, the bound is 1.0, so 0/15 tells us nothing. Past same-family reviews caught gross, self-contradicting errors but missed subtle ones: an omitted event, an overstated count, a cut-off quote. A clean review should not raise confidence in any status hypothesis. Certified stays 0.

**Limits.**
- n is tiny: 6 plants, one reviewer, one prompt.
- Difficulty and the artifact are confounded: the artifact-free plants were also the subtler types.
- The trial was Track C (claims), but Bowditch is Track S (status proposals), so the result only transfers as a rough order of magnitude.
- The Track S practice packets don't include source texts yet.

**Next steps.**
1. Seed MW-C2 with the fixed operators, about 40 items, excluding MW-C1's orders.
2. Run a no-access test first: can a model that can't see sources spot the plants from wording alone?
3. Use a reviewer from a different model family, or a human, and compare.
4. Build Track S packets with source texts, then re-test Bowditch-style review.
5. Write operators for D11 and D12, and a D9 that can be checked inside the packet.

**Results.** Final `check` over the whole repo: ok, 0 problems, 74,430 files. Tests: 29/29 pass. Changed files:
- `/home/user/Executive-Orders/jobs/mountweazel/mountweazel.py`
- `/home/user/Executive-Orders/jobs/mountweazel/test_mountweazel.py`
- `/home/user/Executive-Orders/jobs/mountweazel/README.md`
- `/home/user/Executive-Orders/research/plans/MOUNTWEAZEL_DESIGN.md` (new §8)

An auto "WIP snapshot" commit in the orchestrator's name already includes my `mountweazel.py` edits; I made no commits myself. Scores are in `/tmp/claude-0/-home-user-Executive-Orders/dc388148-b92d-5956-9825-90ce34a3dac7/scratchpad/mountweazel/trial/MW-C1/score_v2.json`.

SUMMARY: Mountweazel trial MW-C1: the same-family reviewer caught 3/6 planted defects (Wilson 0.19–0.81) with 0/14 false alarms (≤0.22). All three catches had a seeding artifact (the rationale rewrite made each packet contradict itself); all three artifact-free plants were missed (0/3). I fixed the artifact, a wrong D2 classification, D9 not being checkable in the packet, loose strict scoring, and `check`'s 24 false positives; `check` now passes over the whole repo and 29 tests pass. Bowditch's 0/15 bounds defect prevalence at ≤0.44 at best and ≤1.0 at worst, so it says almost nothing. Next: MW-C2, a no-access test, a reviewer from a different model family, Track S packets with source texts.
