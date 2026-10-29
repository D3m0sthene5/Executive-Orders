# 5. Shepard and retained PLO extracts into native source supplements

`jobs/fr-pages/land_handoff.py` connects the existing FR-page records to the exact `eo-source-excerpt-declarations/v1` contract consumed by claim-kit's source_supplement.prepare. The two initial targets are EO7373 and EO7510; the audit identified already-held PLO570/PLO4079 and PLO1249 extracts respectively.

The default path reads retained excerpts only. It checks both raw PDF and text SHA-256, producer-relative confinement, an explicit later-instrument role, high location confidence and the producer's page-check flag. Missing or mismatched bytes and ambiguous actor versions stay in HANDOFF.json holds. A high-confidence machine location remains unreviewed evidence. PLO actor labels and target EO identities are separate; no target original is manufactured. Existing native preparation verifies parent packet lineage and preserves blank legal judgments.

## Held-source preparation

First prepare an ordinary parent packet for the two targets through `kit.py prepare`, preserving its normal rules and independent-review requirements. Then use fresh destinations:

```sh
python jobs/fr-pages/land_handoff.py --repo . declare --ids EO:7373 EO:7510 --write research/excavator/land-handoff/held
python jobs/fr-pages/land_handoff.py --repo . prepare --ids EO:7373 EO:7510 --parent research/excavator/land-handoff/parent --agent Astra --write research/excavator/land-handoff/supplemented
```

The second command calls the existing source_supplement.prepare; it does not fill a legal decision or file a claim. The first is an independently usable declaration/provenance preview.

## Optional bounded acquisition, kept separate

```sh
python jobs/fr-pages/land_handoff.py --repo . acquire --ids EO:7373 EO:7510 --write research/excavator/land-handoff/acquisition
```

This explicit command reuses frpages.auto_wanted and frpages.run. It selects at most three missing PLOs for one or two explicit target EOs, skips rehashed held actors, writes a pinned plan and temporary configuration, and uses the native downloader with 24-request, 40-MB-per-issue and 120-MB-total settings. Issue slicing stays disabled. Global settings, scheduled acquisition and canonical outputs are unchanged. Inspect the resulting source records before passing their SOURCES.jsonl through `--sources` to a fresh declaration/preparation. No cyclic claim-kit-after-Shepard dependency is introduced.

Twelve focused local tests passed. They cover exact native declaration fields, actor/target separation, raw/text failures, missing custody, location holds, path traversal, duplicate association merging, conflicting actor versions, fresh destinations, acquisition selection/configuration with a mocked native downloader, and zero-download no-op. A live download and a complete research/review cycle were not performed for this code PR; no readiness or savings result is claimed. Existing fr-pages job now includes these tests. Leave unmerged.
