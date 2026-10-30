# Independent engineering contract challenge

Frozen input: `f9c6d806ad059dcad7875ab3708715f20ea386df`.
Reviewer: separate OpenAI-family context (platform self-identification GPT-6/Codex; exact serving model and actual tokens unavailable). This is engineering review, not different-family review, legal adjudication, or scientific certification. No fix, production record, Git index, or immutable codebook was changed by this reviewer.

## Existing rules versus desired improvements

1. **Confirmed existing-contract violation: status exhaustion.** `research/readiness/README.md` enumerates seven exhaustible steps and excludes `provisional_status`; tracker README requires an adopted provisional YES/NO. `load_exhausted` uses all eight `STEP_NAMES`. In the synthetic native tracker fixture, a valid exact checked claim for EO:4 with no adopted status and a `provisional_status` exhaustion record produces `ready_for_human_review=yes`, `ready_tier=complete_claim`, empty status, and no input problem. Smallest repair: a distinct exhaustible-step allowlist excluding provisional status. A regression must require status remains open and readiness false even with the record.
2. **Confirmed existing-contract violation: undisclosed exhausted gap.** Readiness README requires the gap in the claim's `unresolved_material_gaps`. Both a missing savings object with `unresolved_material_gaps=[]` and no claim at all can become `machine_exhausted`. Smallest repair: exhaustion-used promotion needs an actual claim with nonempty well-formed gap disclosure; preserve ordinary complete-claim readiness. An exact formal linkage between free-text gap and step does not currently exist and cannot honestly be proved by text matching.
3. **Confirmed malformed witness acceptance, bounded repair warranted.** `searched:[null]` is accepted as route documentation. Reject empty/non-string entries and whitespace-only provenance, while preserving the existing string-list manual-attestation format. A nonempty string can still be false or incomplete; semantic source-ladder thoroughness remains a trusted research judgment. Inventing a new signed/certified exhaustion protocol would be a desired improvement, not merely this parser repair.
4. **Intentional exception, not a regression:** a changed exact claim receives a stale source-hold warning and is not blocked by the prior version's hold. This is explicit in README, code docstring, and `test_exact_claim_source_audit_blocks_only_readiness`. An irrelevant rationale edit can evade the former hold after an exact new mechanical receipt, but forbidding it changes existing policy. Any assurance must disclose this exact-version limitation and may not prove that all historical substantive objections have been resolved.

All four synthetic probes and their native output rows are in `initial-probes.json`. The scratch script uses the existing `test_tracker.TrackerTest` fixture and the actual production tracker/claim gate. These are counterexamples on made-up records, not evidence that any real production count is wrong.

## Trust boundaries for any claimed guarantee

- Exact claim-hash matching means the receipt names the current canonical claim. It does not authenticate who generated the receipt, prove that source bytes are still present, or establish legal correctness.
- The current tracker trusts committed checker step booleans and legacy source/status registries. A mechanically complete row is ready for human review, never human verified or certified.
- Search exhaustion is an exception route to human review with an unresolved gap. It does not establish a lifecycle endpoint or convert unknown-whether into known-within-an-interval. The October 28 evidence ruling retains this distinction.
- Existing stale-hold handling deliberately weakens any proposed monotonic statement across versions. A theorem about the current exact hold can be supported; a theorem that an unresolved substantive audit follows all descendants cannot describe current behavior.
- The first probe's tier stays `complete_claim` despite status being exhausted. A proof that only `machine_exhausted` rows consume exhaustion would therefore be unsound on the baseline.

## Smallest repair acceptance criteria

Preserve the existing positive exhaustion test, exact stale-hold behavior, exact active-hold precedence, current claim-hash mismatch refusal, working-text policy failures, and source grades. Add regression coverage for forbidden status exhaustion, absent claim, undisclosed/invalid gap, and empty/null search entries. Do not tighten manual search prose into a new evidence standard by stealth. Native checker→tracker validation must be scoped and use retained outputs without publishing production claims or totals.

## Process and costs

Read AGENTS, HANDOFF README/Kean, latest visible entries, relevant owner evidence and delegation rulings. Kean searches for combined terms, `exhaustion`, and `source audit` completed; search warned that 803 tracked reports were not checked out. No sparse state was changed. Independent review setup began before the first recorded clock: its elapsed time is unavailable and is not retroactively allocated. Probe start and measured execution interval are retained in `initial-probes.json`; actual tokens/cash/active labor are unavailable. Coordinator must integrate this result into Kean and HANDOFF because shared-register writes are outside this reviewer's assigned file ownership.

## Coordinator guard proposal, preimplementation review

The proposed seven-step allowlist, string validation, explicit nonqualifying-ladder markers, and nonempty claim gap disclosure fit the existing contract. The tracked canonical `EXHAUSTED.jsonl` is empty on the frozen baseline, so no existing exhaustion row migration is known to be required. `claim_gate` uses the same `unresolved_material_gaps` error for malformed and properly nonempty values; the tracker must therefore validate a nonempty list of nonblank strings rather than testing truthiness. Source-ladder proposal rows do not include `result`/`outcome`, so those fields cannot become mandatory. Reject explicit `retry_later`/`no_route` fields if present and the explicit `WEAK` marker; do not infer disqualification merely from prose recounting an earlier failed route. Any row that actually consumes exhaustion should be labeled `machine_exhausted`, retaining the distinction even if surrounding completeness logic later changes.
