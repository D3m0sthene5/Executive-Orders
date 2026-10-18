# Claude's handoff notes

Newest entry first. See `README.md` in this folder for the format.

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
