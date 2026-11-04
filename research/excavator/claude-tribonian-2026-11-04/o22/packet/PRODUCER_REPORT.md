# Producer report, packet o22 (claude, Tribonian)

Start 2026-11-04T06:37:00Z. End: see final line.

Final applied directory: research/excavator/claude-tribonian-2026-11-04/o22/packet/applied-v4 (v1: 8 rejected for end-source actor; v2/v3 fixed that and EO 13225 later events; v4 blocks EO 13225).

## Outcomes
Submitted (11): EO 13018, 13065, 13136, 13137 (express revocation of the amended parent by EO 13316, 13138, 13225, 13316 respectively, with amendments as later events); EO 13068, 13109, 13238, 13281, 13320, 13343 (one-day closing orders, own-terms end on the named day, inclusive); EO 13184 (revocation of EO 12834 exhausted by performance 2001-01-20).
Blocked (19):
- Emergency boards EO 13027, 13036, 13060, 13205, 13248, 13334, 13351: report date not held, no express revocation held; report deadline is not an end.
- Pay orders EO 13033, 13071, 13144, 13182, 13249, 13282, 13291, 13322, 13332, 13368: supersession date is agency pay-period variable; no held pay-period source.
- EO 13267: termination is "whichever occurs first" bound; enactment date of the Homeland Security Act not held.
- EO 13225: EO 13230 sec. 9 revokes EO 12900 (item 1(c)); EO 13230 not citable from the packet; needs source supplement.
All 11 submitted orders rest on FR text-layer originals (page images not held; original_pages_confirmed false).

## Time
Most time went to reading the 30 views, tracing ending instruments (EO 13316, 13138, 13225), and fixing end-source actor ids (use ORIGINAL id when no ACT/TERM record). Apply/batch-check ran about 1-2 minutes each.

## Batch-check (applied-v4)
11 claims checked, strict pass 11, fail 0; actual checker 9 all-pass, 2 pass with unverified custody (EO 13018 and 13137: custody record only for the PDF), 0 mechanical failures. Exit code 1 is from the two unverified items.

## Geddes
applied-v4: 0 defect flags, 8 coverage gaps (EO 13137, disputed in GEDDES_RESOLUTIONS.json). Earlier v3 had 2 flags on EO 13225 (resolved by blocking).

## Full-packet files opened beyond the views
PACKET.json via load_packet (pickled to scratch); no READ.md or LOOKUPS.details.json.

## Tool defects
Clause rows as end source lack actor ids (assembler needs ORIGINAL/TERM/ACT evidence); batch-check exits 1 on custody-only unverified items. Generator script: /tmp/claude-0/tribonian-work/o22/gen.py.
2026-11-04T11:38:50Z
