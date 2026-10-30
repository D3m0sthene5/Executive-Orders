# Final cross-stream integration — in progress

Baseline main: f9c6d806ad059dcad7875ab3708715f20ea386df. Scoped owner authorization: D-20261029-final-cross-stream-integration. This coordinator owns final integration; original stream owners retain implementation ownership. PR103 notified in comment6511574188.

PR103 source1cdef3d0, PR104 actual frozen source8adc9396cfd6da015757466b95ca6fa8ab1a4b9a and head9fa8432, PR105 source77abf218, and PR106 runtimef750886a / handoff0252e3ca are combined. Original heads remain merge ancestors. Append-only Kean findings were combined with collision checks and the brief regenerated. Generated branch results remain in Git history; the candidate keeps published baseline output bytes pending a compatible refresh. No canonical claim/status/census/grade changed.

## Review and integration corrections

Fresh independent engineering review found five defects, retained in review/engineering-initial.json and its counterexamples:

- Nested Hathi attributes normalized TARGETS.json despite the root exact-byte policy, causing run40956514088 publication refusal at an unchanged head. Preserve the original CRLF blob with the nested -text rule; verify actual clean hashing and checkout under both autocrlf settings.
- Cached row mutation could remove a known-incomplete-text policy hold. Cache schema v2 checks a payload digest and rebuilds on mismatch. This detects accidental corruption; it is not protection against a malicious local writer who rewrites the digest.
- Shared cached indexes missed symlink resolution changes. Revalidate all lexical path resolutions, including normal paths later replaced by symlinks, with directory memoization; retain existence checks.
- Separate-clone publication audit had no ordinary CI consumer. The new read-only workflow runs the native audit on PR heads and main, retaining its JSON result.
- Reordering old canonical lines could change the last-line winner while the audit accepted the line multiset. Preserve the old nonblank sequence as a prefix; reviewed append-only versions remain permitted.

The coordinator added explicit claim-kit cross-job code input fingerprints from PR104 R1-R3/R6. No provider blanket was narrowed and no new selective certificate was granted. Combined Valla CI now runs native lifecycle and custody replays and checks full tracked package materialization.

## Validation and known pending work

Local Road tests passed. Initial claim-kit runs failed only because the sparse checkout omitted claim_gate.py and four contract examples; those failed logs are retained in scratch and prerequisites restored. The next 479-test run passed with five existing corpus opt-in skips. Final cache corrections require a new exact-candidate pass and fresh independent review. Valla36 and checker/materializer focused suites passed. Kean initially exceeded8192bytes by4; the authorization summary was shortened through append-only revisions, preserving the complete ruling, and strict check now passes.

The original PR104 expanded SHA in its comment was incorrect; Git and CI resolve the short pin as recorded above. Retained reviews must be checked against actual objects.

Current verified published tracker generation is run40829686426, commit_run adcf881ef7eb897e6bec8a8bd7717f4eb3629039, finished2026-10-29T07:09:13Z:395 ready. It predates this candidate. No new total is inferred from isolated replay gains.

Pending: exact-candidate CI/review, ordinary retained rehearsal, qualifying merge, coordinated main producer/consumer refresh and receipt compatibility verification. New Valla reasoning, Cruden optimization, shared-research continuation and ProQuest census expansion remain pending until their actual handoffs are observed. Existing merged NRA/Cruden work is baseline, not evidence that those new assignments are complete. No background watcher is active.

## Costs and limits

Mechanical inventory: gpt-6-luna. Cache fix: gpt-6-luna, two implementation iterations (first incomplete witness proposal rejected by coordinator). Fresh engineering review: separate inherited coordinator-model context. Tokens, cash and complete active labor are unavailable. All review, setup failures, corrections and integration belong to cost; no net savings claimed. PR104 historical timings are retained as source-stream measurements and have not yet been remeasured with final corrections. Git shell push lacks credentials; publication uses the connected GitHub API preserving source parents and exact tree bytes.

## Final source review and first remote candidate

Fresh independent final review approved source2fbc45654acedf94ace1c46ace616ecb0b7bee06 with combined/native/production conditions; exact hashes and64 focused tests (63pass,1existing corpus skip) are in review/final-fix-review.json. It also caught and corrected omitted production-package checkout, missing explicit lifecycle-baseline fetch and failure to inspect merge-result changes after parent-only publication audit. Previous review and counterexamples remain retained.

PR104 explicitly superseded its source pin with b1890d7a0cc5329cec387b804a4e88962262b5d0: completion control review scopes now match lifecycle tasks and submitted member scope. Its2new regressions and unchanged genuine rehearsal result were independently examined. Final combined completion suite:40passing. Initial combined candidate b8c40e97 tree exactly matched local25ba05dd; final update adds the reviewed scope/merge-tree corrections and review receipts. Road Linux/Windows, Kean and publication audit passed on that first candidate.

PR105 run40976840282 succeeded and published branch outputs at e87c9ad6. This is an actual branch checker result, not a new canonical tracker generation. Its source is unchanged; combined/main fingerprints still require verification. Runs40979721659 and40979725966 predate the control-scope supersession and are preliminary. Manual workflow controls are unavailable without browser sign-in; no cancellation or dispatch claimed. Automatic runs and bounded exact-ID watcher remain usable.

## Frozen follow-ons and combined consumer evidence

PR108 f3d9fad88e7d0288967b2674d3ef64fba1db3010 and PR109 4d2448360a42dca9c3556d128ad1721d0a4eeb0c are incorporated with original ancestry. Findings were unioned with collision checks; long brief lessons were shortened through append-only revisions while original records remain. Existing checker job now logs attempted artifacts, bytes, selection fingerprint, cursor and deferred tail. Its single bounded call covers the five demonstrated PDFs; future tail resumption remains explicit, never an unbounded loop. Original three-case replay now explicitly selects its three identities.

Candidate07280 passed Road Linux/Windows, Kean, publication audit, full Valla/native lifecycle/three-source custody checks and ordinary claim-kit+Kean production. Independently downloaded artifact12944962786 has SHA256e8f0bdff33ccd7b2eb7fc29e8db2e3171685664c42f042837586dd00f9f04e09. Valla loaded93tracked packages with zero absent; no examined reasoning dependencies or legal promotions inferred. Branch generated heada27af5b1 is retained as history, not adopted for changed follow-on inputs.

Current local487claim-kit tests pass with4corpus-dependent skips;69checker/materializer tests pass. Initial rerun failed because newly available census/status metadata enabled the historical population fixture but six authorization files were sparse-missing; exact files restored and rerun passed. Native local lifecycle replay preserves both positive controls and blocks five invalid variants. Native retained rehearsal was not run locally: its full prior-research/provider context exceeded the bounded hydration allowance. The existing CI now materializes research, retains native view/completion outcomes without repinning, compares Cruden legacy/cold/warm outputs, and runs five-source custody replay. Unexpected tracebacks or missing completion tallies fail the harness.

Shared substantive research has a handoff-only branch,7f653c20, and remains unfinished. No new Valla reasoning implementation branch/PR was found across130branches. Neither is presumed complete. Review/readiness/census/source-grade/human authority is unchanged. Production main remains pending;395 is still the last verified historical published ready total.

Fresh same-family independent follow-on review APPROVE at d56ba86ca703c14395bd13852aa62f514fc19465, conditional on exact native CI. Report SHA25683bdb4b45c1e34ea9bcb77d9933b7f33be643f16352997907edfd10b8d4e9a37;40unit tests and82overlapping challenge checks pass. All report-listed support artifacts are losslessly retained by filename in review/followon-support.tar.xz. Reviewed source hashes independently matched the final candidate before publication.

Compiler comparison: all15runner whitelist sources match PR104 b1890d7; all11reported compiler hashes,16shard hashes, counts, population hashes and warnings match between PR104 outputb8881 and combined outputa27af5b1. Their input commits differ; this is output equality, not a claim every noncompiler input was identical. Mechanical report validation/compiler-comparison.json uses local9dcb451e. Coordinator API publication independently verified its full tree651f9e8beb089783203b0cc00e16f6b19c18f999 equals remote4ef71ff4, supplying that report's missing remote-tree equivalence.

Coordinator found the first native harness used a nonexistent r1/completion path. The actual retained manifest is r1/packet/supp/completion/COMPLETION.json; path corrected without changing any packet/review bytes. Independent path review and replacement exact-candidate CI required; previous run remains historical.

PR110 sourcebbc66a83/handoff4b4f0c0d now retained as qualified research with original ancestry, without canonical claims/status writes or disputed historical adoption. Fresh bounded mechanical check confirms14assignments,2eligible,8blocked,4owner-routed,0exceptions/claims published/human certifications and exact publishable SHAfe5c3fafc4dacbe86e867450d457b94b043182b9f16bf72bd7c15be83e986a6a. Private control keys remain excluded. Historical first-control/review corrections, killed completion and unchanged-pin successful retry remain retained. Existing sourcegrade/replacement obligations remain; externalAPP rawHTML was not independently re-fetched byintegration. Combined nativeCI now exercises this manifest without --publish, retaining results or native frozen-input refusals and copying exact receipts into the validationartifact. This does not adopt its isolated395→397count.

Fresh independent shared-native amendment approves runtime/harness source8bd150ec conditional exactCI;21checks and26manifest references match. Report SHA07389f6a95909d6831cad7a56f9f0e69e397f61c3492b70c060c6d48ffa825e3. Root independently verified originalbaseline→PR110handoff all207paths stay in research/coordination and sourcehashes stillmatch. Earlier full run40979721659 finished computations but correctly refused publication after branch inputs changed; its497ready is an unpublished stale result, not the currentgeneration. Main refresh must run after the finalfreeze.

Actual native run40982822620 reached and passed the custody/lifecycle steps, then failed at retained-view before loading data: the harness incorrectly used Python-I, which removed sibling imports (ModuleNotFoundError:assemble). The corrected ordinary entrypoint omits-I for view and both complete calls. This does not change claim-kit implementation. Independent actual CLI missing-path and help probes exercise imports and handled native refusals;13checks pass. cli-entrypoint-amendment.json SHA9102f10031bd07ef5fb5cd3441a0a2123995668c6b07d8c95d58dff16da0895c. Earlier native successes are not inferred; final corrected invocation must run remotely.
