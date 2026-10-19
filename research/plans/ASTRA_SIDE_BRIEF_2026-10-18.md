# Astra side brief, 2026-10-18: where a parallel Astra session helps most

Written from a read-only survey of branch `claude/astra-brief-f2a36a` (cut from `app-executive-orders` at
`2585914c`) and of `origin/main` at `c9e1da64`. The tracker headline is identical on both: **130 of 14,972
orders ready for human review; 0 orders independently human-certified for their whole lifecycle.** Every
number below names the file it was read from. Counts derived from a per-order file are marked "derived".

The brief has three parts: (1) a workload map of the eight readiness steps, (2) a ranking of the areas a side
Astra session can improve without touching work in flight, and (3) the Astra prompt itself.

## Work in flight that this brief must not overlap

| Who | What | Files they own right now |
|---|---|---|
| Claude session `app-ingest` | wiring the American Presidency Project (APP) texts into the tracker, clause-drafts, a new `jobs/app-footnote-leads/`, and later-events leads | `jobs/readiness-tracker/tracker.py`, `jobs/clause-drafts/`, `jobs/later-events/` inputs, `jobs/app-footnote-leads/` |
| Claude session (APP priority) | rebuilding `jobs/app-executive-orders/data/PRIORITY.txt`; summarising `MIRROR_AUDIT.jsonl` | `jobs/app-executive-orders/` |
| Main Claude session | resolving conflicts on PR #24 (`codex/corpus-excavator-20261018`: shared evidence across claim batches, reviewed status proposals, `jobs/claim-kit/`) | `jobs/claim-kit/`, `research/excavator/`, `research/readiness/CLAIM_KIT_LOCK.json` |
| Claude (owner of the codification claims) | the 44 partial claims in `research/readiness/claims/claude-2026-10-18-codif-b*.jsonl` (actors EO 11708, 12534, 11811, 11812, 12110, 9687 and 53 other families) | those claim files and their families |
| Codex | `jobs/hathi-gpo-orders/` (1,531 texts for orders 5076-7531, on main), `jobs/numbered-early-orders/` (184 orders, on main) | those two job folders |

Open pull request (the only one): **#24** "Share evidence across claim batches and enable reviewed status
proposals" (`codex/corpus-excavator-20261018` → `main`). Its body reports: a six-case matched experiment that
does **not** show lower producer-plus-reviewer cost (10% more calls, 5.4% more elapsed time, 21.8% more input
tokens after independent review); 358 shared-provision groups affecting 412 decided orders (preparation leads,
not conclusions); one independently reviewed provisional-NO proposal for EO 11352 with owner acceptance
`false`; canonical readiness unchanged at 130. Reading it is fine; pushing to that branch is not.

## 1. Workload map

Sources: `jobs/readiness-tracker/output/SUMMARY.json` and `TRACKER.md` (headline and per-step counts),
`jobs/readiness-tracker/output/READINESS_BY_ORDER.csv` (derived per-order counts),
`jobs/claim-drafts/output/SUMMARY.json` and `TODO_BY_ORDER.csv`, `jobs/claim-checker/output/REPORT.md`,
`jobs/source-ladder/output/SUMMARY.json`, `jobs/family-rules/output/SUMMARY.json`,
`jobs/opus-media-match/output/REFETCH_LIST.jsonl`, `research/readiness/EXHAUSTED.jsonl` (0 lines).

Universe 14,972 orders. Decided (provisional YES/NO): 3,359, of which 2,954 NO and 405 YES (derived from
`READINESS_BY_ORDER.csv`). Undecided: 11,613. Ready for human review: 130, all in tier `complete_claim`
(`SUMMARY.json` → `ready_by_tier`). No order is in tier `machine_exhausted` because `EXHAUSTED.jsonl` is empty.

Three kinds of gap are kept apart below. A **machine gap** is a missing download, match or bounded search that a
job can close. An **agent judgment gap** is legal reading an AI agent may do and record in a claim (it then counts
toward "ready for human review", never toward certification). A **human gap** is something the project's rules
reserve to a person or the owner: a provisional status, an admitted census identity, a codebook change, or an
`independent_human` review.

| Step | Done / applicable | Open | Machine gap (blocker: orders) | Agent judgment gap | Human gap | From |
|---|---:|---:|---|---|---|---|
| 1 `provisional_status` | 3,359 / 3,359 decided; **0 / 11,613 undecided** | 11,613 | none: no job may assign a status | none | **11,613** orders need a reconciled status (`research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv` is owner-controlled; PR #24's "status proposals" stay proposals until the owner accepts) | `SUMMARY.json` → `orders_blocked_by.NO_PROVISIONAL_STATUS` |
| 2 `original_text` | 2,312 / 3,359 | 1,047 | `NO_OFFICIAL_SOURCE_LOCATED` 959 decided (7,814 all); `ONLY_COMPILED_TRANSCRIPTION_FOUND` 2 decided (68 all) | `ORIGINAL_FOUND_NEEDS_PAGE_CHECK` **88 decided** (286 all; 72 NO, 16 YES, derived): an agent confirms the page | none for FR-era orders; pre-1937 orders whose only text is a compilation need the owner's rule on what counts | `SUMMARY.json` → `decided_orders_blocked_by`; `TRACKER.md` "What blocks orders" |
| 3 `clause_inventory` | 178 / 3,359 | 3,181 | none: machine drafts exist for 1,806 orders (13,228 clauses, `claim-drafts/output/SUMMARY.json` → `filled.operative_clauses`); 1,553 drafts lack a clause source | **3,142** `NO_CLAUSE_INVENTORY` plus 39 Astra and 44 Claude partial claims (`CLAIM_INCOMPLETE` 83) | none | `SUMMARY.json`; `claim-checker/output/REPORT.md` |
| 4 `ending_or_current_basis` | 134 / 3,359 | 3,225 | none: 1,029 decided orders have a whole-order-end candidate and 510 a current-predicate lead (`claim-drafts` → `candidates`) | **`FIRST_END_UNPROVED` 2,742** (NO orders) and **`CURRENT_BASIS_UNPROVED` 400** (YES orders) | none | `SUMMARY.json` |
| 5 `savings_residuals` | 166 / 3,359 | 3,193 | none | **3,142** `SAVINGS_RESIDUALS_NOT_CLOSED` | none | `SUMMARY.json` |
| 6 `counterevidence` | 2,470 / 3,359 | 889 | **`NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE` 693** (pre-1937 orders: the OFR catalog starts in 1937, so no machine search covers them yet) | **`MACHINE_SEARCH_FOUND_CONTRARY_LEAD` 159** (151 from current-law, 8 from later-events, derived); `QUARANTINED_RELATIONSHIP_CONFLICT` 36 | none | `SUMMARY.json`; `READINESS_BY_ORDER.csv` |
| 7 `shared_sources` | 209 / 236 | 27 | **`SHARED_SOURCE_NOT_RETRIEVED` 27**: EO::4314 (10), EO::6868 (6), 48 U.S.C. 863 (3), EO::6964 (3), EO::6910 (3), 26 CFR 458.324 (2). The ladder's `EXHAUSTED_PROPOSED.jsonl` has 22 lines for the four EOs, each after **one route**, so none qualifies for `EXHAUSTED.jsonl` | none | none | `SHARED_UNLOCKS.csv`; `source-ladder/output/EXHAUSTED_PROPOSED.jsonl` |
| 8 `opus_media` | 82 / 844 | 762 | **`OPUS_MEDIA_REFETCH_NEEDED` 472** (`REFETCH_LIST.jsonl`: 848 URLs, 825 on govinfo, 617 orders, 834 marked `left_out_of_release_too_large`); `OPUS_MEDIA_PARTLY_RESOLVED` 52; `OPUS_MEDIA_ORIGINAL_NOT_KEPT` 20; `OPUS_MEDIA_MATCH_AMBIGUOUS` 1 | `OPUS_MEDIA_NONE_CITED` **217** needs a rule decision (what counts when Opus cited no medium), not a fetch | the rule for `NONE_CITED` is the owner's | `SUMMARY.json`; `REFETCH_LIST.jsonl` |

Two cross-cutting facts matter more than any single row:

- **1,315 decided orders have every machine step done and lack only the three judgment steps** (clauses,
  ending or current basis, savings): 1,130 NO and 185 YES (derived from `READINESS_BY_ORDER.csv`: original text,
  counterevidence, shared sources and Opus media all done or not applicable, not ready). `claim-drafts` rates 780
  of its drafts "only judgment left" (599 NO, 181 YES; 739 of them small effort). 556 drafts are single-clause
  orders (526 NO, 30 YES). This is the pool from which "ready" can grow fastest, and only an agent or a person can
  work it.
- **The source-ladder is not picking up the Opus re-fetch list.** Its log (`jobs/source-ladder/output/log.txt`,
  line 6) says "0 Opus originals to re-fetch" although `REFETCH_LIST.jsonl` has 848 lines; its 170 items were 80
  queue lines plus 90 Stage 20 shared sources. Until that is fixed, the largest unlock in `SHARED_UNLOCKS.csv`
  (472 orders) does not move by itself.

Also measured but outside the eight steps: 25 family rules in `research/readiness/rules/` (all
`review_state: source_reviewed`) name 668 targets in the universe, 607 of them decided; 36 are claimed; **571
decided targets have no claim, and 476 of those already have original text and counterevidence done** (derived).
The family-rules job issued 748 certificates, all blocked (`ORIGINAL_SOURCE_CUSTODY_UNVERIFIED` 748,
`TARGET_INDEPENDENT_CLAUSES_UNREVIEWED` 748, `LATER_OR_UNDATED_SAVED_TEXT_USE` 670,
`INDEPENDENT_CLAUSE_OR_SAVINGS_LEAD` 739, `CURRENT_LAW_USE_LEAD` 316; `jobs/family-rules/output/SUMMARY.json`).

### What finishing means under the project's own rules

`AGENTS.md` states the objective: the legally defensible lifecycle of every executive order from 1789 to the
2026-10-14 cutoff, plus historical census recovery. Under `research/stage19/CLAIM_SCHEMA.md` and
`jobs/readiness-tracker/README.md`, an order is finished when:

1. it has a reconciled provisional status (owner-controlled ledger);
2. a Stage 19 claim passes `claim_gate.py` and claim-checker in full: complete clause inventory with exact
   original spans and held sources, an exact first-end date, actor, mechanism and source for every terminated
   clause (or a current predicate checked through 2026-10-14 for every operative clause), savings and residuals
   closed, a bounded later-source search recorded, no unresolved material gaps;
3. a separate `eo-lifecycle-review/v1` record with `reviewer_role: independent_human` and `decision: uphold`
   matches that claim's SHA-256.

Point 3 is what "0 certified whole-lifecycle orders" counts, and **no machine or AI step can satisfy it**. An AI
review by another model is still an AI review (`HANDOFF/COORDINATION.md`). Likewise no machine step can assign a
provisional status to the 11,613 undecided orders, admit any of the historical candidates (67 LOC items, 1,023
Lord appearances, 0 admitted; `TRACKER.md` census section), change the codebook, or declare a search exhausted
without route-by-route evidence (`research/readiness/README.md`). For the pre-1900 census, `census-completeness`
estimates 43-103 undiscovered orders for 1801-1861 and 295-555 for 1862-1899, all lower bounds because Lord's
list depends on the same books (`jobs/census-completeness/output/SUMMARY.json`; Claude's note of 2026-10-18
14:30). Those gaps close only through archival reading the project has drafted but not sent
(`research/plans/SCAN_REQUESTS_2026-10-18.md`).

So the honest statement of "done" is: 14,972 orders each with a reconciled status, a gate-passing claim, and an
independent human review, plus a census whose undiscovered remainder has been bounded by an archival audit. The
machines and agents can carry orders to the door of human review (130 today, 1,315 within reach); the last step,
and the first step for 11,613 orders, is human.

## 2. Excavator ranking for a side Astra session

Ranked by orders unblocked per Astra minute, then by whether only Astra can do it well (legal reading,
adversarial review, independent review of another agent's proposals). Minute estimates are derived from Astra's
own measured windows in `HANDOFF/notes-astra.md` (1.59 min per retained-original page check; 0.85 min per
partial claim; 13.9 wall minutes for one complete ready order) and from Claude's swarm measurement in
`research/plans/EXCAVATOR_FUNNEL_2026-10-18.md` (about 2 agent-minutes per accepted claim across producer and
reviewer, with a 10.7% reviewer rejection rate). They are planning ranges, not promises.

### A1. Queue the Opus re-fetch list (472 orders, machine step 8)

- **What Astra does.** Verify first: read `jobs/opus-media-match/output/REFETCH_LIST.jsonl` and count lines whose
  `instrument_ids` is non-empty and whose `url` starts with `https://`. If most lines qualify, the ladder's
  own pickup is broken and that is Claude's bug to fix (ask it in HANDOFF); meanwhile append one
  `FETCH_QUEUE.jsonl` line per distinct `expected_sha256` with `instrument_id` set to the first id,
  `urls: [url]`, `citation` carrying the expected SHA-256 and the other ids as text, `step: "opus_media"`,
  `requested_by: "Astra opus-refetch 2026-10-19"`. If `instrument_ids` is empty on most lines, do not queue;
  the mapping back to orders is missing and only opus-media-match (Claude's) can supply it.
- **Inputs today.** `jobs/opus-media-match/output/REFETCH_LIST.jsonl` (848 lines); `jobs/source-ladder/output/
  log.txt` line 6; `jobs/source-ladder/ladder_queue.py` (`opus_refetch_wanted`, the pickup code);
  `jobs/readiness-tracker/tracker.py` lines 209-217 and 427-429 (how re-fetched files are counted).
- **Pushes.** Appended lines in `research/readiness/FETCH_QUEUE.jsonl`; a HANDOFF ask to Claude with the count.
- **Gain.** Up to 472 decided orders clear step 8 once the ladder holds bytes matching `expected_sha256`.
  None becomes ready by this alone (they still need steps 3-5), but it is the largest single unlock.
- **Cost.** 20-40 Astra minutes (one script, one check of the next ladder `SUMMARY.json`).
- **Rule risks.** A re-fetched file whose SHA-256 differs from `expected_sha256` is a different document and
  must not be treated as the Opus original; the ladder records `matches_expected_sha256` for that reason. No
  legal content is asserted.

### A2. Turn family-rule targets into claims (571 decided targets, steps 3-5)

- **What Astra does.** For the 25 rules Astra already wrote and had reviewed (`research/readiness/rules/
  EO_*.json`), produce claims for the decided targets that have no claim yet, starting with the 476 whose
  original text and counterevidence are already done. For each target: start from its draft in
  `jobs/claim-drafts/output/DRAFT_CLAIMS.jsonl` (or the one-fetch packet in `jobs/case-bundles/output/bundles/`),
  read the held original, fix the clause inventory, read the acting instrument's effective-date wording, and
  check the order's own terms and earlier partial amendments before taking the family revocation as the first
  end. Where the earlier actual end cannot be dated, commit the partial claim with the gap in
  `unresolved_material_gaps` (partial claims count step by step). Finish Astra's own 39 `CLAIM_INCOMPLETE` claims
  the same way (a new file supersedes the old line for the same `instrument_id`).
- **Inputs today.** `research/readiness/rules/*.json`; `jobs/claim-drafts/output/DRAFT_CLAIMS.jsonl` and
  `TODO_BY_ORDER.csv` (`only_judgment_left`, `clauses`, `conflicts`); `jobs/family-rules/output/FRAGMENTS.jsonl`
  and the per-target certificate blockers; `jobs/later-events/output/EDGES.csv` (amendment chains);
  `jobs/readiness-tracker/output/MACHINE_LATER_SEARCH.jsonl` (claim-shaped `later_source_search` to copy);
  `jobs/official-fixity/output/MATCHED_BY_SHA256.json` (custody). The Claude codification method that reached
  132 complete claims out of 176 is described in `HANDOFF/notes-claude.md` (2026-10-18 02:00).
- **Pushes.** `research/readiness/claims/astra-2026-10-19-<family>.jsonl`, one file per family batch; an AI
  review record per batch under a new `research/readiness/reviews/astra-2026-10-19/` folder.
- **Gain.** 150-300 claims; by Claude's measured ratio roughly 60-75% complete, the rest partial. Each complete
  claim is one more "ready for human review". This is the largest realistic move in the headline number.
- **Cost.** 2-4 Astra minutes per accepted claim with producer and reviewer in separate contexts (fed one
  dossier each, never whole texts), so 6-20 hours for the full set; a first batch of 50 is 2-3 hours.
- **Rule risks.** The sprint of 2026-10-17 was stopped twice for unsupported "cleanup" dates and for
  completed-amendment dates; a formal revocation is the first end only when nothing in the order's own terms or
  an earlier instrument ended that clause first. A report deadline is never an end. Do not take an order claimed
  in any `claude-*.jsonl` file (actors EO 11708, 12534, 11811, 11812, 12110, 9687 and the rest of those 59
  families) or any order PR #24's reports name; list the families you will take in HANDOFF before starting.
  A passed claim is not a human review.

### A3. YES orders: current legal basis through the cutoff (185 orders, step 4)

- **What Astra does.** The 185 YES orders whose only open steps are the three judgment steps (derived) need a
  `current_predicate` for at least one clause: the statute, regulation or later order that keeps it operating,
  with `checked_through: 2026-10-14`. Use `jobs/current-law/output/` leads (U.S. Code release 119-121, current
  through 2026-10-09, and eCFR), read the cited provision, and close the 2026-10-09 to 2026-10-14 gap by checking
  the Federal Register for a revocation in those five days. Start with the 160 YES drafts that `TODO_BY_ORDER.csv`
  rates `only_judgment_left = yes` and `estimated_effort = small`. Skip the 162 YES orders blocked by
  `OPUS_MEDIA_NONE_CITED`; they cannot become ready until the owner rules on that blocker.
- **Inputs today.** `jobs/claim-drafts/output/TODO_BY_ORDER.csv` (filter `provisional_status = yes`);
  `jobs/current-law/output/POSSIBLE_CONFLICTS.csv` and `SUMMARY.json`; `jobs/later-events/output/
  COUNTEREVIDENCE_LEADS.csv` (eight YES orders with a full-revocation candidate, four of them with a 2025
  reinstatement candidate: EO 13933, 13934, 13957 and others); Astra's own complete YES claim for EO 13306
  (`research/readiness/claims/astra-2026-10-18-p3complete.jsonl`) as the worked pattern.
- **Pushes.** `research/readiness/claims/astra-2026-10-19-yes-*.jsonl`; a short `research/readiness/reviews/
  astra-2026-10-19/YES_METHOD.md` stating how the five-day gap was closed.
- **Gain.** 50-150 ready orders; today only 1 YES order is ready, so this also tests whether the YES method
  scales at all.
- **Cost.** 8-15 Astra minutes per order (Astra's EO 13306 window was 13.9 wall minutes); 7-35 hours for the
  pool, so take batches of 20.
- **Rule risks.** A U.S. Code or eCFR mention is a lead, not a basis; the 1989 Codification in-force snapshot is
  never a basis; "checked through 2026-10-14" must be true, not assumed. A YES order with a full-revocation
  candidate and a later reinstatement needs both events in `later_events` with effective dates read from the
  instruments. If the evidence says the YES is wrong, leave the claim incomplete and write it up for the owner;
  never change the status.

### A4. Adjudicate the contrary leads and quarantined conflicts (159 + 36 orders, step 6)

- **What Astra does.** For each of the 151 provisional-NO orders that current-law found printed or cited in the
  U.S. Code or eCFR, and the 8 orders later-events flagged, read the citing provision and decide whether it is a
  historical or definitional citation (the order stays NO and the claim's `later_source_search` records the
  resolution with the quote) or evidence the order still operates (a status conflict: record it in a research
  report and in HANDOFF for the owner; never resolve it by changing the status). Do the 43 that are also
  "only judgment left" first. For the 36 `QUARANTINED_RELATIONSHIP_CONFLICT` orders, read the conflicting edges
  in `jobs/claim-drafts/output/CONFLICTS.csv` and write a per-order resolution memo.
- **Inputs today.** `jobs/current-law/output/POSSIBLE_CONFLICTS.csv` (166 lines, with the exact snippet, for
  example EO 10005 printed at 48 U.S.C. 734 note); `jobs/later-events/output/COUNTEREVIDENCE_LEADS.csv`;
  `jobs/claim-drafts/output/CONFLICTS.csv`; `jobs/readiness-tracker/output/READINESS_BY_ORDER.csv` (filter
  `MACHINE_SEARCH_FOUND_CONTRARY_LEAD`).
- **Pushes.** `research/readiness/reviews/astra-2026-10-19/CONTRARY_LEADS.md` (one row per order: lead, what
  the provision says, resolution, quote) and the `later_source_search` block inside each order's claim.
- **Gain.** Up to 159 orders clear step 6; for those also in the 1,315 pool it removes the last machine-side
  blocker. The status conflicts it surfaces are the project's best early warning that a provisional NO is wrong.
- **Cost.** 3-6 Astra minutes per order; 8-16 hours for all, 2-4 hours for the first 43.
- **Rule risks.** The pull is to "resolve" a lead by dismissing it. Every resolution must quote the provision
  and say why it does or does not keep the order operating. A printed order text in a U.S. Code note is a strong
  lead that the order is live; that is a status hypothesis for the owner, not a finding, and not a reason to
  write a YES claim.

### A5. Adversarial and independent review (quality, not count)

Three reviews only Astra is well placed to do, because each checks another agent's or another model's work:

- **(i) A sample of the 130 ready claims.** Claude's 132 complete codification claims were produced and
  reviewed by Claude agents. Astra reads 30 of them (stratified across the eight codification batches), tests
  each first-end date against the acting instrument and the order's own terms, and reports the error rate.
  The funnel document says the true error rate must be established before scaling, and a person has not yet
  done it; an Astra read triages which claims a person should look at first. Inputs:
  `research/readiness/claims/claude-2026-10-18-codif-b0.jsonl` to `-b7.jsonl`; `jobs/claim-checker/output/
  PER_CLAIM.json`. Output: `research/readiness/reviews/astra-2026-10-19/READY_CLAIM_SAMPLE.md` with one row
  per claim and an explicit `reviewer_role: ai_review` on any record. Never write `independent_human`. Never edit
  a `claude-*.jsonl` line; a disputed claim is reported in HANDOFF for Claude to fix. Cost 1-2 hours. Gain: a
  measured error rate for the headline number, and fewer wrong claims reaching the human reviewer.
- **(ii) The census-completeness estimators.** Claude asked for this read (notes 2026-10-18 14:30): the choice
  of Mt maximum likelihood (Darroch), Chapman and Chao1, the positive-dependence argument, and the three
  matching scenarios in `jobs/census-completeness/complete.py` and `output/REPORT.md`. Output:
  `research/plans/ASTRA_REVIEW_CENSUS_ESTIMATORS_2026-10-19.md`. Cost 1-2 hours. Gain: the project's only
  quantitative answer to "have we looked everywhere" is either defended or corrected before anyone quotes it.
- **(iii) PR #24's proposals.** Read the EO 11352 provisional-NO proposal and the claim that 358 shared-provision
  groups affect 412 decided orders, from the PR body and the files it adds under `research/excavator/2026-10-18/`
  (read on the PR branch; write nothing there). Output: a review section in the same plans file and a HANDOFF
  ask to Codex or the owner. Cost 1 hour. Gain: an independent read before the owner accepts a status proposal.

### A6. Page checks for the 88 decided orders with a located but unconfirmed original (step 2)

- **What Astra does.** For each decided order blocked by `ORIGINAL_FOUND_NEEDS_PAGE_CHECK`, open the fr-originals
  or compilation PDF at the proposed pages, confirm they hold this order's complete text, and commit a partial
  claim whose `original_representation` carries the confirmed `page_or_item`. Only decided orders can carry a
  claim, so the 198 undecided page-check orders are out of reach here.
- **Inputs today.** `jobs/claim-drafts/output/DRAFT_CLAIMS.jsonl` (`_draft.proposals.original_representation`
  with `strong: false`); `jobs/fr-originals/output/FRAGMENTS.jsonl` and `data/full_run/`; `jobs/official-fixity/
  output/MATCHED_BY_SHA256.json`.
- **Pushes.** `research/readiness/claims/astra-2026-10-19-pagecheck.jsonl`.
- **Gain.** 88 orders clear step 2 (72 NO, 16 YES).
- **Cost.** About 1.6 Astra minutes per page check measured; 2.5-3 hours.
- **Rule risks.** Confirming the Federal Register page is identifying the official printing, not authenticating a
  signed original; say so in the rationale. PDF fonts can decode a dash as a plus-or-minus sign (Astra's EO 13054
  stop); quotations are word for word from the held bytes.

### A7. Retrieve the six shared sources (27 orders, step 7)

- **What Astra does.** The ladder gave up on EO 4314, 6868, 6910 and 6964 after one route each, so no
  `EXHAUSTED.jsonl` line is justified. New routes exist since: Codex's `jobs/hathi-gpo-orders/output/` on main
  holds 1,531 texts for orders 5076-7531, which covers the three 1934-35 orders; the GPO 1974 Hoover
  compilation (`jobs/ofr-compilations/`) covers Hoover orders; EO 4314 (Coolidge, 1925) may be on Wikisource or
  in the APP captures (discovery only). Add `FETCH_QUEUE.jsonl` lines with concrete `https://` URLs and
  citations for each, plus `48 U.S.C. 863` (repealed; govinfo USCODE historical editions or Statutes at Large)
  and `26 CFR 458.324` (a historical CFR edition; name the year).
- **Inputs today.** `jobs/source-ladder/output/EXHAUSTED_PROPOSED.jsonl`, `RESULTS.csv`; `jobs/hathi-gpo-orders/
  output/RESULTS.csv` and `SOURCES.jsonl` (on main); `jobs/app-executive-orders/output/INDEX.csv` (read only).
- **Pushes.** 6-12 `FETCH_QUEUE.jsonl` lines.
- **Gain.** 27 orders clear step 7.
- **Cost.** 30-60 Astra minutes.
- **Rule risks.** A compiled or mirror transcription may satisfy a lead but not custody of the shared source;
  prefer an official printing. The 16 `no_route` results in the last ladder run were all Astra queue lines with
  free text and no URL ("Actual emergency-board report submitted under EO 12495"); the ladder cannot route
  those. Every new line needs an `https://` URL or a citation the ladder parses (FR, Stat., U.S.C., CFR, EO).

### A8. A pre-1937 later-source search protocol (693 orders, step 6), design only

- **What Astra does.** The 693 decided pre-1937 orders cannot clear counterevidence because the machine search
  rests on the OFR catalog. Write the protocol a claim's `later_source_search` must follow for a pre-1937 order:
  which repositories (the 1989 Codification disposition tables, which list earlier orders a later one amended or
  ended; the WPA numbered list's disposition notes; the APP footnotes once `jobs/app-footnote-leads/` lands;
  Lord's list; the saved-text sweep), what query, and what "nothing contrary found" means for each.
- **Inputs today.** `jobs/ofr-codification-1989/output/`; `jobs/readiness-tracker/README.md` (the
  counterevidence rule); `jobs/later-events/README.md`.
- **Pushes.** `research/plans/PRE1937_LATER_SEARCH_PROTOCOL_2026-10-19.md`. No job: the APP footnote job in
  flight will supply the machine half, and Astra must not build a competing one.
- **Gain.** None directly; it makes 693 orders claimable later at a known cost.
- **Cost.** 1-2 hours.
- **Rule risks.** A protocol is not a search. No `EXHAUSTED.jsonl` line follows from writing it.

### Suggested order of work

Do A1 and A5(ii) first (cheap, and A1 compounds while the ladder runs), then A2 as the main production line
with A3 interleaved by batch, then A4 for the 43 overlap orders, then A5(i) and A5(iii), then A6 and A7 as fill,
and A8 only if time remains. Stop any production batch whose independent review rejects more than 15% and
rework the method before continuing, as the 2026-10-17 sprint did.

## 3. The Astra prompt

```text
You are Astra, working on the Executive-Orders repository (GitHub: D3m0sthene5/Executive-Orders). This is a
side session that runs alongside other agents. Read this whole prompt before doing anything.

START. Pull origin/main. Read, in this order: HANDOFF/README.md; HANDOFF/notes-claude.md, HANDOFF/notes-codex.md,
HANDOFF/notes-sol.md and your own HANDOFF/notes-astra.md (newest entries first); AGENTS.md;
research/readiness/README.md; jobs/readiness-tracker/output/TRACKER.md and SHARED_UNLOCKS.csv;
research/plans/ASTRA_SIDE_BRIEF_2026-10-18.md (the brief this prompt comes from; it has the numbers and the
file paths for every task below). Check `gh pr list --state open`. Do not rely on an older summary of the repo.

NON-INTERFERENCE. Other sessions are working right now. Do not edit, move or write under any of these:
  jobs/app-executive-orders/ (any file, including data/PRIORITY.txt and output/)
  jobs/readiness-tracker/tracker.py (and anything else in jobs/readiness-tracker/ except reading output/)
  jobs/clause-drafts/
  jobs/claim-kit/ and research/readiness/CLAIM_KIT_LOCK.json
  jobs/later-events/ (its inputs, code and output)
  jobs/app-footnote-leads/ (being created by another session)
  HANDOFF/notes-claude.md, HANDOFF/notes-codex.md, HANDOFF/notes-sol.md, HANDOFF/DIGEST.md
  research/readiness/claims/claude-*.jsonl (Claude's claims; report problems in HANDOFF instead)
  any jobs/*/output/ folder (jobs rewrite them)
  the branch codex/corpus-excavator-20261018 (PR #24): read it, never push to it
Write only to: research/readiness/claims/astra-<YYYY-MM-DD>-<topic>.jsonl (new files; never edit a committed
claim line, a new file supersedes the old line for the same instrument_id), research/readiness/FETCH_QUEUE.jsonl
(append only), HANDOFF/notes-astra.md, and new folders you create (for example
research/readiness/reviews/astra-<date>/, research/plans/ASTRA_*.md, jobs/astra-<name>/ with needs.txt).
Work on a branch named astra/side-<date>; open one pull request to main per batch; do not merge.
Do not claim any order already present in research/readiness/claims/ under another agent's file, any target of
the families Claude claimed (actors EO 11708, 12534, 11811, 11812, 12110, 9687 and the other families in
claude-2026-10-18-codif-b0..b7.jsonl), or any order PR #24's reports name. Before a production batch, write
the list of families or orders you are taking into HANDOFF/notes-astra.md and commit it.

EVIDENCE RULES. These override anything convenient:
  - Never change a provisional status, the research ledger, the codebook, a census identity, or any count.
    If the evidence contradicts a provisional status, leave the claim incomplete, say so in
    unresolved_material_gaps, and write it up for the owner in HANDOFF.
  - Never write a review with reviewer_role independent_human, and never write eo-lifecycle-review/v1 records.
    Your reviews are AI reviews: label them reviewer_role: ai_review in a research/ folder.
  - Never write a line to research/readiness/EXHAUSTED.jsonl unless research/readiness/README.md's two
    conditions hold: a source-ladder exhausted_proposed line that is not WEAK, or your own route-by-route
    search at least as thorough as the ladder. A one-route ladder result, a block, a timeout or a robots
    refusal is never exhaustion.
  - Never fetch a source by hand. Every source request is a FETCH_QUEUE.jsonl line with an https:// URL or a
    citation the ladder parses (FR, Stat., U.S.C., CFR, EO number); the 16 no_route results in the last ladder
    run were all free-text requests without a URL, so do not repeat that.
  - Quotations are word for word from the held bytes (watch PDF fonts that decode a dash as a plus-or-minus
    sign). Cite sources with URL plus SHA-256 and page; cite jobs/official-fixity/output/MATCHED_BY_SHA256.json
    for custody.
  - A first end is the earliest actual cessation of that clause: the order's own terms, an earlier partial
    amendment, a temporary body's actual end, or the revoking instrument's effective date, whichever came
    first and can be dated exactly. A report deadline is never an end. A formal "cleanup" revocation is the end
    only when nothing earlier ended the clause. Where the earlier date cannot be fixed, commit a partial claim
    with the gap stated; partial claims count step by step.
  - For YES orders, current_predicate needs a legal basis actually read (a U.S. Code or eCFR mention is a
    lead), with checked_through 2026-10-14 and a stated check of the Federal Register for 2026-10-09 to
    2026-10-14 (U.S. Code release 119-121 ends 2026-10-09). The 1989 Codification snapshot is never a basis.
  - APP texts (jobs/app-executive-orders/output/, mirror captures), Richardson, Wikisource, the HathiTrust and
    GPO scans Codex saved, and numbered-early-orders texts are discovery material: acceptable_as_original is
    false on all of them. Use them to find the official text, never as the original.
  - Machine outputs (drafts, certificates, candidates, leads) are leads. Nothing a job wrote is a finding until
    you have read the cited source.

TASKS, in this order. Each has a definition of done. Stop a task and move on when its budget is spent.

T1 (30-40 min). Opus re-fetch queue. Read jobs/opus-media-match/output/REFETCH_LIST.jsonl (848 lines). Count
   lines with a non-empty instrument_ids and an https url. If most qualify: the source-ladder is not picking
   the list up (jobs/source-ladder/output/log.txt line 6 says "0 Opus originals to re-fetch"); append one
   FETCH_QUEUE.jsonl line per distinct expected_sha256 {instrument_id: first id, urls: [url], citation:
   "opus refetch sha256=<expected_sha256>; also <other ids>", step: "opus_media", requested_by: "Astra
   opus-refetch <date>"} and ask Claude in HANDOFF to fix ladder_queue.opus_refetch_wanted. If instrument_ids
   is empty on most lines, queue nothing and write that finding as the ask instead. Done: the lines are
   committed, or the finding is in HANDOFF, and the next ladder SUMMARY.json shows the queue count.

T2 (1-2 h). Adversarial read of the census estimators. Read jobs/census-completeness/complete.py (functions
   chapman, chao1, mt_mle, mt_ci, match_mentions), output/REPORT.md and output/ESTIMATES.json. Judge the
   Mt/Chapman/Chao1 choice, the positive-dependence argument (Lord cites the same books), the direction of
   each bias, and the three matching scenarios. Write research/plans/ASTRA_REVIEW_CENSUS_ESTIMATORS_<date>.md
   with: what holds, what does not, what to change, and which numbers may be quoted with which caveat. Done:
   the file is committed and HANDOFF names it for Claude.

T3 (main production, batches of 25, independent producer and reviewer contexts, each fed one dossier at a
   time). Family-rule targets to claims. From research/readiness/rules/*.json take the decided targets with no
   claim (571; 476 already have original text and counterevidence done), excluding the orders in the
   non-interference list. For each: start from its line in jobs/claim-drafts/output/DRAFT_CLAIMS.jsonl (copy
   only the claim object, never _draft, never a PLACEHOLDER) or the packet in jobs/case-bundles/output/bundles/;
   read the held original; fix the clause inventory; read the acting instrument's effective-date wording and the
   order's own terms; check jobs/later-events/output/EDGES.csv for earlier partial amendments; copy the matching
   later_source_search from jobs/readiness-tracker/output/MACHINE_LATER_SEARCH.jsonl only after reading its
   scope; close savings with a quoted phrase or "none after bounded search" naming the search. Also finish your
   own 39 CLAIM_INCOMPLETE claims (astra-2026-10-17-*.jsonl) the same way, in a new file. Commit each batch to
   research/readiness/claims/astra-<date>-<family>.jsonl after your reviewer has read every source, with the
   AI review record under research/readiness/reviews/astra-<date>/. After each batch read
   jobs/claim-checker/output/REPORT.md and fix anything it fails. If the reviewer rejects more than 15% of a
   batch, stop, write the cause in HANDOFF, fix the method, then continue. Done per batch: claim file
   committed, checker read, counts recorded.

T4 (batches of 20, same producer/reviewer split). YES orders. From jobs/claim-drafts/output/TODO_BY_ORDER.csv
   take provisional_status = yes, only_judgment_left = yes, estimated_effort = small (160), skipping any order
   whose blockers in jobs/readiness-tracker/output/READINESS_BY_ORDER.csv include OPUS_MEDIA_NONE_CITED. Use
   jobs/current-law/output/ leads, read the cited provision, record current_predicate with checked_through
   2026-10-14 and the five-day Federal Register check. For the YES orders in jobs/later-events/output/
   COUNTEREVIDENCE_LEADS.csv (full-revocation candidate, some with a 2025 reinstatement), put both events in
   later_events with effective dates read from the instruments. Pattern: your EO 13306 claim in
   research/readiness/claims/astra-2026-10-18-p3complete.jsonl. Write research/readiness/reviews/astra-<date>/
   YES_METHOD.md once. Done per batch: as T3.

T5 (2-4 h first pass). Contrary leads. From READINESS_BY_ORDER.csv take the orders with
   MACHINE_SEARCH_FOUND_CONTRARY_LEAD (159: 151 current-law, 8 later-events), first the 43 that
   TODO_BY_ORDER.csv rates only_judgment_left = yes. For each, read the citing provision in
   jobs/current-law/output/POSSIBLE_CONFLICTS.csv (exact snippet given) or the lead in COUNTEREVIDENCE_LEADS.csv.
   Write research/readiness/reviews/astra-<date>/CONTRARY_LEADS.md: one row per order with the quote, whether
   the citation is historical or definitional (order stays NO; put the resolution in the claim's
   later_source_search) or evidence the order still operates (a status conflict: write it for the owner in
   HANDOFF; do not write a YES claim; do not change the status). Then the 36 QUARANTINED_RELATIONSHIP_CONFLICT
   orders from jobs/claim-drafts/output/CONFLICTS.csv, one memo each. Done: the file is committed and each
   resolved order's claim carries the resolution.

T6 (1-2 h). Sample review of the ready claims. Pick 30 claims across research/readiness/claims/
   claude-2026-10-18-codif-b0.jsonl to -b7.jsonl (stratified, at least 3 per file). For each, test the
   first-end date against the acting instrument and the order's own terms, and the clause inventory against the
   original. Write research/readiness/reviews/astra-<date>/READY_CLAIM_SAMPLE.md with one row per claim
   (claim sha256 from jobs/claim-checker/output/PER_CLAIM.json, verdict, reason) and the measured rate. Do not
   edit any claude-*.jsonl line; list disputed claims in HANDOFF for Claude. Also read PR #24's body and the
   EO 11352 proposal under research/excavator/2026-10-18/ on branch codex/corpus-excavator-20261018 and add a
   short section with your view for the owner. Done: file committed, HANDOFF names the disputed claims.

T7 (2.5-3 h). Page checks. From READINESS_BY_ORDER.csv take decided orders blocked by
   ORIGINAL_FOUND_NEEDS_PAGE_CHECK (88). For each, open the proposed pages from
   _draft.proposals.original_representation in DRAFT_CLAIMS.jsonl, confirm the complete text of this order,
   and commit a partial claim with the confirmed page_or_item in research/readiness/claims/
   astra-<date>-pagecheck.jsonl. State in the rationale that this identifies the official printing, not a
   signed original. Done: file committed, checker read.

T8 (30-60 min). Shared sources. For EO 4314, 6868, 6910, 6964, 48 U.S.C. 863 and 26 CFR 458.324
   (SHARED_UNLOCKS.csv rows 3-8), find concrete https:// routes: jobs/hathi-gpo-orders/output/RESULTS.csv and
   SOURCES.jsonl on main for the 1934-35 orders, govinfo USCODE historical editions or Statutes at Large for
   48 U.S.C. 863, a named historical CFR edition for 26 CFR 458.324, Wikisource or an official printing for
   EO 4314. Append FETCH_QUEUE.jsonl lines. Write no EXHAUSTED.jsonl line. Done: lines committed.

T9 (if time remains, 1-2 h). Write research/plans/PRE1937_LATER_SEARCH_PROTOCOL_<date>.md: the repositories
   and queries a pre-1937 order's later_source_search must cover (1989 Codification disposition tables in
   jobs/ofr-codification-1989/output/, the WPA numbered list's disposition notes, APP footnotes once
   jobs/app-footnote-leads/ exists, Lord's list, the saved-text sweep) and what "nothing contrary" means for
   each. Build no job for it.

TELEMETRY. For every batch record in HANDOFF: orders worked, steps lit (before and after from
jobs/readiness-tracker/output/SUMMARY.json), claims accepted and rejected by your reviewer, wall minutes, and
model-usage telemetry where your tools expose it; write null where they do not, and never substitute payload
savings for agent cost.

DEFINITION OF DONE for this session. All of these are true:
  1. Every claim you committed appears in jobs/claim-checker/output/REPORT.md with no mechanical failure, or the
     failure is listed in HANDOFF with what you will do about it.
  2. Every file you wrote is under the paths allowed above; `git status` on your branch shows nothing under the
     non-interference list.
  3. research/readiness/FETCH_QUEUE.jsonl gained only appended lines, each with an https URL or a parseable
     citation.
  4. No provisional status, ledger row, codebook entry, census identity, EXHAUSTED.jsonl line (unless both README
     conditions hold) or independent_human review was written.
  5. One pull request per batch is open against main, and none is merged by you.
  6. The top of HANDOFF/notes-astra.md has an entry in the README's shape:
       ## <date time ET>: <one line>
       - Done: files and commits per task (T1-T9), with the before/after tracker numbers.
       - Running: ladder or checker runs to look at, by job name and what to read.
       - Next: what you would do next, in priority order.
       - Asks: @Claude (the ladder's Opus re-fetch pickup; disputed claims from T6), @Codex, @Owner (status
         conflicts from T5; the OPUS_MEDIA_NONE_CITED rule; PR #24 view), one request each, specific enough
         to act on without asking back.
       - Do not: the files and families you are mid-way through.
     Write it before you stop, even if a task is unfinished.
```
