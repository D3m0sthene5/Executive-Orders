# Producer report c02 (Claude)

Start 2026-11-25T09:07:33Z; end 2026-11-25T09:09:14Z.

## Outcomes
All eight assigned orders are blocked; EO:10125 is dispatch-blocked (left as prepared, unresolved; mandatory sources custody_record_only).
- Common reason: each order's first end is its own status-quo period ("thirty days after the board has made its report"). The actual report date appears only in the NMB report PDFs (PEB-086 for 10130, 087 for 10139, 088 for 10138, 089 for 10140, 090 for 10142, 091 for 10147, 092 for 10150, 093 for 10165), whose bytes are not held (custody_record_only; astra-source-retention and source-ladder blob caches are absent). The thirty-day deadline is not the report date (EO 10140's report is dated 1950-11-03). EO 12553 (1986-02-25) lists every one of these numbers in its revocation table, but under the 2026-10-28 ruling a cleanup revocation is the formal disposition, not the first end. The filed claims' not_later_than bound leaves the step open, so no new claim was submitted.
- Missing source per order: the NMB report PDF named above (bytes).

## What took the time
All eight: reading the filed claim and confirming that no held-bytes source gives the report date. Nothing was researched at length.

## batch-check
Packet members 9; claims checked 0; strict pass 0, fail 0; outcomes blocked 8, unresolved 1; actionable failures none. Final applied directory: applied-v1.

## Geddes
0 flags, 0 coverage gaps (applied-v1/GEDDES_LINT.json); no resolutions file needed.

## Files opened beyond views
None beyond LOOKUPS.md and DISPATCH_CHECK.json; EO_12553 text and jobs/source-ladder/output/SOURCES.jsonl read directly.

## Tool defects
None.
