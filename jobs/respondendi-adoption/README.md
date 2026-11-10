# Respondendi: standing adoption of reviewed undecided-route statuses

Named for the *ius publice respondendi*, by which Augustus let vetted jurists give opinions with standing authority,
so that each answer did not need the emperor. The owner approves one rule ([`RULE.md`](RULE.md)) once; a status
proposal that meets every condition of that exact text is adopted without a per-order owner decision.

**Not in force until the owner approves it.** The tool refuses every `--write` adoption until both a Kean decision and
an owner-ruling file under `research/readiness/owner_rulings/` carry `respondendi-rule-sha256:<sha>` for the current
`RULE.md` (`respondendi.py rule-sha`). Any edit to `RULE.md`, a parameter included, needs a new decision. No agent may
record that decision for the owner.

## What it does

It carries out by script the hand route used for D-20261108-haloander-adopt and D-20261110-papinian-adopt:

1. qualifies each line of a completion's `REPLACEMENT_PROPOSAL.jsonl` against the rule from pinned receipts only
   (manifest hash as the completion ran, publication, tally, checker result, both blind arms, after-reveal reviews,
   planted controls, status review, decision, proposal, `ADMISSION.json`);
2. writes `research/respondendi/lots/<lot>/ADOPTION_ROWS.csv`, `LOT.json` (every check and pin) and
   `RULE_AT_ADOPTION.md`;
3. appends the rows to `research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv`;
4. adds one `accepted_additions` entry to `jobs/claim-kit/population_contract.json` pinning the rule copy, the
   owner ruling, the lot receipt and every review file;
5. files the qualifying claims canonically as `research/readiness/claims/respondendi-<lot>.jsonl`, byte-identical to
   the reviewed proposal lines;
6. draws the lot's audit sample, seeded by the lot receipt's hash;
7. runs the claim kit's `population.validate_inputs` and restores every byte if the decided count did not grow by
   exactly the adopted orders.

## Commands

```bash
python -I jobs/respondendi-adoption/respondendi.py rule-sha
python -I jobs/respondendi-adoption/respondendi.py check --completion WAVE/u01/completion/complete-v1 --admission WAVE/u01/packet/ADMISSION.json
python -I jobs/respondendi-adoption/respondendi.py adopt --lot wave-u01 --completion ... --admission ... --write
python -I jobs/respondendi-adoption/respondendi.py audit-queue
python -I jobs/respondendi-adoption/respondendi.py audit-record --lot wave-u01 --order EO:N --auditor NAME --role independent_ai --family OpenAI --verdict agree --status-found no --basis "..." --write
python -I jobs/respondendi-adoption/respondendi.py reverse --lot wave-u01 --order EO:N --reason "..." --write
python -I jobs/respondendi-adoption/respondendi.py status
python -I jobs/respondendi-adoption/respondendi.py report --write      # research/respondendi/REPORT.md
python -I jobs/respondendi-adoption/respondendi.py verify               # exit 1 on any problem
```

Without `--write`, `adopt` reports what would qualify and why the rest would not, and writes nothing.

## Safeguards built in

- **Audit sample** per lot, by a person or an AI of a model family different from every reviewer of that order
  (34% and at least 2 while on probation, until 59 agreeing audits in a row; then 10% and at least 1).
- **Stop rule:** one disagreeing audit writes `register/STOP.json`; nothing more is adopted until the owner records a
  decision citing `respondendi-resume:<stop_id>`. Reverse the disputed order with `reverse`.
- **Audit debt:** no new lot while more than 20 sampled orders wait, or any has waited more than 14 days.
- **Size:** at most 60 orders a lot, 300 a week.
- **Suspension:** a decision citing `respondendi-suspend-sha256:<sha>` stops the rule.
- **Reversal** removes the row, the canonical claim and the contract count, and pins a `REVERSAL_EO_N.json`.
- **Verify** re-checks every standing-rule entry: rule copy, owner decision, unaltered lot receipt, rows, ledger,
  canonical claims against the reviewed proposal lines, and the population contract.

## What it never does

It never certifies (AI review and status audits are not human certification; the certified count stays 0), never
changes a decided status, never adopts a YES unless the rule's `statuses_allowed` includes it, and never decides a
status: it only checks that the project's existing review route reached the same verdict three independent times.

## Measured basis

Replayed on every owner adoption of an undecided-route proposal so far (Haloander ux 3, Papinian u01b 3, u02 3):
each of the 9 met every condition except the admission receipt, which predates `admission.py`; no other proposal
line exists in those completions. See `research/excavator/claude-respondendi-2026-11-10/REPORT.md`.
