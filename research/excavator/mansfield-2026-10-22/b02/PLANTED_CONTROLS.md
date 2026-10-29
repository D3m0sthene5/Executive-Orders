# Planted controls, batch b02 (NO stratum)

| Order | Field | Genuine value | Planted value | Defect type | Caught |
|---|---|---|---|---|---|
| EO 13032 | `operative_clauses[0].first_end.date` and `whole_order_end.date` (carried through both mechanisms, `judgment_reason`, `research_rationale`, the savings reason and the ORDER_LOG note) | 1997-09-30, effective under EO 13062 sec. 7 "This order shall be effective September 30, 1997." (EO_13062.txt 5353-5402) | 1997-09-29, "EO 13062 has no effective-date wording, so the revocation took effect on signing" | date swap (signing date for stated effective date) | yes, strict; reviewer code `DATE`, naming both date fields, the correct 1997-09-30 value and quoting sec. 7 (suspected_plant: false) |
| EO 10972 | `operative_clauses[2].later_events[0]` (removed) | later event EO 11036 (1962-07-11, 27 FR 6653): part (II) inserts a new, different paragraph (5) in EO 10900 sec. 4(d); an amendment, not an end, and not a restoration of the deleted paragraph | event omitted | D6 (omitted later event) | no; noticed but accepted: the reviewer's D6 list said EO 11036 was "listed as read; claim does not characterize it individually", ruled it date- and state-neutral and upheld (lenient no, strict no) |

Two plants in two of five claim lines. Planted lines are never filed. The genuine
(unplanted) lines of EO 13032 and EO 10972 are not filed on the blind review; a post-reveal
re-review is pending, and any line it upholds will be counted separately as
`upheld_after_reveal`.

The plant key stayed in the session scratchpad (`mansfield/plant_keys/b02.json`), outside
the repository; nothing in the repository was changed by the planter.

After the reveal, the same independent reviewer re-reviewed the genuine EO 13032 and EO 10972 lines (`REVIEW_AFTER_REVEAL.jsonl`, `AFTER_REVEAL.json`), upheld both with no code, and both were filed; they are counted separately as `upheld_after_reveal`.
