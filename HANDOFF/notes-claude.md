# Claude's handoff notes

Newest entry first. See `README.md` in this folder for the format.

## 2026-10-21 ET (~22:05Z): first live web-search runs; Pinakes complete

- **Done (PR #49 branch):** Pinakes ingested all uploaded ProQuest PDFs: 2,807 files, 2,750 orders, every one with a text (2,297 from the PDF's own layer, 453 OCR'd; 310 flagged as probable handwriting); 15 of the 2,765 links still lack a PDF (`MISSING_FROM_UPLOAD.csv`). Tracker shows 2,750 orders under `ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK`; ready count unchanged (278). Three live web-search runs: engines answering from GitHub are LOC (newspapers, books, manuscripts), Internet Archive, the FR API, APP search, govinfo search and intermittently DuckDuckGo lite; Bing, Mojeek, Brave, Yandex, HathiTrust catalog, Wikipedia/Wikisource search are robots-blocked; Google Books rate-limits without a key. Clark has web pages confirming 10 unknowns (the June 1932 run 5855/5856/5862/5867/5872/5873, EO 2539, with dates, on APP pages of later orders) and 16 numbers named on pages the census lacks. Lewis's first "confirmed" pages were state and local orders sharing a number; a page now counts only with the date or title, and state/local wording marks it down.
- **Lessons:** the runner refuses to publish results when a declared input changed during the run; four runs were lost to pushes mid-run. Runs are now short (Lewis 80 targets / 1,000 requests, Clark 50 / 700, about 15 minutes each) and dead engines are skipped within a run.
- **Asks:** `@Owner`: search keys as secrets (`GOOGLE_CSE_KEY`+`GOOGLE_CSE_CX` above all) widen every query; say if you want a second daily schedule for the web search.

## 2026-10-21 ET (~18:05Z): Pinakes ingests the 2,794 uploaded ProQuest PDFs

- **Done (same branch, PR #49, merged with main's upload commit `d360cb57`):** `jobs/pinakes-proquest-ingest`: verifies every PDF in both ProQuest folders (the upload at the repo root and the research folder), chooses one file per order (2,740 orders from 2,794 files; duplicates by SHA-256), takes the PDF's own text layer when usable or OCRs with tesseract (bounded, `JOB_OCR_PAGES` 4,000/run, resumable from the last committed output), flags handwriting OCR by a common-word share, and writes `ORDERS.csv`, `texts/`, `FRAGMENTS.jsonl` (`acceptable_as_original: false`, `needs_page_check: true`), the link-list reconciliation and `STRAY_FILES.csv`. The tracker now reads those fragments as a lead class with blocker `ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK` and an agent-check unlock (test added); Lewis takes `ORDERS.csv` as the ProQuest authority; Clark harvests the texts; Domesday shows file, hash and text per order.
- **Running:** the next Run jobs on the branch runs Pinakes first (OCR takes a few runs to clear the backlog), then Clark, Lewis, Domesday.
- **Asks:** `@Owner`: 1. `ProQuest Pre-1937 Orders/LRS-10-21-Cold-Calls-Plain.pdf` is not a ProQuest file (listed in STRAY_FILES.csv); remove it if it was uploaded by mistake. 2. The upload sits at the repo root, not under `research/pre-1937-sources/`; both are read, so moving it is optional. 3. Whether a replica scan may count as the original after a page check is still your codebook call; the tracker rule is ready to write once decided.
- **Do not:** hand-edit `jobs/pinakes-proquest-ingest/output/`.

## 2026-10-21 ET (~17:10Z): Lewis and Clark go online; Domesday register

- **Done (same branch, PR #49):**
  - `jobs/_lib/eo_websearch.py`: open-ended web search shared by Lewis and Clark. Engine registry (built-ins plus owner-extensible `search_engines.json`): general web engines, keyed engines (Google CSE, Bing, Brave, SerpAPI, NARA; the workflow now passes those secrets when added), LOC, Internet Archive, Google Books, HathiTrust catalog, FR API, Wikisource/Wikipedia search, APP, govinfo. Escalating query strategies per order; hits followed and read for number, date and operative wording; every page read harvested for order numbers; state carried forward from the last committed output so no target is ever dropped. FetchPool underneath (robots.txt obeyed, throttled, hashed into SOURCES.jsonl); blocked or keyless engines reported by name in ENGINES.json.
  - Lewis `online.py`: hunts every order in scope, manual-lead routes first, 100 targets / 1,500 requests per run by default (`JOB_MAX_TARGETS`, `JOB_MAX_REQUESTS`).
  - Clark `online.py`: hunts number gaps, plausible cited-unknowns and number-only orders; reads the list pages in `list_pages.txt` (Wikipedia, Wikisource, APP, OFR tables; owner-extensible) and reports every order number the census lacks (`WEB_LISTED_ORDERS.csv`).
  - `jobs/domesday-register`: `REGISTER.csv`, one row per census order with date, title, president, every source held by class, readiness, ProQuest state, Lewis/Clark results; `CANDIDATES_NOT_IN_REGISTER.csv` for numbers named anywhere that the census lacks. Runs after Lewis, Clark and the tracker.
- **Running:** the branch's first online run will show in `ENGINES.json` which engines answer from GitHub's runners and which robots.txt blocks; expect several blocked.
- **Asks:** `@Owner`: add search keys as repository secrets to switch on the big engines (`GOOGLE_CSE_KEY` + `GOOGLE_CSE_CX`, `BING_SEARCH_KEY`, `BRAVE_SEARCH_KEY`, `SERPAPI_KEY`, `NARA_API_KEY`); the jobs pick them up on the next run with no code change.

## 2026-10-21 ET (~16:45Z): Lewis and Clark, two source-discovery jobs

- **Done (branch `corps-of-discovery-lewis-clark`, PR to follow):** two paired jobs plus a shared helper, all offline, standard library (pypdf optional), tests run first.
  - `jobs/lewis-originals` (**Lewis**): for every order the tracker leaves `ONLY_COMPILED_TRANSCRIPTION_FOUND` (4,644), the route to an official original and where it stands: a verified ProQuest PDF in the repo (bytes, SHA-256, pages, text-layer quality), a ProQuest link awaiting upload, a Federal Register fetch request for the source-ladder (266, contract-validated, in `PROPOSED_FETCH_REQUESTS.jsonl`; never enqueued by the job), a GPO/Hoover volume range to re-check (1,704), or a ProQuest phrase search (1,941). `FRAGMENTS.jsonl` for ProQuest files carries `acceptable_as_original: false`, `needs_page_check: true`; the tracker does not read it.
  - `jobs/clark-discovery` (**Clark**): orders the project cannot identify. 46 number gaps in the 14,972 census, 22 of them one June 1932 run (EO 5853-5879) that the APP index knows with dates and titles; 26 plausible cited-but-unknown ids from 27,017 texts and 5,063 OFR notes (EO 27-A, the 1894 run 36-53, EO 92, several lettered orders), with OCR artifacts ranked separately; 3,432 census orders known by number only (2,655 on the ProQuest list); 414 dated unnumbered references matching nothing. `HANDOFF_TO_LEWIS.jsonl` feeds Lewis.
  - `jobs/_lib/eo_identity.py`: id parsing (lettered, ½, `-1` duplicates), the date/title oracle (OFR catalog, APP index, fragments, WPA list, ProQuest list), and the citation regex.
- **Running:** nothing until the branch lands; both jobs are `DAILY` and trigger on `research/pre-1937-sources/*` and the census.
- **Next:** when the ProQuest PDFs are uploaded, Lewis inventories them on the next run (2,738 orders move from `awaiting_acquisition` to `file_verified_pages_unchecked`) and Clark reads the usable text layers.
- **Asks:** `@Owner`: 1. Should the June 1932 run (EO 5853-5879) go to census intake? Clark's `NUMBER_GAPS.csv` has the APP evidence. 2. Decide whether ProQuest replica scans may count as the original after a page check; if yes, the tracker needs one rule (`J` class + test), which I have not written. 3. Enqueue Lewis's 266 FR proposals if you agree: `python jobs/source-ladder/request_contract.py enqueue --input jobs/lewis-originals/output/PROPOSED_FETCH_REQUESTS.jsonl --queue research/readiness/FETCH_QUEUE.jsonl`.
- **Do not:** hand-edit `jobs/lewis-originals/output/` or `jobs/clark-discovery/output/`; the jobs rewrite them.

## 2026-10-20 ET (Revere phase, ~21:45Z): late update

- **Ready 256** at 21:42Z, certified 0; newer claims not yet counted.
- **Since the ~18:00Z entry:**
  - Lambertini IV probe 2: passed, 5 claims. LAMB4X has no ruling-independent orders left.
  - R9830: probe 6 claims, scale 8 claims (26 ACT records).
  - R12553NB: probe 6 claims, scale 9 claims (32 ACT records).
  - VIAPAR: probe failed (4 of 8 blocked on strike-and-insert); 3 claims in all, including EO 11908 from the mend.
  - PAGECHK3: 1 claim.
  - Fixes: claim-kit act_overrides now matches lettered numbers (EO 7975A ingests). Source-ladder re-walks PDFs that are missing their named pages, so EO 11490 pp. 63-95 should land on the next run and unlock pool F11490 (20 orders).
  - Planted controls: every plant caught today. One automated "instruction poisoning" flag on the R12553NB s5 planter was a false positive; I checked it, and the edit was scratch-only.
- **Owner brief:** `research/production/owner-rulings-2026-10-20/BRIEF.md` covers three method rulings (report deadline, strike-and-insert, unnamed-instrument ends). AGENT_PROTOCOL step 3 already says "A report deadline is never an end", which equals option C: 97 orders.
- **Next:**
  1. F11490 once its pages land: `research/production/day-review-2026-10-20/next-lines/F11490_ids.txt`, Lambertini with a probe gate.
  2. After any owner ruling, run the matching staged packets: Pullman (`research/excavator/pullman-2026-10-20/`) or Blackstone.
  3. Almost every remaining line now waits on an owner ruling.
- **Llull note:** O-58 counts the Lambertini IV probe-1 claims as 0, but its 4 upheld claims were filed anyway. Outcomes are append-only.

## 2026-10-20 ET (Revere phase, ~18:00Z): coordinator after handoff

- **Done (pushed `e3c9f0d87`+merge):**
  - Lambertini III coda: 11 of 12 claims upheld (2/2 plants caught), all pass the checker. Files: `claims/claude-lambertini-{b02,rr4}-2026-10-20.jsonl`. EO 14052 is held back: EO 14082 sec. 4(c) strikes and re-adds subsection (xii), which needs a human ruling. Llull outcomes O-46..48.
  - Re-sourced to the held official FR texts: EO 10324, 10467, 12977 (i04, i08). 21 of 21 claims pass the checker, 1/1 plant caught. EO 10169 and 10390 are recorded as blocked (`instruments/REMNANTS.md`).
  - Sinclair mend II/III: 9 NO proposals written (EO 11209, 13555, 9294, 9762, 10704, 12573, 13975, 12604, 11796), 2/2 plants caught. Owner adoption batch is now **56** (Bowditch 15, Sinclair 41).
  - Tycho: 32 PEB report dates landed. **0** orders can close without the owner's report-deadline ruling; **47** depend on it. Re-rank: `research/production/day-review-2026-10-20/RERANK-evening.md`.
  - Ready for human review was 230 at 16:45Z, before these claims were counted. Certified: 0.
- **Running:** Lambertini IV (16 orders, probe gate in code). EO 9830 probe (10 ACT records, then claims; scale only if at least 4 of 10 enable claims).
- **Process lessons:**
  - (a) Overlay proposals must be frozen and proposed with no push in between. Every Run jobs run regenerates claim-kit output, which gives `stale_compiled_generation`.
  - (b) `python3 -I jobs/claim-kit/kit.py` fails on imports; run it without `-I`.
  - (c) Workflow scripts must handle a null agent result. A session-limit hit at 14:30Z killed agents mid-run; resume from the journal works.
  - (d) The PR for this branch is #40.
- **Next:**
  1. Read the Lambertini IV and R9830 results, then scale whichever passes.
  2. After the next ladder run, check the 43 remaining Lamm III PEB lines.
  3. Pre-stage the EO 12553 emergency-board packets so they can run as soon as the ruling lands.
- **Asks:** `@Owner`:
  1. Report-deadline ruling (47 orders now, about 89 in all).
  2. Adopt the 56 NO proposals?
  3. EO 14052 strike-and-reinsert reading (does a delete-and-insert end the clause?).
  4. The transcription-as-copy and Lamm readings are still pending.

## 2026-10-20 ET: Merged PRs #38, #40, #42-#45 into main; Domesday tool audit

- **Done (owner consent to merge everything):** integrated on `claude/dazzling-gates-4xkkzo`, then into main.
  Merge order: #40 junto, #43 Valla, #44 portfolio repair, #45 NORTON (supersedes the closed #41), #42 NEYMAN, #38 ProQuest.
  `astra/apollo-audit-20261020-1407utc` (no PR) was already contained in #44's notes.
  Generated `jobs/*/output` conflicts were resolved by taking the newer side, then regenerated by the runner.
- **Conflict decisions:** both Valla and repair holds on EOs 13792/13101/13148/13783/13807 kept (one finding, two reviews).
  Junto keeps the repair's stricter missing-quality rule, which NEYMAN had also fixed independently, plus NEYMAN's
  embedded `test_contract` check. A new `origin_kind()` stops string origins from crashing `check`.
  corpus-excavator `measure.py` takes both `--closures` and `--baseline-receipts`.
- **ID renumbering** (parallel branches reused ids):
  - Junto: NORTON C-14/R-4 → C-15/R-5; NEYMAN C-14..16/R-4 → C-16..18/R-6.
  - Llull: repair outcomes O-44..46 → O-49..51; NORTON L-56/O-44 → L-65/O-52.
  - Rows carry `renumbered_from`; Llull now proves a renumbered forecast against its original registration
    (L-65 verifies as preregistered at 4d456ec).
  - `jobs/neyman-pilot/output/junto-ledger/` is that pilot's isolated copy and keeps the old ids.
- **Fixes found by tests:** NEYMAN's Junto test was updated to the merged evidence rule. Mountweazel had a
  blinding leak: claim-kit's provenance block appeared on some real claims only, so it is now stripped from packets.
  All local suites pass except claim-kit's 35 status-overlay tests, which only need the runner's rebuild
  ("run claim-kit build once").
- **Audit:** `research/plans/DOMESDAY_TOOL_AUDIT_2026-10-20.md`. All 225 ready orders came from claim batches.
  The meta-tools (Junto, Llull, Polya, NEYMAN, NORTON, Hamilton, Valla, Mountweazel) have $0 verified savings.
  Recommendation: build no new tools; run claim batches on ~890 judgment-only drafts, drain source-ladder online,
  and wire unused acquisitions (csc-annual-reports branch, hathi, wikisource and others) into the tracker.
- **Asks:** `@Astra` / `@Codex` / `@Sol`: allocate ledger ids per agent (e.g. `C-sol-…`) so parallel branches cannot
  collide; register NEYMAN's three candidates as `contracts.jsonl` contracts and stop using embedded `test_contract`.
  `@Owner`: the report-deadline and transcription-as-copy rulings unlock the most orders.
- **Do not:** reuse the old ids above; reopen #41.

## 2026-10-20 ET (evening): handoff to a fresh coordinator

- **Since the afternoon entry:**
  - Lambertini III: 52 of 82 upheld, 49 pass the checker.
  - Y2LEAD probe: 7 of 50 upheld; the gate failed and the line stops.
  - Lamm III: 2 claims, plus 84 PEB report-date fetch lines.
  - Near-ready fix-ups: 4 claims.
  - Sinclair re-freeze: the owner adoption batch is now 47 NO proposals (Bowditch 15, Sinclair 32).
- **Expected:** ready count rises from 176 by about 60 once the tracker runs on these claims.
- **Next for the new coordinator** (follow `research/plans/CONTINUOUS_PROTOCOL.md`):
  1. Lambertini III batch 02 (8 claims, never reviewed) and re-review of EO 14055, 13986, 13123 and 5624.
  2. Sinclair EO 11209, 13555 and 9294 producer fix.
  3. When the PEB report dates land (84 queued), report-relative claims, after the owner's report-deadline ruling.
  4. Re-run the day review (Llull rank).
- **Lines stopped:** Craigellachie, Y2LEAD, and the Lamm sunsets are exhausted.

## 2026-10-20 ET (afternoon): continuous run, ready 135 -> 176

- **Done:**
  - Claims from Lambertini (per ending instrument), Rastell (EO 12553), Lamm (sunsets) and Bowditch Y2 made 41 of 45 claimed orders ready.
  - claim-kit now ingests reviewed, hash-checked agent-located ACT records (`jobs/claim-kit/act_overrides.py`; 163 records).
  - source-ladder gained Panizzi I/II routes, including report dates via NMB, WCPD and Public Papers.
  - Mountweazel planted controls: plants now live in scratch copies only.
  - Sinclair Y1 sweep: 35 NO upheld of 150, proposals only.
  - Day review: `research/production/day-review-2026-10-20/REPORT.md`, with ranked next workflows and cost per ready order (Lambertini about $1.55, Lamm about $4.40).
- **Protocol** for workflows: a shared PROTOCOL in the coordinator's scratchpad, summarised here.
  - Preregister Llull forecasts (ledger-only commit, no push).
  - Use an independent Opus reviewer with held sources and a D6 step.
  - Producers write to scratch; the planter plants in a scratch review copy; only the tally writes into `research/`.
  - Never retry an auto-mode denial.
- **Push discipline:** never push while a Run jobs run is in progress on the branch. A push makes that run's "Commit results" fail, which lost two claim-checker runs today. Batch commits and push once.
- **Process defects found:**
  - Sinclair's script ran every batch even though the probe gate failed (4 of 5). Gates must be enforced in the workflow script.
  - Sinclair batches 01-05 are stale-generation and need a re-freeze.
- **Next (day-review ranking):**
  1. Lamm III sunsets and the PEB report-date queue (running).
  2. Lambertini III (running).
  3. Near-ready fix-ups (about 7 orders).
  4. Y2LEAD probe of 50, excluding EO 12553 targets.
  5. EO 12553 emergency-board claims (89 orders, about 52 ready) after the owner's report-deadline ruling and PEB dates.
  6. Report-relative claims as dates land.
- **Asks:**
  - `@Owner`, ranked by orders unblocked:
    1. Report-deadline ruling: about 52 ready soon, the most of any ruling.
    2. Transcription-as-copy: Lamm retirement exemptions.
    3. Y1 batch adoption: 15 rechecked, plus 35 Sinclair and 6 current.
    4. ProQuest/NYU request.
    5. Lamm "further exempt" and "until" readings (EO 8554, 8392, 8828, 8058, 7300, 6933).
  - `@Astra`: Lambertini P1 claims EO 10249, 10897 and 12262 overlap your BATCH1_RESERVATION; please reconcile.

## 2026-10-20 ET: thinking tools (Llull, Polya, Mountweazel), Craigellachie, Panizzi; continuous run paused at cost cap

- **Done:** `jobs/llull/` checks plans before they run: Brier forecast ledger, prerequisite census, premortem
  wheel, rank, selfscore. Postmortem of 23 past plans: 12 of 15 scored plans missed, median delivered/forecast
  0.036, 10 of 12 misses mechanically predictable. `jobs/polya/` measures alternative units of work: owner
  rulings reach 89% of not-ready orders; no frame reaches savings_residuals or counterevidence.
  `jobs/mountweazel/` calibrates reviewers with planted defects. MW-C2 caught 9/10 (Opus, packet only),
  8/10 (Opus with sources) and 6/10 (Sonnet); all missed one D6 (removed later event). Use Opus with
  sources plus a D6 step. Bowditch Y1's 0/15 certifies nothing.
  Craigellachie: 23 last-step orders, 0 upheld, all blocked on unheld sources (27 FETCH lines).
  Panizzi: `jobs/source-ladder` now routes citations embedded in prose, plus Public Law and Reorganization
  Plan routes, queue-first (50 items per run); expect about 37 real documents per run.
- **Running:** the source-ladder Actions run from commit b5aeb93d0. Check `jobs/source-ladder/output/STATUS.json`,
  then retry Craigellachie and Bowditch-Y2 orders whose sources arrived (Llull rank #2: Y2LEAD batches).
- **Next (continuous queue, 3 workflows at a time):**
  1. Retry claims after fetches land.
  2. ACT-provision producer probe (reach 1,213).
  3. A unit for savings_residuals and counterevidence.
  4. Own-term family probes.
  5. Mountweazel check fix for D8 false positives.
  6. Routes for 36 unservable lines (report dates, land records).
- **Cost:** session $87.5 of token value; paused at the owner's $100/day cap.
- **Asks:** `@Owner`:
  1. Raise the cap to continue?
  2. Batch adoption of reviewed statuses (reach 11,613)? Re-review Y1 with Opus plus sources first.
  3. Send the ProQuest/NYU request?
  4. Is a compiled transcription an acceptable copy (codebook reading)?
  5. 138 ready and 0 certified: should human review start?

## 2026-10-20 ET: Panizzi, source-ladder now resolves citations buried in prose and works the queue first

- **Done:** `jobs/source-ladder/embedded_cites.py` (+ `ladder_queue.py`, `fetch_ladder.py`, `plan.py`, `job.py`, README,
  `test_panizzi_resolvers.py`; 77 tests pass, and the tests of the jobs that import the ladder pass). Prose-only FETCH_QUEUE
  lines are split into one item per embedded Stat./Pub. L./FR/U.S.C./CFR/Reorganization Plan cite. New routes: Public Law
  by Congress and number (govinfo statute link service, checked back to 52 Stat.), and Reorganization Plan through the
  Title 5 Appendix heading, then the plan's own Stat./FR page. Default plan: queue-first, 50 items, 300 requests, 800 MB.
- **Review fixes (same day):** a Public Law or plan is no longer dropped because of an unrelated Stat. cite (only a cite in a
  volume of that Congress drops it); `5USC3345etseq` gives section 3345; a prose line with a link falls back only to the
  official copy of the SAME document as its link; no Wayback copy of the Title 5 Appendix, and a U.S. Code compilation is
  rejected as a plan's source; the eCFR renderer-API route was removed (robots.txt disallows it); a govinfo PREMIS/MODS
  metadata file is logged but never accepted as the document; no-route items are recorded before the plan.
- **Preview (container, not committed):** the default plan worked 50 queue items: 44 found, 6 retry_later, 108 requests,
  389 MB, 654 s. Of the 44, 5 are NARA finding-aid pages given by the requester and 1 was PREMIS metadata (now rejected).
- **Running:** pushing a non-`output/` change under `jobs/source-ladder/` (or to `research/readiness/`) starts the Actions job.
  Check `jobs/source-ladder/output/STATUS.json`, then `SUMMARY.json` (`found`, `embedded_cite_items`, `bytes_downloaded`).
- **Not fixed:** 52 queue lines still have no route (report dates, land records, agency orders, pay calendars and others);
  files over the shared 100 MB per-file pool bound (27 FR 2983 and 45 FR 44245 issues, 95 Stat. 357 granule).
- **Do not:** treat a found statute or CFR page as authentication, or a current CFR/Code edition as the text in force at the
  order's date (5 CFR 6 is served as the 2026 edition, which does not answer the 1953 question).

## 2026-10-20 ET: Bowditch, the Y2 claim-factory probe failed its gate and Y1 passed

- **Done:** random probe of the funnel plan (`research/excavator/bowditch-2026-10-20/REPORT.md`). **Y2** covered 50
  orders drawn from the 2,022 modern orders with a status and text but no claim. **3 upheld (6%, test needs
  ≥50%)** and 2 of 5 rejected (40%, test allows ≤11%), so it was **not scaled**. Claims are in
  `research/readiness/claims/claude-bowditch-y2-0{1,2}-2026-10-20.jsonl`; all pass the checker. Expect 0-3 new
  ready orders after the Actions tracker run.
  **Y1** covered 50 of the 4,271 no-status modern orders. 15 NO proposals were accepted, with 0 of 15
  reviewer disagreements (limit ≤11%) and about 1.5 agent-min per accepted status (limit 5): **passes**.
  The reviewer came from the same model family, and nothing was adopted.
- **Finding:** Y2 is blocked by missing inputs, not by agent effort. Most orders have no held TERM/ACT ending
  instrument or CURRENT predicate. The probe added 53 FETCH_QUEUE requests. Next: an unblocker that fetches
  ending instruments and current-law predicates in bulk (a job, not agents), then probe Y2 again.
- **Cost:** about $21 of token value for 10 agents (session total $31.67 including Junto).
- **Asks:** `@Owner`: (1) adopt the 15 Y1 NO proposals via batch PR (idea 2 in the funnel plan)? (2) rule on EO
  12080 (spent amending order), 12086 (ledger NO possibly contradicted), 14125 Sec. 4, 9704.

## 2026-10-20 ET: Junto, a scored ledger of token-saving finders

- **Done (branch `claude/junto-1727`):** design `research/plans/JUNTO_DESIGN.md`; `jobs/junto/` (append-only ledger,
  `junto.py run|score|allocate|propose|add-test|check`, 19 stdlib tests); three finders: Hamilton (fitted),
  Clausewitz (friction) and Gallatin (wasted work); five more catalogued but not built. First run:
  `research/production/junto-2026-10-20/REPORT.md`. It produced 13 candidates, **all unverified; every finder
  scores 0 verified $**. Score = verified $ saved / ($ spent + $2 prior). Only `add-test`, with measured before
  and after values, can verify a saving.
- **Next tests:** Watchman (about $1 marginal), Revere (about $3 marginal, on a planned Y1 phase; fix X1's
  phase count first), idle-cache avoidance (about $2).
- **Build cost:** $10.18 of token value and 49 M cache reads in about 50 min, against an estimate of $12-25.
  Hamilton on the coordinator thread: narration 27%, fixed setup 26%, system/user messages 17%.
- **Gap:** session 017gGL is only about 9% read (page 52 copy was blocked by auto mode, and not worked around).
- **Asks:** `@Astra` / `@Codex`: log any saver you try with `junto.py add-test`; never enter estimates as savings.

## 2026-10-20 ET: Hamilton, a token audit of agent sessions

- **Done:** `jobs/hamilton-token-audit/` (offline profiler of `list_events` transcripts) and its first audit,
  `research/production/hamilton-2026-10-20/REPORT.md`. Findings: in X1 the coordinator thread was 72% of
  input-side cost (median context 421 k) against 28% for the 11 helpers doing the research. Fixed setup is about
  70 k tokens per call. Waiting (status checks, a cache rebuild after an idle hour) was about 15%.
- **Proposed tools (probe before build):** Revere (phase handoff to fresh sessions), Watchman (monitoring outside
  big sessions), a setup trim measured by first-call context, and a quiet protocol.
- **Asks:** `@Astra` / `@Codex`: keep coordinators short-lived; start a fresh session per phase with a state file.
- **Do not:** commit raw transcripts. Auto mode blocked one copy of the Oct 16-17 session's transcript as possible
  exfiltration; it was not worked around.

## 2026-10-20 ET: refreshed remaining-work figures; gated funnel for the next excavators

- **Done (branch `claude/great-ptolemy-9r6zah`, restarted from main f57cffe8):** reran `build_remaining_work.py` and
  `build_effort.py` (code untouched; X1 owns it): 135 ready, 86,572 open steps, 16,178 agent-hours (was 17,144;
  APP and CSC transcriptions moved about 3,200 old orders to cheaper text and clause tiers). Dashboard updated:
  https://claude.ai/artifact/531KGTebdrgdeUitKhp8du. New plan `research/plans/EXCAVATOR_FUNNEL_2026-10-20.md`,
  sized only by orders that pass their prerequisites.
- **Finding:** 4,274 modern (1937+) orders have no provisional status, yet 4,273 already have status-history or OFR
  catalog records and 3,952 have their Federal Register text. They are the cheapest pool; both my series plan and X1
  skipped them. 2,150 more modern orders have status and text and wait on claim work.
- **Next:** probes before builds. Y1 modern status sweep (50 orders through `status_overlay`, then a draft
  batch-adoption pull request to `DECIDED_CASE_COMPLETENESS_RECONCILED.csv`, not merged); Y2 claim factory on 50 random
  modern status-plus-text orders, plus the own-terms mechanism.
- **Asks:** `@Owner`: yes/no on batch adoption pull requests; whether to send the NYU ProQuest access request.
  `@Astra` / `@Codex`: whoever picks up Y1 or Y2, record minutes and tokens per order from harness telemetry.
- **Do not:** quote hours saved for Y1-Y3 before their probes run; merge status rows without the owner.

## 2026-10-19 14:10 ET: owner declined paid or manual microfilm acquisition

- **Decision (owner):** no paid reproduction (Harvard Film S 1130 quote estimated at roughly $1.5k-4k) and no
  hand-scanning of microfilm. X3 must rely on free sources: HathiTrust via the owner's NYU login (public-domain PDFs,
  optional, owner's choice), existing jobs, and the negative-search automaton. Do not plan around the reel set.
- **Asks:** `@Astra` / `@Codex` / X1 session: do not request paid copies or manual scanning from the owner.

## 2026-10-19: gap orders routed to public sources; csc-annual-reports job started (branch `csc-annual-reports`)

- **Done:** ProQuest Congressional (owner's NYU login) surveyed: Presidential Materials 1789-1936 hold
  53,671 records, 9,503 tagged Numbered Executive Orders, each with a PDF scan ("Replica of Original").
  Details in `research/pre-1937-sources/PROQUEST_CONGRESSIONAL.md`. The 3,593 `PRIORITY.txt` ids minus 30
  in HathiTrust public volumes = 3,563 (`PROQUEST_RESIDUE.txt`). Routed each by the full WPA/Lord list
  (`wpa-lists` branch): `GAP_ROUTES.md/.csv`. Results: 840 cite a Civil Service Commission annual report;
  about 90 are candidates in other compilations; 2,635 have no known printing (NARA RG 11 or ProQuest only).
- **Running:** `jobs/csc-annual-reports/` fetches the CSC annual reports from the GovInfo Serial Set
  (public PDFs) and cuts each WPA-cited order from its date line. An offline trial on FY 1917 located 67 of
  68 orders. Check `output/SUMMARY.json` (orders_located, by confidence) and `CITATION_RESULTS.csv` for
  misses. Outputs are `compiled_transcription_lead` fragments with `acceptable_as_original: false`.
- **Next:** extract the Panama Canal 1922 and Kappler IV candidates (archive.org texts are free);
  HathiTrust vol. 2 of the Indian reservations orders needs a person in a browser (Cloudflare).
- **Asks:** `@Owner`: `ACCESS_REQUESTS.md` has drafts for NYU (bulk ProQuest access) and NARA (API key), not
  sent. `@Astra` / `@Codex`: the CSC fragments are report printings, not originals; grade them as leads.
- **Do not:** run a bulk ProQuest harvest through the owner's NYU session without NYU's written approval;
  treat WPA dates as verified signing dates.
## 2026-10-19 13:15 ET: X1 lifecycle class engine built, piloted on all 52 eligible old orders, recalibrated

- **Done (branch `claude/x1-class-engine`, PR to main):** `jobs/x1-class-engine/` (zero-token job): type
  classifier for all 8,014 pre-1937 orders (`TYPES.csv`; 198 unknown), 22 type rules in
  `research/readiness/type-rules/` (`eo-type-rule/v1`, three rounds of independent AI review, frozen hashes),
  5-event extinction register (`data/EVENTS.json`; 8 primary sources queued, none held yet), look-alike clusterer
  (656 texts, 132 clusters, 187 clean clones), 128 batch sheets. Report: `research/production/x1-2026-10-19/REPORT.md`.
- **Measured:** classifier on a fresh blind holdout of 80: exact type 90% (CI 82-95%), class 95%. Pilot: all 52
  pre-1937 orders that have both a provisional status and a held text (the canonical path's ceiling), in two batches;
  6 submitted, 5 upheld by an independent AI reviewer, 1 rejected (17%, above the 11% target); 46 blocked, all
  blocks confirmed. 25.4 agent-minutes in all: 0.49 min per order screened, 5.1 min and 153k tokens per accepted
  claim (harness telemetry, `AGENT_TELEMETRY.jsonl`). Claims: `research/readiness/claims/claude-2026-10-19-x1-pilot.jsonl`
  (EO 5614, 5707, 5881, 5981, 5982); actual claim-checker passes all 5 on every step, and the tracker on the branch now counts them ready for human review (130 → 135). PR #36.
- **Recalibrated** (`MEASURED.json`, `excavator_scenarios.py` now reads X1 types and measured values): X1 saves about
  463 h (assumed 4,134 incl. the unapproved review change); about 16,681 h left after X1; series without risk-tiered
  review about 11,256 h. Bug found and documented: census-gap rows were counted as "other", not land.
- **Finding:** typing is not the bottleneck for old orders; originals, end instruments and provisional statuses are.
- **Asks:** `@Owner`: (1) risk-tiered review stays off (flag `X1_RISK_TIERED_REVIEW`, default off) until you decide;
  (2) a route to CSC annual reports / Official Register would date the 1,490 one-person waivers. `@Codex` / `@Sol`
  (claim-kit): an own-terms end mechanism (EO 5763, 5930 blocked only by this) and locating the EO 7968 and EO 5707
  provisions in dossiers (6 rows). `@Astra`: EO 5874 is recited by EO 5881 but is not in the identity universe;
  check as a census gap. Anyone: the 5,297 `status_first` rows need a provisional-status path before X1 sheets help.
- **Do not:** treat X1 types, rules, events or clones as findings; enable risk-tiered review without the owner;
  reuse the round-1/2 rule files (superseded; only hashes in `TYPE_RULES_REVIEW.json` are frozen).

## 2026-10-19 13:30 ET: excavator series plan to cut the remaining agent-hours

- **Done (branch `claude/great-ptolemy-9r6zah`):** `research/plans/EXCAVATOR_SERIES_2026-10-19.md`, a funnel of ten
  ideas and a selected series of five excavators (X1 lifecycle class engine, X2 Public Land Order ledger, X3
  reel-to-text acquisition with a negative-search automaton, X4 living-law counter-search, X5 census gap admission
  line). `research/progress/remaining-work/excavator_scenarios.py` scores each idea alone and the series without
  double counting: 17,144 to about 9,100 agent-hours (47% less). Coverage sets come from committed data; hit rates and
  new minutes are assumptions in the script. `build_effort.py` now exposes `assign()`; outputs unchanged.
- **Finding:** 83% of the hours are pre-1937 orders; 7,065 h are pre-1937 orders of unknown type, so a type classifier
  is the first build.
- **Asks:** `@Owner`: (1) a route to a full-text source for EO 1-7403 (microfilm Film S 1130 at Harvard Lamont, or
  HeinOnline via a law library); (2) yes/no on risk-tiered review (20% independent-AI audit for rows matching a
  reviewed exemplar). `@Astra` / `@Codex`: pick up X1 step 1 (type classifier) or X2 (PLO harvester) as jobs; pilot
  50 orders and record minutes per step and tier.
- **Do not:** treat the scenario savings as measured, or let any excavator fill judgment fields or admit orders.

## 2026-10-19 12:30 ET: remaining work weighted by AI effort (second treemap tab)

- **Done (branch `claude/great-ptolemy-9r6zah`):** `research/progress/remaining-work/build_effort.py` gives every
  open step (same 86,607 as the count view) an AI agent-minute weight from `EFFORT_MODEL.csv`, by tier: what the
  jobs already hold for that order (clause-drafts, status-history, later-events, family-rules certificates,
  fr-originals, numbered-early-orders, claim-drafts `only_judgment_left` and `estimated_effort`). Method and the
  basis of each weight: `EFFORT_NOTES.md`. Outputs `EFFORT_LONG.csv`, `EFFORT_BY_TIER.csv`, `EFFORT.json`. Shown as
  the "AI effort" tab of https://claude.ai/artifact/531KGTebdrgdeUitKhp8du#effort. `build_remaining_work.py`
  now exposes `attribute()`; its outputs are unchanged.
- **Result:** about 17,144 agent-hours (range 8.6k-34k), about 63 min per APP order. Ending/current basis 5,625 h,
  original text 3,025 h, savings 2,612 h, counterevidence 2,297 h, clauses 1,889 h, first yes/no 1,337 h, admit
  328 h, sources/images 18 h. Pre-1937 orders about 90-108 min each, modern about 25 min. FDR, Wilson and Coolidge
  together 47%.
- **Calibration:** only CI1+EB2+SR2+CE2 (25 min) are calibrated, from Codex's batch pilot (about 26 agent-min per
  upheld modern dossier, `research/excavator/2026-10-18/batch-pilot/COST_COMPARISON.json`); OT1 uses Astra's
  measured source-read time; all other weights are assumptions.
- **Asks:** `@Astra` / `@Codex`: when the instrumented 40-80 order pilot runs, record agent-minutes per step and
  tier so `EFFORT_MODEL.csv` can be replaced with measured values; the build reruns in seconds.
- **Do not:** quote the agent-hour total as a measurement or a schedule.

## 2026-10-19 11:45 ET: remaining-work treemap against the APP count

- **Done (branch `claude/great-ptolemy-9r6zah` from main `a6d61007`):** `research/progress/remaining-work/build_remaining_work.py`
  (offline, reads committed outputs only) writes `REMAINING_WORK.json`, `REMAINING_WORK_BY_PRESIDENT.csv` and
  `REMAINING_WORK_LONG.csv`. Unit: one open readiness-tracker step for one order. Orders APP counts but the project
  does not hold (per president, APP count minus project orders, when positive) each add one "admit" step plus the six
  core steps. Owner's treemap dashboard: https://claude.ai/artifact/531KGTebdrgdeUitKhp8du (private until shared).
- **Measured:** APP counts 16,239 orders; the project holds 14,972; 1,314 APP-counted orders are not yet held (net
  1,267; Coolidge has 44 more in the project than APP counts, 18 NARA unnumbered rows sit outside any president's APP
  count by date). 86,607 open steps vs 13,503 done (13.5%). 130 ready for human review. Open steps by kind: ending or
  current basis 16,152; savings 16,120; clause inventory 16,108; counterevidence 13,816; first yes/no 12,927;
  original text 9,414; admit 1,314; shared sources + Opus media 756.
- **Attribution of orders to presidents:** APP index 9,918; exact WPA/NARA/Lord date 3,122; numbered neighbours
  agreeing on both sides 1,772; year only 158; nearest neighbour 2. Boundary years can still be off by a few orders.
- **Next:** rerun the script after each readiness-tracker run; it is cheap (seconds).
- **Asks:** `@Owner`: share the dashboard from its Share menu if others should see it.
- **Do not:** read the per-president gap as a census finding; APP's pre-1945 counts are editorial (Ragsdale/Lord).

## 2026-10-18 20:15 ET: app-executive-orders, live lane finished; capture audit 205/205 agree; PRIORITY rebuilt (3,593)

- **Done (branch `app-executive-orders`, one commit):** the live lane completed at 23:58 UTC (`output/STATE.json`
  remaining 0, complete true, 0 failures; 792 live pages, 10,270 archive captures, 10,998 texts). Harvester and the
  resume loop have exited; **no APP crawler is running.** `output/MIRROR_AUDIT_SUMMARY.md`: every 50th
  archive-covered path in path order (206), fetched live at 10 s between 23:05 and 23:58 UTC; **205 of 205 compared
  texts agree byte-for-byte** (Common Crawl 194/194 across capture years 2024-2026, Wayback 11/11 across 2022-2026);
  no disagreements to list; page hashes differ on all 205 (chrome, expected). The 206th sample path (EO 5382) had
  been fetched live before the archive reached it; its recorded hashes agree too. `data/PRIORITY.txt` rebuilt:
  **3,593 numbered census orders have no saved text of any kind** (was 6,070). **3,585 of them APP does not list at
  all** (3,529 below EO 5000, 56 at EO 5000+, e.g. EO 5000-5018, 6447-6466). The other 8 are listed but APP's page
  is "[Not Published.]" (EO 8302, 9132A, 9427A, 9451A, 9457, 10026A, ...). So the APP lane is exhausted: nothing
  left to fetch from APP.
- **Fix in `build_priority.py`:** claim-kit's discovery globs `FRAGMENTS*.jsonl`, so the archive lane's
  `MIRROR_FRAGMENTS.jsonl` (9,387 records) was invisible and the plain rebuild gave 5,652, leaving 2,059 orders with
  saved archive text on the list. The builder now also counts this job's own fragments (hash-verified): +2,090 held.
- **Caveat:** 183 ids absent from the 16:36 list reappear now (e.g. EO 28, 29, 219, 860, 1136); they are `open` in
  the readiness tracker and in no job's FRAGMENTS/SOURCES, so I could not see what held them earlier. Cause not found.
- **Next:** second index pass with a different sort for the 38 duplicate listing rows; owner's decision on the
  Common Crawl captures (19:15 entry) still open.
- **Asks:** `@Astra` / `@Codex` (whoever maintains claim-kit): decide whether `jobs/claim-kit/inputs.py` discovery
  should match `*FRAGMENTS*.jsonl` so the 2,090 archive texts reach the readiness pipeline, or whether the archive
  lane should write `FRAGMENTS_MIRROR.jsonl` instead; I changed neither. Also: `load_corpus` emits 1,310
  `text_sha256 mismatch; skipped` warnings for FRAGMENTS records in family-rules (582), ofr-compilations (500),
  isthmian-canal-1911 (105), richardson-volumes (68) and indian-reservations-1912 (55) that point at
  `jobs/clause-drafts/output/texts/cd-job-fr-originals-*.txt`; the files match their git blobs, so the recorded hashes
  are stale (clause-drafts regenerated texts after those jobs ran). 728 orders lose their held text in claim-kit
  until those jobs rerun. `@Owner`: the archive lane's stance question (19:15 entry) still needs your call.
- **Do not:** hand-edit `jobs/app-executive-orders/output/`; count APP or capture texts as originals.

## 2026-10-18 19:15 ET: app-executive-orders, archive lane: 30 h crawl collapsed to a 67-page residue

- **Done (branch `app-executive-orders`, commits `5d97ee47`, `78e7d795` + outputs):** `jobs/app-executive-orders/app_mirror.py`,
  an archive lane that reads public web-archive captures of the same APP pages instead of asking APP: WARC byte ranges
  from Common Crawl (`data.commoncrawl.org`, crawls 2024-10 to 2026-04) and original bytes from the Wayback Machine
  (`web.archive.org/web/<ts>id_/`). It never sends a request to APP, so it runs four workers. Result: **10,270 pages in
  about 55 minutes** (9,861 Common Crawl, 409 Wayback), `output/MIRROR_DOCUMENTS/SOURCES/FRAGMENTS.jsonl` (9,387
  claim-kit fragments for numbered orders), `texts/` now holds 10,727 order texts. 47 captures hold no text
  (APP's own "[Not Published.]" pages, recorded in `MIRROR_FAILURES.jsonl`); 66 index pages have no capture anywhere.
- **Live lane:** `app_harvest.py documents` now skips every archive-covered path except an `--audit-every 50`
  sample (about 205 pages) that it fetches live and compares in `MIRROR_AUDIT.jsonl` (text and page hash agreement
  plus capture date), so the captures carry a measured staleness rate. The residue it still owes APP is **67 pages**
  (44 priority orders), about 11 minutes at 10 s. APP answered HTTP 504 twice tonight (21:53 and 22:26 UTC) and the
  harvester stops on 5xx by design; a resume loop on the owner's PC (`%LOCALAPPDATA%\Temp\live_resume_loop.ps1`,
  log `~/.cache/app-documents-2.log`) reruns the documents phase after a ten-minute pause, at most six rounds, never
  retrying the failed request immediately.
- **Caveats for readers of the captures:** a capture is the APP page as of its capture date (2018-12-09 to
  2026-10-16; each record names archive, crawl and `captured_utc`), route `archive/<archive>/american-presidency-project`,
  grade `mirror_transcription`, `acceptable_as_original=false`. APP's robots.txt now disallows CCBot outright, so the
  2026 crawls hold nothing and the captures predate that rule; the owner should judge whether reading those public
  datasets fits the project's stance toward APP. Nothing here changes census, ledger, codebook or certified counts.
- **Next:** read `MIRROR_AUDIT.jsonl` once the audit sample is in and report the disagreement rate; rebuild
  `data/PRIORITY.txt` against the new texts; second index pass with a different sort for the 38 duplicate rows.
- **Asks:** `@Owner`: decide on the Common Crawl captures (above); approve committing crawl progress as it lands.
  `@Astra` / `@Codex`: `MIRROR_FRAGMENTS.jsonl` is discovery material only, same as `FRAGMENTS.jsonl`.
- **Do not:** run a second APP crawler while the resume loop is alive; hand-edit `jobs/app-executive-orders/output/`.
## 2026-10-18 17:15 ET: numbered-early-orders, printed texts for 184 of the 3,324 undecided orders 1-5075

- **Done (branch `numbered-early-orders` from main `224fd70c`, PR to main):** `jobs/numbered-early-orders/`
  matches the 3,324 census all-no numbered orders below 5076 (`data/TARGETS.csv`, with the WPA 1944 date and
  summary from `wpa-lists` commit `121ca07e`) against printed books, by number or by exact date plus
  summary words. It imports early-orders-hunt unchanged and declares hits in wikisource-texts' shape
  (`government_printed_copy`, `acceptable_as_original=false`, book URL, image, page, line span, hashes).
- **Measured (local run):** 184 orders, 197 texts. 41 came from books already held (MR 1916 37, MR 1910 2,
  Richardson IX 2, IR 1912 1). 143 came from new books: Civil Service Commission reports for FY 1914, 1915,
  1918 and 1922 (95), Kappler IV (26), Official U.S. Bulletin (17), Panama Canal 1921 (6). Kappler III gave
  0. 3,140 orders still have no text. claim-kit's loader recognized all 197 texts with no warnings.
- **Blocked:** the Archive holds only four 1908-29 CSC reports. The full run is on HathiTrust behind a
  Cloudflare bot challenge, not fetched. The Archive's 1975 Indian-reservation reprint is a lending copy.
- **Known false positive:** EO 860 matched on a citation inside a later order. Every hit must be read
  against the scan.
- **Running:** the job's first GitHub run on this branch. Check `output/STATUS.json` and `SUMMARY.json`.
- **Asks:** `@Owner`: a sanctioned route to the remaining CSC annual reports (1909-13, 1916-17, 1919-21,
  1923-29) would reach most of the remaining 695 civil-service waivers.
- **Do not:** count these texts as originals or as decided orders.

## 2026-10-18 16:45 ET: app-executive-orders, American Presidency Project index, statistics and texts

- **Done (branch `app-executive-orders` from main `224fd70c`):** `jobs/app-executive-orders/app_harvest.py`
  (phases `statistics`, `index`, `documents`; offline tests in `test_app_harvest.py`). The full APP
  "Executive Orders" category index is committed: 10,840 documents (1791-01-22 to 2026-10-16), 9,949 distinct
  numbered EOs, 890 unnumbered (`output/INDEX.csv/.jsonl`). The APP statistics table (65 rows, by president
  and term, last updated 2026-10-16) is committed with its methodology, notes and sources (`output/STATISTICS.*`).
- **Priority:** `build_priority.py` → `data/PRIORITY.txt`: 6,070 numbered census orders with no saved text
  (claim-kit loaded texts ∪ readiness-tracker `step_original_text=done`). 2,661 of them are on APP, mostly
  EO 5000-8999 (Hoover/FDR); the documents phase fetches those first (about 7.5 h), then the rest.
- **Running (owner's PC, detached):** `documents` phase, one request per 10 s (APP robots.txt Crawl-delay: 10;
  APP blocks AI-training crawlers by name and reports stability problems, so do not parallelise requests or move
  this to a runner while it runs). Log `~/.cache/app-documents.log`; progress `output/STATE.json`. Rerunning
  resumes. Output per order: text, APP footnote (Federal Register note or APP editorial note, e.g. EO 1071's
  Richardson misidentification), citation/node, categories, raw-page SHA-256; FRAGMENTS.jsonl in claim-kit shape.
- **Caveat:** the listing produced 38 duplicate rows across pages (sort ties shifting during pagination), so a
  few documents may be missing from the index; a second index pass with a different sort would check it.
- **Asks:** `@Astra` / `@Codex`: APP texts are `secondary_compilation_transcription`,
  `acceptable_as_original=false`; use them for discovery and clause reading, not custody. `@Owner`: commit
  crawl progress now and then (`git add jobs/app-executive-orders/output && git commit`).
- **Do not:** count APP texts as originals or decided orders, or run a second APP crawler concurrently.

## 2026-10-18 14:30 ET: census-completeness, a measured answer to "have we looked everywhere?"

- **Done (branch `census-completeness`, stacked on `early-orders-hunt`; local only, nothing pushed):**
  - `jobs/census-completeness/`: treats every list of pre-1900 orders the project holds as a capture of one population
    (Lord 1943; Richardson VI/VII/IX documents from `richardson-volumes`; the 1912 Indian-reservation acts; dated
    "Executive order" mentions read from the MR and GLO books `early-orders-hunt` fetched; the WPA numbered list is
    kept only to set numbered orders aside), matches mentions conservatively (same day and a shared distinctive word,
    or a citation link the earlier job made; a date alone never matches), and estimates the undiscovered remainder
    per era with the Mt maximum-likelihood estimate (Darroch) and its asymptotic interval, Chapman two-list estimates
    against Lord, and Chao1 as a check. Three matching scenarios bracket the result (strict, blind-only, every
    same-date pair as one order). Assumptions and the direction of each bias are written into the outputs. 12 tests,
    including recovery of a synthetic hidden population of 400.
  - `data/SOURCE_UNIVERSE.csv`: a 40-row series-level map of where orders could be (NARA record groups 11, 45, 56,
    59, 75, 94, 107, 48/49; LOC presidential papers; Founders Online; the printed compilations; newspapers) with
    each series' search status in this project. Only 8 rows are `searched_to_end`.
  - `research/plans/SCAN_REQUESTS_2026-10-18.md`: three draft reference/scan-request emails (NARA Archives I for
    RG 107 letters received 1789-1861; NARA for GLO/BIA reservation files; LOC Manuscript Division for the
    1841-1861 presidents' outgoing letters) plus a reproduction-order template. Drafts only; nothing sent.
  - Measured (local, books from the hunt's first six fetches): 1,394 distinct unnumbered orders 1789-1899 observed.
    1801-1861: 213 observed, Mt total 316 (269-362), undiscovered 43-103 depending on matching. 1862-1899: 1,174
    observed, Mt total 1,729 (1,634-1,825), undiscovered 295-555. Lord lists 31% of president-signed documents in
    Richardson VI and 51% in Richardson IX. All lower bounds: Lord cites these books, so the lists are positively
    dependent, and orders that reached no printed compilation are invisible to every list.
- **Running:** nothing. `early-orders-hunt`'s first GitHub run (PR #25) was in progress at the time of writing;
  this job reads its `output/books/`.
- **Next:** push after PR #25 lands (the branch stacks on it); a person settles the 260 pre-1862 ambiguous pairs;
  adjudicate the 72 president-signed Richardson VI documents Lord does not list against the codebook; draw the
  random audit months and send the three emails; add Kappler and the Civil Service Commission reports to the hunt
  registry (338 and many Lord citations respectively, none fetched).
- **Asks:**
  - `@Owner`: review the three draft emails and the audit-month sampling before anything is sent; approve pushing
    `census-completeness` once PR #25 is merged.
  - `@Astra`: the Mt/Chapman/Chao1 choice and the dependence argument in `complete.py` would benefit from your
    adversarial read; the estimators are population-level by construction.
- **Do not:** quote any undiscovered count without its bracket and the dependence caveat; treat an unmatched book
  mention as a missing order (AMBIGUOUS_MATCHES.csv exists for that); admit anything from these outputs.

## 2026-10-18 13:00 ET: early-orders-hunt, a zero-token job that goes and gets the printed texts of 1789-1899 orders

- **Done (branch `early-orders-hunt`, from main `43f415dd`; local only, nothing pushed):**
  - `jobs/early-orders-hunt/`: reads Lord's 1943 unnumbered list (the `wpa-lists` parse, or a committed pre-1900
    subset of it with hashes in `data/PROVENANCE.json`), the 1,023 Stage 14 scan date markers and the six Stage 18
    candidates; parses every printed-source citation (Richardson vol/appendix/page, `YEAR MR page`, `YEAR GLO page`,
    Statutes at Large, Annals, American State Papers, Kappler, Sparks, documents, newspapers); fetches each cited
    book once from the Internet Archive (`data/BOOKS.json`: Richardson GPO vols I-X, the four War Department
    reservation books 1898-1916, fifteen GLO annual reports), checks the Archive's sha1 and the edition (the Bureau
    of National Literature Richardson reprints are repaginated and are refused), maps printed pages from running
    heads, and cuts the passage carrying the lead's date or subject into `texts/` with image, page, line span and
    hashes. Pre-1862 leads with a day date and no book text get bounded loc.gov collection searches (Chronicling
    America, the president's papers), responses saved by hash. Richardson VI/VII/IX are read from
    `jobs/richardson-volumes/data/`, not downloaded again. 20 offline tests (a fake Archive serves a synthetic book).
  - Measured locally (6 books, 327 s, 120 MB, 26 requests): 1,994 leads (320 pre-1862); 6,744 citations
    (4,775 GLO, 1,050 MR, 436 Richardson); 2,261 citations resolved to a page, 1,594 with date and subject on it;
    **texts cut for 950 leads, 125 pre-1862**; heads agreed with the page map on 93-100% of readable pages.
    Spot-read: Washington Barracks (MR 1916 p. 52, "announced by Executive order dated July 25, 1798"), the 1838
    Pensacola live-oak reserve, the 1827 Bois Blanc fuel reserve all cut correctly. A second run confirmed the
    alternate-copy fallback: the first `GLO_1893` copy was an 84-page extract (0 texts); the full copy gives 273.
  - Telemetry: zero model tokens in the job; this session's agent time about 2.5 h including the survey.
- **Running:** nothing on GitHub yet. Outputs are in the session scratchpad only.
- **Next:** push the branch and run the job once on GitHub (`HUNT_MAX_BOOKS` default 12; the cache carries fetched
  books to the next run, so three runs cover the registry); then have a person read 10-15 pre-1862 slices against
  the scan images; then put `RICH_X` (appendix) and `RICH_VIII` page files into `richardson-volumes` with one
  PROVENANCE entry each, so its parser splits them into orders. `GLO_1886`, `GLO_1897` and `GLO_1901` still need an
  Archive identifier (candidates listed in `books/<key>.json`).
- **Asks:**
  - `@Owner`: approve pushing `early-orders-hunt` and running it on GitHub.
  - `@Astra`: the `wpa-lists` branch is still unmerged; the job falls back to a committed subset of its output.
    When it merges, nothing changes except the source line in `SUMMARY.json`.
- **Do not:** treat a `texts/*.txt` slice as the original or as an identity: it is OCR of a printed compilation and
  a lead for `original_text`; signer, capacity and inclusion stay with the reviewer. Never write a search with
  no results into `EXHAUSTED.jsonl`.

## 2026-10-18 02:00 ET: printed volumes wired in; 176 claims from the 1989 Codification / FR revocation families; ready 1 -> 130

- **Done (branch `wire-new-sources`, local only, nothing pushed):**
  - Wiring (commits `33028c03`..`150c0457`): merged `ofr-compilations`, `indian-reservations-1912`,
    `isthmian-canal-1911`, `ofr-codification-1989` and `richardson-volumes`. The tracker counts official
    compilations like fr-originals (only finds not flagged `needs_page_check`); Richardson is a lead only
    (new blocker `ONLY_COMPILED_TRANSCRIPTION_FOUND`, 68 orders, 2 decided). claim-checker holds the committed
    volumes and their per-order texts; claim-drafts reads the printed-volume jobs. No order lost a step.
  - Claims: `research/readiness/claims/claude-2026-10-18-codif-b0.jsonl` .. `-b7.jsonl`, 176 decided orders
    (all provisional `no`), copied byte for byte from the reviewer-accepted files. 197 drafted, 21 rejected
    by the reviewers (10.7%): per batch 0/28, 2/23, 2/25, 0/24, 4/26, 12/24, 1/23, 0/24. 132 are complete
    claims (full gate pass); 44 are partial (ending, and sometimes savings/clauses, left open in
    `unresolved_material_gaps`, e.g. where only a deadline or a temporary body's term bounds the end).
  - Method: 59 families, each one revoking or superseding order (actor) taken from the 1989 Codification
    disposition tables and the Federal Register job (largest: EO 11708, 12534, 11408, 11342, 11230, 11811,
    11812, 12110, 9687). For each family the acting order and every target were read in the held official
    FR/OCR text; `first_end.date` is the effective date stated or implied in the acting instrument; the
    order's own terms (expiry, temporary bodies, conditions), earlier partial amendments and statutes were
    checked before taking the revocation as the end; partial amendments are not whole-order ends; deadlines
    never fix an actual end date; quotations are word for word from the held text. No statuses, ledger rows,
    codebook or counts changed; no `independent_human` reviews written.
  - Excluded: every order already in `research/readiness/claims/`, every Astra-owned order and family
    (EO 12076 and EO 12399 were in planned families and were left out), all targets of EO 12553.
  - claim-checker (local, downloads off), the 176 new claims: mechanical pass 176/176, 0 fail, 0 unverified;
    full gate 132; steps passed: original_text 176, clause_inventory 171, ending_or_current_basis 132,
    savings_residuals 159, counterevidence 166. Every quotation exact (3,164 across all 218 claims).
  - Tracker (local run with this run's checker output) vs main's committed `SUMMARY.json`, decided orders
    (3,359): ready_for_human_review 1 -> 130 (129 of the new claims + EO 13306); original_text 2,281 -> 2,312;
    clause_inventory 7 -> 177; ending_or_current_basis 2 -> 133; savings_residuals 7 -> 160;
    counterevidence 2,461 -> 2,470. With downloads off, six of Astra's claims (EO 14134-14139) show
    `CLAIM_CHECK_FAILED` locally (their govinfo PDFs are record-only here; GitHub re-downloads and verifies
    them). Taking GitHub's committed result for those six (same claim hash) gives 178 / 134 / 166 and no
    step lost anywhere; expect those numbers on GitHub.
  - Of the 47 new claims not ready: 44 are partial (`CLAIM_INCOMPLETE`; EO 11811 and EO 9407 are also
    quarantined); the complete claims for EO 11708 and EO 11812 are blocked by
    `QUARANTINED_RELATIONSHIP_CONFLICT`, and EO 9789 by `OPUS_MEDIA_REFETCH_NEEDED`.
  - Telemetry: token and wall-time per order were not measured in this integration step.
  - Run order (`390fa519`): `ofr-codification-1989` no longer lists `readiness-tracker` in `after.txt`; with
    `claim-drafts` now after the codification job, that made a cycle the runner broke silently (tracker before
    `claim-drafts`). Simulated order: codification, claim-drafts, readiness-tracker, case-bundles, daily-digest.
  - Known gap (not fixed): claim-checker now holds the Richardson volumes, and neither the gate nor the checker
    tests that `original_representation` is an official original, so a hand-written claim citing Richardson
    could pass `original_text`. None of the 176 claims does; worth a checker rule before anyone relies on it.
- **Running:** nothing. Local outputs only, in the session scratchpad `final_run/` (not committed).
- **Next:** push `wire-new-sources` and open one PR once the owner approves; let GitHub rerun claim-checker,
  claim-drafts and the tracker. Then the 44 partial claims (find the actual end of temporary bodies and
  deadline-bounded clauses) and the next Codification families.
- **Asks:**
  - `@Owner`: review and approve pushing `wire-new-sources` (wiring + 176 claims) as one PR.
  - `@Astra`: before claiming an order in a family whose actor is EO 11708, 12534, 11811, 11812, 12110 or
    9687, check `claude-2026-10-18-codif-b*.jsonl`; those targets are claimed here.
- **Do not:** edit the `claude-2026-10-18-codif-b*.jsonl` lines (a changed claim waits for a new check);
  treat a passed claim as a human review.

## 2026-10-17 20:45 ET: custody unblocked, machine later-source search, Opus re-fetch list

- **Done (branch `unblock-claims`, one PR):**
  - `jobs/official-fixity/`: GPO's published SHA-256 for every govinfo file: 3,384 byte-identical, 0 mismatches.
  - claim-checker counts a source as held when GPO publishes those exact bytes, or when a record-only govinfo PDF is re-downloaded and matches. Before this, **every** cited source showed `custody_record_only` on GitHub, so no claim step could ever pass; 116 of the 211 references in Astra's first claims are now GPO-verified.
  - The tracker counts `counterevidence` from the machines' complete bounded searches (OFR catalog, 7,619 saved texts, full U.S. Code and eCFR) when nothing contrary was found: **0 → 2,461 decided orders**.
  - The pdfplumber recheck: 155 upgrades.
  - The opus-media-match re-fetch list, which never reached main.
- **Asks:**
  - `@Astra`: copy `jobs/readiness-tracker/output/MACHINE_LATER_SEARCH.jsonl` (claim-shaped `later_source_search`) into claims instead of writing searches by hand.
  - `@Astra`: cite `jobs/official-fixity/output/MATCHED_BY_SHA256.json` before setting a rule's `original_custody_verified`, and add `official-fixity` to `jobs/family-rules/after.txt`.
  - `@Astra`: consider batch review sheets in the production swarm: one compact table of 50-100 same-type orders (for example single-paragraph orders, where the clause inventory is one clause), approved row by row and converted to claims by a job.
  - `@Astra`: the 172 orders with `MACHINE_SEARCH_FOUND_CONTRARY_LEAD` are judgment work for P3/P1.
- **Do not:** treat the machine search step as a legal conclusion; it records what was searched and that nothing contrary turned up.

## 2026-10-17 17:00 ET: eight research jobs merged; tracker hooked up; standard agent procedure

- **Done:**
  - Eight zero-token jobs are on `main`: `source-ladder`, `fr-originals`,
    `clause-drafts`, `later-events`, `current-law`, `opus-media-match` (PR #4
    pending at time of writing), `claim-checker` and `claim-drafts`. Each was
    built and adversarially reviewed by separate agents (5.6M tokens, 21 agents).
  - This PR (`integrate-tools`) hooks the readiness tracker to their outputs.
    Claim steps now count only after claim-checker passes them for that exact
    claim version.
  - Runner fixes: no more cancelled queued runs; `triggers.txt`, `after.txt`;
    several jobs per manual run. A new claim reruns claim-checker and then the
    tracker within minutes.
  - **Standard procedure for all agents:** `research/readiness/README.md`, with
    a pointer in `AGENTS.md`.
- **Running:** the fr-originals full run on the owner's PC: about 7,200
  Federal Register orders, resumable. When it finishes I will commit its texts
  to `jobs/fr-originals/data/full_run/`, which reruns clause-drafts,
  later-events, claim-drafts and the tracker on the full corpus.
- **Next:** commit the full run, then spot-check the headline numbers (357 Opus
  orders matched, 930 end candidates, 293 YES current-law leads) against the
  committed outputs.
- **Asks:**
  - `@Astra` / `@Opus` / `@Codex`: from now on, follow
    `research/readiness/README.md`. Request sources via
    `research/readiness/FETCH_QUEUE.jsonl` (no hand fetching), start orders from
    `jobs/claim-drafts/output/DRAFT_CLAIMS.jsonl`, and commit claims to
    `research/readiness/claims/<agent>-<date>.jsonl`.
  - `@Astra`, on your two points:
    - **Exhaustion:** source-ladder never writes `EXHAUSTED.jsonl`. It only
      proposes lines when every route answered definitively, and records
      timeouts and blocks as `retry_later`. The procedure now allows an
      `EXHAUSTED.jsonl` line only from a non-WEAK `exhausted_proposed` result
      or a fully documented route-by-route search.
    - **Telemetry:** the procedure asks every agent to report tokens and time
      per order in HANDOFF, as your ROI model needs.
    - **Not done:** your Madison 1814 / Jackson 1832 inclusion request. It is
      still open for a separate session.
  - `@Owner`: approve this PR and PR #4 (opus-media-match).
- **Do not:** copy a `retry_later` or `WEAK` ladder result into
  `EXHAUSTED.jsonl`; hand-edit any `jobs/*/output/`.

## 2026-10-17: readiness tracker added (the owner's new main progress measure)

- **Done:** `jobs/readiness-tracker/` counts orders **ready for human review**:
  every machine step done or recorded as searched to the end. It runs daily and
  writes `jobs/readiness-tracker/output/TRACKER.md`. The steps are: status,
  original text, clause inventory, ending/current basis, savings, counterevidence,
  shared sources, and Opus media. First run: 0 of 14,972 ready. Among the 3,359
  decided orders, 54 have their original text saved and none has a clause
  inventory yet.
- **Running:** the tracker's first run on the `readiness-tracker` branch.
- **Next:** the two biggest machine unlocks in `SHARED_UNLOCKS.csv`:
  matching the 496 Opus images to orders (844 orders) and bulk-downloading the
  362 official links Stage 21 already found.
- **Asks:**
  - `@Astra` / `@Opus`: from now on, write your per-order results as claims in
    `research/readiness/claims/*.jsonl` (Stage 19 claim format). **Partial claims
    count step by step**, so commit the clause inventory as soon as you have it.
    When a step truly cannot be finished, record it in
    `research/readiness/EXHAUSTED.jsonl` (see `research/readiness/README.md`).
    Pick work from the top of `SHARED_UNLOCKS.csv`: one source there unblocks
    many orders at once.
  - `@Owner`: approve the pull request for `readiness-tracker`.
- **Do not:** hand-edit `jobs/readiness-tracker/output/`; the job rewrites it.

## 2026-10-17: shared runner and HANDOFF folder set up; Stage 9 ownership check done

- **Done:**
  - Added `jobs/` (shared script runner on GitHub Actions, see
    `jobs/README.md`) and this `HANDOFF/` folder, on branch
    `shared-runner-and-handoff`, pending the owner's approval.
  - Checked Opus Stage 9's 131 "reviewed, held for ownership" orders (90 tax
    inspection, 39 WWI eight-hour, 2 alien property) against Astra's Stage 7
    assignment split (`FROZEN_STAGE7_ASSIGNMENT_SPLIT_ORIGINAL.zip`, sha256
    `5b553c02…815a`; all seven member-list hashes match `SCOPE_ACCOUNTING.json`).
    None of the 131 is in Astra's 1,181 civil-service IDs or in any other
    Stage 7 list. All 131 were already NO in the Opus Stage 11 patched ledger
    (sha256 `0046070c…6d71`), merged at `POST_ASTRA_STAGE10_OPUS_STAGE9_V2`
    while still marked `OWNERSHIP_NOT_VERIFIED`, and every status matches the
    Stage 9 review. So the merge was correct and **no count changes**.
- **Running:** `jobs/example-hello` (smoke test of the runner).
- **Next:** none planned; waiting for the owner.
- **Asks:**
  - `@Astra`: from your next session, read and write `HANDOFF/` instead of
    relying on the owner to paste messages. For scripts too big for your
    container, commit them as a job under `jobs/`.
  - `@Owner`: approve the pull request for this branch.
- **Do not:** none.
