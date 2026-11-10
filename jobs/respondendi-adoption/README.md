# Respondendi: standing adoption of reviewed undecided-route statuses

Named for the *ius publice respondendi*, by which Augustus let vetted jurists give opinions with standing authority,
so that each answer did not need the emperor. The owner approves one rule ([`RULE.md`](RULE.md)) once; a status
proposal that meets every condition of that exact text is adopted without a per-order owner decision.

**Not in force until the owner approves it.** The tool refuses every `--write` plan or adoption until, on GitHub's
main (the local origin/main must equal `git ls-remote` when writing), a Kean decision whose ruling is exactly
`Owner approves respondendi-rule-sha256:<sha>` and an owner-ruling file under `research/readiness/owner_rulings/`
holding that exact line both name the current `RULE.md`
(`respondendi.py rule-sha`). Any edit to `RULE.md`, a parameter included, needs a new decision. No agent may record
that decision for the owner. One approval covers every lot kind in the rule; a kind with a route opens by itself
once the merged claim kit lists that route in `UNDECIDED_ROUTES` (`jobs/claim-kit/status_overlay.py`), starting on
its own audit probation. `respondendi.py kinds` shows which kinds are active.

## What it does

It carries out by script the hand route used for D-20261108-haloander-adopt and D-20261110-papinian-adopt, in
three steps:

1. **plan:** qualifies each line of a completion's `REPLACEMENT_PROPOSAL.jsonl` against the rule from pinned
   receipts only (manifest hash as the completion ran, publication, tally, checker result, both blind arms,
   after-reveal reviews, typed planted controls, status review, decision, proposal, `ADMISSION.json`), assigns each
   proposal to exactly one lot kind and checks that kind's zero-token predicate, gives each member its stratum
   (process fingerprint + kind + text basis + tier) and draws the audit sample: every member of a stratum on
   probation, then 20% (at least 2), seeded by the plan's hash.
2. **audit:** a person or an AI of another model family records agree or disagree for each sampled order;
   `adjudicate` settles a disagreement, and only a confirmed error counts.
3. **adopt:** once every sampled order is audited, writes `research/respondendi/lots/<lot>/ADOPTION_ROWS.csv`,
   `LOT.json`, `AUDITS.jsonl` and `RULE_AT_ADOPTION.md`; appends the rows to the status ledger; adds one pinned
   `accepted_additions` entry to `jobs/claim-kit/population_contract.json`; files whole-case claims canonically as
   `research/readiness/claims/respondendi-<lot>.jsonl`, byte-identical to the reviewed proposal lines; runs
   `population.validate_inputs` and restores every byte if the decided count did not grow by exactly the adopted
   orders.

## Commands

```bash
python -I jobs/respondendi-adoption/respondendi.py rule-sha
python -I jobs/respondendi-adoption/respondendi.py check --completion WAVE/u01/completion/complete-v1 --admission WAVE/u01/packet/ADMISSION.json
python -I jobs/respondendi-adoption/respondendi.py plan --lot wave-u01 --completion ... --admission ... --prompt WAVE/tools/prompts/producer.txt --prompt ... --write
python -I jobs/respondendi-adoption/respondendi.py audit-queue
python -I jobs/respondendi-adoption/respondendi.py audit-record --lot wave-u01 --order EO:N --auditor NAME --role independent_ai --family OpenAI --verdict agree --status-found no --basis "..." --evidence research/respondendi/lots/wave-u01/audit-evidence/EO_N.json --write
python -I jobs/respondendi-adoption/respondendi.py adjudicate --lot wave-u01 --order EO:N --adjudicator owner --role human --finding auditor_wrong --basis "..." --evidence research/respondendi/lots/wave-u01/audit-evidence/adj-EO_N.json --write
python -I jobs/respondendi-adoption/respondendi.py kinds              # which lot kinds are active on main
python -I jobs/respondendi-adoption/respondendi.py adopt --lot wave-u01 --write
python -I jobs/respondendi-adoption/respondendi.py reverse --lot wave-u01 --order EO:N --reason "..." --write
python -I jobs/respondendi-adoption/respondendi.py status
python -I jobs/respondendi-adoption/respondendi.py report --write      # research/respondendi/REPORT.md
python -I jobs/respondendi-adoption/respondendi.py verify               # exit 1 on any problem
```

Without `--write`, `plan` and `adopt` report what would qualify and why the rest would not, and write nothing. The
owner report is regenerated after every write. Coordinators follow [`UNDECIDED_CHECKLIST.md`](UNDECIDED_CHECKLIST.md);
producers of batches (the Maudslay conveyor, claim-drafting sessions) follow [`INTERFACE.md`](INTERFACE.md), the list
of every file and field `plan` reads.

## Safeguards built in

- **Lot kinds** (RULE.md table), fixed by the kit-emitted basis record, never by the producer's wording: express
  named revocation (`ACT:`, with a sentence-level check and a second witness) and own terms (`TERM:`), both active;
  spent on issue, including amendment-only orders (`OWN_TEXT:`, route `own_text`, F5; always fully audited); YES with a positive current
  source and negative screens (`CURRENT:`, route `current`, F3; always fully audited; stops on one confirmed error);
  the owner-approved Ulpian life-bound lot (opens when PR #271 is on main); a working-text basis for each kind
  (route `working_text`, F6). The merged kit's `UNDECIDED_ROUTES` opens a route;
  the kit's own gates are re-run on every proposal. Orders outside every kind stay on named owner decisions.
- **Sequential audit per stratum** (process fingerprint + kind + text basis + tier): every member is audited until
  the stratum's 95% upper bound on the error rate reaches 5% (59 audits with no confirmed error, 93 with one), then
  20% of each lot, each member drawn by its own claim hash. Only in-sample agreeing audits of adopted lots count;
  reversals count as errors; an order with a confirmed error or reversal never returns. Every audit and adjudication
  pins its own evidence file under `research/respondendi/lots/<lot>/audit-evidence/`, never reused, naming the order
  and its claim hash; an AI's is a JSON run receipt whose model id gives the family (another family than every
  reviewer's); a person must be on the rule's `human_auditors` list.
- **Stop rule, per kind** (kind + text basis + tier, across process changes): 2 confirmed errors in the last 59
  counted audits (1 for YES), or an upper bound above 10% after 30, stops the kind until the owner records on main
  `Owner resumes respondendi-resume:<kind key>@<audit count>`. A disagreement unadjudicated for 7 days blocks every
  adoption. Dates come from the clock.
- **Typed controls:** at least 2 a review set, of 2 kinds, one status-determining, each named in its adjudication.
- **Size and cadence:** at most 60 orders a lot, 300 a week, 1 lot a day (frozen evidence of packets in flight pins
  the whole ledger).
- **Suspension:** a decision citing `respondendi-suspend-sha256:<sha>` stops the rule.
- **Reversal** removes the row and lowers the contract count; a filed claim stays (claim files are append-only) with an
  unresolved source-audit hold; a pinned `REVERSAL_EO_N.json` says why.
- **Verify** re-checks every standing-rule entry: rule copy, committed owner decision, unaltered lot receipt, rows,
  ledger, canonical claims against the reviewed proposal lines, holds for reversals, and the population contract.

## What it never does

It never certifies (AI review and status audits are not human certification; the certified count stays 0), never
changes a decided status, never adopts a YES unless the rule's `statuses_allowed` includes it, and never decides a
status: it only checks that the project's review route and an outside audit reached the same verdict.

## Measured basis

Replayed on every owner adoption of an undecided-route proposal so far (Haloander ux 3, Papinian u01b 3, u02 3),
with the real claim-kit gates: 5 of the 9 meet every kind predicate (EO 11957, 12348, 9245, 10679, 11962); EO 9674
ends a body rather than naming the order, and EO 10733, 7814 and 12082 cite no qualifying record. Per-kind reachable
counts on main are in `research/excavator/claude-respondendi-2026-11-10/KINDS.json`. No past completion meets the
control condition (each review set had one untyped date-shift control), so the first lots under the rule come from
the next wave. See `research/excavator/claude-respondendi-2026-11-10/REPORT.md`.
