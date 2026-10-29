# Planted controls, batch b03 (NO stratum)

| Order | Field | Genuine value | Planted value | Defect type | Caught |
|---|---|---|---|---|---|
| EO 10312 | `operative_clauses[3,4,8].later_events[3]` (removed) and `research_rationale` (also judgment reasons, savings reading record, ORDER_LOG note) | later event EO 11051 of 1962-09-27 (27 FR 9683), sec. 601(2): OCDM and OCDM Director references in EO 10312 amended to the Office of Emergency Planning and its Director (EO_11051.txt 21962-22419); amendment, clause continues, in secs. 1(c), 2 and 6(a) | event omitted; officer chain stops at the OCDM Director (EO 10782) | D6 (omitted later event) | yes, strict; reviewer code `D6_OMISSION`, naming EO 11051 sec. 601(2), quoting it, and naming secs. 1(c), 2 and 6(a) and the changed acting officer (reviewer could not tell plant from producer miss) |
| EO 5825 | `operative_clauses[0,1].first_end.date`, `whole_order_end.date`, both mechanisms, `research_rationale`, `judgment_reason` | 1939-07-05: EO 8189 states no effective date, so the revocation took effect on signing | 1939-07-01, attributing EO 8190's "This order shall become effective on July 1, 1939." (EO_8189.txt 18505-18556) to EO 8189 | date swap (carried consistently) | yes, strict; reviewer code `DATE`, naming whole_order_end and both clause first_end dates, giving 1939-07-05 and showing the sentence belongs to EO 8190 (suspected plant) |

Two plants in two of seven claim lines. Planted lines are never filed. The genuine
(unplanted) lines of EO 10312 and EO 5825 are not filed on the blind review; a post-reveal
re-review is pending, and any line it upholds will be counted separately as
`upheld_after_reveal`.

The plant key stayed in the session scratchpad (`mansfield/plant_keys/b03.json`), outside
the repository; nothing in the repository was changed by the planter.

After the reveal, the same independent reviewer re-reviewed the genuine EO 10312 and EO 5825 lines (`REVIEW_AFTER_REVEAL.jsonl`, `AFTER_REVEAL.json`), upheld both with no code, and both were filed; they are counted separately as `upheld_after_reveal`.
