# Sinclair lean review, attempt 2 (2026-10-22)

Independent AI lean review of AI status hypotheses; not adopted; not a finding; not a certification. Certified whole-lifecycle count stays 0.

## Counts

- 41 Sinclair proposals reviewed by four reviewers (Q1-Q4): 39 genuine plus 2 planted controls.
- Genuine, 39: 37 uphold, 2 reject, 0 needs_research, 0 no verdict returned.
- Review complete: yes.

## Planted controls

- Two planted errors (EO:12314, a wrong-date type; EO:10610, a D10 wrong-ending-actor type). Both were rejected by their reviewers with a locus naming the planted field and value: 2 of 2 strict, 2 of 2 lenient.
- Both reviewers also marked the order as a suspected plant. The EO:12314 reviewer noted the error was visible by comparison with the rest of the set, so this is a necessary check, not proof of general sensitivity.
- Attempt 1 also caught 2 of 2, but only the two plants were reviewed and a timestamp tell was present (removed for attempt 2), so it is not counted.

## Rejected genuine orders

- EO:9762 (reviewer Q2): No express whole-order ending; displacement reading contradicted by the 9809 para. 12 / 9841 sec. 404 continuation clauses
- EO:12488 (reviewer Q4): Ending instrument does not name the order (whole_via_parent), contrary to owner ruling 2026-10-21 unnamed-instruments option C and checklist Q2

## Needs research

- None.

## Missing verdicts

- None; every genuine order received a verdict.

## Upheld with non-fatal defects noted

Upheld because the NO and its cited basis hold against the held text; the reviewers listed non-fatal defects (for example, a decision describing a 1989 snapshot row as empty when it says the order was revoked or terminated):

EO:7980, EO:8051, EO:8706, EO:8714, EO:8751, EO:9301, EO:9380, EO:9593, EO:10656, EO:10704, EO:11098, EO:11105, EO:11261, EO:11796, EO:11943, EO:11979, EO:12240, EO:12573, EO:12785, EO:13371, EO:13422, EO:13555, EO:13572, EO:13824

## Re-review queue

4 orders: the 2 planted orders (genuine proposals, to be re-reviewed), the rejected orders and any needs_research or missing.

- EO:12314
- EO:10610
- EO:9762
- EO:12488

## Adoption rows

ADOPTION_ROWS.csv prepares rows for the 15 Bowditch orders (all upheld) plus the 37 Sinclair orders upheld here, for the owner to merge by pull request per ruling 5. The reconciled CSV itself was not edited. These stay provisional AI status hypotheses.


## Pending-adoption cleanup addendum (2026-10-22)

The review findings above remain the historical attempt-2 record. This addendum changes the pending proposal set, not those verdicts. PR51 at `e07f115f12a007171cf3b554680242ce57178beb` had added 52 proposed rows to the reconciled CSV; the earlier sentence saying that CSV was not edited described preparation of this report and no longer describes the PR patch.

Six proposals are now held out of pending adoption: **EO:11261, EO:11943, EO:11979, EO:12240, EO:12573, and EO:13371**. PR51 disclosed inconsistent treatment of these parent-based endings and EO:12488 under the review-cited `2026-10-21-unnamed-instruments` option C. The six historical uphold verdicts and all underlying review evidence remain unchanged. Their exact removed proposal records, review pointers, naming caveats, reasons, and source/ruling references are preserved in [HELD_PROPOSALS.json](HELD_PROPOSALS.json). This is a procedural hold pending resolution through the existing owner/review process, not a new legal determination.

`ADOPTION_ROWS.csv` and the PR's appended reconciled rows now contain **46 pending proposals: 15 Bowditch and 31 Sinclair**. Only the six newly proposed rows were removed; every pre-existing reconciled row and every retained proposal remains byte-for-byte unchanged and in its original order. No proposal was merged or adopted by this cleanup. Historical prospective wording about adoption in retained rows remains unchanged and does not establish adoption. Certified whole-lifecycle count stays **0**; codebook, source evidence, `LEAN_REVIEW.json`, `PLANT_SCORE.json`, and earlier review attempts remain unchanged.
