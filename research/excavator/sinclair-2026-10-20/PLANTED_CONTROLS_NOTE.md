# Planted controls note

The Sinclair review copies carried planted controls (one per batch, kept in scratch). Review records here have the
planted orders' rows removed from REVIEW_LOG.csv, and reviewer free text that quoted a planted value is redacted in
REVIEW_TELEMETRY.json (batches 02, 04, 06). The planted order in each batch had a genuine producer decision whose
review was therefore lost; those orders (01: EO 9762; 02: EO 10704; 03: EO 12573; 04: EO 13975; 05: EO 11796;
06: EO 12604) have NO accepted proposal and are pending re-review. OUTCOMES.csv rows are the producers' genuine rows.
No planted text is in any proposal.

# Stale generation note (batches 01-05)

Batches 01-05 were frozen before claim-kit's compiled output was regenerated; overlay-propose refuses them
(stale_compiled_generation). Their accepted STATUS_REVIEW.json sheets are kept under <NN>/reviews/ but they are NOT
proposals. They need a re-freeze at the current generation and a fresh independent review. Batch 06 was frozen on the
current generation and has 6 proposals in 06/PROPOSALS.jsonl.
