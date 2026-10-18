# Source gaps in the saved local pilot packets

The 50 saved producer sheets contain 10 provisional approvals and 40 unable outcomes. This audit describes the deliberately partial local packets, not remaining defects in the full-corpus run 39106221293. Reconfirm each gap against its frozen replacement dossier before doing further work.

`SOURCES_NEEDED.jsonl` contains 93 deduplicated tasks. Each task names affected orders, a concrete objective, availability, next action, and decision-file hashes/fingerprints. Categories overlap across orders; task counts are not distinct-order counts.

| Task category | Tasks |
| --- | ---: |
| actual implementation or completion | 6 |
| actual report submission receipt or termination | 14 |
| current law exact spans | 24 |
| earlier amendment or actor context | 26 |
| earlier statutory or administrative change | 3 |
| implementation schedule | 1 |
| local hydration artifact | 3 |
| original image confirmation | 12 |
| indexed original byte custody verification | 4 |

All 21 literal unlocated actor IDs (23 target/actor links) already have indexed FR originals and local texts. Five additional prose-only amendment references bring the context tasks to 26, all local. These are packet/context checks. EO10480 and EO10647 are indexed but unhydrated here; the complete EO14008 overflow appendix is local. No acquisition request was added for those texts.

Current-law tasks group the exact already recorded original witnesses, not duplicate snippets. Recover the current-law cache/runner artifacts and extract attributed operative spans. The bulk U.S. Code witness stops at 2026-10-09; coverage of 2026-10-10 through 2026-10-14 remains a distinct currency question. A missing top-level hash on a draft wrapper does not prove that the nested source or held original lacks a hash.

16 deduplicated official-witness requests (12 image confirmations and 4 actual-checker custody verifications) were appended to `research/readiness/FETCH_QUEUE.jsonl`, preserving all 80 original rows byte-for-byte. Each uses the exact previously indexed official URL and hash, requests cache reuse first, and distinguishes downloaded custody from image confirmation. No matching image request was present in the existing queue or 147 source-ladder source records. Local absence of image bytes is not a claim of repository absence.

24 tasks need actual report/receipt/implementation facts or specifically identified earlier legal authority. Their locations were not established by the saved packets. No verified URL was identified for these new facts, so they remain concrete gap tasks rather than guessed fetch requests. Deadlines, outer limits and later cleanup revocations do not establish actual submission or performance dates.

Reproduction: read only the 50 direct `producer-*/*.decision.json` sheets (exclude `rejected/`), their local-dossier fingerprints, `jobs/fr-originals/output/FRAGMENTS.jsonl`, and `jobs/current-law/output/SOURCES.jsonl`. Literal actor counts use `target provision not located: EO:<id>`; the five additional named actors are EO12855, EO13033, EO13034, EO12823 and EO12743. Current-law witnesses deduplicate `(source.url, source.sha256)`, reading both flat fragments and nested `proposal.source`. Queue prefix SHA-256 and the wire-new-sources Git blob SHA are recorded in the JSON summary.

The provisional strict assembler passes all 10 approved sheets. The actual offline checker passes 5 completely and returns `pass_with_unverified` for 5, with no failures. The remaining 64 record-only source references concern four already indexed PDFs: EO13138 (15 references, EO13050), EO13316 (7, EO13263), EO13345 (29, EO13028/EO13131), and EO13385 (13, EO13283). Exact official URLs, recorded original hashes and checker-file provenance are in the four custody tasks. Verify/recover those bytes; no new legal authority is implied. All results await reconfirmation against the full frozen dossier fingerprints.

No provisional statuses, claims, reviews or code were changed. No primary source was fetched manually.
