# Producer report: t2 NIRA sweep (producer claude-t2-producer)

Start UTC: 2026-10-29T14:13:24Z
End UTC: 2026-10-29T15:02:06Z (recorded immediately before this file was written)

Final applied directory: `applied-v2` (v1 was identical except the `agent` column, which the coordinator corrected from `claude-t2-producer` to `claude`, the packet's preparing agent; the producer identity is given here instead).

## Outcome per order

Submitted (20):
- EO:6258C, 6291, 6400, 6402, 6413, 6416, 6417, 6448, 6480, 6508, 6513F, 6885A: plain approvals; one clause each ended by S.J. Res. 113 section 2 (1935-06-14). 6416 keeps its Article VI review-right exception inside the approval; 6885A modifies the earlier approval to include the code as amended.
- EO:6274: denial of exemption; exhausted by performance 1933-09-07, repeal as later event.
- EO:6505: two clauses; approval ends at the repeal; condition (1) eliminating Section 4 of Article VIII exhausted 1933-12-15, repeal as later event.
- EO:6686: inventory corrected (item 6 report command; omitted final approval paragraph); both end at the repeal; the three-month report is a deadline, not an end.
- EO:6729: three clauses (approval, committee condition, report condition); each ends at the repeal; ninety days and December 1, 1934 are report deadlines, not ends.
- EO:6756D: inventory corrected to the one operative approval paragraph; ends at the repeal.
- EO:6828: approval with 14-day suspensive proviso; ends at the repeal; the 6861 and 6871 stays are described in the rationale but not claimed as later events (no evidence record in this dossier).
- EO:6861: inventory corrected to three commands. Paragraph 1 (stay) ended by express revocation in EO 6871 on 1934-10-12 (ACT:EO:6861>EO:6871@b1d44425e1c70307). Paragraph 2 (committee) exhausted 1934-10-10 (report date, per EO 6871 recital). Paragraph 3 (transmittal) exhausted by 1934-10-12 (interval 10-10 to 10-12 stated; the day is not shown).
- EO:6870A: inventory corrected to the revising order and the replacement condition (commission of four appointed by the Board); both end at the repeal. This is a judgment call: the appointment direction is treated as code-dependent because the Commission's only functions concern the code.

Blocked (4):
- EO:6242C: the denial is exhausted 1933-08-04 but the "except as affected by the stay" clause ended about 1933-12-11 (EO 6407, 6463, 6476, held APP and HathiTrust texts) and those orders are not evidence records in the packet; needs a re-prepared packet with those excerpts.
- EO:6450: stay "until 90 days after the effective date of this code"; the code's effective date is not held.
- EO:6606C: conditions 1 and 2 end 90 days after the code's effective date, which is not held.
- EO:6454: no text of the order is held anywhere (register and WPA listing only); override columns need a held original.

## What took the time (one line per order)

- 6242C: working out that the stay exception ends by held orders outside the packet; block.
- 6258C, 6291, 6400, 6402, 6413, 6416, 6417, 6448, 6480, 6508, 6513F: page check and earlier-end search only; 6417 also needed the parent automobile code's expiration-date chain (6513-K, 6837, 6895, 6955).
- 6274: applying the denial rule; checking for a reopening order.
- 6450: deciding the stay cannot be dated without the effective date; offsets for the split.
- 6454: confirming no text exists in any held directory.
- 6505: separating the exhausted elimination from the approval.
- 6606C: same effective-date gap as 6450 with two time-limited conditions.
- 6686: finding the omitted approval and the item 6 report command; computing override offsets.
- 6729: classifying the committee and report conditions.
- 6756D: override offsets; comparing later Distilled Spirits amendment orders.
- 6828: reading the 14-day proviso and the 6861/6871 stays.
- 6861: longest; per-command ends from EO 6871's recitals, override offsets for the three commands, and the ACT evidence id.
- 6870A: override offsets and the independent-command question for the appointments.
- 6885A: page check only; one other held order (EO 6312) is the earlier approval.

## Batch-check counts (applied-v2, same as v1)

packet_members 24; blocked 4; assembled_proposal 20; claims_checked 20; strict_claim_pass 20; strict_claim_fail 0; actionable_failures none; actual checker: all 20 checks passed, gate passed 20, mechanical pass 20, unverified 0, fail 0. No "changed Valla review context" refusal occurred. Apply took about 232 seconds.

## Tool defects

- `kit.py view --order` for the batch exceeded the 120 s tool timeout (moved to background; completed).
- Dossier text references use `@eo:ref` indirection, which broke a quick script until resolved.
- My own check for quoted text in the rationale found no issue in the final sheets after the quote at 6828 was fixed; the checker does not report quotes that are not in registered texts beyond what the actual checker reads.
- No defect in apply or batch-check.

## Where the shared analysis did not fit

- Orders with periods measured from an unstated code effective date (6450, 6606C) are own-terms ends the analysis does not cover; they cannot be dated from held evidence, so blocked rather than given the repeal date.
- 6242C: the analysis correctly says the exception is a separate clause with its own end, but the evidence for that end is not in the packet.
- 6861 and 6870A: independent commands to the Board (committee, appointments) needed per-command treatment. For 6861 they were ended by performance shown in EO 6871; for 6870A the appointment direction was kept code-dependent.
- 6686 and 6756D: machine inventories were wrong (findings listed as clauses; approval omitted).
- Not in the analysis: a line showing the ends of denial clauses use end_id ORIGINAL:EO:N with an exhausted-by-performance mechanism string chosen by me (batch-check accepted it).

## Tool calls

About 100 in total across both phases (approximate; the earlier phase before compaction was about 70).
