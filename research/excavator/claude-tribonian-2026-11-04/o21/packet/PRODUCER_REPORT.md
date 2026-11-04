# Producer report, batch o21 (claude)

Start UTC 2026-11-04T06:31:32Z. End UTC 2026-11-04T11:31Z (the long gap includes a usage-limit pause).
Final applied directory: `applied-v1` (no later version was needed). Submitted (assembled proposals) 18, blocked 12.

## Outcome per order
- EO 12739, 12910 (one-day closings): submit; each ends by its own terms on the stated day (1990-12-24, 1994-04-27).
- EO 12771, 12773, 12785: submit; own-terms or express later-order endings read in held Federal Register text; EO 12785's candidate earlier end (1992-12-31) disclosed as a source note, not adopted.
- EO 12786, 12944, 12990: submit; pay schedules end by the successor schedule orders (EO 12826, 12984, 13033) with disclosed alternatives (first pay period after January 1).
- EO 12869, 12974: submit; continuance clauses end by supersession (EO 12974, EO 13062); EO 12869 sec. 2 ends earlier by EO 12882; one-time clauses spent on their effective dates.
- EO 12775, 12779, 12853, 12872, 12914, 12917, 12920, 12922 (Haiti): submit; all end 1994-10-16 under EO 12932 (revocation by number, effective 12:01 a.m. EDT). Dossier conflict resolved as a whole ending. Inventory corrected for 12775, 12779, 12853, 12872, 12917, 12920 (dossier inventories truncated or mis-segmented); kept for 12914, 12922. EO 12922's sentence preserving payments under EO 12920 is a later event, not an end.
- EO 12794, 12795, 12796, 12874, 12899, 12925, 12950, 12967, 13001, 13003, 13004, 13012 (emergency boards): blocked. The order says the board terminates on submission of its report, but no held source gives the submission date, and no held instrument revokes or supersedes the order. Needed: the board report transmittal (or a terminating notice) plus a source that the no-change period lapsed. EO 12899's recital about EO 12874's board and EO 12952's amendment of EO 12950 are later events only.

## What took the time
Reading and quote-verifying held texts for 18 orders; the Haiti inventory corrections; building the assembler-compatible sheets; the rest was tool runtime (apply 80 s, batch-check 90 s, Geddes 75 s).

## Batch-check
packet_members 30; claims_checked 18; strict pass 18, fail 0; outcomes assembled_proposal 18, blocked 12. Actual claim-checker: all checks passed 14, mechanical unverified 4 (EO 12771, 12914, 12922 have a clause quote too short to verify; EO 12944 first-end sources are custody records only), mechanical fail 0, gate passed 18.

## Geddes
6 flags, all `unaddressed_citing_instrument` on EO 12974 (EO 13031, 13203, 13226, 13256, 13265, 14327). All recorded as disputed in `applied-v1/GEDDES_RESOLUTIONS.json`: each is a later revocation of a committee's establishing order after 1997-09-30 (or, for EO 13031, of a portion EO 12974 sec. 3(b) already revoked), so none changes an end. 29 coverage gaps listed in `GEDDES_LINT.json`, mainly on the blocked orders' absent searches.

## Files opened beyond the views
Packet: LOOKUPS.md, decisions.csv, clauses.csv, RATIONALES.json, PACKET.json (via load_packet). Outside the packet, for format and precedent only: `research/excavator/claude-spent-probe-2026-10-28/packet-v4-supp/` (clauses.csv, decisions.csv, RATIONALES.json, PRODUCER_REPORT_v2.md), research/readiness claims, type-rules, rules and factual files, owner rulings, and a grep that surfaced lines from other batches' DRAFT_NOTES.md and the erasmus c2 report (read only the matching lines). Repository sources cited by the packet (held Federal Register texts) were read directly.

## Settings notes
original_confirmed true and original_pages_confirmed false on submit rows (official Federal Register text layer read; no page image viewed; the assembler requires original_confirmed true for these originals). For later-event and end evidence I used full actor texts (ACTOR_TEXT) rather than the transcription-based ACT records for EO 12853, 12917 and 12882, which would have required working-text confirmations.

## Tool defects
- `batch._apply_rows` reports `original_confirmed_required` while the NIRA producer brief says original_confirmed false; the brief is out of date for these FR originals.
- Geddes flags later revocations that come after the first end as unaddressed; it does not compare dates.
- Dossier inventories for several Haiti orders are truncated at mid-section (stub clauses such as an empty Sec. 6).
