# STAGE 14 — THE LEVERAGE ENGINE

**Project:** The Afterlife of Executive Orders. **Research cutoff:** October 14, 2026. **Built:** October 16, 2026. **Output:** a reusable source-and-dependency platform that makes later legal research cheaper and less repetitive. Not a new legal-status stage.

## What was actually built

1. Indexed 15,010 immutable Stage 11 bibliographic/status records with Stage 13 identity/date projections into `DATA/EO_SOURCE_DEPENDENCY_GRAPH.sqlite`. The original 14,973 validated bibliography entries and 14,972 de-duplicated working proxies remain separately distinguishable. No status decisions changed.
2. Joined all **11,164** cached NARA/Office of the Federal Register editorial source rows to their originating **25** frozen official cache files by byte SHA. Added **6,575** nonquarantined *candidate* actor-to-predecessor relationships plus **117** explicitly quarantined extracted hypotheses. Historical editorial dates are preserved; they are not current-law conclusions.
3. Compiled **1,029** controlling-actor clusters with research dependencies. **1,369** still-UNKNOWN orders have potential ending-instrument relationships; **895** orders accepted NO but lacking first-cause determinations also appear in ending-reference chains. These are **nonadditive evidence-search opportunities**. A formal endpoint may supply only a latest possible end date; the scheduler heavily downweights that reference for first-cause work.
4. Built a source-vault FTS index from previously saved Opus/Astra evidence. **1,051** file representations de-duplicate to **966** content SHA blobs. **243** candidate representations look like EO-text caches by filenames, but no unreviewed text has been promoted to an authenticated original. **158** extracted files match their recorded text-byte SHA; zero recorded mismatches in that subset. **17** blocked/unsuitable pages are specifically flagged. Other cache source types (statutes, news, agency, index, snippets) remain available for search with their provenance.
5. Built an explicit-URL fetch manifest from the prior Federal Register API export: **4,331** HTML/PDF/XML URLs for **1,546** distinct EO identities, including **1,144** currently substantive-UNKNOWN identities. Fixed 32 hyphenated lettered-label joins with a reversible normalized crosswalk. No downloaded-primary-document claim is made: a network test failed DNS resolution in this runtime; the documented optional source fetcher is portable to a network-enabled environment.
6. Generated 20 actor-centered workpacks and 60 truly blind-source packets. They include recovered source-cache references, official editorial claims, known caveats and legal review checklists. Blind packets exclude the current ledger's answer fields.
7. Built `LORD/LORD_SOURCE_REVIEW.html`: 226 historical chronology pages, 1,023 unverified date markers, short extracted snippets, links to the LOC scans and an **exportable human review form** to mark provisional keep/split/merge/reject/hold. None is admitted to the EO census without original-document/authorship confirmation. Multiple documents per same date remain possible, so 1,023 is not a count of orders.
8. Ran a reusable, line-anchored schedule-to-graph test on **EO 12553**: the 386 distinct predecessors listed in the cached hosted order text match the 386 distinct nonquarantined actor-target references exactly. This tests one major source-enumeration extraction, *not* legal cessation of all 386 or first-cause classification.
9. Compiled `QUEUES/EXECUTION_ACTIONS_DEPENDENCY_FIRST.csv`, source-action queues for Astra/Opus, and correlated-review exposure groups, distinguishing documents already cached from those with direct official URLs and those still needing archival discovery.
10. Created a self-checking one-command offline rebuild, source retrieval tooling, graph search CLI and integrity verifier. `REPORTS/STAGE14_VERIFICATION.json` says PASS.

## Scientific progress

**Frozen substantive findings:** YES 193; NO 2,322; UNKNOWN 12,458 of the 14,973 bibliographically included entries. 14,972 is the deduplicated working-document proxy denominator, making the corresponding UNKNOWN count 12,457. Source-index, evidence availability and decision-readiness improved; **zero** substantive statuses, zero first cessation mechanisms and zero original-document identity adjudications were newly accepted by Stage14.

The general source graph can help workers search *once* for relevant ends and dependencies. It is not a proof graph of law in force. **2,216** substantive-NO orders still have `cessation_mechanism: unknown` in the frozen Stage 11 ledger.

## Immediate usage (already built)

From this folder:

```
python SCRIPTS/eo_leverage_engine.py show --database DATA/EO_SOURCE_DEPENDENCY_GRAPH.sqlite --id EO:13286
python SCRIPTS/eo_leverage_engine.py cluster --database DATA/EO_SOURCE_DEPENDENCY_GRAPH.sqlite --actor EO:12553
python SCRIPTS/eo_leverage_engine.py search --database DATA/EO_SOURCE_DEPENDENCY_GRAPH.sqlite --query 'civil service' --limit 10
python SCRIPTS/eo_leverage_engine.py search-cache --database DATA/EO_SOURCE_DEPENDENCY_GRAPH.sqlite --query 'Wool Textile' --limit 10
python SCRIPTS/eo_leverage_engine.py source --database DATA/EO_SOURCE_DEPENDENCY_GRAPH.sqlite --id EO:12553 --max-chars 13000
python SCRIPTS/verify_stage14.py .
```

For one offline rebuild, use `SCRIPTS/run_stage14_all.py` with the complete source ZIPs (Stage11 compact; Stage11 full-source handoff; Stage10 government importer), Stage13 projected JSONL, the Stage12 60-case blind sample, the Stage13 Lord geometry leads and the 1943 Lord PDF. Those prior releases are in `/Executive Order Research/Checkpoints/` or `/Executive Order Research/Sources/` in Library. Large originals are not duplicated in this audit release. All relevant upstream ZIP hashes and verification are in `REPORTS/ENGINE_METRICS.json`. The tool does NOT require external browsing.

With network access, optionally run `SCRIPTS/fetch_verified_official_urls.py --manifest QUEUES/OFFICIAL_DIRECT_DOCUMENT_FETCH_MANIFEST.csv --destination SOURCES/OFFICIAL_PRIMARY_CACHE --limit 10 --delay 1.5`. It only accepts explicit official-source URLs with restrictive host checks, rate limits and a raw-byte acquisition log. Do not infer saved or legally verified originals until the logs show successful retrieval and further content checks pass.

## Highest-return next operations; not yet completed

1. Use the indexed cached materials first and bulk-fetch missing originals for the **210 Stage11 priority-queue orders** for which direct official URLs are now known, in a network-enabled environment. Avoid re-fetching when matching complete originals are already in the source vault.
2. Build a reliable physical-document crosswalk for Lord's over-1,500-entry unnumbered historical source; the provisional browser helps document-level review but is not the final extractor. Address grouped descriptions and unavailable original manuscripts.
3. Quality-gate EO12553, EO11408, EO9521, EO3461 and similar high-fanout conditional/savings actors **once for each legally distinct subtype** before applying findings in batches. The EO12553 *enumeration* is verified, but its legal scope, rights and first-cause questions remain open.
4. Complete the independent 60-case source-first legal audit (eight first-pass cases were reviewed in Stage13; Stage14 produced no additional legal adjudications). Use the baseline answer key only after freezing each independent decision.
5. Construct original clause + later-event intervals across authentic, probability-sampled issued EOs to allow causal inference and Kaplan-Meier/competing-risk analysis. An actor revocation is not an automatic first-cause observation.

## Research integrity

Source files are not legal conclusions, a FTS result is not an original signed instrument, an editorial link is not a whole-order revocation, and a checksum is not proof that the original government document was properly captured. `PRIORITIZATION_CONTRACT.md` is a new standing workflow rule for future agents; the controlling legal codebook 2.0.0 and Stage 11 decisions remain frozen. All file modifications from this stage are new versioned outputs in a separate folder.
