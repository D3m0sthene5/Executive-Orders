# Claude's handoff notes

Newest entry first. See `README.md` in this folder for the format.

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
