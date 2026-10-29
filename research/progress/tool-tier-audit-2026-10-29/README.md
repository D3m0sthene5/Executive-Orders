# Production-file readiness association audit

Pinned repository: `D3m0sthene5/Executive-Orders`, commit `73d99f666573ee10f5b1ff2ada60f7d9331c3952`.

This is a read-only cross-tabulation of **already published artifacts**, not a new research, checker, or tracker run. It measures the number of currently ready orders associated with each producer's claim-file group. It does **not** estimate the number caused exclusively by a method, its marginal contribution, cost, accuracy, or human certification.

## Files and source fidelity

- `SOURCE_PINS.json`: exact commit, local input paths, file sizes, Git blob SHA-1s for all 67 claim files, and the tracker SHA-256.
- `CLAIM_READINESS_ASSOCIATIONS.csv`: all 510 physical claim lines, case identity, file, line, grouping, current tracker readiness, text tier, blockers, and deduplication flags.
- `CATEGORY_TOTALS.csv`: distinct-case counts by the named file groups; ready column sums to 395.
- `STATUS_READINESS_ASSOCIATIONS.csv`: the 15 Bowditch and 29 Sinclair adopted status rows and current readiness, kept apart from claim production credit.
- `RESULTS.json`: completeness/deduplication checks and historical/current qualifications.

All 67 claim files matched the pinned GitHub directory listing by Git blob SHA. The local tracker matched the pinned GitHub output-directory listing: blob `070dcf2bb0825e0fd0efac49faa2493b727bb8e8`, 2,374,558 bytes, SHA-256 `c7dd78d76ede3183fa337407d17b1a6e03812f64fd9010bb68335a380af86efb`.

The partial mirror's `jobs/claim-checker/output/PER_CLAIM.json` was found to be older than the three newest claim files. It was **not** used for the final partition. The current tracker and exact pinned claim files are the only substantive inputs.

Primary sources:
- [Current readiness CSV](https://github.com/D3m0sthene5/Executive-Orders/blob/73d99f666573ee10f5b1ff2ada60f7d9331c3952/jobs/readiness-tracker/output/READINESS_BY_ORDER.csv)
- [Claim directory](https://github.com/D3m0sthene5/Executive-Orders/tree/73d99f666573ee10f5b1ff2ada60f7d9331c3952/research/readiness/claims)

## Reproduction and grouping

1. Read the pinned readiness CSV keyed by `instrument_id`.
2. Read every nonblank JSON line in the 67 pinned claim files and take its `instrument_id`.
3. Assign each file to the explicitly named category. Lambertini includes `claude-lambertini-*`, `claude-viapar-*`, and `claude-pagechk3-*`. Rastell includes `claude-rastell-*`, `claude-r9830-*`, and `claude-r12553nb-*`. The other filename-to-category mappings are explicit in the associations CSV.
4. Count distinct `(category, instrument_id)` pairs with tracker `ready_for_human_review=yes`. Do not sum ready physical lines.
5. Check that no case belongs to multiple categories and that every one of the 395 ready tracker identities has a claim-file association.

**Only duplicate:** EO13306 appears at line 1 of both `astra-2026-10-17-p3originals.jsonl` and `astra-2026-10-18-p3complete.jsonl`. It is currently ready. Both files belong to **Astra Oct17-18 sprint**, so distinct category/case counting credits it once. The row flag `counted_category_case` marks the first lexicographic file/line solely to make summation reproducible; it does not select the governing scientific version.

The final set has 510 lines, 509 distinct claim identities, 395 ready identities, zero ready identities without a claim, and zero identities assigned to more than one category.

## Historical versus current results

**Spent-order probe:** the historical completion filed 15 claims and the contemporary report stated a 285→300 ready gain. On pinned current main only 13 of those 15 IDs are ready. EO1547 has working-text fragment identity/grade mismatches and failed text/claim steps; EO4782 has unresolved source/page verification and failed claim steps. These are current verification holds, **not established substantive legal rejections**. Preserve the historical result; do not silently treat it as current readiness. This audit adds no cost estimate. The later effort audit's 5.90 recorded worker-minutes per filed claim is a separate historical observation.

**Sinclair and Bowditch:** 15 adopted Bowditch status rows currently have zero ready histories. Of 29 adopted Sinclair status rows, EO10704 and EO13975 are currently ready; their full-lifecycle claims were later produced through the Codex continuous work. Status adoption and later lifecycle production share a case but must not receive additive ready credit. The status table is therefore separate from the 395 partition.

**Cumulative research:** the exact file grouping places EO9452 in `Astra cumulative` and EO11782 in `Astra source first`. The latter file was subsequently corrected by the cumulative-research work. The cumulative report properly describes two recovered/reconciled ready proposals. Do not infer that the original six-partial source-first run itself completed a ready history.

**Counterexample-first trial:** its report established two ready histories in its isolated replay; four of its five filed claims are ready on current main. EO8992 remains blocked by the EO6964 shared source and historical-media requirements. Current association does not prove the sequencing intervention caused these completions or saved time.

**Mansfield:** pinned main contains only the two b01 claim lines, neither currently ready. PR54 remains open and unmerged at head `d8613babe75bbee5ac6b46d9e756835a8d61c5ab`; its 14 branch-filed claims are a separate, qualified historical result, not 14 claims added to the canonical partition.

**Historical catalog:** the TOOLS snapshot's Lambertini “120+ ready” and Rastell “20+ ready” describe historical/cooperative contribution. They are not an exclusive current claim-file census. This exact cross-tab yields Lambertini 93/102 and Rastell 35/35; it should be labeled file association, not a correction of every historical contribution claim.

No tokens, dollars, savings, or exclusive causal attribution are inferred.

