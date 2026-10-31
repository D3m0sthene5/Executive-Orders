# Independent engineering review: R1 Valla materialization

## Verdict and exact scope

**Uphold the final implementation and read-only comparison harness at the exact hashes below.** No unresolved correctness finding remains from this bounded review. This is engineering review, not scientific adoption, human certification, a successful production comparison, or evidence of measured campaign savings.

Final implementation source commit: `8ecda574226159457a5aab22c5728caf5ec34798`. The certificate is a separately generated file and must be committed with these exact implementation bytes before a production proof can establish selective operation. Any implementation or harness byte change requires renewed review. Later commits adding only this review, tests, receipts or outputs do not change the reviewed implementation hashes.

| File | SHA256 |
|---|---|
| `.github/scripts/materialize_job_inputs.py` | `81d83bb72d7df96a160127e503042bade9d2e5c2382d830cefa1475c6edc5a88` |
| `.github/scripts/result_freshness.py` | `2afe85a3a9aa01bca39c7e1cb1968561375ae428ed432355ffdd326b20bddf75` |
| `.github/scripts/materialization_certificates.json` | `a460793e73342fba683d7c2a543dc25fe4e1f1496c32e78e7b551918afafeed6` |
| `jobs/valla/inputs.txt` | `aa6c52fb3594094cec003b946b48e2ef32605513b32c537bac80b714e1f4dc17` |
| `jobs/valla/needs.txt` | `a311ef1e7a7dca865034936e09924b37cff6905cf7c2ebef6a117b47f56daa76` |
| `jobs/valla/triggers.txt` | `aa6c52fb3594094cec003b946b48e2ef32605513b32c537bac80b714e1f4dc17` |
| `jobs/valla/valla.py` | `14a371edf8ee9242a32398e396f0046d074df6d661cd458de541baadb26872f6` |
| `jobs/valla/job.py` | `feedae908579f1698e510aef3c75b6fdc07e436b4c61d8439bd3096c13455fc4` |
| `research/progress/r1-materializer-followthrough/run_production_comparison.py` | `3f2e432f0c7ca877ae28a5150cf87638ad23f9526ad4ab34169310a4a8c7e004` |
| `.github/workflows/r1-materializer-proof.yml` | `ea75a85b94e31e08d82368bb742f5ab8ea3925612196d0dc6b3390a35f055fa1` |
| `.github/scripts/test_valla_materialization.py` tested working bytes | `6aede36c61ea182110924bdb228a0eb3fac2e0d8925ef371877c539c6312e324` |

The actual certificate signature is `07fef593187848774aef7e91420a9df75fc2586717a0bebddc58c05c33f7de77`. On the final production checkout, independent inspection returned `implementation_certified: true`, `dynamic_complete: true`, 309 direct referenced files and no compatibility fallback job.

## Retained defect history

The first review rejected source commit `d49cddc0c7029c059b6efe716666339c5aa1ab7a`, with materializer SHA256 `27aafd304a2e92fbe90b9e49a2fce57fd4f56ca3c31dd4121c808326c193e4aa` and freshness SHA256 `40fb6aabd4581cbba736cb634e771132880f2f0962e23edf238ca118e43a8b69`. Later source `56bad91fc5b8c8828237682c8fb47245dc3e8476`, freshness SHA256 `712a4d79a839afa36f3ab2c105f106205eac1cabfcf7f270457b653b8c5ccb20`, still failed the ignored-input cases. The following failures were proved in disposable Git fixtures and reported before their corrections:

1. **Symlink before parent traversal resolved differently.** With `link -> held/subdir`, Valla read `held/source.txt` for `link/../source.txt`; the resolver selected `source.txt` and reported a complete closure. Correction: parent-traversal references decline narrowing rather than normalizing away traversal semantics.
2. **Provider directory symlinks escaped detection.** A symlinked `method_reviews` directory exposed a JSONL provider to Valla but selected neither the tracked alias nor target for sparse availability. Correction: inspect every provider and all live/tracked ancestors.
3. **Static reads could alias omitted targets.** A symlinked `AGENT_PROTOCOL.md` produced a real protocol hash in a full checkout and `null` after its omitted target disappeared. Correction: inspect all selected read families, including fixed paths, claims and package members, for live and tracked symlinks; decline narrowing on aliases.
4. **Broad fallback did not version ignored symlink targets.** A valid native quotation component read an ignored body through a tracked alias. Changing that body invalidated the native component while freshness remained `fresh`. Correction: unresolved dynamic closures may restore broad availability and run, but their captured results are refused for publication.
5. **Ignored static reads escaped ordinary Git inventory.** An ignored `decisions.csv` beside tracked `RATIONALES.json` changed native shared-rationale references without changing captured inputs. Fixed protocols had the same gap. Correction: enumerate fixed protocol reads, all live claim/provider JSONL files, and every tracked package's three members, including absent siblings; hash these direct reads independently of Git ignore rules. Independent final probes confirmed present ignored package sheets and protocols are captured and rejected when absent from the remote tree.
6. **Late ignored record arrivals escaped the stored inventory.** Creating an ignored canonical claim after capture changed native active claims from one to two while freshness returned `fresh`. Correction: re-discover current direct reads at verification and compare the union of current and captured inventories. Independent final claim and provider probes both reject these additions.
7. **Fallback reporting hid changed working implementations.** Broad restoration could occur with an empty compatibility-fallback receipt. Correction: report the uncertified working implementation explicitly.
8. **Comparison baseline included receipt-only work.** The broad arm timed a new `input_closure` call used only to populate a receipt. Correction: remove that call; snapshot startup metadata before runner and guard execution. A temporary mixed `changed_paths` report schema also broke a regression consumer; the final schema consistently uses path dictionaries.

## Validation and limits

Read the runner `valla.job -> valla.build` branches, dependency declarations, materializer/freshness implementation, applicable AGENTS/HANDOFF/Kean material, and retained PR104 closure/handoff qualifications. The review exercised dynamic provider additions, edits and deletions; missing references; ignored inputs; tracked/live symlink ancestors; fixed protocol and package reads; and late record discovery in bounded temporary repositories. The native comparison tests preserve valid and invalid method/component outcomes rather than substituting projected body metadata.

The final 25-test Valla materialization suite passed independently. It includes native full-versus-selected output equality, sparse provider recovery, unknown/changed implementation fallback, package triples, same-run predecessor output handling, failed-run prior-output preservation, and the corrected ignored-input cases. The original 37 freshness tests and six materializer tests also completed successfully: 68 tests passed across the three suites. No partial test output is treated as a completed pass.

A separate positive control confirmed a direct record reference to an ignored body is captured and then rejected against a Git tree lacking that body. That rejection is required. No absent source body was projected into publishability, and no freshness mismatch was suppressed to manufacture a successful production comparison.

The read-only proof harness uses one pinned commit and the same absolute temporary worktree path for both arms, shared prewarmed Git objects, empty per-arm job caches, the same prior generation, actual native runner execution, actual freshness checks and exact output/input-map equality. It has no result publisher and the workflow grants only read access. Construction time and host-interface network deltas are separately disclosed. The arm transfer claim is limited to a local object pool with no remote; OS page-cache state remains uncontrolled. These conditions do not establish cold-network transfer savings or campaign-level savings. A production run and its retained actual outcomes remain necessary; this reviewer did not run the production comparison locally.

Review independence: separate OpenAI reviewer context, inherited model identifier and token/cash telemetry not exposed. No different-family or human review is claimed. Implementation and test corrections were made by the coordinator/worker; this reviewer changed only this review file. No scientific source, canonical claim, legal status or accepted finding was modified or adopted.
