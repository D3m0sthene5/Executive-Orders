# Y1 recheck with calibrated reviewer (2026-10-20)

I re-reviewed all 15 Y1 NO proposals against the held source texts and tried to refute each one, with an explicit D6 step: was any later event that ended or changed the clause removed or ignored? None was rejected. Three were upheld with a defect that does not change the NO. Nothing was adopted or committed, and the certified count stays 0.

**Verdict rule.** A proposal is rejected if the NO, or the basis it cites, fails against the held text: a misquote, the wrong instrument, a savings clause that still operates, a part of the order left in force, or a revival. A D6 miss or a record error that leaves the NO standing is upheld and listed as a defect.

All source paths are under `jobs/fr-originals/data/full_run/texts/`.

| EO | Verdict | Reason / defect | Source checked |
|---|---|---|---|
| 11417 | upheld | EO 12163 sec. 1-903(a)(1) revokes EO 10973 "as amended". Sec. 1-505 sets up a new Development Loan Committee, which replaces the inserted clause. The producer did not cite 1-505; it strengthens the NO. | EO_11417, EO_12163 |
| 11532 | upheld | EO 11981 sec. 5 supersedes the whole order, with no savings clause. | EO_11532, EO_11981 |
| 12291 | upheld | EO 12866 sec. 11 revokes it with no conditions. The "terminate" event for EO 12482 is a mis-match: it ends a committee, not EO 12291. | EO_12291, EO_12866, EO_12482 |
| 12686 | upheld | EO 12774 sec. 3(b) revokes it by number, effective Sept. 30, 1991. | EO_12686, EO_12774 |
| 13137 | upheld | EO 13316 sec. 3(b) names it. | EO_13137, EO_13316 |
| 14228 | upheld, with defect | **D6 miss by the producer:** EO 14357 cut the 20% rate to 10% from Nov. 10, 2025, the probable first end. The original reviewer caught it. EO 14389 still ends whatever remained, and no later held order brings the rate back. | EO_14228, EO_14389, EO_14357, EO_14388, EO_14256, EO_14324 |
| 9811 | upheld, with defect | **Record error:** the producer says "EO 10250 is not held", but it is held. Sec. 1(e) only hands the extension power to Interior. The NO rests on the order's own 25-year term running out, which can be argued. | EO_9811, EO_10250 |
| 10085 | upheld | EO 10903 sec. 5(a) item 3 revokes it by name. Sec. 5(b) keeps only rules and actions taken under it. | EO_10085, EO_10903 |
| 11841 | upheld | Its parent order is revoked "as amended", and EO 12163 sec. 1-506 replaces the committee it created. | EO_11841, EO_12163 |
| 12759 | upheld | EO 13123 sec. 604 revokes it with no exceptions, which ends secs. 3, 9 and 10 that EO 12902 had kept. | EO_12759, EO_12902, EO_13123 |
| 13018 | upheld | EO 13316 sec. 3(b) names it. EO 13137 had already rewritten the clause it changed. | EO_13018, EO_13137, EO_13316 |
| 8226 | upheld | EO 8384 sec. 21 supersedes it by number. | EO_8226, EO_8384 |
| 9067 | upheld, with defect | EO 9243 para. 3 revokes it by name. **Minor overstatement by the producer:** EO 9994 keeps some reemployment rights alive past the 1948 expiry, but none can still operate in 2026. EO 9695 does not revive the order. | EO_9067, EO_9243, EO_9695, EO_9994, EO_9952 |
| 9204 | upheld | EO 9649 ends the Office and the Coordinator, and every provision of EO 9204 runs through them. It is not named as revoked, which the producer said openly. | EO_9204, EO_9649 |
| 9982 | upheld | EO 10011 para. 3(b) revokes it by name, and its own term ended June 30, 1949. | EO_9982, EO_10011 |

**Survivors:** 15/15. If every defect counted as a rejection, 12/15 would survive (all except 14228, 9811 and 9067).

**What changed from the original 0/15:**
- The headline is the same: no rejections.
- This pass was calibrated (Opus with held sources plus a D6 step) and it found three defects the original pass did not flag:
  - It confirmed the EO 14357 miss in 14228. The original reviewer had caught it but still recorded 0 disagreements.
  - It found the false "EO 10250 is not held" statement in 9811.
  - It found the overstated EO 9994 claim in 9067.
- In Mountweazel's MW-C2 trial, this reviewer setup still left room for up to about 0.27 of items being defective (0.49 at the low end of its catch rate). It was weakest on D6, catching only 0 to 1 of 3. I am the same model family as the producer, so this is not independent of it.

**Fit to put to the owner:** Yes, as provisional NO hypotheses for the owner to decide on, provided the 14228, 9811 and 9067 notes travel with them. 14228 and 9811 are the most open to challenge. This is not a certification.

**Llull:** Outcome O-20261020-4 resolves forecast L-20261020-14 at 1.0. The forecast's p90 was 1.0, so the planner was too pessimistic again. The ledger line was added but not committed.

**Files:**
- `/home/user/Executive-Orders/research/excavator/bowditch-2026-10-20/Y1_RECHECK_OPUS_SOURCES.json` (new, not committed)
- `/home/user/Executive-Orders/jobs/llull/ledger/outcomes.jsonl` (one line added)

This task had no cost cap, so "raise the cap to $1000" had nothing to apply to here.

SUMMARY: Opus with held sources and a D6 step upheld 15 of 15 Y1 NO proposals, 0 rejected. Three have defects that do not change the NO: 14228 missed EO 14357, 9811 wrongly says EO 10250 is not held, and 9067 overstates EO 9994. Counting defects as rejections leaves 12 of 15. Fit to put to the owner as hypotheses. Llull O-20261020-4 recorded at 1.0. Nothing adopted; certified count stays 0.
