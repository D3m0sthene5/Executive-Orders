# Integration handoff

This is an isolated draft for the final integrator. Do not merge automatically.
Base is `2c85459cf38b08dc1eea6d7c84a74268fa45c28e`. Only checker source parsing
and six new checker regressions are implementation changes. No CLI glue patch
is needed. Session A's dispatch/current-evidence/source-supplement policies and
shared `kit.py` remain untouched.

## First executable next step

On an isolated combined branch, run:

```sh
CLAIM_CHECKER_VERIFY_DOWNLOADS=0 PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s jobs/claim-checker -p 'test_*.py'
python3 -I research/progress/sol-runtime-economy/review/adversarial_probe.py
python3 -I jobs/kean/kean.py check --strict
```

The independent harness reads baseline code from the pinned Git commit. Preserve
access to that commit. Verify the implementation and current engineering seal
against `evidence/PINS.json` before accepting the review. If Session A modifies
this adapter or adds consumed fields, reconcile the projection, repeat the
differential probes and obtain an exact final engineering recheck.

## Reproduction

Start a separate partial clone with `GIT_LFS_SKIP_SMUDGE=1`, no checkout, and the
pinned base. Configure non-cone sparse checkout **before** checkout, using the
patterns in `SPARSE_CHECKOUT.txt`; do not copy the compiled corpus. The materialized
input inventory lists 620 exact tracked files, including the final implementation;
it is a reproduction inventory, not a universal dynamic-read certificate.

Run the bounded checker comparison to a new scratch directory:

```sh
python3 -I research/progress/sol-runtime-economy/native_replay.py --repo . --out /tmp/eo-native-new
python3 -I research/progress/sol-runtime-economy/native_replay.py --repo . --out /tmp/eo-native-cap-new --memory-mb 256
python3 -I research/progress/sol-runtime-economy/checker_probe.py 100000
```

The native comparison uses the ordinary checker main and changes only which
`sources` module is loaded for the baseline arm. It records module hashes,
index calls/time, wall time, peak RSS, read characters and full-file equality.
Every process has empty application caches; OS cache warmth is uncontrolled.
Use separate idle-machine repetitions for a timing claim.

For the actual fresh-packet CLI route, obtain exactly `PACKET.json`,
`decisions.csv`, `clauses.csv`, `RATIONALES.json` from
`research/excavator/claude-tribonian-2026-11-04/o27/packet/` at state commit
`2bc32c6d4ea87abf969c406dd4049dc3dddcc3c7`. Fetching that state branch is read-only;
its packets/reviews remain frozen. The local files' Git blobs were compared to
the state tree; their SHA256 pins are in `evidence/RETAINED_INPUT_PINS.json`.

```sh
python3 -I research/progress/sol-runtime-economy/batch_route.py --repo . --retained /tmp/o27-exact --out /tmp/eo-batch-new
```

That helper extracts two frozen dossiers as evidence, prepares a new packet,
preserves the archived unresolved-row outcome, then rechecks already-filed
exact claims through `kit.py batch-check`. Its explicit
`retained_existing_claim` audit label is mechanical replay provenance, not an
assembly or review attestation. It never completes or publishes claims, and
removes its temporary research folder. The helper needs Python 3.12-compatible
dependencies; this run used Python 3.12.14 and pypdf 6.10.0.

## Pins, declarations and authority

`sources.py` is already loaded by checker Context and completion input pinning.
Completion already pins it as code; dispatch receipts already contain its code
hash. Run fresh dispatch checks after integration; do not alter old receipt
hashes or reuse stale approvals. No new dependency or `needs.txt` pattern is
introduced. This change does not modify claim-kit compiler inputs, packet policy
pins or Valla's certificate roots. No certificate is renewed by this PR.
Native completion under the final combined source remains a later integration
check; no reviewed manifest was reconstructed here.

Union the exact appended records in `KEAN_FINDINGS.jsonl` with Session A's
register, keep both unique handoff files, then regenerate `HANDOFF/KEAN.md`.
Do not choose one generated brief over the other branch's register.

Publication uses `[skip actions]` on the engineering commit: `jobs/**` pushes
can start expensive generated jobs, even on draft branches. Hosted checks on
that commit are skipped/unrun, not passing. Final integration must run the
existing bounded PR checks intentionally, including Windows where available,
without dispatching a global generation. No workflow or trigger was disabled.

## Remaining opportunities

The measured repair reduces transient memory, not provider hashing or duplicate
checker index construction. See the runtime diagnosis and baseline receipts
before pursuing reuse. Any reuse needs exact dependency validation and final
checks; do not replace content checks with mtimes. The 10–30 minute original
report was not reproduced from this bounded snapshot.

`RUNNER_AUDIT.md` retains the fallback problem: compatibility `*` captures
same-run transient files. First establish the exact disposable-cache contract
and test genuine tracked/explicit cache inputs before proposing exclusions.
No `.gitignore`, provider inventory, scientific gate, review count, claim,
canonical readiness output, schedule, main branch or live site was changed.

## Main advanced during publication

Draft PR140 was published at engineering head `d9c183f0ad2326cd400f0782002fcce9b23846f5`. An existing production run then advanced main to `a3bfac64b3e1c43400a8ed8c744419eb17f6e2e6`. A complete local name-only tree comparison found 2,459 changed paths, all under job output directories, with zero overlap with Session B. Matched measurements deliberately retain `2c85459` and its exact source inventory. Preserve the newer generated outputs when integrating and run fresh source/dispatch checks; do not copy the old generation over them. `evidence/MAIN_ADVANCE.json` records this read-only check. No workflow run was present on the published engineering head when inspected.
