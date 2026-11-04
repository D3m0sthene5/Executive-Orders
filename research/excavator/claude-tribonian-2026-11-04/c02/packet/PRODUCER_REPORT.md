# Producer report c02 (Tribonian corrections)

Start UTC: 2026-11-04T12:05:26Z
End UTC: 2026-11-04T16:27:29Z

## Re-prepare
The first apply refused with "changed prior research". The coordinator re-prepared the packet at the same path (stale copy kept as packet-stale-v1). I compared all 34 views: only prior_research_for_order (29 orders; extra locations and reviews recorded for the same prior claims by other batches) and size/fingerprint fields changed; own text, sources and lookups were identical (LOOKUPS.md byte-identical), so no row was revised for that reason.

## Final applied directory
applied-v3 (applied-v1 rejected 28 for original_confirmed_required and inventory override source id; applied-v2 fixed those, 28 assembled; v3 fixed the EO 10156 paragraph 3 end).

## Outcomes
28 submitted (assembled proposals), 6 blocked: 10061, 10295, 10397, 10792, 10825, 10856. Each block names the missing source in decisions.csv unresolved_material_gaps (a pinned source is needed that the packet's evidence list does not hold, e.g. Career Compensation Act and EO 10084/10098/10118 pins for 10061; post-1989 seal source for 10295; EO 10441 not pinned as a later event for 10397). Submitted orders were corrected for each brief defect confirmed in held sources (for example: 12480/12481 standstill ran to 1984-10-18 by the order's own terms; 12554 supersession sentences corrected, EO 12670 does not supersede; 12584 report dated 1987-02-26 with the parent's report-relative sunset disclosed, EO 12581 an earlier amendment; 12447 EO 12455 and EO 12534 disclosed as unnamed candidates; 10045 and 10125 reports described from the held NMB copies; 10156 paragraph 3 end now consistently EO 10753 on 1958-02-15).

## What took the time
Per order: reading the held original and the cited sources to test each brief defect, then rewriting the affected rationale, check and clause sentences. Longest: 10061/10295/10397/10792/10825/10856 (searching for a supportable source before blocking), 11452 (15 clauses), 12202 and 12275 (inventory corrected to cover the whole text), 12554 (eight later events), 12584 (parent sunset analysis). The apply step took about 1 and 4 minutes.

## Batch-check (applied-v3)
34 members; 28 claims checked; strict pass 28, fail 0; 6 blocked. Actual checker: 27 all checks passed, 1 mechanical fail (EO 10156): order_exists:not_in_universe on operative_clauses[2].original_operative_text. The held text prints "Executive Order No. 98661" (an OCR footnote digit fused to 9866), so the checker reads a nonexistent order number. It is a property of the held bytes, which must be quoted exactly; not changed.

## Geddes
GEDDES_LINT.json: 28 claims, 0 defect flags, 18 coverage gaps in 9 claims (advisory). GEDDES_RESOLUTIONS.json records no resolutions because there are no flags.

## Full-packet files opened beyond the views
PACKET.json (via load_packet, check_sources=False). Prior-claim files named by the brief, read as drafts; no review files.

## Tool defects
- OCR "98661" in EO 10156 triggers the checker's order_exists failure on a verbatim quote.
- original_confirmed must be true for these original_representation_unverified orders, although the NIRA example shows false.
- A claim's decoded inventory override source id (OVERRIDE:ORIGINAL:...) cannot be reused as the sheet's inventory_source_id; it must be ORIGINAL:EO:N.
