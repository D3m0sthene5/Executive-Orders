# Stage 15 — Issue-by-issue methodological closure audit and repair

**The Afterlife of Executive Orders.** Historical legal cutoff: **October 14, 2026 (America/New_York)**. Run date: October 16, 2026. This is a **reversible research overlay**. Stage 11's frozen 15,010-row ledger and Stage 14's source graph have not been edited; the controlling substantive codebook 2.0.0 and all inherited legal statuses remain unchanged.

## Result in one paragraph

The earlier work did **not** resolve all the foundational critiques. Stage 15 systematically decomposed the user's original numbered critiques **1, 2, 3, 5, 6, and 7** (the user pasted no item 4) into **36 separately tracked requirements**, implemented reusable guards or data representations where the available evidence permits, and retained explicit unresolved conditions wherever legal or historical research is still necessary. The most consequential discovery is a **loss of 513 already-parsed National Archives successor references** in the Stage 14 research graph. Stage 15 reconstructed 512 as valid-chronology **candidate** references, quarantined one retrospective chronological contradiction, and rebuilt the candidate feed. Separately, Stage 14's single escaped backward amendment edge is now suppressed. None of these candidate references is promoted to a present legal status or a historical cause of cessation.

## Measured results, directly reproduced from inputs

| Measure | Current value | What it does and does not mean |
|---|---:|---|
| Stage 11 preserved rows | 15,010 | Frozen original record count, including excluded/provisional |
| Stage 11 bibliographically included | 14,973 | Original inclusion denominator; not all actual historical presidential orders |
| Stage 14 deduplicated working identities | 14,972 | Document **proxies**, not certified physical signed originals |
| Substantive YES/NO/UNKNOWN among 14,972 | 193 / 2,322 / 12,457 | Unchanged inherited research conclusions |
| Determinate substantive coverage | 2,515 / 14,972 = 16.7980% | Model-reviewed classification coverage only |
| NOs with any populated cessation mechanism | 106 / 2,322 | Some populated entries remain bounds, not first causes |
| NOs with populated first cessation date | 99 / 2,322 | Only **68** are exact `YYYY-MM-DD`-formatted **candidates**, not independently verified legal dates |
| Determinate YES/NO orders with zero `operative_episodes` | **1,868 / 2,515** | A serious provision-reconstruction/structured-evidence gap; may exist in narrative notes |
| Lord unnumbered catalog | **over 1,500** catalogued entries by 1943 per compiler | User supplied original PDF; not exhaustively authenticated or admitted |
| Stage 14 extracted Lord date markers | 1,023 | Machine date-column tokens, not distinct EO documents |
| Source relationship edges in Stage 14 | 6,692 total / 6,575 not quarantined | Original candidate graph, not actual legally established relations |
| Stage 15 previously escaped reversed edge | 1 | EO 13257 (2002) cannot amend EO 13333 (2004); newly suppressed |
| Stage 14 missing NARA successor leads | **513** | Original NARA observation notes already contain the later named actor |
| Newly recovered NARA candidate links after chronology check | **512** | New discovery leads only, not proven full predecessor cessations |
| Stage 15 candidate relationship feed | **7,086** | 6,574 surviving old +512 recovered leads; status unchanged |
| Stage 15 representative *planned* probability sample | 120 unique proxies | Sample identities drawn and weights documented; **not yet reviewed** |

### Confirmed infrastructure flaw with disproportionate leverage

The original Stage 14 SQL graph omitted 513 `successor_candidates` embedded in existing NARA observations, including **45 EO 3461 predecessor references** that the research engine should have exposed automatically. Of the 513, one would point from a supposed older actor to a later target; it remains quarantined. The other 512 are now included in `AUDIT/CHRONOLOGY_AND_COMPLETENESS_GATED_RELATION_FEED.csv` with source observation IDs, editorial statements, exact source-file checksums and no status-promotion authority. **The cached source texts already contained much of the research material**: this was an extraction/integration failure, not an inability to retrieve hundreds of new documents.

The recovered refs touch **303 distinct current-UNKNOWN identities** and **191 NO identities**. Their value is cross-document discovery. Some catalog relations are only partial revocations, terminal-date bounds or administrative changes. EO 12553's historical primary revocation schedule was previously independently enumerated as 386 distinct targets; discrepancies with editorial tables remain quarantined for scope review. A larger set of links from different editorial sources is not proof that the official schedule contained more items.

### Exact critiques, in the requested order of feasibility

1. **Easy: separate and certify accounting, data representations, and descriptive progress.** `CENSUS/POPULATION_ESTIMANDS.json` distinguishes bibliography, deduplicated documentary proxies, authenticated physical originals (unknown), and all historical orders actually issued (unknown). The original FR bulk export has 6,938 labels but 6,937 distinct working proxies. Under **44 U.S.C. § 1505** the statutory publication regime excludes categories of EOs, so no method may equate a FR-only extraction to every order issued. `CAUSAL/INDEPENDENT_PROGRESS_METRICS.json` keeps cause progress separate from substantive status coverage.
2. **Easy: repair false/missing dependency links before further individual research.** `SCRIPTS/recover_missing_nara_successors.py` repairs the 513 omitted references; `SCRIPTS/build_verified_edge_feed.py` suppresses the reverse-dated edge that escaped Stage 14. No old records are overwritten. These guards prevent project agents from silently building arguments on source-graph artifacts.
3. **Easy-to-medium: impose legal-quality failure gates at scale.** `SCRIPTS/legal_gate.py` blocks a NO if the whole original footprint or qualified whole endpoint is not documented, an amender's host chain is unresolved, saved rights and residuals are unexamined, or later amendments remain unchecked. It separately blocks first-cause claims without a demonstrated earlier operative episode and properly ordered events. `LEGAL/SEVEN_SHARED_FAILURE_MODES.csv` enumerates all seven specifically requested shared errors; `LEGAL/CONSERVATIVE_RISK_SCREEN_NO_ORDERS.csv` identifies possible vulnerable records, without changing any acceptance.
4. **Medium: document the Chemical Foundation authorship split.** EO 3016C and 3016K match Polk orders dated Feb. 26 and Apr. 5, 1919 in *United States v. Chemical Foundation, Inc.*, 272 U.S. 1 (1926), following Wilson's 1918-12-03 delegation. EO 3016N has a different named transferee and **cannot** be attributed to Polk on the basis of that opinion alone. All three physical signatures still need original-image confirmation. Their numbered bibliographic identities are preserved.
5. **Medium: separate complete legal histories from whole-order labels.** `LEGAL/OPERATIONAL_STATE_CODEBOOK_DRAFT.json` adds explicit states for ever operative, never activated, hortatory, invalid at inception, dormant, revived, effective date, and first cause; it also distinguishes present normative operations from lasting consequences. Six example operative clauses have been reconstructed as **provisional demonstrations**, not a full conversion of the 14,972-record ledger. This draft does not supersede legal codebook 2.0.0.
6. **Medium: create a valid statistical starting point.** `STATISTICS/STRATIFIED_POPULATION_SAMPLE_120_BLIND.csv` draws reproducibly from **all** currently included working proxies, including UNKNOWN, in period × source-class strata. Inclusion probabilities and design weights are available; the Stage 11 status answer is in a separate file. The previous 60-case sample of determinate cases can be used for diagnostic misclassification, but cannot estimate survival in the full population.
7. **Hard, still open: finish a defensible historical census.** The Lord unnumbered volume contains far more material than 19 NARA source rows; 1,023 OCR date leads do **not** cover all catalog entries. A source-row-to-signed-document crosswalk remains unbuilt. Even Lord explicitly regarded his catalogue as incomplete; no exact all-history issued count is currently supportable. Registration of the PDF is an acquisition improvement, not a census solution.
8. **Hard, still open: choose doctrinal legal-effect attribution.** TC07 spent repeals, TC09 surviving host amendments, TC06 durable land status, saved rights, and executed property transfers still require broader substantive legal comparison and specialist review. The new schema makes alternative questions answerable; it does not establish which is correct or calculate universal sensitivities.
9. **Hard, still open: reconstruct first cessation and perform legal validity audit.** The present ledger has 2,216 NO cases with an unknown cessation mechanism; 2,223 lack the first date. This cannot be repaired from historical revocation annotations alone. The representative 120-case sample and diagnostic screening queue need independent source-first adjudication. No causation estimate or human-validated classification error rate has yet been produced.

## Sources for selected independently checked legal links

- [44 U.S.C. § 1505](https://uscode.house.gov/view.xhtml?edition=prelim&num=0&req=granuleid%3AUSC-prelim-title44-section1505): mandatory publication exceptions.
- [*United States v. Chemical Foundation*, 272 U.S. 1 (1926)](https://supreme.justia.com/cases/federal/us/272/1/): Wilson's Dec. 3, 1918 delegation and Polk's Feb. 26/Apr. 5, 1919 orders; this does **not** authenticate EO 3016N.
- [EO 3461 source text](https://en.wikisource.org/wiki/Executive_Order_3461): names EO 2596 and EO 2602 in the 1921 wartime civil-service revocation list and saves incumbent status in defined circumstances.
- [EO 2596 1917 original text transcription](https://www.presidency.ucsb.edu/documents/executive-order-2596-allowing-treasury-department-employees-be-appointed-defense): specific exception to EO 9.
- [EO 11408 1968 source text](https://www.presidency.ucsb.edu/documents/executive-order-11408-revoking-executive-order-no-9-january-17-1873-and-amendatory-orders): 1968 cancellation **insofar as** earlier orders construed or amended EO 9. For EO 2596, 1921/1968 events need distinct causal treatment.
- [National Archives historical codification guidance](https://www.archives.gov/federal-register/codification/numeric.html): 1989 editorial snapshot and scope exclusions.
- Clifford L. Lord, *List and Index of Presidential Executive Orders (Unnumbered Series), 1789–1941* (1943), user-provided scan, original checksum in `CENSUS/LORD_ACQUISITION_QA.json`.

## Release map

- `AUDIT/COMPLETE_ISSUE_CLOSURE_MATRIX.csv`: **36 acceptance checks**, each with evidence and remaining closure work. **Read this first.**
- `AUDIT/EO_STAGE15_SCHEMA_AND_RISK_SIDECAR.sqlite`: normalized identities, special signatures, six example operative clauses, 118 edge guards, requirement registry, and 8,000+ risk flags, with no Stage 11 mutations.
- `AUDIT/RECOVERED_MISSING_NARA_SUCCESSOR_CANDIDATES.csv`: exact source-backed 513 recovered references with chronological classification.
- `AUDIT/CHRONOLOGY_AND_COMPLETENESS_GATED_RELATION_FEED.csv`: **7,086** usable candidate edges, and distinct source labels for recovered annotations.
- `AUDIT/REBUILT_HIGH_LEVERAGE_ENDING_SOURCE_QUEUE.csv`: 803 source-centered clusters, with anti-overgeneralization instructions; not a status list.
- `LEGAL/OPERATIONAL_STATE_CODEBOOK_DRAFT.json`, `LEGAL/SEEDED_OPERATIVE_EPISODE_EXAMPLES.csv`: future legal modeling.
- `STATISTICS/STRATIFIED_POPULATION_SAMPLE_120_BLIND.csv`, `STATISTICS/SEALED_POPULATION_SAMPLE_BASELINE_120.csv`, and `STATISTICS/SURVIVAL_ANALYSIS_PROTOCOL.md`: sampling and inference prerequisites.
- `CAUSAL/INDEPENDENT_PROGRESS_METRICS.json`, `CAUSAL/NO_ORDERS_EVIDENCE_COMPLETENESS.csv`: accurate first-cause progress.
- `SCRIPTS/build_stage15.py`, `SCRIPTS/build_verified_edge_feed.py`, `SCRIPTS/recover_missing_nara_successors.py`, `SCRIPTS/legal_gate.py`, `SCRIPTS/verify_stage15.py`, `TESTS/test_legal_gate.py`: code and executable guards.

## Reproduction

Use the exact Stage 11 ledger from `EO_STAGE11_RECONCILED_EXECUTION_PACKET_2026-10-16.zip`; Stage 14 SQLite graph and Lord leads from `EO_STAGE14_LEVERAGE_ENGINE_2026-10-16.zip`. The original releases remain available in Library. Unzip them into a working tree equivalent to `/mnt/data/eo_stage15_workspace/` or configure environment variables: `EO_STAGE15_OUTPUT_DIR`, `EO_STAGE15_INPUT_ROOT`, `EO_STAGE11_LEDGER`, `EO_STAGE14_GRAPH`, and `EO_STAGE14_LORD_LEADS`. Run:

```bash
python SCRIPTS/build_stage15.py
python SCRIPTS/build_verified_edge_feed.py
python SCRIPTS/recover_missing_nara_successors.py
python SCRIPTS/verify_stage15.py
python -m unittest discover -s TESTS -v
```

The verification script tests immutable input hashes where available, cross-record arithmetic, nonleakage of sealed status answers, issue register completeness, and candidate-edge policy. Passing means **structural integrity only**. Stage 11 ledger SHA256: `c0308e008cd719cd153ca667271c93267d5d855bf3eb26d48076e41938fc7729`. Stage 14 SQLite SHA256: `41310b46f97712b28fcb7fd00e5ab5d38770c225fa57f5c10e5c9836738af55b`. Lord PDF SHA256: `0553dd2318903af8fd4cdbb56140cd035f3bac52ec5420148307206940ab69e1`.

**Remaining methodological uncertainty is intentional and visible.** A reliable conclusion that the user-specified critique is fully resolved requires historical source authentication, whole-operative-scope legal review, and independently evaluated causal dates—not merely a new parser or data schema.