# Stage 1 bulk-evidence report

Historical cutoff: **October 14, 2026, America/New_York**. This bounded run is complete, with acquisition gaps and interpretive questions explicitly carried forward. It produced a merged evidence release; it did not adjudicate national legal-force totals.

## Result

The observed inventory increased from **5,670 to 14,925 identities**, adding **9,255** after suffix normalization and overlap reconciliation. These include provisional records extracted from a historical index. They are not 14,925 independently authenticated, separate presidential instruments: the index includes documentary groupings, uncertain numbering and metadata requiring review.

The release contains **37,669 new observations**, each with an exact quotation present in its stored representation: 36,815 official editorial observations, 846 primary-direct-coded observations, and eight research/editorial-coding observations. One primary-direct-coded observation is supported only by an explicitly incomplete official search representation. Quotations matching bytes does not establish the truth or completeness of their propositions.

There are **24,778 directed observation rows**, grouped into **10,903 relation candidates** while retaining every supporting observation. These numbers include different provisions, repeated editorial notes and historical actions. They are not unique ended orders. Source classes, scope and provisional review flags remain attached.

The original ledger, its **2,086 earlier event rows**, **346 latest observations**, and **58 inherited dependency inferences** are preserved in the identical original handoff. The fixed **1,943-member cohort still has 1,798 unresolved outcomes under its inherited rule**, which includes the reopened scope cases EO10480 and EO12364. Stage1 assigned no new final legal statuses and did not change the inherited outcomes.

## What actually ran

Ten delegated instances were launched: four acquisition pilots continued their finite shards, two additional evidence workers, and four audit instances. One audit instance failed because GPT-6.1 Sol was at capacity; its replacement and the modern audit requested GPT-6 Sol/high. Nine instances performed work. Peak delegated concurrency was six, or seven including the coordinator, matching the platform limit. No nested agents were used.

The other workers requested GPT-6.1 Sol/high, with isolated contexts. The tool accepted these requested configurations, but actual internal serving details, token usage and dollar costs were not exposed. No dollar cap is claimed. The prior-turn read-only handoff review is separately noted and was not a Stage1 execution worker. All assignments are closed. Per-worker calls and finite HTTP manifests are retained; no paid API, deployment or publication was used.

## Coverage and counts

| Acquisition family | Inventory evidence rows | Unique raw IDs in family | Verified observation rows |
|---|---:|---:|---:|
| dependencies | 4 | 4 | 23 |
| early | 8,461 | 8,461 | 7 |
| historical | 4,226 | 4,226 | 12,957 |
| modern | 11,960 | 6,938 | 23,843 |
| primary_controls | 440 | 440 | 839 |
| replication | 0 | 0 | 0 |

Family counts overlap; they must not be summed into unique instruments. The early raw-ID count precedes separator normalization. `merged/comparative_coverage.json` reports inherited and new evidence separately by source host and signing era, preserving the different units.

| Signing-era field | Inherited inventory | Enriched observed inventory |
|---|---:|---:|
| pre_1937 | 0 | 7,931 |
| 1937_1989 | 0 | 5,203 |
| 1990_2026 | 13 | 1,737 |
| date_unknown | 5,657 | 54 |

The inherited ledger's main signing-date field was mostly blank. This table therefore shows metadata enrichment as well as inventory expansion; it does not imply that almost every inherited order lacked a historically knowable date. Thirty-seven conflicting date observations remain in `identity_conflicts.jsonl`.

**Historical official tables:** all 18 linked NARA numerical tables were acquired as raw HTML and parsed. They contain 4,226 rows against the inherited 4,225 IDs. The source repeats an identical August8,1914 row twice; both source rows are retained, without merging solely on date. Eighteen unnumbered source-row identifiers await crosswalk to legacy IDs. All status annotations stay dated January20,1989. After repair, the shard contains 6,911 directed relations and 6,046 complete editorial annotations. Unsupported grammar remains in its residual-candidate file.

**Modern official collections:** the global Federal Register export returned 6,939 records across seven verified pages: 6,938 EO identities and one correction. Sixteen administration collections supplied 6,937 raw records; their date boundaries excluded two anomalously dated records recovered through the global export. NARA annual-page closure found 91 explicitly linked URLs: 66 acquired, 25 unavailable. Six heading-less first-entry fragments and 1,874 records without disposition notes were conserved. Absence of notes produces no active-status inference.

Three acquisition defects were documented: a nominal10,000-record UI export yielded only20 records; a global signing-date filter suppressed historical records; and source metadata duplicated EO10571 where the second record represented10571A. Explicit pagination, the exact unfiltered global export and a historical codification row supplied the respective controls. Source-date conflicts for EOs8969 and10276 remain visible. The 25 annual-page failures are genuine coverage gaps despite overlapping Federal Register evidence.

**Early index:** the complete695-page Lord1944 V1 PDF yielded8,461 provisional identities from8,450 source entries. A cleaner PDF text layer replaced heavily corrupted OCR as the extraction basis. The full source was processed; a slot count was never substituted for enumerated records. Seventy-two ambiguous/unmatched labels,22 redirects and six document groups are preserved. Eight numeric hyphen suffixes were visually checked; fractional OCR variants remain candidates. Alphabetic separator aliases retain original spellings. V2 is a subject index, not the unnumbered-series volume. Comprehensive unnumbered inventory remains missing.

**Primary controls:** ten HTML sources and three official PDFs support839 observations. EO12553's386 unique targets exactly match the inherited list. Formal revocation is separated from its collective recital; no earlier cessation dates are inferred. Savings and transition qualifications for EOs12919,13637,13318,13830 and14173 remain explicit.

**Dependencies:** six full official payloads and two incomplete search representations produced23 observations and57 child review paths for parents6910,11888,12163 and1888. Continuing or residual authority was investigated alongside cessation. No child was automatically closed. USCode access failures and missing child-provision comparisons remain open.

**Academic replication:** the article and part of its rendered supplement were acquired. Harvard dataset/API and original supplement access failed. No replication data files, version, license or row-level replication inventory were acquired. Seven methods excerpts and the study's stated scope are saved separately from legal observations. The article's stated population and coding cannot supply this project's denominator.

## Audit and repairs

The initial handoff check passed283 files,16 original artifacts and255 extracted members. A working-copy reproduction passed all40 inherited tests and reproduced six core outputs byte-for-byte. A fresh extraction of the portable release also rebuilt all17 merged outputs with identical hashes, using only Python and no network.

The predeclared audit seed was20261014. Historical audit sampled24 directed positives across all18 tables plus12 negative/residual cells. Modern audit sampled24 directed positives plus12 no-action/unparsed rows. The combined audit checked all386 EO12553 targets,12 non-list controls, the selected savings clauses, and30 early identities spanning suffixes, page thirds and all six document groups. These samples are checks of extraction, not estimates of national legal status or proof of all early identities.

Systematic review found and repaired20 historical false relations:14 cases matching “continued” inside “discontinued,” and six actions against offices/agencies/positions misattributed to the EO. Full annotations and removed observations are preserved. Modern repairs addressed clause bleed, false self-relations, a null document-number join, and2,001 row locators that previously pointed to earlier identical text. Independent post-repair checks cleared the modern locator, quote, hash and pagination failures. Source-date fields were separated from the research cutoff; four PDF corroborating spans retain page furniture with explicit formatting notes.

Final merge checks conserve every old ID and cohort member; retain both reopened cases; verify337 unique referenced source/text paths; validate all37,669 quotation links; preserve aliases; and quarantine no quote failures. Fifteen opposing-direction review pairs and ten apparent inherited timeline tensions are retained for chronology/scope review. An earlier revocation followed by reinstatement is not itself a contradiction. No inherited legal conclusion was conclusively overturned in this stage.

## Ranked Stage2 work

1. **Identity reconciliation:** review72 early candidates,22 redirects, six document groups,19 merger-held unnumbered/source-row identities,37 date conflicts and25 reference-only IDs. Complete the unnumbered-series acquisition. Maintain numbering suffixes and source-specific aliases.
2. **Acquisition gaps:** resolve25 unavailable NARA annual pages where useful beyond overlapping FR metadata; acquire the replication dataset/codebook and complete supplement; obtain inaccessible USCode/child texts and missing early primary instruments. Do not reacquire completed corpora without a concrete defect.
3. **Parser and evidence review:** process historical residual grammar, six modern heading-less fragments and scope/date details not encoded by editorial notes. Audit samples leave unexamined records provisional.
4. **Substantive legal adjudication:** evaluate continuing substantive rules, dormant authority, durable designations, residual provisions, completion, sunsets, later intervention and revival; resolve high-impact savings and57 dependency paths. Source evidence must support each scope determination.
5. **Methodological decisions:** design the final multidimensional taxonomy, instrument/document-group counting rule, denominator and explicit uncertainty protocol. Review prior research before novelty claims. None was finalized in Stage1.
6. **Publication tasks:** prepare final analyses, article and any formalization only after those decisions. This release contains no national percentages, blog draft, dashboard or Lean module.

## Resume and verification

Unzip `EO_STAGE1_BULK_RESULTS.zip`, open its top folder, and run:

```sh
python stage1/scripts/rebuild.py
```

This needs Python3.9+ and no network. It restores byte-deduplicated files and the identical inherited archive, checks the file manifest, rebuilds the merged outputs from saved shard records, and compares their hashes. The individual raw-source parsers and audit reproduction scripts are also included; some optional PDF re-extraction scripts use Poppler/PyMuPDF. The default rebuild needs only the standard library.

`STAGE2_INPUT.json` names exact paths, hashes, schemas, completed source clusters and review decisions. It is a factual handoff, not a second execution prompt. Source-specific access and rights information is in `SOURCE_ATTRIBUTION.md` and each source record.
