# Stage 5 present-status research release

**Project:** The Afterlife of Executive Orders. **Cutoff:** October 14, 2026, America/New_York.
**Contract:** EO-2026-10-14-PARALLEL-V1 / ASTRA-STAGE5. Legal codebook 2.0.0; inherited identity rules 3.0.0.

This release accepts **191 distinct present-status decisions** after internal independent review. On the fixed Stage4 validated population, it reduces substantive UNKNOWN by **179** and any-operative-effect UNKNOWN by **179**. These axes overlap and must not be added.

## Fixed-population results

| Axis | Status | Completed Stage4 | Stage5 | Change |
|---|---|---:|---:|---:|
| Substantive | YES | 151 | 191 | +40 |
| Substantive | NO | 1,103 | 1,242 | +139 |
| Substantive | INDETERMINATE | 13,719 | 13,540 | -179 |
| Any operative EO effect | YES | 151 | 203 | +52 |
| Any operative EO effect | NO | 1,024 | 1,151 | +127 |
| Any operative EO effect | INDETERMINATE | 13,798 | 13,619 | -179 |

The fixed cohort contains **14,973 validated instruments** before and after. There are **12 residual-only determinations** (substantive NO / any-effect YES), compared with 0 before. Gross accepted decisions: 191; accepted decisions reopening or reversing a previously determinate axis: 0. A correction to an unaccepted proposal is not counted as a reversal of an accepted finding.

Claude V1 remains 952 and V2 remains 151. V1 includes the 941 Stage3 validated-NO cases and 11 then-provisional NO cases; their later identity validation did not create new causal-workstream members. **V3 contains 139 new accepted substantive-NO cases** relative to completed Stage4, with zero overlap. Any-effect-only changes on prior-NO instruments do not enter V3. All seven inherited Claude-owned fields are preserved exactly.

## Identity and historical coverage

No identity promotions, additions, merges, exclusions or new instrument discoveries were accepted in Stage5. The population remains 14,973 validated plus 17 observed provisional document-group candidates: 14,990 observed identities. The ledger additionally preserves 17 excluded duplicate placeholders and three outside-union unresolved records, for 15,010 rows. Alias mapping rows are not additional instruments.

The validated population is the project inventory, not the number of executive orders ever signed. The separately catalogued unnumbered series, early coverage uncertainty, EO10807 and the inherited historical-source gaps remain limitations. Stage4 Lord validation was reused unchanged.

| Era, fixed validated cohort | Instruments | Substantive YES before → after | NO before → after | UNKNOWN before → after | Any YES / NO / UNKNOWN after |
|---|---:|---:|---:|---:|---:|
| 1937–1989 | 5,203 | 17 → 33 | 774 → 879 | 4412 → 4291 | 33 / 856 / 4314 |
| 1990–2026 | 1,735 | 133 → 157 | 249 → 275 | 1353 → 1303 | 169 / 209 / 1357 |
| pre1937 | 7,915 | 1 → 1 | 78 → 86 | 7836 → 7828 | 1 / 84 / 7830 |
| unknown | 120 | 0 → 0 | 2 → 2 | 118 → 118 | 0 / 2 / 118 |

Across the complete observed inventory, substantive YES / NO / UNKNOWN are 191 / 1242 / 13557; any-effect YES / NO / UNKNOWN are 203 / 1151 / 13636. Detailed counts by identity source criterion, evidence grade, era and population eligibility are in COVERAGE_AND_COUNTS.json.

## Method and production

The completed Stage4 release was verified before work began: 29 output bindings and the main archive plus 18 companion volumes matched recorded hashes. Its ledger was frozen at SHA-256 `fdcd0ff692798d90b27f18a6ea89a3f11d8cd524c289b0c41df8162d64b11313`. The reported Stage4 187 accepted decisions and 151-case V2 were checked against the actual files; Stage4’s prior 22-of-22 replay receipt was preserved, not misreported as a new Stage5 replay.

Code grouped the unresolved inventory by source, dependency, amendment chain, baseline and blocker. The engine scanned 10,903 relationship candidates, 37,669 original observations and cross-stage evidence stores; 2,712 overlapping routing groups are not classification counts. Only the 13,719 validated substantive-UNKNOWN members were initially eligible for new substantive determinations. Seventy-nine prior substantive-NO cases had unresolved any-effect status and were routed separately. The 37 unvalidated preserved rows were kept out of validated production.

Workers used shared primary controls, full target footprints where needed, bounded subsequent-change checks, actual report completion evidence and current operative provisions. No legal standard or national denominator was loosened to increase output. Primary transcripts, historical scans, current official compilations and retrospective sources retain their source date, retrieval provenance, limits and exact quotation locators. Later documentation is used for facts at the cutoff, not post-cutoff legal changes.

New retained source records contain 233 distinct raw byte representations (248,144,001 bytes) across 233 recorded source URLs, in addition to reused prior-stage evidence. These include derived primary excerpts and are not HTTP request, instrument or classification counts. Every registered new raw path was present and matched its recorded hash. Detailed accounting is in audits/SOURCE_ACQUISITION_SUMMARY.json.

Largest individual accepted rule groups:

| Rule | Accepted instruments |
|---|---:|
| S5-CLOSURE-A-12553-P01-CLOSED-HOSTS | 14 |
| s5-closure_b-rule11708-mapped | 14 |
| s5-finite-annual-whole-supersession-v1 | 14 |
| S5-CLOSURE-A-P03-10480-WHOLE | 13 |
| s5-continuity-14354-current-mandates | 12 |
| s5-finite03-recent-records-residual-v1 | 12 |
| s5-finite-peb-template-v1 | 11 |
| s5-continuity-complete-footprint-controls | 10 |
| s5-finite03-records-unproved-old-v1 | 10 |
| s5-closure_b-rule11708-mapped-supplement04 | 9 |

The research includes current incorporated award/foreign-assistance provisions, mapped pay and civil-service amendments, whole defense-mobilization endpoints, annual-pay replacements, completed emergency boards, and separately evaluated records duties. BATCH_RULES.jsonl preserves exact member predicates, scope, exceptions and independent judgments. Original finite authority, a time limit on making appointments, and a time limit on the resulting appointment are treated separately.

## Audit findings and corrections

Every accepted proposal is bound to an independent review and immutable source/evidence snapshot. Shared saved-position rules were reviewed across their aggregate family, including the 25-member EO11708 family, rather than evading the 25-case gate by splitting packets. Source-first checks and deterministic samples accompany ordinary decisions; an additional 18-case unresolved sample covers three eras and identity-only/lifecycle-evidence strata. AI cross-review is internal quality control, not external scholarly peer review.

The final reviewer audit records 37 reviews, 99 reproducibly selected exact accepted proposal versions, and 639 source paths freshly rehashed. No final packet, source-hash or duplicate-acceptance errors remained.

- EO11252’s extra presidential-memorandum footprint blocked a proposed blanket closure. The original proposal and withdrawal remain visible.
- Three EO8379 targets were held because incorporated Consular Regulations provisions were not mapped. A coordinator challenge also prevented automatic acceptance of the historical 17-case list merely because its source/quote checks and peer recommendation passed. Sixteen remain held; a corrected EO4701 proposal separately maps its tariff provision to a complete replacement and distinguishes spent cancellation clauses. The original broad proposal and both peer opinions remain archived.
- Two saved-position names and one positive original-versus-current provision attribution required corrected immutable proposal versions. Earlier versions remain archived.
- Literal source membership, partial clauses and saved terms overrode editorial graph edges. A missing EO13549 continuation edge was recovered from the primary text. A truncated EO5417 abstract was recovered without rewriting the inherited corpus.
- Technical audit caught use of a mutable aggregate member-check file. The merger now derives checks from exact bound snapshots and review findings. It also verifies declared auxiliary hashes, rejects portable-path escapes and prevents historical diagnostic paths from pulling unrelated corpora into the package.
- The frozen 18-case unresolved sample was preserved without outcome-based resampling. Seventeen remain unresolved; EO14135 was subsequently resolved using its full original text and a whole-order endpoint. The final audit distinguishes that later decision from the sample outcome at its original checkpoint.
- EO13205/PEB235 did not issue the report named in its termination clause. Review therefore did not infer that the report trigger occurred: the preserved current substantive-NO baseline rests on the completed and settled dispute mandate, official closure, and the chair’s contemporaneous account. Its residual-records axis remains unknown; it is not a new Stage5 substantive decision or V3 case.

There are 211 unique instruments with a submitted Stage5 proposal, 244 preserved proposal versions, and 20 proposed instruments without an accepted Stage5 finding. These are not additive to accepted or queue counts. Pending, corrected and withdrawn versions are retained in PENDING_OR_REJECTED.jsonl and the producer/review packets.

## Remaining work and stopping point

The large remaining queue is dominated by missing operative text or a concrete dependency gap, not bibliographic identity uncertainty. Important blocked families include the selective-service saved regulations; EO11408 orders with additional non-EO9 provisions; EO3461’s missing controlling text and saved status; EO9521’s required published substitutions; old consular/diplomatic regulation versions; land designations needing parcel/authority continuity; EO13672’s incorporated host scope; older board-record custody; and specific committee termination or judicial qualifications. No age-based inference is used.

This run followed high-yield cached and cheaply obtainable source families, then checkpointed the less productive missing-source and disputed-scope tail. Family selection is not representative sampling. No national survival percentage, first-cause allocation, cleanup percentage or article is released.

Actual delegation: 6 worker launches, at most 6 simultaneous delegated workers plus the coordinator. Five requested gpt-6.1-sol/high configurations handled production and technical work; one gpt-6-astra/xhigh configuration led independent legal review. Two completed producers subsequently cross-reviewed unrelated families. No nested swarm or separately billed API was used. Exact billed token usage is not exposed and is not estimated.

## Reconstruction and download

Extract ASTRA_STAGE5_PRESENT_STATUS_DELTA.zip and run `python REPRODUCE_STAGE5.py` inside its directory. The package includes the frozen Stage4 comparison ledger, accepted review inputs, new evidence and the required immutable old-source subset. It does not need the original workspace paths or an internet connection for Stage5 reconstruction. The full preceding historical evidence remains in the named main Stage4 archive and 18 companion archives, with exact hashes in IMMUTABLE_STAGE4_COMPANIONS.json.

Final offline replay: **PASS**, 13 of 13 canonical outputs matched from 2009 sealed inputs. Network and subprocess operations were blocked; independent population, review, Claude-field and V3 invariants passed.

A second replay from a relocated directory also returned **PASS**, with 13 of 13 outputs identical. The portable resolver rejects unmapped original-host paths.

All worker research and review is completed or explicitly checkpointed before delivery. No background continuation is promised.
