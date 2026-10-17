# Stage 17 — integrated source-linked research release

**Research cutoff:** 2026-10-14, America/New_York. **Release assembled:** 2026-10-17. **Status:** independently reproducible AI research; no human-certified legal conclusions.

## Actual migration

The release rebuilds from the actual Stage 16 and Opus Checkpoint 2 ZIPs using the independent Stage 17 bridge script. Checked SHA-256 values:

- Stage 16 original canonical SQLite: `0a8f4c6f734cfb7c77382426eced747e5dea31175587d86497803afb35036f64`.
- Stage 11 immutable JSONL: `c0308e008cd719cd153ca667271c93267d5d855bf3eb26d48076e41938fc7729`.
- Opus patched Stage 11 JSONL: `087e85b9e99afb6a77bc44f1a17ed707dd1b932cd338cf561893a62af53a03f6`.
- Stage 17 canonical SQLite, rebuilt independently and byte-identically: **`c362f5a8de7c31be2d1a700b00272aca9597136d74ff575fdc72ac24373984e1`**.

The integrated database retains the 15,010 raw Stage 11 entries, 14,972 counted working proxies, 11,164 source observations, 7,084 usable relation candidates and 121 quarantined candidates, 438 Stage 16 legal event records, 21 Stage 16 episodes, all five Stage 16 v3 assessments, and both earlier research codebooks. The Opus overlay imports all 540 new, previously UNKNOWN legacy-v2 decisions (75 YES, 465 NO), while preserving 531 held, 414 unprocessed, 155 conflicts, and 747 decision-state records. Nothing is promoted automatically to human confirmation or independent v3 certification.

**New provisional, deduplicated v2 totals: 268 YES, 2,787 NO, 11,917 UNKNOWN.** Research-classification coverage is 3,055 / 14,972 = **20.404756%**. This is not the historical national denominator, the survival rate, causal completeness, or publication-quality accuracy. The 540 Opus source packages lack their separately claimed original-image companion. This release explicitly grades each as AI-reviewed, independent original reinspection pending.

## New substantive research (not only an importer)

The new tables contain **15 curated source records, 13 source-linked provision histories, 26 dated legal transitions, 14 independent AI source-review assessments**, and **five newly verified printed-index catalogue candidates for 1789–1790** (not authenticated original instruments, and excluded from 14,972). There are **13 scoped first prospective normative sunset assertions**, supported by actual time-limiting text and referenced amendment sources. Those are not 13 newly demonstrated whole-order first-cessation dates nor independently human-certified causal holdings. New locally preserved signed original presidential EO images: **zero**. One indexed printed historical source (Lord) is locally scanned; the other 14 source records have inspected, publicly linked text but the signed image bytes are not locally retained.

### Family A: EO 10084, Career Compensation Act regulations (original-forward plus successor-backward)

Sources: Harry S. Truman Presidential Library institutional transcriptions for EOs 10084, 10098, 10118, 10136, 10158 and 10174; 1949–50 National Archives disposition table as secondary completeness check. The time-bound parent provision is divided into four statutory section groups:

| Parent EO 10084 grant / statutory coverage | Initially set to end | Scope-dependent documented successive amendments | Current prospective authorization ends (exclusive) |
|---|---|---|---|
| General adopted regulations outside specifically extended provisions | Jan. 31, 1950 | EO 10098 extended to Mar. 31 | Apr. 1, 1950 |
| Career Compensation Act §§ 201(e), 204, 501(d) | Jan. 31, 1950 | EOs 10098, 10118 and 10136 | Sep. 1, 1950 |
| Section 206 | Jan. 31, 1950 | EOs 10098, 10118, 10136 and 10158 | Nov. 1, 1950 |
| Section 302 | Jan. 31, 1950 | All five successive amenders, through EO 10174 | Feb. 1, 1951 |

These are precise **prospective operative windows** anchored to the quoted amending orders. They prove why using the original January 1950 expiration for all scopes would be wrong. Whether accrued benefits, incorporated earlier regulations or independent later authority make the parent/amenders substantively effective under competing TC07/TC09 conventions remains **held**. All six instruments receive Stage 17 research assessments of *indeterminate*, preserving the Opus legacy NO alongside the new legally narrower independent judgment. This is a discrepancy in evidentiary confidence, **not an established reversal of legal truth**. The NARA 1950 editor's metadata erroneously calls EO 10084 dated October 12, 1929 in the EO 10098 entry; the contemporaneous order is October 12, 1949. The source conflict is not silently erased.

### Family B: six annual acting-judge authorizations

EOs **10035, 10097, 10188, 10310, 10517, 10599** authorize specified Puerto Rico jurists to exercise a conditional acting federal-judicial authority solely during the stated calendar year (1949, 1950, 1951, 1952, 1954 and 1955). Official Federal Register text is linked for EOs 10035, 10097, 10599; published institutional transcriptions are linked for the others. Each instrument's single prospective grant expires at the first instant of the following January, irrespective of whether the beneficiary actually exercised that authority. The Stage 17 AI normative assessment is NO for these six; accrued validity of any judicial orders issued pursuant to those permissions is **not** adjudicated as a current EO-sourced command. The Stage 17 database records each legal clause, time-bounded end, cited original, rationale and strongest evidence gap. EO **10599 has conflicting source dates**: the American Presidency Project says March 14, 1955, while NARA disposition metadata says March 15. The conflict is recorded and does not affect the 1955 time-limit conclusion.

### Family C: two dated ceremonial directives

EO **9896** orders federal half-staff flag displays for October 10 and October 26, 1947. EO **11481** orders a half-staff display on September 11, 1969. All three discrete prospective commands have specified date bounds; none persists as an ongoing command in 2026 under the primary normative measure. These two instrument-level NO assessments and three provision sunsets are AI source-reviewed transcriptions, not human certification or locally authenticated signed originals.

**Existing legacy YES/NO determinations conclusively overturned by independent whole-order source review:** **0**. The six amendment-chain legacy NOs are now **v3 indeterminate** because broader attribution and original footprint questions remain; no false assurance of a definitively wrong legacy label is asserted.

## Historical census

Five previously absent 1789–1790 **catalogue candidate rows**, visually confirmed from page 23 of the actual 1943 Lord scanned volume, are now queryable with date, description and older manuscript/publication citations. On August 28, 1790 Lord lists two different descriptions for a proposed fourteen-million-dollar borrowing transaction; identity multiplicity cannot be determined without original sources, so both remain uncounted. Other Lord OCR markers remain unvalidated. **No claim** of new authenticated signed EO documents or a complete all-history universe.

## Human verification docket

The SQLite release contains 60,505 claim records spanning **every one of the 15,010 raw ledger entries**. `review_docket.py dossier DATABASE EO:10084 --html output.html` creates a self-contained browser review file showing identity claims, source links/grades, examined and missing provisions, a host-amendment redline timeline, source observations, previous statuses (ordinary exposed review), a legal rationale and counterevidence gaps. The `--blind` mode conceals inherited candidate answers; the 120-case QA sample remains separate. The browser form exports one JSON file per review session. `review_docket.py import DB REVIEW.json` atomically checks identities, source-fingerprint/codebook version, reviewer name, rationale, revision text and event uniqueness, then appends reviews without rewriting source decisions. Fingerprint changes invalidate prior approval. Test-only reviews cannot enter production unless explicitly placed in a test run.

Round trip tested with a clearly marked **TEST_FIXTURE_NO_HUMAN** review in a disposable database: first import inserted 1, second inserted 0, a source fingerprint change rendered the review stale and rejected reimport. Production dataset remains at **0 real human reviews**.

## Incomplete / blocked

- The GitHub repository retains an LFS archive of the earlier large corpora, but the connected GitHub API returns LFS pointers. The 2.966 GB reconstructed archive was **not byte-verified in this execution environment**. Stage16 + Opus + bridge small originals were independently checked using recoverable Library copies.
- Missing Opus `OPUS_STAGE11_CHECKPOINT2_EVIDENCE_ORIGINALS.zip`; without the source images no Opus source-package certification is permitted. Stage16 notes 9 earlier viewed texts without cached original bytes.
- No statistically representative 120-case independent legal audit has been carried out in this stage; no population-level accuracy claim is justified.
- Historical national denominator and pre-1937 archival completeness remain unproved; the Lord OCR list cannot be admitted automatically.
- The vast majority of WHOLE-ORDER first-cessation causes remain unknown, even after source-backed additions here.

## Highest-leverage next actions

The machine-readable `NEXT_LEVERAGE_QUEUE_STAGE17.csv` includes **155** original-forward Opus temporary-order cases, **386** EO 12553 formal predecessor links, **45** EO 3461 references, **1,023** Lord OCR candidate date markers, five newly recovered 1789–90 printed references, and six named original-acquisition blockers. The 1,620 queue rows represent **tasks with overlap and dependencies**, not distinct executive orders or legal conclusions. Obtain full original bytes for the six new source families and Opus companion, then validate clause histories and human review responses before expanding affirmative first-cause claims.

## Rebuild and review commands

Run `python research/stage17/build_stage17.py --stage16 ORIGINAL_STAGE16.zip --opus OPUS_CHECKPOINT2.zip --bridge-script research/stage17/build_stage17_bridge.py --out out_dir` after restoring the Git LFS archive or otherwise supplying the named exact ZIP inputs. The script verifies parent hashes and counts before migrating. Rebuild in two independent directories to confirm identical canonical DB SHA. Use `python research/stage17/review_docket.py dossier out_dir/data/AFTERLIFE_STAGE17_CANONICAL.sqlite EO:10084 --html EO10084.html` and `python research/stage17/review_docket.py import out_dir/data/AFTERLIFE_STAGE17_CANONICAL.sqlite REVIEW.json` for actual review; never import test fixtures to production.
