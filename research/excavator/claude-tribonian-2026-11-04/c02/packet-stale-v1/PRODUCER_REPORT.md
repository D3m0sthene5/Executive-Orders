# Producer report c02 (Tribonian corrections)

Start UTC: 2026-11-04T12:05:26Z
End UTC: 2026-11-04T12:27:10Z

## Outcome: STOPPED at apply

`python3 jobs/claim-kit/kit.py apply <packet> --write <packet>/applied-v1` refused with: "claim-kit: changed prior research; prepare a new version" (check at jobs/claim-kit/batch.py line 290). Per the instructions I stopped and did not work around it. No applied-v1 was written, batch-check and Geddes lint were not run.

## Work completed before the stop
- decisions.csv and clauses.csv were filled for all 34 orders (28 submit, 6 blocked: EO 10061, 10295, 10397, 10792, 10825, 10856, each with a precise missing-source gap). RATIONALES.json left as {} (free-text rationales used).
- Defects in the brief were checked against held sources and corrected in the sheet rows (for example EO 12480/12481 standstill ran to 1984-10-18 by the order's own terms; EO 12554 supersession sentences corrected; EO 12584 report dated 1987-02-26 and the parent's report-relative sunset disclosed; EO 12447 earlier candidates disclosed).
- The sheet has not been validated by the kit, so it may contain further errors.

## Full-packet files opened beyond the views
PACKET.json (loaded via load_packet, check_sources=False). Prior-claim files named in the brief were read as drafts; review files were not opened.

## Tool defects
apply refuses with "changed prior research" on an unmodified-by-me packet (only decisions.csv and clauses.csv were edited). The packet's prior-research fingerprint appears out of date relative to the repository; a new prepare is needed by the coordinator.
