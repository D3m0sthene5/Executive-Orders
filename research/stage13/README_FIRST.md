# STAGE 13 — Foundational research verification and historical coverage repair

**Cutoff remains:** October 14, 2026. **Mode:** source-grounded, non-destructive corrections, with explicit legal confidence. **Source releases:** Stage 11 frozen ledger SHA256 `c0308e008cd719cd153ca667271c93267d5d855bf3eb26d48076e41938fc7729`; Stage 12 ZIP bundled unaltered in `SOURCES/`.

## Results, and what they mean

Current **working deduplicated bibliography = 14,972 identities**. Substantive Stage11 determinate results = **193 YES, 2,322 NO, 12,457 UNKNOWN**, or **2,515/14,972 = 16.7980% classification coverage**. NONE of these legal status assignments was newly promoted or altered. The true 1789–2026 all-history count remains unknown, so the 16.8% is neither a historical census completion fraction nor a survival rate.

**Three genuinely completed foundation checks:**

1. Located original **1,943**-record cohort CSV in persistent Library; compared real unique `canonical_id`s against **1,950** true Stage11 legacy flags; directly verified exactly **seven false-positive cohort flags**, zero missing originals. This previously inherited finding now has original source CSV, source hashes and deterministic `SCRIPTS/verify_original_cohort.py` proof.
2. Recovered **18 exact NARA dated *source-row labels*** for previously undated, already-counted unnumbered identities from the frozen Stage 10 importer. Three labels date to before 1862 (1849, 1852, 1856). Working identity proxies with no usable date decreased **118 → 100**; no legal status nor census membership changed. Keep original signed-date fields NULL until authenticated. Bibliographic month/day/year and actual document signing dates are not automatically equivalent. EO9761 expressly identifies and supersedes an order of President James K. Polk dated Feb. 9, 1849. The Feb. 26, 1852 date may refer to multiple distinct presidential acts; original-document crosswalk required.
3. Conducted and froze **eight** first-pass source-first legal reviews before checking Stage11 outcome key (SHA256 `d5ece5abbe4ab0b713921d498ef96a853971631a11ffa244809a32f4eab44234`). **Seven** independently supported the substantive Stage11 status; **one** (EO13286) was held. Subsequent and **explicitly post-key** independent source research identifies EO13286 §22, amending EO12978, and current 31 CFR §536.312 plus Sept. 30, 2026 official Federal Register authority referencing EO13286. EO13286 YES is supported. This is an eight-case diagnostic, not an estimated overall error rate. Most ancillary-effect questions still need deeper proof.

**Causation and attribution findings:** EO6877's original February 1, 1935 expiry was extended on that date by EO6955-A until 30 days after submission of the Board's report; first cessation remains unknown. EO12220 in June 1980 explicitly describes EO10746 and other revokee EOs as previously superseded at least *in part*: express final revocation is not their first-proven cause. EO14371's two-day 2025 closure is independently checked against original text as a spent substantive dated task, with ancillary-pay rights separately unclosed. EO8507 supersedes the August 8, 1914 public-water-reserve withdrawal only as to lands covered by the new withdrawal; the two same-date NARA rows may be duplicate representations and must not be automatically coded wholesale NO.

**Lord source work:** A better geometric extraction of the provided 1943 *Unnumbered Series* identifies **1,023 potential date-column month tokens**, of which 927 include a plausible day. Its OCR year heuristics proved unreliable; **all extracted years are intentionally NULL** and hints are stored separately as unverified. The leads are **NOT 1,023 executive orders** and none has been admitted. Need manual/document-level inspection and independent original sourcing before expanding the denominator.

## Status by period (source reference dates add a provisional historical layer)

| Period | Working entries | Determinate | Classification coverage |
|---|---:|---:|---:|
| 1789–1861 | 3 | 0 | 0.0% |
| 1862–1906 | 617 | 14 | 2.27% |
| 1907–1936 | 7,311 | 641 | 8.77% |
| 1937–1989 | 5,204 | 1,414 | 27.17% |
| 1990–2026 | 1,737 | 445 | 25.62% |
| Undated | 100 | 1 | 1.0% |

Where the date comes only from the old NARA table, it is a **source reference date**, not authenticated signing date. The pre-1862 row is particularly nonrepresentative. The 2020s include only 2020–October 14 2026.

## Recommended immediate execution gates

- Finish the **60-case independently blind** review from Stage12. The eight completed were a small diagnostic subset; do not compute a national legal error rate from them. Add a source-document/signature check to each validation.
- Independently authenticate a stratified subset of Lord's >1,500 unnumbered catalog entries; extract more document-based identifiers, especially 1789–1862 and 1862–1936, and handle second-hand references separately.
- Resolve possible same-date duplicates of Aug. 8, 1914, and distinct same-date Fillmore orders Feb. 26, 1852. Authenticate EO3016C/K/N signatures and differentiate delegated statutory action from direct presidential instrument.
- Build first-cause **operative episode** timelines, starting with EO6877 and other bounded-ended/revoked orders, and preserve evidence for original automatic expiry vs later-amended condition vs statutory/judicial action.
- Select and publish the primary **legal-effect attribution estimand** only after adversarial TC07/TC09 sensitivity and specialist review; do not rewrite codebook 2.0.0 or alter existing accepted status prematurely.

## How to verify

Use `SCRIPTS/verify_original_cohort.py` with the included `SOURCES/EO_Original_1943_Status_Queue_2026-10-14.csv` and original Stage11 ledger (inside bundled Stage12 frozen release). Use `SCRIPTS/build_source_date_overlay.py` with the included frozen Stage12 normalized JSONL and the previously saved Stage10 disposition-import zip in Library. For the Lord PDF, run `SCRIPTS/geometry_lord_candidates.py` with the PDF in Library, verifying its SHA256 `0553dd2318903af8fd4cdbb56140cd035f3bac52ec5420148307206940ab69e1`. `SCRIPTS/verify_stage13.py` checks structure, source links, sample and no legal decision mutations. No claim is made that all 60 legal reviews or all 30 identity certifications were completed.

**External sources and adverse cases:** `LEGAL/PROVISION_LEVEL_FALSIFICATION_FINDINGS.md`, `CENSUS/IDENTITY_COLLISION_RISK_REGISTER.csv`, `LEGAL/CAUSE_TIMELINE_INDEPENDENT_EVIDENCE.csv`, and `LEGAL/TC07_TC09_ALTERNATIVE_OUTCOME_PANEL.csv`.
