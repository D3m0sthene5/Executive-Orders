# Mountweazel: first reviewer calibration (2026-10-20)

**Design.** Mountweazel builds a practice batch that mixes real claims with "plants": copies of real claims, each carrying one documented defect, drawn from the real rejection types (D1–D13). Reviewers see an unmarked copy of each plant in `scratchpad/mountweazel/<batch>/batch/`. The sealed answer key (mode 0600, hash-sealed) sits beside it. Marked copies live only in `jobs/mountweazel/fixtures/`, carrying the seeded flag, id prefix and schema described in the design document, and the claim checker rejects them. `score` reports catch rate per defect type and pooled. A "strict" catch must name the specific changed value, actor or clause; a "lenient" catch is any reject. It also reports the false-alarm rate as lower and upper bounds, with Wilson and Clopper-Pearson 95% intervals. `check` scans the whole repo for leaks.

**Trial MW-C1** (20 items, 6 plants; reviewer from the same model family as the producer, reading the batch only):

| Defect type | Plants | Caught (strict) | 95% interval |
|---|---|---|---|
| D4 partial end applied to another clause | 1 | 1 (item 04) | 0.03–1.0 |
| D5 missed earlier end | 2 | 2 (07, 15) | 0.16–1.0 |
| D3 quote cut before the verb | 1 | 0 (09) | 0–0.98 |
| D6 later event removed | 1 | 0 (16) | 0–0.98 |
| D9 coverage count inflated | 1 | 0 (01) | 0–0.98 |
| **Pooled** | 6 | **3/6** | Wilson 0.19–0.81, Clopper-Pearson 0.12–0.88 |

- **Plants with no seeding artifact:** 0/3 caught (Wilson 0–0.56).
- **False alarms:** 0/14 real items flagged (Wilson 0–0.22).
- **Noticed but accepted:** on item 09 the reviewer named the missing "revoked" but accepted it as OCR truncation. One real item has a similar naturally cut quote.
- **Relabel:** I scored item 07 as D5 rather than its keyed D2. The clause is an annual report, so it was never a one-time duty.

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

## MW-C2: reviewer configurations (2026-10-20)

**Batch.** 40 items, 10 plants (25%): D3 x2, D4 x1, D6 x3, D7 x2, D8 x2. No D5 plant, so no D5 coverage; D4 has n=1. The orders used in MW-C1 were excluded. The key was sealed and kept outside the batch folder. Llull forecast L-20261020-13 (pooled strict catch: p10 0.03, p50 0.30, p90 0.60) was registered before any review. Every reviewer used the MW-C1 blinding rules. Item-level scores stay in the session scratchpad. Aggregates are in `MW-C2_SCORES.json` next to this report, with no item ids and no plant text.

| Config | Strict catch (Wilson / C-P 95%) | Lenient | Flags on 30 real (false-alarm bounds) | Tokens processed (uncached in+out) |
|---|---|---|---|---|
| Opus, packet only, no sources | **9/10** (0.60–0.98 / 0.56–1.0) | 9/10 | 1 (0 to 0.03; Wilson upper 0.17) | 5.4M (0.26M) |
| Opus + held source texts | **8/10** (0.49–0.94 / 0.44–0.97); 7/10 after my reading (0.40–0.89) | 8/10 | 2 (0 to 0.07; Wilson upper 0.21) | 11.2M (0.26M) |
| Sonnet + held source texts | **6/10** (0.31–0.83 / 0.26–0.88) | 7/10 | 0 (0; Wilson upper 0.11) | 10.1M (0.19M) |
| Union: Opus-sources or Sonnet-sources reject | **8/10** (0.49–0.94) | 9/10 | 2 (0 to 0.07) | 21.3M (0.45M) |

Token counts are summed from the reviewer transcripts. Output tokens are under-logged there, so compare on tokens processed.

**By defect type.**
- **Caught by every config:**
  - D3, the quote cut before "revoked": 2/2.
  - D4: 1/1.
  - D8, the neighbouring order's text: 2/2.
- **D7, a date replaced by another date the text states:**
  - Both Opus configs: 2/2.
  - Sonnet: 1/2.
- **D6, a later event removed that the packet still names, was the weak spot:**
  - Opus packet-only: 2/3.
  - Opus-sources: 1/3, and 0/3 after my reading.
  - Sonnet: 0/3 strict, 1/3 lenient. Its one reject cited a cut-off clause text, not the missing event.
  - One D6 plant was accepted by all three reviewers.

**Scoring adjustment.**
- I scored one Opus-sources D6 credit as right verdict, wrong reason. It matched the right order number, but the reason flagged a cut quote in a different clause; the removed event was not named.
- `score` counted it as strict. Its term matching is still too loose for D6, because it accepts the order number alone.

**Flags on real items.** None has been adjudicated, so I counted none as a false alarm.
- **Opus-sources flagged two upheld claims.** In each, a quote stops mid-phrase although the operative verb is still present. One of them leaves out the insertion that the claim's mechanism relies on. These may be real minor defects in upheld claims. A human should look at them before calling them false alarms.
- **Opus packet-only flagged one other item** for a dropped trailing word.

**Sources added no catches.**
- Packet-only Opus did as well as Opus with sources, at half the tokens.
- That is a property of these operators, not evidence that sources are unnecessary. D3, D6, D7 and D8 are all built so the refuting evidence sits inside the packet: the original quote, the event named elsewhere, the clause's own date, the original representation.
- The packet-only run therefore measured internal-consistency checking. It is not the planned no-access wording test.
- The only defects that needed sources were the two possible real truncations, and only the sources configs found them.

**Union.**
- Adding Sonnet to Opus-sources added one lenient catch and no strict catch.
- It found nothing new on real items and nearly doubled the cost.
- Not worth it.

**Which config to use for future claim and status reviews:**
- Use **Opus with the held source texts**, as one reviewer.
- It had the highest strict catch of the source-reading configs, and only a source-reading reviewer can catch defects that are absent from the packet. The truncations above are an example, and so is any status hypothesis whose evidence lives in held texts.
- Sonnet costs about the same in tokens processed and caught 2 fewer plants, so it is not the cheap option it might seem.
- **Add a D6 step to the reviewer prompt:** list every later event named anywhere in the packet, then confirm that each clause's `later_events` either includes it or says why not.
- **Re-measure on the next batch.** D6, an omitted event, is closest to the main Bowditch failure (a missed revocation or amendment), and it is where every config was weakest.

**Llull.** Forecast L-20261020-13 is resolved by outcome O-20261020-3 at **0.8**, the Opus-sources config.
- That config is the production-like one, and it was the median of the three.
- The other configs scored 0.9, 0.6 and 0.8 (union). Every one is at or above the forecast's p90 of 0.60, so the planner was too pessimistic.
- The p50 of 0.30 rested on MW-C1's 0/3 for artifact-free plants. That result does not carry over: these plants are artifact-free and still checkable inside the packet.

**What this means for Bowditch Y1's 0/15.**

`score --production 0/15` gives these upper 95% bounds on defect prevalence:

| Config | At the point catch rate | At the catch rate's lower bound |
|---|---|---|
| Opus-sources | 0.27 | 0.49 |
| Opus packet-only | 0.24 | 0.39 |
| Sonnet | 0.36 | 0.83 |

This is better than MW-C1, where the bound ran up to 1.0. Even so, it still does not support Bowditch Y1, for three reasons:
- **Different track.** Bowditch is Track S (status proposals), and its packets lack source texts.
- **D6 catch is low.** Its missed-event defect resembles D6, and the D6 catch rate is 0–2 of 3.
- **The planted mix is easy.** It is dominated by defects visible inside the packet.

A 0/15 review is consistent with up to about a quarter to a half of the proposals being defective. It certifies nothing, and certified stays 0. The next steps are unchanged:
- Track S packets with source texts.
- A D6-focused batch with n≥10.
- A D5 operator with real coverage.
- A reviewer from a different model family, or a human.

**`check` (final run).** 11 problems, down from 13.
- **Two cleared.** The two hits on this report (an MW-C1 batch id and a marker string) are gone; I reworded both.
- **The other 11 are D8 false positives.** They come from the two D8 plants. I confirmed the following:
  - The matched text is the real wording of the donor order, inside that order's own upheld claim in `research/readiness/claims/claude-2026-10-19-x1-pilot.jsonl`, which was committed 2026-10-19, before seeding.
  - The same text appears in the claim-kit and excavator copies of that claim. None of those files changed.
- **The cause** is that `novel_needles` compares a plant only with its own base. For D8 it should also exclude text found in the donor order's real item.
- **A seeding issue in the same plants.** The two D8 plants are each other's donor, so the same swapped text appears twice in the batch.
- **Nothing planted was written** into readiness, FETCH_QUEUE, ledgers or job inputs. The Llull outcome row and `MW-C2_SCORES.json` hold aggregates only.
