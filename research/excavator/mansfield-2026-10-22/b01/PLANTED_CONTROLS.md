# Planted controls, batch b01 (NO stratum)

| Order | Field | Genuine value | Planted value | Defect type | Caught |
|---|---|---|---|---|---|
| EO 10926 | `operative_clauses[0].first_end.source.quote` (same cut carried into `whole_order_end.source.quote`; both `char_end` recomputed) | EO_12553.txt 691-966, ending "...and any amendments thereto, are revoked:" | EO_12553.txt 691-953, ending "...and any amendments thereto," (operative words "are revoked:" at 953-966 removed) | D3 (truncated quote) | yes, strict; reviewer code `QUOTE`, naming both end sources, the cut at 953 and the missing "are revoked:" (suspected_plant: true) |

One plant in one of two claim lines. Planted lines are never filed. The genuine
(unplanted) EO 10926 line is not filed on the blind review; a post-reveal re-review is
pending, and any line it upholds will be counted separately as `upheld_after_reveal`.

The plant key stayed in the session scratchpad (`mansfield/plant_keys/b01.json`), outside
the repository; nothing in the repository was changed by the planter.

After the reveal, the same independent reviewer re-reviewed the genuine EO 10926 line (`REVIEW_AFTER_REVEAL.jsonl`, `AFTER_REVEAL.json`), upheld it with no code, and it was filed; it is counted separately as `upheld_after_reveal`.
