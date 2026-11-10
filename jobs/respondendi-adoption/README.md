# Respondendi: standing adoption of reviewed undecided-route statuses

Named for the *ius publice respondendi*, by which Augustus let vetted jurists give opinions with standing authority,
so that each answer did not need the emperor. The owner approves one rule ([`RULE.md`](RULE.md)) once; a status
proposal that meets every condition of that exact text is adopted without a per-order owner decision.

**Not in force until the owner approves it.** The tool refuses every `--write` plan or adoption until a committed Kean
decision and a committed owner-ruling file under `research/readiness/owner_rulings/` both carry
`respondendi-rule-sha256:<sha>` for the current `RULE.md` (`respondendi.py rule-sha`). Any edit to `RULE.md`, a
parameter included, needs a new decision. No agent may record that decision for the owner.

## What it does

It carries out by script the hand route used for D-20261108-haloander-adopt and D-20261110-papinian-adopt, in
three steps:

1. **plan:** qualifies each line of a completion's `REPLACEMENT_PROPOSAL.jsonl` against the rule from pinned
   receipts only (manifest hash as the completion ran, publication, tally, checker result, both blind arms,
   after-reveal reviews, typed planted controls, status review, decision, proposal, `ADMISSION.json`), keeps only
   members of the rule's lot (express, named, unqualified revocations), fixes the process stratum and draws the audit
   sample: every member while the stratum is on probation, then 20% (at least 2), seeded by the plan's hash.
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
python -I jobs/respondendi-adoption/respondendi.py audit-record --lot wave-u01 --order EO:N --auditor NAME --role independent_ai --family OpenAI --verdict agree --status-found no --basis "..." --write
python -I jobs/respondendi-adoption/respondendi.py adjudicate --lot wave-u01 --order EO:N --adjudicator NAME --role human --finding auditor_wrong --basis "..." --write
python -I jobs/respondendi-adoption/respondendi.py adopt --lot wave-u01 --write
python -I jobs/respondendi-adoption/respondendi.py reverse --lot wave-u01 --order EO:N --reason "..." --write
python -I jobs/respondendi-adoption/respondendi.py status
python -I jobs/respondendi-adoption/respondendi.py report --write      # research/respondendi/REPORT.md
python -I jobs/respondendi-adoption/respondendi.py verify               # exit 1 on any problem
```

Without `--write`, `plan` and `adopt` report what would qualify and why the rest would not, and write nothing. The
owner report is regenerated after every write. Coordinators follow [`UNDECIDED_CHECKLIST.md`](UNDECIDED_CHECKLIST.md).

## Safeguards built in

- **One lot:** express, named, unqualified whole-order revocations by a later order or proclamation (a zero-token
  check on the claim's located ending quote). Own-terms ends, amendment-only orders, statutes, working texts and every
  YES stay on named owner decisions until each has its own lot.
- **Sequential audit per process stratum** (prompts, checklist, kit code, lot and model families): every member is
  audited until the 95% upper bound on the error rate reaches 5% (59 audits with no confirmed error, 93 with one),
  then 20% of each lot. Auditors: a person or another model family.
- **Stop rule:** 2 confirmed errors in a stratum's last 59 audits, or an upper bound above 10% after 30 audits, stops
  the stratum until the owner records `respondendi-resume:<stratum>`. A disagreement unadjudicated for 7 days blocks
  every adoption.
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

Replayed on every owner adoption of an undecided-route proposal so far (Haloander ux 3, Papinian u01b 3, u02 3):
7 of the 9 are in the lot (EO 12082 and 7814 end by their own terms and stay on named decisions); every other
per-order condition held except the admission receipt, which predates `admission.py`. No past completion meets the
control condition (each review set had one untyped date-shift control), so the first lots under the rule come from
the next wave. See `research/excavator/claude-respondendi-2026-11-10/REPORT.md`.
