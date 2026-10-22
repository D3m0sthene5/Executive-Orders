# Ranger variable-plan repair: offline replay, 2026-10-22

## Scope and method

Run 39666192712 exposed the historical `23`-response assertion in reparse after Scout produced 24 successful LOC response records. This replay validates the four repaired stages without publishing research outputs or making network requests. Scout attempts and Lord input were hydrated from bot commit `640279c84d99c9eeb34681e77ab49e23c99f5093`; other held metadata and image inputs are pinned below.

The replay blocked socket connections. Reparse consumed only cache files referenced by the actual attempts and checked their decompressed SHA-256 values. Its output fed triage; triage output fed the original-items plan. For original-items, a replay adapter supplied each requested item’s held gzip metadata after verifying its SHA-256 against PRIMARY_ITEM_METADATA.jsonl; the stage then wrote fresh scratch packets and Lord crosswalk results. Full-pages consumed those regenerated packets. Its adapter supplied held page bytes only after verifying the existing custody hash; the normal JPEG validation then ran. This validates transformations and held evidence reuse, not current network availability.

## Results

| Stage | Actual replay result |
| --- | --- |
| Reparse | 24 preserved LOC responses; 77 result rows; 65 unique canonical LOC item/resource links |
| Triage | 65 candidates; 6 priority directive-title leads; 14 within-term correspondence leads |
| Original-items | 21 distinct planned items; 21 held metadata packets processed; 0 failed, skipped, or deferred; request budget 22 |
| Full-pages | Three explicit manuscript targets; page counts 3/3/4; 10 verified JPEGs; 3,406,378 bytes; no historical count drift |

No EO identity, inclusion, legal effect, or human review was promoted. Original-items reported zero same-date Lord OCR matches on this input. Scratch outputs live outside the repository under `work/ranger-replay-20261022/`; they are validation artifacts, not acquisition output publication.

## Regression and independent review

All 11 new tests passed with network connections blocked: four reparse, two triage, two original-items, and three full-pages tests. Coverage includes 24 successful responses, valid empty result catalogs versus no successful responses, duplicate request IDs, custody mismatch, bounded decompression, complete unique 1789–1861 coverage, variable lead counts, deduplicated fixed follow-ups, 22-request deferral with preserved leads, truthful planned/attempted reporting, changed page counts, missing metadata, page bounds, and rejection of unapproved URLs before prefetch.

A separate swarm agent reviewed the patch and reran the tests. Its reporting finding (plans were described as requests even when deferred) was fixed and regression-tested. Full-page count drift remains explicit in JSON metrics and the human-facing report; it does not authenticate sequence completeness.

## Input pins

| Input | SHA-256 |
| --- | --- |
| `jobs/early-ranger-scout/output/LIVE_SEARCH_ATTEMPTS.jsonl` | `6aa7b857cf9cb33009f85112160fc83ffc842d7c667ba86cc881174fc5513252` |
| `research/stage20/output/ARCHIVAL_COVERAGE_GRID.csv` | `cd0afadbefd52012f1f6a96ce4418412d1e3219f7ccdc8216fb5ead21d6dfdf1` |
| `research/stage18/data/EARLY_SOURCE_CANDIDATES.csv` | `a9e0a0ea0265bed41356dec913a95a598181e8ae82ae2d0fba894c17a7169a09` |
| `research/stage14/LORD/LORD_CHRONOLOGICAL_REVIEW_LEADS.csv` | `7303bed0ca9f337353edac22a69c891b2cc47a9403a7c65d9024bc9e456ebfca` |
| `jobs/early-ranger-original-items/output/PRIMARY_ITEM_METADATA.jsonl` | `cc59246149b2ae56101b1f9c51cc030c7f28d4269898af072cb54adf7c9276bb` |
| `jobs/early-ranger-full-pages/output/PAGE_IMAGE_CUSTODY.csv` | `95335ab0b8d11f7c2b3663cd0843394ab4051592f0b610f95aef05c2bdf6be66` |

## Replay output summaries

- `reparse/REPARSE_SUMMARY.json`: SHA-256 `d415de0a6d0af389e84ec81a45a117688106d8ca788347119c42522c7a73d7f3`
- `triage/TRIAGE_SUMMARY.json`: SHA-256 `fa492384ae8ecda2696825deb3158d57f5d40a1603aa185317145679de87ee34`
- `original-items/METRICS.json`: SHA-256 `c20eec2416ab6a5ba3a89d4ea41b775001dce1f902876151816278db17a73780`
- `full-pages/PAGE_IMAGE_METRICS.json`: SHA-256 `60aed4cb654321facb9fa7d994b47470aedcf4a2dab13150ce5df6f9ff61b6c4`
