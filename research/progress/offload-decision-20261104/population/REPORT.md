# Remaining population and bounded exact-span example

The remaining-work eligibility denominator is **not established**. The defensible starting census is 12,963 unfinished orders after excluding all 1,218 protected planned orders and seven additional unfinished published reservations. Within that ceiling, 114 orders have an existing claim. Four intentionally selected published versions on those order identities demonstrate real repeated exact-source spans, but do not establish that their latest canonical versions are eligible for production reuse.

Main remains pinned to `600ae3018f71025b3e53dc8538b8f92e6e159b76`; the protected published plan is pinned to `cacfb8f4af6db949476bd7bec8220a464055c931`. The checker/tracker generation is Nov 2, not a live assignment or source-access census. The complete protected plan is read solely for exclusion; its IDs are not republished here. Its sorted membership digest is in `POPULATION.json`, and the exact plan source/blob/SHA256 is in `SOURCE_HASHES.json`.

## Structural ceilings and their overlap

| Predicate on unfinished native rows | Before exclusions | Protected overlap | Additional reserved overlap | Remaining ceiling |
|---|---:|---:|---:|---:|
| All unfinished | 14,188 | 1,218 | 7 | 12,963 |
| Text check done/provisional/n/a | 7,960 | 1,218 | 7 | 6,735 |
| Original-supported evidence tier | 6,410 | 990 | 7 | 5,413 |
| Transcription-dependent evidence tier | 1,551 | 228 | 0 | 1,323 |
| Existing claim present | 114 | 0 | 0 | 114 |
| Shared-source check applicable | 234 | 24 | 0 | 210 |
| Shared-source check open | 27 | 0 | 0 | 27 |
| Opus-media check open | 714 | 0 | 0 | 714 |
| Text and clause inventory admitted | 68 | 0 | 0 | 68 |
| All listed checks admitted | 1 | 0 | 0 | 1 |

Each row is a unique-order predicate, not an eligible version, document or source-load count. Counts overlap. Of 210 shared-source-applicable remaining orders, 204 also have an open Opus-media check; 26 of the 27 open shared-source rows also have that media opening. Only two shared-source-applicable orders have a filed claim, and only one of those has an open shared-source step. Thus 210 cannot serve as an additional disjoint source-reuse queue. `remaining_intersections` retains the exact matrix.

The 6,735 text-admitted ceiling includes provisional text, and the evidence-tier predicate differs from the step predicate. There are 1,323 transcription-dependent rows but only 1,322 pass the text check. A text/check admission says nothing about source applicability, complete clauses or remaining legal review. The sole all-checks-admitted row, EO 14139, still records `unresolved_material_gaps`; it is not an observed filing opportunity.

Reservation exclusion is conservative and does not infer that the records are active. Unpublished assignments can further shrink availability. No vacancy or current phase is inferred from old reservations, plans or quiet publication surfaces.

## Historical outcome join cannot fill the remaining denominator

| Published historical unit | Whole retained cohort | Overlap after both exclusions |
|---|---:|---:|
| Completion memberships | 508 | 119 |
| Distinct completion order identities | 444 | 117 |
| Completion non-null order/version pairs | 313 | 0 |
| Genuine review versions | 358 | 2 |
| Distinct genuine reviewed orders | 300 | 2 |

All 119 remaining completion memberships are blocked and carry no exact claim hash; both remaining reviewed versions are rejected. Historical protected overlap is 41 completion order identities and 12 reviewed order identities, all excluded. Null-hash blocked memberships are not invented versions. The two rejected versions are not a successful reuse denominator.

The 306 published completion-version observations in the historical baseline are a different, largely completed scope. They cannot be multiplied into future remaining-work savings. Exact source documents and duplicate context loads for the 12,963 ceiling or the 114 claim-present orders remain unknown. An exact GitHub read of `jobs/claim-checker/output/PER_CLAIM.json` returned only blob metadata (`5a02cceddba050b54bd38d1a344455e91ceb8bfe`) and empty content. Startup case bundles carry older draft pointers, not proof of current selected claim versions. Full latest-claim selection plus source/custody closure would be needed to audit all 114.

## Four exact published versions give a positive mechanical example

The bounded source sample comprises EO 10622, 11040, 11078 and 9922, from exact main-pinned Mansfield b02/b03 claim files. All four order identities are unfinished, unprotected and unreserved, and all retain an open source audit. They share the held EO 12553 text, SHA256 `6361bdc557b6acaeae6e6908cded18f4f8fef9fde1a97cc11fb7c12c8cdea761`.

| Exact sample unit | Count |
|---|---:|
| Orders / published claim versions examined | 4 / 4 |
| Target text documents | 1 |
| Reference occurrences to that text | 14 |
| Distinct complete source dictionaries | 4 |
| Distinct exact text-hash/offset/quote spans | 2 |
| Exact span/quote matches | 14 of 14 |

Three orders repeat characters 691–966; EO 9922 repeats the complete 33,227-character text. Grouping the exact text check can retain all 14 independent reference dispositions, including distinct evidence metadata, while reading the text once and comparing two unique spans within one invocation. It does not merge the four complete source dictionaries or their case-specific meaning.

This sample verifies a narrow byte/span predicate, not full source custody. The raw PDF SHA256 is retained, but its bytes were not verified here. Original-page examination, source identity/grade, correct clause extraction, earlier ending, savings and legal applicability stay with the ordinary verifier and reviewers. EO 10622 illustrates the difference: its common quote matches while its native row still has a clause-inventory failure and source-audit hold. Neither this sample nor its dictionary projection establishes the latest selected canonical version. No result is generalized to the other 110 claim-present order identities or to the remaining ceiling.

## Local grouping probe and its limits

`span_probe.py` compares the same 14 full-reference dispositions with three strategies. Exact warm-filesystem timing distributions are retained in `SPAN_PROBE.json`; timings are descriptive and will vary:

| Experimental predicate strategy | Text reads / hashes | Span comparisons | Dispositions |
|---|---:|---:|---:|
| Naive per occurrence | 14 / 14 | 14 | 14 |
| Competent per claim | 4 / 4 | 4 | 14 |
| Grouped within the four-claim invocation | 1 / 1 | 2 | 14 |

Each strategy has 200 local trials. The separately measured common setup verifies pins, parses all three retained claim files and selects the 14 references. This overhead is larger than the submillisecond median predicate differences in the recorded run. Grouped output preserves per-occurrence source dictionary hashes and exact field pointers. Nine controls preserve equal results: unchanged bytes pass; changed bytes, non-UTF8 changed bytes and truncation refuse all 14; an altered quote and an out-of-range span each refuse exactly one; a boolean offset after a cached integer span is refused; a zero-width empty quote is refused; a previously successful invocation does not mask later truncation. Span-comparison counts are instrumented calls, not hardcoded estimates. The cache is invocation-scoped.

Independent review rejected the first isolated prototype for three actual edge defects: bool/integer cache-key aliasing could approve an invalid offset, zero-width empty spans passed, and changed non-UTF8 bytes decoded before hash refusal. The revised prototype validates strict nonempty typed spans/quotes before cache lookup and verifies the byte digest before decoding. These failures and their targeted corrections remain recorded in `SPAN_PROBE.json`. No native gate was changed.

Review also demonstrated a real boundary counterexample: if the source mutates between per-reference reads, fresh checking refuses the second reference while pooled checking reuses the previously loaded snapshot. The two strategies are **not equivalent for mutable source paths**. The probe preserves that failed equivalence. Any future grouping must first establish an immutable pinned byte snapshot and unchanged predicate policy; this experiment does not establish that native production already admits that contract. Until then the grouped prototype is not an eligible replacement for native checking.

These are prototype predicates, not the native full checker. Exact PR135 review found that `blind_verify.verify_files` calls its source check per reference, while providing the existing mechanical-verification boundary. A native implementation could consider grouping immutable byte/span predicates behind that boundary, retaining all per-card identity/grade/custody checks. This experiment does not establish that ordinary research sent these 14 references in a single invocation, that actual model/tool calls would disappear, or that independent reviewers can share source approval. Fresh independent source access remains necessary. There is no measured token, cash, labor, readiness or campaign-wall saving.

## Reproduction and publication

Run from the repository root:

```sh
python3 -I research/progress/offload-decision-20261104/population/build_population.py
python3 -I research/progress/offload-decision-20261104/population/span_probe.py
```

The builder verifies pinned census, sanitized historical outcomes, all 14 retained baseline sources and four exact example inputs before replacing outputs. `VALIDATION.json` records byte-identical clean regeneration and refusal of altered exact text while keeping the last good outputs. Both scripts write only in this population directory. Example inputs are read from ignored `.source-cache/`; missing inputs must be materialized by supported exact-ref file reads using `SOURCE_HASHES.json`. Raw inputs and their complete source content must not be published from this directory.

Publication allowlist: `.gitignore`, `build_population.py`, `span_probe.py`, `POPULATION.json`, `SOURCE_HASHES.json`, `SPAN_PROBE.json`, `VALIDATION.json`, `REPORT.md`, `COSTS.json`, `KEAN_FINDING.json`. No commits, remote writes, job dispatch, source acquisition run, scientific edits, protected packet/checkpoint mutation or assignment were made. Root owns shared Kean/handoff integration.
