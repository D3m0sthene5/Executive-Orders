# Producer report, batch t4 (claude-t4-producer; agent column set to `claude` per coordinator correction)

Start 2026-10-29T14:33:07Z. End 2026-10-29T14:59:26Z. Final applied directory: `applied-v1` (first apply passed; no v2 needed). Approx. 55 tool calls.

## Outcome: 15 submitted, 9 blocked (24 orders)

Submitted (first end 1935-06-14, S.J. Res. 113 sec. 2, unless noted):
- 6270, 6315, 6351, 6418, 6513E, 6520: plain section 3 approvals.
- 6606D, 6620B, 6812, 6900, 7019: amendment/modification approvals; 6812 inventory corrected (machine listed five findings as clauses; one operative clause).
- 6296: denial of exemption; exhausted on 1933-09-18 (end_id ORIGINAL:EO:6296, mechanism exhausted_by_performance_on_issuance_one_time_determination), repeal recorded as later event.
- 6458: approval plus six conditions (administrator powers, stays pending report, exemption); each ends at repeal; no earlier end held.
- 6606B: inventory corrected to nine clauses (condition 1 split into deletion and Labor Board proviso; President's published statement split off condition 6); condition 6 stay of 90 days ends 1934-05-18 by own terms (counted from order date; extension "at discretion of Administrator" not held); others end at repeal.
- 6684D: inventory corrected to four clauses (approval, two stays pending further order, hearing-question understanding); none has a fixed own-terms end; all end at repeal.

Blocked:
- 6205C: section 4(a) interim agreement (outlier category); possible supersession by Silk Textile Code (EO 6330) not shown.
- 6414: only registered text is a Wayback-only APP capture (fails offline custody); otherwise a plain approval.
- 6532: condition limits separate approval to three months from an effective date not held; undatable own-terms end.
- 6606E: amends the EO 6533 approval, which carries the same undatable three-month limit.
- 6969: study direction to NRA Division of Research and Planning has no supportable end (EO 7075 terminated the Board only; EO 7252 transferred named divisions only).
- 6459, 6462, 6534, 6756G: no text held (WPA listing only).

## What took the time (one line each)
6205C: deciding it is 4(a) and reading EO 6330/6210. 6270: Motion Picture sibling check. 6296: finding the exhaustion mechanism vocabulary (none documented; free text accepted). 6315, 6513E, 6520: routine. 6351: retail sub-trade codes and EO 6467. 6414: custody (searched all FRAGMENTS for another representation). 6418: EO 6647-B cross-reference. 6458: per-condition reasons. 6459/6462/6534/6756G: confirming no text anywhere in the repo. 6532 and 6606E: searching for the code text or effective date. 6606B: offsets and clause split, 90-day count. 6606D: later chapter orders. 6620B: EO 6723 service-trade suspension check. 6684D: splitting four commands. 6812: inventory correction. 6900, 7019: listing sibling amendment orders. 6969: reading EO 7075/7252.

## Batch-check
Packet members 24; claims checked 15; strict pass 15, fail 0; blocked 9; actual claim-checker all checks passed 15/15; actionable failures none; certifications 0. Apply took 223 s.

## Tool defects / friction
- Exhaustion mechanism string and end_id for a one-time determination are undocumented; accepted as free text (ORIGINAL id as end_id), unreviewed by any controlled vocabulary.
- Machine inventory for 6458 etc. includes signature blocks and, for 6606B clause 6, a following command; whole-paragraph spans for 6684D/6969 hide several commands.
- Prefilled working_text lists a second (clause-drafts copy) confirmation for seven orders; I removed it, apply accepted.
- cruden.py search covers the entire corpus; I filtered to 1933-35 order texts with grep.
- Dossiers carry no chain events, so later_events could be filled only with SUPPLEMENT ids (6296, 6606B).

## LOOKUPS.md
Useful: page check, own-text signals (found the 6532 and 6606B limits), code-name mentions (retail, FACA, Graphic Arts). Missed: the no-text orders gave nothing; it did not flag EO 6723 (service-trade suspension), EO 6647-B/6600 cross-references, or that machine clause spans include signature blocks; it lists no separate-code time limits for 6606E's parent (EO 6533), which I found by reading the sibling order.

## Shared analysis fit
Fit the plain approvals, amendments and the denial rule. Did not fit: (a) three-month "separate code" approvals (6532, 6533-parent of 6606E), (b) open-ended stays pending a report or further order (6458, 6684D): treated as ending with the code, with no earlier end held, a reading the analysis does not expressly cover; (c) a 90-day stay with a discretionary extension (6606B); (d) section 4(a) interim agreement (6205C); (e) agency-direction commands inside approvals (6969).

## Memory-worthy
None for the main session beyond the above.
