# Exact adoption and replay

This PR contains reviewed research and isolated native completion output. It does not publish canonical claims, modify statuses, or approve any historical owner's replacement claim.

## Selected artifact

- Bytes: `new-v1/packet/supp/completed-v3/CLAIMS.publishable.jsonl`
- SHA256: `fe5c3fafc4dacbe86e867450d457b94b043182b9f16bf72bd7c15be83e986a6a`
- Proposed native destination: `research/readiness/claims/shared-research-2026-10-29-nra.jsonl`
- EO6847A canonical claim hash: `d9b58fdc13144e42a59dab92e9377ef44dc0de4a4ba257f904ac00b17a5425dd`
- EO6925A canonical claim hash: `eba666352fb572539a17e0dae6e4d03f93f656efd890e55fac7a0cec968c26ac`
- Native manifest: `completion-v2/COMPLETION.json`; final successful output: `new-v1/packet/supp/completed-v3/`.

The first genuine claim uses final blind review line 1; the second uses genuine after-reveal review. `completion-v2/CONTROL_ADJUDICATION.json` binds the strictly caught final control. The eight blocks and four owner routes are explicit manifest members. Human certifications: zero. Both eligible claims retain the provisional-transcription original-replacement and quotation-recheck obligations.

## Frozen replay

Use a separate checkout of PR104 full commit `8adc9396cfd6da015757466b95ca6fa8ab1a4b9a`, with its pinned data and held source bytes. Overlay only this PR's `research/excavator/shared-research-production/` artifacts. Do not substitute current-main code, regenerated dossiers, a newer Cruden, or later scientific records without re-preparation and exact-version review as required by the native contracts. `FREEZE.json`, `measurements/RUNTIME_COMPATIBILITY.json`, the packet fingerprints, and `completed-v3/INPUTS.json` record the actual pins. This is not a combined PR103/104 engineering approval.

From the runtime repository root, run the ordinary native command with a fresh isolated destination:

```sh
python3 jobs/claim-kit/kit.py complete   research/excavator/shared-research-production/completion-v2/COMPLETION.json   --write research/excavator/shared-research-production/new-v1/packet/supp/completed-replay
```

Do not add `--publish` for this assignment. Native completion must again validate controls, exact review records, sources, unchanged dependencies, checker and actual tracker replay. Do not copy the proposed file into canonical claims as a substitute for that transaction. The current artifact is adoption-ready at its frozen inputs; changed inputs may require new review, and the destination must still be unoccupied.

Six large derived replay outputs are stored as `.gz` in the PR. `new-v1/packet/supp/completed-v3/LARGE_OUTPUTS.json` records each native path, original SHA256 and compressed SHA256. Python `gzip.decompress` restores byte-identical files if full raw tracker output is needed. The manifest, selected/publishable claim lines, checker, source reviews, tally, publication receipt and dependency receipts are directly readable without decompression. Private control keys and raw plants are deliberately not part of the PR.

## Historical owner routing

`reconcile-v1/packet/APPLICATIONS-v2.json` names each old claim path and canonical hash. EO6686 and EO6729 need individual administrative/report analysis; EO6870A also lacks its approved attachment and demonstrated replacement appointments; EO6861 has affirmative report evidence but needs amended continuing duties represented as later events. These are reviewed correction targets, not completed replacement claims. Their owners retain control of any correction. Prior versions and qualification corrections are preserved.
