# Integration contract

Adopt only after both sessions have finished. No merge, auto-merge, deployment,
canonical source registration, claim/status publication or scientific adoption
was authorized here.

## Owned changes and dependencies

Implementation: `jobs/claim-kit/dispatch.py`, `current_evidence.py`,
`source_supplement.py`; two new adjacent `test_readiness_economy*.py` files.
No implementation outside the listed ownership was changed. Existing batch,
assembler, completion, checker, caches, runner and shared CLI remain untouched.
Namespaced Kean finding/register and the generated brief are coordination changes.
Union `KEAN_FINDINGS.jsonl` with B's entries, then regenerate the brief once.

`dispatch/INTEGRATION_GLUE.patch` is an exact unapplied `kit.py apply` hook. It
writes a selected-source receipt after native assembly and returns failure before
review assignment when the diagnostic refuses. Preserve proposed rows and normal
apply/check/complete behavior; reconcile with B's execution changes. It passes
`git apply --check` on this baseline. The maintained standalone route is usable
without glue:

```sh
CLAIM_KIT_CACHE_DIR=/tmp/eo-session-a-cache python3 -B jobs/claim-kit/dispatch.py \
  --repo . PACKET --claims PACKET/applied-vN/CLAIMS.proposed.jsonl \
  --write PACKET/applied-vN/SELECTED_SOURCE_CHECK.json
```

Exit 0 is source-diagnostic success only; 1 reports source/binding gaps; 2 refuses
invalid or stale input. Rerun after any change. No historical receipt approves a
new claim/source version. Do not inject these receipts into blind reviewer
prompts by default. The optional hook does not automatically intercept external
model launchers.

## First executable checks

From the repository root:

```sh
python3 research/progress/sol-readiness-economy/validate.py --suite claim-kit --label integrated
python3 research/progress/sol-readiness-economy/validate.py --suite claim-checker --label integrated
python3 research/progress/sol-readiness-economy/review/independent_probes.py
git apply --check research/progress/sol-readiness-economy/dispatch/INTEGRATION_GLUE.patch
```

For exact retained evidence inspection, unpack `RETAINED_EVIDENCE.tar.gz` at the
repository root, checking `ARCHIVE_INDEX.json`. Historical code pins remain
historical. Reproducing the observation requires the materialized paths in
`MATERIALIZED_INPUTS.json`, especially the already-committed EO13286 PDF,
official extraction, four parent dossiers/original texts, source inventories
and current reservations. Do not download or register duplicates blindly.

To observe ordinary consumers on current inputs, materialize those dependencies
and run a fresh bounded source-delivery trial (never a producer wave):

```sh
python3 research/progress/sol-readiness-economy/sources/demo_13286.py --repo . \
  --write research/progress/sol-readiness-economy/sources/native-integrated
```

The helper uses its own temporary cache, checks reservations, validates input
hashes and preserves all scientific gates. Full-repository prior research may
give a different freshness context than the recorded sparse demonstration;
prepare fresh rather than rewriting seals. Its engineering source-only probes
are not submitted claims or reviewed legal conclusions.

## Source requests, code freshness and certificates

`source-first/FETCH_PROPOSALS.jsonl` contains two native-valid EO13224 requests.
`sources/SOURCE_DECLARATIONS.json` is the exact EO13286 multi-target supplement
proposal. No canonical queue, registration or provider inventory was appended.
Before adoption, deduplicate against held witnesses, verify exact original/text
bytes and per-order applicability, and retain replacement/quotation obligations.
No project-wide continuation-chain sufficiency has been decided.

`current_evidence.py` is in existing `inputs.COMPILER_FILES`; its change invalidates
compiler versions. `source_supplement` lineages pin preparation code and require
fresh preparation. `dispatch` returns its own code pins; add any future caller
hook to ordinary runtime provenance where appropriate. Existing `inputs.txt`
already declares checker/provider dependencies. No new provider dependency or
runner narrowing was introduced.

The current materializer has a Valla-only certificate, no claim-kit certificate.
This PR grants neither a new certificate nor a renewed old one. The integrator
must run existing certificate validation against the final A+B tree; if the
audited dependency closure changes, re-establish proof rather than renew hashes.
No `.gitattributes`, declaration or workflow was edited here.

## Publication and remaining checks

Jobs-path pushes can launch the broad compiler. Publish the engineering commit
with `[skip actions]`, then a HANDOFF-only follow-up without that marker to request
existing read-only PR checks. Do not dispatch Run jobs, disable guards or treat a
skipped hosted check as passing. Linux/Windows Road, Kean, publication audit and
Valla statuses should be inspected at the actual final PR head before integration.
Main remains the common baseline unless the final coordinator deliberately
rebases and retests. Scientific adoption retains its existing authority.
