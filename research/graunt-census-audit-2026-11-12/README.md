# Graunt: census audit of every U.S. executive order (Astra, 2026-11-12)

Named for John Graunt, whose *Bills of Mortality* (1662) first counted a population from scattered parish records and
said plainly which parts of the count were known and which were guessed.

An owner-commissioned Astra (ChatGPT, maximum effort) audit of the question "how many executive orders have presidents
signed, 1789 to the 2026-10-14 cutoff, and which ones?" It started from the census
(`research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv`, 14,998 rows, SHA-256 `facfb05b...`) and did not modify
the repository. Kean F-20261112-graunt-census-audit; owner decision D-20261112-graunt-adopted.

## Results

| Quantity | Value | Kind |
|---|---:|---|
| Numbered catalog labels | 15,009 | counted: 14,979 census rows + 24 missing whole numbers + 5 missing suffix entries + EO 1-A alias |
| Numbered presidential-directive proxies | 14,995 | counted under provisional grouping (Cleveland clause groups, EO 27/27-1, Seward certifications EO 6 and 7 excluded) |
| Unnumbered identified proxies | 1,816 (1,405 without 411 inferred power-site groups) | counted, each individually sourced |
| **Identified inventory** | **16,811 (16,400-16,811)** | counted; an evidence-rule range, not a statistical interval |
| All orders ever issued | no defensible finite estimate | the lost and never-catalogued tail is not identified by any data |

The 24 missing whole numbers are not unused: EO 36-49, 51-53, 92, 2103, 2539, 2703, 3493, 3733 and 6585 all have
documentary support. The missing suffix entries are 130A, 2687A, 5151A, 7010F and 8606A.

## Files

| File | What it is |
|---|---|
| `REPORT.html` | The audit's report: definition, era table, reconciliation, unpublished orders, estimators. |
| `EO_census_audit.xlsx` | The workbook (sheets Count, Findings, Corrections, Unpublished, Source review, Estimates, Methods). |
| `EO_reconciled_inventory.csv` | 16,879 rows: the census baseline plus every accepted new proxy, with `count_weight`. |
| `FINDINGS.csv` | Findings sheet as CSV: 3,820 sourced rows, 1,817 with Add count 1. |
| `CORRECTIONS.csv` | 78 census rows to correct or review (4 change the count by -1; 62 supply blank dates). |
| `UNPUBLISHED.csv` | 394 unpublished or not-received numbered orders 1937-1968, all already in the census. |
| `SOURCE_REVIEW.csv` | 30 source entries that should not be added (cross-references, source errors). |
| `POPULATION_ESTIMANDS.json` | The updated estimands for reporting; the archived Stage 15 file stays byte-identical. |
| `SHA256SUMS.txt` | Hashes of the three delivered files as received. |

## Checked by Claude before adoption (2026-11-12)

- The baseline hash Astra reports matches the census file on main.
- The 24 missing whole numbers it lists are exactly the integers 1..14435 absent from the census.
- The two questioned unnumbered rows exist: the 1863-03-10 Lord 1944 instrument and the duplicated 1914-08-08 pair.
- EO 14435 is the census's last order; EO 14436 (2026-10-16) is correctly outside the cutoff.
- The four new whole numbers 2103, 2703, 3493 and 3733 cite GPO printings on govinfo; 2539 an Alaska State Library copy.
- EO 25's corrected date (1886-11-18) agrees with Chester Arthur's death; EO 6 and 7 are Secretary Seward's
  Fourteenth Amendment certifications.
- Of 1,817 counted additions (Lord 908, power-site date groups 475, Richardson 306, TR Library 105, numbered 18,
  Federal Register 5), only two same-day Lord pairs (1888-11-01, 1912-04-19) look like possible duplicates; the
  EO 38/43/47 group is the documented Cleveland grouping.

## What this changes and what it does not

- **Changes the project's understanding:** the numbered series is nearly complete (29 labels short); the unnumbered
  series has at least 1,405-1,816 individually sourced identities; no finite estimate of all orders ever issued is
  defensible. The domesday-register Chapman interval (about 4,100-5,100) is a model output whose two lists are not
  independent (Lord compiled from the same Richardson, military-reservation and land-office sources), not a national
  estimate; it is no longer presented as one.
- **Does not change, until the owner rules:** the numbered census the tracker counts (14,998 rows), any readiness
  count, or the 0 human-certified count. Admitting the 29 numbered labels, applying the 78 corrections and seeding
  `catalogued_unnumbered` from these identities are the open asks A-20261112-graunt-admit-numbered,
  A-20261112-graunt-corrections and A-20261112-graunt-unnumbered-seed.
- A catalogue entry identifies an order; it does not authenticate one. Every row keeps the codebook distinction between
  historical document discovery and identity authentication.

## Next, from the audit

A document-level inventory of NARA RG 49 (General Land Office executive orders and proclamations), then Interior, War,
Navy and Treasury approval records; for a missing-population estimate, an archival sampling frame stratified by era
and agency.
