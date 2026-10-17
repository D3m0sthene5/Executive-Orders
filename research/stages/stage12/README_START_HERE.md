# STAGE 12 — Independent census audit, source intake, and review design

**Project:** The Afterlife of Executive Orders  
**Prepared:** October 16, 2026  
**Legal cutoff preserved:** October 14, 2026, America/New_York  
**Inputs:** Actual immutable Stage 11 ledger (SHA-256 `c0308e008cd719cd153ca667271c93267d5d855bf3eb26d48076e41938fc7729`); original 1943 Clifford L. Lord *Unnumbered Series, 1789–1941* (user-supplied Library of Congress scan, SHA-256 `0553dd2318903af8fd4cdbb56140cd035f3bac52ec5420148307206940ab69e1`).  
**Nature of release:** a reversible analytical overlay, NOT retroactive edits to frozen stage history or model-reviewed substantive judgments.

## Start with the corrected scope

Stage 11 has 15,010 records, 14,973 flagged included bibliographic identities, 193 substantive YES, 2,322 substantive NO, and 12,458 UNKNOWN. Determinate status coverage: 2,515/14,973 = 16.796901%.

Stage 12 identifies an independently corroborated documentary duplicate: `EO:7933A` (the early-index version) and `EO:7933a` (modern Federal Register version) are **the same July 14, 1938 instrument**. The modern representative has accepted substantive NO/any-effect NO; the older source alias is indeterminate. Stage 12's `included_unique_document_proxy` excludes the redundant source identity without deleting either record, source quotation, ID, prior result, or provenance. Consequently the **candidate deduplicated working denominator is 14,972**. Its rollups are **193 YES, 2,322 NO, and 12,457 UNKNOWN**. Coverage is 2,515/14,972 = 16.798023%. All 2,515 legal decisions remain the provisional Stage 11 decisions, not newly externally revalidated determinations.

This does **not** mean 14,972 is the true all-history EO count. The historical unnumbered universe is radically undercovered; the notion of 'EO' varies with historical editorial series. Do not report a national survival fraction using this denominator.

## Implemented changes

1. **Immutable preservation and reversible identity crosswalk.** New source-preserving normalized projection in `DATA/STAGE12_NORMALIZED_NONDESTRUCTIVE_15010.jsonl`. `QA/OVERLAY_CHANGE_LOG.jsonl` records every intentional change, including exact original and new values. Stage 11 ledger bytes remain identical.
2. **Census metadata audit and partial repair.** EO8969 signing year 1946→1941 (1943 3 CFR contemporary table confirms 1941, despite erroneous NARA metadata); EO10276 1961→1951; EO13174 null→2000-10-27 (official 3 CFR text and APP; NARA 2000 disposition says October 31, so `signing_date_conflict` remains true); EO13333 null→2004-03-16. Exact links in the overlay. All these affect date metadata only, not current legal judgments.
3. **Year-by-year comparator.** `QA/ANNUAL_OFR_RECONCILIATION.csv` compares the FederalRegister.gov annual published-order table with deduplicated ledger signing years. After repairs, four mismatches remain: 1937 +1, 1941 +1, 1951 +1 and 2009 -1. Reasons are NOT assumed. EO7700-A is a separately documented August 31, 1937 order not found in the OFR annual table; EO9001A is a distinct 1941 suffixed instrument; the 1951 range (10200–10317) contains 118 serial numbers, whereas the table says 117; the 2009 table says 40 Obama orders, but 13489–13527 comprise 39 numbered orders. Distinct sources have differing inclusion/printing conventions and sometimes erroneous totals. See `QA/REMAINING_YEAR_MISMATCHES.md`.
4. **Lord 1943 volume actually introduced as a source.** `DATA/LORD_1943_PAGE_REGISTER_226.jsonl` records SHA-256 of the OCR text of every chronological-list page, physical PDF pages 23–248, and records how many machine-recognized month/day anchors appeared. `DATA/LORD_1943_DATE_LEADS_SOURCE_ONLY.jsonl` holds **717 OCR-derived date-line leads** with exact page, OCR line, text and source PDF hash. OCR years and full dates are intentionally NULL and any inferred heading is explicitly marked unreliable. These 717 are **neither independently authenticated executive orders nor an exhaustive extraction of the volume**: the 1943 editor wrote that more than 1,500 unnumbered items were listed, but many have split/corrupt/absent OCR date labels, and a few OCR lines could be non-order citations. This lead list is a human/AI page-review work queue and **adds zero validated orders**.
5. **Historical-authorship and identity flags.** `QA/IDENTITY_AUTHENTICATION_SAMPLE_30.csv` is a reproducible 30-entry identity audit sample spanning historical index, official-numbered, and 19 currently included unnumbered rows. `QA/ADVERSARIAL_TARGETED_CHAIN_PANEL.csv` flags document-vs-number and delegated-authority questions (including EO 3016C/K/N); codebook supplement below defines a signer/authority crosswalk. These are actual sample files, not claims that the full authentication has been performed.
6. **Blinded legal audit.** `QA/BLIND_PRESENT_STATUS_AUDIT_60.csv` draws a fixed-seed disproportionate status-by-era sample to independently reconstruct whole legal footprints. Existing project outcomes are excluded from this blind sheet; a separately stored `QA/REVIEW_KEY_WITH_BASELINE_60.jsonl` enables comparison after independent review. A review must re-acquire original source independently. The sample creates an evaluation protocol and cases; **the legal reviews are not completed in this release**. Stratum-weighted rather than unweighted error estimates will be necessary.
7. **Legal-meaning alternatives and episode model.** `METHODOLOGY_CODEBOOK_SUPPLEMENT_PROPOSED.md` describes the competing present-effect estimands and introduces an ever-operative state and provision/episode timeline. Original codebook 2.0.0 is **not silently changed**; a new legal definition may be adopted only after adjudicating the adversarial cases and recoding sensitivities.
8. **Causation gets its own progress metric.** Normalized field `cause_evidence_state` distinguishes untouched causal questions, later termination but unresolved first cause, populated but unverified cause/date, and unresolved status. Of 2,322 substantive NO, **2,216** still have a literal unknown cessation mechanism. Merely populated causal fields do not establish that the causal history was proved.
9. **Historical coverage visualized with defensible denominators.** A standalone, offline `VISUALS/EO_STAGE12_AUDIT_DASHBOARD.html` plus PNGs and row-level CSVs show issuance-decade histogram, substantive YES/NO/UNKNOWN counts, and research-coverage percentages, using only the deduplicated **included working bibliography**. The 1789–1861 gap is visibly marked as missing inventory, rather than falsely charted as zero orders ever issued. The uploaded unnumbered leads are deliberately not counted as new orders.
10. **Deterministic regeneration and verification.** `SCRIPTS/build_stage12.py` regenerates overlay, source leads, samples, metrics and figures directly from the frozen Stage 11 JSONL and original PDF; `SCRIPTS/verify_stage12.py` checks counts, identities, source hashes, correction reversibility, sampled cases, and nonpromotion of Lord leads.
11. **Seven original-queue provenance flags receive an explicit *provisional* overlay.** The source dossier reported that seven NARA source-row IDs were falsely marked members of the original 1,943-identity queue. Stage 12 carries these seven repairs in a separate normalized field with provenance to that audit; the exact original 1,943 CSV was not separately inspected in this release. This is transparent inherited finding, not independently certified.

## Deliberately not done

- No attempt to force Lord's 1,500+ entries into 1,500 signed presidential instruments, or to add 717 OCR lines to the denominator.
- No status change from NO to YES (or reverse), and no claim to have proved any first cessation cause or legal error rate.
- No wholesale collapse of other aliases on similar titles without documentary identity proof.
- No use of the 16.8% coverage metric to estimate the survival fraction.
- No claim that the official Federal Register published-order universe equals *all* presidential executive orders issued since 1789.
- No assertion of a complete post-cutoff week: October 14 is the immutable legal cutoff; official publication can lag signature.

## Reproduction

Unzip original `EO_STAGE11_RECONCILED_EXECUTION_PACKET_2026-10-16.zip` so its JSONL is available, and have the original `public-gdc-43013029-43013029.pdf` in your work folder. Run:

```bash
python SCRIPTS/build_stage12.py /path/to/RECONCILED_STATUS_LEDGER_STAGE11_PROVISIONAL.jsonl /path/to/public-gdc-43013029-43013029.pdf .
python SCRIPTS/verify_stage12.py /path/to/RECONCILED_STATUS_LEDGER_STAGE11_PROVISIONAL.jsonl /path/to/public-gdc-43013029-43013029.pdf .
```

PDF source can be retrieved at <https://www.loc.gov/item/43013029/>; contemporary and official crosschecks are linked in the change log. Use `pdftotext` and `matplotlib`; all other dependencies are Python standard library. The supplied Stage 11 execution packet was separately reverified with its own `SCRIPTS/verify_release.py` PASS on this run.

## Next legal/archival gates in highest-return order

1. Verify the 717 machine-extracted date-line leads and harvest **all other list entries** page-by-page, separating exact signed sources, copied text, references and undated entries. Do not inflate the numerator.
2. Finish the 30-case identity sample, including signed instrument vs administrative derivative and all source date conflicts.
3. Complete the 60 blind whole-instrument status audits and the targeted TC07/TC09/EO3461/Polk panels. Quarantine entire affected producer families for systematic evidence failures, if discovered.
4. Implement clause/episode first-cause extraction and a stratified cohort survival study for a defined, reasonably complete series before commissioning thousands of more convenience-selected current-status findings.
5. Reconcile the four remaining annual discrepancies against original 3 CFR, signed instruments and OFR data; document true table error vs extra valid suffixes or changed conventions.

**This release's main achievement is improved accounting and an executable falsification apparatus, not an artificial increase in substantive-legal-status coverage.**