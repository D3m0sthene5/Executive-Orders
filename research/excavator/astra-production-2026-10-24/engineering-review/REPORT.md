# Independent engineering review — completion glue

Approved the exact completion engine SHA256
`0d2bb39e961548c3936e38501751dcf7374eb2392b4343f8773fa4a24a8aa756`
on 2026-10-24 at 16:51 UTC. No remaining engineering blocker was found in this
scope. This is a separate same-family engineering context, not legal review,
cross-family review, or human certification. All reviewed code/document hashes
and known telemetry are in `REVIEW.json`.

The final executable replay passed **13/13 independent probes** using the real
Stage 19 gate, strict assembler checks, claim-checker subprocess, and tracker
build/summarise APIs. The source corpus is deliberately synthetic. The two
successful paths preserve CRLF producer bytes and exclusive publication:
own-agent claims and isolated replacement proposals. Replacement proposals
retain owner-acceptance-required and zero canonical claims-published credit.
Other-owner filing and an existing destination fail without clobbering bytes.

The adversarial paths verify missing partial-review gaps, actual checker gate
errors differing from reviewed errors, partial machine-exhausted readiness,
changed raw custody after checking, newly appearing canonical/frozen owners,
empty controls, family-name whitespace, and unsafe seed-container selectors.
Full receipts are in `approved-probes/`; rerun `review_probes.py NEW-DIRECTORY`
from the repository root. Every probe uses a temporary repository and never
changes the real canonical claim files or tracker outputs.

The completion and existing batch unit suites additionally passed 33 tests in
1.150 seconds at the preceding `656354c6` engine pin. The final difference is
the optional pin of the existing frozen-ownership manifest; the final actual
API replay explicitly exercised that addition. The final 13-probe replay took
1.940695246 machine seconds. Whole-review labor, actual/cached model tokens,
and cash are unknown; they remain null in the receipt.

Resolved findings:

- Partial scope originally defaulted absent `expected_gate_errors` to an empty
  list. It now requires an explicit nonempty exact list and refuses complete or
  machine-exhausted readiness without whole-case review.
- A full actual-consumer probe showed a partial claim publishing despite an
  unreviewed `whole_order_status_mismatch` from the actual checker. The final
  engine compares the checker's complete gate errors to the reviewed list.
  `probe-run3/` preserves the failing reproduction; later runs preserve refusal.
- Freshness now covers referenced raw custody, source manifests, direct policy
  code, canonical file membership, holds, and frozen upstream ownership. Raw
  drift and concurrent ownership appearances block filing.
- Mandatory recorded controls, normalized family comparisons, a standalone
  metadata-only seed receipt, explicit packet filename pinning, and a coherent
  checker receipt union close the reviewed control/provenance gaps.

The first probe run intentionally remains as failure accounting: its tiny
fixture omitted signing-date data, so the real checker returned
`pass_with_unverified` and completion refused it. `probe-run2/` adds that missing
synthetic evidence. These are engineering-fixture iterations, not new historical
research or readiness gains. Early fixture artifacts contain artificial EO:1
plant data; no actual production planted claim or private mutation key was read
or saved by this review.

The helper checks explicit review attestations; it cannot establish a model's
actual identity, separate context, semantic control catch, or legal conclusion.
The coordinator still supplies those independently recorded facts and an
authorized publication destination. Exact final after-reveal claim hashes,
raw producer lines, receipt versions, held exclusions, and actual consumer
results are mechanically enforced. The separate pending resume timestamp
normalization change is outside this approval.
