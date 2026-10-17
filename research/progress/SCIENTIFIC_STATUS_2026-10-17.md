# Scientific validity audit — 2026-10-17

**Scope:** inspect the released Stage 17 SQLite and the complete Opus Stage 11 Git LFS package published at commit `50d5be3`. This audit changes no legal determination. Cutoff remains October 14, 2026, America/New_York.

## What holds up

- The project still distinguishes bibliographic candidates, authenticated instruments, provision-level operative histories, current status, first cessation, and human certification. The Stage 17 database retains raw Stage 11 rows and the v2 and v3 research layers. It has explicit source, event, episode, transition, review, and conflict tables. The provision/event architecture is appropriate for the stated all-history objective.
- The two complementary search routes remain necessary: start at an original order to find an endogenous sunset, and start at a later legal source to discover earlier affected orders. The EO 10084 amendment chain demonstrates why the first printed sunset cannot be assumed to end the whole instrument. A formal revocation does not establish that the target was still operative immediately before it.
- The complete Opus archive can be retrieved from GitHub and is an additive overlay: 844 accepted cases include the interim 540 already in Stage 17 with identical verdicts and 304 further cases. All 597 in the earlier Opus ZIP retain their verdicts. Its 26,741 included files matched manifest hashes, after resolving seven ZIP filename encoding aliases. See [`OPUS_COMPLETE_RECONCILIATION.json`](OPUS_COMPLETE_RECONCILIATION.json).

## Current threats to inference

1. **Denominator:** The 14,972 identities are a working bibliography. The early census is extremely thin (3 included before 1862, 617 in 1862–1906). Twenty-five percent of this bibliography is not 25% of all issued orders, nor 25% of the historical or causal work. The Office of the Federal Register's [disposition tables](https://www.archives.gov/federal-register/executive-orders/disposition) begin in 1937; NARA's [Record Group 11 guide](https://www.archives.gov/research/guide-fed-records/groups/011.html) identifies executive-order originals from 1862, leaving earlier presidential directives to be reconciled across dispersed collections.
2. **Label validity:** The complete Opus release's 844 accepted labels are AI producer/reviewer results. Its `STAGE11_STATUS_RECORDS.jsonl` leaves historical causes unknown for all 844. The ZIP manifest lists 496 PDF/image files omitted for a separately named 359 MB original-media companion; that companion has not been verified or uploaded here. Stage 17's 540 interim imports likewise lacked their claimed original-image companion. These records must not be described as independently source-certified or as proved first-cessation histories.
3. **Causal completeness:** Among 3,359 reconciled provisional YES/NO cases, only 14 have a linked Stage 16 or 17 structured scoped episode/provision record; 3,345 lack that structure. A legal-event reference alone may denote a formal amendment or revocation and does not prove whole-order first cessation. This audit found 13 Stage 17 scoped prospective first-sunset assertions and no production human reviews. Some raw legacy and Opus records contain narrative information not normalized into the newer tables; the CSV identifies the structured gap rather than declaring those narratives nonexistent.
4. **Source retention:** Fourteen of 15 Stage 17 source records do not hold local original bytes; the fifteenth is a scanned historical index page, not an original signed presidential order. Text transcriptions and official metadata are useful leads, but the strongest evidentiary claims need exact source images or authoritative public reproductions, retrieval metadata, and clause-level citation.
5. **Mixed ontologies:** The complete Opus results use codebook 2.0.0; Stage 16/17 v3 assessments distinguish normative effect, enduring consequences, formal disposition, and policy continuity. A v2 YES/NO cannot silently override a v3 hold. In particular, the existing cautions for EO 9616, EO 12446, EO 13286, EO 14129, EO 14133, and EO 14371 require preservation.
6. **Accuracy:** No production human review has occurred. The research cannot report a representative legal error rate or population-level confidence from AI agreement alone. The planned 120-case sample is useful only after blind, independent review and resolution of nonresponse and source gaps.

**Limited independent source spot check:** The official [August 14, 2026 Federal Register PDF](https://www.govinfo.gov/content/pkg/FR-2026-08-14/pdf/2026-16630.pdf) does contain OPM's instruction to remove paragraphs (a)–(c) of 5 CFR 6.8 and cites [EO 14410](https://www.govinfo.gov/app/details/DCPD-202600378/). This supports the existence of the later source cited in Opus's EO 11887/12021/11839 discussion. This spot check did **not** establish the rule's eventual effective status, trace each older order's complete clause lineage, or certify their first cessation.

## Required data for each decision

The existing labels remain **provisional** until the following fields are checked rather than inferred: document identity and presidential capacity; original or accurately graded substitute; complete clause footprint (or a sufficient surviving YES predicate); provision-to-event links; mechanism (original expiration, performance, supersession, express revocation, statute, judicial action, nonactivation, or another evidenced category); effective date or bounded interval; earlier-intervention search; savings and accrued consequences; contrary evidence; source hashes and locations; codebook version; reviewer grade; and independent human disposition. Unknown is an acceptable recorded value. The project must not fill missing fields with a story that evidence does not support.

**First-cessation rule:** a later revocation proves a formal disposition at that later time if the source is authentic and scope is established. It does not, without earlier-history research, prove the first time a clause ceased to operate. A sunset in the original text is likewise subject to extensions, amendments, savings, and nonactivation.

## How to reproduce this audit

Restore the public database with [`research/releases/restore_releases.py`](../releases/restore_releases.py), then run:

```text
python research/progress/build_decision_completeness.py PATH_TO_STAGE17.sqlite
python research/progress/reconcile_opus_complete.py PATH_TO_STAGE17.sqlite releases/opus_stage11_complete/OPUS_STAGE11_FINITE_STATUS_DELTA_COMPLETE.zip releases/opus_stage11/OPUS_STAGE11_FINITE_STATUS_DELTA.zip
```

The scripts check expected source SHA-256 values and fail if core counts or the Opus overlap differ. Their outputs are the [3,359-case reconciled CSV](DECIDED_CASE_COMPLETENESS_RECONCILED.csv), [canonical completeness summary](DECISION_COMPLETENESS_SUMMARY_STAGE17.json), [complete Opus reconciliation](OPUS_COMPLETE_RECONCILIATION.json), and [304-case integration queue](OPUS_COMPLETE_304_PENDING_CANONICAL_INTEGRATION.csv). The outputs inventory recorded fields; they are not new legal opinions.
