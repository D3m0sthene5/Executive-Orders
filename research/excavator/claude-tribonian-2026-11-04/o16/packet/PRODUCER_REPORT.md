# Producer report, packet o16 (Tribonian), claude

Start 2026-11-04T06:22:08Z. End 2026-11-04T06:42:44Z.
Final applied directory: applied-v2 (applied-v1 is retained: all 19 submissions failed assembly because the CLAUSES evidence record carries no actor; v2 cites the ORIGINAL record, or the matching until_event term record for EO 11333, as the end source).

## Outcome per order
Submitted (19), all terminated by own terms, no later events found:
- Inspection-of-returns orders (16): 11065 (end of 87th Congress, 1963-01-03); 11082, 11083, 11099, 11109, 11133, 11153 (88th, 1965-01-03); 11192, 11201, 11204, 11217, 11235 (89th, 1967-01-03); 11332, 11337, 11358, 11370 (90th, 1969-01-03). The Congress end date comes from the Twentieth Amendment, section 1, whose text is not held; the claims say so. A held House Historian session-dates capture (jobs/source-ladder) is disclosed as an earlier-candidate note but is not a packet-citable source. Reviewer should look at this dependency first.
- 11128 closing of agencies, ends 1963-11-25.
- 11333 suspension of 10 U.S.C. 6374, ends 1968-06-29 inclusive (exclusive reading stated).
- 11076 advisory commission, six clauses, sunset 1963-12-31 (stated as not later than; outer bound disclosed).

Blocked (11): 11064 (holiday period end for leave paragraph not fixed); 11193 and 11233 (interment dates not held); 11211 and 11285 (statute ending the interest equalization tax not held; 11285 also has a bad order boundary and 45-scope inventory); 11215, 11309 (final report transmittal date not held; 11309 is tied to 11215); 11341, 11365 (final report presentation date not held; 11365 inventory also mis-segmented); 11378 (start of the three-year exemption not stated); 11381 (no held ending of EO 10807 or the Council).

## What took the time (one line each)
Tax-return orders: reading the Congress-end question and finding the held House page (one decision shared by 16). 11076: split of six clauses and the not-later-than sunset. 11128, 11333: quick own-terms reads. Blocked orders: confirming by held-text search that no interment, report or statute source exists (three cruden searches).

## Batch-check
claims_checked 19, strict pass 19, strict fail 0; actual claim-checker 19 of 19 all checks passed; blocked 11.

## Geddes
Lint run on applied-v2: 0 defect flags, 0 coverage gaps. No GEDDES_RESOLUTIONS.json needed.

## Full-packet files opened beyond the views
LOOKUPS.md (read) and decisions.csv / clauses.csv. PACKET.json was loaded once through batch.load_packet to list evidence ids; READ.md and LOOKUPS.details.json were not opened. Outside the packet I read the held EO 12553 text, the held source-ladder House page, the cruden number search for EO 10807, and committed claims for precedent on mechanisms.

## Tool defects
Standalone `geddes.py lint .` run with a relative path inside the applied directory failed with a PACKET.json lookup error and overwrote batch-check's lint file; I reran it with an absolute path and the result is clean. The CLAUSES record has no actor, so it cannot serve as an end source without an error that only says first_end.
