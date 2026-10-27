# Production work and a measured preparation fix

This run advanced four selected unfinished histories in two convenience batches (EO8179/8300 and EO8705/8707), while tracing production, source handling, review, correction and integration. They are not a representative sample, a randomized comparison, or a campaign-wide hours estimate. Final filing and combined tracker results are recorded in FINAL_RESULTS.json; incomplete or held versions remain preserved.

## What actually became cheaper

Required native dossier preparation repeatedly hashed an entire prior-research JSONL file for every admitted record, including unrelated records. In the profiled preparation, 165,363 SHA calls consumed 197.006 of 209.106 seconds. The small fix computes each admitted file's full-content hash once per collection and reuses it; discovery, record selection, source pins and legal checks are unchanged. A regression checks both one hash per file and invalidation on a content edit.

The saved ordinary native preparation receipts are 109.2081 seconds before and 4.3402 seconds after: 104.8679 seconds, or 96.03%, less machine elapsed time for two dossiers. Decoded dossiers, held-text pins **and prior-research context compare exactly equal**. See NATIVE_PREPARE_COMPARISON.json, both pinned packets, and PRIOR_HASH_EQUIVALENCE.json. An independent reviewer reproduced exact frozen context equality in 2.590 seconds and inspected the old profile. These are observed machine timings on this checkout, not model token, active labor or campaign savings. The patch also makes subsequent native freshness checks cheaper when they call this collector.

The root and independent engineering checks passed 407 claim-kit tests and seven Stage19 tests, with zero skipped. Separate engineering review covered the source supplement, optional source notes, source-note URL coverage at the human gate, and hash fix. No codebook or legal admission rule was changed.

## What the production work taught us

The prior attempt used a manual export path for newly held source quotations. The next batch used an additive source-excerpt supplement around native prepare/view/apply/batch-check. It carries exact raw/text hashes and excerpts as explicitly unreviewed source material; it does not turn quotes into legal conclusions. Optional source_notes let producers retain qualified earlier versions and multiple saving provisions without inventing a precise event date. Ordinary decisions and clause CSVs, strict source checks, independent review, controls and native completion remain required.

This did **not** demonstrate a faster overall research path. Initial producer elapsed intervals were 1,106.512 seconds for batch1 and 1,391.013 for batch2. Initial export-related observations were about 272.8 and 437.443 seconds respectively; the latter includes decisions, apply, a failed checker, source-catalog repair, retry and audit. The cases and phase contents differ, so neither a speedup nor a causal slowdown is established by those numbers. Subsequent source review, correction, recovery and integration costs must be added, not hidden by comparing producer-only timings.

Independent review found two material unplanted omissions: EO8514's exception in the first batch and an April1946 CSC reinstatement amendment in the second. The latter required retaining a new primary source and correcting EO8707's treatment of the earlier rules. It has a March7 effective date distinct from its signing, filing and publication dates. A genuine incomplete-probation exception is separate from a six-month war-service conversion provision. Simple named-EO link scans had not supplied that full host-regulation history. This is direct evidence of a remaining expensive task: discovering and reviewing relevant agency-rule versions and exceptions beyond the named executive-order chain. It does not establish that every remaining order shares this bottleneck.

Two workspace resets added substantial reconstruction and re-review. Most code, claims and native artifacts had been committed before interruption; new historical attestations identify which original bytes were lost rather than pretending they survived. A coordinator recovery message also exposed the second control's identity before blind sealing. That attempt is explicitly **invalid/unscored**, with its cost retained. A fresh final source review and new undisclosed control are required; the invalid test is never converted into a catch.

## What this establishes about total hours

There is one proved recurring preparation saving and usable production output. There is no established reduction in total agent hours or tokens from this run. The collector fix removes about105 seconds per observed two-dossier ordinary prepare on the frozen workload; review, source discovery, correction and integration were much larger observed intervals. It would be misleading to turn a96% preparation reduction into a96% project reduction. Model tokens, cached tokens, billing and exclusive active labor are unavailable; overlapping worker and coordinator elapsed intervals are not summed as a measured labor total.

The next substantive acceleration test should target source discovery that caused actual rework here: reuse a pinned, complete provision/version/exception history of the shared civil-service rules across affected orders, with each order retaining its own scope and first-end judgment. The existing family grouping, source retention, claim-kit excerpts and source notes provide integration points. This run does not justify building another general accelerator or claiming a large campaign saving. A bounded production comparison would have to include independent review and all corrections, and demonstrate that this particular repeated discovery work disappears without missing the April-style exception.

## Evidence and cost accounting

- NATIVE_PREPARE_COMPARISON.json and PRIOR_HASH_EQUIVALENCE.json: exact preparation comparisons; before profile retained compressed.
- recovery/prior-hash-review/: independent engineering review, exact-context replay and seal.
- TESTS.final.json and test logs:407+7 passing checks.
- recovery/production-claims-v5/TIMING_RECOVERED_FACTS.json and recovery/recovered-production-review1/: original production, correction, source-review and first recovery observations.
- recovery/review-v5/COST.new-v6.json:354.707 seconds of additional exact-version recovery review.
- packet-b2-final-v8/producers/batch2/COST.v1.json:initial second production and export/checker intervals, including preserved failed check.
- recovery2/review2/:independent source findings, April hold, preserved review and recovery cost; the control attempt is invalid as recorded separately.
- recovery2/correction/:April primary-source correction research and recovery qualifications.
- Final corrected packet, final review, native completion receipts, FINAL_RESULTS.json and packet-b2-correction-v9/COST_LEDGER.json:exact versions, final outcomes and additional costs. These files determine what was actually filed.

AI source review is from separate OpenAI contexts. It is not human certification. No provisional legal statuses, canonical source-audit holds, census identities or codebook were adopted or rewritten. PR66 is stacked on unmerged PR65; neither PR was merged by this run.
