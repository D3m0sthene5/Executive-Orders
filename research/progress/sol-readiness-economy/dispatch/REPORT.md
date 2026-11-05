# Dispatch and late-selected source guard

Owned implementation: `jobs/claim-kit/dispatch.py`; new direct regressions:
`jobs/claim-kit/test_readiness_economy_dispatch.py`. No B-owned module or shared
CLI was changed. `PINS.json` binds this worker's final code and tests.

The ordinary dispatch consumer now emits one source-ladder Wanted proposal per
missing original-byte identity, retaining each affected order, evidence ID,
mandatory/optional role, original locator, expected hash and actual checker
failure. Proposals are never submitted. It exposes the exact existing research
tasks, dossier missing questions and qualified source-blocked checkpoints
separately from the checked original/inventory contract. An explicit wrong-order
`Instrument:` marker now prevents dispatch. Heuristic heading mismatches,
current-law gaps and YES status alone do not make a legal prerequisite rule.

`check_selected(repo, packet, claims)` rechecks immutable packet/runtime, exact
claim-dossier/source-reference bindings, selected quote spans and actual offline
custody. It includes newly selected source notes and all ordinary checker source
fields. It binds exact canonical claim hashes and does not accept a prior receipt
as permission. It accepts partial research because it does not run a whole-case
scientific gate or decide legal applicability. The ordinary full checker and
independent review remain necessary.

Runnable existing-input route before review:

```sh
python3 -B jobs/claim-kit/dispatch.py --repo . PACKET \
  --claims PACKET/applied-vN/CLAIMS.proposed.jsonl \
  --write PACKET/applied-vN/SELECTED_SOURCE_CHECK.json
```

Exit 0 means the selected-source diagnostic found no mechanical source problem;
1 reports source/binding blocks; 2 refuses invalid/stale inputs. The receipt must
be a new file inside the packet. This standalone route requires no shared CLI
edit. `INTEGRATION_GLUE.patch` is an exact, unapplied optional hook for `kit.py
apply`: preserve candidates, produce a full selected-source receipt, and return
nonzero before assigning a reviewer when sources fail. Reconcile it with Session
B before adoption. Do not add this test to blind reviewer prompts by default.

Validation: 11 existing dispatch tests and 9 new native-packet regressions pass.
The new tests cover one shared optional source task across two orders, selection
turning that gap into a hold, exact byte retention reopening the same claims,
a ready comparator, false-hold protection for YES without a current-law witness,
an explicit wrong-instrument marker, wrong-order source substitution, changed
claim fingerprints, changed raw bytes, stale text/runtime refusal, offline
read-only checks and immutable CLI receipts. These are engineering fixtures,
not a retained Tribonian accuracy/savings estimate.

Existing prior-research checkpoints retain requests and source-version pins but
do not supply a generic reviewed applicability/mandatory-prerequisite schema.
The implementation carries those attributed prior blocks without inferring a
new scientific requirement from reviewer prose or the absence of a machine match.

Costs: the two focused unittest suites reported 1.820 s (11 tests) and 1.782 s
(first 8 new tests); the final 9-test run reported 1.100 s.
These are subprocess timings only. Preparation, coordination, model usage,
token classes, cash, peak memory and active labor are unknown. This worker used
an inherited OpenAI context, with exact model/tier unavailable. No different-family
or human scientific certification and no model-token saving is claimed.
