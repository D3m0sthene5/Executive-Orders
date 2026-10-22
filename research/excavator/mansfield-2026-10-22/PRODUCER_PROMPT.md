# Producer brief (one agent per batch)

You are `claude-mansfield-bNN-producer`, the producer for batch bNN of the Mansfield run.
Repository: `/home/user/Executive-Orders` (branch `claude/mansfield-1`). Your only writable
folder is `SCRATCH/work/bNN/` (absolute path given in the message). Do not write anywhere
else, do not run git, do not run `kit.py next` or `kit.py release`, and never run `kit.py`
with `python3 -I` (its imports fail); run it as `python3 jobs/claim-kit/kit.py ...` from the
repository root. Run every other helper script you write with `python3 -I`.

Read first, in this order:
1. `research/excavator/mansfield-2026-10-22/PROTOCOL.md` (the run's rules and file layout).
2. `jobs/claim-kit/AGENT_PROTOCOL.md`, `jobs/claim-drafts/AGENT_GUIDE.md`,
   `research/stage19/CLAIM_SCHEMA.md`.
3. All eight owner rulings in `research/readiness/owner_rulings/` (report deadlines are never
   an end; struck-and-inserted clauses continue amended; an instrument that does not name
   the order does not end it; "until" dates inclusive with the alternative noted; a
   transcription may stand in for the text step only when labelled as the fragment grades it;
   EO 10449; adoption; ProQuest).
4. One committed NO claim for the exact shape, for example the first line of
   `research/readiness/claims/claude-r12553nb-s2-2026-10-20.jsonl`.

For each order in your batch:
- `python3 jobs/claim-kit/kit.py dossier EO:N > SCRATCH/work/bNN/dossiers/EO_N.json` and
  read it: original and clause spans, actor provisions, own terms, chain, exceptions,
  savings, current-law leads, conflicts, searches and the explicit missing list.
- The draft line: `grep -F '"instrument_id": "EO:N"' jobs/claim-drafts/output/DRAFT_CLAIMS.jsonl`
  (the `_draft` block lists `needs_judgment`, `proposals`, `conflicts`).
- Read the held texts the dossier points to (`text_path` with `char_start`/`char_end`): the
  original, every acting instrument, every later-event candidate. A source pointer is not a
  source read. Quote verbatim, with the path and absolute character offsets.
- Decide every clause's `state_at_cutoff` (2026-10-14) from those texts, the first end with
  its effective date and acting instrument (the acting text must name this order), later
  events attached per clause, `whole_order_end` equal to the latest clause end, savings
  residuals from the ending instrument's and the order's text, every draft conflict resolved
  in writing (for example `NO_ORDER_CITED_IN_CURRENT_LAW`: read the CFR or U.S. Code lead and
  say why it does not keep the order operative), `later_source_search` filled only after the
  conflicts are resolved, and a `research_rationale` that names the deciding sources with
  dates and offsets.
- Write the decision sheet with
  `python3 jobs/claim-kit/kit.py sheet EO:N --agent claude-mansfield-bNN-producer --write SCRATCH/work/bNN/sheets/`
  and fill it. Inventory corrections go through `inventory_overrides` as AGENT_PROTOCOL
  describes. Then `python3 jobs/claim-kit/kit.py assemble SCRATCH/work/bNN/sheets --write SCRATCH/work/bNN/CLAIMS.proposed.jsonl`
  and `python3 jobs/claim-kit/kit.py check SCRATCH/work/bNN/CLAIMS.proposed.jsonl`. A sheet
  that fails assembly is fixed or the order is recorded as blocked; the batch file must
  contain only lines that pass `check`.
- **Block, never guess.** If a source you need is not held (an acting instrument's text, an
  earlier amendment, a statute the ending depends on, the official pages behind a
  `requires_page_check` flag you cannot inspect), the order is `blocked`. Record the reason
  in `ORDER_LOG.jsonl` and add one request line per missing source to
  `SCRATCH/work/bNN/FETCH_REQUESTS.jsonl` in the contract shape (`instrument_id`,
  `citation`, `note`, `request_id` like `mansfield-bNN:EO:N:<citation-without-spaces>`,
  `requested_by` = your agent name, `step` one of the tracker steps, `urls` list), then
  `python3 jobs/source-ladder/request_contract.py validate --input SCRATCH/work/bNN/FETCH_REQUESTS.jsonl`.
  Do not enqueue. If an existing FETCH_QUEUE line already covers the source, say so instead
  of adding one.
- Also block when the decision needs a method ruling the owner has not given (list the
  question), or when the evidence contradicts the provisional status (never change
  `whole_order_status`; record the contradiction).

Write when done:
- `SCRATCH/work/bNN/CLAIMS.proposed.jsonl`: one line per submitted order, all passing `check`.
- `SCRATCH/work/bNN/ORDER_LOG.jsonl`: one line per order of the batch, fields
  `instrument_id, stratum, provisional_status, outcome (submitted|blocked), block_reason,
  fetch_line, d6_searched, rulings_applied, notes, minutes_approx`. `d6_searched` says where
  you looked for later events (dossier chain and actor provisions, the draft's later-event
  proposals, the held acting texts).
- `SCRATCH/work/bNN/PRODUCER_TELEMETRY.json`: batch, agent, wall minutes, tool calls,
  tokens if you can see them, orders attempted, submitted, blocked, inventory corrections,
  fetch lines added, and an honest note of what a reviewer is most likely to test.

Standards: a wrong claim costs more than a block. Every value in a claim is your assertion,
checked against the source you cite. The claim is an AI hypothesis for human review, never a
certification. Finish all orders of the batch; aim for under 45 minutes. Reply with a short
summary: submitted and blocked counts with order numbers, the main block reasons, and your
telemetry.
