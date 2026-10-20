# Panizzi: serving the fetch queue (2026-10-20)

The review found seven defects in Panizzi's changes and I fixed them all. All 77 source-ladder tests pass, as do the tests of the six jobs that import it (_lib/fetch_pool, clause-drafts, claim-checker, corpus-excavator, and fr-originals ×2). The codebook and the acceptance rules are untouched. A live preview of the default 50-item plan from this container found 44 of 50, though some of those are not real documents (see below). Nothing is committed or pushed.

**Diagnosis**

| # | Problem found | Effect | Fix |
|---|---|---|---|
| 1 | Any Stat. cite on a line dropped its Public Law or Reorganization Plan cite, even an unrelated one | "Pub. L. 98-525 … 90 Stat. 1255" would lose 98-525 | A cite is dropped only when the Stat. cite is in a volume of that Congress |
| 2 | The U.S. Code section pattern swallowed following text | `5USC3345etseq` became section "3345etseq", a URL that would fail | Letter suffix limited to 3 letters |
| 3 | A prose line with a link fell back to *every* statute/Code/CFR cite in the line | A request could be marked found with a different document (e.g. 50 U.S.C. 1622 standing in for 31 CFR 536) | Fallback only to the official copy of the same document the link names; no current-edition fallback for a link to a dated USCODE/CFR edition |
| 4 | Reorganization Plan index routes also got Wayback routes | A Wayback copy of the Title 5 Appendix (a compilation) could be accepted as the plan itself | No Wayback for the index step, and a USCODE compilation is rejected as a plan's source |
| 5 | The new eCFR renderer API route is disallowed by ecfr.gov/robots.txt | In the live preview every attempt ended `blocked_by_robots_txt`, so the claimed new route never works | Route removed. The ladder still obeys robots.txt (the older eCFR `/on/` route is disallowed too) |
| 6 | A govinfo PREMIS metadata file was accepted as the found source for P.L. 97-35 because the PDF was over 100 MB | A "found" with no statute text | Metadata is hashed and logged but never accepted as the document. This applies to old requests too; no committed source used metadata |
| 7 | No-route items were placed after the plan | A budget stop would mark them `not_attempted_budget` instead of `no_route` | They now go first (they make no request) |

**Hand checks.** I checked 14 requests against the live services; all resolved to the right document:
- 71 Stat. 78 → granule starting at Pg70
- Pub. L. 94-412 → 90 Stat. 1255
- 79th Congress Pub. L. 724 → 60 Stat. 999
- Reorganization Plan 2 of 1970 → 84 Stat. 2085
- Reorganization Plan 2 of 1968 → 82 Stat. 1369
- Pub. L. 94-82 → 89 Stat. 419
- Pub. L. 92-578 → 86 Stat. 1266
- Pub. L. 110-186 → 122 Stat. 623
- 77 FR 38459 → EO 13617
- 52 Stat. 154, 56 Stat. 363 (→ Pg359), 63 Stat. 802
- 5 U.S.C. 5312 and 5 U.S.C. 3345

40 U.S.C. 485 and 22 CFR 105 no longer exist; govinfo answers with HTTP 400, so those requests end as recorded failures.

Other checks: official hosts only (govinfo, uscode.house.gov, eCFR); every attempt keeps its URL, final URL, status, sha256 and error; bounds are 50 items, 300 requests and 800 MB.

**Change.** Edited `embedded_cites.py`, `fetch_ladder.py`, `job.py`, the job README and `test_panizzi_resolvers.py` (6 new regression tests; the 2 eCFR-renderer tests were replaced by 1 that checks the route is gone). I also rewrote my entry in `HANDOFF/notes-claude.md`. On the old requests, route plans are unchanged apart from the 33 that gained a fallback; the only other old-request change is fix 6.

**Expected on the next run (an estimate, not yet run on Actions).** 22 lines go from no route to routed, and 33 link-only lines gain a same-document official fallback. The preview (`/tmp/claude-0/-home-user-Executive-Orders/dc388148-b92d-5956-9825-90ce34a3dac7/scratchpad/panizzi/review/live/out`) found 44 of 50 in 108 requests, 389 MB and 654 s. Of those 44:
- 5 are NARA finding-aid pages the requester gave as links (pre-existing behaviour), not documents.
- 1 was the PREMIS metadata, which is now rejected.
- The 5 CFR 6 item came back as the 2026 edition, which does not answer the 1953 question.

So expect about 37 to 38 real documents. The 6 that failed did so for container network reasons (blocked Wayback, connection resets) and may succeed on GitHub.

**Still unservable, and why**
- 52 lines have no route: emergency-board and commission report dates, land orders and land records, agency orders, pay calendars, and others. These need National Mediation Board, NARA or Public Papers records, BLM land-order records, or historical CFR editions (LoC/HeinOnline or owner access), plus 1945–1957 State Department orders by Federal Register page.
- Three files are over the shared 100 MB per-file limit (27 FR 2983 issue, 45 FR 44245 issue, 95 Stat. 357), which I did not change.

**How to trigger and verify.** Pushing any non-`output/` change under `jobs/source-ladder/` or `research/readiness/` starts `run-jobs.yml`. So does a manual "Run jobs" with `source-ladder`. Afterwards check `jobs/source-ladder/output/STATUS.json`, then `SUMMARY.json` (`found`, `embedded_cite_items`, `bytes_downloaded`, `stopped_early`) and `RESULTS.csv`.

SUMMARY: The review found and fixed seven defects. The main ones: unrelated Stat. cites dropped Public Law and plan cites, `etseq` was swallowed into Code sections, a prose line could be "found" with a different document, a Wayback copy of the Title 5 Appendix could stand in for a plan, the eCFR route is blocked by robots.txt, and PREMIS metadata was accepted as a document. 77 tests pass and the codebook is untouched. The preview found 44 of 50, about 38 of them real documents. 52 lines still need non-govinfo archives. Push `jobs/source-ladder/` and check `output/STATUS.json`.

## Panizzi II (2026-10-20)

The build added a report-date route and fixed the five defects Craigellachie II found. An adversarial review then found six more problems and I fixed them. All 148 source-ladder tests pass (137 before the review, 11 added), as do the tests of the 11 jobs that import the ladder. The codebook is untouched. Nothing is committed or pushed.

**Routes added (`report_dates.py`).** A queue line that asks when a report was submitted is kept whole. It gets a spec: the body's name, its orders with their OFR signing dates, and a due date or window. It never gets a date field. Each lane looks in one place:
- **Emergency boards:** the National Mediation Board table at nmb.gov, then the board's report PDF (first 8 pages).
- **1993–2009:** the Weekly Compilation MODS for up to 20 issues on govinfo.
- **Before 1993:** the Public Papers volume on govinfo, read by HTTP Range. Running heads are bisected to the date, then nearby pages are scanned.

Each lane returns the record, its hash, and the dated lines verbatim, unlabelled. Which line is the transmittal is left to the reviewer.

**Defects fixed (build):**
1. Gzip bodies are decoded before hashing, and the raw hash is kept.
2. Statute PDFs are read in full (up to 500 pages).
3. Tables of contents, the uscode.house.gov editions list and listing pages are rejected, and never proposed as exhausted.
4. A dated CFR or U.S. Code question uses that year's govinfo edition, or ends `no_route` before 1996 (CFR) or 1994 (Code).

**Review findings, all fixed:**
1. **Carry-forward made the defect fixes inert.** Found records are carried forward and never re-checked. Pub. L. 98-525 pages 1–40, the gzip pages (EO 12335, 11065), the 2026 CFR for 1953 and the congress.gov listings would therefore have stayed in the output as "found". `carried_defect` now re-checks every carried record. Against the committed output, 31 of 251 fail and are walked again. The old record stays, marked `carried_defect`, until it is replaced. A replacement names it in `supersedes_defective_source`, and a failed re-walk names its URL and sha256 in its RESULTS row.
2. **New routes never got planned.** Lines that had ended `no_route` counted as "tried", so only 6 of 29 routable report-date lines entered the 50-item plan. A `no_route` line now ranks with the untried lines, which brings 29 report-date lines into the plan.
3. **Two boards created the same day.** EO 12491 and 12492 both match PEBs 205 and 206 (Long Island Rail Road), and the first PDF fetched would have been taken for both orders. A report whose front matter names a different order, by number or by "Executive Order dated …", is now refused. Ties are listed in `equal_candidates`.
4. **A spent Range budget stopped the whole run.** It raised `BudgetExceeded`, which would leave every later item `not_attempted_budget`. Now only the Range route fails (`rd_range_budget_reached`, a passing failure).
5. **NARA Guide to Federal Records pages were "found" as the record** for EO 12095, 12159 and 12182 (the RG 13 page). They are now `index_page`, and these lines go to the NMB lane.
6. **Missed dates and a misleading failure.** Upper-case title-page dates ("FEBRUARY 9, 1979") were missed as leads. A scanned report with no text layer passed the 200-character check on page markers alone, then failed as "no_word_report". It now ends `rd_no_meaningful_text`.

**Official hosts and robots.txt.** Every new request goes to nmb.gov or www.govinfo.gov. I checked both robots.txt files today:
- nmb.gov answers 404, which means no rules.
- govinfo allows `/metadata/`, `/sitemap/` and `/content/pkg/`. It disallows only `/app/search/` and similar paths.

`open_range` checks robots.txt before any Range read, and redirects are re-checked. Wayback is never used for report-date index steps.

**Bounds:**
- Plan: 50 items, 300 page requests, 800 MB in total.
- Weekly Compilation: at most 20 MODS files per case.
- Range reads: at most 600 requests and 40 MB per case, and 1500 per run (`JOB_MAX_RANGE_REQUESTS`). They count toward the 800 MB ceiling and are spaced 0.25 s apart, or by the host's crawl delay. The whole volume is never downloaded.

**Regression check.** I compared the route plans of HEAD and the working tree for all 1,149 current queue items:
- 1,097 plans are identical.
- 29 only gained routes (report-date lanes).
- 15 were only reordered: a live uscode.house.gov or eCFR page now comes before its Wayback copy.
- 8 lost routes. All are current Code/CFR routes for questions dated earlier (37 U.S.C. 110 in 1946, 31 U.S.C. 16a for 1967–70, 5 U.S.C. 5312 in 1977, 5 U.S.C. 4103 for 1986–89, 22 CFR 105 for 1945–57, 5 CFR 6 in 1953, 5 U.S.C. 3161 for 2021). The last of these now uses the 2021 edition.

No item ID appeared or disappeared. Of the 251 earlier found records, 220 still pass and stay carried; the 31 that fail are re-walked (finding 1).

Edge case: the 5 U.S.C. 4103 note for "expiry 1987–1989 and any extension" lost its current-Code route. A later edition could have shown the extension; that line now relies on 100 Stat. 964.

**Hand checks (live, 10 results).** I checked each against the document text:
- **EO 14077:** PEB 250, letter of transmittal dated August 16, 2022.
- **EO 12095:** PEB 189, title page "FEBRUARY 9, 1979". It names EO 12095 dated November 2, 1978.
- **EO 12433:** Public Papers 1984 Book I, page 44, "Remarks to Reporters on Receiving the Report of the National Bipartisan Commission on Central America, January 11, 1984". It took 167 Range reads and 10.9 MB of an 895 MB file.
- **EO 12575:** Public Papers 1987 Book I, page 199. The Tower board report was received on February 26, 1987. 42 Range reads, 2.7 MB.
- **EO 12961 (synthetic request):** Weekly Compilation of 1997-01-13, "Remarks on Receiving the Report of the Presidential Advisory Committee on Gulf War Veterans' Illnesses", January 7, 1997.
- **Pub. L. 98-525:** all 169 pages, with SEC. 1632 and "Approved October 19, 1984".
- **84 Stat. 785:** all 69 pages, with sec. 15 and "Approved August 12, 1970".
- **3 U.S.C. 110 note:** the 2024 edition, which carries the EO 11145/11565 note. The request asks for current law; the editions-list page was rejected.
- **5 CFR 6 for 1953:** `no_route`, correctly.
- **EO 12491/12492:** PEBs 205 and 206 have no text layer, so the line ends retry_later and is not mis-attributed.

The gzip decoding was not run live (Wayback resets here); tests cover it.

**Expected newly served lines on the next run (an estimate, not run on Actions):**
- **Report-date lines:** 29 are in the plan (16 emergency-board lines, 11 Public Papers lines, 2 with other routes). Two of three live-tested board PDFs had a text layer, and both tested Public Papers cases hit. Expect about 13 to 20 new transmittal records: roughly 9–12 from boards and 5–8 from Public Papers.
- **Re-walked records:** 13 of the 31 defective earlier records are in this plan. The partial statutes should come back complete (Pub. L. 98-525 for EO 12499 and 12502, Pub. L. 91-375, 76 Stat. 451, 92 Stat. 1705).
- **Honest drops:** EO 10440 <5 CFR 6> and EO 11941 <5 U.S.C. 5312> become `no_route`, and EO 14027 gets the 2021 edition. The 5 congress.gov-listing lines and the 5 NARA-guide lines stop counting as found unless another route serves them. So `found` may fall by about 5 to 10, while the records that remain become real.
- **Displaced lines:** the plan now holds fewer brand-new statute lines (7 instead of 22). They move to the next run.

**Still unservable:**
- **7 report-date lines with no lane:**
  - reports to an agency head (EO 14087, 13792);
  - commissions where only the signing date is known (EO 13038, 13090, 11256, 12285, 11262). These need a due date in the request, or the report's own front matter.
- **Emergency-board reports scanned without OCR** (PEBs 205/206, and probably other 1980s boards). These need OCR or a human reader.
- **No Daily Compilation (post-2009) lane.** None is needed by the current queue.
- **37 queue lines with no route:**
  - pre-1996 CFR and pre-1994 Code questions, which need Federal Register issues of the year, historical editions or LoC/HeinOnline;
  - land orders, agency orders and pay calendars.
- **Unchanged from before:** the 3 files over the 100 MB per-file limit.

**Before pushing.** Queue items gained `queue_note` and `report_date`, so any saved `SOURCE_PLAN.json` (`JOB_PLAN_FILE`, the corpus-excavator plan) is stale and must be rebuilt. Another workflow appended a line to `FETCH_QUEUE.jsonl` during this review; it is not part of this change. Files changed in review: `fetch_ladder.py`, `report_dates.py`, `job.py`, `README.md`, `test_panizzi2_defects.py` (7 tests) and `test_report_dates.py` (4 tests added, 1 rewritten). Review scratch: `/tmp/claude-0/-home-user-Executive-Orders/dc388148-b92d-5956-9825-90ce34a3dac7/scratchpad/panizzi2/rev/`.
