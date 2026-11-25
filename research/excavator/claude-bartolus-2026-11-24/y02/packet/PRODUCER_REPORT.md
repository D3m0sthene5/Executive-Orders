# Producer report y02 (bartolus)

Start 2026-11-25T01:11:29Z; end 2026-11-25 (see handback). Final applied directory: applied-v2 (applied-v1 was an earlier partial apply, kept as history).

## Outcomes (6 submitted and clean, 1 submitted but not clean, 1 blocked)
- Final applied directory: applied-v4 (v1 to v3 kept as history). The four earlier claims (EO 11623, 11935, 12905, 13736) are byte-identical to applied-v2 and v3 (same claim hashes).
- EO:12171 submit (16 clauses over the 54-clause dossier inventory, merged by section): reconciled against 18 held amending orders. EO 12632 (restates 1-209) is described in the 1-209 reason but not attached as a later event, because its held printing is page-check pending and the kit cannot take it without a grade on the source. VA notices FR 2025-06566 and 2025-19867 concern sections 1-402/1-404 added by EO 14251, not original clauses (conflict resolution recorded).
- EO:12293 submit (14 clauses, merged and one added): later events EO 12363, 12388, 12536, 13118, 13325, 13374; EO 12536 revoked added paragraph 9(e), not an original clause (conflict resolution recorded).
- EO:12580 NOT clean: 76 clauses built, section 1 restated by EO 12777 (described in each section 1 reason, not attached as a cited later event for the same page-check reason as EO 12632), EO 13286, 13308 and 13016 attached. applied-v4 shows 12 unverified quote_verbatim:too_short_to_verify entries (the sec1-c items). The fix (merge 1(c) intro with item (1), and items (3) to (5)) is staged in decisions.csv and clauses.csv, but apply now fails with 'changed prior research; prepare a new version' because research/readiness/owner_rulings/2026-11-24-bartolus-adoption.md changed after applied-v4 (not by me). It needs a coordinator re-prepare, then apply and batch-check. Do not hand applied-v4's EO 12580 claim to completion.
- EO:13179 blocked: performance sources for dated tasks (sections 2, 3(b), 5) not in packet; Working Group end not shown.

## What took the time
Section-by-section reconciliation for 12171, 12293 and 12580; diagnosing why two page-check-pending later-order printings (EO 12632, EO 12777) cannot be cited; the owner ruling file changing mid-run.

## batch-check (applied-v4)
claims_checked 7, actual checker all passed 6, unverified 1 (EO 12580, 12 too-short quotes), fail 0. Every other receipt has an empty unverified list and no out_of_universe quote. Blocked 1.

## Geddes
Run on applied-v4: 0 defect flags, 5 coverage gaps (2 claims, including EO 12580 order-boundary); GEDDES_RESOLUTIONS.json empty.

## Full-packet files opened beyond views
LOOKUPS.md (once), PACKET.json via batch.load_packet (evidence ids, pickled to scratch), decisions.csv, clauses.csv. Papinian y05/y06 PRODUCER_REPORT and decisions/clauses rows for 11935 and 13736 (format only).

## Notes and tool defects
ASSESSMENT first_cause is 'unresolved' for in-force orders (no cessation found). The working directory variable once switched to another packet (r01); I did not read it.
