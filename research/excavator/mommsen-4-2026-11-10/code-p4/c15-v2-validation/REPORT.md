# C15 final candidate validation

Target main: `5f1193d62a5182a39c64c3d3c2903132e2d6873a`. Validated runtime/test tree: candidate `a5a6c23f7a8e89a56949a81875ad1b6195b9108a`; exact file hashes in VALIDATION_INPUTS.json. Final publication adds only this validation record and the register/brief.

Only five claim-kit runtime files, two claim-kit tests and one checker test differ. `git diff --stat origin/main...HEAD -- jobs/readiness-tracker` is empty. Tracker/Montfaucon routes, digest and counts remain target-main versions.

Fresh focused tests: assembly54, inputs30, build18, Lachmann8, cache16 and checker1:127 passed. Pass/fail/unsure/forged-provenance, false-original and required informational-flag assertions are included. Test logs and summaries are retained here; older code-p4 tests refer to their historical versions only.

Native checker selection scans1891 canonical claim lines, finds0 affected archival_replica_checked claims, and checks the explicit empty selector successfully. This asserts no existing affected claim and does not invent a scientific pass. Native paired tracker builds:1156 before and1156 after, byte-identical canonical order results.652 input diagnostics remain:445 missing/rejected Montfaucon checks,203 invalid Montfaucon official fragments and4 stale source-audit holds. Published main1223 is a separate generation. No scientific inputs or seals renewed. One inline replay quoting failure is retained, followed by successful native calls.

Artifact disclosure: superseded WIP.patch and intermediate0ed draft patch are unavailable; neither is relied-on evidence or reconstructed as an original.

No claims submitted/filed; human certification0. Claude full-diff review and owner code merge are required. This lane cannot merge code. Source exceptions for3403/3415/3885B remain separate.
