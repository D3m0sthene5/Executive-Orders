# Estimand: what "share of executive orders still in legal effect" means

Justinian, 2026-11-06. Owner ruling R1 (Kean D-20261106-justinian-r1). It changes no codebook text, status or count.

## Headline

**The headline statistic is operative force at the legal cutoff.** It is the share of executive orders that, on
2026-10-14, still had at least one operative clause: one that commanded, authorized or established something with
legal effect. This is the codebook's `present_normative_effect`, rolled up by rule TC03 (`yes` if at least one
supported ongoing substantive, institutional, dormant, durable or incorporated effect; `no` only if every
substantive scope ended; otherwise `indeterminate`). Rule TC01 applies: "formal disposition, operative effect,
cessation cause, judicial enforceability and evidence sufficiency are distinct"; never derive current force from a
formal label alone.

**Formal validity is a separate column and never the headline.** It asks whether the order was unrevoked on the
books at the cutoff, meaning no instrument formally revoked, superseded or rescinded it. An order can lack operative
force yet be formally valid: an emergency board that reported in 1946 and was never revoked. It can also be formally
revoked in 1986 after it had lost force in 1946. Schema v2 records the formal disposition (`formal_disposition`)
apart from the first end, and the gate derives `formal_revocation_after_earlier_cessation`.

| Column | Question at 2026-10-14 | Source field |
|---|---|---|
| **Operative force (headline)** | Did any clause still operate? | `whole_order_status` (`yes` = some clause `state_at_cutoff: operative` with a current predicate checked through the cutoff) |
| Formal validity | Was the order unrevoked on the books? | `formal_disposition` (v2), else the v1 `whole_order_end` when its mechanism is a formal revocation |
| First-end certainty | Is the first end established, and how precisely? | v2 `date_kind`: `exact`, `interval`, or `not_later_than` (cause unresolved) |

## What `whole_order_end` is

**`whole_order_end` is the latest clause first end.** The v1 gate requires its date to equal the latest first-end
date in the complete clause inventory (`claim_gate.py`, `whole_order_end_not_last_clause_end`). It is the day the
last surviving clause stopped operating. It is not the first moment any part of the order lost force, and it is
not the date of a formal revocation that came later. It assumes cessation is monotone: no clause revived after
another ended. A history with revival needs the separate state-history treatment in the contract proposal. In v2,
the whole-order end is `[max(clause earliest), max(clause latest)]`, and it is bounded if any clause end is bounded.

## Reporting rules

1. **Population.** The working census denominator is 14,972 identities. The numbered series and the catalogued
   unnumbered series get separate denominators everywhere a denominator is printed (task E4). Census-candidate
   orders outside the census are never counted.
2. **The estimate.**
   - Population share: from the Stage 15 stratified blind sample (`STRATIFIED_POPULATION_SAMPLE_120_BLIND.csv`, a
     protected stratum under R4), weighted by its design weights, with a confidence interval, and with nonresponse
     (source-blocked orders) reported by stratum. Nonresponse is not imputed as `no`.
   - The ready set (orders whose dossiers are ready for human review) is a convenience population, not a sample.
     It is reported as a count, never as the population share.
3. **The three statuses.**
   - `yes`: operative at the cutoff.
   - `no`: no operative clause at the cutoff.
   - `indeterminate`: stated, never folded into either.

   A v2 `not_later_than` claim is a `no` with first end unresolved. It counts in the operative-force column, since
   the order was formally disposed of no later than the bound, but not as a ready whole-lifecycle dossier.
4. **Single-date claims.** Most NO claims end every clause on one day. Today 1,262 of the 1,363 ready NO claims do,
   and 960 have a single clause. Report them as they are: one first-end date for the whole order. Do not present
   the common date as evidence that the clauses ended independently on the same day. When the shared date is a
   formal revocation that the claim's own text marks as a later cleanup of a spent order, the 10-21 reading, the
   claim is re-tagged under R3 (C3 PR: 184 claims). The single date then becomes a `not_later_than` bound and the
   formal disposition, and is no longer a first end. The remaining 101 ready NO claims, whose clauses end on
   different dates, report the whole-order end as the latest clause end.
5. **Tiers stay separate.** Every published figure is labelled with its tier: machine status lead, provisional
   ledger status, AI-reviewed claim, ready dossier, or human-certified dossier. Human-certified whole-lifecycle
   dossiers: 0.

## Numbers on main today (2026-11-06, tracker data at `454a70716`, code at `125723fc3`)

- Census: 14,972 identities. Provisional ledger: 3,886 `no`, 405 `yes`, 10,681 undecided.
- Ready for human review: 1,384 (1,363 NO, 21 YES). With the C3 re-tag: 1,208.
- Claims: 1,505, all v1. Contested: 0.

The single authoritative generated number is `ready_for_human_review` in
`jobs/readiness-tracker/output/SUMMARY.json`, together with its `generation_id` (A3).
