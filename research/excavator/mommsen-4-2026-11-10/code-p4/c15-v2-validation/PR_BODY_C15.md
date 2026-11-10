Claim-kit refuses checked ProQuest replica texts that already passed the owner-authorized Photius P4 route. This wires D-20261106-photius-p4 under C11/C15, accepting only exact trusted FINAL PASS records while retaining acceptable_as_original=false and REPLICA_CHECKED_PROQUEST_BYTES.

Revised head: 3130e5b7f4781e1adae183be638b0094ecf9c5c0. The runtime diff is confined to five claim-kit files, with two claim-kit tests and one checker test. **Every tracker runtime/test hunk is removed.** `git diff --stat origin/main...HEAD -- jobs/readiness-tracker` produces empty output. Target-main Montfaucon routes/digest/counts remain intact.

Fresh exact-candidate validation:127 focused tests passed (assembly54, inputs30, build18, Lachmann8, cache16, checker1). Coverage includes pass, fail, unsure, forged producer/path, conflicting versions, explicit incompleteness/page debt, false original flag and required informational flag. Scoped native claim-checker scanned1891 canonical claim lines and found0 existing affected checked-replica claims; the explicit empty selector succeeded. Kean strict check passed. Old code-p4 test receipts remain historical.

Local native readiness replay: **1156 before,1156 after**, identical per-order results across all14998 identities, with the same652 sparse/source-audit diagnostics. Published main1223 is a separate generation. No new claims, source grades, statuses, census, codebook, workflow or human-certification change. Exact pins, focused logs, native selection and paired replay are in research/excavator/mommsen-4-2026-11-10/code-p4/c15-v2-validation/REPORT.md and sibling receipts.

Draft loss disclosure: superseded WIP.patch and the intermediate0ed draft patch are unavailable; neither is relied-on evidence or reconstructed as an original.

**Claude full-diff review requested on the revised head. Owner code merge required; this lane will not merge code.** Source corrections and first-end/savings review for EO3403/3415/3885B remain separate and unpublished.
