# STAGE 16 — Scientific reconstruction and source-prioritized research release

**Research project:** The Afterlife of Executive Orders  
**Legal cutoff:** 2026-10-14, America/New_York  
**Release:** Stage 16, codebook 3.0.0-research (legacy legal codebook 2.0.0 frozen)  
**Historical scope retained:** George Washington through October 14, 2026  
**Status:** Executable research checkpoint, **not** a complete historical census or an independently certified legal dataset.

## What was actually changed

This release is a versioned **canonical SQLite migration**, rather than a diagnostic sidecar. The database contains all 15,010 original Stage 11 records and SHA-256 fingerprints, 14,972 canonical working-document proxies, canonical bibliography and signer/delegation fields, 11,164 original-source observations, source-evaluated relationship candidates, 1,023 unnumbered-series Lord date-markers, 1,015 page-linked readable source context excerpts, original NARA date references, a multi-axis v3 legal-effect model, 21 provision episodes, 438 dated source-scoped events, 5 v3 case-assessment records, a 120-case probability sample, and named codebook/evidence guards.

1. **Rebuilt source graph directly from original observations.** The Stage 14/15 feeder had 513 omitted NARA 1989 successor candidates; 512 passed its chronology check. Source-schedule reconciliation then quarantined two additional conflicting EO 12553 editorial references (11920 and 12395). Exactly **7,084** candidates are available for research and **121** quarantined, including **510** usable recovered candidates. No relationship can be promoted directly to a legal determination.
2. **Integrated original-source event research.** The retained EO 12553 schedule yields 386 distinct named formal revocations dated February 25, 1986; EO 3461's 1921 civil-service revocation family supplies 45 predecessor references with incumbent-saving qualifications. These 431 references are represented as **formal historical events**, not 431 supported present-status NOs or first cessation causes. The 438-event total includes separately reconstructed examples.
3. **Separated legal operation, consequences, formal repeal, policy survival.** New codebook 3.0.0-research has a primary operative-norm/constitutive-status axis and a separate enduring-consequences axis, plus separate formal disposition and successor-policy fields. Source/host amendment attribution and residual limitations are explicit. The original 2.0.0 statuses remain unchanged.
4. **Reconstructed actual dated provisions, with limits.** The source text of EOs 14129, 14133, and 14371 establishes four distinct past office-closure dates and eight dated closure/essential-exception scope expirations. The pay/leave and implementation clauses remain unresolved. As a direct result of the legal gate, these **three whole-order assessments are held indeterminate**, despite the expired date-specific duties. EO 6877's originally scheduled sunset was replaced by EO 6955-A's report-based condition, whose performance date remains unverified. EO 8885's completed revocation is a provisional normative-NO under the primary TC07-style convention, while its enduring-consequences 2026 status is held.
5. **Added enforceable refusal rules.** SQL triggers reject (a) unsupported first-cessation promotion from later revocation references, (b) candidate-relationship legal promotion without scope review, (c) determinate v3 status insertion without linked, inspected source, and (d) sample verdicts lacking review attestations. Python status/cause rules require all-scope, savings, exercised-authority, residual, host-amendment and independent-review evidence. Seventeen positive/negative regression tests pass.
6. **Historical manuscript preparation.** Lord's full 1943 scanned catalogue was incorporated through its SHA-256 and 1,023 date-marker positions; 1,015 readable snippets were extracted from its existing OCR text layer, linked to exact PDF pages. Eight need visual transcription. Five matches to NARA unnumbered rows are DATE-ONLY hypotheses. Zero new manuscript identities were asserted and zero signatures falsely authenticated.
7. **Scientific sampling and dashboard.** The 120-case probability sample now resides in the working DB with its weights. None has completed independent source adjudication. The estimator refuses to calculate national legal survival or competing-risk curves. The HTML dashboard and decade histogram are generated from the same database and separate five types of progress.

## Actual numerical progress

| Research dimension | Current verified description |
|---|---|
| **All-history census** | 14,972 working documentary proxies; actual issued order count unknown; 1,023 extra historical date cues not yet authenticated |
| **Present legal status** | Stage11 legacy 193 YES / 2,322 NO / 12,457 UNKNOWN; 2,515 / 14,972 = 16.798% research-classification coverage, **not survival percentage** |
| **New v3 adjudications** | 1 first-pass whole normative NO, 4 held/indeterminate, **0 independently certified** |
| **Causal-history research** | 21 represented episodes, 8 provision-level exact expiration dates, 438 historical event records; **0 newly proved first WHOLE-order termination causes** |
| **Independent scientific validity** | 0 / 120 completed blind probability-sample legal reviews; no defensible error rate or whole-population estimate |
| **Reusable research capacity** | 11,164 source obs; 7,084 candidate relationship leads; 510 recovered usable; 1,015 readable original-volume excerpts; 17 code regression tests |

## Most important uncompleted requirements

- Historical census: acquire/reconcile full unnumbered physical manuscripts, not just index references; distinguish 1789–1862 order types and signer capacity. An exact national denominator is **not known**.
- Evidence: the original 15,010 ledger has 1,868 inherited YES/NO decisions without machine-readable operative episodes. All 2,515 inherited determinate classifications remain provisional, and the new source rules are not yet retroactive legal certification. No representative independent legal error rate exists.
- Legal ontology: v3 separates operative norms and durable consequences, but a population-wide attribution/sensitivity recode of TC06/TC07/TC09 remains undone; doctrinal review is outstanding.
- Causation: 2,216 of the 2,322 inherited substantive-NO records lack populated cause mechanism and 2,223 lack first-cessation dates; even populated values may be only latest bounds. Do not treat EO12553 or EO3461 formal revocation as first cause.
- Population inference: the 120 probability-sample decisions and operative histories have not been independently adjudicated, so **no national survival estimate or competing-risk curve** is justified. Right-censoring, never-operative orders, recurrent episodes, historical gaps and nonrandom adjudication all remain analysis constraints.
- EO12553 and EO3461 event families were processed for source-linked formal event evidence; independently verified predecessor whole-effect closures have **not** been completed. The directive's stronger requirement of one large family with legally verified whole-order status for every member therefore remains **unfulfilled**.
- EO 3016C/K's Polk attribution is inferred from the judicial decision and source descriptions; physical signatures remain unauthenticated. EO 3016N's signer remains unresolved.
- The existing evidence-vault caches from Stage14 were retained by their file hashes and source observations; 11 original Stage16 research URLs are declared, but most full document bytes were accessed through source reading and not locally acquired as originals. The Lord source PDF is locally available and preserved in Library.

## Exact contents and reproducible commands

`DATA/AFTERLIFE_STAGE16_CANONICAL.sqlite` is the canonical versioned release. Core code: `CODE/build_stage16.py`, `CODE/policy.py`, `CODE/estimators.py`, and `CODE/render_dashboard.py`. Source map: `SOURCES/CURATED_OFFICIAL_EVENTS.json`; archived original input copies: `PINNED_INPUTS/`; review export: `REPORTS/LORD_SOURCE_EXCERPTS_FOR_REVIEW.csv`; numeric build metrics: `REPORTS/VERIFIED_BUILD_METRICS.json`; changes: `REPORTS/ACTUAL_DATA_CHANGES.csv`; and issue dispositions: `REPORTS/ORIGINAL_CRITICISMS_5_AXIS_CLOSURE_MATRIX.csv` and `REPORTS/STAGE16_DIRECTIVE_COMPLIANCE.csv`.

The original 1943 Lord PDF scan is **not embedded in this ZIP** because it is preserved separately under `/Executive Order Research/Sources/Clifford_Lord_Unnumbered_Executive_Orders_1943.pdf` in your persistent Library. To reproduce after downloading the release, also materialize that original PDF into your local working directory and use its path for `STAGE16_LORD_PDF`. The build verifies the PDF SHA-256 against `0553dd2318903af8fd4cdbb56140cd035f3bac52ec5420148307206940ab69e1`.

```bash
# At the extracted Stage16 root (with sibling full PDF scan available):
export STAGE16_RELEASE_ROOT="$PWD"
export STAGE16_INPUT_ROOT="$PWD/PINNED_INPUTS"
export STAGE16_LORD_PDF="/path/to/Clifford_Lord_Unnumbered_Executive_Orders_1943.pdf"
python CODE/build_stage16.py
python -m unittest discover -s TESTS -p 'test*.py' -v
python CODE/render_dashboard.py
python CODE/estimators.py DATA/AFTERLIFE_STAGE16_CANONICAL.sqlite
```

**Clean independent rebuild: PASS.** Two separate isolated executions from the pinned inputs generated identical SQLite database SHA-256 **`0a8f4c6f734cfb7c77382426eced747e5dea31175587d86497803afb35036f64`**, identical metrics JSON SHA-256 `a586e1cd9e77904d9e021441e7c7bc885e32b22fe4880a5828511d36a116f3fc`, and identical 1,023-row original-volume excerpt CSV SHA-256 `0eb0ca5cd2fc7c3022cc9e6b50c4099284bfbbaa19f28351994a2480794d1ed5`.

## Research dependencies, in evidence-first order

1. **Original text and event-graph reconciliation:** exploit 510 recovered source candidates with primary text, starting with large clusters whose metadata conflicts have been quarantined; prevent duplicate or reversed edges in future imports. Reuse cached original representations and grade source limitations.
2. **High-fanout true legal-scope adjudication:** use the common source once (EO12553 and EO3461 included), establish original predecessor scope, amendment chains and saving clauses, then classify each member individually. NO only after whole-footprint closure; do not infer first historical cause from formal revocation.
3. **Historical documentary identity:** use the 1,015 extracted Lord context packets and page scans for authentication; add all new unique unnumbered instruments only after signer/date/document-level crosswalk, with grouped and date-only ambiguities retained.
4. **Independent blind 120-case probability audit:** retrieve independent originals, evaluate all provisions without seeing v2 statuses, document human/legal specialist or comparable genuinely independent source validation, then compute error by era/family/source strata.
5. **First-cessation episodes and causal inference:** construct legal operation from issuance to cutoff, including contingent nonoperation, rights, extensions, resurrection and statutory interventions; use uncertain dates/intervals and competing causes.
6. **Statistical survival analyses only after coverage and independent review:** stage a right-censored recurrent multi-state/competing-risk analysis with bounded population definitions; preserve all-history aims and incompleteness qualification.

## Sources

The original Stage11–15 archived inputs and user-uploaded 1943 Lord scan are preserved by SHA. Official and hosted EO 14129, 14133, 14371, 6877, 6955-A, 8885, 12220, 3461 and 12553 reference URLs and source limitations are in `SOURCES/CURATED_OFFICIAL_EVENTS.json` and the canonical `source_documents`/`source_evaluation` tables. EO 12553 full schedule is from a preserved text representation with a known SHA, not a newly acquired official image; government codification dispositions are contemporaneous editorial observations, not present-2026 legal opinions. All claims of scientific validity remain bounded by that distinction.

**Do not repeat past release mistakes.** Successful code, source ingestion, a recovered link, a reviewer packet, and a correctly worded legal rule are different kinds of progress from independently established substantive legal outcomes. This release verifies the former; the latter remain only partly established.
