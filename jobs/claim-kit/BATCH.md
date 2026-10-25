# Prepared evidence to explicit reviewed proposals

Run from the repository root. Check `output/STATUS.json`, `SUMMARY.json` and the
runner's `RUNNER_INPUTS.json` first. Source matches and status observations are
leads. Only explicit `complete --publish` files eligible claims or isolated
replacement proposals; no command publishes a status, identity or human review.

```text
python jobs/claim-kit/kit.py prepare EO:NUMBER EO:OTHER --agent NAME --write research/excavator/RUN/packet
python jobs/claim-kit/kit.py view research/excavator/RUN/packet
python jobs/claim-kit/kit.py view research/excavator/RUN/packet --source TEXT_BLOCK_ID
python jobs/claim-kit/kit.py apply research/excavator/RUN/packet --write research/excavator/RUN/packet/applied-v1
python jobs/claim-kit/kit.py batch-check research/excavator/RUN/packet research/excavator/RUN/packet/applied-v1
python jobs/claim-kit/kit.py complete research/excavator/RUN/COMPLETION.json --write research/excavator/RUN/complete-v1
```

After independent source review, `complete` selects explicitly reviewed producer
versions, checks controls and exact source-audit holds, runs the existing gates,
actual checker and before/after tracker, and prepares publication bytes and a
compact exception/tally report. See [COMPLETION.md](COMPLETION.md) for its input
contract. It preserves source/legal judgment in independent records. Add
`--publish` only when filing the manifest's own-agent destination or isolated
replacement proposal is authorized. Human certification remains separate.

`prepare` accepts 1–50 explicit identities, decided or undecided. It freezes complete dossiers, verifies
held source text hashes/spans once, and writes a lossless `PACKET.json`, readable
`READ.md`, blank `decisions.csv` / `clauses.csv`, shared `RATIONALES.json`, and
`PREPARE.json`. Use the small `view` catalogue to navigate common text and member
metadata instead of printing both large representations. READ links evidence to
exact text blocks and absolute character spans. Unverified text remains literal;
missing material, overflow pointers and codec warnings remain visible. Overflow
is an explicit load task, not a claim that its body was reviewed.

Existing claims and frozen upstream proposals are routed to their owner. An
explicit `--replacement-proposal` permits an isolated proposal for owner review;
it does not take ownership. Other agents' reservations are preserved. `next`
groups actual shared actor/provision/source/exception patterns, then falls back
to individual orders. Generic own-term categories are never shared legal groups.

Read every original and common source independently. In decisions.csv, retain
one row for every member and choose `submit`, `blocked`, `unresolved`, or
`route_owner`. Give every submitted member its own earlier-end, scope,
independent-command and savings explanations. Common rationale can be referenced
as `@rationale:KEY`, with that key defined in RATIONALES.json. A deadline, a
not-later-than bound, an implementation command and an actual completion date
are different propositions. A later revocation does not prove first cessation
for a command already performed.

The dossier's `lifecycle_obligations` retains clause-specific wording features
and first-cessation questions. Deadline, actual-performance lead, recurring
duty, fixed sunset, contingent end, extension, renewal, and savings are separate
features; overlapping features remain visible. Every field remains a research
obligation, never an established ending. ACT ingestion records likewise do not
establish a complete lifecycle.

For a source-blocked attempt, retain the original failure and run
`lifecycle_obligations.py checkpoint` with the dossier, validated unresolved
requests, the SHA-256 of relevant route code/configuration, and result paths.
Pass `--source-results` with relevant acquisition receipts so a newly held
document can reopen work before the next corpus rebuild. Receipt timing alone
does not reopen an unchanged failure. The content fingerprint is recomputed;
a stale embedded dossier fingerprint cannot conceal changed evidence.
Before repeating research, `lifecycle_obligations.py resume` compares those
substantive inputs: unchanged work is deferred; changed evidence, requests or
routes reopen it. Use a new output filename for every checkpoint/decision.
Submit requests through `jobs/source-ladder/request_contract.py`; metadata and
delivery deadlines cannot substitute for the required occurrence evidence.

Clause rows execute through the existing assembler. For corrected inventory,
fill the `inventory_source_id`, absolute `inventory_char_start` / `end`, and
`inventory_reason` columns for every replacement scope. They become the existing
`inventory_overrides`; no free-text source substitution occurs. Every unresolved
member remains in AUDIT.json and counts. Failed submissions are retained rather
than disappearing from the batch. Each apply uses a new result directory.

`batch-check` repeats exact dossier/claim checks and invokes the actual
claim-checker against the proposed lines, using held evidence with network
verification disabled. It prints compact counts and actionable assembly errors;
the complete checker audit and log remain under the applied directory. Its exit
code fails on any unsuccessful submitted claim. This mechanical gate does not
replace independent source/legal review. Read the actual checker audit when
custody, identity or quotations fail. A separate reviewer checks every member;
keep rejections and correction versions. Owner acceptance governs promotion of
replacement proposals through the existing claim workflow.

Decision edits reuse the sealed packet and held source hashes. Neither `apply`
nor `batch-check` extracts or rebuilds the corpus. A changed source/packet or
assembler pin fails closed; prepare and review the changed evidence explicitly.

## Undecided identities

Ordinary `prepare` uses `status_overlay.freeze_evidence` for undecided members:
the full base dossier starts with `whole_order_status` unset and a blank
`STATUS_DECISION.json` beside it. Selection includes undecided work by default;
`next --scope decided|undecided|all` can bound an assignment. Existing ownership,
reservations and source grades still govern selection.

Use one cumulative source analysis for both output scopes. Fill the ordinary
lifecycle CSV while investigating status. `apply` preserves the populated sheet
and returns `awaiting_status_review` until the exact status decision is reviewed.
Pass that saved sheet to `overlay-propose --lifecycle-sheet PATH`; the command
preserves analysis, changes only the explicit status/dossier binding and resets
producer approval to false. Reconfirm it after inspection, then assemble and
obtain the separate exact lifecycle review. This path never adopts a status.
The explicit overlay commands below remain supported.

```text
python jobs/claim-kit/kit.py overlay-prepare EO:NUMBER --agent NAME --write research/excavator/RUN/overlay/EO_NUMBER/freeze-v1
python jobs/claim-kit/kit.py overlay-review-sheet --evidence EVIDENCE.json --decision STATUS_DECISION.json --reviewer OTHER --write STATUS_REVIEW.json
python jobs/claim-kit/kit.py overlay-propose --evidence EVIDENCE.json --decision STATUS_DECISION.json --review STATUS_REVIEW.json --write research/excavator/RUN/overlay/EO_NUMBER/proposal-v1
python jobs/claim-kit/kit.py overlay-assemble research/excavator/RUN/overlay/EO_NUMBER/proposal-v1 --sheet LIFECYCLE_DECISION.json --write research/excavator/RUN/overlay/EO_NUMBER/proposal-v1/CLAIMS.working.jsonl
python jobs/claim-kit/kit.py overlay-check research/excavator/RUN/overlay/EO_NUMBER/proposal-v1 research/excavator/RUN/overlay/EO_NUMBER/proposal-v1/CLAIMS.working.jsonl
```

Fill the producer status decision before creating the independent review sheet.
Review every history observation/conflict, establish a source-backed provisional
recommendation, and retain lifecycle gaps separately. An editorial snapshot
alone cannot support promotion; a YES needs the current predicate through the
cutoff. The independent review pins the exact producer decision and evidence.
`overlay-propose` emits a versioned promotion proposal, complete experimental
dossier and blank lifecycle decision. Its owner acceptance is always false.
The subsequent working assembler uses existing clause gates and preserves the
experimental label; it cannot silently enter the canonical claims path.

Freeze consumes compiled inputs once. Decision edits revalidate bounded held
sources, identity/status authority, history and consumed compiler manifests.
Runner receipt-only updates reuse the same evidence and proposal; actual code,
source, history, authority or consumed-manifest changes require a new freeze and
review. No authoritative status/census write command exists here.

The real EO11352 status proposal and the EO4314/EO12331 blocked handoffs are in
`research/excavator/2026-10-18/batch-pilot/overlay/`. EO11352's provisional NO is
not a certified whole lifecycle or an inferred exact first-end date.

## Verification and limits

The prespecified six-case matched experiment, initial errors, corrections,
independent completeness audit, frozen fifty-case preflight, corpus opportunity
pass and actual checker/tracker replays live under
`research/excavator/2026-10-18/batch-pilot/`. Byte reductions are not token or
review savings. Count blocked cases, acquisition, implementation and corrections
in the workload. The sample's legal rejections demonstrate that packaging does
not eliminate substantive research or independent review.

Runner input declarations in `inputs.txt` complement literal `needs.txt` and
`after.txt`. The publication guard records actual consumed repository versions
and rejects concurrent newer inputs/outputs; it does not establish source truth.


The `working_text` column contains the decision sheet's provisional-text disclosure
as JSON. Complete its source-specific identity/completeness/page confirmations only
after inspecting the held representation, and keep its standing replacement/recheck
note. Blank confirmation values remain blocked. See `AGENT_PROTOCOL.md` for scope;
this column grants no original authentication or custody waiver.

Ordinary `prepare` also discovers actual status decisions, their exact scoped
reviews and adoption state, withheld findings and parent-ending holds, alongside
existing lifecycle claims, exact-version AI
reviews, selected-version manifests and unfinished producer checkpoints throughout
`research/`. `prior_research` in PACKET and the prior-work section in READ / `view
--order` retain paths, hashes, review scope, rejected versions, source availability,
conflicting propositions and the current claim's remaining gaps. Different original
quotes or source identities require scope reconciliation; a matching scope name or
an overall upheld verdict supplies no approval. Decisions remain blank. No directory
recency or checkpoint selection silently replaces the canonical claim.

`apply` / `batch-check` recheck that context, including newly discovered work and
changed source or review dependencies. Prepare a new packet when it changes. The
existing `lifecycle_obligations.py checkpoint` / `resume` commands include this same
context by default (`--repo` selects the repository), so newly found research reopens
an unchanged source-blocked attempt. These commands do not convert prior research
into a new legal conclusion or certify its sources.

Before normal preparation in a sparse checkout, materialize this job's existing
`needs.txt` roots. `research/readiness` already includes canonical claims and
versioned producer/reviewer work; `research/excavator` and `research/production`
retain the other checkpoints, reconciliation and frozen-selection artifacts.
These declarations avoid treating an unmaterialized research session as an empty
history. They do not materialize the ProQuest corpus or fetch primary sources.
