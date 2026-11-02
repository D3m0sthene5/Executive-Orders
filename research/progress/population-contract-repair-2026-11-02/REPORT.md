# Restore the accepted-population contract after PR119

The production refresh [41400645645](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/41400645645)
failed in `test_historical_fixture_and_current_accepted_population` at 07:22:53 UTC
on November 2. Its input ledger held 4,291 statuses, while the independent contract
still authorized 3,403. Claim-kit failed before rebuilding; its downstream jobs
were correctly blocked. Successful upstream outputs were still published in
`f07b023133640f288fd44c10c5176888c49f23e2`.

[PR119](https://github.com/D3m0sthene5/Executive-Orders/pull/119) had already been
owner-merged as `c469d94d796a65a2779ef857156903774b0fbda9` on October 31 at
22:01:47 UTC. It adopted exactly 174 first-wave and 714 second-wave individually
reviewed provisional NO statuses. No lot passed sampled adoption. The 59
coordinator holds and voided controls EO370/3031 are outside the adopted rows.

The repair adds those two existing adoption records to
`jobs/claim-kit/population_contract.json`, pinning the exact merged row files,
ruling, rule cards, review verification, acceptance records, holds and rereview.
The historical 3,359-row prefix, census identities, two older adoption entries,
validation implementation and authoritative status ledger are unchanged. This
is engineering reconciliation of an existing adoption, not a new adoption or a
change in evidentiary requirements. Future unaccepted rows must still fail.

`python3 research/progress/population-contract-repair-2026-11-02/reconcile.py`
reproduces the original failure against the old contract, checks every new pin
against PR119's merge bytes, confirms the adopted IDs were individually upheld
and excluded from holds, and runs the unchanged native validator. Its retained
output is `RECONCILIATION.json`: 14,972 census identities, 4,291 decided orders,
3,359 historical rows plus 932 authorized additions (44 older + 888 Jacquard).

Validation: all 18 population refusal/coverage tests pass. The complete existing
claim-kit suite runs separately with its committed metadata test enabled; its
result and independent engineering review are retained alongside this report.
No legal claims, source grades, review verdicts, census rows or human
certifications are changed. A local contract pass does not establish that a
full native compiler refresh has completed.

The owner authorized continuation of the prior dashboard job-tier priorities
and qualifying merges, and confirmed the old run was stopped on November 2.
This scoped authorization does not answer the older standing-future-merges
question. Root coordinates integration; independent engineering review uses a
separate gpt-6.1-sol context. Full token, cache, cash and active labor totals are
unavailable; no savings or readiness gain is claimed for this contract repair.
