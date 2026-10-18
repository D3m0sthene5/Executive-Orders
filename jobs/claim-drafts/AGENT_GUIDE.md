# Agent guide: from a draft to a claim the tracker counts

For Opus, Astra and any other research agent. A draft saves you the copying; it
does not save you the reading. Every value you put into a claim is your
assertion, checked against the source you cite.

## 1. Pick an order

Open `jobs/claim-drafts/output/TODO_BY_ORDER.csv`.

- Start with `only_judgment_left = yes` and `estimated_effort = small`: all the
  evidence is in the draft; you read and decide.
- `remaining_gate_errors` is your to-do list (`clause_*_state x12` means twelve
  clauses still need a state).
- `gate_errors_if_proposals_accepted` lists what no machine found: that part
  needs research, not just judgment.
- `conflicts` must be resolved before the claim can be complete.

Find the order's line in `DRAFT_CLAIMS.jsonl` (search for
`"instrument_id": "EO:12944"`).

## 2. Copy only `claim`

Copy the `claim` object. Never copy `_draft`, and never keep a value that
contains `PLACEHOLDER`. The claim must stay in the Stage 19 format
(`research/stage19/CLAIM_SCHEMA.md`).

If the draft has no clause inventory, `operative_clauses` holds one clause
with `scope_id` `DRAFT-PLACEHOLDER-no-clause-inventory`. It only stands in for
the real clauses. Replace it with the order's real clauses; never delete it
and leave the list empty (see the hard rules in section 5).

## 3. Finish the judgment fields

Work through `_draft.needs_judgment`, then `_draft.gate.errors_now`.

- **`whole_order_status`**: copied from the provisional ledger. Never change it.
  If the evidence contradicts it, leave the claim incomplete, say so in
  `unresolved_material_gaps`, and write a note in `HANDOFF/`.
- **`original_representation`**: if filled, open the cited pages and confirm they
  are this order's complete official text; correct `page_or_item` if needed. If
  empty, pick from `_draft.proposals.original_representation`. A candidate with
  `strong: false` (for example `fr_originals_needs_page_check` or
  `official_compilation_needs_page_check`) counts only after you have checked
  the PDF pages yourself. A `compiled_transcription_lead` (Richardson,
  `acceptable_as_original: false`) is never the original: use it to find the
  official text.
- **Clause inventory**: compare `operative_clauses` with the official original.
  Add missing clauses, fix boundaries, and keep each `scope_id` unique. Clauses
  copied from a mirror (`_draft.clause_inventory_info.source_grade`
  `mirror_transcription_app`) must be checked word for word against the
  official text; cite the official copy where you can.
- **`state_at_cutoff`** for every clause: `operative`, `terminated` or
  `never_activated`.
  - `terminated` / `never_activated`: fill `first_end` with
    `{date, actor, mechanism, source}`. The shapes in
    `_draft.proposals.whole_order_end[].proposal` already fit. Their `date` is
    the acting instrument's signing or printed date: confirm the **effective**
    date in the acting instrument (see `meta.stated_effective_date_candidates`).
    `suggested: true` marks the earliest usable candidate; it is a suggestion,
    not a finding.
  - On a YES order, check `PARTIAL_END_CANDIDATE_ON_YES_ORDER` conflicts and
    the `operative_clauses[*].state_at_cutoff / first_end` judgment. They
    list later events that revoke or supersede named sections. Those clauses
    are `terminated` unless you rule the event out from the acting
    instrument.
  - `operative`: fill `current_predicate` with
    `{legal_basis, source, checked_through}`. `_draft.proposals.current_predicate`
    has leads in this shape. A mention in the U.S. Code or eCFR is only a lead;
    read the provision. `checked_through` must be `2026-10-14`, and you must
    actually have checked that far (U.S. Code release 119-121 is current only
    through 2026-10-09). A lead with `basis_code`
    `ofr_codification_1989_in_force` says only that the 1989 Codification
    printed the order as in force on 1989-01-20; it is never a legal basis.
  - Proposals flagged `ofr_codification_1989_editorial` come from the 1989
    Codification's disposition table (an OCR cell, status as of 1989-01-20).
    A formal revocation there may follow an earlier cessation by the order's
    own terms; read the order and the acting instrument.
- **`later_events`** of each clause: attach the candidates from
  `_draft.proposals.later_events` that affected that clause
  (`clause_hint_scope_ids` suggests where), each with `effective_date`,
  `actor`, `mechanism` and `source`. The proposals carry `date_candidate`
  instead of `effective_date` on purpose. That date is the acting
  instrument's signing or printed date. Rename the key to `effective_date`
  only after you have confirmed the effective date in the acting instrument.
- **`whole_order_end`** (NO orders only): its `date` must equal the **latest**
  `first_end.date` among the clauses. For YES orders it stays `null`.
- **`savings_residuals`**: `{state, reason, source}` with state
  `none_after_bounded_search`, `continuing_independent` or
  `transferred_or_accrued`. Read the ending instrument and the order itself;
  `_draft.proposals.savings_leads` lists phrases worth reading.
- **`later_source_search`**: empty in every draft. The searches the jobs
  ran over the whole corpus are in
  `_draft.proposals.later_source_search_machine` (by `search_id`; the wording
  to paste is the `entry` with the same `search_id` in
  `output/SUMMARY.json` → `machine_searches`). Paste an entry only after
  judging it adequate for this order. An item with a
  `coverage_warning` (for example, an order from before 1937, which the OFR
  catalog does not reach) is not enough on its own. Add your own searches
  (`{repository, query_or_scope, checked_on}`).
  `_draft.proposals.later_source_search_partial` lists sample-run searches that
  did not cover everything; they are not enough either.
- **Conflicts** (`_draft.conflicts`): resolve each one from the sources. Delete
  its `CONFLICT ...` line from `unresolved_material_gaps` only when it is
  resolved.
- **`research_rationale`**: your substantive reasoning (at least 40 characters;
  in practice a paragraph naming the sources that decide the case).
- **`unresolved_material_gaps`**: must be `[]` for a complete claim. Remove each
  `DRAFT: ...` line only when that item is done.

If a step cannot be finished by anyone (no source exists), add a line to
`research/readiness/EXHAUSTED.jsonl` (format in `research/readiness/README.md`)
and keep the gap listed in `unresolved_material_gaps`. Lines in the source
ladder's `EXHAUSTED_PROPOSED.jsonl` may be copied only after you have checked
them, and never when their note says `WEAK`.

## 4. Check before you commit

From the repo root:

```
python - <<'EOF'
import json, sys
sys.path.insert(0, "research/stage19/code")
import claim_gate
claim = json.load(open("my_claim.json", encoding="utf-8"))
print(claim_gate.validate_claim(claim, expected_status=claim["whole_order_status"]))
EOF
```

An empty list `[]` means the structure is complete. Then run the claim checker
on your file (it checks that your sources are held and your quotations are word
for word):

```
CLAIM_CHECKER_CLAIMS=my_claims.jsonl REPO_ROOT=. OUTPUT_DIR=C:/Users/danie/AppData/Local/Temp/eo-jobs/my-check python jobs/claim-checker/job.py
```

## 5. Commit the claim

Append the claim as **one line** of JSON to a file in `research/readiness/claims/`,
for example `research/readiness/claims/astra-2026-10.jsonl`. If two lines have the
same `instrument_id`, the later one (by file name, then line) wins.

Partial claims are allowed: the readiness tracker lights up each step as soon
as its part passes the gate (for example `original_text` once
`original_representation` is right, `clause_inventory` once every clause has a
state and a source). Do not commit machine values you have not checked: a
machine search record or a suggested ending in a committed claim is *your*
assertion.

**Hard rules.** The tracker does not catch these yet, so a claim that breaks
them would count steps nobody has done:

1. **Never commit a claim whose `operative_clauses` is empty.** The gate
   stops at `operative_clauses_empty` and checks nothing after it. The
   tracker would then count `ending_or_current_basis`, `savings_residuals`
   and `counterevidence` as done. The same applies to a claim that still
   holds the `DRAFT-PLACEHOLDER-no-clause-inventory` clause. That clause is
   harmless, because it never passes, but it means the inventory is not done.
2. **Never fill `later_source_search` while any `CONFLICT ...` line remains**
   in `unresolved_material_gaps`. The tracker counts `counterevidence` as
   soon as `later_source_search` has entries, and it does not read the
   CONFLICT lines. Resolve the conflicts first, or leave the search empty.
3. Never commit a claim for an order with no provisional status
   (`whole_order_status` empty).

The tracker (`jobs/readiness-tracker/output/TRACKER.md`) and the claim checker
pick the claim up on their next run. A claim is not a review: the independent
human review (`eo-lifecycle-review/v1`) is separate and is never written by an
agent.

## Step names (readiness tracker)

`original_text`, `clause_inventory`, `ending_or_current_basis`,
`savings_residuals`, `counterevidence`, `shared_sources`, `opus_media`.
`_draft.readiness.by_step` says, per step, `confirm` (evidence is in the draft;
check and accept it), `agent_judgment`, `resolve_conflicts`, `research` (no
machine evidence yet), `done_now` / `done_now_by_custody` (the tracker already
counts it) or `n/a`.
