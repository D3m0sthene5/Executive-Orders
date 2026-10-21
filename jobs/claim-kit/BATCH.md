# Prepared evidence to explicit reviewed proposals

Run from the repository root. Check `output/STATUS.json`, `SUMMARY.json` and the
runner's `RUNNER_INPUTS.json` first. Source matches and status observations are
leads. No command below publishes a claim, status, identity or human review.

```text
python jobs/claim-kit/kit.py prepare EO:NUMBER EO:OTHER --agent NAME --write research/excavator/RUN/packet
python jobs/claim-kit/kit.py view research/excavator/RUN/packet
python jobs/claim-kit/kit.py view research/excavator/RUN/packet --source TEXT_BLOCK_ID
python jobs/claim-kit/kit.py apply research/excavator/RUN/packet --write research/excavator/RUN/packet/applied-v1
python jobs/claim-kit/kit.py batch-check research/excavator/RUN/packet research/excavator/RUN/packet/applied-v1
```

`prepare` accepts 1–50 explicit identities. It freezes complete dossiers, verifies
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
