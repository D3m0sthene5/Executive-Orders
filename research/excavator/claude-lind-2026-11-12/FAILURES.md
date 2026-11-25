# Lind stage 0: per-order failure table (2026-11-12)

Bounded diagnosis from the existing artifacts only. No new research was run.

**Sources** (all under `research/excavator/claude-lind-2026-11-12/` unless noted):
- `p1|p2/packet/DISPATCH_CHECK.json`;
- `ASSESSMENT.jsonl` (the producer's blocker, quoted below);
- the frozen `undecided/EO_N/EVIDENCE.json`;
- `overlay/EO_N/review-v1/STATUS_REVIEW.json`;
- `reviews/BLIND_REVIEW_[AB].jsonl` and `reviews/AFTER_REVEAL_[AB].jsonl`;
- `completion/complete-v1/EXCEPTIONS.json`;
- the actual claim checker re-run offline on the 7 assembled drafts (`CLAIMS.working.jsonl`), as completion runs it.

**Category codes:**
- **ME:** missing evidence (a needed source is not held).
- **CU:** custody (the source's text is held, but its bytes are not kept in a committed place).
- **FL:** a factual or legal error.
- **II:** an internal inconsistency.
- **IN:** an integration failure (a held source not routed into the dossier, a stale brief, or a tool artifact).

**When it was detectable:**
- **pre:** before producer work, from the frozen evidence and the dispatch check.
- **draft:** after drafting, before review, by an existing deterministic check.
- **review:** only by substantive, source-based review.

**Additional cost:** list-price dollars, estimated from this pilot's measured unit costs, or "unknown".
- A blind re-review set carries about $1.5-2.5 per arm of fixed overhead (this pilot: arms $1.98 and $2.70 for 7 claims plus the reveal).
- A producer correction costs about $0.3-0.5.

## Submitted claims (7; 6 in the all-gates group)

| Order (group) | Furthest stage | Category: exact reason | Detectable | Smallest corrective action | Work still valid | Additional cost |
|---|---|---|---|---|---|---|
| EO 12753 (all) | Upheld by both arms; failed the completion checker | **CU:** the ending source (APP page of EO 12791, sha256 576b4755…) is `custody_record_only`; bytes are not in a committed place | draft (offline checker; shown) | Cotton retains the exact Common Crawl bytes (hash already matches), then re-complete | Claim, status review and both blind reviews (the claim does not change) | about $0 tokens; runner; then one owner adoption |
| EO 12437 (hard) | Arms split (A rejected) | **II:** the rationale says a held-text search found no other citation, yet its previous sentence cites the held 42 U.S.C. 8373 note | review | Delete or correct that sentence, then re-review | Status review; the sole spent-on-issue reading (both arms agree on it) | correction about $0.3 plus re-review share |
| EO 11943 (all) | Arms split (B rejected) | **FL:** the savings reason says EO 12010's schedules took effect 1977-10-01; its sec. 3 applies that date only to uniformed services | review | Correct the effective-date sentence, then re-review | Status review; the spent-on-issue reading | as above |
| EO 13476 (all) | Both rejected | **II:** the rationale says 31 scopes where 34 are listed. A also found sec. 4(a)'s end date inconsistent with "done on issue". The offline checker flags 2 quotations too short to verify | draft (the short quotes); review (the rest) | Fix the count, the sec. 4(a) date and the two quotes; re-review | Status review; the sec. 4(d) sunset basis | correction about $0.5 plus re-review share |
| EO 12701 (all) | Both rejected | **FL:** EO 12334 is called the PFIAB order (it established the Intelligence Oversight Board), and that board is said to have been abolished. **CU:** two sources are `custody_record_only` (offline checker) | draft (CU); review (FL) | Correct the identity of EO 12334, retain both sources' bytes through Cotton, re-review | Status review (the PARENT_END basis) | correction plus Cotton plus re-review share |
| EO 11294 (all) | Arms split (A rejected) | **II/FL:** the reasoning says sec. 4 was one-time and done on issue (1966), but the clause table dates its end to the 1986 revocation. A's reading of ruling P2 on secs. 1 and 3 is a legal question | review | Reconsider each clause's first end under P2, then re-review | Status review; the EO 12561 revocation | unknown (legal reading) |
| EO 9447 (all; control) | Control caught by both arms; genuine version split after reveal (A rejected) | **FL:** the amending command is not treated as ended on issue (ruling P2). **IN:** the A-row ending quote cites the whole page file rather than the ending words. B noted the omitted EO 9583 | review | Narrow the quote, apply P2, add EO 9583, re-review | Status review; the EO 9744B supersession | unknown (legal reading) |

## Status accepted, lifecycle blocked (1)

| Order (group) | Furthest stage | Category: exact reason | Detectable | Smallest corrective action | Work still valid | Additional cost |
|---|---|---|---|---|---|---|
| EO 9739 (all) | Status NO accepted; lifecycle blocked | **ME:** "End of the saved applicability ('so long as necessary') for returns ordered before 1946-11-01 and incomplete then is not shown by any held source" | review | A held source for the end of the EO 9834 sec. 3 saving, or an owner ruling on the saved interval | Status decision and review | unknown (source) |

## Blocked by the producer (16)

| Order (group) | Category: exact reason (producer's words, shortened) | Detectable | Smallest corrective action | Additional cost |
|---|---|---|---|---|
| EO 12340 (all) | **IN:** "The ending instrument is held but not in the frozen dossier: EO 12473 … rescinds the Manual for Courts-Martial, 1969 … as amended by EO Nos. … 12340 …" | pre, in principle (a held text names the order); not caught by an existing check | Route the held EO 12473 text into the dossier (a reviewed ACT override), re-prepare, resume the producer | about $0.5 producer plus review share |
| EO 14103 (all) | **IN/ME:** "its current-law lead lacks an original-source sha256 and no uniquely located legal-text slice is held" | pre (the lead's missing hash is mechanical) | Current-law extract with a hash for the pointer | unknown |
| EO 10755 (hard) | **IN/ME:** the only TERM fragments "come from neighbouring documents on the same Federal Register issue"; no ending or CURRENT record | partly pre (fr-originals multi-document span; an open defect cluster) | Repair the fr-originals span; it still needs an ending source | unknown |
| EO 1957 (all) | **ME:** "revoking EO 2048 held only as a compilation OCR text". **IN:** also blocked on "ProQuest replica (acceptable_as_original false)", although the frozen original carries `working_text_basis` `tracker_original_supported`, which the F6 validator accepts. The Papinian route brief reused for this pilot predates F6 | pre (IN: the brief); ME needs a source | Correct the route brief before any next batch (the Papinian file is a historical record and stays unchanged); hold an official EO 2048 text | unknown |
| EO 4193 (hard) | **ME:** "no held ending or CURRENT record and no held text naming the order". **IN:** the same stale-brief replica block as EO 1957 | pre (IN) | As EO 1957 | unknown |
| EO 2898 (hard) | **ME:** "no held source shows a later notification, revocation or current statutory basis; the OFR catalog search does not reach 1918" | review | Hold a later notification or revocation | unknown |
| EO 4145 (hard) | **ME:** "no held source fixes the 1925 expiry date of any allotment, so the own-terms end is only a 1935 bound (an interval, not the exact date schema v1 needs)" | review | Hold the allotment expiry dates, or an owner ruling on interval ends under 2026-10-28 | unknown |
| EO 13650 (all) | **ME:** "No held ending record and no held evidence of performance of the dated tasks …; only CURRENT record is the 6 U.S.C. 621-629 note printing the text" | review | A current-predicate source (it may be YES) | unknown |
| EO 14274 (hard) | **ME:** "No held ending or CURRENT record … performance of section 2(c) and the continuing force of 2(d) … not shown" | review | A current source | unknown |
| EO 1538 (hard) | **ME:** "no held source shows what remained reserved on 2026-10-14", plus a page-image check owed (soft gate) | pre (page check); review (ME) | Page check plus land-status source | unknown |
| EO 7841 (hard) | **ME:** "Alaska Railroad Transfer Act (45 U.S.C. 1201 et seq.) and any public land order not held" | review | Statute text plus PLO | unknown |
| EO 8678 (hard) | **ME:** "later land transfers not held" | review | Land transfer records | unknown |
| EO 9481 (hard) | **ME:** "Secretary's determination and return of the mines not held" | review | Archival determination | unknown |
| EO 8877 (all) | **ME:** revoked only in part by four PLOs; "lacks a held acting-instrument text for PLO 5001"; actor texts are non-census leads | review | PLO 5001 text plus reviewed PLO identities | unknown |
| EO 9159 (all) | **ME:** "only extends EO 7126 … its life depends on the parent order, whose later status is not held" | review | Decide the parent EO 7126 first | unknown |

## Dispatch-blocked (7; assessment row only, no research)

All seven have a mandatory source not held:
- all gates: EO 12280, EO 4658;
- hard-only: EO 4475, 4621, 4788, 4861, 4968.

These were detected **pre**, as designed. They cost only an assessment row.

Smallest action: acquire the original (and the clause source).
- EO 12280 (1981) is likely a Federal Register PDF retention task.
- The pre-1937 ones need Film 709, HeinOnline page facts or an archive copy.

Additional cost: unknown, mostly acquisition.

## Totals by category

| Category | Orders | Notes |
|---|---:|---|
| ME | 22 | 7 dispatch-blocked plus 15 producer-blocked; mostly substantive source gaps, 14 in the hard-only group |
| CU | 2 | EO 12753 (the only both-upheld claim) and EO 12701 (also FL) |
| FL | 4 | EO 12701, 11943, 11294, 9447 |
| II | 3 | EO 12437, 13476, 11294 |
| IN | 5 | 12340 and 14103 (a held source not usable in the dossier), 10755 (tool artifact), 1957 and 4193 (stale brief; ME also present) |

Several orders carry more than one category.
