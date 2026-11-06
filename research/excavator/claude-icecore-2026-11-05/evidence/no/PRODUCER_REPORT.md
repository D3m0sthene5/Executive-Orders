# Producer report: icecore "no" packet (claude)

Start 2026-11-05T21:20:36Z. End 2026-11-05T21:36:06Z.

Final applied directory: applied-v2 (applied-v1 kept; it had EO:10359 submitted and failed the actual checker).
Result: 1 submitted (EO:13071), 25 assigned orders blocked, 2 non-assigned (13682, 14011) left as coordinator-blocked. batch-check on applied-v2: exit 0, 1 claim, strict pass 1, actual checker all-passed 1, mechanical fail 0, unverified 0, Geddes flags 0 (GEDDES_RESOLUTIONS.json empty).

## Outcome per order (and time sink)
- EO:13071 SUBMIT. Ended by EO 13106 sec. 7 ("is superseded"), recorded 1998-12-07 (signing); disclosed alternative: replacement schedules take effect 1999-01-01 / first pay period after. Inventory restated as 14 clauses (one-character "7." fragment merged into 3(c)) after v1 "too_short_to_verify". Time: deciding the supersession effective date; inventory fix.
- EO:10359 BLOCKED (substance supported: EO 10480 sec. 607(8) supersedes/revokes it, 1953-08-14; inventory corrected to Section 1 and Section 2). Actual checker fails order_exists (not_in_universe) on OCR tokens "Executive Order 96361" (neighbouring EO 10358 text inside the registered original's whole-record quote) and "E. O. 1-C" (EO 10480 whole-record quote); a sheet cannot narrow these. Needs a cleaner registered text or a checker fix. Time: inventory correction, quote verification, v1 failure.
- EO:11949 BLOCKED: only amends EO 11821 (sunset 1976 to 1977); EO 11821 expiry not citable evidence in packet; extension search not shown.
- EO:11503 BLOCKED: sec. 1 own-terms end 1969-12-26, but sec. 2 "holiday period" leave policy has no fixed end.
- EO:12650, EO:13351 BLOCKED: Board terminates on report; submission date not held; no revocation held (EO 13810 hit is an unrelated sanctions order).
- EO:10227, 9023, 9519 BLOCKED: First War Powers Act title II text/expiry not held; EO 10789 does not revoke EO 10210.
- EO:10907, 10911, 11631 BLOCKED: IRC return-inspection statutory change (e.g. TRA 1976) not held.
- EO:10126 BLOCKED: 1966 FAA Part 73 amendment shrinks P-56 but does not say the EO reservation ended.
- EO:12079, 10311, 10240 BLOCKED: underlying statute repeal/expiry text not held.
- EO:12328 BLOCKED: no end; delegation under 18 U.S.C. 437(b), heading/boundary unverified.
- EO:10330 BLOCKED: indefinite exemption; end of person's service not held.
- EO:11309 BLOCKED: amends EO 11215 only; final-report transmittal date not held.
- EO:7678, 8932, 9026 BLOCKED: no revoking public land order/act held.
- EO:8215, 8766, 9709, 9776 BLOCKED: no ending instrument/fact held (details in decisions.csv gaps).
Most time went to triage scans of the held corpus for later instruments; each blocked order took one targeted scan.

## Files and defects
- Opened beyond views: LOOKUPS.md, decisions.csv, clauses.csv, RATIONALES.json, PACKET.json (via load_packet, check_sources=False, cached in /tmp/claude-0/icecore-work/no). Also read one other folder by mistake: claude-production-2026-10-28/b1a/packet/decisions.csv (first row only, no content used).
- Repository sources read: held EO texts for 13106, 10480, 10789, 12044, 11821, 11215, 9212, 9280, and the FAA text cited in LOOKUPS.
- Tool defects: (1) actual checker order_exists false positive on OCR numbers in whole-record quotes (EO 10359); (2) inventory fragments such as "7." fail quote_verbatim (too_short_to_verify) with no sheet-level merge short of restating the whole inventory.
