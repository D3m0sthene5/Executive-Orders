# Producer report, producer-y01 (Papinian lane)

Start 2026-11-10T03:22:54Z; end 2026-11-10T03:48Z (follow-up pass). Final applied directory: `applied-v5` (7 submit, 18 blocked; the 7 submitted claims are identical to applied-v4).

## Outcomes (25 members: 7 submit, 18 not submitted)

Submitted (YES, original-plus-bounded-search route, all clauses decided): EO:11471, EO:12112, EO:12642, EO:12879, EO:13243, EO:14177, EO:14354.
- EO:13243: Sec. 3(a) replaced by EO 13261 Sec. 4(c) (later event, before/after recorded); Sec. 4 (revocation of an earlier order) terminated on signing 2001-12-18; two heading-only clauses merged by inventory correction (too short to verify).
- EO:14177: Sec. 6 (revokes EO 14007) terminated on signing 2025-01-23; Sec. 5 own-terms end 2027-01-23 is after the cutoff; EO 14354 recorded as a later event (continues PCAST to 2027-09-30).
- EO:14354: Sec. 3 (supersedes EO 14109 Secs. 1-2) terminated 2025-09-30 (effective date, Sec. 4); dossier conflict PARTIAL_END_CANDIDATE_ON_YES_ORDER resolved (the seven machine-detected terminations are Federal Register committee notices restating the 2027-09-30 end).

Blocked (precise gap): 
- EO:9873: no held source dating performance of either transfer clause or a current command.
- EO:12423: current text of EO 12163 Sec. 1-301(b) not held; Sec. 2's target (EO 11958) revoked by EO 13637 (2013-03-08).
- EO:13106: effective date of EO 13144 supersession of Secs. 1-7 and current text of EO 12748 Sec. 2(c) not held.
- EO:13303, 13553, 13662, 13949, 14033, 14068: emergency-dependent; National Emergencies Act continuation notices (dossier lists them through 2026) are absent from the census and not citable.
- EO:14283: no held source dating the EPA termination of the advisory council under Sec. 6.

Follow-up pass (applied-v5): the eight earlier unresolved members are now quick precise blocks, decided from held views only, not full per-clause work:
- EO:11023: Text of Public Law 107-372 and the repealed 1948 Act, needed for per-clause state of EO 12608 Sec. 10 and EO 13341 amendments.
- EO:11651: Held text of the Agreement on Textiles and Clothing expiry and current 7 U.S.C. 1854.
- EO:11755: Held FAR or successor text showing performance of Sec. 2 revision; inventory correction for Secs. 2 and 3.
- EO:12038: Six proclamation actors (PROC:4317, 4341, 4355, 4370, 4377, 4412) absent from census and statute texts not held.
- EO:12146: EO 13286 actor context (actor-texts/EO_13286.json) not read; no current text of the Federal Legal Council provisions held.
- EO:12154: Current Executive Schedule (5 U.S.C. 5316-5317 as of 2026-10-14) not held.
- EO:12600: Per-agency completion dates of Secs. 1 and 7 commands and own-terms end source for Sec. 3(a)(i).
- EO:12656: Page-image check, scope of EO 13603 partial revocation (2012-03-16), and EO 13286 actor context.

No member was found not in force on 2026-10-14. No ledger change.

## What took the time (one line each)
Submitted orders: 11471/12112/12642/12879 short standing orders, reading only; 13243 reading EO 13261 and the inventory merge; 14177 and 14354 clause-by-clause reasons and the 14354 conflict resolution. Blocked and unresolved orders: triage from the views (events, dossier missing lists, notice lists) only.

## Batch-check (applied-v4)
claims checked 7, strict pass 7, fail 0; actual checker: 7 gate passed, 7 all checks passed, 0 mechanical fail, 0 unverified. Earlier versions: applied-v1 rejected 3 (end source lacked an actor), applied-v2 passed with 1 unverified (13243 heading quotes too short), applied-v3 superseded by v4 (text corrections only).

## Geddes
3 flags, all EO:14177 (unaddressed_citing_instrument for EO 13381, EO 13467, EO 13764, which Geddes reads as revoking EO 12968); all disputed in `applied-v4/GEDDES_RESOLUTIONS.json` (each quoted text preserves the remainder of EO 12968 as amended and ends no clause of EO 14177). Coverage gaps (citing_corpus_incomplete and own-body unverified) are advisory.

## Files opened beyond the views
LOOKUPS.md (head only), LOOKUPS.details.json (structure only), PACKET.json via batch.load_packet (conflicts, evidence records), jobs/current-law/output/ORDERS_CURRENT_LAW.csv (per-order ending/conflict columns), jobs/fr-originals/data/full_run/texts/EO_13261.txt (Sec. 4), jobs/claim-kit assemble.py, batch.py and research/stage19/code/claim_gate.py (formats). No READ.md.

## Tool defects
- Self-executing revocation clauses cannot use their own clause evidence as an end source (the clause record has no actor); ORIGINAL:EO:N worked.
- Heading-only clauses in the inventory (EO 13243 Sec. 2 and Sec. 3) fail the verbatim-quote check as too short; fixed by inventory override.
- A view-printing pitfall: source_catalogue holds dozens of TERM records per order when a U.S. Code note prints the order.

## Follow-up pass
applied-v5: apply and batch-check repeated; 7 claims strict pass, 0 fail, 7 of 7 actual checker passes, 0 unverified; outcomes 7 assembled, 18 blocked. GEDDES_LINT.json regenerated by batch-check (same 3 EO:14177 flags); GEDDES_RESOLUTIONS.json copied unchanged (flag ids identical). ASSESSMENT.jsonl outcomes for the eight updated to blocked.
