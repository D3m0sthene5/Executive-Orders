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

## Post-review test wiring addendum

**Uphold the test-only changes at the following exact working hashes.** The coordinator identified published source `9fc12f9e37780ae5831fce6d698139920bf51589`; this addendum pins the inspected local bytes independently of that reported remote publication.

| File | SHA256 |
|---|---|
| `.github/scripts/test_roads.py` | `1ca5fea01727c053c118d0d0cfa0787a9f6a109cfd504d05d01c4e35fbd08c9f` |
| `.github/scripts/test_valla_materialization.py` | `1f84fd151072d38b9d728fd8df1d7ca2ae58296f7e5647046fe05fdf75bcd95a` |

Inspected the complete working diffs: Road now invokes the Valla materialization suite with the same Python interpreter, repository cwd, `check=True` and disabled bytecode writes used by its existing focused script suites. The disposable Git fixture disables automatic CRLF conversion and explicitly enables real symlink semantics before its first commit; this prevents fixture transformations from replacing the byte and alias behavior under test. The remaining test edits align changed-path assertions with the final report dictionary schema. No assertion about native Valla output equality, rejection, source validity or prior-output preservation was weakened.

Reran the focused suite independently on the current environment: **25 tests passed in 8.276 seconds**. This is a local Linux result; this addendum does not infer a Windows CI pass. The 37-test freshness suite was not repeated for these test-only changes. Rehashed the materializer, freshness implementation, certificate, production harness and proof workflow: every hash remains identical to the reviewed table above. No new implementation finding arose, and no production comparison outcome or savings claim is adopted here.

## Production receipt addendum

**Uphold the matched production result for the measured warm local-object conditions.** Independently inspected the downloaded artifact for run `41168642078`, source `9fc12f9e37780ae5831fce6d698139920bf51589`; no rerun or result publication was performed. This addendum supersedes the earlier statement that production results were not yet inspected, while preserving its historical scope.

Recomputed the downloaded ZIP SHA256, compared all 13 ZIP members against the unpacked bytes, verified all 13 production-manifest member hashes and sizes, and verified all 11 retained compressed-receipt members against their retained files. Actual full and selective `INDEX.json`, `SUMMARY.json`, `RUNNER_INPUTS.json`, `FRESHNESS.json` and `runner.log` are byte-identical between arms. Both freshness receipts say `fresh`, contain no problems, and identify the exact production source commit. Both captured scopes are implementation-certified and dynamically complete, with 421 identical input entries and input digest `2ddbc85bdfa55cae68be334cd7f6044c2a99aaa3ee29603c394e217a242b0ef9`; neither contains a broad `*` fallback pattern. The selective checkout receipt records no compatibility fallback.

Both native indexes report 97 tracked **packages**, zero unmaterialized packages, 612 active claims, 783 shared rationale references, zero valid components, zero legal promotions and zero model calls. The package count is not a source count or scientific review count. Independently running `git hash-object` over the actual artifact INDEX yields `96b0d07d201b22960cdfcc5b553295cce41a5f72`, exactly the object ID named by `88cef0253ed735b2a6e612770f25f9148641ce93:jobs/valla/output/INDEX.json`. This verifies the retained baseline content address; the baseline body was not separately fetched into this local sparse checkout. Equality is based on actual native artifact bytes, with no body projection.

| Receipt or actual output | SHA256 |
|---|---|
| Downloaded production ZIP | `63526b20feb943086371607103432e3511d71e928c1bb9d3c3f98e45ed3bad9f` |
| `COMPARISON.json` | `0971df6a8b7c65381552136ac6a53fd9581c5f139bdc75d8a6444b140c6c9af6` |
| Both actual `INDEX.json` | `2a91d3f14eb3681ca8058fd1cdc2cdfd60d82c17ddfed8102ef546fb1b15f32d` |
| Both `SUMMARY.json` | `196c539ba59a3c4e0ab2cf6fc9b70bdabe80fa3057bce3bc2ba9ac5ae5f80f27` |
| Both `RUNNER_INPUTS.json` | `824256a4268db96dddf28c5cc77afbc075f1c7366b0c17b2e4dce7404be9027b` |
| Both `FRESHNESS.json` | `5c81f083153c1050e0b9108531af2c8f8018d0f7bf3fd211dc2fbc7929d9e805` |
| Both `runner.log` | `4d357d29f524bb917f298cecc82cf9b76908be3410d00689475497515a11dd34` |
| Full `METADATA.json` | `c9ab4151c12150730aac886df4e35273dad6cd1e4d8429b0b3f3fdce5ef8a25e` |
| Selective `METADATA.json` | `950be03e11c36b6c00fd5d446e9845f3766abb6d1d04ab7dac7f9c34808e6c13` |
| Retained `PRODUCTION_RECEIPTS.tar.gz` | `a4cada72aad85018448ff67c29be8d827dbc2e5c6d6bb2ad445e9e7890a35c6d` |
| Retained `production/ARTIFACT_MANIFEST.json` | `61afdd372156bf460d22846d44801a69bff9d5c4b3f87686c3dcf5f5f4e4a2ac` |

The two large INDEX bodies are represented in retained repository evidence by their exact pre-existing Git blob and manifest hashes; the downloaded ZIP contains both actual bodies. The retained compressed receipt archive does not pretend to contain those two omitted duplicate bodies.

| Measured quantity | Historical broad arm | Selective arm |
|---|---:|---:|
| Entire materialized checkout paths | 93,673 | 8,238 |
| Entire materialized checkout bytes | 7,938,002,512 | 263,913,198 |
| Startup seconds | 37.559355 | 11.732158 |
| Native runner seconds | 8.688073 | 8.962367 |
| Startup metadata calls | 22 | 61 |
| Startup metadata stdout bytes | 11,501,356 | 25,393,169 |
| Startup metadata seconds | 1.075393 | 3.089980 |

The selective declared closure is 426 paths / 56,372,491 bytes; this is distinct from its entire materialized checkout footprint, which includes bootstrap availability. Recomputed metadata sums from the first 22 and 61 records reproduce every reported startup count, byte total and duration. The full metadata files contain 44 and 83 calls respectively, with 22 later verification calls per arm; their totals must not be relabeled as startup costs. Selective startup is lower in this observation, while native execution is slightly slower and metadata overhead is higher.

Construction consumed 372.020461 seconds and the total run including construction and verification consumed 453.989959 seconds. The construction host-interface sent-plus-received delta is 5,076,038,384 bytes. Arm host-interface deltas are 191,178 and 101,584 bytes, despite both arm receipts reporting zero remote Git transfer because neither arm has a configured remote and both reuse prewarmed local objects. Host-interface deltas include unrelated traffic and are not pack bytes or avoided transfer. This is one matched warm-object-pool observation with uncontrolled OS page-cache state. It establishes the recorded checkout-footprint and startup differences under those conditions; it does not establish a cold-network saving, general native-runtime improvement, amortization, campaign savings or scientific progress.

The separately retained small-fixture harness failure is also preserved: `validation/harness-fixture/full/runner.log` SHA256 `91d66c7c20a766f224d816ed884ba1d43ee68c59250d3b9bf0caaf84b5c191d3`, and `validation/harness-fixture/harness.log` SHA256 `d45c34bb882fe8141b09fb9303a89545a4c343c019a5d668c43d6af2d1fca735`. Inspection shows its native Valla build completed, then its copied `cache_cap.py` failed importing missing `fetch_pool`. That fixture omitted a shared-library dependency. It is a retained fixture-setup failure, not a failure of the production comparison whose complete source/library inputs and successful native/freshness receipts were independently inspected above.
