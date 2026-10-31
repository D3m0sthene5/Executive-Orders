# R1 result: selective materialization for the production Valla runner

PR112 extends the existing materializer and exact-version certificates to one
audited production job: `valla`. The same-pin native comparison passed without
projecting away missing bodies. Full and selective executions produced identical
INDEX, SUMMARY, provenance, freshness receipt and runner-log bytes. Their421
relevant input versions and prior output generation also matched exactly.

Source: `9fc12f9e37780ae5831fce6d698139920bf51589`.
Read-only proof: run41168642078, job124441594349, artifact13030233064.
Both arms loaded all97 tracked packages, with zero unmaterialized packages.
No job implementation, shared library, canonical claim, status, source grade,
readiness result or human certification was changed by this repair.

## Measured production comparison

| Measurement | Historical full availability | Selective Valla |
|---|---:|---:|
| Complete materialized worktree paths | 93,673 | 8,238 |
| Complete materialized worktree bytes | 7,938,002,512 | 263,913,198 |
| Startup, including matched input verification | 37.559 s | 11.732 s |
| Native transactional runner execution | 8.688 s | 8.962 s |
| Instrumented materializer/freshness helper Git calls during startup | 22 | 61 |
| Those calls' stdout bytes | 11,501,356 | 25,393,169 |
| Those calls' elapsed time | 1.075 s | 3.090 s |
| Relevant input versions | 421 | 421 |
| Remote transfer within measured arms | 0 | 0 |

The worktree reduction is96.68%, and observed startup is25.827s shorter.
Native runtime did not improve. Closing/verifying the read contract added
helper metadata work; those extra costs are included in startup. Instrumented
call counters cover Python materializer/freshness helpers, including provider
blob reads, rather than every internal Git operation performed by checkout.

The selective **declared closure** was426 paths/56,372,491 bytes, including the
prior Valla generation. This is smaller than its complete263,913,198-byte
worktree because the existing workflow bootstrap deliberately retains all job
code/data. Neither quantity is measured avoidable network transfer. The earlier
95,025-path/8.31GB integration measurement concerns a different selection/pin;
it is not used as this comparison's baseline.

Both arms used the same source commit, absolute worktree path, prior outputs,
fully warmed local Git object pool and empty job/download caches. There was no
configured remote in either arm. OS page-cache state was uncontrolled; this is
one matched host comparison, not a repeatability distribution or a cold-network
experiment. Background host-interface activity was191,178/101,584 bytes and is
not attributed to the job.

Constructing the complete old-availability object pool cost372.020s and observed
5,076,038,384 host-interface sent+received bytes. Exact Git pack/remote transfer
bytes are unmeasured. Total script time including construction, both arms,
native execution, scans, copies, equality checks and cleanup was453.990s.
Actions checkout/setup,25 focused tests (8.599s), upload and independent review
are additional costs, visible in retained logs and COSTS.json. No cold transfer,
model-token, overall research-labor or campaign saving is claimed.

The ordinary runner also succeeded on source9fc12f9 with `example-hello valla`:
no fallback,448 declared paths/61,468,881 bytes. This separate real run proves
ordinary integration; its different selection is not the matched baseline.

## Safety and verification

INPUT_AUDIT.md records every runtime read family. Fresh independent static and
engineering workers examined branches beyond the historical PR104 trace. The
25 new native/adversarial tests,37 existing freshness tests,6 materializer tests
and36 Valla tests passed. The focused suite is wired into the ordinary Linux and
Windows road entrypoint. Final CI outcomes are in VALIDATION.json.

Independent review rejected concrete intermediate implementations: symlinks
before parent traversal, symlinked provider directories/protocols, ignored package
sheets and protocols, unresolved aliases to ignored sources, and late ignored
claim/provider arrival. Each correction is retained with exact hashes and native
regressions in review/REVIEW.md. The approved implementation hashes did not change
after the successful production proof.

Unknown/changed code and unsupported metadata retain full repository
materialization. Unresolved dynamic scope cannot pass publication freshness.
Direct ignored bytes are captured but still rejected against a branch tree
that does not retain them. Existing same-run generation handling and failed-run
prior-success preservation are exercised, rather than replaced or bypassed.

A later tiny coordinator-only harness rehearsal omitted fetch_pool from its
fixture while copying cache_cap, so the cache-pruning step failed after native
Valla succeeded. Its failure is retained under validation/harness-fixture and
qualified as incomplete fixture setup; it is not the successful production
comparison and supplies no performance claim. The production harness used the
complete shared-library closure and both actual runners succeeded.

## Retained artifacts and integration

validation/production/ARTIFACT_MANIFEST.json pins all13 original archive members
and the ZIP SHA256. Exact small receipts/logs/metadata are losslessly retained in
validation/PRODUCTION_RECEIPTS.tar.gz. The two13,962,185-byte INDEX bodies are
byte-identical to the already-retained baseline Git blob
`96b0d07d201b22960cdfcc5b553295cce41a5f72`, path
`jobs/valla/output/INDEX.json` at base88cef025; no duplicate corpus body is added.
Standalone COMPARISON.json and the complete production log remain readable.

INTEGRATION.md gives the exact implementation closure, certificate regeneration,
tests, R2–R4 request boundaries and remaining fallback reasons. Root must test
the combined branches and re-establish any certificate whose implementation
closure changed. Leave PR112 unmerged; this work authorizes no main update,
scientific adoption or broad compiler rebuild.
