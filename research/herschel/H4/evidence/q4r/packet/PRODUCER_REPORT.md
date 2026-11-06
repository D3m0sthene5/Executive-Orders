# PRODUCER_REPORT — H4-w14, packet q4r (EO:12720)

Start 2026-11-06T00:08:07Z; end 2026-11-06T00:17Z (UTC). Final applied directory: applied-v2 (applied-v1 was rejected: I left the savings_check column empty).

## EO 12720 (President's Council on Rural America): submitted (publication_kind whole_case, replacement proposal for the frozen sol-2026-10-18 upstream proposal)
- Clause inventory: done. Corrected to nine disjoint spans of the held government-printed text (55 FR 29337-29338). The machine inventory had 3(d) merged into 3(c).
- Ending / current basis: done. All clauses terminated 1993-01-16 by the order's own sec. 3(e) as amended by EO 12783. The order has no effective-date provision, so the amendment is taken as effective on signing, 1991-12-17. The exclusive reading is stated. EO 12783 is a later event on 3(e), with before and after. EO 12869 (58 FR 51751, effective 1993-09-30) is a later formal revocation, not the first end. Status is NO, so no current predicate is needed.
- Savings and residuals: done. Neither EO 12783 nor EO 12869 has a saving clause. The only residual is accrued travel entitlements under 3(b), by operation of the cited statute (5 U.S.C. 5701-5707).
- Counterevidence: done. A regex search of held order texts for 12720 and "Rural America" found only EO 12783 and EO 12869, so no earlier end and no extension is held. The frozen prior proposal reached the same first-end date.
- Caveats: original_pages_confirmed is false, because only the OCR text was read and no page image. The three machine-search hits (3 each) are not itemized in the view.
- Time: most went to reading the packet and rules, the inventory offsets, and one wasted apply run (about 35 s).

## Checks
batch-check: 1 claim checked, 1 strict pass, 0 fail, actual checker 1/1 passed (mechanical pass, gate pass). Geddes: 0 defect flags, 2 coverage gaps (own_order_body_unverified and citing_own_body_unverified, both reason order_heading_unresolved). GEDDES_RESOLUTIONS.json is empty, with no flags to resolve.

## Files opened beyond the views
jobs/claim-kit/BATCH.md, COMPLETION.md, batch.py, assemble.py, working_text.py (read to learn the sheet format and publication_kind), research/stage19/code/claim_gate.py (grep only), PACKET.json (machine_searches only), and the held texts of EO 12720, 12783 and 12869.

## Tool defects / notes
- jobs/claim-kit/q4r.md and the packet's LOOKUPS.md do not exist, so I worked from the views only.
- apply fails with a generic error when savings_check is blank (it names the "member-specific legal check").
