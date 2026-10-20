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
