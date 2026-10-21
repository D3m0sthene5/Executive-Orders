# Claim drafts (job 8)

**What it does, in one line:** for every order, it gathers what the other
machine jobs found and writes one pre-filled *draft* of the order's
whole-lifecycle claim, plus a to-do list of exactly what a research agent
(Opus, Astra) still has to decide.

It is an ordinary Python script: it costs no model tokens and makes no
downloads.

The embedded claim checker also runs **offline**. It reuses held bytes,
official-fixity records and existing verified-download receipts, and leaves a
missing receipt unverified. Acquisition belongs to source-ladder or the
standalone claim-checker job; `CLAIM_CHECKER_VERIFY_DOWNLOADS` does not enable
downloads inside claim-drafts. Previously this job inherited the standalone
checker's default allowance of 400 downloads with 120-second request timeouts,
despite promising no network requests.

Receipts are read from the draft's `checker-text/verified/` store and the
sibling standalone checker stores (`claim-checker/verified/` under the shared
runner cache, or `claim-checker-cache/verified/` for local runs). Additional
`CLAIM_CHECKER_CACHE_ROOTS` and their checker subdirectories are searched too.
Reuse is read-only and requires hashing the bytes; the draft job neither
copies nor writes predecessor receipts. A receipt changed or removed during
hashing is unverified for that invocation.

Existing verified-download bytes are hashed once per file version per run,
then reused for repeated references. The key includes the path, expected hash,
device, inode, size, nanosecond mtime and ctime. Changed, replaced or deleted
files are checked afresh; a new run rehashes all receipts it uses. No verdict
is persisted, and no absent receipt is promoted. Drafts, gates and quotations
are still rebuilt and checked on each run. The console reports rehashes,
within-run reuse and missing receipts separately. Windows rehashes each
reference because its ctime may be creation time, which cannot safely detect
a same-size edit whose mtime was restored.

## Why

Agents were spending most of their tokens copying source references, clause
texts and candidate dates by hand into the Stage 19 claim format. This job does
that copying. What is left for the agent is the part that needs judgment:
deciding the state of each clause on the cutoff date (2026-10-14), choosing the
real first ending among the candidates and confirming its effective date,
closing savings and residual effects, resolving conflicts, and writing the
rationale.

## What it reads

| From | What it uses |
|---|---|
| `jobs/fr-originals/output/` (or `data/full_run/`) | the order's printed Federal Register page (original text) |
| `jobs/opus-media-match/output/` | Opus archived page images/PDFs matched to the order (original text), and the Opus media status |
| `jobs/clause-drafts/output/` | the drafted clause inventory (each clause's exact text and source) |
| `jobs/later-events/output/` | later events and whole-order ending candidates from the OFR notes and order texts; the OFR catalog |
| `jobs/current-law/output/` | U.S. Code and eCFR mentions (leads that an order still operates), and endings stated there |
| `jobs/source-ladder/output/` | shared legal sources retrieved for the orders that cite them |
| `jobs/ofr-compilations/output/`, `jobs/isthmian-canal-1911/output/`, `jobs/indian-reservations-1912/output/` | official government printings of the orders' texts (OFR 1974 Hoover compilation, GPO 1911 Canal Commission orders, GPO 1912 Indian-reservation orders): original-text candidates, graded like fr-originals |
| `jobs/richardson-volumes/output/` | Richardson's *Messages and Papers* (vols VI, VII, IX): a printed compilation transcribed from records and newspapers. A lead to the original only |
| `jobs/ofr-codification-1989/output/` | the OFR 1989 Codification: later events and whole-order ends from its disposition table (`FRAGMENTS.jsonl`), and the orders printed as in force on 1989-01-20 (`CODIFIED_1989.csv`) |
| `research/stage21/original_sources/` | the 40 official per-document PDFs captured in Stage 21 |
| `research/stage20/output/` | the shared-source and statute queues; the Opus media audit |
| `research/progress/`, `research/stage15/CENSUS/`, `research/stage19/` | provisional statuses, the 14,972-order universe, the causal queue and the **claim gate** |
| `jobs/claim-checker/` | its mechanical checks (sources held, quotations word for word, dates, order numbers) are run on each draft |

Any other `jobs/*/output/FRAGMENTS.jsonl` in the shared fragment format is
merged too. A job with no output yet is simply skipped (the summary says so).

## What it writes (in `output/`)

- `DRAFT_CLAIMS.jsonl`: one line per order **with a provisional status** (all
  3,359 decided orders). Each line is
  `{"draft_schema": "eo-claim-draft/v1", "instrument_id", "claim", "_draft"}`.
  - `claim` is in the exact Stage 19 format. It contains only mechanical facts:
    the provisional status copied from the ledger, an original-text reference
    when a strong candidate exists, and the clause texts and their sources.
    Every judgment field (`state_at_cutoff`, `first_end`, `current_predicate`,
    `whole_order_end`, `savings_residuals`, `later_source_search`,
    `research_rationale`) is left empty on purpose, and
    `unresolved_material_gaps` lists what is open, so a draft can never pass
    the gate as it stands.
  - **A draft committed unchanged turns on no readiness step except
    `original_text`.** Two things make sure of that. First, machine search
    records are never put into `later_source_search`; they wait in
    `_draft.proposals.later_source_search_machine`. Second, when no clause
    inventory exists, the claim holds one placeholder clause
    (`DRAFT-PLACEHOLDER-no-clause-inventory`). An empty clause list would make
    the gate stop early, and the tracker would then count the steps it never
    checked. A unit test checks this with the tracker's own step mapping.
  - `_draft` says which fields were machine-filled and from which job, which
    fields need judgment, what evidence is missing, the conflicts, the
    candidates to choose from (already in the claim's field shapes), the gate
    errors that remain, the claim-checker result, the readiness steps the
    draft would satisfy once an agent confirms it, and an effort estimate.
- `DRAFT_CLAIMS_UNDECIDED.jsonl`: only with `CLAIM_DRAFTS_SCOPE=all`: the same
  for orders without a provisional status that some job found something for.
  These can never pass the gate (no status), so by default they are not
  written. (A file that would pass 90 MB is continued in `..._2.jsonl`,
  because GitHub cannot keep files over 95 MB.)
- `TODO_BY_ORDER.csv`: one row per draft: order, remaining gate errors, gate
  errors that would remain even after accepting the machine suggestions,
  whether only judgment is left, fields needing judgment, missing evidence,
  conflicts, `sources_and_quotes_check`, readiness steps, and estimated effort
  (small / medium / large). `sources_and_quotes_check` is the claim checker's
  verdict on **only the sources and quotations copied into the draft**
  (`sources_ok`, `sources_ok_some_unverified`, `source_or_quote_problem`). It
  never means the claim passes.
- `CONFLICTS.csv`: one row per conflict (order, code, detail).
- `SUMMARY.json`: counts, including orders with a draft, drafts whose only
  remaining gaps are judgment fields, and the most common conflict types.

### The printed-volume jobs (wired in 2026-10-18)

- **Official compilations** (`ofr-compilations`, `isthmian-canal-1911`,
  `indian-reservations-1912`) are government printings of the orders' texts.
  Their `original_representation` fragments become original-text candidates
  graded exactly like fr-originals: `official_compilation_high` (strong, so it
  can fill `claim.original_representation`) only when the job did not flag
  `needs_page_check` and the location is `high`; otherwise
  `official_compilation_needs_page_check` (never strong). An FR printing found
  by fr-originals ranks above them; they rank above the source ladder's FR
  pages.
- **Richardson** (`richardson-volumes`) is a compilation transcribed from
  department records and newspapers, not the signed or officially printed
  original. No rule in this job, the tracker or the claim checker treated a
  compiled printing as the original (an unknown producer was always graded
  `fr_originals_needs_page_check`, never strong; clause-drafts grades the
  American Presidency Project as `mirror_transcription_app`). So it becomes
  `compiled_transcription_lead`: `strong: false` and
  `acceptable_as_original: false`. It is never filled, never used by the
  feasibility test, and an order with only this lead keeps `original_text` in
  `missing_evidence`.
- **The 1989 Codification** (`ofr-codification-1989`). Its later-event
  fragments become later-event proposals (`date_candidate`, never
  `effective_date`), flagged `ofr_codification_1989_editorial` with a caution.
  An unqualified revocation (or rescission, or "superseded or revoked") is also
  offered as a whole-order-end proposal, under later-events' own rule: no
  qualifier, no `needs_page_check` from the codification job (medium/low
  pairing), and no item from any job saying the same acting instrument acted
  only in part (else the item stays a later event, flagged
  `full_and_partial_evidence_conflict`). Plain supersessions and terminations
  stay later events, as in later-events. Those proposals carry the flag
  `whole_end_from_1989_disposition_table`; like every whole-order-end proposal
  their `date` is the acting document's signing date, not a confirmed
  effective date. The disposition table and the later-events OFR catalog notes
  are the same OFR data (the online edition of these tables), so when both
  name the same ending the group is **not** `corroborated_by_two_jobs`, and
  later-events' item stays first.
  The orders printed as in force on 1989-01-20 (`CODIFIED_1989.csv`) become a
  `current_predicate` lead with `basis_code` `ofr_codification_1989_in_force`
  and `checked_through` `1989-01-20`. It is listed after every current-law
  lead, never used by the feasibility test, never counted as a current-law
  lead, and it can never pass the gate (which needs `2026-10-14`). The
  codified texts are as amended to 1989, so they are never original-text
  candidates.
- `SUMMARY.json` -> `book_sources` counts the drafts that use each of these.

### What "only judgment left" means

The job makes a *copy* of each draft, puts the suggested candidates and
placeholder text into it, and runs the claim gate on that copy. If the copy
passes, every gap in the real draft is something the agent decides from
evidence that is already in the draft. If it fails, the remaining errors show
evidence that no machine has found yet. The copy is never written out.

### Conflict codes

| Code | Meaning |
|---|---|
| `NO_ORDER_CITED_IN_CURRENT_LAW` | provisional NO, but the U.S. Code or eCFR still cites the order |
| `NO_ORDER_IN_FORCE_ON_1989_01_20` | provisional NO, the OFR 1989 Codification prints the order as in force on 1989-01-20 (not restated by a later order), and no ending candidate is dated after that day |
| `YES_ORDER_HAS_WHOLE_END_CANDIDATE` | provisional YES, but a source says the whole order was revoked or superseded |
| `WHOLE_END_DATE_DISAGREEMENT` / `WHOLE_END_ACTOR_DISAGREEMENT` | ending candidates name different dates or different acting instruments |
| `WHOLE_END_DATE_MISSING_OR_DISPUTED` | an ending candidate has no single exact date |
| `FULL_AND_PARTIAL_EVIDENCE_CONFLICT` | sources read as both a whole and a partial ending |
| `LATER_REINSTATEMENT_CANDIDATE` | a later instrument may have restored the order |
| `STATED_EFFECTIVE_DATE_DIFFERS` | the source states an effective date different from the instrument's date |
| `EVENT_BEFORE_SIGNING` | a candidate date is earlier than the order's signing date |
| `CANDIDATE_DATED_AFTER_CUTOFF` | a candidate is dated after 2026-10-14 (left out of the proposals) |
| `SIGNING_DATE_DISAGREEMENT` / `ORIGINAL_FR_CITATION_DISAGREEMENT` | sources disagree on the order's own date or FR citation |
| `QUARANTINED_RELATIONSHIP_CONFLICT` | the Stage 19 causal queue holds quarantined relationships for the order |
| `CLAUSE_TEXT_NOT_AT_OFFSETS` | a drafted clause text is not where clause-drafts said it was in its saved text |
| `PARTIAL_END_CANDIDATE_ON_YES_ORDER` | provisional YES, but a later event revokes, supersedes or ends part of the order (e.g. "sections 1 and 2"); those clauses are not simply operative |

## How to run

**On GitHub:** commit a change to this folder, or open Actions, choose **Run
jobs**, then **Run workflow**, and type `claim-drafts`. It reads whatever the
other jobs have committed in their `output/` folders. Run it again after those
jobs have new results.

**On the PC** (Git Bash, from the repo folder):

```
REPO_ROOT=. OUTPUT_DIR=C:/Users/danie/AppData/Local/Temp/eo-jobs/claim-drafts/out python jobs/claim-drafts/job.py
```

or PowerShell:

```
$env:REPO_ROOT='.'; $env:OUTPUT_DIR='C:/Users/danie/AppData/Local/Temp/eo-jobs/claim-drafts/out'; python jobs/claim-drafts/job.py
```

Always use an output folder outside the repo (the job refuses to write inside
`research/`). The unit tests run first; if they fail, nothing is written.

Options (environment variables):

- `JOB_LIMIT=50`: draft only the first 50 orders (decided orders first, the
  ones with the most machine evidence first).
- `CLAIM_DRAFTS_IDS=EO:12944,EO:9066`: draft only these orders.
- `CLAIM_DRAFTS_SCOPE=decided` (the default): only the 3,359 orders with a
  provisional status. `CLAIM_DRAFTS_SCOPE=all` also writes
  `DRAFT_CLAIMS_UNDECIDED.jsonl`.
- `CLAIM_DRAFTS_INPUTS="<folder>;<folder>"`: read other jobs' results from these
  folders instead of `jobs/*/output/` (for trying out sample runs kept outside
  the repo). Each folder's job is read from its `SUMMARY.json`; write
  `<job>=<folder>` if it cannot be told. A folder listed twice is read once.
  The output names such folders by their path inside the repo, or by their
  last two folder names, never by the full local path.
- `CLAIM_DRAFTS_CHECKER=0`: skip the claim-checker checks (faster).
- `CLAIM_CHECKER_CACHE_ROOTS=<folder>`: where other jobs' download caches are,
  so the checker can re-hash their saved bytes.
- `JOB_CACHE_DIR`: where the checker keeps extracted PDF text (default
  `<OUTPUT_DIR>/../claim-drafts-cache`; never committed).
- `CLAIM_DRAFTS_MAX_FILE_MB=90`: when a drafts file is continued in a new file.

A job whose `output/STATUS.json` says its last run failed is not merged; the
summary says so in `input_notes`. Order ids in `CLAIM_DRAFTS_IDS` that are not
in the universe are listed there too.

A full run over all inputs takes a few minutes. Committed output is the
decided drafts plus two CSV files; candidate details that would only repeat
other fields or are empty are left out to keep it small. Measured on the PC
with full clause-drafts, later-events and U.S. Code inputs: 62 seconds, a
36 MB `DRAFT_CLAIMS.jsonl` and a 4 MB `TODO_BY_ORDER.csv`. With the full U.S.
Code and fr-originals results it will grow, which is why each file is
continued in a new one before 90 MB.

### Note for the readiness tracker's owner

The tracker counts a claim step as done when no claim-gate error maps to it.
Two gaps let a careless claim light steps it has not earned:

- A claim with an empty `operative_clauses` list makes the gate stop early,
  so `ending_or_current_basis`, `savings_residuals` and `counterevidence`
  show as done. The tracker should treat `operative_clauses_empty` as failing
  every clause-dependent step.
- `counterevidence` is done as soon as `later_source_search` has entries,
  even while `unresolved_material_gaps` still lists `CONFLICT ...` lines.
  The tracker should fail `counterevidence` while such lines remain.

This job's drafts avoid both, and AGENT_GUIDE.md tells agents never to commit
either case. The tracker itself still needs the change; this job does not
edit it.

## What it does NOT establish

- Nothing legal. A draft is a collection of leads with their sources. It does
  not say whether a clause was operative on 2026-10-14, when the order really
  ended, or whether any savings or residual effects survive.
- Candidate dates are the acting instrument's signing or printed date, never a
  verified effective date. That is why later-event proposals call the date
  `date_candidate`, not `effective_date`. The agent renames the key only after
  confirming the effective date.
- A complete machine search is not proof that nothing was missed. The OFR
  catalog search starts in 1937, so for older orders it is flagged
  `coverage_warning` and not counted as enough.
- A current-law mention is a lead, not a legal basis.
- It never writes into `research/readiness/claims/` (claims there are written
  by agents, after judgment), never changes a provisional status, a ledger or
  a count, and never counts as a human review.
- The claim-checker result on a draft only tells you whether the sources and
  quotations the machines copied hold up; the gate result tells you what is
  still missing.

For agents: see [AGENT_GUIDE.md](AGENT_GUIDE.md).
