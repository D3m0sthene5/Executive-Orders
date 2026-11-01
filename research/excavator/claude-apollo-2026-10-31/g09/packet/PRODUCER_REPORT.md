# Producer report, packet g09 (24 orders)

Start UTC: 2026-10-31T22:16:14Z. End UTC: 2026-11-01T03:41:17Z (batch-check finished). The session was paused by a usage-limit reset between roughly 2026-10-31T23:xxZ and 2026-11-01T03:35Z, so elapsed wall time overstates working time.

Final applied directory: `research/excavator/claude-apollo-2026-10-31/g09/packet/applied-v1` (one apply, no later versions needed).

## Batch-check counts
23 submitted, 1 blocked, 0 unresolved. `batch-check`: claims_checked 23, strict_claim_pass 23, strict_claim_fail 0, actual claim-checker all_checks_passed 23 (mechanical pass 23, unverified 0, fail 0, gate passed 23), actionable failures none. Independent human certifications 0. apply wall time 82 s; no "changed Valla review context" refusal occurred in the real packet.

## Outcomes
All 24 orders keep their provisional status NO. All submitted claims cite held official Federal Register text layers (grade original_representation_unverified, acceptable as original); no transcription is used, so no working-text disclosure is needed.

Ended by EO 12553 (1986-02-25, effective on signing; no effective-date, savings or exception wording in the held text): 11486, 11543, 11558, 11559, 11585, 11664, 11679, 11783 (emergency boards; report deadline and standstill recorded as spent facts under the 2026-10-21 report-deadline ruling), 11621 (board of inquiry; EO 11622 amendment recorded as a later event with before/after text), 11650 and 11706 (tax-return inspection orders; the 1976 statutory rewrite of IRC 6103 is disclosed as an unnamed earlier candidate, not used), 11771 (Liaison Office privileges; later change of status and statute disclosed as candidates), 12162 (deletes the sunset sentence of EO 12140), 12189 (heavy-oil exemption; EO 12287 of 1981-01-28 disclosed as an unnamed overlapping command, not an end).
Ended by EO 12379 (1982-08-17): 12095 and 12159 (boards, named by number in Secs. 5 and 6), 12121 (amends EO 12083, revoked "as amended" by Sec. 20; later event EO 12156), 11547 (amends EO 11330, revoked "as amended" by Sec. 17). For 12121 and 11547 the claim states that the order is not named by number and gives the alternative reading.
Ended by EO 11562 Sec. 7, named by number (1970-09-25): 11492 (savings state transferred_or_accrued through Sec. 6 continuity).
11646: first end 1981-09-30 (Great Lakes Basin Commission terminated, EO 12319 Sec. 1(b)); revocation of EO 11345 as amended effective 1981-10-01 recorded as later event and alternative first end; EO 11882 and EO 12038 amendments recorded as later events.
12176: own-terms sunset 1980-03-15 inclusive (exclusive reading stated); EO 12258 (effective 1980-12-31) recorded as a later event, not the end; the report date of the same day is a deadline.
12060 and 11877 (Executive Schedule amendments): dossier inventories were incomplete or bundled (12060 omitted Secs. 1 and 2; 11877's scope (c) swallowed Sec. 2), so I corrected inventories with absolute offsets. Amending clauses end 1978-08-18 with EO 11861 "as amended" (EO 12076 Sec. 1-202); the one-time commands (12060 Sec. 3 revoking three orders, 11877 Sec. 2 superseding EO 11864) are exhausted on signing; EO 12035 recorded as a later event on 11877 1(b); savings transferred_or_accrued (EO 12076 Sec. 1-201 and re-placed positions).
11559: dossier inventory of thirteen scopes (OCR spill of neighbouring FR documents) replaced by one scope, offsets 521-2171.

Blocked: EO 12091. Gap: no held source dates the conclusion of the White House Conference on Small Business, so which limb of Sec. 1-402 as amended (April 30, 1980, or 60 days after the conference, whichever is sooner) ended the Commission first cannot be dated; EO 12258 (1980-12-31) postdates every possible own-terms end and is not the first end.

Corrections to dossier leads: the dossier chain events dated 1962, 1965 and 1975 for EO 12095 and EO 11547 come from source-ladder files filed under EO 11022, 11256 and 11829 that are reprints of EO 12379's pages; ACT leads for EO 12189 against EO 12209 and EO 12919 do not concern it (12209 amends EO 12187; 12919 does not contain the number 12189).

## What took the time (one line per order)
- 11486, 11543, 11558, 11585, 11664, 11679: reading the order and locating the EO 12553 table entry (the dossier had no provision located); templated reasoning.
- 11559: diagnosing and replacing the OCR-polluted inventory.
- 11783, 12162, 12189: positional pairing of EO 12553's number-only column (PDF page 14) with the subject column.
- 11621: amendment text of EO 11622 and the continuing-existence sentence.
- 11650, 11706: deciding how to disclose the statutory-rewrite candidate under the unnamed-instruments ruling.
- 11771: disclosing the Liaison Office status candidate; statute not held.
- 11492: reading EO 11562 Secs. 6 and 7 and choosing the FR ACT copy over mirrors.
- 12095, 12159: spotting mislabeled source-ladder reprints behind the bogus chain dates.
- 12121, 11547: reasoning that revocation "as amended" reaches the amending order and stating the alternative reading.
- 11646: reading EO 12319 (termination 09-30 vs revocation 10-01) and the two later amendments.
- 12176: reading the sunset wording and choosing an end source with an actor (ORIGINAL record).
- 12060, 11877: inventory corrections, one-time-command analysis, scanning fourteen later amendments.
- 12091: searching held texts for the Conference's conclusion date; block.
- Tool time: the first `apply` of any harness run took 1.5 to 2.5 minutes before loading (cold cache); batch-check about 4 minutes.

## Tool defects and friction
- The first end source for a self-ended clause must carry an actor: a `CLAUSES:` evidence id as `end_id` fails with clause_first_end, so own-terms and performed-command ends cite the `ORIGINAL:` record (whole original text as quote).
- `apply` refuses output outside the packet and a copy of the packet outside the repository fails the Valla context check, so dry runs had to call `batch._apply_rows` in-process.
- Dossier gaps "target provision not located" for tables printed in one-line layout (EO 12553 page 13) and number-only columns (page 14) should be solved by an ACT-override pass; here the whole actor text is the cited source and the exact table entry is quoted in the reason.
- `original_confirmed` must be true for an acceptable-as-original FR text layer even when `original_pages_confirmed` is false (no page images were inspected by me; the text layer is machine-extracted OCR).
