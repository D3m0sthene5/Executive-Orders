# Sol's handoff notes

## 2026-11-08 17:33 ET: all nonboard rank-8 members triaged

- **Done:** Reconciled 223 rank-8 members into 146 board and 77 nonboard cases. The disjoint nonboard packets n01 (25), n02 (25) and n03 research packet (25) plus two n03 preflight blocks cover all 77 exactly. `r8-n03/packet-b-v1` isolates 21 of the final 27 and passed a fresh 21/21 dispatch with 93 custody checks and free lease. Four others have exact HathiTrust/Internet Archive raw-source blocks (EO:5825, 6437, 6530, 6743); EO:6331B and EO:6370 have invalid working-text confirmations with named Mabillon text-hash mismatches. No page checks or claims were made.
- **Done:** Validated nine direct NMB report requests in `source-requests-v6.jsonl` and appended them to the source queue without changing older requests. Public PDF text names their corresponding orders, but exact bytes and dates remain unverified. `BOARD_CLASSIFICATION_TRIAGE.csv` holds six apparent non-PEB orders from the board-report roster and EO:11054's distinct Taft-Hartley Board of Inquiry route; no PEB date rule was applied to them.
- **Running:** Separate source triage found EO:5825's frozen raw SHA in an existing Git LFS release asset, and identified exact Internet Archive `_djvu.xml` URLs for the other three mandatory n03 source blocks. These raw bytes are not yet acquired into the claim-kit cache. Automatic unrelated Arsenale requeues may still advance Sol's remote branch.
- **Next:** Commit n03 and v6 source queue, reconcile the second source-ladder publisher and current remote Sol branch, push, then dispatch the nine direct board-report requests through source-only Run jobs. Acquire exact n03 raw sources without page checks and refresh the packet gate. Add a Kean ask for the six apparent classification errors; the owner must decide their rule before claims use the board route.
- **Asks:** @Owner: Six apparent non-PEB orders in `BOARD_CLASSIFICATION_TRIAGE.csv` need a classification ruling; `A-20261108-bracton-11033-no-report` remains open.

## 2026-11-08 17:17 ET: second source run and n02 packet

- **Done:** Targeted source-only [run 42528093766](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42528093766) selected only source-ladder and published a successful receipt: 13 newly found source records, including four direct rank-6 official issue routes, the 1955 CFR shared issue, three NMB board reports, the Truman receipt letter, NMB annual report, BLS bulletin, Reagan archival bundle and 1982 FR notice. `research/bracton/ACQUISITIONS.csv` names each state. Several PDF text extracts are partial; the historical CFR issue does not establish 1959–1960 applicability. Retained two public 1934/1935 GPO compilation DjVu candidates by SHA-256 in Sol raw upstream custody only; identity and order pages remain unverified. No page-check record or claim was made.
- **Done:** Prepared disjoint `research/bracton/r8-n02/packet-v5` for 25 existing Claude rank-8 cases. Fresh dispatch passed 25/25 with 115 custody checks and no lease conflict. Forty-four relevant exact APP archive captures resolve through Sol custody, 43 newly registered. Twelve optional source routes remain uncited. No producer or reviewer tokens used; model cost ledger stays at $0 measured worker spend.
- **Running:** `r8-n03` is preparing the final 27 nonboard rank-8 cases as packets of 25 and 2. Automatic unrelated Arsenale requeue may still advance the remote Sol branch.
- **Next:** Commit n02 and the acquisition ledger, then reconcile the latest source publisher on Sol's remote branch before pushing. Refresh the board-report coverage snapshot and packet seals after source publication; keep Claude-family blind reviews after Monday 6 PM ET reset. Montfaucon still owns the five named missing page checks and all original page checks.
- **Asks:** @Owner: Kean `A-20261108-bracton-11033-no-report` remains open.

## 2026-11-08 16:53 ET: first source acquisition published

- **Done:** Source-ladder run [42510818817](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42510818817) published a successful source-ladder receipt on Sol's remote branch despite the overall multi-job workflow failure. Exact official FR issue PDFs were retained for EO:10053 (1949-04-22, SHA-256 `ad3bb2b7...`) and EO:10578 (1954-11-24, `2683bcce...`), with machine locators of medium confidence. No Sol page check occurred. Four shared EO routes and two other rank-6 original routes each ended after one attempt; CFR::26 CFR 458.324 is `retry_later`. `research/bracton/ACQUISITIONS.csv` names the state and next need for each. Montfaucon m003 landed on main but did not cover Sol's five named page-check blocks.
- **Running:** Automatic Arsenale requeue of stale unrelated downstream jobs may still advance the remote Sol branch. A local picker change makes a future nonempty `source_only` dispatch select source-ladder alone; the targeted manual picker check selected exactly that job.
- **Next:** Finish and commit r8-n02 staging, rebase local work onto the published remote branch without rewriting its history, push the source-only picker and queued URLs, then dispatch the next targeted source run. Refresh current main and blocked-order page-check status before any merge. Keep Claude-family reviews after Monday 6 PM ET reset.
- **Asks:** @Owner: Kean `A-20261108-bracton-11033-no-report` remains open.

## 2026-11-08 16:43 ET: first nonboard rank-8 packet source-ready

- **Done:** Prepared `research/bracton/r8-n01/packet-v3` for 25 rank-8 cases outside the 146 board orders. Seventy-nine official FR issue PDFs and 23 archived APP captures matched frozen SHA-256 values, with the APP bytes and provenance retained in Sol's custody job. Exact tracked text/context files were loaded. Fresh `dispatch-v3.json` passed 25/25 with 128 distinct custody checks, zero mandatory source blocks, and no Kean lease conflicts. These are existing Claude claims, so Sol may only file isolated replacement proposals. Eight live APP routes yielded hash mismatches, and two named Opus archive members remain unstaged; they are optional to the current gate and listed in `SOURCE_ROUTE_FAILURES.csv`. No producer may cite them until custody passes. No model, page check, claim, or status change occurred.
- **Running:** First targeted source-ladder Run jobs [42510818817](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42510818817) remained active at the last watcher observation. Source-ladder lease lasts until 2026-11-09 01:03:41 UTC.
- **Next:** Reconcile the first run's publisher commit and current main before pushing Sol's branch. Continue bounded source acquisition for the 37 board reports without records and the other 52 nonboard rank-8 cases. Refresh all packet seals before Monday's producer/reviewer work.
- **Asks:** @Owner: Kean `A-20261108-bracton-11033-no-report` remains open.
- **Do not:** Infer a legal outcome from the machine gate or cite the ten optional unverified source routes.

## 2026-11-08 16:26 ET: bounded CFR/US Code extraction content audit

- **Done:** `research/bracton/yes-y03/EXTRACTION_AUDIT.csv` compares 22 held text extracts with the 12 exact raw official artifacts without editing source declarations. All raw and held text hashes match their respective records. Sixteen of 17 CFR extracts appear once as contiguous whitespace-normalized text in the raw XML; the remaining CFR part has 971/972 sampled 30-word chunks present. The five US Code section extracts are not contiguous as formatted, though their chunks largely occur in the raw ZIP XML. This corroborates content but does not reproduce extraction bytes or establish a legal predicate. The 22 source tasks remain blocked at the claim-kit gate.
- **Running:** First targeted source-ladder Run jobs [42510818817](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42510818817) remained active at the last watcher observation.
- **Next:** Reproduce the exact extraction/formatting from raw XML and ZIP or create a correctly authenticated source declaration through an owned route, then recheck the gate. Continue ranks #1–#9 before the 92-order Photius continuation.
- **Asks:** @Owner: Kean `A-20261108-bracton-11033-no-report` remains open.
- **Do not:** Count normalized content matching as an original page check, byte-exact derivation, or legal review.

## 2026-11-08 16:24 ET: Cujas continuation roster added after ranks #1–#9

- **Done:** Reconciled `compare_193.csv`, Cujas's three merged claim files (68 unique filed orders), and current main `487e18ab` readiness. Of 193 compared orders, 93 are ready and 100 remain unready. The seven lowest-coverage IDs include six unready and one already ready; EO:8538 and EO:8907 are already in Bracton rank #7. Excluding those disjoint sets yields exactly 92 orders in `research/bracton/PHOTIUS_POST_RANK9_ROSTER.csv`. `PHOTIUS_POST_RANK9.md` states the word-by-word GPO comparison, two fresh blind arms, planted controls, and priority after #1–#9. Reopened the two rank-7 overlap entries in `RECOVERY_TRIAGE.csv`. No producer, reviewer, claim, page check, or status change occurred.
- **Running:** First targeted source-ladder Run jobs [42510818817](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42510818817) remained active at the last watcher observation. Source-ladder lease lasts until 2026-11-09 01:03:41 UTC.
- **Next:** Finish ranks #1–#9 first; refresh the 92 roster against main before its producer phase. Keep Cujas's 68 filed claims and seven lowest-coverage orders out of the new stratum. Reconcile the source publisher before pushing Sol's branch.
- **Asks:** @Owner: Kean `A-20261108-bracton-11033-no-report` remains open.
- **Do not:** Rewrite Cujas claims or Montfaucon page-check records, or treat word coverage as a review verdict.

## 2026-11-08 16:15 ET: official upstream artifacts retained; Montfaucon main checked

- **Done:** Fetched all eight GovInfo bulk-title XML and four OLRC release-point ZIP artifacts named upstream of the 22 y03 CFR/US Code text extracts. All 12 raw hashes matched; 110,025,997 bytes were retained in `jobs/bracton-source-custody/output/upstream/` with `UPSTREAM.jsonl`. The 22 held text extracts match their own hashes, but the extraction from raw artifacts has not been independently reproduced. No false source-declaration substitution, page check, legal review, or claim occurred.
- **Main check:** Fetched `origin/main` at `487e18ab`. Montfaucon's m001 page checks landed, but none of Sol's five page-only blocked orders (EO:8341, EO:8613, EO:8639, EO:10117, EO:12414) is among its 50 m001 targets. They remain blocked on Montfaucon. No merge was attempted while the first source-ladder publisher is still active.
- **Running:** First targeted source-ladder Run jobs [42510818817](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42510818817) remained active at the last watcher observation. Sol's source-ladder lease was renewed until 2026-11-09 01:03:41 UTC.
- **Next:** Independently reproduce the exact CFR/US Code text extraction from the retained raw artifacts, then correct the source declarations through an owned route and recheck packet gates. Reconcile the first run's publisher commit before pushing Sol's branch; pull main again immediately before any merge.
- **Asks:** @Owner: Kean `A-20261108-bracton-11033-no-report` remains open.
- **Do not:** Count raw upstream custody as an original page check or a current-law legal finding.

## 2026-11-08 16:06 ET: y03 source routes tested

- **Clarification:** The 17 eCFR and five US Code source hashes represent extracted text, not the raw official artifact. Their source notes specify upstream GovInfo bulk XML and OLRC ZIP URLs and SHA-256 values, now copied into `SOURCE_ROUTE_FAILURES.csv`. The live rendered-page mismatch/404 does not authenticate or invalidate those upstream artifacts; raw bytes plus extraction still need verification.
- **Done:** The full y03 acquisition pass matched 69/69 official FR issue PDFs and 45/45 APP archive captures with frozen metadata. Forty-three new APP exact bodies and provenance rows were retained in Sol's custody job; two were already staged for y04. Direct live fetches of the remaining source references failed exact custody: 20 APP hash mismatches, 17 dated eCFR hash mismatches, and five House US Code HTTP 404 responses. `research/bracton/yes-y03/SOURCE_ROUTE_FAILURES.csv` records the exact expected sources and outcomes. Each of the 19 y03 orders outside source-ready y04 retains at least one of these source needs. No page check or legal finding was made.
- **Running:** First targeted source-ladder Run jobs [42510818817](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42510818817) remained active at the last watcher observation. Sol's existing source-ladder lease was renewed until 2026-11-09 01:03:41 UTC.
- **Next:** Find exact dated archival bytes or separately authenticated official substitutes for the 42 nonmatching routes; reconcile the source run's publisher commit and current main before pushing the branch. Refresh gates after main changes and before Monday's producer/reviewer work.
- **Asks:** @Owner: Kean `A-20261108-bracton-11033-no-report` remains open.
- **Do not:** Convert current live bytes into proof of the frozen source, or treat unavailable live routes as an order rejection.

## 2026-11-08 15:59 ET: six YES/FR orders source-ready and reserved

- **Done:** Selected six rank-9 YES/FR orders from the y03 source triage (EO:10111, EO:10431, EO:10444, EO:10457, EO:10670, EO:10718). Nine official FR issue PDFs and two APP archive captures matched their frozen SHA-256 values. Used `kit.py next` with an exact exclusion list to reserve only these six to `sol-bracton`, then prepared `research/bracton/yes-y04/packet-v1`. Fresh `dispatch-v1.json` passed 6/6 with 11 distinct custody checks, zero source blocks, and no Kean lease conflict. No original page check, producer, reviewer, claim, or status change occurred.
- **Running:** First targeted source-ladder Run jobs [42510818817](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42510818817) was still active at the last watcher observation.
- **Next:** Reconcile the run's publisher commit and current main, acquire further y03 sources, and refresh y04 immediately before producer work after Monday's Claude reset.
- **Asks:** @Owner: Kean `A-20261108-bracton-11033-no-report` remains open.
- **Do not:** Treat a passing research gate as legal review or file a claim without two fresh blind arms and controls.

## 2026-11-08 15:53 ET: next YES/FR acquisition packet triaged

- **Done:** Prepared `research/bracton/yes-y03/packet-v1` research-only for 25 rank-9 orders, excluding reserved EO:10538 and all Cujas identities. The packet is source blocked 25/25 and lists 156 distinct missing or different-hash source tasks. `SOURCE_TRIAGE.csv` summarizes per-order source tasks and the first required URL. No new reservation, producer, reviewer, page check, claim, or status change occurred.
- **Running:** First targeted source-ladder Run jobs [42510818817](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42510818817) was still active at the last watcher observation.
- **Next:** Acquire and authenticate the y03 source tasks in bounded groups, then recheck the gate and reserve selected orders. Reconcile the first run's publisher commit before pushing Sol's local branch. Refresh packets against main before production after Monday's Claude reset.
- **Asks:** @Owner: Kean `A-20261108-bracton-11033-no-report` remains open.
- **Do not:** Send a producer from this source-blocked packet, infer a legal current predicate from a citation, or write Montfaucon page-check records.

## 2026-11-08 15:48 ET: all source-record-present board cases staged

- **Done:** Prepared `research/bracton/board-b05/packet-v2` (25 orders) and `board-b06/packet-v2` (six orders), completing packet staging for all 109 board cases with report source records at this snapshot. Thirty-one official FR issue PDFs and ten NMB reports were re-fetched or cached and SHA-256 matched; thirty-two APP archive captures were reproduced against frozen hashes, with provenance and bytes retained in Sol's custody job. Exact tracked text and context files were materialized. Fresh `dispatch-v2.json` receipts passed 25/25 and 6/6 with 69 and 14 distinct custody checks, zero mandatory source blocks, and free Kean leases. These are Justinian-owned replacement-proposal routes. No original page check, producer, reviewer, claim, or status change occurred.
- **Running:** First targeted source-ladder Run jobs [42510818817](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42510818817) was still executing at the last watcher observation. Thirty-seven other board cases lack report source records and remain in acquisition.
- **Next:** Read the run's published source receipts, reconcile the runner commits and current main, and refresh all packet seals before production after Monday's Claude reset.
- **Asks:** @Owner: Kean `A-20261108-bracton-11033-no-report` remains open.
- **Do not:** Count source hash matches as page checks or legal findings; do not touch Montfaucon files.

## 2026-11-08 15:36 ET: third 25-order board packet staged

- **Done:** Prepared `research/bracton/board-b04/packet-v2` for the next 25 rank-8 board cases (EO:10877 through EO:11135, exact list in `PACKET.json`). Materialized the exact tracked dossiers and FR/NMB text extracts. Twenty-four official Federal Register PDFs and 17 NMB reports matched their frozen SHA-256 values and were staged in untracked local caches. `dispatch-v2.json` passed 25/25 with 72 distinct custody checks, no mandatory source blocks, and no Kean lease conflicts. This is source/packet preparation for Justinian-owned replacement proposals. No original page check, model producer, blind review, claim, or status change occurred.
- **Running:** First targeted source-ladder Run jobs [42510818817](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42510818817) was still executing at the last watcher observation.
- **Next:** Read its published source receipts, reconcile the runner commits and current main, and refresh all packet seals before production after Monday's Claude reset.
- **Asks:** @Owner: Kean `A-20261108-bracton-11033-no-report` remains open.
- **Do not:** Count hash matches as page checks, legal findings, or portable custody; do not edit Montfaucon files.

## 2026-11-08 16:23 ET: second 25-order board packet staged

- **Done:** Prepared `research/bracton/board-b03/packet-v2` for the next 25 rank-8 board cases (EO:10314 through EO:10875, exact list in `PACKET.json`). Materialized the exact tracked dossiers and FR/NMB text extracts. Twenty-four official Federal Register PDFs and 23 NMB reports matched their frozen SHA-256 values and were staged in untracked local caches. `dispatch-v2.json` passed 25/25 with 76 distinct custody checks, no mandatory source blocks, and no Kean lease conflicts. This is source/packet preparation for Justinian-owned replacement proposals. No original page check, model producer, blind review, claim, or status change occurred.
- **Running:** The first targeted source-ladder Run jobs [42510818817](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42510818817) was still active at the last watcher observation.
- **Next:** Read its published source receipts, reconcile runner commits and current main, and refresh all packet seals before production after Monday's Claude reset.
- **Asks:** @Owner: Kean `A-20261108-bracton-11033-no-report` remains open.
- **Do not:** Count hash matches as page checks, legal findings, or portable custody.

## 2026-11-08 16:16 ET: 25-order board packet source preflight passed

- **Done:** Prepared `research/bracton/board-b02/packet-v3` for 25 disjoint rank-8 board cases (EO:10032 through EO:10306, exact member list in `PACKET.json`). The partial clone initially lacked frozen dossiers and text extracts. After materializing those exact tracked files, 24 official FR issue PDFs and 20 NMB report PDFs matched their frozen SHA-256 values and were staged in untracked local caches. A fresh `dispatch-v4.json` passed 25/25 with 74 distinct custody checks, zero mandatory source blocks, and no Kean lease conflicts. No original page was checked. No producer, reviewer, claim or status change was made. The packet is a Justinian-claim replacement-proposal route and must be refreshed after shared inputs change.
- **Running:** First targeted source-ladder Run jobs [42510818817](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42510818817) was still executing at the last watcher observation. Local source hints and queue additions remain unpublished until its result is published.
- **Next:** Read the run's published source receipts, reconcile the branch with its runner commit and current main, and continue bounded source batches. After Monday's Claude reset, confirm fresh packets and leases, then assign bounded producer and blinded reviewer tasks with planted controls.
- **Asks:** @Owner: Kean `A-20261108-bracton-11033-no-report` remains open.
- **Do not:** Treat the 25/25 machine preflight as legal review or portable source custody; do not page-check originals or write Montfaucon's records.

## 2026-11-08 15:57 ET: direct shared-source hint and EO 12285 report located

- **Done:** Staged an exact `CFR::26 CFR 458.324` source-ladder URL hint to the official 1955 Federal Register issue, with a passing routing test. The earlier 1955 publication does not answer 1959–1960 applicability. Found a Reagan Library archival bundle containing EO:12285's commission final report and an official 1982 Federal Register notice of its September 21, 1981 submission; two validated requests are in the append-only fetch queue. Identified catalog holdings for EO:4314's 1925 booklet but no verified full scan. No page check, claim, or blind review was made. The full source-ladder test file has two unrelated PDF extraction failures in this embedded Python environment because `pypdf` is absent; the new targeted test passes.
- **Running:** First targeted Run jobs [42510818817](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42510818817) remains active. Local commits and the new queue lines remain unpublished until its pinned-input run publishes.
- **Next:** Reconcile the runner's remote branch commit, merge current main, then dispatch direct-source and untried-board batches. Read published source receipts before marking an acquisition complete. Revisit page-only cases only after Montfaucon's checks land on main; refresh packets for Monday's review reset.
- **Asks:** @Owner: Kean `A-20261108-bracton-11033-no-report` remains open.
- **Do not:** Run #10/#13, create page-check records, or count a discovered URL as authenticated source custody.

## 2026-11-08 15:37 ET: Bracton board source retries staged; first source run still active

- **Done:** Kept the first targeted source run pinned. Classified nine absent board-report sources with prior failures in `research/bracton/BOARD_RETRY_TRIAGE.csv`. Five page-reading blocks now name exact sources in `BLOCKED_MONTFAUCON.csv` (three recovery FR printings plus EO:10117 and EO:12414 scanned NMB reports). No Sol page-check record was written. Added six direct board source leads to the append-only fetch queue: NMB PEB-067/086/142, Truman Library's EO:10106 receipt letter, NMB's EO:11033 annual report, and BLS's EO:11078 bulletin. They remain unacquired. `COST.md` still has $0 measured worker cost and explicitly leaves Codex coordinator usage unmeasured. Kean ask `A-20261108-bracton-11033-no-report` names the possible owner rule exception; strict Kean check passes.
- **Running:** Run jobs [42510818817](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42510818817) still had its source-ladder/downstream execute station active at about 59 minutes. Live logs are unavailable until the station finishes. Local Bracton commits are deliberately unpublished pending that run's result and publisher. `origin/main` advanced to `6662199a` after Cujas PR #224 merged 68 Photius claims; continue to exclude all 193 Cujas identities per owner. No Montfaucon PR was listed at this check.
- **Next:** Wait for the first source run's published receipts, then fetch/rebase local Bracton commits onto the remote publisher result, merge the latest main, regenerate the plan and Kean brief, and push. Dispatch the staged four direct rank-6 issue leads, six board leads, and 28 untried board report requests in bounded source-ladder batches. Confirm each from published status before changing acquisition states. Monday after 6 PM ET, refresh packets and run controlled blind reviews.
- **Asks:** @Owner: Kean `A-20261108-bracton-11033-no-report` asks how to apply the board rule if an authenticated NMB record confirms no report was submitted.
- **Do not:** Run #10/#13 or page-check originals, edit Montfaucon files, count URL discovery as source custody, or send Claude-family review work before the reset.

## 2026-11-08 14:00 ET: Bracton exhaustive #1–#9 acquisition and ownership split

- **Done:** Switched to `sol/bracton-2026-11-08`, merged current main, and recomputed Bentham without a dollar cap: ranks #7–#9 have 9, 223, and 338 current members. `research/bracton/BASELINE.csv` records all 570; two recovery identities (EO:8538, EO:8907) overlap Cujas's exact 193 and remain excluded. `RECOVERY_TRIAGE.csv` names each recovery disposition. Three OCR/page-only recovery blocks, with exact FR sources, are in `BLOCKED_MONTFAUCON.csv`; Montfaucon owns their page checks. No Sol page-check record or claim was made. `BOARD_REPORT_STATUS.csv` finds current source records for 109 of 146 R3 report-date cases; 28 absent cases are untried and nine have named `retry_later` failures. Price/usage limits are recorded honestly in `COST.md`.
- **Running:** Source-ladder Run jobs [42510818817](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42510818817) on nine rank #1–#6 source identities. It selected downstream consumers and had not published `STATUS.json` when this note was written. The branch also has incidental auto-push job outputs to remove before PR. Four direct govinfo leads for EO:10053, EO:10578, EO:11633 and EO:8947 are validated and queued locally for a following source run; the first run's pinned inputs are kept stable until it publishes. The EO:8947 issue conflicts with the Archives disposition table and requires Montfaucon's page check after acquisition.
- **Next:** Read the first run's published `STATUS.json`, `RESULTS.csv`, and `SOURCES.jsonl`; update `ACQUISITIONS.csv` and `COST.md`, then fetch and reconcile the branch's runner commits. Run direct issue and missing-board-report source batches, marking unavailable routes. Pull latest main before every merge, recheck Cujas/Montfaucon outcomes, and revisit page-only blocks only after Montfaucon records land. After Monday 2026-11-09 6 PM ET reset, refresh disjoint claim packets and run fresh blind review with controls, gates and per-batch cost.
- **Asks:** @Owner: none.
- **Do not:** Run Bentham #10/#13, check original pages, edit Montfaucon or Cujas files, infer a page match from a URL or OCR result, dispatch from an old packet seal, or spend Claude quota before the reset.

## 2026-11-08 13:03 ET: Bracton board and YES packets staged for Monday review

- **Done:** Recomputed Bentham's $300 plan after filtering historical recoveries through current tracker readiness (48 old rejected-mechanical identities, 9 still not ready). Fixed Valla's canonical v2 review-context acceptance. All 35 Valla and 13 Bentham candidate/planner tests pass. `research/bracton/STAGING.md` records the packet seals and source custody; Kean findings F-20261108-1 through F-20261108-4 record attempts and lessons. Cujas c01 identities are disjoint. EO:10538 is locked to `sol-bracton`.
- **Running:** No producer, reviewer, or job. Board packet EO:10010/10923/10944 and YES packet EO:10538 both pass fresh offline dispatch checks in this checkout. Four APP archive captures are retained in `jobs/bracton-source-custody/`; ten exact public PDFs are in local untracked job caches and must be reacquired in a fresh checkout.
- **Next:** After Monday 2026-11-09 6 PM ET reset, pull main and Cujas, reconcile any changed frozen inputs, recheck dispatch, then follow Bentham recovery/correction gates and run different-family blind reviews with controls. YES remains staged until budget and gate permit. File only accepted claims and report checker/tracker deltas.
- **Asks:** @Owner: none.
- **Do not:** Treat a staged source match as a legal finding or human review; dispatch from a stale receipt; edit Cujas's c02 packet or another agent's claims; check out restricted ProQuest or `_attempts` trees.

## 2026-10-18: claim-kit implementation and runner validation in progress

- **Done:** Created `sol-claim-kit` from `wire-new-sources` commit `5e3e00b2c1bdb0fcd68202b4aff735f7dd691353`. Read the complete Sol brief, handoffs, claim guide, schema, funnel and existing runner. Added generic evidence discovery, exact-span excavators, whole-corpus dossiers and status leads, blank decision sheets, fail-closed Stage19 assembler, reservations CLI and model-neutral protocol. Only pointers added to AGENTS/readiness. Source metadata on the base branch pins 14,972 identities / 3,359 provisional statuses; tracker baseline is **130 ready**.
- **Running:** Initial `jobs/claim-kit` branch run. Read `output/STATUS.json`, `SUMMARY.json`, `ASSEMBLY_REPORT.json` and the exact `commit_run` before using dossiers. Corpus outputs are leads, never accepted findings. Implementation has separate ingest/excavator/assembler agents and independent integration review; the pilot has not yet been promoted.
- **Next:** Inspect full-corpus coverage, fix runner failures if any, then produce and separately review 50 disjoint decided orders in eligible families. Record exact reviewer outcomes, checker and tracker effect.
- **Asks:** None while validation is running.
- **Do not:** Merge this branch, change census/status/ledger/codebook, edit others' claims or notes, treat an AI review as a human review, or infer pilot savings from synthetic tests. Model billing/cache token telemetry is unavailable in this session; do not fabricate token-per-claim measurements.
