# Producer handoff: bounded EO11490 evidence pilot

**Two proposed claims, three retained blocks, zero published claims or asserted readiness gain.** Producer: `codex-swarm-producer` (AI). Both exact proposals are now upheld by the separate independent AI reviewer after codebook verification; this is never an independent-human certification. Original main: `cd5dba93874a04e014b0167293fd2a95dffca63b`. No provisional status, census, source hold or canonical claim was changed.

## Outputs and why these cases

The prior F11490 pool was selected from the current handoff after the shared ending source became available. All five identities were unclaimed in canonical claims and unreserved at preparation; packet ownership and source fingerprints were preserved by the standard `kit.py prepare` path. Three sealed packets retain all five attempts.

- **EO11087 (State)** and **EO11089 (Atomic Energy Commission):** [frozen proposed claims](packet-v1/applied-v1/CLAIMS.proposed.jsonl). Complete official original pages inspected (28 FR1835–1836 and1839–1840); exact held texts reviewed. Their commands establish continuing preparedness and supporting functions. Original text expressly makes planning part of continuing activities. A performed plan or installment does not end that standing duty. The held OFR catalog edges identify only EO11490; no earlier ending appears in the frozen dossier. EO11490 §3015 names both, and §3014 expressly excepts §3015 from its retained-authority provision. Proposed first ends are October 28, 1969, on the signed immediate revocation. Similar functions reissued by EO11490 are treated as separately authorized, not as continued legal force of the original order.
- **EO11088 (Treasury): blocked.** Original §2(12) narcotics and §2(16) Coast Guard functions raise intervening agency-transfer questions. EO11490 §101 explicitly warns of organizational changes. No first transfer date or legal effect was assumed.
- **EO11090 (Civil Aeronautics Board): blocked.** Original §3(d) accident investigation raises the intervening DOT/NTSB transfer question. Exact transfer, savings and effective-date evidence must be read.
- **EO11092 (FCC): blocked.** Original §9 expressly preserves subordinate telecom orders rooted in EO10705/10995/11051 and predecessors. Those savings and possible earlier changes were not silently treated as closed.

The EO11087/11089 inventories had missing whole sections. Exact original-source offsets now retain complete sections 1–8 and 1–7, including scope, evaluation, emergency-authority limits and prior-actions provisions. Corrected inventory rows are in [corrected inventory rows](packet-v1/clauses.csv). Full subparts remain included. The section-level grouping asserts a common first end for each included obligation; the reviewer must challenge that assertion, not just check text coverage.

## Actual verification

Standard `apply` produced 2 proposals and 1 blocked member in the first packet; the other packets preserve one block apiece. Standard `batch-check` ran the real claim-checker: **2 checked, 2 all-checks-passed, 2 structural passes, 0 mechanical failures, 0 unverified claims**. The detailed audit and log are in [actual checker report](packet-v1/applied-v1/actual-checker/REPORT.md), [check summary](packet-v1/applied-v1/CHECK_SUMMARY.json) and [checker log](packet-v1/applied-v1/CHECKER.log). Source references: 36 published-GPO hash matches; identity checks 17; exact quotations 51. This is a mechanical result, not a legal conclusion or proof of completeness.

The checker ran offline against held provenance/text. Its environment lacked some unrelated archive inputs and `pypdf`; these warnings are preserved in its log. Independently retrieved official PDFs matched the exact existing hashes: FR1963-02-28 `ebb2bd8d0dacda2dd7840bb9fd1c031a649f116ac29750854a9a2f8e51277fcd`, FR1969-10-30 `0e1eda31eff5ec1d4aa81a8172be39e348c1ec5e486568e0e59d1ebfc93895ea`. Large PDFs remain local scratch outside the repository production tree. [source verification record](verification/SOURCE_VERIFICATION.json) records exact URLs, hashes, bytes, local location, and the explicit list of page images actually inspected. Only the eight inspected images are retained; see the [portable source navigation](verification/README.md). Historical absolute paths in raw records are not publication dependencies. No existing source receipt was overwritten.

## Required independent review and limitation

**The original missing-codebook blocker is resolved.** The exact existing frozen codebook 2.0.0 was recovered from the pinned main archive and authenticated against both the nested ZIP hash and its member SHA-256 manifest. Its bytes and provenance are in [verification/codebook](verification/codebook/README.md). This supplies the existing method; it does not change that method. The original availability statement remains in `PILOT.json` as a historical snapshot, superseded only on that point by [METHODOLOGY_RECOVERY.json](METHODOLOGY_RECOVERY.json).

The [initial independent AI review](../reviewer/REPORT.initial-codebook-hold.md) supported source components and retained a methodology hold. The [final independent AI review](../reviewer/REPORT.md) and [exact review records](../reviewer/REVIEW.jsonl) supersede that hold: **both exact proposals upheld, all three producer blocks upheld**. The reviewer applied the recovered codebook to clause grouping, first cessation, delegation/authority limits and saved independent acts. No original packet, decision, claim hash or checker result was regenerated. Canonical publication and an actual tracker replay remain the coordinator’s responsibility; this producer package asserts no readiness increment.

Review priority: verify every original section and its subduties, challenge any earlier cessation/transfer, distinguish the continuing function from the continuing original source, verify immediate effect from the signed revocation, and test whether §3014 or any independent saved obligation defeats the proposed disposition. The bounded U.S.Code machine search is current only through 2026-10-09; it was treated as corroboration, never a claimed YES predicate through 2026-10-14. The source search is bounded; no exhaustive absence proof is asserted.

No planted controls, reviewer-sensitivity estimate, token savings, dollar savings or per-order time measurements were produced. Packet preparation runtimes and bytes in PREPARE.json are machine observations only. Model token telemetry and active/per-order labor are unavailable. Work includes clone wait, five preflights, one sandbox network failure, one missing renderer-library probe, source downloading, inventory correction and validation. The independent review and its initial hold are recorded separately; reviewer labor and codebook recovery are not included in the preparation-to-check timing interval. Filesystem timestamps place first packet preparation at 15:38:10 ET and the successful check summary at 15:41:32 ET on October 21, about 3 minutes 22 seconds apart. This interval excludes earlier reading/clone wait and later codebook recovery and is not a per-order labor or savings estimate.

## Replay

From repository root, with the unchanged claim-kit code pins and held sources:

```sh
python3 jobs/claim-kit/kit.py batch-check research/production/codex-swarm-20261021/producer/packet-v1 research/production/codex-swarm-20261021/producer/packet-v1/applied-v1
```

The apply results and originals are immutable versions. To change producer decisions, retain these records, edit a copied/new packet version as required by the protocol, and apply into a fresh output directory. `write_decisions.py` records the explicit original producer decisions but overwrites decision CSVs if rerun; do not run it against a reviewed version. No command here publishes to `research/readiness/claims/`.
